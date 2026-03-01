# Feature Context: SAM Task Planner — Merge Same-File Tasks into Single Agent Assignment

## Document Metadata

- **Generated**: 2026-03-01
- **Input Type**: simple_description
- **Source**: Session observation from #128 validate-agent-browser (Tasks 2.1-2.3 all editing SKILL.md), GitHub Issue #316
- **Status**: DISCOVERY_COMPLETE

---

## Original Request

When multiple SAM tasks edit the same file (e.g., Tasks 2.1-2.3 all modifying `.claude/skills/agent-browser/SKILL.md`), launching separate sub-agents via `/start-task` causes edit conflicts. The current workaround is executing them inline in the orchestrator, which bypasses the hook automation (SubagentStop, PostToolUse).

The swarm-task-planner agent should detect when multiple tasks share output files (read/write resources) and group them into a single compound task assigned to one agent. The implement-feature orchestrator also needs to understand and dispatch these grouped/compound tasks while preserving hook-based status tracking.

Design decision (user-specified): The planner should design tasks so that tasks sharing read/write resources are grouped and assigned as a unit to a single agent. This is a merge-into-compound-task approach.

---

## Core Intent Analysis

### WHO (Target Users)

1. **swarm-task-planner agent** — produces task plans that currently allow multiple tasks to write the same file without grouping them.
2. **implement-feature orchestrator** — dispatches tasks one-at-a-time via `/start-task` sub-agents; currently has no concept of compound tasks.
3. **start-task skill** — executes a single task within a sub-agent; would need to handle compound tasks (multiple task IDs, multiple acceptance criteria sets).
4. **task_status_hook.py** — tracks status per-task via SubagentStop and PostToolUse; would need to mark multiple task IDs COMPLETE when a compound task finishes.
5. **Feature developers using SAM** — benefit from fewer edit conflicts and more reliable automated task execution.

### WHAT (Desired Outcome)

When a task plan contains multiple tasks that write to the same file(s), those tasks are merged into a single compound task that is dispatched to one agent. The compound task:

- Contains all requirements, acceptance criteria, and verification steps from each constituent task
- Is tracked as a unit by the orchestrator and hooks
- Marks all constituent task IDs as COMPLETE when the compound agent finishes
- Preserves the existing status tracking pipeline (SubagentStop timestamps, PostToolUse activity tracking)

### WHEN (Trigger Conditions)

1. During plan creation (swarm-task-planner): when two or more tasks in the same dependency tier share one or more files in their Expected Outputs sections.
2. During plan validation (plan-validator): when the validator detects the "Two tasks write to same file without dependency" red flag (already documented but not enforced).
3. During execution (implement-feature): when `ready-tasks` returns multiple tasks whose Expected Outputs overlap.

### WHY (Problem Being Solved)

When separate sub-agents edit the same file concurrently or sequentially without coordination:

1. **Edit conflicts**: The second agent's Read-Edit cycle may read stale content if the first agent's writes are not yet visible, or the Edit tool's exact-match replacement may fail because the first agent already changed the surrounding context.
2. **Hook bypass**: The current workaround (running tasks inline in the orchestrator) skips the SubagentStop hook, so tasks are not automatically marked COMPLETE with timestamps.
3. **Wasted context**: Each sub-agent independently reads and loads the same file, paying the context-window cost multiple times for the same content.

Concrete example: `plan/tasks-10-validate-agent-browser.md` Tasks 2.1, 2.2, and 2.3 all modify `.claude/skills/agent-browser/SKILL.md` — Task 2.1 adds an inline comment to line 155, Task 2.2 inserts a Prerequisites section before Core Workflow, and Task 2.3 inserts Error Recovery and Validation Status sections. Three separate agents each read the same 414-line file and make non-overlapping edits, but the sequential execution means each agent's view of the file differs from the previous agent's output.

---

## Codebase Research

### Similar Patterns Found

#### Pattern 1: Parallelization and Conflict Avoidance section (swarm-task-planner)

- **Location**: `plugins/python3-development/agents/swarm-task-planner.md:328-335` and `plugins/development-harness/agents/swarm-task-planner.md:328-335`
- **Relevance**: This section already acknowledges the file conflict problem. It says "Parallel tasks must not collide on the same files unless a merge protocol is specified" and offers two mitigations: (a) split by non-overlapping sections with explicit line/section ownership, or (b) create an integration task that performs the merge at a sync checkpoint. Neither option includes merging the tasks themselves into a compound unit.
- **Reusable**: The `parallelize-with` and `reason` YAML frontmatter fields. The `reason` field already documents "avoid file conflicts" as a concern. A new `compound-group` or similar field could follow the same pattern.

#### Pattern 2: plan-validator "Two tasks write to same file" red flag

