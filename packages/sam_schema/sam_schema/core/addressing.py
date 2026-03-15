"""Plan addressing module for SAM task/plan files.

Resolves human-readable address strings (``P1/T3``, ``P1``, ``my-slug/T3``)
to file system paths, and parses address components for use by the CLI and
MCP server.

Address format:
    ``P{N}`` — plan by sequence number (matches ``tasks-{N}-{slug}.*`` filename)
    ``P{slug}`` — plan by slug substring match
    ``P{N}/T{M}`` — task within a plan
    ``P{slug}/T{M}`` — task within a plan by slug
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

# Pattern: tasks-{N}-{slug}.yaml / tasks-{N}-{slug}.md / tasks-{N}-{slug}/
_TASKS_NUMERIC_RE = re.compile(r"^tasks-(\d+)-")


class AddressingError(Exception):
    """Raised when an address cannot be resolved to a file system path.

    Args:
        address: The address string that failed to resolve.
        plan_dir: The directory that was searched.
    """

    def __init__(self, address: str, plan_dir: Path) -> None:
        """Initialize AddressingError with the unresolvable address and search directory."""
        self.address = address
        self.plan_dir = plan_dir
        super().__init__(f"Cannot resolve address '{address}' in plan directory '{plan_dir}'.")


def resolve_plan_address(address: str, plan_dir: Path) -> Path:
    """Resolve a plan address string to a file system path.

    Resolution order:
    1. If ``address`` is a digit-prefixed reference (``P{N}``), match filenames
       with pattern ``tasks-{N}-*``.
    2. If ``address`` is a slug reference (``P{slug}``), match filenames
       containing the slug substring.
    3. If no match is found, raise ``AddressingError``.

    Args:
        address: Plan address string such as ``"P1"`` or ``"my-feature-slug"``.
                 Leading ``P`` prefix is stripped before matching.
        plan_dir: Directory to search for plan files and directories.

    Returns:
        Resolved path to the plan file or directory.

    Raises:
        AddressingError: If no plan matching the address is found.
        FileNotFoundError: If ``plan_dir`` does not exist.
    """
    if not plan_dir.exists():
        msg = f"Plan directory does not exist: {plan_dir}"
        raise FileNotFoundError(msg)

    # Strip leading P/p prefix if present
    ref = address.lstrip("Pp") if address.upper().startswith("P") else address

    # Collect all candidate entries: .yaml files, .md files, directories
    candidates: list[Path] = sorted([p for p in plan_dir.iterdir() if p.name.startswith("tasks-")])

    # Phase 1: numeric match — search for tasks-{N}-* where N == ref
    if ref.isdigit():
        numeric_matches = [p for p in candidates if (m := _TASKS_NUMERIC_RE.match(p.name)) and m.group(1) == ref]
        if numeric_matches:
            return numeric_matches[0]
        raise AddressingError(address, plan_dir)

    # Phase 2: slug substring match
    slug_matches = [p for p in candidates if ref in p.name]
    if slug_matches:
        return slug_matches[0]

    raise AddressingError(address, plan_dir)


def parse_address(address: str) -> tuple[str, str | None]:
    """Parse a task address string into its plan and task components.

    Args:
        address: Address string in one of the following forms:
                 - ``"P1/T3"`` → plan reference ``"1"``, task reference ``"3"``
                 - ``"P1"`` → plan reference ``"1"``, task reference ``None``
                 - ``"my-slug/T3"`` → plan reference ``"my-slug"``, task ``"3"``
                 - ``"my-slug"`` → plan reference ``"my-slug"``, task ``None``

    Returns:
        A tuple ``(plan_ref, task_ref)`` where ``task_ref`` is ``None`` if no
        task component is present.

    Raises:
        ValueError: If the address string cannot be parsed.
    """
    if not address or not address.strip():
        msg = f"Address cannot be empty: {address!r}"
        raise ValueError(msg)

    # Split on "/" to separate plan and task components
    parts = address.split("/", 1)
    plan_part = parts[0].strip()

    if not plan_part:
        msg = f"Address has empty plan component: {address!r}"
        raise ValueError(msg)

    # Strip leading P/p prefix from plan component
    plan_ref = plan_part[1:] if plan_part.upper().startswith("P") and len(plan_part) > 1 else plan_part

    if len(parts) == 1:
        return plan_ref, None

    task_part = parts[1].strip()
    if not task_part:
        msg = f"Address has empty task component: {address!r}"
        raise ValueError(msg)

    # Strip leading T/t prefix from task component
    task_ref = task_part[1:] if task_part.upper().startswith("T") and len(task_part) > 1 else task_part

    return plan_ref, task_ref
