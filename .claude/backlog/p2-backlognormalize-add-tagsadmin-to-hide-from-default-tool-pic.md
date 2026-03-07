---
name: "backlog_normalize: add tags={'admin'} to hide from default tool pickers"
description: "backlog_normalize is a one-off maintenance operation that reorganizes all local files. It should not appear alongside operational tools (add, list, view, etc.) in standard MCP tool pickers. FastMCP v3 supports tags= on @mcp.tool — clients can filter by tag to show only tools matching their context.\n\nFiles affected: .claude/skills/backlog/backlog_core/server.py\n\nChange required: @mcp.tool() -> @mcp.tool(tags={'admin'}) on backlog_normalize\n\nThis is a 1-line change. No logic changes required.\n\nSource: fastmcp v3 docs servers/tools.mdx — tags= for tool visibility filtering"
metadata:
  topic: backlognormalize-add-tagsadmin-to-hide-from-default-tool-pic
  source: fastmcp-creator skill analysis of backlog_core/server.py
  added: '2026-03-07'
  priority: P2
  type: Feature
  status: open
  issue: '#512'
  last_synced: '2026-03-07T13:53:42Z'
---