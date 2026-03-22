# Feature Context: Dispatch Orchestration MCP Tools

## Document Metadata

- **Generated**: 2026-03-22
- **Input Type**: existing_document
- **Source**: Backlog item #986 -- "Add dispatch orchestration MCP tools with background task support to backlog server"
- **Status**: DISCOVERY_COMPLETE

---

## Original Request

The kage-bunshin `spawn.py` script handles per-item process launching (worktree creation, `.venv` symlinking, lock file, `claude -p` spawn). What is missing is the orchestration layer that reads a dispatch plan, iterates waves, spawns kage-bunshins, tracks state, and collects results. This orchestration belongs in the backlog MCP server -- not a standalone script. The backlog MCP server already has four dispatch DATA tools (`dispatch_read`, `dispatch_validate`, `dispatch_stale_check`, `dispatch_conflicts`). The missing piece is dispatch EXECUTION and STATE tools. Four new tools are requested: `dispatch_wave_start`, `dispatch_item_status`, `dispatch_wave_status`, `dispatch_spawn`.

---

## Core Intent Analysis

### WHO (Target Users)

Two primary consumers:

1. **The orchestrator agent** running `/dh:dispatch`, `/dh:work-milestone`, or `/dh:groom-milestone` -- this agent needs to start a wave, spawn kage-bunshins, and track completion without managing PIDs and shell scripts directly.
2. **Any MCP client** (monitoring agent, human with MCP inspector, another orchestrator session) that wants to query dispatch progress -- wave status, item completion, elapsed time.

### WHAT (Desired Outcome)

An MCP-native interface for dispatch orchestration that:

- Starts a dispatch wave and records which items are in-progress with their PIDs
- Tracks item completion/failure as kage-bunshin sessions finish
- Allows any MCP client to query wave and item status at any time
- Runs the full spawn-and-monitor loop as a background task with progress reporting via the FastMCP task protocol
- Persists state to SQLite at `~/.dh/projects/{project-stub}/dispatch-state.db` so it survives MCP server restarts and is visible across worktrees

Success looks like: an orchestrator calls `dispatch_spawn(milestone=5, wave_num=1, phase="work")` and receives a task ID. It (or any other client) can poll `dispatch_wave_status(milestone=5, wave_num=1)` to see real-time progress. When all items complete, the background task returns a structured summary.

### WHEN (Trigger Conditions)

- A milestone has been groomed and a dispatch plan exists at `plan/milestone-{N}-dispatch.yaml`
- The user invokes `/dh:dispatch` or `/dh:work-milestone` to execute a wave
- An orchestrator needs to groom multiple backlog items in parallel (groom phase, no worktree)
- A monitoring agent or human wants to check on an active dispatch

### WHY (Problem Being Solved)

**Current state**: Dispatching kage-bunshins requires shell scripting -- bash loops, PID arrays, `wait` calls, manual result file parsing. This is documented in the kage-bunshin SKILL.md "Milestone Dispatch Pattern" section but is fragile, not queryable by other agents, and loses state on orchestrator crash.

**Pain points**:

1. **No shared state** -- spawned PIDs and completion status exist only in the orchestrator's bash variables. If the orchestrator session dies, all tracking is lost. Other agents cannot monitor progress.
2. **No concurrency throttle** -- a 10-item wave spawns 10 sessions simultaneously. Each context load costs ~$0.13+ (observed with haiku). No mechanism to limit concurrent sessions to 3-5.
3. **No MCP-native interface** -- the dispatch DATA tools (read, validate, stale_check, conflicts) are MCP tools, but the EXECUTION layer is bash scripts. This forces orchestrators to context-switch between MCP calls and shell execution.
4. **No progress reporting** -- clients cannot observe wave progress without parsing shell output. FastMCP's task protocol provides structured progress updates (total, increment, message) that any MCP client can consume.

---

## Codebase Research

### Similar Patterns Found

#### Pattern 1: Existing Dispatch DATA Tools

- **Location**: `plugins/development-harness/backlog_core/server.py:1295-1409`
- **Relevance**: The four new tools will be co-located with these existing dispatch tools. They follow the same patterns: `@mcp.tool` decorator, async functions, dict return type with error handling, `_dispatch_plan_path()` helper for resolving plan file locations.
- **Reusable**: The `_dispatch_plan_path()` helper (server.py:1289-1291), the `dispatch_read` tool's plan loading logic, and the error-return-dict pattern used across all four tools.

