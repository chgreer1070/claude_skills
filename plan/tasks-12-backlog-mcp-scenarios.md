# Task Plan: Backlog MCP Scenario Testing

Fixes #328

**Feature**: Backlog MCP Scenario Testing
**Architecture Spec**: [architect-backlog-mcp-scenarios.md](./architect-backlog-mcp-scenarios.md)
**Feature Context**: [feature-context-backlog-mcp-scenarios.md](./feature-context-backlog-mcp-scenarios.md)
**Test Directory**: `.claude/skills/backlog/tests/`

## Context Manifest

| Path | Purpose |
|------|---------|
| `.claude/skills/backlog/tests/conftest.py` | Shared test fixtures (to be extended) |
| `.claude/skills/backlog/tests/test_backlog_core_server.py` | Existing 42 unit tests (DO NOT MODIFY) |
| `.claude/skills/backlog/backlog_core/server.py` | FastMCP server exposing 10 MCP tools |
| `.claude/skills/backlog/backlog_core/operations.py` | Business logic layer (~1300 lines) |
| `.claude/skills/backlog/backlog_core/github.py` | GitHub API boundary (18 functions) |
| `.claude/skills/backlog/backlog_core/models.py` | Data models, BACKLOG_DIR constant |
| `.claude/skills/backlog/backlog_core/parsing.py` | Frontmatter parsing, build_backlog_frontmatter |
| `plan/architect-backlog-mcp-scenarios.md` | Architecture spec with fixture design and mocking strategy |
| `plan/feature-context-backlog-mcp-scenarios.md` | Feature context with scenario tables and Response Shape Registry |

---

## Group 1: Test Infrastructure

## Task 1.1: Create Shared Fixtures in conftest.py

**Status**: ✅ COMPLETE
**Dependencies**: None
**Priority**: 1
**Complexity**: Medium
**Agent**: fastmcp-python-tests
**Started**: 2026-03-01T08:50:00Z
**Completed**: 2026-03-01T09:00:00Z

### Description

Extend the existing `.claude/skills/backlog/tests/conftest.py` with three shared fixtures required by all scenario integration tests. The existing content (sys.path manipulation) must be preserved. Add `backlog_dir`, `mock_github`, and `write_test_item` fixtures as specified in the architecture spec. The `backlog_dir` fixture must patch `BACKLOG_DIR` in all three modules (`models`, `operations`, `parsing`). The `mock_github` fixture must patch all 13 github.py functions at the `backlog_core.operations.*` boundary and return a configurable dict of mocks. The `write_test_item` fixture must be a factory using `build_backlog_frontmatter()` for format correctness.

### Acceptance Criteria

- [ ] `backlog_dir` fixture patches `backlog_core.models.BACKLOG_DIR`, `backlog_core.operations.BACKLOG_DIR`, and `backlog_core.parsing.BACKLOG_DIR` to `tmp_path / ".claude" / "backlog"`
- [ ] `mock_github` fixture patches all 13 github.py functions listed in the architecture spec at the `backlog_core.operations.*` namespace, returns `dict[str, MagicMock]` for per-test override
- [ ] `write_test_item` fixture is a factory callable that uses `build_backlog_frontmatter()` to create per-item files with valid frontmatter
- [ ] Existing 42 tests in `test_backlog_core_server.py` still pass with `uv run pytest .claude/skills/backlog/tests/test_backlog_core_server.py -x`
- [ ] No `@pytest.mark.asyncio` decorators added (global `asyncio_mode = "auto"`)
- [ ] Fixtures work with `pytest-xdist` (`-n auto`) -- no shared mutable state

### Verification Steps

1. Run `uv run pytest .claude/skills/backlog/tests/test_backlog_core_server.py -x` and confirm all 42 existing tests pass
2. Run `uv run pytest .claude/skills/backlog/tests/conftest.py --collect-only` and confirm no collection errors
3. Verify `backlog_dir` fixture creates the temp directory and patches all three module bindings by reading the fixture code

---

## Task 1.2: Create test_scenarios.py Boilerplate

**Status**: ✅ COMPLETE
**Dependencies**: Task 1.1
**Priority**: 1
**Complexity**: Low
**Agent**: fastmcp-python-tests
**Started**: 2026-03-01T09:01:00Z
**Completed**: 2026-03-01T09:05:00Z

### Description

