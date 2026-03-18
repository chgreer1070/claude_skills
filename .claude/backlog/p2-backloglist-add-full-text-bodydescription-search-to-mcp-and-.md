---
name: 'backlog_list: Add full-text body/description search to MCP and CLI'
description: "backlog_list filters by title, type, topic, section, and status — but has no way to search item bodies or descriptions. Items that describe a concept (e.g. 'migrate python3-development steps into development-harness') but don't contain the search terms in their title are invisible to the MCP. This caused a failed investigation where the correct item existed but couldn't be found via any available filter.\n\nAdd a `body` (or `search`) parameter to backlog_list that performs full-text substring search across the item description and body sections (Groomed, Research, etc.). Should work in both the MCP tool and the CLI (`backlog.py list --search '...'`)."
metadata:
  topic: backloglist-add-full-text-bodydescription-search-to-mcp-and-
  source: Session observation — backlog_list title-only filter missed items during investigation
  added: '2026-03-18'
  priority: P2
  type: Feature
  status: open
  issue: '#842'
  last_synced: '2026-03-18T18:09:54Z'
---