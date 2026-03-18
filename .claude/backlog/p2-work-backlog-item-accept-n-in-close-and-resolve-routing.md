---
name: 'work-backlog-item: accept `#N` in `close` and `resolve` routing'
description: '`work-backlog-item close` currently expects a title substring. Since GitHub Issues are now the canonical source of truth, `close #N` and `resolve #N` should also be valid — fetch the title from the issue and proceed. This eliminates the need to remember exact title substrings for the common case of closing work started with `/work-backlog-item #N`. Routing table in `SKILL.md` needs a new `#N` row for the close/resolve paths.'
metadata:
  topic: work-backlog-item-accept-n-in-close-and-resolve-routing
  source: 'PR #149 follow-up — start-milestone automation (2026-02-22)'
  added: '2026-02-22'
  priority: P2
  type: Feature
  status: done
---

**Suggested location**: `.claude/skills/work-backlog-item/SKILL.md` — Routing table (Step 9 path column), plus Step 9 Extension GitHub issue close command
