"""YAML-frontmatter-in-markdown reader for SAM task/plan files.

Reads ``.md`` files where each task is delimited by ``---`` YAML frontmatter
blocks. Handles both single-task files and multi-task monolithic files.

The reader correctly skips ``---`` delimiters that appear inside Markdown
code fences (triple-backtick blocks) to avoid spurious task splits.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

from sam_schema.readers._yaml_utils import coerce_to_plain, load_yaml
from sam_schema.readers.detect import FormatType

if TYPE_CHECKING:
    from pathlib import Path


def _load_yaml_block(text: str) -> dict[str, Any]:
    """Parse a single YAML block string using ruamel.yaml round-trip mode.

    Args:
        text: Raw YAML text (without ``---`` delimiters).

    Returns:
        Parsed dict.

    Raises:
        ValueError: If the text cannot be parsed as a YAML mapping.
    """
    result = load_yaml(text)

    if not isinstance(result, dict):
        msg = f"Expected a YAML mapping, got {type(result).__name__}"
        raise TypeError(msg)

    # Coerce CommentedMap/Seq to plain Python types
    return coerce_to_plain(result)


def _split_outside_fences(body: str) -> list[str]:
    """Split a markdown body on ``---`` delimiters, ignoring those inside code fences.

    A ``---`` delimiter inside a triple-backtick code fence is NOT treated as a
    task section separator. This prevents spurious task splits when task body
    content contains YAML code examples.

    Args:
        body: Markdown text that may contain multiple YAML task blocks separated
              by ``---`` lines and interspersed prose.

    Returns:
        List of segments split on section delimiters that are outside code fences.
    """
    # We walk through the body tracking whether we're inside a code fence.
    # When outside, we detect ``\n---+\n`` as a segment boundary.
    segments: list[str] = []
    current_parts: list[str] = []
    in_fence = False

    # Split on code fence boundaries first to identify fence regions
    # Strategy: scan line by line, toggle fence state on ``` lines,
    # accumulate content, and flush segment on delimiter lines outside fences.
    lines = body.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i]

        # Toggle code fence state on ``` lines
        if line.startswith("```"):
            in_fence = not in_fence
            current_parts.append(line)
            i += 1
            continue

        # Outside fence: check if this line is a --- delimiter
        if not in_fence and re.match(r"^---+\s*$", line):
            # Flush current segment
            segments.append("\n".join(current_parts))
            current_parts = []
            i += 1
            continue

        current_parts.append(line)
        i += 1

    # Flush the last segment
    segments.append("\n".join(current_parts))
    return segments


def _parse_prose_fields(prose: str) -> dict[str, str]:
    """Extract named content sections from a markdown prose segment.

    Looks for ``## SectionName`` or ``### SectionName`` headings and collects
    the text beneath each one.  The results are mapped to canonical task field
    names so they can be merged into a task dict.

    Recognised section → field mappings (case-insensitive):

    - Context / Background → ``description`` (combined with Objective /
      Requirements if those are also present)
    - Objective → ``objective``
    - Requirements → ``requirements``
    - Constraints → ``constraints``
    - Expected Outputs / Expected Output → ``expected-outputs``
    - Acceptance Criteria / Acceptance → ``acceptance-criteria``
    - Verification Steps / Verification / CoVe Checks / CoVe → ``verification-steps``
    - Context Notes → ``context-notes``
    - Handoff → ``handoff``

    When multiple sections map to ``description`` (Context + Objective +
    Requirements), only ``description`` is populated; the others are left in
    their own fields as well.

    Args:
        prose: Raw markdown text, possibly starting with section headings.

    Returns:
        Dict of canonical field name → text content.  Only non-empty sections
        are included.
    """
    # Heading pattern: ## or ### followed by text
    heading_re = re.compile(r"^(?:#{2,4})\s+(.+)$", re.MULTILINE)
    matches = list(heading_re.finditer(prose))

    # Map heading names to canonical field names
    HEADING_TO_FIELD: dict[str, str] = {
        "context": "description",
        "background": "description",
        "objective": "objective",
        "requirements": "requirements",
        "constraints": "constraints",
        "expected outputs": "expected-outputs",
        "expected output": "expected-outputs",
        "acceptance criteria": "acceptance-criteria",
        "acceptance": "acceptance-criteria",
        "verification steps": "verification-steps",
        "verification": "verification-steps",
        "cove checks": "verification-steps",
        "cove": "verification-steps",
        "context notes": "context-notes",
        "handoff": "handoff",
    }

    result: dict[str, str] = {}

    if not matches:
        # No headings — treat the whole prose as description
        stripped = prose.strip()
        if stripped:
            result["description"] = stripped
        return result

    for idx, match in enumerate(matches):
        heading_text = match.group(1).strip()
        field = HEADING_TO_FIELD.get(heading_text.lower())
        if field is None:
            continue

        section_start = match.end()
        section_end = matches[idx + 1].start() if idx + 1 < len(matches) else len(prose)
        content = prose[section_start:section_end].strip()
        if not content:
            continue

        if field in result:
            # Append to existing content (e.g. multiple sections → description)
            result[field] = result[field] + "\n\n" + content
        else:
            result[field] = content

    return result


def _parse_embedded_task_blocks(
    plan_meta: dict[str, Any], body: str, path: Path
) -> tuple[dict, list[dict], FormatType]:
    """Parse per-task YAML blocks embedded in the markdown body.

    Used by the multi-task frontmatter variant where the first ``---`` block
    is plan-level metadata and per-task YAML blocks follow in the body,
    separated by ``---`` delimiters (outside code fences).

    Each task YAML block may be followed immediately by a prose segment
    containing markdown sections such as ``## Context``, ``## Acceptance
    Criteria``, and ``## Verification Steps``.  These are parsed by
    ``_parse_prose_fields`` and merged into the task dict so that content
    fields (``description``, ``acceptance-criteria``, ``verification-steps``,
    etc.) survive the read → write round-trip.

    Args:
        plan_meta: Parsed plan-level metadata from the first frontmatter block.
        body: Markdown body text after the closing ``---`` of the first block.
        path: Source path (used in error messages).

    Returns:
        ``(plan_meta, task_dicts, FormatType.YAML_FRONTMATTER)``.

    Raises:
        ValueError: If no valid task blocks are found in the body.
    """
    segments = _split_outside_fences(body)

    # Build a list of (is_task, dict_or_prose) pairs so we can look ahead
    # to the segment immediately following each task YAML block.
    parsed_segments: list[tuple[bool, Any]] = []
    for raw_segment in segments:
        segment = raw_segment.strip()
        if not segment:
            parsed_segments.append((False, ""))
            continue
        try:
            block = _load_yaml_block(segment)
        except (ValueError, TypeError):
            # Not a valid YAML mapping (prose, comment, etc.) — keep as prose
            parsed_segments.append((False, segment))
            continue

        is_task_block = ("task" in block or "task_id" in block) and bool(block.get("task") or block.get("task_id"))
        parsed_segments.append((is_task_block, block))

    task_dicts: list[dict] = []
    for idx, (is_task, payload) in enumerate(parsed_segments):
        if not is_task:
            continue
        task_dict = dict(payload)
        task_id = task_dict.get("task") or task_dict.get("task_id")
        task_dict["task"] = str(task_id)

        # Look at the immediately following non-empty segment.  If it is prose
        # (not another task YAML block), parse it for content fields.
        next_idx = idx + 1
        while next_idx < len(parsed_segments):
            next_is_task, next_payload = parsed_segments[next_idx]
            if isinstance(next_payload, str) and not next_payload:
                # Empty segment — skip over it
                next_idx += 1
                continue
            if not next_is_task and isinstance(next_payload, str) and next_payload:
                # Prose segment immediately following the task YAML block
                prose_fields = _parse_prose_fields(next_payload)
                for field, value in prose_fields.items():
                    task_dict.setdefault(field, value)
            break

        task_dicts.append(task_dict)

    if not task_dicts:
        msg = f"No task blocks found in {path}"
        raise ValueError(msg)
    return dict(plan_meta), task_dicts, FormatType.YAML_FRONTMATTER


def _parse_tasks_list_block(tasks_value: list[Any], path: Path) -> tuple[dict, list[dict], FormatType]:
    """Extract task dicts from a frontmatter ``tasks:`` list.

    Handles the tasks-list variant where a single frontmatter block contains a
    ``tasks:`` key whose value is a list of task dicts.  Each non-dict item in
    the list is silently skipped.  Raises if the resulting task list is empty.

    Args:
        tasks_value: The raw list value from the ``tasks:`` frontmatter key.
        path: Source path (used in error messages).

    Returns:
        ``({}, task_dicts, FormatType.YAML_FRONTMATTER)`` with an empty plan-meta
        dict, because there is no separate plan-level metadata in this format.

    Raises:
        ValueError: If no valid task dicts are found in ``tasks_value``.
    """
    task_dicts: list[dict] = []
    for raw_item in tasks_value:
        if not isinstance(raw_item, dict):
            continue
        task_entry = dict(raw_item)  # copy to avoid mutating the parsed value
        task_id = task_entry.get("task") or task_entry.get("task_id")
        if task_id is not None:
            task_entry.setdefault("task", str(task_id))
        task_dicts.append(task_entry)
    if not task_dicts:
        msg = f"No task entries found in frontmatter 'tasks:' list in {path}"
        raise ValueError(msg)
    return {}, task_dicts, FormatType.YAML_FRONTMATTER


def read_frontmatter_plan(path: Path) -> tuple[dict, list[dict], FormatType]:
    r"""Read a YAML-frontmatter-in-markdown plan file.

    Supports three file structures:
    - **Tasks-list**: File has a single ``---`` block with a ``tasks:`` list key.
      Each list item is a task dict.  The body below the closing ``---`` is prose
      only and is not parsed for task blocks.
    - **Single-task**: File has a single ``---`` block with ``task:`` field.
    - **Multi-task**: File starts with a global manifest ``---`` block (``feature:``
      field, no ``task:`` field) followed by per-task ``---`` blocks embedded in
      the markdown body. Task blocks are split on ``\n---+\n`` but only outside
      code fences.

    Args:
        path: Path to a ``.md`` file with YAML frontmatter task blocks.

    Returns:
        A tuple of ``(plan_meta_dict, task_dicts, FormatType.YAML_FRONTMATTER)``.

    Raises:
        FileNotFoundError: If ``path`` does not exist.
        ValueError: If no valid task blocks can be extracted.
    """
    if not path.exists():
        msg = f"Path does not exist: {path}"
        raise FileNotFoundError(msg)

    content = path.read_text(encoding="utf-8")
    return _parse_frontmatter_content(content, path)


def _parse_frontmatter_content(content: str, path: Path) -> tuple[dict, list[dict], FormatType]:
    """Parse frontmatter content from a string.

    Args:
        content: Full file content.
        path: Source path (used in error messages).

    Returns:
        ``(plan_meta_dict, task_dicts, FormatType.YAML_FRONTMATTER)``.

    Raises:
        ValueError: If the structure is unrecognizable.
    """
    if not (content.startswith(("---\n", "---\r\n"))):
        msg = f"Expected file to start with '---' frontmatter: {path}"
        raise ValueError(msg)

    # Strip the leading "---\n"
    after_open = content[4:]

    # Find the closing delimiter for the first YAML block
    close_match = re.search(r"\n---\s*\n", after_open)
    if not close_match:
        msg = f"No closing '---' found for first YAML block in {path}"
        raise ValueError(msg)

    first_yaml_text = after_open[: close_match.start()]
    body = after_open[close_match.end() :]

    try:
        first_block = _load_yaml_block(first_yaml_text)
    except ValueError as exc:
        msg = f"Failed to parse frontmatter in {path}: {exc}"
        raise ValueError(msg) from exc

    # CASE 0: Tasks-list variant — first block has a ``tasks:`` key whose value is
    # a list of task dicts.  Each list item is a self-contained task object.  The
    # body below the closing ``---`` is human-readable prose and is not parsed for
    # task blocks.  About 20 follow-up task files in ``plan/`` use this format.
    tasks_value = first_block.get("tasks")
    if isinstance(tasks_value, list):
        return _parse_tasks_list_block(tasks_value, path)

    # CASE 1: Single-task file — first block has ``task:`` field
    if "task" in first_block or "task_id" in first_block:
        task_id = first_block.get("task") or first_block.get("task_id")
        if task_id is not None:
            first_block.setdefault("task", str(task_id))
        return {}, [first_block], FormatType.YAML_FRONTMATTER

    # CASE 2: Multi-task file — first block is plan metadata (has ``feature:`` field)
    # Per-task blocks are embedded in the body, separated by ``---`` lines.
    return _parse_embedded_task_blocks(first_block, body, path)
