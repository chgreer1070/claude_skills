# SAM Task Enforcement Patterns

**Analysis Date:** 2026-03-22
**Context:** Issue #990 — Enforce complete-implementation quality gate phases with SAM tasks and hook checkpoints
**Scope:** Document existing SAM task enforcement patterns from implement-feature to enable reuse in complete-implementation

---

## Summary

The `implement-feature` skill demonstrates a complete SAM-based task enforcement pattern combining:
- **MCP tool coordination** (sam_ready, sam_claim, sam_state) for explicit state transitions
- **Hook-based automation** (SubagentStop, PostToolUse) for timestamp recording and async completion
- **Readiness-gated loops** ensuring tasks cannot be skipped or dispatched twice
- **Checkpoint files** for pre-implementation baseline and post-implementation verification

The `complete-implementation` skill currently lacks this enforcement, using only prose instructions for its 6 quality gate phases.

---

## Pattern 1: SAM Task Loop with Readiness Gating

**Location:** `plugins/development-harness/skills/implement-feature/SKILL.md:39-108`

**Pattern:** Query ready tasks, delegate each to its agent, rely on hooks to mark completion, repeat until complete.

```text
Loop:
  1. Query status: mcp__plugin_dh_sam__sam_status(plan="P{N}")
  2. Query ready tasks: mcp__plugin_dh_sam__sam_ready(plan="P{N}")
     - Returns {"ready_tasks": [...], "count": N}
     - A task is ready when:
       * Status is NOT_STARTED
       * All dependency tasks have status COMPLETE
  3. For each ready task:
     - Route to agent named in task.agent field
     - Pass task.skills list for task-level skill loading
     - Launch via: Skill(skill="start-task", args="{task_file_path} --task {task_id}")
  4. After SubagentStop hook fires: task marked COMPLETE
  5. Repeat until no tasks remain ready
```

**Key Constraints:**

- Only ready tasks surface from sam_ready → guarantees dependency ordering
- No agent can start a task that is already claimed or complete
- Bookend tasks (T0, TN) have automatic ordering: T0 has priority 1 + no dependencies (first); TN has dependencies on all impl tasks (last)
- Single ready task = single Agent call; 2+ ready tasks = TeamCreate for parallel dispatch

**Backward Compatibility:**

- skills field is optional; agents work without it
- Concern block accumulation: agents output `<concerns>`, loop appends each to backlog item via backlog_groom

---

## Pattern 2: Task Claiming with sam_claim (Exclusive Lock)

**Location:** `plugins/development-harness/skills/start-task/SKILL.md:89-108`

**Pattern:** Agent must call sam_claim before starting work. This is the ONLY permitted way to mark a task IN_PROGRESS.

```text
Step 1: Call mcp__plugin_dh_sam__sam_claim(plan="P{N}", task="T{M}")

Step 2: Check response:
  - If "claimed": true
    * Status is now IN_PROGRESS
    * Started timestamp is written to disk
    * Proceed with implementation

  - If "claimed": false
    * Task was already claimed by another agent
    * OR task is already complete
    * OR task was not found
    * Output: full JSON result for orchestrator
    * STOP: do not proceed
    * Orchestrator's hook detects the stop; task state is unchanged
```

**Why Exclusive Lock:**

- Prevents duplicate dispatch when multiple agents are ready simultaneously
- Critical in parallel dispatch scenarios (TeamCreate with 2+ ready tasks)
- sam_claim writes IN_PROGRESS + Started timestamp atomically

**Constraint Enforcement:**

- Do NOT edit status or started fields directly with Edit tool
- sam_claim is the ONLY permitted transition to IN_PROGRESS
- Any direct edit bypass would break the enforcement model

---

## Pattern 3: Hook-Driven Status Updates and Timestamps

**Location:** `plugins/development-harness/skills/start-task/SKILL.md:6-11` + `plugins/development-harness/skills/implementation-manager/scripts/task_status_hook.py`

**Pattern:** Two hooks coordinate task lifecycle without agent code.

