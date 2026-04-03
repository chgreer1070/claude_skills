---
name: Fix Task.name populated from task_id instead of issue title in GitHub fetch
description: Task.name field is populated from sam.task_id (e.g. 'T1') instead of the GitHub issue title in fetch_tasks_from_github and _load_tasks_from_cache. Status output shows task IDs not human-readable titles.
metadata:
  topic: fix-taskname-populated-from-taskid-instead-of-issue-title-in
  source: 'GitHub Issue #499'
  added: '2026-03-22'
  priority: P2
  type: Bug
  status: needs-grooming
  issue: '#499'
  last_synced: '2026-03-22T15:10:01Z'
---

## Story

As a **developer relying on this plugin**, I want to **fix task.name populated from task_id instead of issue title in github fetch** so that **the tool works correctly and reliably**.

## Description

Task.name field is populated from sam.task_id (e.g. "T1") instead of the GitHub issue title in fetch_tasks_from_github and _load_tasks_from_cache. Status output shows task IDs not human-readable titles.

## Acceptance Criteria

- [ ] Work matches description
- [ ] Plan or implementation complete

## Context

- **Source**: Code review of migrate-sam-task-github-subissues
- **Priority**: P2
- **Added**: 2026-03-06
- **Research questions**: None