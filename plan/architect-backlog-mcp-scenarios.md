# Architecture Spec: Backlog MCP Scenario Testing

## Overview

This spec defines the test architecture for two complementary test suites that close the coverage gaps in the backlog FastMCP server. Suite 1 adds 28 scenario integration tests that exercise the full operations layer with mocked GitHub and filesystem boundaries. Suite 2 adds 11 live validation tests that exercise the full stack against real GitHub infrastructure. Both suites use the in-memory FastMCP `Client(mcp)` transport and follow existing test patterns from [test_backlog_core_server.py](../../../.claude/skills/backlog/tests/test_backlog_core_server.py).

## Design Decisions

### 1. Mock at github.py boundary, not operations.py

The existing 42 tests mock `operations.*` functions, validating server-to-operations parameter forwarding. The new scenario tests mock `github.*` functions imported into `operations.py`, letting the full operations logic execute with real parsing, file I/O, and business rules. This catches regressions in the operations layer that the existing tests cannot detect.

**Rationale**: The operations layer contains ~1300 lines of business logic (duplicate detection, groomed content merging, pull section merging, status transitions, PR blocking checks). Mocking it entirely means none of this logic is tested through the MCP interface.

### 2. Patch imported names in operations.py, not originals in github.py

`operations.py` does `from .github import create_issue_for_item, ...`, binding names at import time. Patches must target `backlog_core.operations.create_issue_for_item`, not `backlog_core.github.create_issue_for_item`. The feature context documents this requirement and it applies to all 13 github.py functions used by operations.

### 3. Three BACKLOG_DIR patches required

`BACKLOG_DIR` is imported at module level by three modules: `models.py`, `operations.py`, and `parsing.py`. All three must be monkeypatched to `tmp_path` for test isolation. Missing any one causes tests to read/write the real backlog directory.

### 4. Real filesystem I/O via tmp_path

Tests use real file I/O against `tmp_path` rather than mocking Path operations. This validates frontmatter parsing, file creation, content merging, and cleanup deletion -- all operations that constitute the "local cache" half of the system.

### 5. build_backlog_frontmatter for test data

Test items are created via `build_backlog_frontmatter()` from `parsing.py`, not hand-crafted YAML. This ensures test data stays compatible as the frontmatter schema evolves.

### 6. No @pytest.mark.asyncio decorators

The root `pyproject.toml` sets `asyncio_mode = "auto"`. All async test functions are detected automatically. No decorator noise.

### 7. pytest-xdist compatibility

Both suites must work with `-n auto` (parallel execution). Suite 1 uses `tmp_path` per test (inherently isolated). Suite 2 uses UUID-prefixed issue titles for cleanup identification and isolation between workers.

### 8. Skill loading requirement

Test-writing agents implementing this spec MUST load the `/fastmcp-python-tests` skill for FastMCP test design patterns and best practices.

## File Organization

```text
.claude/skills/backlog/tests/
  conftest.py                       # shared fixtures (extended, not replaced)
  test_backlog_core_server.py       # EXISTING: 42 unit tests (mock at operations) — DO NOT MODIFY
  test_scenarios.py                 # NEW: 28 scenario integration tests (mock at github.py)
  test_live_validation.py           # NEW: 11 live e2e tests (real GitHub, @pytest.mark.e2e)
```

No test helpers directory. All shared fixtures live in `conftest.py`. The `_call` helper is duplicated in each test file (same pattern as the existing test file) rather than imported, because it is 4 lines and importing it would require making conftest.py async-aware in a way that complicates the module.

## Suite 1: Scenario Integration Tests

### Fixture Design

Three fixtures added to `conftest.py`:

#### `backlog_dir` fixture

```python
@pytest.fixture()
def backlog_dir(tmp_path, monkeypatch):
    """Redirect BACKLOG_DIR to a temp directory for test isolation."""
    bd = tmp_path / ".claude" / "backlog"
    bd.mkdir(parents=True)
    monkeypatch.setattr("backlog_core.models.BACKLOG_DIR", bd)
    monkeypatch.setattr("backlog_core.operations.BACKLOG_DIR", bd)
    monkeypatch.setattr("backlog_core.parsing.BACKLOG_DIR", bd)
    return bd
```

