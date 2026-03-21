---
plan_number: 2
slug: dispatch-plan-tooling
goal: Implement dispatch_schema/ module with Pydantic models, YAML I/O,
  validation, conflict analysis, and MCP tool exposure for milestone dispatch
  plans
context: 'Story issue #920. dispatch_schema/ module in plugins/development-harness/.
  See Context Manifest section below.'
issue: 920
feature: Dispatch Plan Tooling
status: not-started
created: '2026-03-20T00:00:00Z'
acceptance_criteria:
- 'AC1: dispatch_schema/ package is importable and exports all public symbols listed
  in architect spec section 4.6'
- 'AC2: read_dispatch_plan() round-trips a valid YAML file through write_dispatch_plan()
  and produces identical DispatchPlan models'
- 'AC3: validate_plan_integrity() detects all five integrity violation types specified
  in architect spec section 4.4'
- 'AC4: detect_stale_plan() correctly identifies added and removed issues'
- 'AC5: analyze_impact_radius_conflicts() produces correct conflict groups using union-find
  for transitive overlap'
- 'AC6: All tests pass with 80%+ overall coverage, 95%+ on validator and conflict
  analysis'
- 'AC7: Four MCP tools (dispatch_read, dispatch_validate, dispatch_stale_check, dispatch_conflicts)
  registered on backlog server'
tasks:
- task: T01
  title: Pydantic models and package scaffolding
  status: complete
  started: '2026-03-20T00:00:00Z'
  completed: '2026-03-20T00:00:00Z'
  agent: python-cli-architect
  dependencies: []
  priority: 1
  complexity: medium
  accuracy-risk: medium
  skills:
  - python3-development
  - fastmcp-python-tests
  parallelize-with: []
  reason: Foundation for all other tasks -- every component imports from
    core/models.py
  handoff: All model classes importable from dispatch_schema.core.models. Enum
    values match YAML schema kebab-case strings.
  body: |
    ## Context

    New module `plugins/development-harness/dispatch_schema/` mirrors the established `sam_schema/` architecture.
    Architecture spec section 4.1 provides the complete Pydantic model definitions.
    Pattern reference: `plugins/development-harness/sam_schema/core/models.py` for field alias conventions.

    ## Objective

    Create the dispatch_schema package scaffolding and all Pydantic v2 models specified in the architecture.

    ## Inputs

    - Architecture spec: `plan/architect-dispatch-plan-tooling.md` (section 4.1 for models, section 4.6 for __init__.py exports)
    - Pattern reference: `plugins/development-harness/sam_schema/core/models.py`

    ## Requirements

    1. Create directory structure: `dispatch_schema/`, `dispatch_schema/core/`, `dispatch_schema/readers/`, `dispatch_schema/writers/`
    2. Create `__init__.py` files for `dispatch_schema/core/`, `dispatch_schema/readers/`, `dispatch_schema/writers/` (empty or minimal)
    3. Implement `dispatch_schema/core/models.py` with all seven model classes: `ItemPriority`, `ItemStatus`, `MilestoneHeader`, `ConflictGroup`, `WaveItem`, `Wave`, `QualityGates`, `DispatchPlan`
    4. All models use `ConfigDict(populate_by_name=True, use_enum_values=True)`
    5. All kebab-case YAML fields have `AliasChoices` accepting both kebab-case and snake_case
    6. Use `from __future__ import annotations` for forward references
    7. Use `StrEnum` from stdlib `enum` module for `ItemPriority` and `ItemStatus`
    8. Field constraints match the spec: `ge=1` on numbers, `min_length=1` on required strings, `min_length=2` on `ConflictGroup.items`

    ## Constraints

    - Do NOT create `dispatch_schema/__init__.py` with full public API re-exports yet -- that is Task T05
    - Create only a minimal `dispatch_schema/__init__.py` (empty or version-only) so the package is importable
    - Do NOT add CLI entry points -- this is a library-only module (ADR-001)
    - Do NOT import from `backlog_core` -- models are standalone

    ## Expected Outputs

    - `plugins/development-harness/dispatch_schema/__init__.py` (minimal)
    - `plugins/development-harness/dispatch_schema/core/__init__.py`
    - `plugins/development-harness/dispatch_schema/core/models.py`
    - `plugins/development-harness/dispatch_schema/readers/__init__.py`
    - `plugins/development-harness/dispatch_schema/writers/__init__.py`

    ## Acceptance Criteria

    1. `from dispatch_schema.core.models import DispatchPlan, Wave, WaveItem, ConflictGroup, MilestoneHeader, QualityGates, ItemPriority, ItemStatus` succeeds
    2. `DispatchPlan` accepts both kebab-case and snake_case field names in `model_validate()`
    3. `ItemPriority("P0")` and `ItemStatus("pending")` produce valid enum instances
    4. `ConflictGroup(group_id=1, reason="overlap", items=["A"])` raises `ValidationError` (min_length=2)
    5. `WaveItem` defaults: `conflict_group=None`, `depends_on=[]`, `status=ItemStatus.PENDING`

    ## Verification Steps

    1. `cd plugins/development-harness && uv run python -c "from dispatch_schema.core.models import DispatchPlan; print('OK')"`
    2. `cd plugins/development-harness && uv run python -c "from dispatch_schema.core.models import ConflictGroup; ConflictGroup(group_id=1, reason='test', items=['a','b']); print('OK')"`
    3. `uv run ruff check plugins/development-harness/dispatch_schema/`
    4. `uv run prek run --files plugins/development-harness/dispatch_schema/core/models.py`

    ## CoVe Checks

    - Key claims to verify:
      - Pydantic v2 `AliasChoices` accepts multiple alias strings for deserialization
      - `StrEnum` is available in Python 3.11+ stdlib `enum` module
      - `ConfigDict(use_enum_values=True)` serializes enum members as their string values
    - Verification questions:
      1. Does `AliasChoices("snake_case", "kebab-case")` allow `model_validate({"kebab-case": val})` to populate the `snake_case` attribute?
      2. Does `use_enum_values=True` cause `model_dump()` to return string values instead of enum instances?
    - Evidence to collect:
      - Run a quick Pydantic model validation in Python REPL to confirm alias behavior
      - Check `sam_schema/core/models.py` for existing working pattern
    - Revision rule:
      - If AliasChoices behavior differs from spec, match the working pattern in sam_schema exactly

