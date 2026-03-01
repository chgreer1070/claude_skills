# Feature Context: SAM Task Skills Context Propagation

**Issue**: #338
**Related Issues**: #337, #315
**Created**: 2026-03-01
**Status**: Discovery Complete

---

## Problem Statement

The SAM pipeline has no mechanism for attaching skill context to task definitions. When the orchestrator delegates a task to a sub-agent, the sub-agent receives only the task file path and task ID via `/start-task`. It does not receive any skill context that would equip it with domain-specific knowledge needed for the task.

This matters concretely for test-writing tasks. When a task requires writing pytest tests against a FastMCP server, the sub-agent needs the `fastmcp-python-tests` and `python3-development` skills to know testing patterns, fixture conventions, and framework-specific APIs. Today, these skills are never attached to the task definition and never propagated to the sub-agent.

### Three Broken Links in the Chain

1. **No `skills:` field in the task YAML schema.** The `TASK_FILE_FORMAT.md` JSON schema defines `task`, `title`, `status`, `agent`, `dependencies`, `priority`, `complexity`, timestamps, `blocked-by`, and `parallelize-with`. There is no `skills` field. The swarm-task-planner has no slot to declare which skills a sub-agent needs.

2. **`start-task` ignores the `agent` field.** The `/start-task` SKILL.md reads the task file to find the task section, updates status to `in-progress`, writes the active-task context file, and implements against acceptance criteria. It never reads the `agent` field from the task metadata. The agent routing happens in `/implement-feature`, not in `/start-task` itself. But even in `/implement-feature`, the agent field is used only to select the `subagent_type` -- no skill context is attached to the delegation prompt.

3. **`implement-feature` does not pass skill context.** The execution loop in `/implement-feature` SKILL.md constructs the delegation as `Skill(skill="start-task", args="{task_file_path} --task {task_id}")`. There is no mechanism to add `skills:` to this invocation. The sub-agent starts with only the `/start-task` skill and whatever skills are declared in the agent definition, but not with task-specific skills that vary per task.

---

## Current State

### Task YAML Schema (TASK_FILE_FORMAT.md)

The schema at `.claude/docs/TASK_FILE_FORMAT.md` defines these optional fields:

```yaml
agent: string        # Agent responsible for task
dependencies: array  # Task IDs that must complete first
priority: integer    # 1-5
complexity: enum     # low/medium/high
created: datetime
started: datetime
completed: datetime
blocked-by: array
parallelize-with: array
```

No `skills` field exists. The JSON schema in the same file (lines 264-345) does not include any skills-related property.

The "Appendix: Field Evolution" section (line 883) lists possible future fields but does not mention `skills`.

### Swarm-Task-Planner Agent (python3-development)

The agent at `plugins/python3-development/agents/swarm-task-planner.md` generates task YAML frontmatter with these fields in its template (lines 250-263):

```yaml
task: [Task ID]
title: [Descriptive Name]
status: not-started
agent: [agent-name]
dependencies: []
priority: [1-5]
complexity: [low/medium/high]
accuracy-risk: [low/medium/high]
parallelize-with: []
reason: [Why parallelization is safe]
handoff: [What the worker must report back]
```

No `skills` field is generated. The Agent Assignment Rules table (lines 315-325) maps task types to agents but has no column for associated skills.

### Swarm-Task-Planner Agent (development-harness)

The agent at `plugins/development-harness/agents/swarm-task-planner.md` uses the same template structure (lines 249-262). It uses `role:` instead of `agent:` (role is resolved to a concrete agent via the language manifest at runtime). Same gap: no `skills` field.

### implement-feature Skill

The skill at `.claude/skills/implement-feature/SKILL.md` executes this delegation pattern (lines 58-65):

```text
3. For each ready task:
- Route to the agent named in the task's **Agent** field.
- Launch the agent with a prompt that invokes start-task:
  Skill(skill="start-task", args="{task_file_path} --task {task_id}")
```

The agent name from the task metadata is used as the `subagent_type` when the orchestrator invokes the Agent tool. But no skills are attached. The orchestrator has no data source for task-level skills.

### start-task Skill

The skill at `.claude/skills/start-task/SKILL.md` receives `$ARGUMENTS` containing the task file path and optional `--task` ID. Its actions (lines 66-89):

1. Read the task file and the linked architecture spec
2. Select the task
3. Update status to `in-progress`
4. Write active-task context file
5. Implement against acceptance criteria

It does not read the `agent` field. It does not read any `skills` field. It does not load or activate any skills based on task metadata. The sub-agent operates with only the skills declared in the agent definition file (the `skills:` frontmatter key in the agent `.md` file), which are static per agent type, not per task.

