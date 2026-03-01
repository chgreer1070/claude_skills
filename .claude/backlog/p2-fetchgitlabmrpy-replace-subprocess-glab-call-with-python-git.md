---
name: 'fetch_gitlab_mr.py: replace subprocess glab call with python-gitlab library'
description: "fetch_gitlab_mr.py shells out to the 'glab' binary (lines 105-114) to fetch MR data. The script already has PyGithub as a dependency and the codebase uses python-gitlab elsewhere. Subprocess call to glab: (1) requires glab binary on PATH, (2) bypasses token auth handled by libraries, (3) triggered S607 linting error that was patched with shutil.which instead of fixed architecturally. Fix: replace subprocess.run(['glab', ...]) with python-gitlab equivalent API call. This eliminates the binary dependency entirely."
metadata:
  topic: fetchgitlabmrpy-replace-subprocess-glab-call-with-python-git
  source: Not specified
  added: '2026-03-01'
  priority: P2
  type: Feature
  status: open
  issue: '#368'
  last_synced: '2026-03-01T20:16:18Z'
---
