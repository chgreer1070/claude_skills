# Architecture: Enforce Single-Authority Task State Mutation

**Backlog Item**: #451 — Enforce single-authority task state mutation in orchestrator
**Date**: 2026-03-06
**Status**: Design Specification

---

## Executive Summary

Task metadata (`status`, `started`, `completed`, `last_activity`) is currently written by three independent paths with no coordination. This causes TOCTOU races and dual-write conflicts. This architecture introduces `claim-task` — a new CLI command in `implementation_manager.py` — as the single authority for the `not-started → in-progress` transition. All other transitions remain with `task_status_hook.py`. The `start-task` skill is updated to delegate its direct YAML edits to the CLI command. `get_ready_tasks()` gains a defense-in-depth guard against returning `IN_PROGRESS` tasks. `TASK_FILE_FORMAT.md` gains a complete Authorized Writers table with per-field ownership.

---

## Technology Stack

All components are in the existing Python 3.11+ codebase. No new runtime dependencies are introduced.

| Component | Technology | Notes |
|-----------|-----------|-------|
| CLI framework | Typer (already in use) | `claim-task` added as a new `@app.command()` |
| YAML read/write | `ruamel.yaml` (already in use via `task_format.py`) | `update_yaml_field()` and `parse_yaml_frontmatter()` already handle frontmatter mutation |
| Atomicity mechanism | Python `pathlib` file read + conditional write in a single function | True atomic file locking is not available across LLM sub-agent boundaries; the design uses a read-check-write sequence with a clear idempotency contract instead |
| JSON output | stdlib `json` | Matches existing CLI output style |
| Exit codes | stdlib `sys.exit` via Typer | `raise typer.Exit(code)` |
| Testing | `pytest` + `typer.testing.CliRunner` | Consistent with existing test patterns in the repo |

**Dependency not introduced**: The design does not require OS-level file locking (`fcntl`, `msvcrt`). The race window between concurrent LLM agents is bounded by the time-to-first-Edit in `start-task`, which in practice exceeds the claim-task round-trip time. The `claim-task` command provides a strong claim signal and returns a machine-readable result that the skill uses to abort or proceed. This is sufficient given the observed failure mode (two `ready-tasks` queries before either agent writes `in-progress`).

---

## System Context: Current State

### Current Write Paths (Three Independent Writers)

```text
WRITER 1: start-task SKILL.md (agent direct write via Edit tool)
  Writes: status → in-progress
          started → {ISO timestamp}
  Guard: None. Overwrites unconditionally.
  Source: SKILL.md step 3, lines 83-85

WRITER 2: task_status_hook.py SubagentStop handler
  Writes: status → complete
          completed → {ISO timestamp}
  Guard: None. Overwrites unconditionally.
  Source: task_status_hook.py:436-439

WRITER 3: task_status_hook.py PostToolUse handler
  Writes: last_activity → {ISO timestamp}
  Guard: None. Does not check task status before writing.
  Source: task_status_hook.py:483-484
```

### TOCTOU Window (Gap 3 from codebase analysis)

```text
Time →

T0: Orchestrator calls `ready-tasks` → returns [T1, T2, T3] (all NOT_STARTED)
T1: Orchestrator dispatches T1 to Agent-A (Sub-agent starts, loads skill)
T2: Orchestrator dispatches T1 again to Agent-B (loop retry or parallel branch)
    -- T1 is STILL NOT_STARTED on disk because Agent-A hasn't reached step 3 --
T3: Agent-A executes step 3: writes status=in-progress, started=...
T4: Agent-B executes step 3: overwrites status=in-progress, started=... (second started timestamp wins)

Result: Two agents working on T1. Second agent's started timestamp silently overwrites first.
```

### Dual-Write for `completed` (Gap 1 from codebase analysis)

```text
If agent uses --complete T1 AND SubagentStop hook fires:

Path A: Agent writes status=complete, completed={T_agent}
Path B: Hook writes status=complete, completed={T_hook}

Whichever fires second wins. T_agent < T_hook always (agent fires before stop event).
Hook timestamp is always later — so hook always silently discards agent-written timestamp.
This is the expected outcome, but undocumented and fragile.
```

### Dual Writer for `started` (Gap 2 from codebase analysis)

```text
If start-task is retried (agent crash + re-dispatch):

First invocation: writes started=2026-03-06T10:00:00Z
Second invocation: overwrites started=2026-03-06T10:15:00Z (restart time)

Original claim time is lost. Audit trail is corrupt.
```

