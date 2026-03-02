---
name: 'complete-implementation: route follow-up task files to backlog instead of orphaning'
description: "The complete-implementation skill's code-reviewer phase creates follow-up task files (plan/tasks-{N}-{slug}-followup-{k}.md) when it finds gaps. The workflow then expects to recurse with /implement-feature on them. Problem: when the orchestrator skips recursion (deferred scope, different priority, session timeout, or context compaction), these files are orphaned — no backlog item links to them, no one knows they exist. This has happened 3+ times in recent sessions.\n\nFix: Add a routing step between 'code reviewer creates follow-up' and 'recurse with implement-feature'. The routing step should:\n1. Search backlog for existing item matching the follow-up scope (by title keywords)\n2. If found: attach follow-up as plan via backlog update --plan\n3. If not found: create new backlog item via create-backlog-item with follow-up as plan\n4. Only recurse (implement now) if same priority AND same session scope\n5. Otherwise: link to backlog only, do not recurse\n\nThis affects: .claude/skills/complete-implementation/SKILL.md and potentially the code-reviewer agent prompt."
metadata:
  topic: complete-implementation-route-follow-up-task-files-to-backlo
  source: 'Observed during #368 implementation — follow-up for get_gitlab_context.py was orphaned until manually linked'
  added: '2026-03-02'
  priority: P1
  type: Feature
  status: open
  issue: '#381'
  last_synced: '2026-03-02T04:04:13Z'
---