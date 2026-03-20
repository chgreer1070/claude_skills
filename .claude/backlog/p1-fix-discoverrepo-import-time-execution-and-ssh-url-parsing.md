---
name: Fix discover_repo() import-time execution and ssh:// URL parsing
description: 'Four issues in the repo-agnostic implementation. Two FIXED in 25706c8c, two remain:\n\nFIXED:\n1. **Import-time execution**: DEFAULT_REPO no longer calls discover_repo() at import. Lazy init via init().\n2. **Inverted dependency chain**: gh CLI removed entirely. Chain is now GITHUB_REPO env var → GitPython → error.\n\nREMAINING:\n3. **ssh:// URL parsing**: ssh://git@github.com/owner/repo.git — regex pattern added but needs verification in an environment that uses this format.\n4. **{OWNER/REPO} placeholders create extra agent work**: Reference docs have {OWNER/REPO} placeholders requiring agent lookup. MCP tools handle repo internally — docs should leverage that instead of raw gh commands with placeholders."'
metadata:
  topic: fix-discoverrepo-import-time-execution-and-ssh-url-parsing
  source: 'Code review and user observation 2026-03-20 during #852 implementation'
  added: '2026-03-20'
  priority: P1
  type: Bug
  status: open
  issue: '#913'
  last_synced: '2026-03-20T16:06:24Z'
---