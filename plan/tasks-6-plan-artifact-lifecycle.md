---
feature: plan-artifact-lifecycle
issue: 117
created: 2026-03-02
architecture-spec: plan/architect-plan-artifact-lifecycle.md
feature-context: plan/feature-context-plan-artifact-lifecycle.md
---

# Tasks: Plan Artifact Lifecycle Policy (Issue #117)

Six tasks implement the plan artifact lifecycle policy from
[plan/architect-plan-artifact-lifecycle.md](./architect-plan-artifact-lifecycle.md).
All changes are documentation and workflow policy only. No Python scripts are created or modified.

## Dependency Graph

```text
T1 (policy doc) ──────────────────────────────────────┐
                                                       │
T6 (TASK_FILE_FORMAT.md schema) ── no deps            │
                                                       ▼
                 T2 (local-workflow.md) ◄── T1
                 T3 (start-task SKILL.md) ◄── T1
                 T5 (context-refinement.md) ◄── T1
                                                 │
                                                 ▼
                              T4 (complete-implementation SKILL.md) ◄── T5
```

Parallel execution opportunities:

- T1 and T6 can start immediately (no dependencies)
- T2, T3, and T5 can start in parallel after T1 completes
- T4 must wait for T5 to complete

---

## Task T1: Create plan-artifact-lifecycle.md Policy Document

```yaml
---
task: T1
title: Create plan-artifact-lifecycle.md policy document
status: not-started
agent: general-purpose
dependencies: []
priority: 1
complexity: medium
accuracy-risk: low
parallelize-with: [T6]
reason: T1 and T6 write to different files with no overlap
handoff: >
  Report: file created at .claude/docs/plan-artifact-lifecycle.md,
  confirm all 9 required sections present, confirm all cross-reference
  paths resolve to existing files.
---
```

## Context

This task was planned as a standalone creation task. The policy document is the canonical
reference for the artifact lifecycle policy. All other tasks in this plan reference it.

The architecture spec defines the required content at
[plan/architect-plan-artifact-lifecycle.md](./architect-plan-artifact-lifecycle.md),
sections "Policy Document" and "Artifact Classification Taxonomy".

## Objective

Create `.claude/docs/plan-artifact-lifecycle.md` containing the canonical plan artifact
lifecycle policy with all nine required sections as specified in the architecture spec.

## Required Inputs

- [plan/architect-plan-artifact-lifecycle.md](./architect-plan-artifact-lifecycle.md) —
  primary source: sections "Policy Document: Required Sections",
  "Artifact Classification Taxonomy", "Resolved Design Questions", "Divergence Recording",
  "Extended Context-Refinement Agent", "Backward Compatibility"
- [.claude/docs/TASK_FILE_FORMAT.md](../.claude/docs/TASK_FILE_FORMAT.md) — to reference
  correctly in cross-references section
- [.claude/skills/start-task/SKILL.md](../.claude/skills/start-task/SKILL.md) — to confirm
  correct path for cross-reference
- [plugins/python3-development/agents/context-refinement.md](../plugins/python3-development/agents/context-refinement.md)
  — to confirm correct path for cross-reference

## Requirements

1. Create the file at `/home/user/claude_skills/.claude/docs/plan-artifact-lifecycle.md`
2. Include all nine required sections in this order:
   1. Purpose and Scope
   2. Artifact Classification (two-category taxonomy with tables)
   3. Rules for Human-Decision Artifacts (3 rules)
   4. Rules for Generated Artifacts (4 rules)
   5. Divergence Detection (when and how divergence is detected)
   6. Divergence Classification (the threshold table from Q1 resolution)
   7. Divergence Recording (divergence note format for `/start-task`)
   8. Divergence Reporting (how findings surface at `/complete-implementation`)
   9. Backward Compatibility (forward-only policy, existing artifacts unaffected)
3. Include the human-decision artifacts table (backlog items, grooming output,
   fact-check results, RT-ICA assessments, interview transcripts, human design decisions)
4. Include the generated artifacts table (feature context, codebase analysis, architecture
   spec, task plan, Context Manifest) with Created By and Updated By columns
5. Include the divergence threshold classification table (5 rows: implementation detail
   differs, approach differs but same goal, scope expanded/reduced, goal redefined/abandoned,
   constraint violated)
6. Include the divergence note format block (DN-N, plan artifact, plan claim, actual
   implementation, classification, recorded timestamp)
7. Include the DIVERGENCE_REQUIRING_REVIEW output block format as it will appear in
   context-refinement output
8. Include the Annotation vs Rewrite Distinction section
9. Use relative markdown links starting with `./` for all cross-references
10. Add language specifiers to all code fences
11. Surround all fenced code blocks with blank lines

## Constraints

- Do not create a Python script or tool — this is documentation only
- Do not modify any existing file in this task
- Do not add content not derived from the architecture spec
- All cross-reference paths must point to files that exist in the repository
- Do not use `@` or `/` skill reference prefixes in prose — use markdown links to the
  actual files

## Expected Outputs

