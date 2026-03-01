---
description: "Executable task plan for the Console Forwarding MCP Server Plugin (GitHub #364)"
version: "1.0"
feature: "console-forwarding-mcp-server-plugin"
github_issue: 364
plugin_location: "plugins/console-forwarding/"
tasks:
  - T1.1: Plugin scaffold — directory structure and plugin.json
  - T2.1: Data models and error hierarchy
  - T3.1: Backend protocol and registry
  - T4.1: Tmux backend implementation
  - T5.1: SSH backend implementation
  - T6.1: Session manager — dispatch, pooling, async wrapping
  - T7.1: MCP server — FastMCP tools wiring
  - T8.1: Test fixtures — conftest.py
  - T8.2: Data model tests
  - T8.3: Tmux backend tests
  - T8.4: SSH backend tests
  - T8.5: Session manager tests
  - T8.6: MCP tool integration tests
  - T9.1: SKILL.md for console-forwarding skill
  - T10.1: Plugin validation and lint fixes
task_exports:
  enabled: false
  directory: "TASK"
---

# Task Plan: Console Forwarding MCP Server Plugin

**GitHub Issue**: #364
**Architecture Spec**: [plan/architect-console-forwarding-mcp-server-plugin.md](./architect-console-forwarding-mcp-server-plugin.md)
**Feature Context**: [plan/feature-context-console-forwarding-mcp-server-plugin.md](./feature-context-console-forwarding-mcp-server-plugin.md)
**Codebase Patterns**: [plan/codebase/plugin-mcp-patterns.md](./codebase/plugin-mcp-patterns.md)
**Reference Server**: `plugins/agentskill-kaizen/mcp/server.py`

---

## Dependency Graph

```text
T1.1 (scaffold)
  |
  +---> T2.1 (models + errors)
          |
          +---> T3.1 (backend protocol)
                  |
                  +---> T4.1 (tmux backend) --------+
                  |                                  |
                  +---> T5.1 (ssh backend) ----------+
                                                     |
                                               T6.1 (session manager)
                                                     |
                                               T7.1 (MCP server)
                                                     |
                  T8.1 (conftest) <------------------+
                  |    |                             |
                  |    +---> T8.2 (model tests)      |
                  |    +---> T8.3 (tmux tests) <-T4.1|
                  |    +---> T8.4 (ssh tests) <--T5.1|
                  |    +---> T8.5 (mgr tests) <-T6.1 |
                  |    +---> T8.6 (server tests) <---+
                  |
                  +---> T9.1 (SKILL.md)
                  +---> T10.1 (validation)
```

## Parallelization Map

| Priority Wave | Tasks | Can Run Concurrently |
|--------------|-------|----------------------|
| 1 | T1.1 | No parallel candidates |
| 2 | T2.1 | No parallel candidates |
| 3 | T3.1 | No parallel candidates |
| 4 | T4.1, T5.1 | YES — no shared files |
| 5 | T6.1 | Waits for T4.1 + T5.1 |
| 6 | T7.1 | Waits for T6.1 |
| 7 | T8.1 | Waits for T7.1 |
| 8 | T8.2, T8.3, T8.4, T8.5, T8.6 | YES — each touches a distinct test file |
| 9 | T9.1, T10.1 | YES — no shared files |

---

## SYNC CHECKPOINT 1: Foundation Complete

**Convergence**: T1.1 + T2.1 + T3.1

**Quality gates**:

- `plugins/console-forwarding/.claude-plugin/plugin.json` is valid JSON with required `name` field
- `plugins/console-forwarding/mcp/models.py` imports cleanly (`python -c "import sys; sys.path.insert(0, 'plugins/console-forwarding/mcp'); import models"`)
- `plugins/console-forwarding/mcp/errors.py` imports cleanly
- `plugins/console-forwarding/mcp/backends/__init__.py` defines `SessionBackend` Protocol and `BackendRegistry`
- `uv run plugins/plugin-creator/scripts/plugin_validator.py plugins/console-forwarding` exits 0 or reports only expected warnings

**Reflection questions**:

- Are Pydantic models complete for all tool return schemas in the architecture spec?
- Does the `SessionBackend` Protocol cover all methods needed by tmux and SSH backends?
- Does `BackendRegistry` have the right interface for the session manager to consume?

**Proceed to Priority 4 only after approval.**

---

## SYNC CHECKPOINT 2: Backends Complete

**Convergence**: T4.1 + T5.1

**Quality gates**:

- Both backend modules import cleanly
- `TmuxBackend` satisfies `SessionBackend` Protocol (no `mypy` or `pyright` errors if run)
- `SSHBackend` satisfies `SessionBackend` Protocol
- `TmuxBackend.is_async` returns `False`
- `SSHBackend.is_async` returns `True`
- All tmux remote commands in `SSHBackend` use `shlex.quote()` on user-supplied values

**Proceed to Priority 5 only after approval.**

---

## SYNC CHECKPOINT 3: Server Complete

**Convergence**: T6.1 + T7.1

**Quality gates**:

- `uv run --script plugins/console-forwarding/mcp/server.py --help` or equivalent exits without import error
- All 7 MCP tools are defined: `list_sessions`, `list_windows`, `list_panes`, `capture_pane`, `send_keys`, `create_session`, `kill_session`
- Read-only tools have `_READONLY_ANNOTATIONS`, mutating tools `_MUTATING_ANNOTATIONS`, kill_session `_DESTRUCTIVE_ANNOTATIONS`
- Session manager connection pool closes on server shutdown

**Proceed to Priority 7 only after approval.**

---

## SYNC CHECKPOINT 4: Tests and Docs Complete

**Convergence**: T8.2 + T8.3 + T8.4 + T8.5 + T8.6 + T9.1 + T10.1

**Quality gates**:

- `uv run pytest plugins/console-forwarding/tests/ -x -q --ignore=plugins/console-forwarding/tests/test_tmux_backend.py` exits 0 (non-integration tests)
- `uv run plugins/plugin-creator/scripts/plugin_validator.py plugins/console-forwarding` exits 0
- `uv run prek run --files plugins/console-forwarding/skills/console-forwarding/SKILL.md` exits 0
- SKILL.md passes SK006 token check (body under 4400 tokens)

---

## Task Details

---

## Task 1.1: Plugin Scaffold

**Status**: NOT STARTED
**Dependencies**: None
**Priority**: 1
**Complexity**: Low
**Agent**: python-cli-architect
**Skills**: ["python3-development"]

### Description

Create the full directory skeleton for the `plugins/console-forwarding/` plugin and populate `plugin.json`. This is the foundational scaffold on which all other tasks build.

Create these files and directories:

```text
plugins/console-forwarding/
    .claude-plugin/
        plugin.json
    mcp/
        __init__.py              (empty)
        backends/
            __init__.py          (placeholder — to be replaced by T3.1)
    skills/
        console-forwarding/
            SKILL.md             (placeholder — to be replaced by T9.1)
    tests/
        __init__.py              (empty)
    README.md                    (stub with title and one-line description only)
```

The `plugin.json` must be fully populated per the architecture spec. The `mcp/server.py` is NOT created here — it belongs to T7.1.

### Acceptance Criteria

1. `plugins/console-forwarding/.claude-plugin/plugin.json` exists and is valid JSON with fields: `name`, `version`, `description`, `author`, `license`, `keywords`, `mcpServers`
2. `mcpServers` entry uses `"command": "uv"` with `"args": ["run", "--script", "${CLAUDE_PLUGIN_ROOT}/mcp/server.py"]`
3. `uv run plugins/plugin-creator/scripts/plugin_validator.py plugins/console-forwarding` exits 0 (PL001-PL005 pass; PR002 for server.py not yet existing is acceptable and must be noted)
4. All directories listed in the directory skeleton exist
5. Empty `__init__.py` files are present where listed
6. Placeholder `SKILL.md` contains valid YAML frontmatter with at minimum `name` and `description` fields

### Verification Steps

1. `cat plugins/console-forwarding/.claude-plugin/plugin.json | python3 -c "import sys, json; d=json.load(sys.stdin); assert d['name']=='console-forwarding'; assert 'mcpServers' in d; print('OK')`
2. `uv run plugins/plugin-creator/scripts/plugin_validator.py plugins/console-forwarding` — report all output; PL001/PL002/PL003 must not appear
3. `find plugins/console-forwarding -type f | sort` — verify directory structure matches spec

---

## Task 2.1: Data Models and Error Hierarchy

**Status**: NOT STARTED
**Dependencies**: Task 1.1
**Priority**: 2
**Complexity**: Medium
**Agent**: python-cli-architect
**Skills**: ["python3-development"]

### Description

Implement `plugins/console-forwarding/mcp/models.py` and `plugins/console-forwarding/mcp/errors.py`.

These two files are pure Python with no external system dependencies beyond Pydantic. They form the shared data layer consumed by all other modules.

#### models.py

Implement all Pydantic v2 models as specified in the architecture spec "Data Models" section:

- `SessionInfo` — 7 fields: `name`, `id`, `windows`, `created`, `attached`, `width`, `height`
- `WindowInfo` — 7 fields: `name`, `id`, `index`, `panes`, `active`, `width`, `height`
- `PaneInfo` — 7 fields: `id`, `index`, `width`, `height`, `active`, `current_command`, `current_path`
- `PaneOutput` — 6 fields: `output`, `line_count`, `total_lines`, `offset`, `session`, `pane`
- `SSHTarget` — frozen model, 3 fields: `user`, `hostname`, `port` (default 22)

Add `model_config = ConfigDict(frozen=True)` to `SSHTarget` so it can be used as a dict key.

All string fields are `str`, bool fields are `bool`, int fields are `int`. No optional fields on these models.

#### errors.py

Implement the exception hierarchy as specified in the architecture spec "Error Handling" section:

```text
ConsoleForwardingError(Exception)          -- base
BackendNotAvailableError(ConsoleForwardingError)
SessionNotFoundError(ConsoleForwardingError)
SessionAlreadyExistsError(ConsoleForwardingError)
PaneNotFoundError(ConsoleForwardingError)
WindowNotFoundError(ConsoleForwardingError)
SSHConnectionError(ConsoleForwardingError)
SSHCommandError(ConsoleForwardingError)
InvalidURIError(ConsoleForwardingError)
```

Each exception class must accept a descriptive message string as its first argument. No additional fields required beyond the message.

