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


def _parse_embedded_task_blocks(
    plan_meta: dict[str, Any], body: str, path: Path
) -> tuple[dict, list[dict], FormatType]:
    """Parse per-task YAML blocks embedded in the markdown body.

    Used by the multi-task frontmatter variant where the first ``---`` block
    is plan-level metadata and per-task YAML blocks follow in the body,
    separated by ``---`` delimiters (outside code fences).

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
    task_dicts: list[dict] = []
    for raw_segment in segments:
        segment = raw_segment.strip()
        if not segment:
            continue
        try:
            task_dict = _load_yaml_block(segment)
        except ValueError:
            # Not a valid YAML block (prose, etc.) — skip
            continue
        if "task" in task_dict or "task_id" in task_dict:
            task_id = task_dict.get("task") or task_dict.get("task_id")
            if task_id is not None:
                task_dict["task"] = str(task_id)
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
