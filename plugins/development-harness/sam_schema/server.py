"""FastMCP server for SAM task/plan operations.

Exposes the same operations as the Typer CLI as MCP tools for use by
Claude Code agents and other MCP clients.

Tools:
    sam_read    — Read a task by address (returns TaskAssignment when task provided)
    sam_state   — Update a task's status
    sam_ready   — List ready tasks for a plan
    sam_status  — Get plan-level progress summary
    sam_list    — List all plans with search and pagination
    sam_create  — Create a new plan from YAML task definitions
    sam_update  — Update plan or task fields, or append a section
    sam_claim   — Claim a task (transition to in-progress)
"""

from __future__ import annotations

import contextlib
import json
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Annotated, Any, cast

import backlog_core.models as _backlog_models
import tiktoken
from backlog_core.artifact_provider import GitHubArtifactProvider
from backlog_core.artifact_registry import ArtifactRegistry as _ArtifactRegistry
from backlog_core.models import ArtifactEntry, ArtifactStatus, ArtifactType, BacklogError
from fastmcp import FastMCP
from pydantic import Field
from ruamel.yaml import YAML, YAMLError

from sam_schema.core.exceptions import (
    PlanExistsError,
    PlanNotFoundError,
    SamError,
    TaskNotFoundError,
    TaskValidationError,
)
from sam_schema.core.models import Plan, Task
from sam_schema.core.task_config import TaskConfig, create_task_backend, get_task_config, set_task_config

if TYPE_CHECKING:
    from sam_schema.core.task_backend import TaskBackend
    from sam_schema.core.task_backend_types import TaskDefinition

_log = logging.getLogger(__name__)
_artifact_registry = _ArtifactRegistry()

_PLAN_DIR_SENTINEL = "plan"

# Stem parsing thresholds used in _build_task_assignment.
_STEM_MIN_PARTS_FOR_NUMBER: int = 2
_STEM_MIN_PARTS_FOR_SLUG: int = 3

# Initialize the default backend at module import time.
# Tests may call set_task_config() before importing this module to inject a custom backend.
try:
    get_task_config()
except RuntimeError:
    set_task_config(TaskConfig(backend=create_task_backend()))


def _resolve_plan_id(plan: str) -> str:
    """Convert a plan address to the backend plan ID.

    The backend resolves all address forms (numeric index, slug, ``P{N}``
    identifier) internally.  This function forwards the address as-is.

    Args:
        plan: Plan address component (e.g., ``'P912'``, ``'auth-system'``).

    Returns:
        Plan identifier to pass to :class:`~sam_schema.core.task_backend.TaskBackend`
        methods.
    """
    return plan


def _get_backend(plan_dir_str: str) -> TaskBackend:
    """Return the configured backend, or a LocalYamlTaskProvider for an explicit plan_dir.

    When *plan_dir_str* is the default sentinel (``"plan"``), returns the
    module-level configured backend from :func:`get_task_config`.  When
    *plan_dir_str* is a concrete filesystem path, creates a
    :class:`~sam_schema.core.backends.local_yaml.LocalYamlTaskProvider` for
    that path to preserve backward compatibility with callers that supply an
    explicit directory.

    Args:
        plan_dir_str: The ``plan_dir`` parameter from the MCP tool call.

    Returns:
        :class:`~sam_schema.core.task_backend.TaskBackend` instance to use for
        this tool call.
    """
    if plan_dir_str == _PLAN_DIR_SENTINEL:
        return get_task_config().backend
    # Non-default plan_dir: callers passing a concrete path expect local filesystem
    # behavior, so create a LocalYamlTaskProvider for that explicit path.
    from sam_schema.core.backends.local_yaml import LocalYamlTaskProvider  # noqa: PLC0415

    return LocalYamlTaskProvider(Path(plan_dir_str))


# Token budget for auto-pagination: 4400 tokens (cl100k_base encoding).
_TOKEN_BUDGET: int = 4_400
_enc: tiktoken.Encoding = tiktoken.get_encoding("cl100k_base")

