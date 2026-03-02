---
task: T5
title: Update context-refinement.md — add plan artifact freshness check steps 5-8
status: complete
started: 2026-03-02T00:00:00Z
completed: 2026-03-02T00:00:00Z
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

## Context

This task was planned as a standalone update. The `context-refinement` agent currently
performs only a task-scoped Context Manifest update. This task expands its scope to cover
plan artifact freshness checking across the feature's feature-context and architect spec
files.

T1 must complete first because the agent prompt references
`.claude/docs/plan-artifact-lifecycle.md` for classification rules.

Architecture spec source: [plan/architect-plan-artifact-lifecycle.md](../architect-plan-artifact-lifecycle.md),
sections "Extended Context-Refinement Agent" and "Modifications to `context-refinement.md`
Agent Prompt".

## Objective

Update `plugins/python3-development/agents/context-refinement.md` to: (1) expand the
YOUR MISSION statement to include plan artifact freshness checking, (2) add Steps 5-8 to
the Process section, (3) add the `DIVERGENCE_REQUIRING_REVIEW` output block to the Output
Format section, and (4) add a reference to the canonical policy document.

## Required Inputs

- [plugins/python3-development/agents/context-refinement.md](../../plugins/python3-development/agents/context-refinement.md)
  — file to modify; read the full file before editing
- [plan/architect-plan-artifact-lifecycle.md](../architect-plan-artifact-lifecycle.md) —
  sections "Extended Context-Refinement Agent", "Modifications to context-refinement.md"
- `.claude/docs/plan-artifact-lifecycle.md` — must exist (T1 output); used as link target

## Requirements

1. Expand `## YOUR MISSION` to include plan artifact freshness check and divergence classification
2. Add policy reference paragraph after `## Context About Your Invocation`
3. Append Steps 5-8 (Locate Plan Artifacts, Collect Divergence Evidence, Classify Divergences,
   Annotate Plan Artifacts) after existing Step 4
4. Update Output Format section with freshness check counts in SUMMARY template
5. Add new "On Success - Intent Divergence Found" output block with DIVERGENCE_REQUIRING_REVIEW format

## Constraints

- Read the full file before editing — do not skip any section
- All new steps append after Step 4; do not renumber or modify Steps 1-4
- The annotation operation in Step 8 is append-only
- All new code fences must have language specifiers
- Surround all fenced code blocks with blank lines

## Expected Outputs

- File modified: `plugins/python3-development/agents/context-refinement.md`

## Acceptance Criteria

1. `## YOUR MISSION` includes "plan artifact freshness check"
2. `## YOUR MISSION` includes "design-refinement or intent-divergence"
3. A policy document reference link exists pointing to `.claude/docs/plan-artifact-lifecycle.md`
4. Steps 5, 6, 7, and 8 exist in the `## Process` section
5. Step 8 contains the `## Post-Implementation Annotations` annotation format
6. The Output Format section contains a `DIVERGENCE_REQUIRING_REVIEW` block
7. The SUMMARY template references design refinements and intent divergences
8. `uv run prek run --files plugins/python3-development/agents/context-refinement.md` exits 0
