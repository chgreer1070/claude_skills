# Feature Context: Backlog MCP Scenario Testing

## Problem Statement

The backlog FastMCP server (`backlog_core/server.py`) exposes 10 MCP tools that are consumed by 4 skills (`/create-backlog-item`, `/work-backlog-item`, `/groom-backlog-item`, `/group-items-to-milestone`) and 1 agent (`@backlog-item-groomer`). The existing test suite (`test_backlog_core_server.py`) validates parameter forwarding and error handling at the server-to-operations boundary by mocking `operations.*` functions. This leaves two gaps:

1. **No scenario integration tests** that traverse the full operations layer with realistic data, mocking only at the github.py and filesystem boundaries. The current tests never exercise `operations.add_item`, `operations.view_item`, `operations.close_item`, etc. with real logic -- they mock the entire function. Regressions in operations code are invisible.

2. **No live validation tests** that exercise the MCP tools against real GitHub infrastructure. The `@backlog-mcp-validator` agent can run live validation manually, but there are no repeatable pytest-based end-to-end tests that create temp issues, exercise the full lifecycle, and clean up.

## Existing State

### Current Test File

- **Path**: `.claude/skills/backlog/tests/test_backlog_core_server.py`
- **Test count**: 42 tests (manually counted from source)
- **Pattern**: All tests mock at `backlog_core.operations.<function>` -- the operations layer is never exercised
- **Transport**: In-memory FastMCP `Client(mcp)` -- no STDIO transport tested
- **Async**: `asyncio_mode = "auto"` in root `pyproject.toml` -- no `@pytest.mark.asyncio` decorators needed
- **Helper**: `_call(tool_name, params)` parses `json.loads(result.content[0].text)` from `Client(mcp)`

### Test Infrastructure (conftest.py)

- **Path**: `.claude/skills/backlog/tests/conftest.py`
- **Content**: Adds `.claude/skills/backlog/` to `sys.path` so `from backlog_core.*` resolves
- **Fixtures**: None defined -- no shared fixtures for `tmp_path`, mock repos, or test items
- **No pytest markers** for e2e or live tests

### Pytest Configuration

From root `pyproject.toml`:

```text
asyncio_mode = "auto"
markers = ["demos", "e2e"]
addopts = ["--cov=scripts", "--strict-config", "-n", "auto"]
```

Dependencies: `pytest>=8.4.1`, `pytest-asyncio>=1.1.0`, `pytest-cov>=6.2.1`, `pytest-mock>=3.12`, `pytest-xdist>=3.5.0`

## Feature Scope

### Suite 1: Scenario Integration Tests (mocked boundaries)

Tests call MCP tools through `Client(mcp)` but let operations.py run real logic. Mocking occurs at:

- `backlog_core.github.*` functions (GitHub API boundary)
- `backlog_core.models.BACKLOG_DIR` (redirected to `tmp_path`)
- Filesystem reads/writes go to `tmp_path` (real I/O, temporary directory)

#### Scenarios by Skill Workflow

##### /create-backlog-item (1 scenario)

| # | Scenario | MCP Tools | What to Assert |
|---|----------|-----------|----------------|
| 1 | Create item with GitHub issue | `backlog_add` | Returns `filepath`, `title`, `priority`, `issue_num`; per-item file written to `tmp_path`; `create_issue_for_item` called once |

##### /work-backlog-item (12 scenarios)

