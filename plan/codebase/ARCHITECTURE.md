# Module Architecture — scientific-method MCP Server

**Analysis Date:** 2026-03-04
**Package:** `experiment-registry` (MCP server)
**Root:** `plugins/scientific-method/mcp/experiment-registry/`

---

## Module Overview

```text
plugins/scientific-method/
├── mcp/
│   └── experiment-registry/          # MCP server package
│       ├── __init__.py
│       ├── pyproject.toml            # fastmcp>=3.0.0, pydantic>=2.0, requires-python>=3.12
│       ├── server.py                 # FastMCP tool registration — public MCP API
│       ├── state_manager.py          # Experiment lifecycle — create/load/advance/list
│       ├── models.py                 # Pydantic models — data contracts
│       ├── registry_loader.py        # JSON registry discovery and step merge logic
│       └── registry/
│           ├── experiment_core.json  # Universal 5-step protocol (core base type)
│           ├── ai_agent_testing.json # Domain type extending experiment_core
│           ├── skill_evaluation_experiments.json
│           └── examples/            # Excluded from type discovery at runtime
│               ├── debugging_javascript.json
│               └── performance_regression.json
├── skills/
│   └── scientific-thinking/
│       └── SKILL.md                  # Phase 2 flowchart — AI-facing execution loop
├── agents/
│   └── retrospective-analyst.md
├── shared/
│   ├── investigation-template.md
│   ├── investigation-workflow.md
│   ├── causality-check.md
│   └── evidence-rules.md
└── hooks/
    └── hooks.json
```

---

## Layer Dependencies

**MCP Tool Layer** (`server.py`):
- Depends on: `models.StepExtension`, `registry_loader.RegistryLoader`, `state_manager.StateManager`
- Provides: 7 FastMCP tools over the MCP protocol
- Owns: module-level `_loader = RegistryLoader()` singleton (loaded once per process)
- Error boundary: converts `ValueError` from lower layers to `fastmcp.exceptions.ToolError`

**State Manager Layer** (`state_manager.py`):
- Depends on: `models.ExperimentState`, `models.StepDefinition`, `models.StepExtension`, `registry_loader.RegistryLoader`
- Provides: experiment CRUD + step lifecycle
- Owns: filesystem persistence at `{project_root}/.claude/experiments/{id}/state.json`

**Registry Loader Layer** (`registry_loader.py`):
- Depends on: `models.ExperimentType`, `models.StepDefinition`, `models.StepExtension`, `models.RubricTemplate`
- Provides: type discovery, type lookup, 3-layer step merge
- Owns: in-memory `dict[str, ExperimentType]` loaded at `__init__` time

**Model Layer** (`models.py`):
- Depends on: `pydantic`, stdlib only
- Provides: all data contracts as Pydantic `BaseModel` subclasses
- No business logic — pure data definitions

---

## Data Flow

```text
MCP Client
    │
    ▼ FastMCP tool call (e.g. start_experiment)
server.py
    │  _make_state_manager(project_root) → StateManager(root, _loader)
    │
    ▼ manager.create_experiment(base, context, extensions)
state_manager.py
    │  _loader.merge_type(base, inline_extensions)
    │
    ▼ registry_loader.py
    │  1. get_type("experiment_core") → core steps
    │  2. get_type(base_name) → domain step_extensions
    │  3. _apply_extension(step, ext) per step → merged StepDefinition list
    │  4. apply inline_extensions last
    │
    ▼ merged list[StepDefinition] returned to state_manager
state_manager.py
    │  ExperimentState(id=..., merged_steps=merged, current_step=first, ...)
    │  _save(state) → .claude/experiments/{id}/state.json
    │
    ▼ ExperimentState returned to server.py
server.py
    └─ serialise to dict → return to MCP client
```

---

## state_manager.py — Complete complete_step Flow

**Entry point:** `StateManager.complete_step(experiment_id, step_id, artefacts)` — `state_manager.py:173`

**Step-by-step execution:**

1. **Load state** (`state_manager.py:194`): `self.load_experiment(experiment_id)` — reads JSON from disk, constructs `ExperimentState`.

2. **Step identity check** (`state_manager.py:197-202`): Raises `ValueError` if `step_id != state.current_step`. The server converts this to `ToolError` (`server.py:294`).

3. **Locate step definition** (`state_manager.py:205-213`): Linear scan of `state.merged_steps` for matching `id`. Raises `ValueError` if not found (should not occur in normal flow since `current_step` is always set from `merged_steps`).

