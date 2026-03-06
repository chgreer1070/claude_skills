# Architecture: Migrate SAM Task Tracking to GitHub Sub-Issues

**Generated**: 2026-03-06
**Feature**: migrate-sam-task-github-subissues
**Input documents**:
- `plan/feature-context-migrate-sam-task-github-subissues.md`
- `plan/codebase/sam-task-migration.md`
- `.claude/skills/backlog/backlog_core/github.py` (lines 450-581)
- `.claude/skills/backlog/backlog_core/models.py` (lines 233-263)
- `.claude/skills/backlog/backlog_core/parsing.py` (lines 873-968)
- `.claude/skills/backlog/backlog_core/server.py`
- `.claude/skills/backlog/backlog_core/operations.py`
- `plugins/python3-development/skills/implementation-manager/scripts/implementation_manager.py`
- `plugins/python3-development/skills/implementation-manager/scripts/task_status_hook.py`

---

## 1. Overview and Design Summary

### Problem Being Solved

The SAM implementation workflow maintains two disconnected tracking systems: GitHub Issues (story level, via backlog MCP) and local `plan/tasks-*.md` files (task level, via `implementation_manager.py` and `task_status_hook.py`). Task status in local markdown can diverge from GitHub, making per-task progress invisible from the GitHub UI.

### Outcome After This Work

Each SAM task appears as a GitHub sub-issue under its parent story issue. Task progress is visible in GitHub. The backlog MCP exposes MCP tools to create, query, and update task sub-issues. `implementation_manager.py` can query GitHub sub-issues (via local cache) in addition to local YAML files. `task_status_hook.py` syncs task completion to GitHub on `SubagentStop`. Offline operation is preserved — local YAML files remain the primary write target and serve as the cache.

### Phase Boundaries

- **Phase 1** (COMPLETE, commit 30066de): `SamTask` model, `parse_sam_task_metadata`, `build_sam_task_body`, `build_sam_task_issue_title`, `create_task_issue`, `get_task_issues`, `update_task_status` in `github.py`.
- **Phase 2** (this spec): MCP tool exposure in `server.py` via `operations.py` intermediary.
- **Phase 3** (this spec): `--github` flag on `implementation_manager.py` `status` and `ready-tasks` commands.
- **Phase 4** (this spec): GitHub sync in `task_status_hook.py` `SubagentStop` handler.
- **Phase 5** (this spec): Skill doc updates for `implement-feature` and `start-task`.

### Confirmed Design Decisions

| Decision | Resolution |
|----------|-----------|
| Dependency model | Option B: deps stored as task IDs in `<!-- sam:task -->` YAML block; `get_ready_tasks()` stays local |
| Offline strategy | Local files are cache; PostToolUse writes local only; SubagentStop writes local + GitHub |
| Preview API risk | Accepted — build now, fall back to body cross-refs if sub-issues unavailable |
| Cache location | `.claude/context/sam-tasks-{feature_slug}.json` keyed by feature slug |
| GitHub dependency in `implementation_manager.py` | `backlog_core` added to `sys.path` — same pattern as `task_format.py` |
| Error handling on GitHub failure during SubagentStop | Log warning, exit 0 — local completion is authoritative, GitHub sync is best-effort |
| `operations.py` intermediary | Required — new MCP tools call through `operations.py`, not directly into `github.py` |
| `github_issue` field in task YAML | Required — added to YAML frontmatter so hook can call `update_task_status` by issue number |

## 2. Data Model Changes

### 2.1 `SamTask` Model — No Changes

`SamTask` (`models.py:233-263`) is complete from Phase 1. No new fields required. The `dependencies` list already supports within-feature task IDs (`["T1", "T2"]`) and cross-feature GitHub issue refs (`["#479"]`).

### 2.2 Local Task YAML Frontmatter — One New Field

The `plan/tasks-*.md` YAML frontmatter for each task gains one new optional field:

```yaml
github_issue: 479
```

This field is populated by `task_status_hook.py` after `create_task_issue()` returns the created issue number. It is read by `task_status_hook.py` `SubagentStop` handler to call `update_task_status(repo, issue_number, "complete")` without needing to search GitHub by title.

**Field contract**:

- Type: `int | None` — absent when no GitHub sub-issue has been created yet
- Written by: `task_status_hook.py` after `create_task_issue()` succeeds, or by the migration script
- Read by: `task_status_hook.py` `SubagentStop`, `implementation_manager.py` `--github` flag path
- Never written by: `get_ready_tasks()`, `handle_activity_update()`, or any read-only query path

### 2.3 Active-Task Context File — One New Field

`.claude/context/active-task-{CLAUDE_SESSION_ID}.json` gains one new optional field:

```json
{
  "task_file_path": "plan/tasks-001-slug/T1.md",
  "task_id": "T1",
  "parent_issue_number": 480
}
```

**Field contract**:

