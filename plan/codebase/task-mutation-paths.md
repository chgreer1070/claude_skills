# Task Metadata Write Paths — SAM Implementation Workflow

**Analysis Date:** 2026-03-06
**Backlog Item:** #451 — Enforcing single-authority task state mutation
**Scope:** All write paths for task metadata fields (`status`, `started`, `completed`, `last_activity`)

---

## Files Analyzed

1. `plugins/python3-development/skills/implementation-manager/scripts/task_status_hook.py`
2. `plugins/python3-development/skills/implementation-manager/scripts/implementation_manager.py`
3. `plugins/python3-development/skills/implementation-manager/scripts/task_format.py`
4. `.claude/skills/start-task/SKILL.md`
5. `.claude/skills/implement-feature/SKILL.md`
6. `.claude/docs/TASK_FILE_FORMAT.md`

Additional write-path files discovered:

7. `plugins/python3-development/scripts/migrate_task_format.py`
8. `plugins/python3-development/scripts/split_task_file.py`

---

## Per-File Analysis

### 1. `task_status_hook.py`

**Role:** Automated hook script. Receives JSON from Claude Code hook events via stdin. Two event handlers.

**Reads:**

- Task file content via `_resolve_task_file()` (line 356–377)
- Active-task context file `.claude/context/active-task-{session_id}.json` via `read_task_context()` (line 147–170)
- Sub-agent prompt via `hook_input.get("prompt")` (line 406–411)

**Writes:**

| Field | Function | Lines | Trigger |
|-------|----------|-------|---------|
| `status` → `complete` | `update_task_status()` | 436 | `SubagentStop` hook event |
| `completed` | `add_timestamp_to_task()` | 438 | `SubagentStop` hook event |
| `last_activity` | `add_timestamp_to_task()` | 483 | `PostToolUse` hook event on Write/Edit/Bash |

**Write dispatch path — `SubagentStop` (lines 396–447):**

```python
# line 436
updated_content = update_task_status(content, task_id, "✅ COMPLETE")
# line 438
updated_content = add_timestamp_to_task(updated_content, task_id, "Completed", timestamp)
# line 439
resolved_path.write_text(updated_content, encoding="utf-8")
```

Trigger condition: hook event `SubagentStop` fires when a sub-agent finishes. The script parses the sub-agent's prompt for a `/start-task` or `Skill(skill="start-task", ...)` pattern (lines 111–128). Falls back to reading the context file if prompt parsing fails (lines 414–416).

**Write dispatch path — `PostToolUse` (lines 450–487):**

```python
# line 483
updated_content = add_timestamp_to_task(content, task_id, "LastActivity", timestamp)
# line 484
resolved_path.write_text(updated_content, encoding="utf-8")
```

Trigger condition: hook event `PostToolUse` fires on any `Write`, `Edit`, or `Bash` tool call (lines 502–506). Reads current task from `.claude/context/active-task-{session_id}.json`.

**Guard analysis:**

- No guard against writing `completed` if it already exists. `update_yaml_field()` in `task_format.py` overwrites any existing value unconditionally (lines 205–215 of `task_format.py`).
- No guard against writing `status: complete` if status is already `complete`. `update_task_status()` calls `update_yaml_field()` which overwrites unconditionally.
- No guard against writing `last_activity` while status is already `complete` (a completed task can still receive `last_activity` updates from any subsequent tool call in the same session if the context file was not yet deleted).
- Context file deletion happens at line 447 (after the `SubagentStop` write), but only if `session_id` is present. If `session_id` is absent, the context file persists.

---

### 2. `implementation_manager.py`

**Role:** Read-only CLI query tool. Does not write task files.

**Reads:**

- Task files via `parse_task_file()` / `parse_task_from_frontmatter()` (lines 475–498, 381–445)
- Status, started, completed, dependencies, skills fields (lines 416–432)

**Writes:** None. No `write_text` or file mutation calls present. All commands (`list-features`, `status`, `ready-tasks`, `validate`) are read-only.

**`get_ready_tasks()` logic (lines 727–756):**