mcp: FastMCP = FastMCP(
    "sam",
    instructions=(
        "SAM (Structured Agent-Managed) task plan server. "
        "Use sam_read to inspect a plan or task. "
        "Use sam_claim to take ownership of a task before starting work. "
        "Use sam_state to update task status. "
        "Use sam_ready to list tasks ready for dispatch. "
        "Use sam_status for a plan-level progress summary. "
        "Use sam_list to enumerate all plans with optional search and pagination. "
        "Use sam_create to create a new plan from YAML task definitions. "
        "Use sam_update to set fields or append a markdown section to a task body."
    ),
)


def run_server() -> None:
    """Entry point for ``sam-mcp`` console script."""
    mcp.run()


@mcp.tool
def sam_read(
    plan: Annotated[str, Field(description="Plan address (e.g., 'P1' or slug)")],
    task: Annotated[str | None, Field(description="Task ID (e.g., 'T3'). Omit to read plan-level fields only.")] = None,
    plan_dir: Annotated[str, Field(description="Plan directory path")] = "plan",
) -> dict:
    """Read a plan or task and return its fields as a dict.

    When ``task`` is provided, returns a ``TaskAssignment`` dict that includes
    both plan-level context (``plan_goal``, ``plan_context``,
    ``plan_acceptance_criteria``) and the nested ``task`` object.  This gives
    agents everything they need in one call.

    When ``task`` is omitted, returns the ``Plan`` fields only.

    Args:
        plan: Plan address component (numeric index or slug).
        task: Task ID component (e.g., ``T3``). Optional.
        plan_dir: Path to the directory containing plan files.

    Returns:
        ``TaskAssignment`` fields as a JSON-serializable dict when ``task`` is
        provided, or ``Plan`` fields when ``task`` is omitted.  Returns a dict
        with an ``error`` key on failure.
    """
    try:
        backend = _get_backend(plan_dir)
        plan_id = _resolve_plan_id(plan)
        plan_data = backend.read_plan(plan_id)

        if task is not None:
            task_data = backend.read_task(plan_id, task)
            return dict(task_data)

        # Plan-only read: rebuild through Plan model for exact serialization shape.
        plan_dict = {k: v for k, v in plan_data.items() if k != "plan_id"}
        plan_model = Plan.model_validate(plan_dict)
        return plan_model.model_dump(mode="json", by_alias=True, exclude_none=True)
    except (PlanNotFoundError, TaskNotFoundError, SamError) as exc:
        return {"error": str(exc)}


@mcp.tool
def sam_state(
    plan: Annotated[str, Field(description="Plan address")],
    task: Annotated[str, Field(description="Task ID")],
    status: Annotated[str, Field(description="New status value")],
    plan_dir: Annotated[str, Field(description="Plan directory path")] = "plan",
) -> dict:
    """Update a task's status.

    Args:
        plan: Plan address component.
        task: Task ID component.
        status: New status string (e.g., ``complete``, ``in-progress``).
        plan_dir: Path to the directory containing plan files.

    Returns:
        Updated task fields as a JSON-serializable dict, or a dict with an
        ``error`` key on failure.
    """
    try:
        backend = _get_backend(plan_dir)
        plan_id = _resolve_plan_id(plan)
        backend.update_task_status(plan_id, task, status)
        task_data = backend.read_task(plan_id, task)
        return dict(task_data)
    except (TaskValidationError, PlanNotFoundError, TaskNotFoundError, SamError) as exc:
        return {"error": str(exc)}