Create `.claude/skills/backlog/tests/test_scenarios.py` with the file structure, imports, `_call` helper, and empty test class stubs as specified in the architecture spec. The file must import `Client` from `fastmcp.client`, `mcp` from `backlog_core.server`, and define the async `_call(tool_name, params)` helper matching the existing test file pattern. Create empty test classes: `TestCreateBacklogItem`, `TestWorkBacklogItem`, `TestGroomBacklogItem`, `TestGroupItemsToMilestone`, `TestBacklogItemGroomer`, `TestSyncAndPull`, `TestNormalize`, `TestErrorPaths`, `TestLifecycles`.

### Acceptance Criteria

- [ ] File exists at `.claude/skills/backlog/tests/test_scenarios.py`
- [ ] Imports include `json`, `MagicMock`, `Client`, `mcp`, `Path`
- [ ] `_call` async helper matches the pattern: `async with Client(mcp) as client: result = await client.call_tool(...)` with `json.loads(result.content[0].text)` return
- [ ] Nine empty test classes present matching the architecture spec organization
- [ ] File collects without errors: `uv run pytest .claude/skills/backlog/tests/test_scenarios.py --collect-only`

### Verification Steps

1. Run `uv run pytest .claude/skills/backlog/tests/test_scenarios.py --collect-only` and confirm no collection errors
2. Confirm `_call` helper signature matches `async def _call(tool_name: str, params: dict | None = None) -> dict`
3. Verify no `@pytest.mark.asyncio` decorators present

---

## Group 2: Suite 1 -- Scenario Integration Tests (mocked boundaries)

## Task 2.1: Create-Backlog-Item Workflow Scenarios (backlog_add)

**Status**: ✅ COMPLETE
**Dependencies**: Task 1.1, Task 1.2
**Priority**: 2
**Complexity**: Medium
**Agent**: fastmcp-python-tests
**Started**: 2026-03-01T09:10:00Z
**Completed**: 2026-03-01T10:30:00Z

### Description

Implement Scenario 1 from the feature context: "Create item with GitHub issue" using `backlog_add`. The test must exercise the full operations layer (NOT mock operations functions) and instead mock only at the github.py boundary via the `mock_github` fixture. Assert the response shape matches the Response Shape Registry: `filepath`, `title`, `priority`, `issue_num` fields present with correct types. Verify the per-item file was written to `backlog_dir`. Verify `create_issue_for_item` was called once. Configure `mock_github["try_get_github"]` to return a `MagicMock()` and `mock_github["create_issue_for_item"]` to return 42 for issue creation. Reference architecture spec Section "Response Shape Contracts" for assertion patterns.

### Acceptance Criteria

- [ ] Test `test_create_item_with_github_issue` in `TestCreateBacklogItem` class
- [ ] Uses `backlog_dir` and `mock_github` fixtures (operations layer NOT mocked)
- [ ] Asserts `result["filepath"]` is a string pointing to an existing file
- [ ] Asserts `result["title"]` is a string, `result["priority"]` is a string, `result["issue_num"]` is an int
- [ ] Asserts output envelope: `result["messages"]` is list, `result["warnings"]` is list, `result["errors"]` is list
- [ ] Verifies `mock_github["create_issue_for_item"]` was called once
- [ ] Test passes with `uv run pytest .claude/skills/backlog/tests/test_scenarios.py::TestCreateBacklogItem -x`

### Verification Steps

1. Run `uv run pytest .claude/skills/backlog/tests/test_scenarios.py::TestCreateBacklogItem -x -v` and confirm test passes
2. Verify test uses `force=True` to avoid duplicate detection issues
3. Confirm no operations-level mocks are used (only `mock_github` fixture)

---

## Task 2.2: Work-Backlog-Item Browse/List Scenarios (backlog_list, backlog_view)

**Status**: ✅ COMPLETE
**Dependencies**: Task 1.1, Task 1.2
**Priority**: 2
**Complexity**: High
**Agent**: fastmcp-python-tests
**Started**: 2026-03-01T09:10:00Z
**Completed**: 2026-03-01T10:30:00Z

### Description

Implement Scenarios 2-7 from the feature context covering browse and view operations consumed by `/work-backlog-item`. Tests: (2) list with `with_status=True` -- assert `items` list with `section`, `title`, `issue`, `plan`, `status`, `milestone`, `file_path`, `groomed` fields; (3) list with `from_github=True` -- assert `refresh_local_cache_from_github` integration; (4) list with `label` filter -- assert only matching items returned; (5) view by issue number `#42` -- assert `title`, `priority`, `issue`, `body`, `groomed`, `status`, `labels`, `milestone` fields; (6) view by title substring -- assert matching item with `file_path`; (7) view with pagination params `offset`/`limit` -- assert `body_truncated`, `body_remaining_lines`, `body_total_lines` fields. Pre-create test items via `write_test_item` fixture. Reference the Response Shape Registry for exact field requirements per consuming skill.