- File created: `/home/user/claude_skills/.claude/docs/plan-artifact-lifecycle.md`

## Acceptance Criteria

1. File exists at `/home/user/claude_skills/.claude/docs/plan-artifact-lifecycle.md`
2. All nine required sections are present (readable with `Read` tool and confirmed by
   section heading search)
3. The human-decision artifacts table contains all six artifact types listed in the spec
4. The generated artifacts table contains all five artifact types with Created By and
   Updated By columns
5. The divergence threshold table contains all five change-type rows
6. The divergence note format block shows `DN-N`, `plan artifact`, `plan claim`,
   `actual implementation`, `classification`, and `recorded` fields
7. All relative markdown links use `./` prefix and point to files that exist (verify
   each path with `Read` tool before writing)
8. All code fences have language specifiers
9. `uv run prek run --files .claude/docs/plan-artifact-lifecycle.md` exits 0

## Verification Steps

1. Read the file and confirm all nine section headings are present
2. Search the file for each required table: `Grep(pattern="Human-Decision",
   path=".claude/docs/plan-artifact-lifecycle.md")` and
   `Grep(pattern="Generated Artifacts", path=".claude/docs/plan-artifact-lifecycle.md")`
3. Confirm the divergence threshold table rows:
   `Grep(pattern="intent-divergence", path=".claude/docs/plan-artifact-lifecycle.md",
   output_mode="count")` — expect at least 3 matches
4. Verify all referenced file paths exist by running `Read` on each one before including
   the link
5. Run linter: `uv run prek run --files .claude/docs/plan-artifact-lifecycle.md`

## Handoff

Return:

- Confirmation that file was created with all 9 sections
- List of all cross-references included and their verified file paths
- Output of linter run (pass or failure with errors)
- Any content from the architecture spec that was ambiguous or required interpretation

---

## Task T2: Update local-workflow.md — Add Artifact Lifecycle Section

```yaml
---
task: T2
title: Update local-workflow.md — add artifact lifecycle section
status: not-started
agent: general-purpose
dependencies: [T1]
priority: 2
complexity: medium
accuracy-risk: low
parallelize-with: [T3, T5]
reason: T2, T3, T5 write to different files with no overlap
handoff: >
  Report: sections added/modified in local-workflow.md, line ranges of each
  change, linter pass/fail.
---
```

## Context

This task was planned as a standalone update. `local-workflow.md` is the SAM workflow
documentation that human operators and orchestrators read to understand the full pipeline.
It needs a new section describing the plan artifact lifecycle policy and updated tables and
diagrams to reflect the expanded Phase 6 behavior.

T1 must complete first because this task references
`.claude/docs/plan-artifact-lifecycle.md` in a new cross-reference link.

Architecture spec source: [plan/architect-plan-artifact-lifecycle.md](./architect-plan-artifact-lifecycle.md),
sections "Modifications to local-workflow.md".

## Objective

Add a Plan Artifact Lifecycle section to `.claude/rules/local-workflow.md`, update the
Phase 1 Artifacts Produced table to include an Artifact Type column, update the Phase 3
quality gate Phase 6 description, and update the Data Flow Diagram's
`/complete-implementation` block.

## Required Inputs

- [.claude/rules/local-workflow.md](../.claude/rules/local-workflow.md) — file to modify;
  read before editing
- [plan/architect-plan-artifact-lifecycle.md](./architect-plan-artifact-lifecycle.md) —
  sections "Modifications to local-workflow.md"
- `.claude/docs/plan-artifact-lifecycle.md` — must exist (T1 output); used as link target

## Requirements

### Artifacts Produced table update

1. Read the existing "Artifacts Produced" table in the Phase 1 section (currently 4 columns:
   Artifact, Path, Created By)
2. Add a fourth column `Artifact Type` to the table header
3. Add values for each row: Feature context → `Generated`, Codebase analysis →
   `Generated (snapshot)`, Architecture spec → `Generated`, Task plan → `Generated`

### New Plan Artifact Lifecycle section

4. Insert a new section titled `## Plan Artifact Lifecycle` after the "Artifacts Produced"
   table and before the "Agent Delegation Sequence" subsection (or as a top-level section
   between Phase 1 and Phase 2 — place it where it reads most naturally for a human
   scanning the document)
5. The new section must include:
   - A one-paragraph summary of the two artifact categories (human-decision and generated)
   - A reference link to `.claude/docs/plan-artifact-lifecycle.md` for full taxonomy
   - A two-column table: Artifact Type | Mutability Rule (human-decision: immutable,
     generated: mutable but intent-bound)
   - A note that divergence detection runs in Phase 6 of `/complete-implementation`

### Phase 3 quality gate Phase 6 description update

6. Find the Phase 6 line in the Phase Sequence table or list under Phase 3
   (`/complete-implementation`). The current text is:
   `Phase 6: context-refinement -> Context Manifest update`
   (or equivalent wording — read the file to find the exact current text)
7. Update the Phase 6 description to:
   `Phase 6: context-refinement -> Update task file Context Manifest + plan artifact freshness check`

