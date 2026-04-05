#!/usr/bin/env python3
"""Run a single live validation query against a skill.

Thin wrapper around run_single_query from run_eval.py.
Exits 0 when the skill is triggered, 1 when it is not.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Resolve path to skill-creator scripts so run_eval and utils are importable
# as `scripts.run_eval` and `scripts.utils` (matching their internal imports).
_SKILL_CREATOR_ROOT = Path(__file__).resolve().parent.parent.parent / "plugin-creator" / "skills" / "skill-creator"
if str(_SKILL_CREATOR_ROOT) not in sys.path:
    sys.path.insert(0, str(_SKILL_CREATOR_ROOT))

from scripts.run_eval import run_single_query
from scripts.utils import parse_skill_md


def _find_project_root() -> str:
    """Walk up from cwd looking for .claude/ to find the project root.

    Returns:
        Absolute path string to the project root, or cwd if not found.
    """
    current = Path.cwd()
    for parent in [current, *current.parents]:
        if (parent / ".claude").is_dir():
            return str(parent)
    return str(current)


def main() -> None:
    """Parse arguments, run query, exit with result code."""
    parser = argparse.ArgumentParser(description="Run a single live validation query against a skill")
    parser.add_argument("--skill-path", required=True, help="Path to skill directory containing SKILL.md")
    parser.add_argument("--query", required=True, help="Prompt string to send to claude -p")
    parser.add_argument(
        "--timeout", type=int, default=30, help="Maximum seconds to wait for claude process (default: 30)"
    )
    parser.add_argument("--model", default=None, help="Model override for claude -p (default: user's configured model)")
    args = parser.parse_args()

    skill_path = Path(args.skill_path)
    if not (skill_path / "SKILL.md").exists():
        print(f"Error: no SKILL.md found at {skill_path}", file=sys.stderr)
        sys.exit(2)

    skill_name, skill_description, _content = parse_skill_md(skill_path)
    project_root = _find_project_root()

    triggered = run_single_query(args.query, skill_name, skill_description, args.timeout, project_root, args.model)

    sys.exit(0 if triggered else 1)


if __name__ == "__main__":
    main()
