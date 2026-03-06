# SAM Task Migration — Codebase Analysis

**Analysis Date:** 2026-03-06
**Focus:** GitHub sub-issues migration for SAM task tracking

---

## 1. Current Task Tracking Architecture

### Task File Format

Tasks are stored in local `.md` files using YAML frontmatter. Two organizational structures exist:

- **Single file**: `plan/tasks-{N}-{slug}.md` — one YAML frontmatter block per task, embedded in body, separated by `\n---\n`
- **Directory**: `plan/tasks-{slug}/` — one `{task-id}.md` file per task, each with a single leading YAML frontmatter block

**Required YAML fields per task** (`task_format.py:49-57`, `implementation_manager.py:415`):

```yaml
---
task: T1
title: "Task title"
status: not-started
agent: context-gathering
priority: 2
complexity: medium
dependencies: [T2, T3]
skills:
  - python3-development
started: 2026-03-06T12:00:00+00:00
completed: 2026-03-06T14:00:00+00:00
last_activity: 2026-03-06T13:00:00+00:00
---
```

**Valid status values** (`task_format.py:49-57`): `not-started`, `in-progress`, `complete`, `blocked`, `deferred`, `skipped`, `wont-fix`

**Terminal statuses** (`implementation_manager.py:82`): `complete`, `deferred`, `skipped` — any of these satisfies a dependency.

### How `implementation_manager.py` Queries Task State

**Entry points** (`implementation_manager.py:827-976`):

```bash
# List all features with task files
uv run implementation_manager.py list-features .

# Full status for a feature — returns all tasks with counts
uv run implementation_manager.py status . {slug}

# Ready tasks only — what orchestrator acts on
uv run implementation_manager.py ready-tasks . {slug}

# Validate frontmatter structure
uv run implementation_manager.py validate . {slug}
```

**Readiness logic** (`implementation_manager.py:774-809`):

```python
_TERMINAL_STATUSES = frozenset({TaskStatus.COMPLETE, TaskStatus.DEFERRED, TaskStatus.SKIPPED})

def get_ready_tasks(tasks: list[Task]) -> list[Task]:
    status_by_id = {task.id: task.status for task in tasks}
    ready = []
    for task in tasks:
        if task.status != TaskStatus.NOT_STARTED:
            continue
        deps_satisfied = all(
            status_by_id.get(dep_id) in _TERMINAL_STATUSES
            for dep_id in task.dependencies
        )
        if deps_satisfied:
            ready.append(task)
    return ready
```

This is a **local, in-memory DAG resolution** — all tasks load from disk first, then readiness is computed in O(N). No network calls at query time.

**`ready-tasks` JSON output shape** (`implementation_manager.py:908-914`):

```json
{
  "feature": "slug",
  "ready_tasks": [
    {"id": "T1", "name": "...", "agent": "context-gathering", "skills": ["python3-development"]}
  ],
  "count": 1
}
```

**`claim-task` command** (`implementation_manager.py:1065-1093`): Atomically sets `status: in-progress` and `started: {timestamp}` by writing YAML fields in-place. Returns non-zero exit if task is already claimed. `/start-task` MUST use `claim-task` and check exit code — it must not edit YAML fields directly.

### How `task_status_hook.py` Writes State

The hook receives JSON on stdin from Claude Code's hook events.

**`SubagentStop` event** (`task_status_hook.py:396-447`): Fires when a sub-agent finishes. Parses the sub-agent's prompt for `/start-task` invocations using two regex patterns:

1. Literal: `/start-task {path}.md --task {id}`
2. Skill call: `Skill(skill="start-task", args="{path}.md --task {id}")`

Falls back to reading `.claude/context/active-task-{session_id}.json` if regex fails. On match: writes `status: complete` and `completed: {timestamp}` to the task YAML file, then deletes the context file.

**`PostToolUse` event** (`task_status_hook.py:450-498`): Fires after Write/Edit/Bash tool use. Reads `active-task-{session_id}.json`, updates `last_activity: {timestamp}` in the task YAML. Skips silently if task is already complete.

**Context file location**: `.claude/context/active-task-{CLAUDE_SESSION_ID}.json`

**Context file format**:

```json
{"task_file_path": "plan/tasks-001-slug/T1.md", "task_id": "T1"}
```

Written by `/start-task` step 4 (`start-task/SKILL.md:124-126`); deleted by hook on `SubagentStop`.

### `Task` Dataclass Fields (`implementation_manager.py:99-144`)

