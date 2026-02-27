---
name: 'clang-format: Fix broken YAML frontmatter'
description: "SKILL.md line 3 has `description:'Configure clang-format...'` — missing the required space after the `description:` key. This causes YAML parsing failures. The frontmatter should be `description: 'Configure clang-format...'`."
metadata:
  topic: clang-format-fix-broken-yaml-frontmatter
  source: Plugin code review session 2026-02-21
  added: '2026-02-21'
  priority: completed
  type: Feature
  status: done
  plan: ''
---