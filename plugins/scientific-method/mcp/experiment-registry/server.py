"""Experiment Registry MCP Server.

Manages controlled experiment lifecycle: creation, stepping, validation, and completion.
Experiment types are composable JSON definitions — a universal core merged with domain extensions.
State persists to .claude/experiments/{id}/state.json.
"""

from __future__ import annotations

from fastmcp import FastMCP

mcp = FastMCP("experiment-registry")

if __name__ == "__main__":
    mcp.run()
