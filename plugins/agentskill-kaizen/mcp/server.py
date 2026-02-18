#!/usr/bin/env -S uv run --quiet --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "fastmcp>=2.0.0",
#     "pm4py>=2.7.0",
#     "pandas>=2.0.0",
#     "prefixspan>=0.5.2",
#     "scikit-learn>=1.0",
# ]
# ///
"""Kaizen Analysis MCP Server.

Exposes process mining, pattern mining, frustration detection,
and session clustering as MCP tools for the transcript-analyst agent.

Tools:
    extract_tool_sequences - Parse JSONL transcripts into tool-call sequences
    discover_process_model - Heuristic Miner process discovery via PM4Py
    check_conformance - Token-based replay conformance checking
    find_frequent_patterns - PrefixSpan sequential pattern mining
    detect_frustration_signals - Regex-based frustration signal extraction
    cluster_sessions - KMeans clustering on tool-call sequence profiles
"""

from __future__ import annotations

import json
import operator
import pathlib
import re
from collections import Counter
from typing import Any

import pandas as pd
import pm4py
from fastmcp import FastMCP
from prefixspan import PrefixSpan
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import CountVectorizer

mcp = FastMCP("kaizen-analysis")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _read_jsonl(file_path: str) -> list[dict[str, Any]]:
    """Read a JSONL file and return a list of parsed records.

    Args:
        file_path: Path to a single JSONL file.

    Returns:
        List of dicts, one per line.
    """
    records: list[dict[str, Any]] = []
    with pathlib.Path(file_path).open(encoding="utf-8") as fh:
        for line in fh:
            stripped = line.strip()
            if stripped:
                records.append(json.loads(stripped))
    return records


def _extract_tools_from_records(records: list[dict[str, Any]]) -> list[str]:
    """Extract ordered tool names from assistant message content blocks.

    Args:
        records: Parsed JSONL records from a single session file.

    Returns:
        Ordered list of tool names invoked in the session.
    """
    tools: list[str] = []
    for record in records:
        if record.get("type") != "assistant":
            continue
        message = record.get("message")
        if not isinstance(message, dict):
            continue
        content = message.get("content")
        if not isinstance(content, list):
            continue
        for block in content:
            if isinstance(block, dict) and block.get("type") == "tool_use":
                name = block.get("name")
                if isinstance(name, str):
                    tools.append(name)
    return tools


def _resolve_glob(glob_path: str) -> list[str]:
    """Resolve a glob pattern to a sorted list of file paths.

    Splits the glob pattern into a non-glob base directory and a
    relative pattern, then uses ``pathlib.Path.glob`` for resolution.

    Args:
        glob_path: Glob pattern (e.g. ``/home/user/sessions/**/*.jsonl``).

    Returns:
        Sorted list of matching absolute file path strings.
    """
    parts = pathlib.PurePosixPath(glob_path).parts
    base_parts: list[str] = []
    glob_chars = {"*", "?", "["}
    for part in parts:
        if any(c in part for c in glob_chars):
            break
        base_parts.append(part)

    if base_parts:
        base = pathlib.Path(*base_parts)
        relative = str(pathlib.PurePosixPath(*parts[len(base_parts) :]))
    else:
        base = pathlib.Path()
        relative = glob_path

    return sorted(str(p) for p in base.glob(relative))


def _build_event_log(sequences: dict[str, list[str]]) -> pd.DataFrame:
    """Convert tool sequences into a PM4Py-compatible event log DataFrame.

    Each tool call becomes an event with a synthetic timestamp so that
    the ordering within a session is preserved.

    Args:
        sequences: Mapping of session_id to ordered tool names.

    Returns:
        A pandas DataFrame formatted for PM4Py.
    """
    rows: list[dict[str, Any]] = []
    for session_id, tools in sequences.items():
        for idx, tool_name in enumerate(tools):
            rows.append({
                "case:concept:name": session_id,
                "concept:name": tool_name,
                "time:timestamp": pd.Timestamp("2026-01-01")
                + pd.Timedelta(seconds=idx),
            })
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    return pm4py.format_dataframe(
        df,
        case_id="case:concept:name",
        activity_key="concept:name",
        timestamp_key="time:timestamp",
    )


# ---------------------------------------------------------------------------
# MCP Tools
# ---------------------------------------------------------------------------


def _extract_tool_sequences_impl(glob_path: str) -> dict[str, list[str]]:
    """Core implementation for extracting tool sequences from JSONL files.

    Args:
        glob_path: Glob pattern pointing to JSONL files.

    Returns:
        Dict mapping session filename (stem) to list of tool names.
    """
    files = _resolve_glob(glob_path)
    result: dict[str, list[str]] = {}
    for file_path in files:
        session_id = file_path.rsplit("/", maxsplit=1)[-1].removesuffix(".jsonl")
        records = _read_jsonl(file_path)
        tools = _extract_tools_from_records(records)
        if tools:
            result[session_id] = tools
    return result


