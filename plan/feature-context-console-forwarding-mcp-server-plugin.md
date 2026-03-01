# Feature Context: Console Forwarding MCP Server Plugin

## Document Metadata

- **Generated**: 2026-03-01
- **Input Type**: simple_description
- **Source**: Feature request for a new plugin with FastMCP server enabling cross-session communication via tmux/dtach (local) and SSH (remote)
- **Status**: DISCOVERY_COMPLETE
- **GitHub Issue**: #364

---

## Original Request

Create a new plugin with a FastMCP server that enables Claude Code sessions to communicate with other Claude sessions locally (via dtach/tmux) and on remote hosts (via SSH). The server should allow monitoring of long-running multi-agent sessions, reading terminal output, sending commands, and coordinating across sessions.

Key MCP tools the server should expose:
- Session discovery: List running tmux/dtach sessions (local and remote)
- Output capture: Read terminal output from any pane (libtmux capture_pane)
- Command sending: Send keystrokes to sessions (libtmux send_keys)
- Session lifecycle: Create, attach, detach, kill sessions
- Remote access: SSH-based session operations on remote hosts (asyncssh)
- Health monitoring: Detect zombie/hung sessions (inspired by gastown Witness pattern)
- Multi-session coordination: Broadcast commands, collect output from multiple sessions

---

## Core Intent Analysis

### WHO (Target Users)

1. **Claude Code agent sessions** that need to monitor, control, or coordinate with other Claude Code sessions running in tmux/dtach
2. **Orchestrator agents** (e.g., `/implement-feature` skill) that spawn sub-agents in tmux sessions and need to observe their progress or inject commands
3. **Human developers** using Claude Code who want to inspect or interact with long-running agent sessions on local or remote machines

### WHAT (Desired Outcome)

A Claude Code session can, through MCP tool calls:
- Discover which tmux/dtach sessions are running (locally and on remote hosts via SSH)
- Read terminal output from any session's pane (scrollback, current visible text)
- Send keystrokes or commands to any session
- Create, detach, and kill sessions
- Detect zombie or hung sessions (tmux alive but Claude process dead)
- Broadcast a command to multiple sessions and collect aggregated output

Success looks like: An orchestrator Claude Code session can call `list_sessions()`, see 5 running agent sessions, call `capture_pane(session="agent-3", lines=100)` to check progress, and call `send_keys(session="agent-3", keys="continue\n")` to unstick a waiting agent.

### WHEN (Trigger Conditions)

- When a user or orchestrator has spawned multiple Claude Code sessions and needs visibility into their state
- When a long-running agent session appears stuck and the orchestrator needs to inspect its output or send a command
- When coordinating distributed agents across local and remote machines (SSH)
- When building dashboards or monitoring tools that aggregate multi-session state

### WHY (Problem Being Solved)

Currently, Claude Code sessions are isolated. A session cannot programmatically:
1. See what other sessions exist
2. Read their terminal output
3. Send them commands
4. Determine if they are healthy or hung

This forces human intervention for multi-agent coordination. The console forwarding MCP server bridges this gap by exposing terminal session control as MCP tools that any Claude Code session can call.

---

## Problem Space: Orchestrator Observability Gaps

This section captures the concrete pain points experienced by an AI orchestrator (e.g., Claude Code running `/implement-feature`) when coordinating multiple agent sessions. These are first-person observations from the orchestrating agent's perspective — the primary consumer of this plugin's MCP tools.

### Gap 1: Blind Spots Between Spawn and Return

When an orchestrator spawns 3-4 agents in parallel (via tmux sessions or sub-agents), it has **zero visibility** into what they're doing until they return. The orchestrator cannot determine:

- Whether agent #2 is stuck in a retry loop
- Whether agent #3 found something that invalidates agent #1's work
- Whether any agent is about to time out or has been idle for minutes

**What the orchestrator needs from capture_pane / session monitoring:**

| Signal | How Console Forwarding Solves It |
|--------|--------------------------------|
| **Heartbeat with current action** | `capture_pane(session="agent-3", lines=5)` — last few lines show what the agent is doing right now |
| **Elapsed time awareness** | `check_session_health()` with inactivity detection — "no output for 5 minutes" signals a stuck agent |
| **Progress estimation** | `capture_pane()` output parsed for task completion markers (e.g., "Task 3 of 7 complete") |

### Gap 2: No Inter-Agent Communication During Execution

Agents are currently fire-and-forget. If agent A discovers the architecture needs a different approach, there's no way to signal agent B (already implementing against the old assumption) to stop. Console forwarding enables:

- **Broadcast channel**: `send_keys(session="agent-*", keys="LIFECYCLE:Shutdown\n")` — signal all agents to halt
- **Dependency invalidation**: Orchestrator reads agent A's output via `capture_pane()`, detects a breaking change, then `send_keys()` to dependent agents with updated instructions
- **Coordination protocol**: Agents can write structured status to their terminal (JSON lines), and the orchestrator reads it via `capture_pane()` — creating a poor-man's message bus over terminal output

### Gap 3: Task Routing Lacks Runtime Intelligence

