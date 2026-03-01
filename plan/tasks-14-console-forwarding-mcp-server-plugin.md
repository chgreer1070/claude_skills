---
description: "Executable task plan for the Console Forwarding MCP Server Plugin (GitHub Issue #364)"
version: "1.1"
feature_slug: "console-forwarding-mcp-server-plugin"
github_issue: 364
plugin_location: "plugins/console-forwarding/"
tasks:
  - T1.1: Plugin scaffold — directory structure and plugin.json
  - T2.1: Data models and error hierarchy
  - T3.1: Backend protocol and registry
  - T4.1: Tmux backend implementation
  - T5.1: SSH backend implementation
  - T6.1: Session manager — dispatch, pooling, async wrapping
  - T7.1: MCP server — FastMCP entry point and all 7 tools
  - T8.1: Test conftest and shared fixtures
  - T8.2: Data model tests
  - T8.3: Tmux backend tests
  - T8.4: SSH backend tests
  - T8.5: Session manager tests
  - T8.6: MCP tool integration tests
  - T9.1: SKILL.md for console-forwarding skill
  - T9.2: README.md
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
          +---> T3.1 (backend protocol + registry)
                  |
                  +---> T4.1 (tmux backend) --------+
                  |                                  |
                  +---> T5.1 (ssh backend)  ---------+
                                                     |
                                               T6.1 (session manager)
                                                     |
                                               T7.1 (MCP server + tools)
                                                     |
                              +----------------------+
                              |
                  T8.1 (conftest fixtures)
                  |    |
                  |    +---> T8.2 (model tests)       [also needs T2.1]
                  |    +---> T8.3 (tmux tests)        [also needs T4.1]
                  |    +---> T8.4 (ssh tests)         [also needs T5.1]
                  |    +---> T8.5 (session mgr tests) [also needs T6.1]
                  |    +---> T8.6 (server tests)      [also needs T7.1]
                  |
                  T9.1 (SKILL.md)   [also needs T7.1]
                  T9.2 (README.md)  [also needs T7.1]
                  T10.1 (validation) [needs all of the above]
```

## Parallelization Map

| Priority Wave | Tasks | Can Run Concurrently |
|--------------|-------|----------------------|
| 1 | T1.1 | No parallel candidates |
| 2 | T2.1 | No parallel candidates |
| 3 | T3.1 | No parallel candidates |
| 4 | T4.1, T5.1 | YES — distinct output files, no shared writes |
| 5 | T6.1 | Waits for T4.1 + T5.1 |
| 6 | T7.1 | Waits for T6.1 |
| 7 | T8.1 | Waits for T7.1 |
| 8 | T8.2, T8.3, T8.4, T8.5, T8.6 | YES — each writes a distinct test file |
| 9 | T9.1, T9.2, T10.1 | T9.1 and T9.2 are parallel; T10.1 waits for all |

---

## SYNC CHECKPOINT 1: Foundation Complete

**Convergence**: T1.1 + T2.1 + T3.1

**Quality gates**:

- `/home/user/claude_skills/plugins/console-forwarding/.claude-plugin/plugin.json` is valid JSON with `name` field
- `uv run python3 -c "import sys; sys.path.insert(0, 'plugins/console-forwarding/mcp'); import models, errors"` exits 0
- `plugins/console-forwarding/mcp/backends/__init__.py` defines `SessionBackend` Protocol (7 methods) and `BackendRegistry`
- `uv run plugins/plugin-creator/scripts/plugin_validator.py plugins/console-forwarding` exits 0 or shows only expected PR002 (server.py not yet fully importable)

**Reflection questions**:

- Are all Pydantic model fields complete for the 7 tool return schemas in the architecture spec?
- Does the `SessionBackend` Protocol cover all methods needed by both backends?
- Does `BackendRegistry` have the right interface for the session manager?

**Proceed to Priority 4 after approval.**

---

## SYNC CHECKPOINT 2: Backends Complete

**Convergence**: T4.1 + T5.1

**Quality gates**:

- `TmuxBackend.is_async` returns `False`; `SSHBackend.is_async` returns `True`
- `uv run prek run --files plugins/console-forwarding/mcp/backends/tmux_backend.py plugins/console-forwarding/mcp/backends/ssh_backend.py` exits 0
- Code inspection: every user-supplied value in `ssh_backend.py` passes through `shlex.quote()` before command interpolation

**Proceed to Priority 5 after approval.**

---

## SYNC CHECKPOINT 3: Server Complete

**Convergence**: T6.1 + T7.1

**Quality gates**:

- `grep -c "@mcp.tool" plugins/console-forwarding/mcp/server.py` outputs `7`
- `grep "_DESTRUCTIVE_ANNOTATIONS" plugins/console-forwarding/mcp/server.py` appears exactly once (on `kill_session`)
- `uv run prek run --files plugins/console-forwarding/mcp/server.py plugins/console-forwarding/mcp/session_manager.py` exits 0

**Proceed to Priority 7 after approval.**

---

## SYNC CHECKPOINT 4: Tests and Docs Complete

**Convergence**: T8.2 + T8.3 + T8.4 + T8.5 + T8.6 + T9.1 + T9.2 + T10.1

**Quality gates**:

- `uv run pytest plugins/console-forwarding/tests/ -v -m "not integration"` exits 0
- `uv run plugins/plugin-creator/scripts/plugin_validator.py plugins/console-forwarding` exits 0 with no ERROR-level findings
- `uv run prek run --files plugins/console-forwarding/skills/console-forwarding/SKILL.md` exits 0

---

## Task T1.1: Plugin Scaffold

**Status**: NOT STARTED
**Dependencies**: None
**Priority**: 1
**Complexity**: Low
**Agent**: python-cli-architect
**Skills**: ["python3-development"]

### Description

Create the full directory skeleton for `plugins/console-forwarding/` and populate `plugin.json`. This is the foundational scaffold all other tasks build on. No implementation logic is written here beyond the `plugin.json` manifest content.

Create these files and directories:

```text
plugins/console-forwarding/
    .claude-plugin/
        plugin.json              (COMPLETE — fully populated per architecture spec)
    mcp/
        __init__.py              (empty)
        backends/
            __init__.py          (stub — single comment "# Replaced by T3.1")
    skills/
        console-forwarding/
            SKILL.md             (stub — frontmatter with name+description only)
    tests/
        __init__.py              (empty)
    README.md                    (stub — title + one-line description only)