### Hook 1: PostToolUse (Write|Edit|Bash)

Fires every time an agent writes, edits, or runs bash during task execution.

```text
Trigger: Any Write, Edit, or Bash tool call
Action: Update LastActivity timestamp

Mechanism:
  1. Read .claude/context/active-task-{CLAUDE_SESSION_ID}.json
  2. Extract task_file_path, task_id
  3. Call sam_update_status(..., last_activity=now)
  4. Exit 0 (success)

Environment Control:
  CLAUDE_SKILLS_HOOK_PROFILE=minimal → skips PostToolUse
  CLAUDE_SKILLS_HOOK_PROFILE=standard → runs PostToolUse (default)
  CLAUDE_SKILLS_HOOK_PROFILE=strict → runs PostToolUse + pre-completion validation

  CLAUDE_SKILLS_DISABLED_HOOKS="task-status:post-tool-use" → disables entirely
```

### Hook 2: SubagentStop

Fires when a sub-agent finishes (either normally or via BLOCKED).

```text
Trigger: Sub-agent execution complete
Action: Mark task COMPLETE, add Completed timestamp, sync to GitHub

Mechanism:
  1. Parse prompt for /start-task invocation
  2. Extract task_file_path, task_id, parent_issue_number
  3. Call sam_update_status(..., status="complete", completed=now)
  4. Call backlog_core.github.update_task_status(repo, github_issue, "complete") (non-fatal)
  5. Delete .claude/context/active-task-{session_id}.json
  6. Exit 0

Profile Control:
  CLAUDE_SKILLS_HOOK_PROFILE=strict → runs pre-completion validation warnings (observational)
```

**Context File Mechanism:**

The `/start-task` skill writes this file after claiming a task:

```json
{
  "task_file_path": "plan/tasks-3-integrate-sam-schema.md",
  "task_id": "T1.1",
  "parent_issue_number": 975
}
```

PostToolUse hooks read this to know which task is active. SubagentStop parses the prompt directly.

**Timestamp Responsibilities:**

| Field | Written By | When |
|-------|-----------|------|
| `started` | sam_claim (in /start-task) | When task claimed |
| `completed` | SubagentStop hook | When agent finishes |
| `last_activity` | PostToolUse hook | On each Write/Edit/Bash during task execution |

---

## Pattern 4: Task Model with Dependency Graph

**Location:** `plugins/development-harness/sam_schema/core/models.py:107-210`

**Pattern:** Task is a Pydantic model with status lifecycle and dependency resolution.

### Task Status Lifecycle

```python
TaskStatus = "not-started" | "in-progress" | "complete" | "blocked" | "deferred" | "skipped" | "wont-fix"
```

Transitions:

```text
NOT_STARTED ──[sam_claim]──> IN_PROGRESS ──[SubagentStop]──> COMPLETE
                                   ↓
                            (agent stops early)
                                   ↓
                              BLOCKED
```

### Dependency Resolution

```python
Task.dependencies: list[str]  # e.g., ["T1", "T1.1", "T2"]

Readiness Logic (in sam_ready):
  A task is ready when:
    - status == NOT_STARTED
    - AND all tasks in dependencies have status == COMPLETE
```

### Priority and Complexity

```python
Task.priority: Priority        # IntEnum: CRITICAL(1), HIGH(2), MEDIUM(3), LOW(4), LOWEST(5)
Task.complexity: Complexity    # StrEnum: LOW | MEDIUM | HIGH
```

Priority determines ready-task order when multiple tasks are ready simultaneously.

### Task-Level Skills

```python
Task.skills: list[str]         # e.g., ["fastmcp-creator:fastmcp", "python3-development:pytest"]
```

When present, `/implement-feature` passes these to the agent in the delegation prompt. Agent loads each skill before starting work. Skill-loading is additive (can load same skill twice = no-op).

### Bookend Metadata

```python
Task.is_bookend: bool
Task.bookend_type: BookendType  # "t0-baseline" | "tn-verification"
```