### Data Flow Diagram update

8. In the `/complete-implementation` block of the Data Flow Diagram, find the
   `context-refinement` line. The current text ends with `updated Context Manifest`.
   Append two new lines beneath it:
   ```text
   ──> plan artifact annotations (if divergence found)
   ──> DIVERGENCE_REQUIRING_REVIEW (if intent divergence)
   ```
9. Preserve all existing diagram content — only append, do not reformat

## Constraints

- Read the full file before editing to understand existing structure and exact wording
- Do not rewrite sections not listed in Requirements
- Do not change the diagram arrows or formatting style for existing lines
- Use `./` relative paths in all new markdown links
- All new code fences must have language specifiers
- All new fenced code blocks must be surrounded by blank lines

## Expected Outputs

- File modified: `/home/user/claude_skills/.claude/rules/local-workflow.md`

## Acceptance Criteria

1. The Artifacts Produced table has an `Artifact Type` column with values for all four rows
2. A `## Plan Artifact Lifecycle` section exists in the file
3. The new section contains a link to `.claude/docs/plan-artifact-lifecycle.md`
4. The Phase 6 description in the phase sequence mentions "plan artifact freshness check"
5. The Data Flow Diagram's `context-refinement` block has the two appended lines
6. `uv run prek run --files .claude/rules/local-workflow.md` exits 0

## Verification Steps

1. `Grep(pattern="Artifact Type", path=".claude/rules/local-workflow.md",
   output_mode="content")` — confirm column header and four row values
2. `Grep(pattern="Plan Artifact Lifecycle", path=".claude/rules/local-workflow.md",
   output_mode="content")` — confirm section heading
3. `Grep(pattern="plan-artifact-lifecycle.md", path=".claude/rules/local-workflow.md",
   output_mode="content")` — confirm link target present
4. `Grep(pattern="freshness check", path=".claude/rules/local-workflow.md",
   output_mode="content")` — confirm Phase 6 description updated
5. `Grep(pattern="DIVERGENCE_REQUIRING_REVIEW", path=".claude/rules/local-workflow.md",
   output_mode="content")` — confirm data flow diagram updated
6. `uv run prek run --files .claude/rules/local-workflow.md`

## Handoff

Return:

- Line ranges of each change made
- The exact new text of the Phase 6 description
- The exact new text of the `## Plan Artifact Lifecycle` section
- Linter pass/fail

---

## Task T3: Update start-task SKILL.md — Add Divergence Recording Step

```yaml
---
task: T3
title: Update start-task SKILL.md — add divergence recording step 5a
status: not-started
agent: general-purpose
dependencies: [T1]
priority: 2
complexity: low
accuracy-risk: low
parallelize-with: [T2, T5]
reason: T2, T3, T5 write to different files with no overlap
handoff: >
  Report: exact location of new step 5a in SKILL.md (line numbers),
  linter pass/fail.
---
```

## Context

This task was planned as a standalone update. The `/start-task` skill is loaded by
sub-agents when they execute tasks. Adding divergence recording instructions ensures
agents capture implementation deviations during task execution, before
`/complete-implementation` runs the freshness check.

T1 must complete first because step 5a references the policy document at
`.claude/docs/plan-artifact-lifecycle.md`.

Architecture spec source: [plan/architect-plan-artifact-lifecycle.md](./architect-plan-artifact-lifecycle.md),
section "Modifications to `/start-task` SKILL.md".

## Objective

Insert a new step 5a into `.claude/skills/start-task/SKILL.md` between the existing step 4
(write active-task context file) and step 5 (implement against acceptance criteria),
instructing the agent to record divergence observations during implementation.

## Required Inputs

- [.claude/skills/start-task/SKILL.md](../.claude/skills/start-task/SKILL.md) — file to
  modify; read before editing; note current step numbering
- [plan/architect-plan-artifact-lifecycle.md](./architect-plan-artifact-lifecycle.md) —
  section "Modifications to `/start-task` SKILL.md", step 5a content
- `.claude/docs/plan-artifact-lifecycle.md` — must exist (T1 output); used as link target

## Requirements

1. Read `.claude/skills/start-task/SKILL.md` to confirm the exact current wording of step 4
   (write active-task context file) and step 5 (implement against acceptance criteria)
