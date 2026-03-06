---
feature: enforce-single-authority-task-state
backlog-item: "#451"
title: Enforce single-authority task state mutation in orchestrator
version: "1.0"
created: "2026-03-06"
architect-spec: plan/architect-enforce-single-authority-task-state.md
codebase-analysis: plan/codebase/task-mutation-paths.md
tasks:
  - "1.1": Add claim-task command and update get_ready_tasks docstring in implementation_manager.py
  - "1.2": Add last_activity guard to task_status_hook.py handle_activity_update
  - "2.1": Replace step 3 in start-task SKILL.md with claim-task invocation
  - "2.2": Replace Authorized Writers section in TASK_FILE_FORMAT.md
  - "3.1": Verification — smoke-test claim-task command end-to-end
---

<!-- Context Manifest -->
<!-- architect-spec: plan/architect-enforce-single-authority-task-state.md -->
<!-- codebase-analysis: plan/codebase/task-mutation-paths.md -->
<!-- backlog: .claude/backlog/p1-enforce-single-authority-task-state-mutation-in-orchestrator.md -->

---

task: "1.1"
title: "Add claim-task command and update get_ready_tasks docstring in implementation_manager.py"
status: not-started
agent: python3-development:python-cli-architect
dependencies: []
priority: 1
complexity: high
accuracy-risk: high
skills:
  - python3-development
parallelize-with: ["1.2"]
reason: "Task 1.2 writes only task_status_hook.py; task 1.1 writes only implementation_manager.py. No file conflict."
handoff: "Report: diff of implementation_manager.py showing new claim_task function and updated get_ready_tasks docstring; output of `uv run implementation_manager.py claim-task --help`; any blocking issues."

---

## Context

This task merged two candidate changes to `plugins/python3-development/skills/implementation-manager/scripts/implementation_manager.py` to avoid edit conflicts:

1. Add a new `@app.command(name="claim-task")` Typer command — the single authority for the `not-started -> in-progress` transition.
2. Update the `get_ready_tasks()` docstring to document the advisory-snapshot contract and the TOCTOU window.

Background: Three independent paths currently write task metadata with no coordination (see `plan/codebase/task-mutation-paths.md` Gaps 2, 3, 6). This causes TOCTOU races and corrupted `started` timestamps on agent retry. The `claim-task` command introduces a read-check-write sequence that refuses to claim a task that is not `not-started`.

Architecture spec: `plan/architect-enforce-single-authority-task-state.md`, sections "Component Design: claim-task Command" and "Component Design: get_ready_tasks Dual-Dispatch Guard".

## Objective

Add `claim-task` as a new Typer command to `implementation_manager.py` and update the `get_ready_tasks()` docstring to document the advisory-snapshot contract.

## Required Inputs

- `plugins/python3-development/skills/implementation-manager/scripts/implementation_manager.py` — full file (read before editing; line numbers from codebase analysis may have shifted)
- `plugins/python3-development/skills/implementation-manager/scripts/task_format.py` — to confirm `update_yaml_field()` and `parse_yaml_frontmatter()` signatures before calling them
- `plan/architect-enforce-single-authority-task-state.md` — authoritative design; sections "Component Design: claim-task Command", "YAML Write Mechanics", "Exit Code Summary", "JSON Output Contract", "Error Handling and Failure Modes"
- Assumption: `update_yaml_field(content: str, field: str, value: str) -> str` operates on string content, returns mutated string. Confirm by reading `task_format.py` lines 155-217 before implementing.

## Requirements

### claim-task command

1. Register a new Typer command `@app.command(name="claim-task")` on the existing `app` instance.
2. Command signature:

   ```python
   def claim_task(
       task_file_path: Annotated[Path, typer.Argument(
           help="Path to the task file or directory.",
           exists=True,
           resolve_path=True,
       )],
       task_id: Annotated[str, typer.Argument(
           help="Task ID to claim (e.g., T1, 1.1).",
       )],
   ) -> None:
   ```

