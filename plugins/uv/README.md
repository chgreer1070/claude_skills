# uv - Astral's Python Package Manager Expert

Supercharge Claude with comprehensive knowledge of uv, the blazing-fast Python package and project manager that replaces pip, pip-tools, pipx, poetry, pyenv, and virtualenv.

## Why Install This?

When you ask Claude to help with Python projects, this plugin ensures Claude:

- Creates projects using modern uv workflows instead of outdated pip/virtualenv patterns
- Writes portable single-file scripts with PEP 723 inline dependency metadata
- Manages dependencies using lockfiles for reproducible environments
- Configures CI/CD pipelines with uv best practices
- Troubleshoots dependency resolution and build failures effectively
- Migrates existing projects from pip, poetry, or conda to uv

Without this plugin, Claude may suggest slower, outdated approaches. With it, Claude becomes an expert in modern Python tooling that's 10-100x faster.

## Note: Compatibility Wrapper

This plugin is a compatibility wrapper. The uv skill was consolidated into the `python3-development` plugin. This plugin provides the same skill via symlink so existing installations continue to work. For new installations, prefer `python3-development@jamie-bitflight-skills`.

## What You Get

### Expert Guidance on Modern Python Workflows

Claude will help you with:

**Project Management**
- Initialize new projects with proper structure (apps, libraries, or bare projects)
- Configure pyproject.toml with modern dependency groups (PEP 735)
- Set up workspaces for monorepo projects
- Build and publish packages to PyPI with PEP 740 attestations

**Dependency Management**
- Add, remove, and upgrade dependencies with automatic lockfile management
- Resolve complex dependency conflicts
- Configure custom package indexes (PyPI, PyTorch, private registries)
- Handle optional dependency groups and extras
- Exclude problematic packages from resolution
- Apply version bounds (compatible, exact, lowest) automatically

**Script Development**
- Create portable single-file scripts with PEP 723 inline metadata
- Lock scripts for reproducible execution
- Run scripts with automatic dependency installation
- Share executable scripts that work anywhere

**Tool Management**
- Install command-line tools globally (ruff, black, mypy, httpie)
- Run tools ephemerally without installation (uvx)
- Keep tools updated across your system

**Python Version Management**
- Install and switch between Python versions automatically
- Support CPython, PyPy, GraalPy, Pyodide, and free-threaded Python (+gil suffix)
- Pin Python versions per project or globally
- Compile standard library bytecode for faster startup

**CI/CD Integration**
- Configure GitHub Actions workflows with uv
- Set up Docker containers optimized for uv
- Integrate with pre-commit/prek git hooks
- Export SBOM (Software Bill of Materials) for security audits

**Migration Support**
- Convert from pip/requirements.txt to modern pyproject.toml
- Migrate from Poetry with automated tools (uvx migrate-to-uv)
- Transition from conda environments
- Update legacy workflows to uv best practices

### Comprehensive Reference Documentation

The plugin includes detailed reference materials on:

- Complete CLI command reference (all commands, flags, and arguments)
- Full configuration guide (pyproject.toml settings and environment variables)
- Common workflow examples (new projects, scripts, migrations, CI/CD)
- Troubleshooting guide (build failures, cache issues, common pitfalls)

### Version-Aware Knowledge

Claude understands:
- Latest features in uv 0.10.x (current as of February 2026)
- Breaking changes and migration paths (e.g., `uv venv --clear` requirement)
- Deprecated flags and their replacements (e.g., `--project` → `--name`)
- Feature availability across versions

### Self-Updating Documentation

This plugin includes a sync script that fetches the latest uv release notes from GitHub and updates the skill documentation automatically:

```bash
# Check for new releases (dry run)
uv run scripts/sync-uv-releases.py --dry-run

# Update the skill documentation
uv run scripts/sync-uv-releases.py

# Force update (bypass cooldown)
uv run scripts/sync-uv-releases.py --force
```

The script annotates each feature with the version it was introduced in, so Claude can compare against whatever uv version you have installed.

## Installation

First, add the marketplace (one-time setup):

```bash
/plugin marketplace add bitflight-devops/claude_skills
```

Then install the plugin:

```bash
/plugin install uv@jamie-bitflight-skills
```

## Usage

Once installed, Claude automatically uses this knowledge when you:

**Start a new Python project:**
```
Create a FastAPI web application with PostgreSQL support
```

Claude will use `uv init`, configure proper dependencies with `uv add`, and set up a modern project structure.

**Create a portable script:**
```
Write a script that fetches GitHub repo stats using the API
```

Claude will create a PEP 723 script with inline dependencies that runs anywhere.

