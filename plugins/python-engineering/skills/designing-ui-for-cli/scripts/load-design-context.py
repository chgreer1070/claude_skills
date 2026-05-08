#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# ///
"""Load design-context files for the designing-ui-for-cli skill.

Searches case-insensitively for PRODUCT.md, DESIGN.TUI.md, and DESIGN.md in the
following directories (first match per file wins):

    1. project root (cwd)
    2. context/
    3. docs/

Emits a JSON document to stdout matching this shape:

    {
      "contextDir": "<absolute path or null>",
      "product":    {"path": "<abs>", "content": "<text>", "isPlaceholder": <bool>} | null,
      "designTui":  {"path": "<abs>", "content": "<text>"} | null,
      "design":     {"path": "<abs>", "content": "<text>", "isPlaceholder": <bool>} | null
    }

Resolution rule: DESIGN.md is the base design system — it holds the full colour
palette, semantic channel tokens, typography, spacing, and component vocabulary.
DESIGN.TUI.md is a supplement that inherits from DESIGN.md and adds TUI-specific
behavioural rules (output channels, symbol set, verbosity levels, interaction
patterns).  When both are present, agents need both.  The ``design`` record is
always emitted with full content regardless of whether ``designTui`` is populated.

``isPlaceholder`` is true when PRODUCT.md is empty, smaller than 200
characters, or contains a ``[TODO]`` marker.

Exit code is 0 even when no files are found; missing fields are returned as
``null`` so the caller can branch deterministically.

Mirrors the JSON output shape of impeccable's ``load-context.mjs`` with the
``designTui`` extension added for TUI projects.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

PRODUCT_NAMES = ("PRODUCT.md",)
DESIGN_TUI_NAMES = ("DESIGN.TUI.md",)
DESIGN_NAMES = ("DESIGN.md",)
SEARCH_DIRS = ("", "context", "docs")
PLACEHOLDER_MIN_CHARS = 200
PLACEHOLDER_MARKER = "[TODO]"


def _index_directory(directory: Path) -> dict[str, Path]:
    """Return a mapping of ``filename.lower() → resolved Path`` for every file in ``directory``.

    Returns an empty dict when ``directory`` does not exist or is not a directory.
    Each directory is listed exactly once; callers resolve multiple names by
    dictionary lookup rather than repeated ``iterdir`` calls.
    """
    if not directory.is_dir():
        return {}
    return {entry.name.lower(): entry.resolve() for entry in directory.iterdir() if entry.is_file()}


def _resolve_name_lists(cwd: Path, *name_lists: tuple[str, ...]) -> tuple[Path | None, ...]:
    """Search SEARCH_DIRS with a single ``iterdir`` per directory and resolve each name list.

    For each search directory the directory is listed once; every name list is
    resolved against that index before moving to the next directory.  The
    first-match-wins semantics of the original per-list search are preserved:
    for each name list, the result is the first hit found across directories in
    SEARCH_DIRS order.

    Args:
        cwd: Absolute path of the project root used as the first search directory.
        *name_lists: One or more tuples of candidate filenames to resolve
            independently (case-insensitive).

    Returns:
        A tuple of ``Path | None`` values, one per name list, in the same order
        as the input name lists.
    """
    results: list[Path | None] = [None] * len(name_lists)
    pending = list(range(len(name_lists)))  # indices not yet resolved

    for rel in SEARCH_DIRS:
        if not pending:
            break
        directory = (cwd / rel).resolve() if rel else cwd
        index = _index_directory(directory)
        still_pending: list[int] = []
        for i in pending:
            hit: Path | None = None
            for name in name_lists[i]:
                hit = index.get(name.lower())
                if hit is not None:
                    break
            if hit is not None:
                results[i] = hit
            else:
                still_pending.append(i)
        pending = still_pending

    return tuple(results)


def is_placeholder(content: str) -> bool:
    """Return True if PRODUCT.md content is empty, too short, or marked TODO."""
    if not content.strip():
        return True
    if len(content) < PLACEHOLDER_MIN_CHARS:
        return True
    return PLACEHOLDER_MARKER in content


def build_file_record(path: Path, *, with_placeholder: bool = False) -> dict[str, object]:
    """Read ``path`` and assemble the JSON record for it.

    Args:
        path: File to read.
        with_placeholder: When ``True``, add an ``isPlaceholder`` key derived
            from the file's content.

    Returns:
        Dict with ``path`` and ``content`` keys, plus ``isPlaceholder`` when
        ``with_placeholder`` is true.
    """
    content = path.read_text(encoding="utf-8")
    record: dict[str, object] = {"path": str(path), "content": content}
    if with_placeholder:
        record["isPlaceholder"] = is_placeholder(content)
    return record


def load_design_context(cwd: Path) -> dict[str, object]:
    """Locate context files relative to ``cwd`` and assemble the result dict.

    Uses a single ``iterdir`` call per search directory (via
    ``_resolve_name_lists``) instead of re-scanning for each name list.  At
    most 3 ``iterdir`` calls occur (one per entry in ``SEARCH_DIRS``), compared
    to up to 9 in the original implementation.

    DESIGN.md is always emitted with full content: it is the base design
    system (colours, tokens, typography, components).  DESIGN.TUI.md
    supplements it with TUI-specific behavioural rules.  Agents need both.

    Returns:
        Dict with ``contextDir``, ``product``, ``designTui``, and ``design``
        keys. Each file field is either a record dict or ``None``.
    """
    product_path, design_tui_path, design_path = _resolve_name_lists(cwd, PRODUCT_NAMES, DESIGN_TUI_NAMES, DESIGN_NAMES)

    first_match = next((p for p in (product_path, design_tui_path, design_path) if p is not None), None)
    context_dir = str(first_match.parent) if first_match is not None else None

    return {
        "contextDir": context_dir,
        "product": (build_file_record(product_path, with_placeholder=True) if product_path is not None else None),
        "designTui": (build_file_record(design_tui_path) if design_tui_path is not None else None),
        "design": (build_file_record(design_path, with_placeholder=True) if design_path is not None else None),
    }


def main() -> int:
    """Print the design-context JSON to stdout.

    Returns:
        ``0`` on the normal success path; missing files do not raise.
    """
    cwd = Path.cwd().resolve()
    result = load_design_context(cwd)
    sys.stdout.write(json.dumps(result))
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
