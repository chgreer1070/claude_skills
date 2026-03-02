# Testing Patterns

**Analysis Date:** 2026-03-02
**Package:** claude_skills (monorepo with plugins)

---

## Test Framework

**Runner:** pytest
**Config:** `/home/user/claude_skills/pyproject.toml` (`[tool.pytest.ini_options]`)
**Parallelism:** `-n auto` (pytest-xdist)
**Async mode:** `asyncio_mode = "auto"` — NO per-test `@pytest.mark.asyncio` decorators needed (except `plugins/agentskill-kaizen/tests/` which uses them redundantly — see Anti-Patterns)

**Run Commands:**

```bash
# All tests
uv run pytest

# With verbose output and specific path
uv run pytest .claude/skills/backlog/tests/ -v

# Only fast (non-e2e) tests
uv run pytest -m "not e2e"

# E2E tests (requires GITHUB_TOKEN)
uv run pytest .claude/skills/backlog/tests/test_live_validation.py -m e2e -v

# With coverage
uv run pytest --cov=scripts
```

**Coverage config** (`pyproject.toml`):

```toml
[tool.coverage.run]
source = ["**/scripts"]
omit = ["tests/*", "*/tests/*", "**/test_*.py"]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "if __name__ == .__main__.:",
    "raise AssertionError",
    "raise NotImplementedError",
    "if TYPE_CHECKING:",
]
```

---

## Test File Locations

```text
.claude/skills/backlog/tests/          # 8 test files (backlog MCP server, core operations)
plugins/plugin-creator/tests/          # 20 test files (validator, CLI, manifests)
plugins/agentskill-kaizen/tests/       # 2 test files (MCP server, dashboard)
plugins/summarizer/tests/              # 1 test file (file_metrics)
.claude/skills/gh/tests/               # 1 test file (github_project_setup CLI)
```

**Full test file inventory:**

| File | Type | What it tests |
|------|------|--------------|
| `.claude/skills/backlog/tests/conftest.py` | Fixtures | `backlog_dir`, `mock_github`, `write_test_item` |
| `.claude/skills/backlog/tests/test_backlog_core_parsing.py` | Unit | `parsing.py` — pure functions, no GitHub |
| `.claude/skills/backlog/tests/test_backlog_core_models.py` | Unit | Data model validation |
| `.claude/skills/backlog/tests/test_backlog_core_operations.py` | Unit | Operations layer with mocked GitHub |
| `.claude/skills/backlog/tests/test_backlog_core_server.py` | Unit | FastMCP server tool routing |
| `.claude/skills/backlog/tests/test_backlog_core_github.py` | Unit | GitHub API integration layer |
| `.claude/skills/backlog/tests/test_scenarios.py` | Integration | Full MCP workflows with mocked GitHub |
| `.claude/skills/backlog/tests/test_backlog_gh_first.py` | Integration | GitHub-first listing flows |
| `.claude/skills/backlog/tests/test_live_validation.py` | E2E | Real GitHub API calls, requires `GITHUB_TOKEN` |
| `plugins/plugin-creator/tests/test_cli.py` | Integration | CLI exit codes and flag parsing |
| `plugins/plugin-creator/tests/test_frontmatter_validator.py` | Unit | YAML frontmatter schema validation |
| `plugins/plugin-creator/tests/test_auto_sync_manifests.py` | Unit | Pre-commit manifest sync idempotency |
| `plugins/plugin-creator/tests/test_skills_array_bugs.py` | Regression | 4 documented bugs in auto-discovery logic |
| `plugins/agentskill-kaizen/tests/test_server.py` | Unit | Async MCP tools (process mining) |
| `plugins/agentskill-kaizen/tests/test_dashboard.py` | Unit | Dashboard state management (stubbed panel/tornado) |
| `.claude/skills/gh/tests/test_github_project_setup.py` | Unit | CLI milestone/label/issue commands |

---

## Pytest Markers

