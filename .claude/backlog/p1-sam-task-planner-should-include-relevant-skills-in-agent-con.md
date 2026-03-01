---
name: SAM task planner should include relevant skills in agent context for test-writing tasks
description: "During #328, test-writing tasks (2.1-2.11) specified agent=general-purpose but did not include the fastmcp-python-tests skill as context. This skill contains pytest patterns, FastMCP testing conventions, fixture design, and async test guidance directly relevant to the work. The swarm-task-planner agent should detect when tasks involve writing tests and automatically include testing-related skills (fastmcp-python-tests, python3-development) in the task's agent context or delegation prompt. Without this, sub-agents write tests without project-specific testing conventions."
metadata:
  topic: sam-task-planner-should-include-relevant-skills-in-agent-con
  source: 'session observation during #328 implementation'
  added: '2026-03-01'
  priority: P1
  type: Enhancement
  status: open
  issue: '#338'
  last_synced: '2026-03-01T13:25:38Z'
---