@mcp.tool()
def extract_tool_sequences(glob_path: str) -> dict[str, list[str]]:
    """Extract ordered tool-call sequences from JSONL transcript files.

    Reads each JSONL file matching the glob pattern, extracts tool_use
    blocks from assistant messages, and returns the ordered tool names
    per session.

    Args:
        glob_path: Glob pattern pointing to JSONL files
            (e.g. ``/home/user/.claude/projects/**/sessions/*.jsonl``).

    Returns:
        Dict mapping session filename (stem) to list of tool names.
    """
    return _extract_tool_sequences_impl(glob_path)


@mcp.tool()
def discover_process_model(
    glob_path: str = "", sequences: dict[str, list[str]] | None = None
) -> str:
    """Discover a process model from tool-call sequences using PM4Py Heuristic Miner.

    Provide either a glob path to JSONL files or pre-extracted sequences.
    Returns a string representation of the discovered heuristic net.

    Args:
        glob_path: Glob pattern for JSONL files (used if sequences is None).
        sequences: Pre-extracted tool sequences from extract_tool_sequences.

    Returns:
        String representation of the discovered heuristic net showing
        nodes and their connection strengths.
    """
    if sequences is None:
        if not glob_path:
            return "Error: provide either glob_path or sequences"
        sequences = _extract_tool_sequences_impl(glob_path)
    if not sequences:
        return "Error: no tool sequences found"

    event_log = _build_event_log(sequences)
    if event_log.empty:
        return "Error: empty event log"

    heu_net = pm4py.discover_heuristics_net(event_log)
    return repr(heu_net)


@mcp.tool()
def check_conformance(
    glob_path: str = "",
    sequences: dict[str, list[str]] | None = None,
    reference_glob_path: str = "",
    reference_sequences: dict[str, list[str]] | None = None,
) -> list[dict[str, Any]]:
    """Check conformance of sessions against a reference process model.

    Discovers a Petri net from the reference sequences via Heuristic
    Miner, then runs token-based replay on the target sessions.

    Args:
        glob_path: Glob pattern for target JSONL files to check.
        sequences: Pre-extracted target tool sequences.
        reference_glob_path: Glob pattern for reference JSONL files.
        reference_sequences: Pre-extracted reference tool sequences.

    Returns:
        List of per-trace conformance dicts with keys including
        ``trace_is_fit``, ``trace_fitness``, ``missing_tokens``,
        ``remaining_tokens``, and the ``session_id``.
    """
    if sequences is None:
        if not glob_path:
            return [{"error": "provide either glob_path or sequences for target"}]
        sequences = _extract_tool_sequences_impl(glob_path)

    if reference_sequences is None:
        if not reference_glob_path:
            return [
                {"error": "provide either reference_glob_path or reference_sequences"}
            ]
        reference_sequences = _extract_tool_sequences_impl(reference_glob_path)

    if not reference_sequences:
        return [{"error": "no reference sequences found"}]
    if not sequences:
        return [{"error": "no target sequences found"}]

    # Build reference model
    ref_log = _build_event_log(reference_sequences)
    heu_net = pm4py.discover_heuristics_net(ref_log)
    net, initial_marking, final_marking = pm4py.convert_to_petri_net(heu_net)

    # Build target event log
    target_log = _build_event_log(sequences)
    replay_results = pm4py.conformance_diagnostics_token_based_replay(
        target_log, net, initial_marking, final_marking
    )

    # Attach session IDs to results
    session_ids = list(sequences.keys())
    output: list[dict[str, Any]] = []
    for idx, diag in enumerate(replay_results):
        entry: dict[str, Any] = {
            "session_id": session_ids[idx]
            if idx < len(session_ids)
            else f"trace_{idx}",
            "trace_is_fit": diag.get("trace_is_fit", False),
            "trace_fitness": diag.get("trace_fitness", 0.0),
            "missing_tokens": diag.get("missing_tokens", 0),
            "remaining_tokens": diag.get("remaining_tokens", 0),
            "consumed_tokens": diag.get("consumed_tokens", 0),
            "produced_tokens": diag.get("produced_tokens", 0),
        }
        output.append(entry)
    return output


@mcp.tool()
def find_frequent_patterns(
    glob_path: str = "",
    sequences: dict[str, list[str]] | None = None,
    min_support: int = 2,
) -> list[dict[str, Any]]:
    """Find frequent sequential patterns in tool-call sequences using PrefixSpan.

    Args:
        glob_path: Glob pattern for JSONL files (used if sequences is None).
        sequences: Pre-extracted tool sequences from extract_tool_sequences.
        min_support: Minimum number of sessions a pattern must appear in.

    Returns:
        List of dicts with ``pattern`` (list of tool names) and
        ``support`` (count of sessions containing the pattern),
        sorted by support descending.
    """
    if sequences is None:
        if not glob_path:
            return [{"error": "provide either glob_path or sequences"}]
        sequences = _extract_tool_sequences_impl(glob_path)
    if not sequences:
        return [{"error": "no tool sequences found"}]

    db = list(sequences.values())
    ps = PrefixSpan(db)
    ps.minlen = 2
    frequent = ps.frequent(min_support)

    results: list[dict[str, Any]] = [
        {"support": count, "pattern": pattern} for count, pattern in frequent
    ]
    results.sort(key=operator.itemgetter("support"), reverse=True)
    return results


