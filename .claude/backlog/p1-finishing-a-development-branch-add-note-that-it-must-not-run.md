---
name: 'finishing-a-development-branch: add note that it must not run while subagent-driven-development is in progress in the same worktree'
description: "The `superpowers:finishing-a-development-branch` skill can be invoked from the plan at the end of `superpowers:executing-plans`, but when `superpowers:subagent-driven-development` is the active execution pattern the finishing step must not run mid-session — it is only valid after the final code quality reviewer has approved all tasks.\n\nThe skill currently has no guard against being invoked while subagent-driven-development is still dispatching subagents.\n\nTwo additions needed:\n\n1. A note (and ideally a check): if a subagent-driven-development session is in progress in the current worktree, warn and refuse to run finishing-a-development-branch until all tasks show complete.\n\n2. A recovery path: if finishing-a-development-branch detects an incomplete subagent-driven-development session, it must re-invoke `superpowers:subagent-driven-development` to resume from where it left off — completing remaining tasks and reviews — before proceeding with the finishing steps."
metadata:
  topic: finishing-a-development-branch-add-note-that-it-must-not-run
  source: Session observation — executing-plans invoked finishing-a-development-branch without awareness that subagent-driven-development was the active execution pattern
  added: '2026-03-04'
  priority: P1
  type: Docs
  status: open
  issue: '#430'
  last_synced: '2026-03-04T16:59:17Z'
---