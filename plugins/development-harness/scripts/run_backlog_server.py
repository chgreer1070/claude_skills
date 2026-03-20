#!/usr/bin/env -S uv --quiet run --active --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "fastmcp>=3.0.2",
#   "gitpython>=3.1.0",
#   "pygithub>=2.8.1",
#   "pydantic>=2.12.3",
#   "python-frontmatter>=1.1.0",
#   "ruamel.yaml>=0.18.0",
#   "tiktoken>=0.12.0",
#   "typer>=0.21.2",
# ]
# ///
"""PEP 723 wrapper for the backlog MCP server."""

from __future__ import annotations

import sys
from pathlib import Path

# Add the plugin root to sys.path so backlog_core can be imported
plugin_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(plugin_root))

from backlog_core.server import mcp

mcp.run()
