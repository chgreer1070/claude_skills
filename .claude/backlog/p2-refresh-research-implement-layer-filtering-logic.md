---
name: 'refresh-research: Implement --layer filtering logic'
description: 'The `--layer` flag is documented in refresh-research but filtering logic is not implemented. When `--layer 0`, `--layer 1`, or `--layer 2` is passed, only research entries with matching layer metadata should be refreshed. Success: `/refresh-research --layer 1` processes only Layer 1 entries. Depends on research entries having `layer` metadata (already added).'
metadata:
  topic: refresh-research-implement-layer-filtering-logic
  source: Session observation — SDLC layer implementation (2026-02-23)
  added: '2026-02-23'
  priority: P2
  type: Feature
  status: open
---
**Suggested location**: `.claude/skills/refresh-research/SKILL.md` and `knowledge-explorer.py`