3. Implement the read-check-write sequence as specified in the architect spec:
   - Read task file content from disk with a single `path.read_text(encoding="utf-8")` call.
   - For directory-based task files, use the existing `_parse_task_directory()` output to locate the individual `.md` file containing `task_id`. The write target is that individual file, not the directory.
   - Parse YAML frontmatter to extract current `status` for `task_id`.
   - If task not found: emit JSON `{"claimed": false, "task_id": ..., "reason": "task-not-found", "task_file": ...}` to both stdout and stderr; `raise typer.Exit(1)`.
   - If parse fails: emit JSON `{"claimed": false, "task_id": ..., "reason": "parse-error", "error": ..., "task_file": ...}` to both stdout and stderr; `raise typer.Exit(1)`.
   - If status != `not-started`: emit JSON `{"claimed": false, "task_id": ..., "reason": "already-{status}", "current_status": ..., "task_file": ...}` to both stdout and stderr; `raise typer.Exit(1)`.
   - Build updated content: call `update_yaml_field(content, "status", "in-progress")` then `update_yaml_field(result, "started", timestamp)` — but write `started` only if the field is currently absent. If `started` already has a value in the frontmatter, preserve it.
   - Write updated content in a single `path.write_text(content, encoding="utf-8")` call.
   - On `OSError` during write: emit JSON `{"claimed": false, "reason": "write-error", "error": ..., "task_file": ...}` to both stdout and stderr; `raise typer.Exit(1)`.
   - On success: emit JSON `{"claimed": true, "task_id": ..., "started": <timestamp>, "task_file": ...}` to stdout only; `raise typer.Exit(0)`.
4. Use UTC ISO 8601 timestamp (`datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")`). Import `datetime` if not already imported.
5. JSON to stdout only (`print(json.dumps(...))`) — stderr only for error messages (`typer.echo(..., err=True)` or `print(..., file=sys.stderr)`).
6. Do not introduce any new `import` beyond what is already present in `implementation_manager.py`. Confirm `json`, `pathlib`, `datetime`, `sys`, `typer`, and `task_format` are already imported before writing.

### get_ready_tasks docstring update

7. Locate `get_ready_tasks()` (currently around line 727 based on codebase analysis — verify actual line number by reading the file). Update its docstring to match this exact text:

   ```text
   Returns tasks whose status is NOT_STARTED at the time of the snapshot.
   This list is advisory: status may change between this query and task dispatch.
   Callers MUST invoke claim-task before beginning task execution to atomically
   mark the task in-progress. If claim-task returns claimed=false, discard the
   task from the dispatch queue without error.
   ```

   The filter logic (`if task.status != TaskStatus.NOT_STARTED: continue`) is correct and must not be changed.

## Constraints

- Do not add any new runtime dependency. Only `task_format`, `typer`, `json`, `pathlib`, `datetime`, `sys`, `typing.Annotated` — all already present.
- Do not use `yaml` (pyyaml) directly. All YAML mutation goes through `task_format.update_yaml_field()`.
- JSON-only stdout. No diagnostic text on stdout. All human-readable output on stderr.
- Do not change any existing command (`list-features`, `status`, `ready-tasks`, `validate`). Add only.
- Do not change `get_ready_tasks()` filter logic — only the docstring changes.
- Do not change `task_status_hook.py`. That file is handled in task 1.2.

## Expected Outputs

- `plugins/python3-development/skills/implementation-manager/scripts/implementation_manager.py` — modified to add `claim_task` function and updated `get_ready_tasks` docstring

## Acceptance Criteria

### claim-task command

1. `uv run plugins/python3-development/skills/implementation-manager/scripts/implementation_manager.py claim-task --help` exits 0 and prints a usage string containing `claim-task`.
2. When invoked on a task with `status: not-started`, the command exits 0, stdout is valid JSON with `{"claimed": true, ...}`, and the task file on disk shows `status: in-progress` and a populated `started:` field.
3. When invoked on the same task a second time (now `status: in-progress`), the command exits 1 and stdout JSON contains `{"claimed": false, "reason": "already-in-progress", ...}`.
4. When invoked with a non-existent `task_id`, the command exits 1 and stdout JSON contains `{"claimed": false, "reason": "task-not-found", ...}`.
5. When invoked on a task that already has a `started:` value and status is reset to `not-started` manually, the `started:` field is preserved (not overwritten) after a successful claim.
6. All existing commands (`list-features`, `status`, `ready-tasks`, `validate`) continue to work — no regressions.

### get_ready_tasks docstring

7. Reading `implementation_manager.py` after the edit shows the updated docstring text verbatim in `get_ready_tasks()`.
8. The filter logic inside `get_ready_tasks()` is byte-for-byte identical to the pre-edit version (only the docstring changed).

## Verification Steps