```python
def get_ready_tasks(tasks: list[Task]) -> list[Task]:
    status_by_id: dict[str, TaskStatus] = {task.id: task.status for task in tasks}
    ready: list[Task] = []

    for task in tasks:
        # Skip if not NOT_STARTED
        if task.status != TaskStatus.NOT_STARTED:
            continue

        # Check if all dependencies are terminal (complete, deferred, or skipped)
        deps_satisfied = all(status_by_id.get(dep_id) in _TERMINAL_STATUSES for dep_id in task.dependencies)

        if deps_satisfied:
            ready.append(task)

    return ready
```

**Dual-dispatch gap — `IN_PROGRESS` check:**

`get_ready_tasks()` filters exclusively on `TaskStatus.NOT_STARTED` (line 747: `if task.status != TaskStatus.NOT_STARTED: continue`). A task with status `in-progress` is excluded from the ready list. This means a task already claimed by one agent will not be returned as ready to a second agent in the same query.

**However, the gap is temporal:** `get_ready_tasks()` reads the task file at query time. If two orchestrator loops call `ready-tasks` before either sub-agent has written `in-progress` to disk (i.e., before `/start-task` step 3 executes), both queries return the same task as ready. There is no locking or atomic claim mechanism. The `IN_PROGRESS` filter only protects against re-dispatch after the status has been written, not before.

---

### 3. `task_format.py`

**Role:** Shared YAML utilities. No direct file I/O — operates on string content only.

**Reads:** Parses YAML frontmatter from string content via `parse_yaml_frontmatter()` (lines 108–147) and `has_yaml_frontmatter()` (lines 79–105).

**Writes (string mutation, not disk):**

| Function | Lines | What it mutates |
|----------|-------|-----------------|
| `update_yaml_field()` | 155–217 | Replaces or inserts any YAML field in frontmatter string |
| `normalize_status()` | 251–292 | Returns normalized status string (no disk write) |

**`update_yaml_field()` behavior (lines 196–215):**

- Scans frontmatter lines for an existing `field:` pattern.
- If found, replaces that line (and any continuation lines for list values) unconditionally.
- If not found, inserts a new line before the closing `---`.
- No idempotency check — calling it twice with the same field writes twice (second call is a no-op only because the value happens to be the same, not by design).

---

### 4. `.claude/skills/start-task/SKILL.md`

**Role:** Agent-facing skill loaded by a sub-agent. Instructs the agent (LLM) directly what to write.

**Reads:** Task file (step 1), architecture spec (step 1), `skills:` field from frontmatter (step 2a).

**Writes instructed by the skill (agent performs these):**

| Field | Format | Lines in SKILL.md | Trigger |
|-------|--------|-------------------|---------|
| `status` → `in-progress` | YAML: `status: in-progress` | 83–85 | Agent starting a task (step 3) |
| `started` | YAML: `started: {ISO timestamp}` | 85 | Agent starting a task (step 3) |
| `status` → `complete` | YAML: `status: complete` | 54–56 | `--complete` argument (explicit) |
| `completed` | YAML: `completed: {ISO timestamp}` | 54–56 | `--complete` argument (explicit) |
| `divergence-notes` (count) | YAML integer field | 125 | Agent records a divergence note |

**Context file write (step 4, lines 91–95):**

```bash
printf '%s' '{"task_file_path": "{task_file_path}", "task_id": "{task_id}"}' \
  > ".claude/context/active-task-${CLAUDE_SESSION_ID}.json"
```

The agent is instructed to write this context file. This is read by `task_status_hook.py`'s `PostToolUse` handler.

**Guard analysis:**

- No instruction to check whether `status` is already `in-progress` before writing.
- No instruction to check whether `started` already has a value before writing.
- If `/start-task` is invoked twice for the same task (e.g., retried), the skill will overwrite `status` and `started` without any guard.

---

### 5. `.claude/skills/implement-feature/SKILL.md`

**Role:** Orchestrator skill. Drives the progress loop. Does not directly write task files.

