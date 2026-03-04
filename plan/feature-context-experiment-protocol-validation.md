# Feature Context: Experiment Protocol Validation

## Document Metadata

- **Generated**: 2026-03-04
- **Input Type**: simple_description
- **Source**: Issue #431 - Experiment protocol validation gaps
- **Status**: DISCOVERY_COMPLETE

---

## Original Request

The experiment-registry MCP server (plugins/scientific-method/) checks artefact key presence but never validates content, file existence, or artefact integrity. 8 gaps identified spanning content validation, trust-based self-reporting, freeze enforcement, rubric locking, iteration log validation, output tracking, phantom path detection, and SKILL.md flowchart terminal-state guard. Success means the MCP mechanically enforces the methodology it claims to enforce.

---

## Core Intent Analysis

### WHO (Target Users)

AI agents (Claude) running controlled experiments via the `/experiment-protocol` skill and the experiment-registry MCP server. The human user is the experiment designer who relies on the MCP to prevent methodology violations.

### WHAT (Desired Outcome)

The MCP server rejects invalid experiment state transitions instead of accepting them silently. Specifically: empty artefacts are rejected, file paths are verified to exist, frozen artefacts (fixture, rubric, task-prompt) cannot be silently modified between iterations, rubric scores must be structured data rather than a trust-based string self-report, and iteration outputs are tracked per-iteration.

### WHEN (Trigger Conditions)

Every call to `complete_step()` -- the MCP should validate artefact content and integrity at each step transition, not just check key presence. Additionally, during the `iterate` loop, frozen artefact integrity should be verified before allowing the iteration to proceed.

### WHY (Problem Being Solved)

The experiment-registry MCP server currently enforces methodology in name only. The `validation` field in `experiment_core.json` is decorative text never read by any code. The `criteria_passed` artefact is a string self-report (`"true"`) with no independent verification. Frozen artefacts have no content hashes, so Claude can silently modify them between iterations without detection. This means experiment results produced through this system have no mechanical integrity guarantee -- the system trusts the caller to follow rules it was built to enforce.

---

## Codebase Research

### Similar Patterns Found

#### Pattern 1: Artefact key-only validation in complete_step

- **Location**: `plugins/scientific-method/mcp/experiment-registry/state_manager.py:216`
- **Relevance**: This is the core validation logic. Line 216 checks `if a not in artefacts` -- pure key presence check. The artefact values (content) are never inspected. An empty string passes validation.
- **Reusable**: The `complete_step` method is the single enforcement point where all content validation would need to occur.

#### Pattern 2: Decorative validation field in experiment_core.json

- **Location**: `plugins/scientific-method/mcp/experiment-registry/registry/experiment_core.json:9`
- **Relevance**: Each step has a `validation` string field (e.g., `"contains HYPOTHESIS:, CURRENT BEHAVIOUR:, SUCCESS CRITERION:"` for the hypothesis step). This field is loaded into `StepDefinition.validation` (models.py:20) and returned by `inspect_experiment_type` (server.py:89) and `get_current_step` (server.py:245), but no code ever evaluates or enforces it.
- **Reusable**: The validation field already contains human-readable validation rules. These could become the specification for actual enforcement logic.

#### Pattern 3: Trust-based criteria_passed in iterate step

- **Location**: `plugins/scientific-method/mcp/experiment-registry/state_manager.py:238`
- **Relevance**: Line 238: `criteria_passed = artefacts.get("criteria_passed", "").lower() == "true"`. The iterate step completes successfully when the caller self-reports `criteria_passed: "true"`. The MCP does not independently verify that rubric criteria were scored or that scores actually pass.
- **Reusable**: The iterate step logic at lines 236-257 is the control point for iteration loop behavior.

#### Pattern 4: No hash tracking on frozen artefacts

- **Location**: `plugins/scientific-method/mcp/experiment-registry/models.py:68`
- **Relevance**: `ExperimentState.artefacts` is `dict[str, str]` -- flat key-value pairs with no content hashing, no freeze timestamps, no immutability tracking. The `experiment_core.json` checklist states "File is frozen -- will not be edited after baseline" (line 22) but no code enforces this.
- **Reusable**: The `ExperimentState` model is the persistence layer where hash fields and freeze metadata would need to live.

#### Pattern 5: Phase 2 flowchart lacks terminal-state guard

- **Location**: `plugins/scientific-method/skills/experiment-protocol/SKILL.md:50-64`
- **Relevance**: The Phase 2 flowchart enters the execution loop at `GetStep` without checking whether the experiment status is already `complete` or `inconclusive`. If `get_current_step()` is called on a terminal-state experiment, the behavior depends on whether the `current_step` field still points to a valid step definition.
- **Reusable**: The flowchart is the caller-side guidance. The MCP server-side should also reject `complete_step` calls on terminal-state experiments.

### Existing Infrastructure

