---
name: Migrate backlog MCP GitHub read operations from PyGithub REST to PyGithub GraphQL API
description: "**Problem**: The backlog MCP server uses PyGithub's REST methods (repo.get_issues, repo.get_issue, issue.edit, etc.) for GitHub operations. PyGithub v2.x includes a GraphQL client (documented at https://pygithub.readthedocs.io/en/v2.8.1/graphql.html) that can fetch issue + labels + body + status in a single query instead of 2-3 REST round-trips. backlog_add has an N+1 pattern with up to 3 repo.get_label() prefetch calls per issue creation. from_github=True full refresh fetches the entire issue list via paginated REST.\n\n**Where it lives**: .claude/skills/backlog/backlog_core/github.py — single module owns GitHub I/O via PyGithub. The migration stays within PyGithub — replacing REST method calls with GraphQL queries using the same library's built-in GraphQL client.\n\n**Success looks like**: Read operations (list, view, batch status, reconciliation) use PyGithub's GraphQL client. Single query fetches issue + labels + body + status. Write operations (create, close, update labels) use GraphQL mutations where supported, REST where not. API call count reduced for common operations. No new dependencies — PyGithub is already installed.\n\n**How you'll know it's working**: backlog_list(from_github=True) makes 1 GraphQL query instead of N paginated REST calls. backlog_view returns labels+body+status in 1 call. backlog_add label prefetch eliminated.\n\n**Reference**: https://pygithub.readthedocs.io/en/v2.8.1/graphql.html — PyGithub's built-in GraphQL API documentation.\n\n**Audit reference**: .claude/reports/backlog-github-api-audit.md (per-operation REST breakdown from this session)"
metadata:
  topic: migrate-backlog-mcp-github-operations-from-rest-pygithub-to-
  source: Session observation — GraphQL audit revealed REST-only GitHub API usage with N+1 patterns
  added: '2026-03-17'
  priority: P1
  type: Refactor
  status: open
  issue: '#773'
  last_synced: '2026-03-17T18:58:06Z'
---