4. **Required artefacts check** (`state_manager.py:216-226`):
   - Computes `missing = [a for a in current_def.required_artefacts if a not in artefacts]`
   - If missing AND `human_input_required`: returns `{"success": False, "blocked_on_human_input": True, "description": ...}`
   - If missing AND NOT `human_input_required`: returns `{"success": False, "missing_artefacts": missing}`
   - **No save occurs on failure** — state is not mutated.

5. **Artefact merge** (`state_manager.py:229`): `state.artefacts.update(artefacts)` — cumulative across all steps; artefacts from earlier steps remain in state.

6. **Iterate step special handling** (`state_manager.py:236-257`):
   - Increments `state.iteration_count`
   - Reads `artefacts.get("criteria_passed", "").lower() == "true"` — string comparison, not boolean
   - If `criteria_passed == "true"`: sets `status = "complete"`, appends `step_id` to `completed_steps`, saves, returns `{"success": True, "next_step": None, "status": "complete"}`
   - If `iteration_count >= max_iterations`: sets `status = "inconclusive"`, saves, returns `{"success": True, "next_step": None, "status": "inconclusive"}`
   - Otherwise (loop back): saves without changing `current_step`, returns `{"success": True, "next_step": step_id, "status": "in_progress"}`

7. **Standard step advancement** (`state_manager.py:260-270`):
   - Appends `step_id` to `state.completed_steps`
   - Advances `current_step` to `step_ids[current_index + 1]`
   - If no next step: sets `status = "complete"`, `next_step = None`
   - Updates `last_updated`, saves, returns `{"success": True, "next_step": ..., "status": ...}`

**Artefact handling notes:**
- All artefacts are `dict[str, str]` — values are strings, not file paths or file content (the key names like `"hypothesis.md"` are identifiers, not actual file system paths)
- Artefacts accumulate on `state.artefacts` — they are never removed
- `state_manager.py:229` merges unconditionally after the missing-artefacts check passes

**Validation field:**
- `StepDefinition.validation` (`models.py:20`) stores a human-readable description string (e.g., `"contains HYPOTHESIS:, CURRENT BEHAVIOUR:, SUCCESS CRITERION:"`)
- `complete_step` in `state_manager.py` does **not** evaluate `validation` — it only checks key presence in `required_artefacts`
- `validation` is read-only metadata: exposed via `get_current_step` (`server.py:246`) and `inspect_experiment_type` (`server.py:89`) for the AI caller to interpret

---

## server.py — MCP Tool Inventory

**Framework:** FastMCP 3.x (`server.py:14`). Server instance: `mcp = FastMCP("experiment-registry")` (`server.py:20`).

**Module-level singleton:** `_loader = RegistryLoader()` (`server.py:23`) — registry files loaded once at process start.

**`_make_state_manager(project_root)`** (`server.py:26-37`): Factory function. Every tool call creates a fresh `StateManager` scoped to the given `project_root` (defaults to `Path.cwd()`). No StateManager singleton.

**Tool table:**

| Tool | MCP annotation | State mutation | Returns |
|------|---------------|----------------|---------|
| `list_experiment_types` | `readOnlyHint: True` | None | `{types: [{name, description}], count}` |
| `inspect_experiment_type` | `readOnlyHint: True` | None | Full type with steps, extensions, rubric_templates, anti_patterns |
| `start_experiment` | (none) | Creates state.json | `{experiment_id, base, context, status, first_step, total_steps, state_path}` |
| `get_current_step` | `readOnlyHint: True` | None | `{experiment_id, status, current_step, provided_artefacts, missing_artefacts, completed_steps, iteration_count}` |
| `complete_step` | (none) | Advances state.json | `{success, next_step, status}` or `{success: False, missing_artefacts/blocked_on_human_input}` |
| `list_experiments` | `readOnlyHint: True` | None | `{experiments: [summaries], count}` |
| `resume_experiment` | `readOnlyHint: True` | None | Full state dict for session recovery |
| `get_experiment_summary` | `readOnlyHint: True` | None | Summary dict + `state_file_path` for retrospective handoff |

**Error boundary pattern** (`server.py:79-82`, `server.py:173-174`, `server.py:291-294`):

```python
try:
    result = manager.some_method(...)
except ValueError as exc:
    raise ToolError(str(exc)) from exc
```

All `ValueError` from `StateManager` and `RegistryLoader` are wrapped in `ToolError`. Other exceptions propagate uncaught.

**`start_experiment` extensions parsing** (`server.py:169-174`): Inline extensions arrive as `dict[str, dict[str, Any]]` from the MCP caller. The tool manually constructs `StepExtension(**ext)` per entry in a `try/except Exception` — the only broad-except in the codebase.

**Private attribute access:** Two tools access `manager._state_path(...)` directly with `# noqa: SLF001` comments (`server.py:200`, `server.py:413`).

