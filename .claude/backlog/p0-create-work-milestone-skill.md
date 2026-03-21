---
name: Create /work-milestone skill
description: Create the /work-milestone skill for the development-harness plugin. The skill reads a dispatch plan YAML, creates an integration branch, spawns TeamCreate teams with one member per parallel item in each wave, each running /work-backlog-item --auto in an isolated worktree. Manages merge queue with slot serialization, conflict severity classification (trivial/medium/heavy), assign_back on heavy conflicts. Inter-worker awareness via SendMessage, design decisions persisted to GitHub Issues. Discovery relay between waves. Lands integration branch to main when done. Design doc at .claude/reports/milestone-orchestration-design-20260320.md defines the full workflow.
metadata:
  topic: create-work-milestone-skill
  source: Milestone orchestration design — .claude/reports/milestone-orchestration-design-20260320.md
  added: '2026-03-21'
  priority: completed
  type: Feature
  status: done
  issue: '#935'
  last_synced: '2026-03-21T01:45:29Z'
---