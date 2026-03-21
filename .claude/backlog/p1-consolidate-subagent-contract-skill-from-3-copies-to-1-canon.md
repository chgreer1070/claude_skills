---
name: Consolidate subagent-contract skill from 3 copies to 1 canonical location in development-harness
description: "Consolidate subagent-contract skill to a single canonical location.\n\nCurrently exists in THREE places:\n1. `plugins/python3-development/skills/subagent-contract/SKILL.md`\n2. `plugins/plugin-creator/skills/subagent-contract/SKILL.md`\n3. dh does NOT have its own copy\n\nThe two existing copies differ only in one line: plugin-creator adds a `## Workflow Reference` pointing to `../../../../.claude/knowledge/workflow-diagrams/multi-agent-orchestration.md`. All other content is identical.\n\nThis skill is used as a `skills: subagent-contract` declaration in agent frontmatter across all three plugins. It enforces bounded specialist behavior and is language-agnostic.\n\nDecide canonical location (dh is the natural home since it's the orchestration harness), create the canonical copy there, and remove the other two."
metadata:
  topic: consolidate-subagent-contract-skill-from-3-copies-to-1-canon
  source: 'Session 2026-03-21: skill-migration-comparison report (.claude/reports/skill-migration-comparison-2026-03-21.md)'
  added: '2026-03-21'
  priority: P1
  type: Refactor
  status: needs-grooming
  issue: '#960'
  last_synced: '2026-03-21T15:59:56Z'
---

## Story

As a **maintainer of the codebase**, I want to **consolidate subagent-contract skill from 3 copies to 1 canonical location in development-harness** so that **the code is cleaner and more maintainable**.

## Description

Consolidate subagent-contract skill to a single canonical location.

Currently exists in THREE places:
1. `plugins/python3-development/skills/subagent-contract/SKILL.md`
2. `plugins/plugin-creator/skills/subagent-contract/SKILL.md`
3. dh does NOT have its own copy

The two existing copies differ only in one line: plugin-creator adds a `## Workflow Reference` pointing to `../../../../.claude/knowledge/workflow-diagrams/multi-agent-orchestration.md`. All other content is identical.

This skill is used as a `skills: subagent-contract` declaration in agent frontmatter across all three plugins. It enforces bounded specialist behavior and is language-agnostic.

Decide canonical location (dh is the natural home since it's the orchestration harness), create the canonical copy there, and remove the other two.

## Acceptance Criteria

- [ ] Work matches description
- [ ] Plan or implementation complete

## Context

- **Source**: Session 2026-03-21: skill-migration-comparison report (.claude/reports/skill-migration-comparison-2026-03-21.md)
- **Priority**: P1
- **Added**: 2026-03-21
- **Research questions**: None
