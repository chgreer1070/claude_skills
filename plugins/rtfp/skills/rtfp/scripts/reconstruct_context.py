#!/usr/bin/env -S uv --quiet run --active --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Reconstruct context around flagged user reactions from a session transcript.

Stage 3 of the RTFP pipeline. Takes a merged set of flagged user message
indexes (from Stage 2 detection across all batches) and the session JSONL file
path. Reads the full session transcript, retrieves those flagged user messages
plus nearby context, identifies the assistant message(s) that triggered each
reaction, determines the current task, and selects the best candidate(s).

Input (stdin JSON or --flagged-file)::

    {
        "source_file": "/path/to/session.jsonl",
        "flagged": [{"index": 0, "source_file": "...", "timestamp": "...", "content": "..."}],
    }

Output (stdout, JSON)::

    {
        "source_file": "/path/to/session.jsonl",
        "winner": {
            "task_summary": "task: writing a Claude Code plugin",
            "triggering_assistant_output": "...",
            "user_reaction": "...",
        },
        "runner_up": null,
    }

Usage::

    reconstruct_context.py --flagged-file /tmp/flagged.json
    reconstruct_context.py --flagged-file /tmp/flagged.json --session-file /path/to/session.jsonl
    cat flagged.json | reconstruct_context.py
"""

from __future__ import annotations

import argparse
import json
import operator
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_CONTEXT_WINDOW = 3  # messages before the triggering assistant message
_MAX_ASSISTANT_CHARS = 2000  # truncation limit for assistant output
_TRUNCATION_NOTE = " [truncated, {remaining} chars omitted]"
_TOOL_INPUT_PREVIEW_LEN = 80  # max chars for a tool_input value preview
_TASK_SUMMARY_MAX_LEN = 60  # max chars for a context-derived task summary
_SHORT_MSG_WORDS = 15  # word count below which density bonus is highest
_MEDIUM_MSG_WORDS = 30  # word count below which a smaller density bonus applies

# ---------------------------------------------------------------------------
# JSONL loading
# ---------------------------------------------------------------------------


def _load_transcript(session_path: Path) -> list[dict]:
    """Load all messages from a session JSONL file in order.

    Each returned dict has at minimum: type, message, timestamp.
    An ``_line_index`` field is added for positional reference.

    Args:
        session_path: Path to the session JSONL file.

    Returns:
        Ordered list of parsed message records.
    """
    records: list[dict] = []
    with session_path.open(encoding="utf-8", errors="replace") as fh:
        for i, line in enumerate(fh):
            raw = line.strip()
            if not raw:
                continue
            try:
                rec = json.loads(raw)
            except json.JSONDecodeError:
                continue
            if isinstance(rec, dict):
                rec["_line_index"] = i
                records.append(rec)
    return records


# ---------------------------------------------------------------------------
# Content extraction
# ---------------------------------------------------------------------------


def _extract_user_text(content: str | list | None) -> str:
    """Extract readable text from a user message content field.

    Args:
        content: Raw content from the message object.

    Returns:
        Plain text representation of the user message.
    """
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    parts: list[str] = []
    for element in content:
        if isinstance(element, dict) and element.get("type") == "text":
            text = element.get("text")
            if isinstance(text, str):
                parts.append(text)
    return "\n".join(parts)


def _extract_assistant_text(content: str | list | None) -> str:
    """Extract readable text from an assistant message content field.

    For tool_use blocks, produces an inline summary. For text blocks,
    includes the full text.

    Args:
        content: Raw content from the message object.

    Returns:
        Human-readable representation of the assistant message.
    """
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    parts: list[str] = []
    for element in content:
        if not isinstance(element, dict):
            continue
        match element.get("type"):
            case "text":
                text = element.get("text")
                if isinstance(text, str):
                    parts.append(text)
            case "tool_use":
                name = element.get("name", "unknown_tool")
                tool_input = element.get("input", {})
                brief = _summarize_tool_input(tool_input)
                parts.append(f"[{name}: {brief}]")
    return "\n".join(parts)


def _summarize_tool_input(tool_input: dict) -> str:
    """Produce a brief description of a tool_use input dict.

    Args:
        tool_input: The input dict from a tool_use content block.

    Returns:
        Short summary string.
    """
    if not isinstance(tool_input, dict):
        return "..."
    # Prefer common keys that describe the action
    for key in ("command", "file_path", "pattern", "query", "url", "content"):
        if key in tool_input:
            val = str(tool_input[key])
            if len(val) > _TOOL_INPUT_PREVIEW_LEN:
                val = val[: _TOOL_INPUT_PREVIEW_LEN - 3] + "..."
            return f"{key}={val}"
    # Fallback: list keys
    keys = list(tool_input.keys())[:4]
    return ", ".join(keys) if keys else "..."


def _truncate_assistant_output(text: str) -> str:
    """Truncate assistant output if it exceeds the character limit.

    If truncation occurs, appends a note indicating how many characters
    were omitted.

    Args:
        text: Full assistant text.

    Returns:
        Possibly truncated text with truncation notice.
    """
    if len(text) <= _MAX_ASSISTANT_CHARS:
        return text
    remaining = len(text) - _MAX_ASSISTANT_CHARS
    note = _TRUNCATION_NOTE.format(remaining=remaining)
    return text[:_MAX_ASSISTANT_CHARS] + note


# ---------------------------------------------------------------------------
# Transcript indexing
# ---------------------------------------------------------------------------


def _build_user_index(records: list[dict]) -> dict[int, int]:
    """Build a mapping from user-message-index to record position.

    The user-message-index is the sequential count of user messages
    (matching the indexing in extract_batches.py), while the record
    position is the index into the full records list.

    Args:
        records: Full transcript records.

    Returns:
        Dict mapping user_msg_index -> records list position.
    """
    noise_prefixes = (
        "<local-command-caveat>",
        "<bash-stdout>",
        "<tool_use_error>",
        "<task-notification>",
        "<command-message>",
        "<system-reminder>",
    )
    user_index_map: dict[int, int] = {}
    user_counter = 0
    for pos, rec in enumerate(records):
        if rec.get("type") != "user":
            continue
        if "toolUseResult" in rec:
            continue
        content = _extract_user_text(rec.get("message", {}).get("content"))
        if not content:
            continue
        stripped = content.lstrip()
        if any(stripped.startswith(p) for p in noise_prefixes):
            continue
        user_index_map[user_counter] = pos
        user_counter += 1
    return user_index_map


def _find_preceding_assistant(records: list[dict], pos: int) -> int | None:
    """Find the record position of the assistant message immediately before pos.

    Args:
        records: Full transcript records.
        pos: Position of the user message in the records list.

    Returns:
        Position of the preceding assistant message, or None if not found.
    """
    for i in range(pos - 1, -1, -1):
        if records[i].get("type") == "assistant":
            return i
    return None


def _infer_task_summary(records: list[dict], pos: int) -> str:
    """Infer a dry one-line task summary from context around a message position.

    Looks at the user messages in the surrounding window to determine what
    the user was working on.

    Args:
        records: Full transcript records.
        pos: Position of the flagged user message.

    Returns:
        A dry task summary like "task: writing a CLI tool".
    """
    # Collect user messages from the window before the reaction
    context_texts: list[str] = []
    count = 0
    for i in range(pos - 1, -1, -1):
        if count >= _CONTEXT_WINDOW * 2:
            break
        rec = records[i]
        if rec.get("type") == "user" and "toolUseResult" not in rec:
            text = _extract_user_text(rec.get("message", {}).get("content"))
            if text and not text.lstrip().startswith("<"):
                context_texts.append(text)
                count += 1

    # Simple heuristic: look for file paths, command names, and action verbs
    # in the context to determine activity
    all_context = " ".join(reversed(context_texts))

    # Try to find file extensions being worked on
    file_patterns = re.findall(r"[\w/.-]+\.(?:py|ts|js|md|yaml|yml|toml|json|sh)\b", all_context)
    # Try to find action verbs
    action_match = re.search(
        r"\b(creat|writ|build|implement|refactor|fix|debug|test|deploy|configur|migrat|updat|add|review|edit|analyz)"
        r"(?:e|ing|ed|s)?\b",
        all_context,
        re.IGNORECASE,
    )

    action = action_match.group(0).lower() if action_match else "working on"
    # Normalize to gerund
    if action.endswith("e") and not action.endswith("ing"):
        action = action.rstrip("e") + "ing"
    elif not action.endswith("ing"):
        action += "ing"

    if file_patterns:
        # Infer from file extension what kind of project
        ext = Path(file_patterns[0]).suffix
        project_types = {
            ".py": "a Python script",
            ".ts": "a TypeScript project",
            ".js": "a JavaScript project",
            ".md": "documentation",
            ".yaml": "configuration",
            ".yml": "configuration",
            ".toml": "configuration",
            ".json": "a JSON file",
            ".sh": "a shell script",
        }
        target = project_types.get(ext, "code")
        return f"task: {action} {target}"

    if all_context:
        # Take first meaningful phrase from context
        first_line = all_context.split("\n")[0].strip()
        if len(first_line) > _TASK_SUMMARY_MAX_LEN:
            first_line = first_line[: _TASK_SUMMARY_MAX_LEN - 3] + "..."
        return f"task: {first_line}"

    return "task: working in a Claude Code session"


# ---------------------------------------------------------------------------
# Candidate scoring
# ---------------------------------------------------------------------------

_PROFANITY_PATTERNS: list[re.Pattern[str]] = [
    re.compile(p, re.IGNORECASE)
    for p in [
        r"\bfuck(?:ing|ed|s)?\b",
        r"\bshit(?:ty|s)?\b",
        r"\bwtf\b",
        r"\bwth\b",
        r"\bffs\b",
        r"\bomfg?\b",
        r"\bdamn\s*it\b",
        r"\bfor\s+fuck'?s\s+sake\b",
        r"\bjesus\s*christ\b",
        r"\bgod\s*damn\b",
        r"\bholy\s+shit\b",
        r"\bbullshit\b",
    ]
]

_CAPS_WORD_RE = re.compile(r"\b[A-Z]{2,}\b")
_BENIGN_ACRONYMS = frozenset({
    "API",
    "URL",
    "CLI",
    "JSON",
    "YAML",
    "TOML",
    "HTML",
    "CSS",
    "HTTP",
    "HTTPS",
    "SQL",
    "SSH",
    "CI",
    "CD",
    "PR",
    "MR",
    "ID",
    "UUID",
    "OK",
    "AWS",
    "GCP",
    "UI",
    "UX",
    "README",
    "TODO",
    "FIXME",
    "NOTE",
    "ENV",
    "CPU",
    "GPU",
    "RAM",
    "OS",
    "IO",
    "TCP",
    "UDP",
    "DNS",
    "TLS",
    "SSL",
    "PDF",
    "CSV",
    "XML",
    "RFC",
    "TTY",
    "PEP",
    "EOF",
    "UTF",
    "ASCII",
    "CRUD",
    "REST",
    "GRPC",
    "SDK",
    "CDN",
    "VM",
    "LLM",
    "GPT",
    "AI",
    "ML",
    "NLP",
    "STDIN",
    "STDOUT",
    "STDERR",
    "RTFP",
    "PNG",
    "SVG",
})
_EXCESSIVE_PUNCT_RE = re.compile(r"[!?]{3,}|!{2,}\?|!\?{2,}")


def _score_signal_density(text: str) -> float:
    """Score the emotional signal density of a user message.

    Higher scores indicate more emotionally charged content. Factors:
    - Profanity count (weighted heavily)
    - ALL-CAPS words (non-acronym)
    - Excessive punctuation runs
    - Short message bonus (density amplifier)

    Args:
        text: User message text.

    Returns:
        Numeric density score (higher = more emotional).
    """
    profanity_count = sum(1 for pat in _PROFANITY_PATTERNS if pat.search(text))
    caps_words = [w for w in _CAPS_WORD_RE.findall(text) if w not in _BENIGN_ACRONYMS]
    punct_runs = len(_EXCESSIVE_PUNCT_RE.findall(text))
    word_count = max(1, len(text.split()))

    # Base score from signals
    score = (profanity_count * 3.0) + (len(caps_words) * 1.0) + (punct_runs * 2.0)

    # Density bonus: short angry messages score higher per-word
    if word_count < _SHORT_MSG_WORDS:
        score *= 1.5
    elif word_count < _MEDIUM_MSG_WORDS:
        score *= 1.2

    return score


# ---------------------------------------------------------------------------
# Candidate construction and selection
# ---------------------------------------------------------------------------


def _build_candidate(records: list[dict], user_index_map: dict[int, int], flagged: dict) -> dict | None:
    """Build a reconstruction candidate from a flagged message entry.

    Args:
        records: Full transcript records.
        user_index_map: Mapping from user-message-index to record position.
        flagged: Flagged entry dict with at least an "index" key.

    Returns:
        Candidate dict with task_summary, triggering_assistant_output,
        user_reaction, and score. None if the index cannot be resolved.
    """
    user_msg_index = flagged.get("index")
    if user_msg_index is None:
        return None

    pos = user_index_map.get(user_msg_index)
    if pos is None:
        print(f"  Warning: user message index {user_msg_index} not found in transcript", file=sys.stderr)
        return None

    # Get the user reaction text
    user_rec = records[pos]
    user_text = _extract_user_text(user_rec.get("message", {}).get("content"))
    if not user_text:
        return None

    # Find the triggering assistant message
    asst_pos = _find_preceding_assistant(records, pos)
    if asst_pos is not None:
        asst_rec = records[asst_pos]
        asst_text = _extract_assistant_text(asst_rec.get("message", {}).get("content"))
        asst_text = _truncate_assistant_output(asst_text)
    else:
        asst_text = "(no preceding assistant message found)"

    # Infer what the user was doing
    task_summary = _infer_task_summary(records, pos)

    return {
        "task_summary": task_summary,
        "triggering_assistant_output": asst_text,
        "user_reaction": user_text,
        "score": _score_signal_density(user_text),
    }


def select_candidates(candidates: list[dict]) -> tuple[dict | None, dict | None]:
    """Select the winner and optional runner-up from scored candidates.

    The winner is the candidate with the highest signal density score.
    A runner-up is selected if it has notably different content from the
    winner (different user reaction text).

    Args:
        candidates: List of candidate dicts, each with a "score" key.

    Returns:
        Tuple of (winner, runner_up). Either may be None.
    """
    if not candidates:
        return None, None

    sorted_candidates = sorted(candidates, key=operator.itemgetter("score"), reverse=True)
    winner = sorted_candidates[0]

    # Find runner-up with notably different content
    runner_up: dict | None = None
    for candidate in sorted_candidates[1:]:
        # Consider "notably different" if the user reaction text differs
        # by more than just punctuation/caps
        winner_normalized = re.sub(r"[^a-z\s]", "", winner["user_reaction"].lower())
        cand_normalized = re.sub(r"[^a-z\s]", "", candidate["user_reaction"].lower())
        if winner_normalized != cand_normalized:
            runner_up = candidate
            break

    return winner, runner_up


def _format_output(candidate: dict) -> dict:
    """Strip internal scoring fields from a candidate for output.

    Args:
        candidate: Candidate dict with score and content fields.

    Returns:
        Dict with only task_summary, triggering_assistant_output, user_reaction.
    """
    return {
        "task_summary": candidate["task_summary"],
        "triggering_assistant_output": candidate["triggering_assistant_output"],
        "user_reaction": candidate["user_reaction"],
    }


# ---------------------------------------------------------------------------
# Main reconstruction
# ---------------------------------------------------------------------------


def reconstruct(input_data: dict, session_override: str | None = None) -> dict:
    """Run the full reconstruction pipeline.

    Args:
        input_data: Parsed input JSON with "source_file" and "flagged" keys.
        session_override: Optional session file path override.

    Returns:
        Result dict with "source_file", "winner", and "runner_up" keys.
    """
    source_file = session_override or input_data.get("source_file", "")
    flagged_entries: list[dict] = input_data.get("flagged", [])

    if not source_file:
        print("Error: no source_file specified in input or via --session-file", file=sys.stderr)
        sys.exit(1)

    session_path = Path(source_file)
    if not session_path.exists():
        print(f"Error: session file not found: {session_path}", file=sys.stderr)
        sys.exit(1)

    if not flagged_entries:
        print("No flagged messages in input.", file=sys.stderr)
        return {"source_file": source_file, "winner": None, "runner_up": None}

    print(f"Loading transcript from {session_path.name}...", file=sys.stderr)
    records = _load_transcript(session_path)
    print(f"  Loaded {len(records)} records.", file=sys.stderr)

    print("Building user message index...", file=sys.stderr)
    user_index_map = _build_user_index(records)
    print(f"  Indexed {len(user_index_map)} user messages.", file=sys.stderr)

    print(f"Reconstructing context for {len(flagged_entries)} flagged message(s)...", file=sys.stderr)
    candidates: list[dict] = []
    for entry in flagged_entries:
        candidate = _build_candidate(records, user_index_map, entry)
        if candidate is not None:
            candidates.append(candidate)
            print(f"  Index {entry.get('index')}: score={candidate['score']:.1f}", file=sys.stderr)

    print(f"Selecting from {len(candidates)} candidate(s)...", file=sys.stderr)
    winner, runner_up = select_candidates(candidates)

    result: dict = {"source_file": source_file, "winner": None, "runner_up": None}
    if winner:
        result["winner"] = _format_output(winner)
        print(f"Winner score: {winner['score']:.1f}", file=sys.stderr)
    if runner_up:
        result["runner_up"] = _format_output(runner_up)
        print(f"Runner-up score: {runner_up['score']:.1f}", file=sys.stderr)

    return result


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def main() -> None:
    """Read flagged messages and reconstruct context from the session transcript."""
    parser = argparse.ArgumentParser(
        description="Reconstruct context around flagged user reactions from a session transcript"
    )
    parser.add_argument(
        "--flagged-file", default=None, help="JSON file with flagged message data (default: read from stdin)"
    )
    parser.add_argument(
        "--session-file", default=None, help="Override session JSONL path (takes precedence over source_file in input)"
    )
    args = parser.parse_args()

    if args.flagged_file is not None:
        flagged_path = Path(args.flagged_file)
        if not flagged_path.exists():
            print(f"Error: flagged file not found: {flagged_path}", file=sys.stderr)
            sys.exit(1)
        with flagged_path.open(encoding="utf-8") as fh:
            input_data = json.load(fh)
    else:
        input_data = json.load(sys.stdin)

    if not isinstance(input_data, dict):
        print("Error: input must be a JSON object with 'source_file' and 'flagged' keys", file=sys.stderr)
        sys.exit(1)

    result = reconstruct(input_data, session_override=args.session_file)

    json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
    print()  # trailing newline


if __name__ == "__main__":
    main()