### Acceptance Criteria

- [ ] Six tests in `TestWorkBacklogItem` class covering Scenarios 2-7
- [ ] Scenario 2: `test_list_with_status` asserts all 8 item-level fields from Response Shape Registry
- [ ] Scenario 3: `test_list_from_github` asserts `from_github=True` triggers refresh path
- [ ] Scenario 4: `test_list_with_label_filter` asserts only matching items returned
- [ ] Scenario 5: `test_view_by_issue_number` asserts all view response fields
- [ ] Scenario 6: `test_view_by_title_substring` asserts match with `file_path`
- [ ] Scenario 7: `test_view_with_pagination` asserts pagination fields (`body_truncated`, `body_remaining_lines`, `body_total_lines`)
- [ ] All tests use `backlog_dir`, `mock_github`, and `write_test_item` fixtures

### Verification Steps

1. Run `uv run pytest .claude/skills/backlog/tests/test_scenarios.py::TestWorkBacklogItem -x -v` and confirm all 6 tests pass
2. Verify each test's assertions cover the fields listed in the Response Shape Registry for the consuming skill
3. Confirm tests work with `-n auto` (no shared state between tests)

---

## Task 2.3: Work-Backlog-Item Plan/Status/Update Scenarios (backlog_update)

**Status**: ✅ COMPLETE
**Dependencies**: Task 1.1, Task 1.2
**Priority**: 2
**Complexity**: Medium
**Agent**: fastmcp-python-tests
**Started**: 2026-03-01T09:10:00Z
**Completed**: 2026-03-01T10:30:00Z

### Description

Implement Scenarios 8-10 from the feature context covering update operations. Tests: (8) update item with plan -- assert `title`, `plan` in response and per-item file metadata updated; (9) update item status to in-progress -- assert `title`, `status` in response and `apply_status_in_progress` called; (10) update item creating a GitHub issue -- assert `title`, `issue_num` for P0/P1 items. Pre-create test items via `write_test_item`. For Scenario 9, configure `mock_github["try_get_github"]` to return a mock repo so `apply_status_in_progress` can be called. For Scenario 10, configure `mock_github["try_get_github"]` and `mock_github["create_issue_for_item"]` to enable issue creation.

### Acceptance Criteria

- [ ] Three tests in `TestWorkBacklogItem` class covering Scenarios 8-10
- [ ] Scenario 8: `test_update_with_plan` asserts `result["plan"]` matches the provided plan path and per-item file reflects update
- [ ] Scenario 9: `test_update_status_in_progress` asserts `result["status"]` is `"in-progress"` and `mock_github["apply_status_in_progress"]` was called
- [ ] Scenario 10: `test_update_create_github_issue` asserts `result["issue_num"]` is an int and `mock_github["create_issue_for_item"]` was called
- [ ] All tests assert output envelope (`messages`, `warnings`, `errors` lists)

### Verification Steps

1. Run `uv run pytest .claude/skills/backlog/tests/test_scenarios.py::TestWorkBacklogItem -x -v -k "update"` and confirm all 3 tests pass
2. Verify mock interactions (`.assert_called_once()` or `.assert_called()`) are validated
3. Confirm per-item file content is inspected via `backlog_dir` path reads

---

## Task 2.4: Work-Backlog-Item Close Scenarios (backlog_close)

**Status**: ✅ COMPLETE
**Dependencies**: Task 1.1, Task 1.2
**Priority**: 2
**Complexity**: Medium
**Agent**: fastmcp-python-tests
**Started**: 2026-03-01T09:10:00Z
**Completed**: 2026-03-01T10:30:00Z

### Description

Implement Scenario 11 from the feature context: "Close item with checklist pass". Call `backlog_close` with `selector`, `plan`, and `checklist_pass=True`. Assert response contains `title` and `closed: True`. Verify `mock_github["close_github_issue"]` was called. Configure `mock_github["get_github"]` and `mock_github["check_open_prs_for_issue"]` to return appropriate values (mock repo, empty PR list). Pre-create an item with an issue number via `write_test_item(title, issue="#42")`.

### Acceptance Criteria

