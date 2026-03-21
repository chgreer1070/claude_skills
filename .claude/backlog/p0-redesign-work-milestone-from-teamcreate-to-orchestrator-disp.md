---
name: Redesign /work-milestone from TeamCreate to orchestrator-dispatched worktree agents
description: "Redesign /work-milestone to use orchestrator-dispatched worktree agents instead of TeamCreate teammates.\n\nVerified 2026-03-21: teammates spawned via TeamCreate lack the Agent tool and cannot spawn sub-agents. context:fork skills fall back to inline injection. This means the current /work-milestone design (spawn teammates that each run /work-backlog-item --auto) cannot work — the SAM pipeline requires agent delegation.\n\nNew architecture:\n1. Orchestrator creates integration branch (github_branches.py already exists)\n2. Orchestrator reads dispatch plan YAML from /groom-milestone\n3. For each wave, orchestrator spawns parallel Agent(isolation: 'worktree') calls — one per item\n4. Each worktree agent loads skills inline, does the work directly, commits to its worktree branch\n5. Orchestrator merges each worktree branch into integration branch\n6. After all waves complete, orchestrator lands integration branch to main\n\nNo TeamCreate needed. No nested agent spawning. Each worktree agent is a single-level worker.\n\nPre-req for milestone orchestration — blocks #921 (cross-item dependency analysis) and the overall milestone execution flow.\n\nEvidence:\n- Teammate Agent tool absence: verified via ToolSearch in test (returned only SendMessage, TaskCreate, TaskUpdate)\n- context:fork inline fallback: verified with /plugin-creator:arl — content injected inline, no fork\n- Official docs confirm: 'No nested teams: teammates cannot spawn their own teams or teammates'\n- Memory: project_teammate_capabilities.md"
metadata:
  topic: redesign-work-milestone-from-teamcreate-to-orchestrator-disp
  source: 'Session 2026-03-21: teammate capability testing revealed Agent tool unavailable to team members'
  added: '2026-03-21'
  priority: P0
  type: Refactor
  status: open
  issue: '#970'
  last_synced: '2026-03-21T19:05:58Z'
---