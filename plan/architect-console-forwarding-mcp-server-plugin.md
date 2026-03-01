# Architecture Spec: Console Forwarding MCP Server Plugin

## Document Metadata

- **Generated**: 2026-03-01
- **Feature**: Console Forwarding MCP Server Plugin
- **GitHub Issue**: #364
- **Input**: [plan/feature-context-console-forwarding-mcp-server-plugin.md](./feature-context-console-forwarding-mcp-server-plugin.md)
- **Reference Implementation**: [plugins/agentskill-kaizen/mcp/server.py](../plugins/agentskill-kaizen/mcp/server.py)
- **Codebase Patterns**: [plan/codebase/plugin-mcp-patterns.md](./codebase/plugin-mcp-patterns.md)

---

## Executive Summary

This architecture defines a Claude Code plugin that exposes terminal session management as MCP tools via a FastMCP server. It enables Claude Code sessions to discover, read from, write to, and manage tmux sessions on local and remote (SSH) hosts. The server uses a backend abstraction to dispatch tool calls to either a local tmux backend (libtmux, sync-wrapped-in-async) or a remote SSH backend (asyncssh, natively async), with graceful degradation when tmux is not installed.

MVP scope: session discovery, pane output capture, keystroke injection, session lifecycle (create/kill), and remote SSH access. Health monitoring, multi-session broadcast, and dtach backend are deferred to v2.

---

## Plugin Directory Structure

```text
plugins/console-forwarding/
+-- .claude-plugin/
|   +-- plugin.json              # Plugin manifest with mcpServers declaration
+-- mcp/
|   +-- server.py                # FastMCP entry point (PEP 723 inline script metadata)
|   +-- backends/
|   |   +-- __init__.py          # Backend protocol definition + registry
|   |   +-- tmux_backend.py      # libtmux-based local tmux backend
|   |   +-- ssh_backend.py       # asyncssh-based remote SSH backend
|   +-- models.py                # Pydantic data models for tool inputs/outputs
|   +-- session_manager.py       # Backend registry, dispatch, connection pooling
|   +-- errors.py                # Error hierarchy and ToolError wrappers
+-- skills/
|   +-- console-forwarding/
|       +-- SKILL.md             # User-facing skill: session naming, SSH setup, troubleshooting
+-- tests/
|   +-- conftest.py              # FastMCP stub, libtmux fixtures, asyncssh mocks
|   +-- test_server.py           # MCP tool integration tests
|   +-- test_tmux_backend.py     # Tmux backend unit tests (libtmux fixtures)
|   +-- test_ssh_backend.py      # SSH backend unit tests (asyncssh mocks)
|   +-- test_session_manager.py  # Session manager dispatch and registry tests
|   +-- test_models.py           # Data model validation tests
```

### File Purposes

| File | Purpose |
|------|---------|
| `plugin.json` | Claude Code plugin manifest; declares `console-forwarding` MCP server using `uv run --script` |
| `server.py` | PEP 723 entry point; declares dependencies inline; registers MCP tools; calls `mcp.run()` |
| `backends/__init__.py` | Defines `SessionBackend` Protocol; exports `BackendRegistry` |
| `backends/tmux_backend.py` | Implements `SessionBackend` using libtmux; all methods sync, wrapped by session manager |
| `backends/ssh_backend.py` | Implements `SessionBackend` using asyncssh; all methods natively async |
| `models.py` | Pydantic models: `SessionInfo`, `PaneOutput`, `SessionCreateRequest`, `SendKeysRequest` |
| `session_manager.py` | Resolves backend from host parameter; manages SSH connection pool; dispatches tool calls |
| `errors.py` | `ConsoleForwardingError` base; subclasses for backend-specific errors; `ToolError` conversion |
| `SKILL.md` | User-facing documentation: session naming conventions, SSH URI format, troubleshooting |

---

## PEP 723 Inline Script Metadata

`mcp/server.py` uses the PEP 723 inline script metadata block. Backend modules in `mcp/backends/` are plain Python files imported by `server.py` -- they do not need their own dependency declarations because `uv run --script server.py` installs all dependencies before execution.