#### Pattern 2: Kage-Bunshin spawn.py Process Launcher

- **Location**: `plugins/development-harness/skills/kage-bunshin/scripts/spawn.py`
- **Relevance**: `dispatch_spawn` will call this script to launch individual kage-bunshin sessions. spawn.py handles worktree creation, symlinks, lock files, and `claude -p` invocation. It returns a JSON record with `pid`, `name`, `worktree`, `result_file`, `error_file`, `model`, `lock_file`.
- **Reusable**: The entire script is reused as-is -- `dispatch_spawn` invokes it as a subprocess per wave item.

#### Pattern 3: Dispatch Schema Models

- **Location**: `plugins/development-harness/dispatch_schema/core/models.py`
- **Relevance**: Defines `DispatchPlan`, `Wave`, `WaveItem`, `ItemStatus` (pending/in-progress/complete/failed/skipped), `ItemPriority`. The new tools operate on these models -- `dispatch_wave_start` reads waves from a `DispatchPlan`, `dispatch_item_status` writes `ItemStatus` transitions.
- **Reusable**: `ItemStatus` enum already defines the exact status values the new tools need. `WaveItem.issue` provides the issue number used as the item identifier.

#### Pattern 4: Quality Gate Executor

- **Location**: `plugins/development-harness/dispatch_schema/gates.py`
- **Relevance**: Shows the pattern for subprocess execution with structured result capture (`CommandResult`, `GateResult`). The `dispatch_spawn` background task will need similar structured result collection per spawned process.
- **Reusable**: The `CommandResult` model pattern (command, exit_code, stdout, stderr, passed computed field) could inform the per-item result structure.

### Existing Infrastructure

- **Dispatch plan path resolution**: `dispatch_schema/paths.py` provides `dispatch_plan_path(milestone_number, project_root)` returning `plan/milestone-{N}-dispatch.yaml`
- **Plan reading and validation**: `dispatch_schema/readers/yaml_reader.py` and `dispatch_schema/core/validator.py`
- **FastMCP server instance**: The backlog MCP server at `backlog_core/server.py` already hosts the `mcp` FastMCP instance where new tools will be registered
- **Kage-bunshin SKILL.md**: Documents the milestone dispatch pattern including groom (no worktree) and work (with worktree) phases at `plugins/development-harness/skills/kage-bunshin/SKILL.md`

### Code References

- `backlog_core/server.py:1295` -- `dispatch_read` tool (pattern for new tools)
- `backlog_core/server.py:1289-1291` -- `_dispatch_plan_path()` helper
- `dispatch_schema/core/models.py:29-39` -- `ItemStatus` enum (pending/in-progress/complete/failed/skipped)
- `dispatch_schema/core/models.py:58-66` -- `WaveItem` model (title, issue, priority, conflict_group, depends_on, status)
- `dispatch_schema/core/models.py:69-74` -- `Wave` model (wave number, parallel flag, items list)
- `dispatch_schema/paths.py:11-21` -- `dispatch_plan_path()` canonical path function
- `kage-bunshin/scripts/spawn.py:286-357` -- `main()` spawn function and JSON output record

---

## Use Scenarios

### Scenario 1: Execute a Work Wave

**Actor**: Orchestrator agent running `/dh:work-milestone`
**Trigger**: A groomed milestone has a validated dispatch plan and the user invokes work execution
**Goal**: Spawn kage-bunshin sessions for all items in wave 1, with concurrency limited to 3, each in an isolated worktree on the integration branch
**Expected Outcome**: The orchestrator calls `dispatch_spawn(milestone=5, wave_num=1, max_concurrent=3, model="sonnet", phase="work")`. The tool returns a task ID immediately. The background task spawns up to 3 sessions at a time, reports progress ("Wave 1: 2/7 items complete"), and when all items finish, returns a structured summary with per-item status, elapsed time, and cost.

### Scenario 2: Monitor Active Dispatch

**Actor**: A second MCP client (monitoring agent, human with MCP inspector)
**Trigger**: A dispatch is running and the user wants to check progress
**Goal**: See which items are in-progress, which have completed, which have failed, and how long each has been running
**Expected Outcome**: The client calls `dispatch_wave_status(milestone=5, wave_num=1)` and receives a dict with items grouped by status, elapsed time per item, and overall wave progress (e.g., 4/7 complete, 1 failed, 2 in-progress).

