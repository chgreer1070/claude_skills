"""Frontmatter parsing and skill content reading for agent definition files.

Handles three input formats for the ``skills:`` field in YAML frontmatter:

- YAML sequence: ``skills: [a, b, c]``
- Comma-separated string: ``skills: "a, b, c"``
- Single bare value: ``skills: a``

All normalize to ``list[str]``. An absent ``skills:`` key normalises to ``[]``.

Public API
----------
parse_agent_file     -- Read agent .md, return (AgentMetadata, body_str).
parse_skill_frontmatter -- Read only the frontmatter of a SKILL.md.
read_skill_content   -- Read SKILL.md content + all references/*.md files.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

# Re-use the shared frontmatter utilities that wrap python-frontmatter with
# ruamel.yaml (per repo convention: never import pyyaml directly).
from backlog_core.frontmatter_utils import load_frontmatter

from agent_profile.models import AgentMetadata

if TYPE_CHECKING:
    from pathlib import Path


def _normalize_skills(raw: object) -> list[str]:
    """Normalise raw YAML skills value to a flat list of stripped strings.

    Args:
        raw: The value bound to the ``skills:`` or ``requires:`` key in YAML.
             May be a list, a comma-separated string, a bare string, or None.

    Returns:
        Ordered list of non-empty skill URI strings. Empty list when *raw* is
        falsy.
    """
    if not raw:
        return []
    if isinstance(raw, list):
        return [str(s).strip() for s in raw if str(s).strip()]
    # Comma-separated string or bare single value.
    return [s.strip() for s in str(raw).split(",") if s.strip()]


def parse_agent_file(path: Path) -> tuple[AgentMetadata, str]:
    """Read an agent ``.md`` file and return its structured metadata and body.

    The file must contain YAML frontmatter delimited by ``---`` at the start.
    Everything after the closing ``---`` delimiter is the instruction body.

    Args:
        path: Absolute or relative filesystem path to the agent ``.md`` file.

    Returns:
        A two-element tuple of:
        - ``AgentMetadata`` populated from the YAML frontmatter.
        - The instruction body as a plain string (may be empty).

    Raises:
        FileNotFoundError: When *path* does not exist.
        ValueError: When the file contains no valid YAML frontmatter block.
    """
    if not path.exists():
        raise FileNotFoundError(f"Agent file not found: {path}")

    post = load_frontmatter(path)

    # python-frontmatter returns an empty metadata dict when no frontmatter
    # is present; there is no reliable sentinel other than checking for the
    # required fields.
    meta = post.metadata
    if not meta or ("name" not in meta and "description" not in meta):
        raise ValueError(f"No valid YAML frontmatter found in agent file: {path}")

    agent_metadata = AgentMetadata(
        name=str(meta.get("name", path.stem)),
        description=str(meta.get("description", "")),
        skills=_normalize_skills(meta.get("skills")),
        tools=_normalize_skills(meta.get("tools")),
        model=str(raw_model) if (raw_model := meta.get("model")) else None,
        color=str(raw_color) if (raw_color := meta.get("color")) else None,
    )
    body: str = post.content or ""
    return agent_metadata, body


def parse_skill_frontmatter(path: Path) -> list[str]:
    """Read only the frontmatter of a SKILL.md to extract sub-skill URIs.

    Looks for a ``skills:`` *or* ``requires:`` field listing dependent skills.
    When both are present, ``skills:`` takes precedence.

    Args:
        path: Filesystem path to the SKILL.md file.

    Returns:
        Ordered list of skill URI strings declared in the frontmatter.
        Returns an empty list when the file has no frontmatter or neither
        field is present.

    Raises:
        FileNotFoundError: When *path* does not exist.
    """
    if not path.exists():
        raise FileNotFoundError(f"SKILL.md not found: {path}")

    post = load_frontmatter(path)
    meta = post.metadata
    if not meta:
        return []

    raw = meta.get("skills") or meta.get("requires")
    return _normalize_skills(raw)


def read_skill_content(skill_dir: Path) -> tuple[str, dict[str, str]]:
    """Read a skill's SKILL.md and all Markdown reference files.

    Reads ``SKILL.md`` from *skill_dir* and then collects every ``.md`` file
    from ``{skill_dir}/references/``. Reference files are read in
    lexicographic order for determinism.

    Args:
        skill_dir: Directory that contains a ``SKILL.md`` file and optionally
                   a ``references/`` subdirectory.

    Returns:
        A two-element tuple of:
        - Full text content of ``SKILL.md``.
        - Mapping of ``{filename: content}`` for every ``.md`` file in
          ``references/``. Empty dict when the subdirectory does not exist.

    Raises:
        FileNotFoundError: When ``SKILL.md`` is missing from *skill_dir*.
    """
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        raise FileNotFoundError(f"SKILL.md not found in skill directory: {skill_dir}")

    skill_content = skill_md.read_text(encoding="utf-8")

    references_dir = skill_dir / "references"
    reference_files: dict[str, str] = {}
    if references_dir.is_dir():
        for ref_path in sorted(references_dir.glob("*.md")):
            reference_files[ref_path.name] = ref_path.read_text(encoding="utf-8")

    return skill_content, reference_files
