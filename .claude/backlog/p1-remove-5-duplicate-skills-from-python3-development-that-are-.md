---
name: Remove 5 duplicate skills from python3-development that are canonical in development-harness
description: "Remove identical duplicate skills from python3-development that already exist in development-harness.\n\nThree skills are byte-for-byte identical in both plugins:\n- `clear-cove-task-design`\n- `generate-task`\n- `planner-rt-ica`\n\nTwo more have dh as the canonical evolved version:\n- `validation-protocol` (dh generalized Python examples to language manifest placeholders)\n- `implementation-manager` SKILL.md (dh uses `sam` CLI, python3-dev uses outdated `implementation_manager.py` CLI)\n\nAction: Remove the python3-development copies. The dh versions are canonical."
metadata:
  topic: remove-5-duplicate-skills-from-python3-development-that-are-
  source: 'Session 2026-03-21: skill-migration-comparison report (.claude/reports/skill-migration-comparison-2026-03-21.md)'
  added: '2026-03-21'
  priority: P1
  type: Refactor
  status: open
  issue: '#957'
  last_synced: '2026-03-21T13:49:37Z'
  plan: plan/tasks-1-consolidate-sam-workflow-skills.md
---