# Frustration signal patterns
_FRUSTRATION_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    (
        "correction",
        re.compile(
            r"\b(?:no[,.]?\s|don'?t|wrong|incorrect|stop|undo|revert)\b", re.IGNORECASE
        ),
    ),
    (
        "denial",
        re.compile(
            r"\b(?:that'?s not|i didn'?t|never|absolutely not)\b", re.IGNORECASE
        ),
    ),
    (
        "interrupt",
        re.compile(
            r"\b(?:wait|hold on|cancel|abort|forget it|nevermind)\b", re.IGNORECASE
        ),
    ),
    (
        "frustration",
        re.compile(
            r"\b(?:why did you|you keep|again\?|still wrong|broken)\b", re.IGNORECASE
        ),
    ),
]


@mcp.tool()
def detect_frustration_signals(glob_path: str) -> list[dict[str, str]]:
    """Detect user frustration signals in JSONL transcripts.

    Scans user-type messages for patterns indicating corrections,
    denials, interrupts, and expressions of frustration. Filters
    out system-generated messages (tool results).

    Args:
        glob_path: Glob pattern for JSONL files to scan.

    Returns:
        List of dicts with ``session_id``, ``timestamp``,
        ``signal_type``, and ``message_text``.
    """
    files = _resolve_glob(glob_path)
    signals: list[dict[str, str]] = []

    for file_path in files:
        session_id = file_path.rsplit("/", maxsplit=1)[-1].removesuffix(".jsonl")
        records = _read_jsonl(file_path)

        for record in records:
            if record.get("type") != "user":
                continue
            # Skip tool results (system-generated)
            if record.get("toolUseResult"):
                continue

            message = record.get("message")
            if not isinstance(message, dict):
                continue

            # Extract text from message content
            text = _extract_user_text(message)
            if not text:
                continue

            timestamp = record.get("timestamp", "")

            for signal_type, pattern in _FRUSTRATION_PATTERNS:
                if pattern.search(text):
                    signals.append({
                        "session_id": session_id,
                        "timestamp": str(timestamp),
                        "signal_type": signal_type,
                        "message_text": text[:200],
                    })
                    break  # One signal per message

    return signals


def _extract_user_text(message: dict[str, Any]) -> str:
    """Extract plain text from a user message content field.

    Handles both string content and list-of-blocks content formats.

    Args:
        message: The ``message`` dict from a ``user`` record.

    Returns:
        Extracted text, or empty string if no text found.
    """
    content = message.get("content")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if isinstance(block, dict):
                if block.get("type") == "text":
                    text = block.get("text", "")
                    if isinstance(text, str):
                        parts.append(text)
            elif isinstance(block, str):
                parts.append(block)
        return " ".join(parts)
    return ""


@mcp.tool()
def cluster_sessions(
    glob_path: str = "",
    sequences: dict[str, list[str]] | None = None,
    n_clusters: int = 3,
) -> dict[str, Any]:
    """Group sessions by behavioral similarity using tool-call sequence profiles.

    Encodes each session's tool sequence as a bag-of-tools vector,
    then applies KMeans clustering.

    Args:
        glob_path: Glob pattern for JSONL files (used if sequences is None).
        sequences: Pre-extracted tool sequences from extract_tool_sequences.
        n_clusters: Number of clusters to create.

    Returns:
        Dict with ``clusters`` mapping cluster_id to list of session_ids,
        and ``cluster_profiles`` mapping cluster_id to the most common
        tools in that cluster.
    """
    if sequences is None:
        if not glob_path:
            return {"error": "provide either glob_path or sequences"}
        sequences = _extract_tool_sequences_impl(glob_path)
    if not sequences:
        return {"error": "no tool sequences found"}

    session_ids = list(sequences.keys())
    # Encode each session as a space-joined string for CountVectorizer
    docs = [" ".join(tools) for tools in sequences.values()]

    n_clusters = min(n_clusters, len(docs))
    if n_clusters < 1:
        return {"error": "need at least 1 session to cluster"}

    vectorizer = CountVectorizer()
    feature_matrix = vectorizer.fit_transform(docs)
    _ = vectorizer.get_feature_names_out()  # validates vocabulary was built

    km = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    labels = km.fit_predict(feature_matrix)

    clusters: dict[str, list[str]] = {}
    cluster_profiles: dict[str, list[str]] = {}

    for cluster_id in range(n_clusters):
        cid = str(cluster_id)
        member_indices = [i for i, lbl in enumerate(labels) if lbl == cluster_id]
        clusters[cid] = [session_ids[i] for i in member_indices]

        # Build profile: most common tools across cluster members
        tool_counts: Counter[str] = Counter()
        for i in member_indices:
            tool_counts.update(sequences[session_ids[i]])
        top_tools = 5
        cluster_profiles[cid] = [t for t, _ in tool_counts.most_common(top_tools)]

    return {"clusters": clusters, "cluster_profiles": cluster_profiles}


if __name__ == "__main__":
    mcp.run()
