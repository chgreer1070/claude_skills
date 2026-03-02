# Architecture Spec: Plan Artifact Lifecycle Policy

**Issue**: #117
**Feature slug**: plan-artifact-lifecycle
**Created**: 2026-03-02
**Feature context**: [plan/feature-context-plan-artifact-lifecycle.md](./feature-context-plan-artifact-lifecycle.md)
**Codebase analysis**: [plan/codebase/plan-artifact-lifecycle.md](./codebase/plan-artifact-lifecycle.md)

---

## Executive Summary

This spec defines a plan artifact lifecycle policy for the SAM workflow. It classifies artifacts into two categories (human-decision and generated), adds divergence detection to quality gates, and establishes rules for when generated artifacts may be updated and when divergence must be surfaced to the human for approval.

The scope is documentation and workflow policy changes. No new Python CLI tools are created. Changes touch: workflow documentation, skill instructions, agent prompts, and task file metadata.

## Document Purpose and Boundaries

**This document specifies:**

- Artifact classification taxonomy and rules
- Divergence detection criteria and reporting format
- Modifications to existing agent prompts and skill instructions
- New quality gate phase for `/complete-implementation`
- Metadata fields to add to plan artifact headers
- Divergence recording format for `/start-task`

**This document does NOT specify:**

- New Python scripts or CLI tools
- Changes to `implementation_manager.py` or `task_status_hook.py`
- Changes to the `swarm-task-planner` or `feature-researcher` agent prompts (those are generators, not consumers of lifecycle policy)

---

## Resolved Design Questions

The feature-context identified five open questions. The human design decision resolves them as follows.

### Q1: What constitutes "divergence from human intent" versus "legitimate design refinement"?

**Resolution: Option B with reporting from Option C.**

Only changes that conflict with claims made in the human's original backlog item or grooming output require approval. Changes within the scope of generated plan artifacts (architect spec design decisions, feature-context research conclusions) are auto-recorded as annotations. All divergences are recorded and reported at `/complete-implementation`, but only intent-conflicting divergences are flagged as requiring human review.

**Rationale**: The human design decision states: "Plans may propose alternatives to the user after research/fact-checking reveals problems, but must never diverge from human intent autonomously." This means generated artifacts can evolve (they reflect research, not human decisions), but the evolution must stay within the bounds set by the human's backlog item and grooming output.

**Divergence threshold**:

| Change type | Classification | Action |
|---|---|---|
| Implementation detail differs from architect spec (e.g., different function signature, different module name) | Design refinement | Auto-record in task file. No approval needed. |
| Approach differs from architect spec but achieves same goal stated in backlog item (e.g., used Strategy B instead of Strategy A) | Design refinement | Auto-record in task file and annotate architect spec. No approval needed. |
| Scope expanded or reduced beyond what backlog item specifies | Intent divergence | Record and flag for human review. |
| Goal redefined or abandoned (e.g., backlog says "add feature X" but implementation skips it) | Intent divergence | Record and flag for human review. |
| Constraint from grooming output violated (e.g., grooming says "must be backward-compatible" but implementation breaks compatibility) | Intent divergence | Record and flag for human review. |

### Q2: Should the freshness check be a new phase or an extension of existing phases?

**Resolution: Option A -- extend Phase 6 (context-refinement).**

The `context-refinement` agent already compares planned vs implemented and produces structured output. Its scope expands from "task file Context Manifest only" to "task file Context Manifest + feature-context file + architect spec." This avoids adding a new agent, keeps the phase count at six, and leverages the agent's existing drift detection methodology.

The `doc-drift-auditor` (Phase 4) continues to audit project documentation against code. The freshness check in Phase 6 audits plan artifacts against implementation outcomes. These are complementary: Phase 4 catches documentation that no longer matches code; Phase 6 catches plans that no longer match what was built.

**Rationale**: The context-refinement agent already has the methodology (compare plan vs implementation, categorize findings, append discoveries). Extending it is less work than creating a new agent, and the agent's existing output format accommodates the additional scope.

### Q3: What should happen to existing plan artifacts?

**Resolution: Option B -- forward-only.**

The new policy applies only to artifacts created after the policy is in place. Existing artifacts in `plan/` are not retroactively modified. Existing artifacts are already known to be stale (the codebase analysis documents five concrete divergences). Retroactive classification would require re-reading and re-analyzing every existing plan against every completed implementation, with no current session benefiting from the work.

