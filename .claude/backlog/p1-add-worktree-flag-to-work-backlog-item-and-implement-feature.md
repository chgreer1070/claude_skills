---
name: Add --worktree flag to work-backlog-item and implement-feature for opt-in isolation
description: "Add --worktree (-wt) flag to work-backlog-item, implement-feature, and start-task skills for opt-in git worktree isolation when working on individual tickets.\n\nCurrently worktree isolation is only used by /work-milestone during parallel wave execution. The user often works on multiple individual tickets manually and wants to avoid conflicts by choosing worktree isolation per-invocation.\n\nBehavior when --worktree is passed:\n- work-backlog-item: passes the flag through to implement-feature when invoking it in Step 8.5a\n- implement-feature: spawns each task agent with Agent(isolation: 'worktree') instead of plain Agent()\n- start-task: if invoked directly with --worktree, the agent runs in a worktree (the caller passes isolation: 'worktree' to the Agent tool)\n\nBehavior when --worktree is NOT passed: no change from current behavior (agents work on main working tree).\n\nImplementation:\n- Add --worktree to argument parsing in each skill's SKILL.md\n- work-backlog-item: detect flag, pass through to implement-feature invocation\n- implement-feature: detect flag, add isolation: 'worktree' to Agent() calls in the dispatch loop\n- start-task: no skill-level change needed — the isolation is set by the caller (implement-feature or manual Agent invocation)\n\nThe flag is orthogonal to /work-milestone — milestone execution always uses worktrees regardless of this flag."
metadata:
  topic: add-worktree-flag-to-work-backlog-item-and-implement-feature
  source: 'Session 2026-03-21: user request for opt-in worktree isolation on individual ticket work'
  added: '2026-03-21'
  priority: P1
  type: Feature
  status: open
  issue: '#974'
  last_synced: '2026-03-21T23:46:47Z'
---