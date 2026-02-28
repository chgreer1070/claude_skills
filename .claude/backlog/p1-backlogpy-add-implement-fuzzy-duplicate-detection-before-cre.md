---
name: 'backlog.py add: implement fuzzy duplicate detection before creating items'
description: The backlog.py add command does not check for fuzzy title duplicates against existing backlog items. It only checks for exact filename collisions. The SKILL.md expects the AI orchestrator to perform duplicate detection manually before invoking the script, but this should be built into the script itself. The add command should scan existing per-item files, compare titles using fuzzy matching (e.g. edit distance or token overlap), and warn/block if a near-duplicate is found.
metadata:
  topic: backlogpy-add-implement-fuzzy-duplicate-detection-before-cre
  source: Session observation
  added: '2026-02-27'
  priority: P1
  type: Bug
  status: open
  issue: '#311'
---