2. Insert a new numbered step between step 4 and step 5. The inserted content must be:

   ```markdown
   5. **Record divergence observations during implementation.**

      While implementing, if you discover that the architect spec or feature-context
      describes something that does not match what you are implementing, append a
      divergence note to the task file under a `## Divergence Notes` section.

      **When to record**: Record a divergence note when ALL of these hold:
      - You are implementing something that differs from what the architect spec or
        feature-context describes
      - The difference is not a trivial implementation detail (e.g., different variable
        name, different import path)
      - The difference affects the observable behavior, structure, or scope of the feature

      **Divergence note format**:

      ```markdown
      ## Divergence Notes

      ### DN-1: {Brief title}

      - **Plan artifact**: plan/architect-{slug}.md, section "{section name}"
      - **Plan claim**: "{quoted text from plan artifact}"
      - **Actual implementation**: "{what was actually done and why}"
      - **Classification**: design-refinement | intent-divergence
      - **Recorded**: {ISO timestamp}
      ```

      After appending a note, update `divergence-notes: {count}` in YAML frontmatter
      (or add `**Divergence Notes**: {count}` in legacy format).

      For full artifact classification rules and divergence thresholds, see
      [.claude/docs/plan-artifact-lifecycle.md](./../docs/plan-artifact-lifecycle.md).
   ```

3. Renumber the original step 5 (implement against acceptance criteria) to step 6
4. Preserve all other existing content unchanged

## Constraints

- Do not modify any step content other than the renumbering of the original step 5
- The new step must be inserted, not replacing any existing step
- Do not change the SKILL.md frontmatter
- Use `./` relative paths in all new markdown links (note: path from SKILL.md to docs is
  `./../docs/plan-artifact-lifecycle.md` — verify this resolves correctly given the file's
  location at `.claude/skills/start-task/SKILL.md`)
- All new code fences must have language specifiers
- Surround all fenced code blocks with blank lines

## Expected Outputs

- File modified: `/home/user/claude_skills/.claude/skills/start-task/SKILL.md`

## Acceptance Criteria

1. A step titled "Record divergence observations during implementation" exists in the file
2. The step contains the divergence note format block with `DN-1`, `Plan artifact`,
   `Plan claim`, `Actual implementation`, `Classification`, `Recorded` fields
3. The step contains the "when to record" criteria (all three conditions)
4. The step contains a link to `.claude/docs/plan-artifact-lifecycle.md`
5. The original "implement against acceptance criteria" step appears after the new step
6. `uv run prek run --files .claude/skills/start-task/SKILL.md` exits 0

## Verification Steps

1. `Grep(pattern="Divergence Notes", path=".claude/skills/start-task/SKILL.md",
   output_mode="content", -C=3)` — confirm the new step is present with context
2. `Grep(pattern="plan-artifact-lifecycle.md",
   path=".claude/skills/start-task/SKILL.md", output_mode="content")` — confirm link
3. `Grep(pattern="Implement against", path=".claude/skills/start-task/SKILL.md",
   output_mode="content")` — confirm original implementation step still present after
   the new step
4. `uv run prek run --files .claude/skills/start-task/SKILL.md`

## Handoff

Return:

- The line numbers of the inserted step 5a
- The exact text of the link to the policy document as it appears in the file
- Linter pass/fail

---

## Task T4: Update complete-implementation SKILL.md — Expand Phase 6 Description

```yaml
---
task: T4
title: Update complete-implementation SKILL.md — expand Phase 6 description
status: not-started
agent: general-purpose
dependencies: [T5]
priority: 3
complexity: low
accuracy-risk: low
parallelize-with: []
reason: T4 depends on T5 completing so Phase 6 description accurately reflects the
  extended context-refinement agent behavior
handoff: >
  Report: exact new text of Phase 6 section, location of new post-Phase-6
  section, linter pass/fail.
---
```

## Context

This task was planned as a standalone update. The `/complete-implementation` skill
orchestrates the six quality gate phases. The Phase 6 description currently describes
only the Context Manifest update. It must be expanded to describe the plan artifact
freshness check, and a new section must be added describing how the orchestrator handles
the `DIVERGENCE_REQUIRING_REVIEW` output.

T5 must complete first because the Phase 6 description accurately references the extended
context-refinement agent behavior, which is defined in T5.

Architecture spec source: [plan/architect-plan-artifact-lifecycle.md](./architect-plan-artifact-lifecycle.md),
section "Modified `/complete-implementation` Skill".

## Objective

Update `.claude/skills/complete-implementation/SKILL.md` to expand the Phase 6 description
and add post-Phase-6 orchestrator behavior for surfacing divergence findings to the human.

## Required Inputs

- [.claude/skills/complete-implementation/SKILL.md](../.claude/skills/complete-implementation/SKILL.md)
  — file to modify; read before editing
- [plan/architect-plan-artifact-lifecycle.md](./architect-plan-artifact-lifecycle.md) —
  section "Modified `/complete-implementation` Skill", subsections "Phase 6 Update" and
  "Orchestrator Post-Phase-6 Behavior"
- [plugins/python3-development/agents/context-refinement.md](../plugins/python3-development/agents/context-refinement.md)
  — read to confirm the `DIVERGENCE_REQUIRING_REVIEW` output block name matches what T5
  will have added

## Requirements

### Phase 6 description update

1. Find the `## Phase 6: Context Refinement` section in the SKILL.md
2. The current text is:
   `Launch \`context-refinement\` to update the task file Context Manifest with discoveries
   from implementation (only if needed).`
3. Replace with:
   `Launch \`context-refinement\` to update the task file Context Manifest with discoveries
   from implementation AND perform a plan artifact freshness check against the
   feature-context and architect spec. The agent compares key claims in plan artifacts
   against the actual implementation and classifies findings as design-refinement or
   intent-divergence (see [.claude/docs/plan-artifact-lifecycle.md](./../docs/plan-artifact-lifecycle.md)).`

