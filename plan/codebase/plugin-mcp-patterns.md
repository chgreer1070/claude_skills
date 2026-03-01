# Plugin MCP Patterns

**Analysis Date:** 2026-03-01
**Reference Plugin:** `plugins/agentskill-kaizen` (FastMCP server with full test suite)

---

## Plugin Directory Structure

A plugin with an MCP server follows this layout:

```text
plugins/{plugin-name}/
├── .claude-plugin/
│   └── plugin.json            # Plugin manifest (required)
├── mcp/
│   ├── server.py              # FastMCP MCP server (PEP 723 inline script)
│   └── dashboard.py           # Optional companion module (imported by server.py)
├── agents/
│   └── {agent-name}.md        # Agent files (optional)
├── skills/
│   └── {skill-name}/
│       └── SKILL.md           # Skill files (optional)
├── scripts/
│   └── {script-name}.py       # Utility scripts (optional)
└── tests/
    ├── conftest.py             # Shared fixtures
    ├── test_server.py          # Tool tests
    └── test_dashboard.py      # Companion module tests (if any)
```

**Source:** `plugins/agentskill-kaizen/` — verified via directory listing.

---

## plugin.json Format

**Location:** `plugins/{plugin-name}/.claude-plugin/plugin.json`

**Minimal valid plugin.json (name is the only required field):**

```json
{
  "name": "my-plugin",
  "version": "0.1.0",
  "description": "...",
  "author": {
    "name": "Your Name",
    "url": "https://github.com/your-handle"
  }
}
```

**Full plugin.json with MCP server and agents:**

```json
{
  "name": "agentskill-kaizen",
  "version": "0.6.78",
  "description": "...",
  "author": {
    "name": "Jamie Nelson",
    "url": "https://github.com/Jamie-BitFlight"
  },
  "license": "MIT",
  "keywords": ["kaizen", "transcript-analysis"],
  "agents": ["./agents/improvement-generator.md", "./agents/transcript-analyst.md"],
  "mcpServers": {
    "kaizen-analysis": {
      "command": "uv",
      "args": ["run", "--script", "${CLAUDE_PLUGIN_ROOT}/mcp/server.py"]
    }
  }
}
```

**Source:** `plugins/agentskill-kaizen/.claude-plugin/plugin.json:1-32`

### mcpServers Declaration Patterns

Two patterns observed:

**Pattern 1 — PEP 723 script (own server.py):**

```json
"mcpServers": {
  "my-server": {
    "command": "uv",
    "args": ["run", "--script", "${CLAUDE_PLUGIN_ROOT}/mcp/server.py"]
  }
}
```

**Pattern 2 — uvx pre-built server:**

```json
"mcpServers": {
  "kaizen-duckdb": {
    "command": "uvx",
    "args": ["mcp-server-motherduck", "--db-path", "${CLAUDE_PLUGIN_ROOT}/data/kaizen.duckdb", "--read-only"],
    "env": {
      "HOME": "$USERPROFILE"
    }
  }
}
```

**Source:** `plugins/agentskill-kaizen/.claude-plugin/plugin.json:19-31`

### Environment Variable: `${CLAUDE_PLUGIN_ROOT}`

Use `${CLAUDE_PLUGIN_ROOT}` in `args` and command paths to reference files within the plugin directory. This variable resolves to the absolute path of the plugin directory at runtime, which is a copy in Claude Code's plugin cache — not the development source directory.

### Required Fields

The only field that triggers a validator error (PL003) when missing is `name`. All other fields are optional but recommended.

- `name` (required): kebab-case string matching plugin directory name
- `version` (recommended): semver string
- `description` (recommended): human-readable description
- `author` (recommended): object with `name` and `url`
- `agents` (conditional): array of `./`-relative paths to agent `.md` files
- `mcpServers` (conditional): object with server config entries
- `skills` (optional): array of `./`-relative skill directory paths — omit to rely on auto-discovery of `./skills/`

All component paths must start with `./` (PL004 error otherwise).

**Source:** `plugins/plugin-creator/scripts/plugin_validator.py:289-294`

---

## MCP Server (server.py) Structure

### PEP 723 Inline Script Metadata

Every `mcp/server.py` uses the PEP 723 inline script format so `uv run --script` handles dependencies without a separate `pyproject.toml`:

```python
#!/usr/bin/env -S uv --quiet run --active --script
# /// script
# requires-python = ">=3.11,<3.14"
# dependencies = [
#     "fastmcp>=3.0.0rc1,<4",
#     "other-dep>=1.0.0",
# ]
# ///
```

**Shebang line:** `#!/usr/bin/env -S uv --quiet run --active --script`

The `--active` flag reuses an active venv when present; `--quiet` suppresses uv output. This shebang is for direct execution. When invoked from `plugin.json`, the command is `uv run --script {path}` — the shebang is not used.

**Source:** `plugins/agentskill-kaizen/mcp/server.py:1-15`

### Imports

```python
from __future__ import annotations

import asyncio
import json
import pathlib
from typing import Any

from fastmcp import Context, FastMCP
from fastmcp.exceptions import ToolError
```

Use `from __future__ import annotations` for deferred annotation evaluation. Import `Context` only when tools use it (add `*, context: Context` parameter). Import `ToolError` for input validation and error signalling.

**Source:** `plugins/agentskill-kaizen/mcp/server.py:30-46`

### FastMCP Instance

Declare one module-level `mcp` instance:

```python
mcp = FastMCP("server-name", mask_error_details=False)
```

`mask_error_details=False` exposes full exception messages to the MCP client — appropriate for development and agent-facing tools.

**Source:** `plugins/agentskill-kaizen/mcp/server.py:83`

### Entry Point

```python
if __name__ == "__main__":
    mcp.run()
```

`mcp.run()` uses stdio transport by default, which is what `uv run --script` expects for MCP servers.

**Source:** `plugins/agentskill-kaizen/mcp/server.py:610-614`

---

## Tool Decorator Patterns

### Read-Only Tool (most tools)

Use `@mcp.tool(annotations=_READONLY_ANNOTATIONS)` for all tools that do not mutate state:

```python
_READONLY_ANNOTATIONS: dict[str, bool] = {
    "readOnlyHint": True,
    "destructiveHint": False,
    "idempotentHint": True,
    "openWorldHint": False,
}

@mcp.tool(annotations=_READONLY_ANNOTATIONS)
async def my_tool(param: str) -> dict[str, Any]:
    ...
```

### Destructive/Side-Effect Tool

For tools that cause visible side effects (opening windows, launching processes, writing files) but are not destructive to data:

```python
_DASHBOARD_ANNOTATIONS: dict[str, bool] = {
    "readOnlyHint": False,
    "destructiveHint": False,
    "idempotentHint": True,
    "openWorldHint": True,
}

@mcp.tool(annotations=_DASHBOARD_ANNOTATIONS)
def open_dashboard() -> dict[str, str | bool]:
    ...
```

**Source:** `plugins/agentskill-kaizen/mcp/server.py:58-70`

### Annotation Constants

Define annotation dicts as module-level constants rather than inline in each decorator. This avoids repetition and makes annotation strategy explicit.

**Source:** `plugins/agentskill-kaizen/mcp/server.py:58-70`

---

## Context Parameter Usage

Use `context: Context` as a keyword-only parameter for progress reporting. It must be keyword-only (`*` before it):

```python
@mcp.tool(annotations=_READONLY_ANNOTATIONS)
async def discover_process_model(
    glob_path: str = "",
    sequences: dict[str, list[str]] | None = None,
    *,
    context: Context,
) -> str:
    await context.info("Resolving tool sequences...")
    ...
```

`context` is provided automatically by FastMCP — callers do not pass it. Available methods: `context.info(msg)`, `context.warning(msg)`.

Do not add `context` to tools that do not use it.

**Source:** `plugins/agentskill-kaizen/mcp/server.py:301-303`

---

## Error Handling with ToolError

Raise `ToolError` for invalid inputs and unrecoverable states that should surface as user-visible errors:

```python
from fastmcp.exceptions import ToolError

def _resolve_sequences(glob_path: str, sequences: dict | None) -> dict:
    if sequences is not None:
        if not sequences:
            raise ToolError("No target sequences found")
        return sequences
    if not glob_path:
        raise ToolError("Provide either glob_path or sequences for target")
    resolved = _extract_tool_sequences_impl(glob_path)
    if not resolved:
        raise ToolError("No target tool sequences found in matched files")
    return resolved
```

`ToolError` propagates the message string to the MCP client as a structured error response. Do not use `raise RuntimeError` or `raise ValueError` — use `ToolError`.

