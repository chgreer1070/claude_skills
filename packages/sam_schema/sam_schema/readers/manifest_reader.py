"""Global-manifest reader for SAM task/plan files.

Reads ``.md`` files with a global YAML frontmatter header containing plan
metadata (``feature:``, ``tasks:`` list) and per-task prose sections structured
as task headings in the markdown body.

This is the format that triggered issue #715 — the previous implementation
returned zero tasks for this format because no per-task YAML blocks were found.

The manifest format has a global frontmatter block containing:
- Plan-level metadata (feature, version, description, etc.)
- A ``tasks:`` list that holds task metadata in two possible structures:
  1. Simple ``{TN: "title"}`` mapping entries: ``- T1: State handler helper functions``
  2. Full task dicts: ``- {id: T1, title: "...", status: "not-started", ...}``
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from sam_schema.readers._yaml_utils import coerce_to_plain, load_yaml
from sam_schema.readers.detect import FormatType

if TYPE_CHECKING:
    from pathlib import Path

# Heading patterns for task prose sections in the body
# Matches: ## TN:, ## TN -, ### TN:, ### Task N:, #### TN
_TASK_SECTION_RE = re.compile(r"^(?:#{1,4})\s+(?:Task\s+)?([A-Za-z]?\d+(?:\.\d+)?)\s*[:\-]\s*(.*?)$", re.MULTILINE)


def _extract_task_id_title_from_entry(entry: dict) -> tuple[str, str] | None:
    """Extract task ID and title from a ``tasks:`` list entry.

    Handles two entry formats:
    1. Simple single-key mapping: ``{T1: "State handler helper functions"}``
       YAML representation: ``- T1: State handler helper functions``
    2. Full task dict: ``{id: T1, title: "...", status: "not-started"}``

    Args:
        entry: A single item from the ``tasks:`` YAML list.

    Returns:
        ``(task_id, title)`` tuple, or ``None`` if the entry cannot be parsed.
    """
    if not isinstance(entry, dict):
        return None

    # Full task dict format: has ``id:`` or ``task:`` field
    if "id" in entry or "task" in entry:
        task_id = str(entry.get("id") or entry.get("task") or "")
        title = str(entry.get("title") or "")
        return (task_id, title) if task_id else None

    # Simple mapping format: ``{TN: "title"}`` — exactly one key
    if len(entry) == 1:
        key, value = next(iter(entry.items()))
        task_id = str(key)
        title = str(value) if value else ""
        return (task_id, title)

    return None


def _extract_prose_sections(body: str) -> dict[str, str]:
    """Extract prose content per task from the markdown body.

    Looks for headings matching task ID patterns (e.g., ``## T1:``, ``### T1 -``).

    Args:
        body: Markdown body text after the closing ``---`` of the frontmatter.

    Returns:
        Dict mapping task ID string to the prose body text for that task section.
    """
    section_matches = list(_TASK_SECTION_RE.finditer(body))
    sections: dict[str, str] = {}

    for idx, match in enumerate(section_matches):
        task_id = match.group(1)
        section_start = match.end()
        section_end = section_matches[idx + 1].start() if idx + 1 < len(section_matches) else len(body)
        prose = body[section_start:section_end].strip()
        sections[task_id] = prose

    return sections


def _build_task_dict(entry: dict, prose_by_task: dict[str, str]) -> dict | None:
    """Build a raw task dict from a manifest ``tasks:`` entry.

    Merges structured fields (from YAML list entry) with prose content
    from the matching body section.

    Args:
        entry: A coerced dict entry from the ``tasks:`` YAML list.
        prose_by_task: Map from task ID to its prose section text.

    Returns:
        Raw task dict, or ``None`` if the entry cannot be parsed.
    """
    if not isinstance(entry, dict):
        return None

    # Full task dict: has ``id:`` or ``task:`` field
    if "id" in entry or "task" in entry:
        task_dict = dict(entry)
        task_id = str(task_dict.get("id") or task_dict.get("task") or "")
        if not task_id:
            return None
        task_dict.setdefault("task", task_id)
        prose = prose_by_task.get(task_id, "")
        if prose:
            task_dict.setdefault("description", prose)
        return task_dict

    # Simple single-key mapping: {TN: "title"}
    parsed = _extract_task_id_title_from_entry(entry)
    if not parsed:
        return None
    task_id, title = parsed
    task_dict = {"task": task_id, "title": title, "status": "not-started"}
    prose = prose_by_task.get(task_id, "")
    if prose:
        task_dict["description"] = prose
    return task_dict


def read_manifest_plan(path: Path) -> tuple[dict, list[dict], FormatType]:
    """Read a global-manifest format plan file.

    The global manifest format has:
    - A single YAML frontmatter block at the top with plan-level metadata
      and a ``tasks:`` list containing task metadata (simple or full dicts).
    - A markdown body with optional task prose sections.

    The reader merges the structured task metadata from the YAML ``tasks:`` list
    with any prose content from the matching body sections.

    Args:
        path: Path to a ``.md`` file with a global manifest frontmatter structure.

    Returns:
        A tuple of ``(plan_meta_dict, task_dicts, FormatType.GLOBAL_MANIFEST)``
        where each task dict contains both the structured fields from the YAML
        ``tasks:`` list and any prose content from the body sections.

    Raises:
        FileNotFoundError: If ``path`` does not exist.
        ValueError: If the frontmatter cannot be parsed or has no recognized task list.
    """
    if not path.exists():
        msg = f"Path does not exist: {path}"
        raise FileNotFoundError(msg)

    content = path.read_text(encoding="utf-8")

    if not (content.startswith(("---\n", "---\r\n"))):
        msg = f"Expected file to start with '---' frontmatter: {path}"
        raise ValueError(msg)

    # Strip the leading "---\n"
    after_open = content[4:]

    # Find the closing delimiter for the frontmatter block
    close_match = re.search(r"\n---\s*\n", after_open)
    if not close_match:
        msg = f"No closing '---' found for frontmatter block in {path}"
        raise ValueError(msg)

    frontmatter_text = after_open[: close_match.start()]
    body = after_open[close_match.end() :]

    # Parse the frontmatter YAML
    parsed_fm = load_yaml(frontmatter_text)
    if not isinstance(parsed_fm, dict):
        msg = f"Expected a YAML mapping in frontmatter of {path}, got {type(parsed_fm).__name__}"
        raise TypeError(msg)

    parsed_fm = coerce_to_plain(parsed_fm)

    # Extract the ``tasks:`` list from frontmatter
    tasks_raw = parsed_fm.pop("tasks", None)

    # Build plan metadata: strip task list, normalize ``slug:`` -> ``feature:`` if needed
    plan_meta = dict(parsed_fm)
    if "feature" not in plan_meta and "slug" in plan_meta:
        plan_meta["feature"] = plan_meta.pop("slug")

    if "feature" not in plan_meta:
        # Derive feature from filename
        slug = re.sub(r"^tasks-\d+-", "", path.stem)
        plan_meta["feature"] = slug

    if not tasks_raw:
        msg = f"No 'tasks:' list found in frontmatter of {path}"
        raise ValueError(msg)

    if not isinstance(tasks_raw, list):
        msg = f"Expected 'tasks:' to be a list in {path}"
        raise TypeError(msg)

    # Extract prose sections from body keyed by task ID
    prose_by_task = _extract_prose_sections(body)

    # Build per-task dicts by merging metadata + prose
    task_dicts: list[dict] = []
    for raw_entry in tasks_raw:
        entry: dict = coerce_to_plain(raw_entry)
        task_dict = _build_task_dict(entry, prose_by_task)
        if task_dict is not None:
            task_dicts.append(task_dict)

    return plan_meta, task_dicts, FormatType.GLOBAL_MANIFEST
