---
name: backlog.py update needs --title and --description flags
description: "backlog.py update command cannot modify an item's title (name) or description after creation. The only way these frontmatter fields are written is during backlog add. When an item needs reframing (title or description change), agents are forced to bypass the script with direct Write/Edit on per-item files and gh issue edit, violating the single-interface rule in CLAUDE.md. Root cause identified via /find-cause on 2026-03-01: backlog.py:1767-1779 update() signature has --plan, --status, --create-issue, --groomed-file, --groomed-content, --section, --content, --groomed but no --title or --description. Fix: add --title and --description flags to the update subcommand that modify frontmatter and sync to GitHub issue."
metadata:
  topic: backlogpy-update-needs-title-and-description-flags
  source: Session observation — /find-cause investigation
  added: '2026-03-01'
  priority: P1
  type: Feature
  status: open
---

