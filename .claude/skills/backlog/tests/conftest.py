"""Pytest configuration for backlog tests.

Adds the backlog package root to sys.path so ``from backlog_core.parsing import ...``
resolves correctly regardless of pytest invocation directory.
"""

from __future__ import annotations

import sys
from pathlib import Path

# .claude/skills/backlog/ must be on sys.path for backlog_core package imports
_BACKLOG_ROOT = Path(__file__).parent.parent
if str(_BACKLOG_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKLOG_ROOT))
