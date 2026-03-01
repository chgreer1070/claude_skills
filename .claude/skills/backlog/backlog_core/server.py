"""FastMCP 3.x server exposing all backlog operations as MCP tools."""

from __future__ import annotations

from typing import Annotated

from fastmcp import FastMCP
from pydantic import Field

from . import operations
from .models import BacklogError, Output

mcp = FastMCP("backlog")


@mcp.tool()
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


@mcp.tool()
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


@mcp.tool()
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


@mcp.tool()
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


@mcp.tool()
def backlog_close(
    selector: Annotated[str, Field(description="Item selector: title substring, #N, bare number, or GitHub issue URL")],
    plan: Annotated[str, Field(description="Plan path or completion summary for closing")],
    checklist_pass: Annotated[
        bool, Field(description="Confirm the completion checklist has been verified. Must be true to close.")
    ] = False,
    cleanup: Annotated[
        bool, Field(description="Remove local file after close; index link becomes GitHub issue URL")
    ] = False,
    force: Annotated[bool, Field(description="Close even if open PRs reference the issue")] = False,
) -> dict:
    """Mark a backlog item as DONE and close its GitHub issue.

    Requires checklist_pass=true (the caller must verify the completion
    checklist before closing). Use force=true to close even when open PRs
    reference the issue.

    Returns:
        Dict with closed item title, issue reference, and output
        messages/warnings. On error, dict contains an error key.
    """
    out = Output()
    try:
        result = operations.close_item(
            selector=selector, plan=plan, checklist_pass=checklist_pass, cleanup=cleanup, force=force, output=out
        )
        return {**result, **out.to_dict()}
    except BacklogError as e:
        return {"error": str(e), **out.to_dict()}


@mcp.tool()
def backlog_resolve(
    selector: Annotated[str, Field(description="Item selector: title substring, #N, bare number, or GitHub issue URL")],
    reason: Annotated[
        str, Field(description="Reason for resolving (e.g. 'duplicate of #42', 'no longer needed', 'out of scope')")
    ],
    cleanup: Annotated[
        bool, Field(description="Remove local file after resolve; index link becomes GitHub issue URL")
    ] = False,
    force: Annotated[bool, Field(description="Resolve even if open PRs reference the issue")] = False,
) -> dict:
    """Mark a backlog item as RESOLVED and close its GitHub issue without completing it.

    Use for items that are duplicates, no longer needed, or out of scope.
    Use force=true to resolve even when open PRs reference the issue.

    Returns:
        Dict with resolved item title, reason, issue reference, and output
        messages/warnings. On error, dict contains an error key.
    """
    out = Output()
    try:
        result = operations.resolve_item(selector=selector, reason=reason, cleanup=cleanup, force=force, output=out)
        return {**result, **out.to_dict()}
    except BacklogError as e:
        return {"error": str(e), **out.to_dict()}


@mcp.tool()
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

    For groomed content, either provide groomed_content (full replacement)
    or section + content (incremental section update). Groomed content is
    synced to the GitHub issue when the item has one.

    Returns:
        Dict with updated item title, applied changes, and output
        messages/warnings. On error, dict contains an error key.
    """
    out = Output()
    try:
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


@mcp.tool()
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


@mcp.tool()
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


@mcp.tool()
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


if __name__ == "__main__":
    mcp.run()
