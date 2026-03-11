# Session Historian Patterns

**Analysis Date:** 2026-03-11
**Package:** session-historian
**Script:** `.claude/skills/session-historian/scripts/session_query.py`

## Command Structure

**Pattern:** Typer CLI with decorator-registered commands

All commands are registered using the `@app.command()` decorator pattern. The app is initialized at the module level:

```python
app = typer.Typer(
    name="session-historian",
    help="Query Claude Code JSONL session history with DuckDB indexing.",
    rich_markup_mode="rich",
    no_args_is_help=True,
)
```

**Commands registered:**

- `@app.command("index")` → `cmd_index()` — `session_query.py:370`
- `@app.command("list")` → `cmd_list()` — `session_query.py:422`
- `@app.command("messages")` → `cmd_messages()` — `session_query.py:498`
- `@app.command("search")` → `cmd_search()` — `session_query.py:609`
- `@app.command("show")` → `cmd_show()` — `session_query.py:652`
- `@app.command("mark-summarized")` → `cmd_mark_summarized()` — `session_query.py:712`

**Entry point:** `if __name__ == "__main__": app()` — `session_query.py:729`

**Conventions:**

- Command names are kebab-case in decorator, snake_case in function name
- Help text provided via docstring first line (not `help=` parameter on decorator)
- All function arguments are annotated with `Annotated[type, typer.Option(...)]` or `Annotated[str, typer.Argument(...)]`
- Each command returns `None` (uses stderr/stdout console objects for output)
- `typer.Exit(code)` used for error signaling (non-zero exit codes)

## Shared Console Objects

**Location:** `session_query.py:42-43`

```python
stderr = Console(stderr=True)
stdout = Console()
```

Rich `Console` instances are created at module level for consistent formatting:

- `stderr`: All error/warning/status messages routed here
- `stdout`: All result output and display tables routed here

Output always uses Rich markup (`[bold]`, `[dim]`, `[red]`, etc.) — no raw print() calls except for `--raw` output mode.

## Core Helper Functions

### `_iter_records(path: Path) -> list[dict]`

**Location:** `session_query.py:108-130`

Parses a JSONL file into list of dicts. Silently skips:
- Empty lines
- Lines that fail JSON parsing
- Non-dict objects

Returns: `list[dict]` — all valid JSON objects from the file

**Key behavior:** Uses `encoding="utf-8", errors="replace"` to handle malformed UTF-8 gracefully.

### `_extract_text(content: str | list[str | dict] | None) -> str`

**Location:** `session_query.py:68-91`

Extracts plain text from a message content field. Handles three formats:

- **Plain string**: Returns as-is
- **None**: Returns empty string
- **List of blocks**: Iterates, extracts text from dicts where `type == "text"`, joins with newlines

Returns: `str` — concatenated text or empty string

**Used by:** `_scan_records()`, `_search_file()`, `cmd_messages()`

### `_is_noise(text: str) -> bool`

**Location:** `session_query.py:94-105`

Filters system messages and tool output. Returns `True` if stripped text starts with any prefix in:

```python
_NOISE_PREFIXES = (
    "<local-command-caveat>",
    "<bash-stdout>",
    "<tool_use_error>",
    "<task-notification>",
    "<command-message>",
    "<system-reminder>",
)
```

**Used by:** `_scan_records()`, `_search_file()` — filters out noise before indexing or searching

## DuckDB Index Usage Pattern

**Database path:** `CACHE_DIR / "session-index.duckdb"` (i.e., `~/.claude/kaizen/session-index.duckdb`) — `session_query.py:51`

**Schema (DDL):** `session_query.py:165-191`

Two tables:

```sql
CREATE TABLE IF NOT EXISTS sessions (
    session_id TEXT PRIMARY KEY,
    file_path TEXT,
    project_slug TEXT,
    project_name TEXT,
    first_ts TEXT,
    last_ts TEXT,
    total_records INTEGER,
    user_msg_count INTEGER,
    assistant_turns INTEGER,
    file_size_kb DOUBLE,
    has_summary BOOLEAN DEFAULT FALSE,
    indexed_at TEXT
);

CREATE TABLE IF NOT EXISTS user_messages (
    session_id TEXT PRIMARY KEY,
    msg_index INTEGER,
    timestamp TEXT,
    content TEXT,
    word_count INTEGER
);
```

**Connection pattern:** `_open_db()` — `session_query.py:194-206`

```python
def _open_db() -> duckdb.DuckDBPyConnection:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(DB_PATH))
    con.execute(_DDL)
    return con
```

Always creates parent directories and runs DDL on connect (idempotent via `IF NOT EXISTS`).

**Query pattern:** Direct parameter substitution via `con.execute(sql, params_list)`. Example — `session_query.py:523-530`:

```python
rows = con.execute(
    """
    SELECT msg_index, timestamp, content
    FROM user_messages
    WHERE session_id LIKE ?
    ORDER BY msg_index
""",
    [f"{session_id}%"],
).fetchall()
```

Uses `?` placeholders for DuckDB parameter binding (positional).

**Helper function:** `_fetch_count(con, sql, params)` — `session_query.py:209-222`

Returns single integer result from COUNT queries.

## Record Parsing and Indexing

### `_scan_records(path: Path, records: list[dict]) -> _FileStats`

**Location:** `session_query.py:238-276`

Extracts statistics from pre-parsed JSONL records:

- Iterates all records, accumulates timestamps
- Filters user messages (type == "user" and no "toolUseResult" key)
- Extracts text and skips noise
- Counts assistant turns
- Returns `_FileStats` dataclass with aggregated metadata

