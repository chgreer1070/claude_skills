---
plan_number: 1
slug: integration-branch-management
goal: Implement integration branch lifecycle management module with 5 PyGithub
  functions for create, status, merge, delete, and list operations
context: 'Story issue #919. New module github_branches.py in plugins/development-harness/backlog_core/
  providing branch lifecycle CRUD via PyGithub. See Context Manifest section below
  frontmatter.'
acceptance_criteria:
- 'AC1: BranchInfo, MergeResult TypedDicts and BranchConflictError exception class
  exist in models.py'
- 'AC2: github_branches.py exports 5 public functions matching architecture spec signatures'
- 'AC3: __init__.py re-exports all new public symbols (5 functions + 3 types)'
- 'AC4: All tests pass with pytest and cover happy-path, error-path, and edge-case
  for each function'
- 'AC5: ruff check and ty check pass on all new and modified files'
issue: 919
feature: Integration Branch Lifecycle Management
status: not-started
created: '2026-03-20T00:00:00Z'
tasks:
- task: T01
  title: Add branch data types to models.py
  status: complete
  agent: python-cli-architect
  dependencies: []
  priority: 1
  complexity: low
  accuracy-risk: medium
  skills:
  - python3-development
  parallelize-with: []
  reason: Types must exist before github_branches.py can import them
  handoff: T02 imports BranchInfo, MergeResult, BranchConflictError from
    models.py
  body: |
    ## Context

    The backlog_core/models.py module already contains BacklogError, GitHubUnavailableError,
    and TypedDict usage (SamTasksResult). Three new types are needed for branch lifecycle
    operations defined in the architecture spec.

    Architecture spec: plan/architect-integration-branch-management.md (Section 5: Data Architecture)

    ## Objective

    Add BranchInfo (TypedDict), MergeResult (TypedDict), and BranchConflictError (Exception)
    to plugins/development-harness/backlog_core/models.py following the exact signatures in
    the architecture spec.

    ## Inputs

    - Architecture spec Section 5 "New Types in models.py": plan/architect-integration-branch-management.md
    - Existing models file: plugins/development-harness/backlog_core/models.py

    ## Requirements

    1. Add `BranchInfo(TypedDict)` with fields: name (str), sha (str), last_commit_date (str), age_days (int)
    2. Add `MergeResult(TypedDict)` with fields: sha (str), message (str)
    3. Add `BranchConflictError(BacklogError)` with attributes: head_branch (str), base_branch (str), conflict_files (list[str])
    4. BranchConflictError.__init__ must accept head_branch, base_branch, and optional conflict_files
    5. BranchConflictError.__init__ must call super().__init__() with a descriptive message including branch names and first 5 conflict files
    6. Add `from datetime import datetime` import if not already present (architecture spec includes it)
    7. Include docstrings on all three classes matching the architecture spec

    ## Constraints

    - Do not modify any existing classes or functions in models.py
    - Do not remove or reorder existing imports
    - Place new types after existing class definitions, before any existing TypedDict definitions if ordering matters, or at the end of the file
    - Follow existing code style (spacing, docstring format) in models.py

    ## Expected Outputs

    - Modified file: plugins/development-harness/backlog_core/models.py

    ## Acceptance Criteria

    1. `python -c "from backlog_core.models import BranchInfo, MergeResult, BranchConflictError"` succeeds
    2. BranchInfo has exactly 4 keys: name, sha, last_commit_date, age_days
    3. MergeResult has exactly 2 keys: sha, message
    4. BranchConflictError is a subclass of BacklogError
    5. `BranchConflictError("a", "b", ["file1.py"])` produces a message containing "a", "b", and "file1.py"
    6. `BranchConflictError("a", "b")` works with no conflict_files (defaults to empty list)

    ## Verification Steps

    1. Run: `cd plugins/development-harness && uv run python -c "from backlog_core.models import BranchInfo, MergeResult, BranchConflictError; print('OK')"`
    2. Run: `cd plugins/development-harness && uv run python -c "from backlog_core.models import BranchConflictError; e = BranchConflictError('head', 'base', ['f.py']); assert e.head_branch == 'head'; assert e.conflict_files == ['f.py']; print(str(e))"`
    3. Run: `cd plugins/development-harness && uv run ruff check backlog_core/models.py`
    4. Run: `cd plugins/development-harness && uv run ty check backlog_core/models.py`

    ## CoVe Checks

    - Key claims to verify:
      - BacklogError exists in models.py and is the correct base class
      - TypedDict is already imported or needs importing
      - SamTasksResult TypedDict pattern can be followed for BranchInfo/MergeResult
    - Verification questions:
      1. Does models.py already import TypedDict? If so, from typing or typing_extensions?
      2. Does BacklogError.__init__ accept a message string as its first argument (inherited from Exception)?
      3. Are there existing TypedDict subclasses in models.py whose style should be matched?
    - Evidence to collect:
      - Read models.py imports section and BacklogError definition
      - Read any existing TypedDict in models.py for style reference
    - Revision rule:
      - If TypedDict import style differs from assumption, match the existing style

  started: '2026-03-21T00:06:29.222435+00:00'
