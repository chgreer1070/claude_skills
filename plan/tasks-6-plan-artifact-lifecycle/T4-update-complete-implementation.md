---
task: T4
title: Update complete-implementation SKILL.md — expand Phase 6 description
status: complete
started: 2026-03-02T00:00:00Z
completed: 2026-03-02T00:00:00Z
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

## Context

This task was planned as a standalone update. The `/complete-implementation` skill
orchestrates the six quality gate phases. The Phase 6 description currently describes
only the Context Manifest update. It must be expanded to describe the plan artifact
freshness check, and a new section must be added describing how the orchestrator handles
the `DIVERGENCE_REQUIRING_REVIEW` output.

T5 must complete first because the Phase 6 description accurately references the extended
context-refinement agent behavior, which is defined in T5.

Architecture spec source: [plan/architect-plan-artifact-lifecycle.md](../architect-plan-artifact-lifecycle.md),
section "Modified `/complete-implementation` Skill".

## Objective

Update `.claude/skills/complete-implementation/SKILL.md` to expand the Phase 6 description
and add post-Phase-6 orchestrator behavior for surfacing divergence findings to the human.

## Required Inputs

- [.claude/skills/complete-implementation/SKILL.md](../../.claude/skills/complete-implementation/SKILL.md)
  — file to modify; read before editing
- [plan/architect-plan-artifact-lifecycle.md](../architect-plan-artifact-lifecycle.md) —
  section "Modified `/complete-implementation` Skill"
- [plugins/python3-development/agents/context-refinement.md](../../plugins/python3-development/agents/context-refinement.md)
  — read to confirm the `DIVERGENCE_REQUIRING_REVIEW` output block name

## Requirements

### Phase 6 description update

1. Find the `## Phase 6: Context Refinement` section in the SKILL.md
2. Replace the existing single-sentence description with expanded text covering
   plan artifact freshness check, divergence classification, and link to policy doc

### Post-Phase-6 section addition

3. After the `## Phase 6` section and before `## Recursive Follow-up Handling`, insert a
   new `## Post-Phase-6: Surface Divergence Findings` section describing how the
   orchestrator checks for and surfaces DIVERGENCE_REQUIRING_REVIEW output

## Constraints

- Read the file before editing to confirm exact current Phase 6 text
- Do not modify Phases 1 through 5
- Do not modify `## Recursive Follow-up Handling`
- All new code fences must have language specifiers
- Surround all fenced code blocks with blank lines

## Expected Outputs

- File modified: `.claude/skills/complete-implementation/SKILL.md`

## Acceptance Criteria

1. Phase 6 description mentions "plan artifact freshness check"
2. Phase 6 description mentions "design-refinement or intent-divergence"
3. Phase 6 description contains a link to `.claude/docs/plan-artifact-lifecycle.md`
4. A `## Post-Phase-6: Surface Divergence Findings` section exists between Phase 6 and
   Recursive Follow-up Handling
5. The new section contains `DIVERGENCE_REQUIRING_REVIEW` as the signal to check
6. `uv run prek run --files .claude/skills/complete-implementation/SKILL.md` exits 0