- task: T02
  title: YAML reader (ruamel.yaml)
  status: complete
  agent: python-cli-architect
  dependencies:
  - T01
  priority: 2
  complexity: medium
  accuracy-risk: low
  skills:
  - python3-development
  parallelize-with:
  - T03
  - T04
  - T06
  reason: Reader is needed before writer tests can round-trip, and before MCP
    tools can read plans
  handoff: read_dispatch_plan() returns validated DispatchPlan from YAML file.
    Raises FileNotFoundError or ValueError on bad input.
  body: |
    ## Context

    Architecture spec section 4.2 defines the reader interface. Pattern reference: `plugins/development-harness/sam_schema/readers/yaml_reader.py`.
    Uses ruamel.yaml in round-trip mode per repo standard (`.claude/rules/yaml-toml-libraries.md`).

    ## Objective

    Implement `read_dispatch_plan()` that loads a dispatch plan YAML file and returns a validated `DispatchPlan` Pydantic model.

    ## Inputs

    - Architecture spec: `plan/architect-dispatch-plan-tooling.md` (section 4.2)
    - Pattern reference: `plugins/development-harness/sam_schema/readers/yaml_reader.py`
    - Models from T01: `plugins/development-harness/dispatch_schema/core/models.py`

    ## Requirements

    1. Implement `read_dispatch_plan(path: Path) -> DispatchPlan` in `dispatch_schema/readers/yaml_reader.py`
    2. Use `ruamel.yaml` YAML() with `typ='safe'` or round-trip mode
    3. Load YAML dict, pass to `DispatchPlan.model_validate()` for Pydantic validation
    4. Raise `FileNotFoundError` if path does not exist
    5. Raise `ValueError` with descriptive message if YAML parsing fails or Pydantic validation fails
    6. Do not catch unexpected exceptions -- let them propagate

    ## Constraints

    - Do NOT use PyYAML (`yaml.safe_load`) -- use `ruamel.yaml` only
    - Do NOT add any GitHub API calls
    - Function is pure I/O: read file, parse, validate, return

    ## Expected Outputs

    - `plugins/development-harness/dispatch_schema/readers/yaml_reader.py`

    ## Acceptance Criteria

    1. `read_dispatch_plan(Path("valid.yaml"))` returns a `DispatchPlan` instance
    2. `read_dispatch_plan(Path("nonexistent.yaml"))` raises `FileNotFoundError`
    3. `read_dispatch_plan(Path("malformed.yaml"))` raises `ValueError`

    ## Verification Steps

    1. `cd plugins/development-harness && uv run python -c "from dispatch_schema.readers.yaml_reader import read_dispatch_plan; print('importable')"`
    2. `uv run ruff check plugins/development-harness/dispatch_schema/readers/yaml_reader.py`
    3. Create a minimal valid YAML fixture manually and test `read_dispatch_plan()` returns a DispatchPlan

  started: '2026-03-21T01:05:06.061720+00:00'
- task: T03
  title: YAML writer with atomic rename
  status: complete
  agent: python-cli-architect
  dependencies:
  - T01
  priority: 2
  complexity: medium
  accuracy-risk: low
  skills:
  - python3-development
  parallelize-with:
  - T02
  - T04
  - T06
  reason: Writer is needed for groom-milestone to persist plans and for
    round-trip testing
  handoff: write_dispatch_plan() serializes DispatchPlan to kebab-case YAML with
    atomic temp+rename. Returns the written path.
  body: |
    ## Context

    Architecture spec section 4.3 defines the writer interface. Pattern reference: `plugins/development-harness/sam_schema/writers/yaml_writer.py`.
    Uses atomic write pattern (tempfile + os.rename) to prevent partial files.

    ## Objective

    Implement `write_dispatch_plan()` that serializes a `DispatchPlan` to YAML using kebab-case keys and atomic file writes.

    ## Inputs

    - Architecture spec: `plan/architect-dispatch-plan-tooling.md` (section 4.3, section 5.1 for key naming)
    - Pattern reference: `plugins/development-harness/sam_schema/writers/yaml_writer.py`
    - Models from T01: `plugins/development-harness/dispatch_schema/core/models.py`

    ## Requirements

    1. Implement `write_dispatch_plan(plan: DispatchPlan, path: Path) -> Path` in `dispatch_schema/writers/yaml_writer.py`
    2. Serialize using `ruamel.yaml` round-trip mode
    3. Output YAML keys in kebab-case (e.g., `conflict-groups`, `depends-on`, `pre-merge`)
    4. Use `model_dump(by_alias=True)` or manual key transformation to produce kebab-case
    5. Write to a temp file in the same directory as target, then `os.rename()` atomically
    6. Create parent directories if they do not exist
    7. Return the path written to
    8. Validate target path does not follow symlinks (security: path traversal prevention per spec section 6)

    ## Constraints

    - Do NOT use PyYAML -- use `ruamel.yaml` only
    - Do NOT write to stdout or return YAML strings -- always write to file
    - Temp file must be in the same directory as target (required for atomic rename on same filesystem)

    ## Expected Outputs

    - `plugins/development-harness/dispatch_schema/writers/yaml_writer.py`

    ## Acceptance Criteria

    1. `write_dispatch_plan(plan, Path("/tmp/test.yaml"))` creates the file with kebab-case keys
    2. Written YAML contains `conflict-groups:` not `conflict_groups:`
    3. If `os.rename()` fails, no partial file remains at the target path
    4. Parent directories are created if missing

    ## Verification Steps

    1. `cd plugins/development-harness && uv run python -c "from dispatch_schema.writers.yaml_writer import write_dispatch_plan; print('importable')"`
    2. `uv run ruff check plugins/development-harness/dispatch_schema/writers/yaml_writer.py`
    3. Write a plan to a temp path and verify `conflict-groups` key appears in output YAML

  started: '2026-03-21T01:08:30.860215+00:00'
