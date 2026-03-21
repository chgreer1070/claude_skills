---
name: backlog_list should always include status and issue state — remove with_status flag
description: "backlog_list hides status behind a with_status=true flag. Status is a tiny field that should be included in every response by default. Additionally, the status field shows only the GitHub label (e.g. status:in-progress) but not the issue state (open/closed). A closed issue with no status label shows status: '' which is indistinguishable from an open issue with no status label. The list should include both the label-based status AND the GitHub issue state (open/closed) in every response without requiring a flag."
metadata:
  topic: backloglist-should-always-include-status-and-issue-state-rem
  source: User observation during session 2026-03-21 — status is too important to hide behind a flag
  added: '2026-03-21'
  priority: P1
  type: Bug
  status: open
  issue: '#969'
  last_synced: '2026-03-21T17:52:24Z'
---