- **Location**: `plugins/development-harness/agents/plan-validator.md:174`
- **Relevance**: The plan-validator already identifies this exact problem as a red flag: "Two tasks write to same file without dependency." However, it only flags it — it does not suggest or enforce grouping. This validation check is the natural place to also recommend merging into a compound task.
- **Reusable**: The Expected Outputs cross-check logic in Dimension 5 (Resource Availability). The file path extraction from Expected Outputs sections could be reused for overlap detection.

#### Pattern 3: get_ready_tasks() in implementation_manager.py

- **Location**: `plugins/python3-development/skills/implementation-manager/scripts/implementation_manager.py:905-934`
- **Relevance**: This function determines which tasks are ready to execute. It checks only two conditions: (1) status is NOT_STARTED, (2) all dependencies are COMPLETE. There is no file-overlap check. This is where file-overlap grouping would need to be enforced at execution time if the planner fails to group tasks at planning time.
- **Reusable**: The `status_by_id` lookup pattern. A similar `outputs_by_id` lookup could be built during parsing.

#### Pattern 4: Task dataclass and YAML frontmatter schema

- **Location**: `plugins/python3-development/skills/implementation-manager/scripts/implementation_manager.py:89-131` (Task dataclass) and `.claude/docs/TASK_FILE_FORMAT.md:127-159` (field definitions)
- **Relevance**: The Task dataclass has no field for grouping, compound membership, or output file paths. The YAML frontmatter schema defines `parallelize-with` but not a `compound-group` or `output-files` field. Adding a grouping mechanism requires schema extension.
- **Reusable**: The existing `parallelize-with` field and the optional fields pattern in the schema.

#### Pattern 5: task_status_hook.py SubagentStop handler

- **Location**: `plugins/python3-development/skills/implementation-manager/scripts/task_status_hook.py:444-491`
- **Relevance**: The SubagentStop handler parses the sub-agent prompt for a single `/start-task` invocation and extracts one task file path and one task ID. It then marks that single task COMPLETE. For compound tasks, this handler would need to mark multiple task IDs COMPLETE from a single sub-agent stop event.
- **Reusable**: The prompt-parsing approach. A compound invocation could use `--task T1,T2,T3` syntax, and the parser regex could be extended.

#### Pattern 6: active-task context file (single task ID)

- **Location**: `plugins/python3-development/skills/implementation-manager/scripts/task_status_hook.py:121-174`
- **Relevance**: The active-task context file stores `{"task_file_path": "...", "task_id": "..."}` — a single task ID. For compound tasks, this would need to store multiple task IDs so the PostToolUse hook can update LastActivity for all constituent tasks.
- **Reusable**: The JSON context file mechanism. The schema could be extended to `{"task_file_path": "...", "task_ids": ["T1", "T2", "T3"]}`.

### Existing Infrastructure

1. **Expected Outputs section** in task body (standardized in CLEAR format) — already documents which files each task modifies. This is the data source for overlap detection.
2. **YAML frontmatter schema** (`TASK_FILE_FORMAT.md`) — extensible with new optional fields without breaking existing parsers (spec says: "All parsers MUST ignore unknown fields to maintain forward compatibility").
3. **plan-validator agent** — already has a cross-task Expected Outputs consistency check (Dimension 5), which could be extended to trigger grouping recommendations.
4. **clear-cove-task-design skill** — already says "avoid shared file conflicts across parallel tasks (or define merge protocol)" at line 213 of SKILL.md.

### Code References

- `plugins/python3-development/agents/swarm-task-planner.md:328-335` — Parallelization and Conflict Avoidance section
- `plugins/development-harness/agents/swarm-task-planner.md:328-335` — Same section in development-harness copy
- `plugins/development-harness/agents/plan-validator.md:169-175` — Dimension 5 file conflict red flag
- `plugins/python3-development/skills/implementation-manager/scripts/implementation_manager.py:905-934` — get_ready_tasks() with no file overlap check
- `plugins/python3-development/skills/implementation-manager/scripts/implementation_manager.py:89-131` — Task dataclass (no grouping fields)
- `plugins/python3-development/skills/implementation-manager/scripts/task_status_hook.py:444-491` — SubagentStop handler (single task ID)
- `plugins/python3-development/skills/implementation-manager/scripts/task_status_hook.py:121-174` — active-task context file (single task ID)
- `.claude/docs/TASK_FILE_FORMAT.md:127-159` — YAML frontmatter field definitions
- `.claude/skills/implement-feature/SKILL.md:58-66` — dispatch loop ("For each ready task... Route to the agent named in the task's Agent field")
- `.claude/skills/start-task/SKILL.md:69-88` — single-task execution flow
- `plan/tasks-10-validate-agent-browser.md:329-666` — concrete example of three tasks (2.1, 2.2, 2.3) all writing to the same SKILL.md
- `plugins/python3-development/skills/clear-cove-task-design/SKILL.md:213` — "avoid shared file conflicts across parallel tasks"
- `plugins/python3-development/skills/generate-task/SKILL.md:46-47` — parallelize-with and reason fields in template