- task: T04
  title: Plan validator (integrity + stale detection)
  status: complete
  agent: python-cli-architect
  dependencies:
  - T01
  priority: 2
  complexity: high
  accuracy-risk: medium
  skills:
  - python3-development
  parallelize-with:
  - T02
  - T03
  - T06
  reason: Validator enforces plan correctness before work-milestone proceeds.
    High complexity due to five independent integrity checks.
  handoff: validate_plan_integrity() returns ValidationResult with
    errors/warnings. detect_stale_plan() returns StalePlanResult with
    added/removed issue lists.
  body: |
    ## Context

    Architecture spec section 4.4 defines both validation functions and their return dataclasses.
    Five integrity checks are specified. Stale detection compares plan issue numbers against a caller-provided list.

    ## Objective

    Implement `validate_plan_integrity()` and `detect_stale_plan()` with their result dataclasses.

    ## Inputs

    - Architecture spec: `plan/architect-dispatch-plan-tooling.md` (section 4.4)
    - Models from T01: `plugins/development-harness/dispatch_schema/core/models.py`

    ## Requirements

    ### validate_plan_integrity(plan: DispatchPlan) -> ValidationResult

    1. Define `ValidationResult` dataclass with `is_valid: bool`, `errors: list[str]`, `warnings: list[str]`
    2. Check 1: All `conflict_group` references in WaveItems point to existing ConflictGroup.group_id values
    3. Check 2: All `depends_on` issue numbers exist in some wave
    4. Check 3: Wave ordering consistency -- `depends_on` references only point to items in earlier waves
    5. Check 4: No item (by issue number) appears in multiple waves
    6. Check 5: Items in the same conflict group are never in the same wave with `parallel=True`
    7. Collect all errors; `is_valid = len(errors) == 0`

    ### detect_stale_plan(plan, current_issue_numbers) -> StalePlanResult

    8. Define `StalePlanResult` dataclass with `is_stale: bool`, `added_issues: list[int]`, `removed_issues: list[int]`, `message: str`
    9. Extract all issue numbers from all waves in the plan
    10. `added_issues` = in `current_issue_numbers` but not in plan
    11. `removed_issues` = in plan but not in `current_issue_numbers`
    12. `is_stale = bool(added_issues or removed_issues)`
    13. `message` describes what changed in human-readable form

    ## Constraints

    - Both functions are pure -- no file I/O, no GitHub calls
    - Use `@dataclass(frozen=True)` for result types (not Pydantic models)
    - Place both functions and dataclasses in `dispatch_schema/core/validator.py`

    ## Expected Outputs

    - `plugins/development-harness/dispatch_schema/core/validator.py`

    ## Acceptance Criteria

    1. `validate_plan_integrity()` returns `is_valid=False` when a WaveItem references a nonexistent conflict_group
    2. `validate_plan_integrity()` returns `is_valid=False` when depends_on references an item in a later wave
    3. `validate_plan_integrity()` returns `is_valid=False` when the same issue appears in two waves
    4. `detect_stale_plan()` returns `is_stale=True` with correct `added_issues` when new issues exist
    5. `detect_stale_plan()` returns `is_stale=False` when plan matches current issues exactly

    ## Verification Steps

    1. `cd plugins/development-harness && uv run python -c "from dispatch_schema.core.validator import validate_plan_integrity, detect_stale_plan, ValidationResult, StalePlanResult; print('OK')"`
    2. `uv run ruff check plugins/development-harness/dispatch_schema/core/validator.py`
    3. Construct a DispatchPlan in Python with a known integrity violation and verify validate_plan_integrity catches it

    ## CoVe Checks

    - Key claims to verify:
      - Check 5 (conflict group + parallel wave) correctly allows sequential items in same wave when parallel=False
      - Union of issue numbers across waves is the correct comparison set for stale detection
    - Verification questions:
      1. If wave.parallel=False and two items share a conflict group, should that be an error or allowed?
      2. Does the spec say parallel=True is the default for Wave? (Yes, per models.py)
    - Evidence to collect:
      - Re-read architect spec section 4.4 check descriptions
    - Revision rule:
      - If parallel=False waves should allow same-group items, add that exception to Check 5

  started: '2026-03-21T01:03:27.635204+00:00'