```

`mcp/server.py`, `mcp/models.py`, `mcp/errors.py`, `mcp/session_manager.py`, `mcp/backends/tmux_backend.py`, and `mcp/backends/ssh_backend.py` are NOT created here — they belong to later tasks.

### Acceptance Criteria

1. `plugins/console-forwarding/.claude-plugin/plugin.json` exists and is valid JSON with fields: `name`, `version`, `description`, `author`, `license`, `keywords`, `mcpServers`
2. `mcpServers` entry uses `"command": "uv"` with `"args": ["run", "--script", "${CLAUDE_PLUGIN_ROOT}/mcp/server.py"]`
3. `uv run plugins/plugin-creator/scripts/plugin_validator.py plugins/console-forwarding` exits 0 (PL001-PL005 pass; PR002 for server.py not yet existing is acceptable)
4. All directories in the skeleton exist on disk
5. `mcp/__init__.py` and `tests/__init__.py` are empty files
6. Placeholder `SKILL.md` contains valid YAML frontmatter with at minimum `name` and `description` fields

### Verification Steps

1. `uv run python3 -c "import json; d=json.load(open('plugins/console-forwarding/.claude-plugin/plugin.json')); assert d['name']=='console-forwarding'; assert 'mcpServers' in d; print('OK')"` — must print `OK`
2. `uv run plugins/plugin-creator/scripts/plugin_validator.py plugins/console-forwarding` — record all output; PL001/PL002/PL003 must not appear
3. `ls plugins/console-forwarding/mcp/ plugins/console-forwarding/tests/ plugins/console-forwarding/skills/console-forwarding/` — all directories must exist

All commands run from `/home/user/claude_skills`.

---

## Task T2.1: Data Models and Error Hierarchy

**Status**: NOT STARTED
**Dependencies**: Task T1.1
**Priority**: 2
**Complexity**: Medium
**Agent**: python-cli-architect
**Skills**: ["python3-development"]

### Description

Implement `plugins/console-forwarding/mcp/models.py` and `plugins/console-forwarding/mcp/errors.py`.

Both files are pure Python with no external system dependencies beyond Pydantic. They form the shared data layer consumed by all other modules.

#### models.py

Implement all Pydantic v2 models as specified in the architecture spec "Data Models" section:

- `SessionInfo` — 7 fields: `name: str`, `id: str`, `windows: int`, `created: str`, `attached: bool`, `width: int`, `height: int`
- `WindowInfo` — 7 fields: `name: str`, `id: str`, `index: int`, `panes: int`, `active: bool`, `width: int`, `height: int`
- `PaneInfo` — 7 fields: `id: str`, `index: int`, `width: int`, `height: int`, `active: bool`, `current_command: str`, `current_path: str`
- `PaneOutput` — 6 fields: `output: str`, `line_count: int`, `total_lines: int`, `offset: int`, `session: str`, `pane: str`
- `SSHTarget` — frozen model, 3 fields: `user: str`, `hostname: str`, `port: int = 22`

Add `model_config = ConfigDict(frozen=True)` to `SSHTarget` so it can be used as a dict key (hashable).

Use `from __future__ import annotations` at the top. Each model has a one-line docstring.

#### errors.py

Implement the exception hierarchy:

```text
ConsoleForwardingError(Exception)                  -- base
BackendNotAvailableError(ConsoleForwardingError)
SessionNotFoundError(ConsoleForwardingError)
SessionAlreadyExistsError(ConsoleForwardingError)
PaneNotFoundError(ConsoleForwardingError)
WindowNotFoundError(ConsoleForwardingError)
SSHConnectionError(ConsoleForwardingError)
SSHCommandError(ConsoleForwardingError)
InvalidURIError(ConsoleForwardingError)
```

Each exception class: accepts a descriptive message string as its first argument, has a one-line docstring. No imports from `fastmcp.exceptions` — `ToolError` conversion happens in the session manager.

### Acceptance Criteria

1. `models.py` defines exactly 5 classes: `SessionInfo`, `WindowInfo`, `PaneInfo`, `PaneOutput`, `SSHTarget`
2. All field names and types match the architecture spec exactly
3. `SSHTarget` is frozen and hashable: `hash(SSHTarget(user="u", hostname="h", port=22))` does not raise
4. `errors.py` defines exactly 9 classes rooted at `ConsoleForwardingError`
5. Both files import cleanly: `uv run python3 -c "import sys; sys.path.insert(0, 'plugins/console-forwarding/mcp'); import models, errors"` exits 0
6. `uv run prek run --files plugins/console-forwarding/mcp/models.py plugins/console-forwarding/mcp/errors.py` exits 0

### Verification Steps

1. `uv run python3 -c "import sys; sys.path.insert(0, 'plugins/console-forwarding/mcp'); import models; s = models.SessionInfo(name='s', id='\$1', windows=1, created='2026-01-01T00:00:00', attached=False, width=220, height=50); print(s.model_dump())"` — must print a dict with all 7 keys
2. `uv run python3 -c "import sys; sys.path.insert(0, 'plugins/console-forwarding/mcp'); import models; t = models.SSHTarget(user='u', hostname='h'); d = {t: 1}; print('hashable:', len(d))"` — must print `hashable: 1`
3. `uv run python3 -c "import sys; sys.path.insert(0, 'plugins/console-forwarding/mcp'); import errors; e = errors.SessionNotFoundError('agent-3'); assert issubclass(type(e), errors.ConsoleForwardingError); print('hierarchy OK')"` — must print `hierarchy OK`
4. `uv run prek run --files plugins/console-forwarding/mcp/models.py plugins/console-forwarding/mcp/errors.py` — must exit 0

All commands run from `/home/user/claude_skills`.

---

## Task T3.1: Backend Protocol and Registry

**Status**: NOT STARTED
**Dependencies**: Task T2.1
**Priority**: 3
**Complexity**: Medium
**Agent**: python-cli-architect
**Skills**: ["python3-development"]

### Description

Implement `plugins/console-forwarding/mcp/backends/__init__.py` with the `SessionBackend` Protocol and `BackendRegistry` class. Replaces the stub from T1.1.

Per ADR-001 in the architecture spec, use `typing.Protocol` (structural typing), not `abc.ABC`. This enables duck typing without forced inheritance.

#### SessionBackend Protocol

Required properties:

- `name: str` — backend identifier (e.g., `"tmux"`, `"ssh"`)
- `is_available: bool` — whether the backend can be used in the current environment
- `is_async: bool` — whether methods are natively async or synchronous

Required methods (exact signatures from the architecture spec "Backend Abstraction" section):

- `list_sessions(self) -> list[SessionInfo]`
- `list_windows(self, session: str) -> list[WindowInfo]`
- `list_panes(self, session: str, window: str | None) -> list[PaneInfo]`
- `capture_pane(self, session: str, pane: str | None, window: str | None, lines: int | None) -> PaneOutput`
- `send_keys(self, session: str, keys: str, pane: str | None, window: str | None, enter: bool, literal: bool) -> None`
- `create_session(self, name: str, command: str | None, width: int, height: int, start_directory: str | None, environment: dict[str, str] | None) -> SessionInfo`
- `kill_session(self, session: str) -> None`

#### BackendRegistry

- Stores backends in a `dict[str, SessionBackend]` keyed by backend name
- `register(name: str, backend: SessionBackend) -> None`
- `get(name: str) -> SessionBackend | None`
- `available_backends() -> list[str]` — names of backends where `is_available` is `True`

### Acceptance Criteria

1. `backends/__init__.py` exports both `SessionBackend` and `BackendRegistry`
2. `SessionBackend` is a `typing.Protocol` subclass (not `abc.ABC`)
3. Protocol has all 3 properties and 7 methods with signatures matching the architecture spec exactly
4. `BackendRegistry.available_backends()` filters by `is_available`, not just presence in the registry
5. File imports cleanly: `uv run python3 -c "import sys; sys.path.insert(0, 'plugins/console-forwarding/mcp'); from backends import SessionBackend, BackendRegistry; print('OK')"` exits 0
6. `uv run prek run --files plugins/console-forwarding/mcp/backends/__init__.py` exits 0

### Verification Steps

1. `uv run python3 -c "import sys; sys.path.insert(0, 'plugins/console-forwarding/mcp'); from backends import BackendRegistry; r = BackendRegistry(); print('BackendRegistry OK')"` — must not raise
2. `uv run python3 -c "import sys; sys.path.insert(0, 'plugins/console-forwarding/mcp'); from backends import SessionBackend; import typing; print(issubclass(SessionBackend, typing.Protocol))"` — note: Protocol subclass check varies by Python version; alternatively verify `SessionBackend.__protocol_attrs__` exists
3. `uv run prek run --files plugins/console-forwarding/mcp/backends/__init__.py` — must exit 0

All commands run from `/home/user/claude_skills`.

---

## Task T4.1: Tmux Backend Implementation

**Status**: NOT STARTED
**Dependencies**: Task T3.1
**Priority**: 4
**Complexity**: High
**Agent**: python-cli-architect
**Skills**: ["python3-development"]

### Description

Implement `plugins/console-forwarding/mcp/backends/tmux_backend.py` — the libtmux-based local tmux backend. Can parallelize with T5.1.

This backend is fully synchronous (all libtmux operations are subprocess-based). The session manager wraps calls in `asyncio.to_thread()` — the backend itself must NOT use asyncio.

#### TmuxBackend class

Properties: `name` returns `"tmux"`, `is_available` returns `True` only if `shutil.which("tmux")` is not `None`, `is_async` returns `False`.

The backend uses `libtmux.Server()` to obtain the user's default tmux server. Do NOT create a custom socket.

#### Method implementations

**`list_sessions() -> list[SessionInfo]`**: Use `server.sessions` to enumerate. Map each `libtmux.Session` to `SessionInfo`. Field mappings: `name` = `session.name`, `id` = `session.id`, `windows` = `len(session.windows)`, `created` = `datetime.fromtimestamp(int(session.session_created)).isoformat()`, `attached` = `session.session_attached == "1"`, `width` = `int(session.session_width)`, `height` = `int(session.session_height)`. Raise `BackendNotAvailableError` if tmux is not installed.

**`list_windows(session: str) -> list[WindowInfo]`**: Resolve session. Raise `SessionNotFoundError` if not found. Map each `libtmux.Window` to `WindowInfo`.

**`list_panes(session: str, window: str | None) -> list[PaneInfo]`**: Resolve session, then window (active window if `window` is `None`). Raise `SessionNotFoundError` or `WindowNotFoundError`. Map each `libtmux.Pane` to `PaneInfo`.

**`capture_pane(session: str, pane: str | None, window: str | None, lines: int | None) -> PaneOutput`**: Resolve session, window, pane. Use `pane_obj.capture_pane()` to get output lines. Compute `total_lines = len(all_lines)` BEFORE slicing. If `lines` is not `None`, take `all_lines[-lines:]`. Construct `PaneOutput` with `offset=0` (offset is applied in `server.py`, not here).

**`send_keys(session: str, keys: str, pane: str | None, window: str | None, enter: bool, literal: bool) -> None`**: Resolve session, window, pane. Use `pane_obj.send_keys(keys, enter=enter, literal=literal)`.

**`create_session(name: str, command: str | None, width: int, height: int, start_directory: str | None, environment: dict[str, str] | None) -> SessionInfo`**: Check for duplicate — raise `SessionAlreadyExistsError` if session with that name exists. Use `server.new_session(session_name=name, x=width, y=height, ...)`. Return `SessionInfo` for the new session.

**`kill_session(session: str) -> None`**: Resolve session. Raise `SessionNotFoundError` if not found. Call `session_obj.kill()`.

#### Private helpers

- `_resolve_session(server, session: str) -> libtmux.Session` — try by name first, then by ID; raise `SessionNotFoundError` if not found
- `_resolve_window(session_obj, window: str | None) -> libtmux.Window` — `None` returns active window; raise `WindowNotFoundError` if not found
- `_resolve_pane(window_obj, pane: str | None) -> libtmux.Pane` — `None` returns active pane; raise `PaneNotFoundError` if not found

### Acceptance Criteria

1. `TmuxBackend` satisfies `SessionBackend` Protocol (all 3 properties + 7 methods with matching signatures)
2. `TmuxBackend.is_async` returns `False`
3. `TmuxBackend.is_available` returns `False` gracefully when tmux binary is absent (does not raise)
4. All resolution helpers raise the correct exception type with a descriptive message
5. `capture_pane` computes `total_lines` before any line slicing
6. No `asyncio` imports or `async/await` anywhere in this file
7. `uv run prek run --files plugins/console-forwarding/mcp/backends/tmux_backend.py` exits 0

### Verification Steps

1. `uv run python3 -c "import sys; sys.path.insert(0, 'plugins/console-forwarding/mcp'); from backends.tmux_backend import TmuxBackend; b = TmuxBackend(); print('is_async:', b.is_async)"` — must print `is_async: False`
2. `uv run python3 -c "import sys, inspect; sys.path.insert(0, 'plugins/console-forwarding/mcp'); from backends.tmux_backend import TmuxBackend; assert not inspect.iscoroutinefunction(TmuxBackend.list_sessions); print('no async OK')"` — must print `no async OK`
3. `grep -n "import asyncio\|async def\|await " plugins/console-forwarding/mcp/backends/tmux_backend.py` — must return empty
4. `uv run prek run --files plugins/console-forwarding/mcp/backends/tmux_backend.py` — must exit 0

All commands run from `/home/user/claude_skills`.

#### CoVe Checks

Key claims to verify before writing implementation:

- libtmux `Pane.capture_pane()` return type (list of strings vs single string)
- Correct API for session lookup via QueryList in libtmux v0.53
- Whether `server.new_session` accepts `x` and `y` for dimensions in libtmux v0.53

Verification questions:

1. Does `libtmux.Pane.capture_pane()` return `list[str]` or `str`?
2. Is `server.sessions.get(session_name=name)` the correct QueryList API for lookup?
3. Does `server.new_session(session_name=name, x=width, y=height)` accept `x`/`y` params in libtmux v0.53?

Evidence to collect:

- Read `/home/user/claude_skills/plan/feature-context-console-forwarding-mcp-server-plugin.md` section "Existing Infrastructure > libtmux Research" to confirm API surface before writing code.

Revision rule:

- If any API claim cannot be confirmed from the research doc, add a `# NOTE: unverified API — verify against libtmux 0.53 docs` comment and implement conservatively. Do not guess.

