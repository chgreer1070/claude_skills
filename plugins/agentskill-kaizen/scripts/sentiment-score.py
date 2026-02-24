#!/usr/bin/env -S uv --quiet run --active --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "duckdb>=1.0.0",
#     "typer>=0.23.1",
#     "vaderSentiment>=3.3.2",
# ]
# ///
"""Score sentiment of user messages in Claude Code JSONL session transcripts.

Reads JSONL session files, extracts user-authored messages, runs VADER
sentiment analysis on each, and outputs a CSV of per-message scores
suitable for plotting time-series sentiment data.

Output columns:
    session_id, timestamp, message_index, compound, positive, negative,
    neutral, message_length, message_preview, project_path, project_name
"""

from __future__ import annotations

import csv
import enum
import json
import statistics
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Annotated

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import BarColumn, MofNCompleteColumn, Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

if TYPE_CHECKING:
    from collections.abc import Iterator

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_DEFAULT_GLOB = "~/.claude/projects/*/*.jsonl"
_DEFAULT_OUTPUT = "~/.claude/kaizen/sentiment.csv"
_NOISE_PREFIXES = (
    "<local-command-caveat>",
    "<bash-stdout>",
    "<tool_use_error>",
    "<task-notification>",
    "<command-message>",
)
_NOISE_CONTAINS = "Base directory for this skill"

# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class _SentimentError(Exception):
    """Domain-specific error for sentiment scoring failures."""


def _die(msg: str) -> None:
    """Raise a ``_SentimentError`` with *msg*.

    Args:
        msg: Human-readable error description.

    Raises:
        _SentimentError: Always.
    """
    raise _SentimentError(msg)


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass(slots=True)
class ScoredMessage:
    """A single user message with its VADER sentiment scores."""

    session_id: str
    timestamp: str
    message_index: int
    compound: float
    positive: float
    negative: float
    neutral: float
    message_length: int
    message_preview: str
    project_path: str  # e.g. "-home-ubuntulinuxqa2-repos-myproject"
    project_name: str  # e.g. "myproject" (last segment, human-readable)


@dataclass
class SessionStats:
    """Accumulator for summary statistics across all scored messages."""

    total_messages: int = 0
    session_ids: set[str] = field(default_factory=set)
    compound_scores: list[float] = field(default_factory=list)

    def record(self, msg: ScoredMessage) -> None:
        """Record a scored message into the running statistics.

        Args:
            msg: The scored message to accumulate.
        """
        self.total_messages += 1
        self.session_ids.add(msg.session_id)
        self.compound_scores.append(msg.compound)


# ---------------------------------------------------------------------------
# JSONL extraction
# ---------------------------------------------------------------------------


def _extract_text(content: str | list[dict[str, object]]) -> str:
    """Extract plain text from a JSONL message ``content`` field.

    Handles two formats emitted by Claude Code:
    * A plain JSON string.
    * A JSON array of ``{type, text?, ...}`` objects — only elements with
      ``type == "text"`` contribute text.

    Args:
        content: The raw ``message.content`` value from the JSONL record.

    Returns:
        Concatenated text suitable for sentiment scoring.
    """
    if isinstance(content, str):
        return content

    parts: list[str] = []
    for element in content:
        if isinstance(element, dict) and element.get("type") == "text":
            text_value = element.get("text")
            if isinstance(text_value, str):
                parts.append(text_value)
    return "\n".join(parts)


def _is_noise(text: str) -> bool:
    """Return True if *text* is system-generated noise that should be skipped.

    Args:
        text: The extracted message text.

    Returns:
        Whether the message is noise.
    """
    stripped = text.lstrip()
    if any(stripped.startswith(prefix) for prefix in _NOISE_PREFIXES):
        return True
    return _NOISE_CONTAINS in text


def _iter_user_messages(
    path: Path, *, min_length: int, session_filter: str | None
) -> Iterator[tuple[str, str, int, str]]:
    """Yield ``(session_id, timestamp, index, text)`` for user messages in *path*.

    Streams the file line-by-line to handle large files without loading
    everything into memory.

    Args:
        path: Path to a JSONL session file.
        min_length: Minimum character length to include a message.
        session_filter: If set, only yield messages from this session ID.

    Yields:
        Tuples of (session_id, timestamp, message_index, text).
    """
    index = 0
    with path.open(encoding="utf-8") as fh:
        for raw_line in fh:
            line = raw_line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue  # skip malformed lines

            if not isinstance(record, dict):
                continue
            if record.get("type") != "user":
                continue
            if "toolUseResult" in record:
                continue

            session_id: str = record.get("sessionId", "unknown")
            if session_filter and session_id != session_filter:
                continue

            timestamp: str = record.get("timestamp", "")

            message = record.get("message")
            if not isinstance(message, dict):
                continue
            content = message.get("content")
            if content is None:
                continue

            text = _extract_text(content)
            if len(text) < min_length:
                continue
            if _is_noise(text):
                continue

            index += 1
            yield session_id, timestamp, index, text