- task: T05
  title: Package public API (__init__.py exports)
  status: complete
  agent: python-cli-architect
  dependencies:
  - T01
  - T02
  - T03
  - T04
  priority: 3
  complexity: low
  accuracy-risk: low
  skills:
  - python3-development
  parallelize-with:
  - T06
  reason: Public API re-exports depend on all components being implemented. Low
    complexity -- just import aggregation.
  handoff: All public symbols importable from dispatch_schema top-level. __all__
    list matches architect spec section 4.6.
  body: |
    ## Context

    Architecture spec section 4.6 defines the exact `__init__.py` exports.
    All component modules (models, reader, writer, validator) must be complete before this task.

    ## Objective

    Replace the minimal `dispatch_schema/__init__.py` with the full public API re-exports.

    ## Inputs

    - Architecture spec: `plan/architect-dispatch-plan-tooling.md` (section 4.6)
    - Completed modules from T01-T04

    ## Requirements

    1. Import all public symbols from `core.models`, `core.validator`, `readers.yaml_reader`, `writers.yaml_writer`
    2. Define `__all__` list matching the spec exactly (14 symbols)
    3. Ensure import order follows: models, then validator types, then reader/writer functions

    ## Constraints

    - Do NOT add symbols beyond those in the architect spec section 4.6
    - Do NOT add version strings or metadata beyond what the spec requires

    ## Expected Outputs

    - `plugins/development-harness/dispatch_schema/__init__.py` (overwrite minimal version from T01)

    ## Acceptance Criteria

    1. `from dispatch_schema import DispatchPlan, read_dispatch_plan, write_dispatch_plan, validate_plan_integrity, detect_stale_plan` succeeds
    2. `dispatch_schema.__all__` contains exactly 14 symbols matching architect spec
    3. No import errors when importing the package

    ## Verification Steps

    1. `cd plugins/development-harness && uv run python -c "import dispatch_schema; print(len(dispatch_schema.__all__))"`
    2. `cd plugins/development-harness && uv run python -c "from dispatch_schema import *; print('OK')"`
    3. `uv run ruff check plugins/development-harness/dispatch_schema/__init__.py`

  started: '2026-03-21T01:09:40.849408+00:00'
- task: T06
  title: analyze_impact_radius_conflicts() in backlog_core/operations.py
  status: complete
  agent: python-cli-architect
  dependencies:
  - T01
  priority: 2
  complexity: high
  accuracy-risk: medium
  skills:
  - python3-development
  parallelize-with:
  - T02
  - T03
  - T04
  reason: High complexity due to union-find algorithm for transitive conflict
    merging. Depends on T01 for ConflictGroup model.
  handoff: Function accepts list[dict] with title/issue/impact_radius keys,
    returns list[ConflictGroup]. Union-find handles transitive overlap.
  body: |
    ## Context

    Architecture spec section 4.5 defines the function signature and behavior.
    ADR-002 mandates union-find for transitive conflict group merging.
    Section 5.4 defines Impact Radius parsing rules.
    This function is added to the existing `plugins/development-harness/backlog_core/operations.py`.

    ## Objective

    Implement `analyze_impact_radius_conflicts()` using union-find to compute conflict groups from Impact Radius file-path overlap.

    ## Inputs

    - Architecture spec: `plan/architect-dispatch-plan-tooling.md` (sections 4.5, 5.4, ADR-002)
    - Existing file: `plugins/development-harness/backlog_core/operations.py`
    - ConflictGroup model from T01: `plugins/development-harness/dispatch_schema/core/models.py`

    ## Requirements

    ### Impact Radius parsing (section 5.4)

    1. Split `impact_radius` string by newlines
    2. Strip leading whitespace, `-`, `*`, and trailing whitespace from each line
    3. Discard empty lines and lines that are pure markdown headers (`##`)
    4. Remaining strings are file paths

    ### Conflict detection

    5. Two items conflict if they share any parsed file path (exact string match, ADR-004)
    6. Items with no impact_radius or empty impact_radius are excluded from conflict analysis

    ### Union-find merging (ADR-002)

    7. Implement union-find (disjoint set) to merge transitively overlapping items
    8. If A overlaps B and B overlaps C, all three form one group even if A and C share no paths
    9. Assign sequential `group_id` values starting from 1

    ### Output

    10. Return `list[ConflictGroup]` where each group has `group_id`, `reason` (shared file paths), and `items` (list of item titles)
    11. Return empty list if no conflicts found

    ## Constraints

    - Function is pure computation -- no GitHub API calls, no file I/O
    - Input is `list[dict[str, object]]` with keys: `title` (str), `issue` (int), `impact_radius` (str)
    - Add the function to existing `backlog_core/operations.py` -- do not create a new file
    - Import `ConflictGroup` from `dispatch_schema.core.models`

    ## Expected Outputs

    - `plugins/development-harness/backlog_core/operations.py` (modified -- add function + import)

    ## Acceptance Criteria

    1. Items A and B sharing file path "x.py" produce one ConflictGroup with both titles
    2. Transitive overlap (A-B share "x.py", B-C share "y.py") produces one group with A, B, C
    3. Items with empty `impact_radius` appear in no conflict group
    4. Markdown bullet markers (`- path/to/file.py`) are correctly stripped
    5. `group_id` values are sequential starting from 1

    ## Verification Steps

    1. `cd plugins/development-harness && uv run python -c "from backlog_core.operations import analyze_impact_radius_conflicts; print('importable')"`
    2. `uv run ruff check plugins/development-harness/backlog_core/operations.py`
    3. Run a quick inline test: 3 items with transitive overlap produce 1 group

    ## CoVe Checks

    - Key claims to verify:
      - Union-find path compression and union-by-rank produce correct transitive closure
      - Impact Radius parsing correctly handles `- ` prefix, `* ` prefix, and bare paths
    - Verification questions:
      1. Does the union-find implementation handle the case where an item overlaps with multiple existing groups (merging them)?
      2. Do markdown header lines (`## Impact Radius`) get correctly discarded?
    - Evidence to collect:
      - Test with 4+ items forming 2 separate groups to verify no cross-contamination
    - Revision rule:
      - If union-find produces incorrect groups, add explicit path compression

  started: '2026-03-21T01:07:06.828033+00:00'