The orchestrator routes tasks based on static metadata (`Agent: python-cli-architect`). It has no signal for:

- **Complexity calibration**: Simple file renames vs. architectural refactors need different agents/models, but the task file says the same agent type
- **Historical success rate**: "Last 5 times this agent handled `complexity: High` tasks, 2 came back BLOCKED" — this would change parallelization strategy
- **Skill compatibility**: When a task lists `skills: ["fastmcp-python-tests", "python3-development"]`, the orchestrator doesn't know if those skills conflict or if a needed skill is missing

**How console forwarding helps**: By monitoring agent output in real-time, the orchestrator can detect early signs of struggle (repeated errors, long pauses) and intervene — reassigning, providing hints, or splitting the task — rather than waiting for the agent to return BLOCKED.

### Gap 4: Unstructured Agent Output

When agents return, the orchestrator receives a blob of text. What it needs instead:

```json
{
  "status": "COMPLETE",
  "files_changed": ["src/server.py", "tests/test_server.py"],
  "decisions_made": [
    {"decision": "Used asyncio.Queue instead of threading", "reason": "consistency with existing transport"}
  ],
  "blockers_encountered": [],
  "follow_up_needed": ["integration test with real MCP client"]
}
```

**How console forwarding enables this**: Agents can be instructed to write structured status lines to their terminal. The orchestrator uses `capture_pane()` with grep/parsing to extract these structured updates without waiting for the agent to finish.

### Gap 5: No Failure Recovery Beyond Retry

When an agent fails or returns BLOCKED, the orchestrator's only options are "try again with more context" or "ask the user." What's needed:

- **Failure taxonomy**: timeout vs. skill-missing vs. conflicting-instructions vs. genuinely-hard-problem — each has a different recovery path
- **Partial work preservation**: If an agent completed 3 of 5 acceptance criteria before failing, the orchestrator should spawn a new agent for just criteria 4-5, not restart from scratch
- **Cascading failure detection**: If task 2.1 fails and tasks 3.1, 3.2, 3.3 all depend on it, auto-hold those rather than discovering they're blocked one-by-one

**How console forwarding enables this**: `capture_pane()` on a failed/stuck agent shows exactly where it stopped — which files it changed, which tests it ran, what error it hit. The orchestrator can make an informed decision about recovery without guessing.

### Per-Task-Type Observability Needs

| Task Type | What Orchestrator Needs to See in Agent Output | Why |
|-----------|-----------------------------------------------|-----|
| New file creation | Target path + what imports it | Verify integration after completion |
| Refactor | Before/after function signatures | Dependent tasks can adapt |
| Test writing | Which source files are under test | Prevent duplicate coverage |
| Config/infra | Which environments affected | Test against correct env |
| Bug fix | Reproduction steps + expected behavior | Verification agent knows what "fixed" means |

### Summary: Console Forwarding as Orchestration Infrastructure

The console forwarding MCP server is not just a tmux convenience tool — it is **orchestration infrastructure**. It bridges the gap between "spawn agent and wait" and "actively manage a fleet of agents." The core value proposition for an AI orchestrator:

1. **Observability**: See what agents are doing without waiting for them to finish
2. **Intervention**: Send commands to stuck/misdirected agents in real-time
3. **Coordination**: Read structured output from agents to make routing decisions
4. **Recovery**: Inspect failed agents to determine the right recovery strategy
5. **Efficiency**: Detect problems early instead of discovering them after wasted work

---

## Prior Art: Orchestration Patterns from Research

This section documents validated multi-agent orchestration patterns from [research/research-agent-patterns/](./../../research/research-agent-patterns/) and [research/developer-tools/](./../../research/developer-tools/) that directly inform the console forwarding plugin's design. Each pattern is cited with its source and describes how existing systems solve the problems this plugin addresses.

### Pattern 1: Supervisor Polling via tmux (Claw Loop)

**Source**: [research/research-agent-patterns/claw-loop.md](./../../research/research-agent-patterns/claw-loop.md) — v2.0, verified 2026-02-15

A supervisory agent ("Clawdbot") polls a tmux session every 3 minutes via cron, detecting completion, stalls, crashes, context exhaustion, and rate limits. Core discipline: **one action per cycle** (state machine, no race conditions). The state file — not conversational memory — is the single source of truth.

**Key concepts this plugin adopts:**

| Claw Loop Concept | Console Forwarding Equivalent |
|-------------------|-------------------------------|
| `tmux capture-pane` to observe before acting (Principle 1) | `capture_pane()` MCP tool — same libtmux primitive exposed as a tool call |
| One action per cycle (Principle 2) | Serialized `send_keys()` — callers send one command, observe result, then decide next action |
| State file as source of truth (Principle 5) | Plugin is stateless; the orchestrator maintains its own state based on tool call results |
| `/clear` between phases to reset context (Principle 3) | `send_keys(session, "/clear\n")` — orchestrator can trigger context resets remotely |
| Crash = expected event, not exception (Principle 6) | `check_session_health()` returns `Zombie`/`Missing` as normal status values, not errors |
| 3-minute polling latency | Plugin eliminates this gap — orchestrator can poll on-demand via `capture_pane()` at any frequency |

