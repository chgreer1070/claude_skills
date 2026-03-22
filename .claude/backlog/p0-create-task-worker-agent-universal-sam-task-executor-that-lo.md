---
name: Create task-worker agent — universal SAM task executor that loads skills from task metadata
description: "Create a task-worker agent in development-harness that serves as the universal SAM task executor.\n\nThe task-worker is the amorphous any-agent. It receives a task reference (P{N}/T{M}), loads the task via sam_read, reads the skills listed in the task metadata, loads those skills, and executes the work. The orchestrator does not need to know which specialist agent to route to — the task metadata declares the skills needed.\n\nAgent responsibilities:\n1. Parse task reference from prompt (P{N}/T{M} pattern)\n2. Load task via sam_read(plan=P{N}, task=T{M}) — if this fails, report error and stop\n3. Read the skills field from task metadata\n4. Load each skill via Skill(skill='{name}') — conditional or unconditional as instructed\n5. Claim the task via sam_claim\n6. Execute against acceptance criteria from the task\n7. Run verification steps\n8. Track progress via sam_state\n9. Report structured completion (STATUS: COMPLETE/PARTIAL/FAILED with details)\n\nAgent frontmatter:\n- name: task-worker\n- tools: all tools\n- mcpServers: sam, backlog (explicit declaration)\n- skills: dh:subagent-contract (bounded specialist behavior)\n- model: inherit (orchestrator chooses model per task complexity)\n\nThis agent replaces the need for the orchestrator to route tasks to specific agent types (python-cli-architect, contextual-ai-documentation-optimizer, etc.). The task file's skills field determines what the worker loads — the worker adapts to any domain by loading the right skills.\n\nComplements /dh:dispatch (manager guidance) — dispatch creates teams of task-workers."
metadata:
  topic: create-task-worker-agent-universal-sam-task-executor-that-lo
  source: 'Session 2026-03-21: completing the manager/worker architecture with dispatch skill as manager guidance and task-worker as the universal worker'
  added: '2026-03-22'
  priority: completed
  type: Feature
  status: done
  issue: '#978'
  last_synced: '2026-03-22T01:05:08Z'
---