@mcp.tool
def sam_ready(
    plan: Annotated[str, Field(description="Plan address")],
    plan_dir: Annotated[str, Field(description="Plan directory path")] = "plan",
    full: Annotated[bool, Field(description="Return full Task model dump instead of routing manifest")] = False,
) -> dict:
    """List tasks ready for dispatch.

    By default returns a compact 7-field routing manifest per task so the
    orchestrator can decide which agent to dispatch next without receiving the
    full task body (25+ fields).  Pass ``full=True`` to get the complete model
    dump (preserves backward compatibility for callers that need all fields).

    Args:
        plan: Plan address component.
        plan_dir: Path to the directory containing plan files.
        full: When True, return full Task model dump instead of routing manifest.

    Returns:
        Dict with ``ready_tasks`` list, ``count``, ``feature``, ``source_path``,
        and ``issue`` envelope fields, or a dict with an ``error`` key on failure.
    """
    try:
        backend = _get_backend(plan_dir)
        plan_id = _resolve_plan_id(plan)
        plan_data = backend.read_plan(plan_id)
        tasks_data = backend.get_ready_tasks(plan_id)
        if full:
            ready_tasks: list[dict[str, Any]] = [Task.model_validate(t).model_dump(mode="json") for t in tasks_data]
        else:
            ready_tasks = [
                {
                    "id": t["id"],
                    "task": t["title"],
                    "agent": t["agent"],
                    "skills": t["skills"] or [],
                    "dependencies": t["dependencies"] or [],
                    "status": t["status"],
                    "priority": int(t["priority"]),
                }
                for t in tasks_data
            ]
        return {
            "ready_tasks": ready_tasks,
            "count": len(tasks_data),
            "feature": plan_data["feature"],
            "source_path": str(plan_data["source_path"] or plan_id),
            "issue": plan_data["issue"],
        }
    except (PlanNotFoundError, SamError) as exc:
        return {"error": str(exc)}


@mcp.tool
def sam_status(
    plan: Annotated[str, Field(description="Plan address")],
    plan_dir: Annotated[str, Field(description="Plan directory path")] = "plan",
) -> dict:
    """Get plan-level progress summary.

    Args:
        plan: Plan address component.
        plan_dir: Path to the directory containing plan files.

    Returns:
        ``PlanStatus`` fields as a JSON-serializable dict including
        ``total_tasks``, ``by_status``, ``ready_tasks``, ``blocked_tasks``,
        ``completion_pct``, and ``has_cycles``, or a dict with an ``error``
        key on failure.
    """
    try:
        backend = _get_backend(plan_dir)
        plan_id = _resolve_plan_id(plan)
        return dict(backend.get_plan_status(plan_id))
    except (PlanNotFoundError, SamError) as exc:
        return {"error": str(exc)}


def _paginate_results(
    all_items: list[dict[str, Any]],
    *,
    offset: int,
    limit: int | None,
    messages: list[str],
    warnings: list[str],
    errors: list[str],
    tool_name: str,
) -> dict[str, Any]:
    """Paginate ``all_items`` within the token budget and return the response dict.

    Returns:
        Dict with ``items``, ``count``, ``pagination``, ``messages``, ``warnings``, ``errors``,
        and optionally ``next_call``.
    """
    total = len(all_items)
    page_items = all_items[offset:]

    if limit is not None:
        effective_limit = limit
    else:
        effective_limit = len(page_items)
        for candidate_limit in range(1, len(page_items) + 1):
            if len(_enc.encode(json.dumps(page_items[:candidate_limit]))) > _TOKEN_BUDGET:
                effective_limit = max(1, candidate_limit - 1)
                break

    page = page_items[:effective_limit]
    has_more = (offset + len(page)) < total
    result: dict[str, Any] = {
        "items": page,
        "count": len(page),
        "pagination": {"offset": offset, "limit": effective_limit, "total": total, "has_more": has_more},
        "messages": messages,
        "warnings": warnings,
        "errors": errors,
    }
    if has_more:
        next_offset = offset + len(page)
        result["next_call"] = f"{tool_name}(offset={next_offset}, limit={effective_limit})"
    return result