**Design validation**: The Claw Loop proves that `capture_pane` + `send_keys` is sufficient infrastructure for autonomous multi-step orchestration. The plugin exposes these same primitives as MCP tools, removing the need for custom cron scripts.

### Pattern 2: Fleet Management with Role Taxonomy (Gas Town)

**Source**: [research/research-agent-patterns/gastown.md](./../../research/research-agent-patterns/gastown.md) — v0.9.0, 10,665 stars, verified 2026-03-01

Gas Town coordinates 20-30+ Claude Code agents using tmux sessions, git worktrees, and a Dolt SQL database. Key architectural patterns:

**ZFC (Zero-state-File Compliance) Principle**: tmux session existence IS the sole source of truth for agent liveness. No PID files, lock files, or on-disk state files. The Witness role cross-references:

1. `IsRunning()` — `tmux has-session` check
2. `IsAgentAlive()` — verifies Claude process inside the session (not just tmux shell)
3. `IsHealthy()` — checks whether session produced output within `maxInactivity` period

This three-layer check catches four distinct states: `SessionHealthy`, `SessionZombie` (tmux alive, Claude dead), `SessionHung` (Claude alive but no output), `SessionMissing`.

**Key concepts this plugin adopts:**

| Gas Town Concept | Console Forwarding Equivalent |
|------------------|-------------------------------|
| ZFC principle — session existence is truth | `check_session_health()` implements the same three-layer cross-reference |
| Four health states (Healthy/Zombie/Hung/Missing) | `check_session_health()` returns the same status enum |
| Witness patrol loop (continuous background monitoring) | Plugin provides on-demand checks (MCP request-response model); orchestrator implements its own polling if needed |
| Nudge = `tmux send-keys`, serialized per session with 30s timeout | `send_keys()` MCP tool — same primitive, stateless per call |
| Three-layer lifecycle: Identity (permanent) → Sandbox (persistent) → Session (ephemeral) | Plugin operates at the Session layer only; identity and sandbox management are out of scope |
| Mail protocol (POLECAT_DONE, MERGE_READY, etc.) | Not adopted — plugin provides raw transport (`send_keys` + `capture_pane`); message protocols are the orchestrator's responsibility |
| Dolt SQL persistent ledger for work state | Not adopted — plugin is stateless. Orchestrators that need persistent work tracking should use their own storage. |

**Design validation**: Gas Town's 10,665-star production deployment at 20-30+ concurrent agents proves the `tmux send-keys` + session health cross-reference pattern scales. The plugin's `check_session_health()` implements Gas Town's three-layer detection as a single stateless MCP tool call.

### Pattern 3: Peer-to-Peer Handoff via File Queue (TinyClaw)

**Source**: [research/research-agent-patterns/tinyclaw.md](./../../research/research-agent-patterns/tinyclaw.md) — v0.0.5, 2,124 stars, verified 2026-02-18

TinyClaw runs named agents 24/7 across Discord/Telegram/WhatsApp with no central orchestrator. Agents communicate peer-to-peer via `[@teammate: message]` bracket tags parsed from response text. File-based queue: `incoming/ → processing/ → outgoing/` with atomic rename as state transition.

**Key concepts relevant (but not directly adopted):**

| TinyClaw Concept | Relevance to Console Forwarding |
|------------------|---------------------------------|
| Per-agent workspace isolation (own `.claude/`, CLAUDE.md) | Validates that agents need separate tmux sessions (the sessions this plugin discovers and manages) |
| tmux daemon for always-on persistence | Confirms tmux as the universal session transport for long-running agents |
| Bracket-tag P2P handoff (no central orchestrator) | Alternative to the Claw Loop's centralized supervisor model. Console forwarding enables either pattern — orchestrator reads/writes via tools, or agents write status to their own terminal for peers to read |
| File-based atomic queue (rename = state transition) | Not adopted — plugin uses tmux I/O, not filesystem queues. But an orchestrator could combine both: use `capture_pane()` for real-time monitoring and file queues for durable message passing |
| Heartbeat system for proactive polling | Validates on-demand health check design — TinyClaw's heartbeat is the proactive equivalent of what `check_session_health()` provides on-demand |

**Design validation**: TinyClaw proves that decentralized coordination (no central orchestrator) works when agents have isolated workspaces and a communication channel. Console forwarding provides that communication channel — `capture_pane()` reads agent status, `send_keys()` injects messages.

### Pattern 4: Stateless Router-Not-Executor (Orchestrator Agent Guide)

**Source**: [research/research-agent-patterns/orchestrator-agent-creation-guide.md](./../../research/research-agent-patterns/orchestrator-agent-creation-guide.md) — OpenCode pattern, verified 2026-01-26

Defines the "Router, Not Executor" pattern: orchestrator analyzes intent, selects subagents, coordinates workflows. No execution tools — only routing and delegation. Capability map enforces delegation only to registered agents.