| # | Scenario | MCP Tools | What to Assert |
|---|----------|-----------|----------------|
| 2 | Browse backlog (list with status) | `backlog_list(with_status=True)` | Returns `items` list with `section`, `title`, `issue`, `plan`, `status`, `milestone`, `file_path`, `groomed` fields |
| 3 | Browse backlog (list from GitHub refresh) | `backlog_list(from_github=True)` | Calls `refresh_local_cache_from_github`; items updated from GitHub |
| 4 | Browse backlog (list with label filter) | `backlog_list(label="priority:p0")` | Only items matching label returned |
| 5 | View item by issue number | `backlog_view(selector="#42")` | Returns `title`, `priority`, `issue`, `body`, `groomed`, `status`, `labels`, `milestone` |
| 6 | View item by title substring | `backlog_view(selector="Error Recovery")` | Returns matching item with `file_path` |
| 7 | View item with pagination | `backlog_view(selector="#42", offset=5, limit=10)` | Returns truncated `body`, `body_truncated`, `body_remaining_lines`, `body_total_lines` |
| 8 | Update item with plan | `backlog_update(selector="...", plan="plan/tasks.md")` | Returns `title`, `plan`; per-item file metadata updated |
| 9 | Update item status to in-progress | `backlog_update(selector="...", status="in-progress")` | Returns `title`, `status`; `apply_status_in_progress` called |
| 10 | Update item: create GitHub issue | `backlog_update(selector="...", create_issue=True)` | Returns `title`, `issue_num` for P0/P1 items |
| 11 | Close item with checklist pass | `backlog_close(selector="...", plan="...", checklist_pass=True)` | Returns `title`, `closed: True`; GitHub issue closed |
| 12 | Resolve item with reason | `backlog_resolve(selector="...", reason="duplicate")` | Returns `title`, `resolved: True`; GitHub issue closed with resolve comment |
| 13 | Resolve with cleanup | `backlog_resolve(selector="...", reason="...", cleanup=True)` | Local file removed; issue closed |

##### /groom-backlog-item (4 scenarios)

| # | Scenario | MCP Tools | What to Assert |
|---|----------|-----------|----------------|
| 14 | Groom with full content replacement | `backlog_groom(selector="...", groomed_content="...")` | Returns `title`, `groomed_updated: True`; per-item file has `## Groomed` section; GitHub issue body updated |
| 15 | Groom with incremental section update | `backlog_groom(selector="...", section="Acceptance Criteria", content="...")` | Returns `title`, `groomed_updated: True`; section appended/replaced in per-item file |
| 16 | Groom item without GitHub issue (local only) | `backlog_groom(selector="...", groomed_content="...")` | Returns `title`, `groomed_updated: True`; no GitHub sync attempted |
| 17 | Groom via backlog_update (groomed_content param) | `backlog_update(selector="...", groomed_content="...")` | Same as #14 but through update tool path |

##### /group-items-to-milestone (1 scenario)

| # | Scenario | MCP Tools | What to Assert |
|---|----------|-----------|----------------|
| 18 | List items for milestone selection | `backlog_list(with_status=True)` | Each item has `section`, `title`, `issue`, `status`, `milestone` fields for milestone assignment UI |

##### @backlog-item-groomer agent (1 scenario)

| # | Scenario | MCP Tools | What to Assert |
|---|----------|-----------|----------------|
| 19 | Groomer reads list then views item | `backlog_list()` then `backlog_view(selector="...")` | List returns items; view returns full item with `body`, `description`, `groomed` for groomer discovery |

##### Sync and Pull (2 scenarios)

| # | Scenario | MCP Tools | What to Assert |
|---|----------|-----------|----------------|
| 20 | Sync creates missing issues and pushes groomed | `backlog_sync()` | Returns `created` count > 0, `pushed` count >= 0; `create_issue_for_item` called for items without issues |
| 21 | Pull updates local from GitHub | `backlog_pull()` | Returns `pulled` count > 0; local files updated with GitHub issue body content |

#### Error Path Scenarios (4)

| # | Scenario | MCP Tools | What to Assert |
|---|----------|-----------|----------------|
| 22 | Close without checklist_pass | `backlog_close(checklist_pass=False)` | Returns `error` key with `"checklist_pass required"` |
| 23 | View nonexistent item | `backlog_view(selector="#99999")` | Returns `error` key with `"No item found"` |
| 24 | Add duplicate item (force=False) | `backlog_add(force=False)` with existing title | Returns `error` key with `"Similar backlog items found"` |
| 25 | List on empty backlog directory | `backlog_list()` | Returns `items: []`, `count: 0` |

#### Full Lifecycle Scenarios (3)

