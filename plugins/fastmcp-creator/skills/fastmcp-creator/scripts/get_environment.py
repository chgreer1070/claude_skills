#!/usr/bin/env python3
"""Get MCP development environment information for dynamic context injection."""

from __future__ import annotations

import sys
from pathlib import Path


def get_python_version() -> str:
    """Get Python interpreter version.

    Returns:
        Formatted string with Python version and executable path.
    """
    return f"Python {sys.version.split()[0]} at {sys.executable}"


def get_mcp_servers() -> str:
    """List available MCP servers if directory exists.

    Returns:
        Newline-separated list of MCP server directory names, or message if none found.
    """
    mcp_dir = Path("mcp_servers")
    if not mcp_dir.exists():
        return "No mcp_servers/ directory found"

    servers = [d.name for d in mcp_dir.iterdir() if d.is_dir()]
    if not servers:
        return "mcp_servers/ directory exists but is empty"

    return "\n".join(sorted(servers))


def get_current_directory() -> str:
    """Get current working directory.

    Returns:
        Absolute path to current working directory as string.
    """
    return str(Path.cwd())


def main() -> None:
    """Print environment information."""
    print(f"**Python interpreter:**\n{get_python_version()}\n")
    print(f"**Available MCP servers:**\n{get_mcp_servers()}\n")
    print(f"**Current directory:**\n{get_current_directory()}")


if __name__ == "__main__":
    main()