### implementation_manager.py

The Task dataclass at `plugins/python3-development/skills/implementation-manager/scripts/implementation_manager.py` (lines 89-113) has these fields:

```python
@dataclass
class Task:
    id: str
    name: str
    status: TaskStatus
    dependencies: list[str] = field(default_factory=list)
    agent: str | None = None
    priority: TaskPriority = TaskPriority.CRITICAL
    complexity: str = "Medium"
    started: str | None = None
    completed: str | None = None
```

No `skills` field. The `to_dict()` method (lines 115-131) and `TaskDict` TypedDict (lines 175-190) also lack a skills field. The `ready-tasks` command output (lines 1029-1035) includes `id`, `name`, and `agent` but not skills.

### task_status_hook.py

The hook script at `plugins/python3-development/skills/implementation-manager/scripts/task_status_hook.py` handles `SubagentStop` and `PostToolUse` events. It does not read or propagate any skills data.

---

## Desired State

### 1. Task YAML Schema Extension

Add an optional `skills` field to the task YAML frontmatter schema:

```yaml
skills:
  type: array
  items:
    type: string
  default: []
  description: "Skills to load in the sub-agent executing this task"
```

Example task frontmatter with skills:

```yaml
---
task: T3
title: Create Scenario Integration Tests
status: not-started
agent: fastmcp-python-tests
skills:
  - fastmcp-python-tests
  - python3-development
dependencies: [T1, T2]
priority: 1
complexity: high
---
```

### 2. Swarm-Task-Planner Auto-Detection

Both swarm-task-planner agents (python3-development and development-harness versions) should:

- Include `skills:` in the task frontmatter template
- Auto-detect test-writing tasks by keywords in the task title or requirements (e.g., "test", "pytest", "tests", "test coverage", "integration tests")
- Map detected task types to relevant skills using a skills mapping table
- Allow explicit skills specification in the architecture spec to override auto-detection

Proposed skills mapping (initial):

| Task Type Pattern | Skills to Attach |
|-------------------|-----------------|
| Test writing (pytest) | `fastmcp-python-tests`, `python3-development` |
| Skill creation | `plugin-creator:skill-creator` |
| Documentation | `development-harness:clear-cove-task-design` |

### 3. implementation_manager.py Data Model Extension

- Add `skills: list[str]` field to the `Task` dataclass (default: empty list)
- Add `skills` to `TaskDict` and `TaskData` TypedDicts
- Parse `skills` from YAML frontmatter in `parse_task_from_frontmatter()`
- Include `skills` in `ready-tasks` command output (so the orchestrator can read it)

### 4. implement-feature Skill Context Propagation

The `/implement-feature` execution loop must read the `skills` field from the ready task data and pass it when constructing the delegation prompt. The mechanism depends on how Claude Code agent invocations support skill loading:

- If the Agent tool supports a `skills` parameter: pass the skills list directly
- If skills must be loaded via `Skill()` calls: the delegation prompt should include instructions for the sub-agent to load the listed skills before starting work
- If skills are loaded via agent definition frontmatter: generate a dynamic agent prompt that includes the task-specific skills in addition to the agent's default skills

### 5. start-task Skill Awareness

The `/start-task` skill should read the `skills` field from the task metadata and either:

- Activate those skills within the current agent context (if the framework supports it)
- Include them in the task execution instructions so the agent knows to reference them
- Pass them as additional context to the implementation step

---

## Scope

### Files Requiring Changes

| File | Change Type | Description |
|------|------------|-------------|
| `.claude/docs/TASK_FILE_FORMAT.md` | Schema extension | Add `skills` field to JSON schema and field definitions table |
| `plugins/python3-development/agents/swarm-task-planner.md` | Template update | Add `skills:` to task frontmatter template, add skills mapping table, add auto-detection logic |
| `plugins/development-harness/agents/swarm-task-planner.md` | Template update | Same changes as python3-development version |
| `plugins/python3-development/skills/implementation-manager/scripts/implementation_manager.py` | Data model + parsing | Add `skills` field to Task, TaskDict, TaskData; parse from frontmatter; include in output |
| `.claude/skills/implement-feature/SKILL.md` | Delegation update | Read `skills` from ready task data, propagate to sub-agent delegation |
| `.claude/skills/start-task/SKILL.md` | Context reading | Read `skills` field from task metadata, integrate into execution context |
| `.claude/rules/local-workflow.md` | Documentation update | Document skills propagation in the SAM workflow reference |

### Files NOT Requiring Changes

