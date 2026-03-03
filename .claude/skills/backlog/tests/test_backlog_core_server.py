"""Tests for the FastMCP 3.x server layer in backlog_core/server.py.

All 10 MCP tools are tested through the in-memory FastMCP transport using
Client(mcp). Operations are mocked at the boundary via
``unittest.mock.patch("backlog_core.operations.<function_name>")``.

Each tool is tested for:
- Successful operation (verifies parameter forwarding and dict merge)
- BacklogError handling (verifies error key is present in response)

No @pytest.mark.asyncio decorators — asyncio_mode = "auto" is set globally.
All imports are at module level.
"""

from __future__ import annotations

import json
from unittest.mock import patch

import pytest
from backlog_core.models import BacklogError, Output
from backlog_core.server import mcp
from fastmcp.client import Client

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_output_dict(
    messages: list[str] | None = None, warnings: list[str] | None = None, errors: list[str] | None = None
) -> dict[str, list[str]]:
    """Build the Output.to_dict() structure returned by all operations."""
    return {"messages": messages or [], "warnings": warnings or [], "errors": errors or []}


async def _call(tool_name: str, params: dict | None = None) -> dict:
    """Call a tool through the in-memory FastMCP transport and parse the result.

    Args:
        tool_name: The registered MCP tool name.
        params: Optional dict of parameters to pass to the tool.

    Returns:
        Parsed JSON response dict from the tool.
    """
    async with Client(mcp) as client:
        result = await client.call_tool(tool_name, params or {})
    return json.loads(result.content[0].text)


# ---------------------------------------------------------------------------
# backlog_add
# ---------------------------------------------------------------------------


async def test_backlog_add_success_returns_merged_result():
    """backlog_add passes params to operations.add_item and merges output."""
    op_result = {"file_path": "/tmp/p1-my-item.md", "title": "My Item", "priority": "P1"}
    with patch("backlog_core.operations.add_item", return_value=op_result) as mock_add:
        response = await _call("backlog_add", {"title": "My Item", "priority": "P1", "description": "A test item"})

    mock_add.assert_called_once()
    call_kwargs = mock_add.call_args.kwargs
    assert call_kwargs["title"] == "My Item"
    assert call_kwargs["priority"] == "P1"
    assert call_kwargs["description"] == "A test item"
    assert response["file_path"] == "/tmp/p1-my-item.md"
    assert response["title"] == "My Item"
    assert "messages" in response
    assert "warnings" in response
    assert "errors" in response


async def test_backlog_add_passes_optional_params():
    """backlog_add forwards source, type_, create_issue, and force to operations."""
    op_result = {"file_path": "/tmp/p0-bug.md", "title": "Bug", "priority": "P0"}
    with patch("backlog_core.operations.add_item", return_value=op_result) as mock_add:
        await _call(
            "backlog_add",
            {
                "title": "Bug",
                "priority": "P0",
                "description": "A real bug",
                "source": "CI pipeline",
                "type": "Bug",
                "create_issue": False,
                "force": True,
            },
        )

    call_kwargs = mock_add.call_args.kwargs
    assert call_kwargs["source"] == "CI pipeline"
    assert call_kwargs["type_"] == "Bug"
    assert call_kwargs["create_issue"] is False
    assert call_kwargs["force"] is True


async def test_backlog_add_backlog_error_returns_error_key():
    """backlog_add catches BacklogError and includes error key in response."""
    with patch("backlog_core.operations.add_item", side_effect=BacklogError("duplicate found")):
        response = await _call("backlog_add", {"title": "Dupe", "priority": "P1", "description": "Already exists"})

    assert response["error"] == "duplicate found"
    assert "messages" in response


async def test_backlog_add_output_messages_included():
    """backlog_add includes output messages from the Output collector."""
    out = Output()
    out.info("created file")
    out.warn("no github token")

    def _add_with_messages(**kwargs):
        kwargs["output"].info("created file")
        kwargs["output"].warn("no github token")
        return {"file_path": "/tmp/p1-item.md"}

    with patch("backlog_core.operations.add_item", side_effect=_add_with_messages):
        response = await _call("backlog_add", {"title": "Item", "priority": "P1", "description": "Test"})

    assert "created file" in response["messages"]
    assert "no github token" in response["warnings"]


# ---------------------------------------------------------------------------
# backlog_list
# ---------------------------------------------------------------------------


async def test_backlog_list_success_returns_items():
    """backlog_list passes params to operations.list_items and merges output."""
    op_result = {"items": [{"title": "Item A", "priority": "P1", "issue": "", "plan": ""}]}
    with patch("backlog_core.operations.list_items", return_value=op_result) as mock_list:
        response = await _call("backlog_list", {})

    mock_list.assert_called_once()
    call_kwargs = mock_list.call_args.kwargs
    assert call_kwargs["with_status"] is False
    assert call_kwargs["from_github"] is False
    assert call_kwargs["label"] is None
    assert response["items"][0]["title"] == "Item A"