**Rationale**: The human's touch points are forward-looking. When they next run `/add-new-feature`, the new artifacts will have lifecycle metadata. Existing artifacts already serve as historical records of what was planned (not what was built), and that is acceptable given that the corresponding task files have `### Discovered During Implementation` sections appended by `context-refinement`.

### Q4: How should divergence be surfaced to the human?

**Resolution: Combination of Option A and Option D.**

1. The extended `context-refinement` agent writes a divergence report section into the task file (Option D -- inline annotation) as a `### Plan Artifact Divergence` subsection.
2. If any intent-conflicting divergences are found, the agent's DONE output includes a `DIVERGENCE_REQUIRING_REVIEW` block that the `/complete-implementation` orchestrator surfaces to the human in its final summary.
3. The workflow does NOT block (Option C rejected). The human reviews divergences after completion.

**Rationale**: The human design decision states the human has "few touch points." Blocking the workflow forces synchronous review, which conflicts with the async nature of SAM execution. Inline annotations ensure the divergence is durable (survives compaction). The orchestrator's final summary ensures the human sees it without needing to read every task file.

### Q5: Where should the policy documentation live?

**Resolution: Option C -- standalone policy document referenced from multiple locations.**

A new document at [.claude/docs/plan-artifact-lifecycle.md](./../.claude/docs/plan-artifact-lifecycle.md) defines the canonical policy. This document is referenced from:

- [.claude/rules/local-workflow.md](./../.claude/rules/local-workflow.md) (SAM workflow documentation)
- [plugins/python3-development/agents/context-refinement.md](./../plugins/python3-development/agents/context-refinement.md) (agent prompt)
- [.claude/skills/start-task/SKILL.md](./../.claude/skills/start-task/SKILL.md) (task execution skill)

**Rationale**: Sub-agents do not read `local-workflow.md`. The policy must be in the agent's own instruction file to be followed. A standalone document avoids duplicating the policy across three files -- each file references the canonical source. The standalone document is loaded on-demand when the agent reads the reference.

---

## Architecture Overview

### System Context

This feature modifies the SAM workflow at three points:

```text
/add-new-feature
  |
  |  (1) Artifact creation: generators add lifecycle metadata headers
  |      to feature-context and architect spec files
  |
  v
/implement-feature
  |
  |  (2) Task execution: /start-task agents record divergence observations
  |      in the task file when implementation deviates from plan
  |
  v
/complete-implementation
  |
  |  (3) Quality gates: extended context-refinement agent detects
  |      plan-vs-implementation divergence and classifies as
  |      "design refinement" or "intent divergence"
  |
  v
Human review of divergence findings (async, non-blocking)
```

### Component Modifications

```text
+-----------------------------------------+
| Documents to CREATE                     |
+-----------------------------------------+
| .claude/docs/plan-artifact-lifecycle.md |  <-- Canonical policy document
+-----------------------------------------+

+-----------------------------------------+
| Documents to MODIFY                     |
+-----------------------------------------+
| .claude/rules/local-workflow.md         |  <-- Add artifact lifecycle section
| .claude/skills/start-task/SKILL.md      |  <-- Add divergence recording step
| .claude/skills/complete-implementation/ |
|   SKILL.md                              |  <-- Expand Phase 6 description
| plugins/python3-development/agents/     |
|   context-refinement.md                 |  <-- Expand scope to plan artifacts
| .claude/docs/TASK_FILE_FORMAT.md        |  <-- Document divergence-note field
+-----------------------------------------+

+-----------------------------------------+
| Documents UNCHANGED                     |
+-----------------------------------------+
| implementation_manager.py               |  <-- No script changes
| task_status_hook.py                     |  <-- No hook changes
| feature-researcher.md                   |  <-- Generator, not consumer
| swarm-task-planner.md                   |  <-- Generator, not consumer
| python-cli-design-spec.md              |  <-- Generator, not consumer
| doc-drift-auditor.md                    |  <-- Complementary, not overlapping
| feature-verifier.md                     |  <-- Reads plan as ground truth (unaffected)
+-----------------------------------------+
```

---

## Artifact Classification Taxonomy

### Category 1: Human-Decision Artifacts (Immutable)

These artifacts capture the human's original intent. Agents must NEVER modify them.