```python
#!/usr/bin/env -S uv --quiet run --active --script
# /// script
# requires-python = ">=3.11,<3.14"
# dependencies = [
#     "fastmcp>=3.0.0rc1,<4",
#     "libtmux==0.53.*",
#     "asyncssh>=2.22.0,<3",
#     "pydantic>=2.0.0",
# ]
# ///
```

### Dependency Justification

| Dependency | Version | Purpose |
|------------|---------|---------|
| `fastmcp` | `>=3.0.0rc1,<4` | MCP server framework; matches codebase convention |
| `libtmux` | `==0.53.*` | Typed tmux API; pinned per upstream pre-1.0 recommendation |
| `asyncssh` | `>=2.22.0,<3` | Async SSH client for remote session operations |
| `pydantic` | `>=2.0.0` | Data model validation; already a FastMCP transitive dep |

### Runtime System Dependencies

| Binary | Required For | Detection |
|--------|-------------|-----------|
| `tmux` >= 3.2a | Local tmux backend | `shutil.which("tmux")` at startup |
| SSH agent or `~/.ssh/` keys | Remote SSH backend | Connection-time validation |

---

## plugin.json

```json
{
  "name": "console-forwarding",
  "version": "0.1.0",
  "description": "MCP server for cross-session terminal communication via tmux (local) and SSH (remote)",
  "author": {
    "name": "Jamie Nelson",
    "url": "https://github.com/Jamie-BitFlight"
  },
  "license": "MIT",
  "keywords": [
    "console-forwarding",
    "tmux",
    "ssh",
    "session-management",
    "multi-agent"
  ],
  "mcpServers": {
    "console-forwarding": {
      "command": "uv",
      "args": ["run", "--script", "${CLAUDE_PLUGIN_ROOT}/mcp/server.py"]
    }
  }
}
```

---

## MCP Tool API

### Tool Annotation Constants

```python
_READONLY_ANNOTATIONS: dict[str, bool] = {
    "readOnlyHint": True,
    "destructiveHint": False,
    "idempotentHint": True,
    "openWorldHint": False,
}

_MUTATING_ANNOTATIONS: dict[str, bool] = {
    "readOnlyHint": False,
    "destructiveHint": False,
    "idempotentHint": True,
    "openWorldHint": False,
}

_DESTRUCTIVE_ANNOTATIONS: dict[str, bool] = {
    "readOnlyHint": False,
    "destructiveHint": True,
    "idempotentHint": False,
    "openWorldHint": False,
}
```

### Tool: `list_sessions`

**Purpose**: Discover running tmux sessions on local or remote host.

**Parameters**:

| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `host` | `str \| None` | No | `None` | SSH URI (`ssh://user@host:port`). `None` = local. |

**Return Schema**:

```python
{
    "sessions": [
        {
            "name": str,            # Session name
            "id": str,              # Tmux session ID ($N)
            "windows": int,         # Window count
            "created": str,         # ISO timestamp
            "attached": bool,       # Whether a client is attached
            "width": int,           # Session width in columns
            "height": int,          # Session height in rows
        }
    ],
    "count": int,
    "host": str | None              # Echoes back the host parameter
}
```

**Annotations**: `_READONLY_ANNOTATIONS`

**Description**:

```text
List running tmux sessions on local host or remote host via SSH.

Returns: {"sessions": [...], "count": int, "host": str|null}.
Each session includes name, id, window count, dimensions, and attached state.

For remote hosts, provide SSH URI: host="ssh://user@hostname:port".
Keys resolved from SSH agent or ~/.ssh/. Port defaults to 22 if omitted.
```

---

### Tool: `list_windows`

**Purpose**: List windows within a specific tmux session.

**Parameters**:

| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `session` | `str` | Yes | -- | Session name or ID |
| `host` | `str \| None` | No | `None` | SSH URI for remote host |

**Return Schema**:

```python
{
    "windows": [
        {
            "name": str,           # Window name
            "id": str,             # Tmux window ID (@N)
            "index": int,          # Window index
            "panes": int,          # Pane count
            "active": bool,        # Whether this is the active window
            "width": int,          # Window width in columns
            "height": int,         # Window height in rows
        }
    ],
    "count": int,
    "session": str,
    "host": str | None
}
```

**Annotations**: `_READONLY_ANNOTATIONS`