# ---------------------------------------------------------------------------
# Project extraction
# ---------------------------------------------------------------------------


def _extract_project(path: Path) -> tuple[str, str]:
    """Extract project_path slug and project_name from a JSONL file path.

    Expects paths of the form:
        ~/.claude/projects/{project_slug}/{session}.jsonl

    The slug encodes a filesystem path with ``/`` replaced by ``-``, e.g.
    ``-home-ubuntulinuxqa2-repos-stateless-agent-methodology``.

    The ``project_name`` is derived by stripping the leading path components
    (``-home-{username}-``) and optional single-word location tokens (e.g.
    ``repos``, ``Desktop``), then joining the remaining segments with ``-``.
    Falls back to the full slug if the structure is not recognised.

    Args:
        path: Path to a JSONL session file.

    Returns:
        Tuple of (project_path_slug, project_name).
    """
    slug = path.parent.name  # directory under ~/.claude/projects/

    # Split on "-"; leading "-" produces an empty leading segment.
    parts = slug.split("-")
    # Remove the leading empty string produced by the initial "-"
    non_empty = [p for p in parts if p]

    # Expected prefix: ["home", "<username>", ...]
    # Skip "home" and the next segment (username, always a single word
    # without embedded hyphens since it was a single path component).
    # Then skip known single-word location tokens before the project name.
    location_tokens = {"repos", "Desktop", "Documents", "Projects", "src", "code", "work"}

    idx = 0
    if idx < len(non_empty) and non_empty[idx] == "home":
        idx += 1  # skip "home"
    if idx < len(non_empty):
        idx += 1  # skip username
    # Skip optional single-word location token
    if idx < len(non_empty) and non_empty[idx] in location_tokens:
        idx += 1

    project_name = "-".join(non_empty[idx:]) if idx < len(non_empty) else slug

    return slug, project_name


# ---------------------------------------------------------------------------
# Sentiment scoring
# ---------------------------------------------------------------------------


def _score_messages(
    files: list[Path],
    *,
    min_length: int,
    session_filter: str | None,
    analyzer: SentimentIntensityAnalyzer,
    progress: Progress,
) -> list[ScoredMessage]:
    """Score all user messages across *files* and return sorted results.

    Args:
        files: JSONL file paths to process.
        min_length: Minimum message length to score.
        session_filter: Optional session ID filter.
        analyzer: Pre-initialised VADER analyzer instance.
        progress: Rich progress bar to update during processing.

    Returns:
        List of ScoredMessage sorted by (session_id, timestamp).
    """
    results: list[ScoredMessage] = []
    task = progress.add_task(":magnifying_glass_tilted_left: Scoring messages", total=len(files))

    for path in files:
        project_path, project_name = _extract_project(path)
        for session_id, timestamp, msg_index, text in _iter_user_messages(
            path, min_length=min_length, session_filter=session_filter
        ):
            scores = analyzer.polarity_scores(text)
            results.append(
                ScoredMessage(
                    session_id=session_id,
                    timestamp=timestamp,
                    message_index=msg_index,
                    compound=scores["compound"],
                    positive=scores["pos"],
                    negative=scores["neg"],
                    neutral=scores["neu"],
                    message_length=len(text),
                    message_preview=text[:100].replace("\n", " "),
                    project_path=project_path,
                    project_name=project_name,
                )
            )
        progress.advance(task)

    results.sort(key=lambda m: (m.session_id, m.timestamp))
    return results


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

_CSV_COLUMNS = [
    "session_id",
    "timestamp",
    "message_index",
    "compound",
    "positive",
    "negative",
    "neutral",
    "message_length",
    "message_preview",
    "project_path",
    "project_name",
]


def _write_csv(results: list[ScoredMessage], output: Path) -> None:
    """Write *results* as CSV to *output*.

    Creates parent directories if they do not exist.

    Args:
        results: Scored messages to serialise.
        output: File path for the CSV output.
    """
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=_CSV_COLUMNS)
        writer.writeheader()
        for msg in results:
            writer.writerow({
                "session_id": msg.session_id,
                "timestamp": msg.timestamp,
                "message_index": msg.message_index,
                "compound": f"{msg.compound:.4f}",
                "positive": f"{msg.positive:.4f}",
                "negative": f"{msg.negative:.4f}",
                "neutral": f"{msg.neutral:.4f}",
                "message_length": msg.message_length,
                "message_preview": msg.message_preview,
                "project_path": msg.project_path,
                "project_name": msg.project_name,
            })


