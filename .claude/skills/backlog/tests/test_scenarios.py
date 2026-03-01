"""Scenario-based integration tests for the backlog MCP FastMCP server.

Tests are organized by the skill/agent workflow that generates each call
pattern. All tests go through the full operations layer — mocking only at
the github.py boundary and filesystem (via conftest fixtures).

Uses in-memory FastMCP Client transport (``Client(mcp)``).
No ``@pytest.mark.asyncio`` decorators — global ``asyncio_mode = "auto"``.
"""

from __future__ import annotations

import json

from backlog_core.server import mcp
from fastmcp.client import Client

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _call(tool_name: str, params: dict | None = None) -> dict:
    """Call MCP tool via in-memory transport and parse JSON response."""
    async with Client(mcp) as client:
        result = await client.call_tool(tool_name, params or {})
    return json.loads(result.content[0].text)


# ---------------------------------------------------------------------------
# Group 2.1: create-backlog-item workflow (backlog_add)
# ---------------------------------------------------------------------------


class TestCreateBacklogItem:
    """Scenarios consumed by /create-backlog-item skill."""


# ---------------------------------------------------------------------------
# Group 2.2-2.5: work-backlog-item workflows
# ---------------------------------------------------------------------------


class TestWorkBacklogItem:
    """Scenarios consumed by /work-backlog-item skill.

    Covers browse/list, view, plan/status/update, close, and resolve.
    """


# ---------------------------------------------------------------------------
# Group 2.6: groom-backlog-item workflow (backlog_groom)
# ---------------------------------------------------------------------------


class TestGroomBacklogItem:
    """Scenarios consumed by /groom-backlog-item skill."""


# ---------------------------------------------------------------------------
# Group 2.7: group-items-to-milestone + backlog-item-groomer
# ---------------------------------------------------------------------------


class TestGroupItemsToMilestone:
    """Scenarios consumed by /group-items-to-milestone skill."""


class TestBacklogItemGroomer:
    """Scenarios consumed by @backlog-item-groomer agent."""


# ---------------------------------------------------------------------------
# Group 2.8-2.9: sync, pull, normalize
# ---------------------------------------------------------------------------


class TestSyncAndPull:
    """Scenarios for backlog_sync and backlog_pull tools."""


class TestNormalize:
    """Scenarios for backlog_normalize tool."""


# ---------------------------------------------------------------------------
# Group 2.10-2.11: error paths and lifecycle tests
# ---------------------------------------------------------------------------


class TestErrorPaths:
    """Error path tests: close without checklist, view nonexistent,
    add duplicate, list empty backlog.
    """


class TestLifecycles:
    """Full lifecycle tests: create→close, create→resolve+cleanup,
    stale discovery.
    """