### Post-Phase-6 section addition

4. After the `## Phase 6` section and before `## Recursive Follow-up Handling`, insert a
   new section:

   ```markdown
   ## Post-Phase-6: Surface Divergence Findings

   After Phase 6 completes, check the `context-refinement` agent output for a
   `DIVERGENCE_REQUIRING_REVIEW` block.

   If present, include in the final output to the human:

   ```text
   Plan artifacts have intent divergences requiring your review.
   See: [annotated artifact paths from agent output]
   Divergences:
     [list from DIVERGENCE_REQUIRING_REVIEW block]
   ```

   This is informational, not blocking. The human reviews at their discretion.
   If absent, no additional output is needed — the feature proceeds normally.
   ```

## Constraints

- Read the file before editing to confirm exact current Phase 6 text
- Do not modify Phases 1 through 5
- Do not modify `## Recursive Follow-up Handling`
- The link to `plan-artifact-lifecycle.md` must use relative path appropriate for the
  SKILL.md file location at `.claude/skills/complete-implementation/SKILL.md`
  (path: `./../docs/plan-artifact-lifecycle.md`)
- All new code fences must have language specifiers
- Surround all fenced code blocks with blank lines

## Expected Outputs

- File modified: `/home/user/claude_skills/.claude/skills/complete-implementation/SKILL.md`

## Acceptance Criteria

1. Phase 6 description mentions "plan artifact freshness check"
2. Phase 6 description mentions "design-refinement or intent-divergence"
3. Phase 6 description contains a link to `.claude/docs/plan-artifact-lifecycle.md`
4. A `## Post-Phase-6: Surface Divergence Findings` section exists between Phase 6 and
   Recursive Follow-up Handling
5. The new section contains `DIVERGENCE_REQUIRING_REVIEW` as the signal to check
6. `uv run prek run --files .claude/skills/complete-implementation/SKILL.md` exits 0

## Verification Steps

1. `Grep(pattern="freshness check",
   path=".claude/skills/complete-implementation/SKILL.md", output_mode="content")`
   — confirm Phase 6 updated
2. `Grep(pattern="DIVERGENCE_REQUIRING_REVIEW",
   path=".claude/skills/complete-implementation/SKILL.md", output_mode="content")`
   — confirm post-phase-6 section present
3. `Grep(pattern="plan-artifact-lifecycle.md",
   path=".claude/skills/complete-implementation/SKILL.md", output_mode="content")`
   — confirm link present
4. `uv run prek run --files .claude/skills/complete-implementation/SKILL.md`

## Handoff

Return:

- The exact new text of Phase 6
- The exact new text of the Post-Phase-6 section
- Linter pass/fail

---

## Task T5: Update context-refinement.md — Add Plan Artifact Freshness Check Steps

```yaml
---
task: T5
title: Update context-refinement.md — add plan artifact freshness check steps 5-8
status: not-started
agent: general-purpose
dependencies: [T1]
priority: 2
complexity: high
accuracy-risk: medium
parallelize-with: [T2, T3]
reason: T2, T3, T5 write to different files with no overlap
handoff: >
  Report: line numbers of each new section added, confirmation that DIVERGENCE_REQUIRING_REVIEW
  block format matches spec, linter pass/fail.
---
```

## Context

This task was planned as a standalone update. The `context-refinement` agent currently
performs only a task-scoped Context Manifest update. This task expands its scope to cover
plan artifact freshness checking across the feature's feature-context and architect spec
files.

T1 must complete first because the agent prompt references
`.claude/docs/plan-artifact-lifecycle.md` for classification rules.

Architecture spec source: [plan/architect-plan-artifact-lifecycle.md](./architect-plan-artifact-lifecycle.md),
sections "Extended Context-Refinement Agent" and "Modifications to `context-refinement.md`
Agent Prompt".

## Objective

Update `plugins/python3-development/agents/context-refinement.md` to: (1) expand the
YOUR MISSION statement to include plan artifact freshness checking, (2) add Steps 5-8 to
the Process section, (3) add the `DIVERGENCE_REQUIRING_REVIEW` output block to the Output
Format section, and (4) add a reference to the canonical policy document.

## Required Inputs

- [plugins/python3-development/agents/context-refinement.md](../plugins/python3-development/agents/context-refinement.md)
  — file to modify; read the full file before editing
- [plan/architect-plan-artifact-lifecycle.md](./architect-plan-artifact-lifecycle.md) —
  sections "Extended Context-Refinement Agent" (steps 5-8),
  "Modifications to context-refinement.md Agent Prompt" (mission update, output format),
  "Divergence Recording" (annotation format)
- `.claude/docs/plan-artifact-lifecycle.md` — must exist (T1 output); used as link target

## Requirements

### YOUR MISSION update

1. Find the `## YOUR MISSION` section. Current text:
   `Check IF context has drifted or new discoveries were made during the implementation
   session. Only update the context manifest if changes are needed.`
