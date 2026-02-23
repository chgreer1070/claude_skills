---
name: 'development-harness: Remove hardcoded machine path and fix version drift'
description: Contains a hardcoded machine-specific path (likely `/home/user/...` or similar) that won't work on other systems. Version references have drifted from actual tool versions. Role table has inconsistencies between documented and actual roles.
metadata:
  topic: development-harness-remove-hardcoded-machine-path-and-fix-ve
  source: Plugin code review session 2026-02-21
  added: '2026-02-21'
  priority: P2
  type: Feature
  status: open
---
**Files**: `plugins/development-harness/` (SKILL.md and reference files)
