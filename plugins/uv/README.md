# uv

Modern Python project management with uv - the extremely fast Python package manager.

## Why Install This?

When working on Python projects, you might encounter:

- Slow dependency installation (pip taking minutes)
- Unclear project setup (where do requirements go?)
- Scripts that break when dependencies change
- Confusion between pip, pipx, poetry, virtualenv
- Different Python versions across team members
- CI builds that don't match local development

This plugin helps Claude guide you toward modern Python project practices using uv.

## Note

This plugin is a compatibility wrapper. The uv skill was consolidated into the
`python3-development` plugin. This plugin provides the same skill via symlink so
existing installations continue to work. For new installations, prefer
`python3-development@jamie-bitflight-skills`.

## What Changes

With this plugin installed, Claude will:

- Recommend uv for new Python projects instead of traditional pip workflows
- Set up projects with proper structure (pyproject.toml, lockfiles, virtual environments)
- Create portable single-file scripts with built-in dependency management
- Configure CI/CD pipelines that are fast and reproducible
- Help migrate existing projects from pip, requirements.txt, or poetry
- Troubleshoot Python dependency and version issues more effectively
- Self-update its documentation via `sync-uv-releases.py` to stay current with new uv releases

## Installation

First, add the marketplace (one-time setup):

```bash
/plugin marketplace add Jamie-BitFlight/claude_skills
```

Then install the plugin:

```bash
/plugin install uv@jamie-bitflight-skills
```

## What You'll Experience

### Better Project Setup

**Before**: You ask Claude to set up a Python project

```
Creates requirements.txt
Tells you to run pip install -r requirements.txt
No version pinning, no lockfile
```

**After**: Same request with this plugin

```
Creates pyproject.toml with dependencies
Creates uv.lock for reproducibility
Sets up virtual environment automatically
Includes proper Python version management
```

### Portable Scripts

**Before**: Creating a script that needs packages

```
Script has no dependency information
You manually pip install packages
Breaks when someone else tries to run it
```

**After**: Same task with this plugin

```python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["requests", "rich"]
# ///

import requests
from rich import print
# Script includes its own dependencies - just run it
```

### Faster Workflows

**Before**: Installing dependencies for a project

```
pip install from PyPI with wheel builds
Per-project virtual environment setup required
Cache exists but installations still copy files
```

**After**: With uv-based workflow

```
uv sync resolves and installs via hardlinks from global cache
Automatic virtual environment creation and management
Near-instant warm-cache installs (milliseconds, not seconds)
```

## When This Helps

This plugin is especially useful when you:

- Start new Python projects
- Set up dependency management
- Create standalone Python scripts
- Configure CI/CD for Python projects
- Migrate from pip, poetry, or conda
- Need to manage multiple Python versions
- Want faster and more reliable builds

## What is uv?

uv is Astral's Rust-based Python package manager that replaces pip, pipx, poetry, pyenv, and virtualenv with a single tool that's 10-100x faster. Think of it as a modern alternative to pip that handles project management, virtual environments, and Python versions all in one place.

## Self-Updating Documentation

This plugin includes a sync script that fetches the latest uv release notes from
GitHub and updates the skill documentation automatically:

```bash
# Check for new releases (dry run)
uv run scripts/sync-uv-releases.py --dry-run

# Update the skill documentation
uv run scripts/sync-uv-releases.py

# Force update (bypass cooldown)
uv run scripts/sync-uv-releases.py --force
```

The script annotates each feature with the version it was introduced in, so
Claude can compare against whatever uv version you have installed.

## Requirements

- Claude Code v2.0+
- uv installed (Claude will guide you through installation if needed)
