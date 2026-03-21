---
slug: simplify-review-fixes
goal: Fix 21 simplify review findings in milestone orchestration tooling across
  dispatch_schema/, github_branches.py, and backlog_core/operations.py without
  breaking 160+ existing tests
issue: 938
context: 'Story #938. Target: plugins/development-harness/dispatch_schema/ (models.py,
  gates.py, validator.py, server.py), github_branches.py, backlog_core/operations.py.
  Stack: Python 3.11+, Pydantic v2, pytest. T01+T02+T03 are fully independent and
  run in parallel. T04 depends on all three completing first.'
acceptance_criteria:
- 'AC1: All 160+ existing tests pass (uv run pytest plugins/development-harness/tests/
  -x -q exits 0)'
- 'AC2: No duplicate _MIN_CONFLICT_GROUP_SIZE definition exists in validator.py'
- 'AC3: tests/test_gates.py deleted; test_dispatch_schema/test_gates.py is the sole
  gates test file'
- 'AC4: CommandResult.passed is a @computed_field derived from exit_code, not a stored
  field'
- 'AC5: analyze_impact_radius_conflicts accepts ImpactRadiusInput TypedDict instead
  of dict[str, object]'
- 'AC6: _dispatch_plan_path importable from dispatch_schema package, not only from
  server.py'
- 'AC7: ruff check exits 0 on all modified files'
tasks:
- task: T01
  title: Fix high-severity subprocess timeout, duplicate constant, and branch
    validation (H1, H3, H4)
  status: complete
  agent: python-cli-architect
  dependencies: []
  priority: 1
  complexity: medium
  accuracy-risk: medium
  skills:
  - python3-development
  parallelize-with:
  - T02
  - T03

  started: '2026-03-21T02:42:21.134359+00:00'
- task: T02
  title: Remove duplicate test file tests/test_gates.py (H2)
  status: complete
  agent: python-pytest-architect
  dependencies: []
  priority: 1
  complexity: low
  accuracy-risk: medium
  skills:
  - python3-development
  - fastmcp-python-tests
  parallelize-with:
  - T01
  - T03

  started: '2026-03-21T02:42:51.878017+00:00'
- task: T03
  title: Fix medium and low severity independent findings (M1, M2, L1, L2, L3)
  status: complete
  agent: python-cli-architect
  dependencies: []
  priority: 1
  complexity: medium
  accuracy-risk: medium
  skills:
  - python3-development
  parallelize-with:
  - T01
  - T02

  started: '2026-03-21T02:42:25.429979+00:00'
- task: T04
  title: Fix H5 (TypedDict for analyze_impact_radius_conflicts) and M3 (extract
    _dispatch_plan_path)
  status: complete
  agent: python-cli-architect
  dependencies:
  - T01
  - T02
  - T03
  priority: 2
  complexity: medium
  accuracy-risk: medium
  skills:
  - python3-development
  started: '2026-03-21T02:46:40.508473+00:00'

---

## Task T01: Fix high-severity subprocess timeout, duplicate constant, and branch validation (H1, H3, H4)

**Status**: NOT STARTED
**Dependencies**: None
**Priority**: 1
**Complexity**: Medium
**Agent**: python-cli-architect
**Parallelize-With**: T02, T03
**Accuracy-Risk**: medium

### Context

Three independent high-severity findings in separate files. No shared file writes between T01, T02, and T03 — safe to run in parallel.

### Objective

Apply H1 (gates.py subprocess timeout), H3 (remove duplicate _MIN_CONFLICT_GROUP_SIZE from validator.py), and H4 (move validation into _branch_name() in github_branches.py).

### Inputs

- plugins/development-harness/dispatch_schema/gates.py
- plugins/development-harness/dispatch_schema/validator.py
- plugins/development-harness/backlog_core/operations.py (read-only, source of _MIN_CONFLICT_GROUP_SIZE)
- plugins/development-harness/github_branches.py

### Requirements

#### H1: subprocess timeout in gates.py

1. Add a `timeout` parameter (default 300) to the subprocess call(s) in gates.py that currently have no timeout
2. Catch `subprocess.TimeoutExpired` and re-raise as or translate to exit code 124 (POSIX timeout convention)
3. Ensure callers that check exit codes still receive a consistent integer result