T0 and TN are special tasks:
- **T0** runs before any implementation task (priority 1, no dependencies)
- **TN** runs after all implementation tasks (priority 5, depends on all non-bookend tasks)

---

## Pattern 5: Bookend Verification (T0/TN Baseline Comparison)

**Location:** `plugins/development-harness/skills/implement-feature/SKILL.md:118-145` + `plugins/development-harness/skills/complete-implementation/SKILL.md:33-71`

**Pattern:** Capture pre-implementation state (T0), post-implementation state (TN), compare to detect regressions.

### T0: Baseline Capture

Agent: `@dh:t0-baseline-capture`

```text
Task ID: T0
Priority: 1
Dependencies: []  (always first)
Agent: t0-baseline-capture
Body:
  - Read feature goal from plan.goal
  - Read acceptance-criteria-structured from plan.acceptance_criteria_structured
  - For each criterion:
    - Extract check_command (shell command)
    - Run the command, capture exit code + stdout
  - Write plan/T0-baseline-{slug}.yaml:
    {
      "baseline_captured": "{ISO timestamp}",
      "criteria": [
        {
          "criterion_id": "AC-1",
          "check_command": "pytest -xvs ...",
          "t0_exit_code": 0,
          "t0_stdout": "...",
          "t0_stderr": ""
        }
      ]
    }
```

### TN: Verification Gate

Agent: `@dh:tn-verification-gate`

```text
Task ID: TN (or T{max+1})
Priority: 5
Dependencies: [all non-bookend task IDs]  (always last)
Agent: tn-verification-gate
Body:
  - Read plan/T0-baseline-{slug}.yaml
  - For each criterion:
    - Re-run the check_command
    - Capture exit code + stdout
    - Compare to T0 baseline
    - Classify:
      * T0 pass + TN pass   = "passed"
      * T0 pass + TN fail   = "regressed" (BLOCKS completion)
      * T0 fail + TN fail   = "pre-existing-fail"
      * T0 fail + TN pass   = "newly-passing"
  - Write plan/TN-verification-{slug}.yaml:
    {
      "verification_run": "{ISO timestamp}",
      "criteria": [
        {
          "criterion_id": "AC-1",
          "check_command": "pytest -xvs ...",
          "t0_exit_code": 0,
          "tn_exit_code": 0,
          "status": "passed",
          "stdout_diff_summary": "..."
        }
      ]
    }
  - IMPORTANT: No top-level "verdict" field
    - Verdict is aggregated by scanning records: FAIL if any status=="regressed"
```

### Integration in complete-implementation

**Pre-Phase 1 Check:**

```text
Read plan/TN-verification-{slug}.yaml
Scan all per-criterion records for status: regressed
If any regressed:
  - STOP: completion blocked
  - Report: each regressed criterion with check_command, T0 output, TN output
  - Instruct: fix regressions before re-running
If none:
  - Proceed to Phase 1
```

---

## Pattern 6: Parallel Dispatch with TeamCreate

**Location:** `plugins/development-harness/skills/implement-feature/SKILL.md:63-93`

**Pattern:** When 2+ tasks are simultaneously ready, dispatch in parallel using TeamCreate.

```text
When sam_ready returns count >= 2:
  1. Create team: TeamCreate(team_name="impl-{slug}")
  2. Spawn one teammate per ready task
  3. Each teammate:
     - Loads task-level skills (if task.skills non-empty)
     - Calls Skill(skill="start-task", args="{file} --task {id}")
     - Returns STATUS: DONE or STATUS: BLOCKED
  4. After all teammates complete:
     - Reassess ready tasks
     - Repeat the loop

When sam_ready returns count == 1:
  - Single Agent call is acceptable
  - No TeamCreate needed
```

**Parallel Safety:**

- Each task calls sam_claim independently
- Only one agent can successfully claim each task
- If agent A claims task T1 before agent B, agent B's sam_claim(T1) returns "claimed": false
- Agent B sees the conflict and stops (hook detects stop, task remains in prior state)

---

## Pattern 7: Concern Accumulation and Backlog Integration

