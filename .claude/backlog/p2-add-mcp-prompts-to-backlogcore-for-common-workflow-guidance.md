---
name: Add MCP prompts to backlog_core for common workflow guidance
description: "backlog_core defines no `@mcp.prompt` components. MCP prompts are reusable, parameterized message templates that guide AI clients through multi-step workflows. They are distinct from tools — clients render prompts as conversation starters, not function calls.\n\nbacklog_core workflows have natural prompt candidates:\n- `add_backlog_item(title, description, type)` → prompt that guides the AI to provide the correct fields and call backlog_add\n- `groom_item(selector)` → prompt that frames the grooming workflow for a specific item\n- `review_priority_section(section)` → prompt for reviewing all items in a priority section\n- `close_or_resolve_item(selector)` → prompt that guides the distinction between close (dismiss) and resolve (complete)\n\nFiles affected: `.claude/skills/backlog/backlog_core/server.py`\n\nSource: FastMCP v3 docs `servers/prompts.mdx` — `@mcp.prompt` registers a reusable message template; clients invoke via `prompts/get`."
metadata:
  topic: add-mcp-prompts-to-backlogcore-for-common-workflow-guidance
  source: fastmcp-creator skill review of backlog_core/server.py
  added: '2026-03-06'
  priority: P2
  type: Feature
  status: open
  issue: '#467'
  last_synced: '2026-03-06T05:22:47Z'
---