**Source:** `plugins/agentskill-kaizen/mcp/server.py:263-275`

---

## Async Patterns for CPU-Bound Work

FastMCP tools are `async`. Use `asyncio.to_thread` to offload blocking / CPU-bound operations:

```python
@mcp.tool(annotations=_READONLY_ANNOTATIONS)
async def extract_tool_sequences(glob_path: str) -> dict[str, list[str]]:
    return await asyncio.to_thread(_extract_tool_sequences_impl, glob_path)
```

Define the implementation in a separate synchronous `_impl` function and call it via `asyncio.to_thread`. This keeps the async tool signature minimal and makes the implementation independently testable.

**Source:** `plugins/agentskill-kaizen/mcp/server.py:281-295`

---

## Private Helper Pattern

Extract reusable logic into private `_` functions so tools can be tested independently and tools can share logic without decorating each other:

```python
# Private implementation — testable directly
def _extract_tool_sequences_impl(glob_path: str) -> dict[str, list[str]]:
    ...

# Public MCP tool — thin async wrapper
@mcp.tool(annotations=_READONLY_ANNOTATIONS)
async def extract_tool_sequences(glob_path: str) -> dict[str, list[str]]:
    return await asyncio.to_thread(_extract_tool_sequences_impl, glob_path)
```

**The comment in server.py explains the rationale:**

> "This private helper exists to avoid type-checker FunctionTool errors when decorated tools call each other directly."

**Source:** `plugins/agentskill-kaizen/mcp/server.py:224-244`

---

## Synchronous Tools

Tools that complete quickly (no I/O, no CPU-bound work) can be synchronous:

```python
@mcp.tool(annotations=_DASHBOARD_ANNOTATIONS)
def open_dashboard() -> dict[str, str | bool]:
    from dashboard import get_dashboard_url  # noqa: PLC0415
    url = get_dashboard_url()
    if url is None:
        raise ToolError("Dashboard is not running.")
    return {"url": url, "opened_browser": False, "message": f"Dashboard running at {url}"}
```

**Source:** `plugins/agentskill-kaizen/mcp/server.py:583-607`

---

## Testing Patterns

### conftest.py Strategy: Stub FastMCP Before Import

The key challenge: `@mcp.tool` triggers Pydantic TypeAdapter resolution at decoration time, which fails in test environments with deferred annotations. The solution is to stub FastMCP before importing server.py.

**Pattern from `plugins/agentskill-kaizen/tests/conftest.py`:**

```python
# 1. Save real fastmcp
_real_fastmcp = sys.modules.get("fastmcp")
_real_fastmcp_exc = sys.modules.get("fastmcp.exceptions")

# 2. Create stub — makes @mcp.tool a no-op
class _StubMCP:
    def __init__(self, *args, **kwargs): pass

    def tool(self, *args, **kwargs):
        def decorator(fn): return fn
        if args and callable(args[0]):
            return args[0]
        return decorator

    def run(self): pass

# 3. Install stub (preserving real ToolError)
_stub_fastmcp = types.ModuleType("fastmcp")
_stub_fastmcp.FastMCP = _StubMCP
_stub_fastmcp.Context = AsyncMock
_stub_exceptions = types.ModuleType("fastmcp.exceptions")
_stub_exceptions.ToolError = _ToolError  # from real fastmcp.exceptions
sys.modules["fastmcp"] = _stub_fastmcp
sys.modules["fastmcp.exceptions"] = _stub_exceptions

# 4. Add mcp/ to sys.path, import server
_MCP_DIR = str(Path(__file__).resolve().parent.parent / "mcp")
sys.path.insert(0, _MCP_DIR)
import server as kaizen_server

# 5. Restore real fastmcp
if _real_fastmcp is not None:
    sys.modules["fastmcp"] = _real_fastmcp
if _real_fastmcp_exc is not None:
    sys.modules["fastmcp.exceptions"] = _real_fastmcp_exc
```

This makes decorated tool functions plain callables, enabling direct `await kaizen_server.my_tool(...)` calls in tests.

**Source:** `plugins/agentskill-kaizen/tests/conftest.py:36-85`

### mock_context Fixture

Always provide a `mock_context` fixture for tools that accept `context: Context`:

```python
@pytest.fixture
def mock_context() -> AsyncMock:
    ctx = AsyncMock()
    ctx.info = AsyncMock()
    ctx.warning = AsyncMock()
    return ctx
```