```python
@dataclass
class Task:
    id: str                    # e.g. "T1", "1.1", "P0-T01"
    name: str                  # title
    status: TaskStatus         # NOT_STARTED | IN_PROGRESS | COMPLETE | BLOCKED | DEFERRED | SKIPPED
    dependencies: list[str]    # task IDs, e.g. ["T1", "T2"]
    agent: str | None          # agent name for dispatch
    priority: TaskPriority     # 1-5 (IntEnum)
    complexity: str            # "Low" | "Medium" | "High"
    started: str | None        # ISO timestamp
    completed: str | None      # ISO timestamp
    skills: list[str]          # skill names for the executing sub-agent
```

---

## 2. Phase 1 Implementation (Already Built)

Phase 1 SAM sub-issue functions exist in `.claude/skills/backlog/backlog_core/github.py` and supporting files.

### `create_task_issue()` (`github.py:455-512`)

```python
def create_task_issue(
    repo: Repository,
    parent_issue_number: int,
    task: SamTask,
    description: str = "",
    acceptance_criteria: list[str] | None = None,
    labels: list[str] | None = None,
    output: Output | None = None,
) -> Issue | None:
```

- Builds title via `build_sam_task_issue_title(task, description)` → `[{feature}/{task_id}] {task_type}: {description}`
- Builds body via `build_sam_task_body(task, description, acceptance_criteria)`
- Creates the GitHub issue
- Links it as sub-issue via `parent.add_sub_issue(task_issue)` — passes the `Issue` object (not `.number` or `.id`) to avoid PyGitHub's `.id`/`.number` confusion (documented in `github.py:505`, `comparison-github-task-dependency-options.md:93-105`)

### `get_task_issues()` (`github.py:515-532`)

```python
def get_task_issues(
    repo: Repository,
    parent_issue_number: int,
    output: Output | None = None,
) -> list[SubIssue]:
```

Returns `sorted(parent.get_sub_issues(), key=lambda si: si.priority_position)`. Empty list on failure.

### `update_task_status()` (`github.py:535-581`)

```python
def update_task_status(
    repo: Repository,
    issue_number: int,
    new_status: str,
    output: Output | None = None,
) -> bool:
```

- Fetches issue body, calls `parse_sam_task_metadata(body)` to extract the `<!-- sam:task ... -->` block
- Returns `False` (no write) if block is absent or status already matches
- Patches only the `status:` line in the invisible block using a targeted `re.sub()` on the DOTALL pattern
- Returns `True` if body was updated

### `SamTask` Model (`models.py:233-262`)

```python
class SamTask(BaseModel):
    task_id: str = ""         # e.g. "T1"
    feature: str = ""         # slug, e.g. "uv-skill-update"
    task_type: str = ""       # "research" | "implement" | "review" | "fix" | "docs"
    status: str = "not-started"
    agent: str = ""
    priority: int = 2
    skills: list[str] = Field(default_factory=list)
    dependencies: list[str] = Field(default_factory=list)
    # Cross-feature deps use GitHub issue numbers: ["#479"]
```

### `parse_sam_task_metadata()` (`parsing.py:880-912`)

Extracts and parses the invisible `<!-- sam:task\n{YAML}\n-->` block from an issue body. Returns `SamTask | None`. Uses `ruamel.yaml` for parsing. Pattern (`parsing.py:873`):

```python
_SAM_TASK_RE = re.compile(r"<!--\s*sam:task\s*\n(.*?)\n-->", re.DOTALL)
```

### `build_sam_task_body()` (`parsing.py:930-968`)

Builds the GitHub issue body: two visible markdown sections (`## What`, `## Acceptance Criteria`) followed by an invisible YAML comment block:

```markdown
## What

{description}

## Acceptance Criteria

- [ ] Work matches description

<!-- sam:task
task_id: T1
feature: uv-skill-update
type: implement
status: not-started
agent: context-gathering
priority: 2
skills: []
dependencies: []
-->
```

### `build_sam_task_issue_title()` (`parsing.py:915-927`)

```python
def build_sam_task_issue_title(task: SamTask, description: str) -> str:
    return f"[{task.feature}/{task.task_id}] {task.task_type}: {description}"
```

---

## 3. MCP Server Patterns

**Source**: `.claude/skills/backlog/backlog_core/server.py`

**Framework**: FastMCP 3.x (`server.py:1`, `server.py:8`)

```python
from fastmcp import Context, FastMCP
mcp = FastMCP("backlog")
```

### Tool Registration Pattern (`server.py:17-53`)

```python
@mcp.tool()
async def backlog_add(
    title: Annotated[str, Field(description="Item title")],
    priority: Annotated[str, Field(description="Priority level: P0, P1, P2, or Ideas")],
    source: Annotated[str, Field(description="...")] = "Not specified",
) -> dict:
    """Docstring describes when to use and what it returns."""
    out = Output()
    try:
        result = await asyncio.to_thread(
            operations.add_item,
            title=title,
            ...
            output=out,
        )
        return {**result, **out.to_dict()}
    except BacklogError as e:
        return {"error": str(e), **out.to_dict()}
```