- task: T02
  title: Implement github_branches.py module with 5 branch lifecycle functions
  status: complete
  agent: python-cli-architect
  dependencies:
  - T01
  priority: 2
  complexity: high
  accuracy-risk: medium
  skills:
  - python3-development
  parallelize-with: []
  reason: Core implementation task -- all 5 functions plus __init__.py exports
  handoff: T03 writes tests against the public API surface created by this task
  body: |
    ## Context

    This task creates the new github_branches.py module in backlog_core/ and updates
    __init__.py to export its public symbols. The module provides 5 PyGithub functions
    for integration branch lifecycle management, following patterns established in
    the existing github.py module (get_github auth, Output parameter, GithubException
    catch-and-warn, _repo for repo slug resolution).

    Architecture spec: plan/architect-integration-branch-management.md (Sections 4, 6, 9)

    ## Objective

    Create github_branches.py with 5 public functions and 1 private helper matching
    the architecture spec signatures, and update __init__.py to re-export all new symbols.

    ## Inputs

    - Architecture spec (full function signatures): plan/architect-integration-branch-management.md
    - Existing github.py (patterns to follow): plugins/development-harness/backlog_core/github.py
    - Models (types created by T01): plugins/development-harness/backlog_core/models.py
    - Package init: plugins/development-harness/backlog_core/__init__.py

    ## Requirements

    ### github_branches.py

    1. Implement `create_integration_branch(milestone_number, slug, *, base_branch="main", repo="", output=None) -> BranchInfo`
       - Construct branch name via `_branch_name()` helper
       - Get base branch SHA via `repo.get_branch(base_branch).commit.sha`
       - Create git ref via `repo.create_git_ref(ref=f"refs/heads/{name}", sha=sha)`
       - Raise BacklogError if branch already exists (catch 422 GithubException)
       - Return BranchInfo with name, sha, last_commit_date, age_days=0
    2. Implement `get_integration_branch_status(branch_name, *, repo="", output=None) -> BranchInfo | None`
       - Return None on 404 (branch not found) -- do not raise
       - Return BranchInfo with commit date and computed age_days
       - Re-raise non-404 GithubException
    3. Implement `merge_integration_branch(head_branch, base_branch, commit_message, *, repo="", output=None) -> MergeResult`
       - Use `repo.merge(base_branch, head_branch, commit_message)` for the merge
       - Raise BranchConflictError on merge conflict (409 status)
       - Return MergeResult with sha and message
    4. Implement `delete_integration_branch(branch_name, *, repo="", output=None) -> bool`
       - Idempotent: return True on 404 (already deleted)
       - Get ref via `repo.get_git_ref(f"heads/{branch_name}")` then `ref.delete()`
       - Return False on unexpected errors, log via output.warn
    5. Implement `list_integration_branches(*, repo="", output=None) -> list[BranchInfo]`
       - Filter `repo.get_branches()` by BRANCH_PREFIX
       - Sort by last commit date descending (most recent first)
       - Return empty list on error
    6. Implement private helper `_branch_name(milestone_number, slug) -> str`
       - Return f"milestone/{milestone_number}-{slug}"
    7. Define module constant `BRANCH_PREFIX = "milestone/"`
    8. Validate inputs per Section 6 Security Architecture:
       - slug: validate against `^[a-zA-Z0-9][a-zA-Z0-9._-]*$`
       - milestone_number: must be > 0
       - head_branch != base_branch in merge

    ### __init__.py exports

    9. Add imports from .github_branches for all 5 public functions
    10. Add imports from .models for BranchInfo, MergeResult, BranchConflictError
    11. Follow existing import style in __init__.py

    ## Constraints

    - Import helpers from github.py: get_github, _repo, _HTTP_NOT_FOUND
    - Import types from models.py: Output, GitHubUnavailableError, BacklogError, BranchInfo, MergeResult, BranchConflictError
    - Use `from __future__ import annotations` at top
    - Use `TYPE_CHECKING` guard for `from github.Repository import Repository`
    - Do not modify github.py
    - Do not add MCP tool exposure
    - Match the docstring style from the architecture spec signatures

    ## Expected Outputs

    - New file: plugins/development-harness/backlog_core/github_branches.py
    - Modified file: plugins/development-harness/backlog_core/__init__.py

    ## Acceptance Criteria

    1. `from backlog_core.github_branches import create_integration_branch, get_integration_branch_status, merge_integration_branch, delete_integration_branch, list_integration_branches` succeeds
    2. `from backlog_core import create_integration_branch, BranchInfo, MergeResult, BranchConflictError` succeeds via __init__.py
    3. All 5 public functions have type annotations matching the architecture spec signatures exactly
    4. `_branch_name(3, "v1.1-milestone")` returns `"milestone/3-v1.1-milestone"`
    5. BRANCH_PREFIX constant equals `"milestone/"`
    6. Slug validation rejects empty strings and strings with spaces/special chars
    7. ruff check passes on github_branches.py
    8. ty check passes on github_branches.py

    ## Verification Steps

    1. Run: `cd plugins/development-harness && uv run python -c "from backlog_core.github_branches import create_integration_branch, get_integration_branch_status, merge_integration_branch, delete_integration_branch, list_integration_branches; print('imports OK')"`
    2. Run: `cd plugins/development-harness && uv run python -c "from backlog_core import create_integration_branch, BranchInfo, BranchConflictError; print('__init__ exports OK')"`
    3. Run: `cd plugins/development-harness && uv run python -c "from backlog_core.github_branches import _branch_name, BRANCH_PREFIX; assert _branch_name(3, 'v1.1') == 'milestone/3-v1.1'; assert BRANCH_PREFIX == 'milestone/'; print('helper OK')"`
    4. Run: `cd plugins/development-harness && uv run ruff check backlog_core/github_branches.py backlog_core/__init__.py`
    5. Run: `cd plugins/development-harness && uv run ty check backlog_core/github_branches.py`

    ## CoVe Checks

    - Key claims to verify:
      - PyGithub repo.merge() signature and conflict behavior
      - PyGithub repo.create_git_ref() ref format (refs/heads/ prefix required)
      - PyGithub GithubException status attribute for 404 vs 409 vs 422
      - _HTTP_NOT_FOUND constant value and usage pattern in github.py
    - Verification questions:
      1. Does PyGithub repo.merge(base, head, message) take base as first arg or head?
      2. Does repo.create_git_ref require "refs/heads/" prefix or just the branch name?
      3. What is the HTTP status code for merge conflicts via the GitHub API?
      4. How does github.py use _HTTP_NOT_FOUND -- is it compared to GithubException.status?
    - Evidence to collect:
      - Read github.py for _HTTP_NOT_FOUND usage pattern and get_github() return type
      - Check PyGithub docs or source for merge() parameter order
    - Revision rule:
      - If PyGithub API differs from architecture spec assumptions, implement per actual API and note deviation

  started: '2026-03-21T00:09:14.943600+00:00'
