---
name: Add --worktree flag to work-backlog-item and implement-feature for opt-in isolation
description: "Add --worktree (-wt) flag to work-backlog-item, implement-feature, and start-task skills for opt-in git worktree isolation when working on individual tickets.\n\nCurrently worktree isolation is only used by /work-milestone during parallel wave execution. The user often works on multiple individual tickets manually and wants to avoid conflicts by choosing worktree isolation per-invocation.\n\nBehavior when --worktree is passed:\n- work-backlog-item: passes the flag through to implement-feature when invoking it in Step 8.5a\n- implement-feature: spawns each task agent with Agent(isolation: 'worktree') instead of plain Agent()\n- start-task: if invoked directly with --worktree, the agent runs in a worktree (the caller passes isolation: 'worktree' to the Agent tool)\n\nBehavior when --worktree is NOT passed: no change from current behavior (agents work on main working tree).\n\nImplementation:\n- Add --worktree to argument parsing in each skill's SKILL.md\n- work-backlog-item: detect flag, pass through to implement-feature invocation\n- implement-feature: detect flag, add isolation: 'worktree' to Agent() calls in the dispatch loop\n- start-task: no skill-level change needed — the isolation is set by the caller (implement-feature or manual Agent invocation)\n\nThe flag is orthogonal to /work-milestone — milestone execution always uses worktrees regardless of this flag."
metadata:
  topic: add-worktree-flag-to-work-backlog-item-and-implement-feature
  source: 'GitHub Issue #974'
  added: '2026-03-22'
  priority: P1
  type: Feature
  status: needs-grooming
  issue: '#974'
  last_synced: '2026-03-22T15:08:47Z'
---

## Story

As a **developer using Claude Code skills**, I want to **add --worktree flag to work-backlog-item and implement-feature for opt-in isolation** so that **the tooling becomes more capable and complete**.

## Description

Add --worktree (-wt) flag to work-backlog-item, implement-feature, and start-task skills for opt-in git worktree isolation when working on individual tickets.

Currently worktree isolation is only used by /work-milestone during parallel wave execution. The user often works on multiple individual tickets manually and wants to avoid conflicts by choosing worktree isolation per-invocation.

Behavior when --worktree is passed:
- work-backlog-item: passes the flag through to implement-feature when invoking it in Step 8.5a
- implement-feature: spawns each task agent with Agent(isolation: "worktree") instead of plain Agent()
- start-task: if invoked directly with --worktree, the agent runs in a worktree (the caller passes isolation: "worktree" to the Agent tool)

Behavior when --worktree is NOT passed: no change from current behavior (agents work on main working tree).

Implementation:
- Add --worktree to argument parsing in each skill's SKILL.md
- work-backlog-item: detect flag, pass through to implement-feature invocation
- implement-feature: detect flag, add isolation: "worktree" to Agent() calls in the dispatch loop
- start-task: no skill-level change needed — the isolation is set by the caller (implement-feature or manual Agent invocation)

The flag is orthogonal to /work-milestone — milestone execution always uses worktrees regardless of this flag.

## Acceptance Criteria

- [ ] Work matches description
- [ ] Plan or implementation complete

## Context

- **Source**: Session 2026-03-21: user request for opt-in worktree isolation on individual ticket work
- **Priority**: P1
- **Added**: 2026-03-21
- **Research questions**: None