**Invariants observed across all tools**:

1. All tools are `async def` returning `dict`
2. All parameters use `Annotated[type, Field(description="...")]`
3. Sync operations are offloaded via `await asyncio.to_thread(...)`
4. An `Output()` instance is always created and merged into the return dict via `{**result, **out.to_dict()}`
5. `BacklogError` (and subclasses) are caught and returned as `{"error": str(e), ...}` — never raised to the MCP framework
6. Tools that accept `Context` (for progress reporting) use `await ctx.info(...)` / `await ctx.warning(...)`

### `Output` Type (`models.py:157-183`)

```python
class Output(BaseModel):
    messages: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)

    def info(self, msg: str) -> None: ...
    def warn(self, msg: str) -> None: ...
    def error(self, msg: str) -> None: ...
    def to_dict(self) -> dict[str, list[str]]: ...
```

All functions accepting `Output | None = None` use the pattern `out = output or Output()`. All GitHub operations pass `output=out` and use `out.warn(...)` for non-fatal GitHub API failures.

### Error Handling Conventions

- GitHub `GithubException` is caught inside `github.py` functions and recorded via `out.warn(...)`. Functions return empty/None/False rather than raising.
- `BacklogError` and its subclasses (`ItemNotFoundError`, `DuplicateItemError`, `GitHubUnavailableError`, `ValidationError`) bubble up from `operations.py` and are caught at the `server.py` tool boundary.
- Callers check the `error` key in the returned dict — no exception propagates to the MCP client.

### `Context` Parameter Pattern

Only tools that need progress streaming (sync, normalize, pull) declare `ctx: Context` as first parameter. `ctx.info()` and `ctx.warning()` are awaited directly, unlike `out.info()` which is sync.

---

## 4. Local Cache Pattern

The backlog MCP uses GitHub Issues as canonical state and `.claude/backlog/` per-item `.md` files as a local cache.

### Sync Direction

- **Push**: `backlog_sync` creates GitHub issues for items lacking them, pushes groomed content to issue bodies
- **Pull**: `backlog_pull` fetches GitHub issue bodies, merges sections into local files (longer content wins per section, `parsing.py:768-803`)

### Offline Behavior

`try_get_github()` (`github.py:64-79`) attempts connection with a 10-second timeout, returns `None` on failure. Callers that use it (e.g., `batch_fetch_statuses`) return empty results silently when GitHub is unavailable. Operations that require GitHub (e.g., `create_issue_for_item`) use `get_github()` which raises `GitHubUnavailableError`, caught at the `server.py` tool boundary.

### Cache Update After GitHub Writes

After creating or resolving a GitHub issue, the local `.md` file's `issue:` frontmatter field is updated with `#N`. The `last_synced:` field (`models.py:153`) is updated during pull operations (`parsing.py:97-98`).

### Applying the Same Pattern to Task State

The analogous design for SAM task state:

1. **Local file is the write-first target** — `task_status_hook.py` writes YAML files directly (no network)
2. **GitHub sync is async/advisory** — a `sync_task_state()` function would call `update_task_status()` for tasks whose local status changed since last sync
3. **Pull on startup** — `sync_tasks_from_github()` would call `get_task_issues()` and populate local task files from the `<!-- sam:task -->` blocks
4. **Offline path** — readiness check reads only local files, never GitHub; the `try_get_github()` pattern applies to sync operations

---

## 5. Skill Integration Points

### `/implement-feature` Calls to `implementation_manager.py`

**Source**: `.claude/skills/implement-feature/SKILL.md:36-58`

```bash
# Step 1: Query status
uv run ./plugins/python3-development/skills/implementation-manager/scripts/implementation_manager.py \
  status . "$ARGUMENTS"

# Step 2: Query ready tasks
uv run ./plugins/python3-development/skills/implementation-manager/scripts/implementation_manager.py \
  ready-tasks . "$ARGUMENTS"
```

The orchestrator reads `ready_tasks[*].skills` from the `ready-tasks` JSON output and conditionally adds `Skill(skill="{name}")` instructions to each delegation prompt.

Delegation prompt format (`implement-feature/SKILL.md:72-73`):

```text
Skill(skill="start-task", args="{task_file_path} --task {task_id}")
```

### `/start-task` Task State Writes

**Source**: `.claude/skills/start-task/SKILL.md:81-126`

1. Calls `claim-task` CLI command — the only permitted way to write `status: in-progress`
2. Checks `claim-task` exit code — stops if non-zero (task already claimed)
3. Writes `.claude/context/active-task-{CLAUDE_SESSION_ID}.json` for hook use
4. Hook (`SubagentStop` on `/implement-feature`) writes `status: complete` and `completed:` timestamp

