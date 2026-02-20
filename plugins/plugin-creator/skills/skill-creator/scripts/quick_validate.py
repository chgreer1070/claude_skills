#!/usr/bin/env python3
"""Quick validation script for skills - minimal version."""

from __future__ import annotations

import re
import sys
from pathlib import Path

from ruamel.yaml import YAML
from ruamel.yaml.error import YAMLError

_yaml = YAML(typ="safe")

# Constants
MAX_NAME_LENGTH = 64
MAX_DESCRIPTION_LENGTH = 1024
REQUIRED_ARGC = 2  # script name + skill-path


def validate_skill(skill_path: str | Path) -> tuple[bool, str]:  # noqa: C901, PLR0912
    """Basic validation of a skill.

    Args:
        skill_path: Path to the skill directory

    Returns:
        Tuple of (is_valid, message)
    """
    skill_path = Path(skill_path)

    # Check SKILL.md exists
    skill_md = skill_path / "SKILL.md"
    if not skill_md.exists():
        return False, "SKILL.md not found"

    # Read and validate frontmatter
    content = skill_md.read_text()
    if not content.startswith("---"):
        return False, "No YAML frontmatter found"

    # Extract frontmatter
    match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    if not match:
        return False, "Invalid frontmatter format"

    frontmatter_text = match.group(1)

    # Parse YAML frontmatter
    try:
        frontmatter = _yaml.load(frontmatter_text)
        if not isinstance(frontmatter, dict):
            return False, "Frontmatter must be a YAML dictionary"
    except YAMLError as e:
        return False, f"Invalid YAML in frontmatter: {e}"

    # Define allowed properties (all optional per January 2026 spec)
    allowed_properties = {
        "name",
        "description",
        "license",
        "allowed-tools",
        "metadata",
        "argument-hint",
        "model",
        "context",
        "agent",
        "user-invocable",
        "disable-model-invocation",
        "hooks",
    }

    # Check for unexpected properties (excluding nested keys under metadata)
    unexpected_keys = set(frontmatter.keys()) - allowed_properties
    if unexpected_keys:
        return False, (
            f"Unexpected key(s) in SKILL.md frontmatter: {', '.join(sorted(unexpected_keys))}. "
            f"Allowed properties are: {', '.join(sorted(allowed_properties))}"
        )

    # All fields are optional, but warn if both name and description are missing
    # (skill will use directory name and first paragraph as defaults)
    if "name" not in frontmatter and "description" not in frontmatter:
        # This is valid but unusual - skill will use directory name and first paragraph
        pass

    # Extract name for validation
    name = frontmatter.get("name", "")
    if not isinstance(name, str):
        return False, f"Name must be a string, got {type(name).__name__}"
    name = name.strip()
    if name:
        # Check naming convention (hyphen-case: lowercase with hyphens)
        if not re.match(r"^[a-z0-9-]+$", name):
            return (
                False,
                f"Name '{name}' should be hyphen-case (lowercase letters, digits, and hyphens only)",
            )
        if name.startswith("-") or name.endswith("-") or "--" in name:
            return (
                False,
                f"Name '{name}' cannot start/end with hyphen or contain consecutive hyphens",
            )
        # Check name length (max 64 characters per spec)
        if len(name) > MAX_NAME_LENGTH:
            return (
                False,
                f"Name is too long ({len(name)} characters). Maximum is 64 characters.",
            )

    # Extract and validate description
    description = frontmatter.get("description", "")
    if not isinstance(description, str):
        return False, f"Description must be a string, got {type(description).__name__}"
    description = description.strip()

    # Check for YAML multiline indicator bug (>-, |-, | are broken in Claude Code skill indexer)
    if description in {">-", "|-", ">", "|"}:
        return (
            False,
            "Description appears to be a YAML multiline indicator (>-, |-, |) which is broken in Claude Code. Use single-line quoted strings instead.",
        )

    if description:
        # Check for angle brackets
        if "<" in description or ">" in description:
            return False, "Description cannot contain angle brackets (< or >)"
        # Check description length (max 1024 characters per spec)
        if len(description) > MAX_DESCRIPTION_LENGTH:
            return (
                False,
                f"Description is too long ({len(description)} characters). Maximum is 1024 characters.",
            )

    return True, "Skill is valid!"


if __name__ == "__main__":
    if len(sys.argv) != REQUIRED_ARGC:
        print("Usage: python quick_validate.py <skill_directory>")
        sys.exit(1)

    valid, message = validate_skill(sys.argv[1])
    print(message)
    sys.exit(0 if valid else 1)
