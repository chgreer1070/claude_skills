---
task: T6
title: "Feature Verifier development-harness: add identical Step 7 Proportional Response Check"
status: complete
started: 2026-03-02T00:16:00Z
completed: 2026-03-02T00:18:00Z
agent: general-purpose
dependencies: [T5]
priority: 3
complexity: medium
accuracy-risk: low
parallelize-with: []
reason: "Depends on T5 for content consistency. T6 copies the Step 7 content from the python3-development version with only the skill-reference difference."
handoff: "Report: diff between python3-development and development-harness versions of Step 7 (should be zero or only the skill reference), prek lint result."
---

## Context

The `feature-verifier.md` exists in two plugins: `python3-development` and `development-harness`. Per ADR-005 in the architect spec, the same proportional response check step is added to both agents. The only permitted difference is the existing skill reference difference between the two agents (`python3-development` vs `development-harness`).

T6 depends on T5 to ensure the Step 7 content is finalized before being mirrored. The agent doing T6 should read the completed T5 output and copy it, adjusting only the skill reference if needed.

Architecture spec: `plan/architect-process-quality-discipline.md`, section "ADR-005: Identical Feature Verifier Changes in Both Plugins".

Fixes #314.

## Objective

Apply identical Step 7 (Proportional Response Check) changes to `plugins/development-harness/agents/feature-verifier.md` as were applied in T5 to the python3-development variant, adjusting only for any existing skill reference differences.

## Required Inputs

- Read `plugins/development-harness/agents/feature-verifier.md` in full — note the existing step structure, current step count, `<success_criteria>` block, and the skill reference in the frontmatter (`skills:` field)
- Read `plugins/python3-development/agents/feature-verifier.md` in full AFTER T5 is complete — read the exact Step 7 and Step 8 content that T5 produced
- Read `plan/architect-process-quality-discipline.md` section "ADR-005" to confirm the only permitted difference

## Requirements

1. Apply the identical changes as T5 to this file:
   - Insert Step 7: Proportional Response Check (copy from python3-development version)
   - Rename current final step to Step 8: Determine Overall Status
   - Update Step 8 status logic (copy from python3-development version)
   - Add `### Proportional Response (Step 7)` checklist to `<success_criteria>` (copy from python3-development version)
2. If the `development-harness` agent currently references a different skill name than `python3-development` (e.g., `development-harness` vs `python3-development` in a prompt or skills list), preserve that difference — do not introduce skill references that do not belong in this agent
3. The Mermaid flowchart in Step 7 must be identical between the two files (the flowchart itself does not reference skill names)

## Constraints

- Do not introduce `python3-development` skill references into the `development-harness` agent
- Steps 1-6 must not be modified
- Apply ONLY the changes specified — do not refactor or improve other parts of the file
- New Step 7 must be inside the `<verification_process>` XML block

## Expected Outputs

- `plugins/development-harness/agents/feature-verifier.md` — modified in place

## Acceptance Criteria

1. `<verification_process>` block contains exactly 8 step headings
2. `## Step 7: Proportional Response Check` exists with the same Mermaid flowchart as in the python3-development version
3. Step 8 status determination logic matches the python3-development version
4. `<success_criteria>` contains the `### Proportional Response (Step 7)` checklist
5. The only differences between the two `feature-verifier.md` files are pre-existing differences (skill references, model, description) — NOT the Step 7 content itself
6. `uv run prek run --files plugins/development-harness/agents/feature-verifier.md` exits 0

## Verification Steps

1. Run `Grep(pattern="## Step [0-9]", path="plugins/development-harness/agents/feature-verifier.md", output_mode="content")` — confirm 8 steps
2. Read Step 7 in development-harness and confirm Mermaid flowchart is identical to python3-development Step 7
3. Run `uv run prek run --files plugins/development-harness/agents/feature-verifier.md` — confirm exit 0
4. Run `Grep(pattern="python3-development", path="plugins/development-harness/agents/feature-verifier.md", output_mode="content")` — confirm no new python3-development skill references were introduced

## Handoff

Return:

- Confirmation that Step 7 Mermaid flowchart is identical between both plugin versions
- Any pre-existing differences between the two files (skill references, etc.) that were preserved
- `prek` lint result

