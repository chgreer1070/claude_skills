# Architecture Spec: Session Historian — Four New Query Commands

- **Slug**: session-historian-enhance
- **Generated**: 2026-03-11
- **Target file**: `.claude/skills/session-historian/scripts/session_query.py`
- **Distribution**: PEP 723 standalone script (existing — no change)

---

## 1. Executive Summary

This spec describes the addition of four Typer commands to the existing `session_query.py`
standalone script. All four commands are pure extensions — no existing command is modified,
no new dependencies are added, and all new code reuses the established patterns for session-ID
resolution, JSONL parsing, Rich/raw output switching, and stderr error reporting.

The commands expose four behavioral views of JSONL session data that the current commands do not
provide: tool error enumeration (`errors`), tool usage statistics with success/failure breakdown
(`tools`), user irritation signal detection (`irritation`), and live session file path resolution
for agent self-inspection (`current-path`).

The primary consumers are Claude Code agents running retrospective analysis or real-time session
inspection. Raw output mode is therefore equally important as Rich-formatted mode.

---

## 2. Architecture Overview

### C4 Context

```text
┌─────────────────────────────────────────────────────────┐
│  Claude Code Session                                     │
│                                                          │
│  ┌───────────────┐      ┌──────────────────────────┐    │
│  │  Orchestrator │─────>│  session_query.py        │    │
│  │  Agent        │      │  (Typer CLI — PEP 723)   │    │
│  └───────────────┘      │                          │    │
│                         │  errors / tools /        │    │
│  ┌───────────────┐      │  irritation /            │    │
│  │  Developer    │─────>│  current-path            │    │
│  │  (human)      │      └────────────┬─────────────┘    │
│  └───────────────┘                   │                  │
│                                      │                  │
│                         ┌────────────▼─────────────┐    │
│                         │  ~/.claude/              │    │
│                         │  ├── projects/<slug>/    │    │
│                         │  │   └── <sid>.jsonl     │    │
│                         │  └── kaizen/             │    │
│                         │      └── session-index.  │    │
│                         │          duckdb           │    │
│                         └──────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
```

### C4 Container — session_query.py internal structure

```text
session_query.py
├── PEP 723 inline metadata (no change)
├── Module constants
│   ├── PROJECTS_DIR = Path.home() / ".claude" / "projects"   (existing)
│   ├── CACHE_DIR / DB_PATH                                    (existing)
│   ├── _CORRECTION_PHRASES: tuple[str, ...]                   (NEW)
│   └── _STUCK_LOOP_THRESHOLD: int = 3                         (NEW)
│
├── Shared console objects: stderr, stdout                     (existing)
│
├── Core helper functions (existing — all reused unchanged)
│   ├── _iter_records(path) -> list[dict]
│   ├── _extract_text(content) -> str
│   ├── _is_noise(text) -> bool
│   ├── _open_db() -> DuckDBPyConnection
│   ├── _get_table_width(table) -> int
│   └── _resolve_session(con, session_id) -> tuple[str, Path]  (NEW helper)
│
├── Existing commands (no change)
│   ├── cmd_index, cmd_list, cmd_messages, cmd_search
│   ├── cmd_show, cmd_mark_summarized
│
└── New commands
    ├── cmd_errors(session_id, raw) -> None
    ├── cmd_tools(session_id, raw) -> None
    ├── cmd_irritation(session_id, raw) -> None
    └── cmd_current_path(rich_flag) -> None
```

---

## 3. Technology Stack

All technology choices are inherited from the existing script. No new decisions required.

| Component | Technology | Justification |
|-----------|------------|---------------|
| CLI framework | Typer 0.21+ | Existing — all commands use `@app.command()` |
| Output formatting | Rich (transitive via Typer) | Existing — `stdout`/`stderr` Console objects |
| Session index | DuckDB | Existing — session ID prefix lookup |
| JSONL parsing | stdlib `json` | Existing — `_iter_records()` |
| Path resolution | stdlib `pathlib`, `os` | `PROJECTS_DIR`, `os.environ` |
| Hash computation | stdlib `hashlib` | Tool input identity for stuck-loop detection |
| Distribution | PEP 723 standalone script | Existing — no change |

**ADR-001 (inherited)**: Typer for CLI — type safety, Rich included, decorator pattern consistent
with all existing commands.

**ADR-002 (inherited)**: PEP 723 distribution — zero-setup execution, single file.