#### H3: duplicate _MIN_CONFLICT_GROUP_SIZE in validator.py

4. Remove the duplicate definition of `_MIN_CONFLICT_GROUP_SIZE` from validator.py
5. Import `_MIN_CONFLICT_GROUP_SIZE` from `backlog_core.operations` (or wherever the canonical definition lives)
6. Verify no other references to the removed definition break

#### H4: branch name validation helper in github_branches.py

7. Extract the inline branch-name validation logic into a dedicated `_branch_name(value)` helper function
8. Call `_branch_name()` from all sites that previously contained the inlined validation

### Constraints

- Do not change the public API signatures of any function or class
- Do not alter test files in this task
- Do not touch tests/test_gates.py (T02 handles that file)

### Expected Outputs

- plugins/development-harness/dispatch_schema/gates.py (modified)
- plugins/development-harness/dispatch_schema/validator.py (modified)
- plugins/development-harness/github_branches.py (modified)

### Acceptance Criteria

1. gates.py subprocess call has explicit timeout=300 and handles TimeoutExpired with exit 124
2. validator.py contains no local definition of _MIN_CONFLICT_GROUP_SIZE; it imports the value from operations.py
3. github_branches.py has a _branch_name() helper and all former inline validation sites call it
4. `uv run pytest plugins/development-harness/tests/ -x -q` exits 0 (no regressions)
5. `uv run ruff check plugins/development-harness/dispatch_schema/gates.py plugins/development-harness/dispatch_schema/validator.py plugins/development-harness/github_branches.py` exits 0

### Verification Steps

1. `grep -n "timeout" plugins/development-harness/dispatch_schema/gates.py` — confirm timeout= present
2. `grep -n "TimeoutExpired" plugins/development-harness/dispatch_schema/gates.py` — confirm handler present
3. `grep -n "_MIN_CONFLICT_GROUP_SIZE" plugins/development-harness/dispatch_schema/validator.py` — confirm import only, no definition
4. `grep -n "_branch_name" plugins/development-harness/github_branches.py` — confirm function defined and called
5. `uv run pytest plugins/development-harness/tests/ -x -q --tb=short`

### CoVe Checks

- Key claims to verify:
  - POSIX exit code for timeout is 124 (used by GNU timeout utility)
  - _MIN_CONFLICT_GROUP_SIZE canonical location is operations.py
- Verification questions:
  1. Does `backlog_core/operations.py` currently export `_MIN_CONFLICT_GROUP_SIZE` at module level or is it private?
  2. Does any test directly assert exit code 124 for timeout, or only check the exception path?
- Evidence to collect:
  - `grep -n "_MIN_CONFLICT_GROUP_SIZE" plugins/development-harness/backlog_core/operations.py`
  - `grep -rn "124" plugins/development-harness/tests/`
- Revision rule: if _MIN_CONFLICT_GROUP_SIZE is private in operations.py, make it importable (remove leading underscore or re-export) before removing it from validator.py

### Handoff

Return: list of files changed, pytest exit code, ruff exit code, and any CoVe check findings

---

## Task T02: Remove duplicate test file tests/test_gates.py (H2)

**Status**: NOT STARTED
**Dependencies**: None
**Priority**: 1
**Complexity**: Low
**Agent**: python-pytest-architect
**Parallelize-With**: T01, T03
**Accuracy-Risk**: medium

### Context

tests/test_gates.py is superseded by tests/test_dispatch_schema/test_gates.py. The duplicate causes redundant test execution and maintenance confusion. This is finding H2.

### Objective

Verify the superseding file covers all tests in the duplicate, then delete the duplicate.

### Inputs

- plugins/development-harness/tests/test_gates.py (duplicate — to be deleted)
- plugins/development-harness/tests/test_dispatch_schema/test_gates.py (authoritative)

### Requirements

1. Read both files and produce a side-by-side list of test function names
2. Confirm every test_* function in tests/test_gates.py has a counterpart (same name or equivalent coverage) in tests/test_dispatch_schema/test_gates.py
3. If any test in the duplicate has no counterpart, migrate it to the authoritative file before deleting the duplicate
4. Delete plugins/development-harness/tests/test_gates.py

