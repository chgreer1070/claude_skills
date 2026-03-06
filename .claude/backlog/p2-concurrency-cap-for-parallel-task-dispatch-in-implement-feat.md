---
name: Concurrency cap for parallel task dispatch in implement-feature
description: "implement-feature dispatches all ready tasks in parallel with no upper bound. A task plan with 20 ready P1 tasks would spawn 20 concurrent agents simultaneously, exhausting API rate limits and making logs unreadable.\n\nSymphony enforces: `available_slots = max(max_concurrent_agents - running_count, 0)`. Both the global cap and per-state caps can be changed in WORKFLOW.md and take effect at runtime.\n\n**Proposed behaviour:**\n- Add `max_concurrent_tasks` setting (default: 5) readable from task file frontmatter or a `plan/config.yaml`.\n- implement-feature skill: before dispatching wave N, count currently IN PROGRESS tasks (via `implementation_manager.py status`); dispatch only `max_concurrent_tasks - in_progress_count` tasks in the next wave.\n- Optional: per-priority cap (e.g., max 2 P1 tasks at once, unlimited P2).\n- Wave loop: after each wave completes, re-query ready tasks and dispatch the next batch within the cap.\n\n**Acceptance criteria:**\n- With 10 ready tasks and cap=5, implement-feature dispatches 5, waits for completions, then dispatches remaining 5.\n- Cap of 0 or negative is rejected with a clear error.\n- Setting is optional; omitting it defaults to current unlimited behaviour for backwards compatibility."
metadata:
  topic: concurrency-cap-for-parallel-task-dispatch-in-implement-feat
  source: OpenAI Symphony SPEC.md §5.3 — global max_concurrent_agents (default 10) and optional per-state caps; available slots = max(max_concurrent_agents - running_count, 0)
  added: '2026-03-06'
  priority: P2
  type: Feature
  status: open
  issue: '#452'
  last_synced: '2026-03-06T02:59:48Z'
---