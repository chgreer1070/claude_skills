# Feature Context: Migrate SAM Task Tracking to GitHub Sub-Issues

## Document Metadata

- **Generated**: 2026-03-06
- **Input Type**: simple_description
- **Source**: Feature request — backlog item #480
- **Status**: DISCOVERY_COMPLETE

---

## Original Request

Migrate SAM task tracking from local markdown files to GitHub sub-issues via backlog MCP (#480).

The SAM workflow splits task tracking across two systems: GitHub Issues (via backlog MCP) for stories/backlog items, and local `plan/tasks-*.md` files for task status, managed by `implementation_manager.py` and `task_status_hook.py`. This causes drift: task status in local markdown can diverge from the GitHub story issue, making it impossible to know task progress from GitHub alone.

Desired outcome: Unify task state in GitHub sub-issues via the backlog MCP. Task progress visible in GitHub. Single source of truth. No drift.

---

## Problem Statement

### What Exists Today

The SAM implementation workflow maintains two separate tracking systems:

1. **GitHub Issues (story level)** — managed by the backlog MCP via `.claude/skills/backlog/backlog_core/`. Each feature has a parent story issue. Labels track `status:in-progress` at the story level only.

2. **Local markdown task files** — `plan/tasks-{N}-{slug}.md` files (YAML frontmatter format). Each task has `status`, `started`, `completed`, `last_activity` fields written locally by:
   - `task_status_hook.py` — hook script that responds to `SubagentStop` (marks complete) and `PostToolUse` (updates `last_activity`)
   - `implementation_manager.py` CLI — queries `status`, `ready-tasks`, `validate` for orchestrator consumption

3. **Local cache pattern** — the backlog MCP already uses `.claude/backlog/*.md` as a local cache of GitHub Issues. Task files follow a similar pattern but with no GitHub sync.

### Observable Pain Points

- GitHub story issue shows no sub-task breakdown or per-task progress
- Task status in `plan/tasks-*.md` can diverge from any GitHub representation
- No way to see which tasks are complete, in-progress, or blocked from GitHub
- Two mental models: story-level issues (GitHub) and task-level files (local only)
- When a session ends abruptly, task state may only be in local files

---

## Desired Outcome

From the outside, when this feature is complete:

1. Each SAM task appears as a GitHub sub-issue under its parent story issue
2. Checking the parent story issue in GitHub shows a sub-issue checklist with per-task completion status
3. The backlog MCP exposes MCP tools to create, query, and update task sub-issues
4. `implementation_manager.py` queries GitHub sub-issues (via cache) instead of local YAML-only files for task status
5. `task_status_hook.py` writes status to local cache AND syncs to GitHub on `SubagentStop` (completion events)
6. `PostToolUse` (LastActivity updates) writes local cache only — no GitHub API call per keystroke
7. Skill docs (`implement-feature`, `start-task`) reflect the new query and write paths

---

## Scope Boundary

### In Scope

- Expose `create_task_issue`, `get_task_issues`, `update_task_status` as MCP tools in `server.py`
- Replace `implementation_manager.py` query path to read from GitHub sub-issue cache
- Update `task_status_hook.py` write path: local cache + GitHub sync on `SubagentStop`
- Update `implement-feature` SKILL.md and `start-task` SKILL.md docs for the new data flow
- A migration/backfill path for existing task files (creating sub-issues for already-tracked tasks) — scope TBD

### Explicitly Out of Scope

- Changing the `get_ready_tasks()` dependency resolution logic (stays local, unchanged)
- Implementing GitHub Projects v2 (Option C from research was rejected)
- Removing local task files entirely — they remain as the local cache (same pattern as backlog MCP)
- Changing the `SamTask` model, `parse_sam_task_metadata`, `build_sam_task_body`, `build_sam_task_issue_title` (Phase 1 complete, commit 30066de)

---

## Phase 1 Completion Summary

Phase 1 is COMPLETE (commit 30066de). The following already exist and must not be re-implemented:

### `models.py` — `SamTask` Pydantic model

Location: `.claude/skills/backlog/backlog_core/models.py:233-263`

Fields: `task_id`, `feature`, `task_type`, `status` (default `"not-started"`), `agent`, `priority` (int 1-5), `skills` (list), `dependencies` (list of feature-scoped task IDs or `#N` cross-feature refs).

### `parsing.py` — SAM task parse/build functions

Location: `.claude/skills/backlog/backlog_core/parsing.py:873-968`

- `parse_sam_task_metadata(body)` — extracts `SamTask` from `<!-- sam:task ... -->` HTML comment block
- `build_sam_task_body(task, description, acceptance_criteria)` — builds issue body with human-readable sections + invisible YAML block
- `build_sam_task_issue_title(task, description)` — format: `[{feature}/{task_id}] {task_type}: {description}`

### `github.py` — sub-issue CRUD functions

Location: `.claude/skills/backlog/backlog_core/github.py:454-581`

- `create_task_issue(repo, parent_issue_number, task, description, acceptance_criteria, labels, output)` — creates issue + links as sub-issue via `parent.add_sub_issue(task_issue)` (passes Issue object, not `.number`, per PyGitHub Issue.py line 588 requirement)
- `get_task_issues(repo, parent_issue_number, output)` — returns sub-issues sorted by `priority_position`
- `update_task_status(repo, issue_number, new_status, output)` — patches `status:` inside `<!-- sam:task ... -->` block via regex

---

## Phases 2–4 Summary

### Phase 2: Expose sub-issue functions as MCP tools in `server.py`

**File**: `.claude/skills/backlog/backlog_core/server.py`

**Current state**: Server has 10 tools (`backlog_add`, `backlog_list`, `backlog_view`, `backlog_sync`, `backlog_close`, `backlog_resolve`, `backlog_update`, `backlog_groom`, `backlog_normalize`, `backlog_pull`). None expose SAM task sub-issue operations.

**Target**: Add MCP tools wrapping:
- `create_task_issue` → new tool (e.g., `backlog_create_task`)
- `get_task_issues` → new tool (e.g., `backlog_get_tasks`)
- `update_task_status` → new tool (e.g., `backlog_update_task_status`)

Tool signatures must follow the existing `server.py` pattern: async function, `Annotated` parameters with `Field(description=...)`, `Output` collector, `asyncio.to_thread()` for blocking calls.

### Phase 3: Replace `implementation_manager.py` query path

**File**: `plugins/python3-development/skills/implementation-manager/scripts/implementation_manager.py`

**Current state**: Reads task status exclusively from local YAML frontmatter files. Key functions: `get_ready_tasks()` (lines ~770-799), `status` command, `ready-tasks` command.

**Target**: `ready-tasks` and `status` commands query GitHub sub-issues (via local cache). The `get_ready_tasks()` function logic is unchanged — it still does local DAG resolution over a `list[Task]`. The change is in how that list is populated: from GitHub sub-issue cache instead of (or in addition to) local YAML files.

**Caching concern**: The query path needs a local cache of sub-issue data (analogous to `.claude/backlog/*.md`) that `implementation_manager.py` can read offline. The sync mechanism between local cache and GitHub is part of this phase.

### Phase 4: Update `task_status_hook.py` write path

**File**: `plugins/python3-development/skills/implementation-manager/scripts/task_status_hook.py`

**Current state**: `handle_subagent_stop` writes COMPLETE + timestamp to local YAML file only. `handle_activity_update` (PostToolUse) writes `last_activity` to local YAML file only.

**Target** (per design decision):
- `PostToolUse` (LastActivity): write local cache only — no GitHub API call
- `SubagentStop` (completion): write local cache AND call `update_task_status()` from `github.py` to sync completion to GitHub sub-issue

### Phase 5: Update skill docs

**Files**:
- `.claude/skills/implement-feature/SKILL.md`
- `.claude/skills/start-task/SKILL.md`
- `plugins/python3-development/skills/development/implement-feature/SKILL.md`
- `plugins/python3-development/skills/development/start-task/SKILL.md`

**Target**: Update documentation to reflect that `implementation_manager.py` now reads from GitHub sub-issue cache, and that `task_status_hook.py` syncs to GitHub on SubagentStop.

---

## Key Constraints and Design Decisions

### Decision 1: Dependency model — Option B (accepted)

Dependencies stored in `<!-- sam:task YAML -->` block in issue body, referencing other sub-issue numbers. `get_ready_tasks()` logic stays local. Source: `plan/research/comparison-github-task-dependency-options.md` (generated 2026-03-06).

### Decision 2: Offline strategy (accepted)

Same as current backlog MCP: local files are cache; hooks write to local cache + sync to GitHub when available. `PostToolUse` (LastActivity) writes local only. `SubagentStop` (completion) syncs to GitHub.

### Decision 3: Preview API risk (accepted)

GitHub sub-issues API is accepted as a known risk. Build now; fall back to Option A (body cross-refs) if sub-issues are unavailable on the repo plan.

### Constraint: `.id` vs `.number` requirement

`add_sub_issue()` requires passing the Issue object, not `.id` or `.number` (both are integers, no type error). This is documented in PyGitHub Issue.py line 588 and already handled in Phase 1's `create_task_issue()`.

### Constraint: Two-file skill copies

Each skill exists in two locations: `.claude/skills/` (local) and `plugins/python3-development/skills/development/` (plugin). Both copies must be updated in Phase 5.

### Constraint: `task_format.py` dependency

`task_status_hook.py` and `implementation_manager.py` both import from `task_format.py` (sibling module in `scripts/`). Any changes to write path must preserve this import contract.

---

## Codebase Research

### Similar Patterns Found

#### Pattern 1: Backlog MCP local cache + GitHub sync

- **Location**: `.claude/skills/backlog/backlog_core/github.py:390-423` (`sync_groomed_to_github_issue`)
- **Relevance**: Establishes the pattern: local file is cache, GitHub is source of truth, sync writes to GitHub when available
- **Reusable**: `try_get_github()` for optional GitHub sync, `GithubException` handling, `Output` collector pattern

#### Pattern 2: `operations.py` as intermediary layer

- **Location**: `.claude/skills/backlog/backlog_core/` (referenced from `server.py` as `from . import operations`)
- **Relevance**: New MCP tools should call through `operations.py` functions, not call `github.py` directly from `server.py`
- **Reusable**: The pattern of `server.py` → `operations.py` → `github.py` is established for all existing tools

#### Pattern 3: `task_status_hook.py` SubagentStop handler

- **Location**: `plugins/python3-development/skills/implementation-manager/scripts/task_status_hook.py:396-447`
- **Relevance**: This is the exact write path to extend for GitHub sync on completion
- **Reusable**: `_resolve_task_file`, `update_task_status` (local), `get_iso_timestamp` can remain; add GitHub sync call after local write

#### Pattern 4: `implementation_manager.py` `get_ready_tasks()`

- **Location**: `plugins/python3-development/skills/implementation-manager/scripts/implementation_manager.py` (lines ~770-799 per research doc)
- **Relevance**: This function is explicitly preserved unchanged — it receives `list[Task]` and returns ready tasks
- **Reusable**: Input type `list[Task]` is what changes; function body stays identical

#### Pattern 5: `server.py` tool pattern

- **Location**: `.claude/skills/backlog/backlog_core/server.py:17-53` (`backlog_add` as exemplar)
- **Relevance**: All new MCP tools must follow this exact pattern: `@mcp.tool()`, `async def`, `Annotated` params, `Output()`, `asyncio.to_thread()`, return `{**result, **out.to_dict()}`
- **Reusable**: Direct template for Phase 2 new tools

---

## Use Scenarios

### Scenario 1: Orchestrator queries ready tasks after GitHub sync

**Actor**: `implement-feature` skill / orchestrator
**Trigger**: Orchestrator starts an implementation loop for a feature with an associated story issue
**Goal**: Get a list of tasks ready to execute, sourced from GitHub sub-issues
**Expected Outcome**: `implementation_manager.py ready-tasks` returns JSON list of tasks that have `not-started` status and satisfied dependencies, where task data comes from cached GitHub sub-issues

### Scenario 2: Task completes — GitHub sub-issue updated

**Actor**: `task_status_hook.py` SubagentStop handler
**Trigger**: Sub-agent finishes a task; `SubagentStop` hook fires
**Goal**: Mark task complete in both local cache and GitHub
**Expected Outcome**: Local task file updated to `complete` with timestamp; GitHub sub-issue `<!-- sam:task -->` block updated with `status: complete` via `update_task_status()`

### Scenario 3: Developer checks story progress in GitHub

**Actor**: Developer (human)
**Trigger**: Wants to know which tasks are done, in-progress, or blocked without running CLI
**Goal**: View task completion status from GitHub UI
**Expected Outcome**: Parent story issue shows sub-issue checklist; individual sub-issues show `status: complete/in-progress/not-started` in their `<!-- sam:task -->` block; labels or issue state reflect current execution phase

### Scenario 4: New feature plan creates task sub-issues

**Actor**: `add-new-feature` workflow / orchestrator
**Trigger**: A new task plan file (`plan/tasks-{N}-{slug}.md`) is created for a feature with a parent story issue
**Goal**: Initialize GitHub sub-issues for each task in the plan
**Expected Outcome**: One GitHub sub-issue per task, linked as sub-issue of the parent story, with `SamTask` metadata in the invisible block; `priority_position` reflects task execution order

### Scenario 5: Offline execution — local cache used

**Actor**: `task_status_hook.py` PostToolUse handler
**Trigger**: Agent makes an edit during task execution; no GitHub token or network
**Goal**: Update LastActivity without failing
**Expected Outcome**: Local task file updated with new `last_activity` timestamp; no GitHub API call attempted; no error surfaced to agent

---

## Gap Analysis

### Identified Gaps

| # | Category | Gap Description | Impact |
|---|----------|-----------------|--------|
| 1 | Scope | Migration path for existing task files — create sub-issues for tasks already tracked locally | Existing in-progress features will not appear in GitHub until migrated |
| 2 | Scope | Where is the GitHub sub-issue cache stored? Local task file itself? Separate cache dir? | `implementation_manager.py` needs a defined path to read from |
| 3 | Behavior | What happens when `get_task_issues()` fails (offline, API unavailable)? Fall back to local file, or error? | Determines whether offline task execution continues uninterrupted |
| 4 | Behavior | When `task_status_hook.py` SubagentStop calls `update_task_status()` and GitHub is unavailable — silent skip or log warning? | Determines whether completion is lost vs. queued for later sync |
| 5 | Integration | `implementation_manager.py` imports only from `task_format.py` (no backlog_core dependency). Adding GitHub sync requires adding `backlog_core` as a dependency or providing a thin wrapper | Dependency graph change; may require script path additions or packaging |
| 6 | Scope | Do the `plugins/python3-development/skills/development/` copies of SKILL.md files need to stay in sync with `.claude/skills/` copies, or are they independent? | Affects how many files Phase 5 must update |

---

## Questions Requiring Resolution

### Q1: Local cache location for GitHub sub-issue data

- **Category**: Integration
- **Gap**: `implementation_manager.py` currently reads only from local YAML task files. If GitHub sub-issues replace the source of truth, what is the local cache format and where does it live?
- **Question**: Should the existing `plan/tasks-*.md` files continue to serve as the local cache (enriched with GitHub issue numbers), or should a separate cache directory be introduced (e.g., `.claude/cache/tasks/`)?
- **Options**:
  - A) Enrich existing `plan/tasks-*.md` YAML frontmatter with `github_issue: N` field; `implementation_manager.py` reads from these files as before
  - B) Introduce a separate cache layer analogous to `.claude/backlog/*.md` per-task files
