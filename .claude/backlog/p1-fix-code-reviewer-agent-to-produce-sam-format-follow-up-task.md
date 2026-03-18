---
name: Fix code-reviewer agent to produce SAM-format follow-up task files with correct filename convention and task key format
description: 'The code-reviewer agent produces follow-up task files that do not conform to SAM filename conventions (expected: plan/tasks-{N}-{slug}-followup-{k}.md) or use the correct task key format. This causes downstream routing failures in /complete-implementation when it attempts to detect and process follow-up files by name pattern, and when backlog-linking logic derives search titles from filenames. Success looks like: code-reviewer follow-up files use the exact SAM filename pattern, task keys within those files match the format expected by sam CLI and task_status_hook.py, and /complete-implementation can detect, route, and attach them to backlog items without manual intervention.'
metadata:
  topic: fix-code-reviewer-agent-to-produce-sam-format-follow-up-task
  source: Agent task — auto-derived from title
  added: '2026-03-18'
  priority: P1
  type: Bug
  status: open
  issue: '#841'
---