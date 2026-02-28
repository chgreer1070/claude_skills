---
name: implement-feature orchestrator bypasses start-task hooks when executing tasks inline
description: "When the /implement-feature orchestrator executes tasks inline (directly in the orchestrator context) or via the Agent tool instead of using Skill(skill='start-task', args='...'), the SubagentStop and PostToolUse hooks declared in the skill frontmatter do not fire. This means task status transitions (NOT STARTED → IN PROGRESS → COMPLETE) and timestamps (Started, Completed, LastActivity) must be maintained manually, defeating the automation purpose of the hook system. Root causes: (1) Agent tool dispatch bypasses Skill/Task tool hook chain entirely, (2) No guidance in /implement-feature for when multiple tasks edit the same file — serialization vs conflict handling is undefined, leading operators to do tasks inline to avoid conflicts. Fix should: document that Skill(skill='start-task') is the ONLY correct dispatch for task execution, add a guard or warning when tasks share output files, and consider whether the orchestrator should detect and prevent inline execution."
metadata:
  topic: implement-feature-orchestrator-bypasses-start-task-hooks-whe
  source: 'Session observation — observed during #128 validate-agent-browser implementation'
  added: '2026-02-28'
  priority: P1
  type: Bug
  status: open
---