Declared in `pyproject.toml` `[tool.pytest.ini_options]` with `--strict-markers`:

```toml
markers = [
    "demos: marks tests as demonstration tests",
    "e2e: marks tests as end-to-end tests",
    "integration: marks tests as integration tests",
    "slow: marks tests as slow (deselect with '-m \"not slow\"')",
    "unit: marks tests as unit tests",
]
```

**`--strict-markers` is set** — any undeclared marker raises an error. Register new markers here before using them.

### skipif Pattern

`pytest.mark.skipif` is used for environment-conditional skips. Two patterns:

**Module-level pytestmark** (applies to all tests in file):

```python
# .claude/skills/backlog/tests/test_live_validation.py:28
_HAS_TOKEN = bool(os.environ.get("GITHUB_TOKEN"))
pytestmark = [
    pytest.mark.e2e,
    pytest.mark.skipif(not _HAS_TOKEN, reason="GITHUB_TOKEN not set — skipping live tests")
]
```

**Mark assigned to a variable** (applied per-test via decorator):

```python
# plugins/plugin-creator/tests/test_auto_sync_manifests.py:58
_requires_prettier = pytest.mark.skipif(
    shutil.which("npx") is None, reason="npx not available — prettier tests require Node.js tooling"
)
```

**No `pytest.mark.xfail` is used anywhere** in these test suites. All known-failing tests in `test_skills_array_bugs.py` are written as regular assertions that fail against the current buggy implementation — not marked xfail.

---

## Test Organization Conventions

### Class-Based Grouping

All test files use class-based grouping. Classes group tests by the function under test or the scenario:

```python
# Pattern: class per function-under-test
class TestParseItemFile:
    """Tests for parse_item_file(text, path) -> BacklogItem."""

class TestFindItem:
    """Tests for find_item(items, selector) -> BacklogItem | None."""
```

```python
# Pattern: class per workflow scenario
class TestCreateBacklogItem:
    """Scenarios consumed by /create-backlog-item skill."""

class TestWorkBacklogItem:
    """Scenarios consumed by /work-backlog-item skill."""
```

Classes never inherit from `unittest.TestCase`. All test methods are plain functions.

### Function Naming

Two naming styles are present:

**Style A — plain verb naming** (backlog, gh tests):

```python
def test_parse_item_file_nested_meta_sets_title(self, tmp_path: Path) -> None:
def test_find_item_exact_title_match_returns_item(self) -> None:
def test_find_item_partial_title_match_returns_item(self) -> None:
```

Convention: `test_<function>_<condition>_<expected_outcome>`

**Style B — scenario naming** (scenario tests, live tests):

```python
async def test_create_item_with_github_issue(self, backlog_dir, mock_github):
async def test_l1_add_with_real_issue(self, live_items):
async def test_list_with_status(self, backlog_dir, mock_github, write_test_item):
```

Convention: `test_<scenario_description>` (no explicit state/outcome separation)

---

## Docstring Style

Two docstring styles are used. Choose the style matching the file you're adding to.

### Style A — Docstring with structured inline comments (plugin-creator tests)

Used in `plugins/plugin-creator/tests/` throughout. Each test has a docstring with three labeled fields:

```python
def test_valid_skill_frontmatter(self, tmp_path: Path) -> None:
    """Test validation passes for valid skill frontmatter.

    Tests: Valid skill SKILL.md with minimal frontmatter
    How: Create file with description only, validate
    Why: Ensure validator accepts valid minimal skill frontmatter
    """
```

Also appears in a compact single-line variant without sub-labels:

```python
def test_validator_instantiation(self) -> None:
    """Test FrontmatterValidator can be instantiated."""
```

### Style B — Short docstring or no docstring (backlog/kaizen tests)

Used in `.claude/skills/backlog/tests/` and `plugins/agentskill-kaizen/tests/`:

```python
async def test_backlog_add_success_returns_merged_result():
    """backlog_add passes params to operations.add_item and merges output."""
```

Or inline comments to explain test data behaviour:

```python
def test_parse_item_file_nested_meta_sets_title(self, tmp_path: Path) -> None:
    # name is a top-level key — survives stringification
    item = parse_item_file(_NESTED_META_FRONTMATTER, tmp_path / "item.md")
    assert item.title == "My Test Item"
```

---

## Arrange-Act-Assert Pattern

All tests follow implicit AAA. In backlog/kaizen tests, sections are not separated by blank lines or comments. In plugin-creator tests, a blank line typically separates arrange from act+assert:

```python
def test_name_field_added_from_directory_when_missing(self, tmp_path: Path) -> None:
    # Arrange
    skill_dir = tmp_path / "my-skill"
    skill_dir.mkdir()
    skill_md = skill_dir / "SKILL.md"
    skill_md.write_text("""...""")

    # Act
    validator = FrontmatterValidator()
    fixes = validator.fix(skill_md)

    # Assert
    assert any("name" in fix.lower() and "my-skill" in fix for fix in fixes)
    content = skill_md.read_text()
    assert "name: my-skill" in content
```

---

## Fixture Patterns

### conftest.py Location

Every test package has a `conftest.py` at its root. Fixtures are not shared across plugin boundaries.

### `tmp_path` (Built-in)

Used universally for file I/O test isolation. All test files that write to disk use `tmp_path`:

```python
def test_parse_item_file_nested_meta_sets_title(self, tmp_path: Path) -> None:
    item = parse_item_file(_NESTED_META_FRONTMATTER, tmp_path / "item.md")
```

### `monkeypatch` (Built-in)

Used to redirect module-level constants (e.g., `BACKLOG_DIR`) for filesystem isolation:

```python
# .claude/skills/backlog/tests/conftest.py:32-44
@pytest.fixture
def backlog_dir(tmp_path, monkeypatch):
    """Redirect BACKLOG_DIR to a temp directory for test isolation."""
    bd = tmp_path / ".claude" / "backlog"
    bd.mkdir(parents=True)
    monkeypatch.setattr("backlog_core.models.BACKLOG_DIR", bd)
    monkeypatch.setattr("backlog_core.operations.BACKLOG_DIR", bd)
    monkeypatch.setattr("backlog_core.parsing.BACKLOG_DIR", bd)
    return bd
```

### `mock_github` (Custom — backlog)

Patches all `backlog_core.operations.*` GitHub functions. Returns `dict[str, MagicMock]` for per-test override:

```python
# .claude/skills/backlog/tests/conftest.py:47-80
@pytest.fixture
def mock_github(monkeypatch):
    """Patch all github.py functions imported by operations.py."""
    mocks: dict[str, MagicMock] = {}
    defaults: dict[str, object] = {
        "try_get_github": None,
        "create_issue_for_item": 42,
        # ...
    }
    for name, default in defaults.items():
        mock = MagicMock(return_value=default)
        monkeypatch.setattr(f"backlog_core.operations.{name}", mock)
        mocks[name] = mock
    return mocks
```

Override a specific mock's return value per test:

```python
mock_github["create_issue_for_item"].return_value = 99
```

### `write_test_item` (Custom — backlog)

Factory fixture that creates a valid per-item file in `backlog_dir`:

```python
# .claude/skills/backlog/tests/conftest.py:83-112
@pytest.fixture
def write_test_item(backlog_dir):
    def _write(title, priority="P1", issue="", description="Test item", status="open", type_val="Feature") -> Path:
        ...
    return _write
```

Usage: `filepath = write_test_item("My Title", priority="P0", issue="#42")`

### `cli_runner` (Custom — plugin-creator)

Returns `_PlainCliRunner` that strips ANSI escape codes from stdout bytes. Required because GitHub Actions sets `FORCE_COLOR=1`:

```python
# plugins/plugin-creator/tests/conftest.py:37-51
class _PlainCliRunner(CliRunner):
    def invoke(self, *args, **kwargs):
        result = super().invoke(*args, **kwargs)
        result.stdout_bytes = _ANSI_ESCAPE.sub(b"", result.stdout_bytes)
        return result
```

### `mock_context` (Custom — agentskill-kaizen)

`AsyncMock` for `fastmcp.Context` with `.info` and `.warning` async methods:

```python
# plugins/agentskill-kaizen/tests/conftest.py:268-278
@pytest.fixture
def mock_context() -> AsyncMock:
    ctx = AsyncMock()
    ctx.info = AsyncMock()
    ctx.warning = AsyncMock()
    return ctx
```

### `live_items` (Custom — E2E, class-scoped)

Class-scoped fixture that creates a real temporary backlog directory, generates a UUID test prefix, tracks created GitHub issue numbers, and closes them on teardown:

```python
# .claude/skills/backlog/tests/test_live_validation.py:48-102
@pytest.fixture(scope="class")
def live_items(tmp_path_factory, monkeypatch_class):
    # redirects BACKLOG_DIR, yields ctx dict, closes issues on teardown
```

---

## Mocking Patterns

### `unittest.mock.patch` — direct function patching

Used in `test_backlog_core_server.py` for operations layer isolation:

```python
with patch("backlog_core.operations.add_item", return_value=op_result) as mock_add:
    response = await _call("backlog_add", {...})
mock_add.assert_called_once()
call_kwargs = mock_add.call_args.kwargs
```

### `monkeypatch.setattr` — module attribute replacement

Used in `conftest.py` fixtures to swap entire function references:

```python
monkeypatch.setattr("backlog_core.operations.create_issue_for_item", mock)
```

### `MagicMock` — PyGithub object stubs

Used in `test_github_project_setup.py` and `mock_github` fixture to simulate PyGithub objects:

```python
def _make_label(name: str) -> MagicMock:
    lbl = MagicMock()
    lbl.name = name
    return lbl
```

### Module-level stub injection — optional dependency isolation

Used when a test module imports code that depends on optional packages not installed in the test environment. Two patterns:

**Pattern A — `sys.modules` replacement before import** (`plugins/agentskill-kaizen/tests/conftest.py:36-85`):

```python
_stub_fastmcp = _types.ModuleType("fastmcp")
_stub_fastmcp.FastMCP = _StubMCP
sys.modules["fastmcp"] = _stub_fastmcp
import server as kaizen_server
# Restore real fastmcp after import
if _real_fastmcp is not None:
    sys.modules["fastmcp"] = _real_fastmcp
```

**Pattern B — `types.ModuleType` stubs** (`plugins/agentskill-kaizen/tests/test_dashboard.py`):

```python
_tornado_mod = types.ModuleType("tornado")
_tornado_web_mod = types.ModuleType("tornado.web")
class _StubRequestHandler: ...
_tornado_web_mod.RequestHandler = _StubRequestHandler
sys.modules["tornado"] = _tornado_mod
sys.modules["tornado.web"] = _tornado_web_mod
```

Both patterns are used when panel, holoviews, hvplot, or tornado are not installed.

### `importlib.util` — hyphenated script loading

Multiple test suites load scripts with hyphenated names (or for path-safety) via importlib:

```python
# Used in: plugin-creator/tests/conftest.py, test_auto_sync_manifests.py, test_skills_array_bugs.py
_VALIDATOR_PATH = Path(__file__).parent.parent / "scripts" / "plugin_validator.py"
spec = importlib.util.spec_from_file_location("plugin_validator", _VALIDATOR_PATH)
plugin_validator = importlib.util.module_from_spec(spec)
sys.modules["plugin_validator"] = plugin_validator
spec.loader.exec_module(plugin_validator)
```

---

## Async Test Patterns

### Global `asyncio_mode = "auto"` (preferred)