- Type: `int | None` — absent when no parent story issue is associated
- Written by: `/start-task` SKILL.md step 5 (extended)
- Read by: `task_status_hook.py` `SubagentStop` handler via `get_parent_issue_number()` helper
- Purpose: Enables the hook to call `update_task_status()` without re-parsing the prompt

### 2.4 GitHub Sub-Issue Cache File

A new per-feature cache file stores the last-known state of GitHub sub-issues:

```text
.claude/context/sam-tasks-{feature_slug}.json
```

**Structure**:

```json
{
  "feature_slug": "migrate-sam-task-github-subissues",
  "parent_issue_number": 480,
  "synced_at": "2026-03-06T12:00:00+00:00",
  "tasks": [
    {
      "issue_number": 481,
      "task_id": "T1",
      "status": "not-started",
      "agent": "context-gathering",
      "priority": 1,
      "skills": ["python3-development"],
      "dependencies": []
    }
  ]
}
```

**Lifecycle**:

- Created/updated by: `get_ready_sam_tasks` MCP tool (after calling `get_task_issues`) and `implementation_manager.py --github` flag path
- Read by: `implementation_manager.py --github` flag path when offline (GitHub unavailable)
- Updated on: every successful call to `get_task_issues()`
- Not used by: PostToolUse handler (reads local YAML only)

### 2.5 Dependency Format Mapping

`Task.dependencies` (local YAML, used by `get_ready_tasks()`) uses task IDs: `["T1", "T2"]`.
`SamTask.dependencies` (GitHub body YAML) uses task IDs for within-feature and `#N` for cross-feature.

When populating `Task.dependencies` from a GitHub sub-issue's `SamTask`, the implementation agent must:

1. Pass through within-feature IDs unchanged: `"T1"` remains `"T1"`
2. For cross-feature `"#479"` references: these are cross-feature deps and are treated as always-satisfied by `get_ready_tasks()` (they resolve to `None` in `status_by_id`, and `None not in _TERMINAL_STATUSES` evaluates to `True` — this is the existing behavior for unknown dep IDs)

No conversion logic is required. The existing `get_ready_tasks()` already handles unknown dep IDs gracefully.

## 3. Interface Contracts

All signatures below are contracts only — no function bodies. Implementation agents apply standard patterns from each module's existing conventions.

### 3.1 Phase 2: New Functions in `operations.py`

These three functions form the intermediary layer between `server.py` and `github.py`. Each follows the existing `operations.py` contract: accept typed args + `Output | None`, call `get_github()` or `try_get_github()` as appropriate, return `dict`.

```python
def create_sam_task(
    parent_issue_number: int,
    task_id: str,
    feature: str,
    task_type: str,
    agent: str,
    priority: int,
    skills: list[str],
    dependencies: list[str],
    description: str,
    acceptance_criteria: list[str] | None,
    labels: list[str] | None,
    output: Output | None = None,
) -> dict:
    """Create a GitHub sub-issue for a SAM task under a parent story issue.

    Calls get_github() — raises GitHubUnavailableError if GitHub is unreachable.
    On success, returns {"issue_number": N, "title": "...", "url": "..."}.
    On partial failure (issue created but sub-issue link failed), returns
    {"issue_number": N, "title": "...", "url": "...", "warnings": [...]}.
    """
    ...
```

```python
def get_sam_tasks(
    parent_issue_number: int,
    refresh_cache: bool = True,
    output: Output | None = None,
) -> dict:
    """Return all sub-issues for a parent story issue as SamTask dicts.

    Calls try_get_github() — returns empty task list with a warning if offline.
    Each task dict mirrors SamTask fields plus "issue_number" and "issue_url".
    Return shape: {"tasks": [...], "count": N, "parent_issue_number": N}.
    If refresh_cache=True, writes the cache file at
    .claude/context/sam-tasks-{feature_slug}.json after a successful fetch.
    feature_slug is derived from the first task's SamTask.feature field; if no
    tasks exist, the cache write is skipped.
    """
    ...
```

```python
def update_sam_task_status(
    issue_number: int,
    new_status: str,
    output: Output | None = None,
) -> dict:
    """Update the status field in a task sub-issue's sam:task block.

    Calls get_github() — raises GitHubUnavailableError if GitHub is unreachable.
    Delegates to github.update_task_status().
    Return shape: {"updated": bool, "issue_number": N, "new_status": "..."}.
    Returns {"updated": False} without error when status already matches.
    """
    ...
```

```python
def get_ready_sam_tasks(
    parent_issue_number: int,
    output: Output | None = None,
) -> dict:
    """Return tasks ready for execution from GitHub sub-issues.

    Calls try_get_github(). If offline, reads from cache file at
    .claude/context/sam-tasks-{feature_slug}.json. If cache is absent, returns
    empty list with a warning.
    Dependency resolution uses the same get_ready_tasks() logic from
    implementation_manager.py applied to the fetched task list.
    Return shape mirrors implementation_manager.py ready-tasks output:
    {"feature": "slug", "ready_tasks": [...], "count": N}.
    Each ready_task dict: {"id": "T1", "name": "...", "agent": "...", "skills": [...],
    "issue_number": N}.
    """
    ...
```

