---
name: backlog.py resolve/close fails on GitHub-only issues without local cache file
description: "Bug: backlog.py view can find and display issues by #N via GitHub API fallback, but resolve and close only search local .claude/backlog/ files. If an issue exists on GitHub but has no local cache file (e.g. it was deleted or never synced), resolve/close fails with 'No item found' even though the issue is accessible. Expected: resolve/close should fall back to GitHub API lookup like view does."
metadata:
  topic: backlogpy-resolveclose-fails-on-github-only-issues-without-l
  source: Session observation 2026-03-01
  added: '2026-03-01'
  priority: P2
  type: Bug
  status: open
  issue: '#323'
  last_synced: '2026-03-01T03:10:01Z'
---