- **Pydantic models** (`models.py`): All state and step definitions are Pydantic `BaseModel` subclasses. Validation logic can be added as Pydantic validators or as explicit checks in `StateManager`.
- **Registry JSON schema** (`experiment_core.json`): Already contains `validation` strings and `checklist` arrays per step. These define what should be validated but are currently unenforced.
- **Step extension merge system** (`registry_loader.py:83-119`): Extensions can add `additional_artefacts` and `checklist` items per step, which means any validation system must work with the merged step definitions, not just core definitions.
- **State persistence** (`state_manager.py:56-64`): State is serialized as JSON via `model_dump_json`. Adding new fields to `ExperimentState` will persist automatically.

### Code References

- `state_manager.py:216` - artefact key-only check: `missing = [a for a in current_def.required_artefacts if a not in artefacts]`
- `state_manager.py:238` - trust-based criteria_passed: `criteria_passed = artefacts.get("criteria_passed", "").lower() == "true"`
- `state_manager.py:229` - blind artefact merge: `state.artefacts.update(artefacts)` (overwrites previous values without freeze check)
- `models.py:20` - validation field exists but unused: `validation: str = ""`
- `models.py:68` - artefacts storage has no hash tracking: `artefacts: dict[str, str] = Field(default_factory=dict)`
- `experiment_core.json:9` - validation text for hypothesis step (decorative)
- `experiment_core.json:18` - validation text for fixture step (decorative)
- `experiment_core.json:22` - checklist claims fixture is frozen (unenforced)
- `experiment_core.json:52` - iterate step requires only `log.md`, not per-iteration output
- `SKILL.md:50-64` (experiment-protocol) - Phase 2 flowchart missing terminal-state guard

---

## Use Scenarios

### Scenario 1: Empty artefact passes validation

**Actor**: AI agent completing the hypothesis step
**Trigger**: Agent calls `complete_step("exp-id", "hypothesis", {"hypothesis.md": ""})`
**Goal**: MCP should reject an empty hypothesis artefact
**Expected Outcome**: Currently succeeds silently. Should return `{"success": false, "reason": "artefact 'hypothesis.md' is empty"}`

### Scenario 2: Self-reported criteria passage without scoring

**Actor**: AI agent completing an iterate step
**Trigger**: Agent calls `complete_step("exp-id", "iterate", {"log.md": "...", "criteria_passed": "true"})` without having scored rubric criteria
**Goal**: MCP should verify rubric criteria were individually scored before accepting criteria_passed
**Expected Outcome**: Currently accepts `criteria_passed: "true"` at face value. Should require structured scoring data (per-criterion pass/fail) that the MCP can independently verify.

### Scenario 3: Frozen artefact modified between iterations

**Actor**: AI agent in iteration 3 of an experiment
**Trigger**: Agent modifies fixture.md on disk between iterations, then calls `complete_step` for the next iterate step
**Goal**: MCP should detect that a frozen artefact has been modified since baseline
**Expected Outcome**: Currently undetectable. Should compare content hashes of frozen artefacts (fixture, rubric, task-prompt) against baseline hashes and reject if changed.

### Scenario 4: Phantom artefact path reaches retrospective

**Actor**: AI agent completing an experiment, handing off to retrospective-analyst
**Trigger**: Agent submits artefact paths that do not exist on disk
**Goal**: MCP should verify that artefact file paths actually exist before accepting them
**Expected Outcome**: Currently accepts any string value. Should verify file existence for artefacts that are file paths (e.g., `hypothesis.md`, `fixture.md`).

### Scenario 5: Iteration output not captured

**Actor**: AI agent running iteration 4 of an experiment
**Trigger**: Agent calls `complete_step` for iterate with only `log.md` (no `output-iter4.md`)
**Goal**: Each iteration should have a corresponding output snapshot
**Expected Outcome**: Currently requires only `log.md` per the iterate step definition. Baseline requires `output-iter0.md` but iterate does not require `output-iterN.md`.

---

## Gap Analysis

### Identified Gaps

| # | Category | Gap Description | Impact |
|---|----------|-----------------|--------|
| 1 | Behavior | No content validation -- empty artefacts pass | Experiments proceed with vacuous artefacts, producing meaningless results |
| 2 | Behavior | No file existence check on artefact paths | Phantom paths reach retrospective-analyst, causing analysis failures |
| 3 | Behavior | criteria_passed is trust-based string self-report | Experiment completion has no independent verification -- the enforcer trusts the subject |
| 4 | Behavior | No freeze enforcement on fixture/rubric/task-prompt | Frozen artefacts can be silently modified, invalidating controlled experiment design |
| 5 | Behavior | Rubric modifiable post-creation (no hash lock) | Rubric criteria can be changed after seeing baseline output, violating pre-registration principle |
| 6 | Behavior | Iteration log content not validated | Selective reporting (omitting regressions) is undetectable |
| 7 | Scope | No per-iteration output-iterN.md tracking | Iterate step requires only log.md, baseline requires output-iter0.md -- asymmetry |
| 8 | Integration | SKILL.md Phase 2 flowchart missing terminal-state guard | Caller can enter execution loop on completed/inconclusive experiment |