_DEFAULT_DB = "~/.claude/kaizen/kaizen.duckdb"


class ScopeTarget(enum.StrEnum):
    """Output scope for lesson files."""

    user = "user"
    project = "project"
    local = "local"


def _resolve_scope_path(scope: ScopeTarget) -> Path:
    """Return the resolved output path for *scope*.

    Args:
        scope: The target scope for lesson output.

    Returns:
        Absolute path to the lesson file or directory.
    """
    if scope == ScopeTarget.user:
        return Path("~/.claude/kaizen/lessons/").expanduser()
    if scope == ScopeTarget.project:
        return Path.cwd() / ".claude" / "kaizen" / "lessons.md"
    # local
    return Path.cwd() / ".claude" / "kaizen" / "lessons.local.md"


_DB_CREATE_SQL = """
CREATE TABLE IF NOT EXISTS sentiment (
    session_id      TEXT    NOT NULL,
    timestamp       TEXT,
    message_index   INTEGER NOT NULL,
    compound        DOUBLE,
    positive        DOUBLE,
    negative        DOUBLE,
    neutral         DOUBLE,
    message_length  INTEGER,
    message_preview TEXT,
    project_path    TEXT,
    project_name    TEXT,
    PRIMARY KEY (session_id, message_index)
)
"""

_DB_UPSERT_SQL = """
INSERT INTO sentiment (
    session_id, timestamp, message_index,
    compound, positive, negative, neutral,
    message_length, message_preview,
    project_path, project_name
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
ON CONFLICT (session_id, message_index) DO UPDATE SET
    timestamp       = excluded.timestamp,
    compound        = excluded.compound,
    positive        = excluded.positive,
    negative        = excluded.negative,
    neutral         = excluded.neutral,
    message_length  = excluded.message_length,
    message_preview = excluded.message_preview,
    project_path    = excluded.project_path,
    project_name    = excluded.project_name
"""


def _write_duckdb(results: list[ScoredMessage], db_path: Path) -> None:
    """Upsert *results* into the persistent DuckDB database at *db_path*.

    Creates the database and table if they do not exist. Uses INSERT OR REPLACE
    to avoid duplicate rows on re-runs.

    The table schema matches ScoredMessage fields plus a surrogate primary key
    of (session_id, message_index).

    Args:
        results: Scored messages to persist.
        db_path: Path to the DuckDB file (created if missing).
    """
    try:
        import duckdb
    except ImportError:
        import warnings

        warnings.warn(
            "duckdb is not installed — skipping database write. Install with: pip install duckdb", stacklevel=2
        )
        return

    db_path.parent.mkdir(parents=True, exist_ok=True)
    rows = [
        (
            msg.session_id,
            msg.timestamp,
            msg.message_index,
            msg.compound,
            msg.positive,
            msg.negative,
            msg.neutral,
            msg.message_length,
            msg.message_preview,
            msg.project_path,
            msg.project_name,
        )
        for msg in results
    ]
    with duckdb.connect(str(db_path)) as con:
        con.execute(_DB_CREATE_SQL)
        con.executemany(_DB_UPSERT_SQL, rows)


def _print_summary(stats: SessionStats, stderr: Console) -> None:
    """Print summary statistics to stderr.

    Args:
        stats: Accumulated statistics from scoring.
        stderr: Rich console targeting stderr.
    """
    if not stats.compound_scores:
        stderr.print("[yellow]No messages scored.[/yellow]")
        return

    scores = stats.compound_scores
    lines = [
        f"[bold]Messages scored:[/bold]  {stats.total_messages}",
        f"[bold]Sessions found:[/bold]   {len(stats.session_ids)}",
        f"[bold]Mean compound:[/bold]    {statistics.mean(scores):.4f}",
        f"[bold]Median compound:[/bold]  {statistics.median(scores):.4f}",
        f"[bold]Min compound:[/bold]     {min(scores):.4f}",
        f"[bold]Max compound:[/bold]     {max(scores):.4f}",
    ]
    panel = Panel("\n".join(lines), title=":bar_chart: Sentiment Summary", border_style="cyan")
    stderr.print(panel)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

app = typer.Typer(
    name="sentiment-score",
    help="VADER sentiment analysis over Claude Code JSONL session transcripts.",
    rich_markup_mode="rich",
    no_args_is_help=True,
)