| Artifact | Location | Created by |
|---|---|---|
| Backlog items | `.claude/backlog/*.md` | Human (via `/create-backlog-item`) |
| Grooming output | Embedded in backlog item under `## Groomed` | Human (via grooming session) |
| Fact-check results | Embedded in backlog item under `## Fact-Check` | Human or agent (captures human-verified facts) |
| RT-ICA assessments | Embedded in backlog item under `## RT-ICA` | Agent (captures human-approved assessment) |
| Interview transcripts | `.claude/docs/interviews/` or inline | Human |
| Human design decisions | Embedded in feature-context under `## Original Request` or backlog item | Human |

**Rules**:

1. No agent may edit, append to, or rewrite a human-decision artifact
2. Human-decision artifacts are the source of truth for intent
3. When a generated artifact references a human-decision artifact, the reference must be by path, not by transcription (transcription decouples from the source and drifts)

### Category 2: Generated Artifacts (Mutable, Intent-Bound)

These artifacts are produced by agents during `/add-new-feature` planning phases. They may be updated, but updates must stay within the intent established by human-decision artifacts.

| Artifact | Location | Created by | Updated by |
|---|---|---|---|
| Feature context | `plan/feature-context-{slug}.md` | `feature-researcher` agent | `context-refinement` agent (new scope) |
| Codebase analysis | `plan/codebase/{FOCUS}.md` | `codebase-analyzer` agent | Not updated (informational snapshot) |
| Architecture spec | `plan/architect-{slug}.md` | `python-cli-design-spec` agent | `context-refinement` agent (new scope) |
| Task plan | `plan/tasks-{N}-{slug}.md` or `plan/tasks-{slug}/` | `swarm-task-planner` agent | Status fields by hooks; Context Manifest by `context-refinement` |
| Context Manifest | Embedded in task file | `context-gathering` agent | `context-refinement` agent (existing behavior) |

**Rules**:

1. Generated artifacts may be annotated with divergence information by the `context-refinement` agent
2. Generated artifacts must NOT be silently rewritten to match implementation -- annotations are appended, not edits
3. When a generated artifact's design decision conflicts with a human-decision artifact, the divergence is classified as "intent divergence" and flagged for human review
4. Codebase analysis files are informational snapshots and are not updated. They reflect the state of the codebase at analysis time. Staleness is expected and acceptable -- they are research inputs, not living documents.

### Annotation vs Rewrite Distinction

**Annotation** (permitted): Appending a clearly demarcated section to a generated artifact that notes what changed and why. The original content remains intact. The annotation is visually distinct.

**Rewrite** (prohibited): Modifying the original content of a generated artifact to match implementation. This destroys the record of what was planned and makes it impossible to trace divergence.

---

## Lifecycle Metadata Headers

### Feature Context Files

New artifacts created by the `feature-researcher` agent will include an `artifact-type` field in their existing `## Document Metadata` section.

**Current format** (observed in existing files):

```markdown
## Document Metadata

- **Generated**: 2026-03-02
- **Input Type**: simple_description
- **Source**: Feature request description
- **Status**: DISCOVERY_COMPLETE
```

**Extended format**:

```markdown
## Document Metadata

- **Generated**: 2026-03-02
- **Input Type**: simple_description
- **Source**: Feature request description
- **Status**: DISCOVERY_COMPLETE
- **Artifact Type**: generated
- **Intent Source**: .claude/backlog/{backlog-item-file}.md
```

The `Intent Source` field links to the human-decision artifact that established the intent this generated artifact serves. This link enables the `context-refinement` agent to locate the human intent when classifying divergence.

### Architecture Spec Files

Architecture specs currently have no standardized metadata header. New specs created by `python-cli-design-spec` will include a metadata block.

**New format**:

```markdown
# Architecture Spec: {Feature Title}

**Issue**: #{number}
**Feature slug**: {slug}
**Created**: {date}
**Artifact Type**: generated
**Intent Source**: .claude/backlog/{backlog-item-file}.md
**Feature context**: plan/feature-context-{slug}.md
**Codebase analysis**: plan/codebase/{focus}.md (if applicable)
```

### Codebase Analysis Files

These already have an `**Analysis Date:**` header. No changes needed. Their artifact type is implicitly "generated, informational snapshot" and they are not subject to freshness checking.

---

## Divergence Recording During Task Execution

### `/start-task` Modification

The `/start-task` skill gains a new step between step 5 (write active-task context file) and step 6 (implement against acceptance criteria).

**New step 5a: Note divergence observations.**