**ADR-NEW-001**: `hashlib.md5` for tool input identity hashing in stuck-loop detection. The hash
is computed over the JSON-serialized `input` dict of each `tool_use` block. MD5 is sufficient
here — this is a fingerprint for equality comparison within a single session parse, not a
security primitive. No new import needed beyond stdlib.

---

## 4. Component Design

### 4.1 New Module-Level Constants

**Purpose**: Configuration values extracted to constants — not magic literals inside functions.

```python
_CORRECTION_PHRASES: tuple[str, ...] = (
    "that's wrong",
    "no,",
    "stop",
    "undo",
    "revert",
    "don't",
    "not what i asked",
    "wrong",
    "incorrect",
    "that's not",
)

_STUCK_LOOP_THRESHOLD: int = 3
```

**Placement**: After the existing `_NOISE_PREFIXES` constant (around line 65).

**Rationale**: Phrases and threshold are policy decisions, not implementation details. Extracting
them to constants allows the implementation agent to find and modify them without touching logic,
and makes them visible to future callers of the module.

### 4.2 New Helper: `_resolve_session`

**Purpose**: Encapsulates the "last" alias resolution + DuckDB prefix lookup + JSONL path
retrieval that is repeated across `cmd_messages`, `cmd_show`, and will be needed by the three
new session-accepting commands. Extracting it eliminates copy-paste.

**Interface**:

```python
def _resolve_session(
    con: duckdb.DuckDBPyConnection,
    session_id: str,
) -> tuple[str, Path]:
    ...
```

**Contract**:
- Input: open DuckDB connection, session ID string (may be `"last"` or a prefix)
- Output: `(resolved_session_id: str, jsonl_path: Path)` — always a complete session ID and
  an existing path
- On failure: prints to `stderr`, raises `typer.Exit(1)` — caller does not need to handle errors

**Dependencies**: `_open_db()` (already called by caller), `stderr`, `typer.Exit`

**Placement**: After `_fetch_count()` (around line 222), before existing command functions.

### 4.3 Command: `cmd_errors`

**Registration**: `@app.command("errors")`

**Interface**:

```python
def cmd_errors(
    session_id: Annotated[str, typer.Argument(help="Session ID prefix, or 'last'")] = "last",
    raw: Annotated[bool, typer.Option("--raw", help="Plain text output for piping")] = False,
) -> None:
    """List tool errors from a session."""
    ...
```

**Data extraction logic** (contract, not implementation):

Iterate records from `_iter_records(path)`. For each record:

1. Examine `record.get("message", {}).get("content")` — when this field is a list, iterate
   each block.
2. A block represents a tool error when both conditions are true:
   - `block.get("type") == "tool_result"`
   - `block.get("is_error") is True` (boolean — not truthy string)
3. For each qualifying block, extract:
   - `timestamp`: from `record.get("timestamp", "")`
   - `tool_use_id`: from `block.get("tool_use_id", "")` — used to cross-reference tool name
   - `error_content`: from `block.get("content", "")` — may be string or list of text blocks;
     use `_extract_text()` to normalize
4. Cross-reference `tool_use_id` against the tool name: scan assistant records in the same
   session for `tool_use` blocks matching the id (build a `dict[str, str]` of
   `tool_use_id -> tool_name` from a first pass). This gives the tool name for display.

**Output — Rich mode** (default):

```text
Tool Errors — <session_id> (N errors)

[timestamp]  [tool_name or "(unknown)"]
[error_content, truncated to ~200 chars with ellipsis if longer]
```

Rendered as `stdout.print()` with Rich markup. No table — errors are variable-length prose.

**Output — raw mode** (`--raw`):

```text
<timestamp>\t<tool_name>\t<error_content_single_line>
```

Tab-separated, one error per line. Newlines in error content replaced with space.

**Zero results**: Print to `stderr` if no errors found: `"No tool errors in session <id>"`.
Exit code 0 (absence of errors is not an error).

**Exit codes**: 0 on success (including zero errors); 1 if session not found.

### 4.4 Command: `cmd_tools`

**Registration**: `@app.command("tools")`

**Interface**:

```python
def cmd_tools(
    session_id: Annotated[str, typer.Argument(help="Session ID prefix, or 'last'")] = "last",
    raw: Annotated[bool, typer.Option("--raw", help="Plain text output for piping")] = False,
) -> None:
    """List tools used with call counts and success/failure breakdown."""
    ...
```

**Data extraction logic**:

Two-pass approach over `_iter_records(path)`:

Pass 1 — collect tool_use entries:
- For each assistant-role record (`record.get("type") == "assistant"`), inspect
  `record.get("message", {}).get("content", [])`.
- For each block where `block.get("type") == "tool_use"`, record:
  `{"id": block["id"], "name": block["name"], "timestamp": record.get("timestamp", "")}`

Pass 2 — correlate tool_result entries:
- For each user-role record, inspect content blocks where `block.get("type") == "tool_result"`.
- Match by `block.get("tool_use_id")` to the tool_use entry collected in Pass 1.
- Classify as success (`block.get("is_error") is not True`) or failure (`is_error is True`).

Aggregate into `dict[str, ToolStats]` keyed by tool name:

```python
# Data model — fields only, no implementation
class ToolStats:
    name: str
    total: int
    successes: int
    failures: int
    unmatched: int  # tool_use blocks with no corresponding tool_result
```

**Output — Rich mode** (default):

Rich table using `box.MINIMAL_DOUBLE_HEAD`:

| Column | Style | no_wrap |
|--------|-------|---------|
| Tool Name | cyan | True |
| Total Calls | right-justified | False |
| Successes | green, right | False |
| Failures | red, right | False |
| Unmatched | dim, right | False |

Table sorted by Total Calls descending. Apply `_get_table_width()` pattern before printing.

**Output — raw mode**:

```text
<tool_name>\t<total>\t<successes>\t<failures>\t<unmatched>
```

Header line: `tool\ttotal\tsuccesses\tfailures\tunmatched`

**Zero results**: Print `"No tool calls recorded in session <id>"` to stderr. Exit 0.

**Exit codes**: 0 on success; 1 if session not found.

### 4.5 Command: `cmd_irritation`

**Registration**: `@app.command("irritation")`

**Interface**:

```python
def cmd_irritation(
    session_id: Annotated[str, typer.Argument(help="Session ID prefix, or 'last'")] = "last",
    raw: Annotated[bool, typer.Option("--raw", help="Plain text output for piping")] = False,
) -> None:
    """Detect user irritation signals: correction phrases and stuck tool loops."""
    ...
```

**Data extraction — correction phrases**:

For each user-role record (same filter as `_scan_records`: `type == "user"` and no
`"toolUseResult"` key):
- Extract text via `_extract_text(record.get("message", {}).get("content"))`.
- Skip if `_is_noise(text)` returns True.
- For each phrase in `_CORRECTION_PHRASES`, check `phrase in text.lower()`.
- On match, record: `{"timestamp": record.get("timestamp", ""), "phrase": phrase, "excerpt": text[:200]}`

**Data extraction — stuck loops**:

Iterate assistant records in chronological order. For each `tool_use` block in each assistant
record:
- Compute identity key: `f"{block['name']}:{hashlib.md5(json.dumps(block.get('input', {}), sort_keys=True).encode()).hexdigest()[:8]}"`
- Maintain a sliding window: track the current consecutive run of identical keys with a
  `(current_key, count, first_timestamp, tool_name)` tuple.
- When consecutive count reaches `_STUCK_LOOP_THRESHOLD`, emit a stuck-loop signal.
- Reset on any different key.

Stuck-loop signal fields: `{"tool_name": str, "count": int, "first_timestamp": str, "input_hash": str}`

**Output — Rich mode**:

Two sections, each rendered if non-empty:

Section 1 — Correction Phrases:
```
Correction Phrases (N found)
[timestamp]  [phrase matched]
[excerpt...]
```

Section 2 — Stuck Tool Loops (N loops detected):
```
Stuck Tool Loops
[timestamp]  [tool_name]  repeated [count] times  (input hash: [hash])
```

If both sections are empty: print `"No irritation signals detected in session <id>"` to stderr.
Exit 0.

**Output — raw mode**:

```text
phrase\t<timestamp>\t<phrase>\t<excerpt_single_line>
loop\t<timestamp>\t<tool_name>\t<count>\t<input_hash>
```

One record per line. Type prefix (`phrase` or `loop`) in first column.

**Exit codes**: 0 on success; 1 if session not found.

### 4.6 Command: `cmd_current_path`

**Registration**: `@app.command("current-path")`

**Interface**:

```python
def cmd_current_path(
    rich_flag: Annotated[bool, typer.Option("--rich", help="Human-readable display")] = False,
) -> None:
    """Resolve and print the current session's JSONL path."""
    ...
```

**This command does not accept SESSION_ID.** It resolves the live session using environment
variables — it has no fallback to DuckDB.

