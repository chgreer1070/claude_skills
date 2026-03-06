---
name: Systematic git worktree isolation for concurrent task agents
description: "implement-feature dispatches multiple agents concurrently into the same working directory. Two agents editing the same file simultaneously produce merge conflicts or silent overwrites. The Agent tool supports `isolation: 'worktree'` but implement-feature never uses it.\n\nSymphony enforces three workspace invariants per issue: agent runs only inside workspace_path; workspace_path must be inside workspace_root; workspace key characters restricted to [A-Za-z0-9._-].\n\n**Proposed behaviour:**\n- implement-feature: set `isolation: 'worktree'` on all Agent tool calls for task execution.\n- Worktree naming: derive from task ID using Symphony's sanitization rule (replace non-[A-Za-z0-9._-] with `_`): e.g., `.worktrees/task-1-2/`.\n- After agent completes in the worktree, merge changes back to the main branch (or flag conflicts for operator resolution).\n- start-task skill: detect if running inside a worktree and adapt file path references accordingly.\n\n**Acceptance criteria:**\n- Concurrent task agents each write to a distinct worktree; no shared file edits between agents on separate tasks.\n- Worktree is cleaned up automatically if the agent makes no changes (already the default Agent tool behaviour).\n- Merge-back step produces a clear conflict report if two agents modified the same file."
metadata:
  topic: systematic-git-worktree-isolation-for-concurrent-task-agents
  source: 'OpenAI Symphony SPEC.md §9 — per-issue workspace isolation: agent runs only inside workspace_path; workspace_path must have workspace_root as prefix; workspace key restricted to [A-Za-z0-9._-]'
  added: '2026-03-06'
  priority: P2
  type: Feature
  status: open
  issue: '#453'
  last_synced: '2026-03-06T03:00:02Z'
---