All three module bindings are patched. The fixture returns the directory path so tests can inspect created files.

#### `mock_github` fixture

```python
@pytest.fixture()
def mock_github(monkeypatch):
    """Patch all github.py functions at the operations.py import boundary.

    Returns a dict of all mock objects keyed by function name for per-test
    configuration (e.g., setting return values for specific scenarios).
    """
    mocks = {}
    functions_and_defaults = {
        "try_get_github": None,
        "get_github": MagicMock(),
        "create_issue_for_item": 42,
        "close_github_issue": None,
        "resolve_github_issue": None,
        "check_open_prs_for_issue": [],
        "batch_fetch_statuses": {},
        "apply_status_in_progress": None,
        "fetch_open_issues_by_title": {},
        "view_enrich_from_github": False,
        "sync_groomed_to_github_issue": True,
        "fetch_github_issue_body": "issue body from github",
        "issue_to_local_fields": IssueLocalFields(
            title="Test", body="body", priority="P1",
            item_type="Feature", status="open",
        ),
    }
    for func_name, default_rv in functions_and_defaults.items():
        mock = MagicMock(return_value=default_rv)
        monkeypatch.setattr(f"backlog_core.operations.{func_name}", mock)
        mocks[func_name] = mock
    return mocks
```

Returns a dict so individual tests can override return values:

```python
async def test_sync_creates_missing_issues(backlog_dir, mock_github):
    mock_github["create_issue_for_item"].return_value = 99
    mock_github["get_github"].return_value = MagicMock()
    mock_github["fetch_open_issues_by_title"].return_value = {}
    # ... test logic
```

#### `write_test_item` fixture

```python
@pytest.fixture()
def write_test_item(backlog_dir):
    """Factory fixture: creates a per-item file in the test backlog directory.

    Returns a callable: write_test_item(title, priority="P1", issue="", description="Test item")
    that returns the Path to the created file.
    """
    def _write(title, priority="P1", issue="", description="Test item"):
        from backlog_core.parsing import title_to_slug, build_backlog_frontmatter
        slug = title_to_slug(title)
        filepath = backlog_dir / f"{priority.lower()}-{slug}.md"
        fm = build_backlog_frontmatter(
            title, description, "test", "2026-01-01", priority,
            "Feature", "open", issue, "", "",
        )
        filepath.write_text(fm, encoding="utf-8")
        return filepath
    return _write
```

Uses `build_backlog_frontmatter` for format correctness. The factory pattern allows creating multiple items per test with different parameters.

### Mocking Strategy

#### github.py functions mocked (13 functions)

These are the functions imported by `operations.py` from `github.py`. All are patched at `backlog_core.operations.<name>`:

| Function | Default Mock Return | Override When |
|----------|-------------------|---------------|
| `try_get_github` | `None` | Testing GitHub-connected scenarios (return `MagicMock()`) |
| `get_github` | `MagicMock()` | Testing sync/pull/close/resolve (needs repository object) |
| `create_issue_for_item` | `42` | Testing issue creation (return specific number) |
| `close_github_issue` | `None` | Verify called with correct args on close |
| `resolve_github_issue` | `None` | Verify called with correct args on resolve |
| `check_open_prs_for_issue` | `[]` | Testing PR blocking (return `[PullRequestRef(...)]`) |
| `batch_fetch_statuses` | `{}` | Testing list with_status (return `{num: IssueStatus(...)}`) |
| `apply_status_in_progress` | `None` | Verify called when status set to in-progress |
| `fetch_open_issues_by_title` | `{}` | Testing sync dedup (return `{title: num}` map) |
| `view_enrich_from_github` | `False` | Testing view enrichment (return `True`, mutate result) |
| `sync_groomed_to_github_issue` | `True` | Testing groom sync (return `True` for updated) |
| `fetch_github_issue_body` | `"issue body from github"` | Testing pull content |
| `issue_to_local_fields` | `IssueLocalFields(...)` | Testing pull_single_issue |

#### Filesystem handling