---

## Task T5.1: SSH Backend Implementation

**Status**: NOT STARTED
**Dependencies**: Task T3.1
**Priority**: 4
**Complexity**: High
**Agent**: python-cli-architect
**Skills**: ["python3-development"]

### Description

Implement `plugins/console-forwarding/mcp/backends/ssh_backend.py` — the asyncssh-based remote tmux backend. Can parallelize with T4.1.

This backend is natively async. It does NOT use libtmux — it runs tmux CLI commands on the remote host via `await conn.run("tmux ...")` and parses tab-delimited output.

Per ADR-003: libtmux operates on a local tmux socket and cannot reach a remote host. The tmux CLI with `-F` format strings provides structured remote output.

#### SSHBackend class

Properties: `name` returns `"ssh"`, `is_available` returns `True` (asyncssh is a Python dependency, always available), `is_async` returns `True`.

#### Connection model

`SSHBackend` does NOT own the connection pool. Each method receives an `asyncssh.SSHClientConnection` as a `conn` parameter. The session manager (T6.1) owns connection pooling and passes `conn` when calling SSH backend methods. This signature diverges from the Protocol because of `conn` — the session manager calls SSH backend methods directly, not through the Protocol dispatch.

#### Remote command methods (all async)

Pattern for each method:

1. Build tmux command string with `shlex.quote()` applied to ALL user-supplied arguments
2. `result = await conn.run(cmd, check=False)`
3. Check `result.exit_status` — non-zero raises the appropriate domain exception
4. Parse `result.stdout` as tab-separated lines using the tmux format strings