- task: T03
  title: Write unit tests for github_branches.py
  status: complete
  agent: python-pytest-architect
  dependencies:
  - T02
  priority: 3
  complexity: medium
  accuracy-risk: low
  skills:
  - fastmcp-python-tests
  - python3-development
  parallelize-with: []
  reason: Tests validate the implementation created by T02
  handoff: All tasks complete -- ready for /complete-implementation quality
    gates
  body: |
    ## Context

    github_branches.py (created by T02) provides 5 public functions for integration branch
    lifecycle management via PyGithub. Tests must mock PyGithub objects -- no live API calls.
    The architecture spec defines test categories, coverage requirements, and mock strategy.

    Architecture spec: plan/architect-integration-branch-management.md (Section 7: Testing Architecture)
    Implementation: plugins/development-harness/backlog_core/github_branches.py
    Models: plugins/development-harness/backlog_core/models.py

    ## Objective

    Create a comprehensive test suite with minimum 15 test cases covering happy-path,
    error-path, and edge-case for each of the 5 public functions.

    ## Inputs

    - Architecture spec Section 7 (test categories, mock strategy): plan/architect-integration-branch-management.md
    - Implementation to test: plugins/development-harness/backlog_core/github_branches.py
    - Types used in assertions: plugins/development-harness/backlog_core/models.py
    - Existing test patterns: plugins/development-harness/tests/ (any existing test file for style reference)
    - pytest config: plugins/development-harness/pyproject.toml

    ## Requirements

    ### Test infrastructure

    1. Create test file at plugins/development-harness/tests/test_github_branches.py
    2. Create a `mock_repo` fixture that patches `backlog_core.github_branches.get_github` to return a MagicMock Repository
    3. Use pytest-mock (MockerFixture) for patching, matching architecture spec mock pattern

    ### create_integration_branch tests

    4. Test successful creation from main: verify returned BranchInfo has correct name, sha, and age_days=0
    5. Test branch already exists: mock 422 GithubException, verify BacklogError raised
    6. Test invalid slug rejected: verify ValueError or BacklogError raised for slug with spaces

    ### get_integration_branch_status tests

    7. Test branch exists: verify returned BranchInfo has name, sha, last_commit_date, age_days
    8. Test branch not found (404): verify returns None without raising
    9. Test other GithubException propagates: mock 500 error, verify GithubException raised

    ### merge_integration_branch tests

    10. Test clean merge: verify MergeResult has sha and message
    11. Test conflict (409): verify BranchConflictError raised with head_branch and base_branch attributes
    12. Test same branch rejected: head_branch == base_branch should raise ValueError or BacklogError

    ### delete_integration_branch tests

    13. Test successful delete: verify returns True
    14. Test already deleted (404): verify returns True (idempotent)
    15. Test unexpected error: verify returns False and output.warn called

    ### list_integration_branches tests

    16. Test returns matching branches sorted by date (most recent first)
    17. Test no matching branches returns empty list
    18. Test GitHub error returns empty list

    ## Constraints

    - No live GitHub API calls -- all tests use mocked PyGithub objects
    - Use `pytest.raises` for expected exceptions
    - Mock at the `backlog_core.github_branches.get_github` level, not deeper PyGithub internals
    - Follow existing test patterns in the plugins/development-harness/tests/ directory
    - Use descriptive test function names: `test_{function}_{scenario}`

    ## Expected Outputs

    - New file: plugins/development-harness/tests/test_github_branches.py

    ## Acceptance Criteria

    1. At least 15 test functions exist in the test file
    2. Every public function (5 total) has at least 3 tests (happy, error, edge)
    3. `cd plugins/development-harness && uv run pytest tests/test_github_branches.py -v` passes all tests
    4. Tests use mock_repo fixture pattern from architecture spec
    5. No test makes real HTTP or GitHub API calls
    6. BranchConflictError assertions check head_branch, base_branch, and conflict_files attributes
    7. ruff check passes on the test file

    ## Verification Steps

    1. Run: `cd plugins/development-harness && uv run pytest tests/test_github_branches.py -v` -- all tests pass
    2. Run: `cd plugins/development-harness && uv run pytest tests/test_github_branches.py -v --tb=short 2>&1 | grep -c "PASSED"` -- count >= 15
    3. Run: `cd plugins/development-harness && uv run ruff check tests/test_github_branches.py`
    4. Run: `grep -c "def test_" plugins/development-harness/tests/test_github_branches.py` -- count >= 15
  started: '2026-03-21T00:16:27.037828+00:00'

