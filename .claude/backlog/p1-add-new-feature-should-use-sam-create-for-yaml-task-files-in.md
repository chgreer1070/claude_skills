---
name: add-new-feature should use sam create for .yaml task files instead of hardcoded .md
description: The add-new-feature skill explicitly names tasks-{N}-{slug}.md as the output format instead of delegating to sam create which produces .yaml. This means task files are created in the legacy markdown format instead of the canonical YAML format. The swarm-task-planner agent should call sam create to get a .yaml task file, not Write a .md file directly. This also caused plan number collisions (P698 matched an unrelated plan slug).
metadata:
  topic: add-new-feature-should-use-sam-create-for-yaml-task-files-in
  source: 'User vision statement 2026-03-21 — divergence #1 from canonical issue lifecycle'
  added: '2026-03-21'
  priority: P1
  type: Bug
  status: needs-grooming
  issue: '#963'
  last_synced: '2026-03-21T15:34:16Z'
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