@mcp.tool
def sam_list(
    plan_dir: Annotated[str, Field(description="Plan directory path")] = "plan",
    search: Annotated[
        str | None, Field(description="Case-insensitive substring filter across feature, description, and goal fields")
    ] = None,
    offset: Annotated[int, Field(description="Zero-based index of the first item to return", ge=0)] = 0,
    limit: Annotated[
        int | None,
        Field(
            description="Maximum number of items to return. Defaults to auto-calculated value within 4400-token budget"
        ),
    ] = None,
) -> dict:
    """List all plans in ``plan_dir`` with optional search and automatic pagination.

    Reads every plan file found in ``plan_dir``, applies optional search filtering,
    then returns a page of results within the 4400-token budget (cl100k_base encoding).

    Search filtering checks the ``feature``, ``description``, and ``goal`` fields
    simultaneously, case-insensitively.  The ``offset`` and ``limit`` parameters
    let callers page through results explicitly.  When ``limit`` is omitted, the
    tool calculates a default limit that keeps the response within budget.

    When ``has_more`` is true in the ``pagination`` object, use the ``next_call``
    hint to request the next page.

    Args:
        plan_dir: Directory to scan for plan files (``*.yaml``, ``*.md``,
                  or subdirectories that are plan directories).
        search: Optional substring to filter by. Matched case-insensitively
                against ``feature``, ``description``, and ``goal`` fields.
        offset: Zero-based start index into the (filtered) result list.
        limit: Maximum items to return. Defaults to a budget-based calculation.

    Returns:
        Dict with keys:

        - ``items``: list of plan summary dicts (``feature``, ``goal``,
          ``description``, ``task_count``, ``path``).
        - ``count``: number of items in this page.
        - ``pagination``: ``{"offset": N, "limit": N, "total": N, "has_more": bool}``.
        - ``next_call``: hint string when ``has_more`` is true.
        - ``messages``: list of informational strings.
        - ``warnings``: list of non-fatal warning strings.
        - ``errors``: list of error strings (e.g. unreadable files).
    """
    warnings: list[str] = []
    errors: list[str] = []
    messages: list[str] = []

    try:
        backend = _get_backend(plan_dir)
        summaries = backend.list_plans(search=search)
    except SamError as exc:
        errors.append(str(exc))
        return _paginate_results(
            [], offset=offset, limit=limit, messages=messages, warnings=warnings, errors=errors, tool_name="sam_list"
        )

    all_items: list[dict[str, Any]] = [
        {
            "feature": s["feature"],
            "goal": s["goal"],
            "description": s["description"],
            "task_count": s["task_count"],
            "path": str(s["source_path"] or s["plan_id"]),
        }
        for s in summaries
    ]

    return _paginate_results(
        all_items, offset=offset, limit=limit, messages=messages, warnings=warnings, errors=errors, tool_name="sam_list"
    )


def _try_register_task_plan_artifact(issue_number: int, plan_path: Path) -> None:
    """Register the newly created plan file as a task-plan artifact.

    Best-effort: logs a warning on any failure but never raises.  Called after
    ``sam_create`` writes the plan file when the plan has an associated GitHub
    issue number.

    Args:
        issue_number: GitHub issue number to register the artifact against.
        plan_path: Absolute or repo-relative path to the created plan file.
    """
    try:
        repo = _backlog_models.DEFAULT_REPO
        if not repo:
            _log.warning("sam_create: skipping artifact registration — DEFAULT_REPO not set")
            return
        provider = GitHubArtifactProvider(
            repo=repo,
            root_worktree=_backlog_models._REPO_ROOT,  # noqa: SLF001
        )
        entry = ArtifactEntry(
            artifact_type=ArtifactType.TASK_PLAN, path=str(plan_path), status=ArtifactStatus.CURRENT, agent="sam_create"
        )
        manifest = provider.get_manifest(issue_number)
        updated_manifest = _artifact_registry.register(manifest, entry)
        provider.set_manifest(issue_number, updated_manifest)
        _log.info("sam_create: registered task-plan artifact %s for issue #%d", plan_path, issue_number)

        try:
            content = plan_path.read_text(encoding="utf-8")
            provider.store_artifact_content(
                issue_number, artifact_type=ArtifactType.TASK_PLAN.value, path=str(plan_path), content=content
            )
            _log.info("sam_create: uploaded task-plan content to GitHub issue #%d", issue_number)
        except (BacklogError, OSError) as upload_exc:
            _log.warning(
                "sam_create: artifact content upload failed for issue #%d (path=%s): %s",
                issue_number,
                plan_path,
                upload_exc,
                exc_info=True,
            )
    except (BacklogError, ValueError, OSError) as exc:
        _log.warning(
            "sam_create: artifact registration failed for issue #%d (path=%s): %s",
            issue_number,
            plan_path,
            exc,
            exc_info=True,
        )


