# Dispatch Orchestration Patterns

**Analysis Date:** 2026-03-22
**Package:** development-harness (`plugins/development-harness/`)
**Focus:** Dispatch plan schema, existing dispatch MCP tools, spawn.py interface, server tool registration patterns, PEP 723 dependencies

---

## 1. Existing Dispatch MCP Tools in server.py

**Location:** `plugins/development-harness/backlog_core/server.py:1278–1423`

Four dispatch tools exist today. All follow the same `async def` + `@mcp.tool` pattern used by every other tool in the server.

### `_dispatch_plan_path` helper (private, not a tool)

```python
# server.py:1278-1291
def _dispatch_plan_path(milestone_number: int) -> Path:
    # BACKLOG_DIR is <project_root>/.claude/backlog — walk up to project root
    return _ds.dispatch_plan_path(milestone_number, _models.BACKLOG_DIR.parent.parent)
```

Resolves path from `_models.BACKLOG_DIR` by walking up two levels. This is the single place that couples `dispatch_schema.dispatch_plan_path` to the server's path constants. All four dispatch tools call this helper — new dispatch tools must also call it.

### `dispatch_read` (`server.py:1294–1316`)

```python
@mcp.tool
async def dispatch_read(milestone_number: Annotated[int, Field(description="GitHub milestone number")]) -> dict:
```

- Calls `asyncio.to_thread(_ds.read_dispatch_plan, plan_path)`
- Returns `{"milestone_number": int, "plan_path": str, "plan": plan.model_dump()}`
- Error paths return `{"error": str, "milestone_number": int, "plan_path": str}`
- Catches `FileNotFoundError` and `ValueError` separately (not `BacklogError`)

### `dispatch_validate` (`server.py:1319–1337`)

```python
@mcp.tool
async def dispatch_validate(milestone_number: Annotated[int, Field(description="GitHub milestone number")]) -> dict:
```

- Reads plan then calls `asyncio.to_thread(_ds.validate_plan_integrity, plan)`
- Returns `{"milestone_number": int, "plan_path": str, **dataclasses.asdict(result)}`
- `ValidationResult` is a frozen `@dataclass`; `dataclasses.asdict` is used (not `.model_dump()`)
- Catches `(FileNotFoundError, ValueError)` as a tuple

### `dispatch_stale_check` (`server.py:1340–1377`)

```python
@mcp.tool
async def dispatch_stale_check(
    milestone_number: Annotated[int, Field(description="GitHub milestone number")],
    repo: Annotated[str, Field(description="Repository slug owner/name. Defaults to repo from project")] = "",
) -> dict:
```

- Two-phase: reads plan file, then fetches live milestone issues from GitHub
- Uses a nested `def _fetch_milestone_issue_numbers()` closure wrapped in `asyncio.to_thread`
- Fetches via `_get_github(repo)` → `gh_repo.get_milestone(milestone_number)` → `gh_repo.get_issues(milestone=ms_obj, state="all")`
- Filters out pull requests: `if issue.pull_request is None`
- Returns `{"milestone_number": int, "plan_path": str, **dataclasses.asdict(result)}`
- Catches `GitHubUnavailableError` and bare `Exception` (with `# noqa: BLE001` suppressor)

### `dispatch_conflicts` (`server.py:1380–1423`)

```python
@mcp.tool
async def dispatch_conflicts(
    milestone_number: Annotated[int, Field(description="GitHub milestone number")],
    repo: Annotated[str, Field(description="Repository slug owner/name. Defaults to repo from project")] = "",
) -> dict:
```

- Fetches open issues for the milestone and extracts `## Impact Radius` sections via regex
- Does NOT read a dispatch plan file — it analyzes raw milestone issues
- Returns `{"milestone_number": int, "conflict_groups": [dataclasses.asdict(cg) ...], "count": int}`
- Same GitHub error handling pattern as `dispatch_stale_check`

**Key constraint:** `dispatch_read`, `dispatch_validate`, `dispatch_stale_check` all call `_dispatch_plan_path(milestone_number)` at the top of the function body before any async work. New dispatch tools that need the plan file must follow this pattern.

---

## 2. Tool Registration Pattern in server.py

**Location:** `plugins/development-harness/backlog_core/server.py:71–79` (mcp instance), all `@mcp.tool` declarations throughout

### FastMCP instance

```python
mcp = FastMCP(
    "backlog",
    instructions="...",
    version="0.1.0",
)
```

Server name is `"backlog"`. All tools are registered by decorating async functions with `@mcp.tool`.

### Standard tool skeleton

Every tool in the server follows this structure:

```python
@mcp.tool
async def tool_name(
    param: Annotated[type, Field(description="...")],
    optional_param: Annotated[type, Field(description="...")] = default,
) -> dict:
    """One-sentence summary.

    Detailed usage guidance.

    Returns:
        Dict with field_names and output messages/warnings. On error, dict contains an error key.
    """
    out = Output()
    try:
        result = await asyncio.to_thread(
            operations.some_function,
            param=param,
            output=out,
        )
        return {**result, **out.to_dict()}
    except BacklogError as e:
        return {"error": str(e), **out.to_dict()}
```

**Dispatch tools deviate from this pattern in two ways:**

1. They catch `(FileNotFoundError, ValueError)` instead of `BacklogError` — because `dispatch_schema` raises these, not `BacklogError`.
2. They use `dataclasses.asdict(result)` not `result.model_dump()` — because `ValidationResult` and `StalePlanResult` are `@dataclass(frozen=True)`, not Pydantic models.

### Tools that use `ctx: Context`

Three tools accept a `ctx: Context` parameter from FastMCP for streaming progress notifications (`ctx.info()`, `ctx.warning()`): `backlog_sync`, `backlog_groom`, `backlog_normalize`, `backlog_pull`. The dispatch tools do not use `ctx`. New dispatch tools that need streaming notifications may add `ctx: Context` as the first parameter.

### Parameter annotation convention

All parameters use `Annotated[type, Field(description="...")]`. Optional parameters with defaults are `Annotated[type | None, Field(...)] = None` or `Annotated[type, Field(...)] = default_value`. The `alias` parameter is used when the Python name conflicts with a keyword (`type_`) — e.g. `Field(alias="type")`.

### Return type is always `dict`

No tool returns a typed Pydantic model directly. All tools return `dict`. The `{**result, **out.to_dict()}` spread merges business result fields with `messages`, `warnings`, `errors` lists from `Output`.

---

## 3. dispatch_schema Package

**Location:** `plugins/development-harness/dispatch_schema/`

### Public API (`dispatch_schema/__init__.py:1–55`)

```python
from dispatch_schema import (
    DispatchPlan, WaveItem, Wave, MilestoneHeader, ConflictGroup,
    QualityGates, ItemPriority, ItemStatus,
    CommandResult, GateResult, GateRunMode,
    ValidationResult, StalePlanResult,
    dispatch_plan_path,
    read_dispatch_plan, write_dispatch_plan,
    validate_plan_integrity, detect_stale_plan,
    run_quality_gates,
)
```

The server imports this as `import dispatch_schema as _ds` (`server.py:14`).

### Data models (`dispatch_schema/core/models.py`)

All models inherit `_DispatchBase(BaseModel)` which sets `model_config = ConfigDict(populate_by_name=True, use_enum_values=True)`.

| Model | Key fields |
|---|---|
| `MilestoneHeader` | `number: int`, `title: str`, `integration_branch: str` |
| `ConflictGroup` | `group_id: int`, `reason: str`, `items: list[str]` |
| `WaveItem` | `title: str`, `issue: int`, `priority: ItemPriority`, `conflict_group: int \| None`, `depends_on: list[int]`, `status: ItemStatus` |
| `Wave` | `wave: int`, `parallel: bool`, `items: list[WaveItem]` |
| `QualityGates` | `pre_merge: list[str]`, `post_merge: list[str]` |
| `DispatchPlan` | `milestone: MilestoneHeader`, `conflict_groups: list[ConflictGroup]`, `waves: list[Wave]`, `quality_gates: QualityGates` |
| `CommandResult` | `command: str`, `exit_code: int`, `stdout: str`, `stderr: str`, computed `passed: bool` |
| `GateResult` | `passed: bool`, `results: list[CommandResult]`, `mode: GateRunMode` |

All multi-word fields accept both `snake_case` and `kebab-case` via `AliasChoices`. Example:

```python
integration_branch: str = Field(
    ..., validation_alias=AliasChoices("integration_branch", "integration-branch")
)
```

Enums:

- `ItemPriority(StrEnum)`: `P0`, `P1`, `P2`, `P3`
- `ItemStatus(StrEnum)`: `pending`, `in-progress`, `complete`, `failed`, `skipped`
- `GateRunMode(StrEnum)`: `fail-fast`, `run-all`

### Validator dataclasses (`dispatch_schema/core/validator.py`)

**Not Pydantic** — uses `@dataclass(frozen=True)`:

```python
@dataclass(frozen=True)
class ValidationResult:
    is_valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

@dataclass(frozen=True)
class StalePlanResult:
    is_stale: bool
    added_issues: list[int] = field(default_factory=list)
    removed_issues: list[int] = field(default_factory=list)
    message: str = ""
```

Use `dataclasses.asdict()` to convert to dict for MCP tool responses. Do not call `.model_dump()` on these.

### File path convention (`dispatch_schema/paths.py:11–21`)

```python
def dispatch_plan_path(milestone_number: int, project_root: Path) -> Path:
    return project_root / "plan" / f"milestone-{milestone_number}-dispatch.yaml"
```

