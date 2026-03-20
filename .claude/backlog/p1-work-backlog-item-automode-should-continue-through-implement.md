---
name: work-backlog-item AUTO_MODE should continue through implement-feature
description: 'The work-backlog-item skill in AUTO_MODE stops at Step 8.5 (Report Next Steps) and tells the user to run /implement-feature manually. In AUTO_MODE the full flow should be: plan → implement-feature → complete-implementation without human intervention. Fix: add AUTO_MODE branch after Step 7 that invokes implement-feature and complete-implementation directly. Step 8.5 reporting is only for interactive mode.'
metadata:
  topic: work-backlog-item-automode-should-continue-through-implement
  source: "User correction 2026-03-20: 'Its called work-backlog-item not dont bother working the backlog item'"
  added: '2026-03-20'
  priority: P1
  type: Bug
  status: open
  issue: '#914'
  last_synced: '2026-03-20T16:06:29Z'
---