| # | Scenario | MCP Tools | What to Assert |
|---|----------|-----------|----------------|
| 26 | Create, groom, update, close lifecycle | `backlog_add` -> `backlog_groom` -> `backlog_update` -> `backlog_close` | Item progresses through states; final close returns `closed: True` |
| 27 | Create, resolve with cleanup lifecycle | `backlog_add` -> `backlog_resolve(cleanup=True)` | Item file created then removed; `resolved: True` |
| 28 | Stale item discovery (list with status shows closed GitHub issue) | `backlog_list(with_status=True)` | Item with closed GitHub issue visible with empty status (not in open issues map); grooming can detect staleness |

### Suite 2: Live Validation Tests (no mocks, real temp issues)

Delegated to `@backlog-mcp-validator` agent pattern but implemented as pytest tests marked `@pytest.mark.e2e`. These tests:

- Create real temporary GitHub issues via `backlog_add(create_issue=True)`
- Use a naming convention: `[MCP-TEST-{uuid}]` prefix for cleanup identification
- Clean up all created issues in teardown (even on failure)
- Require `GITHUB_TOKEN` environment variable (skip if absent)

#### Live Test Scenarios

| # | Scenario | MCP Tools Exercised | What to Assert |
|---|----------|---------------------|----------------|
| L1 | Add item with real GitHub issue | `backlog_add(create_issue=True)` | Returns `issue_num` > 0; GitHub issue exists |
| L2 | List includes created item | `backlog_list()` | Item appears in `items` with correct `title`, `priority`, `issue` |
| L3 | View created item by issue number | `backlog_view(selector="#N")` | Returns full item with `state: open`, `labels` containing priority |
| L4 | Update: attach plan | `backlog_update(plan="test-plan.md")` | Returns `plan: "test-plan.md"` |
| L5 | Update: set status in-progress | `backlog_update(status="in-progress")` | Returns `status: "in-progress"`; GitHub label updated |
| L6 | Groom: write content | `backlog_groom(groomed_content="...")` | Returns `groomed_updated: True`; GitHub issue body contains groomed section |
| L7 | Groom: incremental section | `backlog_groom(section="...", content="...")` | Section appears in GitHub issue body |
| L8 | Sync: push groomed content | `backlog_sync()` | Returns `pushed` >= 0 (may be 0 if already synced) |
| L9 | Pull: refresh from GitHub | `backlog_pull()` | Returns `pulled` >= 0; local file matches GitHub |
| L10 | Close: full lifecycle end | `backlog_close(checklist_pass=True)` | Returns `closed: True`; GitHub issue state = closed |
| L11 | Resolve: alternative end | `backlog_resolve(reason="test cleanup")` | Returns `resolved: True`; GitHub issue closed |

## Response Shape Registry

Fields that each skill/agent reads from MCP tool responses, verified from source SKILL.md files:

| MCP Tool | Return Fields | Consuming Skill/Agent | Fields Read |
|----------|---------------|----------------------|-------------|
| `backlog_add` | `filepath`, `filename`, `title`, `priority`, `issue_num?`, `messages[]`, `warnings[]`, `errors[]` | `/create-backlog-item` | `title`, `priority`, `filepath` (for confirmation); `issue_num` (for next-steps display) |
| `backlog_list` | `items[{section, title, issue, plan, file_path?, groomed?, status?, milestone?}]`, `count`, `messages[]`, `warnings[]`, `errors[]` | `/work-backlog-item` (Step 0, Step 1) | `items[].title`, `items[].issue`, `items[].plan`, `items[].section`, `items[].status`, `items[].milestone`, `items[].file_path`, `items[].groomed` |
| `backlog_list` | (same) | `/groom-backlog-item` (Step 1) | `items[].title`, `items[].section`, `items[].file_path`, `items[].groomed` |
| `backlog_list` | (same) | `/group-items-to-milestone` (Step 2) | `items[].title`, `items[].issue`, `items[].section`, `items[].status`, `items[].milestone` |
| `backlog_list` | (same) | `@backlog-item-groomer` (Step 4) | `items[].title`, `items[].issue` (for dependency identification) |
| `backlog_view` | `title`, `priority`, `description`, `source`, `added`, `plan`, `issue`, `file_path`, `groomed` (bool), `status`, `number?`, `state`, `body`, `labels[]`, `milestone`, `body_truncated?`, `body_remaining_lines?`, `body_total_lines?`, `messages[]`, `warnings[]`, `errors[]` | `/work-backlog-item` (Step 1b, Step 2, Step 9a) | `title`, `body`, `priority`, `status`, `milestone`, `plan`, `file_path`, `state`, `labels` |
| `backlog_view` | (same) | `@backlog-item-groomer` (Step 1-3) | `title`, `body`, `priority`, `description` |
| `backlog_sync` | `created`, `pushed`, `dry_run`, `messages[]`, `warnings[]`, `errors[]` | `/work-backlog-item` (implicit via CLI) | `created`, `pushed` (counts for reporting) |
| `backlog_close` | `title`, `closed` (bool) or `already_closed` (bool), `messages[]`, `warnings[]`, `errors[]` | `/work-backlog-item` (Step 9f) | `title`, `closed` (confirmation) |
| `backlog_resolve` | `title`, `resolved` (bool) or `already_resolved` (bool), `messages[]`, `warnings[]`, `errors[]` | `/work-backlog-item` (Step 9b) | `title`, `resolved` (confirmation) |
| `backlog_update` | `title`, `plan?`, `issue_num?`, `status?`, `groomed_updated?` (bool), `messages[]`, `warnings[]`, `errors[]` | `/work-backlog-item` (Step 2.5a, Step 2.7, Step 7) | `title`, `plan`, `issue_num`, `status` |
| `backlog_update` | (same) | `@backlog-item-groomer` (output step) | `title`, `groomed_updated` |
| `backlog_groom` | `title`, `groomed_updated` (bool), `messages[]`, `warnings[]`, `errors[]` | `/groom-backlog-item` (Step 7) | `title`, `groomed_updated` |
| `backlog_groom` | (same) | `@backlog-item-groomer` (output step) | `title`, `groomed_updated` |
| `backlog_normalize` | `updated`, `dry_run?`, `messages[]`, `warnings[]`, `errors[]` | (maintenance only, no skill consumer) | `updated` |
| `backlog_pull` | `pulled`, `dry_run?`, `messages[]`, `warnings[]`, `errors[]` | (used via CLI in sync workflows) | `pulled` |

### Key Observation

Every tool response MUST include `messages[]`, `warnings[]`, `errors[]` from `Output.to_dict()`. On error, every response MUST include `error` (string). These are contract requirements already tested in the existing suite's parametrized tests.

## Mocking Boundary Analysis

### github.py Functions That Need Mocks (18 functions)

| Function | Used By Operations | Mock Strategy |
|----------|-------------------|---------------|
| `get_github(repo)` | `close_item`, `resolve_item`, `sync_items`, `pull_items` | Return mock `Repository` object |
| `try_get_github(repo)` | `list_items`, `_ensure_github_issue`, `_write_groomed_to_github`, `_apply_plan_to_item` | Return mock `Repository` or `None` |
| `create_issue_for_item(repo, item, dry_run, output)` | `add_item`, `sync_items`, `_ensure_github_issue` | Return mock issue number (int) |
| `close_github_issue(issue_ref, plan, repo, output)` | `close_item` | Verify called with correct args |
| `resolve_github_issue(issue_ref, reason, repo, output)` | `resolve_item` | Verify called with correct args |
| `check_open_prs_for_issue(issue_num, repo)` | `close_item`, `resolve_item` | Return empty list (no blocking PRs) |
| `batch_fetch_statuses(items, repo)` | `list_items` | Return dict mapping issue numbers to `IssueStatus` |
| `apply_status_in_progress(item, repo, output)` | `update_item` | Verify called |
| `fetch_open_issues_by_title(repo)` | `sync_create_missing_issues` | Return empty dict or title->number map |
| `view_enrich_from_github(result, issue_num, repo)` | `view_item` | Modify `ViewItemResult` in place, return `True` |
| `sync_groomed_to_github_issue(repo, num, content, section, output)` | `_write_groomed_to_github` | Return `True` (updated) |
| `fetch_github_issue_body(repo, num, output)` | `_pull_item` | Return body string |
| `issue_to_local_fields(issue)` | `pull_single_issue` | Return `IssueLocalFields` |
| `fetch_item_status(item, repo, output)` | (single-item fallback, not in main paths) | Return status string |