**Remote command table** (from architecture spec "SSH Backend: Remote Command Model"):

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

Apply `shlex.quote()` to every user-supplied value before string interpolation: session names, keys content, pane IDs, window names, paths, command strings. Mandatory per the architecture spec "Security Considerations" section.

#### Output parsing

Parse tab-separated output. For `"1"`/`"0"` boolean fields, convert with `value == "1"`. For integer fields, convert with `int()`. For timestamps, convert Unix epoch to ISO: `datetime.fromtimestamp(int(ts)).isoformat()`.

### Acceptance Criteria

1. `SSHBackend.is_async` returns `True`
2. `SSHBackend.is_available` returns `True`
3. All remote command methods are `async def`
4. Every user-supplied value is wrapped in `shlex.quote()` before interpolation
5. Tab-delimited parsing correctly converts `"1"`/`"0"` to `bool` and numeric strings to `int`
6. Non-zero exit from `conn.run()` raises the correct domain exception
7. `uv run prek run --files plugins/console-forwarding/mcp/backends/ssh_backend.py` exits 0

### Verification Steps

1. `uv run python3 -c "import sys; sys.path.insert(0, 'plugins/console-forwarding/mcp'); from backends.ssh_backend import SSHBackend; b = SSHBackend(); print('is_async:', b.is_async)"` — must print `is_async: True`
2. `uv run python3 -c "import sys, inspect; sys.path.insert(0, 'plugins/console-forwarding/mcp'); from backends.ssh_backend import SSHBackend; assert inspect.iscoroutinefunction(SSHBackend.list_sessions); print('async OK')"` — must print `async OK`
3. `grep -c "shlex.quote" plugins/console-forwarding/mcp/backends/ssh_backend.py` — count must be >= 5 (at minimum one per method accepting user input)
4. `uv run prek run --files plugins/console-forwarding/mcp/backends/ssh_backend.py` — must exit 0

All commands run from `/home/user/claude_skills`.

#### CoVe Checks

Key claims to verify before writing implementation:

- `asyncssh.SSHCompletedProcess` attribute names for stdout, stderr, exit status
- Whether `conn.run()` is a coroutine and its return type

Verification questions:

1. Is the return of `await conn.run(command)` an object with `.stdout`, `.stderr`, `.exit_status` attributes?
2. Does `asyncssh.connect()` return a context manager (`async with`) or a bare connection object?

Evidence to collect:

- Read `/home/user/claude_skills/plan/feature-context-console-forwarding-mcp-server-plugin.md` section "asyncssh Research" to confirm API before writing connection usage.

Revision rule:

- If asyncssh API cannot be confirmed from the research doc, add `# NOTE: unverified asyncssh API` and implement defensively. Do not guess attribute names.

---

## Task T6.1: Session Manager

**Status**: NOT STARTED
**Dependencies**: Task T4.1, Task T5.1
**Priority**: 5
**Complexity**: High
**Agent**: python-cli-architect
**Skills**: ["python3-development"]

### Description

Implement `plugins/console-forwarding/mcp/session_manager.py` — the central dispatch layer between MCP tools and backends.

Responsibilities:

1. SSH URI parsing into `SSHTarget`
2. Backend resolution: `host=None` -> tmux backend; `host="ssh://..."` -> SSH backend
3. Async wrapping: sync tmux calls use `asyncio.to_thread()`; async SSH calls use direct `await`
4. SSH connection pooling: `dict[SSHTarget, asyncssh.SSHClientConnection]` keyed by frozen `SSHTarget`
5. Error conversion: all `ConsoleForwardingError` subclasses caught and re-raised as `ToolError`
6. Graceful degradation: local calls when tmux unavailable raise `ToolError` with installation guidance

#### SSH URI parsing

`_parse_ssh_uri(host: str) -> SSHTarget`:

- Input: `"ssh://user@hostname:port"` or `"ssh://user@hostname"` (port defaults to 22)
- Raise `InvalidURIError("Invalid SSH URI '{host}'. Expected format: ssh://user@hostname:port")` for any malformed input
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

#### Connection pool

`async def _get_connection(self, target: SSHTarget) -> asyncssh.SSHClientConnection`:

- Return existing connection if `target in self._connections` and connection is not closed
- Create new: `asyncssh.connect(host=target.hostname, port=target.port, username=target.user, known_hosts="~/.ssh/known_hosts", connect_timeout=_SSH_CONNECT_TIMEOUT)`
- Raise `SSHConnectionError` on asyncssh connection failure

`async def close_all(self) -> None`: Close all pooled connections and clear dict.

#### Dispatch methods

Implement async dispatch matching the 7 MCP tools. Pattern:

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

Apply this pattern for all 7 methods with appropriate parameter threading.

#### Error conversion

Wrap each dispatch method in `try/except` catching `ConsoleForwardingError` subclasses, re-raise as `ToolError` per architecture spec "ToolError Conversion" section:

- `SessionNotFoundError("agent-3")` -> `ToolError("Session 'agent-3' not found. Use list_sessions() to see available sessions.")`
- `BackendNotAvailableError("tmux")` -> `ToolError("tmux is not installed. Install tmux >= 3.2a for local sessions. Remote SSH sessions are available via host parameter.")`
- `SSHConnectionError(host, reason)` -> `ToolError("SSH connection to {host} failed: {reason}. Check SSH keys and host availability.")`
- All other `ConsoleForwardingError` subclasses -> `ToolError(str(exception))`

#### Module-level factory

```python
def create_session_manager() -> SessionManager:
    """Create a SessionManager with detected backends."""
    import shutil
    from backends.tmux_backend import TmuxBackend
    from backends.ssh_backend import SSHBackend
    tmux_backend = TmuxBackend() if shutil.which("tmux") else None
    return SessionManager(tmux_backend=tmux_backend, ssh_backend=SSHBackend())
```

Module constant: `_SSH_CONNECT_TIMEOUT: int = 10`

### Acceptance Criteria

1. `_parse_ssh_uri("ssh://user@host:2222")` returns `SSHTarget(user="user", hostname="host", port=2222)`
2. `_parse_ssh_uri("ssh://user@host")` returns `SSHTarget(user="user", hostname="host", port=22)`
3. `_parse_ssh_uri("http://user@host")` raises `InvalidURIError`
4. Dispatch methods use `asyncio.to_thread()` for tmux backend calls (not direct `await`)
5. Dispatch methods use direct `await` for SSH backend calls (not `to_thread`)
6. All 8 `ConsoleForwardingError` subclasses are caught and converted to `ToolError` — no domain exceptions leak
7. `create_session_manager()` returns a `SessionManager` without raising even when tmux is absent
8. `uv run prek run --files plugins/console-forwarding/mcp/session_manager.py` exits 0