async def test_backlog_list_passes_filter_params():
    """backlog_list forwards with_status, from_github, and label flags."""
    op_result = {"items": []}
    with patch("backlog_core.operations.list_items", return_value=op_result) as mock_list:
        await _call("backlog_list", {"with_status": True, "from_github": True, "label": "priority:p0"})

    call_kwargs = mock_list.call_args.kwargs
    assert call_kwargs["with_status"] is True
    assert call_kwargs["from_github"] is True
    assert call_kwargs["label"] == "priority:p0"


async def test_backlog_list_passes_new_filter_params():
    """backlog_list forwards section, status, and title to list_items."""
    op_result = {"items": []}
    with patch("backlog_core.operations.list_items", return_value=op_result) as mock_list:
        await _call("backlog_list", {"section": "P1", "status": "needs-grooming", "title": "auth"})
    call_kwargs = mock_list.call_args.kwargs
    assert call_kwargs["section"] == "P1"
    assert call_kwargs["status"] == "needs-grooming"
    assert call_kwargs["title"] == "auth"


async def test_backlog_list_backlog_error_returns_error_key():
    """backlog_list catches BacklogError and includes error key in response."""
    with patch("backlog_core.operations.list_items", side_effect=BacklogError("backlog dir missing")):
        response = await _call("backlog_list", {})

    assert response["error"] == "backlog dir missing"


# ---------------------------------------------------------------------------
# backlog_view
# ---------------------------------------------------------------------------


async def test_backlog_view_success_returns_item_detail():
    """backlog_view calls operations.view_item and merges result with output."""
    op_result = {
        "title": "My Feature",
        "priority": "P1",
        "description": "details",
        "source": "issue",
        "added": "2026-01-01",
        "plan": "",
        "issue": "#42",
        "file_path": "/tmp/p1-my-feature.md",
        "groomed": False,
        "status": "",
        "number": 42,
        "state": "open",
        "body": "## Details\nsome content",
        "labels": ["priority:p1"],
        "milestone": "",
    }
    with patch("backlog_core.operations.view_item", return_value=op_result) as mock_view:
        response = await _call("backlog_view", {"selector": "#42"})

    mock_view.assert_called_once()
    call_kwargs = mock_view.call_args.kwargs
    assert call_kwargs["selector"] == "#42"
    assert call_kwargs["offset"] == 0
    assert call_kwargs["limit"] == 0
    assert response["title"] == "My Feature"
    assert response["issue"] == "#42"


async def test_backlog_view_passes_pagination_params():
    """backlog_view forwards offset and limit to operations."""
    op_result = {"title": "Item", "body": "line1\nline2\nline3"}
    with patch("backlog_core.operations.view_item", return_value=op_result) as mock_view:
        await _call("backlog_view", {"selector": "Item", "offset": 5, "limit": 20})

    call_kwargs = mock_view.call_args.kwargs
    assert call_kwargs["offset"] == 5
    assert call_kwargs["limit"] == 20


async def test_backlog_view_backlog_error_returns_error_key():
    """backlog_view catches BacklogError when item is not found."""
    with patch("backlog_core.operations.view_item", side_effect=BacklogError("No item found for: #999")):
        response = await _call("backlog_view", {"selector": "#999"})

    assert "No item found for: #999" in response["error"]


# ---------------------------------------------------------------------------
# backlog_sync
# ---------------------------------------------------------------------------


async def test_backlog_sync_success_returns_counts():
    """backlog_sync calls operations.sync_items and returns created/pushed counts."""
    op_result = {"created": 3, "pushed": 2}
    with patch("backlog_core.operations.sync_items", return_value=op_result) as mock_sync:
        response = await _call("backlog_sync", {})

    mock_sync.assert_called_once()
    call_kwargs = mock_sync.call_args.kwargs
    assert call_kwargs["dry_run"] is False
    assert response["created"] == 3
    assert response["pushed"] == 2


async def test_backlog_sync_dry_run_forwarded():
    """backlog_sync passes dry_run=True to operations.sync_items."""
    op_result = {"created": 0, "pushed": 0}
    with patch("backlog_core.operations.sync_items", return_value=op_result) as mock_sync:
        await _call("backlog_sync", {"dry_run": True})

    assert mock_sync.call_args.kwargs["dry_run"] is True