**Reads:** Output of `implementation_manager.py status` and `ready-tasks` commands (Progress Loop steps 1–2).

**Writes:** None directly. Delegates task execution to sub-agents via `Skill(skill="start-task", ...)`.

**Relevant dispatch (lines 58–79):**

The skill instructs the orchestrator to iterate `ready-tasks` output and delegate each to an agent. No coordination between parallel delegations is specified. No check for `IN_PROGRESS` tasks before dispatching — relies entirely on `get_ready_tasks()` returning `NOT_STARTED` only.

---

### 6. `.claude/docs/TASK_FILE_FORMAT.md`

**Role:** Specification document. Defines the authorized writers table and field schema. Not executable.

**Authorized Writers Table (lines 176–186):**

| Script | Purpose |
|--------|---------|
| `implementation_manager.py` | Read-only (queries only) |
| `task_status_hook.py` | Timestamp and status updates from hooks |
| `split_task_file.py` | Splits monolithic files |
| `migrate_task_format.py` | Converts legacy format |

Note: `start-task/SKILL.md` (agent-driven writes) and `split_task_file.py` / `migrate_task_format.py` writes are present in practice but the authorized writers table does not distinguish between lifecycle writes (`status`, `started`, `completed`) and structural writes (format migration). The `start-task` skill is absent from this table entirely despite being a primary writer of `status` and `started`.

---

## Additional Write Paths Beyond the 6 Listed Files

### 7. `plugins/python3-development/scripts/migrate_task_format.py`

**Writes (lines 378–383):**

- Creates a timestamped backup: `file_path.with_suffix(f".md.backup.{timestamp}").write_text(content)` (line 379)
- Overwrites the original task file with migrated YAML frontmatter content: `file_path.write_text(new_content)` (line 383)

**Fields written:** All metadata fields including `status`, `started`, `completed`, `agent`, `dependencies`, `priority`, `complexity` — full frontmatter rewrite.

**Guard:** Only writes if `errors == 0` (line 376). Has `--dry-run` mode. Backs up original. Does not check for `in-progress` tasks before overwriting.

### 8. `plugins/python3-development/scripts/split_task_file.py`

**Writes (line 343):**

- Creates individual per-task `.md` files: `output_path.write_text(content)` (line 343)
- Writes `started` and `completed` fields if they exist on the source task (lines 330–333)

**Fields written:** Full frontmatter including `status`, `started`, `completed` in per-file output.

**Guard:** None for `in-progress` tasks. Structural script only; not called during normal workflow execution.

---

## Consolidated Field Ownership Table

| Field | Writers | Trigger | Has Guard Against Overwrite? |
|-------|---------|---------|------------------------------|
| `status` → `in-progress` | `start-task` skill (agent direct write) | Agent begins task (step 3) | No |
| `status` → `complete` (hook path) | `task_status_hook.py:436` | `SubagentStop` hook event | No |
| `status` → `complete` (explicit path) | `start-task` skill (agent direct write) | `--complete` argument | No |
| `started` | `start-task` skill (agent direct write) | Agent begins task (step 3) | No |
| `completed` (hook path) | `task_status_hook.py:438` | `SubagentStop` hook event | No |
| `completed` (explicit path) | `start-task` skill (agent direct write) | `--complete` argument | No |
| `last_activity` | `task_status_hook.py:483` | `PostToolUse` on Write/Edit/Bash | No |
| `divergence-notes` | `start-task` skill (agent direct write) | Agent records divergence note | No |
| All fields (migration) | `migrate_task_format.py:383` | Manual CLI invocation | `errors == 0` only |
| All fields (split) | `split_task_file.py:343` | Manual CLI invocation | None |

---

## Gaps and Race Conditions

### Gap 1: Dual-writer for `status` and `completed`

Both `task_status_hook.py` (SubagentStop path) and the `start-task` skill (agent direct write via `--complete`) can write `status: complete` and `completed: {timestamp}` to the same file. There is no coordination between them.

