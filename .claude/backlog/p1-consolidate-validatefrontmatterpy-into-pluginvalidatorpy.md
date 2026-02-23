---
name: Consolidate validate_frontmatter.py into plugin_validator.py
description: "`plugin_validator.py` (4190 lines) copy-pastes frontmatter\nvalidation logic from `validate_frontmatter.py` (1341 lines) instead of\nimporting it. Comments acknowledge this: 'PYDANTIC FRONTMATTER MODELS (from\nvalidate_frontmatter.py)' and 'Complexity preserved from validate_frontmatter.py\nfor behavioral parity.' This creates two maintenance surfaces: any change must\nbe applied to both scripts (as seen when reversing the name-field bug workaround).\n\n**Required work:**\n1. Audit both scripts for all "
metadata:
  topic: consolidate-validatefrontmatterpy-into-pluginvalidatorpy
  source: Frontmatter validation bug-fix session 2026-02-20
  added: '2026-02-20'
  priority: P1
  type: Feature
  status: done
---
**Suggested location**: `plugins/plugin-creator/scripts/`