**Description**:

```text
List windows in a tmux session.

Returns: {"windows": [...], "count": int, "session": str}.
Each window includes name, id, index, pane count, active flag, and dimensions.
```

---

### Tool: `list_panes`

**Purpose**: List panes within a specific tmux window.

**Parameters**:

| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `session` | `str` | Yes | -- | Session name or ID |
| `window` | `str \| None` | No | `None` | Window name or index. `None` = active window. |
| `host` | `str \| None` | No | `None` | SSH URI for remote host |

**Return Schema**:

```python
{
    "panes": [
        {
            "id": str,             # Tmux pane ID (%N)
            "index": int,          # Pane index within window
            "width": int,          # Pane width in columns
            "height": int,         # Pane height in rows
            "active": bool,        # Whether this is the active pane
            "current_command": str, # Currently running command
            "current_path": str,   # Current working directory
        }
    ],
    "count": int,
    "session": str,
    "window": str | None,
    "host": str | None
}
```

**Annotations**: `_READONLY_ANNOTATIONS`

**Description**:

```text
List panes in a tmux window.

Returns: {"panes": [...], "count": int, "session": str, "window": str|null}.
Each pane includes id, index, dimensions, active state, running command, and cwd.
If window is omitted, lists panes in the active window.
```

---

### Tool: `capture_pane`

**Purpose**: Read terminal output from a tmux pane.

**Parameters**:

| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `session` | `str` | Yes | -- | Session name or ID |
| `pane` | `str \| None` | No | `None` | Pane ID (%N) or index. `None` = active pane. |
| `window` | `str \| None` | No | `None` | Window name or index. `None` = active window. |
| `lines` | `int \| None` | No | `None` | Number of lines to capture from end. `None` = full visible pane. |
| `offset` | `int` | No | `0` | Lines to skip from the start of captured output (for pagination). |
| `host` | `str \| None` | No | `None` | SSH URI for remote host |

**Return Schema**:

```python
{
    "output": str,                # Captured pane content (newline-joined)
    "line_count": int,            # Number of lines returned
    "total_lines": int,           # Total lines available before offset/limit
    "offset": int,                # Echoes back offset
    "session": str,
    "pane": str,                  # Resolved pane ID
    "host": str | None
}
```

**Annotations**: `_READONLY_ANNOTATIONS`

**Description**:

```text
Capture terminal output from a tmux pane.

Returns: {"output": str, "line_count": int, "total_lines": int, ...}.
output is the captured text with lines joined by newlines.

Pagination: use lines and offset parameters to control the capture window.
lines=50 captures the last 50 lines. offset=10 skips the first 10 of those.
Omit lines for full visible pane content (no artificial truncation).

Warning: MCP output tokens are limited (warn at 10K, max 25K). For large
panes, use lines parameter to limit output size.
```

---

### Tool: `send_keys`

**Purpose**: Send keystrokes to a tmux pane.

**Parameters**:

| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `session` | `str` | Yes | -- | Session name or ID |
| `keys` | `str` | Yes | -- | Keys to send. Include `\n` for Enter. |
| `pane` | `str \| None` | No | `None` | Pane ID or index. `None` = active pane. |
| `window` | `str \| None` | No | `None` | Window name or index. `None` = active window. |
| `enter` | `bool` | No | `True` | Whether to press Enter after the keys. |
| `literal` | `bool` | No | `False` | Send keys literally (bypass tmux key bindings). |
| `host` | `str \| None` | No | `None` | SSH URI for remote host |

**Return Schema**:

```python
{
    "sent": True,
    "keys": str,                  # Echoes back the keys sent
    "session": str,
    "pane": str,                  # Resolved pane ID
    "host": str | None
}
```

**Annotations**: `_MUTATING_ANNOTATIONS`

**Description**:

```text
Send keystrokes to a tmux pane.

Returns: {"sent": true, "keys": str, "session": str, "pane": str}.

Side effects: Injects keystrokes into the target pane's terminal. The pane's
running process receives the input as if typed by a user.

enter=True (default) appends Enter after keys. Set enter=False for partial input.
literal=True sends keys literally, bypassing tmux key binding interpretation.

Example: send_keys(session="agent-1", keys="yes") sends "yes" + Enter.
```