- task: T07
  title: 'Tests: models, reader, writer (unit + integration)'
  status: complete
  agent: python-pytest-architect
  dependencies:
  - T01
  - T02
  - T03
  - T05
  priority: 3
  complexity: high
  accuracy-risk: low
  skills:
  - fastmcp-python-tests
  - python3-development
  parallelize-with:
  - T08
  reason: Tests validate the I/O pipeline. High complexity due to fixture
    creation, round-trip tests, and error path coverage.
  handoff: Test suite covers model validation, reader error paths, writer
    kebab-case output, and round-trip integrity. All tests pass.
  body: |
    ## Context

    Architecture spec section 7 defines the test structure, categories, and coverage requirements.
    Tests go in `plugins/development-harness/tests/test_dispatch_schema/`.
    Fixture YAML files go in `tests/test_dispatch_schema/fixtures/`.

    ## Objective

    Create comprehensive tests for Pydantic models, YAML reader, and YAML writer including round-trip integration tests.

    ## Inputs

    - Architecture spec: `plan/architect-dispatch-plan-tooling.md` (section 7)
    - Implementation from T01-T03, T05
    - Pattern reference: existing tests in `plugins/development-harness/tests/`

    ## Requirements

    ### Test infrastructure

    1. Create `tests/test_dispatch_schema/__init__.py`
    2. Create `tests/test_dispatch_schema/conftest.py` with shared fixtures (sample DispatchPlan, tmp_path usage)
    3. Create `tests/test_dispatch_schema/fixtures/valid-plan.yaml` (known-good dispatch plan)
    4. Create `tests/test_dispatch_schema/fixtures/invalid-plan-bad-ref.yaml` (ConflictGroup ref to nonexistent group)

    ### test_models.py (unit)

    5. Test valid construction of each model class
    6. Test field alias acceptance (kebab-case dict input)
    7. Test enum coercion for ItemPriority and ItemStatus
    8. Test validation errors: missing required fields, constraint violations (min_length, ge)
    9. Test default values: WaveItem.conflict_group=None, WaveItem.depends_on=[], WaveItem.status=PENDING

    ### test_yaml_reader.py (unit + integration)

    10. Test reading valid-plan.yaml fixture returns DispatchPlan
    11. Test FileNotFoundError on missing file
    12. Test ValueError on malformed YAML
    13. Test ValueError on schema-violating YAML (missing required fields)

    ### test_yaml_writer.py (unit + integration)

    14. Test writer produces kebab-case keys in output
    15. Test atomic write: verify no partial file on simulated os.rename failure (mock)
    16. Test round-trip: write then read produces equal model
    17. Test parent directory creation

    ## Constraints

    - Use `pytest.mark.unit` and `pytest.mark.integration` markers per spec
    - Use `tmp_path` fixture for all file I/O tests -- no writing to real directories
    - Do NOT test validator or impact radius here -- those are T08

    ## Expected Outputs

    - `plugins/development-harness/tests/test_dispatch_schema/__init__.py`
    - `plugins/development-harness/tests/test_dispatch_schema/conftest.py`
    - `plugins/development-harness/tests/test_dispatch_schema/fixtures/valid-plan.yaml`
    - `plugins/development-harness/tests/test_dispatch_schema/fixtures/invalid-plan-bad-ref.yaml`
    - `plugins/development-harness/tests/test_dispatch_schema/test_models.py`
    - `plugins/development-harness/tests/test_dispatch_schema/test_yaml_reader.py`
    - `plugins/development-harness/tests/test_dispatch_schema/test_yaml_writer.py`

    ## Acceptance Criteria

    1. `uv run pytest tests/test_dispatch_schema/test_models.py -v` passes with 10+ test cases
    2. `uv run pytest tests/test_dispatch_schema/test_yaml_reader.py -v` passes with 4+ test cases
    3. `uv run pytest tests/test_dispatch_schema/test_yaml_writer.py -v` passes with 4+ test cases
    4. Round-trip test proves write-then-read produces identical DispatchPlan

    ## Verification Steps

    1. `cd plugins/development-harness && uv run pytest tests/test_dispatch_schema/ -v --tb=short`
    2. `cd plugins/development-harness && uv run pytest tests/test_dispatch_schema/ --cov=dispatch_schema --cov-report=term-missing`
    3. Verify fixture YAML files are parseable: `uv run python -c "from dispatch_schema import read_dispatch_plan; from pathlib import Path; read_dispatch_plan(Path('tests/test_dispatch_schema/fixtures/valid-plan.yaml'))"`

  started: '2026-03-21T01:12:39.567790+00:00'
