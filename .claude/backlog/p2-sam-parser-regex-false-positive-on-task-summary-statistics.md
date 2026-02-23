---
name: "SAM: Parser regex false positive on '## Task Summary Statistics'"
description: The widened task header regex `^#{2,3}\s+Task:?\s+([A-Za-z0-9.]+)[:\s-]+(.+)$` in `implementation_manager.py` matches `## Task Summary Statistics` as task ID 'Summary' with title 'Statistics'. The regex needs a negative lookahead or post-parse filter to exclude non-task sections. Observed when parsing `plan/tasks-1-plugin-linter.md`.
metadata:
  topic: sam-parser-regex-false-positive-on-task-summary-statistics
  source: Migration proof-of-concept (2026-02-13)
  added: '2026-02-13'
  priority: P2
  type: Feature
  status: open
---