**Migrate an existing project:**
```
Convert this pip-based project to use uv
```

Claude will migrate requirements.txt to pyproject.toml, set up lockfiles, and update workflows.

**Configure CI/CD:**
```
Set up GitHub Actions for testing and publishing this package
```

Claude will create workflows using uv best practices with caching and trusted publishing.

**Troubleshoot issues:**
```
uv lock is failing with a dependency conflict
```

Claude will diagnose the issue and suggest solutions using uv-specific troubleshooting techniques.

## Example: Before and After

**Before (without plugin):**
```
User: Set up a new Python project
Claude: *creates setup.py, requirements.txt, uses pip and virtualenv*
```

**After (with plugin):**
```
User: Set up a new Python project
Claude: I'll create a modern Python project using uv.

*runs:*
uv init myproject
cd myproject
uv add --dev pytest ruff mypy
uv sync

*creates proper pyproject.toml with dependency groups, lockfile, and .venv*
```

## What Makes This Different

**Comprehensive Coverage**: Covers all aspects of uv - not just basic commands but advanced features like workspaces, custom indexes, PyTorch backends, SBOM export, and dependency exclusions.

**Modern Standards**: Focuses on current best practices (PEP 723 scripts, PEP 735 dependency groups, lockfile-first workflows).

**Version-Aware**: Includes breaking changes in 0.10.0, deprecated flags, and feature availability across versions.

**Real-World Workflows**: Includes complete examples for CI/CD, Docker, pre-commit integration, and monorepos.

**Troubleshooting Focus**: Dedicated guidance on common errors, cache issues, and migration challenges.

**Auto-Updated**: Sync script keeps documentation current with latest uv releases.

## Requirements

- Claude Code v2.0+
- uv installed on your system (Claude can help you install it)

## What This Plugin Doesn't Do

This plugin provides knowledge and guidance only. It does not:
- Install uv itself (you need to install uv separately)
- Add new commands or tools to Claude Code
- Modify Claude's core behavior outside of Python project tasks

## Real-World Use Cases

**Scenario 1: Data Science Script**
You need a script that analyzes CSV files using pandas and matplotlib. Claude creates a PEP 723 script with inline dependencies, locks it for reproducibility, and makes it executable. Share the single file with colleagues - it works on any machine with uv.

**Scenario 2: Web API Development**
You're building a FastAPI application. Claude sets up a project with proper dependency groups (production, development, testing), configures uvicorn, adds database libraries, and creates Docker and GitHub Actions configurations using uv best practices.

**Scenario 3: Legacy Migration**
You have a 5-year-old project using pip, requirements.txt, and virtualenv. Claude analyzes your dependencies, migrates to pyproject.toml with proper version constraints, sets up lockfiles, and updates CI/CD pipelines to use uv.

**Scenario 4: Monorepo Management**
You're building a multi-package project with shared libraries. Claude configures uv workspaces, sets up workspace dependency references, creates a unified lockfile, and shows you how to build specific packages.

**Scenario 5: PyTorch Development**
You're building a machine learning project requiring specific CUDA versions. Claude configures custom PyTorch indexes, sets up torch-backend settings for automatic accelerator detection, and creates reproducible environments across different GPU systems.

## Key Concepts Covered

**Projects vs Scripts**
- Projects: Multi-file applications with pyproject.toml, lockfiles, and virtual environments
- Scripts: Single-file executables with PEP 723 inline metadata (dependencies embedded in comments)

**Lockfiles**
- uv.lock ensures reproducible installations across machines
- Lock scripts with `uv lock --script` for portable execution
- Upgrade packages with `uv lock --upgrade` or `--upgrade-package`

**Dependency Groups**
- Production dependencies in `[project.dependencies]`
- Development tools in `[dependency-groups]` (PEP 735)
- Optional features in `[project.optional-dependencies]`

**Virtual Environments**
- Auto-created in `.venv/` for projects
- Ephemeral environments for scripts
- Global tool environments managed by `uv tool`

**Python Management**
- Automatic downloads from python.org (CPython, PyPy, GraalPy, Pyodide)
- Pin versions with `.python-version` files
- Free-threaded Python support with `+gil` suffix

## Learn More

- uv Documentation: <https://docs.astral.sh/uv/>
- uv GitHub: <https://github.com/astral-sh/uv>
- PEP 723 (Inline Script Metadata): <https://peps.python.org/pep-0723/>
- PEP 735 (Dependency Groups): <https://peps.python.org/pep-0735/>
- PEP 740 (Attestations): <https://peps.python.org/pep-0740/>
