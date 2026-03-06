---
name: Fix stale input shapes count in test_fm009_guard docstring
description: The test_fm009_guard method docstring in test_frontmatter_fixes.py referenced '7 input shapes' while the actual parametrize decorator and class docstring both reflect 9 cases. The literal count drifted as cases were added (case8, case9) without updating the method-level docstring. The method docstring should either use the correct count or be rephrased to avoid a literal count that will drift again.
metadata:
  topic: fix-stale-input-shapes-count-in-testfm009guard-docstring
  source: Code review — tasks-28 followup analysis (2026-03-06)
  added: '2026-03-06'
  priority: P2
  type: Docs
  status: open
  plan: plan/tasks-29-multi-ecosystem-plugin-creator-followup-4.md
---