Canonical file path: `plan/milestone-{N}-dispatch.yaml`.

### YAML reader (`dispatch_schema/readers/yaml_reader.py`)

Uses `ruamel.yaml` with `typ="rt"` (round-trip mode), `preserve_quotes=True`. Coerces `CommentedMap`/`CommentedSeq` to plain Python types before passing to `DispatchPlan.model_validate()`. Raises `FileNotFoundError` or `ValueError` — not `BacklogError`.

### YAML writer (`dispatch_schema/writers/yaml_writer.py`)

- Uses `ruamel.yaml` with `typ="rt"`, `default_flow_style=False`
- Converts `snake_case` model keys to `kebab-case` via `_keys_to_kebab()` before serializing
- Atomic write: `tempfile.mkstemp` in same directory, then `os.rename`
- Rejects symlinks (path traversal prevention)
- Signature: `write_dispatch_plan(plan: DispatchPlan, path: Path) -> Path`

### Quality gates executor (`dispatch_schema/gates.py`)

```python
def run_quality_gates(
    commands: list[str],
    *,
    mode: GateRunMode = GateRunMode.FAIL_FAST,
    cwd: Path | None = None,
    timeout: float = 300.0,
) -> GateResult:
```

- No `shell=True` — tokenizes with `shlex.split`, resolves via `shutil.which`
- Exit code 127: command not found; exit code 124: timeout (Unix convention)
- `OSError` after successful `which()` lookup propagates — not caught
- `@cache` on `_resolve_executable` — repeated gate runs reuse PATH lookups

---

## 4. backlog_core/models.py — Existing Pydantic Models

**Location:** `plugins/development-harness/backlog_core/models.py`

All models use `pydantic.BaseModel`. The module is standalone (no imports from other `backlog_core` submodules).

### Key models relevant to dispatch

**`Output` (`models.py:430–456`)** — used in every tool:

```python
class Output(BaseModel):
    messages: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)

    def info(self, msg: str) -> None: ...
    def warn(self, msg: str) -> None: ...
    def error(self, msg: str) -> None: ...
    def to_dict(self) -> dict[str, list[str]]: return self.model_dump()
```

**`SamTask` (`models.py:518–550`)** — SAM task metadata:

```python
class SamTask(BaseModel):
    task_id: str = ""
    feature: str = ""
    task_type: str = ""
    status: str = "not-started"
    agent: str = ""
    priority: int = 2
    skills: list[str] = Field(default_factory=list)
    dependencies: list[str] = Field(default_factory=list)
```

**`ArtifactType` (`models.py:556–570`)** — StrEnum, includes `RESEARCH = "research"` added recently.

**Exception hierarchy** (`models.py:292–348`):
```
BacklogError
├── ItemNotFoundError
├── DuplicateItemError
├── GitHubUnavailableError
├── ValidationError
└── BranchConflictError
```

`dispatch_schema` does not raise `BacklogError`. Dispatch tool error handling must catch `(FileNotFoundError, ValueError)` from schema I/O in addition to (or instead of) `BacklogError`.

---

## 5. spawn.py — Interface and JSON Output Format

**Location:** `plugins/development-harness/skills/kage-bunshin/scripts/spawn.py`

### CLI arguments

```
spawn.py [--worktree] [--branch BRANCH] [--model MODEL]
         [--max-budget MAX_BUDGET] [--name NAME]
         [--no-session-persistence] [--output-dir DIR]
         PROMPT
```

| Argument | Type | Default | Purpose |
|---|---|---|---|
| `PROMPT` | positional str | required | Prompt sent to spawned `claude -p` session |
| `--worktree` | flag | False | Create isolated git worktree |
| `--branch` | str | current branch | Branch for worktree creation |
| `--model` | str | `"sonnet"` | Model identifier |
| `--max-budget` | float | None | Max USD spend |
| `--name` | str | first 30 chars of PROMPT | Session display name |
| `--no-session-persistence` | flag | False | Pass to `claude -p` |
| `--output-dir` | Path | `/tmp/kage-bunshin` | Result/error log directory |

### JSON output to stdout

On success, prints one JSON object and exits 0:

```json
{
  "pid": 12345,
  "name": "session display name",
  "worktree": "/path/to/worktree or null",
  "result_file": "/tmp/kage-bunshin/slug-result.json",
  "error_file": "/tmp/kage-bunshin/slug-err.log",
  "model": "sonnet",
  "lock_file": "/path/to/.claude/kage-bunshin.lock or null"
}
```

- `pid`: PID of spawned `claude -p` subprocess (not waited on — fire-and-forget)
- `result_file`: path where the spawned process writes its JSON output (stdout redirect)
- `error_file`: path where the spawned process writes stderr
- `worktree`: null when `--worktree` not passed
- `lock_file`: null when no worktree

