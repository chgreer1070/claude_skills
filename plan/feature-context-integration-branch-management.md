# Feature Context: Integration Branch Management

## Document Metadata

- **Generated**: 2026-03-20
- **Input Type**: existing_document
- **Source**: `.claude/reports/milestone-orchestration-design-20260320.md` + orchestrator observations
- **Status**: DISCOVERY_COMPLETE
- **Story Issue**: #919

---

## Original Request

The milestone orchestration system (`/work-milestone` and `/groom-milestone` skills, to be created) requires integration branch lifecycle management via PyGithub. No branch management functions exist in the project tooling today. The design doc at `.claude/reports/milestone-orchestration-design-20260320.md` specifies the integration branch pattern (adopted from gastown research). PyGithub is already in use across the project. The primary GitHub module is `plugins/development-harness/backlog_core/github.py`.

Scope: branch lifecycle operations — create from main, get status, merge to main, delete, list — for branches named `milestone/{N}-{slug}`.

---

## Core Intent Analysis

### WHO (Target Users)

- **`/work-milestone` skill** (to be created) — primary consumer. Creates an integration branch at workflow start, merges worker branches into it during execution, lands it to main at completion, then deletes it.
- **`/groom-milestone` skill** (to be created) — reads integration branch name for the dispatch plan YAML (`integration_branch` field). May check whether a stale branch already exists before writing the plan.
- **Milestone orchestrator** (the Claude session running `/work-milestone`) — needs to know branch existence and HEAD SHA to make merge slot decisions.

### WHAT (Desired Outcome)

A set of functions in `plugins/development-harness/backlog_core/github.py` (or a new sibling module) that allow the milestone orchestration skills to:

1. Create a branch named `milestone/{N}-{slug}` from the current HEAD of `main`
2. Check whether a branch exists and return its HEAD SHA
3. List branches matching the `milestone/` prefix
4. Merge the integration branch into `main` (or merge a worker branch into the integration branch)
5. Delete the integration branch after milestone completion

All operations use PyGithub (not `gh` CLI). All operations follow the patterns established in the existing `github.py` — `get_github()` for auth-required calls, `try_get_github()` for soft-failure paths, `Output` parameter for status/warning messages, `GithubException` catch-and-warn pattern.

### WHEN (Trigger Conditions)

| Operation | Trigger |
|---|---|
| Create | `/work-milestone` Step 3 — after plan validation, before spawning team members |
| Get status | `/work-milestone` Step 7b — pre-verification check (worker base commit vs integration branch HEAD) |
| List | `/groom-milestone` — check for stale branches before writing dispatch plan |
| Merge | `/work-milestone` Step 7f — merge worker worktree branch into integration branch (one merge slot at a time); Step 9d — merge integration branch into main |
| Delete | `/work-milestone` Step 10 — after `/complete-milestone` is invoked |

### WHY (Problem Being Solved)

The `/work-milestone` skill needs to coordinate parallel workers merging into a shared integration branch before landing to main. Without branch CRUD, the skill would have to shell out to `git` commands — violating the project constraint of PyGithub-only GitHub operations. The gastown research established that integration branches (per-milestone shared branch) are the correct isolation pattern for parallel worker workflows. No branch management capability currently exists in `backlog_core/github.py` or anywhere in the 28-file PyGithub footprint.

---

## Codebase Research

### Similar Patterns Found

#### Pattern 1: `get_github` / `try_get_github` — connection helpers

- **Location**: `plugins/development-harness/backlog_core/github.py:227-275`
- **Relevance**: All new branch functions must accept a `repo: str = ""` parameter and call `_repo(repo)` then `get_github(repo)`. Auth failure raises `GitHubUnavailableError`. Soft-failure paths use `try_get_github`.
- **Reusable**: `get_github()`, `try_get_github()`, `_repo()`, `Output` parameter pattern, `GithubException` catch-and-warn

#### Pattern 2: `close_github_issue` / `resolve_github_issue` — write operations with Output

- **Location**: `plugins/development-harness/backlog_core/github.py:317-368`
- **Relevance**: Shows the standard pattern for operations that mutate GitHub state: accept `repo: str = ""` and `output: Output | None = None`, call `get_github(repo)`, perform operation inside `try: ... except GithubException as e: out.warn(...)`.
- **Reusable**: Function signature shape, try/warn pattern, `out = output or Output()` idiom

#### Pattern 3: `apply_status_verified` — label-not-found (404) auto-create

- **Location**: `plugins/development-harness/backlog_core/github.py:478-513`
- **Relevance**: Shows how to handle "resource not found" gracefully — check `e.status != _HTTP_NOT_FOUND` before re-raising. Branch-not-found scenarios follow the same pattern.
- **Reusable**: `_HTTP_NOT_FOUND` constant, conditional re-raise on 404

