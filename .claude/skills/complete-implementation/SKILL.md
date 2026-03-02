---
name: complete-implementation
argument-hint: <task-file-path>
user-invocable: true
description: "Holistic completion workflow after a feature's tasks are marked COMPLETE: code review, feature verification, integration check, documentation drift audit/update, and context refinement. Creates follow-up task files when issues are found."
metadata:
  version: "1.0.0"
  last_updated: "2026-02-28"
  source: python3-development plugin (local adaptation)
---
# Complete Implementation (Quality Gates + Recursion)

You MUST validate that the implemented feature meets its goals and quality gates. This workflow is recursive: if follow-up task files are created, re-run `implement-feature` on them and then re-run this skill.

<task_file>
$ARGUMENTS
</task_file>

---

## Phase 1: Code Review

Launch `code-reviewer` with the task file path.

---

## Phase 2: Feature Verification (goal-backward)

Launch `feature-verifier` with the task file path. If the task file contains `issue-classification` metadata, include it in the agent prompt so the feature verifier can apply proportional verification checks.

---

## Phase 3: Integration Check

Launch `integration-checker` with the task file path.

---

## Phase 4: Documentation Drift Audit

Launch `doc-drift-auditor` with the task file path (audit-only).

---

## Phase 5: Documentation Update (if drift found)

If drift exists or docs must be updated for the feature, launch `service-docs-maintainer`.

---

## Phase 6: Context Refinement

Launch `context-refinement` to update the task file Context Manifest with discoveries from implementation AND perform a plan artifact freshness check against the feature-context and architect spec. The agent compares key claims in plan artifacts against the actual implementation and classifies findings as design-refinement or intent-divergence (see [.claude/docs/plan-artifact-lifecycle.md](./../../docs/plan-artifact-lifecycle.md)).

---

## Post-Phase-6: Surface Divergence Findings

After Phase 6 completes, check the `context-refinement` agent output for a `DIVERGENCE_REQUIRING_REVIEW` block.

If present, include in the final output to the human:

```text
Plan artifacts have intent divergences requiring your review.
See: [annotated artifact paths from agent output]
Divergences:
  [list from DIVERGENCE_REQUIRING_REVIEW block]
```

This is informational, not blocking. The human reviews at their discretion.
If absent, no additional output is needed — the feature proceeds normally.

---

## Recursive Follow-up Handling

If Phase 1 creates follow-up task files (expected naming: `plan/tasks-{N}-{slug}-followup-{k}.md`), run:

```text
Skill(skill="implement-feature", args="{followup_task_file_path}")
```

Then re-run `complete-implementation` on the follow-up task file.