async def test_backlog_sync_backlog_error_returns_error_key():
    """backlog_sync catches BacklogError and includes error key."""
    with patch("backlog_core.operations.sync_items", side_effect=BacklogError("GitHub unavailable")):
        response = await _call("backlog_sync", {})

    assert response["error"] == "GitHub unavailable"


# ---------------------------------------------------------------------------
# backlog_close
# ---------------------------------------------------------------------------


async def test_backlog_close_success_returns_closed_item():
    """backlog_close calls operations.close_item and merges result."""
    op_result = {"title": "Done Feature", "issue": "#7"}
    with patch("backlog_core.operations.close_item", return_value=op_result) as mock_close:
        response = await _call(
            "backlog_close", {"selector": "Done Feature", "plan": "plan/tasks-done.md", "checklist_pass": True}
        )

    mock_close.assert_called_once()
    call_kwargs = mock_close.call_args.kwargs
    assert call_kwargs["selector"] == "Done Feature"
    assert call_kwargs["plan"] == "plan/tasks-done.md"
    assert call_kwargs["checklist_pass"] is True
    assert call_kwargs["cleanup"] is False
    assert call_kwargs["force"] is False
    assert response["title"] == "Done Feature"


async def test_backlog_close_passes_cleanup_and_force():
    """backlog_close forwards cleanup and force flags."""
    op_result = {"title": "Item", "issue": "#5"}
    with patch("backlog_core.operations.close_item", return_value=op_result) as mock_close:
        await _call(
            "backlog_close",
            {"selector": "Item", "plan": "complete", "checklist_pass": True, "cleanup": True, "force": True},
        )

    call_kwargs = mock_close.call_args.kwargs
    assert call_kwargs["cleanup"] is True
    assert call_kwargs["force"] is True


async def test_backlog_close_backlog_error_returns_error_key():
    """backlog_close catches BacklogError (e.g. item not found)."""
    with patch("backlog_core.operations.close_item", side_effect=BacklogError("checklist not passed")):
        response = await _call("backlog_close", {"selector": "Item", "plan": "summary", "checklist_pass": False})

    assert response["error"] == "checklist not passed"


# ---------------------------------------------------------------------------
# backlog_resolve
# ---------------------------------------------------------------------------


async def test_backlog_resolve_success_returns_resolved_item():
    """backlog_resolve calls operations.resolve_item and merges result."""
    op_result = {"title": "Old Feature", "reason": "duplicate of #10", "issue": "#3"}
    with patch("backlog_core.operations.resolve_item", return_value=op_result) as mock_resolve:
        response = await _call("backlog_resolve", {"selector": "Old Feature", "reason": "duplicate of #10"})

    mock_resolve.assert_called_once()
    call_kwargs = mock_resolve.call_args.kwargs
    assert call_kwargs["selector"] == "Old Feature"
    assert call_kwargs["reason"] == "duplicate of #10"
    assert call_kwargs["cleanup"] is False
    assert call_kwargs["force"] is False
    assert response["title"] == "Old Feature"
    assert response["reason"] == "duplicate of #10"


async def test_backlog_resolve_passes_cleanup_and_force():
    """backlog_resolve forwards cleanup and force to operations."""
    op_result = {"title": "Item", "reason": "out of scope", "issue": ""}
    with patch("backlog_core.operations.resolve_item", return_value=op_result) as mock_resolve:
        await _call("backlog_resolve", {"selector": "Item", "reason": "out of scope", "cleanup": True, "force": True})

    call_kwargs = mock_resolve.call_args.kwargs
    assert call_kwargs["cleanup"] is True
    assert call_kwargs["force"] is True


async def test_backlog_resolve_backlog_error_returns_error_key():
    """backlog_resolve catches BacklogError when resolution fails."""
    with patch("backlog_core.operations.resolve_item", side_effect=BacklogError("open PRs exist")):
        response = await _call("backlog_resolve", {"selector": "Item", "reason": "no longer needed"})

    assert response["error"] == "open PRs exist"


# ---------------------------------------------------------------------------
# backlog_update
# ---------------------------------------------------------------------------


async def test_backlog_update_success_with_plan():
    """backlog_update calls operations.update_item and merges result."""
    op_result = {"title": "Feature", "changes": ["plan attached"]}
    with patch("backlog_core.operations.update_item", return_value=op_result) as mock_update:
        response = await _call("backlog_update", {"selector": "Feature", "plan": "plan/tasks-feature.md"})

    mock_update.assert_called_once()
    call_kwargs = mock_update.call_args.kwargs
    assert call_kwargs["selector"] == "Feature"
    assert call_kwargs["plan"] == "plan/tasks-feature.md"
    assert call_kwargs["status"] is None
    assert call_kwargs["create_issue"] is False
    assert call_kwargs["groomed_content"] is None
    assert call_kwargs["section"] is None
    assert call_kwargs["content"] is None
    assert response["title"] == "Feature"


