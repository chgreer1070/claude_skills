---
name: Implementation Manager MCP Server — orchestrator-facing FastMCP server wrapping SAM task file operations
description: >-
  The orchestrator has no atomic, validated tooling for managing SAM task files.
  It currently reaches those files through read-only CLI calls, raw markdown/YAML
  edits, multi-step JSON writes for session context, and zero tracking of
  delegated subagent work. A FastMCP 3.x MCP server exposing these operations as
  first-class tools would make orchestrator task management reliable, auditable,
  and state-machine-enforced.
metadata:
  topic: implementation-manager-mcp-server-orchestrator-facing-fastmc
  source: Session observation — manual hook fix (#337) revealed systematic tooling gap
  added: '2026-03-01'
  groomed: '2026-03-03'
  priority: P1
  type: Feature
  status: open
  issue: '#365'
  stack: fastmcp
  language: python
---

## Groomed (2026-03-03)

### Problem Space

The orchestrator interacts with SAM task files (plan/tasks-*.md) through four
separate, fragile mechanisms today:

1. **CLI calls to `implementation_manager.py`** — read-only; scoped to one
   feature at a time; requires `uv run` subprocess and JSON parsing by the
   caller.
2. **Raw Edit/Read tool calls on markdown/YAML files** — no state machine; an
   invalid transition (e.g. `COMPLETE → NOT_STARTED`) is silently accepted; a
   partial write leaves the file inconsistent.
3. **Three-step manual JSON writes for session context** — `bash printf`,
   `mkdir -p`, and file write must all succeed in sequence. A partial failure
   leaves context files orphaned or missing.
4. **No delegation tracking** — once a subagent is launched, the orchestrator
   has no record of which task it owns, what agent was used, or whether it
   completed. The `SubagentStop` hook (commit `872e38d3`, fix for #337) is the
   only completion signal and it is regex-fragile.

The gap is structural: all write operations on task files happen outside any
validation layer, and the session-context and delegation surfaces do not exist
as tool calls at all.

**Files and code involved:**

| Path | Role |
|------|------|
| `plugins/python3-development/skills/implementation-manager/scripts/implementation_manager.py` | Existing CLI data layer (1172 lines); read-only commands: `list-features`, `status`, `ready-tasks`, `validate` |
| `plugins/python3-development/skills/implementation-manager/scripts/task_format.py` | Task parsing/serialisation utilities (311 lines) |
| `plugins/python3-development/skills/implementation-manager/scripts/get_task_context.py` | Single-session context file reader |
| `plugins/python3-development/skills/implementation-manager/scripts/task_status_hook.py` | `SubagentStop` hook; sole completion-marking mechanism |
| `.claude/context/active-task-{session_id}.json` | Session context files; pattern already established |
| `plugins/agentskill-kaizen/mcp/server.py` | Reference FastMCP 3.x server in this repo |
| `.claude/skills/backlog/backlog_core/server.py` | Reference project-level FastMCP 3.x server in this repo |
| `.claude/skills/start-task/SKILL.md` | Documents the 3-step manual bash `task_claim` equivalent |
| `plugins/development-harness/` | Natural host plugin for the new server |

**Verified facts (from fact-check):**

- The project uses **FastMCP 3.x** (`fastmcp>=3.0.2` in `pyproject.toml`). The
  original item description incorrectly said "FastMCP 2.x" — this is **refuted**.
- No delegation-tracking code exists anywhere in the repository (grep confirms
  no `task_log_delegation`, no delegation log files).
- `.claude/settings.json` has an empty `mcpServers` object; MCP registration
  mechanism is not yet established (inconclusive — to be resolved in planning).
- `implementation_manager.py` CLI offers only read operations; all write paths
  go through raw file edits today.

### Priority

8/10 — The delegation black hole and context-file partial-failure are live
reliability risks on every SAM feature cycle. The absence of state-machine
enforcement means any session can silently corrupt task state. Fixing this
unblocks reliable multi-session orchestration.

### Impact

- **Orchestrator reliability**: partial context writes and silent state
  corruption affect every feature that uses the SAM workflow.
- **Delegation visibility**: no record of live subagents means a crashed
  subagent is indistinguishable from a running one until the next hook fires.
- **Scalability**: as feature count grows, the lack of a cross-feature dashboard
  query forces repeated CLI invocations that scale linearly with feature count.

### Benefits

- Atomic, validated writes eliminate partial-failure classes for context and
  status operations.
- State-machine enforcement makes invalid task transitions observable errors
  rather than silent data corruption.
- Delegation log surfaces agent lifecycle, enabling timeout detection and
  result persistence across context compaction.
- Cross-feature dashboard query replaces O(N) CLI calls with a single tool call.

### Expected Behaviour

When the orchestrator needs to act on a SAM task file — start a task, mark it
complete, block it, query readiness, or delegate to a subagent — it calls a
single MCP tool. That tool validates the requested operation against the state
machine, performs all required file operations atomically, and returns
structured JSON. The orchestrator never touches markdown or JSON files directly.

**Tool surface (what must exist, not how it is built):**

| Group | Tools |
|-------|-------|
| Query | `task_dashboard`, `task_view`, `task_ready`, `task_dependency_graph` |
| Status mutation | `task_transition`, `task_block`, `task_unblock`, `task_add_note` |
| Session context | `task_claim`, `task_release`, `task_active` |
| Delegation tracking | `task_log_delegation`, `task_log_result`, `task_active_agents` |
| Workflow | `task_next`, `task_validate`, `task_create` |

State machine for `task_transition`:
`NOT_STARTED → IN_PROGRESS → COMPLETE`, any state `→ BLOCKED`,
`BLOCKED → NOT_STARTED | IN_PROGRESS`.

**Out of scope:** subagent output tailing, task deletion, auto-scheduling.

### Acceptance Criteria

1. An MCP server binary/script is present and startable with no import errors.
2. Calling `task_view` with a valid task ID returns the task's fields (status,
   agent, acceptance criteria, timestamps) as structured JSON without requiring
   the caller to parse markdown.
3. Calling `task_transition` with an invalid transition (e.g. `COMPLETE →
   NOT_STARTED`) returns an error; the file is unchanged.
4. Calling `task_claim` once writes the context file at
   `.claude/context/active-task-{session_id}.json`, sets the task to
   `IN_PROGRESS`, and records a `Started` timestamp — in one call with no
   partial-state risk.
5. Calling `task_release` marks the task `COMPLETE`, adds a `Completed`
   timestamp, and removes the context file.
6. Calling `task_active` returns all currently claimed tasks across all sessions
   (scans `.claude/context/`).
7. Calling `task_log_delegation` writes a delegation record that persists across
   session context compaction; `task_active_agents` returns it until
   `task_log_result` closes it.
8. `task_dashboard` returns a cross-feature summary (all features, task counts
   by status, blockers) in a single call.
9. All mutation tools are idempotent where possible (repeat call = same outcome,
   no duplicate writes or errors on repeat).
10. The server is reachable by the orchestrator; the registration mechanism
    (settings.json or plugin manifest) is documented and verified working.

### Issue Classification

**Type**: unbounded-design
**Rationale**: Greenfield MCP server — tool surface, delegation-log storage
format, and registration mechanism are all open design choices with no prior
failure to trace. Emerged from recognising a systematic tooling gap, not from a
broken component.
**Analysis Method**: design-framing
**Scenario Target**: Orchestrator managing SAM task files manually via CLI +
raw edits → Orchestrator uses atomic MCP tools with state-machine enforcement
and delegation tracking

### Resources

| Type | Item |
|------|------|
| Reference server (FastMCP 3.x) | `plugins/agentskill-kaizen/mcp/server.py` |
| Reference server (project-level) | `.claude/skills/backlog/backlog_core/server.py` |
| Data layer | `plugins/python3-development/skills/implementation-manager/scripts/implementation_manager.py` |
| Data layer | `plugins/python3-development/skills/implementation-manager/scripts/task_format.py` |
| Session context reader | `plugins/python3-development/skills/implementation-manager/scripts/get_task_context.py` |
| Hook reference | `plugins/python3-development/skills/implementation-manager/scripts/task_status_hook.py` |
| Host plugin | `plugins/development-harness/` |
| Related ideas item | `.claude/backlog/ideas-development-harness-task-status-mcp.md` (#257) |
| Skill | `implementation-manager` (python3-development plugin) |
| Framework | `fastmcp>=3.0.2` (pyproject.toml) |

### Dependencies

- **Depends on**: FastMCP 3.x available in project (`pyproject.toml` ✓)
- **Unblocks**: reliable multi-session orchestration, delegation timeout
  detection, cross-feature dashboard queries

### Effort

High — ~15 MCP tools, delegation log storage design, state machine
implementation, registration mechanism, and multi-session context scanning are
all net-new.