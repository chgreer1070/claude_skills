#!/usr/bin/env -S uv run --quiet --script
# /// script
# requires-python = ">=3.11"
# ///
"""Check for broken symlinks. Windows-compatible.

The upstream pre-commit-hooks check-symlinks uses os.path.exists(path) for
symlinks. On Windows, os.path.exists() returns False for symlinks even when
the target exists, causing false positives. This script uses
Path(path).resolve().exists() which correctly follows symlinks on Windows.

Accepts filenames from pre-commit (pass_filenames). Exits 1 if any symlink
points to a non-existent target.
"""

from __future__ import annotations

import sys
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    """Check filenames for broken symlinks.

    Returns:
        0 if all symlinks valid, 1 if any broken.
    """
    filenames = argv[1:] if argv is not None else sys.argv[1:]
    retv = 0

    for filename in filenames:
        path = Path(filename)
        if not path.is_symlink():
            continue
        try:
            resolved = path.resolve()
        except OSError:
            resolved = None
        if resolved is None or not resolved.exists():
            print(f"{filename}: Broken symlink")
            retv = 1

    return retv


if __name__ == "__main__":
    sys.exit(main())