---

### Tool: `create_session`

**Purpose**: Create a new tmux session.

**Parameters**:

| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `name` | `str` | Yes | -- | Session name (must be unique) |
| `command` | `str \| None` | No | `None` | Initial command to run in the session |
| `width` | `int` | No | `220` | Session width in columns |
| `height` | `int` | No | `50` | Session height in rows |
| `start_directory` | `str \| None` | No | `None` | Working directory for the session |
| `environment` | `dict[str, str] \| None` | No | `None` | Environment variables to set |
| `host` | `str \| None` | No | `None` | SSH URI for remote host |

**Return Schema**:

```python
{
    "created": True,
    "session": {
        "name": str,
        "id": str,
        "width": int,
        "height": int,
    },
    "host": str | None
}
```

**Annotations**: `_MUTATING_ANNOTATIONS`

**Description**:

```text
Create a new tmux session.

Returns: {"created": true, "session": {...}, "host": str|null}.

Side effects: Creates a new detached tmux session. The session persists until
explicitly killed or the tmux server exits.

Width and height default to 220x50 (suitable for headless/TTY-less environments).
If command is provided, it runs as the initial process in the session's first pane.

Errors: SessionAlreadyExists if name is already taken.
```

---

### Tool: `kill_session`

**Purpose**: Kill (destroy) a tmux session.

**Parameters**:

| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `session` | `str` | Yes | -- | Session name or ID |
| `host` | `str \| None` | No | `None` | SSH URI for remote host |

**Return Schema**:

```python
{
    "killed": True,
    "session": str,
    "host": str | None
}
```

**Annotations**: `_DESTRUCTIVE_ANNOTATIONS`

**Description**:

```text
Kill a tmux session and all its windows/panes.

Returns: {"killed": true, "session": str}.

Side effects: Terminates all processes running in the session. This is
destructive and irreversible. All unsaved state in the session is lost.

Errors: SessionNotFound if session does not exist.
```

---

## Backend Abstraction

### SessionBackend Protocol

The `SessionBackend` Protocol defines the contract that all backends must satisfy. The tmux backend implements synchronous methods (wrapped by the session manager in `asyncio.to_thread`). The SSH backend implements async methods natively.

**Protocol Definition** (in `backends/__init__.py`):

```python
class SessionBackend(Protocol):
    """Contract for terminal session backends.

    Implementations may be synchronous (tmux) or asynchronous (SSH).
    The session manager handles async wrapping for sync backends.
    """

    @property
    def name(self) -> str: ...

    @property
    def is_available(self) -> bool: ...

    @property
    def is_async(self) -> bool: ...

    # Discovery
    def list_sessions(self) -> list[SessionInfo]: ...
    def list_windows(self, session: str) -> list[WindowInfo]: ...
    def list_panes(self, session: str, window: str | None) -> list[PaneInfo]: ...

    # Capture
    def capture_pane(
        self,
        session: str,
        pane: str | None,
        window: str | None,
        lines: int | None,
    ) -> PaneOutput: ...

    # Input
    def send_keys(
        self,
        session: str,
        keys: str,
        pane: str | None,
        window: str | None,
        enter: bool,
        literal: bool,
    ) -> None: ...

    # Lifecycle
    def create_session(
        self,
        name: str,
        command: str | None,
        width: int,
        height: int,
        start_directory: str | None,
        environment: dict[str, str] | None,
    ) -> SessionInfo: ...

    def kill_session(self, session: str) -> None: ...
```

### Async Wrapping Strategy

The session manager handles the impedance mismatch between sync and async backends:

```text
Tool call (async)
    |
    v
SessionManager.dispatch()
    |
    +-- host is None --> TmuxBackend (sync)
    |       |
    |       +-- asyncio.to_thread(backend.method, args)
    |
    +-- host is SSH URI --> SSHBackend (async)
            |
            +-- await backend.method_async(args)
```

**Tmux Backend**: All libtmux operations are synchronous (subprocess-based `tmux_cmd()`). Every backend method call is wrapped in `asyncio.to_thread()` by the session manager.

