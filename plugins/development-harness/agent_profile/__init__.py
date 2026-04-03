"""Agent-profile MCP package.

Exposes ``mcp`` — a FastMCP server that provides ``profile_load`` and
``profile_list`` tools for compiling agent definitions into loadable skill
bundles. Mounted into the backlog_core server with the ``profile_`` prefix.

``server.py`` (and therefore ``mcp``) is created in T5. The import below is
added in that task. Until then this package is importable for model access.
"""

from __future__ import annotations

from agent_profile.server import mcp as mcp

__all__: list[str] = ["mcp"]