---

## System Context: Target State

### Target Write Paths (Single Authority per Transition)

```text
TRANSITION: not-started → in-progress
  Authority: implementation_manager.py claim-task command
  Called by: start-task SKILL.md (replaces direct Edit calls)
  Guard: Reads current status before writing. Refuses if status != not-started.
  Idempotency: Returns claimed=false (exit 1) if already in-progress or complete.

TRANSITION: in-progress → complete (hook path)
  Authority: task_status_hook.py SubagentStop handler (unchanged)
  Guard: No change needed — hook firing after complete is a no-op by design
         (SubagentStop only fires once per sub-agent stop event).

TRANSITION: in-progress → complete (explicit path)
  Authority: start-task SKILL.md --complete argument (unchanged — agent writes via Edit)
  Guard: None added. SubagentStop hook overwrites with later timestamp, which is acceptable.
  Note: This path is used when agent confirms its own completion before the hook fires.

FIELD: last_activity
  Authority: task_status_hook.py PostToolUse handler (unchanged)
  Guard: Added: check task status before writing. Skip write if status == complete.
         (Addresses Gap 4: last_activity written to completed tasks.)

FIELD: divergence-notes
  Authority: start-task SKILL.md (agent direct write, unchanged)
  Reason: Divergence notes are body content appended during implementation, not lifecycle state.
```

### Component Interaction: Target State

```text
Orchestrator (/implement-feature)
  │
  ├─ ready-tasks query → [T1, T2, T3] (NOT_STARTED only, IN_PROGRESS now excluded)
  │
  ├─ For each ready task:
  │    └─ Delegates to sub-agent with start-task skill
  │
Sub-agent (/start-task)
  │
  ├─ Step 3 (NEW): uv run implementation_manager.py claim-task <path> <task-id>
  │    ├─ Exit 0 + {"claimed": true, ...}  → proceed with implementation
  │    └─ Exit 1 + {"claimed": false, "reason": "already-in-progress"} → ABORT
  │
  ├─ Step 4 (unchanged): write active-task context file
  │
  └─ Step 5+: implement acceptance criteria
       │
       └─ PostToolUse hook: task_status_hook.py
            ├─ Reads context file → gets task_id
            ├─ NEW guard: checks status != complete before writing last_activity
            └─ Writes last_activity timestamp

SubagentStop hook: task_status_hook.py
  ├─ Sets status → complete
  ├─ Writes completed timestamp
  └─ Deletes context file
```

---

## Component Design: `claim-task` Command

### Command Signature

```text
uv run implementation_manager.py claim-task <task_file_path> <task_id>
```

This is a new `@app.command(name="claim-task")` registered on the existing `app = typer.Typer(...)` instance. It follows the same Typer patterns as the existing `list-features`, `status`, `ready-tasks`, and `validate` commands.

### Arguments

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `task_file_path` | `Path` | Yes | Path to the task file (`.md`) or task directory. Accepts both absolute and relative paths. Must exist on disk. |
| `task_id` | `str` | Yes | Task identifier to claim (e.g., `"T1"`, `"1.1"`). Must match a task in the file. |

**Typer annotations**:

- `task_file_path`: `Annotated[Path, typer.Argument(help="Path to the task file or directory.", exists=True, resolve_path=True)]`
- `task_id`: `Annotated[str, typer.Argument(help="Task ID to claim (e.g., T1, 1.1).")]`

No optional flags. The command is intentionally minimal.

### Preconditions (all checked in order)

1. `task_file_path` exists on disk (enforced by Typer `exists=True`).
2. File is parseable (at least one task found). If parse fails, exit 1 with JSON error.
3. `task_id` matches a task in the file. If not found, exit 1 with JSON error.
4. Task status is `not-started`. If status is anything else, exit 1 with JSON `claimed: false`.

### Read-Check-Write Sequence (atomic semantics contract)

The command performs a single-file read, status check, and conditional write. This is not OS-atomic (no `flock`), but it is the narrowest possible window — the check and write happen in the same Python function call without any blocking I/O in between. The implementation contract:

```text
1. Read task file content from disk (single read_text call)
2. Parse YAML frontmatter to extract current status for task_id
3. If status != not-started:
     emit JSON {claimed: false, task_id: ..., reason: "already-{status}"} to stdout
     write same JSON to stderr
     raise typer.Exit(1)
4. Build updated content:
     set status field → in-progress
     set started field → current UTC ISO 8601 timestamp (if field is absent)
     NOTE: if started field already exists (should not happen after fix), preserve it
5. Write updated content to disk (single write_text call)
6. Emit JSON {claimed: true, task_id: ..., started: <timestamp>} to stdout
7. raise typer.Exit(0)
```