During implementation, when the agent discovers that the architect spec or feature-context describes something that does not match what the agent is implementing, the agent appends a divergence note to the task file.

**Divergence note format** (appended as a markdown section in the task body):

```markdown
## Divergence Notes

### DN-1: {Brief title}

- **Plan artifact**: plan/architect-{slug}.md, section "{section name}"
- **Plan claim**: "{quoted text from plan artifact}"
- **Actual implementation**: "{what was actually done and why}"
- **Classification**: design-refinement | intent-divergence
- **Recorded**: {ISO timestamp}
```

The `Classification` field is the agent's assessment. The `context-refinement` agent validates this classification during `/complete-implementation` by comparing the divergence against the human-decision artifact referenced in the plan's `Intent Source` field.

### When to Record a Divergence Note

The agent records a divergence note when ALL of these conditions hold:

1. The agent is implementing something that differs from what the architect spec or feature-context describes
2. The difference is not a trivial implementation detail (e.g., different variable name, different import path)
3. The difference affects the observable behavior, structure, or scope of the feature

The agent does NOT record a divergence note for:

- Implementation choices not addressed by the plan (the plan is silent on the topic)
- Standard coding patterns or style choices
- Bug fixes in the plan's own inconsistencies (e.g., the plan references a non-existent API -- the fix is obvious)

### Task File Format Extension

The `divergence-notes` field is added to the YAML frontmatter optional fields in [.claude/docs/TASK_FILE_FORMAT.md](./../.claude/docs/TASK_FILE_FORMAT.md).

**New optional field**:

| Field | Type | Description | Example |
|---|---|---|---|
| `divergence-notes` | integer | Count of divergence notes in the task body | `2` |

This field is a count, not the notes themselves. The notes live in the markdown body under `## Divergence Notes`. The count in frontmatter enables the `context-refinement` agent to quickly identify which tasks recorded divergences without parsing every task body.

**JSON schema addition**:

```json
{
  "divergence-notes": {
    "type": "integer",
    "minimum": 0,
    "default": 0,
    "description": "Count of divergence notes recorded during implementation"
  }
}
```

---

## Extended Context-Refinement Agent

### Current Scope (Unchanged)

The `context-refinement` agent currently:

1. Reads the task file and architecture spec
2. Compares planned vs implemented for the task's Context Manifest
3. Appends `### Discovered During Implementation` if drift found
4. Outputs `RECOMMENDED DOCUMENTATION UPDATES` for architecture.md changes

All of this behavior is preserved.

### New Scope: Plan Artifact Freshness Check

After completing the existing Context Manifest update (or determining no update needed), the agent performs a plan artifact freshness check.

**New steps (appended to existing process)**:

**Step 5: Locate Plan Artifacts and Intent Source**

1. Read the feature-context file path from the task file or architecture spec header
2. Read the architecture spec file path from the task file header
3. Read the `Intent Source` path from the feature-context or architecture spec header to locate the human-decision artifact

If `Intent Source` is absent (pre-policy artifact), skip intent-divergence classification -- treat all divergences as design-refinement.

**Step 6: Collect Divergence Evidence**

1. Read all task files for the feature (all tasks, not just the current one)
2. Collect all `## Divergence Notes` sections from task bodies
3. Collect all `### Discovered During Implementation` sections from Context Manifests
4. Compare key claims in the architecture spec against the actual implementation files

**Step 7: Classify Divergences**

For each divergence found:

1. If `Intent Source` is available, read the human-decision artifact
2. Compare the divergence against the human's stated intent (scope, goals, constraints)
3. Apply the divergence threshold table from Q1 resolution above
4. Classify as `design-refinement` or `intent-divergence`

**Step 8: Annotate Plan Artifacts**

If divergences were found:

1. Append a `## Post-Implementation Annotations` section to `plan/feature-context-{slug}.md`
2. Append a `## Post-Implementation Annotations` section to `plan/architect-{slug}.md`

**Annotation format**:

```markdown
## Post-Implementation Annotations

_Added by context-refinement agent on {date}_

### Design Refinements

1. **{Title}**: {Description of what changed and why}
   - Original: "{quoted from plan}"
   - Actual: "{what was implemented}"
   - Recorded in: {task file path}, DN-{N}

### Intent Divergences Requiring Review

1. **{Title}**: {Description of how implementation diverges from human intent}
   - Human intent: "{quoted from backlog item or grooming output}"
   - Actual: "{what was implemented}"
   - Recorded in: {task file path}, DN-{N}
   - **Action needed**: Human review required
```

