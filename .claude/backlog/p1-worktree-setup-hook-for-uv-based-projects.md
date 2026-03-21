---
name: Worktree setup hook for uv-based projects
description: Add a WorktreeCreate hook that auto-runs uv sync and uv run prek install when worktrees are created for parallel agent work. Workers in /work-milestone need dependencies installed in their worktrees. Pattern sourced from Citadel worktree-setup.js — adapted for our uv-based toolchain.
metadata:
  topic: worktree-setup-hook-for-uv-based-projects
  source: Citadel assessment .claude/reports/citadel-assessment-20260320.md
  added: '2026-03-21'
  priority: P1
  type: Feature
  status: open
  issue: '#928'
  last_synced: '2026-03-21T01:07:08Z'
---