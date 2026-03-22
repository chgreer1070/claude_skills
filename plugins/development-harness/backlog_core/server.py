"""FastMCP 3.x server exposing all backlog operations as MCP tools."""

from __future__ import annotations

import argparse
import asyncio
import dataclasses
import json as _json
import re as _re
import sys
from datetime import UTC, datetime as _datetime
from typing import TYPE_CHECKING, Annotated, cast

import dispatch_schema as _ds
import tiktoken
from fastmcp import Context, FastMCP
from pydantic import Field
from ruamel.yaml import YAML as _YAML

from . import models as _models, operations
from .artifact_provider import GitHubArtifactProvider
from .artifact_registry import ArtifactRegistry
from .github import get_github as _get_github
from .models import (
    ArtifactContent,
    ArtifactEntry,
    ArtifactStatus,
    ArtifactType,
    BacklogError,
    GitHubUnavailableError,
    Output,
    RegisterResult,
    init as _init_models,
)

if TYPE_CHECKING:
    from pathlib import Path

    from .operations import ImpactRadiusItem as _ImpactRadiusItem

# Token budget for auto-pagination in backlog_list: 4400 tokens (cl100k_base encoding).
_LIST_TOKEN_BUDGET = 4_400
_enc: tiktoken.Encoding = tiktoken.get_encoding("cl100k_base")


def _parse_args() -> argparse.Namespace:
    """Parse server startup arguments.

    Returns:
        Parsed namespace; ``project_dir`` is ``None`` when not supplied.
    """
    parser = argparse.ArgumentParser(description="Backlog MCP server")
    parser.add_argument(
        "--project-dir",
        type=str,
        default=None,
        help=(
            "Absolute path to the user's project root. "
            "Required when installed as a plugin so BACKLOG_DIR resolves "
            "to the user's project rather than the plugin cache directory."
        ),
    )
    # parse_known_args prevents FastMCP/uvicorn arguments from causing errors
    namespace, _ = parser.parse_known_args(sys.argv[1:])
    return namespace


_args = _parse_args()
_init_models(_args.project_dir)

mcp = FastMCP(
    "backlog",
    instructions=(
        "Backlog management server. Manages per-item markdown files in .claude/backlog/, "
        "syncs with GitHub Issues (source of truth), and provides CRUD operations for "
        "backlog items including add, list, view, update, groom, close, resolve, and sync."
    ),
    version="0.1.0",
)


@mcp.tool
async def backlog_add(
    title: Annotated[str, Field(description="Item title")],
    priority: Annotated[str, Field(description="Priority level: P0, P1, P2, or Ideas")],
    description: Annotated[str, Field(description="Item description")],
    source: Annotated[str, Field(description="Where this item came from")] = "Not specified",
    type_: Annotated[
        str, Field(description="Item type: Feature, Bug, Refactor, Docs, or Chore", alias="type")
    ] = "Feature",
    create_issue: Annotated[bool, Field(description="Create a GitHub issue for this item")] = True,
    force: Annotated[bool, Field(description="Skip fuzzy duplicate check")] = False,
) -> dict:
    """Add a new item to the backlog. Creates a per-item file and optionally a GitHub issue.

    Use priority P0 for must-have, P1 for should-have, P2 for could-have,
    or Ideas for exploratory items.

    Returns:
        Dict with file_path, title, priority, issue number (if created),
        and output messages/warnings. On error, dict contains an error key.
    """
    out = Output()
    try:
        result = await asyncio.to_thread(
            operations.add_item,
            title=title,
            priority=priority,
            description=description,
            source=source,
            type_=type_,
            create_issue=create_issue,
            force=force,
            output=out,
        )
        return {**result, **out.to_dict()}
    except BacklogError as e:
        return {"error": str(e), **out.to_dict()}