### Exit codes

- `0`: Process spawned successfully
- `1`: Fatal error (claude not found, git worktree failed)

### claude command assembled

```python
cmd = ["claude", "-p", "--model", model, "--permission-mode", "auto",
       "--output-format", "json"]
# optional: ["--max-budget-usd", str(max_budget)]
# optional: ["--name", display_name]
# optional: ["--no-session-persistence"]
cmd.append(prompt)
```

### Worktree path convention

Worktrees created at: `{repo_root}/.worktrees/kb-{name_slug}/`

Shared artifacts symlinked into worktree: `.venv`, `node_modules`.

Lock file written to: `{worktree}/.claude/kage-bunshin.lock`

Lock file content:
```json
{
  "session_id": "uuid4-string",
  "parent_pid": 12345,
  "spawned_at": "2026-03-22T...",
  "item": "first 100 chars of prompt",
  "model": "sonnet"
}
```

### PEP 723 metadata

`spawn.py` has minimal PEP 723 metadata — only `requires-python = ">=3.11"`, no external dependencies. It uses stdlib only (`subprocess`, `uuid`, `json`, `pathlib`, `argparse`, `shutil`, `re`, `os`).

---

## 6. PEP 723 Dependencies in run_backlog_server.py

**Location:** `plugins/development-harness/scripts/run_backlog_server.py:1–14`

```python
#!/usr/bin/env -S uv --quiet run --active --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "fastmcp>=3.0.2",
#   "gitpython>=3.1.0",
#   "pygithub>=2.8.1",
#   "pydantic>=2.12.3",
#   "python-frontmatter>=1.1.0",
#   "ruamel.yaml>=0.18.0",
#   "tiktoken>=0.12.0",
#   "typer>=0.21.2",
# ]
# ///
```

**What is NOT listed:** `dispatch_schema` itself. The `dispatch_schema` package is a local package at `plugins/development-harness/dispatch_schema/` and is resolved via `sys.path` manipulation:

```python
plugin_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(plugin_root))
from backlog_core.server import mcp
```

The `plugin_root` is `plugins/development-harness/`. Both `backlog_core` and `dispatch_schema` are subdirectories of this root, so they are importable once `plugin_root` is on `sys.path`.

**`tiktoken`** is listed as a dependency because `server.py` uses it for token-budget auto-pagination in `backlog_list` (`_LIST_TOKEN_BUDGET = 4_400`, `_enc = tiktoken.get_encoding("cl100k_base")`).

Any new MCP tool that needs additional third-party dependencies must add them to this `dependencies` list. Local packages (`dispatch_schema`, `backlog_core`) do not need to be listed — they are resolved through the `sys.path.insert`.

---

## 7. Key Constraints and Conventions Summary

### Import convention for dispatch_schema

```python
import dispatch_schema as _ds
```

Used at `server.py:14`. Access all dispatch schema functions through this alias: `_ds.read_dispatch_plan(...)`, `_ds.validate_plan_integrity(...)`, etc.

### Error handling asymmetry

| Source | Exception raised | Catch pattern in tools |
|---|---|---|
| `operations.*` functions | `BacklogError` subclasses | `except BacklogError as e:` |
| `dispatch_schema` I/O | `FileNotFoundError`, `ValueError` | `except (FileNotFoundError, ValueError) as exc:` |
| GitHub API failures | `GitHubUnavailableError`, bare `Exception` | `except GitHubUnavailableError`, `except Exception # noqa: BLE001` |

### dataclass vs Pydantic model serialization

- `ValidationResult`, `StalePlanResult` → `dataclasses.asdict(result)` (they are `@dataclass`)
- `ArtifactEntry`, `RegisterResult`, `ArtifactContent` → `.model_dump(mode="json")` (they are Pydantic)
- `DispatchPlan` → `.model_dump()` (Pydantic, returns nested dicts)

### YAML library

`ruamel.yaml` throughout — never `pyyaml`. Reader uses `typ="rt"` with `preserve_quotes=True`. Writer uses `typ="rt"` with `default_flow_style=False`. File keys are kebab-case on disk, snake_case in Python models (via `AliasChoices`).

### Atomic writes

`write_dispatch_plan` uses `tempfile.mkstemp` + `os.rename` — never direct open-write. Symlinks at the target path are rejected.

### asyncio pattern for synchronous I/O

All disk and network I/O in tool handlers is wrapped in `asyncio.to_thread(...)`. Tools themselves are `async def`. Blocking I/O is never called directly in the async handler body.

### spawn.py is fire-and-forget

`subprocess.Popen` (not `subprocess.run`). The caller receives the PID immediately; it must poll `result_file` separately to get completion output. There is no wait mechanism in spawn.py itself.

---

*Analysis performed 2026-03-22 by codebase-analyzer agent against actual source files.*