### Scenario 3: Groom Multiple Items in Parallel

**Actor**: Orchestrator agent running `/dh:groom-milestone`
**Trigger**: A milestone has ungroomed backlog items
**Goal**: Spawn kage-bunshin sessions for grooming (no worktree needed, read-heavy, MCP-mediated writes)
**Expected Outcome**: The orchestrator calls `dispatch_spawn(milestone=5, wave_num=1, max_concurrent=5, model="sonnet", phase="groom")`. Sessions run in the current project directory without worktree isolation. Each completes independently and reports back via `dispatch_item_status`.

### Scenario 4: Resume After Crash

**Actor**: Orchestrator agent restarting after a session crash
**Trigger**: The previous orchestrator session died mid-wave
**Goal**: Determine what completed and what remains
**Expected Outcome**: The orchestrator calls `dispatch_wave_status(milestone=5, wave_num=2)` and sees 3/5 items complete, 2 items still showing in-progress (their PIDs may be dead). The orchestrator can decide whether to re-spawn the incomplete items or mark them failed.

---

## Gap Analysis

### Identified Gaps

| # | Category | Gap Description | Impact |
|---|----------|-----------------|--------|
| 1 | Scope | Boundary between `dispatch_spawn` and existing skills (`/dh:dispatch`, `/dh:work-milestone`) is unclear -- do the skills call the MCP tool, or does the MCP tool replace the skill logic? | Risk of duplicate orchestration paths that diverge over time |
| 2 | Behavior | What happens to in-progress items when an orchestrator crashes -- are stale PIDs detected automatically, or must the caller handle this? | Stale "in-progress" records that never resolve, blocking re-dispatch |
| 3 | Behavior | Should `dispatch_spawn` execute all waves sequentially (wave 1 completes before wave 2 starts), or only a single wave per invocation? | Determines whether the caller manages wave sequencing or the tool does |
| 4 | Integration | How does `dispatch_item_status` get called -- does the `dispatch_spawn` background task call it internally, or does each kage-bunshin session call it upon completion? | Affects whether kage-bunshin sessions need MCP client capability or whether the spawner monitors PIDs |
| 5 | Scope | Should `dispatch_spawn` run quality gates between waves (per the `quality_gates` field in `DispatchPlan`)? | Quality gates are part of the dispatch plan model but not mentioned in the tool descriptions |
| 6 | Behavior | The `{project-stub}` in the SQLite path `~/.dh/projects/{project-stub}/dispatch-state.db` -- how is it derived? Repo name? Path hash? | Determines whether two checkouts of the same repo share state or not |
| 7 | Integration | FastMCP `task=True` requires the `fastmcp[tasks]` extra (Docket dependency). Is this acceptable as a new dependency for the backlog MCP server? | Adds Docket + its dependencies to the plugin's requirements |
| 8 | User | The `cost` parameter on `dispatch_item_status` -- where does cost data come from? Claude CLI output? Estimated from model? | Determines whether cost tracking is real or placeholder |

---

## Questions Requiring Resolution

### Q1: Wave sequencing scope

- **Category**: Scope
- **Gap**: Should `dispatch_spawn` handle multi-wave sequencing (run wave 1, then wave 2, etc.) or only execute a single wave?
- **Question**: Does `dispatch_spawn` execute a single wave (caller manages sequencing), or does it accept `wave_num=None` to run all waves in order?
- **Options**:
  - A) Single wave per invocation -- caller (skill) decides when to start the next wave
  - B) All waves sequentially -- `dispatch_spawn` iterates through all waves in the plan
- **Why It Matters**: Option A keeps the tool simple and composable but requires the skill to loop. Option B is more autonomous but harder to interrupt or skip waves.
- **Resolution**: _pending_

### Q2: Quality gate integration

- **Category**: Scope
- **Gap**: The `DispatchPlan` model includes `quality_gates` (pre-merge and post-merge commands). The backlog item does not mention running these.
- **Question**: Should `dispatch_spawn` run quality gates between waves, or is that the caller's responsibility?
- **Options**:
  - A) `dispatch_spawn` runs pre-merge gates after each wave completes, blocking next wave on failure
  - B) Quality gates are the caller's responsibility -- `dispatch_spawn` only spawns and tracks
