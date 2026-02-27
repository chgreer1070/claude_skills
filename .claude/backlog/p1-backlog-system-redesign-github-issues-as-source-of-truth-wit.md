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
  issue: '#282'
---

## Design Constraints

### Authorization gate: preventing untrusted issue injection

Agents must never auto-action issues from arbitrary contributors. The approved work queue requires an explicit gate:

1. **Project board membership** (coarse gate) — only issues added to the GitHub Project are visible to `backlog.py pull`. Issues opened by external contributors exist in the repo tracker but are invisible to agents until a maintainer adds them to the project.
2. **Label filter** (fine-grained) — within the project, only issues carrying an `agent:actionable` label (or equivalent) enter the agent's working set. This prevents half-triaged items from being picked up prematurely.
3. **Author allowlist** (optional hardening) — `.claude/config.json` or `pyproject.toml` can list approved GitHub logins. `backlog.py pull` skips issues from authors not on the list even if they're in the project. Useful for repos with many collaborators.

The combination means: random drive-by issues stay in the repo's issue tracker, never enter the agent's local cache, and never get worked. A maintainer explicitly approves work by adding the issue to the project board and labeling it.