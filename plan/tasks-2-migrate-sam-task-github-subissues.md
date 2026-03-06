---
feature: migrate-sam-task-github-subissues
parent_issue: 480
branch: claude/automate-backlog-processing-vKtX4
phase: "2-5"
generated: 2026-03-06
version: "1.0"
status: not-started
---

## Feature

Migrate SAM task tracking from local markdown files to GitHub sub-issues via backlog MCP.
Phase 1 is complete (commit 30066de). This file covers Phases 2–5.

## Context Manifest

### Key source files (read before implementing any task)

| File | Purpose | Required by |
|---|---|---|
| `.claude/skills/backlog/backlog_core/github.py` lines 454-581 | Phase 1 functions (frozen) | T1, T2, T4, T10 |
| `.claude/skills/backlog/backlog_core/models.py` lines 233-263 | `SamTask` model (frozen) | T1, T6 |
| `.claude/skills/backlog/backlog_core/parsing.py` lines 873-968 | Parse/build functions (frozen) | T1 |
| `.claude/skills/backlog/backlog_core/operations.py` | Add 4 functions (T1 output) | T1, T2, T6 |
| `.claude/skills/backlog/backlog_core/server.py` | Add 4 MCP tools (T2 output) | T2, T7 |
| `plugins/python3-development/skills/implementation-manager/scripts/implementation_manager.py` | Add `--github` flag (T3 output) | T3, T8 |
| `plugins/python3-development/skills/implementation-manager/scripts/task_status_hook.py` | Add GitHub sync (T4 output) | T4, T9 |
| `.claude/skills/implement-feature/SKILL.md` | Update docs (T5 output) | T5 |
| `plugins/python3-development/skills/development/implement-feature/SKILL.md` | Update docs — identical to above (T5 output) | T5 |
| `.claude/skills/start-task/SKILL.md` | Update docs (T5 output) | T5 |
| `plugins/python3-development/skills/development/start-task/SKILL.md` | Update docs — identical to above (T5 output) | T5 |
| `plan/architect-migrate-sam-task-github-subissues.md` | Architecture spec — interface contracts, error strategy, testing strategy | All tasks |
| `plan/codebase/sam-task-migration.md` | Codebase analysis — patterns, existing code shapes | All tasks |

---
task_id: "T1"
title: "Add SAM task operations to operations.py"
status: not-started
agent: python3-development:python-cli-architect
priority: 1
complexity: Medium
accuracy_risk: medium
dependencies: []
skills:
  - python3-development
parallelize_with: []
reason: "Foundational layer. No other task writes operations.py."
handoff: "Summary of 4 functions added, line ranges, result of uv run prek run --files, any deviations from spec."
---

## Context

Phase 1 is complete (commit 30066de). `github.py` has `create_task_issue`, `get_task_issues`, `update_task_status`. `models.py` has `SamTask`. `parsing.py` has `parse_sam_task_metadata`. `server.py` calls all existing tools through `operations.py` — never directly into `github.py`. This task adds four new functions to `operations.py` following that established pattern.

Files to read before starting:
- `.claude/skills/backlog/backlog_core/operations.py` — existing function signatures and patterns
- `.claude/skills/backlog/backlog_core/github.py` lines 454-581 — Phase 1 functions being wrapped
- `.claude/skills/backlog/backlog_core/models.py` lines 157-183 (Output), 233-263 (SamTask)
- `plan/architect-migrate-sam-task-github-subissues.md` section 3.1 — interface contracts

## Objective

Add four new functions to `operations.py` that wrap Phase 1 `github.py` functions and serve as the intermediary layer for Phase 2 MCP tools.

## Required Inputs

- `.claude/skills/backlog/backlog_core/operations.py` (existing file — read first)
- `.claude/skills/backlog/backlog_core/github.py` (Phase 1 functions at lines 454-581)
- `.claude/skills/backlog/backlog_core/models.py` (Output, SamTask, BacklogError)
- `plan/architect-migrate-sam-task-github-subissues.md` section 3.1 (interface contracts)
- `plan/codebase/sam-task-migration.md` section 3 (MCP server patterns, Output type)

## Requirements

### create_sam_task

1. Accept parameters: `parent_issue_number: int`, `task_id: str`, `feature: str`, `task_type: str`, `agent: str`, `priority: int`, `skills: list[str]`, `dependencies: list[str]`, `description: str`, `acceptance_criteria: list[str] | None`, `labels: list[str] | None`, `output: Output | None = None`.
2. Construct a `SamTask` from the scalar parameters.
3. Call `get_github()` to obtain `repo` — raises `GitHubUnavailableError` on failure (propagate to server boundary).
4. Call `github.create_task_issue(repo, parent_issue_number, task, description, acceptance_criteria, labels, output=out)`.
5. Return `{"issue_number": issue.number, "title": issue.title, "url": issue.html_url}` on success. Include `"warnings"` key from `out.to_dict()` when sub-issue linking logged warnings.

### get_sam_tasks

