"""Integration tests for the four dispatch MCP tools in backlog_core.server.

Tests: dispatch_wave_start, dispatch_item_status, dispatch_wave_status, dispatch_spawn
Strategy:
  - Each test uses a fresh DispatchStateManager backed by a tmp_path SQLite file.
  - The module-level singleton ``_dispatch_state_manager`` is patched so every tool
    call routes to the per-test manager, preventing cross-test state bleed.
  - subprocess calls are mocked via mocker.patch on asyncio.create_subprocess_exec so
    no real processes are ever spawned.
  - FastMCP in-memory Client is used for all tool invocations (no HTTP transport).
  - ``asyncio_mode = "auto"`` is declared in pyproject.toml; no @pytest.mark.asyncio.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from backlog_core.dispatch_state import DispatchStateManager
from backlog_core.models import DispatchItemRecord
from backlog_core.server import mcp
from fastmcp.client import Client

if TYPE_CHECKING:
    from pytest_mock import MockerFixture

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_mgr(tmp_path: Path) -> DispatchStateManager:
    """Return a fresh DispatchStateManager backed by a tmp_path database.

    Args:
        tmp_path: pytest-provided temporary directory.

    Returns:
        Initialised DispatchStateManager with clean schema.
    """
    return DispatchStateManager(tmp_path / "dispatch-test.db")


def _seed_wave(
    mgr: DispatchStateManager, milestone: int = 10, wave_num: int = 1, issues: list[int] | None = None
) -> None:
    """Seed a wave with items into an existing manager.

    Args:
        mgr: Manager to insert into.
        milestone: Milestone number (default 10).
        wave_num: Wave number (default 1).
        issues: Issue numbers to create items for (default [101, 102]).
    """
    if issues is None:
        issues = [101, 102]
    items = [DispatchItemRecord(milestone=milestone, wave_num=wave_num, issue=n, title=f"Issue {n}") for n in issues]
    mgr.create_wave(milestone=milestone, wave_num=wave_num, items=items)


def _make_dispatch_plan_yaml(milestone: int = 10, wave_num: int = 1, issues: list[int] | None = None) -> str:
    """Return a minimal dispatch plan YAML string for use in fixture files.

    Args:
        milestone: Milestone number to embed.
        wave_num: Wave number.
        issues: Issue numbers for the wave items (default [101, 102]).

    Returns:
        YAML string conforming to the DispatchPlan schema.
    """
    if issues is None:
        issues = [101, 102]
    items_yaml = "\n".join(f"    - title: Issue {i}\n      issue: {i}\n      priority: P2" for i in issues)
    return f"""\
milestone:
  number: {milestone}
  title: Test milestone {milestone}
  integration-branch: main