### Acceptance Criteria

1. `models.py` defines exactly 5 classes: `SessionInfo`, `WindowInfo`, `PaneInfo`, `PaneOutput`, `SSHTarget`
2. All field names and types match the architecture spec exactly
3. `SSHTarget` is frozen (hashable, usable as dict key): `hash(SSHTarget(user="u", hostname="h", port=22))` does not raise
4. `errors.py` defines exactly 9 classes in the hierarchy rooted at `ConsoleForwardingError`
5. Both files import cleanly: `python3 -c "import sys; sys.path.insert(0, 'plugins/console-forwarding/mcp'); import models, errors"` exits 0
6. `uv run prek run --files plugins/console-forwarding/mcp/models.py plugins/console-forwarding/mcp/errors.py` exits 0

### Verification Steps

1. `python3 -c "import sys; sys.path.insert(0, 'plugins/console-forwarding/mcp'); import models; s = models.SessionInfo(name='s', id='$1', windows=1, created='2026-01-01T00:00:00', attached=False, width=220, height=50); print(s.model_dump())"` — must print a dict
2. `python3 -c "import sys; sys.path.insert(0, 'plugins/console-forwarding/mcp'); import models; t = models.SSHTarget(user='u', hostname='h'); d = {t: 1}; print('hashable:', len(d))"` — must print `hashable: 1`
3. `python3 -c "import sys; sys.path.insert(0, 'plugins/console-forwarding/mcp'); import errors; e = errors.SessionNotFoundError('agent-3'); assert issubclass(type(e), errors.ConsoleForwardingError); print('hierarchy OK')"` — must print `hierarchy OK`
4. `uv run prek run --files plugins/console-forwarding/mcp/models.py plugins/console-forwarding/mcp/errors.py` — must exit 0

---

## Task 3.1: Backend Protocol and Registry

**Status**: NOT STARTED
**Dependencies**: Task 2.1
**Priority**: 3
**Complexity**: Medium
**Agent**: python-cli-architect
**Skills**: ["python3-development"]

### Description

Implement `plugins/console-forwarding/mcp/backends/__init__.py` with the `SessionBackend` Protocol and `BackendRegistry` class.

#### SessionBackend Protocol

Define using `typing.Protocol` (structural typing, not `abc.ABC`). Per ADR-001, this enables duck typing without forced inheritance.

Required properties:

- `name: str` — backend identifier
- `is_available: bool` — whether the backend can be used
- `is_async: bool` — whether methods are natively async or sync

Required methods (see architecture spec "Backend Abstraction" section for full signatures):

- `list_sessions(self) -> list[SessionInfo]`
- `list_windows(self, session: str) -> list[WindowInfo]`
- `list_panes(self, session: str, window: str | None) -> list[PaneInfo]`
- `capture_pane(self, session: str, pane: str | None, window: str | None, lines: int | None) -> PaneOutput`
- `send_keys(self, session: str, keys: str, pane: str | None, window: str | None, enter: bool, literal: bool) -> None`
- `create_session(self, name: str, command: str | None, width: int, height: int, start_directory: str | None, environment: dict[str, str] | None) -> SessionInfo`
- `kill_session(self, session: str) -> None`

#### BackendRegistry

A class that:

- Stores backends in a `dict[str, SessionBackend]` keyed by backend name
- Provides `register(name: str, backend: SessionBackend) -> None`
- Provides `get(name: str) -> SessionBackend | None`
- Provides `available_backends() -> list[str]` — returns names of backends where `is_available` is `True`

### Acceptance Criteria

1. `backends/__init__.py` exports `SessionBackend` (Protocol) and `BackendRegistry`
2. `SessionBackend` is a `typing.Protocol` subclass (not `abc.ABC`)
3. Protocol has all 3 properties and 7 methods with correct signatures matching the architecture spec
4. `BackendRegistry` supports `register`, `get`, and `available_backends` with correct behavior
5. File imports cleanly: `python3 -c "import sys; sys.path.insert(0, 'plugins/console-forwarding/mcp'); from backends import SessionBackend, BackendRegistry; print('OK')"` exits 0
6. `uv run prek run --files plugins/console-forwarding/mcp/backends/__init__.py` exits 0

### Verification Steps

1. `python3 -c "import sys; sys.path.insert(0, 'plugins/console-forwarding/mcp'); from backends import SessionBackend, BackendRegistry; import typing; print(issubclass(SessionBackend, typing.Protocol))"` — must print `True` (or verify via `runtime_checkable` decoration if added)
2. `python3 -c "import sys; sys.path.insert(0, 'plugins/console-forwarding/mcp'); from backends import BackendRegistry; r = BackendRegistry(); print('BackendRegistry OK')"` — must not raise
3. `uv run prek run --files plugins/console-forwarding/mcp/backends/__init__.py` — must exit 0

---

## Task 4.1: Tmux Backend Implementation

**Status**: NOT STARTED
**Dependencies**: Task 3.1
**Priority**: 4
**Complexity**: High
**Agent**: python-cli-architect
**Skills**: ["python3-development"]

### Description

Implement `plugins/console-forwarding/mcp/backends/tmux_backend.py` — the libtmux-based local tmux backend.

This backend is fully synchronous (all libtmux operations are subprocess-based). The session manager wraps calls in `asyncio.to_thread()` — the backend itself must not use asyncio.

#### TmuxBackend class

Properties:

- `name` returns `"tmux"`
- `is_available` returns `True` if `shutil.which("tmux")` is not None
- `is_async` returns `False`

The backend uses `libtmux.Server()` to obtain the default tmux server. Do NOT create a custom socket — use the user's default tmux server.

#### Method implementations

**`list_sessions() -> list[SessionInfo]`**

Use `server.sessions` (QueryList) to enumerate sessions. Map each `libtmux.Session` to `SessionInfo`. Fields:

- `name`: `session.name`
- `id`: `session.id` (e.g., `$1`)
- `windows`: `len(session.windows)`
- `created`: convert `session.session_created` (Unix timestamp string) to ISO format
- `attached`: `session.session_attached == "1"`
- `width`: `int(session.session_width)`
- `height`: `int(session.session_height)`

Raise `BackendNotAvailableError` if tmux is not installed.

**`list_windows(session: str) -> list[WindowInfo]`**

Resolve session by name or ID. Raise `SessionNotFoundError` if not found. Map each `libtmux.Window` to `WindowInfo`.

**`list_panes(session: str, window: str | None) -> list[PaneInfo]`**

Resolve session, then window (active window if `window` is None). Raise `SessionNotFoundError` or `WindowNotFoundError`. Map each `libtmux.Pane` to `PaneInfo`.

**`capture_pane(session: str, pane: str | None, window: str | None, lines: int | None) -> PaneOutput`**

Resolve session, window, pane. Use `pane_obj.capture_pane()` to get output lines (returns a list of strings). If `lines` is not None, take the last `lines` items from the list. Compute `total_lines` before slicing. Construct `PaneOutput` with `offset=0` (offset is handled by the session manager layer, not the backend; the backend always starts from the beginning of its captured slice).

**`send_keys(session: str, keys: str, pane: str | None, window: str | None, enter: bool, literal: bool) -> None`**

Resolve session, window, pane. Use `pane_obj.send_keys(keys, enter=enter, literal=literal)`.

**`create_session(name: str, command: str | None, width: int, height: int, start_directory: str | None, environment: dict[str, str] | None) -> SessionInfo`**

Check `server.find_where({"session_name": name})` -- raise `SessionAlreadyExistsError` if found. Use `server.new_session(session_name=name, ...)`. Pass `x=width, y=height`. Pass `start_directory` as `start_directory` kwarg if not None. Environment variables must be set via `server.new_session(..., env=environment)` or via pre-setting in the system environment -- use whatever libtmux v0.53 supports. Return `SessionInfo` for the new session.

**`kill_session(session: str) -> None`**

Resolve session. Raise `SessionNotFoundError` if not found. Call `session_obj.kill()`.

#### Session and pane resolution helpers

Implement private helpers:

- `_resolve_session(server, session: str) -> libtmux.Session` — try by name first, then by ID
- `_resolve_window(session_obj, window: str | None) -> libtmux.Window` — None returns active window
- `_resolve_pane(window_obj, pane: str | None) -> libtmux.Pane` — None returns active pane

### Acceptance Criteria

1. `TmuxBackend` satisfies `SessionBackend` Protocol (all 3 properties + 7 methods present with matching signatures)
2. `TmuxBackend.is_async` returns `False`
3. `TmuxBackend.is_available` returns `False` gracefully when tmux binary is absent (no exception)
4. All resolution helpers raise the correct exception type (`SessionNotFoundError`, `WindowNotFoundError`, `PaneNotFoundError`) with a descriptive message
5. No `asyncio` imports or `async/await` in this file
6. `uv run prek run --files plugins/console-forwarding/mcp/backends/tmux_backend.py` exits 0

### Verification Steps

1. `python3 -c "import sys; sys.path.insert(0, 'plugins/console-forwarding/mcp'); from backends.tmux_backend import TmuxBackend; b = TmuxBackend(); print('is_async:', b.is_async, 'is_available:', b.is_available)"` — must print `is_async: False` and not raise
2. `python3 -c "import sys; sys.path.insert(0, 'plugins/console-forwarding/mcp'); import inspect; from backends.tmux_backend import TmuxBackend; assert not inspect.iscoroutinefunction(TmuxBackend.list_sessions); print('no async OK')"` — must print `no async OK`
3. `uv run prek run --files plugins/console-forwarding/mcp/backends/tmux_backend.py` — must exit 0

---

## Task 5.1: SSH Backend Implementation

**Status**: NOT STARTED
**Dependencies**: Task 3.1
**Priority**: 4
**Complexity**: High
**Agent**: python-cli-architect
**Skills**: ["python3-development"]

### Description

Implement `plugins/console-forwarding/mcp/backends/ssh_backend.py` — the asyncssh-based remote tmux backend.

This backend is natively async. It does NOT use libtmux — it runs tmux CLI commands on the remote host via `conn.run("tmux ...")` and parses their tab-delimited output.

Per ADR-003: libtmux operates on a local tmux socket and cannot reach a remote host. The tmux CLI with `-F` format strings provides structured output that can be parsed from `conn.run()` stdout.

#### SSHBackend class

Properties:

- `name` returns `"ssh"`
- `is_available` returns `True` (asyncssh is a Python dependency, always available)
- `is_async` returns `True`

#### Connection model

The `SSHBackend` does NOT own the connection pool. It receives an `asyncssh.SSHClientConnection` as a parameter to each method. The session manager (T6.1) owns connection pooling. Every method signature takes a `conn: asyncssh.SSHClientConnection` parameter.

This is the correct separation of concerns: the backend knows how to run tmux commands; the session manager knows how to obtain and reuse connections.

#### Remote command methods (all async)

All methods follow this pattern:

1. Build a tmux command string with `shlex.quote()` applied to all user-supplied arguments
2. Call `result = await conn.run(cmd, check=False)`
3. Check `result.exit_status` — non-zero means the session/pane/window was not found (raise appropriate error)
4. Parse `result.stdout` as tab-separated lines using the format strings from the architecture spec

**Remote command table** (from architecture spec "Remote tmux Commands" section):

| Method | tmux command pattern |
|--------|----------------------|
| `list_sessions` | `tmux list-sessions -F "#{session_name}\t#{session_id}\t#{session_windows}\t#{session_created}\t#{session_attached}\t#{session_width}\t#{session_height}"` |
| `list_windows` | `tmux list-windows -t {session} -F "#{window_name}\t#{window_id}\t#{window_index}\t#{window_panes}\t#{window_active}\t#{window_width}\t#{window_height}"` |
| `list_panes` | `tmux list-panes -t {session}:{window} -F "#{pane_id}\t#{pane_index}\t#{pane_width}\t#{pane_height}\t#{pane_active}\t#{pane_current_command}\t#{pane_current_path}"` |
| `capture_pane` | `tmux capture-pane -t {session}:{window}.{pane} -p [-S -{lines}]` |
| `send_keys` | `tmux send-keys -t {session}:{window}.{pane} [-l] {keys} [Enter]` |
| `create_session` | `tmux new-session -d -s {name} -x {width} -y {height} [-c {dir}] [{command}]` |
| `kill_session` | `tmux kill-session -t {session}` |

#### Shell injection prevention

Apply `shlex.quote()` to every user-supplied value before string interpolation. This includes: session names, keys content, pane IDs, window names, paths, and command strings. This is mandatory per the architecture spec "Security Considerations" section.

#### Method signatures

All methods are `async def` and match the `SessionBackend` Protocol signatures with an additional `conn` parameter prepended:

```python
async def list_sessions(self, conn: asyncssh.SSHClientConnection) -> list[SessionInfo]: ...
async def list_windows(self, conn: asyncssh.SSHClientConnection, session: str) -> list[WindowInfo]: ...
# etc.
```

Note: This signature diverges from the Protocol because of the `conn` parameter. The session manager calls SSH backend methods directly (not through the Protocol dispatch), so this is intentional. The Protocol is satisfied by `TmuxBackend` which does not need `conn`.

#### Output parsing

Parse tab-separated output from tmux format strings. For boolean-like fields (`session_attached`, `window_active`, `pane_active`), tmux returns `"1"` or `"0"` — convert to `bool`. For integer fields, convert with `int()`. For `created` timestamps, convert Unix epoch string to ISO format using `datetime.fromtimestamp(...).isoformat()`.

### Acceptance Criteria

1. `SSHBackend.is_async` returns `True`
2. `SSHBackend.is_available` returns `True`
3. All remote command methods are `async def`
4. Every user-supplied value is wrapped in `shlex.quote()` before interpolation — confirm by code inspection that no string formatted with user input lacks `shlex.quote()`
5. Tab-delimited parsing correctly converts `"1"`/`"0"` to `bool` and numeric strings to `int`
6. `uv run prek run --files plugins/console-forwarding/mcp/backends/ssh_backend.py` exits 0

### Verification Steps

1. `python3 -c "import sys; sys.path.insert(0, 'plugins/console-forwarding/mcp'); from backends.ssh_backend import SSHBackend; b = SSHBackend(); print('is_async:', b.is_async)"` — must print `is_async: True`
2. `python3 -c "import sys; sys.path.insert(0, 'plugins/console-forwarding/mcp'); import inspect; from backends.ssh_backend import SSHBackend; assert inspect.iscoroutinefunction(SSHBackend.list_sessions); print('async OK')"` — must print `async OK`
3. `uv run prek run --files plugins/console-forwarding/mcp/backends/ssh_backend.py` — must exit 0

---

## Task 6.1: Session Manager

**Status**: NOT STARTED
**Dependencies**: Task 4.1, Task 5.1
**Priority**: 5
**Complexity**: High
**Agent**: python-cli-architect
**Skills**: ["python3-development"]

### Description

Implement `plugins/console-forwarding/mcp/session_manager.py` — the central dispatch layer between MCP tools and backends.

This is the most complex module. It owns:

1. SSH URI parsing into `SSHTarget`
2. Backend resolution (local vs SSH)
3. Async wrapping for sync (tmux) backend calls
4. SSH connection pooling
5. Error conversion from domain exceptions to `ToolError`

#### SSHTarget

Import from `models.py`. The session manager uses `SSHTarget` as the connection pool dict key.

#### SSH URI parsing

Implement `_parse_ssh_uri(host: str) -> SSHTarget`:

- Input: `"ssh://user@hostname:port"` or `"ssh://user@hostname"` (port defaults to 22)
- Raise `InvalidURIError` with message `"Invalid SSH URI '{host}'. Expected format: ssh://user@hostname:port"` for any malformed input
- Scheme must be `ssh://`, user required, hostname required, port 1-65535 if given
- Use `urllib.parse.urlparse()` for parsing

#### SessionManager class

```python
class SessionManager:
    def __init__(
        self,
        tmux_backend: TmuxBackend | None,
        ssh_backend: SSHBackend,
    ) -> None:
        self._tmux = tmux_backend
        self._ssh = ssh_backend
        self._connections: dict[SSHTarget, asyncssh.SSHClientConnection] = {}
```

#### Connection pool methods

**`async def _get_connection(self, target: SSHTarget) -> asyncssh.SSHClientConnection`**:

- Return existing connection if `target in self._connections` and connection is not closed
- Create new connection via `asyncssh.connect(...)` with:
  - `host=target.hostname`, `port=target.port`, `username=target.user`
  - `known_hosts="~/.ssh/known_hosts"` (NOT `None`)
  - `connect_timeout=_SSH_CONNECT_TIMEOUT` (10 seconds, module constant)
- Store in `self._connections[target]`
- Raise `SSHConnectionError` on asyncssh connection failure

**`async def close_all(self) -> None`**: Close all pooled connections and clear dict.

#### Dispatch methods

Implement async dispatch methods matching the 7 MCP tools. Pattern:

```python
async def list_sessions(self, host: str | None) -> list[SessionInfo]:
    if host is None:
        if self._tmux is None or not self._tmux.is_available:
            raise BackendNotAvailableError("tmux is not installed...")
        return await asyncio.to_thread(self._tmux.list_sessions)
    target = _parse_ssh_uri(host)
    conn = await self._get_connection(target)
    return await self._ssh.list_sessions(conn)
```

Apply this pattern for all 7 methods, with appropriate parameter threading.

#### Error conversion

Wrap each dispatch method body in a try/except that catches `ConsoleForwardingError` subclasses and re-raises as `ToolError` with actionable messages per the architecture spec "ToolError Conversion" section:

- `SessionNotFoundError("agent-3")` → `ToolError("Session 'agent-3' not found. Use list_sessions() to see available sessions.")`
- `BackendNotAvailableError("tmux")` → `ToolError("tmux is not installed. Install tmux >= 3.2a for local sessions. Remote SSH sessions are available via host parameter.")`
- `SSHConnectionError(host, reason)` → `ToolError("SSH connection to {host} failed: {reason}. Check SSH keys and host availability.")`

Other `ConsoleForwardingError` subclasses must also be caught and converted to `ToolError` with their message string.

#### Module-level factory

```python
def create_session_manager() -> SessionManager:
    """Create a SessionManager with detected backends."""
    import shutil
    tmux_backend = TmuxBackend() if shutil.which("tmux") else None
    ssh_backend = SSHBackend()
    return SessionManager(tmux_backend=tmux_backend, ssh_backend=ssh_backend)
```

### Acceptance Criteria

1. `_parse_ssh_uri("ssh://user@host:2222")` returns `SSHTarget(user="user", hostname="host", port=2222)`
2. `_parse_ssh_uri("ssh://user@host")` returns `SSHTarget(user="user", hostname="host", port=22)`
3. `_parse_ssh_uri("http://user@host")` raises `InvalidURIError`
4. Dispatch methods use `asyncio.to_thread()` for tmux backend calls (not direct `await`)
5. Dispatch methods use direct `await` for SSH backend calls (not `to_thread`)
6. All `ConsoleForwardingError` subclasses are caught and converted to `ToolError` — no domain exceptions leak to callers
7. `create_session_manager()` returns a `SessionManager` without raising (even when tmux is absent)
8. `uv run prek run --files plugins/console-forwarding/mcp/session_manager.py` exits 0

### Verification Steps

1. `python3 -c "import sys; sys.path.insert(0, 'plugins/console-forwarding/mcp'); from session_manager import _parse_ssh_uri; t = _parse_ssh_uri('ssh://deploy@buildserver:2222'); print(t.user, t.hostname, t.port)"` — must print `deploy buildserver 2222`
2. `python3 -c "import sys; sys.path.insert(0, 'plugins/console-forwarding/mcp'); from session_manager import _parse_ssh_uri; from errors import InvalidURIError; [_parse_ssh_uri(x) for x in ['noscheme', 'http://u@h', 'ssh://nouser']]" 2>&1 | head -5` — must show `InvalidURIError` for at least the first two
3. `python3 -c "import sys; sys.path.insert(0, 'plugins/console-forwarding/mcp'); from session_manager import create_session_manager; m = create_session_manager(); print('OK', type(m).__name__)"` — must print `OK SessionManager`
4. `uv run prek run --files plugins/console-forwarding/mcp/session_manager.py` — must exit 0

---

## Task 7.1: MCP Server — FastMCP Tools

**Status**: NOT STARTED
**Dependencies**: Task 6.1
**Priority**: 6
**Complexity**: High
**Agent**: python-cli-architect
**Skills**: ["python3-development", "fastmcp-creator"]

### Description