**Hook wiring in skill frontmatter** (`implement-feature/SKILL.md:6-11`):

```yaml
hooks:
  SubagentStop:
  - hooks:
    - type: command
      command: python3 "./plugins/python3-development/skills/implementation-manager/scripts/task_status_hook.py"
```

**PostToolUse hook** (`start-task/SKILL.md:7-12`) fires on Write/Edit/Bash within a task execution session, updating `last_activity`.

---

## 6. Gaps and Integration Points for Phases 2–4

### What Phase 1 Has Built

Phase 1 provides the GitHub API surface (`create_task_issue`, `get_task_issues`, `update_task_status`) and the body format (`build_sam_task_body`, `parse_sam_task_metadata`, `build_sam_task_issue_title`). All data models (`SamTask`) are in `models.py`.

### Gap: No `sync_tasks_from_github()` Function

`get_task_issues()` returns `list[SubIssue]` but there is no function that:

1. Calls `get_task_issues(repo, parent_issue_number)`
2. For each `SubIssue`, fetches its body and calls `parse_sam_task_metadata(body)`
3. Updates local task YAML files (status, timestamps) from the parsed `SamTask`

This is the pull-sync path needed for Phases 2–4.

### Gap: No `create_tasks_for_feature()` Orchestration Function

No function exists that takes a list of `Task` objects (from `implementation_manager.py`) and a parent issue number, then calls `create_task_issue()` for each. Phase 2 needs this to bootstrap task issues from existing task files.

### Gap: No MCP Tools for SAM Task Operations

`server.py` has no tools wrapping `create_task_issue`, `get_task_issues`, or `update_task_status`. Phase 2/3 will need new MCP tool registrations following the `server.py` pattern (async def → asyncio.to_thread → Output → dict return).

### Gap: `update_task_status()` Is GitHub-Only

`github.py:update_task_status()` updates the `<!-- sam:task -->` block in the GitHub issue body. It does NOT update the local task YAML file. The hook-driven path (`task_status_hook.py`) updates only local YAML. A complete status update needs both: local YAML write (via `update_yaml_field`) AND GitHub issue body write (via `github.py:update_task_status`).

### Gap: `implementation_manager.py` Has No GitHub Awareness

The `status`, `ready-tasks`, and `claim-task` commands read only local YAML files. Phases 2–4 require either:

- A new `--from-github` flag that pulls sub-issues before computing readiness (like `backlog_list`'s `from_github=True`), OR
- A separate sync step that populates local files before `implementation_manager.py` is invoked

The research document (`plan/research/comparison-github-task-dependency-options.md:283-296`) confirms the recommendation is Option B (sub-issues + local cache), which preserves the existing `get_ready_tasks()` logic unchanged. Readiness stays a local computation.

### Gap: `claim-task` Has No GitHub Counterpart

`claim-task` atomically writes `status: in-progress` to the local YAML. Phase 2 needs a companion call to `github.py:update_task_status(repo, issue_number, "in-progress")` after a successful local claim — but `claim-task` does not know the issue number.

The task YAML would need a new field (e.g., `github_issue: 479`) populated during task issue creation, so that `task_status_hook.py` or `claim-task` can look up the issue number and call `update_task_status`.

### Gap: `SubIssue` Has No `body` Attribute in Context

`get_task_issues()` returns `list[SubIssue]`. `SubIssue` inherits from `Issue` (`comparison-github-task-dependency-options.md:87-90`), so `.body` is available — but this is not explicitly validated in the current code. The `update_task_status` function fetches `.body` from `repo.get_issue(issue_number)`, not from a `SubIssue` object directly.

### Dependency Format Mismatch

`Task.dependencies` (local) uses task IDs: `["T1", "T2"]`. `SamTask.dependencies` (GitHub body) uses task IDs for within-feature deps and GitHub issue numbers for cross-feature deps: `["T1", "#479"]`. The conversion between these two formats is not yet implemented.

### `implementation_manager.py` Slug-to-File Discovery

`find_task_file_by_slug()` (`implementation_manager.py:750-771`) searches local `plan/` directories. After migration, a feature's "task source" is GitHub sub-issues, not local files. The slug-to-file discovery must either: (a) continue to work against locally-synced files, or (b) be augmented with a GitHub issue number → feature slug mapping. Option (a) is consistent with the local-cache approach.

---

*Analysis sources: `implementation_manager.py`, `task_status_hook.py`, `task_format.py`, `github.py`, `models.py`, `parsing.py`, `server.py`, `implement-feature/SKILL.md`, `start-task/SKILL.md`, `plan/research/comparison-github-task-dependency-options.md` — all read 2026-03-06.*