**Relevance**: Console forwarding is orchestration infrastructure that the router-not-executor pattern needs. The orchestrator routes tasks to subagents, but currently has no way to observe their progress or intervene. Console forwarding's `capture_pane()` and `send_keys()` tools give the router runtime visibility without breaking the router-not-executor constraint — the orchestrator still doesn't execute tasks, it observes and directs.

### Pattern 5: Context-Driven Development Lifecycle (Claude Conductor)

**Source**: [research/developer-tools/claude-conductor.md](./../../research/developer-tools/claude-conductor.md) — v1.2.1, verified 2026-02-17

Claude Conductor enforces a strict Context → Spec & Plan → Implement lifecycle with managed artifact generation. Relevant as a consumer pattern: Conductor's workflow phases could use console forwarding to monitor agent progress during the Implement phase.

**Relevance**: Validates the "orchestrator as consumer" pattern — structured workflows (like SAM's `/implement-feature`) that spawn agents need runtime visibility into agent progress. Console forwarding is the infrastructure layer that enables this.

### Cross-Pattern Synthesis: What This Plugin Provides That None of These Systems Have

| Capability | Claw Loop | Gas Town | TinyClaw | Console Forwarding Plugin |
|-----------|-----------|----------|----------|--------------------------|
| tmux session control | Custom bash scripts | Go library (`internal/tmux/`) | Shell scripts | **MCP tools** callable by any Claude Code session |
| Output capture | `tmux capture-pane` in cron script | Bead state from Dolt SQL | File queue reads | **`capture_pane()` with `lines` + `offset` pagination** |
| Remote SSH sessions | Not supported | Not supported | Not supported (uses messaging platforms) | **asyncssh-based remote tmux operations** |
| Health check | Clawdbot poll cycle | Witness patrol loop | Heartbeat daemon | **Single stateless MCP tool call** |
| Session management | Manual tmux commands | `gt polecat spawn/nuke` CLI | `tinyclaw start/stop` CLI | **`create_session()` / `kill_session()` MCP tools** |
| Integration model | Standalone cron job | Standalone Go binary | Standalone Node.js platform | **Claude Code plugin** — auto-loaded, no separate install |

The plugin's unique contribution: exposing validated patterns (tmux transport, ZFC health detection, serialized send_keys) as **MCP tools within the Claude Code plugin ecosystem**, eliminating the need for standalone orchestration infrastructure.

---

## Codebase Research

### Similar Patterns Found

#### Pattern 1: Kaizen Analysis MCP Server (FastMCP + PEP 723 inline script)

- **Location**: `plugins/agentskill-kaizen/mcp/server.py:1-614`
- **Relevance**: The only existing FastMCP server in the codebase. Demonstrates the exact pattern this feature needs: PEP 723 inline script metadata for `uv run --script`, `FastMCP("name")` instantiation, async tool definitions with `@mcp.tool(annotations=...)`, `Context` parameter for progress reporting, `ToolError` for error handling, and `asyncio.to_thread()` for wrapping blocking operations.
- **Reusable**: PEP 723 script header pattern (lines 1-15), tool annotation dicts `_READONLY_ANNOTATIONS` and `_DASHBOARD_ANNOTATIONS` (lines 58-70), `mcp.run()` entry point (line 614), async-wrapping pattern via `asyncio.to_thread()`.

#### Pattern 2: Kaizen Plugin JSON (mcpServers declaration)

- **Location**: `plugins/agentskill-kaizen/.claude-plugin/plugin.json:19-31`
- **Relevance**: Shows the exact `mcpServers` declaration format that Claude Code uses to auto-start MCP servers from plugins. The `"kaizen-analysis"` server uses `"command": "uv"` with `"args": ["run", "--script", "${CLAUDE_PLUGIN_ROOT}/mcp/server.py"]` -- this is the deployment pattern the console forwarding server must follow.
- **Reusable**: The entire `mcpServers` block structure, `${CLAUDE_PLUGIN_ROOT}` variable for plugin-relative paths.

#### Pattern 3: FastMCP Creator Reference (MCP tool design guidelines)

- **Location**: `plugins/fastmcp-creator/skills/fastmcp-creator/references/mcp-best-practices.md:1-60`
- **Relevance**: Documents tool naming conventions (`{service}_{action}_{resource}` in snake_case), tool annotation requirements (`readOnlyHint`, `destructiveHint`, `idempotentHint`, `openWorldHint`), and output token limits (warning at 10,000 tokens, max 25,000). These constraints directly shape tool API design.
- **Reusable**: Naming conventions, annotation patterns, output size awareness.

#### Pattern 4: Claude Code MCP Integration Reference

- **Location**: `plugins/fastmcp-creator/skills/fastmcp-creator/references/claude-code-mcp-integration.md:1-248`
- **Relevance**: Documents how Claude Code discovers, configures, and connects to MCP servers. Covers plugin-bundled server lifecycle (`${CLAUDE_PLUGIN_ROOT}`), transport selection (stdio for local), scope rules, output limits, tool search behavior, and `list_changed` notification support.
- **Reusable**: Transport selection guidance (stdio for local plugin), output limit awareness, plugin server lifecycle understanding.

### Existing Infrastructure

#### libtmux Research (verified API surface)

- **Location**: `research/developer-tools/libtmux.md:1-571`
- **Key findings**: `Server` is NOT a dataclass (traditional class with mixins); `Session`, `Window`, `Pane` ARE dataclasses. `Pane.send_keys(text, enter=True)` for keystroke injection. `Pane.capture_pane(start=-50, end="-")` for output capture. `Server(socket_name="...")` for socket isolation. `server.sessions` returns `QueryList[Session]` with ORM-style filtering. Context manager support for cleanup. Pytest fixtures for isolated testing. All operations are synchronous (subprocess-based `tmux_cmd()`) -- requires `asyncio.to_thread()` wrapping for async MCP tools.

#### dtach Research

- **Location**: `research/developer-tools/dtach.md:1-204`
- **Key findings**: Unix-domain socket per session. `-n` for fire-and-forget daemon creation. `-p` for piping stdin into running session. Executable-bit on socket indicates attachment state. No terminal emulation layer (raw byte passthrough). No Python API -- requires subprocess invocation. No scrollback or capture capability (unlike tmux).

#### asyncssh Research

- **Location**: `research/async-libraries/asyncssh.md:1-493`
- **Key findings**: Full async/await API on asyncio. `asyncssh.connect()` for SSH client. `conn.run(command)` for remote commands. `tunnel` parameter for jump-host chaining. `connect_reverse()` / `listen_reverse()` for NAT traversal. `start_sftp_client()` for file transfer. Depends on PyCA/cryptography (NOT pure Python keys as sometimes claimed). Key generation via `asyncssh.generate_private_key()`.

#### gastown Witness Pattern (zombie detection)

- **Location**: `research/research-agent-patterns/gastown.md:49-80`
- **Key findings**: ZFC principle -- tmux session existence IS source of truth for liveness. Four states: `SessionHealthy`, `SessionZombie` (tmux alive, Claude dead), `SessionHung` (alive but no output in maxInactivity period), `SessionMissing`. Detection cross-references tmux `has-session` with process liveness check (`IsAgentAlive()`), then activity check (`IsHealthy()`). Witness patrols on a continuous loop.

#### Tabz Console Forwarding Pattern

- **Location**: `research/developer-tools/tabz-browser-console-forwarder.md:1-246`
- **Key findings**: Demonstrates the "forwarding" concept -- intercepting output from one context and making it available in another. Tabz forwards browser console to terminal stdout via batched HTTP POST. The naming "console forwarding" in this feature request draws from this pattern but applies it to terminal sessions rather than browser consoles.

### Code References

- `plugins/agentskill-kaizen/mcp/server.py:1-15` - PEP 723 inline script metadata pattern for `uv run --script`
- `plugins/agentskill-kaizen/mcp/server.py:58-63` - `_READONLY_ANNOTATIONS` dict for read-only MCP tool hints
- `plugins/agentskill-kaizen/mcp/server.py:83` - `FastMCP("kaizen-analysis", mask_error_details=False)` instantiation
- `plugins/agentskill-kaizen/mcp/server.py:280-296` - Async tool with `asyncio.to_thread()` wrapping synchronous code
- `plugins/agentskill-kaizen/mcp/server.py:610-614` - `mcp.run()` entry point
- `plugins/agentskill-kaizen/.claude-plugin/plugin.json:27-30` - `mcpServers` declaration with `uv run --script`
- `plugins/fastmcp-creator/.claude-plugin/validator.json:1-5` - Validator ignore configuration

---

## Use Scenarios

### Scenario 1: Orchestrator Monitors Agent Fleet

**Actor**: An orchestrator Claude Code session running `/implement-feature`
**Trigger**: Multiple sub-agent sessions spawned in tmux for parallel task execution; orchestrator needs to check progress
**Goal**: List all running agent sessions, read output from each to assess completion status
**Expected Outcome**: Orchestrator calls `list_sessions()`, receives JSON listing 4 sessions with names, states, and pane counts. Calls `capture_pane(session="agent-task-2", lines=50)` and reads the last 50 lines to determine if the task is complete or stuck.

### Scenario 2: Unsticking a Hung Agent

**Actor**: A Claude Code session acting as a monitoring agent (similar to gastown Witness)
**Trigger**: Health check detects a session that has produced no output for 5 minutes
**Goal**: Inspect the hung session and send a recovery command
**Expected Outcome**: Calls `check_session_health(session="worker-3")` which returns `SessionHung` status. Calls `capture_pane(session="worker-3", lines=20)` to see the agent is waiting for user input. Calls `send_keys(session="worker-3", keys="yes\n")` to provide the expected input.

### Scenario 3: Remote Agent Coordination via SSH

**Actor**: A local Claude Code session coordinating with agents on a remote build server
**Trigger**: User has agents running on `build-server.corp.com` in tmux sessions
**Goal**: List remote sessions, read output from a specific remote session
**Expected Outcome**: Calls `list_sessions(host="ssh://deploy@build-server.corp.com")` to discover remote tmux sessions. Calls `capture_pane(host="ssh://deploy@build-server.corp.com", session="ci-runner", lines=100)` to read build output.

### Scenario 4: Broadcast Command to All Sessions

**Actor**: An orchestrator needing to signal all agents to stop work
**Trigger**: A critical error is discovered that requires all agents to halt
**Goal**: Send a shutdown signal to all running agent sessions at once
**Expected Outcome**: Calls `broadcast_keys(pattern="agent-*", keys="LIFECYCLE:Shutdown\n")` which sends the command to all sessions matching the pattern. Returns a summary of which sessions received the command.

### Scenario 5: Session Lifecycle Management

**Actor**: A Claude Code session setting up a multi-agent workspace
**Trigger**: User wants to create isolated tmux sessions for parallel agent work
**Goal**: Create named sessions with specific dimensions, then later kill completed ones
**Expected Outcome**: Calls `create_session(name="agent-task-1", width=220, height=50, command="claude")` three times. After tasks complete, calls `kill_session(name="agent-task-1")` to clean up.

---

## Gap Analysis

### Identified Gaps

| # | Category | Gap Description | Impact |
|---|----------|-----------------|--------|
| 1 | Scope | The feature lists 7 tool categories but does not specify which are MVP vs future. All 7 implemented at once is a large scope. | Over-scoping risks incomplete implementation; under-scoping risks missing critical tools |
| 2 | Behavior | libtmux is synchronous (subprocess-based). The request says "no blocking I/O" but libtmux cannot be made async natively. `asyncio.to_thread()` is the workaround but has concurrency implications. | Concurrent tool calls hitting the same tmux server via `to_thread()` may have race conditions |
| 3 | Behavior | dtach has no output capture capability (no scrollback, no capture-pane equivalent). The request lists it as a backend but does not clarify what operations it supports vs tmux. | dtach backend can only create/attach/detach/kill sessions and pipe input -- it cannot read output. Users may expect parity with tmux backend. |
| 4 | Integration | The request suggests `ssh://user@host/session` URI syntax for remote sessions but does not define the full URI format, credential handling, or connection pooling strategy. | Ambiguous URI format leads to inconsistent implementation; missing credential story blocks remote usage |
| 5 | Behavior | Health monitoring (zombie/hung detection) requires a polling/patrol loop, but MCP tools are request-response. How does health monitoring work as a tool? Is it a single-call check or a persistent background monitor? | Determines whether health check is a simple tool call or requires background task infrastructure |
| 6 | Scope | "Multi-session coordination: Broadcast commands, collect output from multiple sessions" -- this implies fan-out/fan-in semantics. What is the expected behavior when some sessions succeed and others fail? | Error aggregation strategy affects tool return schema |
| 7 | User | The backlog item says the server should run "with no external daemon dependencies" but dtach requires dtach binary and tmux requires tmux binary on the system. Are these treated as runtime prerequisites? | If tmux/dtach are not installed, should the server gracefully degrade or fail to start? |
| 8 | Integration | PEP 723 inline script metadata means all dependencies are declared in the server.py file. But the request describes 5 separate Python files (server.py + 3 backends + session_manager). PEP 723 only applies to the entry point script. How do the other files get their dependencies? | Multi-file structure may require a pyproject.toml or package setup rather than pure PEP 723 |
| 9 | Behavior | The kaizen server pattern uses `asyncio.to_thread()` to wrap blocking code. For remote SSH operations, asyncssh is already async and does NOT need `to_thread()`. This means the tmux backend and SSH backend have fundamentally different async patterns. | Backend abstraction must accommodate both sync-wrapped-in-async and natively-async implementations |
| 10 | Scope | The request mentions creating a SKILL.md for the plugin. What user-facing guidance does the skill provide beyond what the MCP tools expose? Is it an instructional skill or does it invoke tools? | Determines skill content scope |

---

## Questions Requiring Resolution

### Q1: What is the MVP tool set?

- **Category**: Scope
- **Gap**: 7 tool categories listed; all at once is large scope
- **Question**: Which tool categories are essential for the first version: (A) session discovery + output capture + command sending only, (B) A plus session lifecycle, (C) A plus B plus remote SSH, (D) all 7 categories including health monitoring and multi-session coordination?
- **Options**:
  - A) Discovery + capture + send_keys (3 tools, local only)
  - B) A + session create/kill (5 tools, local only)
  - C) B + remote SSH variants (5 tools, local + remote)
  - D) All 7 categories including health monitoring and broadcast