6. Accept parameters: `parent_issue_number: int`, `refresh_cache: bool = True`, `output: Output | None = None`.
7. Call `try_get_github()` — if it returns `None`, read cache from `.claude/context/sam-tasks-{feature_slug}.json` and return cached tasks with a warning; if cache absent or malformed, return `{"tasks": [], "count": 0, "parent_issue_number": parent_issue_number}` with a warning.
8. Call `github.get_task_issues(repo, parent_issue_number, output=out)` — returns `list[SubIssue]`.
9. For each `SubIssue`: fetch `.body` via `repo.get_issue(si.sub_issue.number)`, call `parse_sam_task_metadata(body)` to extract `SamTask`. Include `"issue_number"` and `"issue_url"` from the sub-issue in each task dict.
10. If `refresh_cache=True` and tasks is non-empty: write `.claude/context/sam-tasks-{feature_slug}.json` (derive `feature_slug` from the first task's `SamTask.feature` field).
11. Return `{"tasks": [...], "count": N, "parent_issue_number": parent_issue_number}`.

### update_sam_task_status

12. Accept parameters: `issue_number: int`, `new_status: str`, `output: Output | None = None`.
13. Call `get_github()` — raises `GitHubUnavailableError` on failure.
14. Call `github.update_task_status(repo, issue_number, new_status, output=out)` — returns `bool`.
15. Return `{"updated": updated_bool, "issue_number": issue_number, "new_status": new_status}`.

### get_ready_sam_tasks

16. Accept parameters: `parent_issue_number: int`, `output: Output | None = None`.
17. Call `get_sam_tasks(parent_issue_number, refresh_cache=True, output=out)` to get task list.
18. Convert task dicts to a local `Task`-compatible structure consumable by `get_ready_tasks()` logic: `status` as `TaskStatus`, `dependencies` as `list[str]` (pass through as-is — cross-feature `#N` refs are treated as always-satisfied by the existing logic).
19. Apply the same readiness resolution as `implementation_manager.py:get_ready_tasks()`: a task is ready when `status == NOT_STARTED` and all deps have terminal status. Do not import `implementation_manager.py` — re-implement the three-line logic inline or extract it.
20. Return `{"feature": feature_slug, "ready_tasks": [...], "count": N}` where each ready task dict has keys: `id`, `name`, `agent`, `skills`, `issue_number`.

## Constraints

- Do not call `github.py` functions directly from `server.py` — all calls go through `operations.py` (this task is establishing that layer).
- Do not modify `github.py`, `models.py`, or `parsing.py` — Phase 1 files are frozen.
- Use `ruamel.yaml` for any YAML serialization in cache writes; do not use `pyyaml`.
- Use `try_get_github()` for read operations (`get_sam_tasks`, `get_ready_sam_tasks`); use `get_github()` for write operations (`create_sam_task`, `update_sam_task_status`).
- Cache file path: `.claude/context/sam-tasks-{feature_slug}.json` — use `Path.home() / ".claude" / "context"` or derive from an established constant in `models.py`.
- `GithubException` is already caught inside `github.py` functions — do not double-catch it in `operations.py`. Catch `BacklogError` subclasses only where noted.

## Expected Outputs

- `.claude/skills/backlog/backlog_core/operations.py` — modified (4 new functions appended)

## Acceptance Criteria

1. `create_sam_task` returns `{"issue_number": int, "title": str, "url": str}` when `create_task_issue` succeeds.
2. `get_sam_tasks` returns `{"tasks": list, "count": int, "parent_issue_number": int}` and writes cache file when online and `refresh_cache=True`.
3. `get_sam_tasks` returns cached data (not empty) when `try_get_github()` returns None and cache file exists.
4. `update_sam_task_status` returns `{"updated": False, ...}` without error when `github.update_task_status` returns False.
5. `get_ready_sam_tasks` return shape matches `{"feature": str, "ready_tasks": [...], "count": int}` with each item having `id`, `name`, `agent`, `skills`, `issue_number`.
6. `get_ready_sam_tasks` treats cross-feature `#N` dependencies as always-satisfied (not as blockers).
7. All four functions handle `output: Output | None = None` with the `out = output or Output()` pattern.
8. `uv run prek run --files .claude/skills/backlog/backlog_core/operations.py` exits 0.

## Verification Steps

1. Read `.claude/skills/backlog/backlog_core/operations.py` after writing — confirm 4 new function definitions are present.
2. Run `uv run prek run --files .claude/skills/backlog/backlog_core/operations.py` — confirm exit 0.
3. Confirm `get_sam_tasks` and `get_ready_sam_tasks` call `try_get_github()` (not `get_github()`) by grepping the function bodies.
4. Confirm `create_sam_task` and `update_sam_task_status` call `get_github()` by grepping the function bodies.
5. Confirm no `import yaml` — only `ruamel.yaml` used in cache writes.

## CoVe Checks

Key claims to verify:

- `SubIssue` inherits from `Issue` and `.body` is accessible via `repo.get_issue(si.sub_issue.number)` (not directly on `SubIssue`).
- `try_get_github()` returns `None` (not raises) when GitHub is unavailable.
- The cache file path `.claude/context/` is writable in the agent's execution context.

Verification questions:

1. Does `get_task_issues()` in `github.py` return `list[SubIssue]` where `SubIssue` has a `.sub_issue.number` or `.number` attribute that can be passed to `repo.get_issue()`?
2. Does `try_get_github()` in `github.py` return `None` on failure or raise an exception?
3. What constant or pattern establishes the `.claude/context/` directory path in the existing codebase?

Evidence to collect:

- Read `github.py` lines 515-532 (`get_task_issues`) and confirm `SubIssue` attribute access pattern.
- Read `github.py` lines 64-79 (`try_get_github`) and confirm return type on failure.
- Grep `".claude/context"` in `task_status_hook.py` to find the established path construction pattern.

Revision rule: If `SubIssue` attribute access differs from what the spec states, use the correct attribute and note the deviation in the handoff.

## Handoff

Return:
- Line ranges of the 4 new functions in `operations.py`
- Whether `SubIssue.body` required fetching via `repo.get_issue()` or was directly accessible
- Result of `uv run prek run --files .claude/skills/backlog/backlog_core/operations.py`
- Any deviations from the interface contracts in section 3.1 of the architecture spec

---
task_id: "T2"
title: "Add SAM task MCP tools to server.py"
status: not-started
agent: python3-development:python-cli-architect
priority: 1
complexity: Medium
accuracy_risk: medium
dependencies:
  - T1
skills:
  - python3-development
parallelize_with: []
reason: "Single file. Depends on T1 operations.py functions existing."
handoff: "Summary of 4 tools added, tool names, result of uv run prek run --files, any deviations from spec."
---

## Context

T1 has added `create_sam_task`, `get_sam_tasks`, `update_sam_task_status`, `get_ready_sam_tasks` to `operations.py`. This task registers those functions as MCP tools in `server.py`. The server currently has 10 tools (`backlog_add` through `backlog_pull`). The `backlog_add` tool at lines 17-53 is the canonical pattern for all new tools.

Files to read before starting:
- `.claude/skills/backlog/backlog_core/server.py` — full file (tool registration pattern)
- `plan/architect-migrate-sam-task-github-subissues.md` section 3.2 — exact tool signatures

## Objective

Add four MCP tools to `server.py` that expose the Phase 2 `operations.py` functions, following the existing `backlog_add` pattern exactly.

## Required Inputs

- `.claude/skills/backlog/backlog_core/server.py` (existing file — read first)
- `.claude/skills/backlog/backlog_core/operations.py` (after T1 completes — verify functions exist)
- `plan/architect-migrate-sam-task-github-subissues.md` section 3.2 (tool signatures and docstrings)
- `plan/codebase/sam-task-migration.md` section 3 (invariants: async def, Annotated, asyncio.to_thread, Output, BacklogError catch)

## Requirements

### All four tools must follow these invariants

1. Decorated with `@mcp.tool()`.
2. Defined as `async def` returning `dict`.
3. All parameters use `Annotated[type, Field(description="...")]`.
4. Sync operation offloaded via `await asyncio.to_thread(operations.FUNC_NAME, param=value, ..., output=out)`.
5. Return `{**result, **out.to_dict()}`.
6. Catch `BacklogError as e` and return `{"error": str(e), **out.to_dict()}`.
7. `out = Output()` created at top of each tool body.

### backlog_create_sam_task

8. Parameters (all required unless noted): `parent_issue_number: int`, `task_id: str`, `feature: str`, `task_type: str`, `agent: str`, `priority: int = 2`, `skills: list[str] = []`, `dependencies: list[str] = []`, `description: str = ""`, `acceptance_criteria: list[str] | None = None`, `labels: list[str] | None = None`.
9. Docstring: "Create a GitHub sub-issue for a SAM task under a parent story issue. Use to bootstrap GitHub visibility for a task when starting a new feature plan. Returns issue_number, title, url, and output messages. On error, returns error key."

### backlog_get_sam_tasks

10. Parameters: `parent_issue_number: int`, `refresh_cache: bool = True`.
11. Docstring: "Return all SAM task sub-issues for a parent story issue. Returns tasks list with SamTask fields plus issue_number and issue_url. Falls back to local cache if GitHub is unavailable. Use to inspect per-task status from the GitHub source of truth."

### backlog_update_sam_task_status

12. Parameters: `issue_number: int`, `new_status: str`.
13. Docstring: "Update the status field in a SAM task sub-issue. Patches the sam:task YAML block in the issue body. No-op if status already matches. Returns updated (bool), issue_number, new_status."

### backlog_get_ready_sam_tasks

14. Parameters: `parent_issue_number: int`.
15. Docstring: "Return SAM tasks ready for execution from GitHub sub-issues. Fetches sub-issues, resolves dependency graph locally, returns tasks whose status is not-started and all dependencies are terminal. Output shape matches implementation_manager.py ready-tasks JSON: feature, ready_tasks, count. Each ready_task includes id, name, agent, skills, issue_number. Falls back to local cache if GitHub is unavailable."

## Constraints

- Do not call `github.py` or any `github.*` function directly from `server.py` — call only `operations.*` functions.
- Do not use `shell=True` in any subprocess call.
- Default mutable arguments (`skills: list[str] = []`) must be handled safely — use `Field(default_factory=list)` in `Annotated` if needed, or accept the FastMCP default behavior for tool parameters.
- Do not modify existing tools or any other part of `server.py`.

## Expected Outputs

- `.claude/skills/backlog/backlog_core/server.py` — modified (4 new tool functions appended)

## Acceptance Criteria

1. All four tools are registered and visible: `grep -n "async def backlog_create_sam_task\|async def backlog_get_sam_tasks\|async def backlog_update_sam_task_status\|async def backlog_get_ready_sam_tasks" server.py` returns 4 matches.
2. Each tool body creates `out = Output()` and returns `{**result, **out.to_dict()}`.
3. Each tool catches `BacklogError as e` and returns `{"error": str(e), **out.to_dict()}`.
4. Each tool offloads the sync operation via `asyncio.to_thread`.
5. `uv run prek run --files .claude/skills/backlog/backlog_core/server.py` exits 0.
6. The file imports `asyncio`, `Annotated`, `Field`, `Output`, `BacklogError`, and `operations` — confirm all are already imported (do not duplicate imports).

## Verification Steps

1. Run `grep -n "async def backlog_create_sam_task\|async def backlog_get_sam_tasks\|async def backlog_update_sam_task_status\|async def backlog_get_ready_sam_tasks" .claude/skills/backlog/backlog_core/server.py` — confirm 4 matches.
2. Run `uv run prek run --files .claude/skills/backlog/backlog_core/server.py` — confirm exit 0.
3. Read each tool body and confirm `asyncio.to_thread` is used (not a direct sync call).
4. Confirm no new top-level imports were added that duplicate existing ones.

## CoVe Checks

Key claims to verify:

- `asyncio`, `Annotated`, `Field`, `BacklogError`, `Output`, and `operations` are all already imported in `server.py` before T2 writes.
- FastMCP accepts `list[str]` with a default of `[]` as a tool parameter without requiring `Field(default_factory=list)`.

Verification questions:

1. Do all required names appear in the existing `server.py` import block?
2. Does the existing `server.py` have any tool with a `list[str]` parameter with a default of `[]`? If so, what pattern does it use?

Evidence to collect:

- Read `server.py` import block (first 20 lines) and list all imported names.
- Search `server.py` for `list[str]` in existing tool parameter annotations.

Revision rule: If any import is missing, add it. If `Field(default_factory=list)` is required, use it. Note deviations in the handoff.

## Handoff

Return:
- Line numbers of the 4 new tool functions in `server.py`
- Whether any new imports were required
- Result of `uv run prek run --files .claude/skills/backlog/backlog_core/server.py`
- Any parameter pattern deviations from the architecture spec

---
task_id: "T3"
title: "Add --github flag to implementation_manager.py"
status: not-started
agent: python3-development:python-cli-architect
priority: 2
complexity: High
accuracy_risk: high
dependencies:
  - T2
skills:
  - python3-development
parallelize_with:
  - T4
reason: "T3 and T4 write different files. Safe to parallelize after T2."
handoff: "Summary of changes, verified sys.path calculation, result of uv run prek run --files, backward-compat test evidence."
---

## Context

This task modifies `implementation_manager.py` — a standalone Python script in `plugins/python3-development/skills/implementation-manager/scripts/`. It currently reads task state exclusively from local YAML files and has no GitHub dependency. T2 has added MCP tools that expose GitHub sub-issue queries. This task adds a `--github` flag to the `ready-tasks` and `status` commands that, when passed, fetches task data from GitHub sub-issues via `backlog_core` instead of local YAML files. The existing local-file path must remain unchanged when the flag is absent.

Files to read before starting:
- `plugins/python3-development/skills/implementation-manager/scripts/implementation_manager.py` — full file
- `plan/architect-migrate-sam-task-github-subissues.md` section 3.3 — exact signatures and sys.path pattern
- `plan/architect-migrate-sam-task-github-subissues.md` section 5.4 — error boundary for `--github` path
- `plan/codebase/sam-task-migration.md` section 1 — `Task` dataclass fields, `get_ready_tasks()` logic

## Objective

Add `--github` and `--parent-issue` optional flags to the `ready-tasks` and `status` commands, with a new `fetch_tasks_from_github()` internal function, while leaving all existing behavior unchanged when the flags are absent.

## Required Inputs

- `plugins/python3-development/skills/implementation-manager/scripts/implementation_manager.py` (existing file — read before editing)
- `plan/architect-migrate-sam-task-github-subissues.md` sections 3.3 and 5.4
- `plan/codebase/sam-task-migration.md` section 1 (`Task` dataclass, `get_ready_tasks()` logic at lines 774-809)

## Requirements

### sys.path extension

1. After the existing `task_format` sys.path insert, add:

   ```python
   _BACKLOG_CORE = Path(__file__).resolve().parents[6] / ".claude" / "skills" / "backlog" / "backlog_core"
   if _BACKLOG_CORE.exists():
       sys.path.insert(0, str(_BACKLOG_CORE.parent))
   ```

   Verify the actual relative path from `implementation_manager.py` to `.claude/skills/backlog/` before writing. The script is at `plugins/python3-development/skills/implementation-manager/scripts/implementation_manager.py`. Count directory levels: `scripts/` → `implementation-manager/` → `skills/` → `python3-development/` → `plugins/` → repo root → `.claude/` → `skills/` → `backlog/`. Adjust `parents[N]` to match the actual count.

### fetch_tasks_from_github()

2. Signature: `def fetch_tasks_from_github(parent_issue_number: int, feature_slug: str, cache_path: Path) -> list[Task] | None`.
3. Import `backlog_core.github` conditionally inside this function (guard with `if _BACKLOG_CORE.exists()`).
4. Call `backlog_core.github.try_get_github()`. If it returns `None`: read `cache_path` (JSON), convert to `list[Task]` from the cache structure, return the list. If cache absent or malformed (`json.JSONDecodeError`, `KeyError`): print warning to stderr, return `None`.
5. Call `backlog_core.github.get_task_issues(repo, parent_issue_number)` — returns `list[SubIssue]`.
6. For each `SubIssue`: fetch body via `repo.get_issue(si.sub_issue.number).body`, call `backlog_core.parsing.parse_sam_task_metadata(body)` to get `SamTask | None`. Skip if `None`.
7. Convert each `SamTask` to a `Task` object using the existing `Task` dataclass: `id=sam.task_id`, `name=sam.task_id` (description not available from sub-issue metadata without parsing body further — use title from issue), `status=TaskStatus(sam.status)`, `dependencies=sam.dependencies`, `agent=sam.agent`, `priority=TaskPriority(sam.priority)`, `complexity="Medium"` (default), `started=None`, `completed=None`, `skills=sam.skills`.
8. Write `cache_path` JSON with structure `{"feature_slug": feature_slug, "parent_issue_number": parent_issue_number, "synced_at": iso_timestamp, "tasks": [...]}`.
9. Return `list[Task]`.

### ready-tasks command changes

10. Add `github: Annotated[bool, typer.Option("--github", help="Query GitHub sub-issues instead of local files")] = False` parameter.
11. Add `parent_issue: Annotated[int | None, typer.Option("--parent-issue", help="Parent story issue number")] = None` parameter.
12. When `github=True` and `parent_issue` is not None: call `fetch_tasks_from_github(parent_issue, feature_slug, cache_path)`. If it returns `None`: fall back to local file read with a warning on stderr. If both GitHub and cache fail and no local file exists: emit `{"error": "No task data available — GitHub unreachable and no cache found"}` to stdout and `sys.exit(1)`.
13. When `github=False` or `parent_issue` is None: existing local-file path unchanged.

### status command changes

14. Add the same `github` and `parent_issue` parameters.
15. When `github=True`: use `fetch_tasks_from_github` as the task source; include `github_issue` field in each task dict in the JSON output if available from the cache.
16. When `github=False`: existing local-file path unchanged.

## Constraints

- `get_ready_tasks()` function body must not change — only its inputs change.
- `claim-task` command must not gain any GitHub behavior.
- When `--github` is absent: zero changes to observable behavior (no imports, no path changes, no output differences).
- `backlog_core` import must be conditional and guarded by `_BACKLOG_CORE.exists()` — the script must remain runnable without `backlog_core` present.
- Use `ruamel.yaml` if any YAML is needed (existing pattern); do not add `pyyaml`.
- Do not use `shell=True`.
- The `parents[N]` value in the sys.path calculation must be verified against the actual directory structure — do not copy it from the spec without checking.

## Expected Outputs

- `plugins/python3-development/skills/implementation-manager/scripts/implementation_manager.py` — modified

## Acceptance Criteria

1. `uv run plugins/python3-development/skills/implementation-manager/scripts/implementation_manager.py ready-tasks . some-slug` (no flag) produces identical output to pre-task behavior.
2. `grep -n "def fetch_tasks_from_github" implementation_manager.py` returns one match.
3. `grep -n "\-\-github" implementation_manager.py` returns matches in both `ready-tasks` and `status` command definitions.
4. `_BACKLOG_CORE.exists()` guard is present before any `backlog_core` import.
5. `uv run prek run --files plugins/python3-development/skills/implementation-manager/scripts/implementation_manager.py` exits 0.
6. `fetch_tasks_from_github` returns `None` (not raises) when `try_get_github()` returns `None` and cache is absent.

## Verification Steps

1. Run `uv run plugins/python3-development/skills/implementation-manager/scripts/implementation_manager.py ready-tasks . nonexistent-slug` — confirm output matches existing error behavior (not a new error from the `--github` path).
2. Run `uv run prek run --files plugins/python3-development/skills/implementation-manager/scripts/implementation_manager.py` — confirm exit 0.
3. Run `grep -c "_BACKLOG_CORE.exists()" plugins/python3-development/skills/implementation-manager/scripts/implementation_manager.py` — confirm at least 1 match.
4. Run `python3 -c "from pathlib import Path; p = Path('plugins/python3-development/skills/implementation-manager/scripts/implementation_manager.py').resolve(); print(p.parents[6])"` from the repo root — confirm the result is the repo root (the `.claude/` dir should be a child of that path).

## CoVe Checks

Key claims to verify:

- `parents[6]` is the correct index to reach the repo root from `implementation_manager.py`.
- `backlog_core.github.try_get_github` is importable as `from backlog_core import github; github.try_get_github()` (not a standalone function at module level).
- `SubIssue` has a `.sub_issue.number` attribute (not `.number` directly) for fetching the issue body.

Verification questions:

1. Running `python3 -c "from pathlib import Path; print(Path('plugins/python3-development/skills/implementation-manager/scripts/implementation_manager.py').resolve().parents[6])"` from repo root — does the result point to the repo root?
2. Is `try_get_github` accessible as `backlog_core.github.try_get_github` or must it be imported differently?
3. What attribute does a `SubIssue` object expose for its issue number — `.number`, `.sub_issue.number`, or another?

Evidence to collect:

- Run path calculation command and capture output.
- Read `github.py` lines 64-79 (`try_get_github`) import/export pattern.
- Read `github.py` lines 515-532 (`get_task_issues`) to see what `SubIssue` attributes are accessed.

Revision rule: Use the verified `parents[N]` index. If `SubIssue` attribute access differs, use the correct attribute and document in handoff.

## Handoff

Return:
- Verified `parents[N]` value used and the path it resolves to
- Whether any `SubIssue` attribute access differed from the spec
- Result of `uv run prek run --files` on the modified file
- Whether backward-compat (no-flag) path produces identical output (confirm with a test run)

---
task_id: "T4"
title: "Extend task_status_hook.py with GitHub completion sync"
status: not-started
agent: python3-development:python-cli-architect
priority: 2
complexity: Medium
accuracy_risk: high
dependencies:
  - T2
skills:
  - python3-development
parallelize_with:
  - T3
reason: "T4 and T3 write different files. Safe to parallelize after T2."
handoff: "Summary of 2 new functions, verified exit-0 guarantee, result of uv run prek run --files."
---

## Context

`task_status_hook.py` responds to Claude Code hook events. Its `SubagentStop` handler (`handle_subagent_stop`, lines 396-447) currently: parses prompt for `/start-task` invocations, resolves task file path, writes `status: complete` + timestamp to local YAML, deletes context file, exits 0. This task adds one new step at the end: `sync_completion_to_github()` — a best-effort GitHub sync that reads the `github_issue` field from the task YAML and calls `github.update_task_status()`. The existing write path must remain unchanged. The hook must always exit 0 regardless of GitHub outcome.

The active-task context file currently has two fields: `task_file_path` and `task_id`. The architecture spec adds a third optional field: `parent_issue_number`. The hook reads this field via a new `get_parent_issue_number()` helper.

Files to read before starting:
- `plugins/python3-development/skills/implementation-manager/scripts/task_status_hook.py` — full file
- `plan/architect-migrate-sam-task-github-subissues.md` sections 3.4 and 5.3 — exact signatures and exit-code contract
- `plan/codebase/sam-task-migration.md` section 1 (`task_status_hook.py` write path description)

## Objective

Add `get_parent_issue_number()` and `sync_completion_to_github()` to `task_status_hook.py`, and call `sync_completion_to_github()` as the final step of `handle_subagent_stop()`, with guaranteed exit 0 on GitHub failure.

## Required Inputs

- `plugins/python3-development/skills/implementation-manager/scripts/task_status_hook.py` (read before editing)
- `plan/architect-migrate-sam-task-github-subissues.md` sections 3.4 and 5.3
- `plan/codebase/sam-task-migration.md` section 1 (hook event handling, context file format)

## Requirements

### Sys.path for backlog_core (conditional)

1. After the existing `task_format` sys.path insert (or using an equivalent pattern), add a conditional sys.path insert for `backlog_core`:

   ```python
   _BACKLOG_CORE_HOOK = Path(__file__).resolve().parents[N] / ".claude" / "skills" / "backlog" / "backlog_core"
   if _BACKLOG_CORE_HOOK.exists():
       sys.path.insert(0, str(_BACKLOG_CORE_HOOK.parent))
   ```

   Verify the `parents[N]` value against the actual directory structure of `task_status_hook.py`. The script is in the same `scripts/` directory as `implementation_manager.py` — use the same verified index from T3.

### get_parent_issue_number()

2. Signature: `def get_parent_issue_number(hook_input: dict[str, Any]) -> int | None`.
3. Read the active-task context file path from `hook_input` using the same method `handle_activity_update` uses.
4. If the context file exists, parse its JSON, return `int(data["parent_issue_number"])` if the key exists, else `None`.
5. If the file does not exist or JSON parsing fails: return `None`. Never raise.

### sync_completion_to_github()

6. Signature: `def sync_completion_to_github(task_file_path: Path, task_id: str, parent_issue_number: int | None) -> None`.
7. Read the task YAML frontmatter from `task_file_path` using `task_format.py` utilities (existing import pattern). Extract `github_issue` field as `int | None`.
8. If `github_issue` is absent (`None`): print warning to stderr (`f"[hook] No github_issue field in {task_file_path} — skipping GitHub sync"`), return.
9. If `_BACKLOG_CORE_HOOK` does not exist on sys.path: print warning to stderr, return.
10. Import `backlog_core.github` inside the function (conditional import, not at module level).
11. Call `backlog_core.github.get_github()` — if it raises `GitHubUnavailableError` or any exception: log to stderr, return.
12. Call `backlog_core.github.update_task_status(repo, github_issue, "complete")` — if it raises any exception: log to stderr, return.
13. On success: print info to stderr (`f"[hook] Synced task {task_id} completion to GitHub issue #{github_issue}"`).
14. Wrap the entire function body in `try/except Exception as e: print(f"[hook] GitHub sync failed: {e}", file=sys.stderr)`.

### handle_subagent_stop() modification

15. After step 4 (delete context file — existing), add step 5: `sync_completion_to_github(resolved_path, task_id, get_parent_issue_number(hook_input))`.
16. The call to `sync_completion_to_github` must not be inside a try/except at the call site — the function itself handles all exceptions internally.

### handle_activity_update() — no changes

17. `handle_activity_update` (PostToolUse) must not import `backlog_core` or call any GitHub function. Confirm no accidental modification.

## Constraints

- Exit code is always 0 from `task_status_hook.py` after GitHub sync — GitHub failure must never change the exit code.
- `backlog_core` import must be conditional (inside `sync_completion_to_github`) and guarded by `_BACKLOG_CORE_HOOK.exists()`.
- `handle_activity_update` must not be modified.
- `task_format.py` import contract must remain intact.
- All GitHub failures write to `sys.stderr`, never to `sys.stdout` (stdout is parsed by Claude Code).

## Expected Outputs

- `plugins/python3-development/skills/implementation-manager/scripts/task_status_hook.py` — modified

## Acceptance Criteria

1. `grep -n "def get_parent_issue_number\|def sync_completion_to_github" task_status_hook.py` returns exactly 2 matches.
2. `grep -n "sync_completion_to_github" task_status_hook.py` returns at least 3 lines (definition + call in `handle_subagent_stop` + at least one internal reference).
3. `handle_activity_update` function body contains no reference to `backlog_core` or `update_task_status`.
4. `sync_completion_to_github` wraps its body in `try/except Exception`.
5. The hook exits 0 when `github_issue` field is absent (no crash, warning to stderr).
6. `uv run prek run --files plugins/python3-development/skills/implementation-manager/scripts/task_status_hook.py` exits 0.

## Verification Steps

1. Run `grep -n "def get_parent_issue_number\|def sync_completion_to_github" plugins/python3-development/skills/implementation-manager/scripts/task_status_hook.py` — confirm 2 matches.
2. Run `grep -n "backlog_core\|update_task_status" plugins/python3-development/skills/implementation-manager/scripts/task_status_hook.py` — confirm all matches are inside `sync_completion_to_github` only (none in `handle_activity_update`).
3. Run `uv run prek run --files plugins/python3-development/skills/implementation-manager/scripts/task_status_hook.py` — confirm exit 0.
4. Read `handle_subagent_stop` function and confirm the call to `sync_completion_to_github` appears after the context file deletion step.

## CoVe Checks

Key claims to verify:

- `task_format.py` provides a function to read YAML frontmatter from a task file that returns a dict with optional `github_issue` key.
- The active-task context file path construction in `handle_activity_update` uses `CLAUDE_SESSION_ID` from environment — confirm the variable name and source used in the existing code.

Verification questions:

1. What function from `task_format.py` is used to read YAML frontmatter in the existing `task_status_hook.py`? Does it return a dict where `github_issue` would appear as a key?
2. How is the active-task context file path constructed in the existing `handle_activity_update` — what environment variable provides the session ID?

Evidence to collect:

- Read `task_status_hook.py` lines 450-498 (`handle_activity_update`) — note context file path construction.
- Read `task_format.py` to identify the YAML-reading function used by the hook.

Revision rule: Use the exact same context file path construction pattern as `handle_activity_update`. Use the exact same YAML-reading function as the existing hook code.

## Handoff

Return:
- Line numbers of the two new functions and the modified call in `handle_subagent_stop`
- The `parents[N]` value verified for this file's location
- Whether `task_format.py` exposes a frontmatter-reading function that accepts optional keys
- Result of `uv run prek run --files` on the modified file

---
task_id: "T5"
title: "Update implement-feature and start-task SKILL.md docs (both copies)"
status: not-started
agent: service-docs-maintainer
priority: 2
complexity: Low
accuracy_risk: low
dependencies:
  - T3
  - T4
skills: []
parallelize_with:
  - T6
  - T7
  - T8
  - T9
  - T10
reason: "T5 writes 4 SKILL.md files. No other task touches these files."
handoff: "Summary of changes to each file, result of uv run prek run --files on each."
---

## Context

This task updates documentation only — no Python code changes. Four SKILL.md files describe the `/implement-feature` and `/start-task` workflows. Each exists in two copies that must be updated identically:

- `.claude/skills/implement-feature/SKILL.md`
- `plugins/python3-development/skills/development/implement-feature/SKILL.md`
- `.claude/skills/start-task/SKILL.md`
- `plugins/python3-development/skills/development/start-task/SKILL.md`

T3 added `--github` flag to `implementation_manager.py`. T4 added GitHub sync to `task_status_hook.py`. The SKILL.md files describing these components need to reflect the new data flow.

Files to read before starting:
- All four SKILL.md files listed above
- `plan/architect-migrate-sam-task-github-subissues.md` section 3.5 — exact text for the new conditional blocks
- `plan/codebase/sam-task-migration.md` section 5 — current skill integration point descriptions

## Objective

Update all four SKILL.md files to document the new `--github` flag preference, the `parent_issue_number` field in the active-task context file, and the GitHub sync behavior of `task_status_hook.py` on `SubagentStop`.

## Required Inputs

- `.claude/skills/implement-feature/SKILL.md` (read before editing)
- `plugins/python3-development/skills/development/implement-feature/SKILL.md` (read before editing)
- `.claude/skills/start-task/SKILL.md` (read before editing)
- `plugins/python3-development/skills/development/start-task/SKILL.md` (read before editing)
- `plan/architect-migrate-sam-task-github-subissues.md` section 3.5

## Requirements

### implement-feature SKILL.md changes (both copies)

1. Find the step that describes the `ready-tasks` CLI command invocation.
2. Replace or augment the CLI invocation text with the following conditional block:

   ```text
   If parent story issue number is known:
     Prefer MCP: backlog_get_ready_sam_tasks(parent_issue_number=N)
     Output shape: {"feature": "...", "ready_tasks": [...], "count": N}
     Falls back to local cache if GitHub unavailable.

   If parent issue number is unknown (or MCP unavailable):
     CLI fallback: uv run implementation_manager.py ready-tasks . {slug}
     With GitHub flag: uv run implementation_manager.py ready-tasks . {slug} --github --parent-issue N
   ```

3. In the section describing how `task_status_hook.py` works on `SubagentStop`, add a sentence: "After marking the task complete locally, the hook calls `backlog_core.github.update_task_status()` to sync the completion to the GitHub sub-issue (if `github_issue` field is set in the task YAML). GitHub sync failure does not affect the hook exit code."

### start-task SKILL.md changes (both copies)

4. Find the step that describes writing `.claude/context/active-task-{CLAUDE_SESSION_ID}.json`.
5. Update the JSON example to include the new optional field:

   ```json
   {
     "task_file_path": "plan/tasks-001-slug/T1.md",
     "task_id": "T1",
     "parent_issue_number": N
   }
   ```

6. Add a note: "Omit `parent_issue_number` if the story issue number is not known. The hook treats absence as `None` and skips GitHub sync."
7. If the skill describes the in-progress GitHub sync (step 3 in architecture spec section 4 write path): add a best-effort GitHub sync step after the `claim-task` call — "If `parent_issue_number` is known and `github_issue` field is set in task YAML: call `backlog_get_sam_tasks` or directly `backlog_core.github.update_task_status(repo, github_issue, 'in-progress')`. Failure is non-fatal — continue regardless."

## Constraints

- Both copies of each SKILL.md must be byte-for-byte identical in the changed sections.
- Do not restructure or reformat sections not being changed.
- Do not add new sections — update existing sections only.
- Use markdown link syntax (`[text](./path)`) for any new file references added, with `./` prefix.
- Language specifiers required on all code fences added.
- Run `uv run prek run --files {file}` on each file after editing.

## Expected Outputs

- `.claude/skills/implement-feature/SKILL.md` — modified
- `plugins/python3-development/skills/development/implement-feature/SKILL.md` — modified (identical changes)
- `.claude/skills/start-task/SKILL.md` — modified
- `plugins/python3-development/skills/development/start-task/SKILL.md` — modified (identical changes)

## Acceptance Criteria

1. Both implement-feature copies contain the conditional MCP-preferred block for ready-tasks.
2. Both implement-feature copies contain a sentence about `task_status_hook.py` GitHub sync on `SubagentStop`.
3. Both start-task copies contain the updated context file JSON example with `parent_issue_number`.
4. Both start-task copies contain the note about omitting `parent_issue_number` when unknown.
5. The changed sections in each pair of copies are identical.
6. `uv run prek run --files {each file}` exits 0 for all four files.

## Verification Steps

1. Run `diff .claude/skills/implement-feature/SKILL.md "plugins/python3-development/skills/development/implement-feature/SKILL.md"` — confirm output is empty (identical files) or if they diverge elsewhere, confirm only the changed sections are identical.
2. Run `diff .claude/skills/start-task/SKILL.md "plugins/python3-development/skills/development/start-task/SKILL.md"` — same check.
3. Run `grep -n "backlog_get_ready_sam_tasks\|parent_issue_number" .claude/skills/implement-feature/SKILL.md` — confirm matches exist.
4. Run `grep -n "parent_issue_number" .claude/skills/start-task/SKILL.md` — confirm match exists.
5. Run `uv run prek run --files .claude/skills/implement-feature/SKILL.md .claude/skills/start-task/SKILL.md "plugins/python3-development/skills/development/implement-feature/SKILL.md" "plugins/python3-development/skills/development/start-task/SKILL.md"` — confirm exit 0.

## Handoff

Return:
- Whether the two pairs of files were already identical before editing (or had existing divergence to preserve)
- Result of `uv run prek run --files` on all four files
- Any sections where the two copies could not be made identical (pre-existing divergence) and how you handled it

---
task_id: "T6"
title: "Write unit tests for operations.py SAM task functions"
status: not-started
agent: python3-development:python-pytest-architect
priority: 2
complexity: Medium
accuracy_risk: low
dependencies:
  - T1
skills:
  - fastmcp-python-tests
  - python3-development
parallelize_with:
  - T5
  - T7
  - T8
  - T9
  - T10
reason: "T6 creates a new test file. No conflict with other tasks."
handoff: "Test file path, count of tests, result of uv run pytest tests/test_backlog_core/test_operations_sam.py."
---

## Context

T1 added four functions to `operations.py`. This task writes unit tests for all four. The test file does not exist yet. The existing test suite for `backlog_core` is in `tests/test_backlog_core/` — follow its conventions for fixtures, imports, and mock patterns.

Files to read before starting:
- `.claude/skills/backlog/backlog_core/operations.py` (after T1 — read the 4 new functions)
- `tests/test_backlog_core/` directory — read one existing test file to understand conventions
- `plan/architect-migrate-sam-task-github-subissues.md` section 7.1 — required test cases

## Objective

Create `tests/test_backlog_core/test_operations_sam.py` with all 11 test cases specified in the architecture testing strategy.

## Required Inputs

- `.claude/skills/backlog/backlog_core/operations.py` (T1 output — functions to test)
- `tests/test_backlog_core/` (existing tests — conventions to follow)
- `plan/architect-migrate-sam-task-github-subissues.md` section 7.1 (required test cases table)
- `plan/codebase/sam-task-migration.md` section 3 (Output type, mock strategy)

## Requirements

1. Create `tests/test_backlog_core/test_operations_sam.py`.
2. Implement all 11 test cases from architecture spec section 7.1:
   - `test_create_sam_task_success`
   - `test_create_sam_task_github_unavailable`
   - `test_create_sam_task_link_failure`
   - `test_get_sam_tasks_online`
   - `test_get_sam_tasks_offline_with_cache`
   - `test_get_sam_tasks_offline_no_cache`
   - `test_get_sam_tasks_writes_cache`
   - `test_update_sam_task_status_success`
   - `test_update_sam_task_status_no_change`
   - `test_get_ready_sam_tasks_dep_resolution`
   - `test_get_ready_sam_tasks_cross_feature_dep`
3. Use `pytest-mock` (`mocker.patch`) to mock `get_github`, `try_get_github`, `create_task_issue`, `get_task_issues`, `update_task_status`. Apply `spec=` when mocking PyGitHub objects.
4. For `test_get_sam_tasks_offline_with_cache`: create a temp cache file using `tmp_path` fixture, populate it with the cache JSON structure from architecture spec section 2.4.
5. For `test_get_sam_tasks_writes_cache`: assert the cache file at `.claude/context/sam-tasks-{slug}.json` was written with valid JSON after a successful `get_sam_tasks` call.
6. For `test_get_ready_sam_tasks_cross_feature_dep`: create tasks where one has `dependencies: ["#479"]` — assert it appears in ready_tasks (cross-feature dep treated as satisfied).
7. For `test_get_ready_sam_tasks_dep_resolution`: create two tasks where T2 depends on T1. T1 status is `not-started` — assert T2 is NOT in ready_tasks. Then set T1 status to `complete` — assert T2 IS in ready_tasks.

## Constraints

- Do not test implementation details of `github.py` — test only `operations.py` function behavior.
- Cache file paths in tests must use `tmp_path` fixture or `monkeypatch` to avoid writing to the real `.claude/context/` directory.
- Each test must be independent — no shared state between tests.
- Use `pytest.raises(GitHubUnavailableError)` for `test_create_sam_task_github_unavailable` (or assert error key in dict if the function catches it — follow the actual `operations.py` behavior from T1).

## Expected Outputs

- `tests/test_backlog_core/test_operations_sam.py` — new file with 11 test functions

## Acceptance Criteria

1. `uv run pytest tests/test_backlog_core/test_operations_sam.py -v` exits 0 with 11 tests collected and passing.
2. All 11 test case names from the architecture spec section 7.1 are present in the file.
3. `test_get_sam_tasks_offline_with_cache` uses `tmp_path` and does not write to the real `.claude/context/` directory.
4. `test_get_ready_sam_tasks_cross_feature_dep` includes a task with `dependencies: ["#479"]` and asserts it is ready.
5. `uv run prek run --files tests/test_backlog_core/test_operations_sam.py` exits 0.

## Verification Steps

1. Run `uv run pytest tests/test_backlog_core/test_operations_sam.py -v` — confirm exit 0 and 11 tests pass.
2. Run `grep -c "^def test_" tests/test_backlog_core/test_operations_sam.py` — confirm output is `11`.
3. Run `uv run prek run --files tests/test_backlog_core/test_operations_sam.py` — confirm exit 0.

## Handoff

Return:
- Test count and result of `uv run pytest tests/test_backlog_core/test_operations_sam.py -v`
- Whether `test_create_sam_task_github_unavailable` uses `pytest.raises` or dict error key (based on how T1 implemented the function)
- Any test cases that required deviation from the spec table

---
task_id: "T7"
title: "Write unit tests for server.py SAM MCP tools"
status: not-started
agent: python3-development:python-pytest-architect
priority: 2
complexity: Low
accuracy_risk: low
dependencies:
  - T2
skills:
  - fastmcp-python-tests
  - python3-development
parallelize_with:
  - T5
  - T6
  - T8
  - T9
  - T10
reason: "T7 creates a new test file. No conflict with other tasks."
handoff: "Test file path, count of tests, result of uv run pytest tests/test_backlog_core/test_server_sam.py."
---

## Context

T2 added four MCP tools to `server.py`. This task writes unit tests for those tools. The test file does not exist yet. The existing test suite for `backlog_core` is in `tests/test_backlog_core/` — follow its conventions.

Files to read before starting:
- `.claude/skills/backlog/backlog_core/server.py` (after T2 — read the 4 new tools)
- `tests/test_backlog_core/` directory — read one existing server test file if present
- `plan/architect-migrate-sam-task-github-subissues.md` section 7.2 — required test cases

## Objective

Create `tests/test_backlog_core/test_server_sam.py` with all 5 test cases specified in the architecture testing strategy.

## Required Inputs

- `.claude/skills/backlog/backlog_core/server.py` (T2 output)
- `tests/test_backlog_core/` (existing tests — conventions)
- `plan/architect-migrate-sam-task-github-subissues.md` section 7.2

## Requirements

1. Create `tests/test_backlog_core/test_server_sam.py`.
2. Implement all 5 test cases from architecture spec section 7.2:
   - `test_backlog_create_sam_task_returns_dict`
   - `test_backlog_create_sam_task_error_key`
   - `test_backlog_get_sam_tasks_shape`
   - `test_backlog_update_sam_task_status_no_op`
   - `test_backlog_get_ready_sam_tasks_shape`
3. Use FastMCP's test client or direct async invocation via `asyncio.run()` — follow whichever pattern the existing test suite uses for server tools.
4. Mock `operations.create_sam_task`, `operations.get_sam_tasks`, etc. using `mocker.patch` — do not call real GitHub APIs.
5. `test_backlog_create_sam_task_error_key`: mock `operations.create_sam_task` to raise `BacklogError("test error")` — assert returned dict has `"error"` key.
6. `test_backlog_update_sam_task_status_no_op`: mock `operations.update_sam_task_status` to return `{"updated": False, "issue_number": 1, "new_status": "complete"}` — assert returned dict has `"updated": False`.
7. `test_backlog_get_ready_sam_tasks_shape`: assert returned dict has keys `"feature"`, `"ready_tasks"`, `"count"`.

## Constraints

- Tests must not make real network calls.
- Use the same test invocation pattern as existing `test_backlog_core/` tests.
- Each test is independent.

## Expected Outputs

- `tests/test_backlog_core/test_server_sam.py` — new file with 5 test functions

## Acceptance Criteria

1. `uv run pytest tests/test_backlog_core/test_server_sam.py -v` exits 0 with 5 tests collected and passing.
2. All 5 test case names from the architecture spec section 7.2 are present.
3. `uv run prek run --files tests/test_backlog_core/test_server_sam.py` exits 0.

## Verification Steps

1. Run `uv run pytest tests/test_backlog_core/test_server_sam.py -v` — confirm exit 0 and 5 tests pass.
2. Run `grep -c "^def test_\|^async def test_" tests/test_backlog_core/test_server_sam.py` — confirm output is `5`.
3. Run `uv run prek run --files tests/test_backlog_core/test_server_sam.py` — confirm exit 0.

## Handoff

Return:
- Test count and result of `uv run pytest tests/test_backlog_core/test_server_sam.py -v`
- Whether async invocation required `asyncio.run()` or a FastMCP test client
- Any deviations from the spec table

---
task_id: "T8"
title: "Write unit tests for implementation_manager.py --github flag"
status: not-started
agent: python3-development:python-pytest-architect
priority: 2
complexity: Medium
accuracy_risk: low
dependencies:
  - T3
skills:
  - fastmcp-python-tests
  - python3-development
parallelize_with:
  - T5
  - T6
  - T7
  - T9
  - T10
reason: "T8 creates a new test file. No conflict with other tasks."
handoff: "Test file path, count of tests, result of uv run pytest tests/test_implementation_manager/test_github_flag.py."
---

## Context

T3 added `--github` and `--parent-issue` flags to `implementation_manager.py`. This task writes unit tests for that new path. The test file does not exist yet. Tests must confirm the new path works and the existing path is unchanged.

Files to read before starting:
- `plugins/python3-development/skills/implementation-manager/scripts/implementation_manager.py` (after T3)
- `tests/test_implementation_manager/` directory — read one existing test file for conventions
- `plan/architect-migrate-sam-task-github-subissues.md` section 7.3 — required test cases

## Objective

Create `tests/test_implementation_manager/test_github_flag.py` with all 7 test cases from the architecture spec.

## Required Inputs

- `plugins/python3-development/skills/implementation-manager/scripts/implementation_manager.py` (T3 output)
- `tests/test_implementation_manager/` (existing tests — conventions)
- `plan/architect-migrate-sam-task-github-subissues.md` section 7.3

## Requirements

1. Create `tests/test_implementation_manager/test_github_flag.py`.
2. Implement all 7 test cases from architecture spec section 7.3:
   - `test_ready_tasks_no_flag_unchanged`
   - `test_ready_tasks_github_online`
   - `test_ready_tasks_github_offline_with_cache`
   - `test_ready_tasks_github_offline_no_cache_no_local`
   - `test_ready_tasks_github_writes_cache`
   - `test_status_github_flag`
   - `test_backlog_core_path_not_found`
3. For `test_ready_tasks_no_flag_unchanged`: invoke the `ready-tasks` command without `--github` using the Typer test runner or subprocess. Mock file-system reads to return a fixed task list. Assert the JSON output shape is identical to pre-T3 behavior.
4. For `test_ready_tasks_github_online`: patch `fetch_tasks_from_github` to return a mock `list[Task]`. Assert output JSON has `"ready_tasks"` key.
5. For `test_ready_tasks_github_offline_with_cache`: patch `try_get_github` to return `None`; provide a temp cache file. Assert output uses cached tasks.
6. For `test_ready_tasks_github_offline_no_cache_no_local`: patch GitHub unavailable, no cache, no local files. Assert output has `"error"` key and process exits 1.
7. For `test_ready_tasks_github_writes_cache`: after `--github` call with mock online GitHub, assert cache file at `tmp_path / "sam-tasks-{slug}.json"` was written.
8. For `test_backlog_core_path_not_found`: monkeypatch `_BACKLOG_CORE.exists()` to return False. Assert `--github` falls back to local files (no crash).

## Constraints

- No real GitHub API calls in any test.
- Use `tmp_path` for cache files — do not write to `.claude/context/`.
- Each test is independent.

## Expected Outputs

- `tests/test_implementation_manager/test_github_flag.py` — new file with 7 test functions

## Acceptance Criteria

1. `uv run pytest tests/test_implementation_manager/test_github_flag.py -v` exits 0 with 7 tests passing.
2. All 7 test case names from architecture spec section 7.3 are present.
3. `uv run prek run --files tests/test_implementation_manager/test_github_flag.py` exits 0.
4. `test_ready_tasks_no_flag_unchanged` does not import `backlog_core` and does not call any GitHub mock.

## Verification Steps

1. Run `uv run pytest tests/test_implementation_manager/test_github_flag.py -v` — confirm exit 0 and 7 tests pass.
2. Run `grep -c "^def test_" tests/test_implementation_manager/test_github_flag.py` — confirm output is `7`.
3. Run `uv run prek run --files tests/test_implementation_manager/test_github_flag.py` — confirm exit 0.

## Handoff

Return:
- Test count and result of `uv run pytest tests/test_implementation_manager/test_github_flag.py -v`
- What invocation method was used (Typer test runner, subprocess, or direct function call)
- Any deviations from the spec table

---
task_id: "T9"
title: "Write tests for task_status_hook.py GitHub sync (unit + integration)"
status: not-started
agent: python3-development:python-pytest-architect
priority: 2
complexity: Medium
accuracy_risk: low
dependencies:
  - T4
skills:
  - fastmcp-python-tests
  - python3-development
parallelize_with:
  - T5
  - T6
  - T7
  - T8
  - T10
reason: "T9 creates two new test files. No conflict with other tasks."
handoff: "Test file paths, count of tests, result of uv run pytest on both files."
---

## Context

This task was merged from two candidate tasks (unit tests and integration test for `task_status_hook.py`) to avoid file conflicts. Both test files live in `tests/test_task_status_hook/` and cover T4's changes.

T4 added `get_parent_issue_number()` and `sync_completion_to_github()` to `task_status_hook.py`, and called `sync_completion_to_github()` as the final step of `handle_subagent_stop`. This task writes 8 unit tests and one integration test scenario across two test files.

Files to read before starting:
- `plugins/python3-development/skills/implementation-manager/scripts/task_status_hook.py` (after T4)
- `tests/test_task_status_hook/` directory — read existing test files for conventions
- `plan/architect-migrate-sam-task-github-subissues.md` sections 7.4 and 7.5 — required test cases

## Objective

Create `tests/test_task_status_hook/test_github_sync.py` (8 unit tests) and `tests/test_task_status_hook/test_subagent_stop_integration.py` (1 integration test with 2 scenario variants).

## Required Inputs

- `plugins/python3-development/skills/implementation-manager/scripts/task_status_hook.py` (T4 output)
- `tests/test_task_status_hook/` (existing tests — conventions)
- `plan/architect-migrate-sam-task-github-subissues.md` sections 7.4 and 7.5
- `plan/codebase/sam-task-migration.md` section 1 (context file format, hook event JSON structure)

## Requirements

### test_github_sync.py — 8 unit tests

1. `test_sync_completion_called_after_local_write`: patch `task_format` write function and `sync_completion_to_github` as a mock. Invoke `handle_subagent_stop` with a valid hook input. Assert `sync_completion_to_github` was called after the local write (use `call_args` or ordering via `side_effect`).
2. `test_sync_completion_no_github_issue_field`: create a temp task YAML without `github_issue` field. Call `sync_completion_to_github(task_path, "T1", 480)`. Assert `backlog_core.github.update_task_status` was NOT called. Assert exit without error (function returns None).
3. `test_sync_completion_github_success`: create a temp task YAML with `github_issue: 481`. Patch `backlog_core.github.get_github` to return a mock repo. Patch `backlog_core.github.update_task_status` to return `True`. Call `sync_completion_to_github`. Assert `update_task_status` was called with `(mock_repo, 481, "complete")`.
4. `test_sync_completion_github_exception`: patch `update_task_status` to raise `GithubException`. Assert function returns None (does not raise) and writes warning to stderr.
5. `test_sync_completion_get_github_unavailable`: patch `get_github` to raise `GitHubUnavailableError`. Assert function returns None (does not raise).
6. `test_get_parent_issue_number_from_context`: create a temp context file with `{"task_file_path": "...", "task_id": "T1", "parent_issue_number": 480}`. Call `get_parent_issue_number(hook_input)`. Assert returns `480`.
7. `test_get_parent_issue_number_absent`: call `get_parent_issue_number` with a context file that lacks `parent_issue_number`. Assert returns `None`.
8. `test_activity_update_no_github_call`: invoke `handle_activity_update` with a valid PostToolUse hook input. Assert no function from `backlog_core` or `update_task_status` was called.

### test_subagent_stop_integration.py — 1 integration test (2 variants)

9. `test_subagent_stop_full_path_with_github_sync` (success variant):
   - Create a temp task YAML with `github_issue: 481` and `status: in-progress`.
   - Create a temp context file with `parent_issue_number: 480`.
   - Construct hook input dict with `hook_event_name: SubagentStop` and a prompt containing `/start-task {path} --task T1`.
   - Patch `backlog_core.github.get_github` to return a mock repo.
   - Patch `backlog_core.github.update_task_status` to return `True`.
   - Call `handle_subagent_stop(hook_input)` directly.
   - Assert: local YAML `status` is `complete`, `completed` field is set, context file deleted, `update_task_status` called once with `(mock_repo, 481, "complete")`.

10. `test_subagent_stop_full_path_github_failure` (failure variant — same setup, `update_task_status` raises `GithubException`):
    - Assert: local YAML still has `status: complete` (local write succeeded), `update_task_status` was called, function returns without raising, warning appears in captured stderr.

## Constraints

- Use `tmp_path` for all temp files — no writes to the real `.claude/context/` directory.
- `test_activity_update_no_github_call` must not require `backlog_core` to be on sys.path.
- Each test is independent.
- Mock `backlog_core.github` at the module level or via `sys.modules` injection if conditional import makes patching difficult.

## Expected Outputs

- `tests/test_task_status_hook/test_github_sync.py` — new file with 8 test functions
- `tests/test_task_status_hook/test_subagent_stop_integration.py` — new file with 2 test functions

## Acceptance Criteria

1. `uv run pytest tests/test_task_status_hook/test_github_sync.py -v` exits 0 with 8 tests passing.
2. `uv run pytest tests/test_task_status_hook/test_subagent_stop_integration.py -v` exits 0 with 2 tests passing.
3. `test_sync_completion_github_exception` does not raise — asserts function returns `None`.
4. `test_subagent_stop_full_path_github_failure` asserts local YAML status is `complete` despite GitHub failure.
5. `uv run prek run --files tests/test_task_status_hook/test_github_sync.py tests/test_task_status_hook/test_subagent_stop_integration.py` exits 0.

## Verification Steps

1. Run `uv run pytest tests/test_task_status_hook/test_github_sync.py -v` — confirm 8 passing.
2. Run `uv run pytest tests/test_task_status_hook/test_subagent_stop_integration.py -v` — confirm 2 passing.
3. Run `uv run prek run --files tests/test_task_status_hook/test_github_sync.py tests/test_task_status_hook/test_subagent_stop_integration.py` — confirm exit 0.

## Handoff

Return:
- Test counts and `uv run pytest` results for both files
- Whether `backlog_core.github` mock required `sys.modules` injection (due to conditional import in T4)
- Any deviations from the test cases in sections 7.4 and 7.5

---
task_id: "T10"
title: "Write migrate_tasks_to_github.py script and its tests"
status: not-started
agent: python3-development:python-cli-architect
priority: 2
complexity: Medium
accuracy_risk: medium
dependencies:
  - T2
skills:
  - python3-development
parallelize_with:
  - T5
  - T6
  - T7
  - T8
  - T9
reason: "T10 creates two new files. No conflict with other tasks."
handoff: "Script path, test file path, result of uv run pytest tests/test_migrate_tasks_to_github.py, dry-run smoke test output."
---

## Context

The migration script creates GitHub sub-issues for tasks already tracked in local `plan/tasks-*.md` files — for in-flight features that pre-date this feature. It is an operator-run, one-time script. Auto-migration on first `implement-feature` invocation is explicitly out of scope.

T2 has made `create_task_issue` available via MCP tools and `operations.py`. The migration script calls `github.py` functions directly (not via MCP) because it runs standalone, not inside the Claude Code MCP context.

Files to read before starting:
- `plan/architect-migrate-sam-task-github-subissues.md` sections 6.1–6.6 — script algorithm, idempotency, task type inference, dry-run
- `plan/architect-migrate-sam-task-github-subissues.md` section 7.6 — test cases
- `plugins/python3-development/scripts/` — read one existing script for PEP 723 inline metadata pattern

## Objective

Create `plugins/python3-development/scripts/migrate_tasks_to_github.py` (standalone migration script) and `tests/test_migrate_tasks_to_github.py` (6 test cases), following the algorithm in architecture spec section 6.

## Required Inputs

- `plan/architect-migrate-sam-task-github-subissues.md` sections 6.1–6.6 and 7.6
- `plugins/python3-development/scripts/` (existing scripts — PEP 723 metadata pattern)
- `.claude/skills/backlog/backlog_core/github.py` (Phase 1 functions: `create_task_issue`, `get_github`)
- `.claude/skills/backlog/backlog_core/models.py` (`SamTask` fields)
- `plan/codebase/sam-task-migration.md` section 2 (`SamTask` model fields, section 6 migration strategy)

## Requirements

### Script: migrate_tasks_to_github.py

1. PEP 723 inline script metadata block at top of file:

   ```python
   # /// script
   # requires-python = ">=3.11"
   # dependencies = ["typer", "ruamel.yaml", "PyGithub"]
   # ///
   ```

2. CLI interface via Typer:
   - `--task-file PATH` (required): path to task file or directory
   - `--parent-issue INT` (required): parent story issue number
   - `--dry-run` (flag): print actions without making API calls or file writes
   - `--label TEXT` (optional, multiple): GitHub label names to apply to created issues

3. Read task file(s) using the `task_format.py` parse pattern (or copy the relevant logic — do not import `implementation_manager.py` directly as it has a `typer` app that would conflict).

4. Process tasks in topological order (dependency-first). Implement a simple topological sort over `task.dependencies` — if a cycle is detected, print warning and process in file order.

5. For each task:
   a. If YAML frontmatter already has `github_issue: N` field: skip with message `"Skipping {task.id} — already has github_issue: {N}"`.
   b. Build `SamTask` from task fields: `task_id=task.id`, `feature=derived_slug`, `task_type=infer_task_type(task.name)`, `agent=task.agent or ""`, `priority=int(task.priority)`, `skills=task.skills`, `dependencies=task.dependencies`, `status=task.status`.
   c. In `--dry-run` mode: print `"Would create: [{feature}/{task_id}] {task_type}: {task.name}"` — no API calls.
   d. In live mode: call `create_task_issue(repo, parent_issue_number, sam_task, description=task.name, acceptance_criteria=[], labels=labels)`.
   e. On success: write `github_issue: N` back to task YAML frontmatter using `ruamel.yaml`.
   f. On failure: print warning, continue to next task.

6. Implement `infer_task_type(title: str) -> str` with the heuristics from architecture spec section 6.5. Default is `"implement"`.

7. After all tasks processed: write `.claude/context/sam-tasks-{slug}.json` cache from created issues (only in live mode, not `--dry-run`).

8. Print summary: `"{N} created, {M} skipped, {K} failed"`.

### Tests: test_migrate_tasks_to_github.py

9. Create `tests/test_migrate_tasks_to_github.py` with 6 test cases from architecture spec section 7.6:
   - `test_dry_run_no_writes`
   - `test_skips_already_migrated`
   - `test_writes_github_issue_field`
   - `test_task_type_inference`
   - `test_partial_failure_continues`
   - `test_writes_cache_file`

10. For `test_dry_run_no_writes`: invoke script with `--dry-run`; patch `create_task_issue` as a mock; assert mock was not called and no files were written.
11. For `test_skips_already_migrated`: create a task YAML with `github_issue: 100`; assert `create_task_issue` not called for that task.
12. For `test_writes_github_issue_field`: mock `create_task_issue` to return a mock Issue with `.number = 481`; assert task YAML has `github_issue: 481` after invocation.
13. For `test_task_type_inference`: test each heuristic from spec section 6.5 directly via `infer_task_type()`.
14. For `test_partial_failure_continues`: mock `create_task_issue` to raise on the first call, succeed on the second; assert second task's `github_issue` field is written.
15. For `test_writes_cache_file`: after successful migration, assert `.claude/context/sam-tasks-{slug}.json` exists and contains valid JSON with `"tasks"` key.

## Constraints

- Do not use `shell=True`.
- Use `ruamel.yaml` for all YAML writes — not `pyyaml`.
- Do not import `implementation_manager.py` at module level in the migration script.
- `--dry-run` must produce zero file writes and zero GitHub API calls.
- `backlog_core` is added to sys.path using the same conditional pattern established in T3/T4.

## Expected Outputs

- `plugins/python3-development/scripts/migrate_tasks_to_github.py` — new file
- `tests/test_migrate_tasks_to_github.py` — new file with 6 test functions

## Acceptance Criteria

1. `uv run plugins/python3-development/scripts/migrate_tasks_to_github.py --help` exits 0 and shows `--task-file`, `--parent-issue`, `--dry-run`, `--label` options.
2. `uv run plugins/python3-development/scripts/migrate_tasks_to_github.py --task-file {path} --parent-issue 480 --dry-run` exits 0 and prints `"Would create:"` lines without making API calls.
3. `uv run pytest tests/test_migrate_tasks_to_github.py -v` exits 0 with 6 tests passing.
4. `test_dry_run_no_writes` asserts no files are written and no API calls are made.
5. `uv run prek run --files plugins/python3-development/scripts/migrate_tasks_to_github.py tests/test_migrate_tasks_to_github.py` exits 0.

## Verification Steps

1. Run `uv run plugins/python3-development/scripts/migrate_tasks_to_github.py --help` — confirm exit 0 and options visible.
2. Run `uv run pytest tests/test_migrate_tasks_to_github.py -v` — confirm exit 0 and 6 tests pass.
3. Run `uv run prek run --files plugins/python3-development/scripts/migrate_tasks_to_github.py tests/test_migrate_tasks_to_github.py` — confirm exit 0.
4. Inspect the PEP 723 metadata block — confirm `PyGithub`, `ruamel.yaml`, `typer` are listed as dependencies.

## CoVe Checks

Key claims to verify:

- `ruamel.yaml` preserves existing YAML frontmatter fields (other than `github_issue`) when adding a new field to an existing task file.
- `task_format.py` has a function that parses a single-file multi-task `.md` file (multiple `---` blocks) — confirm it exists and is usable standalone without the full `implementation_manager.py` app.

Verification questions:

1. Does `task_format.py` expose a parse function that accepts a file path and returns a list of task dicts, usable without instantiating a Typer app?
2. Does `ruamel.yaml` round-trip existing YAML comments and field order when adding a new key?

Evidence to collect:

- Read `task_format.py` and list all public functions and their signatures.
- Read `ruamel.yaml` round-trip example from existing codebase (grep for `ruamel` in `parsing.py` or `task_format.py`).

Revision rule: If `task_format.py` cannot be imported standalone, copy only the needed parsing logic directly into the migration script and document this in the handoff.

## Handoff

Return:
- Whether `task_format.py` was importable standalone or logic was inlined
- Result of `uv run plugins/python3-development/scripts/migrate_tasks_to_github.py --help`
- Result of `uv run pytest tests/test_migrate_tasks_to_github.py -v`
- Result of `uv run prek run --files` on both new files