**Resolution algorithm**:

1. Read `session_id = os.environ.get("CLAUDE_SESSION_ID", "")`.
   If empty: print to stderr `"CLAUDE_SESSION_ID is not set"`, raise `typer.Exit(1)`.

2. Compute encoded CWD:
   - `cwd = Path.cwd()`
   - `encoded = str(cwd).replace("/", "-").lstrip("-")`
   - Result for `/home/user/repos/foo` → `"home-user-repos-foo"` (leading slash removed,
     slashes become hyphens)

3. Construct candidate path: `PROJECTS_DIR / encoded / f"{session_id}.jsonl"`

4. If path exists: print the absolute path string (raw by default, Rich panel if `--rich`).
   Exit 0.

5. If path does not exist: print to stderr:
   ```
   Session file not found.
   Session ID: <session_id>
   Expected path: <candidate_path>
   Projects dir: <PROJECTS_DIR>
   ```
   Raise `typer.Exit(1)`.

**Default output**: Raw path on stdout — one line, no decoration. Optimized for agent piping.

**`--rich` output**: Rich Panel with title `"Current Session Path"`, green border, full path
inside.

**No DuckDB**: This command does not open or query DuckDB. It is a pure filesystem check. This
keeps it fast and dependency-free relative to the session index state.

---

## 5. Data Architecture

### 5.1 JSONL Schema — Verified Fields

These field paths are the contract for the new commands:

```text
Tool-use block (inside assistant-role message.content[]):
  record.type == "assistant"
  record.message.content[N].type == "tool_use"
  record.message.content[N].id        -- str, unique tool call ID
  record.message.content[N].name      -- str, tool name (e.g., "Read", "Bash")
  record.message.content[N].input     -- dict, tool arguments

Tool-result block (inside user-role message.content[]):
  record.type == "user"
  record.message.content[N].type == "tool_result"
  record.message.content[N].tool_use_id  -- str, matches tool_use.id above
  record.message.content[N].is_error     -- bool, True if error
  record.message.content[N].content      -- str or list, error/result text

Common fields on all records:
  record.timestamp   -- ISO 8601 string
  record.sessionId   -- str, session UUID
  record.type        -- "user" | "assistant" | "system" | ...
```

### 5.2 In-Memory Data Models

These are data-holding structures passed between extraction logic and output rendering. No
persistence beyond the lifetime of a single command invocation.

```python
# Tool statistics aggregate — used by cmd_tools
class ToolStats:
    name: str
    total: int
    successes: int
    failures: int
    unmatched: int  # tool_use with no matching tool_result

# Tool error record — used by cmd_errors
class ToolError:
    timestamp: str
    tool_name: str      # resolved from tool_use_id cross-reference; "" if unresolvable
    tool_use_id: str
    error_content: str  # normalized via _extract_text()

# Correction phrase signal — used by cmd_irritation
class CorrectionSignal:
    timestamp: str
    phrase: str         # the matched phrase from _CORRECTION_PHRASES
    excerpt: str        # first 200 chars of the message containing the phrase

# Stuck-loop signal — used by cmd_irritation
class StuckLoopSignal:
    tool_name: str
    count: int
    first_timestamp: str
    input_hash: str     # 8-char MD5 hex prefix of JSON-serialized tool input
```

**Implementation note**: These may be implemented as `dataclass`, `TypedDict`, or `NamedTuple`.
The architecture does not prescribe the form — only the fields and types.

### 5.3 Encoded CWD Format

The `current-path` command encodes the working directory using this algorithm:

```text
Input:  /home/alice/repos/my-project
Step 1: replace all "/" with "-"  →  -home-alice-repos-my-project
Step 2: lstrip("-")               →  home-alice-repos-my-project
Output: home-alice-repos-my-project
```

This matches the directory naming convention used by Claude Code for project slug directories
under `~/.claude/projects/`.

---

## 6. Security Architecture

New commands inherit all security properties of the existing script. No new security surface
is introduced.

**Checklist**:
- [x] Path traversal prevention — `PROJECTS_DIR / encoded / f"{session_id}.jsonl"` uses
  `pathlib.Path` concatenation, which does not allow `..` traversal through component join.
  The encoded CWD replaces `/` with `-` so no traversal characters remain.
- [x] Command injection prevention — no subprocess calls in any new command.
- [x] Secure temp file handling — no temp files created.
- [x] Rate limiting — not applicable (local filesystem reads only).
- [x] Certificate validation — not applicable (no network calls).
- [x] Input sanitization — session ID from env var is used only as a filename component joined
  via `Path`; DuckDB queries use parameterized `?` placeholders (existing pattern).