- **Why It Matters**: Determines task count, complexity, and delivery timeline. Health monitoring and multi-session coordination add significant complexity.
- **Resolution**: **Option C** — MVP includes discovery + capture + send_keys + lifecycle + remote SSH. Health monitoring and broadcast are deferred to a follow-up. Rationale: SSH is a core requirement (user request specifically mentions remote hosts). Health monitoring and broadcast add significant complexity without being essential for v1 cross-session communication.

### Q2: How should dtach backend limitations be handled?

- **Category**: Behavior
- **Gap**: dtach cannot capture output (no scrollback/capture-pane equivalent). It can only create/kill sessions and pipe input.
- **Question**: Should the dtach backend (A) be included as a limited backend that supports only session lifecycle and input piping, with capture operations returning an error, (B) be deferred to a later version, or (C) be dropped since tmux covers all use cases that dtach covers plus more?
- **Options**:
  - A) Include with limited capability (create, kill, send input -- no capture)
  - B) Defer to later version
  - C) Drop dtach entirely; tmux is sufficient
- **Why It Matters**: dtach adds a separate backend with unique edge cases but provides no capabilities that tmux lacks. Including it increases scope without clear benefit unless users specifically need dtach's lightweight footprint.
- **Resolution**: **Option B** — Defer dtach to a later version. tmux covers all dtach capabilities plus output capture. The session_manager abstraction will be designed to support additional backends, making dtach easy to add later.

