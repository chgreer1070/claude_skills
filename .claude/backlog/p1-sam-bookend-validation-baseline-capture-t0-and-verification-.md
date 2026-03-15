---
name: SAM bookend validation — baseline capture (T0) and verification gate (TN) as mandatory plan tasks
description: "Every SAM plan needs two mandatory bookend tasks that bracket implementation work. T0 (baseline capture) runs before any implementation — it executes the plan's acceptance criteria against the current codebase and records what passes and fails. TN (verification gate) runs after all implementation tasks — it re-runs the same checks and compares against the baseline. This is TDD at the plan level.\n\nThe problem: the current swarm-task-planner creates implementation tasks and test-writing tasks but never creates a 'prove it works' task. The feature-verifier runs as a post-completion quality gate outside the plan, but it checks structure (task count, field presence) not behavior (does the feature actually work end-to-end). This allowed a converter that destroyed content to pass validation.\n\nWhat's needed:\n1. Plan schema: add structured acceptance_criteria field with check_command, expected_baseline, expected_final per criterion. Add goal and context fields.\n2. swarm-task-planner: auto-generate T0 (baseline) and TN (verification gate) from the acceptance criteria.\n3. T0 agent: runs each check command, records actual output, writes structured baseline YAML.\n4. TN agent: re-runs baseline checks, compares results, produces pass/fail/regressed report.\n5. Verdict: if any baseline-failing check is still failing after implementation, the plan is incomplete — more iterations needed.\n\nWhat success looks like: running /implement-feature produces a T0-baseline.yaml before implementation starts and a TN-verification.yaml after it completes. The verification report shows which checks flipped from failing to passing.\n\nHow you'll know it's working: the content-destroyer bug (readers stripping markdown body during conversion) would have been caught by TN — the verification check 'load .md, write .yaml, compare content length' would have failed."
metadata:
  topic: sam-bookend-validation-baseline-capture-t0-and-verification-
  source: Session observation — feature verification passed structural checks but missed behavioral failure (content loss during format conversion, 2026-03-15)
  added: '2026-03-15'
  priority: P1
  type: Feature
  status: open
  issue: '#718'
  last_synced: '2026-03-15T05:20:42Z'
---