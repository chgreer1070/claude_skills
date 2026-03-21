---
name: Architect and planner agents lack orchestrator discipline rules when designing workflow skills
description: "Architect and task planner agents designing workflow skills do not load the orchestrator discipline rules or agent-orchestration delegation guidelines. This caused the work-milestone SKILL.md to encode a pre-decomposition anti-pattern where the orchestrator pre-gathers data (backlog_view, sam_read, skill aggregation) that the worktree agent can and should discover itself.\n\nRoot cause: agents spawned as plugin-creator:contextual-ai-documentation-optimizer with only plugin-creator skills loaded. They had no access to:\n- .claude/CLAUDE.md Context Window Discipline section\n- .claude/rules/source-fidelity.md State-Before-Execute scope\n- plugins/orchestrator-discipline/ plugin\n- agent-orchestration:agent-orchestration skill (delegation template, pre-gathering prohibition)\n\nProcess gap: no quality gate checks skill/agent content against orchestrator discipline rules. The plan-validator checks DAG validity and AC coverage but not whether designed workflows violate delegation constraints.\n\nSuggested fix: either (a) add orchestrator-discipline as a required skill for agents writing workflow SKILL.md files, or (b) add an orchestrator-discipline compliance check to the plan-validator or code-reviewer agent when reviewing workflow skill content."
metadata:
  topic: architect-and-planner-agents-lack-orchestrator-discipline-ru
  source: 'Session 2026-03-21: discovered during work-milestone audit'
  added: '2026-03-21'
  priority: P1
  type: Bug
  status: open
  issue: '#973'
  last_synced: '2026-03-21T22:56:41Z'
---