Set in `pyproject.toml` for the root workspace. Tests in `.claude/skills/backlog/tests/` and scenarios use this — no per-test decorator needed:

```python
# .claude/skills/backlog/tests/test_backlog_core_server.py — top-level async test functions
async def test_backlog_add_success_returns_merged_result():
    """backlog_add passes params ..."""
    with patch("backlog_core.operations.add_item", return_value=op_result) as mock_add:
        response = await _call("backlog_add", {...})
```

```python
# .claude/skills/backlog/tests/test_scenarios.py — class-based async tests
class TestCreateBacklogItem:
    async def test_create_item_with_github_issue(self, backlog_dir, mock_github):
        ...
```

### `@pytest.mark.asyncio` decorator (inconsistency — see Anti-Patterns)

Used in `plugins/agentskill-kaizen/tests/test_server.py` even though global `asyncio_mode = "auto"` is active. This is redundant but not harmful:

```python
@pytest.mark.asyncio
async def test_extracts_sequences(self, single_session_jsonl: Path) -> None:
    ...
```

### In-memory FastMCP transport

MCP server tests call tools via the `fastmcp.client.Client` in-memory transport — no network:

```python
async def _call(tool_name: str, params: dict | None = None) -> dict:
    """Call MCP tool via in-memory transport and parse JSON response."""
    async with Client(mcp) as client:
        result = await client.call_tool(tool_name, params or {})
    return json.loads(result.content[0].text)
```

This helper is duplicated in `test_backlog_core_server.py`, `test_scenarios.py`, and `test_live_validation.py` rather than being shared.

---

## Parametrize Patterns

### Inline value tuples

Used for pure string transformation tests (slugify, normalize):

```python
# .claude/skills/backlog/tests/test_backlog_core_parsing.py:679
@pytest.mark.parametrize(
    ("title", "expected"),
    [
        ("Hello World", "hello-world"),
        ("SAM: Error Recovery", "sam-error-recovery"),
        ("Add [new] feature (v2)", "add-new-feature-v2"),
        ("  Spaces   Around  ", "spaces-around"),
    ],
)
def test_title_to_slug_converts_title_to_valid_slug(self, title: str, expected: str) -> None:
    assert title_to_slug(title) == expected
```

### Single-value parametrize (list of strings)

Used for equivalence class testing:

```python
# .claude/skills/backlog/tests/test_backlog_core_models.py:451
@pytest.mark.parametrize("selector", ["", "abc", "123", "my-feature-item", "P1"])
def test_is_issue_selector_returns_false_for_non_issue(self, selector: str) -> None:
    ...
```

### Parametrize with expected error codes

Used to test that each invalid input produces the correct error code:

```python
# plugins/plugin-creator/tests/test_frontmatter_validator.py:500
@pytest.mark.parametrize(
    ("content", "expected_error_code"),
    [
        ("---\ndescription: short\n---\n", "SK004"),
        ("---\ndescription: ...\n---\n", "SK005"),
    ],
)
def test_validation_produces_expected_error_code(self, ...) -> None:
    ...
```

---

## Test Data Patterns

### Module-level string constants for fixture inputs

Used in `test_backlog_core_parsing.py` — test data strings defined at module level with explanatory comments:

```python
# .claude/skills/backlog/tests/test_backlog_core_parsing.py:46-99
# Nested-metadata format (produced by build_backlog_frontmatter) — only name/description accessible
_NESTED_META_FRONTMATTER = """\
---
name: My Test Item
description: A test description
metadata:
  source: test-source
  ...
---
Body content here.
"""

# Legacy flat format — all top-level keys are accessible
_FLAT_FRONTMATTER = """\
---
title: Legacy Title
...
"""
```

### Inline test data (inline strings in test body)

Used in plugin-creator tests — YAML frontmatter strings are written directly in test functions via `tmp_path` file creation.

### Builder helper methods

Used in test classes to construct test objects consistently:

```python
# .claude/skills/backlog/tests/test_backlog_core_parsing.py:349
class TestFindItem:
    def _make_items(self) -> list[BacklogItem]:
        return [
            BacklogItem(title="SAM Error Recovery", issue="#10", file_path="/tmp/p1-sam.md"),
            BacklogItem(title="Backlog Duplicate Detection", issue="#20", file_path="/tmp/p1-dup.md"),
        ]
```

---

## Documented Limitations and Known Behaviors in Tests

### Nested metadata stringification (FIXED in commit 0e0611f)

The module-level comment block in `test_backlog_core_parsing.py:26-44` documents the historical limitation that `_parse_frontmatter` stringified all frontmatter values, causing nested `metadata:` blocks to be inaccessible. The comment explains the prior behavior and why tests used flat-key frontmatter.

The test `TestParseFrontmatter::test_parse_frontmatter_nested_meta_preserves_metadata` (line 300) now documents the **fixed** behavior:

```python
def test_parse_frontmatter_nested_meta_preserves_metadata(self) -> None:
    # _parse_frontmatter now preserves nested metadata dicts instead of
    # stringifying them. The metadata block is extracted and returned as meta.
    _fm, meta, _body = _parse_frontmatter(_NESTED_META_FRONTMATTER)

    assert meta["source"] == "test-source"
    assert meta["priority"] == "P1"
```

The large comment block above line 47 explains WHY tests in that file still use flat frontmatter (backward compatibility reasons).

### FileType detection scope limitation

`test_hook_validator.py:75` uses "scope limitation" in a docstring:

```python
def test_js_outside_hooks_dir_not_detected_as_hook(self, tmp_path: Path) -> None:
    """...
    Tests: FileType detection scope limitation
    Why: Only .js/.cjs files inside a hooks/ directory are HOOK_SCRIPT
    """
```

This is documenting an intentional design constraint, not a bug.

### Bug regression tests (`test_skills_array_bugs.py`)

The file documents 4 bugs as regular (currently-failing) tests. The module docstring explicitly states:

> "Each test documents the DESIRED behaviour (what the code SHOULD do once fixed) and is written so it FAILS against the current buggy code."

This is the only file in the codebase that uses this "failing test as bug documentation" pattern. Tests are NOT marked `xfail` — they run and fail against the current code.

### Workaround: name field restoration (`test_frontmatter_validator.py:547-553`)

```python
class TestNameFieldRestoration:
    """Test that the name field is restored during auto-fix (bug workaround reversed).

    The Claude Code bug (2026-01-29) that caused plugin skills with a 'name' field to
    not appear as slash commands has been resolved. The validators previously removed the
    'name' field as a workaround; they now add it back when absent.
    """
```

Documents a corrected workaround — the bug is fixed and the behavior is now inverted.

### Workaround: FastMCP `@mcp.tool` decorator stub (`plugins/agentskill-kaizen/tests/conftest.py:26-34`)

```python
# Workaround: Replace FastMCP with a stub that makes ``@mcp.tool`` a
# transparent passthrough, then import the module. The actual async tool
# functions are plain coroutines -- the decorator only adds MCP metadata.
```

FastMCP 3.x `@mcp.tool` triggers Pydantic TypeAdapter resolution at decoration time, which fails on Python 3.11 due to `from __future__ import annotations` deferring type evaluation. The stub bypasses decorator resolution entirely.

### Threshold behavior documentation (`test_token_counting.py:206`)

```python
class TestThresholdBoundaries:
    """Test exact threshold boundary conditions.

    Tests: Thresholds trigger warnings/errors at exact token counts
    How: Create content with precise token counts at boundaries
    Why: Users need predictable behavior at documented thresholds
    """
```

The "Why" field uses "documented thresholds" to signal that this tests externally-documented contract behaviour.

---

## Coverage and Linting Rules for Tests

