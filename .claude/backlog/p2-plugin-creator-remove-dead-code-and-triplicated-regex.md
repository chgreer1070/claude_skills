---
name: 'plugin-creator: Remove dead code and triplicated regex'
description: Contains triplicated regex patterns (same regex defined 3 times), a dead `skipped` list that is populated but never read, an unused `sum()` call, and HK005 warning is incorrectly treated as an error in certain code paths. Also has a `noqa BLE001` suppression that should be addressed per CLAUDE.md linting policy.
metadata:
  topic: plugin-creator-remove-dead-code-and-triplicated-regex
  source: Plugin code review session 2026-02-21
  added: '2026-02-21'
  priority: P2
  type: Feature
  status: open
---
**Files**: `plugins/plugin-creator/` (scripts and skill files)
