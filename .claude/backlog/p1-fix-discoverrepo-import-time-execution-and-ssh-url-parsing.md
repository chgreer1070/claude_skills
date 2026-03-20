---
name: Fix discover_repo() import-time execution and ssh:// URL parsing
description: 'Two issues in the new discover_repo() function in backlog_core/models.py: (1) DEFAULT_REPO = discover_repo() executes at module import time, triggering a subprocess call on every import. Should be lazy — use GitPython for import-time safety or make DEFAULT_REPO a lazy property. (2) ssh://git@github.com/owner/repo.git URL format is not matched by either _SSH_REMOTE_RE or _HTTPS_REMOTE_RE regex. This silently falls through to RepoDiscoveryError for users with ssh:// protocol remotes.'
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