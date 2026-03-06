---
name: Fix Task.name populated from task_id instead of issue title in GitHub fetch
description: Task.name field is populated from sam.task_id (e.g. 'T1') instead of the GitHub issue title in fetch_tasks_from_github and _load_tasks_from_cache. Status output shows task IDs not human-readable titles.
metadata:
  topic: fix-taskname-populated-from-taskid-instead-of-issue-title-in
  source: Code review of migrate-sam-task-github-subissues
  added: '2026-03-06'
  priority: P2
  type: Bug
  status: open
  issue: '#499'
  last_synced: '2026-03-06T23:48:00Z'
  plan: plan/tasks-32-migrate-sam-task-github-subissues-followup-3.md
---