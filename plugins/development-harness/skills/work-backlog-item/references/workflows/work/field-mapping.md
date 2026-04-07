# Field Mapping Reference

```text
~/.dh/projects/{slug}/backlog/    →  GitHub Issue
  metadata.priority →  priority:* label
  Description       →  Issue body (story format)
  metadata.status   →  status:* label
  metadata.plan     →  Issue body Notes
  metadata.issue    ←  written back after creation
  metadata.status   →  Issue closed
```

The issue body template is built into the `backlog_update` MCP tool — it generates the story format automatically from the per-item file fields.
