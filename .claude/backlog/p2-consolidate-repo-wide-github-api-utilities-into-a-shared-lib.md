---
name: Consolidate repo-wide GitHub API utilities into a shared library
description: 'The repo has shared GitHub API interaction scattered across multiple scripts and plugins (backlog.py, daily-releases scripts, etc.), each with its own inline GitHub client construction, SSL handling, and token management. Success: a single shared github_utils library installable by any script or plugin in the repo via PEP 723 [tool.uv.sources] or a proper package dependency, so all GitHub API work goes through one place. Done when all existing inline GitHub client code is replaced with imports from the shared library and CI stays green.'
metadata:
  topic: consolidate-repo-wide-github-api-utilities-into-a-shared-lib
  source: Session observation
  added: '2026-03-06'
  priority: P2
  type: Refactor
  status: open
---

