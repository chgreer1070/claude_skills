"""High-level CRUD operations for backlog items.

Combines parsing, GitHub, and file I/O into public functions that return
dicts. Each public function accepts an optional ``output: Output | None``
parameter and returns ``{...result, **out.to_dict()}``.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from github import GithubException, GithubObject

from .github import (
    apply_status_in_progress,
    batch_fetch_statuses,
    check_open_prs_for_issue,
    close_github_issue,
    create_issue_for_item,
    fetch_github_issue_body,
    fetch_open_issues_by_title,
    get_github,
    issue_to_local_fields,
    resolve_github_issue,
    sync_groomed_to_github_issue,
    try_get_github,
    view_enrich_from_github,
)
from .models import (
    _COMMIT_PREFIX_RE,
    BACKLOG_DIR,
    DEFAULT_REPO,
    MIN_FRONTMATTER_PARTS,
    BacklogError,
    BacklogItem,
    DuplicateItemError,
    ItemNotFoundError,
    Output,
    ValidationError,
    ViewItemResult,
)
from .parsing import (
    append_or_replace_section,
    build_backlog_frontmatter,
    build_body_extra_only,
    build_issue_body_from_file,
    dump_frontmatter,
    extract_description_from_issue_body,
    extract_groomed_section,
    extract_normalize_metadata,
    find_fuzzy_duplicates,
    find_item,
    items_needing_issues,
    items_with_issues,
    loads_frontmatter,
    merge_sections,
    normalize_issue_title,
    now_iso,
    parse_backlog,
    parse_body_extra_fields,
    parse_issue_selector,
    title_to_slug,
    today,
    view_result_from_local_item,
)

if TYPE_CHECKING:
    from github.Repository import Repository


# ---------------------------------------------------------------------------
# File metadata
# ---------------------------------------------------------------------------


def update_item_metadata(
    filepath: Path, updates: dict[str, str | dict[str, str]], set_synced: bool = False, output: Output | None = None
) -> dict[str, str | bool | list[str]]:
    """Update per-item file frontmatter. Supports nested metadata.plan, metadata.issue, etc.

    When set_synced=True, also sets metadata.last_synced to current UTC time.

    Returns:
        Dict with filepath and updated flag plus output messages.
    """
    out = output or Output()
    post = loads_frontmatter(filepath.read_text(encoding="utf-8"))
    meta = post.metadata or {}
    for key, value in updates.items():
        if key == "metadata" and isinstance(value, dict):
            raw_nested = meta.get("metadata")
            nested_dict: dict[str, str] = (
                {str(k): str(v) for k, v in raw_nested.items()} if isinstance(raw_nested, dict) else {}
            )
            nested_dict.update(value)
            if set_synced:
                nested_dict["last_synced"] = now_iso()
            meta["metadata"] = nested_dict
        else:
            meta[key] = value
    if set_synced and "metadata" not in updates:
        raw_nested = meta.get("metadata")
        nested_dict2: dict[str, str] = (
            {str(k): str(v) for k, v in raw_nested.items()} if isinstance(raw_nested, dict) else {}
        )
        nested_dict2["last_synced"] = now_iso()
        meta["metadata"] = nested_dict2
    post.metadata = meta
    filepath.write_text(dump_frontmatter(post), encoding="utf-8")
    return {"filepath": str(filepath), "updated": True, **out.to_dict()}


# ---------------------------------------------------------------------------
# Internal helpers (not exported)
# ---------------------------------------------------------------------------


def _create_issue_and_update_item(item: BacklogItem, repo: str, output: Output | None = None) -> int | None:
    """Create GitHub issue for item and update per-item file metadata.

    Returns:
        Issue number if created, None otherwise.
    """
    out = output or Output()
    try:
        repository = get_github(repo)
        issue_num = create_issue_for_item(repository, item, dry_run=False, output=out)
    except (GithubException, BacklogError) as e:
        out.warn(f"  WARNING: Issue creation failed: {e}")
        return None
    else:
        if not issue_num:
            return None
        filepath_str = item.file_path
        if filepath_str:
            update_item_metadata(Path(filepath_str), {"metadata": {"issue": f"#{issue_num}"}}, output=out)
        return issue_num


def _rename_item_title(item: BacklogItem, title: str, repo: str = DEFAULT_REPO, output: Output | None = None) -> bool:
    """Update the name field in the per-item file. Syncs to GitHub issue title if linked.

    Returns:
        True if updated, False if no file path on item.
    """
    out = output or Output()
    filepath_str = item.file_path
    if not filepath_str:
        return False
    update_item_metadata(Path(filepath_str), {"name": title}, output=out)

    issue_ref = item.issue
    if issue_ref:
        repository = try_get_github(repo)
        if repository is not None:
            try:
                num = int(issue_ref.lstrip("#"))
                gh_issue = repository.get_issue(num)
                gh_issue.edit(title=title)
                out.info(f"  GitHub issue {issue_ref} title updated to: {title}")
            except GithubException as e:
                out.warn(f"  WARNING: Could not update issue {issue_ref} title: {e}")

    return True


def _update_item_description(item: BacklogItem, description: str, output: Output | None = None) -> bool:
    """Update the description field in the per-item file. Local-only, no GitHub sync.

    Returns:
        True if updated, False if no file path on item.
    """
    out = output or Output()
    filepath_str = item.file_path
    if not filepath_str:
        return False
    update_item_metadata(Path(filepath_str), {"description": description}, output=out)
    return True


def _apply_plan_to_item(item: BacklogItem, plan: str, repo: str = DEFAULT_REPO, output: Output | None = None) -> bool:
    """Apply plan update: write to GitHub Issue first (comment), then update local cache.

    GH-first: posts a plan comment on the linked GitHub Issue before updating local.
    If GH is unavailable, local update still succeeds.

    Returns:
        True if updated, False otherwise.
    """
    out = output or Output()
    filepath_str = item.file_path
    if not filepath_str:
        return False
    update_item_metadata(Path(filepath_str), {"metadata": {"plan": plan}}, output=out)

    # GH-first: post plan reference as a comment on the linked issue
    issue_ref = item.issue
    if issue_ref:
        repository = try_get_github(repo)
        if repository is not None:
            try:
                num = int(issue_ref.lstrip("#"))
                gh_issue = repository.get_issue(num)
                gh_issue.create_comment(f"**Plan**: {plan}")
                out.info(f"  Plan comment posted to issue {issue_ref}")
            except GithubException as e:
                out.warn(f"  WARNING: Could not post plan to issue {issue_ref}: {e}")

    return True


def _resolve_groomed_content(
    section: str | None, content: str | None, groomed_content: str | None, groomed_file: str | None
) -> tuple[str, str | None]:
    """Resolve groomed content from section/content, groomed_content, groomed_file, or stdin.

    Returns:
        Tuple of (content_string, section_name_or_None).
    """
    if section is not None and content is not None:
        return content, section
    if groomed_content is not None:
        return groomed_content, None
    if groomed_file:
        return Path(groomed_file).read_text(encoding="utf-8"), None
    return sys.stdin.read(), None


def _write_groomed_to_item_file(
    filepath: Path, groomed_content: str, section_name: str | None = None, output: Output | None = None
) -> None:
    """Merge groomed content into per-item file.

    Updates frontmatter groomed date and body.
    If section_name is set, append/replace that section only (incremental).
    Else replace full ## Groomed.
    """
    text = filepath.read_text(encoding="utf-8")
    if not text.startswith("---"):
        raise ValidationError("Item file has no frontmatter")
    parts = text.split("---", 2)
    if len(parts) < MIN_FRONTMATTER_PARTS:
        raise ValidationError("Malformed item file")
    fm_text, body = parts[1].strip(), parts[2].strip()
    today_str = today()
    if section_name:
        new_body = append_or_replace_section(body, section_name, groomed_content)
    else:
        groomed_section = f"## Groomed ({today_str})\n\n{groomed_content.strip()}"
        groomed_re = re.compile(r"\n## Groomed\s*\([^)]*\)\s*\n[\s\S]*?(?=\n## |\Z)", re.MULTILINE)
        if groomed_re.search(body):
            new_body = groomed_re.sub(lambda _: f"\n{groomed_section}\n", body)
        else:
            new_body = body.rstrip() + "\n\n" + groomed_section + "\n"
    try:
        post = loads_frontmatter(text)
        meta_block = post.metadata.get("metadata")
        if isinstance(meta_block, dict):
            updated = dict(meta_block)
            updated["groomed"] = today_str
            post.metadata["metadata"] = updated
        else:
            post.metadata["groomed"] = today_str
        post.content = new_body
        new_content = dump_frontmatter(post)
    except (ValueError, KeyError, TypeError):
        new_content = "---\n" + fm_text + "\n---\n\n" + new_body
        if "groomed:" not in fm_text:
            new_content = new_content.replace("---\n", f'---\ngroomed: "{today_str}"\n', 1)
    filepath.write_text(new_content, encoding="utf-8")


def _ensure_github_issue(item: BacklogItem, filepath: Path, repo: str, output: Output | None = None) -> str | None:
    """Create GitHub issue if item doesn't have one.

    Uses try_get_github for graceful fallback when GitHub is unavailable.

    Returns:
        Issue ref like '#42', or None if no issue was created.
    """
    out = output or Output()
    repository = try_get_github(repo)
    if not repository:
        out.info("  INFO: GitHub unavailable — working locally only")
        return None
    try:
        issue_num = create_issue_for_item(repository, item, dry_run=False, output=out)
    except GithubException as e:
        out.warn(f"  WARNING: Could not create issue: {e}")
        return None
    else:
        if not issue_num:
            return None
        update_item_metadata(filepath, {"metadata": {"issue": f"#{issue_num}"}}, set_synced=True, output=out)
        out.info(f"  Created GitHub issue #{issue_num}")
        return f"#{issue_num}"


def _write_groomed_to_github(
    issue_ref: str, content: str, section_name: str | None, repo: str, output: Output | None = None
) -> bool:
    """Write groomed content to GitHub issue.

    Gracefully falls back to local-only when GitHub is unavailable.

    Returns:
        True if content was synced to GitHub, False otherwise.
    """
    out = output or Output()
    repository = try_get_github(repo)
    if not repository:
        out.info(f"  INFO: GitHub unavailable — {issue_ref} will sync on next `backlog pull` or `backlog sync`")
        return False
    try:
        num = int(issue_ref.lstrip("#"))
        updated = sync_groomed_to_github_issue(repository, num, content, section_name, output=out)
    except GithubException as e:
        out.warn(f"  WARNING: Could not sync to GitHub: {e}")
        return False
    else:
        if updated:
            out.info(f"  Synced to GitHub issue {issue_ref}")
        else:
            out.info(f"  No changes to sync to GitHub issue {issue_ref}")
        return updated


def _handle_update_groomed(
    item: BacklogItem, groomed_content_val: str, section_name: str | None, repo: str, output: Output | None = None
) -> None:
    """Handle groomed content update: GitHub-first, then cache locally.

    Write order: (1) GitHub issue (canonical), (2) local file (cache).
    If item has no issue, creates one for P0/P1 first.
    Sets last_synced after successful GitHub write.
    """
    out = output or Output()
    filepath = Path(item.file_path)
    issue_ref = item.issue

    # Step 1: Ensure GitHub issue exists for P0/P1 items
    if not issue_ref and not item.skip and item.section in {"P0", "P1", "P2", "Ideas"}:
        issue_ref = _ensure_github_issue(item, filepath, repo, output=out)

    # Step 2: Write to GitHub FIRST (canonical source of truth)
    github_synced = False
    if issue_ref:
        github_synced = _write_groomed_to_github(issue_ref, groomed_content_val, section_name, repo, output=out)

    # Step 3: Write to local file (cache)
    _write_groomed_to_item_file(filepath, groomed_content_val, section_name, output=out)
    out.info(f"Updated {filepath.name} with groomed content")

    # Step 4: Set last_synced if GitHub write succeeded
    if github_synced:
        update_item_metadata(filepath, {"metadata": {"last_synced": now_iso()}}, output=out)


def _overwrite_body_from_github(filepath: Path, issue_body: str) -> None:
    """Replace the body of a local cache file with content from GitHub issue body.

    Preserves frontmatter, replaces everything after it.
    """
    text = filepath.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return
    parts = text.split("---", 2)
    if len(parts) < MIN_FRONTMATTER_PARTS:
        return
    # Keep frontmatter, replace body
    new_content = "---" + parts[1] + "---\n\n" + issue_body.strip() + "\n"
    filepath.write_text(new_content, encoding="utf-8")


def _close_cleanup(item: BacklogItem, issue_ref: str, repo: str, output: Output | None = None) -> None:
    """Remove local per-item file after close (canonical state lives in GitHub)."""
    out = output or Output()
    filepath_str = item.file_path
    if not filepath_str:
        return
    filepath = Path(filepath_str)
    if filepath.exists():
        filepath.unlink()
        out.info(f"  Removed local file {filepath.name} (canonical: GH #{issue_ref.lstrip('#')})")


def _build_normalized_content(filepath: Path, output: Output | None = None) -> str | None:
    """Build normalized content for one file.

    Returns:
        Normalized content string or None if skip.
    """
    out = output or Output()
    try:
        text = filepath.read_text(encoding="utf-8")
    except OSError as e:
        out.warn(f"  Skip {filepath.name}: {e}")
        return None
    if not text.startswith("---"):
        return None
    try:
        post = loads_frontmatter(text)
        fm: dict[str, object] = (
            {k: (v if isinstance(v, dict) else str(v)) for k, v in post.metadata.items()} if post.metadata else {}
        )
        body: str = post.content or ""
    except (ValueError, KeyError, TypeError):
        return None
    meta_raw = fm.get("metadata")
    meta: dict[str, str] = {str(k): str(v) for k, v in meta_raw.items()} if isinstance(meta_raw, dict) else {}
    md = extract_normalize_metadata(fm, meta)
    if not md["name"]:
        return None
    parsed = parse_body_extra_fields(body)
    if parsed[0] and not md["description"]:
        md["description"] = parsed[0]
    groomed = extract_groomed_section(body)
    new_body = build_body_extra_only(parsed[1], parsed[2], parsed[3], parsed[4], parsed[5], groomed)
    fm_str = build_backlog_frontmatter(
        md["name"],
        md["description"],
        md["source"],
        md["added"],
        md["priority"],
        md["type_val"],
        md["status"],
        md["issue"],
        md["plan"],
        md["groomed"],
    )
    result = fm_str.rstrip()
    return result + ("\n" if not result.endswith("\n\n") else "") + new_body


def _normalize_item_file(filepath: Path, dry_run: bool, output: Output | None = None) -> bool:
    """Normalize one backlog item file.

    Returns:
        True if updated, False if skipped.
    """
    content = _build_normalized_content(filepath, output=output)
    if content is None:
        return False
    if not dry_run:
        filepath.write_text(content, encoding="utf-8")
    return True


# ---------------------------------------------------------------------------
# Pull helpers
# ---------------------------------------------------------------------------


def _pull_item_create_new(
    item: BacklogItem,
    issue_num: int,
    issue_ref: str,
    title: str,
    github_body: str,
    dry_run: bool,
    output: Output | None = None,
) -> bool:
    """Create a new local file from a GitHub issue body.

    Returns:
        True if created (or would create in dry-run).
    """
    out = output or Output()
    slug = title_to_slug(title)
    priority = item.priority or "P2"
    filename = f"{priority.lower()}-{slug}.md"
    filepath = BACKLOG_DIR / filename
    BACKLOG_DIR.mkdir(parents=True, exist_ok=True)
    if dry_run:
        out.info(f"  [dry-run] Would create {filename} from #{issue_num}: {title}")
        return True
    fm_str = build_backlog_frontmatter(
        title,
        item.description,
        item.source,
        item.added or today(),
        priority,
        item.item_type,
        "open",
        issue_ref,
        item.plan,
        "",
    )
    filepath.write_text(fm_str.rstrip() + "\n\n" + github_body, encoding="utf-8")
    out.info(f"  Created #{issue_num} -> {filename}: {title}")
    return True


def _pull_item_update_existing(
    item: BacklogItem,
    issue_num: int,
    title: str,
    filepath: Path,
    github_body: str,
    dry_run: bool,
    force: bool,
    output: Output | None = None,
) -> bool:
    """Update an existing local file with content from a GitHub issue body.

    Returns:
        True if updated (or would update in dry-run), False if no change needed.
    """
    out = output or Output()
    local_body = item.raw_body

    if force:
        if dry_run:
            out.info(f"  [dry-run] Would overwrite {filepath.name} from #{issue_num}: {title}")
            return True
        post = loads_frontmatter(filepath.read_text(encoding="utf-8"))
        post.content = github_body
        filepath.write_text(dump_frontmatter(post), encoding="utf-8")
        out.info(f"  Pulled #{issue_num} -> {filepath.name}: {title}")
        return True

    merged_body, modified = merge_sections(local_body, github_body)
    if not modified:
        return False

    if dry_run:
        out.info(f"  [dry-run] Would merge #{issue_num} -> {filepath.name}: {title}")
        return True

    post = loads_frontmatter(filepath.read_text(encoding="utf-8"))
    post.content = merged_body
    filepath.write_text(dump_frontmatter(post), encoding="utf-8")
    out.info(f"  Pulled #{issue_num} -> {filepath.name}: {title}")
    return True


def _pull_item(
    item: BacklogItem, repo_obj: Repository, dry_run: bool, force: bool, output: Output | None = None
) -> bool:
    """Pull GitHub issue body into local per-item file.

    Returns:
        True if pulled (or would pull in dry-run), False if skipped.
    """
    out = output or Output()
    issue_ref = item.issue
    num_str = issue_ref.lstrip("#")
    if not num_str.isdigit():
        return False

    issue_num = int(num_str)
    title = item.title
    filepath_str = item.file_path

    github_body = fetch_github_issue_body(repo_obj, issue_num, output=out)
    if github_body is None:
        return False

    if not filepath_str or not Path(filepath_str).exists():
        return _pull_item_create_new(item, issue_num, issue_ref, title, github_body, dry_run, output=out)

    return _pull_item_update_existing(
        item, issue_num, title, Path(filepath_str), github_body, dry_run, force, output=out
    )


# ---------------------------------------------------------------------------
# Public API: ADD  (private helpers)
# ---------------------------------------------------------------------------


def _check_for_duplicates(title: str, force: bool) -> None:
    """Raise DuplicateItemError if a fuzzy duplicate exists and force is False.

    Args:
        title: Title of the new item.
        force: When True, skip the check entirely.

    Raises:
        DuplicateItemError: If one or more similar titles are found.
    """
    if force:
        return
    existing_items = parse_backlog()
    duplicates = find_fuzzy_duplicates(title, existing_items)
    if not duplicates:
        return
    raise DuplicateItemError(duplicates)


def _resolve_filepath(priority: str, slug: str) -> Path:
    """Return a collision-free Path inside BACKLOG_DIR for (priority, slug).

    Appends a numeric suffix when the base filename already exists.

    Args:
        priority: Item priority string (e.g. "high").
        slug: URL-safe slug derived from the item title.

    Returns:
        A Path that does not yet exist on disk.
    """
    BACKLOG_DIR.mkdir(parents=True, exist_ok=True)
    base = f"{priority.lower()}-{slug}"
    filepath = BACKLOG_DIR / f"{base}.md"
    idx = 0
    while filepath.exists():
        idx += 1
        filepath = BACKLOG_DIR / f"{base}-{idx}.md"
    return filepath


def _try_create_github_issue(item_data: BacklogItem, repo: str, out: Output) -> int | None:
    """Attempt to create a GitHub issue for item_data; return issue number or None.

    Args:
        item_data: Populated BacklogItem (file_path may be empty at this stage).
        repo: Repository slug (owner/name).
        out: Output collector for warnings.

    Returns:
        Issue number on success, None when GitHub is unavailable or creation fails.
    """
    repository = try_get_github(repo)
    if repository is None:
        out.warn("  WARNING: GitHub unavailable — creating local-only item")
        return None
    try:
        return create_issue_for_item(repository, item_data, dry_run=False, output=out)
    except GithubException as e:
        out.warn(f"  WARNING: Issue creation failed: {e}")
        return None


def _build_item_body(research_first: str, files: str, suggested_location: str) -> str:
    """Build the markdown body appended below the frontmatter.

    Args:
        research_first: Optional research-first note.
        files: Optional file references.
        suggested_location: Optional suggested location note.

    Returns:
        Markdown string (empty when all inputs are empty).
    """
    parts: list[str] = []
    if research_first:
        parts.append(f"**Research first**: {research_first}")
    if files:
        parts.append(f"**Files**: {files}")
    if suggested_location:
        parts.append(f"**Suggested location**: {suggested_location}")
    return "\n".join(parts) + "\n" if parts else ""


def _write_local_item(filepath: Path, fm_str: str, body: str, issue_num: int | None, out: Output) -> None:
    """Write the frontmatter + body to disk and mark synced when an issue exists.

    Args:
        filepath: Destination path (must not already exist).
        fm_str: Rendered frontmatter block.
        body: Markdown body section.
        issue_num: GitHub issue number, or None for local-only items.
        out: Output collector forwarded to update_item_metadata.
    """
    filepath.write_text(fm_str.rstrip() + "\n\n" + body, encoding="utf-8")
    if issue_num:
        update_item_metadata(filepath, {}, set_synced=True, output=out)


# ---------------------------------------------------------------------------
# Public API: ADD
# ---------------------------------------------------------------------------


def add_item(
    title: str,
    description: str,
    priority: str,
    source: str = "Not specified",
    type_: str = "Feature",
    research_first: str = "",
    files: str = "",
    suggested_location: str = "",
    create_issue: bool = True,
    force: bool = False,
    repo: str = DEFAULT_REPO,
    output: Output | None = None,
) -> dict[str, str | int | bool | list[str]]:
    """Add item to backlog. Creates per-item file and optionally a GitHub issue.

    Returns:
        Dict with title, priority, filepath, and optionally issue_num.
    """
    out = output or Output()

    _check_for_duplicates(title, force)

    today_str = today()
    slug = title_to_slug(title)
    filepath = _resolve_filepath(priority, slug)

    # GH-first: try to create GitHub Issue BEFORE writing local file
    issue_num: int | None = None
    if create_issue:
        item_data = BacklogItem(
            title=title,
            description=description,
            source=source,
            added=today_str,
            priority=priority,
            item_type=type_,
            research_first=research_first,
            files=files,
            suggested_location=suggested_location,
        )
        issue_num = _try_create_github_issue(item_data, repo, out)

    # Build frontmatter with issue number already included (single write)
    issue_ref = f"#{issue_num}" if issue_num else ""
    fm_str = build_backlog_frontmatter(
        title, description, source, today_str, priority, type_, "open", issue_ref, "", ""
    )
    body = _build_item_body(research_first, files, suggested_location)
    _write_local_item(filepath, fm_str, body, issue_num, out)

    out.info(f"Backlog item created.\n  Title: {title}\n  Priority: {priority}\n  File: {filepath.name}")
    if issue_num:
        out.info(f"  Issue: #{issue_num}")
    out.info(f"Next steps: /groom-backlog-item {title}  /work-backlog-item {title}")

    result: dict[str, str | int | bool | list[str]] = {
        "title": title,
        "priority": priority,
        "filepath": str(filepath),
        "filename": filepath.name,
    }
    if issue_num:
        result["issue_num"] = issue_num
    return {**result, **out.to_dict()}


# ---------------------------------------------------------------------------
# Public API: LIST
# ---------------------------------------------------------------------------


def refresh_local_cache_from_github(
    repo: str = DEFAULT_REPO, label: str | None = None, output: Output | None = None
) -> dict[str, int | list[str]]:
    """Fetch open GitHub Issues and update local cache files.

    Returns:
        Dict with count of refreshed issues.
    """
    out = output or Output()
    repo_obj = try_get_github(repo)
    if repo_obj is None:
        out.warn("  WARNING: GitHub unavailable — listing from local cache only")
        return {"refreshed": 0, **out.to_dict()}

    label_objs = []
    if label:
        try:
            label_objs.append(repo_obj.get_label(label))
        except GithubException:
            out.warn(f"  WARNING: label '{label}' not found — listing all issues")

    issues = repo_obj.get_issues(state="open", labels=label_objs or GithubObject.NotSet)
    count = 0
    for issue in issues:
        if issue.pull_request is not None:
            continue
        pull_single_issue(repo_obj, issue.number, output=out)
        count += 1
    out.info(f"  Refreshed {count} issue(s) from GitHub into local cache.")
    return {"refreshed": count, **out.to_dict()}


def list_items(
    with_status: bool = False,
    from_github: bool = False,
    label: str | None = None,
    repo: str = DEFAULT_REPO,
    output: Output | None = None,
) -> dict[str, int | list[str] | list[dict[str, str | bool]]]:
    """List backlog items. Default reads local cache only. Use from_github=True to refresh first.

    Returns:
        Dict with items list (each item a dict with section, title, issue, plan,
        file_path, groomed, and optionally status/milestone).
    """
    out = output or Output()
    if from_github:
        refresh_local_cache_from_github(repo, label, output=out)
    items = parse_backlog()
    open_items = [it for it in items if not it.skip and it.section]

    status_map = batch_fetch_statuses(open_items, repo)

    result_items: list[dict[str, str | bool]] = []
    for it in open_items:
        entry: dict[str, str | bool] = {"section": it.section, "title": it.title, "issue": it.issue, "plan": it.plan}
        if it.file_path:
            entry["file_path"] = it.file_path
        if it.groomed:
            entry["groomed"] = True
        if with_status and it.issue:
            num_str = it.issue.lstrip("#")
            num = int(num_str) if num_str.isdigit() else 0
            info = status_map.get(num)
            if info is not None:
                entry["status"] = info.status
                entry["milestone"] = info.milestone
            else:
                entry["status"] = ""
                entry["milestone"] = ""
        result_items.append(entry)

    return {"items": result_items, "count": len(result_items), **out.to_dict()}


# ---------------------------------------------------------------------------
# Public API: VIEW
# ---------------------------------------------------------------------------


def view_item(
    selector: str, repo: str = DEFAULT_REPO, offset: int = 0, limit: int = 0, output: Output | None = None
) -> dict[str, str | int | bool | list[str] | None]:
    """View a backlog item or GitHub issue by URL, #N, bare number, or title.

    Args:
        selector: Issue URL, #N, bare number, or title substring.
        repo: GitHub repo in owner/repo format.
        offset: Skip N lines from the start of the body.
        limit: Show at most N body lines (0 = all, no truncation).
        output: Optional Output collector.

    Returns:
        Dict with item/issue details.
    """
    out = output or Output()
    items = parse_backlog()
    item = find_item(items, selector)
    issue_num = parse_issue_selector(selector)

    result: ViewItemResult = view_result_from_local_item(item) if item else ViewItemResult()

    if issue_num:
        if not view_enrich_from_github(result, issue_num, repo) and not item:
            raise ItemNotFoundError(selector)
    elif not item:
        raise ItemNotFoundError(selector)

    data = result.model_dump()
    # Apply pagination to body field
    body = data.get("body", "")
    if body and (offset > 0 or limit > 0):
        lines = body.splitlines()
        total = len(lines)
        if offset > 0:
            lines = lines[offset:]
        if limit > 0:
            lines = lines[:limit]
        data["body"] = "\n".join(lines)
        remaining = total - offset - len(lines)
        if remaining > 0:
            data["body_truncated"] = True
            data["body_remaining_lines"] = remaining
            data["body_total_lines"] = total

    return {**data, **out.to_dict()}


# ---------------------------------------------------------------------------
# Public API: SYNC
# ---------------------------------------------------------------------------


def find_or_create_issue(
    item: BacklogItem,
    existing_issues: dict[str, int],
    repository: Repository,
    dry_run: bool,
    output: Output | None = None,
) -> int | None:
    """Check for existing issue by title; create only if no match found.

    Returns:
        Issue number (existing or newly created), or None for dry-run creates.
    """
    out = output or Output()
    title = item.title
    normalized = normalize_issue_title(title)
    if normalized in existing_issues:
        existing_num = existing_issues[normalized]
        out.info(f"  Linked #{existing_num}: {title[:60]} (existing issue found)")
        return existing_num
    if dry_run:
        out.info(f"  [dry-run] Would create: {title[:60]}")
        return None
    return create_issue_for_item(repository, item, dry_run=False, output=out)


def sync_create_missing_issues(
    items: list[BacklogItem], repo: str, dry_run: bool, output: Output | None = None
) -> dict[str, int | bool | list[str]]:
    """Pass 1 of sync: create GitHub issues for all items that lack them.

    Before creating any issues, fetches all open issues from GitHub and checks
    for title matches. If an existing open issue matches (after stripping
    conventional-commit prefixes), links to it instead of creating a duplicate.

    Returns:
        Dict with count of created/linked issues.
    """
    out = output or Output()
    needed = items_needing_issues(items)
    if not needed:
        out.info("No items need GitHub issues created.")
        return {"created": 0, **out.to_dict()}
    out.info(f"Found {len(needed)} item(s) without GitHub issues:")
    for it in needed:
        out.info(f"  - {it.title[:60]}")
    repository = get_github(repo)

    # Dedup: fetch existing open issues to prevent duplicate creation.
    out.info("Fetching open issues for deduplication check...")
    existing_issues = fetch_open_issues_by_title(repository)
    out.info(f"  Found {len(existing_issues)} existing open issues.")

    created = 0
    for item in needed:
        issue_num = find_or_create_issue(item, existing_issues, repository, dry_run, output=out)
        if not issue_num or dry_run:
            continue
        created += 1
        # Track newly created/linked issues to prevent intra-batch duplicates.
        new_normalized = normalize_issue_title(item.title)
        if new_normalized not in existing_issues:
            existing_issues[new_normalized] = issue_num
        # Update per-item file metadata with issue number
        filepath_str = item.file_path
        if filepath_str:
            update_item_metadata(Path(filepath_str), {"metadata": {"issue": f"#{issue_num}"}}, output=out)

    return {"created": created, **out.to_dict()}


def sync_push_groomed_content(
    items: list[BacklogItem], repo: str, dry_run: bool, output: Output | None = None
) -> dict[str, int | bool | list[str]]:
    """Pass 2 of sync: push groomed content to existing GitHub issues.

    Skips items with no '## Groomed' section in their body.

    Returns:
        Dict with count of pushed items.
    """
    out = output or Output()
    groomed_items = [it for it in items_with_issues(items) if "## Groomed" in (it.raw_body or "")]
    if not groomed_items:
        out.info("No items with groomed content to push.")
        return {"pushed": 0, **out.to_dict()}
    out.info(f"Found {len(groomed_items)} item(s) with groomed content to push to GitHub:")
    if dry_run:
        for it in groomed_items:
            issue_ref = it.issue
            out.info(f"  [dry-run] Would update issue {issue_ref}: {it.title[:60]}")
        return {"pushed": 0, "dry_run": True, **out.to_dict()}
    repository = get_github(repo)

    pushed = 0
    for item in groomed_items:
        issue_ref = item.issue
        num_str = issue_ref.lstrip("#")
        if not num_str.isdigit():
            out.warn(f"  WARNING: Skipping item with invalid issue ref '{issue_ref}'")
            continue
        body = build_issue_body_from_file(item)
        if body is None:
            continue
        try:
            gh_issue = repository.get_issue(int(num_str))
            gh_issue.edit(body=body)
            out.info(f"  Updated issue #{num_str}: {item.title[:60]}")
            pushed += 1
        except GithubException as e:
            out.warn(f"  WARNING: Could not update issue #{num_str}: {e}")

    return {"pushed": pushed, **out.to_dict()}


def sync_items(
    repo: str = DEFAULT_REPO, dry_run: bool = False, output: Output | None = None
) -> dict[str, int | bool | list[str]]:
    """Create GitHub issues for all items missing them, and push groomed content to existing issues.

    Returns:
        Dict with sync results.
    """
    out = output or Output()
    items = parse_backlog()
    create_result = sync_create_missing_issues(items, repo, dry_run, output=out)
    push_result = sync_push_groomed_content(items, repo, dry_run, output=out)
    return {
        "created": create_result.get("created", 0),
        "pushed": push_result.get("pushed", 0),
        "dry_run": dry_run,
        **out.to_dict(),
    }


# ---------------------------------------------------------------------------
# Public API: CLOSE
# ---------------------------------------------------------------------------


def close_item(
    selector: str,
    plan: str,
    checklist_pass: bool = False,
    cleanup: bool = False,
    force: bool = False,
    repo: str = DEFAULT_REPO,
    output: Output | None = None,
) -> dict[str, str | bool | list[str]]:
    """Mark item DONE and close GitHub issue. Requires checklist_pass=True.

    Returns:
        Dict with closed item title and status.
    """
    out = output or Output()
    if not checklist_pass:
        raise ValidationError("checklist_pass required (skill must verify checklist first)")
    items = parse_backlog()
    item = find_item(items, selector)
    if not item:
        raise ItemNotFoundError(selector)
    issue_ref = item.issue
    if issue_ref and not force:
        issue_num_val = int(issue_ref.lstrip("#"))
        open_prs = check_open_prs_for_issue(issue_num_val, repo)
        if open_prs:
            out.warn(f"WARNING: Open PRs reference issue {issue_ref}:")
            for pr in open_prs:
                out.warn(f"  - PR #{pr.number}: {pr.title}")
                out.warn(f"    {pr.url}")
            out.warn(f"\nIssue {issue_ref} will auto-close when a PR merges with 'Fixes {issue_ref}'.")
            out.warn("Use force=True to close anyway.")
            raise BacklogError(f"Open PRs reference issue {issue_ref}. Use force=True to close anyway.")

    today()

    # Close item in index
    filepath_str = item.file_path
    if not filepath_str:
        raise BacklogError("Item has no file path")
    raw = item.raw_body
    already_closed = "**Status**: DONE" in raw or "**Completed**:" in raw
    if already_closed:
        out.info("Item already closed.")
        return {"title": item.title, "already_closed": True, **out.to_dict()}

    update_item_metadata(
        Path(filepath_str), {"metadata": {"status": "done", "priority": "completed", "plan": plan}}, output=out
    )

    out.info(f'Backlog item "{item.title}" closed.')
    if issue_ref:
        close_github_issue(issue_ref, plan, repo, output=out)
    if cleanup and issue_ref:
        _close_cleanup(item, issue_ref, repo, output=out)

    return {"title": item.title, "closed": True, **out.to_dict()}


# ---------------------------------------------------------------------------
# Public API: RESOLVE
# ---------------------------------------------------------------------------


def resolve_item(
    selector: str,
    reason: str,
    cleanup: bool = False,
    force: bool = False,
    repo: str = DEFAULT_REPO,
    output: Output | None = None,
) -> dict[str, str | bool | list[str]]:
    """Mark item RESOLVED and close GitHub issue.

    Returns:
        Dict with resolved item title and status.
    """
    out = output or Output()
    if not reason.strip():
        raise ValidationError("reason is required")
    items = parse_backlog()
    item = find_item(items, selector)
    if not item:
        raise ItemNotFoundError(selector)
    issue_ref = item.issue
    if issue_ref and not force:
        issue_num_val = int(issue_ref.lstrip("#"))
        open_prs = check_open_prs_for_issue(issue_num_val, repo)
        if open_prs:
            out.warn(f"WARNING: Open PRs reference issue {issue_ref}:")
            for pr in open_prs:
                out.warn(f"  - PR #{pr.number}: {pr.title}")
                out.warn(f"    {pr.url}")
            out.warn("\nResolving will close the issue and orphan these PRs.")
            out.warn("Use force=True to resolve anyway.")
            raise BacklogError(f"Open PRs reference issue {issue_ref}. Use force=True to resolve anyway.")

    today()

    # Resolve item in index
    filepath_str = item.file_path
    if not filepath_str:
        raise BacklogError("Item has no file path")
    raw = item.raw_body
    already_resolved = "**Resolved**:" in raw
    if already_resolved:
        out.info("Item already resolved.")
        return {"title": item.title, "already_resolved": True, **out.to_dict()}

    update_item_metadata(Path(filepath_str), {"metadata": {"status": "resolved"}}, output=out)

    out.info(f'Backlog item "{item.title}" resolved.')
    if issue_ref:
        resolve_github_issue(issue_ref, reason, repo, output=out)
    if cleanup and issue_ref:
        _close_cleanup(item, issue_ref, repo, output=out)

    return {"title": item.title, "resolved": True, **out.to_dict()}


# ---------------------------------------------------------------------------
# Public API: UPDATE
# ---------------------------------------------------------------------------


def update_item(
    selector: str,
    plan: str | None = None,
    status: str | None = None,
    create_issue: bool = False,
    groomed_file: str | None = None,
    groomed_content: str | None = None,
    section: str | None = None,
    content: str | None = None,
    groomed: bool = False,
    title: str | None = None,
    description: str | None = None,
    repo: str = DEFAULT_REPO,
    output: Output | None = None,
) -> dict[str, str | int | bool | list[str]]:
    """Update item: add Plan, set status:in-progress, create issue, or write groomed content.

    Returns:
        Dict with update results.
    """
    out = output or Output()
    items = parse_backlog()
    item = find_item(items, selector)
    if not item:
        raise ItemNotFoundError(selector)

    result: dict[str, str | int | bool | list[str]] = {"title": item.title}

    if title:
        _rename_item_title(item, title, repo, output=out)
        result["renamed_to"] = title

    if description is not None:
        _update_item_description(item, description, output=out)
        result["description_updated"] = True

    has_groomed = groomed or groomed_file or groomed_content or (section and content)
    if has_groomed:
        if not item.file_path:
            raise BacklogError("Item has no file path")
        groomed_content_val, section_name = _resolve_groomed_content(section, content, groomed_content, groomed_file)
        if not groomed_content_val.strip():
            raise ValidationError("No groomed content provided")
        _handle_update_groomed(item, groomed_content_val, section_name, repo, output=out)
        return {**result, "groomed_updated": True, **out.to_dict()}

    if plan:
        _apply_plan_to_item(item, plan, repo, output=out)
        out.info(f"  Plan: {plan}")
        result["plan"] = plan

    if create_issue and not item.issue and item.section in {"P0", "P1"}:
        issue_num = _create_issue_and_update_item(item, repo, output=out)
        if issue_num:
            out.info(f"  Issue: #{issue_num}")
            result["issue_num"] = issue_num

    if status == "in-progress" and item.issue:
        apply_status_in_progress(item, repo, output=out)
        result["status"] = "in-progress"

    return {**result, **out.to_dict()}


# ---------------------------------------------------------------------------
# Public API: GROOM
# ---------------------------------------------------------------------------


def groom_item(
    selector: str,
    groomed_file: str | None = None,
    groomed_content: str | None = None,
    section: str | None = None,
    content: str | None = None,
    repo: str = DEFAULT_REPO,
    output: Output | None = None,
) -> dict[str, str | int | bool | list[str]]:
    """Write groomed content into per-item file. Delegates to update_item.

    Returns:
        Dict with groom results.
    """
    out = output or Output()
    has_input = groomed_file or groomed_content or (section and content)
    return update_item(
        selector=selector,
        plan=None,
        status=None,
        create_issue=False,
        groomed_file=groomed_file,
        groomed_content=groomed_content,
        section=section,
        content=content,
        groomed=not has_input,
        repo=repo,
        output=out,
    )


# ---------------------------------------------------------------------------
# Public API: NORMALIZE
# ---------------------------------------------------------------------------


def normalize_items(dry_run: bool = False, output: Output | None = None) -> dict[str, int | bool | list[str]]:
    """Rewrite per-item files to research-style metadata, remove body duplication.

    Returns:
        Dict with count of normalized items.
    """
    out = output or Output()
    if not BACKLOG_DIR.exists():
        raise BacklogError(f"{BACKLOG_DIR} not found")
    pattern = re.compile(r"^(p0|p1|p2|ideas|completed)-[a-z0-9-]+\.md$", re.IGNORECASE)
    files = sorted(f for f in BACKLOG_DIR.glob("*.md") if pattern.match(f.name))
    if not files:
        out.info("No backlog item files found")
        return {"updated": 0, **out.to_dict()}
    updated = sum(1 for f in files if _normalize_item_file(f, dry_run, output=out))
    out.info(f"Normalized {updated} item file(s)" + (" [dry-run]" if dry_run else ""))
    return {"updated": updated, "dry_run": dry_run, **out.to_dict()}


# ---------------------------------------------------------------------------
# Public API: PULL
# ---------------------------------------------------------------------------


def pull_single_issue(
    repo_obj: Repository, issue_num: int, filepath: Path | None = None, output: Output | None = None
) -> Path | None:
    """Fetch a GitHub issue and write/update the local cache file.

    If filepath is None, derives it from the issue title and priority.

    Returns:
        Path to the local file, or None on failure.
    """
    out = output or Output()

    try:
        issue = repo_obj.get_issue(issue_num)
    except GithubException as e:
        out.warn(f"  WARNING: Could not fetch issue #{issue_num}: {e}")
        return None

    fields = issue_to_local_fields(issue)
    # Strip conventional-commit prefix from title (e.g., "feat: Title" -> "Title")
    raw_title = fields.title
    clean_title = _COMMIT_PREFIX_RE.sub("", raw_title).strip()

    if filepath is None:
        slug = title_to_slug(clean_title)
        filename = f"{fields.priority.lower()}-{slug}.md"
        filepath = BACKLOG_DIR / filename

    BACKLOG_DIR.mkdir(parents=True, exist_ok=True)

    if filepath.exists():
        # Update existing file: overwrite description, body, metadata
        update_item_metadata(
            filepath,
            {
                "name": clean_title,
                "description": extract_description_from_issue_body(fields.body),
                "metadata": {
                    "issue": f"#{issue_num}",
                    "priority": fields.priority,
                    "type": fields.item_type,
                    "status": fields.status,
                    "last_synced": now_iso(),
                },
            },
            output=out,
        )
        # Overwrite body sections from GitHub issue body
        _overwrite_body_from_github(filepath, fields.body)
    else:
        # Create new cache file from GitHub issue
        fm_str = build_backlog_frontmatter(
            name=clean_title,
            description=extract_description_from_issue_body(fields.body),
            source=f"GitHub Issue #{issue_num}",
            added=today(),
            priority=fields.priority,
            type_val=fields.item_type,
            status=fields.status,
            issue=f"#{issue_num}",
        )
        filepath.write_text(fm_str.rstrip() + "\n\n" + fields.body + "\n", encoding="utf-8")
        update_item_metadata(filepath, {"metadata": {"last_synced": now_iso()}}, output=out)

    return filepath


def pull_items(
    repo: str = DEFAULT_REPO, dry_run: bool = False, force: bool = False, output: Output | None = None
) -> dict[str, int | bool | list[str]]:
    """Pull issue body content from GitHub into local per-item files.

    Also auto-migrates P0/P1 items that lack GitHub Issues by creating them.
    Merges by section — keeps longer version of each section.
    Skips items with no issue number (after migration).

    Returns:
        Dict with count of pulled items.
    """
    out = output or Output()
    items = parse_backlog()

    # Auto-migration: create missing GitHub Issues for P0/P1 items
    items_without_issues = [it for it in items if it.section in {"P0", "P1"} and not it.skip and not it.issue]
    if items_without_issues:
        out.info(f"Auto-migrating {len(items_without_issues)} P0/P1 item(s) to GitHub Issues...")
        sync_create_missing_issues(items, repo, dry_run, output=out)
        # Re-parse after migration to pick up updated issue numbers
        items = parse_backlog()

    candidates = [it for it in items if it.issue and not it.skip]

    if not candidates:
        out.info("No items with GitHub issue numbers found.")
        return {"pulled": 0, **out.to_dict()}

    out.info(f"Checking {len(candidates)} item(s) with GitHub issues...")
    repository = get_github(repo)
    pulled = 0
    for item in candidates:
        if _pull_item(item, repository, dry_run, force, output=out):
            pulled += 1

    if pulled == 0:
        out.info("Nothing to pull — local files are up to date.")
    else:
        suffix = " [dry-run]" if dry_run else ""
        out.info(f"Pulled {pulled} item(s){suffix}.")

    return {"pulled": pulled, "dry_run": dry_run, **out.to_dict()}
