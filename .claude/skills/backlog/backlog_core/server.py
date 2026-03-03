"""FastMCP 3.x server exposing all backlog operations as MCP tools."""

from __future__ import annotations

from typing import Annotated

from fastmcp import FastMCP
from mcp.types import ToolAnnotations
from pydantic import Field

from . import operations
from .models import BacklogError, Output, ValidationError

mcp = FastMCP("backlog")

# ---------------------------------------------------------------------------
# Shared ToolAnnotations singletons (F11)
# ---------------------------------------------------------------------------
_READ_ONLY = ToolAnnotations(readOnlyHint=True, destructiveHint=False)
_DESTRUCTIVE = ToolAnnotations(readOnlyHint=False, destructiveHint=True)
_WRITE = ToolAnnotations(readOnlyHint=False, destructiveHint=False)


@mcp.tool(annotations=_WRITE)
def backlog_add(
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
        result = operations.add_item(
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


@mcp.tool(annotations=_READ_ONLY)
def backlog_list(
    with_status: Annotated[bool, Field(description="Include GitHub issue status for each item")] = False,
    from_github: Annotated[bool, Field(description="Refresh local cache from GitHub Issues before listing")] = False,
    label: Annotated[str | None, Field(description="Filter by GitHub label (e.g. 'priority:p1', 'type:bug')")] = None,
    section: Annotated[
        str | None, Field(description="Filter by priority section: P0, P1, P2, or Ideas (case-insensitive)")
    ] = None,
    status: Annotated[
        str | None, Field(description="Filter by status value e.g. 'needs-grooming', 'status:in-progress'")
    ] = None,
    title: Annotated[
        str | None, Field(description="Filter items whose title contains this substring (case-insensitive)")
    ] = None,
) -> dict:
    """List all open backlog items.

    Use from_github=true to refresh the local cache from GitHub before listing.
    Use label to filter items by a specific GitHub label.
    Use section to filter by priority section (P0, P1, P2, Ideas).
    Use status to filter by status value (e.g. needs-grooming, status:in-progress).
    Use title to filter by title substring (case-insensitive).

    Returns:
        Dict with items list (each containing title, priority, issue, plan)
        and output messages/warnings. On error, dict contains an error key.
    """
    out = Output()
    try:
        result = operations.list_items(
            with_status=with_status,
            from_github=from_github,
            label=label,
            section=section,
            status=status,
            title=title,
            output=out,
        )
        return {**result, **out.to_dict()}
    except BacklogError as e:
        return {"error": str(e), **out.to_dict()}


@mcp.tool(annotations=_READ_ONLY)
def backlog_view(
    selector: Annotated[str, Field(description="Item selector: GitHub issue URL, #N, bare number, or title substring")],
    offset: Annotated[int, Field(ge=0, description="Skip N lines from body start (for pagination)")] = 0,
    limit: Annotated[int, Field(ge=0, description="Show at most N body lines (0 = all, no truncation)")] = 0,
) -> dict:
    """View a single backlog item or GitHub issue in detail.

    Accepts a GitHub issue URL, #N, bare number, or title substring as selector.
    Use offset and limit to paginate long issue bodies.

    Returns:
        Dict with title, priority, issue, plan, file_path, body, groomed
        content, and output messages/warnings. On error, dict contains an
        error key.
    """
    out = Output()
    try:
        result = operations.view_item(selector=selector, offset=offset, limit=limit, output=out)
        return {**result, **out.to_dict()}
    except BacklogError as e:
        return {"error": str(e), **out.to_dict()}


@mcp.tool(annotations=_WRITE)
def backlog_sync(
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
        result = operations.sync_items(dry_run=dry_run, output=out)
        return {**result, **out.to_dict()}
    except BacklogError as e:
        return {"error": str(e), **out.to_dict()}


@mcp.tool(annotations=_DESTRUCTIVE)
def backlog_close(
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
        result = operations.close_item(
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


@mcp.tool(annotations=_DESTRUCTIVE)
def backlog_resolve(
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
        result = operations.resolve_item(
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


@mcp.tool(annotations=_WRITE)
def backlog_update(
    selector: Annotated[str, Field(description="Item selector: title substring, #N, bare number, or GitHub issue URL")],
    plan: Annotated[str | None, Field(description="Path to a plan file to attach to the item")] = None,
    status: Annotated[
        str | None,
        Field(description="Set item status (e.g. 'in-progress'). Updates GitHub issue labels when applicable."),
    ] = None,
    create_issue: Annotated[
        bool, Field(description="Create a GitHub issue for this item if it lacks one (P0/P1 items only)")
    ] = False,
    groomed_content: Annotated[
        str | None,
        Field(
            description="Groomed content to write into the item's per-item file. Replaces the entire groomed section."
        ),
    ] = None,
    section: Annotated[
        str | None,
        Field(description="Section name for incremental groomed content update (use with content parameter)"),
    ] = None,
    content: Annotated[
        str | None,
        Field(description="Content for the named section (use with section parameter for incremental updates)"),
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
) -> dict:
    """Update a backlog item: attach a plan, set status, create a GitHub issue, or write groomed content.

    Intended call patterns (mutually exclusive for groomed content):
    - Attach a plan: provide ``plan`` only.
    - Set status: provide ``status`` only (e.g. 'in-progress', 'open', 'blocked').
    - Full groomed content replacement: provide ``groomed_content`` only.
    - Incremental section update: provide ``section`` + ``content`` together.
    - Rename: provide ``title`` only.
    - Update description: provide ``description`` only.

    Combining ``groomed_content`` with ``section`` is invalid — use one approach
    at a time.

    Returns:
        Dict with updated item title, applied changes, and output
        messages/warnings. On error, dict contains an error key.
    """
    out = Output()
    try:
        if groomed_content is not None and section is not None:
            raise ValidationError(
                "groomed_content and section are mutually exclusive: "
                "use groomed_content for full replacement or section+content for incremental update"
            )
        if section is not None and content is None:
            raise ValidationError("section requires a content parameter for incremental update")
        result = operations.update_item(
            selector=selector,
            plan=plan,
            status=status,
            create_issue=create_issue,
            groomed_content=groomed_content,
            section=section,
            content=content,
            title=title,
            description=description,
            output=out,
        )
        return {**result, **out.to_dict()}
    except BacklogError as e:
        return {"error": str(e), **out.to_dict()}


@mcp.tool(annotations=_WRITE)
def backlog_groom(
    selector: Annotated[str, Field(description="Item selector: title substring, #N, bare number, or GitHub issue URL")],
    groomed_content: Annotated[
        str | None,
        Field(description="Full groomed content to write into the per-item file. Replaces the entire groomed section."),
    ] = None,
    section: Annotated[
        str | None, Field(description="Section name for incremental update (use with content parameter)")
    ] = None,
    content: Annotated[
        str | None, Field(description="Content for the named section (use with section parameter)")
    ] = None,
) -> dict:
    """Write groomed content into a backlog item's per-item file and sync to its GitHub issue.

    Provide either groomed_content for full replacement, or section + content
    for incremental section updates. When the item has a GitHub issue, the
    groomed content is synced there automatically.

    Returns:
        Dict with groomed item title, synced status, and output
        messages/warnings. On error, dict contains an error key.
    """
    out = Output()
    try:
        result = operations.groom_item(
            selector=selector, groomed_content=groomed_content, section=section, content=content, output=out
        )
        return {**result, **out.to_dict()}
    except BacklogError as e:
        return {"error": str(e), **out.to_dict()}


@mcp.tool(annotations=_WRITE)
def backlog_normalize(
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
        result = operations.normalize_items(dry_run=dry_run, output=out)
        return {**result, **out.to_dict()}
    except BacklogError as e:
        return {"error": str(e), **out.to_dict()}


@mcp.tool(annotations=_WRITE)
def backlog_pull(
    dry_run: Annotated[bool, Field(description="Preview what would be pulled without modifying local files")] = False,
    force: Annotated[
        bool, Field(description="Overwrite local content even if local version is newer or longer")
    ] = False,
) -> dict:
    """Pull issue body content from GitHub into local per-item files.

    Auto-migrates P0/P1 items lacking GitHub Issues by creating them.
    Merges by section, keeping the longer version of each section unless
    force=true. Use dry_run=true to preview changes.

    Returns:
        Dict with count of pulled items and output messages/warnings.
        On error, dict contains an error key.
    """
    out = Output()
    try:
        result = operations.pull_items(dry_run=dry_run, force=force, output=out)
        return {**result, **out.to_dict()}
    except BacklogError as e:
        return {"error": str(e), **out.to_dict()}


# ---------------------------------------------------------------------------
# New tools: F12 — Session Diff
# ---------------------------------------------------------------------------


@mcp.tool(annotations=_READ_ONLY)
def backlog_session_diff(
    since: Annotated[
        str,
        Field(
            description="ISO 8601 timestamp (e.g. '2026-03-01T10:00:00Z'). Items with file mtime after this are returned."
        ),
    ],
) -> dict:
    """Return backlog items modified since a given ISO timestamp.

    Use after context compaction to see what changed without re-running backlog_list.
    Returns the same shape as backlog_list.

    Returns:
        Dict with items list, count, and output messages/warnings.
        On error, dict contains an error key.
    """
    out = Output()
    try:
        result = operations.session_diff_items(since=since, output=out)
        return {**result, **out.to_dict()}
    except BacklogError as e:
        return {"error": str(e), **out.to_dict()}


# ---------------------------------------------------------------------------
# New tools: F13 — Dashboard
# ---------------------------------------------------------------------------


@mcp.tool(annotations=_READ_ONLY)
def backlog_dashboard() -> dict:
    """Return a single-call backlog health overview.

    Replaces 3-5 round-trips of backlog_list + manual counting.

    Returns:
        Dict with counts_by_section, total_open, items_without_issue,
        items_needing_grooming, recently_modified (last 7 days), and
        output messages/warnings. On error, dict contains an error key.
    """
    out = Output()
    try:
        result = operations.dashboard_items(output=out)
        return {**result, **out.to_dict()}
    except BacklogError as e:
        return {"error": str(e), **out.to_dict()}


# ---------------------------------------------------------------------------
# New tools: F14 — Named status tools
# ---------------------------------------------------------------------------


@mcp.tool(annotations=_WRITE)
def backlog_start(
    selector: Annotated[str, Field(description="Item selector: title substring, #N, bare number, or GitHub issue URL")],
) -> dict:
    """Set a backlog item's status to 'in-progress'.

    Provides explicit, auditable intent compared to backlog_update(status=...).

    Returns:
        Dict with item title, status, and output messages/warnings.
        On error, dict contains an error key.
    """
    out = Output()
    try:
        result = operations.start_item(selector=selector, output=out)
        return {**result, **out.to_dict()}
    except BacklogError as e:
        return {"error": str(e), **out.to_dict()}


@mcp.tool(annotations=_WRITE)
def backlog_block(
    selector: Annotated[str, Field(description="Item selector: title substring, #N, bare number, or GitHub issue URL")],
    reason: Annotated[str, Field(description="Why the item is blocked (required)")],
) -> dict:
    """Set a backlog item's status to 'blocked' with an explicit reason.

    Returns:
        Dict with item title, status, blocked_reason, and output messages/warnings.
        On error, dict contains an error key.
    """
    out = Output()
    try:
        result = operations.block_item(selector=selector, reason=reason, output=out)
        return {**result, **out.to_dict()}
    except BacklogError as e:
        return {"error": str(e), **out.to_dict()}


@mcp.tool(annotations=_WRITE)
def backlog_unblock(
    selector: Annotated[str, Field(description="Item selector: title substring, #N, bare number, or GitHub issue URL")],
) -> dict:
    """Clear a block on a backlog item: sets status back to 'open'.

    Returns:
        Dict with item title, status, and output messages/warnings.
        On error, dict contains an error key.
    """
    out = Output()
    try:
        result = operations.unblock_item(selector=selector, output=out)
        return {**result, **out.to_dict()}
    except BacklogError as e:
        return {"error": str(e), **out.to_dict()}


# ---------------------------------------------------------------------------
# New tools: F15 — Batch update
# ---------------------------------------------------------------------------


@mcp.tool(annotations=_WRITE)
def backlog_batch_update(
    selectors: Annotated[list[str], Field(description="List of item selectors to update (title substrings, #N, URLs)")],
    status: Annotated[
        str | None, Field(description="Status to apply to all selected items (e.g. 'in-progress', 'open')")
    ] = None,
    plan: Annotated[str | None, Field(description="Plan path to attach to all selected items")] = None,
) -> dict:
    """Update multiple backlog items with the same status and/or plan in a single call.

    Replaces N sequential backlog_update calls with one call.
    Each item is processed independently; per-item errors are collected but do
    not abort processing of remaining selectors.

    Returns:
        Dict with updated count, total count, per-item results list, and
        output messages/warnings. On error, dict contains an error key.
    """
    out = Output()
    try:
        result = operations.batch_update_items(selectors=selectors, status=status, plan=plan, output=out)
        return {**result, **out.to_dict()}
    except BacklogError as e:
        return {"error": str(e), **out.to_dict()}


# ---------------------------------------------------------------------------
# F17 — MCP Prompts (discoverability in Claude Code prompt picker)
# ---------------------------------------------------------------------------


@mcp.prompt()
def backlog_add_prompt(
    title: Annotated[str, Field(description="Item title")],
    priority: Annotated[str, Field(description="Priority level: P0, P1, P2, or Ideas")],
    description: Annotated[str, Field(description="Item description")],
) -> str:
    """Prompt to add a new backlog item.

    Returns:
        Prompt string for adding a backlog item.
    """
    return f"Add backlog item '{title}' at priority {priority}: {description}"


@mcp.prompt()
def backlog_list_prompt(
    section: Annotated[str | None, Field(description="Filter by section: P0, P1, P2, Ideas")] = None,
    status: Annotated[str | None, Field(description="Filter by status")] = None,
) -> str:
    """Prompt to list open backlog items.

    Returns:
        Prompt string for listing backlog items.
    """
    parts = ["List open backlog items"]
    if section:
        parts.append(f"in section {section}")
    if status:
        parts.append(f"with status {status}")
    return " ".join(parts)


@mcp.prompt()
def backlog_dashboard_prompt() -> str:
    """Prompt to get a backlog health overview.

    Returns:
        Prompt string for the dashboard overview.
    """
    return "Show me the backlog health dashboard with counts by section, items needing grooming, and recent changes."


@mcp.prompt()
def backlog_view_prompt(
    selector: Annotated[str, Field(description="Item selector: #N, title substring, or GitHub issue URL")],
) -> str:
    """Prompt to view a single backlog item.

    Returns:
        Prompt string for viewing an item.
    """
    return f"Show the details for backlog item: {selector}"


@mcp.prompt()
def backlog_groom_prompt(selector: Annotated[str, Field(description="Item selector")]) -> str:
    """Prompt to groom a backlog item.

    Returns:
        Prompt string for grooming an item.
    """
    return f"Groom backlog item {selector}: research it, add acceptance criteria, context, and implementation notes."


@mcp.prompt()
def backlog_start_prompt(selector: Annotated[str, Field(description="Item selector")]) -> str:
    """Prompt to start work on a backlog item.

    Returns:
        Prompt string for starting an item.
    """
    return f"Start work on backlog item {selector}: set it to in-progress."


@mcp.prompt()
def backlog_resolve_prompt(
    selector: Annotated[str, Field(description="Item selector")],
    summary: Annotated[str, Field(description="What was done")] = "",
) -> str:
    """Prompt to mark a backlog item as resolved.

    Returns:
        Prompt string for resolving an item.
    """
    return f"Resolve backlog item {selector}" + (f": {summary}" if summary else ".")


@mcp.prompt()
def backlog_session_diff_prompt(since: Annotated[str, Field(description="ISO 8601 timestamp")]) -> str:
    """Prompt to see what changed in the backlog since a timestamp.

    Returns:
        Prompt string for the session diff query.
    """
    return f"What backlog items changed since {since}?"


if __name__ == "__main__":
    mcp.run()