- [ ] Test `test_close_with_checklist_pass` in `TestWorkBacklogItem` class
- [ ] Pre-creates item with issue number via `write_test_item`
- [ ] Calls `backlog_close` with `checklist_pass=True`
- [ ] Asserts `result["closed"]` is `True` and `result["title"]` is a string
- [ ] Verifies `mock_github["close_github_issue"]` was called with correct arguments
- [ ] Asserts output envelope fields present

### Verification Steps

1. Run `uv run pytest .claude/skills/backlog/tests/test_scenarios.py -x -v -k "test_close"` and confirm test passes
2. Verify the test configures `mock_github["get_github"]` to return a mock repository
3. Confirm `check_open_prs_for_issue` returns empty list (no blocking PRs)

---

## Task 2.5: Work-Backlog-Item Resolve Scenarios (backlog_resolve)

**Status**: ✅ COMPLETE
**Dependencies**: Task 1.1, Task 1.2
**Priority**: 2
**Complexity**: Medium
**Agent**: fastmcp-python-tests
**Started**: 2026-03-01T09:10:00Z
**Completed**: 2026-03-01T10:30:00Z

### Description

Implement Scenarios 12-13 from the feature context covering resolve operations. Tests: (12) resolve item with reason -- assert `title`, `resolved: True`, verify `resolve_github_issue` called with correct args; (13) resolve with `cleanup=True` -- assert `resolved: True` and local file removed. For cleanup testing, pre-create an item with an issue number and configure `mock_github["get_github"]` to return a mock repo. The `_close_cleanup` guard requires `issue_ref` to exist for file removal.

### Acceptance Criteria

- [ ] Two tests in `TestWorkBacklogItem` class covering Scenarios 12-13
- [ ] Scenario 12: `test_resolve_with_reason` asserts `result["resolved"]` is `True` and `resolve_github_issue` called
- [ ] Scenario 13: `test_resolve_with_cleanup` asserts `result["resolved"]` is `True` and the per-item file no longer exists on disk
- [ ] Both tests pre-create items with issue numbers via `write_test_item`
- [ ] Both tests configure `mock_github["get_github"]` appropriately
- [ ] Output envelope asserted on both tests

### Verification Steps

1. Run `uv run pytest .claude/skills/backlog/tests/test_scenarios.py -x -v -k "resolve"` and confirm both tests pass
2. For Scenario 13, verify that the file path from `write_test_item` no longer exists after the resolve call
3. Confirm `check_open_prs_for_issue` returns empty list in both tests

---

## Task 2.6: Groom-Backlog-Item Scenarios (backlog_groom)

**Status**: ✅ COMPLETE
**Dependencies**: Task 1.1, Task 1.2
**Priority**: 2
**Complexity**: High
**Agent**: fastmcp-python-tests
**Started**: 2026-03-01T10:31:00Z
**Completed**: 2026-03-01T11:30:00Z

### Description

Implement Scenarios 14-17 from the feature context covering groom operations consumed by `/groom-backlog-item`. Tests: (14) groom with full content replacement -- assert `groomed_updated: True`, verify per-item file has `## Groomed` section, verify GitHub issue body updated via `sync_groomed_to_github_issue`; (15) groom with incremental section update -- assert `groomed_updated: True`, verify section appended/replaced in per-item file; (16) groom item without GitHub issue (local only) -- assert `groomed_updated: True`, verify no GitHub sync attempted (`sync_groomed_to_github_issue` NOT called); (17) groom via `backlog_update` with `groomed_content` param -- same assertions as Scenario 14 but through the `backlog_update` tool path. Configure `mock_github["try_get_github"]` appropriately: return mock repo for Scenarios 14-15, return `None` for Scenario 16.

### Acceptance Criteria

- [ ] Four tests in `TestGroomBacklogItem` class covering Scenarios 14-17
- [ ] Scenario 14: `test_groom_full_content` asserts `groomed_updated` is `True`, file contains groomed section
- [ ] Scenario 15: `test_groom_incremental_section` asserts `groomed_updated` is `True`, specific section updated in file
- [ ] Scenario 16: `test_groom_local_only` asserts `groomed_updated` is `True`, `sync_groomed_to_github_issue` NOT called
- [ ] Scenario 17: `test_groom_via_update` calls `backlog_update` with `groomed_content` param and asserts `groomed_updated` is `True`
- [ ] All tests pre-create items via `write_test_item` and verify file contents after groom

### Verification Steps

1. Run `uv run pytest .claude/skills/backlog/tests/test_scenarios.py::TestGroomBacklogItem -x -v` and confirm all 4 tests pass
2. Verify Scenario 16 uses `.assert_not_called()` on `sync_groomed_to_github_issue`
3. Read per-item file contents after each groom test to verify content changes

