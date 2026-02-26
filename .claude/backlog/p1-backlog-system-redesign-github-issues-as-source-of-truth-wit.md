---
name: 'Backlog system redesign: GitHub Issues as source of truth with local cache'
description: 'Current architecture has BACKLOG.md as primary source of truth with GitHub Issues as a secondary mirror. This is inverted — only works for one agent in one repo clone. A second session, different machine, or teammate sees stale markdown files. Redesign so GitHub Issues + Projects are the backend (available from anywhere) and local .claude/backlog/ files are a derived read cache rebuilt on demand. Key changes: (1) add creates GitHub Issue first, writes local cache from response, (2) list queries gh issue list with label filters, caches locally for speed, (3) update does gh issue edit first then updates cache, (4) close happens via Fixes #N in PR — GitHub auto-closes on merge, no manual skill workflow needed, (5) status lives in GitHub labels not markdown fields, (6) priority lives in GitHub labels not markdown section headers, (7) plan artifacts attached as issue comments or linked in body, (8) groomed content written into issue body expandable sections. Add pull/push commands: backlog.py pull fetches all open issues and rebuilds local cache, backlog.py push syncs local edits back to GitHub. The Fixes #N convention in commits/PRs handles closing automatically.'
metadata:
  topic: backlog-system-redesign-github-issues-as-source-of-truth-wit
  source: Session observation — identified during work-backlog-item close workflow for CI failures item
  added: '2026-02-26'
  priority: P1
  type: Feature
  status: open
---

