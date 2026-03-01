---
name: migrate backlog to mcp server system
description: "The backlog-mcp FastMCP server is implemented (10 tools, 382 tests passing) and a CLI-to-MCP migration map exists at .claude/skills/backlog/CLI_TO_MCP_MIGRATION.md identifying ~40 files and ~34 direct CLI invocations that need updating. Tasks: (1) register backlog-mcp in .mcp.json, (2) update CLAUDE.md Backlog Operations policy section, (3) update session hooks (session-start-backlog.cjs, stop-backlog-reminder.cjs), (4) update skill files — work-backlog-item (19 invocations), create-backlog-item, groom-backlog-item, group-items-to-milestone, (5) update agent files — backlog-item-groomer, (6) update backlog/SKILL.md and backlog-tools-administrator/SKILL.md docs, (7) close the idea item 'Convert backlog.py into MCP server'. GitHub Actions backlog-sync.yml stays as CLI — CI has no MCP client."
metadata:
  topic: migrate-backlog-to-mcp-server-system
  source: Agent task — auto-derived from backlog MCP server completion
  added: '2026-03-01'
  priority: P1
  type: Feature
  status: open
  issue: '#329'
---