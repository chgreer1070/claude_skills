---
name: 'complete-implementation/SKILL.md: migrate 3 CLI invocations to MCP tool calls'
description: 'The complete-implementation skill still uses 3 uv run backlog.py CLI invocations (lines 112, 126, 138) for backlog list/update operations during the recursive follow-up handling workflow. These should be migrated to mcp__backlog__* tool calls for consistency with the rest of the ecosystem (completed in issue #329). Low urgency since the CLI still works; MCP is preferred.'
metadata:
  topic: complete-implementationskillmd-migrate-3-cli-invocations-to-
  source: Quality gate integration check — discovered during backlog CLI-to-MCP migration (#329)
  added: '2026-03-02'
  priority: p2
  type: enhancement
  status: open
  issue: '#397'
  last_synced: '2026-03-02T07:03:52Z'
  plan: plan/tasks-20-backlog-mcp-migration-followup-1.md
---