### Constraints

- Do not delete tests/test_gates.py until coverage parity is confirmed
- Do not modify the authoritative file unless a migration is required under Requirement 3
- Do not alter any implementation files in this task

### Expected Outputs

- plugins/development-harness/tests/test_gates.py (deleted)
- plugins/development-harness/tests/test_dispatch_schema/test_gates.py (unchanged, or with migrated tests appended)

### Acceptance Criteria

1. plugins/development-harness/tests/test_gates.py no longer exists
2. `uv run pytest plugins/development-harness/tests/ -x -q` exits 0
3. No test function that previously existed only in the deleted file is missing from the suite

### Verification Steps

1. Before deletion: `uv run pytest plugins/development-harness/tests/test_gates.py --collect-only -q` — record names
2. `uv run pytest plugins/development-harness/tests/test_dispatch_schema/test_gates.py --collect-only -q` — confirm superset
3. Delete the file, then: `uv run pytest plugins/development-harness/tests/ -x -q --tb=short`
4. `ls plugins/development-harness/tests/test_gates.py 2>&1` — confirm file absent (expect error)

### CoVe Checks

- Key claims to verify:
  - tests/test_dispatch_schema/test_gates.py is a strict superset of tests/test_gates.py
- Verification questions:
  1. Are there any tests in test_gates.py that test behavior not present in test_dispatch_schema/test_gates.py?
  2. Does the pytest suite collect test_gates.py via any conftest import that would break on deletion?
- Evidence to collect:
  - Side-by-side function name lists from both files
  - `grep -rn "test_gates" plugins/development-harness/tests/conftest.py` (if conftest exists)
- Revision rule: if any unique test is found in the duplicate, migrate it first; document the migration in the handoff

### Handoff

Return: confirmation of deletion, list of any migrated tests, pytest exit code

---

## Task T03: Fix medium and low severity independent findings (M1, M2, L1, L2, L3)

**Status**: NOT STARTED
**Dependencies**: None
**Priority**: 1
**Complexity**: Medium
**Agent**: python-cli-architect
**Parallelize-With**: T01, T02
**Accuracy-Risk**: medium

### Context

Five independent findings across dispatch_schema/models.py, backlog_core/operations.py, and dispatch_schema/validator.py. No shared file writes with T01 or T02 — safe to run in parallel.

### Objective

Apply M1 (CommandResult.passed as computed_field), M2 (union-find rank), L1 (shared ConfigDict), L2 (regex DRY), and L3 (shutil.which caching) in a single pass.

### Inputs

- plugins/development-harness/dispatch_schema/models.py
- plugins/development-harness/backlog_core/operations.py
- plugins/development-harness/dispatch_schema/validator.py (L2 only)

### Requirements

#### M1: CommandResult.passed as @computed_field

1. Change `CommandResult.passed` from a plain field with default logic to a Pydantic v2 `@computed_field` derived from `exit_code == 0`
2. Ensure `@computed_field` is imported from `pydantic`
3. Confirm serialization behavior: `passed` must still appear in `.model_dump()` output

#### M2: union-find rank in operations.py

4. Add a `rank` dict to `_UnionFind` (initialized to `{node: 0}` on `make_set`)
5. Update `union()` to attach the shorter tree under the taller tree using rank; increment rank only when ranks are equal

#### L1: shared ConfigDict for Pydantic models in dispatch_schema

6. Define a single `_BASE_CONFIG = ConfigDict(...)` in models.py (or a shared module)
7. Apply it as `model_config = _BASE_CONFIG` on each Pydantic model that currently duplicates the same ConfigDict settings
8. Do not change the ConfigDict values, only deduplicate them

#### L2: regex pattern DRY in _validate_slug

9. Extract the repeated regex pattern(s) in `_validate_slug` (validator.py) to a module-level constant (e.g., `_SLUG_PATTERN`)
10. Replace all inline uses with the constant

#### L3: shutil.which caching via lru_cache

