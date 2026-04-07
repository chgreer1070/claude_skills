# Field Mapping Reference

```text
Backlog Item (via MCP)        →  GitHub Issue
  priority                    →  priority:* label
  description                 →  Issue body (story format)
  status                      →  status:* label
  plan                        →  Issue body Notes
  issue                       ←  written back after creation
  status                      →  Issue closed
```

The issue body template is built into the `backlog_update` MCP tool — it generates the story format automatically from the backlog item fields.