2. Replace with:
   `Check IF context has drifted or new discoveries were made during the implementation
   session. Update the context manifest if changes are needed. Then perform a plan artifact
   freshness check: compare the feature-context and architect spec against the actual
   implementation to detect and classify divergences as design-refinement or
   intent-divergence.`

### Add policy reference

3. After the `## Context About Your Invocation` section, insert a new paragraph:
   `For artifact classification rules, divergence thresholds, and annotation formats, see
   [.claude/docs/plan-artifact-lifecycle.md](./../../docs/plan-artifact-lifecycle.md).`
   (Note: path from agent file at
   `plugins/python3-development/agents/context-refinement.md` to
   `.claude/docs/plan-artifact-lifecycle.md` — verify the relative path resolves correctly)

### Add Steps 5-8 to the Process section

4. After the existing Step 4 (Update Format), append four new steps to the `## Process`
   section:

   **Step 5: Locate Plan Artifacts and Intent Source**

   ```markdown
   ### Step 5: Locate Plan Artifacts and Intent Source

   1. Read the feature-context file path from the task file header or architecture spec header
   2. Read the architecture spec file path from the task file header
   3. Read the `Intent Source` path from the feature-context or architecture spec header to
      locate the human-decision artifact
   4. If `Intent Source` is absent (pre-policy artifact), skip intent-divergence
      classification — treat all divergences as design-refinement
   ```

   **Step 6: Collect Divergence Evidence**

   ```markdown
   ### Step 6: Collect Divergence Evidence

   1. Read all task files for the feature (all tasks, not just the current one)
   2. Collect all `## Divergence Notes` sections from task bodies
   3. Collect all `### Discovered During Implementation` sections from Context Manifests
   4. Compare key claims in the architecture spec against the actual implementation files
   ```

   **Step 7: Classify Divergences**

   ```markdown
   ### Step 7: Classify Divergences

   For each divergence found:

   1. If `Intent Source` is available, read the human-decision artifact
   2. Compare the divergence against the human's stated intent (scope, goals, constraints)
   3. Apply the divergence threshold table from the policy document:
      - Implementation detail differs from architect spec → design-refinement (auto-record)
      - Approach differs but achieves same goal → design-refinement (auto-record, annotate
        architect spec)
      - Scope expanded or reduced beyond backlog item → intent-divergence (flag for review)
      - Goal redefined or abandoned → intent-divergence (flag for review)
      - Constraint from grooming output violated → intent-divergence (flag for review)
   ```

   **Step 8: Annotate Plan Artifacts**

   ```markdown
   ### Step 8: Annotate Plan Artifacts

   If divergences were found, append a `## Post-Implementation Annotations` section to
   the feature-context file and architect spec file. Use the annotation format:

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

   If no intent divergences are found, omit the `### Intent Divergences Requiring Review`
   subsection.

   Annotation rule: APPEND only. Never modify the original content of the plan artifact.
   ```

### Update Output Format section

5. In the `## Output Format` section, update the "On Success - Context Updated" block:
   - Change the SUMMARY line template to:
     `SUMMARY: Context manifest updated with [N] discoveries. Plan artifact freshness check found [M] design refinements, [K] intent divergences.`
   - Add `ARTIFACTS` entries for the annotated plan files:
     `- Annotated feature context: [path] (if annotated)`
     `- Annotated architect spec: [path] (if annotated)`

6. Add a new output block after "On Success - Context Updated" for when intent divergence
   is found:

   ```markdown
   ### On Success - Intent Divergence Found

   ```text
   STATUS: DONE
   SUMMARY: Context manifest updated. Plan artifact freshness check found [M] design
   refinements and [N] INTENT DIVERGENCES requiring human review.
   ARTIFACTS:
     - Updated task file: [path]
     - Annotated feature context: [path]
     - Annotated architect spec: [path]
   DIVERGENCE_REQUIRING_REVIEW:
     1. [Title]: [Brief description]
        - Human intent: [quoted]
        - Actual: [description]
        - Task: [task file path]
   RISKS:
     - Intent divergence detected -- human review needed before feature is considered complete
   NOTES:
     - [Summary]
   ```
   ```

## Constraints