If no intent divergences were found, the `### Intent Divergences Requiring Review` subsection is omitted.

### Updated Output Format

The agent's DONE output gains a new section.

**When no divergence requiring review**:

```text
STATUS: DONE
SUMMARY: Context manifest updated with [N] discoveries. Plan artifact freshness check found [M] design refinements, 0 intent divergences.
ARTIFACTS:
  - Updated task file: [path]
  - Annotated feature context: [path] (if annotated)
  - Annotated architect spec: [path] (if annotated)
RISKS:
  - [Any patterns that may need architecture.md updates]
NOTES:
  - [Summary]
```

**When intent divergence found**:

```text
STATUS: DONE
SUMMARY: Context manifest updated. Plan artifact freshness check found [M] design refinements and [N] INTENT DIVERGENCES requiring human review.
ARTIFACTS:
  - Updated task file: [path]
  - Annotated feature context: [path]
  - Annotated architect spec: [path]
DIVERGENCE_REQUIRING_REVIEW:
  1. [Title]: [Brief description]
     - Human intent: [quoted]
     - Actual: [description]
     - Task: [task file path]
  2. ...
RISKS:
  - Intent divergence detected -- human review needed before feature is considered complete
NOTES:
  - [Summary]
```

---

## Modified `/complete-implementation` Skill

### Phase 6 Update

Phase 6 description changes from:

> Launch `context-refinement` to update the task file Context Manifest with discoveries from implementation (only if needed).

To:

> Launch `context-refinement` to update the task file Context Manifest with discoveries from implementation AND perform plan artifact freshness check against feature-context and architect spec. If `DIVERGENCE_REQUIRING_REVIEW` is present in the agent's output, include it in the final summary to the human.

### Orchestrator Post-Phase-6 Behavior

After Phase 6 completes, the `/complete-implementation` orchestrator checks the `context-refinement` agent's output for `DIVERGENCE_REQUIRING_REVIEW`.

```text
If DIVERGENCE_REQUIRING_REVIEW present:
  Include in orchestrator's final output to the human:
    "Plan artifacts have intent divergences requiring your review.
     See: [annotated artifact paths]
     Divergences:
       [list from agent output]"

If DIVERGENCE_REQUIRING_REVIEW absent:
  No additional output. Feature proceeds normally.
```

This is informational, not blocking. The human reviews at their discretion.

---

## Policy Document: `.claude/docs/plan-artifact-lifecycle.md`

This is the canonical policy document. Its structure and content are specified below. Implementation agents write the actual file.

### Required Sections

1. **Purpose and Scope**: Why this policy exists, what it covers
2. **Artifact Classification**: The two-category taxonomy with tables from this spec
3. **Rules for Human-Decision Artifacts**: Immutability rules (3 rules from taxonomy above)
4. **Rules for Generated Artifacts**: Mutability rules (4 rules from taxonomy above)
5. **Divergence Detection**: When and how divergence is detected
6. **Divergence Classification**: The threshold table from Q1 resolution
7. **Divergence Recording**: The divergence note format for `/start-task`
8. **Divergence Reporting**: How findings are surfaced at `/complete-implementation`
9. **Backward Compatibility**: Forward-only policy, existing artifacts unaffected

### Cross-References

The policy document references:

- [.claude/rules/local-workflow.md](./../.claude/rules/local-workflow.md) -- for SAM workflow context
- [.claude/docs/TASK_FILE_FORMAT.md](./../.claude/docs/TASK_FILE_FORMAT.md) -- for task file schema
- [.claude/skills/start-task/SKILL.md](./../.claude/skills/start-task/SKILL.md) -- for divergence recording trigger
- [plugins/python3-development/agents/context-refinement.md](./../plugins/python3-development/agents/context-refinement.md) -- for freshness check agent

---

## Modifications to `local-workflow.md`

### New Section: Plan Artifact Lifecycle

Add a new section between the existing "Phase 1: Planning" and "Phase 2: Execution" sections (or as a standalone section after the Data Flow Diagram). The section documents:

1. The artifact classification taxonomy (reference to `.claude/docs/plan-artifact-lifecycle.md`)
2. The lifecycle table showing which artifacts are mutable vs immutable
3. The divergence detection mechanism
4. How the existing Phase 6 now includes plan artifact freshness checking