#### Pattern 4: `check_open_prs_for_issue` — returns empty list on GitHub unavailable

- **Location**: `plugins/development-harness/backlog_core/github.py:376-400`
- **Relevance**: Read operations that are non-critical return empty/None on failure rather than raising. Branch existence checks follow this pattern.
- **Reusable**: `return []` / `return None` on `GithubException` for read-only queries

#### Pattern 5: Dispatch plan YAML — `integration_branch` field

- **Location**: `.claude/reports/milestone-orchestration-design-20260320.md:208` (dispatch plan schema)
- **Relevance**: The `integration_branch` field in the dispatch plan YAML stores the full branch name (`milestone/3-v1.1-milestone-workflow`). The create function must return this name so the caller can write it into the plan.
- **Reusable**: Branch naming pattern is `milestone/{N}-{slug}`

### Existing Infrastructure

- `plugins/development-harness/backlog_core/github.py` — all PyGithub operations live here. New branch functions belong in this module unless size warrants a sibling `branch.py` module.
- `plugins/development-harness/backlog_core/models.py` — `Output`, `BacklogError`, `GitHubUnavailableError` are defined here and imported by `github.py`. Any new return types (e.g. a `BranchStatus` TypedDict) go here.
- `plugins/development-harness/backlog_core/__init__.py` — public surface. New functions need to be exported if callers outside `backlog_core` need them directly.

### Code References

- `plugins/development-harness/backlog_core/github.py:47` — `_HTTP_NOT_FOUND = 404` constant (reuse for branch-not-found)
- `plugins/development-harness/backlog_core/github.py:50-56` — `_repo()` resolver (call on every `repo` param)
- `plugins/development-harness/backlog_core/github.py:227-249` — `get_github()` with timeout
- `plugins/development-harness/backlog_core/github.py:252-275` — `try_get_github()` soft-failure
- `plugins/development-harness/backlog_core/models.py` — `Output`, `BacklogError`, `GitHubUnavailableError`
- `.claude/reports/milestone-orchestration-design-20260320.md:202-267` — dispatch plan YAML schema with `integration_branch` field and branch naming convention
- `.claude/reports/milestone-orchestration-design-20260320.md:504-510` — explicit statement that integration branch management is a "new capability needed" with no existing tooling

---

## Use Scenarios

### Scenario 1: Start of milestone work

**Actor**: `/work-milestone` skill (milestone orchestrator)
**Trigger**: Dispatch plan validated; about to spawn team members
**Goal**: Create `milestone/3-v1.1-milestone-workflow` from `main` HEAD and record the name in the dispatch plan
**Expected Outcome**: Branch exists on GitHub, HEAD SHA returned, branch name written to `plan/milestone-3-dispatch.yaml` `integration_branch` field. If the branch already exists (stale from a previous run), the orchestrator receives a clear signal to decide whether to delete-and-recreate or resume.

### Scenario 2: Pre-verification check before merge slot

**Actor**: `/work-milestone` skill (merge slot logic)
**Trigger**: Worker signals COMPLETE with the integration branch HEAD SHA it verified against
**Goal**: Confirm the integration branch HEAD has not moved since the worker verified
**Expected Outcome**: Function returns current HEAD SHA. Orchestrator compares with worker-reported SHA. If equal, skip quality gates (fast path). If diverged, run gates before merge.

### Scenario 3: Squash-merge worker branch into integration branch

**Actor**: `/work-milestone` skill (merge slot holder)
**Trigger**: Worker's worktree branch is ready; quality gates passed (or fast path applies)
**Goal**: Merge `worktree/item-42-auth-middleware` into `milestone/3-v1.1-milestone-workflow` as a squash merge with a descriptive commit message
**Expected Outcome**: Merge succeeds and integration branch advances. Returns new HEAD SHA. On conflict, returns conflict file list so orchestrator can classify severity.

### Scenario 4: Land integration branch to main

**Actor**: `/work-milestone` skill (Step 9d)
**Trigger**: All waves complete; final quality gates passed on integration branch
**Goal**: Merge `milestone/3-v1.1-milestone-workflow` into `main`
**Expected Outcome**: `main` advances. Returns merge commit SHA. On failure, propagates error to orchestrator.

### Scenario 5: Stale branch detection in groom

**Actor**: `/groom-milestone` skill
**Trigger**: About to write dispatch plan; checking whether integration branch already exists
**Goal**: List branches with `milestone/` prefix and report any that match this milestone number
**Expected Outcome**: Returns list of matching branch names and ages. Orchestrator presents stale branch options to user (delete/resume) per error condition spec in design doc.

### Scenario 6: Cleanup after completion

