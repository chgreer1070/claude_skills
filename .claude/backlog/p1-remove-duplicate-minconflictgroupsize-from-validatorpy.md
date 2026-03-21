---
name: Remove duplicate _MIN_CONFLICT_GROUP_SIZE from validator.py
description: _MIN_CONFLICT_GROUP_SIZE constant is defined in both backlog_core/operations.py and dispatch_schema/core/validator.py. T01 of simplify review fixes was supposed to remove the duplicate from validator.py and import from the canonical location but did not complete this change.
metadata:
  topic: remove-duplicate-minconflictgroupsize-from-validatorpy
  source: 'Code review of Issue #938 — simplify review fixes'
  added: '2026-03-21'
  priority: P1
  type: Bug
  status: open
  issue: '#952'
  last_synced: '2026-03-21T04:44:04Z'
---