### Verification Steps

1. `uv run python3 -c "import sys; sys.path.insert(0, 'plugins/console-forwarding/mcp'); from session_manager import _parse_ssh_uri; t = _parse_ssh_uri('ssh://deploy@buildserver:2222'); print(t.user, t.hostname, t.port)"` — must print `deploy buildserver 2222`
2. `uv run python3 -c "import sys; sys.path.insert(0, 'plugins/console-forwarding/mcp'); from session_manager import create_session_manager; m = create_session_manager(); print('OK', type(m).__name__)"` — must print `OK SessionManager`
3. `grep -c "asyncio.to_thread" plugins/console-forwarding/mcp/session_manager.py` — must be >= 7 (one per dispatch method)
4. `uv run prek run --files plugins/console-forwarding/mcp/session_manager.py` — must exit 0

All commands run from `/home/user/claude_skills`.

---

## Task T7.1: MCP Server — FastMCP Entry Point and All 7 Tools

**Status**: NOT STARTED
**Dependencies**: Task T6.1
**Priority**: 6
**Complexity**: High
**Agent**: python-cli-architect
**Skills**: ["python3-development", "fastmcp-creator"]

### Description

Implement `plugins/console-forwarding/mcp/server.py` — the PEP 723 entry point and all 7 MCP tool definitions.

Reference: `plugins/agentskill-kaizen/mcp/server.py` lines 1-15 (PEP 723 header), lines 58-70 (annotation dicts), line 83 (FastMCP instantiation), line 614 (`mcp.run()`).

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

- `_READONLY_ANNOTATIONS`: `readOnlyHint: True, destructiveHint: False, idempotentHint: True, openWorldHint: False`
- `_MUTATING_ANNOTATIONS`: `readOnlyHint: False, destructiveHint: False, idempotentHint: True, openWorldHint: False`
- `_DESTRUCTIVE_ANNOTATIONS`: `readOnlyHint: False, destructiveHint: True, idempotentHint: False, openWorldHint: False`

#### FastMCP instantiation and startup

```python
mcp = FastMCP("console-forwarding", mask_error_details=False)
session_manager = create_session_manager()
```

#### 7 MCP tools

Each tool is a thin async function. Parameters and return schemas must exactly match the architecture spec "MCP Tool API" section.

| Tool | Annotations | Required Params | Optional Params |
|------|-------------|-----------------|-----------------|
| `list_sessions` | `_READONLY_ANNOTATIONS` | — | `host=None` |
| `list_windows` | `_READONLY_ANNOTATIONS` | `session` | `host=None` |
| `list_panes` | `_READONLY_ANNOTATIONS` | `session` | `window=None, host=None` |
| `capture_pane` | `_READONLY_ANNOTATIONS` | `session` | `pane=None, window=None, lines=None, offset=0, host=None` |
| `send_keys` | `_MUTATING_ANNOTATIONS` | `session, keys` | `pane=None, window=None, enter=True, literal=False, host=None` |
| `create_session` | `_MUTATING_ANNOTATIONS` | `name` | `command=None, width=220, height=50, start_directory=None, environment=None, host=None` |
| `kill_session` | `_DESTRUCTIVE_ANNOTATIONS` | `session` | `host=None` |

Each tool returns `dict[str, Any]` matching the return schema in the architecture spec. Use `model.model_dump()` to serialize Pydantic objects.