Pass as `context=mock_context` in test calls.

**Source:** `plugins/agentskill-kaizen/tests/conftest.py:268-278`

### File-Based Fixtures

Use `tmp_path` (pytest built-in) plus explicit fixture functions to create test JSONL/data files:

```python
@pytest.fixture
def single_session_jsonl(jsonl_dir: Path) -> Path:
    jsonl_dir.mkdir(parents=True, exist_ok=True)
    records = [_make_assistant_tool_use("Read"), _make_assistant_tool_use("Grep")]
    session_file = jsonl_dir / "session-abc.jsonl"
    session_file.write_text("\n".join(json.dumps(r) for r in records), encoding="utf-8")
    return jsonl_dir
```

Fixtures return a directory path (not the file path) so tests can pass glob patterns like `str(path / "*.jsonl")`.

**Source:** `plugins/agentskill-kaizen/tests/conftest.py:129-142`

### Data Builder Helpers

Define `_make_*` helper functions for constructing test records (not fixtures):

```python
def _make_assistant_tool_use(tool_name: str) -> dict[str, Any]:
    return {"type": "assistant", "message": {"content": [{"type": "tool_use", "name": tool_name, "input": {}}]}}

def _make_user_message(text: str, *, timestamp: str = "") -> dict[str, Any]:
    record: dict[str, Any] = {"type": "user", "message": {"content": text}}
    if timestamp:
        record["timestamp"] = timestamp
    return record
```

**Source:** `plugins/agentskill-kaizen/tests/conftest.py:93-111`

### Test Class Organization

Group tests into classes by tested unit:

```python
class TestExtractToolSequences:
    """Tests for the extract_tool_sequences async MCP tool."""

    @pytest.mark.asyncio
    async def test_extracts_sequences(self, single_session_jsonl: Path) -> None:
        glob_path = str(single_session_jsonl / "*.jsonl")
        result = await kaizen_server.extract_tool_sequences(glob_path)
        assert isinstance(result, dict)
        assert "session-abc" in result
```

**Source:** `plugins/agentskill-kaizen/tests/test_server.py:428-449`

### ToolError Assertion Pattern

```python
@pytest.mark.asyncio
async def test_raises_on_missing_input(self, mock_context: AsyncMock) -> None:
    from fastmcp.exceptions import ToolError
    with pytest.raises(ToolError):
        await kaizen_server.discover_process_model("", None, context=mock_context)
```

Import `ToolError` inside the test to avoid conftest stub ordering issues.

**Source:** `plugins/agentskill-kaizen/tests/test_server.py:488-494`

### Stubbing Heavy Third-Party Modules

For modules with heavy dependencies (panel, holoviews, tornado), stub them before importing the module under test:

```python
_tornado_mod = types.ModuleType("tornado")
_tornado_web_mod = types.ModuleType("tornado.web")

class _StubRequestHandler:
    def __init__(self, *args, **kwargs): ...
    def set_header(self, name, value): ...
    def write(self, chunk): ...

_tornado_web_mod.RequestHandler = _StubRequestHandler
sys.modules["tornado"] = _tornado_mod
sys.modules["tornado.web"] = _tornado_web_mod
# ... repeat for panel, holoviews, hvplot ...

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "mcp"))
import dashboard
```

**Source:** `plugins/agentskill-kaizen/tests/test_dashboard.py:37-113`

### autouse Fixture for Module State Reset

When testing modules with module-level state, use `autouse=True` to reset before/after each test:

```python
@pytest.fixture(autouse=True)
def _reset_module_state() -> Any:
    dashboard._reset_dashboard_state()
    yield
    dashboard._reset_dashboard_state()
```

**Source:** `plugins/agentskill-kaizen/tests/test_dashboard.py:121-129`

---

## Plugin Validator Checks

Run validation with:

```bash
uv run plugins/plugin-creator/scripts/plugin_validator.py plugins/{plugin-name}
```

### plugin.json Checks (PL codes)

| Code | Check | Fix |
|------|-------|-----|
| PL001 | `.claude-plugin/plugin.json` file missing | Create the file |
| PL002 | Invalid JSON syntax | Fix JSON syntax |
| PL003 | `name` field missing | Add `"name": "my-plugin"` |
| PL004 | Component path does not start with `./` | Use `"./agents/foo.md"` not `"agents/foo.md"` |
| PL005 | Referenced component file does not exist | Create file or remove from array |

