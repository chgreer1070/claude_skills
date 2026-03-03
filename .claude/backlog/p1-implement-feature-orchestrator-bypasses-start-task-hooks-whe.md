---
name: implement-feature orchestrator bypasses start-task hooks when executing tasks inline
description: "When the /implement-feature orchestrator executes tasks inline (directly in the orchestrator context) or via the Agent tool instead of using Skill(skill='start-task', args='...'), the SubagentStop and PostToolUse hooks declared in the skill frontmatter do not fire. This means task status transitions (NOT STARTED → IN PROGRESS → COMPLETE) and timestamps (Started, Completed, LastActivity) must be maintained manually, defeating the automation purpose of the hook system. Root causes: (1) Agent tool dispatch bypasses Skill/Agent tool hook chain entirely, (2) No guidance in /implement-feature for when multiple tasks edit the same file — serialization vs conflict handling is undefined, leading operators to do tasks inline to avoid conflicts. Fix should: document that Skill(skill='start-task') is the ONLY correct dispatch for task execution, add a guard or warning when tasks share output files, and consider whether the orchestrator should detect and prevent inline execution."
metadata:
  topic: implement-feature-orchestrator-bypasses-start-task-hooks-whe
  source: 'Session observation — observed during #128 validate-agent-browser implementation'
  added: '2026-02-28'
  priority: P1
  type: Bug
  status: open
  issue: '#315'
  groomed: '2026-03-03'
---

## Story

As a **developer using Claude Code skills**, I want to **implement-feature orchestrator bypasses start-task hooks when executing tasks inline** so that **the tooling becomes more capable and complete**.

## Description

When the /implement-feature orchestrator executes tasks inline (directly in the orchestrator context) or via the Agent tool instead of using Skill(skill='start-task', args='...'), the SubagentStop and PostToolUse hooks declared in the skill frontmatter do not fire. This means task status transitions (NOT STARTED → IN PROGRESS → COMPLETE) and timestamps (Started, Completed, LastActivity) must be maintained manually, defeating the automation purpose of the hook system. Root causes: (1) Agent tool dispatch bypasses Skill/Task tool hook chain entirely, (2) No guidance in /implement-feature for when multiple tasks edit the same file — serialization vs conflict handling is undefined, leading operators to do tasks inline to avoid conflicts. Fix should: document that Skill(skill='start-task') is the ONLY correct dispatch for task execution, add a guard or warning when tasks share output files, and consider whether the orchestrator should detect and prevent inline execution.

## Acceptance Criteria

- [ ] Work matches description
- [ ] Plan or implementation complete

## Context

- **Source**: Session observation — observed during #128 validate-agent-browser implementation
- **Priority**: P1
- **Added**: 2026-02-28
- **Research questions**: None

## Fact-Check

Claims checked: 5 | VERIFIED: 5 | REFUTED: 0 | INCONCLUSIVE: 0

1. #315 is open and describes hook bypass during inline execution — VERIFIED
   Source: https://github.com/Jamie-BitFlight/claude_skills/issues/315
2. `/implement-feature` delegates ready tasks via `Skill(skill="start-task", args="{task_file_path} --task {task_id}")` — VERIFIED
   Source: `./.claude/skills/implement-feature/SKILL.md`
3. Hook-based status tracking depends on SubagentStop (`COMPLETE`) and PostToolUse (`LastActivity`) — VERIFIED
   Source: `./.claude/skills/implementation-manager/SKILL.md`
4. Same-file task conflicts were previously documented as pressure toward inline orchestration — VERIFIED
   Source: `./.claude/backlog/p1-sam-task-planner-merge-same-file-tasks-into-single-agent-ass.md`
5. A second incident of inline orchestration bypassing task delegation is documented — VERIFIED
   Source: `./.claude/backlog/p1-implement-feature-orchestrator-wrote-code-directly-instead-o.md`

## RT-ICA

RT-ICA: implement-feature orchestrator bypasses start-task hooks when executing tasks inline
Goal: Ensure orchestration always follows the `start-task` dispatch path so hook-driven task lifecycle updates remain reliable.

Conditions:
1. Required dispatch path is clearly defined | Status: AVAILABLE | Info needed: None
2. Hook lifecycle expectations are documented | Status: AVAILABLE | Info needed: None
3. Problem reproducibility evidence exists across incidents | Status: AVAILABLE | Info needed: None
4. Recurrence class can be measured from backlog history | Status: AVAILABLE | Info needed: None
5. Missing conditions that block grooming today | Status: DERIVABLE | Info needed: Additional runtime traces for future implementation verification

Decision: APPROVED
Missing: None

## Issue Classification

**Type**: recurring-pattern
**Rationale**: The same failure class appears in multiple incidents (#315 and #337), with related same-file conflict pressure documented in completed item #316.
**Analysis Method**: 6-sigma
**Scenario Target**: Ready task execution under orchestration pressure routes inline instead of through `start-task` -> task execution remains on `start-task` path with consistent hook-updated lifecycle fields

## Root-Cause Analysis

**Method**: 6-sigma
**Classification**: recurring-pattern

#### Measurement

- **Frequency**: 2 observed incidents in the current backlog batch (#315 and #337), with one related completed predecessor (#316)
- **Common factors**: Orchestrator behavior diverged from required `start-task` dispatch when task execution pressure increased
- **Affected scope**: SAM implementation execution reliability (status transitions, Completed timestamp, LastActivity updates)

#### Analysis

- **Root cause pattern**: Process-path nonconformance allows execution outside the hook-enabled path
- **Missing guardrail**: No strong enforcement signal that blocks or warns when execution drifts from `start-task`-driven delegation

#### Improvement

- **Proposed guardrail**: Explicitly verify and surface dispatch-path compliance for every ready task execution cycle
- **Verification**: Confirm executed tasks show `start-task` invocation evidence plus expected hook-driven lifecycle updates

## Groomed (2026-03-03)

### Priority

8/10 — Recurring process-integrity defect affecting reliability of automation across feature execution sessions.

### Impact

- Reduces trust in task status transitions and timestamps maintained by hooks
- Increases manual correction risk during orchestration
- Affects all features executed through `/implement-feature`

### Expected Behavior

Ready tasks are always executed via `Skill(skill="start-task", args="...")`, and lifecycle updates (`IN PROGRESS`, `COMPLETE`, `LastActivity`) are produced by hook automation rather than manual edits.

### Acceptance Criteria

1. Execution traces for ready tasks show delegation through `start-task` dispatch, not inline edits.
2. For sampled runs, task metadata updates include hook-driven completion and activity timestamps.
3. No repeated incident reports of inline orchestration bypassing `start-task` in follow-up backlog reviews.

### Resources

| Type | Item |
|------|------|
| Issue | `#315` |
| Skill | `./.claude/skills/implement-feature/SKILL.md` |
| Skill | `./.claude/skills/implementation-manager/SKILL.md` |
| Prior work | `./.claude/backlog/p1-sam-task-planner-merge-same-file-tasks-into-single-agent-ass.md` |
| Related incident | `./.claude/backlog/p1-implement-feature-orchestrator-wrote-code-directly-instead-o.md` |

### Dependencies

- Hook pipeline observability remains available for execution sessions
- Active-task context management remains intact for PostToolUse updates

### Effort

Medium
