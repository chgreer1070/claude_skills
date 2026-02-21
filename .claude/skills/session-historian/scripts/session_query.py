#!/usr/bin/env -S uv run --quiet --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "duckdb>=1.0.0",
#     "typer>=0.21.0",
#     "rich>=13.0.0",
# ]
# ///
"""Session Historian — query and summarize Claude Code JSONL session transcripts.

Commands:
    list       — list recent sessions with metadata
    messages   — print verbatim user messages for a session
    search     — search raw JSONL files for text
    index      — build/rebuild the DuckDB session index
    show       — show session summary from cache (or generate structure)
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated

import duckdb
import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer(
    name="session-historian",
    help="Query Claude Code JSONL session history with DuckDB indexing.",
    rich_markup_mode="rich",
    no_args_is_help=True,
)

stderr = Console(stderr=True)
stdout = Console()

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

PROJECTS_DIR = Path("~/.claude/projects").expanduser()
CACHE_DIR = Path("~/.claude/kaizen").expanduser()
DB_PATH = CACHE_DIR / "session-index.duckdb"
SUMMARIES_DIR = CACHE_DIR / "session-summaries"

# ---------------------------------------------------------------------------
# JSONL parsing
# ---------------------------------------------------------------------------

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
    parts: list[str] = []
    for element in content:
        if isinstance(element, dict) and element.get("type") == "text":
            text = element.get("text")
            if isinstance(text, str):
                parts.append(text)
    return "\n".join(parts)


def _is_noise(text: str) -> bool:
    stripped = text.lstrip()
    return any(stripped.startswith(p) for p in _NOISE_PREFIXES)


def _iter_records(path: Path) -> list[dict]:
    """Parse a JSONL file, return all records as dicts."""
    records: list[dict] = []
    with path.open(encoding="utf-8", errors="replace") as fh:
        for raw_line in fh:
            stripped = raw_line.strip()
            if not stripped:
                continue
            try:
                rec = json.loads(stripped)
                if isinstance(rec, dict):
                    records.append(rec)
            except json.JSONDecodeError:
                continue
    return records


def _slug_to_project_name(slug: str) -> str:
    parts = [p for p in slug.split("-") if p]
    location_tokens = {
        "repos",
        "Desktop",
        "Documents",
        "Projects",
        "src",
        "code",
        "work",
    }
    idx = 0
    if idx < len(parts) and parts[idx] == "home":
        idx += 1
    if idx < len(parts):
        idx += 1  # username
    if idx < len(parts) and parts[idx] in location_tokens:
        idx += 1
    return "-".join(parts[idx:]) if idx < len(parts) else slug


# ---------------------------------------------------------------------------
# DuckDB index
# ---------------------------------------------------------------------------

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


def _open_db() -> duckdb.DuckDBPyConnection:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(DB_PATH))
    con.execute(_DDL)
    return con


def _fetch_count(
    con: duckdb.DuckDBPyConnection, sql: str, params: list | None = None
) -> int:
    """Execute a COUNT query and return the integer result."""
    row = con.execute(sql, params or []).fetchone()
    return int(row[0]) if row else 0


@dataclass
class _FileStats:
    primary_sid: str
    slug: str
    project_name: str
    first_ts: str
    last_ts: str
    total_records: int
    user_msgs: list[dict]
    assistant_turns: int
    file_kb: float
    now: str


def _scan_records(path: Path, records: list[dict]) -> _FileStats:
    """Extract statistics from parsed JSONL records."""
    slug = path.parent.name
    session_ids: set[str] = set()
    timestamps: list[str] = []
    user_msgs: list[dict] = []
    assistant_turns = 0

    for rec in records:
        sid = rec.get("sessionId", "unknown")
        session_ids.add(sid)
        ts = rec.get("timestamp", "")
        if ts:
            timestamps.append(ts)
        msg_type = rec.get("type", "")
        if msg_type == "user" and "toolUseResult" not in rec:
            content = _extract_text(rec.get("message", {}).get("content"))
            if content and not _is_noise(content):
                user_msgs.append({"sid": sid, "ts": ts, "content": content})
        elif msg_type == "assistant":
            assistant_turns += 1

    return _FileStats(
        primary_sid=next(iter(session_ids), path.stem),
        slug=slug,
        project_name=_slug_to_project_name(slug),
        first_ts=min(timestamps) if timestamps else "",
        last_ts=max(timestamps) if timestamps else "",
        total_records=len(records),
        user_msgs=user_msgs,
        assistant_turns=assistant_turns,
        file_kb=path.stat().st_size / 1024,
        now=datetime.now(UTC).isoformat(),
    )


def _index_file(con: duckdb.DuckDBPyConnection, path: Path) -> tuple[int, int]:
    """Index one JSONL file. Returns (user_msgs_indexed, assistant_turns)."""
    stats = _scan_records(path, _iter_records(path))
    sid = stats.primary_sid

    con.execute(
        """
        INSERT INTO sessions VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, FALSE, ?)
        ON CONFLICT (session_id, file_path) DO UPDATE SET
            first_ts = excluded.first_ts,
            last_ts = excluded.last_ts,
            total_records = excluded.total_records,
            user_msg_count = excluded.user_msg_count,
            assistant_turns = excluded.assistant_turns,
            file_size_kb = excluded.file_size_kb,
            indexed_at = excluded.indexed_at
    """,
        [
            sid,
            str(path),
            stats.slug,
            stats.project_name,
            stats.first_ts,
            stats.last_ts,
            stats.total_records,
            len(stats.user_msgs),
            stats.assistant_turns,
            stats.file_kb,
            stats.now,
        ],
    )

    for i, msg in enumerate(stats.user_msgs):
        words = len(msg["content"].split())
        con.execute(
            """
            INSERT INTO user_messages VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT (session_id, msg_index) DO UPDATE SET
                content = excluded.content,
                word_count = excluded.word_count
        """,
            [sid, str(path), i, msg["ts"], msg["content"], words],
        )

    return len(stats.user_msgs), stats.assistant_turns


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------


@app.command("index")
def cmd_index(
    rebuild: Annotated[
        bool, typer.Option("--rebuild", help="Drop and rebuild from scratch.")
    ] = False,
    project: Annotated[
        str, typer.Option("--project", "-p", help="Filter by project name substring.")
    ] = "",
) -> None:
    """Build or update the DuckDB session index from ~/.claude/projects/."""
    con = _open_db()

    if rebuild:
        con.execute("DELETE FROM user_messages")
        con.execute("DELETE FROM sessions")
        stderr.print("[yellow]Index cleared — rebuilding...[/yellow]")

    files = sorted(
        PROJECTS_DIR.glob("*/*.jsonl"), key=lambda f: f.stat().st_mtime, reverse=True
    )
    if project:
        files = [f for f in files if project.lower() in f.parent.name.lower()]

    stderr.print(f"[dim]Indexing {len(files)} JSONL file(s)...[/dim]")
    total_user = total_asst = 0
    for f in files:
        u, a = _index_file(con, f)
        total_user += u
        total_asst += a
        stderr.print(f"  [dim]{f.name}[/dim]  {u} user msgs, {a} assistant turns")

    count = _fetch_count(con, "SELECT COUNT(*) FROM sessions")
    stdout.print(
        f"\n[bold green]Index updated:[/bold green] {count} sessions, "
        f"{total_user} user messages, {total_asst} assistant turns"
    )
    stdout.print(f"[dim]DB: {DB_PATH}[/dim]")


def _ensure_indexed(con: duckdb.DuckDBPyConnection) -> None:
    """Build index from scratch if it is empty."""
    if _fetch_count(con, "SELECT COUNT(*) FROM sessions") == 0:
        stderr.print("[yellow]Index is empty — building now...[/yellow]")
        for f in sorted(
            PROJECTS_DIR.glob("*/*.jsonl"),
            key=lambda f: f.stat().st_mtime,
            reverse=True,
        ):
            _index_file(con, f)


@app.command("list")
def cmd_list(
    limit: Annotated[int, typer.Option("--limit", "-n")] = 20,
    project: Annotated[
        str, typer.Option("--project", "-p", help="Filter by project name substring.")
    ] = "",
    rebuild: Annotated[
        bool, typer.Option("--rebuild", help="Re-index before listing.")
    ] = False,
) -> None:
    """List recent sessions with metadata. Runs index if DB is empty."""
    con = _open_db()

    if rebuild:
        con.execute("DELETE FROM user_messages")
        con.execute("DELETE FROM sessions")

    _ensure_indexed(con)

    where = "WHERE project_name LIKE ?" if project else ""
    params: list = [f"%{project}%"] if project else []
    rows = con.execute(
        f"""
        SELECT session_id, project_name, last_ts, user_msg_count, assistant_turns,
               file_size_kb, has_summary, file_path
        FROM sessions
        {where}
        ORDER BY last_ts DESC
        LIMIT ?
    """,
        [*params, limit],
    ).fetchall()

    if not rows:
        stdout.print("[yellow]No sessions found. Run 'index' first.[/yellow]")
        return

    table = Table(title="Recent Sessions", show_lines=False)
    table.add_column("Session ID", style="cyan", width=12)
    table.add_column("Project", style="green")
    table.add_column("Last Active", style="dim")
    table.add_column("User Msgs", justify="right")
    table.add_column("Asst Turns", justify="right")
    table.add_column("KB", justify="right", style="dim")
    table.add_column("Summary", justify="center")

    for sid, proj, last_ts, umsg, aturns, kb, has_sum, _ in rows:
        date_str = last_ts[:16].replace("T", " ") if last_ts else "?"
        table.add_row(
            sid[:12],
            proj or "unknown",
            date_str,
            str(umsg or 0),
            str(aturns or 0),
            f"{kb:.0f}" if kb else "?",
            "✓" if has_sum else "·",
        )

    stdout.print(table)
    stdout.print(
        "\n[dim]Use 'messages <session-id>' for verbatim user messages, "
        "'search <text>' to search raw files.[/dim]"
    )


@app.command("messages")
def cmd_messages(
    session_id: Annotated[
        str, typer.Argument(help="Session ID prefix or 'last' for most recent.")
    ],
    raw: Annotated[
        bool, typer.Option("--raw", help="Output plain text, no formatting.")
    ] = False,
) -> None:
    """Print verbatim user messages for a session."""
    con = _open_db()

    if session_id == "last":
        row = con.execute(
            "SELECT session_id FROM sessions ORDER BY last_ts DESC LIMIT 1"
        ).fetchone()
        if not row:
            stderr.print("[red]No sessions indexed. Run 'index' first.[/red]")
            raise typer.Exit(1)
        session_id = row[0]

    rows = con.execute(
        """
        SELECT msg_index, timestamp, content
        FROM user_messages
        WHERE session_id LIKE ?
        ORDER BY msg_index
    """,
        [f"{session_id}%"],
    ).fetchall()

    if not rows:
        stderr.print(
            f"[yellow]No messages in index for '{session_id}' — check 'list' for valid IDs.[/yellow]"
        )
        raise typer.Exit(1)

    if raw:
        for idx, ts, content in rows:
            date_str = ts[:19].replace("T", " ") if ts else "?"
            print(f"[{idx + 1}] {date_str}")
            print(content)
            print()
    else:
        stdout.print(
            f"\n[bold]User Messages — {session_id}[/bold] ({len(rows)} messages)\n"
        )
        for idx, ts, content in rows:
            date_str = ts[:19].replace("T", " ") if ts else "?"
            stdout.print(f"[dim]── [{idx + 1}] {date_str} ──[/dim]")
            stdout.print(content)
            stdout.print()


def _highlight_excerpt(pattern: re.Pattern, content: str, context_chars: int) -> str:
    """Extract context window around first match and bold the match text."""
    match = pattern.search(content)
    if not match:
        return content[:context_chars]
    start = max(0, match.start() - context_chars // 2)
    end = min(len(content), match.end() + context_chars // 2)
    excerpt = content[start:end]
    prefix = "…" if start > 0 else ""
    suffix = "…" if end < len(content) else ""
    highlighted = pattern.sub(
        lambda m: f"[bold yellow]{m.group()}[/bold yellow]", excerpt
    )
    return f"{prefix}{highlighted}{suffix}"


def _search_file(
    path: Path, pattern: re.Pattern, limit: int, hits: list[tuple[str, str, str, str]]
) -> None:
    """Search one JSONL file for pattern matches, appending to hits."""
    try:
        records = _iter_records(path)
    except OSError:
        return
    for rec in records:
        if len(hits) >= limit:
            return
        if rec.get("type") != "user" or "toolUseResult" in rec:
            continue
        content = _extract_text(rec.get("message", {}).get("content"))
        if not content or _is_noise(content):
            continue
        if pattern.search(content):
            hits.append((
                str(path),
                rec.get("sessionId", path.stem),
                rec.get("timestamp", ""),
                content,
            ))


@app.command("search")
def cmd_search(
    query: Annotated[
        str, typer.Argument(help="Text to search for (case-insensitive).")
    ],
    limit: Annotated[int, typer.Option("--limit", "-n")] = 20,
    project: Annotated[str, typer.Option("--project", "-p")] = "",
    context_chars: Annotated[
        int, typer.Option("--context", "-c", help="Chars of context around match.")
    ] = 200,
) -> None:
    """Search raw JSONL files for text. Returns verbatim matching user messages.

    IMPORTANT: Searches raw files, not the summary cache.
    """
    pattern = re.compile(re.escape(query), re.IGNORECASE)
    files = sorted(
        PROJECTS_DIR.glob("*/*.jsonl"), key=lambda f: f.stat().st_mtime, reverse=True
    )
    if project:
        files = [f for f in files if project.lower() in f.parent.name.lower()]

    hits: list[tuple[str, str, str, str]] = []
    for path in files:
        if len(hits) >= limit:
            break
        _search_file(path, pattern, limit, hits)

    if not hits:
        stdout.print(f"[yellow]No matches for '{query}'[/yellow]")
        return

    plural = "es" if len(hits) != 1 else ""
    stdout.print(
        f"\n[bold]Search results for '{query}'[/bold] ({len(hits)} match{plural})\n"
    )
    for path_str, sid, ts, content in hits:
        date_str = ts[:16].replace("T", " ") if ts else "?"
        proj = _slug_to_project_name(Path(path_str).parent.name)
        stdout.print(f"[dim]── {proj} / {sid[:12]} @ {date_str} ──[/dim]")
        stdout.print(_highlight_excerpt(pattern, content, context_chars))
        stdout.print()


@app.command("show")
def cmd_show(
    session_id: Annotated[str, typer.Argument(help="Session ID prefix or 'last'.")],
) -> None:
    """Show cached summary for a session, or print metadata for manual summarization."""
    con = _open_db()

    if session_id == "last":
        row = con.execute(
            "SELECT session_id FROM sessions ORDER BY last_ts DESC LIMIT 1"
        ).fetchone()
        if not row:
            stderr.print("[red]No sessions indexed.[/red]")
            raise typer.Exit(1)
        session_id = row[0]

    row = con.execute(
        """
        SELECT session_id, file_path, project_name, first_ts, last_ts,
               user_msg_count, assistant_turns, file_size_kb, has_summary
        FROM sessions WHERE session_id LIKE ?
        ORDER BY last_ts DESC LIMIT 1
    """,
        [f"{session_id}%"],
    ).fetchone()

    if not row:
        stderr.print(
            f"[red]Session '{session_id}' not found in index. Run 'list' first.[/red]"
        )
        raise typer.Exit(1)

    sid, file_path, proj, first_ts, last_ts, umsg, aturns, kb, has_sum = row
    SUMMARIES_DIR.mkdir(parents=True, exist_ok=True)
    summary_path = SUMMARIES_DIR / f"{sid}.md"

    if has_sum and summary_path.exists():
        stdout.print(summary_path.read_text())
        return

    date_range = (
        f"{first_ts[:19] if first_ts else '?'} → {last_ts[:19] if last_ts else '?'}"
    )
    summary_status = f"Cached at {summary_path}" if has_sum else "Not yet generated"
    stdout.print(f"""
[bold]Session: {sid}[/bold]
Project:       {proj}
File:          {file_path}
Date range:    {date_range}
User messages: {umsg}
Asst turns:    {aturns}
File size:     {kb:.1f} KB
Summary:       {summary_status}

[dim]To generate summary: read the file, then write to {summary_path}[/dim]
[dim]To view user messages: session-historian messages {sid[:12]}[/dim]
""")


@app.command("mark-summarized")
def cmd_mark_summarized(
    session_id: Annotated[
        str, typer.Argument(help="Session ID to mark as having a cached summary.")
    ],
) -> None:
    """Mark a session as having a cached summary in the index."""
    con = _open_db()
    con.execute(
        "UPDATE sessions SET has_summary = TRUE WHERE session_id LIKE ?",
        [f"{session_id}%"],
    )
    count = _fetch_count(
        con,
        "SELECT COUNT(*) FROM sessions WHERE session_id LIKE ? AND has_summary = TRUE",
        [f"{session_id}%"],
    )
    stdout.print(f"Marked {count} session(s) as summarized.")


if __name__ == "__main__":
    app()
