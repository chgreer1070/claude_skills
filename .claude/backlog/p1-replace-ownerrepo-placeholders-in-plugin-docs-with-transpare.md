---
name: Replace {OWNER/REPO} placeholders in plugin docs with transparent MCP tool calls
description: 'Plugin reference docs and SKILL.md files now have {OWNER/REPO} placeholders that require agents to do a lookup step. The MCP tools already handle repo discovery internally via discover_repo() — docs should use MCP tool instructions (which are repo-transparent) instead of raw commands with placeholders. Goal: zero extra steps for agents in other repos. The plugin should work without the agent needing to discover or pass the repo.'
metadata:
  topic: replace-ownerrepo-placeholders-in-plugin-docs-with-transpare
  source: 'Session observation 2026-03-20: user pointed out placeholders create extra work for agents in other repos'
  added: '2026-03-20'
  priority: P1
  type: Refactor
  status: open
  issue: '#915'
  last_synced: '2026-03-20T18:32:14Z'
---