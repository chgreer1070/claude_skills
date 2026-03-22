---
name: Architect and planner agents lack orchestrator discipline rules when designing workflow skills
description: "Architect and task planner agents designing workflow skills do not load the orchestrator discipline rules or agent-orchestration delegation guidelines. This caused the work-milestone SKILL.md to encode a pre-decomposition anti-pattern where the orchestrator pre-gathers data (backlog_view, sam_read, skill aggregation) that the worktree agent can and should discover itself.\n\nRoot cause: agents spawned as plugin-creator:contextual-ai-documentation-optimizer with only plugin-creator skills loaded. They had no access to:\n- .claude/CLAUDE.md Context Window Discipline section\n- .claude/rules/source-fidelity.md State-Before-Execute scope\n- plugins/orchestrator-discipline/ plugin\n- agent-orchestration:agent-orchestration skill (delegation template, pre-gathering prohibition)\n\nProcess gap: no quality gate checks skill/agent content against orchestrator discipline rules. The plan-validator checks DAG validity and AC coverage but not whether designed workflows violate delegation constraints.\n\nSuggested fix: either (a) add orchestrator-discipline as a required skill for agents writing workflow SKILL.md files, or (b) add an orchestrator-discipline compliance check to the plan-validator or code-reviewer agent when reviewing workflow skill content."
metadata:
  topic: architect-and-planner-agents-lack-orchestrator-discipline-ru
  source: 'GitHub Issue #973'
  added: '2026-03-22'
  priority: P1
  type: Bug
  status: needs-grooming
  issue: '#973'
  last_synced: '2026-03-22T15:08:48Z'
---

## Story

As a **developer relying on this plugin**, I want to **architect and planner agents lack orchestrator discipline rules when designing workflow skills** so that **the tool works correctly and reliably**.

## Description

Architect and task planner agents designing workflow skills do not load the orchestrator discipline rules or agent-orchestration delegation guidelines. This caused the work-milestone SKILL.md to encode a pre-decomposition anti-pattern where the orchestrator pre-gathers data (backlog_view, sam_read, skill aggregation) that the worktree agent can and should discover itself.

Root cause: agents spawned as plugin-creator:contextual-ai-documentation-optimizer with only plugin-creator skills loaded. They had no access to:
- .claude/CLAUDE.md Context Window Discipline section
- .claude/rules/source-fidelity.md State-Before-Execute scope
- plugins/orchestrator-discipline/ plugin
- agent-orchestration:agent-orchestration skill (delegation template, pre-gathering prohibition)

Process gap: no quality gate checks skill/agent content against orchestrator discipline rules. The plan-validator checks DAG validity and AC coverage but not whether designed workflows violate delegation constraints.

Suggested fix: either (a) add orchestrator-discipline as a required skill for agents writing workflow SKILL.md files, or (b) add an orchestrator-discipline compliance check to the plan-validator or code-reviewer agent when reviewing workflow skill content.

## Acceptance Criteria

- [ ] Work matches description
- [ ] Plan or implementation complete

## Context

- **Source**: Session 2026-03-21: discovered during work-milestone audit
- **Priority**: P1
- **Added**: 2026-03-21
- **Research questions**: None