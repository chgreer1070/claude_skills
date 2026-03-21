---
name: add-new-feature should use sam create for .yaml task files instead of hardcoded .md
description: 'Three skill files (add-new-feature, work-backlog-item, complete-implementation) reference legacy tasks-{N}-{slug}.md naming instead of canonical P{NNN}-{slug}.yaml naming. This causes the swarm-task-planner orchestration to produce .md files instead of using sam create. Additionally, 4 documentation files (local-workflow.md, plan-artifact-lifecycle.md, backlog-lifecycle.draft.md, project_workflow.draft.md) have stale naming references. Root cause: skill instructions were not updated when sam create was introduced.'
metadata:
  topic: add-new-feature-should-use-sam-create-for-yaml-task-files-in
  source: 'User vision statement 2026-03-21 — divergence #1 from canonical issue lifecycle'
  added: '2026-03-21'
  priority: P1
  type: Bug
  status: in-progress
  issue: '#963'
  last_synced: '2026-03-21T16:07:53Z'
  groomed: '2026-03-21'
---

## Story

As a **developer relying on this plugin**, I want to **add-new-feature should use sam create for .yaml task files instead of hardcoded .md** so that **the tool works correctly and reliably**.

## Description

The add-new-feature skill explicitly names tasks-{N}-{slug}.md as the output format instead of delegating to sam create which produces .yaml. This means task files are created in the legacy markdown format instead of the canonical YAML format. The swarm-task-planner agent should call sam create to get a .yaml task file, not Write a .md file directly. This also caused plan number collisions (P698 matched an unrelated plan slug).

## Acceptance Criteria

- [ ] Work matches description
- [ ] Plan or implementation complete

## Context

- **Source**: User vision statement 2026-03-21 — divergence #1 from canonical issue lifecycle
- **Priority**: P1
- **Added**: 2026-03-21
- **Research questions**: None

## Groomed (2026-03-21)

### Progress

<div><sub>2026-03-21T16:07:53Z</sub>

2026-03-21: Skill files updated (add-new-feature, work-backlog-item, complete-implementation) — all references changed from tasks-{N}-{slug}.md to P{NNN}-{slug}.yaml. Documentation files (local-workflow.md, plan-artifact-lifecycle.md, backlog-lifecycle.draft.md, project_workflow.draft.md) update in progress via background agent.
</div>