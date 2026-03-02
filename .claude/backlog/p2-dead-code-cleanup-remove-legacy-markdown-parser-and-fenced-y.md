---
name: 'Dead code cleanup: remove legacy markdown parser and fenced YAML recovery from implementation_manager'
description: 'Legacy markdown parser (## Task N: + **Bold**: fields), fenced YAML recovery path in parse_task_content, _update_legacy_timestamp/_legacy_field_to_yaml in task_status_hook.py, and FIELD_PARSERS registry are dead code now that all task files use directory format with bare YAML frontmatter. Done = those code paths deleted, FIELD_PARSERS registry removed, _depth recursion guard removed, and all tests pass.'
metadata:
  topic: dead-code-cleanup-remove-legacy-markdown-parser-and-fenced-y
  source: 'Session observation — PR #383 converted the last two mixed-format files'
  added: '2026-03-02'
  priority: P2
  type: Refactor
  status: open
---

