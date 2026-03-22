---
name: Add append=True parameter to backlog_groom MCP tool for incremental section writes
description: "Add append=True parameter to backlog_groom MCP tool's section write mode.\n\nCurrently backlog_groom(selector, section, content) replaces the entire section content. The quality vigilance concerns tracking (added in fc5c449d) needs to append individual concern lines to a ## Concerns section as agents report them — each agent reports one concern, and they accumulate.\n\nWithout append, each backlog_groom call overwrites the previous concerns. With append=True, the content is appended to the existing section content (with a newline separator) instead of replacing it.\n\nImplementation: in the backlog_groom tool handler, when append=True and the section already exists, read the existing section content, concatenate the new content, then write the combined result.\n\nConsumers: implement-feature SKILL.md Step 4 (concern collection from agent outputs)."
metadata:
  topic: add-appendtrue-parameter-to-backloggroom-mcp-tool-for-increm
  source: 'Session 2026-03-22: concerns tracking requires append-mode for backlog_groom section writes'
  added: '2026-03-22'
  priority: P1
  type: Feature
  status: open
  issue: '#980'
  last_synced: '2026-03-22T03:27:56Z'
---