`pyproject.toml` `[tool.ruff.lint.per-file-ignores]` relaxes multiple linting rules for test files:

```toml
"**/tests/**" = [
    "ANN",  # Type annotations optional for test fixtures/methods
    "D",    # Docstring requirements relaxed for tests
    "DOC",  # Docstring content requirements relaxed
    "E501", # Line length relaxed for test data
    "EXE",  # Shebang executable check skipped for PEP723 test files
    "N",    # camelCase in test names acceptable when testing API fields
    "PLC",  # Local imports acceptable in test helpers
    "PLR",  # Testing private methods is valid test pattern
    "S",    # Security checks not needed in tests
    "SLF",  # Private name imports acceptable for testing internals
    "T",    # print() statements are intentional for CI output visibility
]
```

**Implication:** Test files may access private functions (`_parse_frontmatter`, `_filter_result_by_ignore`) and import them at function level without lint errors.

---

## Anti-Patterns Present in the Codebase

### 1. Duplicate `_call` helper

The `_call(tool_name, params)` async helper for FastMCP in-memory transport is copy-pasted across three files:
- `.claude/skills/backlog/tests/test_backlog_core_server.py:37`
- `.claude/skills/backlog/tests/test_scenarios.py:24`
- `.claude/skills/backlog/tests/test_live_validation.py:36`

A shared fixture or conftest helper would remove this duplication.

### 2. Redundant `@pytest.mark.asyncio` in agentskill-kaizen

`plugins/agentskill-kaizen/tests/test_server.py` decorates every async test method with `@pytest.mark.asyncio` despite `asyncio_mode = "auto"` being set globally. This is harmless but inconsistent with the backlog test style.

### 3. `sys.path.insert` in test files

Several test files manually insert paths into `sys.path` rather than relying on `pyproject.toml` `[tool.pytest.ini_options] pythonpath`:

```python
# plugins/plugin-creator/tests/test_frontmatter_validator.py:18
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
```

This pattern predates the centralized `pythonpath` config. The conftest.py for plugin-creator uses the same pattern at:
- `plugins/plugin-creator/tests/conftest.py:27-32`
- `plugins/agentskill-kaizen/tests/conftest.py:73-75`
- `.claude/skills/backlog/tests/conftest.py:21-23`

### 4. `monkeypatch_class` custom fixture in live tests

`.claude/skills/backlog/tests/test_live_validation.py:95-102` defines a custom `monkeypatch_class` fixture to work around pytest's lack of a built-in class-scoped monkeypatch. This is a known limitation that was addressed in pytest 6.2 via `MonkeyPatch.context()`, but not leveraged here.

---

## Where to Add New Tests

| Scenario | File location |
|----------|--------------|
| New backlog MCP tool | `.claude/skills/backlog/tests/test_backlog_core_server.py` |
| New backlog operation (with mock GitHub) | `.claude/skills/backlog/tests/test_scenarios.py` |
| New parsing function | `.claude/skills/backlog/tests/test_backlog_core_parsing.py` |
| New plugin-validator validator | `plugins/plugin-creator/tests/test_<validator_name>.py` |
| New plugin-creator CLI flag | `plugins/plugin-creator/tests/test_cli.py` |
| New kaizen MCP tool | `plugins/agentskill-kaizen/tests/test_server.py` |
| New summarizer script function | `plugins/summarizer/tests/test_file_metrics.py` |
| New gh CLI command | `.claude/skills/gh/tests/test_github_project_setup.py` |

**When adding async tests to backlog or scenarios:** do NOT add `@pytest.mark.asyncio`. The global `asyncio_mode = "auto"` handles it.

**When adding async tests to agentskill-kaizen:** match existing style and add `@pytest.mark.asyncio` per method (for consistency within that file).

**When adding a new pytest marker:** declare it in `pyproject.toml` `[tool.pytest.ini_options] markers` before first use — `--strict-markers` enforces this.

---

_Testing analysis: 2026-03-02_
