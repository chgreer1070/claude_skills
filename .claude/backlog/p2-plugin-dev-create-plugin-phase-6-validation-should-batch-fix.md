---
name: '`/plugin-dev:create-plugin` Phase 6 validation should batch fixes by file, not by finding'
description: Phase 6 collected findings from 3 parallel review agents, then applied fixes one finding at a time. This resulted in SKILL.md being edited 3 separate times (description rewrite, SQL removal, MCP server name fix) when a single pass through the file would have applied all fixes together. The workflow should group all findings by file, then make one editing pass per file. Reduces Edit tool calls and context consumed by repeated reads.
metadata:
  topic: plugin-dev-create-plugin-phase-6-validation-should-batch-fix
  source: agentskill-kaizen plugin build Phase 6 (2026-02-18)
  added: '2026-02-18'
  priority: P2
  type: Feature
  status: open
---