- Read the full file before editing — do not skip any section
- All new steps append after Step 4; do not renumber or modify Steps 1-4
- The annotation operation in Step 8 is append-only; the instructions must make this clear
- The relative path from `plugins/python3-development/agents/context-refinement.md` to
  `.claude/docs/plan-artifact-lifecycle.md` must be verified before writing (count
  directory levels up from the agent file's location)
- All new code fences must have language specifiers
- Surround all fenced code blocks with blank lines

## Expected Outputs

- File modified:
  `/home/user/claude_skills/plugins/python3-development/agents/context-refinement.md`

## Acceptance Criteria

1. `## YOUR MISSION` includes "plan artifact freshness check"
2. `## YOUR MISSION` includes "design-refinement or intent-divergence"
3. A policy document reference link exists in the file pointing to
   `.claude/docs/plan-artifact-lifecycle.md`
4. Steps 5, 6, 7, and 8 exist in the `## Process` section
5. Step 8 contains the `## Post-Implementation Annotations` annotation format with both
   `### Design Refinements` and `### Intent Divergences Requiring Review` subsections
6. The Output Format section contains a `DIVERGENCE_REQUIRING_REVIEW` block
7. The SUMMARY template in "On Success - Context Updated" references design refinements
   and intent divergences
8. `uv run prek run --files plugins/python3-development/agents/context-refinement.md`
   exits 0

## Verification Steps

1. `Grep(pattern="freshness check",
   path="plugins/python3-development/agents/context-refinement.md",
   output_mode="content")` — confirm mission statement updated
2. `Grep(pattern="Step 5",
   path="plugins/python3-development/agents/context-refinement.md",
   output_mode="content", -C=2)` — confirm Step 5 present
3. `Grep(pattern="DIVERGENCE_REQUIRING_REVIEW",
   path="plugins/python3-development/agents/context-refinement.md",
   output_mode="content")` — confirm output block present
4. `Grep(pattern="Post-Implementation Annotations",
   path="plugins/python3-development/agents/context-refinement.md",
   output_mode="content")` — confirm annotation format present
5. `Grep(pattern="plan-artifact-lifecycle.md",
   path="plugins/python3-development/agents/context-refinement.md",
   output_mode="content")` — confirm policy reference link present
6. `uv run prek run --files plugins/python3-development/agents/context-refinement.md`

## CoVe Checks

- Key claims to verify:
  - The relative path from `plugins/python3-development/agents/context-refinement.md`
    to `.claude/docs/plan-artifact-lifecycle.md`
  - That adding Steps 5-8 after Step 4 does not create a numbering conflict with any
    subsections or numbered items already in the file

- Verification questions (falsifiable):
  1. Reading `plugins/python3-development/agents/context-refinement.md` — does the file
     currently contain a Step 4 and no Step 5? If Step 5 already exists, the new steps
     must use different labels (e.g., 5a, 5b) or a new subsection.
  2. From `plugins/python3-development/agents/context-refinement.md`, what is the
     correct relative path to `.claude/docs/`? Count: the file is at
     `plugins/python3-development/agents/` — three levels deep from repo root. The target
     is `.claude/docs/` — one level deep from repo root. Correct relative path:
     `./../../.claude/docs/plan-artifact-lifecycle.md`.

- Evidence to collect:
  - Read the file and confirm whether "Step 5" text already appears anywhere
  - Verify path: `Read(file_path=".claude/docs/plan-artifact-lifecycle.md")` — confirm
    it exists at that path after T1 completes
  - Confirm the resolved relative path by counting directory depth

- Revision rule:
  If Step 5 already exists in the file (from a prior modification), rename new steps to
  avoid collision. If the relative path resolution is uncertain, use the absolute path
  approach from the architecture spec as a fallback and note it in the handoff.

## Handoff

Return:

- Line numbers of each new section added
- The exact relative path used for the policy document link and confirmation it resolves
- Confirmation that the `DIVERGENCE_REQUIRING_REVIEW` block format matches the spec
- Whether any CoVe checks required revision and what changed
- Linter pass/fail

---

## Task T6: Update TASK_FILE_FORMAT.md — Add divergence-notes Field

```yaml
---
task: T6
title: Update TASK_FILE_FORMAT.md — add divergence-notes optional field
status: not-started
agent: general-purpose
dependencies: []
priority: 1
complexity: low
accuracy-risk: low
parallelize-with: [T1]
reason: T6 and T1 write to different files with no overlap
handoff: >
  Report: line numbers of each addition in TASK_FILE_FORMAT.md, confirmation that
  divergence-notes appears in both the Optional Fields table and JSON schema,
  backward-compatibility validation result.
---
```

## Context

This task was planned as a standalone update. `TASK_FILE_FORMAT.md` is the schema
document that defines valid YAML frontmatter fields for task files. The `divergence-notes`
field needs to be added as an optional field so it is recognized as part of the schema,
enabling the `context-refinement` agent to quickly identify tasks that recorded divergences.

T6 has no dependencies — the schema change is self-contained and does not reference the
policy document.

Architecture spec source: [plan/architect-plan-artifact-lifecycle.md](./architect-plan-artifact-lifecycle.md),
section "Task File Format Extension".

## Objective

Add `divergence-notes` as an optional integer field to the Optional Fields table and the
JSON Schema `properties` block in `.claude/docs/TASK_FILE_FORMAT.md`.

## Required Inputs

- [.claude/docs/TASK_FILE_FORMAT.md](../.claude/docs/TASK_FILE_FORMAT.md) — file to modify;
  read before editing; note current Optional Fields table structure and JSON schema
  properties block

## Requirements

### Optional Fields table addition

1. Read the Optional Fields table (section "Optional Fields" under "Field Definitions")
2. Add a new row for `divergence-notes` after the existing `analysis-method` row:

   | Field | Type | Description | Example |
   | `divergence-notes` | integer | Count of divergence notes recorded during implementation | `2` |

3. The row must follow the same column order and formatting as existing rows

### JSON Schema addition

4. Find the JSON schema `properties` block (inside the `## YAML Schema` section)
5. After the `"analysis-method"` property definition and before the closing `}` of the
   `"properties"` object, add:

   ```json
   "divergence-notes": {
     "type": "integer",
     "minimum": 0,
     "default": 0,
     "description": "Count of divergence notes recorded during implementation"
   }
   ```

6. Ensure the JSON remains valid (trailing comma on the preceding property if needed, or
   no trailing comma on the new property if it is last)

### Template update

7. Find the template file contents block in `## Template File` section
8. Add a commented-out optional field line for `divergence-notes` after
   `# analysis-method`:
   ```text
   # divergence-notes: 0   # OPTIONAL: integer count of ## Divergence Notes sections in body
   ```

## Constraints

- Read the file fully before editing to understand current structure
- Do not modify any existing field definitions
- The JSON schema addition must maintain valid JSON syntax — verify by reading surrounding
  context carefully before writing
- Do not add `divergence-notes` to the Required Fields table
- Do not change the `## Migration Guide` section

## Expected Outputs

- File modified: `/home/user/claude_skills/.claude/docs/TASK_FILE_FORMAT.md`

## Acceptance Criteria

1. `divergence-notes` appears in the Optional Fields table with type `integer`,
   description including "divergence notes", and example `2`
2. `divergence-notes` appears in the JSON schema `properties` block with `"type":
   "integer"`, `"minimum": 0`, `"default": 0`
3. The template block contains a commented `divergence-notes` line
4. Existing backward-compatibility claim holds: running
   `uv run plugins/python3-development/skills/implementation-manager/scripts/implementation_manager.py
   validate . plugin-linter` succeeds (existing task files without `divergence-notes`
   still validate — the field is optional with default 0)
5. `uv run prek run --files .claude/docs/TASK_FILE_FORMAT.md` exits 0

## Verification Steps

1. `Grep(pattern="divergence-notes", path=".claude/docs/TASK_FILE_FORMAT.md",
   output_mode="content", -C=2)` — confirm field appears in table, schema, and template
2. `Grep(pattern="\"minimum\": 0", path=".claude/docs/TASK_FILE_FORMAT.md",
   output_mode="content")` — confirm JSON schema minimum constraint
3. Run backward-compatibility check:
   `uv run plugins/python3-development/skills/implementation-manager/scripts/implementation_manager.py
   validate . plugin-linter`
   — expect exit 0 with no schema errors
4. `uv run prek run --files .claude/docs/TASK_FILE_FORMAT.md`

## Handoff

Return:

- The exact text of the new Optional Fields table row
- The exact JSON added to the schema properties block
- Output of the backward-compatibility validation command
- Linter pass/fail

---

## SYNC CHECKPOINT 1: All Tasks Complete

Convergence point: T1 + T2 + T3 + T4 + T5 + T6 outputs

### Quality Gates

1. All six tasks have `status: complete` in this file
2. `.claude/docs/plan-artifact-lifecycle.md` exists with all nine required sections
3. `Grep(pattern="freshness check", path=".claude/skills/complete-implementation/SKILL.md")`
   returns a match
4. `Grep(pattern="DIVERGENCE_REQUIRING_REVIEW",
   path="plugins/python3-development/agents/context-refinement.md")` returns a match
5. `Grep(pattern="divergence-notes", path=".claude/docs/TASK_FILE_FORMAT.md")` returns
   matches in table, schema, and template
6. All linter runs passed (T1 through T6 each ran
   `uv run prek run --files <modified-file>` with exit 0)
7. Backward-compatibility check passed:
   `uv run plugins/python3-development/skills/implementation-manager/scripts/implementation_manager.py
   validate . plugin-linter` exits 0

### Cross-Reference Integrity Check

Verify all new inter-file references resolve:

1. `Grep(pattern="plan-artifact-lifecycle.md", path=".claude/rules/local-workflow.md")`
   — T2 must reference T1's output
2. `Grep(pattern="plan-artifact-lifecycle.md",
   path=".claude/skills/start-task/SKILL.md")` — T3 must reference T1's output
3. `Grep(pattern="plan-artifact-lifecycle.md",
   path=".claude/skills/complete-implementation/SKILL.md")` — T4 must reference T1's output
4. `Grep(pattern="plan-artifact-lifecycle.md",
   path="plugins/python3-development/agents/context-refinement.md")` — T5 must reference
   T1's output

### Reflection Questions

- Do the new divergence note format and the annotation format in context-refinement.md
  use consistent field names?
- Does the DIVERGENCE_REQUIRING_REVIEW block format in context-refinement.md match the
  format described in complete-implementation SKILL.md?
- Are there any paths in the new content that cross plugin boundaries in a way that could
  break when the skill is installed in a different location?

Proceed to consider implementation complete after all quality gates pass.