async def test_backlog_update_passes_status_and_create_issue():
    """backlog_update forwards status and create_issue to operations."""
    op_result = {"title": "Item", "changes": ["status updated"]}
    with patch("backlog_core.operations.update_item", return_value=op_result) as mock_update:
        await _call("backlog_update", {"selector": "Item", "status": "in-progress", "create_issue": True})

    call_kwargs = mock_update.call_args.kwargs
    assert call_kwargs["status"] == "in-progress"
    assert call_kwargs["create_issue"] is True


async def test_backlog_update_passes_groomed_content():
    """backlog_update forwards groomed_content for full replacement."""
    op_result = {"title": "Item", "changes": ["groomed"]}
    with patch("backlog_core.operations.update_item", return_value=op_result) as mock_update:
        await _call("backlog_update", {"selector": "Item", "groomed_content": "## Section\nsome content"})

    call_kwargs = mock_update.call_args.kwargs
    assert call_kwargs["groomed_content"] == "## Section\nsome content"


async def test_backlog_update_passes_section_and_content():
    """backlog_update forwards section and content for incremental update."""
    op_result = {"title": "Item", "changes": ["section updated"]}
    with patch("backlog_core.operations.update_item", return_value=op_result) as mock_update:
        await _call("backlog_update", {"selector": "Item", "section": "Acceptance Criteria", "content": "- [ ] Done"})

    call_kwargs = mock_update.call_args.kwargs
    assert call_kwargs["section"] == "Acceptance Criteria"
    assert call_kwargs["content"] == "- [ ] Done"


async def test_backlog_update_passes_title():
    """backlog_update forwards title to operations.update_item."""
    op_result = {"title": "Old", "renamed_to": "New Title"}
    with patch("backlog_core.operations.update_item", return_value=op_result) as mock_update:
        await _call("backlog_update", {"selector": "Old", "title": "New Title"})

    call_kwargs = mock_update.call_args.kwargs
    assert call_kwargs["title"] == "New Title"


async def test_backlog_update_passes_description():
    """backlog_update forwards description to operations.update_item."""
    op_result = {"title": "Item", "description_updated": True}
    with patch("backlog_core.operations.update_item", return_value=op_result) as mock_update:
        await _call("backlog_update", {"selector": "Item", "description": "Updated description."})

    call_kwargs = mock_update.call_args.kwargs
    assert call_kwargs["description"] == "Updated description."


async def test_backlog_update_backlog_error_returns_error_key():
    """backlog_update catches BacklogError."""
    with patch("backlog_core.operations.update_item", side_effect=BacklogError("item not found")):
        response = await _call("backlog_update", {"selector": "Missing"})

    assert response["error"] == "item not found"


# ---------------------------------------------------------------------------
# backlog_groom
# ---------------------------------------------------------------------------


async def test_backlog_groom_success_with_full_content():
    """backlog_groom calls operations.groom_item with groomed_content."""
    op_result = {"title": "Feature", "synced": True}
    with patch("backlog_core.operations.groom_item", return_value=op_result) as mock_groom:
        response = await _call(
            "backlog_groom", {"selector": "Feature", "groomed_content": "## Acceptance Criteria\n- [ ] Pass tests"}
        )

    mock_groom.assert_called_once()
    call_kwargs = mock_groom.call_args.kwargs
    assert call_kwargs["selector"] == "Feature"
    assert call_kwargs["groomed_content"] == "## Acceptance Criteria\n- [ ] Pass tests"
    assert call_kwargs["section"] is None
    assert call_kwargs["content"] is None
    assert response["title"] == "Feature"
    assert response["synced"] is True


async def test_backlog_groom_passes_section_and_content():
    """backlog_groom forwards section and content for incremental update."""
    op_result = {"title": "Item", "synced": False}
    with patch("backlog_core.operations.groom_item", return_value=op_result) as mock_groom:
        await _call("backlog_groom", {"selector": "Item", "section": "Background", "content": "Some background info"})

    call_kwargs = mock_groom.call_args.kwargs
    assert call_kwargs["section"] == "Background"
    assert call_kwargs["content"] == "Some background info"
    assert call_kwargs["groomed_content"] is None


async def test_backlog_groom_backlog_error_returns_error_key():
    """backlog_groom catches BacklogError."""
    with patch("backlog_core.operations.groom_item", side_effect=BacklogError("item not found")):
        response = await _call("backlog_groom", {"selector": "#999"})

    assert response["error"] == "item not found"


# ---------------------------------------------------------------------------
# backlog_normalize
# ---------------------------------------------------------------------------


