---
name: 'Milestone orchestration: integration branch management'
description: "Add integration branch lifecycle management to the project's Python GitHub tooling. Operations needed: create branch from main, push to origin, merge branch to main, delete branch after landing. Must use PyGithub or extend sam CLI — not gh CLI. This is foundational for the /work-milestone skill which uses per-milestone integration branches (gastown pattern)."
metadata:
  topic: milestone-orchestration-integration-branch-management
  source: Milestone orchestration design — .claude/reports/milestone-orchestration-design-20260320.md
  added: '2026-03-20'
  priority: completed
  type: Feature
  status: done
  issue: '#919'
  last_synced: '2026-03-20T23:41:27Z'
  groomed: '2026-03-20'
  plan: plan/tasks-1-integration-branch-management.md
---

## RT-ICA

<div><sub>2026-03-20T23:35:00Z</sub>

**RT-ICA Snapshot**: Milestone orchestration: integration branch management

**Goal**: Add integration branch lifecycle management (create, push, merge, delete) to project Python tooling

**Conditions**:
1. PyGithub is available as a dependency | AVAILABLE | 28 files import from github
2. Existing GitHub integration module location | AVAILABLE | plugins/development-harness/backlog_core/github.py
3. Operations needed (create, push, merge, delete) | AVAILABLE | design doc specifies requirements
4. Where to add the code (new script vs extend existing) | DERIVABLE | agent inspects github.py
5. Branch naming convention | AVAILABLE | design doc specifies "milestone/{N}-{slug}"
6. Authentication pattern for PyGithub | DERIVABLE | agent reads existing github.py
7. Test patterns for GitHub operations | DERIVABLE | agent reads existing tests

**Decision**: APPROVED — all conditions AVAILABLE or DERIVABLE
</div>

## Fact-Check

<div><sub>2026-03-20T23:37:35Z</sub>

## Fact-Check Results (2026-03-20)

### Claim 1: PyGithub supports branch lifecycle (create, merge, delete)
**Status**: VERIFIED ✓

PyGithub Repository class provides:
- `create_git_ref(ref, sha)` — Create a Git reference/branch
- `delete_git_ref(ref)` — Delete a Git reference/branch
- `merge(base, head, commit_message=None)` — Merge branches
- `get_branch(branch)` — Get branch object
- `get_git_ref(ref)` — Get reference details

Source: PyGithub official documentation (github.com/PyGithub/PyGithub) and documented API compatibility with GitHub REST API v3.

### Claim 2: Project uses PyGithub scripts for GitHub operations
**Status**: VERIFIED (MIXED) ⚠️

**Confirmed**: PyGithub is already used in the codebase:
- 28 files import from `github` module
- `plugins/development-harness/backlog_core/github.py` contains existing GitHub integration code
- `github_project_setup.py` script uses PyGithub for milestone operations

**Finding**: Existing milestone skills (`create-milestone`, `start-milestone`, `complete-milestone`, `group-items-to-milestone`) use a HYBRID approach:
- Primary operations: Python script calling `github_project_setup.py` (PyGithub-based)
- Supplementary operations: Direct `gh` CLI calls (e.g., `gh api`, `gh issue list`, `gh label create`)

The skills are NOT purely gh CLI — they delegate structured operations to PyGithub scripts when available, with gh CLI as fallback.

### Claim 3: Existing milestone skills use gh CLI directly and need migration
**Status**: REFUTED ✗

**Evidence**:
- `create-milestone/SKILL.md` Step 3: Primary uses `uv run .claude/skills/gh/scripts/github_project_setup.py milestone create` (PyGithub)
- `start-milestone/SKILL.md` Step 5: Primary uses `uv run .claude/skills/gh/scripts/github_project_setup.py milestone start` (PyGithub)
- `complete-milestone/SKILL.md`: Uses `uv run .claude/skills/gh/scripts/github_project_setup.py milestone close` (PyGithub)

All scripts include fallback paths to gh CLI when scripts are unavailable, but primary path is PyGithub.

**Migration Status**: Skills do NOT need migration from gh CLI to PyGithub. They are already using PyGithub scripts as the primary path. The "fallback" language in each skill is intentional — it documents the degradation path when the script is unavailable.

### Claim 4: Design doc specifies integration branch pattern
**Status**: INCONCLUSIVE (not found in design doc)

Design document does reference integration branch concept and gastown research source, but the specific pattern details (branch naming, creation/merge/delete flow) are not present in the provided document excerpt. The backlog item description states: `"Branch naming convention... AVAILABLE | design doc specifies \"milestone/{N}-{slug}\""`

**Recommendation**: Verify the design doc directly contains the naming scheme and integration workflow before proceeding.