**Location:** `plugins/development-harness/skills/implement-feature/SKILL.md:95-106`

**Pattern:** Agents emit concerns, orchestrator accumulates them, quality gates verify them.

### During Task Execution

Each agent MAY output a `<concerns>` block:

```xml
<concerns>
- Detected unused variable in auth.py:45 — should be removed or documented
- Test coverage for error paths is missing in service/integration_test.py
- Configuration validation could be stricter in handlers.py
</concerns>
```

### Orchestrator Accumulation Loop

After each agent returns (Phase 1-6):

```text
1. Parse output for <concerns> block
2. For each concern:
   a. Call mcp__plugin_dh_backlog__backlog_groom(
        selector="#{issue}",
        section="Concerns",
        content="- [ ] {concern text} (reported by {agent_name} on {task_id})",
        append=True
      )
3. Concerns accumulate as unchecked items
```

### Quality Gate Processing

In `complete-implementation` Pre-Phase 1b:

```text
1. Query: mcp__plugin_dh_backlog__backlog_view(selector="#{issue}")
2. If Concerns section exists with unchecked items:
   - For each item:
     * Verify: is it a real issue?
     * If YES: check it off, create new backlog item
     * If NO: check it off with reason "Not confirmed — {reason}"
3. Update concerns section via backlog_groom
```

---

## Pattern 8: Quality Gate Agent Dispatch Structure

**Location:** `plugins/development-harness/skills/complete-implementation/SKILL.md:109-195`

**Pattern:** Six sequential phases, each dispatching a specialized agent with TaskAssignment JSON.

### Phase Structure

```text
Phase 1: Code Review (agent from language manifest or fallback)
  Input: TaskAssignment JSON from sam_status(plan="P{N}")
  Output: Task files (follow-up), code findings, concerns

Phase 2: Feature Verification (@dh:feature-verifier)
  Input: TaskAssignment JSON from sam_read(plan="P{N}", task="T{M}")
  Checks: Feature meets acceptance criteria (goal-backward)

Phase 3: Integration Check (@dh:integration-checker)
  Input: TaskAssignment JSON from sam_read(plan="P{N}", task="T{M}")
  Checks: No integration regressions

Phase 4: Documentation Drift Audit (@dh:doc-drift-auditor)
  Input: TaskAssignment JSON from sam_read(plan="P{N}", task="T{M}")
  Checks: Docs match implementation (read-only)

Phase 5: Documentation Update (@dh:service-docs-maintainer)
  Input: TaskAssignment JSON from sam_read(plan="P{N}", task="T{M}")
  Writes: Updated docs if drift found

Phase 6: Context Refinement (@dh:context-refinement)
  Input: TaskAssignment JSON from sam_read(plan="P{N}", task="T{M}")
  Writes: Updated Context Manifest
  Checks: Plan artifacts are fresh (design-refinement vs intent-divergence)
  Outputs: DIVERGENCE_REQUIRING_REVIEW block if found
```

### Current Enforcement Gap

- Phases 1-6 are launched sequentially via prose instructions
- No SAM state transitions between phases
- No mechanical check that all phases completed
- Agent can skip phases (e.g., skip Phase 2-5, jump to Phase 6)
- No barrier prevents applying `status:verified` label if phases were skipped

---

## Pattern 9: Artifact Manifest Discovery (Worktree Safety)

**Location:** `plugins/development-harness/skills/start-task/SKILL.md:58-75` + `plugins/development-harness/skills/complete-implementation/SKILL.md:75-85`

**Pattern:** Agents in isolated worktrees use artifact manifest MCP instead of filesystem paths.

### Discovery Flow

```text
1. Query artifact manifest: mcp__plugin_dh_backlog__artifact_list(issue_number=N)
2. Response:
   {
     "artifacts": [
       {
         "type": "architect",
         "path": "plan/architect-data-validation.md",
         "status": "ready",
         "agent": "python-cli-design-spec"
       },
       {
         "type": "feature-context",
         "path": "plan/feature-context-data-validation.md",
         "status": "ready",
         "agent": "feature-researcher"
       }
     ]
   }

3. Read artifacts via MCP: mcp__plugin_dh_backlog__artifact_read(issue_number=N, artifact_type="architect")
4. Fallback: If artifact_list empty/error, use filesystem conventions (plan/architect-{slug}.md)
```