**Actor**: `/work-milestone` skill (Step 10)
**Trigger**: `/complete-milestone` has been invoked; milestone is closed
**Goal**: Delete `milestone/3-v1.1-milestone-workflow` from GitHub
**Expected Outcome**: Branch deleted. If branch is already gone (already deleted manually), operation succeeds silently (idempotent).

---

## Gap Analysis

### Identified Gaps

| # | Category | Gap Description | Impact |
|---|---|---|---|
| 1 | Scope | Design doc specifies "squash merge" for worker-to-integration merges but does not specify merge strategy for integration-to-main (Step 9d). PyGithub's `merge()` API does not have a native squash option — squash requires creating a commit manually or using the PR merge endpoint. | Function signature and implementation approach for merge operations cannot be fully defined without resolving this. |
| 2 | Scope | The design doc says "merge worktree branch into integration branch" but worktrees are local git concepts; GitHub API merges are between remote branches. The design assumes worktree branches are pushed to origin before merge. This push step is not explicitly scoped into the integration branch management feature — it may belong to the worktree isolation feature or to the merge slot logic in the skill itself. | If push is out of scope, the branch management functions receive already-pushed branch names. If push is in scope, the function set must include a push-to-origin operation. |
| 3 | Behavior | Conflict detection: the design doc describes auto-resolve for trivial conflicts and assign_back for heavy conflicts. Whether conflict detection/classification belongs in the branch management functions or in the skill orchestration layer is unspecified. | Determines whether the merge function returns a conflict dict or simply raises on conflict. |
| 4 | Integration | Module location: `github.py` already has issue CRUD, PR checks, label management, status management, and SAM task operations. Adding full branch lifecycle may push the module past a maintainable size. Whether branch operations go into `github.py` or a new `branch.py` sibling module is unspecified. | Affects import paths and `__init__.py` exports. No functional impact. |
| 5 | Behavior | Stale branch definition: the design doc states "stale if no recent commits for 7+ days" (error conditions section). Whether this threshold is hardcoded, configurable, or passed as a parameter is unspecified. | Affects function signature for list/check operations. |
| 6 | Integration | MCP server exposure: `github.py` functions are called from `operations.py` which backs the MCP server. Whether the new branch functions need MCP tool wrappers (for orchestrator use via `mcp__plugin_dh_backlog__*`) or are called directly from skill scripts is unspecified. | Determines whether new MCP tool definitions are also in scope for this feature. |

---

## Questions Requiring Resolution

### Q1: Merge strategy for integration-to-main landing

- **Category**: Behavior
- **Gap**: Design doc specifies squash merge for worker-to-integration but is silent on integration-to-main merge strategy.
- **Question**: When landing the integration branch to main (Step 9d of `/work-milestone`), should the merge be a regular merge commit (preserving integration branch history), a squash, or a rebase?
- **Options**:
  - A) Regular merge commit — preserves full milestone commit history; `main` log shows one merge commit per milestone
  - B) Squash merge — collapses all commits; cleaner `main` log but loses per-item history
  - C) Rebase — linear history; requires force-push if integration branch has diverged
- **Why It Matters**: PyGithub's `repo.merge()` does a regular merge. Squash requires using the PR merge endpoint with `merge_method="squash"`. The implementation approach differs significantly.
- **Resolution**: _pending_

### Q2: Is pushing worktree branches to origin in scope?

- **Category**: Scope
- **Gap**: GitHub API merges operate on remote branches. Worktrees are local. The question is whether the "push worktree branch to origin" step belongs to this feature or to the worktree isolation mechanism.
- **Question**: Should the integration branch management functions include push-to-origin for worktree branches before merging, or does the caller (skill) handle the push and pass already-existing remote branch names?
- **Options**:
  - A) In scope — branch management functions accept a local worktree path and push before merging
  - B) Out of scope — caller ensures branch is already pushed; functions receive remote branch names only
- **Why It Matters**: If A, the functions need `git push` via subprocess or PyGithub's ref creation API. If B, functions are pure PyGithub API calls with no local git operations.
- **Resolution**: _pending_

### Q3: Where does conflict detection/classification live?

- **Category**: Behavior
- **Gap**: The design doc describes auto-resolve for trivial conflicts and assign_back for heavy conflicts. This logic could live in the branch management functions or in the skill orchestration layer.
- **Question**: Should the merge function classify conflicts (trivial/medium/heavy) and return a classification, or should it simply raise or return a conflict indicator and let the skill decide?
- **Options**:
  - A) Classification in function — returns an enum/string: `clean`, `trivial`, `medium`, `heavy`
  - B) Classification in skill — function returns raw conflict file list; skill applies the severity matrix
