"""Shared test configuration for development-harness tests."""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure backlog_core package is importable when running tests from repo root.
# The package lives at plugins/development-harness/ (not installed as editable
# from root), so we add its parent directory to sys.path explicitly.
_plugin_dir = Path(__file__).parent.parent
if str(_plugin_dir) not in sys.path:
    sys.path.insert(0, str(_plugin_dir))