- task: T08
  title: 'Tests: validator, stale detection, impact radius conflicts'
  status: complete
  agent: python-pytest-architect
  dependencies:
  - T04
  - T05
  - T06
  priority: 3
  complexity: high
  accuracy-risk: low
  skills:
  - fastmcp-python-tests
  - python3-development
  parallelize-with:
  - T07
  reason: Validator and conflict analysis are the highest-risk components. 95%+
    coverage required. Property-based testing for union-find.
  handoff: Test suite covers all five validator integrity checks, stale
    detection, and conflict analysis with property-based tests. All pass.
  body: |
    ## Context

    Architecture spec section 7 requires 95%+ coverage on validator and conflict analysis.
    Property-based testing with `hypothesis` is specified for `analyze_impact_radius_conflicts()`.
    Stale plan fixture: `tests/test_dispatch_schema/fixtures/stale-plan.yaml`.

    ## Objective

    Create tests for plan validation, stale detection, and impact radius conflict analysis, including property-based tests.

    ## Inputs

    - Architecture spec: `plan/architect-dispatch-plan-tooling.md` (section 7)
    - Implementation from T04 (validator), T06 (conflict analysis)
    - Fixtures from T07 conftest.py (shared DispatchPlan builders)

    ## Requirements

    ### test_validator.py

    1. Test each of the five integrity checks independently with a plan that violates exactly one rule
    2. Test a plan that passes all checks returns `is_valid=True`
    3. Test that warnings are collected separately from errors
    4. Create `fixtures/stale-plan.yaml` for stale detection tests
    5. Test `detect_stale_plan()`: added issues, removed issues, unchanged (not stale), both added and removed

    ### test_impact_radius.py (in tests/test_backlog_core/)

    6. Create `tests/test_backlog_core/__init__.py` if not exists
    7. Create `tests/test_backlog_core/test_impact_radius.py`
    8. Test basic pairwise overlap: 2 items sharing a file path
    9. Test transitive merging: A-B and B-C overlap -> one group
    10. Test no overlap: items with disjoint paths -> empty list
    11. Test empty impact_radius: items excluded from analysis
    12. Test markdown parsing: bullet markers stripped, headers discarded
    13. Property-based test with hypothesis: random item sets verify group invariants (every group has 2+ items, every pair shares a path, no item in multiple groups)

    ## Constraints

    - Use `pytest.mark.critical` for property-based tests per spec
    - Add `hypothesis` as a test dependency if not already present
    - Use `pytest.mark.unit` for deterministic tests
    - 95%+ coverage target on `core/validator.py` and `analyze_impact_radius_conflicts`

    ## Expected Outputs

    - `plugins/development-harness/tests/test_dispatch_schema/fixtures/stale-plan.yaml`
    - `plugins/development-harness/tests/test_dispatch_schema/test_validator.py`
    - `plugins/development-harness/tests/test_backlog_core/__init__.py` (if not exists)
    - `plugins/development-harness/tests/test_backlog_core/test_impact_radius.py`

    ## Acceptance Criteria

    1. `uv run pytest tests/test_dispatch_schema/test_validator.py -v` passes with 8+ test cases
    2. `uv run pytest tests/test_backlog_core/test_impact_radius.py -v` passes with 7+ test cases
    3. Property-based test runs 100+ examples without failure
    4. Coverage on `core/validator.py` is 95%+ (check via `--cov` report)

    ## Verification Steps

    1. `cd plugins/development-harness && uv run pytest tests/test_dispatch_schema/test_validator.py tests/test_backlog_core/test_impact_radius.py -v --tb=short`
    2. `cd plugins/development-harness && uv run pytest tests/test_dispatch_schema/test_validator.py --cov=dispatch_schema.core.validator --cov-report=term-missing`
    3. `cd plugins/development-harness && uv run pytest tests/test_backlog_core/test_impact_radius.py -v -k critical` to run property-based tests specifically

  started: '2026-03-21T01:12:19.201240+00:00'
- task: T09
  title: MCP tools on backlog server
  status: complete
  agent: python-cli-architect
  dependencies:
  - T05
  - T06
  priority: 4
  complexity: medium
  accuracy-risk: medium
  skills:
  - python3-development
  - fastmcp-python-tests
  parallelize-with: []
  reason: MCP tools are the consumer-facing API. Depends on complete
    dispatch_schema package and conflict analysis function.
  handoff: 'Four tools registered on backlog MCP server: dispatch_read, dispatch_validate,
    dispatch_stale_check, dispatch_conflicts. Each returns a dict.'
  body: |-
    ## Context

    Architecture spec section 11 defines four candidate MCP tools for the backlog server.
    The backlog server is a FastMCP v3 server at `plugins/development-harness/run_backlog_server.py`.
    Tools import from `dispatch_schema` (pure file ops) and `backlog_core.operations` (conflict analysis).
    `dispatch_stale_check` and `dispatch_conflicts` need GitHub data fetched via existing backlog_core operations.

    ## Objective

    Register four dispatch plan MCP tools on the existing backlog MCP server.

    ## Inputs

    - Architecture spec: `plan/architect-dispatch-plan-tooling.md` (section 11)
    - Backlog server: `plugins/development-harness/run_backlog_server.py`
    - dispatch_schema package (T05): `plugins/development-harness/dispatch_schema/`
    - Conflict analysis (T06): `plugins/development-harness/backlog_core/operations.py`

    ## Requirements

    1. Add `dispatch_read(milestone_number: int) -> dict` tool: reads `plan/milestone-{N}-dispatch.yaml`, returns plan as dict or error dict
    2. Add `dispatch_validate(milestone_number: int) -> dict` tool: reads plan, runs `validate_plan_integrity()`, returns `{"is_valid": bool, "errors": [...], "warnings": [...]}`
    3. Add `dispatch_stale_check(milestone_number: int) -> dict` tool: reads plan, fetches current milestone issues via existing backlog operations, runs `detect_stale_plan()`, returns stale/fresh result
    4. Add `dispatch_conflicts(milestone_number: int) -> dict` tool: fetches groomed items from milestone, runs `analyze_impact_radius_conflicts()`, returns conflict groups as list of dicts
    5. All tools use `@server.tool()` decorator pattern consistent with existing tools
    6. Error handling: return `{"error": "message"}` dict on failure, do not raise exceptions from tools
    7. Plan file path convention: `plan/milestone-{milestone_number}-dispatch.yaml`

    ## Constraints

    - Do NOT create a new MCP server -- add tools to existing backlog server
    - Do NOT modify the dispatch_schema library code -- only add MCP wrapper functions
    - `dispatch_stale_check` and `dispatch_conflicts` may call existing backlog_core GitHub operations for data fetching
    - Tool return types must be `dict` (FastMCP serializes to JSON)

    ## Expected Outputs

    - `plugins/development-harness/run_backlog_server.py` (modified -- add 4 tool functions + imports)

    ## Acceptance Criteria

    1. All four tools are registered and appear in server tool listing
    2. `dispatch_read` returns plan dict for existing valid plan file
    3. `dispatch_read` returns error dict for nonexistent milestone
    4. `dispatch_validate` returns `{"is_valid": true, ...}` for a valid plan

    ## Verification Steps

    1. `uv run ruff check plugins/development-harness/run_backlog_server.py`
    2. `cd plugins/development-harness && uv run python -c "from run_backlog_server import *; print('importable')"`
    3. Grep for all four tool names in run_backlog_server.py to confirm registration

    ## CoVe Checks

    - Key claims to verify:
      - FastMCP v3 `@server.tool()` decorator registers tools with the given function name
      - Existing backlog server uses the same decorator pattern for current tools
    - Verification questions:
      1. Does the backlog server use `mcp = FastMCP(...)` or `server = Server(...)` initialization?
      2. Are existing tools defined as `@mcp.tool()` or `@server.tool()`?
    - Evidence to collect:
      - Read first 30 lines of run_backlog_server.py to confirm server variable name and decorator pattern
    - Revision rule:
      - Match exact decorator pattern used by existing tools in the file
  started: '2026-03-21T01:13:22.175711+00:00'

