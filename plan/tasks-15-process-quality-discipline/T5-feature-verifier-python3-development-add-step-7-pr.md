---
task: T5
title: "Feature Verifier python3-development: add Step 7 Proportional Response Check"
status: complete
started: 2026-03-02T00:06:00Z
completed: 2026-03-02T00:15:00Z
agent: general-purpose
dependencies: [T1]
priority: 2
complexity: medium
accuracy-risk: medium
parallelize-with: [T2, T3, T4]
reason: "Independent file from T2, T3, T4. T6 depends on T5 for content consistency."
handoff: "Report: exact step numbers before and after edit, prek lint result, exact text of the Mermaid flowchart Step 7 label."
---

## Context

The `feature-verifier.md` agent in `plugins/python3-development/` currently has 7 steps (Steps 1-7 inside `<verification_process>`). This task inserts a new Step 7 (Proportional Response Check) before the existing final step (Determine Overall Status), which becomes Step 8.

T6 depends on this task to copy the identical Step 7 content to the `development-harness` variant — ensuring they stay in sync.

Architecture spec: `plan/architect-process-quality-discipline.md`, sections "Feature Verifier Enhancement", "New Step in Both Feature Verifier Agents", "Step Specification: Proportional Response Check", "Update to Status Determination Step", "Update to Success Criteria".

Fixes #314.

## Objective

Insert Step 7 (Proportional Response Check with Mermaid decision flowchart) into `plugins/python3-development/agents/feature-verifier.md`, renumber current final step to Step 8, update Step 8 status determination logic, and add proportional response checklist to `<success_criteria>`.

## Required Inputs

- Read `plugins/python3-development/agents/feature-verifier.md` in full — note exact current step headings and their line numbers, current Step 7 heading text, the `<success_criteria>` block
- Read `plan/architect-process-quality-discipline.md` sections: "Step Specification: Proportional Response Check" (full Mermaid flowchart), "Status output for this step", "Update to Status Determination Step", "Update to Success Criteria"
- Note: this agent uses `<verification_process>` XML wrapper for steps, NOT a bare markdown heading block

## Requirements

### New Step 7: Proportional Response Check

1. Insert `## Step 7: Proportional Response Check` INSIDE `<verification_process>`, AFTER Step 6 (Test Edge Cases), BEFORE current Step 7 (Determine Overall Status)
2. Step 7 body must include:
   - Instruction to read task file YAML frontmatter for `issue-classification`, `scenario-target`, and `analysis-method`
   - Skip instruction: "If `issue-classification` is absent: SKIP this step. Existing verification is sufficient."
   - The Mermaid decision flowchart from the architect spec (classification type → check criteria)
   - Status output definition: VERIFIED / FAILED / SKIPPED

### Step renumbering and status update

3. Rename current `## Step 7: Determine Overall Status` to `## Step 8: Determine Overall Status`
4. Update Step 8 status determination logic to include: "VERIFIED requires all existing checks PLUS proportional response check is VERIFIED or SKIPPED" and "GAPS_FOUND if proportional response check is FAILED — include specific failure description"

### Success criteria update

5. Add to `<success_criteria>`:

   ```text
   ### Proportional Response (Step 7)

   - [ ] issue-classification read from task metadata
   - [ ] Proportional checks applied per classification type
   - [ ] Root-cause vs symptom fix verified (for defect type)
   - [ ] Guardrail added and pattern-scoped (for recurring-pattern type)
   - [ ] Results included in overall status determination
   ```

## Constraints

- Steps 1-6 must not be modified
- The new Step 7 must be inside the `<verification_process>` XML block — not outside it
- Mermaid flowcharts: use `<br>` for line breaks in node labels, use `=` not `:` for assignments in label strings
- The SKIP path (`issue-classification` absent) must be explicit as the first conditional branch
- Do not change the `skills` or `model` frontmatter fields

## Expected Outputs

- `plugins/python3-development/agents/feature-verifier.md` — modified in place

## Acceptance Criteria

1. `<verification_process>` block contains exactly 8 step headings (`## Step 1` through `## Step 8`)
2. `## Step 7: Proportional Response Check` exists and contains a Mermaid flowchart with branches for all 5 classification types plus absent/SKIP
3. `## Step 8: Determine Overall Status` exists (was Step 7) and references proportional check results in its logic
4. `<success_criteria>` contains the `### Proportional Response (Step 7)` checklist with all 5 checkbox items
5. `uv run prek run --files plugins/python3-development/agents/feature-verifier.md` exits 0

## Verification Steps

1. Run `Grep(pattern="## Step [0-9]", path="plugins/python3-development/agents/feature-verifier.md", output_mode="content")` — confirm 8 steps in order
2. Read Step 7 and confirm Mermaid flowchart includes `absent` → SKIP branch as well as all 5 classification branches
3. Read Step 8 and confirm proportional check results are referenced in the status determination logic
4. Run `Grep(pattern="Proportional Response", path="plugins/python3-development/agents/feature-verifier.md", output_mode="content")` — confirm it appears in both Step 7 body and `<success_criteria>`
5. Run `uv run prek run --files plugins/python3-development/agents/feature-verifier.md` — confirm exit 0

## CoVe Checks

- Key claims to verify:
  - Current final step is "Determine Overall Status" (not renamed already)
  - Steps are inside `<verification_process>` block (not a top-level heading structure)
  - Current step count is 7 (not 6 or 8)
- Verification questions (falsifiable):
  1. What is the exact current step count inside `<verification_process>`? Run `Grep(pattern="## Step [0-9]", path="plugins/python3-development/agents/feature-verifier.md", output_mode="content")`
  2. Does the file already contain any reference to "Proportional Response"? Run `Grep(pattern="Proportional", path="plugins/python3-development/agents/feature-verifier.md")`
- Evidence to collect:
  - Current step headings and their line numbers
  - Confirm no partial implementation exists
- Revision rule:
  - If any step content related to proportional checks already exists, read it fully before editing. Do not duplicate existing content.

## Handoff

Return:

- Step headings before and after (list of all 8 steps)
- Confirmation that the new Step 7 is inside `<verification_process>` XML block
- Exact Mermaid flowchart title used in Step 7
- `prek` lint result

