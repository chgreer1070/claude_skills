---
name: backlog.py pull should accept issue selector argument
description: "Bug: backlog.py pull takes no arguments — it only does a bulk pull of all issues. There is no way to pull a single issue by #N, title, or URL into the local cache. This was expected to exist (attempted as 'backlog.py pull #321') but failed with 'Got unexpected extra argument'. Expected: pull should accept a SELECTOR argument (same as view/resolve/close) to pull a specific issue into the local cache."
metadata:
  topic: backlogpy-pull-should-accept-issue-selector-argument
  source: Session observation 2026-03-01
  added: '2026-03-01'
  priority: P2
  type: Bug
  status: open
  issue: '#324'
  last_synced: '2026-03-01T03:10:32Z'
---