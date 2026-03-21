---
name: Add input validation to github_branches.py
description: 'Add missing input validation to github_branches.py per architecture spec Section 6: slug regex, milestone_number > 0, head_branch != base_branch. Add corresponding tests. Without validation, invalid inputs reach the GitHub API without sanitization.'
metadata:
  topic: add-input-validation-to-githubbranchespy
  source: 'Code review of Issue #919'
  added: '2026-03-21'
  priority: P1
  type: Bug
  status: open
  issue: '#927'
  last_synced: '2026-03-21T00:27:46Z'
  plan: plan/P784-integration-branch-management-followup-2.yaml
---