- **Why It Matters**: Option A puts domain logic in `github.py`; Option B keeps `github.py` as a thin API wrapper. The severity matrix from the design doc (1-2 files vs 3+ files, whitespace vs refactor) is skill-level policy, not GitHub API behavior — which suggests B.
- **Resolution**: _pending_

### Q4: New module vs. extend `github.py`?

- **Category**: Integration
- **Gap**: `github.py` is already 813 lines covering issue CRUD, PRs, labels, status management, and SAM task sub-issues. Adding full branch lifecycle adds approximately 5-6 new functions.
- **Question**: Should branch management functions be added to `github.py` or placed in a new `backlog_core/branch.py` sibling module?
- **Options**:
  - A) Extend `github.py` — keeps all GitHub API calls in one module; simpler imports
  - B) New `branch.py` — better separation; `github.py` stays focused on issue/PR operations
- **Why It Matters**: Affects imports in `operations.py`, `server.py`, and any skill scripts that call these functions directly.
- **Resolution**: _pending_

### Q5: Do the branch functions need MCP server wrappers?

- **Category**: Integration
- **Gap**: The MCP server (`server.py`) exposes backlog operations as MCP tools. Skills call branch operations during milestone orchestration. Whether they need to be MCP tools or can be called from skill Python scripts directly is unspecified.
- **Question**: Should the new branch lifecycle operations be exposed as MCP tools (callable via `mcp__plugin_dh_backlog__*` from within a Claude session), or are they internal Python functions called only from skill-level Python scripts?
- **Options**:
  - A) MCP tools — orchestrator invokes `mcp__plugin_dh_backlog__create_integration_branch(...)` directly from skill instructions
  - B) Internal functions — wrapped in a CLI script or sam CLI extension; skills invoke via `uv run`
  - C) Both — internal functions with optional MCP exposure
- **Why It Matters**: MCP tools are callable from skill instruction text without a subprocess. Internal-only functions require a script wrapper that skills invoke via `Bash(uv run ...)`.
- **Resolution**: _pending_

---

## Goals (Pending Resolution)

_These goals will be finalized after questions Q1-Q5 are resolved._

1. Create `create_integration_branch(milestone_number, slug, repo, output)` — creates `milestone/{N}-{slug}` from `main` HEAD; returns branch name and HEAD SHA; handles already-exists case
2. Create `get_branch_status(branch_name, repo, output)` — returns HEAD SHA and last-commit timestamp; returns None if branch does not exist (non-raising)
3. Create `list_milestone_branches(repo, output)` — returns all branches with `milestone/` prefix including name, HEAD SHA, and age in days
4. Create `merge_branch(head_branch, base_branch, commit_message, repo, output)` — merges head into base; returns result indicating clean/conflict; conflict detail TBD per Q3
5. Create `delete_branch(branch_name, repo, output)` — deletes named branch; idempotent on already-deleted (404 treated as success)
6. All functions follow existing `github.py` patterns: `repo: str = ""`, `output: Output | None = None`, `get_github()` for write ops, `GithubException` catch-and-warn
7. Functions placed per Q4 decision; exported via `__init__.py` per Q5 decision

---

## Next Steps

After questions are resolved:

1. Update "Resolution" fields in Questions section
2. Finalize Goals section (especially merge function signature per Q1, Q2, Q3)
3. Proceed to RT-ICA assessment
4. Then proceed to architecture design (`python-cli-design-spec` agent)

---

## Post-Implementation Annotations

Added by context-refinement agent on 2026-03-21

### Design Refinements

1. **Q4 Resolved — Separate `github_branches.py` Module**: Q4 asked "New module vs. extend `github.py`?" The architecture spec resolved this as ADR-001 (separate module). Implementation confirmed this choice. The new module is at `plugins/development-harness/backlog_core/github_branches.py`.

2. **Q5 Resolved — No MCP Exposure Initially**: Q5 asked whether branch functions need MCP server wrappers. ADR-005 deferred MCP exposure. Implementation followed this decision — no `@mcp.tool()` wrappers added.

3. **Q1 Partially Resolved — `repo.merge()` Used for Both Merge Directions**: The merge function supports both worker-to-integration and integration-to-main via the same `merge_integration_branch()` call. PyGithub's `repo.merge()` performs a regular merge commit in both cases. Squash-merge (Q1 option B) was not implemented; the caller can use the PR merge endpoint separately if needed.

4. **Input Validation Gap**: The feature context did not explicitly call out input validation requirements. The architecture spec (Section 6) added them, but they were not implemented. Future consumers should be aware that invalid slugs or negative milestone numbers will produce GitHub 422 errors rather than clear Python exceptions.

No intent divergences identified. `Intent Source` field absent — all divergences classified as design-refinement per plan artifact lifecycle policy.
