#!/usr/bin/env python3
"""Wrapper script for build_quality_gate_plan callable from any working directory.

Adds the plugin root to sys.path so sam_schema is importable regardless of cwd,
then delegates to build_quality_gate_plan from sam_schema.core.quality_gates.

Usage:
    uv run python3 plugins/development-harness/scripts/build_quality_gate_plan.py \
      --slug <slug> --issue <issue_number> --impl-plan-address <P{N}>
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Add the plugin root (plugins/development-harness/) to sys.path so that
# sam_schema is importable regardless of the calling working directory.
_plugin_root = Path(__file__).parent.parent
sys.path.insert(0, str(_plugin_root))

from sam_schema.core.quality_gates import build_quality_gate_plan


def _parse_args() -> argparse.Namespace:
    """Parse CLI arguments.

    Returns:
        Parsed namespace with slug, issue, and impl_plan_address attributes.
    """
    parser = argparse.ArgumentParser(
        description="Generate a quality gate plan YAML for the complete-implementation workflow."
    )
    parser.add_argument(
        "--slug", required=True, help="Feature slug used as the plan feature identifier, e.g. my-feature"
    )
    parser.add_argument("--issue", required=True, help="GitHub issue number as a string, e.g. 123")
    parser.add_argument(
        "--impl-plan-address",
        required=True,
        dest="impl_plan_address",
        help="Implementation plan address, e.g. P003 or Pabc123",
    )
    return parser.parse_args()


def main() -> None:
    """Entry point: parse args, call build_quality_gate_plan, print YAML to stdout."""
    args = _parse_args()
    yaml_str = build_quality_gate_plan(slug=args.slug, issue=args.issue, impl_plan_address=args.impl_plan_address)
    print(yaml_str, end="")


if __name__ == "__main__":
    main()
