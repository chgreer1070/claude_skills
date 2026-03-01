---
name: 'Task file format: evaluate pure YAML multi-document notation and enforce script-only writes'
description: Current task files use markdown with YAML frontmatter. Consider converting to pure YAML to leverage multi-document YAML notation (--- separators). Additionally, enforce that task data files are only written via scripts (backlog.py, implementation_manager.py, split_task_file.py, task_status_hook.py) — never manually edited by agents. The swarm-task-planner agent generated tasks with YAML inside fenced code blocks which the parser couldn't read, causing null agents and NOT_STARTED defaults. This suggests the generation pipeline needs format validation.
metadata:
  topic: task-file-format-evaluate-pure-yaml-multi-document-notation-
  source: Not specified
  added: '2026-03-01'
  priority: P2
  type: Enhancement
  status: open
  issue: '#320'
  last_synced: '2026-03-01T02:38:06Z'
---