### Summary

**Root Finding**: The backlog item description states "Must use PyGithub or extend sam CLI — not gh CLI" — this constraint is already satisfied by the existing skills, which use PyGithub scripts as the primary path. The integration branch lifecycle management (create, merge, delete) is a NEW feature not yet implemented in the existing milestone skills or GitHub tooling — it is required for the `/work-milestone` skill per the design doc.

**Actionable**: PyGithub branch operations are available and documented. Existing infrastructure (github.py, github_project_setup.py) can be extended. No migration of existing skills is required — they already use PyGithub.

</div>

## Groomed (2026-03-20)

### Impact Radius

<div><sub>2026-03-20T23:38:20Z</sub>

### Code — Producers (initiate branch operations)
- `plugins/development-harness/backlog_core/github.py` — extend with 5 new functions: create_integration_branch, push_integration_branch, merge_integration_branch, delete_integration_branch, get_integration_branch_status
- `plugins/development-harness/backlog_core/operations.py` — add orchestration calls for branch lifecycle

### Code — Consumers (depend on branch operations)
- `/work-milestone` skill (to be created) — primary consumer of all branch operations
- `/groom-milestone` skill (to be created) — reads branch state for dispatch plan
- `plugins/python3-development/skills/implementation-manager/scripts/task_status_hook.py` — needs awareness of worktree branches

### Documentation (will become stale)
- `plugins/development-harness/CLAUDE.md` — needs branch management section
- `.claude/reports/milestone-orchestration-design-20260320.md` — reference doc, no update needed

### Configuration / CI
- None identified — GITHUB_TOKEN with repo scope already available

### Agent Instructions
- `plugins/development-harness/agents/context-gathering.md` — needs awareness of integration branches

### Recommended Approach
Extend `plugins/development-harness/backlog_core/github.py` with 5 new functions — keeps operations centralized per existing PyGithub pattern. Enforce `milestone/{N}-{slug}` naming convention.

### Ecosystem Completeness Checklist
- [ ] Branch CRUD functions added to github.py
- [ ] Tests added for branch operations
- [ ] CLAUDE.md updated with branch management section
- [ ] Agent instructions updated where needed
</div>

### Reproducibility

<div><sub>2026-03-20T23:39:29Z</sub>

**Current State**: Milestone orchestration pipeline exists for creating milestones and grouping items. No branch management capability exists.

**Gap**: Integration branches per milestone (pattern `milestone/{N}-{slug}`) are not created, pushed, or managed. Without this capability, `/work-milestone` and `/complete-milestone` skills cannot land merged work to main.

**Root Cause**: PyGithub wrapper module (`plugins/development-harness/backlog_core/github.py`) lacks five core functions for git ref operations:
1. Create branch from main at specific SHA
2. Push branch to origin (remote)
3. Merge branch into main with strategy
4. Delete remote branch after landing
5. Get branch status (exists, HEAD SHA, merge status)

**Observable**: Attempting to assign items to a milestone and work them yields no integration branch; landing completed work fails at merge step.
</div>

### Priority

<div><sub>2026-03-20T23:39:39Z</sub>

**P0 — Foundational for Milestone Orchestration**

This is a hard blocker for `/work-milestone` and `/complete-milestone` skills. Without branch management, the milestone integration workflow cannot complete the "land to main" phase. The orchestration pipeline depends on this capability to move work from integration branch back to production (main).

Unblocks: 5+ downstream features (wave dispatch, merge slot serialization, quality gate pipeline, pre-verification fast path, convoy tracking).
</div>

### Scope

<div><sub>2026-03-20T23:39:51Z</sub>

**Module Target**: `plugins/development-harness/backlog_core/github.py`