@app.command()
def score(
    *,
    glob_pattern: Annotated[
        str,
        typer.Option(
            "--glob-pattern", "-g", help="Glob pattern matching JSONL session files.", rich_help_panel="Input Options"
        ),
    ] = _DEFAULT_GLOB,
    output: Annotated[
        Path,
        typer.Option(
            "--output",
            "-o",
            help="Output CSV path. Defaults to ~/.claude/kaizen/sentiment.csv.",
            rich_help_panel="Input Options",
        ),
    ] = Path(_DEFAULT_OUTPUT),
    min_length: Annotated[
        int,
        typer.Option(
            "--min-length", "-m", help="Minimum message character length to score.", rich_help_panel="Filter Options"
        ),
    ] = 10,
    session_filter: Annotated[
        str | None,
        typer.Option(
            "--session-filter", "-s", help="Restrict scoring to a single session ID.", rich_help_panel="Filter Options"
        ),
    ] = None,
    db: Annotated[
        Path, typer.Option("--db", help="Path to DuckDB database file.", rich_help_panel="Output Options")
    ] = Path(_DEFAULT_DB),
    scope: Annotated[
        ScopeTarget | None,
        typer.Option(
            "--scope",
            help=(
                "Lesson output scope: 'user' → ~/.claude/kaizen/lessons/, "
                "'project' → {cwd}/.claude/kaizen/lessons.md (git-tracked), "
                "'local' → {cwd}/.claude/kaizen/lessons.local.md (gitignored)."
            ),
            rich_help_panel="Output Options",
        ),
    ] = None,
) -> None:
    r"""Score user-message sentiment in Claude Code JSONL transcripts.

    Reads JSONL files matching --glob-pattern, extracts user messages,
    runs VADER sentiment analysis, and writes a CSV of per-message scores.
    """
    stderr = Console(stderr=True)

    # Resolve ~ in output path so ~/.claude/kaizen/sentiment.csv works
    resolved_output = output.expanduser()

    expanded = Path(glob_pattern).expanduser()
    # Split into the longest concrete prefix and the glob tail so we can
    # use Path.glob (PTH207) instead of the stdlib glob module.
    parts = expanded.parts
    root_parts: list[str] = []
    for part in parts:
        if any(c in part for c in ("*", "?", "[")):
            break
        root_parts.append(part)
    root = Path(*root_parts) if root_parts else Path()
    tail = str(Path(*parts[len(root_parts) :])) if len(root_parts) < len(parts) else "*"
    files = sorted(p for p in root.glob(tail) if p.is_file())

    if not files:
        stderr.print(f"[yellow]No JSONL files matched pattern:[/yellow] {glob_pattern}")
        raise typer.Exit(0)

    stderr.print(f"[dim]Matched {len(files)} JSONL file(s)[/dim]")

    analyzer = SentimentIntensityAnalyzer()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        MofNCompleteColumn(),
        TimeElapsedColumn(),
        console=stderr,
    ) as progress:
        results = _score_messages(
            files, min_length=min_length, session_filter=session_filter, analyzer=analyzer, progress=progress
        )

    # Compute summary stats
    stats = SessionStats()
    for msg in results:
        stats.record(msg)

    _write_csv(results, resolved_output)
    _write_duckdb(results, db.expanduser())
    if scope is not None:
        scope_path = _resolve_scope_path(scope)
        stderr.print(f"[dim]Lesson scope:[/dim] [cyan]{scope.value}[/cyan] → {scope_path}")
    _print_summary(stats, stderr)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    """Run the CLI application.

    Args:
        argv: Command-line arguments. ``None`` uses ``sys.argv``.

    Returns:
        Exit code (0 for success, non-zero for errors).
    """
    try:
        app(argv, standalone_mode=False)
    except _SentimentError as exc:
        stderr = Console(stderr=True)
        stderr.print(Panel(str(exc), title=":cross_mark: Error", border_style="red"))
        return 1
    except SystemExit as exc:
        return exc.code if isinstance(exc.code, int) else 1
    except FileNotFoundError as exc:
        stderr = Console(stderr=True)
        stderr.print(Panel(f"File not found: {exc}", title=":cross_mark: Error", border_style="red"))
        return 2
    except PermissionError as exc:
        stderr = Console(stderr=True)
        stderr.print(Panel(f"Permission denied: {exc}", title=":cross_mark: Error", border_style="red"))
        return 2
    except OSError as exc:
        stderr = Console(stderr=True)
        stderr.print(Panel(f"I/O error: {exc}", title=":cross_mark: Error", border_style="red"))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