### Filesystem Operations That Need tmp_path

| Operation | Location | Mock Strategy |
|-----------|----------|---------------|
| `BACKLOG_DIR` constant | `backlog_core.models` | Monkeypatch to `tmp_path / ".claude" / "backlog"` |
| `Path(filepath).read_text()` | `operations.py` (multiple) | Real I/O to `tmp_path` |
| `Path(filepath).write_text()` | `operations.py` (multiple) | Real I/O to `tmp_path` |
| `Path(filepath).unlink()` | `_close_cleanup` | Real I/O to `tmp_path` |
| `BACKLOG_DIR.mkdir()` | `_resolve_filepath`, `_pull_item_create_new` | Real I/O to `tmp_path` |
| `BACKLOG_DIR.glob("*.md")` | `normalize_items` | Real I/O to `tmp_path` |

### Recommended Fixture Design

```python
@pytest.fixture()
def backlog_dir(tmp_path, monkeypatch):
    """Redirect BACKLOG_DIR to a temp directory for test isolation."""
    bd = tmp_path / ".claude" / "backlog"
    bd.mkdir(parents=True)
    monkeypatch.setattr("backlog_core.models.BACKLOG_DIR", bd)
    monkeypatch.setattr("backlog_core.operations.BACKLOG_DIR", bd)
    return bd


@pytest.fixture()
def mock_github():
    """Patch all github.py functions used by operations.py."""
    with (
        patch("backlog_core.operations.try_get_github", return_value=None),
        patch("backlog_core.operations.get_github") as mock_get,
        patch("backlog_core.operations.create_issue_for_item", return_value=42),
        patch("backlog_core.operations.close_github_issue"),
        patch("backlog_core.operations.resolve_github_issue"),
        patch("backlog_core.operations.check_open_prs_for_issue", return_value=[]),
        patch("backlog_core.operations.batch_fetch_statuses", return_value={}),
        patch("backlog_core.operations.apply_status_in_progress"),
        patch("backlog_core.operations.fetch_open_issues_by_title", return_value={}),
        patch("backlog_core.operations.view_enrich_from_github", return_value=False),
        patch("backlog_core.operations.sync_groomed_to_github_issue", return_value=True),
        patch("backlog_core.operations.fetch_github_issue_body", return_value="issue body"),
    ):
        yield mock_get


def _write_test_item(backlog_dir, title, priority="P1", issue="", description="Test item"):
    """Helper to create a per-item file in the test backlog directory."""
    from backlog_core.parsing import title_to_slug, build_backlog_frontmatter
    slug = title_to_slug(title)
    filepath = backlog_dir / f"{priority.lower()}-{slug}.md"
    fm = build_backlog_frontmatter(
        title, description, "test", "2026-01-01", priority,
        "Feature", "open", issue, "", "",
    )
    filepath.write_text(fm, encoding="utf-8")
    return filepath
```

## Test Infrastructure

### Existing Capabilities

- **conftest.py**: Only adds `sys.path` for `backlog_core` imports. No fixtures.
- **Client pattern**: `async with Client(mcp) as client: result = await client.call_tool(...)` with `json.loads(result.content[0].text)` parsing.
- **No `@pytest.mark.asyncio`**: Global `asyncio_mode = "auto"` handles this.
- **pytest-xdist**: `-n auto` in `addopts` -- tests run in parallel by default. Fixtures must be thread-safe (use `tmp_path` not shared state).

### Needed Additions to conftest.py

1. `backlog_dir` fixture (redirects `BACKLOG_DIR` to `tmp_path`)
2. `mock_github` fixture (patches all `github.py` functions at the operations boundary)
3. `_write_test_item` helper (creates per-item files with valid frontmatter)
4. `_call` async helper (same as existing test file but importable)
5. `@pytest.mark.e2e` marker for live tests (already declared in `pyproject.toml`)

