---
name: start-task
description: "Start or complete a specific task inside a SAM task file. Updates task status to IN PROGRESS with Started timestamp, writes active-task context for hooks, and supports --complete to mark tasks complete."
version: "1.0.0"
last_updated: "2026-01-27"
python_compatibility: "3.11+"
user-invocable: true
argument-hint: "<task-file-path> [--task <task-id>] [--complete <task-id>]"
hooks:
  PostToolUse:
    - matcher: "Write|Edit|Bash"
      hooks:
        - type: command
          command: "python3 \"${CLAUDE_PLUGIN_ROOT}/skills/implementation-manager/scripts/task_status_hook.py\""
---

# Start Task (SAM Task Execution Helper)

You are implementing a specific task from a SAM task file.

<task_input>
$ARGUMENTS
</task_input>

---

## Parse Arguments

- `task_file_path` (required): path to a `plan/tasks-*.md` file
- `--task <id>` (optional): Task ID to start (defaults to first ready task)
- `--complete <id>` (optional): Task ID to mark COMPLETE

---

## If `--complete <task-id>` Provided

1. Read the task file.
2. Edit the selected task section:
   - Change `**Status**` to `✅ COMPLETE`
   - Add/update `**Completed**: {ISO timestamp}`
3. Output: `Task {ID} marked as COMPLETE`

---

## Starting a Task

1. Read the task file and the linked architecture spec.
2. Select the task:
   - if `--task` provided, use it
   - else pick the first task where Status is NOT STARTED and all Dependencies are COMPLETE/None
3. Edit the task section:
   - set `**Status**: 🔄 IN PROGRESS`
   - add `**Started**: {ISO timestamp}`
4. Write the active-task context file (required for hook-driven LastActivity updates):

```bash
mkdir -p .claude/context
printf '%s' "{\"task_file_path\": \"{task_file_path}\", \"task_id\": \"{task_id}\"}" > ".claude/context/active-task-${CLAUDE_SESSION_ID}.json"
```

5. Implement against the task acceptance criteria and run its verification steps.
