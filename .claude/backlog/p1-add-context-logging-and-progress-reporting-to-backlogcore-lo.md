---
name: Add Context logging and progress reporting to backlog_core long-running tools
description: "No tool in backlog_core/server.py uses `ctx: Context`. Operations like `backlog_sync`, `backlog_pull`, and `backlog_groom` make multiple sequential GitHub API calls but emit zero progress feedback to the client. The client sees nothing until the operation completes or errors.\n\nFastMCP v3 provides `ctx.info()`, `ctx.warning()`, `ctx.report_progress(progress, total)` for real-time feedback during tool execution. These map directly to MCP protocol log messages and progress notifications.\n\nFiles affected: `.claude/skills/backlog/backlog_core/server.py`\n\nWork required:\n- Add `ctx: Context` parameter to backlog_sync, backlog_pull, backlog_groom, backlog_normalize\n- Emit `ctx.info()` at key milestones (e.g., 'Fetching open issues…', 'Syncing item: {title}')\n- Use `ctx.report_progress(i, total)` for batch operations where total is known\n- Use `ctx.warning()` to surface warnings currently buried in `out.warnings`\n\nSource: FastMCP v3 docs `servers/context.mdx` — `ctx.info()`, `ctx.warning()`, `ctx.report_progress()` send real-time messages to the MCP client."
metadata:
  topic: add-context-logging-and-progress-reporting-to-backlogcore-lo
  source: 'GitHub Issue #465'
  added: '2026-03-06'
  priority: P1
  type: Feature
  status: needs-grooming
  issue: '#465'
  last_synced: '2026-03-06T05:50:42Z'
---

## Story

As a **developer using Claude Code skills**, I want to **add context logging and progress reporting to backlog_core long-running tools** so that **the tooling becomes more capable and complete**.

## Description

No tool in backlog_core/server.py uses `ctx: Context`. Operations like `backlog_sync`, `backlog_pull`, and `backlog_groom` make multiple sequential GitHub API calls but emit zero progress feedback to the client. The client sees nothing until the operation completes or errors.

FastMCP v3 provides `ctx.info()`, `ctx.warning()`, `ctx.report_progress(progress, total)` for real-time feedback during tool execution. These map directly to MCP protocol log messages and progress notifications.

Files affected: `.claude/skills/backlog/backlog_core/server.py`

Work required:
- Add `ctx: Context` parameter to backlog_sync, backlog_pull, backlog_groom, backlog_normalize
- Emit `ctx.info()` at key milestones (e.g., "Fetching open issues…", "Syncing item: {title}")
- Use `ctx.report_progress(i, total)` for batch operations where total is known
- Use `ctx.warning()` to surface warnings currently buried in `out.warnings`

Source: FastMCP v3 docs `servers/context.mdx` — `ctx.info()`, `ctx.warning()`, `ctx.report_progress()` send real-time messages to the MCP client.

## Acceptance Criteria

- [ ] Work matches description
- [ ] Plan or implementation complete

## Context

- **Source**: fastmcp-creator skill review of backlog_core/server.py
- **Priority**: P1
- **Added**: 2026-03-06
- **Research questions**: None