**SSH Backend**: All asyncssh operations are natively async. The session manager calls backend methods directly with `await`. The SSH backend internally runs tmux commands on the remote host via `conn.run("tmux ...")` and parses their output.

### Backend Detection

At server startup, the session manager probes for available backends:

1. **Tmux**: `shutil.which("tmux")` returns a path --> tmux backend is available
2. **SSH**: Always available (asyncssh is a Python dependency, not a system binary)

If tmux is not available, the server still starts but local-only tools raise `ToolError("tmux is not installed. Install tmux >= 3.2a for local session management. Remote SSH tools are available.")`.

### Backend Registry

```text
BackendRegistry
    |
    +-- "local" --> TmuxBackend instance (or None if tmux not found)
    +-- SSH URI --> SSHBackend instance (created on demand, connection pooled)
```

---

## Session Manager

The session manager is the central dispatch layer between MCP tools and backends.

### Responsibilities

1. **Backend resolution**: Parse `host` parameter to determine backend (local vs SSH)
2. **Async wrapping**: Wrap sync backend calls in `asyncio.to_thread()`
3. **SSH connection pooling**: Reuse asyncssh connections per host URI
4. **Error conversion**: Convert backend-specific exceptions to `ToolError`
5. **Availability enforcement**: Return clear errors when a backend is unavailable

### SSH URI Parsing

Format: `ssh://user@hostname:port` (port optional, defaults to 22)

Parsing produces:

```python
@dataclass(frozen=True)
class SSHTarget:
    user: str
    hostname: str
    port: int = 22
```

Validation rules:

- Scheme must be `ssh://`
- User is required
- Hostname is required
- Port must be 1-65535 if specified
- Invalid URIs raise `ToolError` with the expected format

### Connection Pool

The session manager maintains a dict of active asyncssh connections keyed by `SSHTarget`:

```text
_connections: dict[SSHTarget, SSHClientConnection]
```

**Lifecycle**:

- Connections are created on first use for a given `SSHTarget`
- Connections are reused for subsequent tool calls to the same host
- Connections are closed when the MCP server shuts down (via `atexit` or `finally` in `mcp.run()`)
- If a connection is dead (closed by remote), the pool detects this and creates a new one

**Connection Parameters**:

- `known_hosts=None` is NOT acceptable for production. Use `known_hosts="~/.ssh/known_hosts"` by default.
- Keys resolved from SSH agent first, then `~/.ssh/id_ed25519`, `~/.ssh/id_rsa` (asyncssh default behavior)
- Connection timeout: 10 seconds (configurable via module constant)

---

## SSH Backend: Remote Command Model

The SSH backend runs tmux commands on the remote host via `conn.run()` and parses their output. It does NOT use libtmux remotely -- libtmux requires a local tmux socket.

### Command Execution Pattern

For each backend method, the SSH backend:

1. Obtains (or creates) an asyncssh connection from the pool
2. Runs a tmux CLI command via `await conn.run("tmux ...")`
3. Parses the stdout using tmux format strings (`-F`) for structured output
4. Returns typed model objects

### Remote tmux Commands

| Backend Method | Remote Command |
|---------------|----------------|
| `list_sessions` | `tmux list-sessions -F "#{session_name}\t#{session_id}\t#{session_windows}\t#{session_created}\t#{session_attached}\t#{session_width}\t#{session_height}"` |
| `list_windows` | `tmux list-windows -t {session} -F "#{window_name}\t#{window_id}\t#{window_index}\t#{window_panes}\t#{window_active}\t#{window_width}\t#{window_height}"` |
| `list_panes` | `tmux list-panes -t {session}:{window} -F "#{pane_id}\t#{pane_index}\t#{pane_width}\t#{pane_height}\t#{pane_active}\t#{pane_current_command}\t#{pane_current_path}"` |
| `capture_pane` | `tmux capture-pane -t {session}:{window}.{pane} -p [-S {start}]` |
| `send_keys` | `tmux send-keys -t {session}:{window}.{pane} [-l] {keys} [Enter]` |
| `create_session` | `tmux new-session -d -s {name} -x {width} -y {height} [-c {dir}] [{command}]` |
| `kill_session` | `tmux kill-session -t {session}` |

### Shell Injection Prevention

