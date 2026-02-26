---
name: 'kaizen: MCP consolidation analysis'
description: 'The plugin currently runs two MCP servers (`kaizen-duckdb` via mcp-server-motherduck,
  `kaizen-analysis` via server.py) plus a standalone CLI script (`sentiment-score.py`).
  Investigate: (1) What does each MCP server provide that the other cannot? Can they
  be merged into a single server? (2) Why is `sentiment-score.py` a standalone script
  rather than an MCP tool inside `server.py`? What would be gained or lost by moving
  scoring into the MCP server (always-on scoring, no manual invocation, lock ownership)?
  (3) Is there a clean boundary between "batch processing" (script) and "query/serve"
  (MCP) that should be preserved?

  **Decision needed**: Consolidate vs. keep separate, with rationale.'
metadata:
  topic: kaizen-mcp-consolidation-analysis
  source: Design session 2026-02-20
  added: '2026-02-20'
  priority: P2
  type: Feature
  status: open
---

**Suggested location**: `plugins/agentskill-kaizen/`

**Decision needed**: Consolidate vs. keep separate, with rationale.
