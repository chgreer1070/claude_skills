"""Backend-neutral rendering utilities for backlog sections.

This module extracts rendering logic from ``github_sync`` into a shared,
backend-agnostic location.  All three BacklogBackend implementations (GitHub,
SQLite, memory) import from here so that section rendering is identical across
backends.

Dependency direction (must remain acyclic):
    models <- rendering

Do not import from github_sync, operations, gh_client, or server.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .models import GroomedData

__all__ = [
    "GROOMED_SUBSECTION_ORDER",
    "SECTION_HEADING",
    "render_groomed_section",
    "section_display_title",
    "unknown_key_to_heading",
]

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Section key (used in BacklogItem.sections) -> markdown heading text
SECTION_HEADING: dict[str, str] = {
    "fact_check": "Fact-Check",
    "rt_ica": "RT-ICA",
    "issue_classification": "Issue Classification",
}

# Frozenset of the display values in SECTION_HEADING.
# Used by section_display_title to recognise display-name keys stored verbatim
# (e.g. "RT-ICA") that bypass the snake_case lookup but are already correct.
_SECTION_HEADING_VALUES: frozenset[str] = frozenset(SECTION_HEADING.values())

# Canonical render order for GroomedData subsections (heading text as stored)
GROOMED_SUBSECTION_ORDER: list[str] = [
    "Priority",
    "Impact",
    "Benefits",
    "Expected Behavior",
    "Desired Structure",
    "Acceptance Criteria",
    "Resources",
    "Dependencies",
    "Effort",
]

# ---------------------------------------------------------------------------
# Heading <-> key helpers
# ---------------------------------------------------------------------------


def unknown_key_to_heading(key: str) -> str:
    """Reconstruct a display heading from an unknown-section storage key.

    Reverses the ``unknown__`` prefixing: strips the prefix, replaces
    underscores with spaces, and title-cases the result.

    Args:
        key: Storage key such as ``"unknown__custom_analysis"``.

    Returns:
        Display heading such as ``"Custom Analysis"``.
    """
    stripped = key.removeprefix("unknown__")
    return stripped.replace("_", " ").title()


# ---------------------------------------------------------------------------
# Rendering functions
# ---------------------------------------------------------------------------


def render_groomed_section(groomed: GroomedData) -> str:
    """Render a GroomedData as ``## Groomed ({date})`` with ``### subsection`` children.

    Subsections are emitted in canonical order defined by
    :data:`GROOMED_SUBSECTION_ORDER`.  Any keys not in the canonical list are
    appended alphabetically.

    Args:
        groomed: GroomedData to render.

    Returns:
        Rendered section string (no trailing newline).
    """
    parts: list[str] = [f"## Groomed ({groomed.date})"]
    ordered = [k for k in GROOMED_SUBSECTION_ORDER if k in groomed.subsections]
    extras = sorted(k for k in groomed.subsections if k not in GROOMED_SUBSECTION_ORDER)
    parts.extend(f"### {key}\n\n{groomed.subsections[key]}" for key in ordered + extras)
    return "\n\n".join(parts)


def section_display_title(key: str, groomed_date: str = "") -> str:
    """Return the human-readable title for a section key.

    Known keys are looked up in :data:`SECTION_HEADING`.  Unknown keys with
    the ``"unknown__"`` prefix are reconstructed via
    :func:`unknown_key_to_heading`.  The special ``"groomed"`` key returns
    ``"Groomed — {date}"`` when a date is provided.  All other keys are
    title-cased with underscores replaced by spaces.

    Args:
        key: Section storage key (e.g. ``"fact_check"``, ``"unknown__story"``).
        groomed_date: Optional date string from a ``GroomedData`` section, used
            to append the date to the ``"groomed"`` title.

    Returns:
        Display title string (e.g. ``"Fact-Check"``, ``"Story"``).
    """
    if key in SECTION_HEADING:
        return SECTION_HEADING[key]
    if key == "groomed":
        return f"Groomed \u2014 {groomed_date}" if groomed_date else "Groomed"
    if key.startswith("unknown__"):
        return unknown_key_to_heading(key)
    if key in _SECTION_HEADING_VALUES:
        return key
    return key.replace("_", " ").title()
