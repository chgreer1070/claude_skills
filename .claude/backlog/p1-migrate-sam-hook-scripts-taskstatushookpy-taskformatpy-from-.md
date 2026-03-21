---
name: Migrate SAM hook scripts (task_status_hook.py, task_format.py) from python3-development to development-harness
description: "Migrate SAM hook scripts from python3-development to development-harness.\n\nThe hook scripts that the entire SAM workflow depends on exist ONLY in python3-development:\n- `plugins/python3-development/skills/implementation-manager/scripts/task_status_hook.py`\n- `plugins/python3-development/skills/implementation-manager/scripts/task_format.py`\n- `plugins/python3-development/skills/implementation-manager/scripts/get_task_context.py`\n\nThe dh `implementation-manager/scripts/` directory has only stale `.pyc` cache files with no source.\n\nThese scripts are language-agnostic (they parse YAML frontmatter and update timestamps). They must move to dh so that `start-task` and `implement-feature` hook paths resolve correctly after migration.\n\nAfter moving, update all hook path references in skill frontmatter that point to the old python3-development location."
metadata:
  topic: migrate-sam-hook-scripts-taskstatushookpy-taskformatpy-from-
  source: 'Session 2026-03-21: skill-migration-comparison report (.claude/reports/skill-migration-comparison-2026-03-21.md)'
  added: '2026-03-21'
  priority: P1
  type: Refactor
  status: open
  issue: '#958'
  last_synced: '2026-03-21T13:49:43Z'
  plan: plan/tasks-1-consolidate-sam-workflow-skills.md
---