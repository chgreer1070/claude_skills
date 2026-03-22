"""Agent file discovery for the agent-profile MCP package.

Provides three public functions:

- :func:`get_plugins_root` — resolve the ``plugins/`` directory from the
  module's own location without requiring an environment variable.
- :func:`scan_all_agents` — enumerate every agent ``.md`` file across all
  installed plugins, returning a sorted :class:`~agent_profile.models.AgentEntry`
  list.
- :func:`find_agent` — locate a single agent by bare name or
  plugin-qualified name (``plugin:agent-name``), raising on ambiguity or
  absence.

Subdirectory agents (``agents/subdir/name.md``) are represented with
colon-separated names (``subdir:name``) so that the same colon-qualified
lookup syntax used by skills also works for agents.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

from .models import AgentEntry

logger = logging.getLogger(__name__)

__all__ = ["find_agent", "get_plugins_root", "scan_all_agents"]


def get_plugins_root() -> Path:
    """Return the absolute path to the directory that contains all plugin directories.

    Uses ``CLAUDE_PLUGIN_ROOT`` env var (set by Claude Code for MCP server
    subprocesses and hooks) when available.  Falls back to walking up from
    ``__file__`` for repo-layout development.

    Layout differences::

        Repo:  plugins/development-harness/agents/
               CLAUDE_PLUGIN_ROOT = plugins/development-harness/
               plugins_root       = plugins/                        (.parent)

        Cache: cache/org/development-harness/4.4.19/agents/
               CLAUDE_PLUGIN_ROOT = cache/org/development-harness/4.4.19/
               plugins_root       = cache/org/                      (.parent.parent)

    Returns:
        Absolute :class:`~pathlib.Path` to the directory whose children are the
        individual plugin directories (e.g. ``python3-development/``,
        ``plugin-creator/``, ``development-harness/``).

    Raises:
        FileNotFoundError: When the plugins root cannot be determined.
    """
    plugin_root_env = os.environ.get("CLAUDE_PLUGIN_ROOT")
    if plugin_root_env:
        plugin_root = Path(plugin_root_env).resolve()
        # Detect layout: in the cache, plugin_root is a version directory
        # (e.g., 4.4.19/) inside a plugin-name directory.  The parent of
        # plugin_root is the plugin-name dir, which contains only version
        # dirs — not sibling plugins.  Go up one more to reach the org dir.
        #
        # In the repo, plugin_root IS the plugin dir (development-harness/)
        # and its parent (plugins/) directly contains sibling plugins.
        candidate = plugin_root.parent
        # Check if candidate has sibling dirs with agents/ or skills/
        has_sibling_plugins = any(
            d.is_dir() and d.name != plugin_root.name and ((d / "agents").is_dir() or (d / "skills").is_dir())
            for d in candidate.iterdir()
            if d.is_dir()
        )
        if has_sibling_plugins:
            logger.debug("plugins_root from CLAUDE_PLUGIN_ROOT (repo): %s", candidate)
            return candidate
        # Cache layout: candidate is plugin-name dir with version subdirs.
        # Go up one more level to the org directory.
        plugins_root = candidate.parent
        if plugins_root.exists():
            logger.debug("plugins_root from CLAUDE_PLUGIN_ROOT (cache): %s", plugins_root)
            return plugins_root

    # Fallback: walk up from __file__ to find agents/ directory.
    current = Path(__file__).resolve().parent
    while current != current.parent:
        if (current / "agents").is_dir():
            plugins_root = current.parent
            logger.debug("plugins_root from __file__ walk: %s", plugins_root)
            return plugins_root
        current = current.parent

    raise FileNotFoundError(
        f"Could not locate the plugin root. "
        f"Searched ancestors of {Path(__file__).resolve()} for 'agents/' subdirectory "
        "and CLAUDE_PLUGIN_ROOT is not set."
    )


def _agent_name_from_path(agent_path: Path, agents_dir: Path) -> str:
    """Derive the colon-separated agent name from its path relative to agents_dir.

    Examples::

        agents/code-reviewer.md           -> "code-reviewer"
        agents/testing/unit-tester.md     -> "testing:unit-tester"

    Args:
        agent_path: Absolute path to the agent ``.md`` file.
        agents_dir: Absolute path to the plugin's ``agents/`` directory.

    Returns:
        Colon-separated name string.
    """
    relative = agent_path.relative_to(agents_dir)
    # Remove the .md suffix from the final component.
    parts = list(relative.parts)
    parts[-1] = parts[-1][: -len(".md")]
    return ":".join(parts)


def scan_all_agents(plugins_root: Path | None = None) -> list[AgentEntry]:
    """Scan all plugins for agent definition files and return a sorted list.

    Searches ``plugins/*/agents/**/*.md`` for agent definitions. Agents in
    subdirectories produce colon-separated names
    (e.g. ``agents/testing/unit-tester.md`` → name ``testing:unit-tester``).

    The result is sorted by ``(plugin, name)`` for deterministic ordering.

    Args:
        plugins_root: Path to the ``plugins/`` directory. When ``None``,
            :func:`get_plugins_root` is called to resolve it automatically.

    Returns:
        Sorted list of :class:`~agent_profile.models.AgentEntry` objects,
        one per discovered agent file. Returns an empty list when no
        ``agents/`` directories exist.
    """
    if plugins_root is None:
        plugins_root = get_plugins_root()

    entries: list[AgentEntry] = []

    for plugin_dir in sorted(plugins_root.iterdir()):
        if not plugin_dir.is_dir():
            continue
        agents_dir = plugin_dir / "agents"
        if not agents_dir.is_dir():
            continue

        plugin_name = plugin_dir.name

        for agent_file in sorted(agents_dir.rglob("*.md")):
            if not agent_file.is_file():
                continue
            name = _agent_name_from_path(agent_file, agents_dir)
            entries.append(AgentEntry(name=name, plugin=plugin_name, path=agent_file))

    return entries


def find_agent(agent_name: str, plugins_root: Path | None = None) -> AgentEntry:
    """Locate a single agent by name and return its :class:`~agent_profile.models.AgentEntry`.

    Supports two addressing forms:

    **Plugin-qualified** (``plugin:agent-name`` or ``plugin:subdir:name``):
        Splits on the first colon, resolves the plugin directory, and constructs
        the expected path directly without scanning. The remainder after the first
        colon is used as a slash-delimited path relative to ``agents/``.
        Example: ``python3-development:code-reviewer``
        → ``plugins/python3-development/agents/code-reviewer.md``

    **Bare name** (no colon):
        Scans all plugins. Exactly one match → returns it. Zero matches →
        raises :class:`FileNotFoundError`. Two or more matches across different
        plugins → raises :class:`ValueError` (ambiguous; use a plugin-qualified
        name to disambiguate).

    Subdirectory-qualified bare names use the colon separator, e.g. the agent
    at ``agents/testing/unit-tester.md`` in any plugin has the bare name
    ``testing:unit-tester``. When such a name is passed, the first colon is
    treated as the plugin qualifier, so callers should always use a
    plugin-qualified form for subdirectory agents to avoid ambiguity.

    Args:
        agent_name: Agent name in bare (``code-reviewer``) or plugin-qualified
            (``python3-development:code-reviewer``) form. Subdirectory agents
            should be plugin-qualified (``dh:testing:analyze-test-failures``)
            to avoid false-positive plugin detection.
        plugins_root: Path to ``plugins/``. When ``None``,
            :func:`get_plugins_root` resolves it automatically.

    Returns:
        Matching :class:`~agent_profile.models.AgentEntry`.

    Raises:
        FileNotFoundError: When no agent matching *agent_name* is found.
        ValueError: When *agent_name* is a bare name that matches agents in
            two or more different plugins (ambiguous).
    """
    if plugins_root is None:
        plugins_root = get_plugins_root()

    if ":" in agent_name:
        return _find_plugin_qualified(agent_name, plugins_root)

    return _find_bare(agent_name, plugins_root)


def _find_plugin_qualified(agent_name: str, plugins_root: Path) -> AgentEntry:
    """Resolve a plugin-qualified agent name (``plugin:rest``) directly.

    Args:
        agent_name: Plugin-qualified name with at least one colon.
        plugins_root: Absolute path to ``plugins/``.

    Returns:
        :class:`~agent_profile.models.AgentEntry` for the agent.

    Raises:
        FileNotFoundError: When the expected file does not exist.
    """
    plugin_part, _, rest = agent_name.partition(":")
    plugin_dir = plugins_root / plugin_part
    agents_dir = plugin_dir / "agents"

    # Convert colon-separated remainder to a slash path + .md suffix.
    relative_path = Path(*rest.split(":")).with_suffix(".md")
    agent_file = agents_dir / relative_path

    if not agent_file.is_file():
        raise FileNotFoundError(f"Agent '{agent_name}' not found: expected file at {agent_file}")

    name = _agent_name_from_path(agent_file, agents_dir)
    return AgentEntry(name=name, plugin=plugin_part, path=agent_file)


def _find_bare(agent_name: str, plugins_root: Path) -> AgentEntry:
    """Scan all plugins for a bare agent name and return the unique match.

    Args:
        agent_name: Bare agent name (no colon), e.g. ``code-reviewer``.
        plugins_root: Absolute path to ``plugins/``.

    Returns:
        :class:`~agent_profile.models.AgentEntry` for the unique matching agent.

    Raises:
        FileNotFoundError: When no match is found across all plugins.
        ValueError: When two or more plugins contain an agent with this name.
    """
    all_agents = scan_all_agents(plugins_root)
    matches = [entry for entry in all_agents if entry.name == agent_name]

    if len(matches) == 1:
        return matches[0]

    if len(matches) == 0:
        raise FileNotFoundError(
            f"Agent '{agent_name}' not found in any plugin under {plugins_root}. "
            "Check the agent name or use a plugin-qualified form."
        )

    # Multiple matches — report which plugins contain this agent.
    locations = ", ".join(f"{m.plugin}/{m.name}" for m in matches)
    raise ValueError(
        f"Ambiguous agent name '{agent_name}': found in multiple plugins: {locations}. "
        "Use a plugin-qualified name (e.g. 'plugin-name:agent-name') to disambiguate."
    )