- `BACKLOG_DIR` redirected to `tmp_path / ".claude" / "backlog"` via monkeypatch
- All file I/O is real -- `Path.read_text()`, `Path.write_text()`, `Path.unlink()`, `Path.glob()` operate on `tmp_path`
- Tests verify file contents by reading from `tmp_path` after MCP tool calls

### Test Organization

Tests are organized by consuming skill/agent workflow, matching the scenario numbering from the [feature context](./feature-context-backlog-mcp-scenarios.md). Each test class groups scenarios for one skill or workflow.

```python
class TestCreateBacklogItem:
    """Scenarios consumed by /create-backlog-item skill."""
    # Scenario 1: Create item with GitHub issue

class TestWorkBacklogItem:
    """Scenarios consumed by /work-backlog-item skill."""
    # Scenarios 2-13: Browse, view, update, close, resolve

class TestGroomBacklogItem:
    """Scenarios consumed by /groom-backlog-item skill."""
    # Scenarios 14-17: Full groom, incremental, local-only, via update

class TestGroupItemsToMilestone:
    """Scenarios consumed by /group-items-to-milestone skill."""
    # Scenario 18: List for milestone selection

class TestBacklogItemGroomer:
    """Scenarios consumed by @backlog-item-groomer agent."""
    # Scenario 19: List then view for groomer discovery

class TestSyncAndPull:
    """Sync and pull workflow scenarios."""
    # Scenarios 20-21: Sync creates + pushes, pull updates local

class TestErrorPaths:
    """Error path scenarios across all tools."""
    # Scenarios 22-25: Close without checklist, view nonexistent, add duplicate, empty list

class TestLifecycles:
    """Full lifecycle scenarios spanning multiple MCP tools."""
    # Scenarios 26-28: Create-groom-update-close, create-resolve-cleanup, stale discovery
```

### Response Shape Contracts

Each test asserts the exact response shape that consuming skills/agents read, as documented in the Response Shape Registry from the feature context. Tests verify:

1. **Presence of expected keys**: Every field listed in the registry for a given tool is asserted to exist in the response.
2. **Type correctness**: String fields are strings, bool fields are bools, list fields are lists.
3. **Output envelope**: Every response includes `messages` (list), `warnings` (list), `errors` (list).
4. **Error responses**: Include `error` (string) key plus the output envelope.

Example assertion pattern:

```python
async def test_create_item_response_shape(backlog_dir, mock_github):
    """Scenario 1: backlog_add returns shape expected by /create-backlog-item."""
    mock_github["try_get_github"].return_value = MagicMock()
    mock_github["create_issue_for_item"].return_value = 42
    result = await _call("backlog_add", {
        "title": "Test Item",
        "priority": "P1",
        "description": "Test description",
        "create_issue": True,
        "force": True,
    })
    # Fields read by /create-backlog-item
    assert isinstance(result["title"], str)
    assert isinstance(result["priority"], str)
    assert isinstance(result["filepath"], str)
    assert isinstance(result["issue_num"], int)
    # Output envelope
    assert isinstance(result["messages"], list)
    assert isinstance(result["warnings"], list)
    assert isinstance(result["errors"], list)
    # File was created
    assert Path(result["filepath"]).exists()
```

### Error Path Coverage

Four error paths tested in `TestErrorPaths`:

| # | Scenario | Tool Call | Assertion |
|---|----------|-----------|-----------|
| 22 | Close without checklist_pass | `backlog_close(selector="...", plan="test", checklist_pass=False)` | Response contains `error` key with `"checklist_pass required"` substring |
| 23 | View nonexistent item | `backlog_view(selector="#99999")` | Response contains `error` key with `"No item found"` substring |
| 24 | Add duplicate (force=False) | `backlog_add(title=<existing>, force=False)` with pre-created item | Response contains `error` key with `"Similar backlog items found"` substring |
| 25 | List on empty backlog | `backlog_list()` with empty `backlog_dir` | Response contains `items: []` and `count: 0` (not an error -- empty is valid) |

Error paths verify that `BacklogError` subclasses (`ValidationError`, `ItemNotFoundError`, `DuplicateItemError`) are caught by the server layer and converted to `{"error": str(e), **out.to_dict()}` responses.