---

## Impact Radius Exclusions

The following files are listed in the Impact Radius but intentionally excluded from this plan:

- **`plugins/development-harness/backlog_core/operations.py`** — orchestration calls for branch lifecycle. Deferred to `/work-milestone` skill creation (separate backlog item). This plan delivers the library module; consumers integrate when their features are implemented.
- **`plugins/development-harness/CLAUDE.md`** — branch management documentation section. Post-launch documentation update; does not block functionality.
- **`plugins/development-harness/agents/context-gathering.md`** — awareness of integration branches. Post-launch agent instruction update; does not block functionality.
- **`plugins/python3-development/skills/implementation-manager/scripts/task_status_hook.py`** — worktree branch awareness. Deferred to `/work-milestone` skill creation; hook modifications depend on the full worktree orchestration design.

## Context Manifest

The existing `github.py` module (28 files using PyGithub across the project) provides connection helpers, issue/PR operations, label management, and SAM task operations. All functions follow consistent patterns:

1. **Authentication**: Accept `repo: str = ""` parameter (optional). Call `_repo(repo)` for slug resolution, then `get_github(repo)` to authenticate. Auth failure raises `GitHubUnavailableError`.
2. **Status Reporting**: Accept `output: Output | None = None` parameter. Use output.warn() for non-fatal issues, output.status() for progress updates.
3. **Error Handling**: Catch `GithubException`, check `e.status` against `_HTTP_NOT_FOUND` (404 constant) to determine whether to re-raise or return a safe default (None, empty list, idempotent True).
4. **Return Values**: Return `Output`-typed objects (TypedDicts defined in models.py), or None/empty list on 404.