---

## 7. Testing Architecture

### 7.1 Strategy

The test suite targets the four new command functions and the `_resolve_session` helper.
All external dependencies (DuckDB, filesystem) are mocked via `pytest-mock`.

**Test types**:
- CLI integration tests via `typer.testing.CliRunner` — test argument parsing, exit codes,
  output presence
- Unit tests on extraction logic via direct function calls with fixture JSONL data

### 7.2 Test Data Fixtures

Fixture JSONL files in `tests/fixtures/` (for the session-historian test suite):

```text
tests/fixtures/
├── session_with_errors.jsonl       # records with tool_result is_error=True
├── session_no_errors.jsonl         # clean session with zero errors
├── session_tools_mixed.jsonl       # mix of successful and failed tool calls
├── session_irritation.jsonl        # records with correction phrases + stuck loops
└── session_empty.jsonl             # empty file (edge case)
```

### 7.3 CLI Integration Tests

```python
# Test pattern — errors command
@pytest.mark.cli
def test_errors_default_raw(runner, tmp_db, session_with_errors):
    result = runner.invoke(app, ["errors", "abc123", "--raw"], env={"NO_COLOR": "1"})
    assert result.exit_code == 0
    assert "Read" in result.stdout  # tool name present

@pytest.mark.cli
def test_errors_no_results_exits_zero(runner, tmp_db, session_no_errors):
    result = runner.invoke(app, ["errors", "abc123"])
    assert result.exit_code == 0

@pytest.mark.cli
def test_current_path_no_env_var(runner):
    result = runner.invoke(app, ["current-path"], env={"CLAUDE_SESSION_ID": ""})
    assert result.exit_code == 1
    assert "CLAUDE_SESSION_ID" in result.stderr

@pytest.mark.cli
def test_current_path_missing_file(runner, tmp_path, monkeypatch):
    monkeypatch.setenv("CLAUDE_SESSION_ID", "nonexistent-session")
    result = runner.invoke(app, ["current-path"])
    assert result.exit_code == 1
    assert "not found" in result.stderr.lower()
```

### 7.4 Unit Tests — Extraction Logic

```python
# Test extraction helpers directly with fixture dicts
@pytest.mark.unit
def test_tool_use_id_cross_reference_resolves_name(sample_records):
    ...  # verify that tool_name is resolved from tool_use_id

@pytest.mark.unit
def test_stuck_loop_detected_at_threshold(assistant_records_with_loops):
    ...  # verify loop detected at exactly _STUCK_LOOP_THRESHOLD

@pytest.mark.unit
def test_correction_phrase_case_insensitive(user_record_with_wrong):
    ...  # "WRONG" should match "wrong" phrase
```

### 7.5 pytest Configuration

```toml
[tool.pytest.ini_options]
addopts = [
    "--cov=.claude/skills/session-historian/scripts",
    "--cov-report=term-missing",
    "-v",
]
testpaths = ["tests"]
markers = [
    "slow: marks tests as slow",
    "cli: marks tests as CLI integration tests",
    "unit: marks tests as unit tests",
]

[tool.coverage.run]
branch = true

[tool.coverage.report]
show_missing = true
fail_under = 80
```

---

## 8. Distribution Architecture

**No change.** `session_query.py` is an existing PEP 723 standalone script with this shebang
and inline metadata block:

```python
#!/usr/bin/env -S uv --quiet run --active --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "duckdb>=1.0.0",
#   "typer>=0.21.0",
# ]
# ///
```

No new dependencies are added. The four new commands use only:
- `duckdb` (existing)
- `typer` / `rich` (existing)
- stdlib: `json`, `os`, `re`, `hashlib`, `pathlib` (all already imported or stdlib-available)

The PEP 723 metadata block does not change.

---

## 9. Architectural Decisions (ADRs)

### ADR-NEW-001: `hashlib.md5` for tool-input identity in stuck-loop detection

**Context**: `irritation` needs to detect consecutive identical tool calls. "Identical" is
defined as same tool name AND same input arguments (per spec: `identity = tool name + input hash`).

**Decision**: Compute `hashlib.md5(json.dumps(input, sort_keys=True).encode()).hexdigest()[:8]`
and concatenate with tool name as the identity key.

**Rationale**:
- `sort_keys=True` on `json.dumps` makes input dict serialization order-independent.
- MD5 is sufficient for this use case — it is not a security primitive, only an equality
  fingerprint within one session parse.