### 3.2 Phase 2: New MCP Tools in `server.py`

Each tool follows the `server.py` invariants: `async def`, `Annotated` params with `Field(description=...)`, `Output()`, `asyncio.to_thread()`, return `{**result, **out.to_dict()}`, catch `BacklogError`.

```python
@mcp.tool()
async def backlog_create_sam_task(
    parent_issue_number: Annotated[int, Field(description="Parent story issue number (without #)")],
    task_id: Annotated[str, Field(description="Feature-scoped task ID, e.g. 'T1'")],
    feature: Annotated[str, Field(description="Feature slug, e.g. 'my-feature'")],
    task_type: Annotated[str, Field(description="Task category: research | implement | review | fix | docs")],
    agent: Annotated[str, Field(description="Agent name to execute this task")],
    priority: Annotated[int, Field(description="Priority 1-5 (1=highest)")] = 2,
    skills: Annotated[list[str], Field(description="Skill names for the executing agent")] = [],
    dependencies: Annotated[list[str], Field(description="Task IDs this task depends on")] = [],
    description: Annotated[str, Field(description="Human-readable description of the task")] = "",
    acceptance_criteria: Annotated[list[str] | None, Field(description="Acceptance criteria strings")] = None,
    labels: Annotated[list[str] | None, Field(description="GitHub label names to apply")] = None,
) -> dict:
    """Create a GitHub sub-issue for a SAM task under a parent story issue.

    Use this to bootstrap GitHub visibility for a task when starting a new feature plan.
    Returns issue_number, title, url, and output messages. On error, returns error key.
    """
    ...
```

```python
@mcp.tool()
async def backlog_get_sam_tasks(
    parent_issue_number: Annotated[int, Field(description="Parent story issue number (without #)")],
    refresh_cache: Annotated[bool, Field(description="Write updated cache after fetching")] = True,
) -> dict:
    """Return all SAM task sub-issues for a parent story issue.

    Returns tasks list with SamTask fields plus issue_number and issue_url.
    Falls back to local cache if GitHub is unavailable.
    Use this to inspect per-task status from the GitHub source of truth.
    """
    ...
```

```python
@mcp.tool()
async def backlog_update_sam_task_status(
    issue_number: Annotated[int, Field(description="Task sub-issue number (without #)")],
    new_status: Annotated[str, Field(description="Target status: not-started | in-progress | complete | blocked")],
) -> dict:
    """Update the status field in a SAM task sub-issue.

    Patches the sam:task YAML block in the issue body. No-op if status already matches.
    Use this to sync local task completion state to GitHub.
    Returns updated (bool), issue_number, new_status.
    """
    ...
```

```python
@mcp.tool()
async def backlog_get_ready_sam_tasks(
    parent_issue_number: Annotated[int, Field(description="Parent story issue number (without #)")],
) -> dict:
    """Return SAM tasks ready for execution from GitHub sub-issues.

    Fetches sub-issues, resolves dependency graph locally, returns tasks whose
    status is not-started and all dependencies are terminal.
    Output shape matches implementation_manager.py ready-tasks JSON:
    {"feature": "slug", "ready_tasks": [...], "count": N}.
    Each ready_task includes id, name, agent, skills, issue_number.
    Falls back to local cache if GitHub is unavailable.
    """
    ...
```

### 3.3 Phase 3: `implementation_manager.py` Extensions

The `sys.path` insertion pattern (already used for `task_format`) is extended for `backlog_core`:

```python
# After existing task_format sys.path insert:
_BACKLOG_CORE = Path(__file__).resolve().parents[6] / ".claude" / "skills" / "backlog" / "backlog_core"
if _BACKLOG_CORE.exists():
    sys.path.insert(0, str(_BACKLOG_CORE.parent))
```

Two new optional parameters added to `status` and `ready-tasks` commands:

```python
@app.command(name="ready-tasks")
def ready_tasks(
    project_path: ProjectPath,
    feature_slug: FeatureSlug,
    github: Annotated[bool, typer.Option("--github", help="Query GitHub sub-issues instead of local files")] = False,
    parent_issue: Annotated[int | None, typer.Option("--parent-issue", help="Parent story issue number")] = None,
) -> None: ...
```

```python
@app.command(name="status")
def status(
    project_path: ProjectPath,
    feature_slug: FeatureSlug,
    github: Annotated[bool, typer.Option("--github", help="Include GitHub sub-issue state")] = False,
    parent_issue: Annotated[int | None, typer.Option("--parent-issue", help="Parent story issue number")] = None,
) -> None: ...
```

New internal function — signature only, no body:

```python
def fetch_tasks_from_github(
    parent_issue_number: int,
    feature_slug: str,
    cache_path: Path,
) -> list[Task] | None:
    """Fetch sub-issues from GitHub and return as Task objects for get_ready_tasks().

    Returns None when GitHub is unavailable. When None is returned, caller falls
    back to reading local YAML files. On success, writes the cache file at
    cache_path before returning.

    Dependency conversion: SamTask.dependencies strings are passed through as-is
    to Task.dependencies. Cross-feature "#N" refs are left as-is; get_ready_tasks()
    treats unknown dep IDs as satisfied (existing behavior).
    """
    ...
```

### 3.4 Phase 4: `task_status_hook.py` Extensions

New helper function — signature only:

```python
def get_parent_issue_number(hook_input: dict[str, Any]) -> int | None:
    """Read parent_issue_number from the active-task context file.

    Returns the integer issue number, or None if the field is absent or the
    context file does not exist. Never raises — all failures return None.
    """
    ...
```

New function added after the existing local write in `handle_subagent_stop`:

```python
def sync_completion_to_github(
    task_file_path: Path,
    task_id: str,
    parent_issue_number: int | None,
) -> None:
    """Sync task completion status to GitHub sub-issue.

    Reads github_issue field from the task YAML frontmatter. If absent and
    parent_issue_number is provided, skips with a warning (issue number unknown).
    Calls update_task_status() from backlog_core.github. Wraps all GitHub calls
    in try/except — failure logs a warning to stderr and returns without raising.
    This function is always called after the local write succeeds; GitHub failure
    does not affect hook exit code.
    """
    ...
```

`handle_subagent_stop` call order after this change:

1. Parse prompt / fallback to context file (unchanged)
2. Resolve task file path (unchanged)
3. Write `status: complete` + `completed:` timestamp to local YAML (unchanged)
4. Delete context file (unchanged)
5. Call `sync_completion_to_github(resolved_path, task_id, get_parent_issue_number(hook_input))` (new)

### 3.5 Phase 5: Skill Doc Update Contracts

**`.claude/skills/implement-feature/SKILL.md` step 2 (ready-tasks query)**:

Replace the current CLI invocation text with a conditional block:

```text
If parent story issue number is known:
  Prefer MCP: backlog_get_ready_sam_tasks(parent_issue_number=N)
  Output shape: {"feature": "...", "ready_tasks": [...], "count": N}
  Falls back to local cache if GitHub unavailable.

If parent issue number is unknown (or MCP unavailable):
  CLI fallback: uv run implementation_manager.py ready-tasks . {slug}
  With GitHub flag: uv run implementation_manager.py ready-tasks . {slug} --github --parent-issue N
```

**`.claude/skills/start-task/SKILL.md` step 5 (context file write)**:

Extend the context file write instructions to include `parent_issue_number`:

```text
Write .claude/context/active-task-{CLAUDE_SESSION_ID}.json:
{
  "task_file_path": "plan/tasks-001-slug/T1.md",
  "task_id": "T1",
  "parent_issue_number": N  // omit if not known; hook treats absence as None
}
```

Both `.claude/skills/` and `plugins/python3-development/skills/development/` copies must be updated.

## 4. Module Interaction Diagram

### Read Path (orchestrator querying ready tasks)

```text
implement-feature SKILL.md (orchestrator)
    |
    |-- [MCP preferred] backlog_get_ready_sam_tasks(parent_issue_number=N)
    |       |
    |       v
    |   server.py: backlog_get_ready_sam_tasks()
    |       |
    |       v
    |   operations.py: get_ready_sam_tasks(parent_issue_number)
    |       |
    |       |-- try_get_github() --> github.py: get_task_issues(repo, parent)
    |       |       |-- [online]  returns list[SubIssue]
    |       |       |             each SubIssue.body -> parse_sam_task_metadata() -> SamTask
    |       |       |             writes .claude/context/sam-tasks-{slug}.json
    |       |       |-- [offline] returns [] with warning
    |       |                     reads .claude/context/sam-tasks-{slug}.json (cache)
    |       |
    |       v
    |   operations.py: converts SamTask list -> Task list -> get_ready_tasks() [unchanged]
    |       |
    |       v
    |   returns {"feature": "...", "ready_tasks": [...], "count": N}
    |
    |-- [CLI fallback] uv run implementation_manager.py ready-tasks . {slug} [--github --parent-issue N]
            |
            |-- [--github flag] fetch_tasks_from_github(parent_issue_number, slug, cache_path)
            |       |-- imports backlog_core.github via sys.path insert
            |       |-- [online]  get_task_issues() -> SamTask -> Task
            |       |             writes .claude/context/sam-tasks-{slug}.json
            |       |-- [offline] reads .claude/context/sam-tasks-{slug}.json
            |       |-- [no flag] reads local plan/tasks-*.md YAML (existing path, unchanged)
            |
            v
        get_ready_tasks(tasks) [unchanged] -> JSON output
```

### Write Path (task completion)