async def test_backlog_normalize_success_returns_count():
    """backlog_normalize calls operations.normalize_items and returns count."""
    op_result = {"normalized": 5}
    with patch("backlog_core.operations.normalize_items", return_value=op_result) as mock_normalize:
        response = await _call("backlog_normalize", {})

    mock_normalize.assert_called_once()
    call_kwargs = mock_normalize.call_args.kwargs
    assert call_kwargs["dry_run"] is False
    assert response["normalized"] == 5


async def test_backlog_normalize_dry_run_forwarded():
    """backlog_normalize passes dry_run to operations."""
    op_result = {"normalized": 0}
    with patch("backlog_core.operations.normalize_items", return_value=op_result) as mock_normalize:
        await _call("backlog_normalize", {"dry_run": True})

    assert mock_normalize.call_args.kwargs["dry_run"] is True


async def test_backlog_normalize_backlog_error_returns_error_key():
    """backlog_normalize catches BacklogError."""
    with patch("backlog_core.operations.normalize_items", side_effect=BacklogError("malformed files")):
        response = await _call("backlog_normalize", {})

    assert response["error"] == "malformed files"


# ---------------------------------------------------------------------------
# backlog_pull
# ---------------------------------------------------------------------------


async def test_backlog_pull_success_returns_count():
    """backlog_pull calls operations.pull_items and returns pulled count."""
    op_result = {"pulled": 4}
    with patch("backlog_core.operations.pull_items", return_value=op_result) as mock_pull:
        response = await _call("backlog_pull", {})

    mock_pull.assert_called_once()
    call_kwargs = mock_pull.call_args.kwargs
    assert call_kwargs["dry_run"] is False
    assert call_kwargs["force"] is False
    assert response["pulled"] == 4


async def test_backlog_pull_passes_dry_run_and_force():
    """backlog_pull forwards dry_run and force to operations."""
    op_result = {"pulled": 0}
    with patch("backlog_core.operations.pull_items", return_value=op_result) as mock_pull:
        await _call("backlog_pull", {"dry_run": True, "force": True})

    call_kwargs = mock_pull.call_args.kwargs
    assert call_kwargs["dry_run"] is True
    assert call_kwargs["force"] is True


async def test_backlog_pull_backlog_error_returns_error_key():
    """backlog_pull catches BacklogError."""
    with patch("backlog_core.operations.pull_items", side_effect=BacklogError("no GitHub token")):
        response = await _call("backlog_pull", {})

    assert response["error"] == "no GitHub token"


# ---------------------------------------------------------------------------
# Cross-cutting: output dict structure is always present
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("tool_name", "params", "mock_target", "mock_return"),
    [
        (
            "backlog_add",
            {"title": "T", "priority": "P1", "description": "D"},
            "backlog_core.operations.add_item",
            {"file_path": "f"},
        ),
        ("backlog_list", {}, "backlog_core.operations.list_items", {"items": []}),
        ("backlog_view", {"selector": "#1"}, "backlog_core.operations.view_item", {"title": "T"}),
        ("backlog_sync", {}, "backlog_core.operations.sync_items", {"created": 0}),
        ("backlog_normalize", {}, "backlog_core.operations.normalize_items", {"normalized": 0}),
        ("backlog_pull", {}, "backlog_core.operations.pull_items", {"pulled": 0}),
    ],
)
async def test_output_fields_always_present_on_success(tool_name, params, mock_target, mock_return):
    """Every tool response includes messages, warnings, and errors keys on success."""
    with patch(mock_target, return_value=mock_return):
        response = await _call(tool_name, params)

    assert "messages" in response, f"{tool_name}: missing 'messages' key"
    assert "warnings" in response, f"{tool_name}: missing 'warnings' key"
    assert "errors" in response, f"{tool_name}: missing 'errors' key"
    assert isinstance(response["messages"], list)
    assert isinstance(response["warnings"], list)
    assert isinstance(response["errors"], list)


