#!/usr/bin/env -S uv --quiet run --active --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "duckdb>=1.0.0",
# ]
# ///
"""List recent Claude Code sessions for the current project.

Usage:
    list_sessions.py [--limit N] [--project SLUG] [--json]

Outputs a numbered list of recent sessions. With --json, outputs machine-readable
JSON with session_id, file_path, project_name, last_ts, user_msg_count fields.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.parse
from datetime import UTC, datetime
from pathlib import Path

import duckdb

PROJECTS_DIR = Path("~/.claude/projects").expanduser()
CACHE_DIR = Path("~/.claude/kaizen").expanduser()
DB_PATH = CACHE_DIR / "session-index.duckdb"
_SNIPPET_LEN = 60

_DDL = """
CREATE TABLE IF NOT EXISTS sessions (
    session_id       TEXT NOT NULL,
    file_path        TEXT NOT NULL,
    project_slug     TEXT,
    project_name     TEXT,
    first_ts         TEXT,
    last_ts          TEXT,
    total_records    INTEGER,
    user_msg_count   INTEGER,
    assistant_turns  INTEGER,
    file_size_kb     DOUBLE,
    has_summary      BOOLEAN DEFAULT FALSE,
    indexed_at       TEXT,
    PRIMARY KEY (session_id, file_path)
);
CREATE TABLE IF NOT EXISTS user_messages (
    session_id   TEXT NOT NULL,
    file_path    TEXT NOT NULL,
    msg_index    INTEGER NOT NULL,
    timestamp    TEXT,
    content      TEXT,
    word_count   INTEGER,
    PRIMARY KEY (session_id, msg_index)
);
"""

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
    return "\n".join(parts)


def _is_noise(text: str) -> bool:
    stripped = text.lstrip()
    return any(stripped.startswith(p) for p in _NOISE_PREFIXES)


def _open_db() -> duckdb.DuckDBPyConnection:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(DB_PATH))
    con.execute(_DDL)
    return con


def _parse_records(records: list[dict]) -> tuple[list[str], list[dict[str, str]], int]:
    """Extract timestamps, user messages, and assistant turn count from records.

    Returns:
        Tuple of (timestamps, user_msgs, assistant_turns).
    """
    timestamps: list[str] = []
    user_msgs: list[dict[str, str]] = []
    assistant_turns = 0
    for rec in records:
        ts = rec.get("timestamp", "")
        if ts:
            timestamps.append(ts)
        msg_type = rec.get("type", "")
        if msg_type == "user" and "toolUseResult" not in rec:
            content = _extract_text(rec.get("message", {}).get("content"))
            if content and not _is_noise(content):
                user_msgs.append({"ts": ts, "content": content})
        elif msg_type == "assistant":
            assistant_turns += 1
    return timestamps, user_msgs, assistant_turns


def _index_file(con: duckdb.DuckDBPyConnection, path: Path) -> None:
    records = []
    try:
        with path.open(encoding="utf-8", errors="replace") as fh:
            for line in fh:
                raw = line.strip()
                if not raw:
                    continue
                try:
                    rec = json.loads(raw)
                    if isinstance(rec, dict):
                        records.append(rec)
                except json.JSONDecodeError:
                    continue
    except OSError:
        return

    slug = path.parent.name
    timestamps, user_msgs, assistant_turns = _parse_records(records)

    sid = path.stem
    first_ts = min(timestamps) if timestamps else ""
    last_ts = max(timestamps) if timestamps else ""
    now = datetime.now(UTC).isoformat()
    has_summary = (CACHE_DIR / "session-summaries" / f"{sid}.md").exists()

    try:
        file_size_kb = path.stat().st_size / 1024
    except OSError:
        return
    con.execute(
        """
        INSERT INTO sessions VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT (session_id, file_path) DO UPDATE SET
            last_ts = excluded.last_ts,
            total_records = excluded.total_records,
            user_msg_count = excluded.user_msg_count,
            assistant_turns = excluded.assistant_turns,
            indexed_at = excluded.indexed_at
        """,
        [
            sid,
            str(path),
            slug,
            slug,
            first_ts,
            last_ts,
            len(records),
            len(user_msgs),
            assistant_turns,
            file_size_kb,
            has_summary,
            now,
        ],
    )

    for i, msg in enumerate(user_msgs):
        con.execute(
            """
            INSERT INTO user_messages VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT (session_id, msg_index) DO NOTHING
            """,
            [sid, str(path), i, msg["ts"], msg["content"], len(msg["content"].split())],
        )


def _current_project_slug() -> str | None:
    """Derive the project slug for the current working directory.

    Returns:
        The project slug string if found, or None if no matching project directory exists.
    """
    cwd = Path.cwd()
    # Try URL-encoded form (Claude Code web / newer versions)
    url_encoded = urllib.parse.quote(str(cwd), safe="")
    url_path = PROJECTS_DIR / url_encoded
    if url_path.exists():
        return url_encoded
    # Try hyphen-joined path form (older versions)
    parts = Path(cwd).parts
    hyphen_slug = "-".join(p.lstrip("/") for p in parts if p and p != "/")
    hyphen_path = PROJECTS_DIR / hyphen_slug
    if hyphen_path.exists():
        return hyphen_slug
    # Try partial match on last path components
    if PROJECTS_DIR.exists():
        basename = Path(cwd).name
        for d in PROJECTS_DIR.iterdir():
            if d.is_dir() and d.name.endswith(basename):
                return d.name
    return None


def main() -> None:
    """List recent Claude Code sessions, optionally filtered by project."""
    parser = argparse.ArgumentParser(description="List recent Claude Code sessions")
    parser.add_argument("--limit", "-n", type=int, default=20, help="Max sessions to show")
    parser.add_argument("--project", "-p", default="", help="Filter by project slug substring")
    parser.add_argument("--json", action="store_true", help="Output JSON array")
    parser.add_argument("--all-projects", action="store_true", help="List from all projects, not just current")
    args = parser.parse_args()

    con = _open_db()

    # Ensure index has data
    count_row = con.execute("SELECT COUNT(*) FROM sessions").fetchone()
    if count_row and count_row[0] == 0:
        print("Building session index...", file=sys.stderr)
        if PROJECTS_DIR.exists():
            for f in sorted(PROJECTS_DIR.glob("*/*.jsonl"), key=lambda x: x.stat().st_mtime, reverse=True):
                _index_file(con, f)

    # Determine project filter
    project_filter = args.project
    if not project_filter and not args.all_projects:
        slug = _current_project_slug()
        if slug:
            project_filter = slug

    BASE_QUERY = (
        "SELECT s.session_id, s.file_path, s.project_slug, s.last_ts, s.user_msg_count,"
        "       s.assistant_turns,"
        "       (SELECT u.content FROM user_messages u"
        "        WHERE u.session_id = s.session_id"
        "        ORDER BY u.msg_index LIMIT 1) AS first_msg"
        " FROM sessions s"
    )
    if project_filter:
        query = BASE_QUERY + " WHERE project_slug LIKE ? ORDER BY s.last_ts DESC LIMIT ?"
        params: list[str | int] = [f"%{project_filter}%", args.limit]
    else:
        query = BASE_QUERY + " ORDER BY s.last_ts DESC LIMIT ?"
        params = [args.limit]
    rows = con.execute(query, params).fetchall()

    if args.json:
        result = [
            {
                "index": i + 1,
                "session_id": sid,
                "file_path": fp,
                "project_slug": slug,
                "last_ts": last_ts,
                "user_msg_count": umsg,
                "assistant_turns": aturns,
            }
            for i, (sid, fp, slug, last_ts, umsg, aturns, _first_msg) in enumerate(rows)
        ]
        print(json.dumps(result, indent=2))
        return

    if not rows:
        print("No sessions found. Check ~/.claude/projects/ exists.", file=sys.stderr)
        sys.exit(1)

    print(f"\nRecent sessions{' (project: ' + project_filter + ')' if project_filter else ''}:\n")
    for i, (sid, _fp, _slug, last_ts, umsg, _aturns, first_msg) in enumerate(rows, 1):
        date_str = (last_ts[:16].replace("T", " ")) if last_ts else "?"
        snippet = ""
        if first_msg:
            snippet = first_msg[:_SNIPPET_LEN].replace("\n", " ")
            if len(first_msg) > _SNIPPET_LEN:
                snippet += "..."
        print(f"  [{i:2d}] {sid[:8]}...  {date_str}  ({umsg} msgs)  {snippet}")

    print(f"\nTotal: {len(rows)} session(s)\n")
    print("Pass session_id to extract_batches.py to begin analysis.")


if __name__ == "__main__":
    main()
