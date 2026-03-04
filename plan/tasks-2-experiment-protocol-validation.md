# Task Plan: Experiment Protocol Validation

**Feature:** Experiment protocol validation gaps (Issue #431)
**Architecture spec:** `plan/architect-experiment-protocol-validation.md`
**Package:** `plugins/scientific-method/mcp/experiment-registry/`
**Total tasks:** 6
**Fixes:** #431

---

## Context Manifest

### How the Experiment Registry MCP Server Currently Works

When an AI agent runs a controlled experiment, it interacts with the experiment-registry MCP server through FastMCP tools defined in `server.py`. The server manages a 5-step experiment protocol: hypothesis, fixture, rubric, baseline, iterate. The entire lifecycle is driven by calls to `complete_step()`, which is the sole state-mutation entry point for advancing experiments.

**Request flow through complete_step.** The MCP client calls the `complete_step` tool in `server.py` (line 258), passing `experiment_id`, `step_id`, and `artefacts: dict[str, str]`. The tool creates a fresh `StateManager` via `_make_state_manager(project_root)` (line 290) and delegates to `StateManager.complete_step()` (line 292). Any `ValueError` raised by the state manager is caught and re-raised as `ToolError` (line 293-294).

**State manager complete_step flow (state_manager.py:173-271).** The method:

1. Loads the experiment state from `{project_root}/.claude/experiments/{id}/state.json` via `load_experiment()` (line 194). State is deserialized as `ExperimentState(**raw_json)`.
2. Validates that `step_id` matches `state.current_step` (line 197-202). Mismatch raises `ValueError`.
3. Finds the `StepDefinition` by linear scan of `state.merged_steps` (lines 205-213).
4. Checks required artefacts via key presence only (line 216): `missing = [a for a in current_def.required_artefacts if a not in artefacts]`. This is the validation gap -- values are never inspected. An empty string `""` passes.
5. If missing artefacts exist and `human_input_required` is true, returns `{"success": False, "blocked_on_human_input": True, ...}`. Otherwise returns `{"success": False, "missing_artefacts": missing}`. No state mutation occurs on either failure path.
6. Merges artefacts unconditionally at line 229: `state.artefacts.update(artefacts)`. This overwrites any previously stored value for the same key with no freeze check.
7. For the `iterate` step (lines 236-257): increments `iteration_count`, reads `criteria_passed` as `artefacts.get("criteria_passed", "").lower() == "true"` (line 238) -- a trust-based string self-report. If criteria passed, sets status to `"complete"`. If iteration count exceeds max, sets `"inconclusive"`. Otherwise loops back.
8. For non-iterate steps (lines 259-270): appends step to `completed_steps`, advances `current_step` to the next in sequence, saves state.

**The validation field is decorative.** Each step in `experiment_core.json` has a `validation` string field (e.g., `"contains HYPOTHESIS:, CURRENT BEHAVIOUR:, SUCCESS CRITERION:"` for the hypothesis step). This field is stored in `StepDefinition.validation` (models.py line 20) and returned to callers via `get_current_step` and `inspect_experiment_type`, but no code ever evaluates it. The MCP relies on the AI caller to self-enforce these rules.

**State persistence.** `StateManager._save()` (line 56-64) writes state as `state.model_dump_json(indent=2)` to `{experiments_dir}/{id}/state.json`. The `_state_path()` method (line 45-54) returns the full path to `state.json`, so `_state_path(id).parent` is the experiment directory where artefact files live.

**Registry loader 3-layer merge.** `RegistryLoader.merge_type()` (registry_loader.py:152-195) always starts from `experiment_core` steps, applies domain type `step_extensions` if the base is not `experiment_core`, then applies inline extensions. The `_apply_extension()` method (lines 83-119) appends `additional_artefacts` to `required_artefacts`, appends `checklist` items, and optionally overrides `human_input_required`/`human_input_description`. Critically, the `validation` field is not merged -- it is always inherited from the core step unchanged. The `_apply_extension` method constructs a new `StepDefinition` passing only the existing fields; it does not currently handle `validation_rules` or `frozen_artefacts` since those fields do not exist yet.

**Pydantic models (models.py).** All models use `from __future__ import annotations` and inherit from `pydantic.BaseModel`. Key models:

- `StepDefinition` (line 14): `id`, `name`, `required_artefacts: list[str]`, `validation: str = ""`, `checklist: list[str]`, `human_input_required: bool`, `human_input_description: str`. All list/dict fields use `Field(default_factory=...)`.
- `StepExtension` (line 37): `additional_artefacts: list[str]`, `checklist: list[str]`, `human_input_required: bool | None = None`, `human_input_description: str`.
- `ExperimentState` (line 58): `id`, `base`, `extensions: list[str]` (unused), `inline_extensions`, `merged_steps: list[StepDefinition]`, `current_step: str`, `completed_steps: list[str]`, `artefacts: dict[str, str]`, `context: str`, `iteration_count: int = 0`, `max_iterations: int = 10`, `status: str = "in_progress"`, `created`, `last_updated`.
- `RubricTemplate` (line 26): `name`, `observable`, `pass_: str = Field(alias="pass")`, `fail`. Uses `model_config = {"populate_by_name": True}`.
- `ExperimentType` (line 46): `name`, `description`, `extends: str | None`, `steps`, `step_extensions`, `rubric_templates`, `anti_patterns`.

**experiment_core.json structure.** Five steps in fixed order. Each step has `id`, `name`, `required_artefacts`, `validation` (decorative string), `checklist`, `human_input_required`. The iterate step's `required_artefacts` is `["log.md"]` only -- baseline requires `["output-iter0.md", "log.md"]` but iterate does not require per-iteration output files. The `rubric_templates` array at the type level is empty for the core type but populated in domain types like `ai_agent_testing.json`.

**SKILL.md Phase 2 flowchart (experiment-protocol/SKILL.md lines 49-64).** The current flowchart goes: `GetStep` -> `StepDetail` -> `Human` decision -> `Produce`/`Surface` -> `Complete` -> `MCPResult` decision (missing artefacts / next step / complete / inconclusive). There is no terminal-state check before entering the loop and no validation-error handling branch from `MCPResult`.

**pyproject.toml.** The package at `plugins/scientific-method/mcp/experiment-registry/pyproject.toml` declares `requires-python = ">=3.12"` with dependencies `fastmcp>=3.0.0` and `pydantic>=2.0`. No test dependencies exist. No `[dependency-groups]` section exists. The build system is hatchling.

### What This Feature Changes: Validation Layer Implementation

This feature adds a validation layer between the artefact-merge step and the state-persistence step in `StateManager.complete_step()`. The layer is a new module `validators.py` containing composable pure-function validators driven by machine-readable rules in `experiment_core.json`.

**New models in models.py (T1).** Two new Pydantic models: `ValidationRule` with `type: Literal["required_sections", "non_empty", "no_forbidden_content", "min_criteria_count"]` and `params: dict[str, Any]`; `ArtefactIntegrity` with `sha256: str`, `frozen_at: str`, `frozen_by_step: str`. Three existing models gain new fields: `StepDefinition` gets `validation_rules: list[ValidationRule]` and `frozen_artefacts: list[str]`; `ExperimentState` gets `artefact_integrity: dict[str, ArtefactIntegrity]`; `StepExtension` gets `additional_validation_rules: list[ValidationRule]` and `additional_frozen_artefacts: list[str]`. All new fields use `Field(default_factory=...)` for backward compatibility -- existing state files with missing fields deserialize correctly with Pydantic filling defaults.

**New validators.py module (T2).** Six public pure functions returning `list[dict]` (empty = no errors): `validate_terminal_state`, `validate_file_existence`, `validate_artefact_content`, `validate_freeze_integrity`, `validate_iteration_output`, `validate_rubric_scores`. A `_RULE_EVALUATORS` dict maps `ValidationRule.type` strings to evaluator callables. Each evaluator takes `(content: str, params: dict)` and returns `str | None` (None = pass, string = error message). Nine error code constants: `EMPTY_ARTEFACT`, `FILE_NOT_FOUND`, `FROZEN_ARTEFACT_MODIFIED`, `MISSING_RUBRIC_SCORES`, `INCOMPLETE_RUBRIC_SCORES`, `UNKNOWN_RUBRIC_CRITERIA`, `CONTENT_VALIDATION_FAILED`, `MISSING_ITERATION_OUTPUT`, `TERMINAL_STATE`. Artefact values are treated as file paths per architecture decision D1 -- the validators read file content from disk via `Path.read_text()`.

**JSON schema changes in experiment_core.json (T3).** Each of the 5 steps gains `validation_rules` (array of rule objects) and `frozen_artefacts` (array of artefact key strings). The existing `validation` string field is preserved alongside for backward compatibility. fixture step freezes `["fixture.md"]`, rubric step freezes `["rubric.md"]`, all others freeze `[]`.

**Integration into state_manager.py and server.py (T4).** Two insertion points in `complete_step()`: (1) Pre-merge validation block after the required-artefacts check, calling all 6 validators and returning `{"success": False, "validation_errors": [...]}` if any fail -- no state mutation on failure. (2) Post-merge hash computation for frozen artefacts using `hashlib.sha256(path.read_bytes()).hexdigest()` stored in `state.artefact_integrity`. The `complete_step` MCP tool gains `rubric_scores: dict[str, bool] | None = None` parameter. The iterate step replaces `criteria_passed` string self-report with `all(rubric_scores.values())`. The `_apply_extension` method in `registry_loader.py` gains merge logic for `additional_validation_rules` and `additional_frozen_artefacts`.

**SKILL.md flowchart update (T5).** The Phase 2 flowchart gains: (1) `TermCheck` decision node between `GetStep` and `StepDetail` checking for terminal state; (2) `FixV` branch from `MCPResult` for validation errors; (3) `Handoff` terminal node for already-completed experiments.

**Test suite creation (T6).** New `tests/` directory with `conftest.py`, `test_validators.py`, `test_state_manager.py`, `test_complete_step_integration.py`. Adds `pytest>=8.0.0`, `pytest-cov>=6.0.0`, `pytest-mock>=3.14.0` as dev dependencies to `pyproject.toml`. Coverage targets: 80% overall, 95% for `validators.py`.

### Technical Reference Details

#### Key Source Files

| File | Path | Role in Feature |
|------|------|-----------------|
| models.py | `plugins/scientific-method/mcp/experiment-registry/models.py` | T1 adds ValidationRule, ArtefactIntegrity, extends StepDefinition/ExperimentState/StepExtension |
| validators.py | `plugins/scientific-method/mcp/experiment-registry/validators.py` | T2 creates this new file with 6 validator functions |
| experiment_core.json | `plugins/scientific-method/mcp/experiment-registry/registry/experiment_core.json` | T3 adds validation_rules and frozen_artefacts to all 5 steps |
| state_manager.py | `plugins/scientific-method/mcp/experiment-registry/state_manager.py` | T4 wires validators into complete_step, adds hash computation |
| server.py | `plugins/scientific-method/mcp/experiment-registry/server.py` | T4 adds rubric_scores parameter to complete_step tool |
| registry_loader.py | `plugins/scientific-method/mcp/experiment-registry/registry_loader.py` | T4 extends _apply_extension for new StepExtension fields |
| SKILL.md | `plugins/scientific-method/skills/experiment-protocol/SKILL.md` | T5 updates Phase 2 flowchart |
| pyproject.toml | `plugins/scientific-method/mcp/experiment-registry/pyproject.toml` | T6 adds pytest dev dependencies |

#### Architecture Spec Location

`plan/architect-experiment-protocol-validation.md` -- contains design decisions D1-D5, component architecture, validation rule engine spec, gap-by-gap design, data model changes, JSON schema changes, backward compatibility analysis, testing architecture, and acceptance criteria mapping.

#### Feature Context Location

`plan/feature-context-experiment-protocol-validation.md` -- contains original request, core intent analysis, codebase research with line-number references, use scenarios, gap analysis (8 gaps), and 5 open questions (Q1-Q5) resolved by the architecture spec.

#### Codebase Analysis Location

`plan/codebase/ARCHITECTURE.md` -- contains module overview, layer dependencies, complete complete_step flow with line numbers, server.py tool inventory, models.py field definitions, experiment_core.json step table, registry loader 3-layer merge documentation, SKILL.md flowchart analysis, and guidance on where to add new code.

#### Critical Implementation Details for Each Task

**T1 (models.py):** Must add `from typing import Any, Literal` -- check existing imports first (currently has `from __future__ import annotations`, `import datetime`, `from pydantic import BaseModel, Field`). New classes `ValidationRule` and `ArtefactIntegrity` must be defined before `StepDefinition` and `ExperimentState` respectively since those reference them. The `from __future__ import annotations` import means forward references work, but defining in dependency order is still best practice for readability.

**T2 (validators.py):** Imports restricted to `pathlib`, `hashlib`, `re`, `typing`, and local `models`. No imports from `state_manager` or `server` to avoid circular dependencies. The `validate_rubric_scores` function needs to handle two paths for criterion discovery: (a) structured `rubric_templates` from merged steps, or (b) parsing `rubric.md` for criterion names when no templates exist.

**T3 (experiment_core.json):** The exact JSON for each step's new fields is specified verbatim in the architecture spec "JSON Schema Changes" section. After editing, verify the file loads correctly via `RegistryLoader` since the loader constructs `StepDefinition(**s)` for each step dict -- the new fields must be accepted by the post-T1 model.

**T4 (state_manager.py):** The experiment directory for artefact file resolution is `self._state_path(experiment_id).parent`, which resolves to `{project_root}/.claude/experiments/{id}/` (confirmed: `_state_path` returns `self._experiments_dir / experiment_id / "state.json"` at line 54). The `complete_step` signature changes to add `rubric_scores: dict[str, bool] | None = None`. The `_apply_extension` method in `registry_loader.py` currently constructs a new `StepDefinition` with explicit keyword arguments (line 111-118) -- the new fields (`validation_rules`, `frozen_artefacts`) must be added to this constructor call after merging base + extension values.

**T5 (SKILL.md):** The existing Phase 2 flowchart is at lines 49-64 of the SKILL.md file. The replacement flowchart is specified verbatim in the architecture spec Gap 8 section. Only the Mermaid code block between the ` ```mermaid ` and ` ``` ` delimiters in the Phase 2 section should be replaced.

**T6 (tests/):** The `pyproject.toml` currently has no `[dependency-groups]` section -- one must be created. All tests use `tmp_path` for filesystem isolation. Integration tests in `test_complete_step_integration.py` must create a real `StateManager` with a real (but controlled) `RegistryLoader` pointing at the actual `registry/` directory to test the full stack. The `conftest.py` `mock_loader` fixture is only for `test_state_manager.py` unit tests.

#### Task Dependencies

```text
T1 → T2, T3, T5 (all three can run in parallel after T1)
T2 + T3 → T4 (T4 needs validators.py from T2 and updated JSON from T3)
T4 + T5 → T6 (T6 needs all implementation complete)
```

#### Environment Requirements

- Python >= 3.12 (declared in pyproject.toml)
- `fastmcp>=3.0.0` and `pydantic>=2.0` (existing dependencies)
- `pytest>=8.0.0`, `pytest-cov>=6.0.0`, `pytest-mock>=3.14.0` (T6 adds as dev dependencies)
- Linting via `uv run prek run --files <file>` (repository-wide pre-commit hooks)
- All Python execution via `uv run` (repository convention)

---

## Dependency Graph

```text
T1 (models.py foundation)
  ├── T2 (validators.py) ──────────────────────────────┐
  ├── T3 (experiment_core.json) ──────────────────────┤
  └── T5 (SKILL.md flowchart) [parallel, no code dep]  │
                                                        ▼
                                                T4 (state_manager.py + server.py integration)
                                                        │
                                                        ▼
                                                T6 (pytest test suite)
```

Parallelization: T2, T3, and T5 can all start after T1 completes and run concurrently.
T4 waits for T2 and T3. T6 waits for T4.

---

## SYNC CHECKPOINT 1 — After T1

**Convergence:** T1 complete
**Quality gates:**
- `models.py` exports `ValidationRule`, `ArtefactIntegrity`; `StepDefinition`, `ExperimentState`, `StepExtension` have new fields with `default_factory` defaults
- `uv run prek run --files plugins/scientific-method/mcp/experiment-registry/models.py` exits 0
- Existing state files load without error (backward compatibility via `default_factory`)

**Proceed:** T2, T3, T5 can launch concurrently after checkpoint passes.

---

## SYNC CHECKPOINT 2 — After T2 + T3

**Convergence:** T2 and T3 complete
**Quality gates:**
- `validators.py` exists, all 6 public functions present, no imports outside stdlib + models
- `experiment_core.json` has `validation_rules` and `frozen_artefacts` on all 5 steps
- `uv run prek run --files plugins/scientific-method/mcp/experiment-registry/validators.py` exits 0
- JSON validates as loadable by `registry_loader.py` (no schema errors on server startup)

**Proceed:** T4 launches after checkpoint passes.

---

## SYNC CHECKPOINT 3 — After T4 + T5

**Convergence:** T4 and T5 complete
**Quality gates:**
- `complete_step` in `state_manager.py` calls all 6 validators before artefact merge
- `server.py` `complete_step` tool has `rubric_scores: dict[str, bool] | None = None` parameter
- `experiment-protocol/SKILL.md` flowchart has `TermCheck` node and `FixV` branch
- `uv run prek run --files` on all changed files exits 0

**Proceed:** T6 launches after checkpoint passes.

---

## SYNC CHECKPOINT 4 — Final

**Convergence:** T6 complete
**Quality gates:**
- `cd plugins/scientific-method/mcp/experiment-registry && uv run pytest tests/ -v --cov=. --cov-report=term-missing` exits 0
- Coverage: overall >= 80%, `validators.py` >= 95%
- All AC1–AC6 acceptance criterion tests pass
- No regressions from pre-existing server.py/state_manager.py behavior

**Final commit message:** `feat(scientific-method): implement experiment protocol validation (Fixes #431)`

---

## Tasks

---

### Task T1: Add Pydantic models for ValidationRule, ArtefactIntegrity, and new StepDefinition/ExperimentState/StepExtension fields

```yaml
task: T1
title: Add Pydantic foundation models for validation layer
status: IN PROGRESS
started: 2026-03-04T00:00:00Z
agent: python3-development:python-cli-architect
dependencies: []
priority: 1
complexity: medium
accuracy-risk: medium
skills:
  - python3-development
  - fastmcp-creator
parallelize-with: []
reason: No other task writes models.py; this is the sole foundation task.
handoff: |
  Report: list of new classes and fields added to models.py, result of
  `uv run prek run --files models.py`, and confirmation that a round-trip
  load of a minimal ExperimentState JSON with none of the new fields succeeds.
```

#### Context

This task was not merged from multiple candidates — it is the sole writer to `models.py`.

Reference files (read before implementing):
- `plugins/scientific-method/mcp/experiment-registry/models.py` — existing model definitions
- `plan/architect-experiment-protocol-validation.md` sections: "Data Model Changes", "New Models", "Modified Models"

The architecture specifies all new types using `Field(default_factory=...)` to ensure backward compatibility with existing state JSON files. Pydantic fills defaults for missing fields during deserialization.

#### Objective

Add `ValidationRule`, `ArtefactIntegrity` as new Pydantic models, and extend `StepDefinition`, `ExperimentState`, and `StepExtension` with new fields — all backward-compatible with existing persisted state.

#### Required Inputs

- `plugins/scientific-method/mcp/experiment-registry/models.py` — existing source to modify
- `plan/architect-experiment-protocol-validation.md` — "Data Model Changes" and "New Models" sections (primary spec)

Confirm before acting: `models.py` currently has `StepDefinition`, `StepExtension`, `ExperimentType`, `ExperimentState`, `RubricTemplate`. The `StepDefinition.validation` field is `str = ""`. Verify these exist at the line numbers referenced in the codebase analysis before editing.

#### Requirements

1. Add `ValidationRule(BaseModel)` with fields:
   - `type: Literal["required_sections", "non_empty", "no_forbidden_content", "min_criteria_count"]`
   - `params: dict[str, Any] = Field(default_factory=dict)`
2. Add `ArtefactIntegrity(BaseModel)` with fields:
   - `sha256: str`
   - `frozen_at: str` (ISO 8601 timestamp string)
   - `frozen_by_step: str` (step ID that froze this artefact)
3. Add to `StepDefinition`:
   - `validation_rules: list[ValidationRule] = Field(default_factory=list)`
   - `frozen_artefacts: list[str] = Field(default_factory=list)`
   - Preserve the existing `validation: str = ""` field unchanged
4. Add to `ExperimentState`:
   - `artefact_integrity: dict[str, ArtefactIntegrity] = Field(default_factory=dict)`
5. Add to `StepExtension`:
   - `additional_validation_rules: list[ValidationRule] = Field(default_factory=list)`
   - `additional_frozen_artefacts: list[str] = Field(default_factory=list)`
6. Add required imports: `from typing import Any, Literal` (check existing imports first; add only what is missing)

#### Constraints

- Do not remove any existing field from any model
- Do not change the type of any existing field
- All new fields must use `Field(default_factory=...)` — never bare mutable defaults
- Do not add Pydantic validators (`@field_validator`, `@model_validator`) — pure data model only
- Do not create a new file — modify `models.py` in-place

#### Expected Outputs

- `plugins/scientific-method/mcp/experiment-registry/models.py` — modified with 2 new classes and 5 new fields on existing classes

#### Acceptance Criteria

1. `ValidationRule` exists and accepts `{"type": "non_empty", "params": {}}` without error
2. `ArtefactIntegrity` exists and accepts `{"sha256": "abc", "frozen_at": "2026-03-04T00:00:00Z", "frozen_by_step": "fixture"}` without error
3. `StepDefinition` loads from existing JSON with no `validation_rules` or `frozen_artefacts` keys (defaults to empty list)
4. `ExperimentState` loads from existing JSON with no `artefact_integrity` key (defaults to empty dict)
5. `StepExtension` accepts the new fields with default values
6. Linter passes: `uv run prek run --files plugins/scientific-method/mcp/experiment-registry/models.py` exits 0

#### Verification Steps

1. `cd plugins/scientific-method/mcp/experiment-registry && uv run python -c "from models import ValidationRule, ArtefactIntegrity, StepDefinition, ExperimentState, StepExtension; vr = ValidationRule(type='non_empty', params={}); print('ValidationRule OK:', vr)"`
2. `cd plugins/scientific-method/mcp/experiment-registry && uv run python -c "import json; from models import ExperimentState; state_json = '{\"id\":\"test\",\"base\":\"experiment_core\",\"status\":\"in_progress\"}'; s = ExperimentState.model_validate_json(state_json); print('Backward compat OK; artefact_integrity:', s.artefact_integrity)"`
3. `uv run prek run --files plugins/scientific-method/mcp/experiment-registry/models.py`

#### CoVe Checks

Key claims to verify:
- `Literal` type for `ValidationRule.type` supports exactly the 4 specified string values
- `Field(default_factory=dict)` and `Field(default_factory=list)` work correctly with Pydantic v2

Verification questions:
1. Does `StepDefinition.model_validate({"id": "x", "name": "y"})` succeed with the new optional fields absent?
2. Does `ValidationRule(type="unknown_type")` raise a Pydantic `ValidationError`?

Evidence to collect:
- Run both Python one-liners in Verification Steps 1 and 2 and report exact output
- Run `uv run python -c "from models import ValidationRule; ValidationRule(type='invalid')"` — expect `ValidationError`

Revision rule: If any check produces an unexpected error or passes when it should fail, fix the model definition before proceeding.

---

### Task T2: Implement validators.py — six composable pure-function validators

```yaml
task: T2
title: Implement validators.py validation engine
status: COMPLETE
started: 2026-03-04T00:00:00Z
completed: 2026-03-04T00:00:00Z
agent: python3-development:python-cli-architect
dependencies:
  - T1
priority: 2
complexity: high
accuracy-risk: medium
skills:
  - python3-development
  - fastmcp-creator
parallelize-with:
  - T3
  - T5
reason: T2, T3, and T5 write to different files (validators.py, experiment_core.json, SKILL.md) — no conflict.
handoff: |
  Report: list of all 6 public functions and all rule evaluators implemented,
  result of `uv run prek run --files validators.py`, and results of running
  the manual smoke tests in Verification Steps.
```

#### Context

`validators.py` is a new file. It does not exist yet. This task creates it from scratch.

Reference files (read before implementing):
- `plugins/scientific-method/mcp/experiment-registry/models.py` — after T1 completion; need `ValidationRule`, `ArtefactIntegrity`, `StepDefinition`, `ExperimentState`
- `plan/architect-experiment-protocol-validation.md` — "Validation Rule Engine", "Component Architecture" (Layer Dependency Changes), and "Gap-by-Gap Design" sections

The module contains only pure functions. No state mutation, no file writes, no class definitions. Every function returns a list of error dicts (empty list = no errors).

#### Objective

Create `plugins/scientific-method/mcp/experiment-registry/validators.py` with all 6 validation functions and all 4 rule evaluators, returning structured error dicts per the architecture spec.

#### Required Inputs

- `plan/architect-experiment-protocol-validation.md` — "Validation Rule Engine" and "Gap-by-Gap Design" sections (primary spec)
- `plugins/scientific-method/mcp/experiment-registry/models.py` — post-T1, to import `ValidationRule`, `StepDefinition`, `ExperimentState`
- Error codes from architecture spec: `EMPTY_ARTEFACT`, `FILE_NOT_FOUND`, `FROZEN_ARTEFACT_MODIFIED`, `MISSING_RUBRIC_SCORES`, `INCOMPLETE_RUBRIC_SCORES`, `UNKNOWN_RUBRIC_CRITERIA`, `CONTENT_VALIDATION_FAILED`, `MISSING_ITERATION_OUTPUT`, `TERMINAL_STATE`

#### Requirements

1. Create `validators.py` in `plugins/scientific-method/mcp/experiment-registry/`
2. Define string constants for all error codes at module level (e.g., `EMPTY_ARTEFACT = "EMPTY_ARTEFACT"`)
3. Implement `_RULE_EVALUATORS: dict[str, Callable[[str, dict], str | None]]` mapping each `ValidationRule.type` to an evaluator function
4. Implement `required_sections` evaluator: for each string in `params["sections"]`, check if it appears in file content (case-sensitive); return error message listing all missing sections or `None`
5. Implement `non_empty` evaluator: strip whitespace from content; return error if empty, else `None`
6. Implement `no_forbidden_content` evaluator: for each pattern in `params["patterns"]`, check if it appears in content (case-insensitive); return error listing all found patterns or `None`
7. Implement `min_criteria_count` evaluator: count lines matching `^- \[[ x]\]` pattern; if count < `params["min"]`, return error; else `None`
8. Implement the 6 public validation functions with exact signatures from the architecture spec:
   - `validate_artefact_content(step_def: StepDefinition, artefacts: dict[str, str], experiment_dir: Path) -> list[dict]`
   - `validate_file_existence(artefacts: dict[str, str], experiment_dir: Path) -> list[dict]`
   - `validate_freeze_integrity(state: ExperimentState, experiment_dir: Path) -> list[dict]`
   - `validate_rubric_scores(rubric_scores: dict[str, bool] | None, state: ExperimentState) -> list[dict]`
   - `validate_iteration_output(state: ExperimentState, artefacts: dict[str, str]) -> list[dict]`
   - `validate_terminal_state(state: ExperimentState) -> list[dict]`
9. `validate_file_existence`: skip artefact keys that do not contain `.` (no file extension = inline value per D1); resolve relative paths against `experiment_dir`; check `Path.exists()` and `Path.is_file()`
10. `validate_freeze_integrity`: for each key in `state.artefact_integrity`, resolve file path, compute `hashlib.sha256(path.read_bytes()).hexdigest()`, compare against `state.artefact_integrity[key].sha256`; return `FROZEN_ARTEFACT_MODIFIED` error if mismatch
11. `validate_rubric_scores`: if `state.current_step == "iterate"` and `rubric_scores is None`, return `MISSING_RUBRIC_SCORES`; if rubric_scores provided, verify completeness against `rubric_templates` names from state (use `state.merged_steps` to find rubric step's artefacts, then read rubric.md if no `rubric_templates` available)
12. `validate_iteration_output`: only for `step_id == "iterate"`; expected key = `f"output-iter{state.iteration_count + 1}.md"`; check key present in artefacts
13. `validate_terminal_state`: check `state.status` in `{"complete", "inconclusive"}`; return `TERMINAL_STATE` error if so
14. All error dicts have at minimum `code` and `message` keys; add context-specific fields per the error response spec in the architecture

#### Constraints

- No side effects: no file writes, no state mutation, no network calls
- No imports outside: `pathlib`, `hashlib`, `re`, `typing`, `models` (from the same package)
- Do not import from `state_manager.py` or `server.py` (would create circular imports)
- Do not short-circuit on first error in `validate_artefact_content` — collect all errors across all artefacts
- Artefact values are file paths; read file content via `Path.read_text()` not by using the value directly as content
- `validate_rubric_scores` must handle the case where the experiment has no `rubric_templates` (ad-hoc experiment): in this case, extract criterion names from `rubric.md` by finding lines matching `^#{1,3} ` or `^- \*\*[^*]+\*\*:` patterns

#### Expected Outputs

- `plugins/scientific-method/mcp/experiment-registry/validators.py` — new file, ~200-300 lines

#### Acceptance Criteria

1. All 9 error code constants defined at module level
2. All 4 rule evaluators implemented and registered in `_RULE_EVALUATORS`
3. All 6 public validation functions present with correct signatures
4. `validate_file_existence` skips keys without `.` in their name
5. `validate_freeze_integrity` returns `FROZEN_ARTEFACT_MODIFIED` when file content changes after hash computed
6. `validate_terminal_state` returns error for status `"complete"` and `"inconclusive"`, passes for `"in_progress"`
7. `uv run prek run --files plugins/scientific-method/mcp/experiment-registry/validators.py` exits 0

#### Verification Steps

1. `cd plugins/scientific-method/mcp/experiment-registry && uv run python -c "from validators import validate_terminal_state; from models import ExperimentState; s = ExperimentState(id='x', base='experiment_core', status='complete'); errors = validate_terminal_state(s); assert errors[0]['code'] == 'TERMINAL_STATE', errors; print('terminal state check OK')"`
2. `cd plugins/scientific-method/mcp/experiment-registry && uv run python -c "from validators import validate_file_existence; errs = validate_file_existence({'hypothesis.md': '/nonexistent/path.md', 'criteria_passed': 'true'}, __import__('pathlib').Path('.')); codes = [e['code'] for e in errs]; assert 'FILE_NOT_FOUND' in codes; assert len(errs) == 1, f'expected 1 error (criteria_passed skipped), got {len(errs)}'; print('file existence check OK')"`
3. `uv run prek run --files plugins/scientific-method/mcp/experiment-registry/validators.py`

#### CoVe Checks

Key claims to verify:
- `hashlib.sha256(path.read_bytes()).hexdigest()` is the correct API in Python 3.12
- `re` pattern `^- \[[ x]\]` correctly matches `- [ ]` and `- [x]` lines (criterion lines in markdown)

Verification questions:
1. Does `hashlib.sha256(b"test").hexdigest()` return a 64-character lowercase hex string?
2. Does `re.match(r'^- \[[ x]\]', '- [ ] criterion')` return a match object?
3. Does importing only `pathlib`, `hashlib`, `re`, `typing`, and the local `models` module avoid circular imports when `state_manager.py` later imports `validators`?

Evidence to collect:
- `uv run python -c "import hashlib; print(len(hashlib.sha256(b'test').hexdigest()))"` — expect 64
- `uv run python -c "import re; print(bool(re.match(r'^- \[[ x]\]', '- [ ] criterion')))"` — expect True

Revision rule: If any evaluator produces incorrect results on the verification inputs, fix the regex or API usage before marking complete.

---

### Task T3: Update experiment_core.json with validation_rules and frozen_artefacts

```yaml
task: T3
title: Add validation_rules and frozen_artefacts to experiment_core.json
status: IN PROGRESS
started: 2026-03-04T00:00:00Z
agent: python3-development:python-cli-architect
dependencies:
  - T1
priority: 2
complexity: low
accuracy-risk: low
skills:
  - python3-development
parallelize-with:
  - T2
  - T5
reason: T3 writes only to experiment_core.json; T2 writes validators.py; T5 writes SKILL.md — no file conflicts.
handoff: |
  Report: the final JSON for each step's validation_rules and frozen_artefacts,
  and confirmation that the file loads without JSON parse errors.
```

#### Context

`experiment_core.json` currently has 5 steps with a decorative `validation` string field and no `validation_rules` or `frozen_artefacts` fields. This task adds machine-evaluable `validation_rules` and `frozen_artefacts` to each step per the architecture spec.

The existing `validation` string field is preserved alongside the new `validation_rules` list — do not remove it.

Reference files:
- `plugins/scientific-method/mcp/experiment-registry/registry/experiment_core.json` — file to modify
- `plan/architect-experiment-protocol-validation.md` — "JSON Schema Changes" section (exact JSON examples provided for all 5 steps)

#### Objective

Edit `experiment_core.json` to add `validation_rules` and `frozen_artefacts` arrays to each of the 5 step definitions, exactly as specified in the architecture spec.

#### Required Inputs

- `plugins/scientific-method/mcp/experiment-registry/registry/experiment_core.json` — file to modify
- `plan/architect-experiment-protocol-validation.md` — "JSON Schema Changes (`experiment_core.json`)" section, which contains the exact JSON for each step

#### Requirements

1. For the `hypothesis` step, add:
   ```json
   "validation_rules": [
     {"type": "non_empty", "params": {}},
     {"type": "required_sections", "params": {"sections": ["HYPOTHESIS:", "CURRENT BEHAVIOUR:", "SUCCESS CRITERION:"]}}
   ],
   "frozen_artefacts": []
   ```
2. For the `fixture` step, add:
   ```json
   "validation_rules": [
     {"type": "non_empty", "params": {}},
     {"type": "no_forbidden_content", "params": {"patterns": ["EXPECTED:", "CORRECT ANSWER:", "SUCCESS CRITERION:", "RUBRIC:"]}}
   ],
   "frozen_artefacts": ["fixture.md"]
   ```
3. For the `rubric` step, add:
   ```json
   "validation_rules": [
     {"type": "non_empty", "params": {}},
     {"type": "min_criteria_count", "params": {"min": 1}}
   ],
   "frozen_artefacts": ["rubric.md"]
   ```
4. For the `baseline` step, add:
   ```json
   "validation_rules": [
     {"type": "non_empty", "params": {}}
   ],
   "frozen_artefacts": []
   ```
5. For the `iterate` step, add:
   ```json
   "validation_rules": [
     {"type": "non_empty", "params": {}},
     {"type": "required_sections", "params": {"sections": ["## Iteration"]}}
   ],
   "frozen_artefacts": []
   ```
6. Preserve all existing fields unchanged (`id`, `name`, `required_artefacts`, `validation`, `checklist`, etc.)

#### Constraints

- Do not remove or rename any existing field
- Preserve the existing `validation` string field alongside `validation_rules`
- JSON must remain valid after edits — verify with `python -m json.tool`
- Do not add `validation_rules` or `frozen_artefacts` to domain type JSON files (`ai_agent_testing.json`, `skill_evaluation_experiments.json`) — only `experiment_core.json`

#### Expected Outputs

- `plugins/scientific-method/mcp/experiment-registry/registry/experiment_core.json` — modified with `validation_rules` and `frozen_artefacts` on all 5 steps

#### Acceptance Criteria

1. All 5 steps have `validation_rules` array with at least one rule
2. `fixture` step has `frozen_artefacts: ["fixture.md"]`
3. `rubric` step has `frozen_artefacts: ["rubric.md"]`
4. `hypothesis`, `baseline`, `iterate` steps have `frozen_artefacts: []`
5. Existing `validation` string field is preserved on all steps
6. `python -m json.tool plugins/scientific-method/mcp/experiment-registry/registry/experiment_core.json` exits 0

#### Verification Steps

1. `python -m json.tool plugins/scientific-method/mcp/experiment-registry/registry/experiment_core.json > /dev/null && echo "JSON valid"`
2. `cd plugins/scientific-method/mcp/experiment-registry && uv run python -c "from registry_loader import RegistryLoader; loader = RegistryLoader(); t = loader.get_type('experiment_core'); steps = {s.id: s for s in t.steps}; assert steps['fixture'].frozen_artefacts == ['fixture.md']; assert steps['hypothesis'].validation_rules; print('Registry loads OK; fixture frozen:', steps['fixture'].frozen_artefacts)"`
3. `cd plugins/scientific-method/mcp/experiment-registry && uv run python -c "from registry_loader import RegistryLoader; loader = RegistryLoader(); t = loader.get_type('experiment_core'); iterate = next(s for s in t.steps if s.id == 'iterate'); assert any(r.type == 'required_sections' for r in iterate.validation_rules); print('iterate required_sections rule present')"`

---

### Task T4: Wire validators into state_manager.py and add rubric_scores to server.py

```yaml
task: T4
title: Integrate validation layer into complete_step and add rubric_scores API parameter
status: COMPLETE
started: 2026-03-04T03:00:00Z
completed: 2026-03-04T04:00:00Z
agent: python3-development:python-cli-architect
dependencies:
  - T1
  - T2
  - T3
priority: 3
complexity: high
accuracy-risk: medium
skills:
  - python3-development
  - fastmcp-creator
parallelize-with: []
reason: T4 is the sole writer to state_manager.py and server.py in this plan.
handoff: |
  Report: the exact insertion points modified in state_manager.py (line numbers),
  the new rubric_scores parameter signature in server.py, result of
  `uv run prek run --files` on both files, and confirmation that
  existing server startup does not error (import smoke test).
```

#### Context

This task was merged from two candidate changes (state_manager integration and server.py API change) to avoid edit conflicts on shared files. Both changes are required together — the server.py parameter passes `rubric_scores` to state_manager, so they must be implemented as a unit.

Reference files (read before implementing):
- `plugins/scientific-method/mcp/experiment-registry/state_manager.py` — existing `complete_step` method, lines ~173-270
- `plugins/scientific-method/mcp/experiment-registry/server.py` — existing `complete_step` tool, ~line 280
- `plugins/scientific-method/mcp/experiment-registry/registry_loader.py` — `_apply_extension` method for StepExtension merge
- `plan/architect-experiment-protocol-validation.md` — "Validation Insertion Point", "Error Response Extension", "Gap 3 (criteria_passed)", "Extension Compatibility", "Backward Compatibility" sections

The architecture specifies two insertion points in `complete_step`:
1. Pre-merge validation block (after required artefacts check, before `state.artefacts.update(artefacts)`)
2. Post-merge hash computation (after `state.artefacts.update(artefacts)`, before step advancement)

#### Objective

Wire the 6 validators from `validators.py` into `StateManager.complete_step()`, add `rubric_scores: dict[str, bool] | None = None` to the server.py `complete_step` MCP tool, compute and store SHA-256 hashes for frozen artefacts post-merge, and update `registry_loader.py` to merge `additional_validation_rules` and `additional_frozen_artefacts` from `StepExtension`.

#### Required Inputs

- `plugins/scientific-method/mcp/experiment-registry/state_manager.py` — primary file to modify
- `plugins/scientific-method/mcp/experiment-registry/server.py` — MCP tool layer to modify
- `plugins/scientific-method/mcp/experiment-registry/registry_loader.py` — `_apply_extension` method to extend
- `plugins/scientific-method/mcp/experiment-registry/validators.py` — post-T2; all 6 functions to import
- `plugins/scientific-method/mcp/experiment-registry/models.py` — post-T1; `ArtefactIntegrity` to import

Confirm before acting: `state_manager.py` has `state.artefacts.update(artefacts)` at approximately line 229. Verify actual line number before editing.

#### Requirements

### state_manager.py changes

1. Add import: `from validators import (validate_terminal_state, validate_file_existence, validate_artefact_content, validate_freeze_integrity, validate_iteration_output, validate_rubric_scores)`
2. Add import: `import hashlib` and `import datetime` (if not already present); `from models import ArtefactIntegrity`
3. Change `complete_step` signature to: `complete_step(self, experiment_id: str, step_id: str, artefacts: dict[str, str], rubric_scores: dict[str, bool] | None = None) -> dict`
4. Insert pre-merge validation block after the existing required artefacts check (after line ~226) and before `state.artefacts.update(artefacts)`:
   ```text
   a. errors = validate_terminal_state(state)
   b. errors += validate_file_existence(artefacts, experiment_dir)
   c. errors += validate_artefact_content(current_def, artefacts, experiment_dir)
   d. errors += validate_freeze_integrity(state, experiment_dir)
   e. errors += validate_iteration_output(state, artefacts)  [only if step_id == "iterate"]
   f. errors += validate_rubric_scores(rubric_scores, state)  [only if step_id == "iterate"]
   if errors: return {"success": False, "validation_errors": errors}
   ```
5. Determine `experiment_dir` as `self._state_path(experiment_id).parent` (the directory containing `state.json`)
6. Insert post-merge hash computation block after `state.artefacts.update(artefacts)` and before step advancement:
   ```text
   for key in current_def.frozen_artefacts:
       artefact_path = experiment_dir / artefacts.get(key, key)
       if artefact_path.is_file():
           content_hash = hashlib.sha256(artefact_path.read_bytes()).hexdigest()
           state.artefact_integrity[key] = ArtefactIntegrity(
               sha256=content_hash,
               frozen_at=datetime.datetime.now(datetime.UTC).isoformat(),
               frozen_by_step=step_id
           )
   ```
7. In the iterate step branch (lines ~236-257): replace `criteria_passed = artefacts.get("criteria_passed", "").lower() == "true"` with `criteria_passed = all(rubric_scores.values()) if rubric_scores else False`; store `rubric_scores` in state.artefacts as JSON: `state.artefacts[f"rubric_scores_iter{state.iteration_count}"] = json.dumps(rubric_scores or {})`
8. Add `import json` if not already present

### server.py changes

9. Add `rubric_scores: dict[str, bool] | None = None` parameter to the `complete_step` tool function
10. Pass `rubric_scores` to `manager.complete_step(experiment_id, step_id, artefacts, rubric_scores=rubric_scores)`

### registry_loader.py changes

11. In `_apply_extension`, add merge logic for new StepExtension fields:
    ```text
    merged.validation_rules = base.validation_rules + ext.additional_validation_rules
    merged.frozen_artefacts = list(dict.fromkeys(base.frozen_artefacts + ext.additional_frozen_artefacts))
    ```
    (use `dict.fromkeys` to deduplicate while preserving order)

#### Constraints

- Do not change any existing response format keys — `missing_artefacts`, `blocked_on_human_input` remain unchanged
- `validation_errors` is the only new response key
- Do not break the existing `criteria_passed` behavior for non-iterate steps — the `rubric_scores` parameter is optional and only enforced for `iterate`
- The old `criteria_passed` artefact key, if provided in `artefacts`, is silently ignored — do not raise an error
- Do not add `rubric_scores` to `required_artefacts` in the JSON — it comes in as a separate parameter
- Hash computation only runs when `current_def.frozen_artefacts` is non-empty; skip if empty list

#### Expected Outputs

- `plugins/scientific-method/mcp/experiment-registry/state_manager.py` — modified
- `plugins/scientific-method/mcp/experiment-registry/server.py` — modified (rubric_scores parameter)
- `plugins/scientific-method/mcp/experiment-registry/registry_loader.py` — modified (_apply_extension merge)

#### Acceptance Criteria

1. `complete_step` in `state_manager.py` calls all 6 validators in the pre-merge block
2. `complete_step` returns `{"success": False, "validation_errors": [...]}` when any validator returns errors; state file is not written on validation failure
3. After a step with `frozen_artefacts` completes, `state.artefact_integrity` contains entries for those artefacts
4. `server.py` `complete_step` tool accepts `rubric_scores` parameter and passes it through
5. `_apply_extension` in `registry_loader.py` merges `additional_validation_rules` and `additional_frozen_artefacts`
6. Import smoke test passes: `cd plugins/scientific-method/mcp/experiment-registry && uv run python -c "from server import mcp; print('import OK')"`
7. `uv run prek run --files` on all three modified files exits 0

#### Verification Steps

1. `cd plugins/scientific-method/mcp/experiment-registry && uv run python -c "from server import mcp; print('server import OK')"`
2. `cd plugins/scientific-method/mcp/experiment-registry && uv run python -c "from state_manager import StateManager; import inspect; sig = inspect.signature(StateManager.complete_step); assert 'rubric_scores' in sig.parameters; print('rubric_scores param present:', sig)"`
3. `uv run prek run --files plugins/scientific-method/mcp/experiment-registry/state_manager.py plugins/scientific-method/mcp/experiment-registry/server.py plugins/scientific-method/mcp/experiment-registry/registry_loader.py`

#### CoVe Checks

Key claims to verify:
- `self._state_path(experiment_id).parent` correctly resolves to the experiment directory containing artefact files
- `hashlib.sha256(path.read_bytes()).hexdigest()` is the correct idiom for file hashing
- `all(rubric_scores.values())` correctly evaluates all-criteria-pass when `rubric_scores` is `{"c1": True, "c2": False}`

Verification questions:
1. What does `self._state_path(experiment_id)` return? Is `.parent` the correct way to get the experiment directory?
2. Does `all({}.values())` return `True` (empty dict vacuously true)? If so, does that break the `rubric_scores or {}` guard?

Evidence to collect:
- Read `state_manager.py` `_state_path` method to confirm its return value before using `.parent`
- `uv run python -c "print(all({}.values()))"` — if True, the guard `rubric_scores.values() if rubric_scores else False` handles it

Revision rule: If `_state_path` returns the state.json file path (not the directory), use `.parent` as planned. If it returns the directory already, use it directly. Confirm before writing.

---

### Task T5: Update experiment-protocol SKILL.md Phase 2 flowchart with terminal-state guard

```yaml
task: T5
title: Add terminal-state guard and validation error branch to SKILL.md Phase 2 flowchart
status: COMPLETE
started: 2026-03-04T00:00:00Z
completed: 2026-03-04T00:00:00Z
agent: service-docs-maintainer
dependencies:
  - T1
priority: 2
complexity: low
accuracy-risk: low
skills: []
parallelize-with:
  - T2
  - T3
reason: T5 writes only to experiment-protocol/SKILL.md; T2 and T3 write to different files — no conflict.
handoff: |
  Report: the exact lines replaced in SKILL.md, the before and after flowchart
  Mermaid block, and result of `uv run prek run --files` on the file.
```

#### Context

The Phase 2 execution loop flowchart in `experiment-protocol/SKILL.md` enters the step loop at `GetStep` without checking whether the experiment is already in a terminal state (`complete` or `inconclusive`). The architecture spec (Gap 8) specifies two additions to the flowchart:

1. A `TermCheck` decision node between `GetStep` and `StepDetail`
2. A `FixV` branch from `MCPResult` for validation errors

Reference files:
- `plugins/scientific-method/skills/experiment-protocol/SKILL.md` — file to modify
- `plan/architect-experiment-protocol-validation.md` — "Gap 8 (LOW)" section, which contains the exact replacement Mermaid flowchart

#### Objective

Replace the Phase 2 flowchart in `experiment-protocol/SKILL.md` with the updated version from the architecture spec that includes the terminal-state guard node and validation error handling branch.

#### Required Inputs

- `plugins/scientific-method/skills/experiment-protocol/SKILL.md` — read the existing Phase 2 flowchart section
- `plan/architect-experiment-protocol-validation.md` — "Gap 8" section for the exact replacement flowchart

#### Requirements

1. Read the existing SKILL.md to locate the Phase 2 Mermaid flowchart block
2. Replace the existing Phase 2 flowchart with the architecture spec's updated flowchart verbatim:
   - Add `TermCheck{status is complete<br>or inconclusive?}` node after `GetStep`
   - Add `Handoff[Experiment already done — see Retrospective Handoff]` terminal node
   - Add `FixV[Fix validation issues and resubmit]` branch from `MCPResult`
   - Add `|Validation errors| FixV` edge from `MCPResult`
   - `FixV --> Complete` loopback edge
3. Do not modify any other section of SKILL.md — only the Phase 2 flowchart block

#### Constraints

- Do not modify Phase 1, Phase 3, or any non-flowchart content
- Mermaid flowchart must be syntactically valid — test by visual inspection of node/edge structure
- Preserve all existing flowchart nodes not mentioned in the architecture spec changes (do not remove existing nodes)
- Do not add a table of contents, summary, or commentary — only the flowchart update

#### Expected Outputs

- `plugins/scientific-method/skills/experiment-protocol/SKILL.md` — modified, Phase 2 flowchart updated

#### Acceptance Criteria

1. The flowchart contains a `TermCheck` diamond node between `GetStep` and `StepDetail`
2. The flowchart contains a `FixV` node connected from `MCPResult` via `|Validation errors|` edge
3. `FixV --> Complete` loopback edge is present
4. `Handoff` terminal node is reachable from `TermCheck` via `|Yes|` edge
5. All existing nodes (`Human`, `Surface`, `Resubmit`, `Produce`, `Fix`, `HandoffC`, `Report`) remain in the flowchart
6. `uv run prek run --files plugins/scientific-method/skills/experiment-protocol/SKILL.md` exits 0

#### Verification Steps

1. `grep -c "TermCheck" plugins/scientific-method/skills/experiment-protocol/SKILL.md` — expect >= 2 (node definition + edge)
2. `grep -c "FixV" plugins/scientific-method/skills/experiment-protocol/SKILL.md` — expect >= 2
3. `uv run prek run --files plugins/scientific-method/skills/experiment-protocol/SKILL.md`

---

### Task T6: Write pytest test suite for validators and complete_step integration

```yaml
task: T6
title: Write pytest test suite covering validators.py, state_manager integration, and AC1-AC6
status: COMPLETE
agent: python3-development:python-pytest-architect
dependencies:
  - T1
  - T2
  - T3
  - T4
priority: 4
complexity: high
accuracy-risk: medium
skills:
  - fastmcp-python-tests
  - python3-development
parallelize-with: []
reason: T6 depends on all implementation tasks and is the final task; no parallelization possible.
handoff: |
  Report: pytest output showing all tests pass, coverage summary (overall >=
  80%, validators.py >= 95%), list of test files created, and any gaps
  in coverage with justification.
```

#### Context

No test infrastructure exists under `plugins/scientific-method/mcp/experiment-registry/`. This task creates the entire test suite from scratch, including `conftest.py`, three test modules, and adds pytest dependencies to `pyproject.toml`.

Reference files (read before implementing):
- `plugins/scientific-method/mcp/experiment-registry/pyproject.toml` — existing deps; add pytest dev deps here
- `plugins/scientific-method/mcp/experiment-registry/validators.py` — post-T2
- `plugins/scientific-method/mcp/experiment-registry/state_manager.py` — post-T4
- `plugins/scientific-method/mcp/experiment-registry/models.py` — post-T1
- `plan/architect-experiment-protocol-validation.md` — "Testing Architecture" section (test strategy, fixture strategy, AC mapping)

#### Objective

Create a complete pytest suite that achieves >= 80% overall coverage and >= 95% coverage of `validators.py`, with all AC1–AC6 acceptance criteria verified by integration tests.

#### Required Inputs

- `plan/architect-experiment-protocol-validation.md` — "Testing Architecture" section (test strategy per module, fixture strategy, AC mapping)
- All implemented source files (post-T1 through T4)

#### Requirements

### pyproject.toml

1. Add to `[dependency-groups]` (or equivalent dev-deps section in pyproject.toml):
   - `pytest>=8.0.0`
   - `pytest-cov>=6.0.0`
   - `pytest-mock>=3.14.0`

### conftest.py

2. Create `plugins/scientific-method/mcp/experiment-registry/tests/conftest.py` with:
   - `experiment_dir` fixture: creates a `tmp_path`-based directory structure
   - `make_state` factory fixture: returns a callable that creates `ExperimentState` with configurable fields (status, iteration_count, artefact_integrity, etc.)
   - `make_artefact_file` factory fixture: returns a callable that writes a file to `tmp_path` and returns its path string
   - `mock_loader` fixture: returns a mock `RegistryLoader` instance with controllable `merge_type` output

### test_validators.py

3. Create `plugins/scientific-method/mcp/experiment-registry/tests/test_validators.py`:
   - Parametrized tests for each of the 4 rule evaluators (valid content → no error; invalid content → specific error code)
   - `validate_artefact_content`: test multiple error accumulation (both empty AND missing section in same call)
   - `validate_file_existence`: test file present, file absent, key without `.` (skipped)
   - `validate_freeze_integrity`: test with empty `artefact_integrity` dict (passes), test with matching hash (passes), test with modified file (returns `FROZEN_ARTEFACT_MODIFIED`)
   - `validate_rubric_scores`: test None (returns `MISSING_RUBRIC_SCORES`), complete scores (passes), missing criteria (returns `INCOMPLETE_RUBRIC_SCORES`), extra criteria (returns `UNKNOWN_RUBRIC_CRITERIA`)
   - `validate_iteration_output`: test correct key present (passes), missing key (returns `MISSING_ITERATION_OUTPUT`), boundary: iteration_count=0 expects `output-iter1.md`
   - `validate_terminal_state`: test `"in_progress"` (passes), `"complete"` (returns `TERMINAL_STATE`), `"inconclusive"` (returns `TERMINAL_STATE`)

### test_state_manager.py

4. Create `plugins/scientific-method/mcp/experiment-registry/tests/test_state_manager.py`:
   - Test that validation errors prevent state file mutation (read state file before and after failed `complete_step`, assert unchanged)
   - Test that `frozen_artefacts` hashes are stored in `state.artefact_integrity` after step completes
   - Test backward compatibility: `ExperimentState` with no `artefact_integrity` field deserializes correctly (defaults to `{}`)
   - Test that `rubric_scores` is stored as JSON under `rubric_scores_iter{N}` key in `state.artefacts`

### test_complete_step_integration.py

5. Create `plugins/scientific-method/mcp/experiment-registry/tests/test_complete_step_integration.py` with one test per acceptance criterion:
   - `test_ac1_empty_artefact_rejected`: write empty `hypothesis.md` to `tmp_path`, call `complete_step`, assert `success=False` and `validation_errors` contains `EMPTY_ARTEFACT`
   - `test_ac3_frozen_artefact_modified_rejected`: complete through fixture step, modify `fixture.md` content, call `complete_step(rubric)`, assert `FROZEN_ARTEFACT_MODIFIED`
   - `test_ac4_missing_iteration_output_rejected`: complete through baseline, call `complete_step(iterate)` with only `log.md`, assert `MISSING_ITERATION_OUTPUT`
   - `test_ac5_criteria_passed_without_rubric_scores_rejected`: call `complete_step(iterate)` with `artefacts={"log.md": "...", "criteria_passed": "true"}` and `rubric_scores=None`, assert `MISSING_RUBRIC_SCORES`
   - `test_ac6_terminal_state_rejected`: complete experiment fully, call `complete_step` again, assert `TERMINAL_STATE`

#### Constraints

- Use `tmp_path` for all file system operations — no writes outside `tmp_path`
- Do not mock `validate_*` functions in integration tests — test the real validators end-to-end
- Mock `RegistryLoader` only in `test_state_manager.py` to isolate state_manager from JSON file changes
- Each test function must be independently runnable (no ordering dependency between tests)
- Coverage must be measured with `--cov=.` scoped to the package directory

#### Expected Outputs

- `plugins/scientific-method/mcp/experiment-registry/tests/__init__.py` — empty file
- `plugins/scientific-method/mcp/experiment-registry/tests/conftest.py`
- `plugins/scientific-method/mcp/experiment-registry/tests/test_validators.py`
- `plugins/scientific-method/mcp/experiment-registry/tests/test_state_manager.py`
- `plugins/scientific-method/mcp/experiment-registry/tests/test_complete_step_integration.py`
- `plugins/scientific-method/mcp/experiment-registry/pyproject.toml` — updated with pytest dev deps

#### Acceptance Criteria

1. `cd plugins/scientific-method/mcp/experiment-registry && uv run pytest tests/ -v` exits 0 with all tests passing
2. `uv run pytest tests/ --cov=. --cov-report=term-missing` shows overall coverage >= 80%
3. `validators.py` coverage >= 95% in the coverage report
4. All 5 AC integration tests (`test_ac1` through `test_ac6`) pass
5. No test writes files outside `tmp_path`
6. `uv run prek run --files` on all test files exits 0

#### Verification Steps

1. `cd plugins/scientific-method/mcp/experiment-registry && uv run pytest tests/ -v --tb=short 2>&1 | tail -20`
2. `cd plugins/scientific-method/mcp/experiment-registry && uv run pytest tests/ --cov=. --cov-report=term-missing 2>&1 | grep -E "validators|TOTAL"`
3. `cd plugins/scientific-method/mcp/experiment-registry && uv run pytest tests/test_complete_step_integration.py -v --tb=short`
4. `uv run prek run --files plugins/scientific-method/mcp/experiment-registry/tests/conftest.py plugins/scientific-method/mcp/experiment-registry/tests/test_validators.py plugins/scientific-method/mcp/experiment-registry/tests/test_state_manager.py plugins/scientific-method/mcp/experiment-registry/tests/test_complete_step_integration.py`

#### CoVe Checks

Key claims to verify:
- `pytest-cov` syntax `--cov=.` is correct for measuring coverage of the current package directory
- `uv run pytest` invocation from the package directory finds the `tests/` subdirectory by default

Verification questions:
1. Does `uv run pytest tests/` from `plugins/scientific-method/mcp/experiment-registry/` correctly discover all test files?
2. Does `--cov=.` measure coverage of modules in the current directory (e.g., `validators.py`, `state_manager.py`) when tests are in `tests/`?

Evidence to collect:
- After writing `conftest.py` and a single stub test, run `uv run pytest tests/ --collect-only` to confirm discovery before writing all tests
- `uv run pytest --version` to confirm pytest is installed via dev deps

Revision rule: If `--cov=.` does not show `validators.py` in the coverage report, try `--cov=plugins/scientific-method/mcp/experiment-registry` with absolute path. Report what worked.

---

## Plan Validation

### CLEAR Lint

- **Concise**: No duplicated requirements across tasks. Each task owns one file set.
- **Logical**: Tasks follow canonical CLEAR section order throughout.
- **Explicit**: All outputs have exact file paths. All acceptance criteria are testable.
- **Adaptive**: Variants provided only in T4 CoVe (two possible `_state_path` behaviors).
- **Reflective**: Each task includes assumption checks (Confirm before acting) and CoVe where risk is medium.

### Schema Completeness

- All tasks: `status`, `agent`, `accuracy-risk`, `skills` in YAML frontmatter ✓
- All tasks: Expected Outputs with file paths ✓
- All tasks: Verification Steps with runnable commands ✓
- Tasks T1, T2, T4, T6: `accuracy-risk: medium` → CoVe Checks included ✓
- Tasks T3, T5: `accuracy-risk: low` → CoVe Checks omitted ✓

### Same-File Conflict Check

| File | Tasks | Resolution |
|------|-------|------------|
| `models.py` | T1 only | No conflict |
| `validators.py` | T2 only | No conflict |
| `experiment_core.json` | T3 only | No conflict |
| `state_manager.py` | T4 only | Merged (was T4 + candidate server-API task) |
| `server.py` | T4 only | Merged |
| `registry_loader.py` | T4 only | Merged |
| `experiment-protocol/SKILL.md` | T5 only | No conflict |
| `tests/` | T6 only | No conflict |

### Skills Field Check

- T1, T2, T4: `["python3-development", "fastmcp-creator"]` — matches Python implementation pattern ✓
- T3: `["python3-development"]` — JSON editing task; no fastmcp-creator needed ✓
- T5: `[]` — documentation-only task; service-docs-maintainer agent handles without skills ✓
- T6: `["fastmcp-python-tests", "python3-development"]` — matches test task pattern ✓
