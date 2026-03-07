---
name: implement-feature
description: Execute a SAM task plan (plan/tasks-*.md) by looping ready tasks, delegating each to its specified agent, and relying on hooks to update task timestamps/status. Use when a task file exists and you need to run the implementation loop that picks up ready tasks and delegates them to agents.
argument-hint: <task-file-path or feature-slug>
user-invocable: true
hooks:
  SubagentStop:
  - hooks:
    - type: command
      command: python3 "${CLAUDE_PLUGIN_ROOT}/skills/implementation-manager/scripts/task_status_hook.py"
version: 1.0.0
last_updated: '2026-02-28'
python_compatibility: 3.11+
---
# Implement Feature (SAM Workflow Execution)

This workflow continues from `add-new-feature`. It executes tasks from a SAM task file until complete (or blocked).

<feature_input>
$ARGUMENTS
</feature_input>

---

## Resolve Task File

Rules:

- If `$ARGUMENTS` ends with `.md`, treat it as the task file path.
- Otherwise, treat it as a feature slug (or partial slug) and resolve via `implementation_manager.py`.

Example resolution:

```bash
uv run "${CLAUDE_PLUGIN_ROOT}/skills/implementation-manager/scripts/implementation_manager.py" \
  status "${CLAUDE_PROJECT_DIR}" "$ARGUMENTS"
```

---

## Progress Loop

1. Query status:

```bash
uv run "${CLAUDE_PLUGIN_ROOT}/skills/implementation-manager/scripts/implementation_manager.py" \
  status "${CLAUDE_PROJECT_DIR}" "$ARGUMENTS"
```

2. If tasks remain, query ready tasks:

If parent story issue number is known, prefer the MCP tool:

```text
backlog_get_ready_sam_tasks(parent_issue_number=N)
Output shape: {"feature": "...", "ready_tasks": [...], "count": N}
Falls back to local cache if GitHub unavailable.
```

If parent issue number is unknown (or MCP unavailable), use CLI fallback:

```bash
uv run "${CLAUDE_PLUGIN_ROOT}/skills/implementation-manager/scripts/implementation_manager.py" \
  ready-tasks "${CLAUDE_PROJECT_DIR}" "$ARGUMENTS"
```

With GitHub flag (when parent issue is known):

```bash
uv run "${CLAUDE_PLUGIN_ROOT}/skills/implementation-manager/scripts/implementation_manager.py" \
  ready-tasks "${CLAUDE_PROJECT_DIR}" "$ARGUMENTS" --github --parent-issue N
```

3. For each ready task:

- Route to the agent named in the task's `agent` field (or resolved from `role`).
- Check the task's `skills` list from the ready-tasks JSON output.
- If `skills` is non-empty, include skill-loading instructions in the delegation prompt:

```text
Before starting work, load these skills: {comma-separated skill names}.
For each skill, call: Skill(skill="{skill-name}")
```

- If `skills` is empty or missing, do not add skill-loading instructions (backward compatible).
- Launch the agent with a prompt that invokes `start-task`:

```text
Skill(skill="start-task", args="{task_file_path} --task {task_id}")
```

> **Note**: Task-level skills are additive to agent-level skills. If the agent definition
> already declares skills via its frontmatter, task-level skills supplement them (they do not
> replace agent-level skills). Loading the same skill twice is a no-op.

4. Repeat until no tasks remain ready.

> **Hook behavior on SubagentStop**: When a sub-agent finishes, `task_status_hook.py` marks
> the task complete in the local task file. After marking the task complete locally, the hook
> calls `backlog_core.github.update_task_status()` to sync the completion to the GitHub
> sub-issue (if `github_issue` field is set in the task YAML). GitHub sync failure does not
> affect the hook exit code.

---

## Completion Gate

When all tasks show `COMPLETE`, invoke:

```text
Skill(skill="complete-implementation", args="{task_file_path}")
```
