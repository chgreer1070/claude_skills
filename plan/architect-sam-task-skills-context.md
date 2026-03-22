# Architecture Spec: SAM Task Skills Context Propagation

**Feature**: SAM Task Skills Context Propagation
**Issue**: #338
**Created**: 2026-03-01
**Status**: Architecture Spec

---

## 1. Schema Changes

### 1.1 YAML Frontmatter Field

Add `skills` as an optional array field to the task YAML schema.

```yaml
skills:
  type: array
  items:
    type: string
  default: []
  description: "Skills to load in the sub-agent executing this task"
```

### 1.2 JSON Schema Addition

Add to the `properties` object in the JSON schema at [plugins/development-harness/docs/TASK_FILE_FORMAT.md](../TASK_FILE_FORMAT.md) (inside the `properties` block, after `parallelize-with`):

```json
"skills": {
  "type": "array",
  "items": {
    "type": "string"
  },
  "default": [],
  "description": "Skills the sub-agent should load before executing this task"
}
```

### 1.3 Field Definitions Table

Add to the Optional Fields table in TASK_FILE_FORMAT.md:

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `skills` | array | Skills for the sub-agent to load | `["fastmcp-python-tests", "python3-development"]` |

### 1.4 YAML Example

```yaml
---
task: T3
title: Create Scenario Integration Tests
status: not-started
agent: python-pytest-architect
skills:
  - fastmcp-python-tests
  - python3-development
dependencies: [T1, T2]
priority: 1
complexity: high
---
```

### 1.5 Legacy Markdown Format

For backward compatibility with the legacy bold-field format:

```markdown
**Skills**: fastmcp-python-tests, python3-development
```

Parsed as comma-separated strings, trimmed. The legacy format parser should handle this field alongside existing fields like `**Agent**`, `**Dependencies**`, etc.

---

## 2. Planner Changes

### 2.1 Keyword-to-Skill Mapping Table

Add a mapping table directly in both swarm-task-planner agent prompts. The table is used during task decomposition (Phase 3) to auto-populate the `skills:` field based on task content.

```markdown
## Skills Mapping Table

Map task content to skills that the executing agent should load. Apply when task title,
requirements, or expected outputs match the pattern. Multiple rows can match.

| Pattern (in title, requirements, or outputs) | Skills |
|-----------------------------------------------|--------|
| pytest, test, tests, test coverage, integration tests, unit tests | `fastmcp-python-tests`, `python3-development` |
| skill creation, SKILL.md, skill structure | `plugin-creator:skill-creator` |
| documentation, docs, README, CONTRIBUTING | `development-harness:clear-cove-task-design` |
| agent creation, agent prompt, agent definition | `plugin-creator:skill-creator` |
| linting, type checking, ty, ruff | `python3-development` |
| CLI, command-line, typer, click | `python3-development` |

**Rules:**
1. If the architecture spec explicitly lists skills for a task, use those (override auto-detection).
2. If multiple patterns match, union all skills (deduplicated).
3. If no pattern matches, set `skills: []` (empty list, not omitted).
4. The table is extensible. Add new rows when new skill-task associations are identified.
```

### 2.2 Template Update

Update the YAML frontmatter template in both planner agents to include `skills:`.

Current template (python3-development version, lines 250-263):

```yaml
---
task: [Task ID]
title: [Descriptive Name]
status: not-started
agent: [agent-name]
dependencies: []
priority: [1-5]
complexity: [low/medium/high]
accuracy-risk: [low/medium/high]
skills: []
parallelize-with: []
reason: [Why parallelization is safe]
handoff: [What the worker must report back]
---
```

Current template (development-harness version, lines 249-262):

```yaml
---
task: [Task ID]
title: [Descriptive Name]
status: not-started
role: [role from table]
dependencies: []
priority: [1-5]
complexity: [low/medium/high]
accuracy-risk: [low/medium/high]
skills: []
parallelize-with: []
reason: [Why parallelization is safe]
handoff: [What the worker must report back]
---
```

### 2.3 Validation Addition

Add to Phase 5 (Plan Validation) in both planners:

```text
10. Skills field check (NEW)
    - Every task has `skills` in YAML frontmatter (may be empty list)
    - Skills values are valid skill activation names (string, optionally colon-separated plugin:skill)
    - If architecture spec prescribes skills for a task type, verify they are present
```

### 2.4 Files to Modify

| File | Change |
|------|--------|
| `plugins/python3-development/agents/swarm-task-planner.md` | Add skills mapping table (new section after Agent Assignment Rules), add `skills:` to task frontmatter template, add validation step 10 |
| `plugins/development-harness/agents/swarm-task-planner.md` | Same changes as above, using `role:` convention |

---

## 3. Orchestrator Changes (implement-feature)

### 3.1 Modified Ready-Tasks Consumption

The `/implement-feature` skill currently reads `ready-tasks` output that contains `id`, `name`, and `agent` per task. After the `implementation_manager.py` change (section 5), the output will also include `skills`.

Updated ready-tasks JSON output:

```json
{
  "feature": "my-feature",
  "ready_tasks": [
    {
      "id": "T3",
      "name": "Create Scenario Integration Tests",
      "agent": "python-pytest-architect",
      "skills": ["fastmcp-python-tests", "python3-development"]
    }
  ],
  "count": 1
}
```

### 3.2 Modified Delegation Prompt

The `/implement-feature` skill's step 3 currently delegates as:

```text
Skill(skill="start-task", args="{task_file_path} --task {task_id}")
```

The delegation prompt sent to the Agent tool must include the skills list so the sub-agent knows which skills to load. The updated delegation instruction in implement-feature's SKILL.md:

```markdown
3. For each ready task:

- Route to the agent named in the task's `agent` field (or resolved from `role`).
- If the task has a non-empty `skills` list, include in the delegation prompt:
  "Before starting work, load these skills: {comma-separated skill names}.
   For each skill, call: Skill(skill="{skill-name}")"
- Launch the agent with a prompt that invokes start-task:

  Skill(skill="start-task", args="{task_file_path} --task {task_id}")
```

The orchestrator constructs the prompt for the Agent tool call. The prompt is a string that the sub-agent reads. The sub-agent has access to the Skill tool and can invoke `Skill(skill="fastmcp-python-tests")` to load each skill.

### 3.3 Mechanism Rationale

