"""TDD RED-phase tests — T04: SAM server routes all tools through TaskBackend.

These tests define expected behaviour AFTER the T04 refactor and FAIL against
the current server.py implementation, which imports and calls query.* directly
instead of routing through get_task_config().backend.

Test groups:
    1. Backend routing — each of the 8 tools calls the expected TaskBackend method
       (not query / yaml_reader / yaml_writer) via get_task_config().backend
    2. Exception handling — PlanNotFoundError / TaskNotFoundError from the backend
       produce {"error": "..."} response dicts, not unhandled exceptions
    3. Module initialisation — server.py source contains set_task_config and
       create_task_backend at module level (not inside a function)
    4. Structural — server.py source has no direct query / yaml_reader / yaml_writer
       imports after the refactor

No @pytest.mark.asyncio decorators — asyncio_mode = "auto" is set in pyproject.toml.
"""

from __future__ import annotations

import inspect
import json
from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest
from fastmcp.client import Client
from fastmcp.exceptions import ToolError
from pytest_mock import MockerFixture  # noqa: F401 — available for future use
from sam_schema.core.exceptions import PlanNotFoundError, TaskNotFoundError
from sam_schema.core.task_config import TaskConfig, reset_task_config, set_task_config
from sam_schema.server import mcp

if TYPE_CHECKING:
    from collections.abc import Generator

# ---------------------------------------------------------------------------
# Shared call helper
# ---------------------------------------------------------------------------


async def _call(tool_name: str, params: dict | None = None) -> dict:
    """Call an MCP tool through the in-memory FastMCP transport.

    Args:
        tool_name: Registered MCP tool name (e.g. ``"sam_read"``).
        params: Optional parameter dict to pass to the tool.

    Returns:
        Parsed JSON response dict from the tool.
    """
    async with Client(mcp) as client:
        result = await client.call_tool(tool_name, params or {})
    return json.loads(result.content[0].text)


# ---------------------------------------------------------------------------
# Canonical minimal return values for the mock backend
# ---------------------------------------------------------------------------

_PLAN_DATA: dict = {
    "plan_id": "P1",
    "feature": "test-feature",
    "version": "1",
    "description": "test description",
    "goal": "test goal",
    "context": "",
    "acceptance_criteria": "",
    "issue": None,
    "tasks": [],
    "source_path": None,
}

_TASK_DATA: dict = {
    "id": "T1",
    "title": "test task",
    "status": "not-started",
    "agent": "test-agent",
    "dependencies": [],
    "blocked_by": [],
    "parallelize_with": [],
    "priority": 2,
    "complexity": "low",
    "skills": [],
    "created": None,
    "started": None,
    "completed": None,
    "last_activity": None,
    "body": "",
    "description": "",
}

_STATUS_DATA: dict = {
    "feature": "test-feature",
    "total_tasks": 0,
    "by_status": {},
    "ready_tasks": [],
    "blocked_tasks": [],
    "completion_pct": 0.0,
    "has_cycles": False,
}

_PLAN_SUMMARY: dict = {
    "plan_id": "P1",
    "feature": "test-feature",
    "goal": "test goal",
    "description": "",
    "task_count": 0,
    "source_path": "/tmp/P001-test.yaml",
}