**Source:** `plugins/plugin-creator/scripts/plugin_validator.py:289-294`

### Plugin Registration Checks (PR codes)

| Code | Check | Fix |
|------|-------|-----|
| PR001 | Agent or command exists but is not registered in plugin.json | Add to `agents` or `commands` array |
| PR002 | Registered path in plugin.json does not exist | Remove entry or create the file |
| PR003 | Metadata fields (repository, homepage, author) not populated | Add optional fields |
| PR004 | Repository URL mismatches git remote | Update `repository` field |
| PR005 | Registered command path is a skill directory | Move from `commands` to `skills` |

Skills under `./skills/` are auto-discovered and do not need explicit registration in the `skills` array. Agents and commands always require explicit registration.

**Source:** `plugins/plugin-creator/scripts/plugin_validator.py:317-321`, `3103-3121`

### Skill Complexity Checks (SK codes)

| Code | Threshold | Action |
|------|-----------|--------|
| SK006 | 4400 tokens (body only) | Warning — extract to `references/` |
| SK007 | 8800 tokens (body only) | Error — must split skill |

**Source:** `plugins/plugin-creator/scripts/plugin_validator.py:192-194`

### Frontmatter Checks (FM codes)

| Code | Check |
|------|-------|
| FM001 | Missing `name` or `description` field |
| FM002 | Invalid YAML syntax |
| FM004 | Forbidden multiline indicator (`>-` or `\|-`) |
| FM007 | `tools` field is YAML array (must be CSV string) |
| FM008 | `skills` field is YAML array (must be CSV string) |

**Source:** `plugins/plugin-creator/scripts/plugin_validator.py:258-268`

---

## Suppress Validation Errors Per-Path

Create `.claude-plugin/validator.json` to suppress specific error codes for specific paths:

```json
{
  "ignore": {
    "skills/legacy-skill": ["SK006"],
    "agents/experimental-agent.md": ["PD001", "PD002"]
  }
}
```

Keys are path prefixes relative to the plugin root. Matching is prefix-based, so `"skills/"` suppresses for all paths starting with `skills/`.

**Source:** `plugins/plugin-creator/scripts/plugin_validator.py:453-481`

---

## Key Constants and Naming

### Server Name Convention

Pass a human-readable name to `FastMCP(...)`:

```python
mcp = FastMCP("kaizen-analysis", mask_error_details=False)
```

This name appears in MCP protocol handshakes and server listings.

**Source:** `plugins/agentskill-kaizen/mcp/server.py:83`

### Module-Level Constants

Define tunable values as module-level named constants with type annotations:

```python
_DEFAULT_MIN_SUPPORT: int = 2
_DEFAULT_N_CLUSTERS: int = 3
_TOP_TOOLS_PER_CLUSTER: int = 5
_KMEANS_RANDOM_STATE: int = 42
```

Use `_` prefix for private constants. Reference them in function signatures as defaults.

**Source:** `plugins/agentskill-kaizen/mcp/server.py:52-56`

---

## Full Plugin Creation Checklist

1. Create directory: `plugins/{plugin-name}/`
2. Create `.claude-plugin/plugin.json` with `name` field
3. Create `mcp/server.py` with PEP 723 header, `fastmcp>=3.0.0rc1,<4` dependency
4. Define annotation dicts (`_READONLY_ANNOTATIONS`, `_DASHBOARD_ANNOTATIONS`)
5. Instantiate `mcp = FastMCP("{server-name}", mask_error_details=False)`
6. Implement each tool as `async def` with `@mcp.tool(annotations=...)` decorator
7. Use `asyncio.to_thread` for blocking operations
8. Raise `ToolError` for input validation failures
9. Add `if __name__ == "__main__": mcp.run()`
10. Add `"mcpServers"` entry to `plugin.json` using `uv run --script` pattern
11. Create `tests/conftest.py` with FastMCP stub and shared fixtures
12. Create `tests/test_server.py` with classes per tool
13. Run: `uv run plugins/plugin-creator/scripts/plugin_validator.py plugins/{plugin-name}`

---

_Analysis based on direct file reads of `plugins/agentskill-kaizen/` (server, tests, plugin.json) and `plugins/plugin-creator/scripts/plugin_validator.py`. All code examples are excerpts from those files._