---

## Questions Requiring Resolution

### Q1: What constitutes valid artefact content?

- **Category**: Behavior
- **Gap**: Gap 1 -- validation field is decorative text, not machine-evaluable rules
- **Question**: Should the `validation` strings in `experiment_core.json` be converted to machine-evaluable rules (e.g., regex patterns, required section headers), or should validation be limited to non-empty + file-exists checks?
- **Options**:
  - A) Minimal validation: non-empty content + file existence
  - B) Structured validation: parse the existing `validation` strings into enforceable rules (e.g., hypothesis.md must contain `HYPOTHESIS:`, `CURRENT BEHAVIOUR:`, `SUCCESS CRITERION:` headers)
- **Why It Matters**: Option B provides stronger guarantees but requires defining a validation rule format and parser. Option A is simpler but still allows structurally invalid artefacts.
- **Resolution**: _pending_

### Q2: What structured scoring format should replace criteria_passed?

- **Category**: Behavior
- **Gap**: Gap 3 -- criteria_passed is a trust-based string
- **Question**: What should the structured scoring data look like when completing an iterate step? Should it be per-criterion pass/fail results that the MCP verifies against the rubric, or a different format?
- **Options**:
  - A) Per-criterion JSON: `{"rubric_scores": {"criterion_1": true, "criterion_2": false}}` -- MCP verifies all rubric criteria are present
  - B) Scored rubric file: require `scored-rubric-iterN.md` as an artefact containing structured scores -- MCP verifies the file exists and contains all criteria
- **Why It Matters**: This determines whether rubric verification happens inside the MCP (option A, MCP needs rubric awareness) or via artefact structure (option B, MCP validates file format).
- **Resolution**: _pending_

### Q3: Which artefacts should be frozen and when?

- **Category**: Scope
- **Gap**: Gaps 4 and 5 -- no freeze enforcement
- **Question**: The checklist says fixture is frozen after baseline. Should rubric also be frozen after creation? Should the task-prompt (if used) be frozen? At which step does freezing take effect?
- **Options**:
  - A) Freeze fixture + rubric + task-prompt after baseline step completes
  - B) Freeze each artefact at the step that produces it (rubric frozen after rubric step, fixture after fixture step)
- **Why It Matters**: Option A is simpler (one freeze point) but allows rubric modification during baseline. Option B is stricter but matches the existing step-ordering intent (rubric must be written before baseline).
- **Resolution**: _pending_

### Q4: Should artefact values be file paths or inline content?

- **Category**: Behavior
- **Gap**: Gap 2 -- no file existence check
- **Question**: Currently `artefacts` is `dict[str, str]` where values are opaque strings. Are values always file paths (relative to experiment dir), always inline content, or mixed? This determines whether file existence checking is applicable.
- **Options**:
  - A) Values are always file paths -- MCP reads and validates file content
  - B) Values are always inline content -- MCP validates content directly
  - C) Mixed -- some artefacts are paths, some are inline (requires a convention to distinguish)
- **Why It Matters**: File-path semantics enable file existence checks and content hashing. Inline content semantics enable direct content validation. The current code treats values as opaque strings with no convention.
- **Resolution**: _pending_

### Q5: Should iterate require per-iteration output snapshots?

- **Category**: Scope
- **Gap**: Gap 7 -- no per-iteration output tracking
- **Question**: The baseline step requires `output-iter0.md` but the iterate step requires only `log.md`. Should iterate also require `output-iterN.md` where N is the current iteration count?
- **Options**:
  - A) Yes -- require `output-iterN.md` for every iteration (enables diffing between iterations)
  - B) No -- keep iterate requiring only `log.md` (output capture is the caller's responsibility)
- **Why It Matters**: Per-iteration output snapshots enable the MCP to detect selective reporting and provide richer data to retrospective-analyst. But they add overhead to every iteration.
- **Resolution**: _pending_

---

## Goals (Pending Resolution)

_These goals will be finalized after questions are resolved._

1. `complete_step` rejects artefacts with empty content (non-empty validation)
2. `complete_step` verifies file existence for artefacts that are file paths
3. `complete_step("iterate")` requires structured rubric scoring data instead of self-reported `criteria_passed: "true"`
4. Frozen artefacts (fixture, rubric) are hash-locked after their freeze point -- subsequent `complete_step` calls verify hashes match
5. Iteration log content is validated for structural completeness (at minimum, non-empty)
6. Per-iteration output tracking is enforced or documented as caller responsibility
7. SKILL.md Phase 2 flowchart includes terminal-state guard before entering execution loop
8. All 8 identified gaps have corresponding fixes

---

## Next Steps

After questions are resolved:

1. Update "Resolution" fields in Questions section
2. Finalize Goals section
3. Proceed to RT-ICA assessment
4. Then proceed to architecture design
