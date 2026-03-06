---
name: Enforce single-authority task state mutation in orchestrator
description: "Currently, task state can be mutated by three independent paths: (1) the orchestrator Claude session directly edits task files when reading ready-tasks and dispatching, (2) task_status_hook.py updates status on SubagentStop, and (3) start-task skill sets IN PROGRESS and adds Started timestamp. There is no canonical authority — any of these can write conflicting state.\n\nSymphony's model: the orchestrator is the *only* component that mutates scheduling state. Workers report outcomes back; the orchestrator converts them into explicit state transitions. This prevents duplicate dispatch and makes state auditable.\n\n**Proposed changes:**\n- Audit all write paths to task files: list every location in start-task, task_status_hook.py, implementation_manager.py, and the orchestrator prompt where task status fields are written.\n- Define which component owns each field: status, Started, Completed, LastActivity, RetryCount, RetryAfter, LastFailureReason.\n- Refactor so that status transitions (NOT STARTED → IN PROGRESS, IN PROGRESS → COMPLETE/BLOCKED) are only performed by task_status_hook.py or implementation_manager.py — never by the orchestrator Claude session editing files directly.\n- Add a guard in implementation_manager.py that detects dual-write: if a task is already IN PROGRESS when dispatch is attempted, skip it with a warning rather than dispatching a second agent.\n\n**Acceptance criteria:**\n- No task status field is written by the orchestrator's direct Edit calls.\n- Dual-dispatch guard is present and tested: two concurrent ready-task queries do not produce two agents for the same task.\n- Component ownership of each task metadata field is documented in TASK_FILE_FORMAT.md."
metadata:
  topic: enforce-single-authority-task-state-mutation-in-orchestrator
  source: OpenAI Symphony SPEC.md §7 Coordination Layer — orchestrator is the single authoritative authority for in-memory state; all worker outcomes are routed through it, preventing duplicate dispatch
  added: '2026-03-06'
  priority: P1
  type: Refactor
  status: open
  issue: '#451'
  last_synced: '2026-03-06T02:59:34Z'
---