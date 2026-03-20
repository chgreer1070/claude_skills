---
name: Fix wrong exception type in test_atomic_write_cleans_up_temp_file_on_failure
description: In packages/sam_schema/, test_writers_new.py::TestAtomicWriteSafety::test_atomic_write_cleans_up_temp_file_on_failure asserts PermissionError but the implementation raises OSError. This mismatch causes uv run pytest packages/sam_schema/ to exit non-zero. This is a pre-existing bug that predates the deduplicate-agents-phase4 work — the test assertion does not match the exception type the implementation actually raises.
metadata:
  topic: fix-wrong-exception-type-in-testatomicwritecleansuptempfileo
  source: Agent task — auto-derived from task description (pre-existing bug, predates deduplicate-agents-phase4)
  added: '2026-03-20'
  priority: P1
  type: Bug
  status: open
  plan: plan/P779-deduplicate-agents-phase4-followup-1.yaml
---