- **Why It Matters**: Embedding quality gates in the tool creates a tighter coupling to the dispatch plan schema but provides a more complete orchestration loop.
- **Resolution**: _pending_

### Q3: Stale PID detection

- **Category**: Behavior
- **Gap**: If the orchestrator crashes, items may remain "in-progress" in SQLite with PIDs that no longer exist.
- **Question**: Should the tools detect stale PIDs (e.g., `os.kill(pid, 0)` check) and auto-transition them to "failed", or should the caller handle stale detection?
- **Options**:
  - A) `dispatch_wave_status` checks PIDs and marks dead ones as failed automatically
  - B) A separate `dispatch_cleanup` tool handles stale detection
  - C) Caller is responsible for stale detection
- **Why It Matters**: Without stale detection, a crashed dispatch leaves permanent "in-progress" records that block re-dispatch of those items.
- **Resolution**: _pending_

### Q4: Project stub derivation

- **Category**: Behavior
- **Gap**: The SQLite path uses `{project-stub}` but the derivation method is unspecified.
- **Question**: How should `{project-stub}` be derived from the current project?
- **Options**:
  - A) Git remote URL slug (e.g., `jamie-bitflight-claude-skills`)
  - B) Repository root directory name (e.g., `claude_skills`)
  - C) Hash of the absolute repo root path
- **Why It Matters**: Option A is stable across clones but requires git remote access. Option B is simple but collides if two repos share a name. Option C is unique but opaque.
- **Resolution**: _pending_

### Q5: Item status reporter

- **Category**: Integration
- **Gap**: It is unclear whether `dispatch_item_status` is called by the `dispatch_spawn` background task (after PID exit) or by the kage-bunshin sessions themselves.
- **Question**: Who calls `dispatch_item_status` -- the spawn loop or the spawned sessions?
- **Options**:
  - A) The `dispatch_spawn` background task monitors PIDs, reads result files, and calls `dispatch_item_status` internally
  - B) Each kage-bunshin session calls `dispatch_item_status` via MCP before exiting
- **Why It Matters**: Option A is simpler (kage-bunshins need no changes) but the spawn loop must monitor PIDs. Option B requires kage-bunshins to know about dispatch state but provides real-time status.
- **Resolution**: _pending_

### Q6: Docket dependency acceptance

- **Category**: Integration
- **Gap**: `task=True` requires `fastmcp[tasks]` which pulls in Docket.
- **Question**: Is adding the Docket dependency acceptable for the backlog MCP server, or should `dispatch_spawn` use a different concurrency mechanism (e.g., `asyncio.create_task` with manual polling)?
- **Why It Matters**: Docket provides production-grade task scheduling but adds a dependency. Manual asyncio is lighter but requires implementing task tracking, progress reporting, and crash recovery from scratch.
- **Resolution**: _pending_

### Q7: Cost tracking source

- **Category**: User
- **Gap**: The `cost` parameter in `dispatch_item_status` has no documented source.
- **Question**: Where does per-item cost data come from? Is it parsed from the `claude -p --output-format json` result, or is it estimated, or is cost tracking deferred?
- **Options**:
  - A) Parse from claude CLI JSON output (if the field exists)
  - B) Placeholder field for future implementation
  - C) Omit cost tracking from initial implementation
- **Why It Matters**: If cost data is not reliably available from the CLI output, the parameter becomes dead weight.
- **Resolution**: _pending_

---

## Goals (Pending Resolution)

_These goals will be finalized after questions are resolved._

1. Add `dispatch_wave_start` MCP tool to the backlog server that records wave initiation and item PIDs in SQLite
2. Add `dispatch_item_status` MCP tool that records item completion/failure with result data
3. Add `dispatch_wave_status` MCP tool that queries current wave state from SQLite
4. Add `dispatch_spawn` MCP tool with `task=True` that runs the spawn-monitor-report loop as a background task with Progress reporting and concurrency throttle
5. Create SQLite state backend at `~/.dh/projects/{project-stub}/dispatch-state.db`
6. Integrate with existing `spawn.py` for process launching (no changes to spawn.py)
7. Integrate with existing `dispatch_read` for plan loading

---

## Next Steps

After questions are resolved:

1. Update "Resolution" fields in Questions section
2. Finalize Goals section
3. Proceed to RT-ICA assessment
4. Then proceed to architecture design
