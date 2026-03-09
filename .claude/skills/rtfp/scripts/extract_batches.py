#!/usr/bin/env -S uv --quiet run --active --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Extract and batch messages from a Claude Code session JSONL file.

Reads all messages (user + assistant) from the given JSONL file,
preserving original message indexes. Splits into batch files of
approximately TARGET_CHARS characters each (default ~400k chars ≈ 100k tokens).

Each batch file is a JSON object:
{
  "source_file": "/path/to/session.jsonl",
  "session_id": "uuid",
  "batch_index": 0,
  "total_batches": N,
  "messages": [
    {
      "index": 0,
      "type": "user" | "assistant",
      "timestamp": "...",
      "content": "...",
      "char_count": N
    },
    ...
  ]
}

Usage:
    extract_batches.py <session_jsonl_path> [--out-dir /tmp/rtfp-batches] [--batch-chars 400000]
    extract_batches.py <session_jsonl_path> --list-only
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

_NOISE_PREFIXES = (
    "<local-command-caveat>",
    "<bash-stdout>",
    "<tool_use_error>",
    "<task-notification>",
    "<command-message>",
    "<system-reminder>",
)


def _extract_text(content: str | list | None) -> str:
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    parts = []
    for element in content:
        if isinstance(element, dict) and element.get("type") == "text":
            text = element.get("text")
            if isinstance(text, str):
                parts.append(text)
        elif isinstance(element, dict) and element.get("type") == "tool_result":
            # Include tool result content for context
            inner = element.get("content", "")
            inner_text = _extract_text(inner)
            if inner_text:
                parts.append(f"[tool_result: {inner_text}]")
    return "\n".join(parts)


def _is_noise(text: str) -> bool:
    stripped = text.lstrip()
    return any(stripped.startswith(p) for p in _NOISE_PREFIXES)


def _extract_assistant_text(message: dict) -> str:
    """Extract readable text from an assistant message, including tool use summaries.

    Returns:
        Concatenated text content from the message, with tool use summarized inline.
    """
    content = message.get("content")
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    parts = []
    for element in content:
        if isinstance(element, dict):
            if element.get("type") == "text":
                text = element.get("text", "")
                if text:
                    parts.append(text)
            elif element.get("type") == "tool_use":
                name = element.get("name", "tool")
                inp = element.get("input", {})
                inp_str = json.dumps(inp)[:200] if inp else ""
                parts.append(f"[{name}({inp_str})]")
    return "\n".join(parts)


def load_messages(session_path: Path) -> list[dict]:
    """Load and parse all messages from a JSONL session file.

    Returns:
        List of message dicts with keys: index, type, timestamp, content, char_count.
    """
    messages = []
    msg_index = 0

    with session_path.open(encoding="utf-8", errors="replace") as fh:
        for line in fh:
            raw = line.strip()
            if not raw:
                continue
            try:
                rec = json.loads(raw)
            except json.JSONDecodeError:
                continue
            if not isinstance(rec, dict):
                continue

            msg_type = rec.get("type", "")
            if msg_type not in {"user", "assistant"}:
                continue

            # Skip tool result lines (they're infrastructure, not conversation)
            if "toolUseResult" in rec:
                continue

            ts = rec.get("timestamp", "")

            if msg_type == "user":
                content = _extract_text(rec.get("message", {}).get("content"))
                if not content or _is_noise(content):
                    continue
            else:
                content = _extract_assistant_text(rec.get("message", {}))
                if not content:
                    continue

            messages.append({
                "index": msg_index,
                "type": msg_type,
                "timestamp": ts,
                "content": content,
                "char_count": len(content),
            })
            msg_index += 1

    return messages