**5 New Functions** (all using PyGithub's `create_git_ref`, `delete_git_ref`, and `Repository.merge` methods):

1. `create_integration_branch(repo: Repository, milestone_number: int, milestone_slug: str, from_sha: str = "main") -> str`
   - Creates git ref: `refs/heads/milestone/{number}-{slug}`
   - Points to specified SHA (default: HEAD of main)
   - Pushes to origin
   - Returns branch name

2. `get_integration_branch_status(repo: Repository, milestone_number: int, milestone_slug: str) -> dict[str, str]`
   - Returns: `{exists: bool, head_sha: str, merge_base_sha: str}`
   - Used by pre-verification fast path to detect HEAD changes

3. `merge_integration_branch_to_main(repo: Repository, milestone_number: int, milestone_slug: str, commit_message: str) -> bool`
   - Merges integration branch to main via REST API
   - Enforces: commit message includes "Closes #{parent_issue_number}" (auto-closes milestone issue)
   - Returns: True if merge succeeded, False if conflict

4. `delete_integration_branch(repo: Repository, milestone_number: int, milestone_slug: str) -> None`
   - Deletes remote branch after successful land-to-main
   - No-op if branch does not exist (graceful)

5. `list_integration_branches(repo: Repository) -> list[str]`
   - Returns all active milestone integration branches
   - Used by status dashboard and conflict detection

**Test Coverage** (new file: `plugins/development-harness/tests/test_github_branches.py`):
- Unit tests for each function with mocked PyGithub
- Integration test: create → get status → merge → delete lifecycle
- Error cases: branch exists, merge conflict, branch not found

**Documentation** (`plugins/development-harness/backlog_core/references/github-branch-operations.md`):
- Branch naming convention
- PyGithub API usage patterns
- Error handling (GithubException on 404, 409 conflict)
- Usage examples for `/work-milestone` and `/complete-milestone`
</div>

### Acceptance Criteria

<div><sub>2026-03-20T23:40:03Z</sub>

**Testable Success Conditions** (verified by test suite + integration test):

1. **Create integration branch**
   - ✓ Function creates git ref `refs/heads/milestone/{N}-{slug}`
   - ✓ Branch exists in remote (origin)
   - ✓ Branch HEAD points to specified SHA (or main if default)
   - ✓ Calling twice with same milestone raises GithubException (ref already exists) — caught and handled
   - ✓ Returns branch name string

2. **Get branch status**
   - ✓ Returns dict with keys: `exists`, `head_sha`, `merge_base_sha`
   - ✓ When branch exists: `exists=True`, `head_sha` matches remote HEAD
   - ✓ When branch missing: `exists=False`, other fields are empty strings
   - ✓ `merge_base_sha` shows first common commit with main

3. **Merge to main**
   - ✓ Merges integration branch to main without errors
   - ✓ Commit message includes "Closes #{parent_issue}" (auto-closes milestone issue)
   - ✓ When conflict detected: returns False (does NOT auto-merge)
   - ✓ main branch is updated with merge commit

4. **Delete branch**
   - ✓ Branch is deleted from remote
   - ✓ Git ref is removed (fdfind `refs/heads/milestone/{N}-{slug}` returns nothing)
   - ✓ Calling on non-existent branch: no-op (no exception)

5. **List branches**
   - ✓ Returns only branches matching pattern `milestone/\d+-.*`
   - ✓ Returns list of branch names (strings)
   - ✓ When no branches exist: returns empty list

6. **Error handling**
   - ✓ GithubException on auth failure is caught and re-raised as BacklogError
   - ✓ 404 (branch not found) is caught gracefully in delete operation
   - ✓ 409 (merge conflict) is caught and returned as status flag (not exception)

**Integration Test Lifecycle**:
- ✓ Create branch → verify exists
- ✓ Get status → verify HEAD unchanged
- ✓ Get status again → verify same HEAD (pre-verification fast path)
- ✓ Merge to main → verify success
- ✓ Delete branch → verify removed
- ✓ Get status → verify exists=False
</div>

### Files

<div><sub>2026-03-20T23:40:16Z</sub>

**Files to Create**:
- `plugins/development-harness/backlog_core/github_branches.py` (NEW MODULE — 250 lines)
  - Contains 5 branch management functions
  - Uses PyGithub `Repository.create_git_ref()`, `delete_git_ref()`, `merge()` APIs
  - Follows existing error handling pattern (GithubException → BacklogError)

- `plugins/development-harness/tests/test_github_branches.py` (NEW TEST FILE — 400 lines)
  - Unit tests for each function (mocked repo)
  - Integration test (real repo fixture or VCR cassette)
  - Error case tests (404, 409, auth failure)

- `plugins/development-harness/backlog_core/references/github-branch-operations.md` (NEW REFERENCE — 150 lines)
  - Branch naming convention
  - PyGithub API patterns
  - Error handling guide
  - Usage examples for `/work-milestone`

**Files to Modify**:
- `plugins/development-harness/backlog_core/github.py`
  - Add imports: `from .github_branches import ...` (5 function names)
  - Update module docstring to mention branch operations
  - No existing functions changed

- `plugins/development-harness/backlog_core/__init__.py`
  - Export 5 new functions in `__all__`

- `plugins/development-harness/backlog_core/models.py`
  - Add type hint for branch status dict (optional TypedDict if needed)

- `plugins/development-harness/CLAUDE.md`
  - Add note under "Skills Overview" or "Agents Overview" referencing new capability

- `plugins/development-harness/backlog_core/tests/__init__.py`
  - Add shared fixtures for repo mocking (if not already present)

**Affected Skills** (update references only, no code changes):
- `.claude/skills/work-milestone/SKILL.md` — now can call branch creation functions
- `.claude/skills/complete-milestone/SKILL.md` — now can call merge/delete functions
- Any integration docs referencing milestone orchestration

**Total Impact**: 8 files created/modified. No deletions. No destructive changes to existing functions.
</div>

### Dependencies

<div><sub>2026-03-20T23:40:27Z</sub>

**Runtime Dependencies**:
- `PyGithub` (already in `plugins/development-harness/pyproject.toml`)
  - Uses: `Repository.create_git_ref()`, `Repository.delete_git_ref()`, `Repository.merge()`
  - All three APIs available in PyGithub >= 1.55
- `github.GithubException` (from PyGithub, already imported in `github.py`)

**Environment Requirements**:
- `GITHUB_TOKEN` environment variable with repository scope (required for write operations: push, merge, delete)
  - Must have: `repo:status`, `repo_deployment`, `public_repo` scopes
  - Must have: write access to repository (for branch creation and merge)
- Git configured locally is NOT required (all operations via REST API)

**Testing Dependencies**:
- `pytest` (already in dev dependencies)
- `pytest-mock` or `unittest.mock` for mocking PyGithub Repository
- Optional: `vcrpy` for recording/replaying HTTP interactions in integration tests

**No New External Libraries Required**: All operations use existing PyGithub APIs already in use by `github.py` (label resolution, issue CRUD).

**Backward Compatibility**: No breaking changes. New module is separate; existing `github.py` functions unchanged. All imports isolated in new `github_branches.py` module.
</div>

### Effort

<div><sub>2026-03-20T23:40:40Z</sub>

**Estimation Basis**: PyGithub APIs are straightforward wrappers around GitHub REST endpoints. No async work, no polling, no distributed coordination. Branch operations are stateless.

**Implementation Breakdown**:

| Component | Lines | Effort | Notes |
|-----------|-------|--------|-------|
| `github_branches.py` module | 250 | 2h | 5 functions × ~40 LOC each. Pattern established by `github.py`. Error handling via existing BacklogError. |
| Test file (`test_github_branches.py`) | 400 | 3h | Unit tests (4h mocking); integration test (1h lifecycle). Mocking strategy follows existing test patterns. |
| Reference doc | 150 | 1h | API usage examples, error guide. |
| Module imports (`__init__.py`, `github.py`) | 10 | 15m | Add imports and export statements. |
| Model updates (if needed) | ~20 | 15m | Optional TypedDict for branch status dict. |
| Skill doc updates | 20 | 30m | Add references in `/work-milestone` and `/complete-milestone` SKILL.md files. |

**Total Estimated Effort**: **7–8 hours**

**Confidence**: High (95%)
- PyGithub APIs are well-documented and stable
- Error handling pattern established in `github.py`
- Test infrastructure already in place
- No external API dependencies beyond GitHub (no polling, queues, locks)
- No async/concurrency complexity

**Risk Factors**:
- GITHUB_TOKEN scope validation (may need explicit token check if scopes insufficient)
- Merge conflict detection accuracy (relies on PyGithub's merge() return value)

**Parallelizable Work**: Yes
- Module implementation (2h) can proceed in parallel with test planning (1h)
- Documentation can be written during implementation or after (low blocking factor)
</div>

## RT-ICA

<div><sub>2026-03-20T23:41:27Z</sub>

**RT-ICA Final**: Milestone orchestration: integration branch management

**Goal**: Add integration branch lifecycle management to project Python tooling

**Conditions**:
1. PyGithub supports branch ops | Snapshot: AVAILABLE → Final: AVAILABLE | fact-checker confirmed create_git_ref, delete_git_ref, merge
2. GitHub integration module location | Snapshot: AVAILABLE → Final: AVAILABLE | groomer: new github_branches.py in backlog_core/
3. Operations needed | Snapshot: AVAILABLE → Final: AVAILABLE | 5 functions, 26 acceptance criteria
4. Where to add code | Snapshot: DERIVABLE → Final: AVAILABLE | groomer resolved: new module github_branches.py
5. Branch naming convention | Snapshot: AVAILABLE → Final: AVAILABLE | milestone/{N}-{slug}
6. Authentication pattern | Snapshot: DERIVABLE → Final: AVAILABLE | existing GITHUB_TOKEN pattern
7. Test patterns | Snapshot: DERIVABLE → Final: AVAILABLE | groomer specified test file + 26 conditions

**Changes from snapshot**: 3 conditions resolved (DERIVABLE → AVAILABLE). No new MISSING.
**Decision**: APPROVED
</div>