### Lifecycle Test Design

Three lifecycle tests in `TestLifecycles`:

#### Lifecycle 1: Create, groom, update, close (Scenario 26)

```text
1. backlog_add(title="Lifecycle Test 1", priority="P1", create_issue=False, force=True)
   → Assert: filepath exists, title correct
2. backlog_groom(selector="Lifecycle Test 1", groomed_content="## Acceptance Criteria\n- Done")
   → Assert: groomed_updated=True, file contains "## Groomed" section
3. backlog_update(selector="Lifecycle Test 1", plan="plan/test.md")
   → Assert: plan="plan/test.md" in response
4. backlog_close(selector="Lifecycle Test 1", plan="plan/test.md", checklist_pass=True)
   → Assert: closed=True
```

#### Lifecycle 2: Create, resolve with cleanup (Scenario 27)

```text
1. backlog_add(title="Lifecycle Test 2", priority="P2", create_issue=False, force=True)
   → Assert: filepath exists
2. backlog_resolve(selector="Lifecycle Test 2", reason="duplicate", cleanup=True)
   → Assert: resolved=True, original file no longer exists
```

Note: `cleanup=True` requires an issue ref to trigger file removal (see `_close_cleanup` guard: `if cleanup and issue_ref`). The test must pre-create an item with an issue number. Configure `mock_github["try_get_github"]` to return a mock repository and set `create_issue=True` on the add call so the item gets `issue="#42"`.

#### Lifecycle 3: Stale item discovery (Scenario 28)

```text
1. write_test_item("Stale Item", priority="P1", issue="#100")
   → Pre-create item with issue #100
2. Configure mock_github["batch_fetch_statuses"] to return {} (issue #100 not in open issues)
3. backlog_list(with_status=True)
   → Assert: item appears with status="" and milestone="" (not in open issues map)
   → This signals staleness: local item references a closed/missing GitHub issue
```

## Suite 2: Live Validation Tests

### Prerequisites

- `GITHUB_TOKEN` environment variable set with repo access to `Jamie-BitFlight/claude_skills`
- Network access to GitHub API
- Tests skip entirely when `GITHUB_TOKEN` is absent:

```python
pytestmark = [
    pytest.mark.e2e,
    pytest.mark.skipif(
        not os.environ.get("GITHUB_TOKEN"),
        reason="GITHUB_TOKEN not set — skipping live validation tests",
    ),
]
```

### Test Organization

All 11 live tests are in a single class `TestLiveLifecycle` that executes as an ordered sequence. The class uses a shared fixture that creates one test issue and tracks its number for subsequent tests.

```python
class TestLiveLifecycle:
    """Full lifecycle against real GitHub. Tests run in order within this class."""

    # L1: Add item with real GitHub issue
    # L2: List includes created item
    # L3: View by issue number
    # L4: Update: attach plan
    # L5: Update: set status in-progress
    # L6: Groom: write full content
    # L7: Groom: incremental section
    # L8: Sync: push groomed content
    # L9: Pull: refresh from GitHub
    # L10: Close: full lifecycle end
    # L11: Resolve: alternative end (separate item)
```

Tests L1-L10 operate on a single item created in L1. Test L11 creates a second item and resolves it. Both items are cleaned up in teardown.

### Cleanup Strategy

A session-scoped fixture creates items and ensures cleanup even on failure:

```python
@pytest.fixture(scope="class")
async def live_items(tmp_path_factory, monkeypatch_session):
    """Create live test items and clean up on teardown."""
    import uuid
    test_id = uuid.uuid4().hex[:8]
    bd = tmp_path_factory.mktemp("live-backlog")
    # monkeypatch BACKLOG_DIR to temp for file isolation
    # (GitHub issues are real, local files are temp)

    created_issues = []  # track issue numbers for cleanup

    yield {"test_id": test_id, "issues": created_issues, "backlog_dir": bd}

    # Teardown: close all created issues
    from backlog_core.github import get_github
    try:
        repo = get_github()
        for issue_num in created_issues:
            try:
                issue = repo.get_issue(issue_num)
                if issue.state == "open":
                    issue.edit(state="closed")
                    issue.create_comment(f"Closed by MCP live validation test {test_id}")
            except Exception:
                pass  # best-effort cleanup
    except Exception:
        pass  # GitHub unavailable during cleanup
```

