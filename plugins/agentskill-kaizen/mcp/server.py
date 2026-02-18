#!/usr/bin/env -S uv run --quiet --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "fastmcp>=2.0.0",
#     "pm4py>=2.7.0",
#     "pandas>=2.0.0",
# ]
# ///
"""Kaizen Analysis MCP Server.

Exposes process mining, pattern mining, and frustration detection
as MCP tools for the transcript-analyst agent.

TODO: Implement tools in Phase 5.
"""

from __future__ import annotations


def main() -> None:
    """Entry point — placeholder for Phase 5 implementation."""
    msg = "Kaizen MCP server not yet implemented. See Phase 5 in .claude/kaizen-plugin-plan.md"
    raise NotImplementedError(msg)


if __name__ == "__main__":
    main()