@pytest.mark.parametrize(
    ("tool_name", "params", "mock_target"),
    [
        ("backlog_add", {"title": "T", "priority": "P1", "description": "D"}, "backlog_core.operations.add_item"),
        ("backlog_list", {}, "backlog_core.operations.list_items"),
        ("backlog_view", {"selector": "#1"}, "backlog_core.operations.view_item"),
        ("backlog_sync", {}, "backlog_core.operations.sync_items"),
        ("backlog_close", {"selector": "X", "plan": "p"}, "backlog_core.operations.close_item"),
        ("backlog_resolve", {"selector": "X", "reason": "r"}, "backlog_core.operations.resolve_item"),
        ("backlog_update", {"selector": "X"}, "backlog_core.operations.update_item"),
        ("backlog_groom", {"selector": "X"}, "backlog_core.operations.groom_item"),
        ("backlog_normalize", {}, "backlog_core.operations.normalize_items"),
        ("backlog_pull", {}, "backlog_core.operations.pull_items"),
    ],
)
async def test_output_fields_always_present_on_error(tool_name, params, mock_target):
    """Every tool response includes error key and output fields on BacklogError."""
    with patch(mock_target, side_effect=BacklogError("test error")):
        response = await _call(tool_name, params)

    assert "error" in response, f"{tool_name}: missing 'error' key on BacklogError"
    assert response["error"] == "test error"
    assert "messages" in response, f"{tool_name}: missing 'messages' key on BacklogError"
    assert "warnings" in response, f"{tool_name}: missing 'warnings' key on BacklogError"
    assert "errors" in response, f"{tool_name}: missing 'errors' key on BacklogError"


# ---------------------------------------------------------------------------
# Tool registration verification
# ---------------------------------------------------------------------------


async def test_all_ten_tools_are_registered():
    """Verify all 10 expected tool names are registered in the MCP server."""
    expected = {
        "backlog_add",
        "backlog_list",
        "backlog_view",
        "backlog_sync",
        "backlog_close",
        "backlog_resolve",
        "backlog_update",
        "backlog_groom",
        "backlog_normalize",
        "backlog_pull",
    }
    async with Client(mcp) as client:
        tools = await client.list_tools()

    registered = {t.name for t in tools}
    assert expected.issubset(registered), f"Missing tools: {expected - registered}"


def test_mcp_server_name_is_backlog_mcp():
    """The FastMCP instance is named 'backlog'."""
    assert mcp.name == "backlog"


# ---------------------------------------------------------------------------
# Output collector is passed (not None) to operations
# ---------------------------------------------------------------------------


async def test_backlog_add_passes_output_instance_to_operations():
    """backlog_add provides an Output instance as the 'output' keyword arg."""
    captured: list[Output] = []

    def _capture(**kwargs):
        captured.append(kwargs["output"])
        return {"file_path": "/tmp/p1-x.md"}

    with patch("backlog_core.operations.add_item", side_effect=_capture):
        await _call("backlog_add", {"title": "X", "priority": "P1", "description": "D"})

    assert len(captured) == 1
    assert isinstance(captured[0], Output)


async def test_backlog_list_passes_output_instance_to_operations():
    """backlog_list provides an Output instance as the 'output' keyword arg."""
    captured: list[Output] = []

    def _capture(**kwargs):
        captured.append(kwargs["output"])
        return {"items": []}

    with patch("backlog_core.operations.list_items", side_effect=_capture):
        await _call("backlog_list", {})

    assert len(captured) == 1
    assert isinstance(captured[0], Output)


# ---------------------------------------------------------------------------
# Tool returns non-error result — error key must NOT be present
# ---------------------------------------------------------------------------


async def test_backlog_add_no_error_key_on_success():
    """Successful backlog_add response must not contain an 'error' key."""
    with patch("backlog_core.operations.add_item", return_value={"file_path": "/tmp/p1-ok.md"}):
        response = await _call("backlog_add", {"title": "OK", "priority": "P1", "description": "Fine"})

    assert "error" not in response


async def test_backlog_sync_no_error_key_on_success():
    """Successful backlog_sync response must not contain an 'error' key."""
    with patch("backlog_core.operations.sync_items", return_value={"created": 1, "pushed": 0}):
        response = await _call("backlog_sync", {})

    assert "error" not in response


# ---------------------------------------------------------------------------
# F11 — Tool annotations
# ---------------------------------------------------------------------------


async def test_backlog_list_is_annotated_read_only():
    """backlog_list must carry readOnlyHint=True annotation."""
    async with Client(mcp) as client:
        tools = await client.list_tools()
    tool = next(t for t in tools if t.name == "backlog_list")
    assert tool.annotations is not None
    assert tool.annotations.readOnlyHint is True


async def test_backlog_view_is_annotated_read_only():
    """backlog_view must carry readOnlyHint=True annotation."""
    async with Client(mcp) as client:
        tools = await client.list_tools()
    tool = next(t for t in tools if t.name == "backlog_view")
    assert tool.annotations is not None
    assert tool.annotations.readOnlyHint is True


async def test_backlog_close_is_annotated_destructive():
    """backlog_close must carry destructiveHint=True annotation."""
    async with Client(mcp) as client:
        tools = await client.list_tools()
    tool = next(t for t in tools if t.name == "backlog_close")
    assert tool.annotations is not None
    assert tool.annotations.destructiveHint is True


