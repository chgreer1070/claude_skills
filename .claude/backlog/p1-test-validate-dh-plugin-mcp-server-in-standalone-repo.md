---
name: 'test: Validate dh plugin MCP server in standalone repo'
description: "Verify that the bundled backlog MCP server starts correctly when the dh plugin is installed on a project that has no pre-existing backlog_core workspace entry. The .mcp.json uses ${CLAUDE_PLUGIN_ROOT} — this must be validated outside the development repo.\n\nTest steps:\n1. Use a separate repo with no .claude/skills/backlog/ and no uv workspace entry for backlog_core\n2. Install the dh plugin via /plugin install\n3. Verify mcp__plugin_dh_backlog__* tools appear in the session\n4. Call backlog_list and confirm it returns successfully"
metadata:
  topic: test-validate-dh-plugin-mcp-server-in-standalone-repo
  source: User request
  added: '2026-03-19'
  priority: P1
  type: Feature
  status: open
  issue: '#851'
  last_synced: '2026-03-19T03:19:08Z'
---