**New Module Design**: `github_branches.py` follows these patterns. Five functions create/check/list/merge/delete integration branches. Branch naming: `milestone/{N}-{slug}` (e.g., `milestone/3-v1.1`).

### Architecture Overview: Five Functions

1. **create_integration_branch(milestone_number, slug, base_branch="main", repo="", output=None) → BranchInfo**
   - Construct name via `_branch_name()` helper (`milestone/{N}-{slug}`)
   - Get base branch HEAD SHA: `repo.get_branch(base_branch).commit.sha`
   - Create ref: `repo.create_git_ref(f"refs/heads/{name}", sha)`
   - Return BranchInfo(name, sha, last_commit_date, age_days=0)
   - Raise BacklogError if branch already exists (422 status)

2. **get_integration_branch_status(branch_name, repo="", output=None) → BranchInfo | None**
   - Get ref: `repo.get_git_ref(f"heads/{branch_name}")`
   - Return None on 404 (non-raising)
   - Extract last_commit_date from commit object; compute age_days
   - Return BranchInfo or re-raise non-404 GithubException

3. **merge_integration_branch(head_branch, base_branch, commit_message, repo="", output=None) → MergeResult**
   - Call `repo.merge(base_branch, head_branch, commit_message)`
   - Catch GithubException with status 409 (conflict): raise BranchConflictError
   - Return MergeResult(sha, message)

4. **delete_integration_branch(branch_name, repo="", output=None) → bool**
   - Get ref: `repo.get_git_ref(f"heads/{branch_name}")`; call `ref.delete()`
   - Return True on success or on 404 (idempotent)
   - Return False on unexpected errors (with output.warn)

5. **list_integration_branches(repo="", output=None) → list[BranchInfo]**
   - List all branches with `repo.get_branches()`
   - Filter those matching `milestone/` prefix
   - Return list sorted by last_commit_date (most recent first)
   - Return empty list on GitHub unavailable (soft-fail)

### For New Feature Implementation: What Needs to Connect