1. Read `plugins/python3-development/skills/implementation-manager/scripts/task_format.py` lines 155-217 and confirm `update_yaml_field(content, field, value)` signature before implementing.
2. Run: `uv run plugins/python3-development/skills/implementation-manager/scripts/implementation_manager.py claim-task --help` — must exit 0.
3. Create a temporary test task file at `/tmp/test-claim-task.md` with a minimal YAML frontmatter containing `task: T1`, `title: Test`, `status: not-started`. Run `claim-task` against it. Confirm exit 0 and `status: in-progress` on disk.
4. Run `claim-task` on the same file again. Confirm exit 1 and `reason: already-in-progress` in JSON.
5. Run `uv run prek run --files plugins/python3-development/skills/implementation-manager/scripts/implementation_manager.py` — must exit 0 (no linting failures).
6. Run `uv run ty check plugins/python3-development/skills/implementation-manager/scripts/implementation_manager.py` if `ty` is available in the project — exit 0.

## CoVe Checks

- Key claims to verify:
  - `update_yaml_field()` in `task_format.py` accepts `(content: str, field: str, value: str)` and returns `str`.
  - The `started` field conditional: `update_yaml_field` overwrites unconditionally; a separate existence check is needed before calling it for `started`.
  - `_parse_task_directory()` returns objects with `.id` and a resolvable file path per task.
  - `task_format` is already imported in `implementation_manager.py` (not just used via a subprocess call).
- Verification questions:
  1. Does `update_yaml_field` (task_format.py lines 155-217) include any idempotency check for existing values, or does it always overwrite?
  2. Is `parse_yaml_frontmatter` the correct function to use to read `status` from a single task's frontmatter string, or is there a higher-level function that returns a `Task` object?
  3. Does `_parse_task_directory()` return a list of `Task` objects each with a `.file_path` attribute pointing to the individual `.md` file?
  4. Is `datetime` already imported in `implementation_manager.py`, or must it be added?
- Evidence to collect:
  - Read `task_format.py` lines 155-217 for `update_yaml_field` signature and behavior.
  - Read `implementation_manager.py` top-level imports (first ~50 lines) to confirm what is already imported.
  - Read `_parse_task_directory()` implementation to confirm return type and file path attribute name.
- Revision rule:
  - If `update_yaml_field` always overwrites, implement the `started` guard using `parse_yaml_frontmatter` to check the existing value before calling `update_yaml_field` for that field. State the check added.
  - If `_parse_task_directory()` returns objects without a direct `.file_path` attribute, locate the correct attribute name from the `Task` dataclass definition and use it.

---

task: "1.2"
title: "Add last_activity guard to task_status_hook.py handle_activity_update"
status: not-started
agent: python3-development:python-cli-architect
dependencies: []
priority: 1
complexity: low
accuracy-risk: medium
skills:
  - python3-development
parallelize-with: ["1.1"]
reason: "Task 1.1 writes only implementation_manager.py; task 1.2 writes only task_status_hook.py. No file conflict."
handoff: "Report: exact lines changed in task_status_hook.py; confirmation that handle_subagent_stop is unchanged; linting result."

---

## Context

`task_status_hook.py`'s `handle_activity_update()` function (PostToolUse handler) writes `last_activity` on every Write/Edit/Bash tool call. It currently has no guard against writing to a task whose status is already `complete` (Gap 4 from `plan/codebase/task-mutation-paths.md`). If the context file is not deleted promptly after SubagentStop, subsequent tool calls in the same session write stale activity timestamps to a completed task.

The fix is a single guard: read the current task status before writing `last_activity`; skip silently if status is `complete`.

Architecture spec: `plan/architect-enforce-single-authority-task-state.md`, section "Error Handling: task_status_hook.py PostToolUse: last_activity on Completed Task".

## Objective

Add a status check in `handle_activity_update()` that skips writing `last_activity` when the task's current on-disk status is `complete`.

## Required Inputs

- `plugins/python3-development/skills/implementation-manager/scripts/task_status_hook.py` — full file; locate `handle_activity_update()` (codebase analysis says lines 450-487; verify exact line numbers by reading)
- `plugins/python3-development/skills/implementation-manager/scripts/task_format.py` — confirm `parse_yaml_frontmatter()` or equivalent for reading current status from string content

## Requirements

1. In `handle_activity_update()`, after reading the task file content and before calling `add_timestamp_to_task()` for `last_activity`, add:

   ```python
   current_status = # parse status field from task file content string
   if current_status == "complete":
       return  # silent skip — no write, no output
   ```