- **Why It Matters**: Determines the scope of changes to `implementation_manager.py` and the data flow for Phase 3
- **Resolution**: _pending_

### Q2: `implementation_manager.py` dependency on `backlog_core`

- **Category**: Integration
- **Gap**: `implementation_manager.py` currently has no dependency on `.claude/skills/backlog/backlog_core/`. Adding GitHub sync requires either importing `github.py` functions or duplicating the GitHub call logic.
- **Question**: Is adding `backlog_core` as a dependency to `implementation_manager.py` acceptable? Or should the GitHub sync calls stay entirely in `task_status_hook.py` and be injected via a separate sync script?
- **Options**:
  - A) Add `backlog_core` to `sys.path` in `implementation_manager.py` (similar to how `task_format` is added)
  - B) GitHub sync stays in `task_status_hook.py` only; `implementation_manager.py` reads local cache exclusively
- **Why It Matters**: Option B means `implementation_manager.py` never needs to know about GitHub; Option A couples it to `backlog_core`
- **Resolution**: _pending_

### Q3: Handling GitHub unavailability in SubagentStop completion sync

- **Category**: Behavior
- **Gap**: Design decision says SubagentStop syncs to GitHub, but GitHub may be offline or token absent
- **Question**: When `update_task_status()` fails during SubagentStop, should the hook: (a) log a warning and exit 0 (task marked complete locally, sync deferred), or (b) exit 2 (signal error, task remains in-progress)?
- **Options**:
  - A) Log warning, exit 0 — local completion is authoritative, GitHub sync is best-effort
  - B) Exit 2 — force re-run until GitHub sync succeeds