### Q3: What is the SSH URI format and credential model?

- **Category**: Integration
- **Gap**: Remote access references `ssh://user@host/session` but no formal URI spec or auth model
- **Question**: What SSH URI format should be used, and how should credentials be provided? Specifically: (A) full URI like `ssh://user@host:port/tmux-session-name` with SSH agent for keys, (B) separate host/user/port parameters on each tool call, or (C) pre-registered host configurations stored in the server?
- **Options**:
  - A) URI format `ssh://user@host:port/session-name`, keys from SSH agent
  - B) Separate parameters: `host`, `user`, `port`, `session` on each tool call
  - C) Named host registry: `register_host(name="build", host="...", user="...", key="...")` then reference by name
- **Why It Matters**: Affects tool parameter design, credential security, and connection reuse. Option C adds state management but simplifies repeated access.
- **Resolution**: **Option A** — URI format `ssh://user@host:port/session-name`, keys from SSH agent or `~/.ssh/`. Simple, standard, stateless. Connection pooling handled internally by asyncssh's connection reuse. No host registry needed for v1.

### Q4: Is health monitoring a single-call tool or a background patrol?

- **Category**: Behavior
- **Gap**: Health monitoring patterns (gastown Witness) use polling loops, but MCP tools are request-response
- **Question**: Should health monitoring be (A) a single tool call `check_session_health(session)` that returns current status at call time, (B) a background patrol that runs continuously and exposes results via a `get_health_report()` tool, or (C) both?
- **Options**:
  - A) Single-call `check_session_health()` -- stateless, on-demand
  - B) Background patrol thread with `get_health_report()` -- stateful, continuous
  - C) Both: on-demand check plus optional background patrol