```text
task_status_hook.py (SubagentStop event)
    |
    1. parse prompt -> (task_file_path, task_id)  [unchanged]
    2. fallback to .claude/context/active-task-{sid}.json  [unchanged]
    3. _resolve_task_file(full_path, task_id)  [unchanged]
    4. write local YAML: status=complete, completed=timestamp  [unchanged]
    5. delete context file  [unchanged]
    6. sync_completion_to_github(resolved_path, task_id, parent_issue_number)  [NEW]
            |
            |-- read github_issue field from task YAML frontmatter
            |-- if absent: log warning, return (no GitHub call)
            |-- if present: import backlog_core.github via sys.path
            |-- get_github() -> repo
            |-- update_task_status(repo, issue_number, "complete")
            |       |-- [success] out.info(...); return True
            |       |-- [GithubException] caught inside update_task_status -> out.warn(...)
            |-- any exception wrapping: log to stderr, return (never re-raise)
    |
    exit 0 (GitHub failure does not change exit code)
```

### Write Path (task claim / start)

```text
start-task SKILL.md (sub-agent)
    |
    1. claim-task CLI -> writes status: in-progress, started: timestamp to local YAML
    |       |-- if claim fails (exit != 0): stop
    |
    2. write .claude/context/active-task-{sid}.json
    |   { "task_file_path": "...", "task_id": "T1", "parent_issue_number": N }
    |
    3. [NEW] if parent_issue_number known AND github_issue field set in task YAML:
    |       import backlog_core.github
    |       update_task_status(repo, issue_number, "in-progress")
    |       [failure: log warning, continue]
    |
    4. execute task (existing path)
```

### Module Dependency Map

```text
server.py
  imports: operations, models.BacklogError, models.Output

operations.py  [NEW: create_sam_task, get_sam_tasks, update_sam_task_status, get_ready_sam_tasks]
  imports: github.get_github, github.try_get_github, github.create_task_issue,
           github.get_task_issues, github.update_task_status
           models.Output, models.BacklogError, models.SamTask
           parsing.parse_sam_task_metadata

github.py  [Phase 1, unchanged for Phases 2-4]
  exports: create_task_issue, get_task_issues, update_task_status

models.py  [Phase 1, unchanged]
  exports: SamTask, Output, BacklogError

parsing.py  [Phase 1, unchanged]
  exports: parse_sam_task_metadata, build_sam_task_body

implementation_manager.py  [Phase 3: new --github flag, fetch_tasks_from_github()]
  sys.path adds: scripts/ (task_format) + backlog_core parent dir
  imports (conditional on --github): backlog_core.github.get_task_issues, try_get_github
  core logic: get_ready_tasks() unchanged

task_status_hook.py  [Phase 4: new sync_completion_to_github(), get_parent_issue_number()]
  sys.path adds (conditional): backlog_core parent dir
  imports (conditional on github_issue field present): backlog_core.github.get_github, update_task_status
  core logic: handle_subagent_stop(), handle_activity_update() structure unchanged
```

## 5. Error Handling Strategy

### 5.1 Failure Classification

| Failure type | Location | Response |
|---|---|---|
| GitHub unavailable (`try_get_github` returns None) | `operations.get_sam_tasks`, `operations.get_ready_sam_tasks` | `out.warn(...)`, read cache file, return cached data; if no cache, return empty list with warning |
| GitHub unavailable (`get_github` raises `GitHubUnavailableError`) | `operations.create_sam_task`, `operations.update_sam_task_status` | Caught at `server.py` tool boundary; returned as `{"error": str(e), ...}` |
| `GithubException` inside `github.py` functions | Any `github.py` call | Already caught inside `github.py`; recorded via `out.warn(...)`; function returns `None`/`[]`/`False` |
| `github_issue` field absent from task YAML | `task_status_hook.py` `sync_completion_to_github` | Log warning to stderr; return without GitHub call; exit 0 |
| `update_task_status` returns False | `task_status_hook.py` | Log info message ("status already matched or block absent"); exit 0 |
| Any exception in `sync_completion_to_github` | `task_status_hook.py` | Caught by broad `except Exception`; log to stderr; return; exit 0 — local completion is authoritative |
| `backlog_core` not on sys.path (path calculation fails) | `implementation_manager.py --github` path, `task_status_hook.py` | Log warning; fall back to local YAML path or skip GitHub sync |
| Cache file absent when offline | `operations.get_sam_tasks`, `fetch_tasks_from_github` | Return empty list with warning message; caller proceeds with empty task list |
| Cache file malformed JSON | Same as above | Catch `json.JSONDecodeError`; log warning; return empty list |
| Sub-issue created but `add_sub_issue` fails | `github.create_task_issue` | Already handled in Phase 1 — `out.warn(...)`; issue created but not linked |

### 5.2 `operations.py` Error Boundary

`operations.py` functions follow the established convention:

- Call `get_github()` for write operations — raises `GitHubUnavailableError` (a `BacklogError` subclass) when GitHub is unreachable.
- Call `try_get_github()` for read/query operations — returns `None` when GitHub is unreachable; callers handle `None` by reading cache.
- `BacklogError` and subclasses propagate up to `server.py` where they are caught and returned as `{"error": str(e), **out.to_dict()}`.
- GitHub `GithubException` is caught inside `github.py` and surfaced as warnings in `Output`, not as raised exceptions.

### 5.3 Hook Error Boundary

`task_status_hook.py` is constrained by Claude Code's hook exit code semantics:

- Exit 0: success or best-effort (GitHub failure, cache miss)
- Exit 2: hard error that should be surfaced to the agent (task file not found, YAML parse failure)

The GitHub sync step (`sync_completion_to_github`) must always exit 0. It wraps all GitHub operations in `try/except Exception` and logs to stderr. Local task state written before the GitHub sync is never rolled back.

### 5.4 `implementation_manager.py` Error Boundary

When `--github` flag is used:

- If `fetch_tasks_from_github` returns `None` (GitHub unavailable): fall back to local file read with a warning printed to stderr. The JSON output is computed from local files; no error key is emitted.
- If both GitHub and cache are unavailable and no local files exist: emit `{"error": "No task data available — GitHub unreachable and no cache found", ...}` and exit 1.
- If `backlog_core` path cannot be resolved (directory not found): emit warning, fall back to local files.

### 5.5 Preview API Fallback Trigger

If `parent.get_sub_issues()` raises `GithubException` with a message indicating the API is unavailable (HTTP 404 or 422 with "sub_issues" in the message body), `get_task_issues()` returns an empty list and records the warning. The caller sees an empty task list and falls back to cache or local files. No automatic switching to Option A (body cross-refs) is implemented — that is a manual operator decision.

## 6. Migration Strategy

Migration is in scope as an explicit script (`migrate_tasks_to_github.py`) that the operator runs once per in-flight feature. Auto-migration on first `implement-feature` invocation is explicitly out of scope — the risk of creating duplicate sub-issues on repeated invocations outweighs the convenience.

### 6.1 Script Location and Invocation

```text
plugins/python3-development/scripts/migrate_tasks_to_github.py
```

```bash
uv run plugins/python3-development/scripts/migrate_tasks_to_github.py \
  --task-file plan/tasks-001-my-feature/  \
  --parent-issue 480                       \
  [--dry-run]                              \
  [--label sam-task]
```

### 6.2 Script Algorithm

```text
1. Read task file(s) via parse_task_file() from implementation_manager.py logic
2. For each task in dependency order (topological sort by task.dependencies):
   a. If task YAML already has github_issue: N field, skip (already migrated)
   b. Build SamTask from Task fields:
      - task_id = task.id
      - feature = derived from task file path (slug)
      - task_type = "implement" (default — YAML may not have task_type field)
      - agent = task.agent
      - priority = task.priority
      - skills = task.skills
      - dependencies = task.dependencies (pass through as-is)
      - status = task.status value (already a valid SamTask status string)
   c. Call create_task_issue(repo, parent_issue_number, sam_task, description="", ...)
   d. On success: write github_issue: N back to task YAML frontmatter
   e. On failure: log warning, continue (partial migration is acceptable)
3. Write .claude/context/sam-tasks-{slug}.json cache from created issues
4. Print summary: N created, M skipped (already had github_issue), K failed
```

### 6.3 Idempotency

The `github_issue` field in task YAML frontmatter serves as the idempotency key. The script skips any task that already has this field set. This means re-running the script after a partial failure is safe — only the tasks that failed on the first run are retried.

### 6.4 Dependency Ordering

The migration script processes tasks in topological order so that dependency references within the GitHub body are populated with real issue numbers where possible. If a dependency's issue number is not yet known (migration failed for that task), the dependency is left as the task ID string (e.g., `"T1"`) in the sub-issue body. This matches the `SamTask.dependencies` format for within-feature deps.

### 6.5 Task Type Inference

Local task YAML does not have a `task_type` field. The migration script infers `task_type` from the task title heuristically:

- Title contains "research", "investigate", "explore" → `"research"`
- Title contains "implement", "add", "build", "create" → `"implement"`
- Title contains "review", "audit", "check" → `"review"`
- Title contains "fix", "repair", "correct" → `"fix"`
- Title contains "doc", "update skill" → `"docs"`
- Default → `"implement"`

This inference is best-effort. The human-visible issue title and body are more authoritative than the YAML `task_type` field.

### 6.6 `--dry-run` Mode

When `--dry-run` is passed, the script prints what it would do (task IDs, inferred task types, parent issue number) without making any GitHub API calls or writing any files.

## 7. Testing Strategy

### 7.1 Unit Tests for Phase 2 (`operations.py`)

**File**: `tests/test_backlog_core/test_operations_sam.py` (new file)

**Required test cases**:

| Test | What it verifies |
|---|---|
| `test_create_sam_task_success` | Returns `{"issue_number": N, "title": "...", "url": "..."}` when `create_task_issue` returns an Issue mock |
| `test_create_sam_task_github_unavailable` | Raises `GitHubUnavailableError` when `get_github()` raises; caught at server boundary |
| `test_create_sam_task_link_failure` | Returns result with `warnings` key when `add_sub_issue` fails (partial success) |
| `test_get_sam_tasks_online` | Returns task list with correct SamTask fields when `get_task_issues` returns sub-issues |
| `test_get_sam_tasks_offline_with_cache` | Returns cached task list when `try_get_github()` returns None and cache file exists |
| `test_get_sam_tasks_offline_no_cache` | Returns `{"tasks": [], "count": 0, "warnings": [...]}` when offline and no cache |
| `test_get_sam_tasks_writes_cache` | Cache file at `.claude/context/sam-tasks-{slug}.json` is written after successful fetch |
| `test_update_sam_task_status_success` | Returns `{"updated": True, "issue_number": N}` |
| `test_update_sam_task_status_no_change` | Returns `{"updated": False}` when status already matches |
| `test_get_ready_sam_tasks_dep_resolution` | Returns only tasks with terminal dependencies; uses same logic as `get_ready_tasks()` |
| `test_get_ready_sam_tasks_cross_feature_dep` | Cross-feature `#N` dep treated as satisfied (unknown dep ID → terminal) |

**Mock strategy**: Use `pytest-mock`'s `mocker.patch` to mock `get_github`, `try_get_github`, `create_task_issue`, `get_task_issues`, `update_task_status`. Pass `spec=` when mocking PyGitHub objects to catch attribute access errors.

### 7.2 Unit Tests for Phase 2 (`server.py` MCP tools)

**File**: `tests/test_backlog_core/test_server_sam.py` (new file)

Use FastMCP's test client or direct async invocation of tool functions.

| Test | What it verifies |
|---|---|
| `test_backlog_create_sam_task_returns_dict` | Tool returns dict (not raises) on success |
| `test_backlog_create_sam_task_error_key` | Tool returns `{"error": "..."}` when `create_sam_task` raises `BacklogError` |
| `test_backlog_get_sam_tasks_shape` | Returns `{"tasks": [...], "count": N}` |
| `test_backlog_update_sam_task_status_no_op` | Returns `{"updated": False}` when status unchanged |
| `test_backlog_get_ready_sam_tasks_shape` | Returns shape matching `implementation_manager.py ready-tasks` output |

### 7.3 Unit Tests for Phase 3 (`implementation_manager.py`)

**File**: `tests/test_implementation_manager/test_github_flag.py` (new file)

| Test | What it verifies |
|---|---|
| `test_ready_tasks_no_flag_unchanged` | `--github` absent → reads local YAML files; no `backlog_core` import |
| `test_ready_tasks_github_online` | `--github` → calls `fetch_tasks_from_github`; returns same JSON shape as local path |
| `test_ready_tasks_github_offline_with_cache` | `--github` + offline → reads cache; returns valid JSON |
| `test_ready_tasks_github_offline_no_cache_no_local` | `--github` + offline + no local files → `{"error": "..."}` in output, exit 1 |
| `test_ready_tasks_github_writes_cache` | Cache file is written after successful GitHub fetch |
| `test_status_github_flag` | `status --github` includes `github_issue` field in each task dict |
| `test_backlog_core_path_not_found` | When `backlog_core` dir absent → falls back to local files with warning |

### 7.4 Unit Tests for Phase 4 (`task_status_hook.py`)

**File**: `tests/test_task_status_hook/test_github_sync.py` (new file)

| Test | What it verifies |
|---|---|
| `test_sync_completion_called_after_local_write` | `sync_completion_to_github` is called after local YAML write (order matters) |
| `test_sync_completion_no_github_issue_field` | When task YAML has no `github_issue`, GitHub is not called; exit 0 |
| `test_sync_completion_github_success` | `update_task_status(repo, N, "complete")` called with correct args |
| `test_sync_completion_github_exception` | `GithubException` caught; exit 0; warning in stderr |
| `test_sync_completion_get_github_unavailable` | `GitHubUnavailableError` caught; exit 0; warning in stderr |
| `test_get_parent_issue_number_from_context` | Returns int when `parent_issue_number` key present in context file |
| `test_get_parent_issue_number_absent` | Returns None when key absent or context file missing |
| `test_activity_update_no_github_call` | PostToolUse handler never imports `backlog_core` or calls `update_task_status` |

### 7.5 Integration Test: SubagentStop → GitHub Sync

**File**: `tests/test_task_status_hook/test_subagent_stop_integration.py`

This test exercises the full `handle_subagent_stop` path including GitHub sync against a mocked `backlog_core.github` module.

**Scenario**:

1. Create a temp task YAML file with `github_issue: 481` and status `in-progress`
2. Create a temp context file with `parent_issue_number: 480`
3. Construct a hook input dict with `hook_event_name: SubagentStop` and a prompt containing `/start-task {path} --task T1`
4. Patch `backlog_core.github.get_github` to return a mock repo
5. Patch `backlog_core.github.update_task_status` to return True
6. Call `handle_subagent_stop(hook_input)` directly
7. Assert: local YAML status is `complete`, `completed` field is set, context file deleted, `update_task_status` called once with `(mock_repo, 481, "complete")`