---

## Task 2.7: Group-Items-to-Milestone and Backlog-Item-Groomer Scenarios (backlog_list)

**Status**: ✅ COMPLETE
**Dependencies**: Task 1.1, Task 1.2
**Priority**: 3
**Complexity**: Medium
**Agent**: fastmcp-python-tests
**Started**: 2026-03-01T10:31:00Z
**Completed**: 2026-03-01T11:30:00Z

### Description

Implement Scenarios 18-19 from the feature context. Scenario 18: list items for milestone selection (consumed by `/group-items-to-milestone`) -- call `backlog_list(with_status=True)` and assert each item has `section`, `title`, `issue`, `status`, `milestone` fields for milestone assignment UI. Scenario 19: groomer reads list then views item (consumed by `@backlog-item-groomer`) -- call `backlog_list()` to get items, then call `backlog_view(selector=...)` on one item and assert `body`, `description`, `groomed` fields present. Pre-create multiple test items with different priorities and issue numbers.

### Acceptance Criteria

- [ ] Scenario 18: `test_list_for_milestone_selection` in `TestGroupItemsToMilestone` asserts milestone-relevant fields on each item
- [ ] Scenario 19: `test_groomer_list_then_view` in `TestBacklogItemGroomer` chains `backlog_list` and `backlog_view` calls, asserts groomer-relevant fields
- [ ] Both tests pre-create items via `write_test_item` with distinct titles and priorities
- [ ] Response field assertions match the Response Shape Registry columns for the consuming skill/agent
- [ ] Output envelope asserted on all responses

### Verification Steps

1. Run `uv run pytest .claude/skills/backlog/tests/test_scenarios.py::TestGroupItemsToMilestone -x -v` and confirm test passes
2. Run `uv run pytest .claude/skills/backlog/tests/test_scenarios.py::TestBacklogItemGroomer -x -v` and confirm test passes
3. Verify Scenario 19 uses the `selector` from the list response to call view (not a hardcoded value)

---

## Task 2.8: Sync and Pull Scenarios (backlog_sync, backlog_pull)

**Status**: ✅ COMPLETE
**Dependencies**: Task 1.1, Task 1.2
**Priority**: 2
**Complexity**: High
**Agent**: fastmcp-python-tests
**Started**: 2026-03-01T10:31:00Z
**Completed**: 2026-03-01T11:30:00Z

### Description

Implement Scenarios 20-21 from the feature context. Scenario 20: sync creates missing issues and pushes groomed -- call `backlog_sync()`, assert `created` count > 0 and `pushed` count >= 0, verify `create_issue_for_item` called for items without issues, verify `fetch_open_issues_by_title` called. Scenario 21: pull updates local from GitHub -- call `backlog_pull()`, assert `pulled` count > 0, verify local files updated with GitHub issue body content. For sync, configure `mock_github["get_github"]` and `mock_github["fetch_open_issues_by_title"]` to return empty dict (no existing issues). For pull, configure `mock_github["fetch_github_issue_body"]` to return specific content. Pre-create items: for sync, items without issue numbers; for pull, items with issue numbers whose local content differs from the mock GitHub body.

### Acceptance Criteria

- [ ] Two tests in `TestSyncAndPull` class covering Scenarios 20-21
- [ ] Scenario 20: `test_sync_creates_missing_issues` asserts `result["created"]` > 0, `create_issue_for_item` called
- [ ] Scenario 21: `test_pull_updates_local` asserts `result["pulled"]` > 0, local file content changed
- [ ] Both tests assert output envelope fields
- [ ] Both tests configure `mock_github["get_github"]` to return a mock repository object
- [ ] Pull test verifies file content on disk matches the mocked GitHub body

### Verification Steps

1. Run `uv run pytest .claude/skills/backlog/tests/test_scenarios.py::TestSyncAndPull -x -v` and confirm both tests pass
2. For sync test, verify pre-created items lack issue numbers before sync and have them after
3. For pull test, read file contents before and after to confirm update occurred

---

## Task 2.9: Normalize Scenarios (backlog_normalize)

**Status**: ✅ COMPLETE
**Dependencies**: Task 1.1, Task 1.2
**Priority**: 3
**Complexity**: Medium
**Agent**: fastmcp-python-tests
**Started**: 2026-03-01T10:31:00Z
**Completed**: 2026-03-01T11:30:00Z

### Description