### Updated Artifacts Produced Table

The existing "Artifacts Produced" table in Phase 1 gains an `Artifact Type` column:

| Artifact | Path | Created By | Artifact Type |
|---|---|---|---|
| Feature context | `plan/feature-context-{slug}.md` | `feature-researcher` agent | Generated |
| Codebase analysis | `plan/codebase/{FOCUS}.md` | `codebase-analyzer` agent (optional) | Generated (snapshot) |
| Architecture spec | `plan/architect-{slug}.md` | `python-cli-design-spec` agent | Generated |
| Task plan | `plan/tasks-{N}-{slug}.md` | `swarm-task-planner` agent | Generated |

### Updated Phase Sequence

The Phase 3 quality gate sequence description for Phase 6 changes to:

```text
Phase 6: context-refinement     -> Update task file Context Manifest + plan artifact freshness check
```

### Updated Data Flow Diagram

The `/complete-implementation` section of the data flow diagram gains:

```text
  └─ context-refinement        ──> updated Context Manifest
                                ──> plan artifact annotations (if divergence found)
                                ──> DIVERGENCE_REQUIRING_REVIEW (if intent divergence)
```

---

## Modifications to `/start-task` SKILL.md

### New Step 5a

Insert between existing step 5 (write active-task context file) and step 6 (implement against acceptance criteria).

**Step 5a: Record divergence observations during implementation.**

While implementing (step 6), if you discover that the architect spec or feature-context describes something that does not match what you are implementing, append a divergence note to the task file under a `## Divergence Notes` section.

Reference the divergence note format and recording criteria from the plan artifact lifecycle policy at [.claude/docs/plan-artifact-lifecycle.md](./../.claude/docs/plan-artifact-lifecycle.md).

Update the `divergence-notes` count in YAML frontmatter (or add `**Divergence Notes**: {count}` in legacy format) after appending each note.

---

## Modifications to `context-refinement.md` Agent Prompt

### Expanded Scope Declaration

The agent's `## YOUR MISSION` section changes from:

> Check IF context has drifted or new discoveries were made during the implementation session. Only update the context manifest if changes are needed.

To:

> Check IF context has drifted or new discoveries were made during the implementation session. Update the context manifest if changes are needed. Then perform a plan artifact freshness check: compare the feature-context and architect spec against the actual implementation to detect and classify divergences as design-refinement or intent-divergence.

### New Steps (Appended)

Steps 5-8 from the "Extended Context-Refinement Agent" section of this spec are added to the agent prompt after the existing Step 4.

### New Output Section

The `DIVERGENCE_REQUIRING_REVIEW` output block format is added to the agent's output format section.

### Reference to Policy

The agent prompt includes a reference to the canonical policy document:

> For artifact classification rules, divergence thresholds, and annotation format, see [.claude/docs/plan-artifact-lifecycle.md](./../docs/plan-artifact-lifecycle.md).

---

## Backward Compatibility

### Existing Plan Artifacts

No changes to existing files in `plan/`. Existing feature-context files, architect specs, and task files continue to work as before. They lack `Artifact Type` and `Intent Source` metadata, which means:

- The `context-refinement` agent treats missing `Intent Source` as "skip intent-divergence classification"
- All divergences in pre-policy artifacts are classified as `design-refinement` (safe default)
- No retroactive annotations are added

### Existing Task Files

The `divergence-notes` field is optional with a default of 0. Existing task files without this field are unaffected. The `implementation_manager.py` parser ignores unknown fields (documented in TASK_FILE_FORMAT.md), so the new field does not require parser changes.

### Existing Agent Behavior

- `feature-verifier` continues to read plan artifacts as ground truth for goal verification. Post-implementation annotations do not change the original content -- they are appended sections that the verifier can distinguish from the original plan.
- `doc-drift-auditor` continues to audit project documentation against code. Its scope does not overlap with plan artifact freshness checking.

---

## Testing Strategy

Since this feature produces documentation and workflow policy changes (not code), testing is verification-based rather than test-suite-based.

### Verification Approach

