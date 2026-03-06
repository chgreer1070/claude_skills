---
name: Migrate SAM task tracking from local markdown files to GitHub sub-issues via backlog MCP
description: "Currently the SAM workflow splits task tracking across two systems:\n- GitHub Issues (via backlog MCP) for stories/backlog items\n- Local `plan/tasks-*.md` files for task status, with `implementation_manager.py` and `task_status_hook.py` managing state\n\n**Proposed architecture:** Unify everything in GitHub Issues using sub-issues.\n- Stories = GitHub Issues (existing)\n- Tasks within a story = GitHub sub-issues of the story issue\n- Research artifacts = tracked as linked issues or issue comments\n- Backlog MCP = extended to handle sub-issue CRUD, status transitions, and readiness queries\n\n**What needs to change:**\n1. Extend backlog MCP server to support sub-issue creation, status query, and dependency-based readiness logic\n2. Replace `implementation_manager.py` task status queries with MCP calls to GitHub sub-issues\n3. Replace `task_status_hook.py` file edits with GitHub API calls (via MCP or CLI) on `PostToolUse`/`SubagentStop` events\n4. Add research artifact tracking (currently absent) as linked issues on the story\n5. Decide offline/network dependency tradeoff — current system works without GitHub; sub-issues require network on every status check\n\n**Benefits:**\n- Single source of truth — no drift between local files and GitHub state\n- Removes accidental complexity (local markdown task files existed because sub-issues weren't prioritized)\n- Better visibility for collaborators\n- Backlog MCP already does CRUD on issues — extending to sub-issues is natural\n\n**Key risk:** Hook scripts fire frequently (every Write/Edit/Bash in a task session); each hook becoming a GitHub API call adds latency and network dependency."
metadata:
  topic: migrate-sam-task-tracking-from-local-markdown-files-to-githu
  source: Architecture discussion — session 2026-03-06
  added: '2026-03-06'
  priority: P1
  type: Refactor
  status: open
  issue: '#480'
  last_synced: '2026-03-06T06:16:23Z'
---