---
name: 'work-backlog-item: Implement --language and --stack routing'
description: 'The `--language` and `--stack` arguments are documented in work-backlog-item but not yet implemented. When provided, they should route to the appropriate language manifest and stack profile for SAM planning. Success: invoking `/work-backlog-item --language python --stack fastapi {title}` loads Python + FastAPI context. Constraint: must integrate with existing language-manifest-schema and stack-profile-schema.'
metadata:
  topic: work-backlog-item-implement-language-and-stack-routing
  source: Session observation — SDLC layer implementation (2026-02-23)
  added: '2026-02-23'
  priority: P2
  type: Feature
  status: open
  issue: '#247'
---

**Suggested location**: `.claude/skills/work-backlog-item/SKILL.md` and related scripts