The `started` field write is conditional: if the field is absent, write the current timestamp. If the field already exists with a value, preserve it. This makes the command safe to call during retry scenarios where a previous claim partially succeeded.

### JSON Output Contract

**Success (exit 0)**:

```json
{
  "claimed": true,
  "task_id": "T1",
  "started": "2026-03-06T10:00:00Z",
  "task_file": "plan/tasks-5-my-feature/T1-setup.md"
}
```

**Already claimed (exit 1)**:

```json
{
  "claimed": false,
  "task_id": "T1",
  "reason": "already-in-progress",
  "current_status": "in-progress",
  "task_file": "plan/tasks-5-my-feature/T1-setup.md"
}
```

**Task not found (exit 1)**:

```json
{
  "claimed": false,
  "task_id": "T99",
  "reason": "task-not-found",
  "task_file": "plan/tasks-5-my-feature/T1-setup.md"
}
```

**Parse failure (exit 1)**:

```json
{
  "claimed": false,
  "task_id": "T1",
  "reason": "parse-error",
  "error": "Missing required YAML frontmatter fields: title"
}
```

**Reason values** (exhaustive):

| `reason` | Meaning | Exit code |
|----------|---------|-----------|
| `already-in-progress` | Task status was `in-progress` at read time | 1 |
| `already-complete` | Task status was `complete` at read time | 1 |
| `already-blocked` | Task status was `blocked` at read time | 1 |
| `already-deferred` | Task status was `deferred` at read time | 1 |
| `task-not-found` | No task with this ID exists in the file | 1 |
| `parse-error` | File could not be parsed as a task file | 1 |

### YAML Write Mechanics

The command reuses `update_yaml_field()` from `task_format.py` (already imported by `implementation_manager.py` via the `task_format` sibling module). Two calls are made:

1. `update_yaml_field(content, "status", "in-progress")` — replaces the existing `status:` line
2. `update_yaml_field(content, "started", timestamp)` — inserts `started:` if absent, or preserves if present

The `update_yaml_field` function operates on string content and returns mutated string content. The command assembles the final string and writes it in a single `path.write_text(content, encoding="utf-8")` call.

For directory-based task files (one task per `.md` file), the command resolves the specific file containing `task_id` before the read-check-write sequence. The resolution uses `_parse_task_directory()` output to find the correct file path by matching `task.id == task_id`.

### Exit Code Summary

| Exit code | Meaning |
|-----------|---------|
| 0 | Task successfully claimed (`claimed: true`) |
| 1 | Task not claimed for any reason (`claimed: false`) |
| 2 | CLI usage error (Typer default for bad arguments) |

### Usage Examples

```bash
# Claim a task in a single monolithic file
uv run plugins/python3-development/skills/implementation-manager/scripts/implementation_manager.py \
  claim-task plan/tasks-5-my-feature.md T1

# Claim a task in a directory-based task file
uv run plugins/python3-development/skills/implementation-manager/scripts/implementation_manager.py \
  claim-task plan/tasks-5-my-feature/ T1

# In shell: check exit code before proceeding
if uv run .../implementation_manager.py claim-task "$TASK_FILE" "$TASK_ID"; then
  echo "Claimed. Proceeding with implementation."
else
  echo "Not claimed. Another agent has this task."
  exit 0
fi
```

---

## Component Design: `get_ready_tasks()` Dual-Dispatch Guard

### Purpose

Defense-in-depth guard that prevents returning a task as ready if its current on-disk status is `IN_PROGRESS`. This is a second line of defense after `claim-task`. It closes the window where a task is claimed but the orchestrator queries `ready-tasks` again before the claim lands.

### Current Logic (lines 727-756 of `implementation_manager.py`)

```text
for task in tasks:
    if task.status != NOT_STARTED:
        continue           <-- only skips if NOT_STARTED already written
    if all dependencies terminal:
        ready.append(task)
```

The guard `!= NOT_STARTED` already excludes `IN_PROGRESS`. The gap is temporal: between the `ready-tasks` query and the `claim-task` write, the status on disk is still `NOT_STARTED`. `get_ready_tasks()` reads the file once per invocation and returns a snapshot.