- **Why It Matters**: Background patrol adds threading complexity and state management. On-demand check is simpler but requires the caller to implement polling.
- **Resolution**: **Option A** — Single-call `check_session_health()`, stateless and on-demand. Aligns with MCP request-response model. Deferred from MVP (see Q1), but when implemented, should be request-response only.

### Q5: How should multi-file structure work with PEP 723?

- **Category**: Integration
- **Gap**: PEP 723 inline script metadata only applies to the entry point (server.py). The request describes 5 files.
- **Question**: Should the plugin (A) use PEP 723 only on server.py with all other files as local imports (no separate dependency declarations), (B) switch to a pyproject.toml-based package structure like standard Python packages, or (C) keep everything in a single server.py file?
- **Options**:
  - A) PEP 723 on server.py; backends as local imports in same directory
  - B) pyproject.toml package with proper `src/` layout
  - C) Single monolithic server.py (matching kaizen pattern)
- **Why It Matters**: The kaizen server is a single file (`server.py`, 614 lines). The console forwarding server with 3 backends and a session manager will be significantly larger. Single-file may be unwieldy; multi-file needs a dependency resolution strategy.
- **Resolution**: **Option A** — PEP 723 on server.py as the entry point; backends as local imports in the same mcp/ directory. `uv run --script server.py` picks up PEP 723 deps; backend modules are plain .py files imported by server.py. This matches how Python scripts with local module imports work under `uv run --script`.

### Q6: Should the server gracefully degrade when tmux/dtach is not installed?

- **Category**: User
- **Gap**: tmux and dtach are system-level binaries, not Python packages
- **Question**: If tmux is not installed, should the server (A) fail to start with a clear error, (B) start but disable tmux-dependent tools and expose only SSH tools, or (C) start and return errors when tmux tools are called?
- **Options**:
  - A) Fail to start if tmux not found
  - B) Graceful degradation: start with available backends only
  - C) Start always; return ToolError on missing backend calls
- **Why It Matters**: Option B is the most resilient but adds startup detection logic. Option A is simplest but blocks SSH-only use cases.
- **Resolution**: **Option B** — Graceful degradation: detect available backends at startup, expose only tools for available backends. If tmux is not installed, SSH tools still work. Aligns with robust server design.

### Q7: What output format should capture_pane return?