Implement tests for the `backlog_normalize` tool. Create test items with non-normalized frontmatter (e.g., hand-crafted YAML with inconsistent field ordering, missing optional fields, or non-canonical slug filenames) and call `backlog_normalize()`. Assert `result["updated"]` count reflects the number of items normalized. Verify file contents are in canonical format after normalization. Note from feature context: `build_backlog_frontmatter()` produces the normalized format, so pre-normalization files may need hand-crafted frontmatter to test the transformation path.

### Acceptance Criteria

- [ ] Test `test_normalize_updates_items` in `TestNormalize` class
- [ ] Creates at least one item with non-canonical frontmatter (hand-crafted, not via `build_backlog_frontmatter`)
- [ ] Calls `backlog_normalize()` and asserts `result["updated"]` > 0
- [ ] Verifies file contents are in canonical format after normalization
- [ ] Asserts output envelope fields present

### Verification Steps

1. Run `uv run pytest .claude/skills/backlog/tests/test_scenarios.py::TestNormalize -x -v` and confirm test passes
2. Read the pre-normalization and post-normalization file contents to verify the transformation
3. Confirm the test uses `backlog_dir` fixture for file isolation

---

## Task 2.10: Error Path Tests

**Status**: ✅ COMPLETE
**Dependencies**: Task 1.1, Task 1.2
**Priority**: 2
**Complexity**: Medium
**Agent**: fastmcp-python-tests
**Started**: 2026-03-01T10:31:00Z
**Completed**: 2026-03-01T11:30:00Z

### Description

Implement Scenarios 22-25 from the feature context covering error paths. Tests: (22) close without `checklist_pass` -- assert `error` key with `"checklist_pass required"` substring; (23) view nonexistent item -- assert `error` key with `"No item found"` substring; (24) add duplicate item with `force=False` -- pre-create item, attempt to add with same title, assert `error` key with `"Similar backlog items found"` substring; (25) list on empty backlog directory -- assert `items: []` and `count: 0` (not an error, empty is valid). Error paths verify that `BacklogError` subclasses are caught by the server layer and converted to `{"error": str(e), **out.to_dict()}` responses.

### Acceptance Criteria

- [ ] Four tests in `TestErrorPaths` class covering Scenarios 22-25
- [ ] Scenario 22: `test_close_without_checklist_pass` asserts `"error"` key present with `"checklist_pass"` or `"checklist"` substring
- [ ] Scenario 23: `test_view_nonexistent_item` asserts `"error"` key present with `"No item found"` or `"not found"` substring
- [ ] Scenario 24: `test_add_duplicate_force_false` pre-creates item, asserts `"error"` key on duplicate add
- [ ] Scenario 25: `test_list_empty_backlog` asserts `result["items"]` is `[]` and `result["count"]` is `0`
- [ ] All error responses assert output envelope (`messages`, `warnings`, `errors` lists)

### Verification Steps

1. Run `uv run pytest .claude/skills/backlog/tests/test_scenarios.py::TestErrorPaths -x -v` and confirm all 4 tests pass
2. Verify error response tests check for both the `error` key and the output envelope
3. Confirm Scenario 25 does NOT assert an `error` key (empty list is valid, not an error)

---

## Task 2.11: Full Lifecycle Tests

**Status**: ✅ COMPLETE
**Dependencies**: Task 2.1, Task 2.4, Task 2.5, Task 2.6
**Priority**: 2
**Complexity**: High
**Agent**: fastmcp-python-tests
**Started**: 2026-03-01T11:35:00Z
**Completed**: 2026-03-01T12:00:00Z

### Description

Implement Scenarios 26-28 from the feature context covering full lifecycle sequences spanning multiple MCP tool calls. Lifecycle 1 (Scenario 26): create -> groom -> update -> close -- verify item progresses through states and final close returns `closed: True`. Lifecycle 2 (Scenario 27): create -> resolve with cleanup -- verify item file created then removed, `resolved: True`. Note: `cleanup=True` requires an issue ref to trigger file removal, so configure `mock_github["try_get_github"]` and use `create_issue=True` on the add call. Lifecycle 3 (Scenario 28): stale item discovery -- pre-create item with issue `#100`, configure `batch_fetch_statuses` to return `{}` (issue not in open issues), call `backlog_list(with_status=True)`, assert item appears with empty status signaling staleness. Reference the architecture spec Lifecycle Test Design section for detailed call sequences.

### Acceptance Criteria

