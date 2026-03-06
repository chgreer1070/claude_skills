---
name: Stall detection for subagent tasks
description: "task_status_hook.py writes LastActivity timestamps on every Write/Edit/Bash call during task execution, but nothing reads those timestamps to detect or act on stalled agents.\n\nA stalled agent (one that starts but produces no tool activity for N minutes) currently holds its task IN PROGRESS indefinitely, blocking dependent tasks and consuming a concurrency slot.\n\n**Proposed behaviour:**\n- Add a stall-checker script (or extend implementation_manager.py) that queries all IN PROGRESS tasks, computes `now - LastActivity`, and flags any task exceeding a configurable threshold (default: 10 min).\n- Flagged tasks: update status to BLOCKED with a note `stall detected after Nm of no activity`; delete the active-task context file.\n- Hook integration: run the stall checker as a SubagentStop or periodic check within implement-feature before dispatching the next wave of ready tasks.\n- Configurable via task file metadata or CLAUDE.md: `stall_timeout_minutes`.\n\n**Acceptance criteria:**\n- IN PROGRESS task with LastActivity older than threshold is detected and marked BLOCKED automatically.\n- implement-feature does not re-dispatch a stalled task without explicit operator action (rerun or manual status reset).\n- Stall events are logged with task ID, last activity time, and elapsed minutes."
metadata:
  topic: stall-detection-for-subagent-tasks
  source: OpenAI Symphony SPEC.md §8.4 — stall_timeout_ms fires after 5 min of no Codex events, terminates worker, schedules retry
  added: '2026-03-06'
  priority: P1
  type: Feature
  status: open
  issue: '#448'
  last_synced: '2026-03-06T02:58:50Z'
---