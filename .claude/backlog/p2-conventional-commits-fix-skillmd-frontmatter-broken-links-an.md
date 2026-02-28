---
name: 'conventional-commits: Fix SKILL.md frontmatter, broken links, and structure'
description: 'Linter found issues in plugins/conventional-commits/skills/conventional-commits/SKILL.md. Requires 3 jobs: (1) fix frontmatter, (2) fix broken links, (3) fix structure. Source: lint validation.'
metadata:
  topic: conventional-commits-fix-skillmd-frontmatter-broken-links-an
  source: Session observation - lint validation
  added: '2026-02-24'
  priority: P2
  type: Refactor
  status: resolved
  issue: '#251'
  groomed: '2026-02-28'
  last_synced: '2026-02-28T05:35:43Z'
---

## Fact-Check

Fact-Check Summary: conventional-commits SKILL.md fixes
Claims checked: 3

VERIFIED (1):
- File exists at plugins/conventional-commits/skills/conventional-commits/SKILL.md: Confirmed

MISSING (2):
- Specific frontmatter issues: Description says 'fix frontmatter' but groomer found frontmatter
  syntactically valid. Specific violations not documented.
- Specific broken links and structure issues: Description says 'fix broken links' and 'fix structure'
  but does not enumerate which links or rules are violated.

ACTION: Run 'uv run prek run --files plugins/conventional-commits/skills/conventional-commits/SKILL.md'
to get actual linter output identifying specific violations.