_MINIMAL_TASKS_YAML = (
    "tasks:\n"
    "  - task: T1\n"
    "    title: Do something\n"
    "    status: not-started\n"
    "    agent: test-agent\n"
    "    dependencies: []\n"
    "    priority: 2\n"
    "    complexity: simple\n"
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def backend_mock() -> Generator[MagicMock, None, None]:
    """Inject a MagicMock TaskBackend via set_task_config for test isolation.

    Configures default return values for all Protocol methods so tool code
    can reach the assertion point without crashing after T04. Calls
    reset_task_config() in teardown to prevent cross-test contamination.

    Yields:
        Configured MagicMock satisfying the TaskBackend Protocol surface.
    """
    mock_backend = MagicMock()
    mock_backend.read_plan.return_value = _PLAN_DATA
    mock_backend.read_task.return_value = _TASK_DATA
    mock_backend.get_ready_tasks.return_value = []
    mock_backend.get_plan_status.return_value = _STATUS_DATA
    mock_backend.list_plans.return_value = [_PLAN_SUMMARY]
    mock_backend.create_plan.return_value = {**_PLAN_DATA, "source_path": "/tmp/P001-test-slug.yaml"}
    mock_backend.claim_task.return_value = True
    mock_backend.update_task_status.return_value = None
    mock_backend.update_plan_fields.return_value = None
    mock_backend.update_task_fields.return_value = None
    mock_backend.append_task_section.return_value = None

    set_task_config(TaskConfig(backend=mock_backend))
    yield mock_backend
    reset_task_config()


# ---------------------------------------------------------------------------
# Group 1: Backend routing — each tool calls the expected TaskBackend method
# ---------------------------------------------------------------------------


async def test_sam_read_plan_only_routes_through_backend_read_plan(backend_mock: MagicMock) -> None:
    """sam_read without task calls backend.read_plan, not query.load_plan.

    After T04, sam_read(plan='P1') must resolve to backend.read_plan('P1').
    The current implementation bypasses the backend entirely, so this assertion
    fails in RED phase.

    Arrange: inject mock backend via set_task_config with default plan data.
    Act: call sam_read with plan='P1', no task.
    Assert: backend.read_plan was called exactly once with plan_id 'P1'.
    """
    # Act
    await _call("sam_read", {"plan": "P1"})

    # Assert
    backend_mock.read_plan.assert_called_once_with("P1")


async def test_sam_read_with_task_routes_through_backend_read_task(backend_mock: MagicMock) -> None:
    """sam_read with task calls backend.read_task, not query.get_task_assignment.

    After T04, sam_read(plan='P1', task='T1') must delegate to
    backend.read_task('P1', 'T1') to retrieve the task with its plan context.

    Arrange: inject mock backend with task data return value.
    Act: call sam_read with plan='P1' and task='T1'.
    Assert: backend.read_task called once with ('P1', 'T1').
    """
    # Act
    await _call("sam_read", {"plan": "P1", "task": "T1"})

    # Assert
    backend_mock.read_task.assert_called_once_with("P1", "T1")


async def test_sam_read_with_task_returns_task_assignment_envelope(backend_mock: MagicMock) -> None:
    """sam_read with task returns TaskAssignment envelope including plan_goal and task fields.

    After the P912 follow-up fix, sam_read(plan='P1', task='T1') must return a dict
    containing plan-level envelope fields (plan-goal, plan-number) alongside the nested
    task object — matching the old TaskAssignment serialization shape.

    Arrange: inject mock backend; _PLAN_DATA has goal='test goal', feature='test-feature'.
    Act: call sam_read with plan='P1' and task='T1'.
    Assert: response contains 'plan-goal' (by_alias serialization) and 'task' keys,
            with plan-goal matching the plan data value.
    """
    # Act
    response = await _call("sam_read", {"plan": "P1", "task": "T1"})

    # Assert
    assert "plan-goal" in response, f"Expected 'plan-goal' in response, got keys: {sorted(response.keys())}"
    assert "task" in response, f"Expected 'task' in response, got keys: {sorted(response.keys())}"
    assert response["plan-goal"] == "test goal"
    assert response["task"]["id"] == "T1"


async def test_sam_state_routes_through_backend_update_task_status(backend_mock: MagicMock) -> None:
    """sam_state calls backend.update_task_status, not query.update_status.

    After T04, sam_state(plan, task, status) must delegate to
    backend.update_task_status(plan_id, task_id, status_str).

    Arrange: inject mock backend via set_task_config.
    Act: call sam_state with plan='P1', task='T1', status='complete'.
    Assert: backend.update_task_status called with ('P1', 'T1', 'complete').
    """
    # Act
    await _call("sam_state", {"plan": "P1", "task": "T1", "status": "complete"})

    # Assert
    backend_mock.update_task_status.assert_called_once_with("P1", "T1", "complete")


async def test_sam_ready_routes_through_backend_get_ready_tasks(backend_mock: MagicMock) -> None:
    """sam_ready calls backend.get_ready_tasks, not query.get_ready_tasks directly.

    After T04, the list of dispatch-ready tasks is fetched via the backend
    Protocol, enabling non-filesystem backends (memory, GitHub) to implement it.

    Arrange: inject mock backend; configure get_ready_tasks to return [].
    Act: call sam_ready with plan='P1'.
    Assert: backend.get_ready_tasks called exactly once with 'P1'.
    """
    # Act
    await _call("sam_ready", {"plan": "P1"})

    # Assert
    backend_mock.get_ready_tasks.assert_called_once_with("P1")


async def test_sam_status_routes_through_backend_get_plan_status(backend_mock: MagicMock) -> None:
    """sam_status calls backend.get_plan_status, not query.get_plan_status.

    After T04, plan-level progress summaries come from the backend Protocol
    rather than direct YAML reads, enabling in-memory and remote backends.

    Arrange: inject mock backend; configure get_plan_status return value.
    Act: call sam_status with plan='P1'.
    Assert: backend.get_plan_status called once with 'P1'.
    """
    # Act
    await _call("sam_status", {"plan": "P1"})

    # Assert
    backend_mock.get_plan_status.assert_called_once_with("P1")


async def test_sam_list_routes_through_backend_list_plans(backend_mock: MagicMock) -> None:
    """sam_list calls backend.list_plans, not direct filesystem iteration.

    After T04, plan enumeration is delegated to the backend, which handles
    search, pagination, and filesystem (or remote) access internally.

    Arrange: inject mock backend; configure list_plans to return a summary list.
    Act: call sam_list with default parameters (plan_dir sentinel).
    Assert: backend.list_plans called at least once.
    """
    # Act
    await _call("sam_list", {})

    # Assert
    backend_mock.list_plans.assert_called_once()


async def test_sam_create_routes_through_backend_create_plan(backend_mock: MagicMock) -> None:
    """sam_create calls backend.create_plan, not query.create_plan directly.

    After T04, plan creation is mediated through the TaskBackend Protocol.
    The YAML parsing of tasks_yaml (user input) may remain in the tool, but
    the actual plan write goes through backend.create_plan.

    Arrange: inject mock backend; configure create_plan return value.
    Act: call sam_create with slug='test-slug', goal='test goal', valid tasks_yaml.
    Assert: backend.create_plan called once; slug argument is 'test-slug'.
    """
    # Act
    await _call("sam_create", {"slug": "test-slug", "goal": "test goal", "tasks_yaml": _MINIMAL_TASKS_YAML})

    # Assert
    backend_mock.create_plan.assert_called_once()
    call_args = backend_mock.create_plan.call_args
    # Accept both positional and keyword slug argument
    slug_value = call_args.kwargs.get("slug") if call_args.kwargs else None
    if slug_value is None and call_args.args:
        slug_value = call_args.args[0]
    assert slug_value == "test-slug"


async def test_sam_update_plan_fields_routes_through_backend_update_plan_fields(backend_mock: MagicMock) -> None:
    """sam_update for plan-level address calls backend.update_plan_fields.

    After T04, plan context and field updates go through the backend Protocol.
    A plan address (no '/') triggers backend.update_plan_fields, not the
    query.update_plan_fields function.

    Arrange: inject mock backend via set_task_config.
    Act: call sam_update with plan address 'P1' and context='new context'.
    Assert: backend.update_plan_fields called once.
    """
    # Act
    await _call("sam_update", {"address": "P1", "context": "new context"})

    # Assert
    backend_mock.update_plan_fields.assert_called_once()


async def test_sam_update_task_fields_routes_through_backend_update_task_fields(backend_mock: MagicMock) -> None:
    """sam_update with task address and set_fields_json calls backend.update_task_fields.

    After T04, task scalar field updates (e.g. agent, status) go through
    backend.update_task_fields when a task address ('P1/T1') is provided.

    Arrange: inject mock backend via set_task_config.
    Act: call sam_update with address='P1/T1' and set_fields_json for agent field.
    Assert: backend.update_task_fields called once.
    """
    # Act
    await _call("sam_update", {"address": "P1/T1", "set_fields_json": '{"agent": "new-agent"}'})

    # Assert
    backend_mock.update_task_fields.assert_called_once()


async def test_sam_update_append_section_routes_through_backend_append_task_section(backend_mock: MagicMock) -> None:
    """sam_update with append_section calls backend.append_task_section.

    After T04, appending a markdown section to a task body goes through
    backend.append_task_section, not through query.update_plan_fields.

    Arrange: inject mock backend via set_task_config.
    Act: call sam_update with task address 'P1/T1', append_section, and content.
    Assert: backend.append_task_section called once.
    """
    # Act
    await _call(
        "sam_update", {"address": "P1/T1", "append_section": "Work Log", "section_content": "Completed the refactor."}
    )

    # Assert
    backend_mock.append_task_section.assert_called_once()


async def test_sam_claim_routes_through_backend_claim_task(backend_mock: MagicMock) -> None:
    """sam_claim calls backend.claim_task, not query.claim_task directly.

    After T04, task claiming is mediated through the backend Protocol,
    enabling atomic claim semantics in non-filesystem backends.

    Arrange: inject mock backend; configure claim_task to return True.
    Act: call sam_claim with plan='P1', task='T1'.
    Assert: backend.claim_task called once with ('P1', 'T1').
    """
    # Act
    await _call("sam_claim", {"plan": "P1", "task": "T1"})

    # Assert
    backend_mock.claim_task.assert_called_once_with("P1", "T1")


# ---------------------------------------------------------------------------
# Group 2: Exception handling — SAM exceptions propagate as MCP ToolError
# ---------------------------------------------------------------------------


async def test_sam_read_raises_tool_error_when_backend_raises_plan_not_found(backend_mock: MagicMock) -> None:
    """sam_read raises ToolError when backend raises PlanNotFoundError.

    FastMCP converts unhandled tool exceptions to isError=true MCP responses,
    which the client surfaces as ToolError. The error message must include the
    plan_id so callers can identify which plan was missing.

    Arrange: configure backend.read_plan to raise PlanNotFoundError("P999").
    Act: call sam_read with plan='P999'.
    Assert: ToolError is raised containing "Plan not found" and "P999".
    """
    # Arrange
    backend_mock.read_plan.side_effect = PlanNotFoundError("P999")

    # Act / Assert
    with pytest.raises(ToolError) as exc_info:
        await _call("sam_read", {"plan": "P999"})
    assert "Plan not found" in str(exc_info.value)
    assert "P999" in str(exc_info.value)


async def test_sam_state_raises_tool_error_when_backend_raises_task_not_found(backend_mock: MagicMock) -> None:
    """sam_state raises ToolError when backend raises TaskNotFoundError.

    FastMCP converts unhandled tool exceptions to isError=true MCP responses,
    which the client surfaces as ToolError. The error message must reference
    the missing task_id.

    Arrange: configure backend.update_task_status to raise TaskNotFoundError("P1", "T999").
    Act: call sam_state with plan='P1', task='T999', status='complete'.
    Assert: ToolError is raised containing "T999".
    """
    # Arrange
    backend_mock.update_task_status.side_effect = TaskNotFoundError("P1", "T999")

    # Act / Assert
    with pytest.raises(ToolError) as exc_info:
        await _call("sam_state", {"plan": "P1", "task": "T999", "status": "complete"})
    assert "T999" in str(exc_info.value)


async def test_sam_claim_raises_tool_error_when_backend_raises_plan_not_found(backend_mock: MagicMock) -> None:
    """sam_claim raises ToolError when backend.claim_task raises PlanNotFoundError.

    FastMCP converts unhandled tool exceptions to isError=true MCP responses,
    which the client surfaces as ToolError. MCP clients must use the isError
    flag (not dict key inspection) to detect tool failures.

    Arrange: configure backend.claim_task to raise PlanNotFoundError("P999").
    Act: call sam_claim with plan='P999', task='T1'.
    Assert: ToolError is raised containing "P999".
    """
    # Arrange
    backend_mock.claim_task.side_effect = PlanNotFoundError("P999")

    # Act / Assert
    with pytest.raises(ToolError) as exc_info:
        await _call("sam_claim", {"plan": "P999", "task": "T1"})
    assert "P999" in str(exc_info.value)


# ---------------------------------------------------------------------------
# Group 3: Module initialisation — set_task_config called at module level
# ---------------------------------------------------------------------------


def test_server_module_source_calls_set_task_config() -> None:
    """server.py source contains a call to set_task_config.

    After T04, the module must call set_task_config(TaskConfig(backend=...))
    at import time so that get_task_config() succeeds without manual setup.
    This structural check ensures the initialisation is present in the source.

    Why: Without module-level initialisation, a fresh import leaves
    get_task_config() raising RuntimeError, breaking all 8 MCP tools.
    """
    import sam_schema.server as server_module

    source = inspect.getsource(server_module)
    assert "set_task_config" in source


def test_server_module_source_calls_create_task_backend() -> None:
    """server.py source contains a call to create_task_backend.

    After T04, the backend instance must be obtained via the factory function
    create_task_backend(), which honours the TASKBACKEND env var and
    taskbackend.toml, rather than directly constructing LocalYamlTaskProvider.

    Why: Direct construction bypasses backend selection, breaking env-based
    backend switching used in tests and CI.
    """
    import sam_schema.server as server_module

    source = inspect.getsource(server_module)
    assert "create_task_backend" in source


# ---------------------------------------------------------------------------
# Group 4: Structural — no direct query / yaml_reader / yaml_writer imports
# ---------------------------------------------------------------------------


def test_server_has_no_direct_query_import() -> None:
    """server.py must not import from sam_schema.core.query after T04.

    After T04, all operations previously performed by query.* functions are
    delegated to the TaskBackend Protocol. Any remaining direct query import
    is a regression that indicates the tool still bypasses the backend.

    Check: neither 'from sam_schema.core.query import' nor
    'from sam_schema.core import query' appear in server.py import lines.
    """
    import sam_schema.server as server_module

    source = inspect.getsource(server_module)
    import_lines = [line for line in source.splitlines() if line.strip().startswith(("from ", "import "))]
    import_block = "\n".join(import_lines)

    assert "from sam_schema.core.query import" not in import_block
    assert "from sam_schema.core import query" not in import_block


def test_server_has_no_yaml_reader_import() -> None:
    """server.py must not import yaml_reader after T04.

    yaml_reader is an internal module of the YAML I/O stack encapsulated inside
    LocalYamlTaskProvider. A direct import in server.py indicates the tool is
    reading YAML files outside the backend abstraction.

    Check: the string 'yaml_reader' does not appear anywhere in server.py source.
    """
    import sam_schema.server as server_module

    source = inspect.getsource(server_module)
    assert "yaml_reader" not in source


def test_server_has_no_yaml_writer_import() -> None:
    """server.py must not import yaml_writer after T04.

    yaml_writer is an internal module of the YAML I/O stack encapsulated inside
    LocalYamlTaskProvider. A direct import in server.py indicates the tool is
    writing YAML files outside the backend abstraction.

    Check: the string 'yaml_writer' does not appear anywhere in server.py source.
    """
    import sam_schema.server as server_module

    source = inspect.getsource(server_module)
    assert "yaml_writer" not in source