Tool docstrings must match the description text in the architecture spec exactly (they become the tool's description visible to the MCP client).

#### capture_pane offset handling

The `offset` parameter is handled in `server.py`:

1. Obtain `PaneOutput` from `session_manager.capture_pane(...)`
2. Split `pane_output.output` on newlines
3. Apply offset: skip first `offset` lines, rejoin
4. `total_lines` preserved from `pane_output.total_lines`
5. `line_count` = count after offset applied

#### Entry point

```python
if __name__ == "__main__":
    mcp.run()
```

### Acceptance Criteria

1. File begins with the exact PEP 723 shebang line `#!/usr/bin/env -S uv --quiet run --active --script`
2. All 4 dependencies declared with correct version constraints in the PEP 723 block
3. All 7 MCP tools defined with correct `@mcp.tool(annotations=...)` decorators
4. `list_sessions`, `list_windows`, `list_panes`, `capture_pane` use `_READONLY_ANNOTATIONS`
5. `send_keys`, `create_session` use `_MUTATING_ANNOTATIONS`
6. `kill_session` uses `_DESTRUCTIVE_ANNOTATIONS`
7. `capture_pane` offset slicing is applied in `server.py` (not delegated to backend)
8. `uv run prek run --files plugins/console-forwarding/mcp/server.py` exits 0

### Verification Steps

1. `head -1 plugins/console-forwarding/mcp/server.py` — must output `#!/usr/bin/env -S uv --quiet run --active --script`
2. `grep -c "@mcp.tool" plugins/console-forwarding/mcp/server.py` — must output `7`
3. `grep "_DESTRUCTIVE_ANNOTATIONS" plugins/console-forwarding/mcp/server.py` — must appear exactly once
4. `grep -n "offset" plugins/console-forwarding/mcp/server.py` — must show offset slicing logic in the `capture_pane` tool body
5. `uv run prek run --files plugins/console-forwarding/mcp/server.py` — must exit 0

All commands run from `/home/user/claude_skills`.

---

## Task T8.1: Test Fixtures — conftest.py

**Status**: NOT STARTED
**Dependencies**: Task T7.1
**Priority**: 7
**Complexity**: Medium
**Agent**: python-pytest-architect
**Skills**: ["python3-development"]

### Description

Implement `plugins/console-forwarding/tests/conftest.py` — shared test fixtures for all test modules.

Reference: `plugins/agentskill-kaizen/tests/conftest.py` (FastMCP stub pattern lines 36-85, `mock_context` fixture lines 268-278).

#### FastMCP stub (required)

Apply the stub-before-import pattern from the kaizen reference. The stub makes `@mcp.tool` a no-op decorator, enabling direct `await server.tool_name(...)` calls in tests. Add `plugins/console-forwarding/mcp` to `sys.path` before importing server modules. Restore real fastmcp after import.

#### Required fixtures (all function scope unless noted)

**`mock_tmux_backend`**: A `MagicMock` configured as a `TmuxBackend` surrogate. Set as attributes: `name="tmux"`, `is_available=True`, `is_async=False`. Set `list_sessions.return_value=[sample_session_info_data]`, other methods to sensible defaults.

**`mock_ssh_backend`**: An `AsyncMock` with `name="ssh"`, `is_available=True`, `is_async=True`. All async methods return appropriate default model objects.

**`session_manager`**: A `SessionManager` instance initialized with `mock_tmux_backend` and `mock_ssh_backend`. Bypasses real backend initialization.

**`mock_context`**: `AsyncMock` with `info=AsyncMock()`, `warning=AsyncMock()` attributes.

**`sample_session_info`** (module scope): Pre-built `SessionInfo(name="test-session", id="$1", windows=1, created="2026-01-01T00:00:00", attached=False, width=220, height=50)`.

**`sample_pane_output`** (module scope): Pre-built `PaneOutput(output="line1\nline2\nline3", line_count=3, total_lines=3, offset=0, session="test-session", pane="%1")`.

**`sample_window_info`** (module scope): Pre-built `WindowInfo` with valid field values.

**`sample_pane_info`** (module scope): Pre-built `PaneInfo` with valid field values.

### Acceptance Criteria

1. FastMCP stub is installed before importing server modules, then restored
2. All 8 fixtures defined: `mock_tmux_backend`, `mock_ssh_backend`, `session_manager`, `mock_context`, `sample_session_info`, `sample_pane_output`, `sample_window_info`, `sample_pane_info`
3. `uv run pytest plugins/console-forwarding/tests/ --collect-only -q` exits 0 (no `ImportError`)
4. `uv run prek run --files plugins/console-forwarding/tests/conftest.py` exits 0

### Verification Steps

1. `uv run pytest plugins/console-forwarding/tests/ --collect-only -q 2>&1 | tail -5` — must NOT show `ImportError` or `ModuleNotFoundError`
2. `uv run prek run --files plugins/console-forwarding/tests/conftest.py` — must exit 0

All commands run from `/home/user/claude_skills`.

---

## Task T8.2: Data Model Tests

**Status**: NOT STARTED
**Dependencies**: Task T8.1, Task T2.1
**Priority**: 8
**Complexity**: Low
**Agent**: python-pytest-architect
**Skills**: ["python3-development"]

### Description

Implement `plugins/console-forwarding/tests/test_models.py` — unit tests for `models.py` and `errors.py`. No external dependencies (no tmux, no SSH). Tests must pass in any environment.

Group tests into classes: `TestSessionInfo`, `TestWindowInfo`, `TestPaneInfo`, `TestPaneOutput`, `TestSSHTarget`, `TestErrorHierarchy`.

**`TestSessionInfo`**: valid construction, `model_dump()` returns all 7 keys, missing required field raises `ValidationError`

**`TestSSHTarget`**: port defaults to 22, frozen (mutation raises `ValidationError` or `TypeError`), hashable (usable as dict key), two instances with same values are equal and have same hash

**`TestErrorHierarchy`**: all 8 subclasses are subclasses of `ConsoleForwardingError`, `ConsoleForwardingError` is subclass of `Exception`, each exception can be raised and caught by its parent class

### Acceptance Criteria

1. All 6 test classes present: `TestSessionInfo`, `TestWindowInfo`, `TestPaneInfo`, `TestPaneOutput`, `TestSSHTarget`, `TestErrorHierarchy`
2. `uv run pytest plugins/console-forwarding/tests/test_models.py -v` exits 0 with all tests PASSED
3. `TestSSHTarget` covers frozen/hashable behavior
4. `uv run prek run --files plugins/console-forwarding/tests/test_models.py` exits 0

### Verification Steps

1. `uv run pytest plugins/console-forwarding/tests/test_models.py -v` — must exit 0
2. `uv run pytest plugins/console-forwarding/tests/test_models.py -v 2>&1 | grep -E "FAILED|ERROR"` — must return empty
3. `uv run prek run --files plugins/console-forwarding/tests/test_models.py` — must exit 0

All commands run from `/home/user/claude_skills`.

---

## Task T8.3: Tmux Backend Tests

**Status**: NOT STARTED
**Dependencies**: Task T8.1, Task T4.1
**Priority**: 8
**Complexity**: High
**Agent**: python-pytest-architect
**Skills**: ["python3-development"]

### Description

Implement `plugins/console-forwarding/tests/test_tmux_backend.py` — unit and integration tests for `TmuxBackend`.

Tests requiring a real tmux server must be marked `@pytest.mark.integration` AND `@pytest.mark.skipif(not shutil.which("tmux"), reason="tmux not installed")`. All integration tests use libtmux's built-in pytest fixtures (`server`, `session`, `window`, `pane`).

#### Test structure

**`TestTmuxBackendAvailability`** (no integration marker): `test_is_not_async`, `test_name_is_tmux`

**`TestTmuxBackendDiscovery`** (`@pytest.mark.integration`, uses `session` fixture): `test_list_sessions_returns_session_info`, `test_list_windows_returns_window_info`, `test_list_panes_returns_pane_info`, `test_session_not_found_raises`

**`TestTmuxBackendCapture`** (`@pytest.mark.integration`, uses `pane` fixture): `test_capture_pane_returns_output` (after `send_keys`, output captured contains sent text), `test_capture_pane_lines_limits_output`

**`TestTmuxBackendLifecycle`** (`@pytest.mark.integration`, uses `server` fixture): `test_create_and_kill_session`, `test_create_session_duplicate_raises`

### Acceptance Criteria

1. All integration tests have both `@pytest.mark.integration` and the `shutil.which` skip marker
2. `uv run pytest plugins/console-forwarding/tests/test_tmux_backend.py -v -m "not integration"` exits 0
3. Non-integration class requires no tmux binary and always passes
4. `uv run prek run --files plugins/console-forwarding/tests/test_tmux_backend.py` exits 0

### Verification Steps

1. `uv run pytest plugins/console-forwarding/tests/test_tmux_backend.py -v -m "not integration"` — must exit 0
2. `uv run pytest plugins/console-forwarding/tests/test_tmux_backend.py --collect-only -q` — must show all test names with no `ImportError`
3. `uv run prek run --files plugins/console-forwarding/tests/test_tmux_backend.py` — must exit 0

All commands run from `/home/user/claude_skills`.

---

## Task T8.4: SSH Backend Tests

**Status**: NOT STARTED
**Dependencies**: Task T8.1, Task T5.1
**Priority**: 8
**Complexity**: High
**Agent**: python-pytest-architect
**Skills**: ["python3-development"]

### Description

Implement `plugins/console-forwarding/tests/test_ssh_backend.py` — unit tests for `SSHBackend` using mocked asyncssh connections. No real SSH connections in any test.

#### Test structure

**`TestSSHBackendProperties`**: `test_is_async` (`is_async is True`), `test_is_available` (`is_available is True`), `test_name_is_ssh`

**`TestSSHBackendListSessions`** (`@pytest.mark.asyncio`): `test_list_sessions_parses_output` (mock stdout returns tab-separated tmux format, assert `list[SessionInfo]` with correct values), `test_list_sessions_empty_returns_empty_list`, `test_list_sessions_nonzero_exit_raises`

**`TestSSHBackendShellEscaping`** (`@pytest.mark.asyncio`): `test_session_name_with_special_chars_is_quoted` (session name `"; rm -rf /"` does not appear unquoted in the built command), `test_keys_content_is_quoted`

**`TestSSHBackendCapturePane`** (`@pytest.mark.asyncio`): `test_capture_pane_returns_pane_output`, `test_capture_pane_with_lines_parameter` (command includes `-S -10` when `lines=10`)

**`TestSSHBackendLifecycle`** (`@pytest.mark.asyncio`): `test_create_session_builds_correct_command` (contains `-d -s`, width, height), `test_kill_session_targets_correct_session`

### Acceptance Criteria

1. All tests use mocked asyncssh connections — no real SSH connections
2. `uv run pytest plugins/console-forwarding/tests/test_ssh_backend.py -v` exits 0 with all tests PASSED
3. Shell escaping tests verify `shlex.quote()` on special characters
4. All async tests use `@pytest.mark.asyncio`
5. `uv run prek run --files plugins/console-forwarding/tests/test_ssh_backend.py` exits 0

### Verification Steps

1. `uv run pytest plugins/console-forwarding/tests/test_ssh_backend.py -v` — must exit 0
2. `grep -c "asyncssh.connect\|real_ssh" plugins/console-forwarding/tests/test_ssh_backend.py` — must output `0`
3. `uv run prek run --files plugins/console-forwarding/tests/test_ssh_backend.py` — must exit 0

All commands run from `/home/user/claude_skills`.

---

## Task T8.5: Session Manager Tests

**Status**: NOT STARTED
**Dependencies**: Task T8.1, Task T6.1
**Priority**: 8
**Complexity**: High
**Agent**: python-pytest-architect
**Skills**: ["python3-development"]

### Description

Implement `plugins/console-forwarding/tests/test_session_manager.py` — unit tests for `SessionManager` using the `session_manager` fixture from conftest.

#### Test structure

**`TestSSHURIParsing`**: `test_full_uri`, `test_uri_without_port` (port=22), `test_invalid_scheme_raises`, `test_missing_user_raises`, `test_missing_host_raises`

**`TestSessionManagerDispatch`** (`@pytest.mark.asyncio`): `test_list_sessions_local_uses_tmux` (`host=None` calls `mock_tmux_backend.list_sessions`), `test_list_sessions_ssh_uses_ssh_backend` (`host="ssh://u@h"` calls ssh backend), `test_tmux_unavailable_raises_tool_error` (set `mock_tmux_backend.is_available = False`; dispatch raises `ToolError`), `test_session_not_found_converts_to_tool_error` (`SessionNotFoundError` raised by mock -> dispatch raises `ToolError` containing "not found")

**`TestConnectionPool`** (`@pytest.mark.asyncio`): `test_connection_reused_for_same_host` (two calls same host; `asyncssh.connect` called only once), `test_close_all_clears_pool` (after `close_all()`, `_connections` is empty)

### Acceptance Criteria

1. All 5 URI parsing tests cover valid and invalid cases
2. `uv run pytest plugins/console-forwarding/tests/test_session_manager.py -v` exits 0
3. `ConsoleForwardingError` subclasses confirmed to convert to `ToolError` (not leak)
4. All async tests use `@pytest.mark.asyncio`
5. `uv run prek run --files plugins/console-forwarding/tests/test_session_manager.py` exits 0

### Verification Steps

1. `uv run pytest plugins/console-forwarding/tests/test_session_manager.py -v` — must exit 0 with all PASSED
2. `uv run pytest plugins/console-forwarding/tests/test_session_manager.py -v 2>&1 | grep -E "FAILED|ERROR"` — must return empty
3. `uv run prek run --files plugins/console-forwarding/tests/test_session_manager.py` — must exit 0

All commands run from `/home/user/claude_skills`.

---

## Task T8.6: MCP Tool Integration Tests

**Status**: NOT STARTED
**Dependencies**: Task T8.1, Task T7.1
**Priority**: 8
**Complexity**: High
**Agent**: python-pytest-architect
**Skills**: ["python3-development"]

### Description

Implement `plugins/console-forwarding/tests/test_server.py` — MCP tool integration tests using the FastMCP stub pattern from conftest.

The stub makes decorated tools plain callables. Call them directly: `await server.list_sessions(...)`.

In each test, replace the module-level session manager: `import server as cf_server; cf_server.session_manager = session_manager_fixture`.

Import `ToolError` inside each test function (not at module top level) to avoid conftest stub ordering issues — per kaizen pattern.

#### Test structure

**`TestListSessions`** (`@pytest.mark.asyncio`): `test_returns_expected_schema` (result has `"sessions"`, `"count"`, `"host"` keys), `test_count_matches_sessions_length`

**`TestListWindows`** (`@pytest.mark.asyncio`): `test_returns_expected_schema` (result has `"windows"`, `"count"`, `"session"`, `"host"` keys)

**`TestListPanes`** (`@pytest.mark.asyncio`): `test_returns_expected_schema` (result has `"panes"`, `"count"`, `"session"`, `"window"`, `"host"` keys)

**`TestCapturePaneOffset`** (`@pytest.mark.asyncio`): `test_offset_zero_returns_all_lines`, `test_offset_skips_lines` (`offset=2` skips 2 lines; `line_count` = total - 2), `test_total_lines_reflects_pre_offset_count`

**`TestSendKeys`** (`@pytest.mark.asyncio`): `test_returns_sent_true`, `test_echoes_keys_in_response`

**`TestCreateSession`** (`@pytest.mark.asyncio`): `test_returns_created_true`, `test_default_dimensions` (omitting width/height uses 220x50)

**`TestKillSession`** (`@pytest.mark.asyncio`): `test_returns_killed_true`, `test_session_not_found_surfaces_as_tool_error`

**`TestGracefulDegradation`** (`@pytest.mark.asyncio`): `test_local_tools_fail_when_tmux_unavailable` (`session_manager._tmux = None`; `list_sessions(host=None)` raises `ToolError`), `test_ssh_tools_work_when_tmux_unavailable` (`session_manager._tmux = None`; `list_sessions(host="ssh://u@h")` succeeds)

### Acceptance Criteria

1. All 7 tool return schemas match architecture spec (correct keys)
2. `capture_pane` offset behavior tested: `total_lines` is pre-offset, `line_count` is post-offset
3. Graceful degradation tests confirm tmux-absent + SSH-present works
4. `uv run pytest plugins/console-forwarding/tests/test_server.py -v` exits 0
5. `uv run prek run --files plugins/console-forwarding/tests/test_server.py` exits 0

### Verification Steps

1. `uv run pytest plugins/console-forwarding/tests/test_server.py -v` — must exit 0 with all PASSED
2. `uv run pytest plugins/console-forwarding/tests/ -v -m "not integration"` — all non-integration tests pass together
3. `uv run prek run --files plugins/console-forwarding/tests/test_server.py` — must exit 0

All commands run from `/home/user/claude_skills`.

---

## Task T9.1: SKILL.md

**Status**: NOT STARTED
**Dependencies**: Task T7.1
**Priority**: 9
**Complexity**: Medium
**Agent**: general-purpose
**Skills**: ["write-to-skill-file"]

### Description

Write `plugins/console-forwarding/skills/console-forwarding/SKILL.md` — the user-facing skill. Replaces the stub from T1.1.

#### Required frontmatter

```yaml
---
name: console-forwarding
description: "MCP tools for managing tmux sessions on local and remote hosts via Claude Code"
tools: list_sessions, list_windows, list_panes, capture_pane, send_keys, create_session, kill_session
---
```

`tools` MUST be a CSV string (not a YAML array) per FM007 validator rule.

#### Required sections

**Core Workflow**: 3-step pattern: (1) `list_sessions()` to discover, (2) `capture_pane(session=..., lines=50)` to inspect, (3) `send_keys(session=..., keys=...)` to interact.

**Session Naming Conventions**: Recommended pattern `agent-{task-id}` or `agent-{role}`. Session names must not contain `.`, `:`, or `!`.

**SSH Remote Access**: URI format `ssh://user@hostname:port` (port defaults to 22). Keys from SSH agent or `~/.ssh/`. Known hosts checked against `~/.ssh/known_hosts`. Concrete example:

```text
list_sessions(host="ssh://deploy@build-server.corp.com")
capture_pane(session="ci-runner", host="ssh://deploy@build-server.corp.com", lines=100)
```

**Output Size Management**: Explain `lines` and `offset` for `capture_pane`. Warn about MCP token limits (10K soft, 25K hard). Recommend `lines=50` for routine checks.

**Troubleshooting**:

| Problem | Cause | Fix |
|---------|-------|-----|
| `ToolError: tmux is not installed` | tmux binary absent | `brew install tmux` or `apt install tmux` |
| `ToolError: Session 'X' not found` | Wrong session name | Call `list_sessions()` to enumerate |
| `ToolError: SSH connection to ... failed` | Auth failure or unreachable | Check SSH keys, verify `~/.ssh/known_hosts` |
| Output appears truncated | Large pane content | Use `lines` parameter; check `total_lines` in response |

### Acceptance Criteria

1. Valid YAML frontmatter with `name`, `description`, and `tools` as a CSV string (no FM007 error)
2. All 5 sections present: Core Workflow, Session Naming Conventions, SSH Remote Access, Output Size Management, Troubleshooting
3. SSH URI format matches architecture spec exactly (`ssh://user@hostname:port`)
4. `uv run prek run --files plugins/console-forwarding/skills/console-forwarding/SKILL.md` exits 0
5. Body token count is under 4400 (SK006 threshold)

### Verification Steps

1. `uv run prek run --files plugins/console-forwarding/skills/console-forwarding/SKILL.md` — must exit 0
2. `uv run plugins/plugin-creator/scripts/plugin_validator.py plugins/console-forwarding 2>&1 | grep -E "SK006|SK007|FM007"` — must return empty
3. `uv run python3 -c "f=open('plugins/console-forwarding/skills/console-forwarding/SKILL.md'); c=f.read(); f.close(); assert 'ssh://' in c; assert 'list_sessions' in c; print('content OK')"` — must print `content OK`

All commands run from `/home/user/claude_skills`.

---

## Task T9.2: README.md

**Status**: NOT STARTED
**Dependencies**: Task T7.1
**Priority**: 9
**Complexity**: Low
**Agent**: plugin-docs-writer
**Skills**: []

### Description

Write `plugins/console-forwarding/README.md` — project-level overview for developers who may extend, test, or install the plugin. Distinct from SKILL.md which targets AI sessions.

Required sections:

1. **What this plugin does** — one-paragraph overview
2. **Installation** — how to enable in Claude Code via plugin marketplace
3. **Available MCP tools** — table with tool name, annotation type (read-only / mutating / destructive), and one-line description for all 7 tools
4. **Development setup** — `uv run pytest plugins/console-forwarding/tests/ -v` and how to run integration tests
5. **Deferred features (v2)** — list from architecture spec "Deferred to v2" section

### Acceptance Criteria

1. All 5 sections present
2. MCP tools table lists all 7 tools; `kill_session` is marked destructive
3. Development setup section includes the exact test command
4. `uv run prek run --files plugins/console-forwarding/README.md` exits 0
5. File is 200-400 lines maximum

### Verification Steps

1. Read `plugins/console-forwarding/README.md` and count section headings — must be at least 5
2. `grep -c "kill_session" plugins/console-forwarding/README.md` — must output >= 1
3. `grep -c "destructive" plugins/console-forwarding/README.md` — must output >= 1
4. `uv run prek run --files plugins/console-forwarding/README.md` — must exit 0

All commands run from `/home/user/claude_skills`.

---

## Task T10.1: Plugin Validation and Lint Fixes

**Status**: NOT STARTED
**Dependencies**: Task T9.1, Task T9.2, Task T8.6
**Priority**: 10
**Complexity**: Low
**Agent**: linting-root-cause-resolver
**Skills**: ["python3-development"]

### Description

Run the plugin validator and all linting tools against the complete plugin. Fix any reported issues. Final quality gate before the plugin is implementation-complete.

#### Steps to execute

1. Plugin validator:

   ```bash
   uv run plugins/plugin-creator/scripts/plugin_validator.py plugins/console-forwarding
   ```

   Fix any PL, PR, FM, or SK errors. Document warnings intentionally accepted.

2. Prek linting on all Python files:

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

3. Non-integration tests:

   ```bash
   uv run pytest plugins/console-forwarding/tests/ -v -m "not integration"
   ```

4. Report all results. Fix root causes in this task — do not defer.

### Acceptance Criteria

1. `uv run plugins/plugin-creator/scripts/plugin_validator.py plugins/console-forwarding` exits 0 with no ERROR-level findings
2. All prek linting passes (exit 0) for all Python files listed above
3. `uv run pytest plugins/console-forwarding/tests/ -v -m "not integration"` exits 0 with all tests PASSED
4. No PL001, PL002, PL003, FM001, FM002, FM007 errors remain

### Verification Steps

1. `uv run plugins/plugin-creator/scripts/plugin_validator.py plugins/console-forwarding` — record full output; must exit 0 or show only WARNING-level findings
2. `uv run pytest plugins/console-forwarding/tests/ -v -m "not integration" 2>&1 | tail -10` — must show all PASSED
3. `uv run prek run --files plugins/console-forwarding/mcp/server.py plugins/console-forwarding/mcp/session_manager.py` — must exit 0

All commands run from `/home/user/claude_skills`.

---

## Context Manifest

The following files are the key inputs for all worker agents. Use absolute paths when passing to sub-agents.

| File | Purpose | Used By |
|------|---------|---------|
| `/home/user/claude_skills/plan/architect-console-forwarding-mcp-server-plugin.md` | Primary architecture spec — all sections | All tasks |
| `/home/user/claude_skills/plan/feature-context-console-forwarding-mcp-server-plugin.md` | Resolved feature Q&A, MVP scope, use cases | T1.1, T5.1, T9.1, T9.2 |
| `/home/user/claude_skills/plan/codebase/plugin-mcp-patterns.md` | Verified MCP server patterns from agentskill-kaizen | T1.1, T7.1, T8.1, T10.1 |
| `/home/user/claude_skills/plugins/agentskill-kaizen/mcp/server.py` | Reference FastMCP server (PEP 723, annotation dicts, mcp.run) | T1.1, T7.1, T8.1 |
| `/home/user/claude_skills/plugins/agentskill-kaizen/.claude-plugin/plugin.json` | Reference plugin.json with mcpServers declaration | T1.1 |
| `/home/user/claude_skills/plugins/agentskill-kaizen/tests/conftest.py` | Reference conftest with FastMCP stub pattern | T8.1 |
| `/home/user/claude_skills/plugins/plugin-creator/scripts/plugin_validator.py` | Plugin validator — error codes PL, PR, FM, SK | T10.1 |
| `/home/user/claude_skills/.claude/rules/linting-exceptions.md` | Linting exception conditions | T10.1 |