---

## models.py — Pydantic Model Definitions

**File:** `plugins/scientific-method/mcp/experiment-registry/models.py`

### StepDefinition (`models.py:14`)

```python
class StepDefinition(BaseModel):
    id: str
    name: str
    required_artefacts: list[str] = Field(default_factory=list)
    validation: str = ""          # Human-readable rule; NOT evaluated by code
    checklist: list[str] = Field(default_factory=list)
    human_input_required: bool = False
    human_input_description: str = ""
```

Validation at model layer: Pydantic type coercion only. `validation` field is a plain `str` — no schema enforcement, no runtime evaluation.

### RubricTemplate (`models.py:27`)

```python
class RubricTemplate(BaseModel):
    name: str
    observable: str
    pass_: str = Field(alias="pass")   # "pass" is a Python keyword; alias required
    fail: str
    model_config = {"populate_by_name": True}
```

Uses `alias="pass"` to handle the reserved keyword. `populate_by_name=True` allows construction with `pass_=` as well as `pass=`.

### StepExtension (`models.py:37`)

```python
class StepExtension(BaseModel):
    additional_artefacts: list[str] = Field(default_factory=list)
    checklist: list[str] = Field(default_factory=list)
    human_input_required: bool | None = None   # None = "do not override base"
    human_input_description: str = ""
```

`human_input_required: bool | None` — `None` is the sentinel meaning "do not override the base step's value". Checked in `registry_loader.py:104`: `if ext.human_input_required is not None`.

### ExperimentType (`models.py:46`)

```python
class ExperimentType(BaseModel):
    name: str
    description: str
    extends: str | None = None                          # Parent type name; informational only
    steps: list[StepDefinition] = Field(default_factory=list)
    step_extensions: dict[str, StepExtension] = Field(default_factory=dict)
    rubric_templates: list[RubricTemplate] = Field(default_factory=list)
    anti_patterns: list[str] = Field(default_factory=list)
```

`extends` field is stored but **not used by `RegistryLoader.merge_type`** for resolution. Merge logic always starts from `experiment_core` regardless of `extends` value — `extends` is documentation only (`registry_loader.py:177-195`).

### ExperimentState (`models.py:58`)

```python
class ExperimentState(BaseModel):
    id: str
    base: str
    extensions: list[str] = Field(default_factory=list)    # Unused — always empty list
    inline_extensions: dict[str, StepExtension] = Field(default_factory=dict)
    merged_steps: list[StepDefinition] = Field(default_factory=list)
    current_step: str = ""
    completed_steps: list[str] = Field(default_factory=list)
    artefacts: dict[str, str] = Field(default_factory=dict)
    context: str = ""
    iteration_count: int = 0
    max_iterations: int = 10
    status: str = "in_progress"                             # Literal values: "in_progress", "complete", "inconclusive"
    created: str = Field(default_factory=lambda: datetime.datetime.now(datetime.UTC).isoformat())
    last_updated: str = Field(default_factory=lambda: datetime.datetime.now(datetime.UTC).isoformat())
```

`status` is an unconstrained `str` — no `Literal` type, no `Enum`. Valid runtime values set in `state_manager.py`: `"in_progress"`, `"complete"`, `"inconclusive"`.

`extensions: list[str]` — present in the schema but never populated. `StateManager.create_experiment` does not write to it (`state_manager.py:118-129`).

---

## experiment_core.json — Step Definitions and Validation Field

**File:** `plugins/scientific-method/mcp/experiment-registry/registry/experiment_core.json`

The universal base defines 5 steps in fixed order:

| Step id | required_artefacts | validation (string, not enforced) |
|---------|-------------------|----------------------------------|
| `hypothesis` | `["hypothesis.md"]` | `"contains HYPOTHESIS:, CURRENT BEHAVIOUR:, SUCCESS CRITERION:"` |
| `fixture` | `["fixture.md"]` | `"no embedded criteria or model answers"` |
| `rubric` | `["rubric.md"]` | `"min 1 binary criterion, written before baseline"` |
| `baseline` | `["output-iter0.md", "log.md"]` | `"log entry for iter0 exists"` |
| `iterate` | `["log.md"]` | `"one change per iter, regressions recorded, all criteria pass in final iter"` |

**`validation` field status:** Every step has a `validation` string. These strings describe human-readable rules for the AI to follow. The `complete_step` method in `state_manager.py` does **not read or evaluate** the `validation` field. Enforcement is implicit (AI caller reads the string via `get_current_step` and self-enforces).