@mcp.tool
def sam_create(
    slug: Annotated[str, Field(description="Short identifier for the plan (e.g., 'auth-system')")],
    goal: Annotated[str, Field(description="Human-readable goal statement for the plan")],
    tasks_yaml: Annotated[str, Field(description="YAML string with a 'tasks' key containing a list of task dicts")],
    plan_dir: Annotated[str, Field(description="Plan directory path")] = "plan",
    context: Annotated[str | None, Field(description="Optional plan-level context (markdown prose)")] = None,
    issue: Annotated[int | None, Field(description="Optional GitHub issue number to associate with the plan")] = None,
) -> dict:
    """Create a new plan from YAML task definitions.

    Parses ``tasks_yaml`` (a YAML string containing a ``tasks:`` list), validates
    each task dict against the ``Task`` Pydantic model, assigns the next available
    plan number, and writes the plan file to ``{plan_dir}/P{NNN}-{slug}.yaml``.

    Mirrors ``sam create`` CLI behaviour. All write operations are atomic.

    Args:
        slug: Short identifier for the plan.
        goal: Human-readable goal statement.
        tasks_yaml: YAML string whose top-level key is ``tasks`` — a list of task
                    dicts (required fields per ``Task`` model: ``task``, ``title``,
                    ``status``, ``agent``, ``dependencies``, ``priority``,
                    ``complexity``).
        plan_dir: Directory in which to create the plan file.
        context: Optional plan-level context string.
        issue: Optional GitHub issue number.

    Returns:
        ``{"path": str, "plan_number": int, "task_count": int}`` on success, or
        ``{"error": str}`` on failure.
    """
    try:
        yaml_parser: Any = YAML()
        parsed: dict[str, Any] = yaml_parser.load(tasks_yaml)
        if not isinstance(parsed, dict) or "tasks" not in parsed:
            return {"error": "tasks_yaml must be a YAML string with a top-level 'tasks' key"}
        task_defs = cast("list[TaskDefinition]", parsed["tasks"])
        backend = _get_backend(plan_dir)
        plan_data = backend.create_plan(slug=slug, goal=goal, tasks=task_defs, context=context, issue=issue)
    except YAMLError as exc:
        return {"error": str(exc)}
    except (TaskValidationError, PlanExistsError, SamError) as exc:
        return {"error": str(exc)}

    # Derive plan_number from plan_id (e.g., "P912" → 912).
    plan_number: int | None = None
    plan_id_str = plan_data["plan_id"]
    if plan_id_str.startswith("P"):
        with contextlib.suppress(ValueError):
            plan_number = int(plan_id_str[1:])

    result = {
        "path": str(plan_data["source_path"] or ""),
        "plan_number": plan_number,
        "task_count": len(plan_data["tasks"]),
    }

    # Auto-register the new plan file as a task-plan artifact when the plan
    # is linked to a GitHub issue.  Best-effort: failure does not block creation.
    if issue is not None and plan_data["source_path"]:
        _try_register_task_plan_artifact(issue, Path(plan_data["source_path"]))

    return result