### Design Decision: No Change Needed to `get_ready_tasks()` Filter Logic

The filter `task.status != NOT_STARTED` already covers `IN_PROGRESS`. The dual-dispatch gap is not a logic bug in `get_ready_tasks()` — it is a timing gap between query and claim. Fixing it in `get_ready_tasks()` would require re-reading the file inside the function, which changes the contract (the function currently accepts a `list[Task]` already parsed from disk).

The correct fix is in the orchestrator loop and in `claim-task`:

1. The orchestrator calls `claim-task` before delegating.
2. `claim-task` re-reads the file at the moment of claim — this is the freshest possible read.
3. If `claim-task` returns `claimed: false`, the orchestrator skips that task.

### Defense-in-Depth: Docstring Clarification

The `get_ready_tasks()` docstring and its caller `ready_tasks` command shall be updated to clarify that the returned list represents a point-in-time snapshot and that callers must use `claim-task` before dispatching. This is a documentation change, not a logic change.

**Updated docstring contract for `get_ready_tasks()`**:

```text
Returns tasks whose status is NOT_STARTED at the time of the snapshot.
This list is advisory: status may change between this query and task dispatch.
Callers MUST invoke claim-task before beginning task execution to atomically
mark the task in-progress. If claim-task returns claimed=false, discard the
task from the dispatch queue without error.
```

### Defense-in-Depth: `IN_PROGRESS` Inclusion in `status` Output

The `status` CLI command output already includes `in_progress` count. No change needed. When an operator or orchestrator calls `status` and sees `in_progress > 0`, they know tasks are running. The `ready-tasks` output will not include those tasks because their on-disk status is already `in-progress` (written by a prior `claim-task` call).

### What the Guard in `get_ready_tasks()` Does Not Need to Do

- Re-read files from disk (the caller already provides parsed tasks)
- Filter `IN_PROGRESS` differently (the existing `!= NOT_STARTED` check covers it)
- Acquire file locks (not applicable in this architecture)

### Summary

No code change to `get_ready_tasks()` logic. The dual-dispatch gap is closed by `claim-task` in the calling path (`start-task` skill), not by modifying the query function. The function docstring is updated to document this contract explicitly.

---

## Component Design: `start-task` SKILL.md Replacement Instructions

### What Changes

Step 3 of the "Starting a Task" section in `.claude/skills/start-task/SKILL.md` currently instructs the agent to directly edit the YAML frontmatter. This is replaced by a `claim-task` CLI invocation. The agent no longer writes `status` or `started` with the `Edit` tool.

The `--complete` path (agent writing `status: complete` and `completed:` when `--complete <id>` is provided) is unchanged. That path remains agent-direct-write because the hook overwrites it at SubagentStop anyway, and consolidating it into a `complete-task` CLI command is out of scope for this backlog item.

### Current Step 3 Text (to be replaced)

Current text in SKILL.md lines 81-89:

```text
3. Update the task status:

   **If YAML frontmatter format:**
   - Edit the `status:` field in frontmatter to `in-progress`
   - Add `started: {ISO timestamp}` field to frontmatter

   **If inline markdown format:**
   - Set `**Status**: 🔄 IN PROGRESS`
   - Add `**Started**: {ISO timestamp}`
```

### Replacement Text for Step 3

The following text block replaces step 3 in its entirety. The inline markdown path is removed because the format is deprecated (TASK_FILE_FORMAT.md Phase 4 in-progress). Any remaining markdown-format tasks must be migrated before execution.

```text
3. Claim the task (prevents duplicate dispatch):

   Run the claim-task command. This is the ONLY permitted way to mark a task in-progress.
   Do NOT edit status or started fields directly with the Edit tool.

   Resolve the implementation_manager.py script path:

   ```bash
   IMPL_MGR="plugins/python3-development/skills/implementation-manager/scripts/implementation_manager.py"
   ```

   Run claim-task:

   ```bash
   CLAIM_RESULT=$(uv run "$IMPL_MGR" claim-task "{task_file_path}" "{task_id}")
   CLAIM_EXIT=$?
   ```

   Parse the result:

   ```bash
   echo "$CLAIM_RESULT"
   ```

   If exit code is non-zero (`CLAIM_EXIT != 0`):

   - The task was already claimed by another agent, or is complete, or could not be found.
   - Output the full JSON result for the orchestrator.
   - STOP. Do not proceed with implementation. Do not write the context file.
   - The orchestrator's hook will detect the stop and the task remains in its current state.

   If exit code is 0 (`CLAIM_EXIT == 0`):

   - The task is claimed. `status: in-progress` and `started:` are written on disk.
   - Proceed to step 4 (write context file) and step 5 (implement).
```