11. Wrap the `shutil.which` call(s) in a helper decorated with `@functools.lru_cache(maxsize=None)` or `@cache`
12. Import `cache` from `functools` (Python 3.9+) or use `lru_cache`

### Constraints

- Do not change observable behavior of any function
- @computed_field must remain serializable (test with .model_dump())
- Do not alter public class names or module-level exports
- Do not modify test files

### Expected Outputs

- plugins/development-harness/dispatch_schema/models.py (modified)
- plugins/development-harness/backlog_core/operations.py (modified)
- plugins/development-harness/dispatch_schema/validator.py (modified)

### Acceptance Criteria

1. `CommandResult(exit_code=0).passed` returns True; `CommandResult(exit_code=1).passed` returns False
2. `CommandResult(exit_code=0).model_dump()` includes `"passed": True`
3. _UnionFind.union() merges by rank; code inspection confirms no redundant rank increments
4. No Pydantic model in dispatch_schema duplicates ConfigDict settings that are now in _BASE_CONFIG
5. _validate_slug uses _SLUG_PATTERN constant; no bare regex literal remains in the function body
6. shutil.which call is wrapped in an lru_cache or @cache decorated helper
7. `uv run pytest plugins/development-harness/tests/ -x -q` exits 0
8. `uv run ruff check plugins/development-harness/dispatch_schema/models.py plugins/development-harness/dispatch_schema/validator.py plugins/development-harness/backlog_core/operations.py` exits 0

### Verification Steps

1. `grep -n "computed_field" plugins/development-harness/dispatch_schema/models.py` — confirm decorator present
2. `grep -n "_SLUG_PATTERN" plugins/development-harness/dispatch_schema/validator.py` — confirm constant defined
3. `grep -n "lru_cache\|@cache" plugins/development-harness/dispatch_schema/gates.py plugins/development-harness/dispatch_schema/validator.py plugins/development-harness/backlog_core/operations.py` — confirm caching present
4. `grep -n "rank" plugins/development-harness/backlog_core/operations.py` — confirm rank dict in _UnionFind
5. `uv run pytest plugins/development-harness/tests/ -x -q --tb=short`

### CoVe Checks

- Key claims to verify:
  - Pydantic v2 @computed_field appears in model_dump() by default
  - Python 3.11 has functools.cache (added in 3.9)
- Verification questions:
  1. Does the repo use `pydantic>=2.0`? Check pyproject.toml.
  2. Are there existing tests that assert `CommandResult.passed` as a plain attribute that would break on type change?
  3. Does `_validate_slug` exist in validator.py or is the function named differently?
- Evidence to collect:
  - `grep "pydantic" plugins/development-harness/pyproject.toml`
  - `grep -n "\.passed" plugins/development-harness/tests/`
  - `grep -n "validate_slug\|_validate_slug" plugins/development-harness/dispatch_schema/validator.py`
- Revision rule: if pydantic version is v1, use `@validator` + `@property` pattern instead of `@computed_field`; document in handoff

### Handoff

Return: files changed, acceptance criteria check results, pytest exit code, ruff exit code, CoVe findings

---

## Task T04: Fix H5 (TypedDict for analyze_impact_radius_conflicts) and M3 (extract _dispatch_plan_path)

**Status**: NOT STARTED
**Dependencies**: T01, T02, T03
**Priority**: 2
**Complexity**: Medium
**Agent**: python-cli-architect
**Accuracy-Risk**: medium

### Context

H5 and M3 depend on GROUP 1 fixes completing first (T01/T02/T03). H5 adds a TypedDict to replace dict[str, object] in the analyze_impact_radius_conflicts signature. M3 moves _dispatch_plan_path from server.py into the dispatch_schema public API so other modules can import it without going through the server layer.

### Objective

Replace dict[str, object] input type with a TypedDict and extract _dispatch_plan_path into the dispatch_schema package, without breaking existing callers or tests.

### Inputs

- plugins/development-harness/dispatch_schema/validator.py or operations.py (where analyze_impact_radius_conflicts lives — confirm by grep)
- plugins/development-harness/dispatch_schema/server.py (source of _dispatch_plan_path)
- plugins/development-harness/dispatch_schema/__init__.py (to update exports if needed)