---

## Context Manifest

Generated by context-gathering agent on 2026-03-20

### How This Currently Works: Dispatch Plan Tooling

The dispatch plan tooling implementation is a library-only Python module that provides structured I/O, validation, and conflict analysis for milestone dispatch plan YAML files. It mirrors the established `sam_schema/` architecture pattern already proven in the codebase.

**The Architecture**:
When `/groom-milestone` or `/work-milestone` skills need to read or write dispatch plans, they import from `dispatch_schema` (the new module). The module provides five core functions:

1. `read_dispatch_plan(path)` — uses `ruamel.yaml` to load a YAML file into a validated Pydantic `DispatchPlan` model
2. `write_dispatch_plan(plan, path)` — serializes a `DispatchPlan` back to YAML with kebab-case keys using atomic temp+rename
3. `validate_plan_integrity(plan)` — checks five structural correctness rules (conflict group refs, wave ordering, no duplicates, parallel constraints)
4. `detect_stale_plan(plan, current_issues)` — compares plan issue numbers against current milestone state to detect drift
5. `analyze_impact_radius_conflicts(items)` — uses union-find to compute transitive file-path overlap between groomed backlog items

**Data Models**:
The Pydantic models (`core/models.py`) define:
- `ItemPriority` and `ItemStatus` — string enums for priority levels and workflow states
- `MilestoneHeader` — top-level milestone ID and integration branch
- `ConflictGroup` — a set of items whose Impact Radii (file paths) overlap
- `WaveItem` — an individual backlog item reference with optional conflict group, dependencies, and status
- `Wave` — a batch of items dispatched sequentially or in parallel (with constraint that parallel waves cannot include items sharing a conflict group)
- `QualityGates` — pre-merge and post-merge gate checks to run
- `DispatchPlan` — the root model containing milestone header, conflict groups, waves, and gates

**The I/O Pipeline**:
1. Reader (`yaml_reader.py`): File → ruamel.yaml dict → Pydantic validation → DispatchPlan object
2. Writer (`yaml_writer.py`): DispatchPlan object → model_dump(by_alias=True) → ruamel.yaml → atomic temp file → os.rename()
3. Validator (`validator.py`): DispatchPlan object → run five checks → ValidationResult with errors/warnings list
4. Stale detection: DispatchPlan + list[int] of current issues → compare → StalePlanResult with added/removed lists
5. Conflict analysis: list[dict] with title/issue/impact_radius → parse file paths → union-find merge → list[ConflictGroup]

**Pattern Fidelity**:
The dispatch_schema module closely mirrors `sam_schema/` to maintain consistency:
- Same `ruamel.yaml` for I/O (round-trip mode to preserve formatting)
- Same atomic write pattern (tempfile + os.rename in same directory)
- Same Pydantic v2 configuration (`ConfigDict(populate_by_name=True, use_enum_values=True)`)
- Same `StrEnum` usage for status/priority types
- Same relative import structure: core/ for models and validators, readers/ for I/O, writers/ for serialization

**Integration Points**:
- `dispatch_schema` is a pure library (no CLI entry points)
- The module is consumed by `/groom-milestone` and `/work-milestone` skills (not yet implemented)
- `backlog_core/operations.py` gains a new function `analyze_impact_radius_conflicts()` that depends on `ConflictGroup` from dispatch_schema
- The backlog MCP server (`run_backlog_server.py`) registers four tools that wrap the dispatch_schema functions and expose them as MCP tools

**Error Handling**:
- Reader raises `FileNotFoundError` if path doesn't exist, `ValueError` if YAML is malformed or Pydantic validation fails
- Validator and stale detection return result dataclasses with `is_valid` and `is_stale` booleans — they do not raise, they report
- Conflict analysis is pure computation with no I/O — returns empty list if no conflicts

### For New Feature Implementation: What Needs to Connect

**Module Structure** — Create under `plugins/development-harness/`:

```text
dispatch_schema/
  __init__.py (re-exports public API)
  core/
    __init__.py (empty)
    models.py (8 Pydantic models + 2 StrEnum classes)
    validator.py (2 functions + 2 frozen dataclasses for results)
  readers/
    __init__.py (empty)
    yaml_reader.py (1 function)
  writers/
    __init__.py (empty)
    yaml_writer.py (1 function)
```

**Integration with backlog_core**:
- File: `plugins/development-harness/backlog_core/operations.py`
- Add: `analyze_impact_radius_conflicts(items: list[dict[str, object]]) -> list[ConflictGroup]`
- Import: `from dispatch_schema.core.models import ConflictGroup`
- No other modifications to existing functions in operations.py

**Testing Structure**:

```text
tests/
  test_dispatch_schema/
    __init__.py
    conftest.py (shared fixtures: DispatchPlan builder, sample data)
    fixtures/
      valid-plan.yaml
      invalid-plan-bad-ref.yaml
      stale-plan.yaml
    test_models.py (unit tests for Pydantic models)
    test_yaml_reader.py (reader error paths, fixture loading)
    test_yaml_writer.py (kebab-case output, round-trip, atomic write)
    test_validator.py (all five integrity checks + stale detection)
  test_backlog_core/
    __init__.py
    test_impact_radius.py (conflict analysis, union-find, property-based)
```

**MCP Tool Registration**:
- File: `plugins/development-harness/run_backlog_server.py`
- Add four `@server.tool()` decorated functions wrapping dispatch_schema operations
- No new MCP server — augment existing backlog server

### Technical Reference Details

**File Locations** (all under `plugins/development-harness/`):

**READ-ONLY REFERENCES** (agents read to understand patterns):
- `sam_schema/core/models.py` — reference for Pydantic field alias patterns
- `sam_schema/readers/yaml_reader.py` — reference for ruamel.yaml usage
- `sam_schema/writers/yaml_writer.py` — reference for atomic write pattern
- `plan/architect-dispatch-plan-tooling.md` — complete specification for models, validation, tool interfaces
- `plan/feature-context-dispatch-plan-tooling.md` — feature intent, existing codebase patterns
- `.claude/rules/yaml-toml-libraries.md` — ruamel.yaml usage standards
- `backlog_core/operations.py` — existing module where `analyze_impact_radius_conflicts()` is added

**CREATE NEW FILES**:
- `dispatch_schema/__init__.py` (minimal initially, full public API in T05)
- `dispatch_schema/core/__init__.py` (empty)
- `dispatch_schema/core/models.py` (8 Pydantic models, 2 StrEnum enums)
- `dispatch_schema/core/validator.py` (2 functions, 2 frozen dataclasses)
- `dispatch_schema/readers/__init__.py` (empty)
- `dispatch_schema/readers/yaml_reader.py` (1 function)
- `dispatch_schema/writers/__init__.py` (empty)
- `dispatch_schema/writers/yaml_writer.py` (1 function)
- `tests/test_dispatch_schema/__init__.py`
- `tests/test_dispatch_schema/conftest.py`
- `tests/test_dispatch_schema/fixtures/valid-plan.yaml`
- `tests/test_dispatch_schema/fixtures/invalid-plan-bad-ref.yaml`
- `tests/test_dispatch_schema/fixtures/stale-plan.yaml`
- `tests/test_dispatch_schema/test_models.py`
- `tests/test_dispatch_schema/test_yaml_reader.py`
- `tests/test_dispatch_schema/test_yaml_writer.py`
- `tests/test_dispatch_schema/test_validator.py`
- `tests/test_backlog_core/__init__.py` (if not exists)
- `tests/test_backlog_core/test_impact_radius.py`

**MODIFY EXISTING FILES**:
- `backlog_core/operations.py` — add `analyze_impact_radius_conflicts()` function + import `ConflictGroup`
- `run_backlog_server.py` — register four MCP tools + imports from dispatch_schema

**Key Function Signatures**:

```python
# readers/yaml_reader.py
def read_dispatch_plan(path: Path) -> DispatchPlan: ...

# writers/yaml_writer.py
def write_dispatch_plan(plan: DispatchPlan, path: Path) -> Path: ...

# core/validator.py
def validate_plan_integrity(plan: DispatchPlan) -> ValidationResult: ...
def detect_stale_plan(plan: DispatchPlan, current_issue_numbers: list[int]) -> StalePlanResult: ...

# backlog_core/operations.py
def analyze_impact_radius_conflicts(items: list[dict[str, object]]) -> list[ConflictGroup]: ...
```

**Data Model Fields** (summary from architect spec section 4.1):
- `DispatchPlan`: milestone_header, conflict_groups, waves, quality_gates
- `Wave`: items, wave_id, description, parallel (default True)
- `WaveItem`: issue, title, conflict_group (optional), depends_on (list), status (default PENDING)
- `ConflictGroup`: group_id, reason, items (list, min 2)
- `MilestoneHeader`: number, title, integration_branch
- `QualityGates`: pre_merge (list), post_merge (list)

**Constraints and Patterns**:
- All kebab-case YAML keys use `AliasChoices()` to accept both kebab and snake_case in Python
- Enums use `StrEnum` from stdlib enum module (Python 3.11+)
- All models use `ConfigDict(populate_by_name=True, use_enum_values=True)`
- Writers use atomic rename pattern: write to `.tmp` file in same directory, then `os.rename()` to target
- No file operations inside validator or conflict analysis functions — pure computation only
- Union-find algorithm for transitive conflict merging (per ADR-002)
- Impact Radius parsing strips markdown bullets (`- `, `* `), blank lines, and header markers