---

## Use Scenarios

### Scenario 1: Planner detects same-file tasks during plan creation

**Actor**: swarm-task-planner agent
**Trigger**: Architecture spec calls for multiple changes to the same file (e.g., add section A, add section B, annotate line C in SKILL.md)
**Goal**: Produce a plan where all changes to the same file are grouped into a single compound task
**Expected Outcome**: Instead of three separate tasks with the same Expected Output file path, the planner produces one compound task containing three requirement sets (with individual acceptance criteria preserved), assigned to one agent

### Scenario 2: Orchestrator dispatches a compound task

**Actor**: implement-feature orchestrator
**Trigger**: `ready-tasks` returns a compound task (one task that represents multiple merged tasks)
**Goal**: Dispatch the compound task to a single sub-agent via `/start-task` while maintaining hook-based tracking for all constituent task IDs
**Expected Outcome**: One sub-agent runs, implements all requirements, SubagentStop hook fires once and marks all constituent task IDs COMPLETE with timestamps

### Scenario 3: Validator catches ungrouped same-file tasks

**Actor**: plan-validator agent
**Trigger**: Validation of a task plan where multiple tasks write to the same file but are not in a compound group and have no dependency chain
**Goal**: Flag the overlap as an error (not just a warning) and recommend grouping
**Expected Outcome**: Validation fails with actionable message: "Tasks T2.1, T2.2, T2.3 all write to `.claude/skills/agent-browser/SKILL.md` — merge into a compound task or add sequential dependencies"

### Scenario 4: Existing plan with sequential dependencies (no change needed)

**Actor**: swarm-task-planner agent
**Trigger**: Tasks that write to the same file are already chained by dependencies (T2.1 depends on T2.2)
**Goal**: Recognize that sequential dependency already prevents concurrent editing
**Expected Outcome**: No grouping applied — the dependency chain already serializes execution. The planner notes this is valid but suboptimal (multiple agent launches for same file)

---

## Gap Analysis

### Identified Gaps

| # | Category | Gap Description | Impact |
|---|----------|-----------------|--------|
| 1 | Scope | No definition of "compound task" in TASK_FILE_FORMAT.md or anywhere in the SAM documentation | Downstream agents (start-task, hooks, orchestrator) have no schema to follow |
| 2 | Scope | Unclear whether compound tasks should be created at planning time only, or also at execution time as a runtime grouping | Determines whether changes go in swarm-task-planner only, or also in implementation_manager.py |
| 3 | Behavior | task_status_hook.py SubagentStop handler assumes one task ID per sub-agent stop event | Compound tasks with multiple IDs would not be fully marked COMPLETE |
| 4 | Behavior | active-task context file stores a single task_id string | PostToolUse hook cannot update LastActivity for all constituent tasks in a compound group |
| 5 | Integration | implement-feature dispatch loop calls start-task with `--task {task_id}` (singular) | No mechanism to pass multiple task IDs to a single sub-agent |
| 6 | Integration | start-task SKILL.md parses `--task <id>` expecting a single alphanumeric ID | No syntax for compound task IDs (e.g., `--task T2.1,T2.2,T2.3`) |
| 7 | Behavior | get_ready_tasks() returns individual Task objects with no grouping awareness | Even if the planner creates compound tasks, the readiness logic would need to understand group membership |
| 8 | Scope | The swarm-task-planner Parallelization and Conflict Avoidance section offers two mitigations (section-splitting and integration tasks) but not a merge-into-compound option | The user-specified design decision (merge approach) is not represented in the current guidance |
| 9 | Integration | The plan-validator flags "Two tasks write to same file without dependency" but only as a warning, not an actionable recommendation | The validation does not suggest the compound task solution or fail the plan |
| 10 | Scope | Both swarm-task-planner copies (python3-development and development-harness) need the same update | Changes must be synchronized across both agent definition files |

---

## Questions Requiring Resolution

### Q1: Compound task representation in the task file

