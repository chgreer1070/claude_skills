---
name: 'backlog_sync and backlog_pull: add task=True background execution with ctx.report_progress()'
description: "backlog_sync and backlog_pull block the MCP client for the duration of all GitHub API calls (one per item). FastMCP v3 supports task=True on @mcp.tool which executes the tool as a background task — the client receives a task handle immediately and can poll status. Combined with ctx.report_progress(i, total), clients get a progress bar during batch operations.\n\nFiles affected: .claude/skills/backlog/backlog_core/server.py, pyproject.toml (add fastmcp[tasks] extra)\n\nChanges required:\n1. Add fastmcp[tasks] to optional dependencies in pyproject.toml\n2. Change @mcp.tool() to @mcp.tool(task=True) on backlog_sync and backlog_pull\n3. Add Progress dependency injection and emit ctx.report_progress(i, total) at each item iteration\n\nSource: fastmcp v3 docs servers/tasks.mdx — task=True + Progress injection for background tools"
metadata:
  topic: backlogsync-and-backlogpull-add-tasktrue-background-executio
  source: fastmcp-creator skill analysis of backlog_core/server.py
  added: '2026-03-07'
  priority: P2
  type: Feature
  status: open
  issue: '#511'
  last_synced: '2026-03-07T13:53:37Z'
---