Key cleanup properties:

- Uses `yield` in fixture -- cleanup runs even when tests fail or error
- Tracks all created issue numbers in a list
- Closes issues via direct PyGithub API (not MCP tools) for reliability
- Best-effort: swallows exceptions during cleanup to avoid masking test failures
- Issue titles use `[MCP-TEST-{uuid}]` prefix for manual identification if cleanup fails

### BACKLOG_DIR for live tests

Live tests still redirect `BACKLOG_DIR` to a temp directory. The GitHub issues are real, but local per-item files go to `tmp_path` to avoid polluting the actual `.claude/backlog/` directory.

### Marker Configuration

```toml
# Already in pyproject.toml:
markers = [
    "e2e: marks tests as end-to-end tests",
]
```

Run selectively:

```bash
# Run only live tests
uv run pytest .claude/skills/backlog/tests/test_live_validation.py -m e2e

# Exclude live tests (default CI behavior with -m "not e2e")
uv run pytest .claude/skills/backlog/tests/ -m "not e2e"

# Run everything
uv run pytest .claude/skills/backlog/tests/
```

The `-n auto` in `addopts` applies to all tests. Live tests within a single class share state via the class-scoped fixture, so they run sequentially within the class. Different xdist workers get different UUIDs, preventing cross-worker interference.

## Shared Infrastructure

### conftest.py Additions

The existing `conftest.py` only adds `sys.path`. These additions are appended, preserving backward compatibility:

```python
# --- Existing content (preserved) ---
import sys
from pathlib import Path

_BACKLOG_ROOT = Path(__file__).parent.parent
if str(_BACKLOG_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKLOG_ROOT))

# --- New fixtures for scenario integration tests ---

import pytest
from unittest.mock import MagicMock

@pytest.fixture()
def backlog_dir(tmp_path, monkeypatch):
    """Redirect BACKLOG_DIR to temp directory. Patches all three module bindings."""
    bd = tmp_path / ".claude" / "backlog"
    bd.mkdir(parents=True)
    monkeypatch.setattr("backlog_core.models.BACKLOG_DIR", bd)
    monkeypatch.setattr("backlog_core.operations.BACKLOG_DIR", bd)
    monkeypatch.setattr("backlog_core.parsing.BACKLOG_DIR", bd)
    return bd


@pytest.fixture()
def mock_github(monkeypatch):
    """Patch all github.py functions imported by operations.py.

    Returns dict of {function_name: MagicMock} for per-test configuration.
    """
    from backlog_core.models import IssueLocalFields

    mocks = {}
    defaults = {
        "try_get_github": None,
        "get_github": MagicMock(),
        "create_issue_for_item": 42,
        "close_github_issue": None,
        "resolve_github_issue": None,
        "check_open_prs_for_issue": [],
        "batch_fetch_statuses": {},
        "apply_status_in_progress": None,
        "fetch_open_issues_by_title": {},
        "view_enrich_from_github": False,
        "sync_groomed_to_github_issue": True,
        "fetch_github_issue_body": "issue body from github",
        "issue_to_local_fields": IssueLocalFields(
            title="Test", body="body", priority="P1",
            item_type="Feature", status="open",
        ),
    }
    for name, default in defaults.items():
        mock = MagicMock(return_value=default)
        monkeypatch.setattr(f"backlog_core.operations.{name}", mock)
        mocks[name] = mock
    return mocks


@pytest.fixture()
def write_test_item(backlog_dir):
    """Factory: create per-item file with valid frontmatter in test backlog_dir.

    Usage: filepath = write_test_item("My Title", priority="P0", issue="#42")
    """
    def _write(title, priority="P1", issue="", description="Test item"):
        from backlog_core.parsing import title_to_slug, build_backlog_frontmatter
        slug = title_to_slug(title)
        filepath = backlog_dir / f"{priority.lower()}-{slug}.md"
        fm = build_backlog_frontmatter(
            title, description, "test", "2026-01-01", priority,
            "Feature", "open", issue, "", "",
        )
        filepath.write_text(fm, encoding="utf-8")
        return filepath
    return _write
```

