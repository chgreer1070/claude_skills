---
name: Resolve 48 pre-existing ty (Astral type checker) diagnostics
description: "ty v0.0.16 reported 48 diagnostics. By v0.0.17 with existing `extra-paths` config, count dropped to 34 warnings (0 errors), all in `plugins/agentskill-kaizen/tests/`. Root causes: FastMCP `@mcp.tool()` decorator returns `FunctionTool` (ty sees as non-callable), and `ModuleType` dynamic attribute stubs. Suppressed `call-non-callable` and `unresolved-attribute` to `'ignore'` in test-file override scope. Added `typecheck-ty` CI job in `allowed-failures` for conservative rollout."
metadata:
  topic: resolve-48-pre-existing-ty-astral-type-checker-diagnostics
  source: '`uv run ty check .` run during session 2026-02-11'
  added: '2026-02-23'
  priority: completed
  type: Feature
  status: done
---