### Why Manifest?

- Root worktree plan files are not visible in isolated worktrees
- Artifact manifest is the bridge: stored in GitHub Issue body, queryable via MCP
- Allows multi-worktree teams to access shared plan artifacts

---

## Implementation Constraints for #990

These patterns must be respected when adding SAM enforcement to `complete-implementation`:

1. **sam_claim is atomic** — use it before each phase, don't edit status directly
2. **Dependencies must chain phases** — Phase 1 → Phase 2 → Phase 3 → Phase 4 → Phase 5 → Phase 6
3. **Hook events are async** — SubagentStop fires after agent returns, don't assume immediate completion
4. **sam_ready respects dependencies** — only ready phases surface, enforces order
5. **Bookend tasks are optional** — quality-gate phases work without T0/TN (no acceptance-criteria-structured)
6. **Parallel dispatch is safe** — TeamCreate + sam_claim ensure no duplicate work
7. **Context files are ephemeral** — deleted by SubagentStop, per-session basis
8. **Artifact manifest is optional** — fallback to filesystem if not present (backward compat)

---

## Files Involved in This Pattern

**Core SAM Execution:**
- `plugins/development-harness/skills/implement-feature/SKILL.md` — reference loop pattern
- `plugins/development-harness/skills/start-task/SKILL.md` — task claiming logic
- `plugins/development-harness/skills/implementation-manager/scripts/task_status_hook.py` — hook automation
- `plugins/development-harness/sam_schema/core/models.py` — Task model definition
- `plugins/development-harness/sam_schema/core/query.py` — sam_claim, sam_state, sam_ready, sam_read operations
- `plugins/development-harness/sam_schema/server.py` — MCP server exposing sam_* tools

**Quality Gates (Target for Enforcement):**
- `plugins/development-harness/skills/complete-implementation/SKILL.md` — current prose-only phases
- `plugins/development-harness/agents/code-reviewer.md` — Phase 1 agent
- `plugins/development-harness/agents/feature-verifier.md` — Phase 2 agent
- `plugins/development-harness/agents/integration-checker.md` — Phase 3 agent
- `plugins/development-harness/agents/doc-drift-auditor.md` — Phase 4 agent
- `plugins/development-harness/agents/service-docs-maintainer.md` — Phase 5 agent
- `plugins/development-harness/agents/context-refinement.md` — Phase 6 agent

**Documentation:**
- `.claude/rules/local-workflow.md` — Phase 2 (Execution) section documents implement-feature pattern; Phase 3 (Quality Gates) describes current prose-only approach
- `plugins/development-harness/docs/workflow-architecture-diagram.md` — data flow; will need phase task creation added
- `plugins/development-harness/dispatch_schema/gates.py` — GateResult, CommandResult models (not directly related but similar checkpoint concept)

---

## Key Insights for Architect

1. **sam_ready is the enforcement mechanism** — it prevents tasks from surfacing until prerequisites complete. This is the core constraint that makes the pattern work.

2. **Hooks are fire-and-forget** — SubagentStop doesn't wait; it marks complete and moves on. Context files are the coordination mechanism between hooks.

3. **Artifact manifest enables multi-worktree safety** — quality gate agents in isolated worktrees need artifact_read instead of filesystem access.

4. **Task-level skills are optional but additive** — backward compatible; agents work without them.

5. **Bookend tasks are automatic** — T0 sorts first (priority 1, no deps); TN sorts last (deps on all others). No special orchestration needed.

6. **Parallel safety is built in** — sam_claim prevents duplicate dispatch; agents that lose the race just stop.

7. **Concern accumulation is a pattern, not a gate** — concerns are collected and verified by quality gates, but don't block task completion.