**`criteria_passed` artefact (iterate step):** The `iterate` step's required_artefacts only lists `["log.md"]`, but `complete_step` also reads `artefacts.get("criteria_passed", "")` to determine loop/complete/inconclusive (`state_manager.py:238`). `criteria_passed` is not in `required_artefacts` — it is an undeclared protocol artefact consumed only by the `iterate` branch.

---

## Registry Loader — 3-Layer Merge

**File:** `plugins/scientific-method/mcp/experiment-registry/registry_loader.py`

**Discovery** (`registry_loader.py:46-49`): Loads all `*.json` files from `registry/` at `__init__` time. Explicitly excludes `registry/examples/` subdirectory.

**`merge_type(base_name, inline_extensions)`** (`registry_loader.py:152-195`) — merge order:

```text
Layer 1: experiment_core steps (always the base)
Layer 2: domain type step_extensions (applied if base_name != "experiment_core")
Layer 3: inline_extensions from start_experiment call (applied last)
```

**`_apply_extension` merge rules** (`registry_loader.py:84-119`):
- `required_artefacts` = base + `additional_artefacts` (append, not replace)
- `checklist` = base checklist + extension checklist (append)
- `human_input_required` = base value unless `ext.human_input_required is not None`
- `human_input_description` = base value unless `ext.human_input_description` is non-empty
- `validation` field is **not merged** — always inherited from the core step unchanged

**`extends` field ignored by merge logic:** `ai_agent_testing.json` declares `"extends": "experiment_core"` (`registry/ai_agent_testing.json:4`). `merge_type` does not read the `extends` field — it hardcodes `get_type("experiment_core")` as the base for all non-core types (`registry_loader.py:177`). The `extends` field is documentation only.

---

## SKILL.md Phase 2 — Execution Loop Flowchart

**File:** `plugins/scientific-method/skills/scientific-thinking/SKILL.md:48-59`

The SKILL.md defines AI-facing execution as a Mermaid flowchart with 6 stages, each gating the next:

```text
Stage 0-3: Observation       → record ONLY factual observations, no interpretation
Stage 4:   Hypothesis        → state H0 (null) and H1 (alternative), both falsifiable
Stage 5:   Prediction        → "If H1 is true, we should observe X when we do Y"
Stage 6-7: Experiment Design → define Path A (confirm H1) and Path B (refute H1)
Stage 8-9: Execute           → run exactly as designed, record results verbatim
Stage 10-11: Conclusion      → classify causality, cite evidence IDs

After conclusion:
  resolved-verified  → notify user: retrospective-analyst agent available
  unresolved/mitigated → loop back to Stage 0
```

The flowchart does **not** reference MCP tools. The SKILL.md and the MCP server are parallel execution paths — the SKILL.md governs the AI's reasoning protocol; the MCP tools manage persistent experiment state. There is no explicit wiring in SKILL.md that calls `start_experiment`, `complete_step`, etc.

**Companion skill:** `evidence-first-debugging` handles evidence IDs and observation recording. `scientific-thinking` handles hypothesis and experiment design.

---

## Existing Tests

No `tests/` directory exists anywhere under `plugins/scientific-method/`:

```text
plugins/scientific-method/
├── mcp/experiment-registry/   # No tests/ subdirectory
├── agents/
├── hooks/
├── shared/
└── skills/
```

There are no test files (`test_*.py` or `*_test.py`) in the plugin. The `pyproject.toml` (`mcp/experiment-registry/pyproject.toml`) declares no test dependencies (only `fastmcp>=3.0.0` and `pydantic>=2.0`).

---

## Where to Add New Code

**New MCP tool:** Add decorated function to `server.py`. Use `@mcp.tool()` for state-mutating tools, `@mcp.tool(annotations={"readOnlyHint": True})` for read-only tools. Convert `ValueError` to `ToolError` at the boundary.

**New experiment type:** Add a new JSON file to `registry/`. Must include `name`, `description`, and optionally `extends`, `step_extensions`, `rubric_templates`, `anti_patterns`. File is auto-discovered at server startup.

**New step in experiment_core:** Add entry to `registry/experiment_core.json` steps array. All domain types inherit the new step. Existing domain `step_extensions` only apply to steps by `id` match — new steps pass through unmodified unless domain types add matching extensions.

**New model field:** Add to the appropriate class in `models.py`. Fields with `default_factory` are backward-compatible with existing persisted state (Pydantic fills the default on load). Fields without defaults break loading of existing state files.

**Tests:** No test infrastructure exists. First test file would go in `mcp/experiment-registry/tests/` and require adding `pytest` to `pyproject.toml` dev dependencies.

**New state lifecycle operation:** Add method to `StateManager` in `state_manager.py`, then expose via a new tool in `server.py`.

---

_Architecture analysis: 2026-03-04_
