"""Pure YAML file I/O for backlog items.

Primary read/write module for ``.yaml`` backlog item files.  Provides a
format-detecting reader that handles legacy ``.md`` files during the
transition period.
"""

from __future__ import annotations

import warnings
from io import StringIO
from typing import TYPE_CHECKING, Literal

from ruamel.yaml import YAML

from .models import BacklogItem
from .parsing import parse_item_file

if TYPE_CHECKING:
    from pathlib import Path

__all__ = ["detect_format", "load_item", "load_item_text", "save_item"]


def detect_format(path: Path) -> Literal["yaml", "legacy_md"]:
    """Return the file format based on path suffix.

    Args:
        path: Path to the backlog item file.

    Returns:
        ``'yaml'`` for ``.yaml`` files, ``'legacy_md'`` for ``.md`` files.

    Raises:
        ValueError: If the suffix is neither ``.yaml`` nor ``.md``.
    """
    if path.suffix == ".yaml":
        return "yaml"
    if path.suffix == ".md":
        return "legacy_md"
    raise ValueError(f"Unsupported file extension: {path.suffix!r} — expected '.yaml' or '.md'")


def load_item(path: Path) -> BacklogItem:
    """Load a backlog item from a file.

    Detects format from the file suffix and dispatches to the appropriate
    parser.  Legacy ``.md`` files emit a ``DeprecationWarning``.

    Args:
        path: Path to the backlog item file (``.yaml`` or ``.md``).

    Returns:
        Parsed ``BacklogItem`` with ``file_path`` set to the resolved path.

    Raises:
        ValueError: If the file extension is not supported.
    """
    fmt = detect_format(path)
    if fmt == "yaml":
        yaml = YAML(typ="safe")
        with path.open(encoding="utf-8") as fh:
            data = yaml.load(fh)
        item = BacklogItem.model_validate(data)
        item.file_path = str(path.resolve())
        return item
    # fmt == "legacy_md"
    warnings.warn(
        f"Loading backlog item from legacy .md format: {path}. Migrate to .yaml format.",
        DeprecationWarning,
        stacklevel=2,
    )
    text = path.read_text(encoding="utf-8")
    item = parse_item_file(text, path)
    item.file_path = str(path.resolve())
    return item


def save_item(item: BacklogItem, path: Path) -> None:
    """Write a backlog item to a YAML file.

    Always writes ``.yaml`` format regardless of the original file extension.
    Line-wrapping is disabled so long field values are not broken.

    Args:
        item: The ``BacklogItem`` to serialise.
        path: Destination path (should have ``.yaml`` suffix).
    """
    data = item.model_dump(exclude={"file_path", "skip"})
    yaml = YAML(typ="rt")
    yaml.default_flow_style = False
    yaml.width = 2147483647
    with path.open("w", encoding="utf-8") as fh:
        yaml.dump(data, fh)


def load_item_text(text: str, path: Path) -> BacklogItem:
    """Load a backlog item from an in-memory string.

    Useful for testing without disk I/O.  Format is detected from ``path``
    suffix; the file does not need to exist on disk.

    Args:
        text: Raw file content string.
        path: Path used only to determine format via suffix (``.yaml`` or
            ``.md``).  The file is not read from disk.

    Returns:
        Parsed ``BacklogItem`` with ``file_path`` set to ``str(path)``.

    Raises:
        ValueError: If the path suffix is not supported.
    """
    fmt = detect_format(path)
    if fmt == "yaml":
        yaml = YAML(typ="safe")
        data = yaml.load(StringIO(text))
        item = BacklogItem.model_validate(data)
        item.file_path = str(path)
        return item
    # fmt == "legacy_md"
    item = parse_item_file(text, path)
    item.file_path = str(path)
    return item