### Helper Utilities

No separate helper module. The `_call` async helper is defined in each test file (4 lines, same as existing pattern):

```python
async def _call(tool_name: str, params: dict | None = None) -> dict:
    """Call MCP tool via in-memory transport and parse JSON response."""
    async with Client(mcp) as client:
        result = await client.call_tool(tool_name, params or {})
    return json.loads(result.content[0].text)
```

This matches the existing `test_backlog_core_server.py` pattern. Extracting it to conftest would require async fixture support machinery that adds complexity without benefit for a 4-line function.

## Constraints

### Backward Compatibility

- `test_backlog_core_server.py` is NOT modified -- its 42 tests continue testing the server-to-operations boundary with operations-level mocks
- New fixtures in `conftest.py` use unique names that do not conflict with any existing test infrastructure
- `asyncio_mode = "auto"` applies globally -- no new configuration needed

### Existing Test Preservation

- New test files are additive: `test_scenarios.py` and `test_live_validation.py`
- No changes to `pyproject.toml` -- `e2e` marker already declared, `asyncio_mode` already set
- Coverage configuration (`--cov=scripts`) does not cover test files -- no impact

### Test Isolation

- Suite 1: Each test gets its own `tmp_path` and fresh mocks via fixtures. No shared mutable state between tests. Safe for `-n auto`.
- Suite 2: UUID-prefixed issue titles prevent cross-worker conflicts. Class-scoped fixture ensures sequential execution within the lifecycle. Cleanup fixture runs on both success and failure.

### Import Requirements

Both new test files import:

```python
from __future__ import annotations

import json
from unittest.mock import MagicMock

from backlog_core.server import mcp
from fastmcp.client import Client
```

Suite 2 additionally imports:

```python
import os
import uuid
```

## Acceptance Criteria

### Suite 1 (test_scenarios.py)

- [ ] 21 scenario tests covering all 10 MCP tools organized by consuming skill/agent
- [ ] 4 error path tests verifying BacklogError conversion to error response
- [ ] 3 lifecycle tests spanning multiple MCP tool calls in sequence
- [ ] Total: 28 tests minimum
- [ ] All tests use `backlog_dir` and `mock_github` fixtures (operations layer NOT mocked)
- [ ] No `@pytest.mark.asyncio` decorators
- [ ] Response shape assertions match the Response Shape Registry from [feature context](./feature-context-backlog-mcp-scenarios.md)
- [ ] All tests pass with `uv run pytest .claude/skills/backlog/tests/test_scenarios.py -x`
- [ ] All tests pass with `-n auto` (parallel execution)
- [ ] Existing `test_backlog_core_server.py` tests still pass unchanged

### Suite 2 (test_live_validation.py)

- [ ] 11 live tests marked with `@pytest.mark.e2e`
- [ ] Tests skip when `GITHUB_TOKEN` is not set
- [ ] Real GitHub issues created with `[MCP-TEST-{uuid}]` prefix
- [ ] Cleanup fixture closes all created issues even on test failure
- [ ] Full lifecycle exercised: add, list, view, update, groom, sync, pull, close, resolve
- [ ] All tests pass with `uv run pytest .claude/skills/backlog/tests/test_live_validation.py -m e2e`
- [ ] `BACKLOG_DIR` redirected to temp -- no pollution of real backlog directory

### Shared Infrastructure

- [ ] `conftest.py` additions do not break existing 42 tests
- [ ] `backlog_dir` fixture patches all three module bindings (models, operations, parsing)
- [ ] `mock_github` fixture returns configurable mock dict
- [ ] `write_test_item` factory produces files parseable by `parse_backlog()`

### Agent Requirements

- [ ] Test-writing agents load the `/fastmcp-python-tests` skill before writing tests
- [ ] Suite 2 implementation validated by `@backlog-mcp-validator` agent