Implement `plugins/console-forwarding/mcp/server.py` — the FastMCP entry point and MCP tool definitions.

Reference implementation: `plugins/agentskill-kaizen/mcp/server.py` (especially lines 1-15 for PEP 723 header, lines 58-70 for annotation dicts, lines 83 for FastMCP instantiation, line 614 for `mcp.run()`).

#### PEP 723 Header

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

#### Module-level constants

```python
_DEFAULT_SESSION_WIDTH: int = 220
_DEFAULT_SESSION_HEIGHT: int = 50
_SSH_CONNECT_TIMEOUT: int = 10
_TMUX_MIN_VERSION: str = "3.2a"
```

#### Annotation dicts

Define all three as module-level constants:

- `_READONLY_ANNOTATIONS` — `readOnlyHint: True, destructiveHint: False, idempotentHint: True, openWorldHint: False`
- `_MUTATING_ANNOTATIONS` — `readOnlyHint: False, destructiveHint: False, idempotentHint: True, openWorldHint: False`
- `_DESTRUCTIVE_ANNOTATIONS` — `readOnlyHint: False, destructiveHint: True, idempotentHint: False, openWorldHint: False`

#### FastMCP instantiation

```python
mcp = FastMCP("console-forwarding", mask_error_details=False)
session_manager = create_session_manager()
```

#### 7 MCP tools

Each tool is a thin async function. Parameters and return schemas must exactly match the architecture spec "MCP Tool API" section.

| Tool | Annotations |
|------|-------------|
| `list_sessions(host=None)` | `_READONLY_ANNOTATIONS` |
| `list_windows(session, host=None)` | `_READONLY_ANNOTATIONS` |
| `list_panes(session, window=None, host=None)` | `_READONLY_ANNOTATIONS` |
| `capture_pane(session, pane=None, window=None, lines=None, offset=0, host=None)` | `_READONLY_ANNOTATIONS` |
| `send_keys(session, keys, pane=None, window=None, enter=True, literal=False, host=None)` | `_MUTATING_ANNOTATIONS` |
| `create_session(name, command=None, width=220, height=50, start_directory=None, environment=None, host=None)` | `_MUTATING_ANNOTATIONS` |
| `kill_session(session, host=None)` | `_DESTRUCTIVE_ANNOTATIONS` |

Each tool must return a `dict[str, Any]` matching the return schema in the architecture spec. Use `model.model_dump()` where appropriate to serialize Pydantic objects.