async def test_backlog_resolve_is_annotated_destructive():
    """backlog_resolve must carry destructiveHint=True annotation."""
    async with Client(mcp) as client:
        tools = await client.list_tools()
    tool = next(t for t in tools if t.name == "backlog_resolve")
    assert tool.annotations is not None
    assert tool.annotations.destructiveHint is True


# ---------------------------------------------------------------------------
# F12 — backlog_session_diff
# ---------------------------------------------------------------------------


async def test_backlog_session_diff_returns_items_shape():
    """backlog_session_diff calls operations.session_diff_items and merges output."""
    op_result = {"items": [{"title": "New Item", "section": "P1", "issue": "", "plan": ""}], "count": 1}
    with patch("backlog_core.operations.session_diff_items", return_value=op_result) as mock_diff:
        response = await _call("backlog_session_diff", {"since": "2026-03-01T00:00:00Z"})

    mock_diff.assert_called_once()
    assert mock_diff.call_args.kwargs["since"] == "2026-03-01T00:00:00Z"
    assert response["count"] == 1
    assert response["items"][0]["title"] == "New Item"
    assert "messages" in response


async def test_backlog_session_diff_backlog_error_returns_error_key():
    """backlog_session_diff catches BacklogError and includes error key."""
    with patch("backlog_core.operations.session_diff_items", side_effect=BacklogError("invalid timestamp")):
        response = await _call("backlog_session_diff", {"since": "not-a-date"})

    assert response["error"] == "invalid timestamp"


# ---------------------------------------------------------------------------
# F13 — backlog_dashboard
# ---------------------------------------------------------------------------


async def test_backlog_dashboard_returns_counts():
    """backlog_dashboard calls operations.dashboard_items and merges output."""
    op_result = {
        "counts_by_section": {"P0": 0, "P1": 3, "P2": 5, "Ideas": 2},
        "total_open": 10,
        "items_without_issue": [{"title": "Ungrouped", "section": "P2"}],
        "items_needing_grooming": [],
        "recently_modified": [],
    }
    with patch("backlog_core.operations.dashboard_items", return_value=op_result) as mock_dash:
        response = await _call("backlog_dashboard", {})

    mock_dash.assert_called_once()
    assert response["total_open"] == 10
    assert response["counts_by_section"]["P1"] == 3
    assert len(response["items_without_issue"]) == 1
    assert "messages" in response


async def test_backlog_dashboard_backlog_error_returns_error_key():
    """backlog_dashboard catches BacklogError and includes error key."""
    with patch("backlog_core.operations.dashboard_items", side_effect=BacklogError("backlog dir missing")):
        response = await _call("backlog_dashboard", {})

    assert response["error"] == "backlog dir missing"


# ---------------------------------------------------------------------------
# F14 — Named status tools
# ---------------------------------------------------------------------------


async def test_backlog_start_calls_start_item():
    """backlog_start delegates to operations.start_item with selector."""
    op_result = {"title": "My Feature", "status": "in-progress"}
    with patch("backlog_core.operations.start_item", return_value=op_result) as mock_start:
        response = await _call("backlog_start", {"selector": "My Feature"})

    mock_start.assert_called_once()
    assert mock_start.call_args.kwargs["selector"] == "My Feature"
    assert response["status"] == "in-progress"
    assert "messages" in response


async def test_backlog_start_backlog_error_returns_error_key():
    """backlog_start catches BacklogError."""
    with patch("backlog_core.operations.start_item", side_effect=BacklogError("item not found")):
        response = await _call("backlog_start", {"selector": "Ghost"})

    assert response["error"] == "item not found"


async def test_backlog_block_calls_block_item():
    """backlog_block delegates to operations.block_item with selector and reason."""
    op_result = {"title": "My Feature", "status": "blocked", "blocked_reason": "waiting on API"}
    with patch("backlog_core.operations.block_item", return_value=op_result) as mock_block:
        response = await _call("backlog_block", {"selector": "My Feature", "reason": "waiting on API"})

    mock_block.assert_called_once()
    assert mock_block.call_args.kwargs["selector"] == "My Feature"
    assert mock_block.call_args.kwargs["reason"] == "waiting on API"
    assert response["blocked_reason"] == "waiting on API"


async def test_backlog_block_backlog_error_returns_error_key():
    """backlog_block catches BacklogError."""
    with patch("backlog_core.operations.block_item", side_effect=BacklogError("item not found")):
        response = await _call("backlog_block", {"selector": "Ghost", "reason": "unknown"})

    assert response["error"] == "item not found"


