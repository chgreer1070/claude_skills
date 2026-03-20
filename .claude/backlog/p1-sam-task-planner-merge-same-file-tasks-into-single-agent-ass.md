---
name: 'SAM task planner: merge same-file tasks into single agent assignment'
description: 'When multiple SAM tasks edit the same file (e.g., Tasks 2.1-2.3 all modifying SKILL.md), launching separate sub-agents via start-task causes edit conflicts. The current workaround is executing them inline in the orchestrator, which bypasses the hook automation (SubagentStop, PostToolUse). The task planner (swarm-task-planner) should detect when multiple tasks share output files and either: (1) merge them into a single compound task assigned to one agent, or (2) enforce sequential dispatch with file-level locking in the orchestrator. The implement-feature orchestrator also needs a dispatch mode for same-file task batches that preserves hook-based status tracking.'
metadata:
  topic: sam-task-planner-merge-same-file-tasks-into-single-agent-ass
  source: 'Session observation — #128 validate-agent-browser Tasks 2.1-2.3 all edited SKILL.md'
  added: '2026-02-28'
  priority: completed
  type: Feature
  status: done
  issue: '#316'
  last_synced: '2026-03-01T00:33:40Z'
  groomed: '2026-03-01'
  plan: plan/tasks-11-merge-same-file-tasks
---

## Fact-Check

All 4 claims VERIFIED:
1. Multiple SAM tasks editing same file causes edit conflicts — VERIFIED (no file-level locking in implement-feature or start-task)
2. Tasks 2.1-2.3 in #128 all modified SKILL.md — VERIFIED (git log confirms commits c7ab66a, cff8fb7)
3. Current workaround is inline execution bypassing hooks — VERIFIED (related backlog item a14fb7b confirms)
4. swarm-task-planner has no merge logic — VERIFIED (agent file mentions conflict avoidance policy but no implementation)

## RT-ICA

Decision: APPROVED
Goal: Enable the SAM task planner to detect and merge same-file tasks, and the orchestrator to dispatch them safely, preserving hook-based status tracking.
All 8 conditions AVAILABLE: swarm-task-planner agent files, implement-feature skill, start-task skill, task_status_hook.py, implementation_manager.py, task file formats, #128 evidence, hook automation understanding.
Missing: None

## Groomed (2026-03-01)

### Priority

9/10 — Unblocks parallel SAM task execution; currently forces workaround that bypasses hook automation. Blocks all feature implementations with multiple tasks editing the same file.

### Impact

- Blocks: All SAM implementations where 2+ tasks modify the same file (e.g., SKILL.md, __init__.py, architecture docs)
- Bottleneck: When task planner generates tasks without same-file detection, the orchestrator has no safe dispatch mechanism and falls back to inline execution, defeating hook-based status tracking

### Benefits

- Safe parallel execution of same-file tasks with hook automation preserved
- Task planner can generate more granular task decompositions without fear of edit conflicts
- Orchestrator gains explicit dispatch mode for file-batched tasks, with clear semantics for order-of-execution

### Expected Behavior

The task planner should analyze task outputs and identify when 2+ tasks write to the same file. It should then either: (1) merge them into a single compound task with sub-goals, or (2) annotate them with a file-batch group ID. The orchestrator (implement-feature) should then dispatch same-file task batches sequentially via Skill(skill='start-task') so hooks fire correctly, rather than falling back to inline execution.

### Desired Structure

1. swarm-task-planner detects same-file outputs and groups tasks
2. Task file includes file-batch metadata or merged task definitions
3. implement-feature queries for tasks with same file-batch ID and runs them serially (not in parallel with other batches)
4. start-task and task_status_hook.py preserve hook firing and timestamp tracking for batched tasks

### Acceptance Criteria

1. swarm-task-planner identifies when 2+ tasks share any output file and flags it in task plan
2. implement-feature ready-tasks CLI includes batch-by-file mode that groups tasks by file and marks dependencies
3. At least one real task plan successfully dispatches 3+ same-file tasks without manual inline execution
4. Hook timestamps (Started, Completed, LastActivity) are recorded correctly for all tasks in a file batch
5. No edit conflicts when tasks in same batch execute sequentially via start-task

### Questions for Human

- Merge vs. Sequential: Should same-file tasks be (1) merged into single compound tasks with sub-goals, or (2) kept separate but run serially with file-level dispatch ordering?
- Batch Priority: Should all tasks in a file batch run at same priority, or should a critical task in a batch bump its priority above non-batched tasks?

### Resources

| Type | Item |
|------|------|
| Agent | @dh:swarm-task-planner |
| Skill | /implement-feature |
| Skill | /start-task |
| Prior work | .claude/backlog/p1-implement-feature-orchestrator-bypasses-start-task-hooks-whe.md |
| Script | plugins/python3-development/skills/implementation-manager/scripts/implementation_manager.py |
| Script | plugins/python3-development/skills/implementation-manager/scripts/task_status_hook.py |

### Dependencies

- Depends on: None — this is foundational
- Blocks: All future SAM feature tasks with 2+ output-sharing tasks

### Blockers

None — RT-ICA APPROVED. All prerequisites exist and are accessible. Design decision on merge vs. sequential can be made during planning phase.

### Effort

High — Changes across multiple files (task planner agent prompt, implementation_manager.py, task_status_hook.py, implement-feature skill), plus new conflict-detection logic and batch dispatch mode. Estimate: 3-4 complex sub-tasks.