### Rationale for Prose Format

The replacement is written as prose instructions with embedded bash blocks rather than a pure bash script. The `start-task` skill is loaded by an LLM agent, not executed as a shell script. The agent reads the instructions and decides how to execute them. Prose is the correct format for agent-facing skill instructions.

### Context File Step (Step 4) — No Change

Step 4 (writing the active-task context file) is unchanged. It must still run after a successful claim:

```bash
mkdir -p .claude/context
printf '%s' '{"task_file_path": "{task_file_path}", "task_id": "{task_id}"}' \
  > ".claude/context/active-task-${CLAUDE_SESSION_ID}.json"
```

This file is required by the `PostToolUse` hook (`task_status_hook.py`) to write `last_activity` updates.

### Abort Protocol When `claim-task` Returns Exit 1

The agent must not silently continue. When claim fails:

1. Print the JSON result from `claim-task` to stdout (so it appears in the orchestrator's sub-agent output).
2. Do not create the context file.
3. Do not call `Skill(skill="start-task", ...)` sub-steps.
4. End the turn. The `SubagentStop` hook will fire, but since no context file exists, the hook will find no active task and will make no writes.

This is the correct behavior: the task remains in its pre-claim state (either `not-started` or `in-progress` if another agent claimed it). The orchestrator can observe the abort via the sub-agent's output and log it.

### Backward Compatibility with Inline Markdown Format

The inline markdown task format is deprecated (TASK_FILE_FORMAT.md). The `start-task` skill no longer provides markdown-format write instructions for step 3. If a legacy markdown task file is encountered:

- The agent should emit a warning: `Task {id} is in legacy markdown format. Run migrate_task_format.py before executing.`
- The agent should not proceed with implementation.
- This converts a silent data corruption risk into a visible error.

The `claim-task` command also returns `reason: "parse-error"` for files that cannot be parsed as YAML frontmatter, which surfaces legacy format files to the caller.

---

## TASK_FILE_FORMAT.md Authorized Writers Table

### Design

The current table in `TASK_FILE_FORMAT.md` (lines 181-186) lists four scripts by name but does not specify which fields each script owns or what trigger fires the write. The replacement table adds per-field ownership, trigger, and guard columns.

The table replaces the existing "Authorized Writers" section in `TASK_FILE_FORMAT.md`. The surrounding prose ("Only designated scripts should write or update task data files...") is retained and extended.

### Replacement Table: Per-Field Ownership

| Field | Authorized Writer | Trigger | Guard | Notes |
|-------|-----------------|---------|-------|-------|
| `status: not-started` | `swarm-task-planner` agent (file creation) | Task file generation | N/A — initial write only | Set once at file creation. Never written again by any component. |
| `status: in-progress` | `implementation_manager.py claim-task` | `start-task` skill step 3 (agent invokes CLI) | Read-check-write: refuses if current status is not `not-started` | Agent must NOT write this field directly via Edit tool. |
| `status: complete` | `task_status_hook.py` SubagentStop handler | Claude Code `SubagentStop` hook event | None — SubagentStop fires once per sub-agent | May also be written by `start-task` `--complete` path; hook overwrites with later timestamp. |
| `status: blocked` | Human operator or `start-task` agent | Manual intervention or acceptance criteria failure | None | Agent may set this when blocked on external dependency. |
| `started` | `implementation_manager.py claim-task` | Same as `status: in-progress` | Conditional: written only if field is absent. Existing value preserved on retry. | Preserving the original timestamp maintains accurate audit trail on agent retry. |
| `completed` | `task_status_hook.py` SubagentStop handler | Claude Code `SubagentStop` hook event | None | Also writable by `start-task --complete` path; hook overwrites. |
| `last_activity` | `task_status_hook.py` PostToolUse handler | Claude Code `PostToolUse` hook (Write, Edit, Bash tools) | Added guard: skip write if task status is `complete` | Prevents stale activity stamps on completed tasks (Gap 4). |
| `divergence-notes` (count) | `start-task` skill (agent direct write via Edit) | Agent detects implementation divergence from architect spec | None | Appended integer count. Body content (`## Divergence Notes`) is also agent-written. |
| `task`, `title`, `agent`, `dependencies`, `priority`, `complexity`, `created`, `skills`, `issue-classification`, `scenario-target`, `analysis-method` | `swarm-task-planner` agent (file creation) | Task file generation | N/A — set at creation | These fields describe task intent and scheduling. No lifecycle component writes them after creation. |

### Replacement Prose (for "Authorized Writers" section)

The following prose replaces the paragraph beginning "Only designated scripts should write or update task data files..." through the end of the Authorized Writers section. The anti-pattern sub-section that follows (about fenced YAML frontmatter) is unchanged.

```text
## Authorized Writers

Task metadata fields are owned by specific components. Only the designated component for
a field may write that field. No other component (including LLM agents acting via Edit
tool calls) may write lifecycle fields (status, started, completed, last_activity) except
through the designated path.

This prevents the following observed failure modes:
- Dual-dispatch (two agents claiming the same task)
- Overwritten started timestamps on agent retry
- last_activity updates written to completed tasks

The table below lists every writeable field, its authorized writer, and the trigger that
fires the write.

[TABLE — see per-field ownership table above]

### Field Ownership Rules

1. status: in-progress and started are written ONLY by implementation_manager.py claim-task.
   LLM agents in the start-task skill must invoke claim-task via uv run and check exit code.
   Direct Edit of these fields by agents is an architectural violation.

2. status: complete and completed are written ONLY by task_status_hook.py SubagentStop handler.
   The start-task --complete path also writes these fields as a convenience, but the hook
   always overwrites them at SubagentStop time. If both paths fire, the hook timestamp wins.

3. last_activity is written ONLY by task_status_hook.py PostToolUse handler, and only when
   the task status is not complete. Writing last_activity to a completed task is a no-op.

4. divergence-notes (count) and the ## Divergence Notes body section are written ONLY by the
   executing agent via the start-task skill. These are not lifecycle fields.

5. All other fields (task, title, agent, dependencies, priority, complexity, created, skills,
   and analytical metadata fields) are written ONCE at task file creation by swarm-task-planner.
   No component modifies them after creation.

### Scripts

| Script | Role | Writes |
|--------|------|--------|
| implementation_manager.py | CLI for status queries AND claim-task | status: in-progress, started (via claim-task only) |
| task_status_hook.py | Hook handler for Claude Code events | status: complete, completed, last_activity |
| swarm-task-planner (agent) | Task file generator | All fields at creation |
| split_task_file.py | Structural: splits monolithic task files into per-task files | Full frontmatter (preserved from source, not lifecycle transition) |
| migrate_task_format.py | Structural: converts legacy markdown to YAML frontmatter | Full frontmatter (format migration, not lifecycle transition) |
```

---

## Error Handling and Failure Modes

### claim-task: Task Not Found

When `task_id` does not match any task in `task_file_path`:

- Exit 1.
- JSON output: `{"claimed": false, "reason": "task-not-found", "task_id": "...", "task_file": "..."}`.
- stderr: `ERROR: Task {task_id} not found in {task_file_path}`.
- Orchestrator action: log and skip. Do not retry. This is a configuration error (wrong task ID or wrong file).

### claim-task: Parse Failure

When the file cannot be parsed (missing frontmatter, malformed YAML, missing required fields):

- Exit 1.
- JSON output: `{"claimed": false, "reason": "parse-error", "error": "...", "task_file": "..."}`.
- stderr: `ERROR: Could not parse task file: {error_detail}`.
- Orchestrator action: log and skip. Flag file for manual inspection.

### claim-task: Status Not `not-started`

When the task exists but status is any value other than `not-started`:

- Exit 1.
- JSON output: `{"claimed": false, "reason": "already-{status}", "current_status": "...", "task_id": "...", "task_file": "..."}`.
- stderr: `ERROR: Task {task_id} cannot be claimed: status is {current_status}`.
- Orchestrator action:
  - If `reason: already-in-progress`: another agent is working on this task. Skip without error. Orchestrator logs this as a concurrent claim event.
  - If `reason: already-complete`: task is done. Skip. This indicates orchestrator state is stale — trigger a `status` refresh.
  - If `reason: already-blocked`: task is externally blocked. Skip. Surface to operator.

### claim-task: Write Failure

If `path.write_text()` raises `OSError` (permissions, disk full):

- Exit 1.
- JSON output: `{"claimed": false, "reason": "write-error", "error": "...", "task_file": "..."}`.
- The status field was NOT mutated (write failed). The file remains in its pre-claim state.
- Orchestrator action: log as infrastructure error. Retry on next orchestrator loop iteration.

### start-task: claim-task Returns Exit 1

The start-task skill receives exit code 1 from claim-task. Protocol:

1. Print `CLAIM_RESULT` JSON to agent stdout.
2. Do not write the active-task context file.
3. End the turn immediately.
4. SubagentStop hook fires. No context file exists. Hook makes no writes.
5. The task remains in its pre-claim state on disk.

This is a graceful abort. No data is mutated. The orchestrator observes the abort via sub-agent output logs.

### start-task: claim-task Binary Not Found

If `uv run .../implementation_manager.py claim-task` fails because the script path is wrong or `uv` is unavailable:

- The agent receives a non-zero exit code and a shell error message on stderr.
- The agent must treat any non-zero exit from the claim-task invocation as a claim failure.
- The agent must NOT fall back to direct Edit of `status` and `started` fields.
- The agent must surface the error to the operator with the full shell output.

### task_status_hook.py PostToolUse: `last_activity` on Completed Task (Gap 4 Fix)

The `handle_activity_update()` function in `task_status_hook.py` must read the task status before writing `last_activity`. If status is `complete`, the write is skipped silently (no error, no output). This is a silent skip, not an error, because the hook fires on every tool call and the completed-task case is normal during session teardown.

**Added guard (pseudocode)**:

```text
current_status = parse status field from task content
if current_status == "complete":
    return  # silent skip, no write
proceed with last_activity timestamp write
```

This guard is added to the `handle_activity_update()` function in `task_status_hook.py`. It is the only change to `task_status_hook.py` required by this backlog item.

---

## Architectural Decisions (ADRs)

### ADR-001: claim-task as a CLI Command in implementation_manager.py, Not a Standalone Script

**Status**: Accepted

**Context**: The new claim authority could be a standalone script (`claim_task.py`) or a new command in the existing `implementation_manager.py`. The start-task skill currently invokes `implementation_manager.py` for `ready-tasks`. Adding `claim-task` to the same binary reduces the number of script paths an agent must know.

**Decision**: Add `claim-task` as `@app.command(name="claim-task")` in `implementation_manager.py`.

**Consequences**:
- Positive: Single entry point for all task file operations from the skill layer.
- Positive: Reuses existing Typer app, JSON output conventions, and `task_format.py` imports.
- Positive: No new file to discover or maintain.
- Negative: `implementation_manager.py` is documented as "read-only" in `TASK_FILE_FORMAT.md`. Adding a write command changes that contract. Mitigated by updating `TASK_FILE_FORMAT.md` to reflect the new role.

**Alternatives Considered**:
- Standalone `claim_task.py`: More discoverable by name but adds a new script path to maintain.
- Add write logic to `task_status_hook.py`: That script is an event handler, not a CLI tool. Mixing roles would make it harder to test claim logic in isolation.

---

### ADR-002: Read-Check-Write Without OS File Locking

**Status**: Accepted

**Context**: True atomic claim would require `fcntl.flock` (POSIX) or `msvcrt.locking` (Windows). Neither is portable across the CI and developer environments this codebase targets. Additionally, LLM sub-agents do not hold persistent processes — they are single-turn invocations. The race window is the time between two `ready-tasks` queries before either agent reaches step 3 of `start-task`.

**Decision**: Use a narrow read-check-write sequence without OS locking. The contract is documented: the window between read and write is a single Python function call with no blocking I/O in between.

**Consequences**:
- Positive: Cross-platform. No platform-specific locking code.
- Positive: Sufficient for the observed failure mode (two orchestrator loop iterations before the first agent writes `in-progress`). The `claim-task` write now happens in milliseconds, before the orchestrator dispatches a second agent.
- Negative: A true concurrent race (two agents calling `claim-task` simultaneously at the OS scheduler level) is still possible in theory. In practice, LLM agent invocations are not concurrent at the filesystem write level — they are serialized by the Claude Code orchestrator.
- Mitigated by: The `claim-task` command returning `claimed: false` on the second call in any race, because the first write will have landed by the time the second agent reaches step 3.

**Alternatives Considered**:
- `portalocker` library: Adds a dependency. Not warranted for the observed failure mode.
- Sentinel file (`T1.lock`): Adds filesystem clutter. Not needed given the race window analysis.

---

### ADR-003: `started` Field Is Preserved on Retry, Not Overwritten

**Status**: Accepted

**Context**: If a sub-agent crashes after `claim-task` succeeds but before completing the task, the orchestrator may re-dispatch. A second `claim-task` call would find status `in-progress` and return `claimed: false`. The operator must manually reset status to `not-started` before the task can be re-dispatched. During that reset, `started` is already present on disk.

**Decision**: `claim-task` writes `started` only if the field is absent. If `started` already has a value, it is preserved. This ensures the original claim timestamp survives operator-driven resets.

**Consequences**:
- Positive: Audit trail accuracy. The `started` timestamp reflects the first claim attempt, not a retry.
- Positive: Idempotent behavior: calling `claim-task` twice (if somehow possible) does not corrupt the timestamp.
- Negative: Operator must be aware that `started` is not reset when they manually reset `status: not-started`. This is documented behavior, not a bug.

---

### ADR-004: `--complete` Path in `start-task` Is Unchanged

**Status**: Accepted

**Context**: The `--complete <task-id>` path in `start-task` has the agent write `status: complete` and `completed:` directly. The `SubagentStop` hook also writes these fields, with a later timestamp (hook fires after agent turn ends). The net result is that the hook timestamp always wins.

**Decision**: Leave the `--complete` path as agent-direct-write. Do not add a `complete-task` CLI command in this iteration.

**Consequences**:
- Positive: Scope is contained. Only the `not-started → in-progress` transition (the one with the TOCTOU race) is fixed.
- Positive: The dual-write for `completed` (Gap 1 from codebase analysis) has a deterministic outcome (hook wins). It is documented but not harmful.
- Negative: The `completed` field is still written by two paths. Deferred to a future backlog item if audit accuracy for `completed` becomes a requirement.

---

### ADR-005: Legacy Markdown Format Tasks Cannot Be Claimed

**Status**: Accepted

**Context**: `claim-task` operates on YAML frontmatter only. The `task_format.py` utilities (`update_yaml_field`, `parse_yaml_frontmatter`) are YAML-only. The legacy markdown format (`**Status**: IN PROGRESS`) is deprecated (TASK_FILE_FORMAT.md Phase 4).

**Decision**: `claim-task` returns `reason: parse-error` for markdown-format task files. The agent must surface this as an error and not proceed.

**Consequences**:
- Positive: Forces migration of legacy format before execution. Prevents silent corruption of markdown files.
- Negative: Legacy tasks cannot be executed until migrated. This is acceptable given that `migrate_task_format.py` already exists for this purpose.
- Mitigation: The `start-task` skill update includes explicit instructions to surface the legacy format error and stop.

---

## Implementation Constraints

The following constraints apply to the development agent implementing this design:

1. **No new runtime dependencies**: `claim-task` must be implementable using existing imports in `implementation_manager.py` (`task_format.py`, `typer`, `json`, `pathlib`, `datetime`).

2. **JSON-only stdout**: `claim-task` must write only valid JSON to stdout. All human-readable messages go to stderr. This enables the skill to parse the output with `json.loads()` reliably.

3. **No silent failures**: If the file write fails, the command must exit non-zero with an error JSON. It must not exit 0 with `claimed: true` unless the write succeeded.

4. **YAML library**: Use `ruamel.yaml` via the existing `task_format.py` module. Do not import `yaml` (pyyaml) directly. Per repo convention in `.claude/rules/yaml-toml-libraries.md`.

5. **`update_yaml_field()` reuse**: Do not write a new YAML mutation function. `update_yaml_field()` from `task_format.py` handles both replacement of existing fields and insertion of new fields. Use it for both `status` and `started` field writes.

6. **Directory task file resolution**: For directory-based task files, the command must locate the specific `.md` file containing `task_id` before performing the read-check-write. The resolution uses `_parse_task_directory()` to find all tasks, then matches by `task.id`. The write target is the individual file, not the directory.

7. **`task_status_hook.py` change scope**: Only `handle_activity_update()` in `task_status_hook.py` changes (Gap 4 guard). No other function in that file changes. The SubagentStop handler (`handle_subagent_stop`) is unchanged.

8. **`start-task` SKILL.md change scope**: Only step 3 of the "Starting a Task" section changes. All other steps (parse arguments, detect task format, load skills, write context file, divergence notes, implementation) are unchanged.

9. **`TASK_FILE_FORMAT.md` change scope**: The "Authorized Writers" section is replaced in full. All other sections are unchanged.
