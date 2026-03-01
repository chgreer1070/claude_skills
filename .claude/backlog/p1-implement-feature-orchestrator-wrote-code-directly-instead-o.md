---
name: implement-feature orchestrator wrote code directly instead of delegating to sub-agents
description: "During #328 (backlog MCP scenario testing), the /implement-feature orchestrator wrote test files directly (test_scenarios.py, test_live_validation.py, conftest.py edits) instead of delegating each task to a sub-agent via /start-task. This violates the SAM execution model where the orchestrator should only: (1) query ready tasks, (2) delegate via Skill(skill='start-task', args=...), (3) loop until complete. Root cause investigation needed — was it context pressure (prior session ran out of context), skill instruction ambiguity, or agent selection failure? Related: #315 (implement-feature orchestrator bypasses start-task)."
metadata:
  topic: implement-feature-orchestrator-wrote-code-directly-instead-o
  source: 'session observation during #328 implementation'
  added: '2026-03-01'
  priority: P1
  type: Bug
  status: open
  issue: '#337'
  last_synced: '2026-03-01T13:25:23Z'
---