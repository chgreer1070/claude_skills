---
name: Fix discover_repo() import-time execution and ssh:// URL parsing
description: 'Four issues in the repo-agnostic implementation:\n\n1. **Import-time execution**: DEFAULT_REPO = discover_repo() runs a subprocess at module import time. Use GitPython (no subprocess) or make lazy.\n\n2. **ssh:// URL parsing**: ssh://git@github.com/owner/repo.git format not matched by regex patterns.\n\n3. **{OWNER/REPO} placeholders create extra agent work**: Reference docs and SKILL.md now have {OWNER/REPO} placeholders that require the agent to do a lookup step. MCP tools already handle repo discovery internally — docs should use MCP tool instructions (repo-transparent) instead of raw gh commands with placeholders.\n\n4. **Inverted dependency chain**: discover_repo() prioritizes gh CLI (not a dependency, not guaranteed installed) over GitPython (declared dependency, always available). Correct order: GITHUB_REPO env var → GitPython remote parsing → gh CLI fallback → error. Need to verify whether GitPython can parse proxy URLs (127.0.0.1 format used in Claude Code sessions) before finalizing the chain."'
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