Option C from the feature context (use `Skill()` invocations at the start of the sub-agent's execution) is the chosen mechanism. This works because:

1. Sub-agents have access to the `Skill` tool.
2. Skill loading is a standard operation that adds context to the agent's session.
3. No framework changes are needed -- the orchestrator simply includes skill-loading instructions in the delegation prompt.
4. Skills are additive: if the agent definition already declares skills, task-level skills supplement them.

### 3.4 File to Modify

| File | Change |
|------|--------|
| `.claude/skills/implement-feature/SKILL.md` | Update step 3 in Progress Loop to read `skills` from ready-tasks output and include skill-loading instructions in the delegation prompt |

---

## 4. Start-Task Changes

### 4.1 Skills Loading at Execution Start

The `/start-task` skill receives `$ARGUMENTS` containing the task file path and `--task` ID. After reading the task file and selecting the task, it should check for a `skills:` field in the frontmatter and load each skill.

Add to the "Starting a Task" section, between step 2 (Select the task) and step 3 (Update status):

```markdown
2a. Read the `skills:` field from the task's YAML frontmatter (or `**Skills**:` from legacy format).
    If non-empty, load each skill:
    - For each skill name in the list, invoke: Skill(skill="{skill-name}")
    - Skills are loaded before implementation begins so the agent has domain context.
    - If a skill fails to load (not found), log a warning and continue with remaining skills.
```

### 4.2 Redundancy with Orchestrator Instructions

Both `/implement-feature` (section 3.2) and `/start-task` (section 4.1) handle skills loading. This is intentional redundancy:

- The orchestrator's prompt instructs the sub-agent to load skills (covers the case where `/start-task` is an older version without skills awareness).
- `/start-task` reads skills from the task file directly (covers the case where the orchestrator's prompt does not include skills, e.g., manual invocation of `/start-task`).

Deduplication: If a skill is already loaded (the Skill tool returns immediately or adds no new context), loading it again is a no-op. No deduplication logic is needed in the skill or orchestrator.

### 4.3 File to Modify

| File | Change |
|------|--------|
| `.claude/skills/start-task/SKILL.md` | Add step 2a to "Starting a Task" section: read `skills:` from frontmatter and invoke `Skill()` for each |

---

## 5. Data Model Changes (implementation_manager.py)

### 5.1 Task Dataclass

Add `skills` field to the `Task` dataclass:

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
    skills: list[str] = field(default_factory=list)  # NEW
```

### 5.2 TaskDict TypedDict

Add `skills` to `TaskDict`:

```python
class TaskDict(TypedDict):
    id: str
    name: str
    status: str
    dependencies: list[str]
    agent: str | None
    priority: int
    complexity: str
    started: str | None
    completed: str | None
    skills: list[str]  # NEW
```

### 5.3 to_dict() Method

Add `skills` to the return value:

```python
def to_dict(self) -> TaskDict:
    return TaskDict(
        id=self.id,
        name=self.name,
        status=self.status.value,
        dependencies=self.dependencies,
        agent=self.agent,
        priority=self.priority.value,
        complexity=self.complexity,
        started=self.started,
        completed=self.completed,
        skills=self.skills,  # NEW
    )
```

### 5.4 parse_task_from_frontmatter()

Add skills extraction after the `completed` line (around line 403):

```python
raw_skills = frontmatter.get("skills")
skills: list[str] = []
if isinstance(raw_skills, list):
    skills = [str(s) for s in raw_skills if s]
elif isinstance(raw_skills, str) and raw_skills:
    skills = [s.strip() for s in raw_skills.split(",") if s.strip()]

return Task(
    id=task_id,
    name=title,
    status=status,
    dependencies=dependencies,
    agent=agent,
    priority=priority,
    complexity=complexity,
    started=started,
    completed=completed,
    skills=skills,  # NEW
)
```

### 5.5 ready-tasks Output

Update the `ready_tasks` command output (around line 1031) to include skills:

```python
output = {
    "feature": feature_slug,
    "ready_tasks": [
        {"id": t.id, "name": t.name, "agent": t.agent, "skills": t.skills}
        for t in ready
    ],
    "count": len(ready),
}
```

### 5.6 Legacy Markdown Parser

If the codebase has a legacy markdown parser that extracts bold fields (e.g., `**Agent**`, `**Dependencies**`), add handling for `**Skills**`:

```python
# In the legacy parser section
elif field_name == "skills":
    task.skills = [s.strip() for s in value.split(",") if s.strip()]
```

### 5.7 File to Modify

| File | Change |
|------|--------|
| `plugins/python3-development/skills/implementation-manager/scripts/implementation_manager.py` | Add `skills` field to `Task` dataclass, `TaskDict`, `to_dict()`, `parse_task_from_frontmatter()`, ready-tasks output, and legacy parser |

---

## 6. Backward Compatibility

### 6.1 Existing Task Files

- `skills` is optional with default `[]`.
- The YAML parser uses `frontmatter.get("skills")` which returns `None` for missing fields.
- `None` is handled by the `isinstance` check and produces an empty list.
- The `validate` command does not flag missing `skills` as an error or warning.

### 6.2 Existing Orchestrator Behavior

- If `skills` is `[]` in the ready-tasks output, the orchestrator's delegation prompt omits skill-loading instructions (conditional on non-empty check).
- If `/implement-feature` is an older version that does not read `skills`, the extra field in JSON output is ignored (JSON consumers ignore unknown keys).

### 6.3 Existing Agent Definitions

- Agent `.md` files already have a `skills:` frontmatter key for static skills.
- Task-level skills are additive. No override or conflict resolution needed.
- If a skill appears in both the agent definition and the task metadata, loading it twice is a no-op.

### 6.4 task_status_hook.py and task_format.py

No changes needed. These scripts handle status and timestamps only. The `skills` field is not relevant to hook operations.

### 6.5 split_task_file.py and migrate_task_format.py

No changes needed. `split_task_file.py` preserves all frontmatter fields. `migrate_task_format.py` converts legacy format to YAML and does not need special handling for `skills` (missing field defaults to empty list).

---

## 7. File Change Summary

| # | File | Change Type | Section Modified |
|---|------|-------------|------------------|
| 1 | `plugins/development-harness/docs/TASK_FILE_FORMAT.md` | Schema extension | JSON Schema `properties`, Optional Fields table, Template, Appendix |
| 2 | `plugins/python3-development/agents/swarm-task-planner.md` | Agent prompt update | Add Skills Mapping Table section, update task YAML template, add validation step 10 |
| 3 | `plugins/development-harness/agents/swarm-task-planner.md` | Agent prompt update | Same as #2 (uses `role:` instead of `agent:`) |
| 4 | `plugins/python3-development/skills/implementation-manager/scripts/implementation_manager.py` | Data model + parsing | `Task` dataclass, `TaskDict`, `to_dict()`, `parse_task_from_frontmatter()`, `ready_tasks()` output |
| 5 | `.claude/skills/implement-feature/SKILL.md` | Skill update | Step 3 in Progress Loop: read `skills`, include in delegation prompt |
| 6 | `.claude/skills/start-task/SKILL.md` | Skill update | Add step 2a: read `skills` from frontmatter, invoke `Skill()` for each |
| 7 | `.claude/rules/local-workflow.md` | Documentation | Document skills propagation in the workflow reference |

### Files NOT Changed

| File | Reason |
|------|--------|
| `plugins/python3-development/skills/implementation-manager/scripts/task_format.py` | YAML utilities are field-agnostic |
| `plugins/python3-development/skills/implementation-manager/scripts/task_status_hook.py` | Handles status/timestamps only |
| `plugins/python3-development/scripts/split_task_file.py` | Preserves all frontmatter fields generically |
| `plugins/python3-development/scripts/migrate_task_format.py` | Missing field defaults to empty list |
| Existing task files in `plan/` | Backward compatible: missing `skills` defaults to `[]` |

---

## 8. Data Flow

```text
Architecture Spec
  │ (may specify skills per task type)
  ▼
swarm-task-planner
  │ 1. Auto-detect task type from title/requirements
  │ 2. Look up Skills Mapping Table
  │ 3. Write skills: [...] in task YAML frontmatter
  ▼
Task File (plan/tasks-*.md)
  │ skills: [fastmcp-python-tests, python3-development]
  ▼
implementation_manager.py ready-tasks
  │ Parses skills from frontmatter, includes in JSON output
  ▼
implement-feature (orchestrator)
  │ Reads skills from ready-tasks output
  │ Includes skill-loading instructions in delegation prompt
  ▼
Agent Tool (sub-agent)
  │ Receives prompt with skill-loading instructions
  ▼
start-task (inside sub-agent)
  │ Reads skills from task frontmatter (redundant safety)
  │ Invokes Skill(skill="...") for each skill
  ▼
Sub-agent executes task with domain-specific skill context loaded
```