### File Organization

```text
.claude/skills/backlog/tests/
  conftest.py                       # shared fixtures
  test_backlog_core_server.py       # existing: 42 unit tests (mock at operations)
  test_scenarios.py                 # NEW: 28 scenario integration tests (mock at github.py)
  test_live_validation.py           # NEW: 11 live e2e tests (real GitHub, @pytest.mark.e2e)
```

## Constraints

### Backward Compatibility

- Existing `test_backlog_core_server.py` must not be modified (it tests a different boundary)
- `conftest.py` additions must not break existing tests
- `asyncio_mode = "auto"` applies globally -- new test files follow the same pattern

### Async Requirements

- All MCP tool calls through `Client(mcp)` are async
- Test functions that call `_call()` must be `async def`
- No `@pytest.mark.asyncio` decorators needed (global auto mode)

### Test Isolation

- Suite 1 tests must be fully isolated via `tmp_path` and mocks -- no shared filesystem state
- Suite 2 tests must create unique-titled GitHub issues and clean up in teardown
- Both suites must work with `pytest-xdist` parallel execution (`-n auto`)

### Marker Requirements

- Suite 1: No special markers needed (runs with default `pytest`)
- Suite 2: `@pytest.mark.e2e` marker; skipped when `GITHUB_TOKEN` not set
- `pyproject.toml` already declares the `e2e` marker

### BACKLOG_DIR Patching

`BACKLOG_DIR` is imported by both `models.py` and `operations.py`. The monkeypatch must target both:

```python
monkeypatch.setattr("backlog_core.models.BACKLOG_DIR", bd)
monkeypatch.setattr("backlog_core.operations.BACKLOG_DIR", bd)
```

Additionally, `parsing.py` imports `BACKLOG_DIR` from `models.py` -- verify whether it uses the module-level binding or re-imports at call time. If it binds at import time, it also needs patching:

```python
monkeypatch.setattr("backlog_core.parsing.BACKLOG_DIR", bd)
```

### GitHub.py Mock Depth

Mocks target the re-exported names in `operations.py`, not the original definitions in `github.py`. This is because `operations.py` does `from .github import create_issue_for_item, ...` which binds the names locally. Patching `backlog_core.operations.create_issue_for_item` is correct; patching `backlog_core.github.create_issue_for_item` would NOT affect operations code.

### Per-Item File Format

Test items must use valid frontmatter format. The `build_backlog_frontmatter()` function from `parsing.py` produces the canonical format. Tests must use this function (not hand-crafted YAML) to ensure format compatibility as the schema evolves.

## Open Questions

1. **parsing.py BACKLOG_DIR binding**: Does `parse_backlog()` use `models.BACKLOG_DIR` at call time or bind it at import time? This determines whether `parsing.py` needs separate monkeypatching. Verified from source: `parse_backlog_from_directory()` calls `BACKLOG_DIR.glob()` -- it imports `BACKLOG_DIR` at module level from `models.py`, so it binds at import time and needs separate patching.

2. **Live test cleanup strategy**: If a live test fails mid-lifecycle (e.g., after creating an issue but before closing it), the cleanup fixture must still close/delete the GitHub issue. A `pytest.fixture(autouse=True)` with `yield` and post-yield cleanup using `try_get_github()` is the safest pattern.

3. **Suite 2 agent delegation**: The feature request mentions Suite 2 is "delegated to the backlog-mcp-validator agent." Should live tests be implemented as pytest tests (repeatable, CI-runnable) or as agent-invocation scripts? Decision: implement as pytest tests with `@pytest.mark.e2e` that can also be validated by the agent. The agent validates the same contracts but via manual MCP tool calls; the pytest tests encode those same contracts in repeatable assertions.

4. **normalize and pull test items**: `normalize_items` and `pull_items` require specific file format states (pre-normalization format, divergent local/GitHub content). Test helpers must create items in those specific states. The `build_backlog_frontmatter()` function's output is already the normalized format, so pre-normalization files may need hand-crafted frontmatter to test the transformation path.