**`_FileStats` structure** (`session_query.py:225-235`):

```python
@dataclass
class _FileStats:
    slug: str
    project_name: str
    first_ts: str
    last_ts: str
    total_records: int
    user_msgs: list[dict]
    assistant_turns: int
    file_kb: float
    now: str
```

### `_index_file(con: DuckDBPyConnection, path: Path) -> tuple[int, int]`

**Location:** `session_query.py:279-338`

Indexes one JSONL file. Uses `path.stem` as the canonical session ID (filename without extension) — stable across re-indexes.

Process:

1. Parse records via `_iter_records(path)` and `_scan_records()`
2. Check if summary exists in `SUMMARIES_DIR / f"{sid}.md"`
3. Insert/upsert sessions table row with `ON CONFLICT ... DO UPDATE`
4. For each user message, insert/upsert into user_messages table

Returns tuple: `(user_msgs_indexed, assistant_turns_count)`

## JSONL Record Structure

**As observed in code** (`session_query.py:254-264`):

User records:

```python
{
    "type": "user",
    "sessionId": "uuid",
    "timestamp": "ISO8601",
    "message": {
        "content": "string or list of blocks"
    }
}
```

Content can be:
- Plain string
- List of blocks: `[{"type": "text", "text": "..."}, ...]`

Filter: Records with `"toolUseResult"` key are skipped (these are tool result blocks, not user messages).

Assistant records:

```python
{
    "type": "assistant",
    "timestamp": "ISO8601"
}
```

Counted for assistant turn metrics but content not extracted.

## Rich Output Patterns

### Table Output

**Pattern:** Rich tables with custom styling. Example — `cmd_list()` — `session_query.py:468-492`:

```python
table = Table(title="Recent Sessions", show_lines=False, box=box.MINIMAL_DOUBLE_HEAD)
table.add_column("Session ID", style="cyan", no_wrap=True)
table.add_column("Project", style="green", no_wrap=True)
# ... add rows ...
table.width = _get_table_width(table)
stdout.print(table, crop=False, overflow="ignore", no_wrap=True, soft_wrap=True)
```

**Measurement helper:** `_get_table_width(table: Table) -> int` — `session_query.py:346-362`

Creates temporary console with width=9999 to get unconstrained table width, preventing wrapping.

### Text Output

All text uses markup:
- `[bold]` for headers
- `[dim]` for secondary info
- `[yellow]` for warnings
- `[red]` for errors
- `[green]` for success

## Session ID Resolution and `last` Alias

**Pattern:** Session ID can be a prefix or the literal string `"last"` — `cmd_messages()` — `session_query.py:516-521`:

```python
if session_id == "last":
    row = con.execute("SELECT session_id FROM sessions ORDER BY last_ts DESC LIMIT 1").fetchone()
    if not row:
        stderr.print("[red]No sessions indexed. Run 'index' first.[/red]")
        raise typer.Exit(1)
    session_id = row[0]
```

Converts `"last"` to the actual session ID of the most recently active session.

**Prefix matching:** Queries use `LIKE f"{session_id}%"` to allow prefix matching:

```python
con.execute(
    "SELECT ... FROM user_messages WHERE session_id LIKE ?",
    [f"{session_id}%"]
)
```

## Output Modes: Raw vs Formatted

**Pattern:** `--raw` flag toggles output formatting — `cmd_messages()` — `session_query.py:537-549`:

```python
if raw:
    for idx, ts, content in rows:
        date_str = ts[:19].replace("T", " ") if ts else "?"
        print(f"[{idx + 1}] {date_str}")
        print(content)
        print()
else:
    stdout.print(f"\n[bold]User Messages — {session_id}[/bold] ({len(rows)} messages)\n")
    for idx, ts, content in rows:
        # Rich-formatted output
        stdout.print(...)
```

Raw mode uses bare `print()`, formatted mode uses `stdout.print()` with Rich markup.

## Search Pattern Extraction

**Pattern:** `_highlight_excerpt()` — `session_query.py:552-577`

Extracts context around regex match with Rich highlighting:

```python
def _highlight_excerpt(pattern: re.Pattern, content: str, context_chars: int) -> str:
    match = pattern.search(content)
    if not match:
        return content[:context_chars]
    start = max(0, match.start() - context_chars // 2)
    end = min(len(content), match.end() + context_chars // 2)
    excerpt = content[start:end]
    highlighted = pattern.sub(lambda m: f"[bold yellow]{m.group()}[/bold yellow]", excerpt)
    return f"{prefix}{highlighted}{suffix}"
```

Used by `cmd_search()` to show match context with ellipsis (`…`) when excerpt is truncated.

## Project Name Slug Resolution

**Pattern:** `_slug_to_project_name(slug: str) -> str` — `session_query.py:133-158`

Converts filesystem slug (directory name like `"home-alice-repos-my-project"`) to human-readable project name (`"my-project"`).

Algorithm:
1. Split slug by hyphens
2. Skip "home" prefix (if present)
3. Skip username (next part)
4. Skip location token if in set: `{"repos", "Desktop", "Documents", "Projects", "src", "code", "work"}`
5. Join remaining parts with hyphens

Fallback: Return original slug if no identifiable prefix found.

## Error Handling

**Pattern:** Commands use `typer.Exit(code)` for non-zero exits:

```python
if not row:
    stderr.print("[red]No sessions indexed.[/red]")
    raise typer.Exit(1)
```

All error messages go to stderr via `stderr.print()`. Normal output goes to stdout.

---

*Pattern analysis: 2026-03-11*
