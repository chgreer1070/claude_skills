---
name: Fix mcp scalar state-machine edge case in FM009 guard
description: "The FM009 state machine in `plugins/plugin-creator/scripts/plugin_validator.py` sets `current_top_level_key = 'mcp'` for scalar forms (`mcp: null`, `mcp: false`) just as it does for block mappings. Scalar forms have no indented children, so any subsequent indented line belonging to a different block key is incorrectly treated as inside `mcp:` and skipped by the ecosystem guard. The fix must distinguish scalar vs. block top-level lines so that `current_top_level_key` is not carried forward after a scalar `mcp:` line. A new unit test exercising `mcp: null` followed by a Claude Code field with a colon must be added, and all 26 existing tests must continue to pass."
metadata:
  topic: fix-mcp-scalar-state-machine-edge-case-in-fm009-guard
  source: Agent task — code review follow-up from plan/tasks-26-multi-ecosystem-plugin-creator-followup-2.md
  added: '2026-03-06'
  priority: P1
  type: Bug
  status: open
  plan: plan/tasks-26-multi-ecosystem-plugin-creator-followup-2.md
  issue: '#517'
---