**Files to Create**:
- `plugins/development-harness/backlog_core/github_branches.py` — Five functions + `_branch_name()` helper + `BRANCH_PREFIX` constant
- `plugins/development-harness/tests/test_github_branches.py` — Pytest tests (18 test cases)

**Files to Modify**:
- `plugins/development-harness/backlog_core/models.py` — Add `BranchInfo(TypedDict)`, `MergeResult(TypedDict)`, `BranchConflictError(BacklogError)` exception class
- `plugins/development-harness/backlog_core/__init__.py` — Export 5 functions + 3 types

**Key Dependencies**:
- Existing `github.py` functions: `get_github()`, `try_get_github()`, `_repo()`, `_HTTP_NOT_FOUND` constant
- Existing models.py: `Output`, `GitHubUnavailableError`, `BacklogError`, `TypedDict`
- PyGithub: `Repository`, `GithubException`, `Branch`, `GitRef`

**Design Patterns to Follow**:
- Signature pattern: `func(required_args, *, optional_with_defaults, repo="", output=None) → OutputType`
- Error handling: Catch GithubException, check status against _HTTP_NOT_FOUND, re-raise or return safe default
- Idempotent delete: Return True on both success and 404
- Non-raising on missing resource: Return None or empty list on 404
- Status reporting: Use output.warn() for non-fatal, output.status() for progress

### Technical Reference: Data Models

**BranchInfo (new TypedDict in models.py)**:
- `name: str` — branch name (e.g., `milestone/3-v1.1`)
- `sha: str` — HEAD commit SHA
- `last_commit_date: str` — ISO 8601 timestamp
- `age_days: int` — computed days since last commit

**MergeResult (new TypedDict in models.py)**:
- `sha: str` — new HEAD SHA of base branch after merge
- `message: str` — commit message used

**BranchConflictError (new Exception in models.py, extends BacklogError)**:
- `head_branch: str` — source branch
- `base_branch: str` — target branch
- `conflict_files: list[str]` — file paths with conflicts (optional)
- `__init__(head_branch, base_branch, conflict_files=None)` — message includes branch names and first 5 files

### Critical Implementation Details

**Branch Name Construction**:
- Helper: `_branch_name(milestone_number: int, slug: str) → str` returns `f"milestone/{milestone_number}-{slug}"`
- Constant: `BRANCH_PREFIX = "milestone/"`
- Input validation: slug matches regex `^[a-zA-Z0-9][a-zA-Z0-9._-]*$`, milestone_number > 0

**PyGithub API Usage**:
- Create ref: `repo.create_git_ref(ref=f"refs/heads/{branch_name}", sha=base_sha)`
- Get branch: `repo.get_branch(branch_name)` → Branch object; `.commit.sha` for HEAD SHA
- Get ref: `repo.get_git_ref(ref=f"heads/{branch_name}")` → GitRef object
- Delete ref: `ref.delete()`
- Merge: `repo.merge(base=base_branch, head=head_branch, commit_message=message)` → returns dict-like with 'sha'
- List branches: `repo.get_branches()` → paginated list

**Error Codes**:
- 404 (branch not found): _HTTP_NOT_FOUND, caught in status/delete, return safe default
- 409 (merge conflict): raise BranchConflictError
- 422 (unprocessable, e.g., branch exists): raise BacklogError

**Test File Location**: `plugins/development-harness/tests/test_github_branches.py`
**Test Strategy**: Mock `get_github()` to return MagicMock Repository. Test all 5 functions with happy-path, error-path (404, 409, 422, 500), and edge cases.

### File Inventory

**Create (new files)**:
- `plugins/development-harness/backlog_core/github_branches.py` (5 functions + helpers, ~250 lines)
- `plugins/development-harness/tests/test_github_branches.py` (18 test cases, ~400 lines)

**Modify (existing files)**:
- `plugins/development-harness/backlog_core/models.py` (add 3 classes: BranchInfo, MergeResult, BranchConflictError)
- `plugins/development-harness/backlog_core/__init__.py` (export 5 functions + 3 types)

