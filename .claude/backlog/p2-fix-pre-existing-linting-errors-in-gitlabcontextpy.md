---
name: Fix pre-existing linting errors in gitlab_context.py
description: 'plugins/gitlab-skill/skills/gitlab-skill/scripts/gitlab_context.py has 3 linting errors: PLC0415 x2 (deferred imports inside functions) and S607 (partial executable path in subprocess). Fix: move imports to top-level, use shutil.which() for glab path resolution. Same pattern was applied in fetch_gitlab_mr.py migration.'
metadata:
  topic: fix-pre-existing-linting-errors-in-gitlabcontextpy
  source: Discovered during fetch_gitlab_mr.py subprocess-to-python-gitlab migration
  added: '2026-02-24'
  priority: P2
  type: Tech Debt
  status: resolved
  issue: '#252'
  groomed: '2026-02-28'
  last_synced: '2026-02-28T05:35:37Z'
---

## Fact-Check

Fact-Check Summary: Fix pre-existing linting errors in gitlab_context.py
Claims checked: 3

QUESTIONABLE (1):
- PLC0415 x2 + S607 violations in gitlab_context.py: Groomer agent read the file and found
  imports at module level with no subprocess calls visible. Errors may have been fixed already
  or description references an earlier state. NEEDS VERIFICATION by running ruff check.

VERIFIED (1):
- Reference pattern in fetch_gitlab_mr.py: shutil.which('glab') pattern confirmed at lines 17, 106-112

DERIVABLE (1):
- Fix is safe to apply if errors exist: Standard refactoring (move imports, replace paths)

ACTION: Run 'uv run ruff check plugins/gitlab-skill/skills/gitlab-skill/scripts/gitlab_context.py'
to confirm whether errors still exist before proceeding to planning.