- **Category**: Scope
- **Gap**: No schema for compound tasks exists in TASK_FILE_FORMAT.md (Gap #1)
- **Question**: Should a compound task be represented as a single YAML frontmatter task with a new `compound-tasks` array field listing the merged task IDs, or should the individual task files remain separate with a `compound-group` field linking them?
- **Options**:
  - A) Single compound task file: one task ID (e.g., `T2-compound`), body contains merged requirements from T2.1/T2.2/T2.3, new `subtasks: [T2.1, T2.2, T2.3]` field in frontmatter
  - B) Individual task files with grouping: each task keeps its own file/section but adds `compound-group: CG1` to frontmatter; orchestrator dispatches the group as a unit
  - C) Planner merges at writing time: no new schema field; planner simply writes one task with all requirements combined; original sub-task IDs do not exist in the plan
- **Why It Matters**: Option A requires schema extension and changes to parsing/hooks. Option B requires less schema change but more orchestrator logic. Option C is simplest but loses individual task traceability.
- **Resolution**: _pending_

### Q2: Runtime grouping vs. planning-time-only grouping

- **Category**: Scope
- **Gap**: Unclear boundary between planner responsibility and orchestrator responsibility (Gap #2)
- **Question**: Should the implementation_manager.py also detect and group same-file tasks at runtime (for plans that were not created with grouping), or should grouping be enforced only at planning time?
- **Options**:
  - A) Planning-time only: swarm-task-planner merges tasks; implementation_manager.py and start-task remain unchanged (simpler, but old plans still have the problem)
  - B) Both: planner merges at planning time, implementation_manager.py also detects overlap at runtime and groups ready tasks before dispatch (handles legacy plans, but more complex)
- **Why It Matters**: Option A is simpler but does not help with existing task files. Option B covers legacy plans but requires changes to implementation_manager.py (Expected Outputs parsing from markdown body).
- **Resolution**: _pending_

### Q3: Hook handling for compound task completion

- **Category**: Behavior
- **Gap**: task_status_hook.py assumes one task ID per SubagentStop event (Gap #3)
- **Question**: When a compound task's sub-agent finishes, how should the SubagentStop hook know which task IDs to mark COMPLETE?
- **Options**:
  - A) Extend start-task argument syntax: `--task T2.1,T2.2,T2.3` — hook parses comma-separated IDs from the prompt
  - B) Use the active-task context file: extend JSON to `{"task_ids": ["T2.1", "T2.2", "T2.3"]}` — SubagentStop reads context file instead of parsing prompt
  - C) Compound task has a single ID; hook marks that ID COMPLETE; orchestrator separately marks constituent IDs COMPLETE after hook fires
- **Why It Matters**: The current prompt-parsing approach (Option A) requires regex changes. The context-file approach (Option B) requires the SubagentStop handler to read context files (currently only PostToolUse does). Option C keeps hook simple but adds orchestrator complexity.
- **Resolution**: _pending_

### Q4: Acceptance criteria and verification for compound tasks

- **Category**: Behavior
- **Gap**: Not explicit how merged acceptance criteria should be structured
- **Question**: When three tasks are merged into one compound task, should the acceptance criteria be a flat list, or should they be organized by original task ID for traceability?
- **Options**:
  - A) Flat list: merge all acceptance criteria into one numbered list
  - B) Grouped by origin: use subsections (`### From Task 2.1`, `### From Task 2.2`) to preserve traceability
- **Why It Matters**: Option A is simpler for the executing agent. Option B preserves the ability to trace which original requirement each criterion came from, which is valuable for debugging and follow-up task creation.
- **Resolution**: _pending_

### Q5: Synchronization between python3-development and development-harness agent copies

- **Category**: Integration
- **Gap**: Both plugins have swarm-task-planner agent files that need the same update (Gap #10)
- **Question**: Should changes be made to both files independently, or should one be designated as the source and the other derived?
- **Why It Matters**: The two files are nearly identical but have minor divergences (e.g., `agent:` vs `role:` field naming in the Task Structure Requirements section). Updating both independently risks further divergence.
- **Resolution**: _pending_

---

## Goals (Pending Resolution)

_These goals will be finalized after questions are resolved._

1. Extend swarm-task-planner to detect when multiple tasks in the same dependency tier write to the same file(s) and merge them into a compound task
2. Define the compound task schema (YAML frontmatter field(s)) in TASK_FILE_FORMAT.md
3. Update implement-feature dispatch logic to handle compound tasks
4. Update start-task argument parsing for compound task IDs
5. Extend task_status_hook.py to mark all constituent task IDs COMPLETE on SubagentStop
6. Extend active-task context file schema for multiple task IDs
7. Update plan-validator to recommend compound grouping when same-file overlap is detected
8. Update clear-cove-task-design and generate-task skills to document compound task patterns
9. Synchronize changes across both python3-development and development-harness plugin copies

---

## Next Steps

After questions are resolved:

1. Update "Resolution" fields in Questions section
2. Finalize Goals section
3. Proceed to RT-ICA assessment
4. Then proceed to architecture design