- [ ] Three tests in `TestLifecycles` class covering Scenarios 26-28
- [ ] Lifecycle 1: `test_create_groom_update_close` chains 4 MCP tool calls in sequence, final `closed` is `True`
- [ ] Lifecycle 2: `test_create_resolve_cleanup` chains 2 MCP tool calls, file does not exist after resolve
- [ ] Lifecycle 3: `test_stale_item_discovery` pre-creates item with issue, asserts empty status in list response
- [ ] Each lifecycle test uses `backlog_dir` and `mock_github` fixtures
- [ ] Lifecycle 2 configures `mock_github["try_get_github"]` to return a mock repo so `create_issue=True` works

### Verification Steps

1. Run `uv run pytest .claude/skills/backlog/tests/test_scenarios.py::TestLifecycles -x -v` and confirm all 3 tests pass
2. For Lifecycle 1, verify intermediate states (groom updates file, update changes plan, close marks closed)
3. For Lifecycle 2, verify file existence before and after resolve using `Path.exists()`

---

## Group 3: Suite 2 -- Live Validation Tests (no mocks)

## Task 3.1: Live Test Fixtures and File Boilerplate

**Status**: ✅ COMPLETE
**Dependencies**: Task 1.1
**Priority**: 3
**Complexity**: Medium
**Agent**: fastmcp-python-tests
**Started**: 2026-03-01T12:05:00Z
**Completed**: 2026-03-01T12:30:00Z

### Description

Create `.claude/skills/backlog/tests/test_live_validation.py` with the live test infrastructure: module-level skip condition (`GITHUB_TOKEN` not set), `pytestmark` with `pytest.mark.e2e`, `_call` helper, and the `live_items` class-scoped fixture. The `live_items` fixture must: create a temp backlog dir, monkeypatch `BACKLOG_DIR`, generate a UUID test ID, track created issue numbers in a list, and clean up all created issues in teardown (closing open issues via direct PyGithub API). Issue titles must use `[MCP-TEST-{uuid}]` prefix. Create the `TestLiveLifecycle` class stub with ordered test method stubs (L1-L11).

### Acceptance Criteria

- [ ] File exists at `.claude/skills/backlog/tests/test_live_validation.py`
- [ ] Module-level `pytestmark` includes `pytest.mark.e2e` and skip condition on `GITHUB_TOKEN`
- [ ] `live_items` fixture is `scope="class"`, yields test context dict, cleans up issues in teardown
- [ ] Cleanup uses PyGithub API directly (not MCP tools) for reliability
- [ ] Issue title convention: `[MCP-TEST-{uuid}]` prefix
- [ ] `TestLiveLifecycle` class with 11 stub test methods (L1-L11)
- [ ] File collects without errors when `GITHUB_TOKEN` is not set (tests skip, not error)

### Verification Steps

1. Run `uv run pytest .claude/skills/backlog/tests/test_live_validation.py --collect-only` and confirm tests are collected (or skipped if no token)
2. Verify the cleanup fixture handles exceptions gracefully (best-effort cleanup)
3. Confirm `BACKLOG_DIR` is redirected to temp directory even for live tests

---

## Task 3.2: Live Lifecycle Tests (L1-L11)

**Status**: ✅ COMPLETE
**Dependencies**: Task 3.1
**Priority**: 3
**Complexity**: High
**Agent**: fastmcp-python-tests
**Started**: 2026-03-01T12:05:00Z
**Completed**: 2026-03-01T12:30:00Z

### Description

Implement all 11 live validation tests (L1-L11) as specified in the feature context and architecture spec. Tests L1-L10 operate on a single item created in L1. Test L11 creates a second item and resolves it. Both items must be tracked in `live_items["issues"]` for cleanup. Tests: L1 add with real issue; L2 list includes created item; L3 view by issue number; L4 update attach plan; L5 update set status in-progress; L6 groom write full content; L7 groom incremental section; L8 sync push groomed; L9 pull refresh from GitHub; L10 close full lifecycle end; L11 resolve alternative end (separate item). Each test asserts the response shape matching the Response Shape Registry. Tests must execute in declaration order within the class (pytest preserves method order). Use `pytest-xdist`-safe patterns: different workers get different UUIDs.

### Acceptance Criteria

- [ ] 11 tests in `TestLiveLifecycle` class (test_l1 through test_l11)
- [ ] L1: `backlog_add` with `create_issue=True`, asserts `issue_num` > 0, stores issue number in `live_items["issues"]`
- [ ] L2-L9: each asserts response fields matching Response Shape Registry for the tool called
- [ ] L10: `backlog_close` with `checklist_pass=True`, asserts `closed: True`
- [ ] L11: creates a second item, resolves it, asserts `resolved: True`, stores second issue number for cleanup
- [ ] All tests skip when `GITHUB_TOKEN` is not set
- [ ] All tests pass with `uv run pytest .claude/skills/backlog/tests/test_live_validation.py -m e2e` when `GITHUB_TOKEN` is available

