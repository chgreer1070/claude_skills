---
name: Streamline backlog URL/issue-number handling to use backlog.py instead of gh CLI
description: "Skills (groom-backlog-item, work-backlog-item) and backlog.py should parse GitHub issue URLs (e.g., https://github.com/Jamie-BitFlight/claude_skills/issues/249) and bare issue numbers (e.g., 249 or #249) directly, using backlog.py's own HTTP/API logic instead of requiring gh CLI installation. Currently, every time an issue URL or number is given, the system tries gh CLI, fails, installs gh, checks info using gh, then starts work. This should be one step. Success: one-step issue lookup with no gh dependency for reading/viewing issues."
metadata:
  topic: streamline-backlog-urlissue-number-handling-to-use-backlogpy
  source: User request
  added: '2026-02-28'
  priority: P0
  type: Feature
  status: open
  issue: '#300'
  last_synced: '2026-02-28T16:55:11Z'
---