| File | Reason |
|------|--------|
| `task_format.py` | Shared YAML utilities are field-agnostic; no changes needed for a new optional field |
| `task_status_hook.py` | Hook script handles status/timestamps only; skills are not relevant to hook operations |
| Existing task files in `plan/` | Backward compatible: missing `skills` field defaults to empty list |
| `split_task_file.py` | Task splitting preserves all frontmatter fields; no special handling needed |
| `migrate_task_format.py` | Legacy format has no skills field; migration produces empty list by default |

---

## Constraints

### Backward Compatibility (MUST)

- Existing task files without a `skills:` field must remain valid
- The `skills` field must be optional with a default of `[]`
- All parsers must handle missing `skills` gracefully (empty list, not error)
- The validate command must not flag missing `skills` as an error or warning

### Schema Consistency (MUST)

- The `skills` field must follow the same pattern as other array fields (`dependencies`, `parallelize-with`, `blocked-by`)
- Values must be strings matching skill activation syntax (e.g., `"fastmcp-python-tests"`, `"plugin-creator:skill-creator"`)

### Dual-Format Support (MUST)

- YAML frontmatter: `skills:` array field in frontmatter block
- Legacy markdown: `**Skills**: skill1, skill2` bold field line (for completeness, though new tasks should use YAML format)

### No Breaking Changes to Agent Definitions (MUST)

- Agent `.md` files already have a `skills:` frontmatter key for static skills
- Task-level skills are additive: they supplement the agent's default skills, not replace them
- If a skill is listed both in the agent definition and the task metadata, it should be deduplicated

---

## Open Questions

### Q1: Skill Activation Mechanism

How does a sub-agent actually "load" a skill at runtime? The Agent tool's `subagent_type` parameter maps to an agent definition file which has a static `skills:` frontmatter key. There is no documented mechanism to dynamically add skills to a running sub-agent.

**Options:**

- A: Embed skill content in the delegation prompt (bloats prompt, but works today)
- B: Use the `skills:` frontmatter key in a dynamically-constructed agent prompt
- C: Use `Skill()` invocations at the start of the sub-agent's execution
- D: Wait for Claude Code to support dynamic skill loading via the Agent tool API

**Recommendation**: Investigate which of these options the current Claude Code framework actually supports before committing to an implementation approach. This is the critical design decision.

### Q2: Skills Mapping Table Location

Where should the mapping from task-type keywords to skill names live?

**Options:**

- A: Inline in the swarm-task-planner agent definition (simple, duplicated between python3-development and development-harness)
- B: In a shared reference file that both planners reference (DRY, but adds a file)
- C: In the language manifest (aligns with the development-harness composition model)

### Q3: Role vs Agent in development-harness

The development-harness swarm-task-planner uses `role:` instead of `agent:` in task frontmatter. Should `skills:` be role-level (shared across all agents resolving that role) or task-level (specific to each task instance)?

**Recommendation**: Task-level. Skills vary by task content, not by agent role. A `test-designer` role may need `fastmcp-python-tests` for one task but `playwright-testing` for another.

### Q4: Interaction with Agent-Level Skills

Agent definition files (e.g., `plugins/python3-development/agents/swarm-task-planner.md`) already have `skills: clear-cove-task-design` in their frontmatter. When a task specifies `skills: [fastmcp-python-tests]` and the agent already has `skills: clear-cove-task-design`, how are they combined?

**Expected behavior**: Union of agent-level and task-level skills, with task-level taking priority in case of conflicts.

---

## Evidence Inventory

All claims in this document are based on direct file reads performed during discovery:

| Claim | Source File | Lines |
|-------|------------|-------|
| No `skills` field in JSON schema | `.claude/docs/TASK_FILE_FORMAT.md` | 264-345 |
| Task dataclass lacks `skills` | `plugins/python3-development/skills/implementation-manager/scripts/implementation_manager.py` | 89-113 |
| swarm-task-planner template lacks `skills` | `plugins/python3-development/agents/swarm-task-planner.md` | 250-263 |
| swarm-task-planner (dev-harness) template lacks `skills` | `plugins/development-harness/agents/swarm-task-planner.md` | 249-262 |
| start-task ignores agent field | `.claude/skills/start-task/SKILL.md` | 66-89 |
| implement-feature delegation pattern | `.claude/skills/implement-feature/SKILL.md` | 58-65 |
| Hook script does not handle skills | `plugins/python3-development/skills/implementation-manager/scripts/task_status_hook.py` | 444-556 |
| ready-tasks output lacks skills | `plugins/python3-development/skills/implementation-manager/scripts/implementation_manager.py` | 1029-1035 |