2. Use the existing YAML parsing utilities from `task_format.py` — do not write a new parser.
3. The skip must be silent (no print, no log, no stderr output). The hook fires on every tool call; logging every skip would be noisy.
4. The `handle_subagent_stop()` function must remain byte-for-byte identical (no changes whatsoever).
5. No other function in `task_status_hook.py` changes.

## Constraints

- Only `handle_activity_update()` changes. No other functions.
- Silent return when status is `complete`. Do not raise, do not log.
- Do not change how `handle_subagent_stop()` works.
- Do not add new imports beyond what is already present in the file.

## Expected Outputs

- `plugins/python3-development/skills/implementation-manager/scripts/task_status_hook.py` — modified with the status guard in `handle_activity_update()`

## Acceptance Criteria

1. `handle_activity_update()` contains a status check that returns early when status is `complete`.
2. `handle_subagent_stop()` is byte-for-byte identical to the pre-edit version (diff shows no changes to that function).
3. `uv run prek run --files plugins/python3-development/skills/implementation-manager/scripts/task_status_hook.py` exits 0.

## Verification Steps

1. Read `task_status_hook.py` to locate `handle_activity_update()` and confirm the exact lines to edit.
2. Read `task_format.py` to confirm the correct function for extracting `status` from frontmatter string content.
3. After editing, read the modified `handle_activity_update()` function and confirm the guard is present before the `add_timestamp_to_task` call.
4. Read `handle_subagent_stop()` and confirm it is unchanged.
5. Run `uv run prek run --files plugins/python3-development/skills/implementation-manager/scripts/task_status_hook.py`.

## CoVe Checks

- Key claims to verify:
  - `task_format.parse_yaml_frontmatter()` (or equivalent) accepts a string and returns a dict or object from which `status` can be read.
  - The status value for a completed task on disk is exactly `"complete"` (lowercase), not `"COMPLETE"` or `"✅ COMPLETE"`.
- Verification questions:
  1. What does `parse_yaml_frontmatter()` return when called on the string content of a task file? A dict? A dataclass? What key/attribute gives the `status` value?
  2. Is there a `normalize_status()` function in `task_format.py` that should be used instead of a raw string comparison?
- Evidence to collect:
  - Read `task_format.py` `parse_yaml_frontmatter()` and `normalize_status()` implementations to confirm return type and comparison value.
- Revision rule:
  - If the status value on disk may be `"✅ COMPLETE"` (legacy emoji format), use `normalize_status()` and compare against the canonical enum value. State which comparison was used.

---

task: "2.1"
title: "Replace step 3 in start-task SKILL.md with claim-task invocation"
status: not-started
agent: general-purpose
dependencies: ["1.1"]
priority: 2
complexity: medium
accuracy-risk: medium
skills: []
parallelize-with: ["2.2"]
reason: "Task 2.1 writes only .claude/skills/start-task/SKILL.md; task 2.2 writes only .claude/docs/TASK_FILE_FORMAT.md. No file conflict. Both depend on 1.1 being complete (claim-task must exist before the skill references it)."
handoff: "Report: diff of SKILL.md showing step 3 replacement; confirmation that all other steps are unchanged; linting result."

---

## Context

`.claude/skills/start-task/SKILL.md` step 3 currently instructs the agent to directly edit the YAML frontmatter (`status: in-progress`, `started: {ISO timestamp}`) using the Edit tool. This is the agent-direct-write path that causes the TOCTOU race (Gap 3) and the lost `started` timestamp on retry (Gap 2).

With task 1.1 complete, `implementation_manager.py` now has a `claim-task` command. Step 3 is replaced to invoke that command instead.

The replacement text is fully specified in the architect spec at:
`plan/architect-enforce-single-authority-task-state.md`, section "Component Design: start-task SKILL.md Replacement Instructions".

Task 1.1 must be complete before this task starts — the `claim-task` command must exist on disk before the skill references it.

## Objective

Replace the current step 3 in `.claude/skills/start-task/SKILL.md` with the `claim-task` invocation protocol from the architect spec, leaving all other steps (1, 2, 2a, 4, 5, 6) unchanged.

## Required Inputs

