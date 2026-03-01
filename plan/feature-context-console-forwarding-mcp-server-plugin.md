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

1. Create a new plugin at `plugins/console-forwarding/` with a FastMCP MCP server that Claude Code can load via `plugin.json` `mcpServers` declaration
2. Expose MCP tools for **local tmux** session discovery, output capture, keystroke injection, and session lifecycle using libtmux
3. Expose MCP tools for **remote** session operations via asyncssh (same tool set, SSH URI parameter)
4. Mark read-only tools with `readOnlyHint` and destructive tools (send_keys, kill) with `destructiveHint`
5. Ensure all I/O is async (libtmux via `asyncio.to_thread()`, asyncssh natively)
6. Gracefully degrade when tmux is not installed (SSH-only tools still available)
7. Include pytest tests using libtmux's built-in test fixtures for isolated tmux testing
8. Create a user-facing SKILL.md documenting session naming, SSH setup, and troubleshooting

**Deferred to v2**: Health monitoring (gastown-style zombie/hung detection), multi-session broadcast/coordination, dtach backend

---

## Next Steps

After questions are resolved:

1. Update "Resolution" fields in Questions section
2. Finalize Goals section (remove/add goals based on MVP scope decision)
3. Proceed to RT-ICA assessment
4. Then proceed to architecture design via `@python3-development:python-cli-design-spec`