@mcp.tool
async def backlog_list(
    from_github: Annotated[bool, Field(description="Refresh local cache from GitHub Issues before listing")] = False,
    label: Annotated[str | None, Field(description="Filter by GitHub label (e.g. 'priority:p1', 'type:bug')")] = None,
    section: Annotated[
        str | None, Field(description="Filter by priority section: P0, P1, P2, or Ideas (case-insensitive)")
    ] = None,
    status: Annotated[
        str | None, Field(description="Filter by status value e.g. 'needs-grooming', 'status:in-progress'")
    ] = None,
    title_filter: Annotated[
        str | None,
        Field(description="Filter items whose title contains this substring (case-insensitive)", alias="title"),
    ] = None,
    type_: Annotated[
        str | None,
        Field(
            description=(
                "Filter by metadata.type — case-insensitive exact match (e.g. 'Bug', 'Feature'). "
                "Items without metadata.type are excluded when this filter is active."
            ),
            alias="type",
        ),
    ] = None,
    topic: Annotated[
        str | None,
        Field(
            description=(
                "Filter by metadata.topic — case-insensitive substring match. "
                "Items without metadata.topic are excluded when this filter is active."
            )
        ),
    ] = None,
    include_closed: Annotated[
        bool, Field(description="Include items with closed/done/resolved status (excluded by default)")
    ] = False,
    search: Annotated[
        str | None,
        Field(
            description=(
                "Case-insensitive substring search across title, section, topic, and type simultaneously. "
                "Unlike title= which only matches the title field, search= matches any of these fields. "
                "Combine with other filters to narrow results further."
            )
        ),
    ] = None,
    offset: Annotated[
        int, Field(ge=0, description="Skip the first N items from the filtered result set (for pagination).")
    ] = 0,
    limit: Annotated[
        int,
        Field(
            ge=0,
            description=(
                "Maximum number of items to return. 0 = auto-paginate to stay within 4400 token budget "
                "(cl100k_base encoding). Caller can override with an explicit positive value."
            ),
        ),
    ] = 0,
) -> dict:
    """List all open backlog items.

    Use from_github=true to refresh the local cache from GitHub before listing.
    Use label to filter items by a specific GitHub label.
    Use section to filter by priority section (P0, P1, P2, Ideas).
    Use status to filter by status value (e.g. needs-grooming, status:in-progress).
    Use title to filter by title substring (case-insensitive).
    Use type_ to filter by metadata.type exact match (e.g. Bug, Feature).
    Use topic to filter by metadata.topic substring match.
    Use include_closed=true to include items with terminal status (done, resolved, closed).
    Use search to search across title, section, topic, and type simultaneously.
    Use offset and limit to paginate results. When limit=0, auto-pagination keeps the
    response under 4400 tokens (cl100k_base encoding). When has_more=true, call again
    with the offset shown in next_call.

    Returns:
        Dict with items list, count, pagination object, and output messages/warnings.
        Each item includes state (open/closed) and status (workflow status from status:* labels).
        pagination contains offset, limit, total, and has_more. When has_more=true,
        next_call provides the suggested follow-up call string.
        On error, dict contains an error key.
    """
    out = Output()
    try:
        result = await asyncio.to_thread(
            operations.list_items,
            from_github=from_github,
            label=label,
            section=section,
            status=status,
            title=title_filter,
            type_=type_,
            topic=topic,
            include_closed=include_closed,
            output=out,
        )
    except BacklogError as e:
        return {"error": str(e), **out.to_dict()}

    # "items" holds list[dict[str, str | bool]] per operations.list_items return type.
    # cast() narrows from the heterogeneous value union (int | list[str] | list[dict[...]]).
    all_items = cast("list[dict[str, str | bool]]", result.get("items", []))

    # Apply cross-field search filter when requested.
    if search is not None:
        needle = search.casefold()
        filtered: list[dict] = []
        for item in all_items:
            haystack = " ".join(
                str(item.get(field, "") or "") for field in ("title", "section", "topic", "type")
            ).casefold()
            if needle in haystack:
                filtered.append(item)
        all_items = filtered

    total = len(all_items)

    # Determine effective page limit.
    if limit > 0:
        # Caller requested an explicit limit — honour it exactly.
        effective_limit = limit
    else:
        # Auto-paginate: binary-search for the largest slice that fits the budget.
        # Start with all items and halve until the token count fits.
        candidate = all_items[offset:]
        effective_limit = len(candidate)
        while effective_limit > 1:
            token_count = len(_enc.encode(_json.dumps(candidate[:effective_limit])))
            if token_count <= _LIST_TOKEN_BUDGET:
                break
            effective_limit = max(1, effective_limit // 2)

    page_items = all_items[offset : offset + effective_limit]
    has_more = (offset + effective_limit) < total
    next_offset = offset + effective_limit

    pagination: dict = {"offset": offset, "limit": effective_limit, "total": total, "has_more": has_more}
    response: dict = {
        **result,
        "items": page_items,
        "count": len(page_items),
        "pagination": pagination,
        **out.to_dict(),
    }
    if has_more:
        response["next_call"] = f"backlog_list(offset={next_offset}, limit={effective_limit})"
    return response


@mcp.tool
async def backlog_view(
    selector: Annotated[str, Field(description="Item selector: GitHub issue URL, #N, bare number, or title substring")],
    include_content: Annotated[
        bool,
        Field(
            description="When True (default), returns full body and section entries. When False, returns metadata and section inventory only (section names with entry counts, no body or entry content)."
        ),
    ] = True,
    offset: Annotated[int, Field(ge=0, description="Skip N entry blocks from body start (for pagination)")] = 0,
    limit: Annotated[int, Field(ge=0, description="Show at most N entry blocks (0 = all, no truncation)")] = 0,
    show: Annotated[
        str | None,
        Field(description="Entry filter: 'all', 'last', 'first', 'struck', or integer N (first N active entries)"),
    ] = None,
    since: Annotated[
        str | None, Field(description="ISO date/datetime. Only entries at or after this timestamp are included.")
    ] = None,
) -> dict:
    """View a single backlog item or GitHub issue in detail.

    Accepts a GitHub issue URL, #N, bare number, or title substring as selector.
    Use offset and limit to paginate long issue bodies.
    Use show and since to filter entry blocks within sections.
    Use include_content=False to get a compact response with section names and
    entry counts only, omitting the full body and entry content.

    Returns:
        Dict with title, priority, issue, plan, file_path, body, sections
        metadata, and output messages/warnings. On error, dict contains an
        error key. When include_content=False, body and sections are omitted
        and sections_metadata (list of section name/count dicts) is included.
    """
    out = Output()
    try:
        # MCP tool parameters are always strings; convert numeric show values to int.
        parsed_show: str | int | None = show
        if show is not None:
            try:
                parsed_show = int(show)
            except ValueError:
                parsed_show = show
        result = await asyncio.to_thread(
            operations.view_item,
            selector=selector,
            include_content=include_content,
            offset=offset,
            limit=limit,
            show=parsed_show,
            since=since,
            output=out,
        )
        return {**result, **out.to_dict()}
    except BacklogError as e:
        return {"error": str(e), **out.to_dict()}


@mcp.tool
async def backlog_sync(
    ctx: Context,
    dry_run: Annotated[bool, Field(description="Preview what would be synced without making changes")] = False,
) -> dict:
    """Sync backlog items with GitHub: create missing issues and push groomed content.

    Use dry_run=true to preview changes without modifying anything.

    Returns:
        Dict with created and pushed counts and output messages/warnings.
        On error, dict contains an error key.
    """
    out = Output()
    try:
        await ctx.info("Starting backlog sync" + (" (dry-run)" if dry_run else ""))
        result = await asyncio.to_thread(operations.sync_items, dry_run=dry_run, output=out)
        for w in out.warnings:
            await ctx.warning(w)
        created = result.get("created", 0)
        pushed = result.get("pushed", 0)
        await ctx.info(f"Sync complete: {created} issue(s) created, {pushed} item(s) pushed")
        return {**result, **out.to_dict()}
    except BacklogError as e:
        return {"error": str(e), **out.to_dict()}


@mcp.tool
async def backlog_close(
    selector: Annotated[str, Field(description="Item selector: title substring, #N, bare number, or GitHub issue URL")],
    reason: Annotated[
        str,
        Field(
            description="Why the item is being dismissed. One of: duplicate, out_of_scope, superseded, wontfix, blocked"
        ),
    ],
    reference: Annotated[
        str, Field(description="Related item reference: #N, URL, or title of the item this duplicates/is superseded by")
    ] = "",
    comment: Annotated[str, Field(description="Additional context about why this item is being closed")] = "",
    cleanup: Annotated[
        bool, Field(description="Remove local file after close; index link becomes GitHub issue URL")
    ] = False,
    force: Annotated[bool, Field(description="Close even if open PRs reference the issue")] = False,
) -> dict:
    """Dismiss a backlog item without completing it and close its GitHub issue.

    Use for items that are duplicates, out of scope, superseded, wontfix,
    or permanently blocked. For completed work, use backlog_resolve instead.

    Returns:
        Dict with closed item title, reason, and output messages/warnings.
        On error, dict contains an error key.
    """
    out = Output()
    try:
        result = await asyncio.to_thread(
            operations.close_item,
            selector=selector,
            reason=reason,
            reference=reference,
            comment=comment,
            cleanup=cleanup,
            force=force,
            output=out,
        )
        return {**result, **out.to_dict()}
    except BacklogError as e:
        return {"error": str(e), **out.to_dict()}


@mcp.tool
async def backlog_resolve(
    selector: Annotated[str, Field(description="Item selector: title substring, #N, bare number, or GitHub issue URL")],
    summary: Annotated[str, Field(description="What was done — 1-2 sentence completion summary (required)")],
    plan: Annotated[str | None, Field(description="Plan path or completion reference")] = None,
    method: Annotated[str | None, Field(description="How the work was done — approach taken")] = None,
    notes: Annotated[str | None, Field(description="Problems found, surprises, or other comments")] = None,
    follow_ups: Annotated[str | None, Field(description="Created follow-up tickets (comma-separated refs)")] = None,
    findings: Annotated[str | None, Field(description="Retrospective learnings from this work")] = None,
    cleanup: Annotated[
        bool, Field(description="Remove local file after resolve; index link becomes GitHub issue URL")
    ] = False,
    force: Annotated[bool, Field(description="Resolve even if open PRs reference the issue")] = False,
) -> dict:
    """Mark a backlog item as DONE (completed) and close its GitHub issue.

    Creates a structured completion record as an audit/retrospective trail.
    Only summary is required — for trivial items a one-liner suffices.
    For dismissals (duplicate, out of scope, etc.), use backlog_close instead.

    Returns:
        Dict with resolved item title, summary, and output messages/warnings.
        On error, dict contains an error key.
    """
    out = Output()
    try:
        result = await asyncio.to_thread(
            operations.resolve_item,
            selector=selector,
            summary=summary,
            plan=plan or "",
            method=method or "",
            notes=notes or "",
            follow_ups=follow_ups or "",
            findings=findings or "",
            cleanup=cleanup,
            force=force,
            output=out,
        )
        return {**result, **out.to_dict()}
    except BacklogError as e:
        return {"error": str(e), **out.to_dict()}


@mcp.tool
async def backlog_update(
    selector: Annotated[str, Field(description="Item selector: title substring, #N, bare number, or GitHub issue URL")],
    plan: Annotated[str | None, Field(description="Path to a plan file to attach to the item")] = None,
    status: Annotated[
        str | None,
        Field(description="Set item status (e.g. 'in-progress'). Updates GitHub issue labels when applicable."),
    ] = None,
    create_issue: Annotated[
        bool, Field(description="Create a GitHub issue for this item if it lacks one (P0/P1 items only)")
    ] = False,
    section: Annotated[
        str | None, Field(description="Section name for groomed content update (use with content parameter)")
    ] = None,
    content: Annotated[
        str | None, Field(description="Content for the named section (use with section parameter)")
    ] = None,
    title: Annotated[
        str | None,
        Field(
            description="New title for the item. Updates the local file name field and GitHub issue title if the item already has a linked issue."
        ),
    ] = None,
    description: Annotated[
        str | None,
        Field(description="New description text for the item. Updates the local file only — no GitHub sync."),
    ] = None,
    entry_id: Annotated[
        str | None, Field(description="Timestamp ID of an existing entry to replace within the section")
    ] = None,
    replace_section: Annotated[
        bool, Field(description="Strike all existing entries in the section and append new content")
    ] = False,
    reason: Annotated[
        str | None, Field(description="Reason for striking entries (required when replace_section=True)")
    ] = None,
    verified: Annotated[
        bool,
        Field(
            description="Apply status:verified label to the GitHub issue. "
            "Signals that /complete-implementation quality gates have passed. "
            "Auto-creates the label if absent. No-op when item has no issue number."
        ),
    ] = False,
) -> dict:
    """Update a backlog item: attach a plan, set status, create a GitHub issue, or write groomed content.

    For groomed content, provide section + content for section updates.
    Use entry_id to replace a specific entry, or replace_section=True to
    strike all entries and append new content. Groomed content is synced
    to the GitHub issue when the item has one.

    Use verified=True after /complete-implementation quality gates pass to
    apply the status:verified label to the linked GitHub issue.

    Returns:
        Dict with updated item title, applied changes, and output
        messages/warnings. On error, dict contains an error key.
    """
    out = Output()
    try:
        result = await asyncio.to_thread(
            operations.update_item,
            selector=selector,
            plan=plan,
            status=status,
            create_issue=create_issue,
            section=section,
            content=content,
            title=title,
            description=description,
            output=out,
            entry_id=entry_id,
            replace_section=replace_section,
            reason=reason,
            verified=verified,
        )
        return {**result, **out.to_dict()}
    except BacklogError as e:
        return {"error": str(e), **out.to_dict()}


@mcp.tool
async def backlog_groom(
    ctx: Context,
    selector: Annotated[str, Field(description="Item selector: title substring, #N, bare number, or GitHub issue URL")],
    section: Annotated[
        str | None, Field(description="Section name for incremental update (use with content parameter)")
    ] = None,
    content: Annotated[
        str | None, Field(description="Content for the named section (use with section parameter)")
    ] = None,
    entry_id: Annotated[
        str | None, Field(description="Timestamp ID of an existing entry to replace within the section")
    ] = None,
    replace_section: Annotated[
        bool, Field(description="Strike all existing entries in the section and append new content")
    ] = False,
    reason: Annotated[
        str | None, Field(description="Reason for striking entries (required when replace_section=True)")
    ] = None,
    append: Annotated[
        bool,
        Field(
            description=(
                "When True and section is provided, append new content after existing section content "
                "(newline-separated) instead of replacing it. No entry-block wrapping is applied. "
                "Use this to incrementally add lines to a section such as ## Concerns."
            )
        ),
    ] = False,
) -> dict:
    """Write groomed content into a backlog item's per-item file and sync to its GitHub issue.

    Provide section + content for section updates. Use entry_id to replace
    a specific entry, or replace_section=True to strike all entries and
    append new content. Set append=True to add content after existing section
    text without entry-block wrapping. When the item has a GitHub issue, the
    groomed content is synced there automatically.

    Returns:
        Dict with groomed item title, synced status, and output
        messages/warnings. On error, dict contains an error key.
    """
    out = Output()
    try:
        await ctx.info(f"Grooming item: {selector}")
        result = await asyncio.to_thread(
            operations.groom_item,
            selector=selector,
            section=section,
            content=content,
            output=out,
            entry_id=entry_id,
            replace_section=replace_section,
            reason=reason,
            append=append,
        )
        for w in out.warnings:
            await ctx.warning(w)
        title = result.get("title", selector)
        await ctx.info(f"Groomed: {title}")
        return {**result, **out.to_dict()}
    except BacklogError as e:
        return {"error": str(e), **out.to_dict()}


@mcp.tool
async def backlog_normalize(
    ctx: Context,
    dry_run: Annotated[bool, Field(description="Preview normalization changes without modifying files")] = False,
) -> dict:
    """Normalize all per-item files to research-style metadata format and remove body duplication.

    This is a one-off maintenance operation. Use dry_run=true to preview
    what would change.

    Returns:
        Dict with count of normalized files and output messages/warnings.
        On error, dict contains an error key.
    """
    out = Output()
    try:
        await ctx.info("Starting normalize" + (" (dry-run)" if dry_run else ""))
        result = await asyncio.to_thread(operations.normalize_items, dry_run=dry_run, output=out)
        for w in out.warnings:
            await ctx.warning(w)
        updated = result.get("updated", 0)
        suffix = " (dry-run)" if dry_run else ""
        await ctx.info(f"Normalized {updated} file(s){suffix}")
        return {**result, **out.to_dict()}
    except BacklogError as e:
        return {"error": str(e), **out.to_dict()}


@mcp.tool
async def backlog_pull(
    ctx: Context,
    selector: Annotated[
        str | None,
        Field(
            description="Optional selector to pull a single issue: #N, bare number, GitHub URL, or title substring. When omitted, pulls all issues."
        ),
    ] = None,
    dry_run: Annotated[bool, Field(description="Preview what would be pulled without modifying local files")] = False,
    force: Annotated[
        bool, Field(description="Overwrite local content even if local version is newer or longer")
    ] = False,
    diff: Annotated[bool, Field(description="Include entry-level diff output showing local vs remote changes")] = False,
) -> dict:
    """Pull issue body content from GitHub into local per-item files.

    When selector is provided, pulls a single issue by #N, bare number,
    GitHub URL, or title substring. When omitted, pulls all issues.

    Auto-migrates P0/P1 items lacking GitHub Issues by creating them.
    Merges by section using entry-aware merge (keeps longer entries,
    preserves strikes). Use dry_run=true to preview changes.
    Use diff=true to include entry-level diff output.

    Returns:
        Dict with count of pulled items (bulk) or file_path (single) and
        output messages/warnings. On error, dict contains an error key.
    """
    out = Output()
    try:
        if selector is not None:
            await ctx.info(f"Pulling issue: {selector}")
            result = await asyncio.to_thread(operations.pull_by_selector, selector, diff=diff, output=out)
            for w in out.warnings:
                await ctx.warning(w)
            file_path = result.get("file_path")
            await ctx.info(f"Pulled: {file_path}" if file_path else "Nothing pulled")
            return {**result, **out.to_dict()}
        await ctx.info("Starting bulk pull from GitHub" + (" (dry-run)" if dry_run else ""))
        result = await asyncio.to_thread(operations.pull_items, dry_run=dry_run, force=force, diff=diff, output=out)
        for w in out.warnings:
            await ctx.warning(w)
        pulled = result.get("pulled", 0)
        await ctx.info(f"Pull complete: {pulled} item(s) pulled")
        return {**result, **out.to_dict()}
    except BacklogError as e:
        return {"error": str(e), **out.to_dict()}


@mcp.tool
async def backlog_create_sam_task(
    parent_issue_number: Annotated[int, Field(description="Parent story issue number (without #)")],
    task_id: Annotated[str, Field(description="Feature-scoped task ID, e.g. 'T1'")],
    feature: Annotated[str, Field(description="Feature slug, e.g. 'my-feature'")],
    task_type: Annotated[str, Field(description="Task category: research | implement | review | fix | docs")],
    agent: Annotated[str, Field(description="Agent name to execute this task")],
    priority: Annotated[int, Field(description="Priority 1-5 (1=highest)")] = 2,
    skills: Annotated[list[str], Field(description="Skill names for the executing agent")] = [],  # noqa: B006
    dependencies: Annotated[list[str], Field(description="Task IDs this task depends on")] = [],  # noqa: B006
    description: Annotated[str, Field(description="Human-readable description of the task")] = "",
    acceptance_criteria: Annotated[list[str] | None, Field(description="Acceptance criteria strings")] = None,
    labels: Annotated[list[str] | None, Field(description="GitHub label names to apply")] = None,
) -> dict:
    """Create a GitHub sub-issue for a SAM task under a parent story issue.

    Use to bootstrap GitHub visibility for a task when starting a new feature plan.

    Returns:
        Dict with issue_number, title, url, and output messages. On error, returns error key.
    """
    out = Output()
    try:
        result = await asyncio.to_thread(
            operations.create_sam_task,
            parent_issue_number=parent_issue_number,
            task_id=task_id,
            feature=feature,
            task_type=task_type,
            agent=agent,
            priority=priority,
            skills=skills,
            dependencies=dependencies,
            description=description,
            acceptance_criteria=acceptance_criteria,
            labels=labels,
            output=out,
        )
        return {**result, **out.to_dict()}
    except BacklogError as e:
        return {"error": str(e), **out.to_dict()}


@mcp.tool
async def backlog_get_sam_tasks(
    parent_issue_number: Annotated[int, Field(description="Parent story issue number (without #)")],
    refresh_cache: Annotated[bool, Field(description="Write updated cache after fetching")] = True,
) -> dict:
    """Return all SAM task sub-issues for a parent story issue.

    Returns tasks list with SamTask fields plus issue_number and issue_url.
    Falls back to local cache if GitHub is unavailable.
    Use to inspect per-task status from the GitHub source of truth.
    """
    out = Output()
    try:
        result = await asyncio.to_thread(
            operations.get_sam_tasks, parent_issue_number=parent_issue_number, refresh_cache=refresh_cache, output=out
        )
        return {**result, **out.to_dict()}
    except BacklogError as e:
        return {"error": str(e), **out.to_dict()}


@mcp.tool
async def backlog_update_sam_task_status(
    issue_number: Annotated[int, Field(description="Task sub-issue number (without #)")],
    new_status: Annotated[str, Field(description="Target status: not-started | in-progress | complete | blocked")],
) -> dict:
    """Update the status field in a SAM task sub-issue.

    Patches the sam:task YAML block in the issue body. No-op if status already matches.

    Returns:
        Dict with updated (bool), issue_number, new_status, and output messages.
        On error, returns error key.
    """
    out = Output()
    try:
        result = await asyncio.to_thread(
            operations.update_sam_task_status, issue_number=issue_number, new_status=new_status, output=out
        )
        return {**result, **out.to_dict()}
    except BacklogError as e:
        return {"error": str(e), **out.to_dict()}


# ---------------------------------------------------------------------------
# Artifact manifest tools
# ---------------------------------------------------------------------------

_artifact_registry = ArtifactRegistry()
_artifact_provider: GitHubArtifactProvider | None = None


def _require_artifact_entries(entries: list, label: str) -> None:
    """Raise BacklogError when no artifact entries are found.

    Args:
        entries: List of artifact entries (may be empty).
        label: Error message to include in the exception.

    Raises:
        BacklogError: When ``entries`` is empty.
    """
    if not entries:
        raise BacklogError(label)


def _get_artifact_provider() -> GitHubArtifactProvider:
    """Return (or lazily create) the GitHubArtifactProvider singleton.

    Deferred so the provider is created after ``_init_models()`` has resolved
    the repo slug and project root from the ``--project-dir`` argument.

    Returns:
        Initialised ``GitHubArtifactProvider`` instance.

    Raises:
        GitHubUnavailableError: When GitHub credentials or repo slug are missing.
    """
    global _artifact_provider  # noqa: PLW0603
    if _artifact_provider is None:
        repo = _models.DEFAULT_REPO
        if not repo:
            raise GitHubUnavailableError("DEFAULT_REPO not set — GitHub credentials or repo slug missing")
        _artifact_provider = GitHubArtifactProvider(
            repo=repo,
            root_worktree=_models._REPO_ROOT,  # noqa: SLF001
        )
    return _artifact_provider


@mcp.tool
async def artifact_register(
    issue_number: Annotated[int, Field(description="GitHub issue number")],
    artifact_type: Annotated[
        str,
        Field(
            description=(
                "Artifact type: feature-context, architect, task-plan, T0-baseline, TN-verification, "
                "codebase-analysis, research"
            )
        ),
    ],
    path: Annotated[str, Field(description="Relative path from repo root, e.g. plan/architect-foo.md")],
    status: Annotated[str, Field(description="Lifecycle status: draft, current, superseded, archived")] = "current",
    agent: Annotated[str, Field(description="Name of the producing agent")] = "",
    content: Annotated[
        str | None,
        Field(
            description=(
                "Optional artifact content to store as a GitHub issue comment. "
                "When provided the content is stored in a collapsible comment identified by type+path. "
                "When omitted only the manifest entry is registered (backward-compatible)."
            )
        ),
    ] = None,
) -> dict:
    """Upsert an artifact entry in the manifest for a GitHub issue.

    Idempotent by (artifact_type, path). If an entry with the same type and
    path already exists it is updated in-place (status, agent, timestamp).
    If only the type matches but the path differs, a new row is added.

    Content upload follows three-tier resolution:

    1. **Explicit content** — when *content* is provided, it is uploaded
       directly to a structured GitHub issue comment so it can be retrieved
       via ``artifact_read`` even from worktree-isolated agents.
    2. **Auto-read from local file** — when *content* is ``None`` but a local
       file exists at *path* (resolved against the root worktree), the file is
       read automatically and uploaded as in tier 1.
    3. **Manifest-only** — when *content* is ``None`` and no local file exists,
       the manifest entry is registered without content storage.  A warning is
       emitted so callers can detect the gap.

    Returns:
        Dict with registered (bool), artifact_count (int), action (str),
        content_stored (bool), and output messages/warnings. On error, dict
        contains an error key.
    """
    out = Output()
    try:
        provider = _get_artifact_provider()
        artifact_type_enum = ArtifactType(artifact_type)
        status_enum = ArtifactStatus(status)
        entry = ArtifactEntry(
            artifact_type=artifact_type_enum,
            path=path,
            status=status_enum,
            created_at=_datetime.now(UTC).isoformat(),
            agent=agent,
        )

        def _run() -> RegisterResult:
            manifest = provider.get_manifest(issue_number)
            updated_manifest = _artifact_registry.register(manifest, entry)
            provider.set_manifest(issue_number, updated_manifest)
            # Determine action: "updated" if entry pre-existed, "added" otherwise.
            existed = any(e.artifact_type == artifact_type_enum and e.path == path for e in manifest.artifacts)
            action = "updated" if existed else "added"

            # Content upload — three-way resolution:
            # 1. Explicit content provided → use it directly.
            # 2. No explicit content but local file exists → read and upload.
            # 3. Neither → register manifest entry only; emit a warning.
            upload_content: str | None = content
            if upload_content is None:
                upload_content = provider.read_local_artifact_content(path)
                if upload_content is None:
                    out.warn(
                        f"No content provided and no local file found at {path!r}. "
                        "Manifest entry registered without content storage."
                    )

            content_stored = False
            if upload_content is not None:
                provider.store_artifact_content(issue_number, artifact_type, path, upload_content)
                content_stored = True

            return RegisterResult(
                registered=True,
                artifact_count=len(updated_manifest.artifacts),
                action=action,
                content_stored=content_stored,
            )

        result = await asyncio.to_thread(_run)
        return {**result.model_dump(), **out.to_dict()}
    except (ValueError, KeyError) as e:
        return {"error": f"Invalid parameter: {e}", **out.to_dict()}
    except BacklogError as e:
        return {"error": str(e), **out.to_dict()}


@mcp.tool
async def artifact_list(
    issue_number: Annotated[int, Field(description="GitHub issue number")],
    artifact_type: Annotated[str | None, Field(description="Filter by artifact type (optional)")] = None,
) -> dict:
    """Return all artifacts registered for a GitHub issue.

    Optionally filter by artifact type. Returns an empty list when no
    manifest section exists yet — this is not an error.

    Returns:
        Dict with artifacts (list of dicts), count (int), and output
        messages/warnings. On error, dict contains an error key.
    """
    out = Output()
    try:
        provider = _get_artifact_provider()
        type_filter: ArtifactType | None = ArtifactType(artifact_type) if artifact_type else None

        def _run() -> list[dict]:
            manifest = provider.get_manifest(issue_number)
            if type_filter is not None:
                entries = _artifact_registry.get_by_type(manifest, type_filter)
            else:
                entries = manifest.artifacts
            return [e.model_dump(mode="json") for e in entries]

        artifacts = await asyncio.to_thread(_run)
        return {"artifacts": artifacts, "count": len(artifacts), **out.to_dict()}
    except (ValueError, KeyError) as e:
        return {"error": f"Invalid parameter: {e}", **out.to_dict()}
    except BacklogError as e:
        return {"error": str(e), **out.to_dict()}


@mcp.tool
async def artifact_get(
    issue_number: Annotated[int, Field(description="GitHub issue number")],
    artifact_type: Annotated[str, Field(description="Artifact type to retrieve")],
) -> dict:
    """Return metadata for a specific artifact type registered on a GitHub issue.

    If multiple artifacts of the same type exist (e.g. multiple
    codebase-analysis files), all are returned.

    Returns:
        Dict with artifacts (list of dicts), count (int), and output
        messages/warnings. Returns error key when type is not found.
    """
    out = Output()
    try:
        provider = _get_artifact_provider()
        type_enum = ArtifactType(artifact_type)

        def _run() -> list[dict]:
            manifest = provider.get_manifest(issue_number)
            entries = _artifact_registry.get_by_type(manifest, type_enum)
            return [e.model_dump(mode="json") for e in entries]

        artifacts = await asyncio.to_thread(_run)
        if not artifacts:
            return {"error": f"No artifacts of type '{artifact_type}' found for issue #{issue_number}", **out.to_dict()}
        return {"artifacts": artifacts, "count": len(artifacts), **out.to_dict()}
    except (ValueError, KeyError) as e:
        return {"error": f"Invalid parameter: {e}", **out.to_dict()}
    except BacklogError as e:
        return {"error": str(e), **out.to_dict()}


@mcp.tool
async def artifact_read(
    issue_number: Annotated[int, Field(description="GitHub issue number")],
    artifact_type: Annotated[str, Field(description="Artifact type whose content to read")],
) -> dict:
    """Read the file content for an artifact registered on a GitHub issue.

    Content retrieval order:

    1. GitHub issue comments — searches for a stored artifact content comment
       matching the artifact type and path.  This succeeds even when the local
       filesystem file does not exist (e.g. from a worktree-isolated agent).
    2. Local filesystem fallback — when no GitHub comment is found, resolves
       the artifact path against the root worktree.

    Path safety (filesystem path): the provider validates that the resolved
    path is under the repository root (path traversal prevention).

    Returns:
        Dict with type (str), path (str), content (str), status (str), and
        output messages/warnings. Returns error key on type-not-found, path
        safety violation, or when content is not found via either source.
    """
    out = Output()
    try:
        provider = _get_artifact_provider()
        type_enum = ArtifactType(artifact_type)

        def _run() -> ArtifactContent:
            manifest = provider.get_manifest(issue_number)
            entries = _artifact_registry.get_by_type(manifest, type_enum)
            _require_artifact_entries(
                entries, f"No artifacts of type '{artifact_type}' found for issue #{issue_number}"
            )
            # Use the first (most recent) entry.
            entry = entries[0]

            # 1. Try GitHub comment storage first.
            github_content = provider.read_artifact_content_from_github(issue_number, artifact_type, entry.path)
            if github_content is not None:
                return ArtifactContent(
                    artifact_type=entry.artifact_type, path=entry.path, content=github_content, status=entry.status
                )

            # 2. Fall back to local filesystem.
            content = provider.read_artifact_content(entry.path)
            return ArtifactContent(
                artifact_type=entry.artifact_type, path=entry.path, content=content, status=entry.status
            )

        result = await asyncio.to_thread(_run)
        return {**result.model_dump(mode="json"), **out.to_dict()}
    except (ValueError, KeyError) as e:
        return {"error": f"Invalid parameter: {e}", **out.to_dict()}
    except BacklogError as e:
        return {"error": str(e), **out.to_dict()}


@mcp.tool
async def backlog_get_ready_sam_tasks(
    parent_issue_number: Annotated[int, Field(description="Parent story issue number (without #)")],
) -> dict:
    """Return SAM tasks ready for execution from GitHub sub-issues.

    Fetches sub-issues, resolves dependency graph locally, returns tasks whose
    status is not-started and all dependencies are terminal.
    Output shape matches implementation_manager.py ready-tasks JSON:
    feature, ready_tasks, count. Each ready_task includes id, name, agent, skills, issue_number.
    Falls back to local cache if GitHub is unavailable.
    """
    out = Output()
    try:
        result = await asyncio.to_thread(
            operations.get_ready_sam_tasks, parent_issue_number=parent_issue_number, output=out
        )
        return {**result, **out.to_dict()}
    except BacklogError as e:
        return {"error": str(e), **out.to_dict()}


@mcp.tool
async def backlog_strike_entry(
    selector: Annotated[str, Field(description="Item selector: title substring, #N, bare number, or GitHub issue URL")],
    entry_id: Annotated[str, Field(description="Timestamp ID of the entry to strike")],
    reason: Annotated[str, Field(description="Human-readable reason for striking the entry")],
    section: Annotated[str | None, Field(description="Optional section name to scope the search within")] = None,
) -> dict:
    """Strike (retract) an entry block within a backlog item.

    Wraps the entry in a collapsed details block with the reason,
    preserving the original content for audit. Syncs to GitHub issue
    if the item has one.

    Returns:
        Dict with strike results and output messages/warnings.
        On error, dict contains an error key.
    """
    out = Output()
    try:
        result = await asyncio.to_thread(
            operations.strike_entry, selector=selector, entry_id=entry_id, reason=reason, section=section, output=out
        )
        return {**result, **out.to_dict()}
    except BacklogError as e:
        return {"error": str(e), **out.to_dict()}


@mcp.tool
async def backlog_list_labels(limit: Annotated[int, Field(description="Maximum labels to return")] = 100) -> dict:
    """List repository labels (read-only).

    Returns all labels defined on the repository, up to ``limit``.
    Label mutations are not supported by this tool; they are owned by
    the state transition handler.

    Returns:
        Dict with ``labels`` (list of dicts with ``name``, ``color``, ``description``),
        ``count``, and output messages/warnings.
        On error, dict contains an ``error`` key.
    """
    out = Output()
    try:
        result = await asyncio.to_thread(operations.list_labels, limit=limit, output=out)
        return {**result, **out.to_dict()}
    except BacklogError as e:
        return {"error": str(e), **out.to_dict()}


@mcp.tool
async def backlog_list_merged_prs(
    search: Annotated[
        str | None,
        Field(
            description=(
                "Optional substring to filter by (checked against PR title and body, "
                "case-insensitive). Use to find PRs related to a specific issue number "
                "(e.g. '#42') or keyword."
            )
        ),
    ] = None,
    limit: Annotated[int, Field(description="Maximum number of PRs to return")] = 20,
) -> dict:
    """List merged pull requests, optionally filtered by a search query.

    Only PRs that were actually merged (not just closed) are returned.
    Use ``search`` to filter by issue reference (e.g. ``'#42'``) or any
    keyword present in the PR title or body.

    Returns:
        Dict with ``pull_requests`` (list of dicts with ``number``,
        ``title``, ``merged_at``, ``author``, ``url``, ``head_branch``),
        ``count``, and output messages/warnings.
        On error, dict contains an ``error`` key.
    """
    out = Output()
    try:
        result = await asyncio.to_thread(operations.list_merged_prs, search=search, limit=limit, output=out)
        return {**result, **out.to_dict()}
    except BacklogError as e:
        return {"error": str(e), **out.to_dict()}


@mcp.tool
async def backlog_list_milestones(
    state: Annotated[str, Field(description="Milestone state filter: open | closed | all")] = "open",
) -> dict:
    """List repository milestones filtered by state.

    Returns milestones with their issue counts and optional due dates.

    Returns:
        Dict with ``milestones`` (list of dicts with ``number``, ``title``,
        ``state``, ``description``, ``due_on``, ``open_issues``,
        ``closed_issues``), ``count``, and output messages/warnings.
        On error, dict contains an ``error`` key.
    """
    out = Output()
    try:
        result = await asyncio.to_thread(operations.list_milestones, state=state, output=out)
        return {**result, **out.to_dict()}
    except BacklogError as e:
        return {"error": str(e), **out.to_dict()}


@mcp.tool
async def backlog_get_soonest_milestone() -> dict:
    """Return the open milestone with the earliest due date.

    Milestones without a due date are excluded. If all open milestones
    lack a due date, the first one by GitHub's default ordering is returned
    with a warning.

    Returns:
        Dict with ``milestone`` (dict or None) containing ``number``, ``title``,
        ``state``, ``description``, ``due_on``, ``open_issues``,
        ``closed_issues``, and output messages/warnings.
        ``milestone`` is ``None`` when no open milestones exist.
        On error, dict contains an ``error`` key.
    """
    out = Output()
    try:
        result = await asyncio.to_thread(operations.get_soonest_milestone, output=out)
        return {**result, **out.to_dict()}
    except BacklogError as e:
        return {"error": str(e), **out.to_dict()}


@mcp.tool
async def backlog_create_milestone(
    title: Annotated[str, Field(description="Milestone title (required, must be non-empty)")],
    description: Annotated[str, Field(description="Optional milestone description")] = "",
    due_on: Annotated[
        str | None,
        Field(description="Optional due date as ISO 8601 string, e.g. '2026-06-30' or '2026-06-30T00:00:00Z'"),
    ] = None,
) -> dict:
    """Create a new milestone on the repository.

    Returns:
        Dict with ``milestone`` containing ``number``, ``title``, ``state``,
        ``description``, ``due_on``, ``open_issues``, ``closed_issues``,
        and output messages/warnings.
        On error, dict contains an ``error`` key.
    """
    out = Output()
    try:
        result = await asyncio.to_thread(
            operations.create_milestone, title=title, description=description, due_on=due_on, output=out
        )
        return {**result, **out.to_dict()}
    except BacklogError as e:
        return {"error": str(e), **out.to_dict()}


@mcp.tool
async def backlog_list_issues(
    milestone: Annotated[str | None, Field(description="Filter by milestone title")] = None,
    labels: Annotated[str | None, Field(description="Comma-separated label names to filter by")] = None,
    state: Annotated[str, Field(description="Issue state: open, closed, or all")] = "open",
    limit: Annotated[int, Field(description="Maximum issues to return")] = 30,
) -> dict:
    """List GitHub issues with optional milestone, label, and state filters.

    Returns:
        Dict with issues list, count, and output messages/warnings.
        On error, dict contains an error key.
    """
    out = Output()
    try:
        result = await asyncio.to_thread(
            operations.list_issues, milestone=milestone, labels=labels, state=state, limit=limit, output=out
        )
        return {**result, **out.to_dict()}
    except BacklogError as e:
        return {"error": str(e), **out.to_dict()}


@mcp.tool
async def backlog_comment_issue(
    issue_number: Annotated[int, Field(description="GitHub issue number (without #)")],
    body: Annotated[str, Field(description="Comment body (Markdown)")],
) -> dict:
    """Add a comment to a GitHub issue.

    Returns:
        Dict with issue_number, comment_id, comment_url, and output messages/warnings.
        On error, dict contains an error key.
    """
    out = Output()
    try:
        result = await asyncio.to_thread(operations.comment_issue, issue_number=issue_number, body=body, output=out)
        return {**result, **out.to_dict()}
    except BacklogError as e:
        return {"error": str(e), **out.to_dict()}


@mcp.tool
async def backlog_list_projects(
    owner: Annotated[str | None, Field(description="GitHub owner (org or user). Defaults to repo owner")] = None,
    limit: Annotated[int, Field(description="Maximum projects to return")] = 20,
) -> dict:
    """List Projects V2 for the repository owner via GraphQL.

    Returns:
        Dict with projects list, count, and output messages/warnings.
        On error, dict contains an error key.
    """
    out = Output()
    try:
        result = await asyncio.to_thread(operations.list_projects, owner=owner, limit=limit, output=out)
        return {**result, **out.to_dict()}
    except BacklogError as e:
        return {"error": str(e), **out.to_dict()}


@mcp.tool
async def backlog_create_project(
    title: Annotated[str, Field(description="Project title")],
    owner: Annotated[str | None, Field(description="GitHub owner (org or user). Defaults to repo owner")] = None,
) -> dict:
    """Create a Projects V2 project under the repository owner.

    Resolves the owner node ID then runs the createProjectV2 GraphQL mutation.

    Returns:
        Dict with project_id, title, url, number, and output messages/warnings.
        On error, dict contains an error key.
    """
    out = Output()
    try:
        result = await asyncio.to_thread(operations.create_project, title=title, owner=owner, output=out)
        return {**result, **out.to_dict()}
    except BacklogError as e:
        return {"error": str(e), **out.to_dict()}


def _dispatch_plan_path(milestone_number: int) -> Path:
    """Return the canonical dispatch plan path for a milestone.

    Delegates to :func:`dispatch_schema.dispatch_plan_path`, resolving the
    project root from ``_models.BACKLOG_DIR``.

    Args:
        milestone_number: GitHub milestone number.

    Returns:
        Path to ``plan/milestone-{N}-dispatch.yaml`` under the project root.
    """
    # BACKLOG_DIR is <project_root>/.claude/backlog — walk up to project root
    return _ds.dispatch_plan_path(milestone_number, _models.BACKLOG_DIR.parent.parent)


@mcp.tool
async def dispatch_read(milestone_number: Annotated[int, Field(description="GitHub milestone number")]) -> dict:
    """Read a dispatch plan for the given milestone.

    Loads and returns the full plan as a dict. Returns an error dict if
    the plan file does not exist or fails YAML/schema validation.

    Returns:
        Dict with ``milestone_number``, ``plan_path``, and ``plan`` (full plan
        as a nested dict), or ``error`` on failure.
    """
    plan_path = _dispatch_plan_path(milestone_number)
    try:
        plan = await asyncio.to_thread(_ds.read_dispatch_plan, plan_path)
    except FileNotFoundError:
        return {
            "error": f"Dispatch plan not found: {plan_path}",
            "milestone_number": milestone_number,
            "plan_path": str(plan_path),
        }
    except ValueError as exc:
        return {"error": str(exc), "milestone_number": milestone_number, "plan_path": str(plan_path)}
    return {"milestone_number": milestone_number, "plan_path": str(plan_path), "plan": plan.model_dump()}


@mcp.tool
async def dispatch_validate(milestone_number: Annotated[int, Field(description="GitHub milestone number")]) -> dict:
    """Validate an existing dispatch plan's structural integrity.

    Reads the plan file then runs five structural checks: duplicate issues,
    conflict group references, depends_on existence, wave ordering, and
    conflict group wave placement.

    Returns:
        Dict with ``is_valid`` (bool), ``errors`` (list[str]), and
        ``warnings`` (list[str]), or ``error`` on file/parse failure.
    """
    plan_path = _dispatch_plan_path(milestone_number)
    try:
        plan = await asyncio.to_thread(_ds.read_dispatch_plan, plan_path)
    except (FileNotFoundError, ValueError) as exc:
        return {"error": str(exc), "milestone_number": milestone_number, "plan_path": str(plan_path)}
    result = await asyncio.to_thread(_ds.validate_plan_integrity, plan)
    return {"milestone_number": milestone_number, "plan_path": str(plan_path), **dataclasses.asdict(result)}


@mcp.tool
async def dispatch_stale_check(
    milestone_number: Annotated[int, Field(description="GitHub milestone number")],
    repo: Annotated[str, Field(description="Repository slug owner/name. Defaults to repo from project")] = "",
) -> dict:
    """Check whether a dispatch plan is stale relative to the current milestone.

    Fetches open issues assigned to the milestone from GitHub, compares
    their issue numbers against those in the plan, and returns a stale/fresh
    indicator with added/removed issue lists.

    Returns:
        Dict with ``is_stale`` (bool), ``added_issues`` (list[int]),
        ``removed_issues`` (list[int]), and ``message`` (str).
        Returns ``error`` on file/parse or GitHub failure.
    """
    plan_path = _dispatch_plan_path(milestone_number)
    try:
        plan = await asyncio.to_thread(_ds.read_dispatch_plan, plan_path)
    except (FileNotFoundError, ValueError) as exc:
        return {"error": str(exc), "milestone_number": milestone_number, "plan_path": str(plan_path)}

    def _fetch_milestone_issue_numbers() -> list[int]:
        gh_repo = _get_github(repo)
        ms_obj = gh_repo.get_milestone(milestone_number)
        return [
            issue.number for issue in gh_repo.get_issues(milestone=ms_obj, state="all") if issue.pull_request is None
        ]

    try:
        current_numbers = await asyncio.to_thread(_fetch_milestone_issue_numbers)
    except GitHubUnavailableError as exc:
        return {"error": str(exc), "milestone_number": milestone_number}
    except Exception as exc:  # noqa: BLE001
        return {"error": f"GitHub API error: {exc}", "milestone_number": milestone_number}

    result = await asyncio.to_thread(_ds.detect_stale_plan, plan, current_numbers)
    return {"milestone_number": milestone_number, "plan_path": str(plan_path), **dataclasses.asdict(result)}


@mcp.tool
async def dispatch_conflicts(
    milestone_number: Annotated[int, Field(description="GitHub milestone number")],
    repo: Annotated[str, Field(description="Repository slug owner/name. Defaults to repo from project")] = "",
) -> dict:
    """Analyze Impact Radius conflicts for items in a milestone.

    Fetches open issues for the milestone from GitHub, extracts the
    Impact Radius section from each issue body, then runs conflict analysis
    to find items that share file paths.

    Returns:
        Dict with ``conflict_groups`` (list of group dicts with group_id,
        reason, and items), ``count`` (int), and ``milestone_number``.
        Returns ``error`` on GitHub failure.
    """

    def _fetch_items_with_impact_radius() -> list[_ImpactRadiusItem]:
        gh_repo = _get_github(repo)
        ms_obj = gh_repo.get_milestone(milestone_number)
        items: list[_ImpactRadiusItem] = []
        ir_re = _re.compile(r"##\s+Impact\s+Radius\b(.*?)(?=\n##|\Z)", _re.IGNORECASE | _re.DOTALL)
        for issue in gh_repo.get_issues(milestone=ms_obj, state="open"):
            if issue.pull_request is not None:
                continue
            body = issue.body or ""
            match = ir_re.search(body)
            impact_radius = match.group(1).strip() if match else ""
            items.append({"title": issue.title, "issue": issue.number, "impact_radius": impact_radius})
        return items

    try:
        items = await asyncio.to_thread(_fetch_items_with_impact_radius)
    except GitHubUnavailableError as exc:
        return {"error": str(exc), "milestone_number": milestone_number}
    except Exception as exc:  # noqa: BLE001
        return {"error": f"GitHub API error: {exc}", "milestone_number": milestone_number}

    conflict_groups = await asyncio.to_thread(operations.analyze_impact_radius_conflicts, items)
    return {
        "milestone_number": milestone_number,
        "conflict_groups": [dataclasses.asdict(cg) for cg in conflict_groups],
        "count": len(conflict_groups),
    }


# ---------------------------------------------------------------------------
# artifact_migrate helpers
# ---------------------------------------------------------------------------

#: Lazily created YAML parser for migration helpers (preserve_quotes prevents
#: round-trip mutations when loading frontmatter).
_migrate_yaml: _YAML | None = None


def _get_migrate_yaml() -> _YAML:
    """Return (or lazily create) the shared YAML instance for migration.

    Returns:
        Configured ``YAML`` instance with ``preserve_quotes=True``.
    """
    global _migrate_yaml  # noqa: PLW0603
    if _migrate_yaml is None:
        _migrate_yaml = _YAML()
        _migrate_yaml.preserve_quotes = True
    return _migrate_yaml


#: Filename pattern → ArtifactType mapping (ordered — first match wins).
_MIGRATE_FILENAME_PATTERNS: list[tuple[_re.Pattern[str], ArtifactType]] = [
    (_re.compile(r"^feature-context-(.+)\.md$"), ArtifactType.FEATURE_CONTEXT),
    (_re.compile(r"^architect-(.+)\.md$"), ArtifactType.ARCHITECT),
    (_re.compile(r"^P\d+-(.+)\.yaml$"), ArtifactType.TASK_PLAN),
    (_re.compile(r"^T0-baseline-(.+)\.yaml$"), ArtifactType.T0_BASELINE),
    (_re.compile(r"^TN-verification-(.+)\.yaml$"), ArtifactType.TN_VERIFICATION),
]

#: Pattern matching markdown files in plan/codebase/ → codebase-analysis.
_MIGRATE_CODEBASE_PATTERN = _re.compile(r"^.+\.md$")


def _migrate_extract_issue(file_path: Path) -> int | None:
    """Read the ``issue`` field from YAML frontmatter or a bare YAML file.

    Args:
        file_path: Absolute path to the file.

    Returns:
        Integer issue number when found and parseable, ``None`` otherwise.
    """
    try:
        text = file_path.read_text(encoding="utf-8")
    except OSError:
        return None

    yaml = _get_migrate_yaml()
    raw_data: object = None
    if file_path.suffix in {".yaml", ".yml"}:
        try:
            raw_data = yaml.load(text)
        except Exception:  # noqa: BLE001
            return None
    else:
        fm_match = _re.match(r"^---\r?\n(.*?)\r?\n(?:---|\.\.\.)(?:\r?\n|$)", text, _re.DOTALL)
        if not fm_match:
            return None
        try:
            raw_data = yaml.load(fm_match.group(1))
        except Exception:  # noqa: BLE001
            return None

    if isinstance(raw_data, dict):
        return _migrate_coerce_issue(raw_data.get("issue"))
    return None


def _migrate_coerce_issue(value: object) -> int | None:
    """Coerce a YAML value to a positive integer issue number.

    Args:
        value: Raw value from YAML (may be int, str, or None).

    Returns:
        Positive integer, or ``None``.
    """
    if value is None:
        return None
    try:
        n = int(str(value))
    except (ValueError, TypeError):
        return None
    return n if n > 0 else None


def _migrate_slug_from_path(file_path: Path) -> str:
    r"""Extract the slug from a plan filename.

    Strips known prefixes and the file extension.

    Args:
        file_path: Path object for the plan file.

    Returns:
        Slug string (e.g. ``"my-feature"``).
    """
    name = file_path.stem
    for prefix in ("feature-context-", "architect-", "T0-baseline-", "TN-verification-"):
        if name.startswith(prefix):
            return name[len(prefix) :]
    p_match = _re.match(r"^P\d+-(.+)$", name)
    if p_match:
        return p_match.group(1)
    return name


def _migrate_find_issue_via_backlog(slug: str, backlog_items: list[dict]) -> int | None:
    """Match a slug against cached backlog items to find an issue number.

    Args:
        slug: Slug string extracted from the artifact filename.
        backlog_items: List of backlog item dicts (each has ``title``,
            ``number``, and optionally ``plan`` fields).

    Returns:
        Matched GitHub issue number, or ``None``.
    """
    slug_words = set(slug.replace("-", " ").replace("_", " ").lower().split())
    for item in backlog_items:
        title: str = item.get("title", "") or ""
        plan_path: str = item.get("plan", "") or ""
        issue_number = _migrate_coerce_issue(item.get("number"))
        if issue_number is None:
            continue
        if slug in plan_path:
            return issue_number
        title_words = set(title.replace("-", " ").replace("_", " ").lower().split())
        overlap = slug_words & title_words
        if len(overlap) >= max(1, len(slug_words) // 2):
            return issue_number
    return None


def _migrate_resolve_issue(file_path: Path, backlog_items: list[dict]) -> int | None:
    """Resolve the issue number for a file via frontmatter or slug fallback.

    Args:
        file_path: Absolute path to the artifact file.
        backlog_items: Pre-fetched backlog items for slug-based fallback.

    Returns:
        Resolved issue number, or ``None``.
    """
    issue = _migrate_extract_issue(file_path)
    if issue is None:
        slug = _migrate_slug_from_path(file_path)
        issue = _migrate_find_issue_via_backlog(slug, backlog_items)
    return issue


def _migrate_classify_plan_file(file_path: Path) -> ArtifactType | None:
    """Classify a plan file by its filename pattern.

    Args:
        file_path: Path to the file.

    Returns:
        Matching ``ArtifactType``, or ``None``.
    """
    name = file_path.name
    for pattern, artifact_type in _MIGRATE_FILENAME_PATTERNS:
        if pattern.match(name):
            return artifact_type
    return None


_MigrateCandidate = tuple[str, ArtifactType, int | None, str | None]

#: Return type for candidate discovery — (actionable candidates, filtered-out count).
_MigrateDiscoveryResult = tuple[list[_MigrateCandidate], int]


def _migrate_make_candidate(
    rel: str, atype: ArtifactType, issue: int | None, issue_filter: int | None
) -> _MigrateCandidate | None:
    """Build a candidate tuple, returning ``None`` when the file is filtered out.

    When ``issue_filter`` is set, candidates whose resolved issue does not
    match are excluded entirely (counted as filtered by the caller) rather
    than included as skipped entries.  This avoids building a 500-entry
    skipped list when a specific issue is requested.

    Args:
        rel: Repo-relative path string.
        atype: Resolved artifact type.
        issue: Resolved issue number or ``None``.
        issue_filter: When set, candidates not matching this issue are
            excluded (returns ``None``).

    Returns:
        ``(rel, atype, issue, skip_reason)`` tuple, or ``None`` when filtered.
    """
    if issue_filter is not None and (issue is None or issue != issue_filter):
        return None
    if issue is None:
        return (rel, atype, issue, "no issue number found")
    return (rel, atype, issue, None)


def _migrate_scan_codebase_dir(
    codebase_dir: Path, repo_root: Path, issue_filter: int | None, backlog_items: list[dict]
) -> _MigrateDiscoveryResult:
    """Scan ``plan/codebase/`` for markdown codebase-analysis files.

    Args:
        codebase_dir: Absolute path to the ``plan/codebase/`` directory.
        repo_root: Absolute path to the repository root.
        issue_filter: When set, non-matching files are counted but not
            included in the returned candidate list.
        backlog_items: Pre-fetched backlog items for slug-based fallback.

    Returns:
        Tuple of ``(candidates, filtered_count)``.
    """
    results: list[_MigrateCandidate] = []
    filtered = 0
    for child in codebase_dir.iterdir():
        if not (child.is_file() and _MIGRATE_CODEBASE_PATTERN.match(child.name)):
            continue
        rel = child.relative_to(repo_root).as_posix()
        issue = _migrate_resolve_issue(child, backlog_items)
        candidate = _migrate_make_candidate(rel, ArtifactType.CODEBASE_ANALYSIS, issue, issue_filter)
        if candidate is None:
            filtered += 1
        else:
            results.append(candidate)
    return results, filtered


def _migrate_scan_plan_dir(
    plan_dir: Path, repo_root: Path, issue_filter: int | None, backlog_items: list[dict]
) -> _MigrateDiscoveryResult:
    """Scan ``plan/`` (excluding subdirectories other than ``codebase/``).

    Args:
        plan_dir: Absolute path to the ``plan/`` directory.
        repo_root: Absolute path to the repository root.
        issue_filter: When set, non-matching files are counted but not
            included in the returned candidate list.
        backlog_items: Pre-fetched backlog items for slug-based fallback.

    Returns:
        Tuple of ``(candidates, filtered_count)``.
    """
    results: list[_MigrateCandidate] = []
    filtered = 0
    for file_path in plan_dir.iterdir():
        if file_path.is_dir():
            if file_path.name == "codebase":
                sub_results, sub_filtered = _migrate_scan_codebase_dir(
                    file_path, repo_root, issue_filter, backlog_items
                )
                results.extend(sub_results)
                filtered += sub_filtered
            continue
        if not file_path.is_file():
            continue
        atype = _migrate_classify_plan_file(file_path)
        if atype is None:
            continue
        rel = file_path.relative_to(repo_root).as_posix()
        issue = _migrate_resolve_issue(file_path, backlog_items)
        candidate = _migrate_make_candidate(rel, atype, issue, issue_filter)
        if candidate is None:
            filtered += 1
        else:
            results.append(candidate)
    return results, filtered


def _migrate_discover_candidates(
    repo_root: Path, issue_filter: int | None, backlog_items: list[dict]
) -> _MigrateDiscoveryResult:
    """Scan plan/ and research/ for artifact files.

    When ``issue_filter`` is set, only candidates linked to that issue are
    returned — non-matching files are counted in ``filtered_count`` instead
    of being included as skipped entries.  This prevents the caller from
    building a 500+ entry skipped list when a specific issue is requested.

    Args:
        repo_root: Absolute path to the repository root.
        issue_filter: When set, only candidates linked to this issue number
            are included in the returned list.
        backlog_items: Pre-fetched backlog items for slug-based fallback.

    Returns:
        Tuple of ``(candidates, filtered_count)`` where ``candidates`` is a
        list of ``(rel_path, artifact_type, issue_number, skip_reason)``
        tuples and ``filtered_count`` is the number of files excluded by the
        issue filter.
    """
    candidates: list[_MigrateCandidate] = []
    filtered = 0

    plan_dir = repo_root / "plan"
    if plan_dir.is_dir():
        plan_candidates, plan_filtered = _migrate_scan_plan_dir(plan_dir, repo_root, issue_filter, backlog_items)
        candidates.extend(plan_candidates)
        filtered += plan_filtered

    research_dir = repo_root / "research"
    if research_dir.is_dir():
        for file_path in research_dir.rglob("*.md"):
            if not file_path.is_file():
                continue
            rel = file_path.relative_to(repo_root).as_posix()
            issue = _migrate_resolve_issue(file_path, backlog_items)
            candidate = _migrate_make_candidate(rel, ArtifactType.RESEARCH, issue, issue_filter)
            if candidate is None:
                filtered += 1
            else:
                candidates.append(candidate)

    return candidates, filtered


def _migrate_register_one(
    provider: GitHubArtifactProvider, rel_path: str, artifact_type: ArtifactType, issue_number: int
) -> tuple[bool, str]:
    """Register a single artifact, uploading content when available.

    Idempotent — the registry upserts on (artifact_type, path).

    Args:
        provider: Initialised ``GitHubArtifactProvider`` instance.
        rel_path: Repo-relative path string.
        artifact_type: Resolved artifact type.
        issue_number: GitHub issue number (must be positive).

    Returns:
        Tuple of ``(success: bool, message: str)``.
    """
    entry = ArtifactEntry(
        artifact_type=artifact_type,
        path=rel_path,
        status=ArtifactStatus.CURRENT,
        created_at=_datetime.now(UTC).isoformat(),
        agent="artifact-migrate",
    )
    manifest = provider.get_manifest(issue_number)
    existed = any(e.artifact_type == artifact_type and e.path == rel_path for e in manifest.artifacts)
    updated_manifest = _artifact_registry.register(manifest, entry)
    provider.set_manifest(issue_number, updated_manifest)

    local_content = provider.read_local_artifact_content(rel_path)
    if local_content is not None:
        provider.store_artifact_content(issue_number, str(artifact_type), rel_path, local_content)
        content_note = " (content uploaded)"
    else:
        content_note = " (no local file — manifest-only)"

    action = "updated" if existed else "added"
    return True, f"{action}{content_note}"


# ---------------------------------------------------------------------------
# artifact_migrate helpers (dry-run / live-run)
# ---------------------------------------------------------------------------


def _migrate_dry_run(issue_number: int | None) -> dict:
    """Discover candidates and return a preview without making any API calls.

    Args:
        issue_number: Optional issue filter passed to candidate discovery.

    Returns:
        Dict with ``dry_run``, ``would_register``, ``would_skip``,
        ``details``, and ``verify`` keys.  ``details`` contains only entries
        that would be registered or cannot be registered due to a missing
        issue number — filtered entries are counted in ``would_skip`` but not
        included individually.
    """
    repo_root = _models._REPO_ROOT  # noqa: SLF001
    candidates, filtered_count = _migrate_discover_candidates(repo_root, issue_number, [])

    details: list[dict] = []
    would_register = 0
    would_skip = filtered_count  # filtered-out files count as skipped
    for rel_path, atype, issue, skip_reason in candidates:
        if skip_reason:
            # Include no-issue entries in details so the caller knows which
            # files could not be resolved — but do NOT include filter skips.
            details.append({"path": rel_path, "type": str(atype), "issue": issue, "outcome": f"skip — {skip_reason}"})
            would_skip += 1
        else:
            details.append({"path": rel_path, "type": str(atype), "issue": issue, "outcome": "would register"})
            would_register += 1

    verify = (
        f"Use artifact_list(issue_number={issue_number}) to verify registered entries"
        if issue_number is not None
        else "Use artifact_list(issue_number=<N>) per issue to verify registered entries"
    )
    return {
        "dry_run": True,
        "would_register": would_register,
        "would_skip": would_skip,
        "details": details,
        "verify": verify,
    }


def _migrate_queue_manifest_only(
    provider: GitHubArtifactProvider, issue_number: int, candidates: list[_MigrateCandidate], out: Output
) -> list[_MigrateCandidate]:
    """Append manifest-only entries (content_stored=False) to the candidate list.

    Called when ``issue_number`` is provided so already-registered entries
    without uploaded content are re-processed to trigger the auto-upload path.

    Args:
        provider: Initialised provider used to read the manifest.
        issue_number: Issue whose manifest to inspect.
        candidates: Existing candidate list (may be mutated by extension).
        out: Output accumulator for warnings.

    Returns:
        Extended candidate list.
    """
    try:
        manifest = provider.get_manifest(issue_number)
    except Exception:  # noqa: BLE001
        out.warn(f"Could not read existing manifest for issue #{issue_number}. Skipping manifest check.")
        return candidates

    result = list(candidates)
    for entry in manifest.artifacts:
        # Re-queue every registered entry so the auto-upload path can attempt
        # content upload for entries where no content was stored yet.
        # _migrate_register_one is idempotent (upserts on type+path).
        already_queued = any(
            rel == entry.path and atype == entry.artifact_type
            for rel, atype, _, skip_reason in candidates
            if skip_reason is None
        )
        if not already_queued:
            result.append((entry.path, entry.artifact_type, issue_number, None))
            out.warn(f"Queued manifest-only entry for re-registration: {entry.path!r}")
    return result


def _migrate_live_run(issue_number: int | None, out: Output) -> dict:
    """Execute the live migration against GitHub.

    Args:
        issue_number: Optional issue filter.
        out: Output accumulator (warnings written here).

    Returns:
        Dict with ``migrated``, ``skipped``, ``failed``, ``details``, and
        ``verify``.  ``details`` contains only migrated and failed entries —
        skipped entries are counted in ``skipped`` but not listed individually
        to keep the response compact.
    """
    repo_root = _models._REPO_ROOT  # noqa: SLF001
    provider = _get_artifact_provider()

    backlog_items: list[dict] = []
    try:
        raw = operations.list_items()
        if isinstance(raw, list):
            backlog_items = raw
        elif isinstance(raw, dict):
            backlog_items = raw.get("items", [])
    except Exception:  # noqa: BLE001
        out.warn("Could not fetch backlog items for slug matching. Continuing without fallback.")

    candidates, filtered_count = _migrate_discover_candidates(repo_root, issue_number, backlog_items)

    if issue_number is not None:
        candidates = _migrate_queue_manifest_only(provider, issue_number, candidates, out)

    migrated = 0
    skipped = filtered_count  # files excluded by issue filter count as skipped
    failed = 0
    run_details: list[dict] = []

    for rel_path, atype, issue, skip_reason in candidates:
        if skip_reason:
            # Count no-issue files as skipped; do NOT add to run_details to
            # avoid a 500-entry skipped list in the response.
            skipped += 1
            continue

        assert issue is not None  # skip_reason is None only when issue resolved  # noqa: S101
        try:
            _ok, action_msg = _migrate_register_one(provider, rel_path, atype, issue)
            migrated += 1
            run_details.append({"path": rel_path, "type": str(atype), "issue": issue, "outcome": action_msg})
        except Exception as exc:  # noqa: BLE001
            failed += 1
            run_details.append({"path": rel_path, "type": str(atype), "issue": issue, "outcome": f"FAILED: {exc}"})

    verify = (
        f"Use artifact_read(issue_number={issue_number}, artifact_type='<type>') "
        f"or artifact_list(issue_number={issue_number}) to verify"
        if issue_number is not None
        else "Use artifact_list(issue_number=<N>) per issue to verify registered entries"
    )
    return {"migrated": migrated, "skipped": skipped, "failed": failed, "details": run_details, "verify": verify}


# ---------------------------------------------------------------------------
# artifact_migrate MCP tool
# ---------------------------------------------------------------------------


@mcp.tool
async def artifact_migrate(
    issue_number: Annotated[
        int | None, Field(description="Migrate artifacts for a specific issue number only. Omit to scan all issues.")
    ] = None,
    dry_run: Annotated[
        bool, Field(description="When true, report what would be migrated without making any API calls.")
    ] = False,
) -> dict:
    """Migrate existing plan/research artifacts into the artifact manifest system.

    Scans ``plan/`` and ``research/`` directories for artifact files,
    determines the artifact type from the filename pattern, extracts the
    linked GitHub issue number from YAML frontmatter (falling back to slug
    matching against backlog items), and calls the artifact_register logic
    for each discovered file.

    When ``issue_number`` is provided the tool also checks the existing
    manifest for that issue: any already-registered entry that has
    ``content_stored=False`` is re-registered so the auto-upload path can
    run and upload the local file content.

    Safe to re-run — the registry upserts on ``(artifact_type, path)``
    so existing entries are updated in-place rather than duplicated.

    Returns:
        Dict with ``migrated`` (int), ``skipped`` (int), ``failed`` (int),
        and ``details`` (list of per-artifact outcome dicts).  Each detail
        dict contains ``path``, ``type``, ``issue``, and ``outcome``.
        On error, dict contains an ``error`` key.
    """
    out = Output()

    if dry_run:
        try:
            result = await asyncio.to_thread(_migrate_dry_run, issue_number)
        except Exception as exc:  # noqa: BLE001
            return {"error": f"Discovery failed: {exc}", **out.to_dict()}
        return {**result, **out.to_dict()}

    try:
        result = await asyncio.to_thread(_migrate_live_run, issue_number, out)
    except GitHubUnavailableError as exc:
        return {"error": str(exc), **out.to_dict()}
    except Exception as exc:  # noqa: BLE001
        return {"error": f"Migration failed: {exc}", **out.to_dict()}

    return {**result, **out.to_dict()}


from agent_profile import mcp as _agent_profile_mcp

mcp.mount(_agent_profile_mcp, namespace="profile")

if __name__ == "__main__":
    mcp.run()
