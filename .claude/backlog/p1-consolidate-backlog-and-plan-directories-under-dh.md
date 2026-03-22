---
name: Consolidate backlog and plan directories under .dh/
description: Backlog items live in .claude/backlog/ and plan artifacts live in plan/ at project root. These are both development-harness artifacts but stored in inconsistent locations. All development-harness artifacts (backlog items, plan files, reports, context files) need to be consolidated under a single .dh/ directory. A migration tool is needed that moves existing files, corrects any internal path references, and updates all consumers. The migration tool must analyze real existing files to determine what path patterns exist and how to detect and transform them — not assume patterns from documentation.
metadata:
  topic: consolidate-backlog-and-plan-directories-under-dh
  source: User request — session 2026-03-21, observed inconsistency between .claude/backlog/ and plan/ locations
  added: '2026-03-22'
  priority: P1
  type: Refactor
  status: open
  issue: '#981'
  last_synced: '2026-03-22T03:41:45Z'
---