All tmux arguments passed via `conn.run()` must be shell-escaped. The SSH backend uses `shlex.quote()` on all user-provided values (session names, keys, paths) before interpolating them into command strings.

---

## Data Models

All models use Pydantic v2 for validation and serialization.

### SessionInfo

```python
class SessionInfo(BaseModel):
    name: str
    id: str
    windows: int
    created: str          # ISO timestamp
    attached: bool
    width: int
    height: int
```

### WindowInfo

```python
class WindowInfo(BaseModel):
    name: str
    id: str
    index: int
    panes: int
    active: bool
    width: int
    height: int
```

### PaneInfo

```python
class PaneInfo(BaseModel):
    id: str
    index: int
    width: int
    height: int
    active: bool
    current_command: str
    current_path: str
```

### PaneOutput

```python
class PaneOutput(BaseModel):
    output: str           # Newline-joined captured lines
    line_count: int       # Lines returned after offset/limit
    total_lines: int      # Total lines before offset/limit
    offset: int
    session: str
    pane: str             # Resolved pane ID
```

### SSHTarget

```python
class SSHTarget(BaseModel, frozen=True):
    user: str
    hostname: str
    port: int = 22
```

---

## Error Handling

### Exception Hierarchy

```text
ConsoleForwardingError (base)
+-- BackendNotAvailableError     # tmux not installed, SSH connection failed
+-- SessionNotFoundError         # Session name/ID does not exist
+-- SessionAlreadyExistsError   # create_session with duplicate name
+-- PaneNotFoundError            # Pane ID/index does not exist
+-- WindowNotFoundError          # Window name/index does not exist
+-- SSHConnectionError           # SSH connection/auth failure
+-- SSHCommandError              # Remote command returned non-zero exit
+-- InvalidURIError              # Malformed SSH URI
```

### ToolError Conversion

All backend exceptions are caught at the session manager layer and converted to `ToolError` with actionable messages:

```text
Backend raises SessionNotFoundError("agent-3")
    --> ToolError("Session 'agent-3' not found. Use list_sessions() to see available sessions.")

Backend raises BackendNotAvailableError("tmux")
    --> ToolError("tmux is not installed. Install tmux >= 3.2a for local sessions. Remote SSH sessions are available via host parameter.")

Backend raises SSHConnectionError(host, reason)
    --> ToolError("SSH connection to ssh://user@host:22 failed: {reason}. Check SSH keys and host availability.")
```

### Graceful Degradation

When tmux is not installed:

1. Server starts successfully
2. `list_sessions()` with `host=None` returns `ToolError` explaining tmux is not available
3. `list_sessions(host="ssh://...")` works normally via SSH backend
4. All local-only tools return the same `ToolError` with installation guidance
5. SSH-based tools function independently

---

## Server Architecture

### FastMCP Instance

```python
mcp = FastMCP("console-forwarding", mask_error_details=False)
```

### Startup Sequence

```text
1. Import backends
2. Detect available backends (shutil.which("tmux"))
3. Initialize BackendRegistry with detected backends
4. Initialize SessionManager with BackendRegistry
5. Register MCP tools
6. mcp.run() -- starts stdio transport
```

### Tool Registration Pattern

Each tool is a thin async function that:

1. Validates parameters via Pydantic models (implicit via FastMCP type hints)
2. Calls `session_manager.dispatch(method, host, **kwargs)`
3. Returns a dict matching the documented return schema

```text
@mcp.tool(annotations=_READONLY_ANNOTATIONS)
async def list_sessions(host: str | None = None) -> dict[str, Any]:
    """..."""
    # session_manager handles backend resolution and async wrapping
```

### Module-Level Constants

```python
_DEFAULT_SESSION_WIDTH: int = 220
_DEFAULT_SESSION_HEIGHT: int = 50
_SSH_CONNECT_TIMEOUT: int = 10
_TMUX_MIN_VERSION: str = "3.2a"
```

---

## Testing Strategy

### Test Dependencies

```text
pytest >= 8.0.0
pytest-asyncio >= 0.24.0
pytest-mock >= 3.14.0
libtmux == 0.53.*      # Provides pytest fixtures: server, session, window, pane
```

### Tmux Backend Tests (`test_tmux_backend.py`)

