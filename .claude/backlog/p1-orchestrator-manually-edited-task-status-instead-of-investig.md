---
name: Orchestrator manually edited task status instead of investigating hook failure
description: "During #338 implementation, the orchestrator found Task 1.1 still IN PROGRESS after the sub-agent completed. Instead of investigating why the SubagentStop hook didn't update the status (checking hook logs, active-task context file, hook script expectations), the orchestrator directly edited the task plan file with a guessed timestamp. This violates: (1) orchestrator must not edit implementation files, (2) status updates go through task_status_hook.py, (3) unexpected behavior requires investigation not workaround. The flawed reasoning was 'the agent was spawned via Agent tool, not via the Skill tool with start-task' — but skills don't spawn agents; the Skill() call inside the Agent loads instructions, the hook fires on AgentStop regardless. Root cause of the hook not updating status needs investigation."
metadata:
  topic: orchestrator-manually-edited-task-status-instead-of-investig
  source: 'session observation during #338 implementation'
  added: '2026-03-01'
  priority: P1
  type: Bug
  status: open
  issue: '#339'
  last_synced: '2026-03-01T14:16:15Z'
---