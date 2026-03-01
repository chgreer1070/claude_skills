---
name: 'ASYNC240 vs ruff-format conflict: pathlib auto-conversion breaks async tests'
description: 'ruff-format auto-converts os.path.exists() to pathlib.Path(...).exists(), which then triggers ASYNC240 (pathlib methods forbidden in async functions). This creates a loop: write os.path.exists -> ruff-format converts to pathlib -> ASYNC240 rejects it -> developer uses workaround. Observed during backlog MCP scenario testing (#328). Workaround used: backlog_dir.glob() pattern instead of Path.exists(). Need: either a ruff config to suppress the os.path->pathlib conversion in async contexts, or a documented pattern for async-safe file existence checks.'
metadata:
  topic: async240-vs-ruff-format-conflict-pathlib-auto-conversion-bre
  source: 'session observation during #328 implementation'
  added: '2026-03-01'
  priority: P2
  type: Bug
  status: open
  issue: '#334'
  last_synced: '2026-03-01T13:20:49Z'
---