- **Why It Matters**: Exit 2 blocks orchestrator progression; exit 0 may leave GitHub out of sync until next manual sync
- **Resolution**: _pending_ (design preference for A given offline strategy decision already accepted)

### Q4: Migration path for in-flight task files

- **Category**: Scope
- **Gap**: Existing `plan/tasks-*.md` files have no GitHub sub-issue equivalents
- **Question**: Is a migration/backfill operation in scope for this feature? If yes, should it be automated (run on first `implement-feature` invocation) or manual (operator runs a script)?
- **Options**:
  - A) In scope — auto-migrate on first use when parent story issue exists and sub-issues are absent
  - B) In scope — explicit script `migrate_tasks_to_github.py` operator runs once
  - C) Out of scope — only new task plans get sub-issues; existing files continue with local-only tracking
- **Why It Matters**: Affects whether existing in-flight features gain GitHub visibility
- **Resolution**: _pending_

### Q5: `operations.py` intermediary for new MCP tools

- **Category**: Integration
- **Gap**: Server pattern routes through `operations.py`; no `operations.py` functions exist for SAM task sub-issue operations
- **Question**: Should Phase 2 add thin operation functions in `operations.py` (following existing pattern), or call `github.py` functions directly from `server.py` for the new SAM task tools?
- **Options**:
  - A) Add `create_task`, `get_tasks`, `update_task_status` functions to `operations.py`
  - B) Call `github.py` directly from `server.py` for these tools (pattern deviation)
- **Why It Matters**: Option A maintains architectural consistency; Option B is faster but creates an inconsistency
- **Resolution**: _pending_ (design preference for A for consistency)

---

## Goals (Pending Resolution)

_These goals will be finalized after questions are resolved._

1. Backlog MCP exposes MCP tools for SAM task sub-issue create, query, and status update operations
2. `implementation_manager.py` `status` and `ready-tasks` commands source task data from GitHub sub-issue cache
3. `task_status_hook.py` SubagentStop handler syncs task completion to GitHub sub-issue
4. `task_status_hook.py` PostToolUse handler continues writing LastActivity to local cache only
5. `implement-feature` and `start-task` SKILL.md files reflect the new data flow
6. Offline operation is preserved — local cache serves as fallback when GitHub is unavailable

---

## Next Steps

After questions are resolved:

1. Update "Resolution" fields in Questions section
2. Finalize Goals section
3. Proceed to RT-ICA assessment
4. Then proceed to architecture design (`python-cli-design-spec` agent)
