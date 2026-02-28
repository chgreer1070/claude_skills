---
name: backlog.py close/resolve should check for open PRs before closing issues
description: backlog.py close/resolve commands should check for open PRs linked to the issue and warn/block before closing. Currently the script closes issues without checking PR state, which can prematurely close issues that have in-flight work.
metadata:
  topic: backlogpy-closeresolve-should-check-for-open-prs-before-clos
  source: Session observation
  added: '2026-02-27'
  priority: P1
  type: Bug
  status: open
  issue: '#312'
---