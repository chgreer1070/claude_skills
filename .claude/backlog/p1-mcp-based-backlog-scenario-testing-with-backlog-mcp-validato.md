---
name: MCP-based backlog scenario testing with backlog-mcp-validator and backlog-item-groomer
description: Build scenario-based integration tests for the backlog-mcp FastMCP server, organized by the skill/agent workflow that generates each call pattern. 20 scenarios covering create-backlog-item (1), work-backlog-item browse/plan/status/close/resolve (12), groom-backlog-item (4), group-items-to-milestone (1), backlog-item-groomer agent (1), sync+pull (2). Plus 4 error paths (close without checklist, view nonexistent, add duplicate, list empty) and 3 full lifecycle tests (create→close, create→resolve+cleanup, stale discovery). Tests use in-memory FastMCP Client through full operations layer (mocking only at github.py and filesystem boundary), verifying the exact response shapes that each skill reads from tool output. Design documented in session and migration map at .claude/skills/backlog/CLI_TO_MCP_MIGRATION.md.
metadata:
  topic: mcp-based-backlog-scenario-testing-with-backlog-mcp-validato
  source: Session observation
  added: '2026-03-01'
  priority: P1
  type: Feature
  status: open
---