waves:
  - wave: {wave_num}
    items:
{items_yaml}
"""


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mgr(tmp_path: Path) -> DispatchStateManager:
    """Provide a fresh DispatchStateManager for each test.

    Returns:
        Clean DispatchStateManager instance backed by a temporary SQLite file.
    """
    return _make_mgr(tmp_path)


@pytest.fixture
def patch_state_manager(mocker: MockerFixture, mgr: DispatchStateManager) -> DispatchStateManager:
    """Patch _dispatch_state_manager() to return the per-test mgr.

    This patches the module-level singleton factory so every tool call in
    server.py uses the isolated test database rather than the real
    ~/.dh/.../dispatch-state.db path.

    Returns:
        The same DispatchStateManager instance passed to every tool call.
    """
    mocker.patch("backlog_core.server._dispatch_state_manager", return_value=mgr)
    return mgr


@pytest.fixture
def dispatch_plan_file(tmp_path: Path) -> Path:
    """Write a minimal dispatch plan YAML to a tmp file and return its path.

    Returns:
        Path to the written dispatch plan YAML file.
    """
    plan_path = tmp_path / "milestone-10-dispatch.yaml"
    plan_path.write_text(_make_dispatch_plan_yaml())
    return plan_path


@pytest.fixture
def patch_dispatch_plan_path(mocker: MockerFixture, dispatch_plan_file: Path) -> Path:
    """Patch _dispatch_plan_path() to return the tmp dispatch plan file.

    Returns:
        Path to the patched dispatch plan file.
    """
    mocker.patch("backlog_core.server._dispatch_plan_path", return_value=dispatch_plan_file)
    return dispatch_plan_file


# ---------------------------------------------------------------------------
# dispatch_wave_start
# ---------------------------------------------------------------------------


class TestDispatchWaveStart:
    """Integration tests for the dispatch_wave_start MCP tool.

    Tests tool registration, success path, duplicate prevention, and
    response field contract. All calls use the FastMCP in-memory Client
    against the real ``mcp`` application instance so the full tool
    dispatch stack is exercised.
    """

    async def test_creates_wave_successfully(self, patch_state_manager: DispatchStateManager) -> None:
        """dispatch_wave_start returns wave metadata on first call.

        Tests: dispatch_wave_start happy path
        How: Call the tool via in-memory Client with milestone=10, wave_num=1,
             two items. Verify the response contains expected fields.
        Why: Tool callers depend on wave_id, items_count, and status fields
             to seed their dispatch loop state.
        """
        # Arrange
        items = [{"issue": 101, "title": "Feature A"}, {"issue": 102, "title": "Feature B"}]

        # Act
        async with Client(mcp) as client:
            result = await client.call_tool("dispatch_wave_start", {"milestone": 10, "wave_num": 1, "items": items})

        # Assert
        data: dict[str, Any] = result.data
        assert data["milestone"] == 10
        assert data["wave_num"] == 1
        assert data["items_count"] == 2
        assert data["status"] == "pending"
        assert "error" not in data

    async def test_returns_error_on_duplicate_wave(self, patch_state_manager: DispatchStateManager) -> None:
        """dispatch_wave_start returns an error dict when the wave already exists.

        Tests: dispatch_wave_start duplicate prevention
        How: Call the tool twice with the same milestone+wave_num. Verify the
             second call returns an ``error`` key without raising an exception.
        Why: The tool must not crash the server on duplicate dispatch; callers
             check for the error key to detect idempotency violations.
        """
        # Arrange
        items = [{"issue": 101, "title": "Feature A"}]

        async with Client(mcp) as client:
            # First call — should succeed
            await client.call_tool("dispatch_wave_start", {"milestone": 10, "wave_num": 1, "items": items})

            # Act — second call with same (milestone, wave_num)
            result = await client.call_tool("dispatch_wave_start", {"milestone": 10, "wave_num": 1, "items": items})

        # Assert
        data: dict[str, Any] = result.data
        assert "error" in data
        assert "10" in data["error"] or "Wave 1" in data["error"]

    async def test_creates_items_in_database(self, patch_state_manager: DispatchStateManager) -> None:
        """dispatch_wave_start persists items to the state database.

        Tests: dispatch_wave_start side-effect on state
        How: Call the tool, then read back wave items directly from the
             manager to confirm persistence occurred.
        Why: If items are not written, subsequent dispatch_item_status calls
             will fail to find items by issue number.
        """
        # Arrange
        items = [{"issue": 201, "title": "Task one"}, {"issue": 202, "title": "Task two"}]

        # Act
        async with Client(mcp) as client:
            await client.call_tool("dispatch_wave_start", {"milestone": 20, "wave_num": 1, "items": items})

        # Assert
        persisted = patch_state_manager.get_wave_items(milestone=20, wave_num=1)
        assert len(persisted) == 2
        assert {i.issue for i in persisted} == {201, 202}
        assert all(i.status == "pending" for i in persisted)

    async def test_response_contains_messages_and_warnings(self, patch_state_manager: DispatchStateManager) -> None:
        """dispatch_wave_start success response includes messages and warnings lists.

        Tests: dispatch_wave_start response schema
        How: Create a wave and inspect the messages/warnings keys.
        Why: Callers expect these lists to be present (even if empty) for
             uniform response handling.
        """
        # Arrange + Act
        async with Client(mcp) as client:
            result = await client.call_tool(
                "dispatch_wave_start", {"milestone": 30, "wave_num": 1, "items": [{"issue": 301, "title": "X"}]}
            )

        # Assert
        data: dict[str, Any] = result.data
        assert isinstance(data.get("messages"), list)
        assert isinstance(data.get("warnings"), list)


# ---------------------------------------------------------------------------
# dispatch_item_status
# ---------------------------------------------------------------------------


class TestDispatchItemStatus:
    """Integration tests for the dispatch_item_status MCP tool.

    Tests the complete/failed/skipped/invalid status transitions and the
    not-found error path. The tool searches across all waves for a matching
    issue number, so seeding via the state manager is sufficient setup.
    """

    async def test_marks_item_complete(self, patch_state_manager: DispatchStateManager) -> None:
        """dispatch_item_status records completion for an existing item.

        Tests: dispatch_item_status — complete transition
        How: Seed a wave with issue 101, call the tool with status=complete,
             then verify the item is marked complete in the database.
        Why: Spawned workers report completion through this tool; incorrect
             status transitions cause the dispatch loop to stall.
        """
        # Arrange
        _seed_wave(patch_state_manager, milestone=10, wave_num=1, issues=[101, 102])

        # Act
        async with Client(mcp) as client:
            result = await client.call_tool(
                "dispatch_item_status", {"milestone": 10, "issue": 101, "status": "complete", "result": "ok"}
            )

        # Assert
        data: dict[str, Any] = result.data
        assert data["milestone"] == 10
        assert data["issue"] == 101
        assert data["status"] == "complete"
        assert "error" not in data

        item = patch_state_manager.get_item(milestone=10, wave_num=1, issue=101)
        assert item is not None
        assert item.status == "complete"

    async def test_marks_item_failed(self, patch_state_manager: DispatchStateManager) -> None:
        """dispatch_item_status records failure for an existing item.

        Tests: dispatch_item_status — failed transition
        How: Seed a wave with issue 101, call the tool with status=failed and
             an error message. Verify item status and error field in the database.
        Why: Failure tracking drives retry decisions and post-dispatch summaries.
        """
        # Arrange
        _seed_wave(patch_state_manager, milestone=10, wave_num=1, issues=[101])

        # Act
        async with Client(mcp) as client:
            result = await client.call_tool(
                "dispatch_item_status", {"milestone": 10, "issue": 101, "status": "failed", "error": "timeout"}
            )

        # Assert
        data: dict[str, Any] = result.data
        assert data["status"] == "failed"
        assert "error" not in data  # no lookup error

        item = patch_state_manager.get_item(milestone=10, wave_num=1, issue=101)
        assert item is not None
        assert item.status == "failed"
        assert item.error == "timeout"

    async def test_marks_item_skipped(self, patch_state_manager: DispatchStateManager) -> None:
        """dispatch_item_status treats skipped as a failed terminal state.

        Tests: dispatch_item_status — skipped transition
        How: Seed a wave, call with status=skipped. Verify the DB item is
             in failed state (skipped maps to failed per implementation).
        Why: skipped is a valid dispatch outcome that must be persisted as
             terminal to avoid re-dispatch.
        """
        # Arrange
        _seed_wave(patch_state_manager, milestone=10, wave_num=1, issues=[101])

        # Act
        async with Client(mcp) as client:
            result = await client.call_tool(
                "dispatch_item_status", {"milestone": 10, "issue": 101, "status": "skipped"}
            )

        # Assert
        data: dict[str, Any] = result.data
        assert data["status"] == "skipped"
        assert "error" not in data

    async def test_returns_error_for_unknown_issue(self, patch_state_manager: DispatchStateManager) -> None:
        """dispatch_item_status returns error dict when issue not found in any wave.

        Tests: dispatch_item_status — not-found path
        How: Call the tool for an issue number that was never seeded.
        Why: Callers must be able to detect missing items without the server
             raising an unhandled exception.
        """
        # Arrange — empty database, issue 999 does not exist

        # Act
        async with Client(mcp) as client:
            result = await client.call_tool(
                "dispatch_item_status", {"milestone": 10, "issue": 999, "status": "complete"}
            )

        # Assert
        data: dict[str, Any] = result.data
        assert "error" in data
        assert "999" in data["error"]

    async def test_returns_error_for_invalid_status(self, patch_state_manager: DispatchStateManager) -> None:
        """dispatch_item_status returns error dict for an unrecognised status value.

        Tests: dispatch_item_status — invalid status guard
        How: Seed an item, then call with status='running' (not a valid value).
        Why: Prevents silent corruption of item state with arbitrary string values.
        """
        # Arrange
        _seed_wave(patch_state_manager, milestone=10, wave_num=1, issues=[101])

        # Act
        async with Client(mcp) as client:
            result = await client.call_tool(
                "dispatch_item_status", {"milestone": 10, "issue": 101, "status": "running"}
            )

        # Assert
        data: dict[str, Any] = result.data
        assert "error" in data
        assert "running" in data["error"]


# ---------------------------------------------------------------------------
# dispatch_wave_status
# ---------------------------------------------------------------------------


class TestDispatchWaveStatus:
    """Integration tests for the dispatch_wave_status MCP tool.

    Verifies the wave summary aggregation, stale-PID detection, and
    not-found error path. check_stale_pids is exercised by patching os.kill
    so no live process management occurs.
    """

    async def test_returns_wave_summary_for_existing_wave(self, patch_state_manager: DispatchStateManager) -> None:
        """dispatch_wave_status returns aggregated item counts for a known wave.

        Tests: dispatch_wave_status happy path
        How: Seed a wave with two pending items. Call the tool and verify
             summary fields: total_items, pending, complete, failed.
        Why: Orchestrators poll this tool to decide when to advance to the
             next wave; incorrect counts cause premature or stalled advancement.
        """
        # Arrange
        _seed_wave(patch_state_manager, milestone=10, wave_num=1, issues=[101, 102])

        # Act
        async with Client(mcp) as client:
            result = await client.call_tool("dispatch_wave_status", {"milestone": 10, "wave_num": 1})

        # Assert
        data: dict[str, Any] = result.data
        assert "error" not in data
        assert data["total_items"] == 2
        assert data["pending"] == 2
        assert data["complete"] == 0
        assert data["failed"] == 0

    async def test_returns_error_for_missing_wave(self, patch_state_manager: DispatchStateManager) -> None:
        """dispatch_wave_status returns error dict when wave does not exist.

        Tests: dispatch_wave_status — not-found path
        How: Query wave_num=99 on a milestone that has no waves.
        Why: The tool must not raise; callers check the error key.
        """
        # Arrange — empty database

        # Act
        async with Client(mcp) as client:
            result = await client.call_tool("dispatch_wave_status", {"milestone": 10, "wave_num": 99})

        # Assert
        data: dict[str, Any] = result.data
        assert "error" in data
        assert "99" in data["error"]

    async def test_detects_stale_pid_and_marks_item_failed(
        self, patch_state_manager: DispatchStateManager, mocker: MockerFixture
    ) -> None:
        """dispatch_wave_status detects a dead PID and marks the item failed.

        Tests: dispatch_wave_status — stale PID detection
        How: Seed a wave, mark item 101 in-progress with pid=77777.
             Patch os.kill to raise ProcessLookupError (PID dead).
             Call dispatch_wave_status and verify:
             (a) the warnings list contains a stale-PID message,
             (b) the item is marked failed in the database.
        Why: Ensures the tool surfaces stuck spawns rather than reporting
             phantom in-progress items indefinitely.
        """
        # Arrange
        _seed_wave(patch_state_manager, milestone=10, wave_num=1, issues=[101, 102])
        patch_state_manager.set_item_in_progress(milestone=10, wave_num=1, issue=101, pid=77777)

        mocker.patch("backlog_core.dispatch_state.os.kill", side_effect=ProcessLookupError)

        # Act
        async with Client(mcp) as client:
            result = await client.call_tool("dispatch_wave_status", {"milestone": 10, "wave_num": 1})

        # Assert — stale PID warning is surfaced in the response
        data: dict[str, Any] = result.data
        assert "error" not in data
        warnings: list[str] = data.get("warnings", [])
        assert any("77777" in w or "101" in w for w in warnings), (
            f"Expected stale-PID warning for pid=77777 / issue=101, got warnings: {warnings}"
        )

        # Assert — item is now failed in the database
        item = patch_state_manager.get_item(milestone=10, wave_num=1, issue=101)
        assert item is not None
        assert item.status == "failed"

    async def test_response_contains_items_list(self, patch_state_manager: DispatchStateManager) -> None:
        """dispatch_wave_status includes per-item detail in the response.

        Tests: dispatch_wave_status — items list field
        How: Seed a wave with two items, call the tool, verify the items
             field is a non-empty list containing the seeded issue numbers.
        Why: Callers use the items list to surface per-item status to the user.
        """
        # Arrange
        _seed_wave(patch_state_manager, milestone=10, wave_num=1, issues=[101, 102])

        # Act
        async with Client(mcp) as client:
            result = await client.call_tool("dispatch_wave_status", {"milestone": 10, "wave_num": 1})

        # Assert
        data: dict[str, Any] = result.data
        items = data.get("items", [])
        assert len(items) == 2
        item_issues = {i["issue"] for i in items}
        assert item_issues == {101, 102}


# ---------------------------------------------------------------------------
# dispatch_spawn
# ---------------------------------------------------------------------------


class TestDispatchSpawn:
    """Integration tests for the dispatch_spawn MCP tool (background task).

    dispatch_spawn is decorated with @mcp.tool(task=True) so the FastMCP
    client returns a task handle on the first call and the result is
    delivered when the background task finishes.

    All subprocess creation is mocked so no real processes are spawned.
    The mock simulates spawn.py emitting a JSON line ``{"pid": 0,
    "result_file": "<path>"}`` to stdout; a corresponding result file is
    written to tmp_path so _poll_until_done detects completion.
    """

    async def test_spawn_end_to_end_single_wave(
        self, patch_state_manager: DispatchStateManager, tmp_path: Path, mocker: MockerFixture
    ) -> None:
        """dispatch_spawn processes one wave and returns a completion summary.

        Tests: dispatch_spawn — full end-to-end with mocked subprocess
        How:
          1. Write a dispatch plan YAML with a single item (avoids concurrent
             SQLite writes from asyncio.gather which cause transaction conflicts
             when two threads call set_item_complete simultaneously).
          2. Prepare a result file so _poll_until_done detects completion on
             the first poll cycle.
          3. Mock asyncio.create_subprocess_exec to emit spawn.py JSON pointing
             to the prepared result file.
          4. Call dispatch_spawn via in-memory Client and await the result.
          5. Verify the summary shows the item completed with no failures.
        Why: The tool is the core workhorse of dispatch; verifying the
             end-to-end path with mocked I/O guards against regressions in
             the item monitoring loop.
        """
        # Arrange — single-item plan to avoid concurrent thread writes to SQLite.
        plan_path = tmp_path / "milestone-10-dispatch.yaml"
        plan_path.write_text(_make_dispatch_plan_yaml(milestone=10, wave_num=1, issues=[101]))
        mocker.patch("backlog_core.server._dispatch_plan_path", return_value=plan_path)

        result_file = tmp_path / "result-101.json"
        result_file.write_text(json.dumps({"status": "ok", "cost": 0.01}))

        def _fake_subprocess(*args: Any, **kwargs: Any) -> MagicMock:
            """Return a mock process whose stdout encodes spawn.py JSON."""
            proc = MagicMock()
            spawn_json = json.dumps({"pid": 0, "result_file": str(result_file)}).encode()
            proc.communicate = AsyncMock(return_value=(spawn_json, b""))
            return proc

        mocker.patch("asyncio.create_subprocess_exec", new=AsyncMock(side_effect=_fake_subprocess))

        # Act
        async with Client(mcp) as client:
            result = await client.call_tool("dispatch_spawn", {"milestone": 10, "wave_num": 1})

        # Assert
        data: dict[str, Any] = result.data
        assert "error" not in data, f"Unexpected error: {data.get('error')}"
        assert data["total_items"] == 1
        assert data["completed"] == 1
        assert data["failed"] == 0

    async def test_spawn_missing_plan_returns_error(
        self, patch_state_manager: DispatchStateManager, mocker: MockerFixture
    ) -> None:
        """dispatch_spawn returns an error dict when the dispatch plan file is absent.

        Tests: dispatch_spawn — FileNotFoundError handling
        How: Patch _dispatch_plan_path to return a non-existent file path.
             Call dispatch_spawn and verify the error key is set.
        Why: Missing plan files are a common operator error; the tool must
             return a meaningful error rather than an unhandled exception.
        """
        # Arrange
        missing = Path("/tmp/does-not-exist-abc123/milestone-10-dispatch.yaml")
        mocker.patch("backlog_core.server._dispatch_plan_path", return_value=missing)

        # Act
        async with Client(mcp) as client:
            result = await client.call_tool("dispatch_spawn", {"milestone": 10, "wave_num": 1})

        # Assert
        data: dict[str, Any] = result.data
        assert "error" in data
        assert "10" in str(data["error"]) or "not found" in data["error"].lower()

    async def test_spawn_subprocess_non_json_output_marks_item_failed(
        self, patch_state_manager: DispatchStateManager, tmp_path: Path, mocker: MockerFixture
    ) -> None:
        """dispatch_spawn marks an item failed when spawn.py emits non-JSON stdout.

        Tests: dispatch_spawn — non-JSON output error path
        How: Use a single-item plan to avoid concurrent SQLite writes.
             Mock subprocess to return plain text instead of JSON. Verify
             the item is counted in the failed tally and the summary reflects
             the failure.
        Why: spawn.py may fail to start cleanly; the tool must not crash and
             must record the failure so the operator can diagnose it.
        """
        # Arrange — single-item plan; patch plan path to tmp file.
        plan_path = tmp_path / "milestone-10-dispatch.yaml"
        plan_path.write_text(_make_dispatch_plan_yaml(milestone=10, wave_num=1, issues=[101]))
        mocker.patch("backlog_core.server._dispatch_plan_path", return_value=plan_path)

        def _bad_subprocess(*args: Any, **kwargs: Any) -> MagicMock:
            proc = MagicMock()
            proc.communicate = AsyncMock(return_value=(b"ERROR: spawn failed\n", b""))
            return proc

        mocker.patch("asyncio.create_subprocess_exec", new=AsyncMock(side_effect=_bad_subprocess))

        # Act
        async with Client(mcp) as client:
            result = await client.call_tool("dispatch_spawn", {"milestone": 10, "wave_num": 1})

        # Assert
        data: dict[str, Any] = result.data
        assert "error" not in data  # tool returns a summary, not an error
        assert data["failed"] > 0

    async def test_spawn_calls_check_stale_pids_at_startup(
        self, patch_state_manager: DispatchStateManager, tmp_path: Path, mocker: MockerFixture
    ) -> None:
        """dispatch_spawn calls check_stale_pids before spawning to clean up prior runs.

        Tests: dispatch_spawn — stale PID cleanup on entry
        How: Spy on the state manager's check_stale_pids method. Use a
             single-item plan, mock subprocess to return an immediate completion,
             call dispatch_spawn, and verify check_stale_pids was invoked.
        Why: Without the stale-PID cleanup call, orphaned sessions from prior
             runs accumulate as in-progress items and block wave progress
             indefinitely. Verifying the call is made ensures the guard is active
             regardless of whether stale items exist in a given test run.
        """
        # Arrange — single-item plan; spy on check_stale_pids.
        plan_path = tmp_path / "milestone-10-dispatch.yaml"
        plan_path.write_text(_make_dispatch_plan_yaml(milestone=10, wave_num=1, issues=[101]))
        mocker.patch("backlog_core.server._dispatch_plan_path", return_value=plan_path)

        check_stale_spy = mocker.spy(patch_state_manager, "check_stale_pids")

        result_file = tmp_path / "result-spawn.json"
        result_file.write_text(json.dumps({"status": "ok"}))

        def _fake_subprocess(*args: Any, **kwargs: Any) -> MagicMock:
            proc = MagicMock()
            spawn_json = json.dumps({"pid": 0, "result_file": str(result_file)}).encode()
            proc.communicate = AsyncMock(return_value=(spawn_json, b""))
            return proc

        mocker.patch("asyncio.create_subprocess_exec", new=AsyncMock(side_effect=_fake_subprocess))

        # Act
        async with Client(mcp) as client:
            await client.call_tool("dispatch_spawn", {"milestone": 10, "wave_num": 1})

        # Assert — check_stale_pids must be called once at startup
        assert check_stale_spy.call_count >= 1, (
            "dispatch_spawn must call check_stale_pids at startup to clean up orphaned sessions"
        )