### Verification Steps

1. Run `uv run pytest .claude/skills/backlog/tests/test_live_validation.py -m e2e -v` with `GITHUB_TOKEN` set and confirm all 11 pass
2. Verify created GitHub issues have `[MCP-TEST-{uuid}]` prefix in title
3. Confirm all created issues are closed after test run (manual check or API query)

---

## Group 4: Quality Gates

## Task 4.1: Run Full Test Suite

**Status**: ✅ COMPLETE
**Started**: 2026-03-01T22:30:00Z
**Completed**: 2026-03-01T22:45:00Z
**Dependencies**: Task 2.1, Task 2.2, Task 2.3, Task 2.4, Task 2.5, Task 2.6, Task 2.7, Task 2.8, Task 2.9, Task 2.10, Task 2.11
**Priority**: 1
**Complexity**: Medium
**Agent**: general-purpose

### Description

Run the complete backlog test suite: all existing tests plus all new scenario integration tests. Verify zero failures and zero errors. Verify existing 42 tests in `test_backlog_core_server.py` still pass unchanged. Run with `-n auto` to validate parallel execution safety. Run with `--tb=short` for readable failure output. If any tests fail, report the failure details and which task introduced the regression.

### Acceptance Criteria

- [ ] `uv run pytest .claude/skills/backlog/tests/test_backlog_core_server.py -x` passes (42 existing tests)
- [ ] `uv run pytest .claude/skills/backlog/tests/test_scenarios.py -x` passes (28+ new scenario tests)
- [ ] `uv run pytest .claude/skills/backlog/tests/ -m "not e2e" -n auto` passes (all non-live tests in parallel)
- [ ] Zero test failures, zero collection errors
- [ ] Test count reported: 42 existing + 28+ new = 70+ total tests (excluding e2e)

### Verification Steps

1. Run `uv run pytest .claude/skills/backlog/tests/ -m "not e2e" -v --tb=short` and capture full output
2. Run `uv run pytest .claude/skills/backlog/tests/ -m "not e2e" -n auto` and confirm parallel execution passes
3. Compare test count against expected: at least 70 tests total (42 existing + 28 new)

---

## Task 4.2: Code Review

**Status**: ✅ COMPLETE
**Started**: 2026-03-01T22:45:00Z
**Completed**: 2026-03-01T23:00:00Z
**Dependencies**: Task 4.1
**Priority**: 1
**Complexity**: Medium
**Agent**: code-review

### Description

Review all new and modified files for code quality, test design, and adherence to the architecture spec. Files to review: `.claude/skills/backlog/tests/conftest.py` (additions only), `.claude/skills/backlog/tests/test_scenarios.py`, `.claude/skills/backlog/tests/test_live_validation.py`. Check: mock boundaries are correct (operations.py boundary, not github.py originals); `BACKLOG_DIR` patched in all three modules; `build_backlog_frontmatter()` used for test data creation; response shape assertions match the Response Shape Registry; no `@pytest.mark.asyncio` decorators; no shared mutable state between tests; cleanup fixture handles exceptions. Flag any tests that mock at the operations layer (should only use `mock_github` fixture for github.py boundary mocks).

### Acceptance Criteria

- [ ] All mock patches target `backlog_core.operations.*` namespace (not `backlog_core.github.*`)
- [ ] `BACKLOG_DIR` patched in `models`, `operations`, and `parsing` modules
- [ ] No test uses `@pytest.mark.asyncio` decorator
- [ ] Response shape assertions verified against Response Shape Registry for each tool/consumer pair
- [ ] Test data created via `build_backlog_frontmatter()` or `write_test_item` fixture (no hand-crafted YAML except for normalize test)
- [ ] Live test cleanup fixture uses `try/except` for best-effort cleanup
- [ ] No follow-up task file needed (or if needed, created at `plan/tasks-12-backlog-mcp-scenarios-followup-1.md`)

### Verification Steps

1. Grep for `@pytest.mark.asyncio` in new test files -- must find zero occurrences
2. Grep for `backlog_core.github.` in mock patches -- must find zero occurrences (all patches at operations boundary)
3. Verify `conftest.py` patches three `BACKLOG_DIR` bindings (models, operations, parsing)
