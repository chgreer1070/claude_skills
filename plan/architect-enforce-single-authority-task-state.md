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

<!-- PENDING: get_ready_tasks guard design -->

---

## Component Design: `start-task` SKILL.md Replacement Instructions

<!-- PENDING: start-task skill replacement instructions -->

---

## TASK_FILE_FORMAT.md Authorized Writers Table

<!-- PENDING: authorized writers table design -->

---

## Error Handling and Failure Modes

<!-- PENDING: error handling design -->

---

## Architectural Decisions (ADRs)

<!-- PENDING: ADRs -->