- `.claude/skills/start-task/SKILL.md` — full file (read before editing; step 3 is currently lines 81-89)
- `plan/architect-enforce-single-authority-task-state.md`, section "Component Design: start-task SKILL.md Replacement Instructions" — authoritative replacement text
- Prerequisite: task 1.1 must be `complete` (claim-task command exists in `implementation_manager.py`)

## Requirements

### Step 3 replacement

1. Read the current SKILL.md and locate step 3 (the block beginning with `3. Update the task status:`).
2. Replace step 3 in its entirety with the following text (copied exactly from the architect spec):

   ````text
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

      Print the result:

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

      If the task file uses legacy inline markdown format (not YAML frontmatter):

      - Emit a warning: `Task {id} is in legacy markdown format. Run migrate_task_format.py before executing.`
      - STOP. Do not proceed with implementation.
   ````

3. Do not modify steps 1, 2, 2a, 4, 5, or 6.
4. Do not modify the YAML frontmatter block at the top of SKILL.md.
5. Do not modify the `## If --complete <task-id> Provided` section.

### Code fence validation

6. All fenced code blocks in the replacement text must use language specifiers (`bash`, `text`, etc.). Verify the replacement has no bare ` ``` ` without a language tag.
7. Fenced code blocks must have a blank line before and after them (MD031 rule).

## Constraints

- Only step 3 of the "Starting a Task" section changes.
- Do not add, remove, or reorder any other steps.
- Do not change the SKILL.md YAML frontmatter (`name`, `description`, `hooks`, `version`, etc.).
- SKILL.md is agent-facing prose — do not convert it to a shell script.

## Expected Outputs

- `.claude/skills/start-task/SKILL.md` — modified with step 3 replaced

## Acceptance Criteria

1. Reading `.claude/skills/start-task/SKILL.md` shows step 3 begins with "Claim the task (prevents duplicate dispatch):" and contains `uv run "$IMPL_MGR" claim-task`.
2. The old text "Edit the `status:` field in frontmatter to `in-progress`" does not appear anywhere in the file.
3. Steps 1, 2, 2a, 4, 5, 6 are word-for-word identical to the pre-edit version.
4. The `## If --complete <task-id> Provided` section is word-for-word identical to the pre-edit version.
5. `uv run prek run --files .claude/skills/start-task/SKILL.md` exits 0.

## Verification Steps

1. Read `.claude/skills/start-task/SKILL.md` before editing — capture current step 3 text.
2. Apply the replacement using the Edit tool with `old_string` set to the full current step 3 block and `new_string` set to the replacement from the architect spec.
3. Read the modified file and verify step 3 now contains `claim-task` invocation.
4. Verify steps 1, 2, 2a, 4, 5, 6 are unchanged by reading them in the modified file.
5. Run `uv run prek run --files .claude/skills/start-task/SKILL.md`.

## CoVe Checks

- Key claims to verify:
  - The replacement text in the architect spec uses `{task_file_path}` and `{task_id}` as template placeholders (curly-brace syntax), which is the existing convention in SKILL.md. Confirm the existing SKILL.md uses the same convention (not `$TASK_FILE_PATH` shell-variable style) so the replacement is consistent.
  - The SKILL.md uses 4-backtick outer fences for nested code blocks. The replacement includes a nested code fence — confirm the backtick count in the replacement matches the file's existing convention.
- Verification questions:
  1. Does the existing SKILL.md use `{task_file_path}` (curly-brace) as its placeholder convention throughout steps 4-6?
  2. What backtick count does the existing SKILL.md use for outer fences wrapping nested code (4 or 3)?
- Evidence to collect:
  - Read `.claude/skills/start-task/SKILL.md` lines 91-96 (step 4 context file write) to confirm placeholder convention.
  - Read SKILL.md around the divergence note template (lines 113-123) to confirm outer fence backtick count.
- Revision rule:
  - If the existing file uses a different placeholder convention or backtick count, adjust the replacement text to match. State what was adjusted.

---

task: "2.2"
title: "Replace Authorized Writers section in TASK_FILE_FORMAT.md"
status: not-started
agent: general-purpose
dependencies: ["1.1"]
priority: 2
complexity: medium
accuracy-risk: low
skills: []
parallelize-with: ["2.1"]
reason: "Task 2.2 writes only .claude/docs/TASK_FILE_FORMAT.md; task 2.1 writes only .claude/skills/start-task/SKILL.md. No file conflict. Both depend on 1.1 being complete (claim-task must exist before it is documented as a writer)."
handoff: "Report: confirmation that Authorized Writers section is replaced and all other sections unchanged; linting result."