async def test_backlog_unblock_calls_unblock_item():
    """backlog_unblock delegates to operations.unblock_item."""
    op_result = {"title": "My Feature", "status": "open"}
    with patch("backlog_core.operations.unblock_item", return_value=op_result) as mock_unblock:
        response = await _call("backlog_unblock", {"selector": "My Feature"})

    mock_unblock.assert_called_once()
    assert mock_unblock.call_args.kwargs["selector"] == "My Feature"
    assert response["status"] == "open"


async def test_backlog_unblock_backlog_error_returns_error_key():
    """backlog_unblock catches BacklogError."""
    with patch("backlog_core.operations.unblock_item", side_effect=BacklogError("item not found")):
        response = await _call("backlog_unblock", {"selector": "Ghost"})

    assert response["error"] == "item not found"


# ---------------------------------------------------------------------------
# F15 — backlog_batch_update
# ---------------------------------------------------------------------------


async def test_backlog_batch_update_returns_counts():
    """backlog_batch_update calls operations.batch_update_items and merges output."""
    op_result = {
        "updated": 2,
        "total": 2,
        "results": [
            {"selector": "Item A", "title": "Item A", "updated": True},
            {"selector": "Item B", "title": "Item B", "updated": True},
        ],
    }
    with patch("backlog_core.operations.batch_update_items", return_value=op_result) as mock_batch:
        response = await _call("backlog_batch_update", {"selectors": ["Item A", "Item B"], "status": "in-progress"})

    mock_batch.assert_called_once()
    assert mock_batch.call_args.kwargs["selectors"] == ["Item A", "Item B"]
    assert mock_batch.call_args.kwargs["status"] == "in-progress"
    assert response["updated"] == 2
    assert response["total"] == 2
    assert "messages" in response


async def test_backlog_batch_update_passes_plan():
    """backlog_batch_update forwards plan to operations."""
    op_result = {"updated": 1, "total": 1, "results": []}
    with patch("backlog_core.operations.batch_update_items", return_value=op_result) as mock_batch:
        await _call("backlog_batch_update", {"selectors": ["#10"], "plan": "plan/tasks-10.md"})

    assert mock_batch.call_args.kwargs["plan"] == "plan/tasks-10.md"


async def test_backlog_batch_update_backlog_error_returns_error_key():
    """backlog_batch_update catches BacklogError."""
    with patch("backlog_core.operations.batch_update_items", side_effect=BacklogError("empty selectors")):
        response = await _call("backlog_batch_update", {"selectors": []})

    assert response["error"] == "empty selectors"


# ---------------------------------------------------------------------------
# F16 — backlog_update validation guard
# ---------------------------------------------------------------------------


async def test_backlog_update_rejects_groomed_content_with_section():
    """backlog_update raises ValidationError when both groomed_content and section are provided."""
    response = await _call(
        "backlog_update", {"selector": "Item", "groomed_content": "## Section\ncontent", "section": "Background"}
    )

    assert "error" in response
    assert "mutually exclusive" in response["error"]


async def test_backlog_update_rejects_section_without_content():
    """backlog_update raises ValidationError when section is provided without content."""
    response = await _call("backlog_update", {"selector": "Item", "section": "Background"})

    assert "error" in response
    assert "content" in response["error"]


# ---------------------------------------------------------------------------
# F17 — MCP prompts registered
# ---------------------------------------------------------------------------


async def test_mcp_prompts_are_registered():
    """All expected prompt names are registered in the MCP server."""
    expected = {
        "backlog_add_prompt",
        "backlog_list_prompt",
        "backlog_dashboard_prompt",
        "backlog_view_prompt",
        "backlog_groom_prompt",
        "backlog_start_prompt",
        "backlog_resolve_prompt",
        "backlog_session_diff_prompt",
    }
    async with Client(mcp) as client:
        prompts = await client.list_prompts()
    registered = {p.name for p in prompts}
    assert expected.issubset(registered), f"Missing prompts: {expected - registered}"


# ---------------------------------------------------------------------------
# All new tools registered
# ---------------------------------------------------------------------------


async def test_all_sixteen_tools_are_registered():
    """All 16 expected tool names are now registered (10 original + 6 new)."""
    expected = {
        "backlog_add",
        "backlog_list",
        "backlog_view",
        "backlog_sync",
        "backlog_close",
        "backlog_resolve",
        "backlog_update",
        "backlog_groom",
        "backlog_normalize",
        "backlog_pull",
        "backlog_session_diff",
        "backlog_dashboard",
        "backlog_start",
        "backlog_block",
        "backlog_unblock",
        "backlog_batch_update",
    }
    async with Client(mcp) as client:
        tools = await client.list_tools()
    registered = {t.name for t in tools}
    assert expected.issubset(registered), f"Missing tools: {expected - registered}"
