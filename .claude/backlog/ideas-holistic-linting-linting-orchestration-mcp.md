---
name: 'holistic-linting: Linting Orchestration MCP'
description: 'Wrap `holistic_lint.py` as an MCP tool. Currently agents must invoke linting via shell. An MCP server would expose structured linting results (errors, warnings, fixes applied) as tool outputs. Tools: `lint_files`, `list_lint_errors`, `auto_fix`.'
metadata:
  topic: holistic-linting-linting-orchestration-mcp
  source: MCP backlog audit 2026-02-23
  added: '2026-02-23'
  priority: Ideas
  type: Feature
  status: open
  issue: '#256'
---

**Suggested location**: `plugins/holistic-linting/mcp/server.py`