Tool docstrings must match the description text in the architecture spec "MCP Tool API" section exactly (they become the tool's description visible to the MCP client).

#### capture_pane offset handling

The `offset` parameter is handled in `server.py`, not in the backend. After obtaining pane output:

1. Apply offset: slice `lines_list[offset:]`
2. The backend returns `total_lines` (before offset); include this in the return dict
3. `line_count` reflects the count after offset is applied

#### Entry point

```python
if __name__ == "__main__":
    mcp.run()
```

### Acceptance Criteria

1. File begins with the exact PEP 723 shebang line `#!/usr/bin/env -S uv --quiet run --active --script`
2. All 4 dependencies are declared in PEP 723 `# dependencies` block with correct version constraints
3. All 7 MCP tools are defined with correct `@mcp.tool(annotations=...)` decorators
4. `list_sessions` and `list_windows` and `list_panes` and `capture_pane` use `_READONLY_ANNOTATIONS`
5. `send_keys` and `create_session` use `_MUTATING_ANNOTATIONS`
6. `kill_session` uses `_DESTRUCTIVE_ANNOTATIONS`
7. `capture_pane` offset slicing is applied in server.py (not delegated to backend)
8. `uv run prek run --files plugins/console-forwarding/mcp/server.py` exits 0

### Verification Steps

1. `head -3 plugins/console-forwarding/mcp/server.py` — first line must be `#!/usr/bin/env -S uv --quiet run --active --script`
2. `python3 -c "import sys; sys.path.insert(0, 'plugins/console-forwarding/mcp'); print('import check — may fail on missing deps, that is OK')"` — check for syntax errors only; dependency import failures are expected without `uv run`
3. `grep -n "@mcp.tool" plugins/console-forwarding/mcp/server.py | wc -l` — must print `7`
4. `grep "_DESTRUCTIVE_ANNOTATIONS" plugins/console-forwarding/mcp/server.py` — must appear exactly once (on `kill_session`)
5. `uv run prek run --files plugins/console-forwarding/mcp/server.py` — must exit 0

---

## Task 8.1: Test Fixtures — conftest.py

**Status**: NOT STARTED
**Dependencies**: Task 7.1
**Priority**: 7
**Complexity**: Medium
**Agent**: python-pytest-architect
**Skills**: ["python3-development"]

### Description

Implement `plugins/console-forwarding/tests/conftest.py` — shared test fixtures for all test modules.

Reference implementation: `plugins/agentskill-kaizen/tests/conftest.py` (FastMCP stub pattern at lines 36-85, mock_context fixture at lines 268-278).

#### FastMCP stub (required)

Apply the stub-before-import pattern from the kaizen reference. Add `plugins/console-forwarding/mcp` to `sys.path` before importing any server module. The stub makes `@mcp.tool` a no-op decorator, enabling direct `await server.tool_name(...)` calls in tests.

#### Required fixtures

**`mock_tmux_backend`** (function scope):

A `MagicMock` that satisfies the `SessionBackend` Protocol interface. Pre-configure:

- `mock.name` returns `"tmux"`
- `mock.is_available` returns `True`
- `mock.is_async` returns `False`
- `mock.list_sessions.return_value` returns `[sample_session_info]`
- Other method return values set to sensible defaults

**`mock_ssh_backend`** (function scope):

An `AsyncMock` for async methods that satisfies the `SessionBackend` interface for the SSH backend:

- `mock.name` returns `"ssh"`
- `mock.is_available` returns `True`
- `mock.is_async` returns `True`
- Async methods return appropriate default values

**`session_manager`** (function scope):

A `SessionManager` instance initialized with `mock_tmux_backend` and `mock_ssh_backend`. Bypasses real backend initialization.

**`mock_context`** (function scope):

```python
@pytest.fixture
def mock_context() -> AsyncMock:
    ctx = AsyncMock()
    ctx.info = AsyncMock()
    ctx.warning = AsyncMock()
    return ctx
```

**`sample_session_info`** (module scope):

A pre-built `SessionInfo` instance for use in assertions:

```python
SessionInfo(
    name="test-session",
    id="$1",
    windows=1,
    created="2026-01-01T00:00:00",
    attached=False,
    width=220,
    height=50,
)
```

**`sample_pane_output`** (module scope):

A pre-built `PaneOutput` for use in assertions:

```python
PaneOutput(
    output="line1\nline2\nline3",
    line_count=3,
    total_lines=3,
    offset=0,
    session="test-session",
    pane="%1",
)
```

**`sample_window_info`** (module scope):

A pre-built `WindowInfo` instance.

**`sample_pane_info`** (module scope):

A pre-built `PaneInfo` instance.

### Acceptance Criteria

1. `conftest.py` applies the FastMCP stub before importing server modules
2. All 7 fixtures are defined: `mock_tmux_backend`, `mock_ssh_backend`, `session_manager`, `mock_context`, `sample_session_info`, `sample_pane_output`, `sample_window_info`, `sample_pane_info`
3. `pytest plugins/console-forwarding/tests/ --collect-only -q` exits 0 (collection succeeds even if no tests yet)
4. `uv run prek run --files plugins/console-forwarding/tests/conftest.py` exits 0

### Verification Steps

1. `uv run pytest plugins/console-forwarding/tests/ --collect-only -q 2>&1 | tail -5` — must show `no tests ran` or collected test count; must NOT show `ImportError` or `ModuleNotFoundError`
2. `uv run prek run --files plugins/console-forwarding/tests/conftest.py` — must exit 0

---

## Task 8.2: Data Model Tests

**Status**: NOT STARTED
**Dependencies**: Task 8.1
**Priority**: 8
**Complexity**: Low
**Agent**: python-pytest-architect
**Skills**: ["python3-development"]

### Description

Implement `plugins/console-forwarding/tests/test_models.py` — unit tests for `models.py` and `errors.py`.

Group tests into classes: `TestSessionInfo`, `TestWindowInfo`, `TestPaneInfo`, `TestPaneOutput`, `TestSSHTarget`, `TestErrorHierarchy`.

#### Test coverage required

**SessionInfo**:

- Valid construction succeeds
- `model_dump()` returns dict with all 7 fields
- Missing required field raises `ValidationError`

**SSHTarget**:

- `port` defaults to 22
- Frozen: attempting mutation raises `ValidationError` or `TypeError`
- Hashable: can be used as dict key
- Two instances with same values are equal and have same hash

**ErrorHierarchy**:

- All 8 subclasses are subclasses of `ConsoleForwardingError`
- `ConsoleForwardingError` is a subclass of `Exception`
- Each exception can be raised and caught by its parent class

### Acceptance Criteria

1. `TestSessionInfo`, `TestWindowInfo`, `TestPaneInfo`, `TestPaneOutput`, `TestSSHTarget`, `TestErrorHierarchy` classes are present
2. `uv run pytest plugins/console-forwarding/tests/test_models.py -v` exits 0 with all tests passing
3. Test coverage includes frozen/hashable behavior for `SSHTarget`
4. `uv run prek run --files plugins/console-forwarding/tests/test_models.py` exits 0

### Verification Steps

1. `uv run pytest plugins/console-forwarding/tests/test_models.py -v` — must exit 0 with all tests PASSED
2. `uv run pytest plugins/console-forwarding/tests/test_models.py -v 2>&1 | grep -E "PASSED|FAILED|ERROR"` — must show only PASSED lines
3. `uv run prek run --files plugins/console-forwarding/tests/test_models.py` — must exit 0

---

## Task 8.3: Tmux Backend Tests

**Status**: NOT STARTED
**Dependencies**: Task 8.1, Task 4.1
**Priority**: 8
**Complexity**: High
**Agent**: python-pytest-architect
**Skills**: ["python3-development"]

### Description

Implement `plugins/console-forwarding/tests/test_tmux_backend.py` — unit and integration tests for `TmuxBackend`.

Tests requiring a real tmux server must be marked `@pytest.mark.integration`. All other tests use libtmux's built-in pytest fixtures for isolated testing.

#### Test structure

**Class `TestTmuxBackendAvailability`** (no integration marker):

- `test_is_not_async` — assert `TmuxBackend().is_async is False`
- `test_name_is_tmux` — assert `TmuxBackend().name == "tmux"`

**Class `TestTmuxBackendDiscovery`** (integration, uses libtmux `session` fixture):

These tests use libtmux's auto-discovered fixtures (`server`, `session`, `window`, `pane`) which create isolated tmux sessions for testing.

- `test_list_sessions_returns_session_info` — after session created, `list_sessions()` returns at least one `SessionInfo` with correct `name`
- `test_list_windows_returns_window_info` — `list_windows(session.name)` returns list of `WindowInfo`
- `test_list_panes_returns_pane_info` — `list_panes(session.name, None)` returns list of `PaneInfo`
- `test_session_not_found_raises` — `list_windows("nonexistent-session-xyz")` raises `SessionNotFoundError`

**Class `TestTmuxBackendCapture`** (integration, uses `pane` fixture):

- `test_capture_pane_returns_output` — after `send_keys`, `capture_pane` output contains the sent text
- `test_capture_pane_lines_limits_output` — `capture_pane(..., lines=5)` returns at most 5 lines

**Class `TestTmuxBackendLifecycle`** (integration, uses `server` fixture):

- `test_create_and_kill_session` — `create_session("test-lifecycle", ...)` succeeds, `kill_session` cleans up
- `test_create_session_duplicate_raises` — creating session with same name raises `SessionAlreadyExistsError`

### Acceptance Criteria

1. All non-integration tests pass without tmux binary (mark integration tests correctly)
2. `uv run pytest plugins/console-forwarding/tests/test_tmux_backend.py -v -m "not integration"` exits 0
3. Test classes match the structure above
4. `uv run prek run --files plugins/console-forwarding/tests/test_tmux_backend.py` exits 0

### Verification Steps

1. `uv run pytest plugins/console-forwarding/tests/test_tmux_backend.py -v -m "not integration"` — must exit 0
2. `uv run pytest plugins/console-forwarding/tests/test_tmux_backend.py --collect-only -q` — must show all test names without ImportError
3. `uv run prek run --files plugins/console-forwarding/tests/test_tmux_backend.py` — must exit 0

---

## Task 8.4: SSH Backend Tests

**Status**: NOT STARTED
**Dependencies**: Task 8.1, Task 5.1
**Priority**: 8
**Complexity**: High
**Agent**: python-pytest-architect
**Skills**: ["python3-development"]

### Description

Implement `plugins/console-forwarding/tests/test_ssh_backend.py` — unit tests for `SSHBackend` using mocked asyncssh connections.

No real SSH connections are used. Mock `asyncssh.SSHClientConnection` and `conn.run()` to return pre-defined `asyncssh.SSHCompletedProcess`-like objects with controlled stdout.

#### Test structure

**Class `TestSSHBackendProperties`**:

- `test_is_async` — `SSHBackend().is_async is True`
- `test_is_available` — `SSHBackend().is_available is True`
- `test_name_is_ssh` — `SSHBackend().name == "ssh"`

**Class `TestSSHBackendListSessions`** (`@pytest.mark.asyncio`):

- `test_list_sessions_parses_output` — mock `conn.run()` to return tab-separated tmux format output; assert returns `list[SessionInfo]` with correct field values
- `test_list_sessions_empty_returns_empty_list` — empty stdout returns `[]`
- `test_list_sessions_nonzero_exit_raises` — `result.exit_status != 0` raises `BackendNotAvailableError` or `SSHCommandError`

**Class `TestSSHBackendShellEscaping`**:

- `test_session_name_is_quoted` — inject a session name containing spaces or special chars; verify `shlex.quote()` was called by checking the built command string does not contain unquoted user input
- `test_keys_content_is_quoted` — same for `send_keys` keys parameter

**Class `TestSSHBackendCapturePane`** (`@pytest.mark.asyncio`):

- `test_capture_pane_returns_pane_output` — mock stdout with multiline output; verify `PaneOutput.output` contains the content
- `test_capture_pane_with_lines_parameter` — verify command includes `-S -{lines}` when `lines` is not None

**Class `TestSSHBackendLifecycle`** (`@pytest.mark.asyncio`):

- `test_create_session_builds_correct_command` — verify tmux command contains all required flags
- `test_kill_session_targets_correct_session` — verify `kill-session -t {session}` is sent

### Acceptance Criteria

1. All tests use mocked asyncssh connections — no real SSH connections
2. `uv run pytest plugins/console-forwarding/tests/test_ssh_backend.py -v` exits 0
3. Shell escaping tests verify `shlex.quote()` behavior on special characters
4. `uv run prek run --files plugins/console-forwarding/tests/test_ssh_backend.py` exits 0

### Verification Steps

1. `uv run pytest plugins/console-forwarding/tests/test_ssh_backend.py -v` — must exit 0 with all tests PASSED
2. `grep -n "real_ssh\|asyncssh.connect" plugins/console-forwarding/tests/test_ssh_backend.py` — must return empty (no real connections)
3. `uv run prek run --files plugins/console-forwarding/tests/test_ssh_backend.py` — must exit 0

---

## Task 8.5: Session Manager Tests

**Status**: NOT STARTED
**Dependencies**: Task 8.1, Task 6.1
**Priority**: 8
**Complexity**: High
**Agent**: python-pytest-architect
**Skills**: ["python3-development"]

### Description

Implement `plugins/console-forwarding/tests/test_session_manager.py` — unit tests for `SessionManager` using mocked backends.

Use the `session_manager` fixture from `conftest.py` which provides a `SessionManager` with mock backends.

#### Test structure

**Class `TestSSHURIParsing`**:

- `test_full_uri` — `ssh://user@host:2222` parses to `SSHTarget(user="user", hostname="host", port=2222)`
- `test_uri_without_port` — `ssh://user@host` uses port 22
- `test_invalid_scheme_raises` — `http://user@host` raises `InvalidURIError`
- `test_missing_user_raises` — `ssh://host` raises `InvalidURIError`
- `test_missing_host_raises` — `ssh://user@` raises `InvalidURIError`

**Class `TestSessionManagerDispatch`** (`@pytest.mark.asyncio`):

- `test_list_sessions_local_uses_tmux` — `host=None` calls `mock_tmux_backend.list_sessions`
- `test_list_sessions_ssh_uses_ssh_backend` — `host="ssh://u@h"` calls `mock_ssh_backend.list_sessions`
- `test_tmux_unavailable_raises_tool_error` — `mock_tmux_backend.is_available = False`; calling `list_sessions(host=None)` raises `ToolError`
- `test_session_not_found_converts_to_tool_error` — `mock_tmux_backend.list_sessions.side_effect = SessionNotFoundError("s")`; calling dispatch raises `ToolError`

**Class `TestConnectionPool`** (`@pytest.mark.asyncio`):

- `test_connection_reused_for_same_host` — call two dispatch methods with same host; verify `asyncssh.connect` called only once
- `test_close_all_clears_pool` — after `close_all()`, pool is empty

### Acceptance Criteria

1. All URI parsing tests cover valid and invalid cases
2. `uv run pytest plugins/console-forwarding/tests/test_session_manager.py -v` exits 0
3. `ConsoleForwardingError` subclasses are confirmed to convert to `ToolError` (not leak)
4. `uv run prek run --files plugins/console-forwarding/tests/test_session_manager.py` exits 0

### Verification Steps

1. `uv run pytest plugins/console-forwarding/tests/test_session_manager.py -v` — must exit 0 with all tests PASSED
2. `uv run pytest plugins/console-forwarding/tests/test_session_manager.py -v 2>&1 | grep "FAILED\|ERROR"` — must return empty
3. `uv run prek run --files plugins/console-forwarding/tests/test_session_manager.py` — must exit 0

---

## Task 8.6: MCP Tool Integration Tests

**Status**: NOT STARTED
**Dependencies**: Task 8.1, Task 7.1
**Priority**: 8
**Complexity**: High
**Agent**: python-pytest-architect
**Skills**: ["python3-development"]

### Description

Implement `plugins/console-forwarding/tests/test_server.py` — MCP tool integration tests using the FastMCP stub pattern.

The FastMCP stub in `conftest.py` makes decorated tools plain callables. Call them directly with `await server.list_sessions(...)`.

Use the `session_manager` fixture from `conftest.py`. In tests, replace the module-level `session_manager` in `server.py` with the mock: `server.session_manager = session_manager_fixture`.

#### Test structure

**Class `TestListSessions`** (`@pytest.mark.asyncio`):

- `test_returns_expected_schema` — result has `"sessions"`, `"count"`, `"host"` keys
- `test_count_matches_sessions_length` — `result["count"] == len(result["sessions"])`
- `test_local_host_routes_correctly` — `host=None` routes to tmux backend

**Class `TestListWindows`** (`@pytest.mark.asyncio`):

- `test_returns_expected_schema` — result has `"windows"`, `"count"`, `"session"`, `"host"` keys
- `test_requires_session_param` — missing `session` raises `TypeError` (required param)

**Class `TestListPanes`** (`@pytest.mark.asyncio`):

- `test_returns_expected_schema` — result has `"panes"`, `"count"`, `"session"`, `"window"`, `"host"` keys

**Class `TestCapturePaneOffset`** (`@pytest.mark.asyncio`):

- `test_offset_zero_returns_all_lines` — `offset=0` returns full output
- `test_offset_skips_lines` — `offset=2` skips first 2 lines; `line_count` reflects remaining lines
- `test_total_lines_reflects_pre_offset_count` — `total_lines` matches lines before offset was applied

**Class `TestSendKeys`** (`@pytest.mark.asyncio`):

- `test_returns_sent_true` — result has `"sent": True`
- `test_echoes_keys_in_response` — result `"keys"` matches input keys

**Class `TestCreateSession`** (`@pytest.mark.asyncio`):

- `test_returns_created_true` — result has `"created": True`
- `test_default_dimensions` — when `width`/`height` omitted, defaults are 220x50

**Class `TestKillSession`** (`@pytest.mark.asyncio`):

- `test_returns_killed_true` — result has `"killed": True`
- `test_session_not_found_surfaces_as_tool_error` — mock raises `ToolError`; test verifies it propagates

**Class `TestGracefulDegradation`** (`@pytest.mark.asyncio`):

- `test_local_tools_fail_when_tmux_unavailable` — `session_manager._tmux = None`; `list_sessions(host=None)` raises `ToolError`
- `test_ssh_tools_work_when_tmux_unavailable` — `session_manager._tmux = None`; `list_sessions(host="ssh://u@h")` succeeds

### Acceptance Criteria

1. All tool return schemas match architecture spec exactly (correct keys, correct types)
2. `capture_pane` offset behavior is tested and correct
3. Graceful degradation tests confirm tmux-absent + SSH-present works
4. `uv run pytest plugins/console-forwarding/tests/test_server.py -v` exits 0
5. `uv run prek run --files plugins/console-forwarding/tests/test_server.py` exits 0

### Verification Steps

1. `uv run pytest plugins/console-forwarding/tests/test_server.py -v` — must exit 0 with all tests PASSED
2. `uv run pytest plugins/console-forwarding/tests/ -v -m "not integration"` — all non-integration tests pass together
3. `uv run prek run --files plugins/console-forwarding/tests/test_server.py` — must exit 0

---

## Task 9.1: SKILL.md for Console Forwarding

**Status**: NOT STARTED
**Dependencies**: Task 7.1
**Priority**: 9
**Complexity**: Medium
**Agent**: general-purpose
**Skills**: ["write-to-skill-file"]

### Description

Write `plugins/console-forwarding/skills/console-forwarding/SKILL.md` — the user-facing skill documenting session naming conventions, SSH URI format, tool usage patterns, and troubleshooting.

The placeholder SKILL.md created in T1.1 must be replaced with the full content.

#### Required sections

**Frontmatter** (YAML, required fields):

```yaml
---
name: console-forwarding
description: "MCP tools for managing tmux sessions on local and remote hosts via Claude Code"
tools: list_sessions, list_windows, list_panes, capture_pane, send_keys, create_session, kill_session
---
```

Note: `tools` must be a CSV string (not a YAML array) per FM007 validator rule.

**Core Workflow section**:

Describe the 3-step workflow:

1. Discover sessions with `list_sessions()` (optionally with `host=` for remote)
2. Inspect a session with `capture_pane(session=..., lines=50)` to read output
3. Interact with `send_keys(session=..., keys=...)` to inject input

**Session Naming Conventions section**:

Document the recommended naming pattern for agent sessions: `agent-{task-id}` or `agent-{role}`. Explain that tmux session names must not contain periods (`.`), colons (`:`), or exclamation marks (`!`).

**SSH Remote Access section**:

Document the SSH URI format: `ssh://user@hostname:port`. Port defaults to 22 if omitted. Keys resolved from SSH agent or `~/.ssh/` (ed25519 or rsa). Known hosts checked against `~/.ssh/known_hosts` — add host before first use.

Include a concrete example:

```text
list_sessions(host="ssh://deploy@build-server.corp.com")
capture_pane(session="ci-runner", host="ssh://deploy@build-server.corp.com", lines=100)
```

**Output Size Management section**:

Explain `lines` and `offset` parameters for `capture_pane`. Warn about MCP output token limits (10K soft warning, 25K hard max). Recommend `lines=50` for routine progress checks.

**Troubleshooting section**:

| Problem | Cause | Fix |
|---------|-------|-----|
| `ToolError: tmux is not installed` | tmux binary absent | `brew install tmux` or `apt install tmux` |
| `ToolError: Session 'X' not found` | Wrong session name | Call `list_sessions()` to enumerate |
| `ToolError: SSH connection to ... failed` | Auth failure or host unreachable | Check SSH keys, verify `~/.ssh/known_hosts` |
| Output appears truncated | Large pane content | Use `lines` parameter; check `total_lines` in response |

### Acceptance Criteria

1. SKILL.md has valid YAML frontmatter with `name`, `description`, and `tools` fields
2. `tools` field is a CSV string (not YAML array) — no FM007 error
3. All 5 sections are present: Core Workflow, Session Naming, SSH Remote Access, Output Size Management, Troubleshooting
4. SSH URI format matches the architecture spec exactly (`ssh://user@hostname:port`)
5. `uv run prek run --files plugins/console-forwarding/skills/console-forwarding/SKILL.md` exits 0
6. Body token count is under 4400 (SK006 threshold) — check `uv run plugins/plugin-creator/scripts/plugin_validator.py plugins/console-forwarding` output

### Verification Steps

1. `uv run prek run --files plugins/console-forwarding/skills/console-forwarding/SKILL.md` — must exit 0
2. `uv run plugins/plugin-creator/scripts/plugin_validator.py plugins/console-forwarding 2>&1 | grep -E "SK006|SK007|FM007"` — must return empty (no token or frontmatter errors)
3. `python3 -c "import sys; sys.path.insert(0, '.'); f=open('plugins/console-forwarding/skills/console-forwarding/SKILL.md'); content=f.read(); f.close(); assert 'ssh://' in content; assert 'list_sessions' in content; print('content OK')"` — must print `content OK`

---

## Task 10.1: Plugin Validation and Lint Fixes

**Status**: NOT STARTED
**Dependencies**: Task 9.1, Task 8.6
**Priority**: 9
**Complexity**: Low
**Agent**: python-cli-architect
**Skills**: ["python3-development"]

### Description

Run the plugin validator and linting tools against the complete plugin. Fix any reported issues.

This task is the final quality gate before the plugin is considered implementation-complete.

#### Steps to execute

1. Run plugin validator:

   ```bash
   uv run plugins/plugin-creator/scripts/plugin_validator.py plugins/console-forwarding
   ```

   Fix any PL, PR, FM, or SK errors. Warnings may be suppressed via `.claude-plugin/validator.json` if they are intentional (e.g., server.py not yet importable without uv).

2. Run prek linting on all Python files:

   ```bash
   uv run prek run --files \
     plugins/console-forwarding/mcp/models.py \
     plugins/console-forwarding/mcp/errors.py \
     plugins/console-forwarding/mcp/backends/__init__.py \
     plugins/console-forwarding/mcp/backends/tmux_backend.py \
     plugins/console-forwarding/mcp/backends/ssh_backend.py \
     plugins/console-forwarding/mcp/session_manager.py \
     plugins/console-forwarding/mcp/server.py \
     plugins/console-forwarding/tests/conftest.py \
     plugins/console-forwarding/tests/test_models.py \
     plugins/console-forwarding/tests/test_tmux_backend.py \
     plugins/console-forwarding/tests/test_ssh_backend.py \
     plugins/console-forwarding/tests/test_session_manager.py \
     plugins/console-forwarding/tests/test_server.py
   ```

3. Run non-integration tests:

   ```bash
   uv run pytest plugins/console-forwarding/tests/ -v -m "not integration"
   ```

4. Report all results. If any issues remain, fix them in this task (do not defer to a follow-up).

### Acceptance Criteria

1. `uv run plugins/plugin-creator/scripts/plugin_validator.py plugins/console-forwarding` exits 0 with no ERROR-level findings
2. All prek linting passes (exit 0) for all Python files listed above
3. `uv run pytest plugins/console-forwarding/tests/ -v -m "not integration"` exits 0
4. No PL001, PL002, PL003, FM001, FM002, FM007 errors remain

### Verification Steps

1. `uv run plugins/plugin-creator/scripts/plugin_validator.py plugins/console-forwarding` — record all output; must exit 0 or show only WARNING-level findings
2. `uv run pytest plugins/console-forwarding/tests/ -v -m "not integration" 2>&1 | tail -10` — must show all PASSED
3. `uv run prek run --files plugins/console-forwarding/mcp/server.py plugins/console-forwarding/mcp/session_manager.py` — must exit 0

---

## Context Manifest

### Feature Overview: Console Forwarding MCP Server Plugin (GitHub Issue #364)

This feature creates a new Claude Code plugin at `plugins/console-forwarding/` that exposes terminal session management as MCP tools via a FastMCP server. The core problem being solved is that Claude Code sessions are currently isolated — a session cannot programmatically discover, read from, write to, or assess the health of other Claude Code sessions running in tmux. This plugin bridges that gap by providing 7 MCP tools: `list_sessions`, `list_windows`, `list_panes`, `capture_pane`, `send_keys`, `create_session`, and `kill_session`. Each tool supports both local tmux operations (via libtmux) and remote operations on SSH hosts (via asyncssh running tmux CLI commands remotely).

The MVP scope was explicitly resolved through 7 questions in the feature context document. The key scope decisions are:

- **Q1 (MVP tool set)**: Option C — discovery + capture + send_keys + lifecycle + remote SSH. Health monitoring (gastown-style zombie/hung detection) and multi-session broadcast are deferred to v2.
- **Q2 (dtach backend)**: Option B — Deferred. tmux covers all dtach capabilities plus output capture. The backend abstraction (`SessionBackend` Protocol) is designed to accommodate future backends.
- **Q3 (SSH URI format)**: Option A — `ssh://user@host:port` format, stateless, keys from SSH agent or `~/.ssh/`. No host registry for v1.
- **Q4 (Health monitoring)**: Option A — Single-call stateless check (deferred from MVP entirely per Q1).
- **Q5 (Multi-file structure)**: Option A — PEP 723 on `server.py` only; backends as local imports. `uv run --script server.py` installs deps; backend modules are plain `.py` files.
- **Q6 (Graceful degradation)**: Option B — Detect available backends at startup. If tmux is not installed, SSH tools still work. Local-only tools return `ToolError` with installation guidance.
- **Q7 (Output format)**: Option A — `capture_pane` accepts `lines` and `offset` parameters for caller-controlled pagination. No artificial truncation. Aligns with CLAUDE.md "No Invented Limits" rule.

### How the Existing Plugin/MCP Pattern Works: agentskill-kaizen Reference

The only existing FastMCP server in the codebase is `plugins/agentskill-kaizen/mcp/server.py`. Understanding its patterns is essential because the console-forwarding server must follow the same conventions.

When Claude Code loads a plugin, it reads the `plugin.json` file at `plugins/{name}/.claude-plugin/plugin.json`. The `mcpServers` object in that file declares MCP servers that Claude Code auto-starts as stdio subprocesses. The kaizen plugin declares its server as:

```json
"kaizen-analysis": {
  "command": "uv",
  "args": ["run", "--script", "${CLAUDE_PLUGIN_ROOT}/mcp/server.py"]
}
```

The `${CLAUDE_PLUGIN_ROOT}` variable resolves to the absolute path of the plugin directory in Claude Code's plugin cache at runtime — not the development source directory. The `uv run --script` command reads PEP 723 inline script metadata from `server.py` (lines 1-15), installs the declared dependencies into an isolated environment, and executes the script.

The server.py file follows a specific structure:

1. **PEP 723 header** (lines 1-15): Shebang `#!/usr/bin/env -S uv --quiet run --active --script` followed by the `# /// script` block declaring `requires-python` and `dependencies`. The `--active` flag reuses an active venv when present; `--quiet` suppresses uv output.

2. **Imports** (lines 30-46): `from __future__ import annotations` for deferred annotation evaluation, then `from fastmcp import Context, FastMCP` and `from fastmcp.exceptions import ToolError`.

3. **Module-level constants** (lines 52-70): Annotation dicts are defined as module-level constants. `_READONLY_ANNOTATIONS` sets `readOnlyHint: True, destructiveHint: False, idempotentHint: True, openWorldHint: False`. A second dict `_DASHBOARD_ANNOTATIONS` has `readOnlyHint: False` for tools with side effects.

4. **FastMCP instance** (line 83): `mcp = FastMCP("kaizen-analysis", mask_error_details=False)`. The `mask_error_details=False` flag exposes full exception messages to the MCP client, appropriate for developer-facing agent tools.

5. **Tool functions**: Each is an async function decorated with `@mcp.tool(annotations=_READONLY_ANNOTATIONS)`. Blocking/CPU-bound work is offloaded via `asyncio.to_thread()` to a separate synchronous `_impl` function. This pattern keeps the async tool signature minimal and makes the implementation independently testable. The `Context` parameter (when needed) must be keyword-only using `*` separator.

6. **Entry point** (lines 610-614): `if __name__ == "__main__": mcp.run()` — starts stdio transport.

The testing pattern is equally important. The kaizen tests at `plugins/agentskill-kaizen/tests/conftest.py` solve a critical problem: `@mcp.tool` triggers Pydantic TypeAdapter resolution at decoration time, which fails in test environments with deferred annotations (`from __future__ import annotations`). The solution is to stub FastMCP before importing server.py:

1. Save the real fastmcp module references
2. Create a `_StubMCP` class where `tool()` returns a no-op decorator
3. Install the stub into `sys.modules["fastmcp"]` and `sys.modules["fastmcp.exceptions"]` (preserving the real `ToolError` class)
4. Add the `mcp/` directory to `sys.path`
5. Import `server` — all `@mcp.tool` decorators become passthrough, leaving plain callable functions
6. Restore the real fastmcp modules

This makes tool functions directly callable in tests: `await server.list_sessions(host=None)`.

### How libtmux Works: The Tmux Backend Foundation

libtmux (v0.53.1, MIT license) provides a typed, ORM-like wrapper over tmux. The tmux hierarchy maps to four Python classes: `Server` -> `Session` -> `Window` -> `Pane`. Each is a dataclass inheriting from `Obj` (in `neo.py`).

**Execution model**: Every public method ultimately calls `tmux_cmd()` in `common.py`, which invokes tmux as a subprocess. This means all libtmux operations are synchronous and blocking. For the async MCP server, every libtmux call must be wrapped in `asyncio.to_thread()` — but this wrapping happens in the session manager, not in the tmux backend itself (per ADR-002).

**Key API calls the tmux backend uses**:

- `libtmux.Server()` — connects to default tmux socket. `Server(socket_name="...")` for isolation. The console-forwarding backend uses the default server (no custom socket) because it needs to access the user's existing sessions.
- `server.sessions` — returns `QueryList[Session]` with ORM-style filtering (`.get(session_name="dev")`, `.filter(session_name__startswith="agent")`).
- `server.new_session(session_name=..., attach=False, x=220, y=50, start_directory=..., environment=...)` — creates a detached session. The `x` and `y` parameters are required in headless environments (no TTY) to set terminal dimensions explicitly; without them tmux defaults to 80x24 or fails.
- `pane.send_keys(text, enter=True, literal=False)` — injects keystrokes. `literal=True` bypasses tmux key binding interpretation.
- `pane.capture_pane(start=-50, end="-")` — returns `list[str]`. `start`/`end` accept integers (negative = scrollback) or `"-"` for history boundaries. No parameters = full visible pane.
- `session.kill()` — destroys session and all its windows/panes.

**Exception hierarchy** relevant to error mapping:

- `LibTmuxException` (base)
- `TmuxSessionExists` — maps to `SessionAlreadyExistsError`
- `TmuxObjectDoesNotExist` — maps to `SessionNotFoundError` / `WindowNotFoundError` / `PaneNotFoundError`
- `BadSessionName` — names must not contain `.`, `:`, or `!`

**Pytest fixtures**: libtmux ships a pytest plugin auto-discovered via `Framework :: Pytest` entry point. Available fixtures: `server` (isolated tmux server on temporary socket), `session` (fresh session within isolated server), `window`, `pane`. Each creates isolated resources preventing interference with user's running tmux. The console-forwarding tests for the tmux backend use these fixtures for integration tests.

**Tmux runtime requirement**: tmux >= 3.2a must be installed. Detection: `shutil.which("tmux")`. The backend sets `is_available = True` only when tmux is found.

### How asyncssh Works: The SSH Backend Foundation

asyncssh (v2.22.0, EPL-2.0/GPL-2.0) is a fully async SSHv2 client and server implementation on Python asyncio. Its core value for this feature is `conn.run(command)` which executes remote commands and returns `SSHCompletedProcess` with `stdout`, `stderr`, and `exit_status` — all without blocking the event loop.

**Key API calls the SSH backend uses**:

- `asyncssh.connect(host, port, username=..., known_hosts="~/.ssh/known_hosts", connect_timeout=10)` — returns `SSHClientConnection`. Keys resolved from SSH agent first, then `~/.ssh/id_ed25519`, `~/.ssh/id_rsa` (asyncssh default behavior). The architecture spec explicitly requires `known_hosts="~/.ssh/known_hosts"` — NOT `None`.
- `conn.run(command, check=False)` — returns `SSHCompletedProcess`. The SSH backend always passes `check=False` and inspects `result.exit_status` manually to raise domain-specific exceptions.
- Connection objects support `async with` for automatic cleanup.

**Critical difference from tmux backend**: The SSH backend does NOT use libtmux. libtmux requires a local tmux socket; there is no mechanism to point it at a remote tmux server. Instead, the SSH backend runs tmux CLI commands on the remote host via `conn.run("tmux ...")` and parses their tab-delimited output using `-F` format strings. This is the same approach tmux itself uses for remote session management (ADR-003).

**Remote command patterns** — each backend method builds a tmux command with `-F` format strings for structured tab-delimited output:

- `list_sessions`: `tmux list-sessions -F "#{session_name}\t#{session_id}\t..."`
- `capture_pane`: `tmux capture-pane -t {session}:{window}.{pane} -p [-S -{lines}]`
- `send_keys`: `tmux send-keys -t {session}:{window}.{pane} [-l] {keys} [Enter]`

**Shell injection prevention**: All user-provided values (session names, keys, paths) must be escaped with `shlex.quote()` before interpolation into command strings. This is mandatory per the architecture spec security section.

**Async nature**: Unlike the tmux backend (sync, wrapped in `asyncio.to_thread`), the SSH backend is natively async. The session manager uses `backend.is_async` to determine calling convention — `asyncio.to_thread()` for sync backends, direct `await` for async backends.

**Connection pooling**: Connections are pooled by the session manager (not the SSH backend). The pool is a `dict[SSHTarget, SSHClientConnection]` keyed by frozen Pydantic model `SSHTarget(user, hostname, port)`. Connections are reused across tool calls to the same host and closed on server shutdown.

### How the Session Manager Orchestrates Backends

The session manager (`session_manager.py`) is the central dispatch layer. It sits between MCP tools and backends, handling five concerns:

1. **SSH URI parsing**: `_parse_ssh_uri(host)` parses `ssh://user@hostname:port` into `SSHTarget` using `urllib.parse.urlparse()`. Validates scheme is `ssh://`, user and hostname are present, port is 1-65535. Raises `InvalidURIError` for malformed input.

2. **Backend resolution**: When `host is None`, route to tmux backend. When `host` is an SSH URI, parse it and route to SSH backend. If tmux backend is `None` (not installed) and `host is None`, raise `BackendNotAvailableError`.

3. **Async wrapping**: For sync tmux backend, wrap every call in `asyncio.to_thread(self._tmux.method, args)`. For async SSH backend, call directly with `await self._ssh.method(conn, args)`.

4. **Connection pooling**: `_get_connection(target)` returns an existing connection or creates a new one via `asyncssh.connect()`. Dead connections are detected and replaced. `close_all()` tears down all connections.

5. **Error conversion**: Every dispatch method wraps its body in try/except for `ConsoleForwardingError` subclasses and converts them to `ToolError` with actionable messages. Domain exceptions never leak to MCP callers.

The factory function `create_session_manager()` probes for tmux via `shutil.which("tmux")`, instantiates backends accordingly, and returns a ready-to-use `SessionManager`. This is called at module level in `server.py`.

### How capture_pane Pagination Works

Pagination for `capture_pane` is split between two layers by design:

1. **Backend layer** (tmux_backend or ssh_backend): Handles the `lines` parameter. For tmux backend, calls `pane.capture_pane(start=-lines, end="-")` when `lines` is not None, or `pane.capture_pane()` for full visible pane. Returns `PaneOutput` with `total_lines` set to the count before any slicing and `offset=0`.

2. **Server layer** (server.py): Handles the `offset` parameter. After receiving `PaneOutput` from the session manager, applies `output_lines[offset:]` slicing. The returned dict includes `total_lines` from the backend (pre-offset count), `line_count` reflecting the count after offset, and the `offset` value echoed back.

This split follows the "No Invented Limits" rule from CLAUDE.md: the caller controls the capture window via `lines` (how many lines from the end) and `offset` (skip first N of those). No artificial truncation is applied. The tool description warns about MCP output token limits (10K warning, 25K max).

### Gastown Zombie Detection Patterns (Deferred to v2, but Informs Architecture)

The gastown Witness pattern uses ZFC (Zero-state-File Compliance) — tmux session existence IS the sole source of truth for agent liveness. The detection algorithm cross-references three checks:

1. `tmux has-session` — is the tmux session alive?
2. `IsAgentAlive()` — is the Claude process inside the session running?
3. `IsHealthy()` — has the session produced output within `maxInactivity` period?

This produces four states: `SessionHealthy`, `SessionZombie` (tmux alive, Claude dead), `SessionHung` (alive but no output), `SessionMissing`. While health monitoring is deferred from the MVP, the `SessionBackend` Protocol and the MCP tool API are designed so that a future `check_session_health()` tool can be added by composing existing tools (`list_sessions` for existence, `capture_pane` for activity) with process liveness checks.

### Plugin Validation Requirements

The plugin validator at `plugins/plugin-creator/scripts/plugin_validator.py` enforces checks that must pass for the final T10.1 task:

- **PL001-PL005**: plugin.json existence, valid JSON, `name` field present, component paths start with `./`, referenced files exist
- **PR001-PR005**: Agent/command registration, metadata completeness
- **FM001-FM008**: SKILL.md frontmatter validation — `name` and `description` required, no multiline YAML indicators, `tools` must be CSV string (not YAML array, per FM007)
- **SK006**: SKILL.md body over 4400 tokens triggers warning — extract to `references/`
- **SK007**: Body over 8800 tokens is an error — must split

Skills under `./skills/` are auto-discovered; they do not need explicit registration in the `skills` array. The `mcpServers` declaration and agent list in `plugin.json` must reference existing files with `./` prefix paths.

Pre-commit linting is run via `uv run prek run --files <file>` and must pass for all Python files and SKILL.md before the plugin is considered complete.

### Technical Reference Details

#### Key Dependency Versions

| Dependency | Version Constraint | Purpose |
|------------|-------------------|---------|
| `fastmcp` | `>=3.0.0rc1,<4` | MCP server framework; matches codebase convention |
| `libtmux` | `==0.53.*` | Typed tmux API; pinned per upstream pre-1.0 recommendation |
| `asyncssh` | `>=2.22.0,<3` | Async SSH client for remote session operations |
| `pydantic` | `>=2.0.0` | Data model validation; transitive dep of FastMCP |

Runtime system dependencies: `tmux >= 3.2a` (detected via `shutil.which("tmux")`), SSH agent or `~/.ssh/` keys (connection-time validation).

#### Module-Level Constants (server.py)

```python
_DEFAULT_SESSION_WIDTH: int = 220
_DEFAULT_SESSION_HEIGHT: int = 50
_SSH_CONNECT_TIMEOUT: int = 10
_TMUX_MIN_VERSION: str = "3.2a"
```

#### Annotation Dicts (server.py)

```python
_READONLY_ANNOTATIONS: dict[str, bool] = {
    "readOnlyHint": True, "destructiveHint": False,
    "idempotentHint": True, "openWorldHint": False,
}
_MUTATING_ANNOTATIONS: dict[str, bool] = {
    "readOnlyHint": False, "destructiveHint": False,
    "idempotentHint": True, "openWorldHint": False,
}
_DESTRUCTIVE_ANNOTATIONS: dict[str, bool] = {
    "readOnlyHint": False, "destructiveHint": True,
    "idempotentHint": False, "openWorldHint": False,
}
```

#### Data Model Definitions (models.py)

```python
class SessionInfo(BaseModel):
    name: str; id: str; windows: int; created: str
    attached: bool; width: int; height: int

class WindowInfo(BaseModel):
    name: str; id: str; index: int; panes: int
    active: bool; width: int; height: int

class PaneInfo(BaseModel):
    id: str; index: int; width: int; height: int
    active: bool; current_command: str; current_path: str

class PaneOutput(BaseModel):
    output: str; line_count: int; total_lines: int
    offset: int; session: str; pane: str

class SSHTarget(BaseModel, frozen=True):
    user: str; hostname: str; port: int = 22
```

#### Error Hierarchy (errors.py)

```text
ConsoleForwardingError(Exception)
+-- BackendNotAvailableError
+-- SessionNotFoundError
+-- SessionAlreadyExistsError
+-- PaneNotFoundError
+-- WindowNotFoundError
+-- SSHConnectionError
+-- SSHCommandError
+-- InvalidURIError
```

#### SessionBackend Protocol (backends/__init__.py)

```python
class SessionBackend(Protocol):
    @property
    def name(self) -> str: ...
    @property
    def is_available(self) -> bool: ...
    @property
    def is_async(self) -> bool: ...

    def list_sessions(self) -> list[SessionInfo]: ...
    def list_windows(self, session: str) -> list[WindowInfo]: ...
    def list_panes(self, session: str, window: str | None) -> list[PaneInfo]: ...
    def capture_pane(self, session: str, pane: str | None, window: str | None, lines: int | None) -> PaneOutput: ...
    def send_keys(self, session: str, keys: str, pane: str | None, window: str | None, enter: bool, literal: bool) -> None: ...
    def create_session(self, name: str, command: str | None, width: int, height: int, start_directory: str | None, environment: dict[str, str] | None) -> SessionInfo: ...
    def kill_session(self, session: str) -> None: ...
```

Note: The SSH backend intentionally diverges from this Protocol — its methods take an additional `conn: asyncssh.SSHClientConnection` parameter. The Protocol is satisfied by `TmuxBackend`; the session manager calls SSH backend methods directly.

#### MCP Tool to Annotation Mapping

| Tool | Annotations | Return Schema Keys |
|------|-------------|-------------------|
| `list_sessions(host=None)` | `_READONLY` | `sessions`, `count`, `host` |
| `list_windows(session, host=None)` | `_READONLY` | `windows`, `count`, `session`, `host` |
| `list_panes(session, window=None, host=None)` | `_READONLY` | `panes`, `count`, `session`, `window`, `host` |
| `capture_pane(session, pane=None, window=None, lines=None, offset=0, host=None)` | `_READONLY` | `output`, `line_count`, `total_lines`, `offset`, `session`, `pane`, `host` |
| `send_keys(session, keys, pane=None, window=None, enter=True, literal=False, host=None)` | `_MUTATING` | `sent`, `keys`, `session`, `pane`, `host` |
| `create_session(name, command=None, width=220, height=50, start_directory=None, environment=None, host=None)` | `_MUTATING` | `created`, `session`, `host` |
| `kill_session(session, host=None)` | `_DESTRUCTIVE` | `killed`, `session`, `host` |

#### Plugin Directory Structure

```text
plugins/console-forwarding/
+-- .claude-plugin/
|   +-- plugin.json
+-- mcp/
|   +-- __init__.py
|   +-- server.py
|   +-- models.py
|   +-- errors.py
|   +-- session_manager.py
|   +-- backends/
|       +-- __init__.py
|       +-- tmux_backend.py
|       +-- ssh_backend.py
+-- skills/
|   +-- console-forwarding/
|       +-- SKILL.md
+-- tests/
|   +-- __init__.py
|   +-- conftest.py
|   +-- test_models.py
|   +-- test_tmux_backend.py
|   +-- test_ssh_backend.py
|   +-- test_session_manager.py
|   +-- test_server.py
+-- README.md
```

#### Input Documents

| Document | Path | Content |
|----------|------|---------|
| Feature context | [plan/feature-context-console-forwarding-mcp-server-plugin.md](./feature-context-console-forwarding-mcp-server-plugin.md) | Resolved questions Q1-Q7, MVP scope, gap analysis, use scenarios |
| Architecture spec | [plan/architect-console-forwarding-mcp-server-plugin.md](./architect-console-forwarding-mcp-server-plugin.md) | Full API design, backend protocol, data models, error hierarchy, testing strategy, ADRs |
| Codebase patterns | [plan/codebase/plugin-mcp-patterns.md](./codebase/plugin-mcp-patterns.md) | Verified patterns from agentskill-kaizen: plugin.json, PEP 723, tool decorators, testing conftest |

#### Reference Files

| File | Path | Relevance |
|------|------|-----------|
| Kaizen MCP server | `plugins/agentskill-kaizen/mcp/server.py` | Reference FastMCP implementation: PEP 723 header, annotation dicts, tool decorator pattern, `asyncio.to_thread()`, `mcp.run()` entry point |
| Kaizen plugin.json | `plugins/agentskill-kaizen/.claude-plugin/plugin.json` | Reference `mcpServers` declaration with `uv run --script` and `${CLAUDE_PLUGIN_ROOT}` |
| Kaizen test conftest | `plugins/agentskill-kaizen/tests/conftest.py` | FastMCP stub-before-import pattern, mock_context fixture, test class organization |
| libtmux research | `research/developer-tools/libtmux.md` | Full API documentation: Server/Session/Window/Pane classes, send_keys, capture_pane, pytest fixtures, exception hierarchy, headless usage |
| asyncssh research | `research/async-libraries/asyncssh.md` | Full API documentation: connect(), conn.run(), SSHCompletedProcess, connection lifecycle, key resolution |
| dtach research | `research/developer-tools/dtach.md` | Deferred backend reference: Unix-domain socket sessions, -n fire-and-forget, -p stdin pipe, no capture capability |
| gastown research | `research/research-agent-patterns/gastown.md` | Zombie detection pattern: ZFC principle, SessionHealthy/Zombie/Hung/Missing states, Witness patrol architecture |
| Plugin validator | `plugins/plugin-creator/scripts/plugin_validator.py` | Validation checks: PL001-PL005, PR001-PR005, FM001-FM008, SK006/SK007 thresholds |

#### Architectural Decisions (from architecture spec)

| ADR | Decision | Rationale |
|-----|----------|-----------|
| ADR-001 | `typing.Protocol` over `abc.ABC` for `SessionBackend` | Structural typing enables duck typing; tmux (sync) and SSH (async) backends have different execution models |
| ADR-002 | Session manager owns `asyncio.to_thread()` wrapping | Tmux backend stays pure sync (testable without asyncio); SSH backend stays natively async (no unnecessary threads) |
| ADR-003 | SSH backend uses tmux CLI, not libtmux | libtmux requires local tmux socket; remote operations use `conn.run("tmux ...")` with `-F` format strings |
| ADR-004 | PEP 723 with local module imports | `server.py` declares deps inline; backend modules are plain `.py` files imported normally |
| ADR-005 | Connection pooling in session manager | Cross-tool connection reuse; centralized cleanup on shutdown |
| ADR-006 | No background threads or daemons | MCP tools are request-response; stdio subprocess lifecycle is simple |
