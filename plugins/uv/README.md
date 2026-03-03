<p align="center">
  <img src="./assets/hero.png" alt="uv - Astral's Python Package Manager Expert" width="800" />
</p>

# uv - Astral's Python Package Manager Expert

Supercharge Claude with comprehensive knowledge of uv, the blazing-fast Python package and project manager that replaces pip, pip-tools, pipx, poetry, pyenv, and virtualenv.

## Compatibility Wrapper

This plugin is a compatibility wrapper. The uv skill was consolidated into the `python3-development` plugin. This plugin provides the same skill via symlink so existing installations continue to work.

**For new installations, prefer `python3-development@jamie-bitflight-skills`.**

## What You Get

Claude gains expert knowledge of uv for:

- **Project management** — `uv init`, `pyproject.toml`, workspaces, lockfiles
- **Dependency management** — add/remove/upgrade with automatic lockfile management
- **Script development** — PEP 723 inline metadata for portable single-file scripts
- **Tool management** — global CLI tools (`uv tool`), ephemeral runs (`uvx`)
- **Python version management** — CPython, PyPy, GraalPy, free-threaded builds
- **CI/CD integration** — GitHub Actions, Docker, pre-commit/prek hooks
- **Migration support** — from pip, Poetry, or conda to uv

## Installation

First, add the marketplace (one-time setup):

```bash
/plugin marketplace add bitflight-devops/claude_skills
```

Then install the plugin:

```bash
/plugin install uv@jamie-bitflight-skills
```

## Self-Updating Documentation

The underlying skill includes a sync script that fetches the latest uv release notes from GitHub:

```bash
# Check for new releases (dry run)
uv run plugins/python3-development/skills/uv/scripts/sync_uv_releases.py --dry-run

# Update the skill documentation
uv run plugins/python3-development/skills/uv/scripts/sync_uv_releases.py

# Force update (bypass cooldown)
uv run plugins/python3-development/skills/uv/scripts/sync_uv_releases.py --force
```

## Requirements

- Claude Code v2.0+
- uv installed on your system (Claude can help you install it)

## Learn More

- uv Documentation: <https://docs.astral.sh/uv/>
- uv GitHub: <https://github.com/astral-sh/uv>