---

## Context

`.claude/docs/TASK_FILE_FORMAT.md` lines 175-186 contain an "Authorized Writers" section listing four scripts in a simple table. This table does not distinguish per-field ownership, does not list the `start-task` skill as a writer, and incorrectly describes `implementation_manager.py` as read-only (which changes with task 1.1).

The architect spec at `plan/architect-enforce-single-authority-task-state.md`, section "TASK_FILE_FORMAT.md Authorized Writers Table", defines the full replacement including the per-field ownership table, Field Ownership Rules prose, and updated Scripts table.

Both task 2.1 and 2.2 depend on task 1.1 being complete so the documentation accurately reflects the new claim-task command.

## Objective

Replace the entire "Authorized Writers" section in `.claude/docs/TASK_FILE_FORMAT.md` with the per-field ownership table, Field Ownership Rules, and Scripts table from the architect spec. Leave all other sections (Problem Statement, Format Specification, Field Definitions, Anti-Pattern: Fenced YAML Frontmatter) unchanged.

## Required Inputs

- `.claude/docs/TASK_FILE_FORMAT.md` — full file (read before editing; current Authorized Writers section is lines 175-186)
- `plan/architect-enforce-single-authority-task-state.md`, section "TASK_FILE_FORMAT.md Authorized Writers Table" — authoritative replacement content (per-field table, Field Ownership Rules subsection, Scripts table)

## Requirements

1. Read `.claude/docs/TASK_FILE_FORMAT.md` in full before editing.
2. Locate the `## Authorized Writers` section (starting at the line "Only designated scripts should write...").
3. Replace the entire section — from the opening prose through the closing row of the scripts table — with the content from the architect spec. The replacement covers:
   - Updated opening prose (explaining per-field ownership and failure modes prevented)
   - Per-field ownership table (9 rows: `status: not-started`, `status: in-progress`, `status: complete`, `status: blocked`, `started`, `completed`, `last_activity`, `divergence-notes`, and all other creation-time fields)
   - `### Field Ownership Rules` subsection (5 numbered rules)
   - `### Scripts` subsection (table with 5 rows: `implementation_manager.py`, `task_status_hook.py`, `swarm-task-planner`, `split_task_file.py`, `migrate_task_format.py`)
4. The `### Anti-Pattern: Fenced YAML Frontmatter` section that follows the Authorized Writers section must remain unchanged.
5. All other sections above the Authorized Writers section must remain unchanged.
6. All code fences in the replacement must have language specifiers (`text`, `markdown`, etc.) and blank lines before and after.

## Constraints

- Only the `## Authorized Writers` section changes. No other sections.
- Do not reorder, add, or remove any section other than the Authorized Writers replacement.
- The `### Anti-Pattern: Fenced YAML Frontmatter` subsection (which may currently be a child of `## Authorized Writers`) must be preserved and positioned immediately after the replacement content.

## Expected Outputs

- `.claude/docs/TASK_FILE_FORMAT.md` — modified with the Authorized Writers section replaced

## Acceptance Criteria

1. Reading `.claude/docs/TASK_FILE_FORMAT.md` shows a per-field ownership table with at least 9 rows covering all lifecycle fields.
2. The phrase "implementation_manager.py Read-only status queries" does not appear (old table row is gone).
3. The phrase "status: in-progress" appears in the table with "implementation_manager.py claim-task" as the authorized writer.
4. `### Field Ownership Rules` subsection exists with 5 numbered rules.
5. `### Scripts` subsection exists with a table including `implementation_manager.py`, `task_status_hook.py`, `swarm-task-planner`, `split_task_file.py`, and `migrate_task_format.py`.
6. The `### Anti-Pattern: Fenced YAML Frontmatter` section is present and unchanged.
7. `uv run prek run --files .claude/docs/TASK_FILE_FORMAT.md` exits 0.

## Verification Steps

1. Read `.claude/docs/TASK_FILE_FORMAT.md` in full before editing.
2. Apply the replacement using the Edit tool.
3. Read the modified file and confirm the per-field table exists with all required rows.
4. Confirm `### Anti-Pattern: Fenced YAML Frontmatter` is still present after the edit.
5. Run `uv run prek run --files .claude/docs/TASK_FILE_FORMAT.md`.

---