def split_into_batches(messages: list[dict], target_chars: int) -> list[list[dict]]:
    """Split messages into batches not exceeding target_chars total.

    Returns:
        List of message batches, each batch being a list of message dicts.
    """
    batches: list[list[dict]] = []
    current_batch: list[dict] = []
    current_chars = 0

    for msg in messages:
        chars = msg["char_count"]
        # Start new batch if we'd exceed target and current batch is non-empty
        if current_chars + chars > target_chars and current_batch:
            batches.append(current_batch)
            current_batch = []
            current_chars = 0
        current_batch.append(msg)
        current_chars += chars

    if current_batch:
        batches.append(current_batch)

    return batches


def write_batch_files(session_path: Path, session_id: str, batches: list[list[dict]], out_dir: Path) -> list[Path]:
    """Write batch JSON files and return their paths.

    Returns:
        List of Path objects for each written batch file.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    written = []
    total = len(batches)

    for i, batch in enumerate(batches):
        payload = {
            "source_file": str(session_path),
            "session_id": session_id,
            "batch_index": i,
            "total_batches": total,
            "message_count": len(batch),
            "total_chars": sum(m["char_count"] for m in batch),
            "messages": batch,
        }
        out_path = out_dir / f"batch_{i:03d}.json"
        with out_path.open("w", encoding="utf-8") as fh:
            json.dump(payload, fh, ensure_ascii=False, indent=2)
        written.append(out_path)
        print(f"  Batch {i}: {len(batch)} messages, {payload['total_chars']:,} chars → {out_path}", file=sys.stderr)

    return written


_DEFAULT_OUT_DIR = str(Path(tempfile.gettempdir()) / "rtfp-batches")


def main() -> None:
    """Extract and batch messages from a Claude Code session JSONL file."""
    parser = argparse.ArgumentParser(description="Extract and batch Claude Code session messages")
    parser.add_argument("session_path", help="Path to session .jsonl file")
    parser.add_argument("--out-dir", default=_DEFAULT_OUT_DIR, help="Output directory for batch files")
    parser.add_argument(
        "--batch-chars",
        type=int,
        default=400_000,
        help="Target chars per batch (~100k tokens at 4 chars/token). Default: 400000",
    )
    parser.add_argument(
        "--list-only", action="store_true", help="Print message count and estimated batches without writing files"
    )
    args = parser.parse_args()

    session_path = Path(args.session_path)
    if not session_path.exists():
        print(f"Error: file not found: {session_path}", file=sys.stderr)
        sys.exit(1)

    print(f"Loading messages from {session_path.name}...", file=sys.stderr)
    messages = load_messages(session_path)

    if not messages:
        print("No messages found in session file.", file=sys.stderr)
        sys.exit(1)

    total_chars = 0
    user_count = 0
    asst_count = 0
    for m in messages:
        total_chars += m["char_count"]
        if m["type"] == "user":
            user_count += 1
        else:
            asst_count += 1
    estimated_batches = max(1, (total_chars + args.batch_chars - 1) // args.batch_chars)

    print(f"Messages: {len(messages)} total ({user_count} user, {asst_count} assistant)", file=sys.stderr)
    print(f"Total chars: {total_chars:,} (~{total_chars // 4:,} tokens)", file=sys.stderr)
    print(f"Estimated batches at {args.batch_chars:,} chars each: {estimated_batches}", file=sys.stderr)

    if args.list_only:
        result = {
            "session_path": str(session_path),
            "session_id": session_path.stem,
            "message_count": len(messages),
            "user_messages": user_count,
            "assistant_messages": asst_count,
            "total_chars": total_chars,
            "estimated_batches": estimated_batches,
        }
        print(json.dumps(result, indent=2))
        return

    batches = split_into_batches(messages, args.batch_chars)
    out_dir = Path(args.out_dir)

    print(f"\nWriting {len(batches)} batch file(s) to {out_dir}...", file=sys.stderr)
    written = write_batch_files(session_path, session_path.stem, batches, out_dir)

    result = {
        "session_id": session_path.stem,
        "source_file": str(session_path),
        "out_dir": str(out_dir),
        "batch_files": [str(p) for p in written],
        "batch_count": len(written),
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
