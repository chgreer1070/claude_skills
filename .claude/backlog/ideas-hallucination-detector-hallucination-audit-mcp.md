---
name: 'hallucination-detector: Hallucination Audit MCP'
description: 'Expose `hallucination-audit-stop.js` logic as an MCP tool. Currently only runs as a Stop hook — an MCP server would let any agent or workflow request on-demand hallucination scanning of arbitrary text. Tools: `audit_text`, `audit_file`.'
metadata:
  topic: hallucination-detector-hallucination-audit-mcp
  source: MCP backlog audit 2026-02-23
  added: '2026-02-23'
  priority: Ideas
  type: Feature
  status: open
  issue: '#254'
---

**Suggested location**: `plugins/hallucination-detector/mcp/server.py` (reimplement core logic in Python) or `plugins/hallucination-detector/mcp/server.js` (wrap existing JS)