**Edge case variant**: Repeat with `update_task_status` raising `GithubException` — assert exit 0, local YAML still updated, warning on stderr.

### 7.6 Migration Script Tests

**File**: `tests/test_migrate_tasks_to_github.py` (new file)

| Test | What it verifies |
|---|---|
| `test_dry_run_no_writes` | `--dry-run` produces no API calls and no file writes |
| `test_skips_already_migrated` | Tasks with `github_issue` field are not re-created |
| `test_writes_github_issue_field` | After create, YAML frontmatter has `github_issue: N` |
| `test_task_type_inference` | Titles map to correct task_type values |
| `test_partial_failure_continues` | One `create_task_issue` failure does not abort remaining tasks |
| `test_writes_cache_file` | `.claude/context/sam-tasks-{slug}.json` written after migration |

## 8. Constraints and Non-Goals

### 8.1 Explicitly Unchanged

These components must not be modified during Phases 2-5:

| Component | Why frozen |
|---|---|
| `get_ready_tasks(tasks: list[Task]) -> list[Task]` in `implementation_manager.py` | Algorithm is correct. Input source changes; function body does not. |
| `SamTask` model in `models.py` | Phase 1 complete. Any model change requires a separate ADR. |
| `parse_sam_task_metadata`, `build_sam_task_body`, `build_sam_task_issue_title` in `parsing.py` | Phase 1 complete. |
| `create_task_issue`, `get_task_issues`, `update_task_status` in `github.py` | Phase 1 complete. |
| `task_format.py` | Shared module; changes affect both `implementation_manager.py` and `task_status_hook.py`. |
| `TaskStatus`, `Task`, `TaskPriority` dataclasses in `implementation_manager.py` | Internal types; changing them breaks the existing local-file path. |
| `handle_activity_update` (PostToolUse) in `task_status_hook.py` | No GitHub call on keystroke. This is a hard latency constraint. |
| `claim-task` command in `implementation_manager.py` | Atomic local write; no GitHub side-effect added. GitHub claim sync is out of scope. |

### 8.2 Non-Goals

- **GitHub Projects v2**: Integration with GitHub Projects boards is out of scope (Option C rejected).
- **Removing local task files**: Local YAML files remain as the primary cache and write target. They are not replaced by GitHub sub-issues.
- **Real-time bidirectional sync**: Only push-on-completion is implemented. Pull-on-startup is provided by the `--github` flag and MCP tools; it is not automatic.
- **Atomic claim-task + GitHub sync**: `claim-task` marks in-progress locally. GitHub sync for in-progress state is triggered by `/start-task` as a best-effort call — not as part of `claim-task` atomicity.
- **Webhook-driven cache invalidation**: No webhook setup. Cache is updated by explicit MCP tool calls or `--github` flag invocations.
- **Task deletion from GitHub**: No MCP tool to delete sub-issues. Deferred and skipped tasks remain as open GitHub issues (reflecting their status via the `sam:task` block).
- **Re-ordering sub-issues by priority**: `priority_position` in `get_task_issues()` reflects the order GitHub assigned on creation. Reordering is out of scope.
- **Multiple repo support**: All operations target `DEFAULT_REPO` from `models.py`. Multi-repo SAM workflows are out of scope.
- **Changing dependency format**: `SamTask.dependencies` continues to use task IDs and `#N` cross-feature refs. Switching to sub-issue number references within the same feature is out of scope.

### 8.3 Constraints

- **`ruamel.yaml` only**: All YAML reads and writes use `ruamel.yaml`. `pyyaml` (`import yaml`) is forbidden per repository convention.
- **No `shell=True`**: Subprocess calls (if any are added in migration script) must not use `shell=True`.
- **`backlog_core` import is conditional**: Both `implementation_manager.py` and `task_status_hook.py` must remain runnable without `backlog_core` present. The import must be guarded by a path existence check (`if _BACKLOG_CORE.exists(): sys.path.insert(...)`). Failure to import logs a warning and falls back to local behavior.
- **Hook exit codes are contract**: `task_status_hook.py` exit 0 = success or advisory failure; exit 2 = hard error for agent visibility. GitHub sync failure is always exit 0.
- **Two-copy skill constraint**: `.claude/skills/implement-feature/SKILL.md` and `plugins/python3-development/skills/development/implement-feature/SKILL.md` are separate files that must be updated identically. Same for `start-task`. There is no symlink or include mechanism.
- **`backlog_core` path calculation**: The relative path from `implementation_manager.py` to `backlog_core` is `../../../../../.claude/skills/backlog/` (6 levels up from `scripts/`). The implementation agent must verify this path against the actual directory structure before writing the `sys.path.insert` call.