**Approach**: Use libtmux's built-in pytest fixtures for isolated tmux testing.

**Fixtures Available** (auto-discovered via libtmux's pytest plugin):

- `server`: Isolated tmux server on a temporary socket
- `session`: Fresh session within isolated server
- `window`: Active window in fresh session
- `pane`: Active pane in fresh window

**Test Categories**:

1. **Discovery**: Verify `list_sessions`, `list_windows`, `list_panes` return correct data from real tmux sessions
2. **Capture**: Verify `capture_pane` returns expected output after `send_keys`
3. **Send Keys**: Verify keystrokes arrive in the pane (check via `capture_pane`)
4. **Lifecycle**: Verify `create_session` creates and `kill_session` destroys sessions
5. **Error Paths**: Verify correct exceptions for non-existent sessions/panes

**Markers**: `@pytest.mark.integration` (requires tmux binary)

### SSH Backend Tests (`test_ssh_backend.py`)

**Approach**: Mock asyncssh at the connection level. No real SSH connections in unit tests.

**Mocking Strategy**:

- Mock `asyncssh.connect()` to return a mock `SSHClientConnection`
- Mock `conn.run()` to return `SSHCompletedProcess` with pre-defined stdout
- Test parsing of tmux format-string output from remote commands
- Test shell escaping of user-provided values

**Test Categories**:

1. **Connection**: Verify connection creation with correct parameters
2. **Command Execution**: Verify correct tmux commands are built and sent
3. **Output Parsing**: Verify tmux format-string output is correctly parsed into models
4. **Shell Escaping**: Verify `shlex.quote()` is applied to all user inputs
5. **Error Handling**: Verify SSH errors convert to correct exception types
6. **Connection Reuse**: Verify pool returns existing connection for same host

### MCP Tool Tests (`test_server.py`)

**Approach**: Use the FastMCP stub pattern from kaizen tests (`conftest.py`). Test tools as plain async functions.

**Pattern**:

1. Stub FastMCP before importing `server.py` (makes `@mcp.tool` a no-op)
2. Mock `session_manager` to return pre-defined model objects
3. Call tool functions directly with `await`
4. Assert return dict matches expected schema

**Test Categories**:

1. **Happy Path**: Each tool returns expected dict structure
2. **Parameter Validation**: Missing required params, invalid types
3. **Host Routing**: `host=None` routes to tmux, `host="ssh://..."` routes to SSH
4. **Error Propagation**: Backend errors surface as `ToolError`
5. **Graceful Degradation**: Tools with `host=None` when tmux unavailable

### Session Manager Tests (`test_session_manager.py`)

**Test Categories**:

1. **Backend Resolution**: `None` host resolves to tmux, SSH URI resolves to SSH
2. **Async Wrapping**: Sync backend methods wrapped in `asyncio.to_thread()`
3. **Connection Pool**: Connections reused, dead connections replaced
4. **URI Parsing**: Valid and invalid SSH URIs
5. **Availability Check**: Correct error when tmux unavailable

### conftest.py Structure

**Key Fixtures**:

- `mock_tmux_backend`: Mock implementing `SessionBackend` with pre-defined returns
- `mock_ssh_backend`: Async mock implementing `SessionBackend`
- `session_manager`: SessionManager with mocked backends
- `mock_context`: AsyncMock for FastMCP `Context` parameter
- `sample_session_info`: Pre-built `SessionInfo` for assertions
- `sample_pane_output`: Pre-built `PaneOutput` for assertions

---

## Security Considerations

### Command Injection Prevention

- **Local tmux**: libtmux uses structured API calls, not shell strings. No injection risk.
- **Remote SSH**: All user-provided values (session names, keys, paths) are shell-escaped with `shlex.quote()` before being interpolated into remote tmux commands.
- **No `shell=True`**: Neither `subprocess.run()` nor any shell-mode execution is used anywhere.

### SSH Key Handling

- Keys are resolved by asyncssh from SSH agent or `~/.ssh/` -- never stored or logged by the server
- No password authentication -- keys only
- `known_hosts` defaults to `~/.ssh/known_hosts` -- not disabled
- SSH URIs in tool responses echo back the URI but never include key material

### Input Validation

- Session names validated against tmux naming rules (no periods, colons, or exclamation marks)
- SSH URIs validated against the documented format before connection attempt
- Pane/window identifiers validated as valid tmux target syntax
- All parameters type-checked by Pydantic via FastMCP

### Information Exposure

- Error messages include session names and host URIs (necessary for debugging) but never include key material, passwords, or full stack traces
- `mask_error_details=False` on FastMCP exposes full `ToolError` messages to the MCP client, which is appropriate for developer-facing agent tools

---

## Output Pagination Design

Following the CLAUDE.md "No Invented Limits" rule, `capture_pane` provides caller-controlled pagination:

- `lines`: Controls how many lines to capture from the end of the pane's scrollback. `None` captures the full visible pane.
- `offset`: Skips the first N lines of the captured output. Used for paginating through large captures.
- `total_lines`: Always returned, so the caller knows how much content is available.

No artificial truncation is applied. The tool description warns about MCP output token limits (10K warning, 25K max) and advises callers to use the `lines` parameter for large panes.

---

## Deferred to v2

The following are explicitly excluded from the MVP architecture and will be designed separately:

1. **Health monitoring**: `check_session_health()` tool -- stateless, single-call zombie/hung detection (gastown Witness pattern)
2. **Multi-session broadcast**: `broadcast_keys()` tool -- fan-out keystroke injection with aggregated results
3. **dtach backend**: Lightweight session backend supporting create/kill/send but not capture
4. **Session filtering**: Glob-pattern filtering on `list_sessions()` (e.g., `pattern="agent-*"`)
5. **Output streaming**: MCP resource-based pane output streaming (requires SSE transport)

---

## Architectural Decisions

### ADR-001: Protocol over ABC for Backend Interface

**Decision**: Use `typing.Protocol` (structural typing) instead of `abc.ABC` (nominal typing) for `SessionBackend`.

**Rationale**: The tmux and SSH backends have fundamentally different execution models (sync vs async). A Protocol defines the contract without forcing a shared base class. This enables type checking with duck typing -- any class implementing the required methods satisfies the Protocol without explicit inheritance.

### ADR-002: Session Manager as Async Wrapper

**Decision**: The session manager, not the backends themselves, is responsible for `asyncio.to_thread()` wrapping.

**Rationale**: The tmux backend should be a pure synchronous library wrapper (testable without asyncio). The SSH backend should be natively async (no unnecessary thread overhead). The session manager knows which backend is sync vs async (`backend.is_async` property) and applies the correct calling convention.

### ADR-003: SSH Backend Uses tmux CLI, Not libtmux

**Decision**: The SSH backend runs `tmux` CLI commands on the remote host via `conn.run()` rather than attempting to use libtmux over SSH.

**Rationale**: libtmux operates on a local tmux socket. There is no mechanism to point libtmux at a remote tmux server over SSH. The tmux CLI with format strings (`-F`) provides structured output that can be parsed remotely. This is the same approach tmux itself uses for remote session management.

### ADR-004: PEP 723 with Local Module Imports

**Decision**: Use PEP 723 inline script metadata on `server.py` only; backends and models are plain `.py` files imported as local modules.

**Rationale**: `uv run --script server.py` installs PEP 723 dependencies, then Python's import system resolves local imports normally. This avoids a full `pyproject.toml` package while keeping the codebase modular. The kaizen server is a single file because its scope is smaller; the console forwarding server with 2 backends and a session manager benefits from multi-file organization.

### ADR-005: Connection Pooling in Session Manager

**Decision**: SSH connections are pooled in the session manager, not in the SSH backend.

**Rationale**: The session manager owns the lifecycle of all backend interactions. Pooling at this level enables cross-tool connection reuse (a `list_sessions` call and a subsequent `capture_pane` call to the same host share one SSH connection). The session manager can also implement cleanup on server shutdown.

### ADR-006: No Background Threads or Daemons

**Decision**: All operations are request-response. No background polling, no persistent watchers, no daemon threads.

**Rationale**: MCP tools are request-response by design. The MCP server runs as a stdio subprocess of Claude Code -- adding background threads complicates shutdown, error handling, and resource management. Health monitoring (deferred to v2) will be a single-call stateless check, not a patrol loop.
