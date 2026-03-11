---
name: Add unit tests for session-historian new commands and helpers
description: 'The session-historian enhancement (session-historian-enhance) added four new commands (errors, tools, irritation, current-path), a shared _resolve_session helper, and seven private helper functions. None of these have unit tests. The helper functions are pure data transforms well-suited to unit testing. Project standard requires 80% minimum coverage. Success: pytest suite covering all new helpers and commands, ruff and ty clean.'
metadata:
  topic: add-unit-tests-for-session-historian-new-commands-and-helper
  source: Code review finding — session-historian-enhance implementation review 2026-03-11
  added: '2026-03-11'
  priority: P2
  type: Chore
  status: open
  plan: plan/tasks-34-session-historian-enhance-followup-1.md
---