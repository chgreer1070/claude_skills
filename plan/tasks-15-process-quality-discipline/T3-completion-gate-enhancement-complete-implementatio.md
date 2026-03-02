---
task: T3
title: "Completion Gate Enhancement: complete-implementation/SKILL.md"
status: complete
started: 2026-03-02T00:06:00Z
completed: 2026-03-02T00:15:00Z
agent: general-purpose
dependencies: [T1]
priority: 2
complexity: low
accuracy-risk: low
parallelize-with: [T2, T4, T5]
reason: "Independent file. Minimal single-line addition to Phase 2. No overlap with T2, T4, T5."
handoff: "Report: exact text added to Phase 2, prek lint result."
---

## Context

The architect spec calls for a minimal one-line addition to Phase 2 of the `/complete-implementation` skill. This is the smallest change in the entire feature — one sentence added to an existing phase description.

Architecture spec: `plan/architect-process-quality-discipline.md`, section "Completion Gate Integration".

Fixes #314.

## Objective

Add a single instruction to Phase 2 of `complete-implementation/SKILL.md` that directs the orchestrator to include `issue-classification` metadata in the feature-verifier agent prompt when present.

## Required Inputs

- Read `.claude/skills/complete-implementation/SKILL.md` in full — locate Phase 2 (~line 28)
- Read `plan/architect-process-quality-discipline.md` section "Completion Gate Integration" for the exact new text

## Requirements

1. Locate Phase 2: "Feature Verification (goal-backward)" in the skill
2. Current text: `Launch feature-verifier with the task file path.`
3. Replace with (or append after): `Launch feature-verifier with the task file path. If the task file contains issue-classification metadata, include it in the agent prompt so the feature verifier can apply proportional verification checks.`

## Constraints

- Change is additive only — do not remove, reorder, or reword any other phase
- Do not add new phases
- The instruction must state the CONDITION (`if the task file contains issue-classification metadata`) — not unconditionally

## Expected Outputs

- `.claude/skills/complete-implementation/SKILL.md` — modified in place

## Acceptance Criteria

1. Phase 2 description contains the sentence: "If the task file contains `issue-classification` metadata, include it in the agent prompt so the feature verifier can apply proportional verification checks."
2. No other phases are modified
3. `uv run prek run --files .claude/skills/complete-implementation/SKILL.md` exits 0

## Verification Steps

1. Read `.claude/skills/complete-implementation/SKILL.md` and confirm Phase 2 contains the new instruction
2. Confirm no other phase text was altered
3. Run `uv run prek run --files .claude/skills/complete-implementation/SKILL.md` — confirm exit 0

## Handoff

Return:

- Exact text of Phase 2 after the edit
- `prek` lint result
- Confirmation that no other phases were modified