### Requirements

#### H5: TypedDict for analyze_impact_radius_conflicts

1. Define a TypedDict (e.g., `ImpactRadiusInput`) capturing all keys currently accessed from the `dict[str, object]` parameter
2. Update the function signature to accept `ImpactRadiusInput` instead of `dict[str, object]`
3. Export `ImpactRadiusInput` from the dispatch_schema package (add to `__init__.py` if applicable)
4. Update all call sites within dispatch_schema/ and backlog_core/ to pass the TypedDict-typed value (structural compatibility means no runtime change needed, but type annotations must be updated)

#### M3: extract _dispatch_plan_path into dispatch_schema public API

5. Move (or re-export) `_dispatch_plan_path` from server.py to an appropriate dispatch_schema module (e.g., `dispatch_schema/paths.py` or `dispatch_schema/__init__.py`)
6. Make it a public name (rename to `dispatch_plan_path` if it was private only due to server-local scope)
7. Update server.py to import it from its new location
8. Confirm no other module imports `_dispatch_plan_path` directly from server.py (grep for such imports and update them)

### Constraints

- Do not change runtime behavior — TypedDict is structural and transparent at runtime
- Do not rename the function `analyze_impact_radius_conflicts`
- Do not remove `_dispatch_plan_path` from server.py until the new location is confirmed working
- Do not modify test files except to update import paths if M3 changes a module location

### Expected Outputs

- plugins/development-harness/dispatch_schema/validator.py or relevant module (modified — H5)
- plugins/development-harness/dispatch_schema/server.py (modified — M3 import update)
- plugins/development-harness/dispatch_schema/__init__.py (modified — new exports)
- New file if a paths.py is created: plugins/development-harness/dispatch_schema/paths.py

### Acceptance Criteria

1. `analyze_impact_radius_conflicts` parameter annotated with `ImpactRadiusInput` TypedDict, not `dict[str, object]`
2. `ImpactRadiusInput` is importable from `dispatch_schema` package root
3. `dispatch_plan_path` (or `_dispatch_plan_path`) is importable from a dispatch_schema module — not only from server.py
4. server.py imports it from the new location rather than defining it locally
5. `uv run pytest plugins/development-harness/tests/ -x -q` exits 0
6. `uv run ruff check plugins/development-harness/dispatch_schema/` exits 0

### Verification Steps

1. `grep -rn "dict\[str, object\]" plugins/development-harness/dispatch_schema/` — should return 0 results for the analyze_impact_radius_conflicts parameter
2. `grep -rn "ImpactRadiusInput" plugins/development-harness/dispatch_schema/` — confirm defined and exported
3. `grep -n "_dispatch_plan_path\|dispatch_plan_path" plugins/development-harness/dispatch_schema/server.py` — confirm import, not definition
4. `uv run pytest plugins/development-harness/tests/ -x -q --tb=short`
5. `uv run ruff check plugins/development-harness/dispatch_schema/`

### CoVe Checks

- Key claims to verify:
  - TypedDict is structural at runtime (no isinstance checks break)
  - _dispatch_plan_path is currently defined in server.py, not imported from elsewhere
- Verification questions:
  1. What keys does analyze_impact_radius_conflicts actually access from its dict parameter? List them to define ImpactRadiusInput fields.
  2. Is _dispatch_plan_path called from any module other than server.py already?
  3. Does dispatch_schema/__init__.py exist and use explicit __all__?
- Evidence to collect:
  - `grep -n "analyze_impact_radius_conflicts\|_dispatch_plan_path" plugins/development-harness/dispatch_schema/server.py plugins/development-harness/dispatch_schema/validator.py`
  - `grep -rn "_dispatch_plan_path" plugins/development-harness/`
  - Read plugins/development-harness/dispatch_schema/__init__.py
- Revision rule: if _dispatch_plan_path is already imported from elsewhere, trace the full import chain before moving it; document in handoff

### Handoff

Return: files changed, ImpactRadiusInput fields defined, new location of dispatch_plan_path, pytest exit code, ruff exit code, CoVe findings
