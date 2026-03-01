---
name: 'SAM task planner: merge same-file tasks into single agent assignment'
description: 'When multiple SAM tasks edit the same file (e.g., Tasks 2.1-2.3 all modifying SKILL.md), launching separate sub-agents via start-task causes edit conflicts. The current workaround is executing them inline in the orchestrator, which bypasses the hook automation (SubagentStop, PostToolUse). The task planner (swarm-task-planner) should detect when multiple tasks share output files and either: (1) merge them into a single compound task assigned to one agent, or (2) enforce sequential dispatch with file-level locking in the orchestrator. The implement-feature orchestrator also needs a dispatch mode for same-file task batches that preserves hook-based status tracking.'
metadata:
  topic: sam-task-planner-merge-same-file-tasks-into-single-agent-ass
  source: 'Session observation — #128 validate-agent-browser Tasks 2.1-2.3 all edited SKILL.md'
  added: '2026-02-28'
  priority: P1
  type: Feature
  status: open
  issue: '#316'
---