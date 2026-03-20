---
name: Complete GraphQL migration for backlog MCP server
description: 'The backlog MCP server (backlog_core/) uses PyGitHub REST API for milestones, issues, PRs, and most operations. Only label lookups (commits 32e5597c, 7280a8ff) and Projects V2 operations use GraphQL. PR #455 (github-graphql-migration branch) only migrated daily-releases scripts, not the backlog server.\n\nOperations still on REST (PyGitHub):\n- repository.get_milestones()\n- repository.get_issues()\n- Issue creation, editing, commenting\n- PR listing\n- Label CRUD (partially — lookup migrated, CRUD not verified)\n\nGraphQL migration eliminates the PyGitHub REST dependency for these operations and provides consistent error handling across all GitHub API calls.'
metadata:
  topic: complete-graphql-migration-for-backlog-mcp-server
  source: 'Session 2026-03-20: discovered milestones, issues, PRs still use PyGitHub REST API. Only labels and Projects V2 were migrated to GraphQL.'
  added: '2026-03-20'
  priority: P1
  type: Refactor
  status: open
---