- **Category**: Behavior
- **Gap**: MCP tool output has a 25,000 token limit. Terminal output can be very large.
- **Question**: Should `capture_pane` (A) accept `lines` and `offset` parameters for caller-controlled pagination, (B) return all available output up to a reasonable default, or (C) return a summary with a way to request more?
- **Why It Matters**: The "No Invented Limits" rule in CLAUDE.md says to let the caller control the window. This aligns with option A. But very large pane captures could hit MCP output token limits.
- **Resolution**: **Option A** — Accept `lines` and `offset` parameters for caller-controlled pagination. Default to full visible pane (no artificial truncation). Warn in tool description about MCP output token limits. Aligns with CLAUDE.md "No Invented Limits" rule.

---

## Goals (MVP — v1)

### Core MCP Server

1. Create a new plugin at `plugins/console-forwarding/` with a FastMCP MCP server that Claude Code can load via `plugin.json` `mcpServers` declaration
2. Expose MCP tools for **local tmux** session discovery, output capture, keystroke injection, and session lifecycle using libtmux
3. Expose MCP tools for **remote** session operations via asyncssh (same tool set, SSH URI parameter)
4. Mark read-only tools with `readOnlyHint` and destructive tools (send_keys, kill) with `destructiveHint`
5. Ensure all I/O is async (libtmux via `asyncio.to_thread()`, asyncssh natively)
6. Gracefully degrade when tmux is not installed (SSH-only tools still available)

### Orchestrator Observability (Primary Consumer: AI Orchestrators)

7. `capture_pane` supports `lines` + `offset` pagination so orchestrators can poll agent output without reading entire scrollback
8. `list_sessions` returns structured metadata (session name, pane count, last activity time, dimensions) enabling fleet-level monitoring
9. `check_session_health` returns a status enum (`Healthy`, `Idle`, `Hung`, `Zombie`, `Missing`) using inactivity timeout + process liveness checks — enabling orchestrators to detect stuck agents without guessing
10. `send_keys` supports targeted intervention: orchestrators can send recovery commands, lifecycle signals (`LIFECYCLE:Shutdown`), or updated instructions to specific sessions

### Quality & Documentation

11. Include pytest tests using libtmux's built-in test fixtures for isolated tmux testing
12. Create a user-facing SKILL.md documenting session naming, SSH setup, troubleshooting, and orchestrator integration patterns (structured output conventions, polling strategies, intervention protocols)

**Deferred to v2**: Multi-session broadcast/coordination (fan-out/fan-in), dtach backend, persistent health patrol (background polling thread), structured agent output protocol (standardized JSON status lines), failure taxonomy classification

---

## Not in Scope (MVP)

The following are explicitly excluded from v1. Items marked **v2** are planned for a future version; items marked **out** are outside the plugin's responsibility entirely.

### Deferred to v2

| Item | Rationale |
|------|-----------|
| Multi-session broadcast/coordination (fan-out/fan-in) | Adds fan-out error-aggregation complexity; orchestrators can loop `send_keys()` calls in v1 (Q1 resolution) |
| dtach backend | tmux covers all dtach capabilities plus output capture; backend abstraction designed for future addition (Q2 resolution) |
| Persistent health patrol (background polling thread) | MCP is request-response; background threads add state management complexity; on-demand `check_session_health()` sufficient for v1 (Q4 resolution) |
| Structured agent output protocol (standardized JSON status lines) | Requires agent-side adoption; v1 provides raw transport, orchestrators parse output themselves |
| Failure taxonomy classification | Useful for automated recovery routing but adds significant complexity; v1 returns raw status values |
| Host registry / connection pooling configuration | Stateless URI-per-call model is sufficient for v1; asyncssh handles internal connection reuse (Q3 resolution) |

### Out of Scope (not planned for any version)

| Item | Rationale |
|------|-----------|
| Identity / sandbox lifecycle management | Plugin operates at the Session layer only; identity and sandbox management belong to the orchestrator (Prior Art Pattern 2: Gas Town three-layer lifecycle) |
| Message protocols (POLECAT_DONE, MERGE_READY, etc.) | Plugin provides raw transport (`send_keys` + `capture_pane`); message protocols are the orchestrator's responsibility (Prior Art Pattern 2) |
| Persistent work state ledger | Plugin is stateless; orchestrators that need persistent work tracking use their own storage (Prior Art Pattern 2: Gas Town uses Dolt SQL) |
| pyproject.toml package structure | PEP 723 on entry point with local imports is sufficient; no distribution packaging needed (Q5 resolution) |
| Task routing intelligence | The plugin provides observability data; routing decisions belong to the orchestrator (Gap 3 in Problem Space) |

### In Scope — Cross-Platform Note

**Windows support** is in scope. The tmux backend is Linux/macOS-only, but the SSH backend works cross-platform. Graceful degradation (Q6 resolution: Option B) ensures the server starts on Windows with SSH tools available even when tmux is absent. Windows-native terminal multiplexers (e.g., psmux) may be added as backends in future versions.

---

## Next Steps

After questions are resolved:

1. Update "Resolution" fields in Questions section
2. Finalize Goals section (remove/add goals based on MVP scope decision)
3. Proceed to RT-ICA assessment
4. Then proceed to architecture design via `@python3-development:python-cli-design-spec`