task: "3.1"
title: "Verification — smoke-test claim-task command end-to-end"
status: not-started
agent: python3-development:python-cli-architect
dependencies: ["1.1", "1.2", "2.1", "2.2"]
priority: 3
complexity: low
accuracy-risk: low
skills:
  - python3-development
parallelize-with: []
reason: "Terminal verification task; no parallelization."
handoff: "Report: output of each verification command; pass/fail per acceptance criterion; any failures with exact error text."

---

## Context

All implementation tasks (1.1, 1.2, 2.1, 2.2) must be complete before this task runs. This task verifies the end-to-end claim-task workflow against a real task file and confirms no regressions in existing commands.

## Objective

Confirm that the `claim-task` command works end-to-end on a real task file, that the `get_ready_tasks` docstring update is present, that `handle_activity_update` contains the status guard, and that linting passes across all modified files.

## Required Inputs

- A test task file to claim against. Create one at `/tmp/test-claim-smoke-task.md` using the minimal template below.
- `plugins/python3-development/skills/implementation-manager/scripts/implementation_manager.py` — to run claim-task
- All four modified files — to run linting

## Requirements

1. Create a temporary task file at `/tmp/test-claim-smoke-task.md` with this exact content:

   ```text
   ---
   task: T1
   title: Smoke Test Task
   status: not-started
   agent: general-purpose
   dependencies: []
   priority: 1
   complexity: low
   ---

   ## Context

   Temporary smoke test task for claim-task verification.

   ## Objective

   Verify claim-task command works.
   ```

2. Run `uv run plugins/python3-development/skills/implementation-manager/scripts/implementation_manager.py claim-task --help` and capture output.

3. Run claim-task against the test file:

   ```bash
   uv run plugins/python3-development/skills/implementation-manager/scripts/implementation_manager.py \
     claim-task /tmp/test-claim-smoke-task.md T1
   ```

   Capture exit code and stdout JSON.

4. Read `/tmp/test-claim-smoke-task.md` after the claim and confirm `status: in-progress` and a populated `started:` field.

5. Run claim-task again on the same file (now `in-progress`):

   ```bash
   uv run plugins/python3-development/skills/implementation-manager/scripts/implementation_manager.py \
     claim-task /tmp/test-claim-smoke-task.md T1
   ```

   Confirm exit code 1 and stdout JSON contains `"claimed": false` and `"reason": "already-in-progress"`.

6. Run `uv run plugins/python3-development/skills/implementation-manager/scripts/implementation_manager.py claim-task --help` — exit 0.

7. Run linting on all four modified files:

   ```bash
   uv run prek run --files \
     plugins/python3-development/skills/implementation-manager/scripts/implementation_manager.py \
     plugins/python3-development/skills/implementation-manager/scripts/task_status_hook.py \
     .claude/skills/start-task/SKILL.md \
     .claude/docs/TASK_FILE_FORMAT.md
   ```

8. Run an existing command to verify no regression:

   ```bash
   uv run plugins/python3-development/skills/implementation-manager/scripts/implementation_manager.py \
     list-features .
   ```

   Must exit 0 (even if output is empty).

## Constraints

- Do not modify any implementation files during this task.
- If a verification step fails, report the full error output and mark the task blocked. Do not patch the failure silently.

## Expected Outputs

- Verification report in the handoff: pass/fail per criterion, exact command outputs.

## Acceptance Criteria

1. `claim-task --help` exits 0 and output contains `claim-task`.
2. First claim on test file exits 0, stdout JSON has `"claimed": true`, file on disk has `status: in-progress`.
3. Second claim on same file (now in-progress) exits 1, stdout JSON has `"claimed": false`, `"reason": "already-in-progress"`.
4. `handle_activity_update()` in `task_status_hook.py` contains a status check guard — confirmed by reading the function.
5. `get_ready_tasks()` docstring in `implementation_manager.py` contains the advisory-snapshot contract text — confirmed by reading.
6. `start-task/SKILL.md` step 3 contains `claim-task` invocation and does not contain the old "Edit the `status:` field" text.
7. `TASK_FILE_FORMAT.md` Authorized Writers section contains the per-field ownership table.
8. Linting passes on all four modified files (prek exits 0).
9. `list-features .` exits 0 (no regression in existing commands).

## Verification Steps

1. Execute requirements 2-8 above in order.
2. For each acceptance criterion, state PASS or FAIL with evidence.
3. If any criterion FAILs, report full command output and error text. Do not proceed past a failure.