- If an agent calls `--complete T1` and the SubagentStop hook also fires, the `completed` field is written twice.
- The second write uses `update_yaml_field()` which unconditionally replaces the existing line — so whichever fires second wins. The first timestamp is silently discarded.
- Files: `task_status_hook.py:436–439`, `start-task/SKILL.md:54–56`

### Gap 2: Dual-writer for `status: in-progress` and `started`

The `start-task` skill writes `status: in-progress` and `started: {timestamp}` as agent direct writes (step 3). No hook or script verifies these fields are absent before writing.

- If a task is retried (e.g., agent crash + re-dispatch), `/start-task` will overwrite both fields.
- The original `started` timestamp is lost — the field will reflect the retry time, not the original claim time.
- File: `start-task/SKILL.md:83–85`

### Gap 3: `get_ready_tasks()` has no `IN_PROGRESS` protection at query time

`get_ready_tasks()` in `implementation_manager.py:727–756` filters on `NOT_STARTED` only. The protection against double-dispatch relies on `status: in-progress` being flushed to disk before the next `ready-tasks` query. If:

1. Orchestrator calls `ready-tasks` → gets task T1
2. Dispatches T1 to sub-agent
3. Sub-agent starts but hasn't written `in-progress` yet
4. Orchestrator calls `ready-tasks` again (loop retry or parallel branch)
5. T1 is returned again as ready

This is a TOCTOU (time-of-check/time-of-use) window. Duration of the window = time between `ready-tasks` query and the agent writing `in-progress` (step 3 of `/start-task`).

### Gap 4: `last_activity` updates on completed tasks

`PostToolUse` hook fires on every Write/Edit/Bash call. If the context file is not deleted promptly after `SubagentStop`, subsequent tool calls in the same session will write `last_activity` to a `complete` task. The context file deletion at `task_status_hook.py:445–447` requires `session_id` to be present; if absent, the file persists indefinitely.

- No guard: `handle_activity_update()` at line 450 does not check task status before writing.
- File: `task_status_hook.py:450–487`

### Gap 5: `start-task` skill absent from TASK_FILE_FORMAT.md authorized writers table

`TASK_FILE_FORMAT.md:176–186` lists 4 authorized writers. The `start-task` skill (via agent direct file writes) is not listed. This means:

- Consumers of the spec do not know the agent itself is a write path.
- No policy governs when the agent may vs. must not write (e.g., "only write `started` if field is absent").
- File: `.claude/docs/TASK_FILE_FORMAT.md:176–186`

### Gap 6: No atomic claim operation

The current architecture has no atomic read-and-set for `status`. The sequence is:

1. Read task file (check status = `not-started`)
2. Write `status: in-progress` (separate operation)

Between steps 1 and 2, another agent could read the same `not-started` state. Without a lock or compare-and-swap, two agents can both observe `not-started` and both proceed to claim the task.

---

## Write Path Summary Diagram

```text
SubagentStop hook
  └─ task_status_hook.py:handle_subagent_stop()
       ├─ update_task_status(content, task_id, "COMPLETE")    → writes status
       ├─ add_timestamp_to_task(content, task_id, "Completed") → writes completed
       └─ resolved_path.write_text(updated_content)           → disk write

PostToolUse hook (Write|Edit|Bash)
  └─ task_status_hook.py:handle_activity_update()
       ├─ add_timestamp_to_task(content, task_id, "LastActivity") → writes last_activity
       └─ resolved_path.write_text(updated_content)               → disk write

Agent direct write (via start-task skill, step 3)
  └─ Agent edits task file with Edit tool
       ├─ status: in-progress
       └─ started: {ISO timestamp}

Agent direct write (via start-task --complete, step if --complete provided)
  └─ Agent edits task file with Edit tool
       ├─ status: complete
       └─ completed: {ISO timestamp}

Manual CLI (migrate_task_format.py)
  └─ file_path.write_text(new_content)  → full frontmatter rewrite

Manual CLI (split_task_file.py)
  └─ output_path.write_text(content)    → new per-task file with full frontmatter
```

---

_Analysis performed: 2026-03-06. All line numbers reference current file state at time of analysis._