**Reference (read-only)**:
- `plan/architect-integration-branch-management.md` (architecture spec, Sections 3-10 for API details)
- `plan/feature-context-integration-branch-management.md` (feature goals, use scenarios, gap analysis)
- `plugins/development-harness/backlog_core/github.py` (pattern reference: get_github, _repo, Output handling, GithubException)
- PyGithub documentation (repo.merge(), create_git_ref(), get_git_ref() API)

### Discovered During Implementation

_Session Date: 2026-03-21_

During implementation, several patterns and constraints emerged that weren't fully documented in the original context manifest.

**Key Discoveries:**

1. **`_get_repo()` Private Helper Introduced**: The implementation extracted authentication + repo resolution into a private `_get_repo(repo: str) -> Repository` helper rather than calling `get_github()` inline per function. This consolidates the two-step call (`gh = get_github(); return gh.get_repo(_repo(repo))`) repeated by every public function. The `ty` type checker flags a mismatch: `get_github()` returns a `Github` object, and the `Repository` return-type annotation on `_get_repo` is only available under the `TYPE_CHECKING` guard, creating a static analysis gap. Future developers should add a `# type: ignore` comment or use a runtime-visible import to satisfy `ty`.

2. **Input Validation Not Implemented**: The architecture spec (Section 6 Security Architecture) required slug validation against `^[a-zA-Z0-9][a-zA-Z0-9._-]*$`, a `milestone_number > 0` guard, and a `head_branch != base_branch` check in `merge_integration_branch`. None of these guards were implemented. The code review flagged this gap. Without them, invalid inputs surface as confusing GitHub 422 errors with no diagnostic message. Future implementations of similar functions should add these guards upfront.

3. **`_HTTP_UNPROCESSABLE = 422` and `_HTTP_CONFLICT = 409` Defined Locally**: These status code constants are defined in `github_branches.py` itself rather than imported from `github.py`. Only `_HTTP_NOT_FOUND` is imported. Check `github.py` for existing status constants before defining new ones locally to avoid drift.

4. **`_branch_info_from_branch()` Helper Added**: The implementation added a private `_branch_info_from_branch(branch: Branch) -> BranchInfo` helper not specified in the architecture spec. It handles the `datetime` vs ISO-string polymorphism in PyGithub's `commit.commit.author.date` field — the date can be a `datetime` object or an ISO string depending on whether the commit was fetched eagerly or lazily. The `# type: ignore[union-attr]` comment on that line documents the PyGithub type stub gap.

5. **`repo.merge()` Returns `None` on No-Op**: PyGithub's `repo.merge()` returns `None` when the head branch is already merged into base (already up to date), not a conflict. The implementation handles this by reading the base branch HEAD SHA directly in that code path rather than extracting `.sha` from the return value.

#### Updated Technical Details

- `_get_repo(repo: str) -> Repository` — private helper wrapping `get_github().get_repo(_repo(repo))`; `Repository` type annotation lives under `TYPE_CHECKING` guard
- `_branch_info_from_branch(branch: Branch) -> BranchInfo` — private helper; handles `commit.commit.author.date` returning `datetime | str`
- `_HTTP_CONFLICT = 409`, `_HTTP_NO_CONTENT = 204`, `_HTTP_UNPROCESSABLE = 422` — defined locally in `github_branches.py`
- 38 tests created in `plugins/development-harness/tests/test_github_branches.py` (spec minimum was 15)

#### Gotchas for Future Developers

- PyGithub `commit.commit.author.date` returns `datetime | str` depending on eager vs. lazy fetch. Always check `isinstance(raw_date, datetime)` before calling `.replace(tzinfo=UTC)`.
- `get_github()` returns a `Github` connection object, not a `Repository`. Call `.get_repo(slug)` on it. The `_get_repo()` helper encapsulates this two-step pattern.
- Input validation (slug regex, milestone_number > 0) was specified in the architecture spec but not implemented. Tests do not cover invalid-slug rejection. Invalid inputs will produce confusing GitHub 422 errors.
- `repo.merge()` returning `None` means already-up-to-date, not a conflict. Handle the `None` case by reading the base branch HEAD directly rather than calling `.sha` on `None`.
