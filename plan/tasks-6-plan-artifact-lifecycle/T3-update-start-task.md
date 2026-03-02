---
task: T3
title: Update start-task SKILL.md — add divergence recording step 5a
status: complete
started: "2026-03-02T12:00:00Z"
completed: 2026-03-02T00:00:00Z
agent: general-purpose
dependencies: [T1]
priority: 2
complexity: low
accuracy-risk: low
parallelize-with: [T2, T5]
reason: T2, T3, T5 write to different files with no overlap
divergence-notes: 1
handoff: >
  Report: exact location of new step 5a in SKILL.md (line numbers),
  linter pass/fail.
---

## Context

This task was planned as a standalone update. The `/start-task` skill is loaded by
sub-agents when they execute tasks. Adding divergence recording instructions ensures
agents capture implementation deviations during task execution, before
`/complete-implementation` runs the freshness check.

T1 must complete first because step 5a references the policy document at
`.claude/docs/plan-artifact-lifecycle.md`.

Architecture spec source: [plan/architect-plan-artifact-lifecycle.md](../architect-plan-artifact-lifecycle.md),
section "Modifications to `/start-task` SKILL.md".

## Objective

Insert a new step 5a into `.claude/skills/start-task/SKILL.md` between the existing step 4
(write active-task context file) and step 5 (implement against acceptance criteria),
instructing the agent to record divergence observations during implementation.

## Required Inputs

- [.claude/skills/start-task/SKILL.md](../../.claude/skills/start-task/SKILL.md) — file to
  modify; read before editing; note current step numbering
- [plan/architect-plan-artifact-lifecycle.md](../architect-plan-artifact-lifecycle.md) —
  section "Modifications to `/start-task` SKILL.md", step 5a content
- `.claude/docs/plan-artifact-lifecycle.md` — must exist (T1 output); used as link target

## Requirements

1. Read `.claude/skills/start-task/SKILL.md` to confirm the exact current wording of step 4
   and step 5
2. Insert a new numbered step between step 4 and step 5 with divergence recording
   instructions including DN-N format, "when to record" criteria, and link to policy doc
3. Renumber the original step 5 (implement against acceptance criteria) to step 6
4. Preserve all other existing content unchanged

## Constraints

- Do not modify any step content other than the renumbering of the original step 5
- The new step must be inserted, not replacing any existing step
- Do not change the SKILL.md frontmatter
- Use `./` relative paths in all new markdown links
- All new code fences must have language specifiers
- Surround all fenced code blocks with blank lines

## Expected Outputs

- File modified: `.claude/skills/start-task/SKILL.md`

## Acceptance Criteria

1. A step titled "Record divergence observations during implementation" exists in the file
2. The step contains the divergence note format block with `DN-1`, `Plan artifact`,
   `Plan claim`, `Actual implementation`, `Classification`, `Recorded` fields
3. The step contains the "when to record" criteria (all three conditions)
4. The step contains a link to `.claude/docs/plan-artifact-lifecycle.md`
5. The original "implement against acceptance criteria" step appears after the new step
6. `uv run prek run --files .claude/skills/start-task/SKILL.md` exits 0

## Divergence Notes

### DN-1: Corrected relative link path to policy document

- **Plan artifact**: plan/tasks-6-plan-artifact-lifecycle.md, section "Requirements"
- **Plan claim**: "path from SKILL.md to docs is `./../docs/plan-artifact-lifecycle.md`"
- **Actual implementation**: Used `./../../docs/plan-artifact-lifecycle.md` because SKILL.md is at `.claude/skills/start-task/SKILL.md` (3 levels deep from repo root), so `./../docs/` resolves to `.claude/skills/docs/` (wrong). `./../../docs/` resolves to `.claude/docs/` (correct). The constraint text itself said "verify this resolves correctly", confirming the intent was correctness over literal match.
- **Classification**: design-refinement
- **Recorded**: 2026-03-02T12:05:00Z
