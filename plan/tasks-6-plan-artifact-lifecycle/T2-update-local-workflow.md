---
task: T2
title: Update local-workflow.md — add artifact lifecycle section
status: complete
started: 2026-03-02T00:00:00Z
completed: 2026-03-02T00:00:00Z
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

## Context

This task was planned as a standalone update. `local-workflow.md` is the SAM workflow
documentation that human operators and orchestrators read to understand the full pipeline.
It needs a new section describing the plan artifact lifecycle policy and updated tables and
diagrams to reflect the expanded Phase 6 behavior.

T1 must complete first because this task references
`.claude/docs/plan-artifact-lifecycle.md` in a new cross-reference link.

Architecture spec source: [plan/architect-plan-artifact-lifecycle.md](../architect-plan-artifact-lifecycle.md),
sections "Modifications to local-workflow.md".

## Objective

Add a Plan Artifact Lifecycle section to `.claude/rules/local-workflow.md`, update the
Phase 1 Artifacts Produced table to include an Artifact Type column, update the Phase 3
quality gate Phase 6 description, and update the Data Flow Diagram's
`/complete-implementation` block.

## Required Inputs

- [.claude/rules/local-workflow.md](../../.claude/rules/local-workflow.md) — file to modify;
  read before editing
- [plan/architect-plan-artifact-lifecycle.md](../architect-plan-artifact-lifecycle.md) —
  sections "Modifications to local-workflow.md"
- `.claude/docs/plan-artifact-lifecycle.md` — must exist (T1 output); used as link target

## Requirements

### Artifacts Produced table update

1. Read the existing "Artifacts Produced" table in the Phase 1 section (currently 4 columns:
   Artifact, Path, Created By)
2. Add a fourth column `Artifact Type` to the table header
3. Add values for each row: Feature context -> `Generated`, Codebase analysis ->
   `Generated (snapshot)`, Architecture spec -> `Generated`, Task plan -> `Generated`

### New Plan Artifact Lifecycle section

4. Insert a new section titled `## Plan Artifact Lifecycle` after the "Artifacts Produced"
   table and before the "Agent Delegation Sequence" subsection
5. The new section must include:
   - A one-paragraph summary of the two artifact categories (human-decision and generated)
   - A reference link to `.claude/docs/plan-artifact-lifecycle.md` for full taxonomy
   - A two-column table: Artifact Type | Mutability Rule (human-decision: immutable,
     generated: mutable but intent-bound)
   - A note that divergence detection runs in Phase 6 of `/complete-implementation`

### Phase 3 quality gate Phase 6 description update

6. Find the Phase 6 line in the Phase Sequence table or list under Phase 3
7. Update the Phase 6 description to include "plan artifact freshness check"

### Data Flow Diagram update

8. In the `/complete-implementation` block of the Data Flow Diagram, find the
   `context-refinement` line and append two new lines for annotations and
   DIVERGENCE_REQUIRING_REVIEW
9. Preserve all existing diagram content — only append, do not reformat

## Constraints

- Read the full file before editing to understand existing structure and exact wording
- Do not rewrite sections not listed in Requirements
- Do not change the diagram arrows or formatting style for existing lines
- Use `./` relative paths in all new markdown links
- All new code fences must have language specifiers
- All new fenced code blocks must be surrounded by blank lines

## Expected Outputs

- File modified: `.claude/rules/local-workflow.md`

## Acceptance Criteria

1. The Artifacts Produced table has an `Artifact Type` column with values for all four rows
2. A `## Plan Artifact Lifecycle` section exists in the file
3. The new section contains a link to `.claude/docs/plan-artifact-lifecycle.md`
4. The Phase 6 description in the phase sequence mentions "plan artifact freshness check"
5. The Data Flow Diagram's `context-refinement` block has the two appended lines
6. `uv run prek run --files .claude/rules/local-workflow.md` exits 0

## Verification Steps

1. `Grep(pattern="Artifact Type", path=".claude/rules/local-workflow.md")` — confirm column header
2. `Grep(pattern="Plan Artifact Lifecycle", path=".claude/rules/local-workflow.md")` — confirm section
3. `Grep(pattern="plan-artifact-lifecycle.md", path=".claude/rules/local-workflow.md")` — confirm link
4. `Grep(pattern="freshness check", path=".claude/rules/local-workflow.md")` — confirm Phase 6
5. `Grep(pattern="DIVERGENCE_REQUIRING_REVIEW", path=".claude/rules/local-workflow.md")` — confirm diagram
6. `uv run prek run --files .claude/rules/local-workflow.md`

## Handoff

Return:

- Line ranges of each change made
- The exact new text of the Phase 6 description
- The exact new text of the `## Plan Artifact Lifecycle` section
- Linter pass/fail