@mcp.tool
def sam_update(
    address: Annotated[str, Field(description="Plan address (e.g., 'P1') or task address (e.g., 'P1/T2')")],
    plan_dir: Annotated[str, Field(description="Plan directory path")] = "plan",
    set_fields_json: Annotated[
        str | None, Field(description="JSON object of field=value pairs to set on the plan or task")
    ] = None,
    context: Annotated[str | None, Field(description="Set the plan-level context field")] = None,
    append_section: Annotated[
        str | None, Field(description="Name of the markdown section to append to the task body")
    ] = None,
    section_content: Annotated[str | None, Field(description="Body content for the appended section")] = None,
) -> dict:
    """Update plan or task fields, or append a markdown section to a task body.

    Supports three non-exclusive operations that can be combined in one call:

    1. ``set_fields_json`` — a JSON object of ``{field: value}`` pairs to update.
    2. ``context`` — shorthand for setting the plan-level ``context`` field.
    3. ``append_section`` + ``section_content`` — append a named markdown section
       to a task's body (task address required for this operation).

    Mirrors ``sam update`` CLI behaviour.

    Args:
        address: Plan or task address. Task address required for
                 ``append_section`` and task-level ``set_fields_json``.
        plan_dir: Directory containing plan files.
        set_fields_json: JSON string ``{"field": "value", ...}`` to set.
        context: If provided, sets the plan-level ``context`` field.
        append_section: Section heading to append to the task body.
        section_content: Body text for the appended section.

    Returns:
        ``{"updated": true, "address": str}`` on success, or ``{"error": str}``
        on failure.
    """
    try:
        # Split address into plan and optional task components.
        if "/" in address:
            plan_part, task_id = address.split("/", 1)
        else:
            plan_part = address
            task_id = None

        plan_id = _resolve_plan_id(plan_part)
        backend = _get_backend(plan_dir)

        set_fields: dict[str, str | int | list[str]] | None = None
        if set_fields_json is not None:
            raw_fields: Any = json.loads(set_fields_json)
            if not isinstance(raw_fields, dict):
                return {"error": "set_fields_json must be a JSON object"}
            set_fields = {str(k): str(v) for k, v in raw_fields.items()}

        if task_id is None:
            # Plan-level operations: context and/or field updates on the plan.
            backend.update_plan_fields(plan_id, context=context, set_fields=set_fields)
        else:
            # Task-level operations.
            # context is plan-level per the tool description; apply it separately.
            if context is not None:
                backend.update_plan_fields(plan_id, context=context)
            if set_fields:
                backend.update_task_fields(plan_id, task_id, set_fields)
            if append_section is not None:
                backend.append_task_section(plan_id, task_id, append_section, section_content or "")
    except (PlanNotFoundError, TaskNotFoundError, SamError) as exc:
        return {"error": str(exc)}
    except ValueError as exc:
        return {"error": str(exc)}
    else:
        return {"updated": True, "address": address}


@mcp.tool
def sam_claim(
    plan: Annotated[str, Field(description="Plan address (e.g., 'P1' or slug)")],
    task: Annotated[str, Field(description="Task ID to claim (e.g., 'T3')")],
    plan_dir: Annotated[str, Field(description="Plan directory path")] = "plan",
) -> dict:
    """Claim a task by transitioning it from ``not-started`` to ``in-progress``.

    Guards against double-claiming: returns an error dict (not an exception) if
    the task is already in-progress or in a terminal state. Mirrors ``sam claim``
    CLI behaviour.

    Args:
        plan: Plan address component (numeric index or slug).
        task: Task ID to claim (e.g., ``T3``).
        plan_dir: Path to the directory containing plan files.

    Returns:
        ``{"claimed": true, "task_id": str, "started": str}`` on success, or
        ``{"claimed": false, "error": str}`` if the task cannot be claimed.
    """
    try:
        backend = _get_backend(plan_dir)
        plan_id = _resolve_plan_id(plan)
        claimed = backend.claim_task(plan_id, task)
    except (PlanNotFoundError, TaskNotFoundError) as exc:
        return {"claimed": False, "error": str(exc)}
    except SamError as exc:
        return {"error": str(exc)}

    if not claimed:
        # Read current status to provide a meaningful error message.
        try:
            task_data = backend.read_task(plan_id, task)
            current_status = task_data["status"]
        except (PlanNotFoundError, TaskNotFoundError, SamError):
            return {"claimed": False, "error": f"Cannot claim task '{task}': task is not available for claiming."}
        else:
            return {
                "claimed": False,
                "error": f"Cannot claim task '{task}': expected status 'not-started' but found '{current_status}'.",
            }

    task_data = backend.read_task(plan_id, task)
    return {"claimed": True, "task_id": task_data["id"], "started": task_data["started"]}