- 8-char hex prefix is displayed in output to help human readers identify which input variation
  recurred.
- No new import: `hashlib` is stdlib.

**Alternatives considered**:
- Tool name only (without input hash): produces false positives when repeated calls have
  different arguments (e.g., `Read` on different files). Rejected.
- `sha256`: overkill — longer, no benefit for equality fingerprinting. Rejected.

### ADR-NEW-002: `_resolve_session` extracted as shared helper

**Context**: `cmd_messages` and `cmd_show` both contain inline copies of the "last" alias
resolution and JSONL path lookup logic. The three new session-accepting commands (`errors`,
`tools`, `irritation`) need the same logic.

**Decision**: Extract `_resolve_session(con, session_id) -> tuple[str, Path]` as a private
module-level helper.

**Rationale**:
- Five commands will use this logic after this feature. Inline copies create five
  divergence points.
- The helper encapsulates error handling and exit — callers are simpler.
- The existing commands (`cmd_messages`, `cmd_show`) should be updated to call `_resolve_session`
  as part of this change, eliminating the existing duplicate code.

**Alternatives considered**:
- Leave existing commands unchanged, only use helper in new commands: leaves the existing
  duplicates in place. Rejected — this is a refactor opportunity with zero risk (behavior
  unchanged, only extraction).

### ADR-NEW-003: `current-path` defaults to raw output without a `--raw` flag

**Context**: Other commands default to Rich and offer `--raw`. The spec says `current-path`
should be "raw output by default (agent consumption)" with `--rich` as an opt-in.

**Decision**: `current-path` defaults to plain `print(path)` on stdout. `--rich` flag enables
Rich Panel display.

**Rationale**:
- `current-path` is agent-facing. Agents parse stdout to get the path. Rich markup in stdout
  would break that parse.
- Inverting the flag convention matches the inverted consumer intent: other commands are
  human-facing by default, this one is agent-facing by default.
- The `--rich` flag name communicates intent clearly for human callers.

**Alternatives considered**:
- `--raw` flag (same as other commands, but default behavior differs): creates an asymmetric
  API where `--raw` on other commands enables plain text but `--raw` on `current-path` would
  be the default. Rejected — more confusing than `--rich` opt-in.

### ADR-NEW-004: Two-pass JSONL scan for `tools` command

**Context**: `tool_use` blocks are in assistant records; `tool_result` blocks are in user
records. Matching them requires seeing both sides.

**Decision**: Two-pass approach: Pass 1 collects `{tool_use_id -> tool_name}` from assistant
records; Pass 2 correlates `tool_result` blocks from user records against that map.

**Rationale**:
- Single-pass would require lookahead or buffering. Two-pass is simpler and `_iter_records()`
  returns all records as a list (already in memory), so two passes over the same list have no
  I/O cost.
- The same two-pass approach is used inside `cmd_errors` for tool name resolution.

---

## 10. Scalability Strategy

### Memory

`_iter_records()` reads the entire JSONL file into a `list[dict]` before processing. For large
sessions (10,000+ records), this is the existing bottleneck — unchanged by this feature. The
new commands add no additional memory allocations beyond the per-command aggregation dicts
(`ToolStats`, etc.), which are bounded by the number of distinct tool names.

### Async

Not applicable. All new commands are synchronous. JSONL parsing and DuckDB queries complete
in milliseconds for typical session files (<50 MB). No async patterns are needed.

### Large sessions

The stuck-loop detection in `irritation` processes records in a single linear pass (O(n) in
record count). Tool-input hash computation adds negligible cost per record.

### `current-path` performance

`current-path` performs no DuckDB query and no JSONL parse — it is a pure filesystem stat
check. Performance is bounded by one `Path.exists()` call.

---

## Appendix: Rich Table Width Pattern

All Rich table output in new commands follows the existing `_get_table_width` pattern already
in `session_query.py`:

```python
# Existing helper (already in file — do not duplicate)
def _get_table_width(table: Table) -> int:
    temp_console = Console(width=9999)
    measurement = Measurement.get(temp_console, temp_console.options, table)
    return int(measurement.maximum)

# Apply before every stdout.print(table, ...)
table.width = _get_table_width(table)
stdout.print(table, crop=False, overflow="ignore", no_wrap=True, soft_wrap=True)
```

The `tools` command is the only new command that renders a Rich table. `errors` and
`irritation` use sectioned text output, not tables.