1. **Policy document completeness**: Verify `.claude/docs/plan-artifact-lifecycle.md` contains all nine required sections from this spec
2. **Agent prompt correctness**: Verify `context-refinement.md` includes the new steps (5-8) and the `DIVERGENCE_REQUIRING_REVIEW` output block
3. **Skill instruction correctness**: Verify `/start-task` SKILL.md includes step 5a with reference to the policy document
4. **Workflow documentation correctness**: Verify `local-workflow.md` includes the artifact lifecycle section and updated phase sequence
5. **Schema correctness**: Verify `TASK_FILE_FORMAT.md` includes the `divergence-notes` field in the optional fields table and JSON schema
6. **Cross-reference integrity**: Verify all file references in the policy document, agent prompt, and skill instructions point to existing files
7. **Backward compatibility**: Verify existing task files without `divergence-notes` field still parse correctly (run `uv run {implementation_manager.py} validate . {existing-slug}` against an existing feature)

### Acceptance Criteria

1. `.claude/docs/plan-artifact-lifecycle.md` exists with all required sections
2. `context-refinement.md` agent prompt includes plan artifact freshness check steps
3. `/start-task` SKILL.md includes divergence recording step (5a)
4. `/complete-implementation` SKILL.md Phase 6 description references plan artifact freshness check
5. `local-workflow.md` includes artifact lifecycle section with classification taxonomy
6. `TASK_FILE_FORMAT.md` includes `divergence-notes` optional field
7. Running `uv run {implementation_manager.py} validate . plugin-linter` succeeds (backward compatibility)

---

## File Inventory

### Files to Create

| File | Purpose |
|---|---|
| `.claude/docs/plan-artifact-lifecycle.md` | Canonical lifecycle policy document |

### Files to Modify

| File | Change |
|---|---|
| `.claude/rules/local-workflow.md` | Add artifact lifecycle section, update artifacts table, update phase sequence, update data flow diagram |
| `.claude/skills/start-task/SKILL.md` | Add step 5a (divergence recording) |
| `.claude/skills/complete-implementation/SKILL.md` | Update Phase 6 description, add post-Phase-6 divergence surfacing |
| `plugins/python3-development/agents/context-refinement.md` | Add steps 5-8, add DIVERGENCE_REQUIRING_REVIEW output block, add policy reference |
| `.claude/docs/TASK_FILE_FORMAT.md` | Add `divergence-notes` to optional fields table and JSON schema |

### Files Unchanged

| File | Reason |
|---|---|
| `plugins/python3-development/skills/implementation-manager/scripts/implementation_manager.py` | No script changes needed; parser ignores unknown fields |
| `plugins/python3-development/skills/implementation-manager/scripts/task_status_hook.py` | No hook changes needed |
| `plugins/python3-development/agents/feature-researcher.md` | Generator agent; lifecycle metadata added to template, not agent logic |
| `plugins/python3-development/agents/swarm-task-planner.md` | Generator agent; unchanged |
| `plugins/python3-development/agents/python-cli-design-spec.md` | Generator agent; metadata header is template guidance, not agent logic change |
| `plugins/python3-development/agents/doc-drift-auditor.md` | Complementary scope; no overlap |
| `plugins/python3-development/agents/feature-verifier.md` | Reads plan as ground truth; annotations are appended, not edits |

---

## References

- Feature context: [plan/feature-context-plan-artifact-lifecycle.md](./feature-context-plan-artifact-lifecycle.md)
- Codebase analysis: [plan/codebase/plan-artifact-lifecycle.md](./codebase/plan-artifact-lifecycle.md)
- SAM workflow: [.claude/rules/local-workflow.md](./../.claude/rules/local-workflow.md)
- Task file format: [.claude/docs/TASK_FILE_FORMAT.md](./../.claude/docs/TASK_FILE_FORMAT.md)
- Context-refinement agent: [plugins/python3-development/agents/context-refinement.md](./../plugins/python3-development/agents/context-refinement.md)
- Start-task skill: [.claude/skills/start-task/SKILL.md](./../.claude/skills/start-task/SKILL.md)
- Complete-implementation skill: [.claude/skills/complete-implementation/SKILL.md](./../.claude/skills/complete-implementation/SKILL.md)
- Doc-drift-auditor agent: [plugins/python3-development/agents/doc-drift-auditor.md](./../plugins/python3-development/agents/doc-drift-auditor.md)
- Feature-verifier agent: [plugins/python3-development/agents/feature-verifier.md](./../plugins/python3-development/agents/feature-verifier.md)
- Backlog item: [.claude/backlog/p2-plan-artifact-diverges-from-implementation-without-update-me.md](./../.claude/backlog/p2-plan-artifact-diverges-from-implementation-without-update-me.md)
