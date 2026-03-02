---
name: Abstract GitHub Issues layer from backlog MCP server into pluggable backend
description: 'The backlog MCP server (10 tools, 382+ tests) is tightly coupled to GitHub Issues as its issue-tracking backend. Every operation — add, list, sync, close, resolve, groom — assumes GitHub Issues API. This prevents using the backlog system with GitLab, Jira, databases, or alternative agent task systems like GSD (get-shit-done), Superpowers, or Beads. Success: a clean backend protocol/interface with 2+ working backends shipped (GitHub Issues as default + at least one alternative like Beads graph tracker or SQLite) proving the abstraction works. You know it works when the same 10 MCP tools produce equivalent behavior against a different backend with zero changes to skill workflows or MCP tool signatures. Research refs: research/agent-frameworks/get-shit-done.md, research/agent-frameworks/superpowers.md, research/task-management/beads.md.'
metadata:
  topic: abstract-github-issues-layer-from-backlog-mcp-server-into-pl
  source: User request
  added: '2026-03-02'
  priority: P2
  type: Feature
  status: open
---

