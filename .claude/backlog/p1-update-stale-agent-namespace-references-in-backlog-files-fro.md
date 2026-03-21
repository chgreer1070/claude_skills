---
name: Update stale agent namespace references in backlog files from python3-development to dh
description: 'Five backlog files contain routing references to agents that were moved from python3-development to development-harness as part of deduplicate-agents-phase4 (e.g., @python3-development:swarm-task-planner, context-gathering, codebase-analyzer, feature-verifier). Any agent acting on these items will attempt to invoke nonexistent agents. References should be updated to use @dh: namespace.'
metadata:
  topic: update-stale-agent-namespace-references-in-backlog-files-fro
  source: Agent task — auto-derived from deduplicate-agents-phase4 session context
  added: '2026-03-20'
  priority: P1
  type: Chore
  status: open
  plan: plan/P780-deduplicate-agents-phase4-followup-2.yaml
  issue: '#937'
---