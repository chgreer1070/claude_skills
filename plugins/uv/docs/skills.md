# Skills Reference

This plugin provides comprehensive guidance for Astral's uv - an extremely fast Python package and project manager.

## uv

**Location**: `skills/uv/SKILL.md`

**Description**: Expert guidance for Astral's uv - an extremely fast Python package and project manager. Use when working with Python projects, managing dependencies, creating scripts with PEP 723 metadata, installing tools, managing Python versions, or configuring package indexes. Covers project initialization, dependency management, virtual environments, tool installation, workspace configuration, CI/CD integration, and migration from pip/poetry.

**User Invocable**: Yes (default)

**Allowed Tools**: Inherits from session (no restrictions)

**Model**: Inherits from session

### When to Use

The uv skill automatically activates when Claude detects you're working with:

- Python project initialization or configuration
- Dependency management (adding, removing, updating packages)
- Creating or modifying PEP 723 scripts with inline metadata
- Installing or running Python tools (ruff, black, pytest, etc.)
- Managing Python interpreter versions
- Virtual environment setup or configuration
- Package index configuration or authentication
- Migrating from pip, pip-tools, poetry, or conda
- CI/CD pipeline configuration for Python projects
- Docker configuration for Python applications
- Dependency resolution or build troubleshooting

### Activation

The skill activates automatically based on context, or you can invoke it explicitly:

```
@uv
```

or

```
Skill(command: "uv")
```

### Core Capabilities

#### 1. Project Management

**Initialize new projects:**

- Standard projects with `uv init`
- Application projects with `--app` flag
- Library projects with `--lib` and build backend configuration
- Bare projects (pyproject.toml only) with `--bare`

**Project structure:**

- Virtual environment (`.venv/`)
- Python version pinning (`.python-version`)
- Project metadata (`pyproject.toml`)
- Dependency lockfile (`uv.lock`)

#### 2. Dependency Management

**Add dependencies:**

- Production dependencies with `uv add`
- Development dependencies with `--dev` flag
- Optional dependency groups with `--group` flag
- Dependencies from git, local paths, or various package sources

**Lock and sync:**

- Update lockfile with `uv lock`
- Install dependencies with `uv sync`
- Upgrade specific packages with `--upgrade-package`
- Production-only installs with `--no-dev`
- Frozen installs for CI/CD with `--frozen`

#### 3. Script Management

**Create portable scripts:**

- Initialize with PEP 723 metadata using `uv init --script`
- Add dependencies with `uv add --script`
- Lock scripts for reproducibility
- Make executable with proper shebang

**Script features:**

- Inline dependency specification
- Python version requirements
- Automatic environment creation
- Cross-platform compatibility

#### 4. Tool Management

**Ephemeral execution:**

- Run tools without installing with `uvx`
- Specify versions or version ranges
- Add plugin dependencies with `--with`

**Persistent installation:**

- Install globally with `uv tool install`
- Upgrade tools with `uv tool upgrade`
- List installed tools with `uv tool list`
- Update shell configuration with `uv tool update-shell`

#### 5. Python Version Management

**Install and manage Python:**

- Auto-download Python versions with `uv python install`
- Pin versions for projects with `uv python pin`
- List available versions with `uv python list`
- Find Python executables with `uv python find`

**Python sources:**

- CPython (official Python)
- PyPy (JIT-compiled Python)
- GraalPy (GraalVM Python)
- Other implementations

#### 6. Virtual Environment Management

**Create environments:**

- Standard virtual environments with `uv venv`
- Specify Python version with `--python`
- Custom paths
- System package access with `--system-site-packages`

**Warning**: `uv venv` overwrites existing environments without confirmation.

#### 7. pip Compatibility

**Drop-in replacement:**

- `uv pip install` - Install packages
- `uv pip compile` - Generate requirements files (like pip-compile)
- `uv pip sync` - Sync environment to requirements (like pip-sync)
- `uv pip list` - List installed packages
- `uv pip show` - Show package information
- `uv pip tree` - Display dependency tree
- `uv pip freeze` - Export installed packages

#### 8. Workspace Management

**Monorepo support:**

- Configure workspaces in root `pyproject.toml`
- Reference workspace members in dependencies
- Build specific packages with `--package`
- Single lockfile for entire workspace

#### 9. Package Building and Publishing

**Build distributions:**

- Create wheels and source distributions with `uv build`
- Build specific workspace packages
- Custom output directories

**Publish to PyPI:**

- Direct publishing with `uv publish`
- Token authentication
- Test PyPI support
- Trusted publishing integration

### Configuration

The skill provides guidance on:

**pyproject.toml:**

- `[project]` - Project metadata and dependencies
- `[dependency-groups]` - Development and optional dependency groups (PEP 735)
- `[build-system]` - Build backend configuration
- `[tool.uv]` - uv-specific settings
- `[tool.uv.sources]` - Custom package sources
- `[[tool.uv.index]]` - Custom package indexes

**Environment Variables:**

- Cache and directory configuration
- Python preference and download settings
- Network concurrency settings
- Index authentication
- Preview features

**For complete configuration reference**, see [../skills/uv/references/configuration.md](../skills/uv/references/configuration.md)

### Common Workflows

The skill provides detailed guidance for:

- Starting a new Python project from scratch
- Creating portable single-file scripts
- Migrating from pip/requirements.txt
- Migrating from Poetry
- CI/CD integration with GitHub Actions
- Docker containerization
- Git hook integration (pre-commit/prek)

### Troubleshooting

The skill includes comprehensive troubleshooting guidance for:

- "Externally managed" interpreter errors
- Build failures and missing dependencies
- Lockfile sync issues
- Cache problems
- Common pitfalls and mistakes

**For detailed troubleshooting**, see [../skills/uv/references/troubleshooting.md](../skills/uv/references/troubleshooting.md)

### Reference Files

The skill includes detailed reference documentation that's loaded on demand:

**CLI Reference** - [../skills/uv/references/cli_reference.md](../skills/uv/references/cli_reference.md)

- Complete command reference
- All command-line arguments and options
- Usage examples for each command

**Configuration Reference** - [../skills/uv/references/configuration.md](../skills/uv/references/configuration.md)

- All configuration options in `pyproject.toml`
- Environment variables
- Authentication and index configuration
- Advanced settings

**Troubleshooting Guide** - [../skills/uv/references/troubleshooting.md](../skills/uv/references/troubleshooting.md)

- Common error messages and solutions
- Build failure diagnosis
- Dependency resolution issues
- Performance optimization

### Assets

The skill provides example templates in the assets directory:

**Docker Examples** - `skills/uv/assets/docker_examples/`

- Simple Dockerfile
- Multi-stage build Dockerfile

**pyproject.toml Templates** - `skills/uv/assets/pyproject_templates/`

- Basic configuration
- Advanced configuration
- GitLab-specific configuration

**Script Examples** - `skills/uv/assets/script_examples/`

- Data analysis script template

**GitHub Actions** - `skills/uv/assets/github_actions/`

- CI workflow template

### Key Principles

The skill emphasizes:

1. **Speed** - uv is 10-100x faster than traditional Python tools
2. **Reproducibility** - Lockfiles ensure consistent environments across machines
3. **Simplicity** - Single tool replaces pip, pip-tools, pipx, poetry, pyenv, virtualenv
4. **Modern Standards** - PEP 723 scripts, PEP 735 dependency groups, standard pyproject.toml
5. **Developer Experience** - Automatic Python installation, smart defaults, minimal configuration

### Version Information

The skill documents uv version **0.9.5** (October 2025) with:

- Python 3.14 support with free-threaded builds
- Enhanced authentication system
- Advanced build configuration
- Workspace improvements
- Docker image optimizations

### External Resources

The skill references:

- [Official Documentation](https://docs.astral.sh/uv/)
- [GitHub Repository](https://github.com/astral-sh/uv)
- [Concepts Guide](https://docs.astral.sh/uv/concepts/)
- [Migration Guides](https://docs.astral.sh/uv/guides/migration/)

---

## Summary

The uv skill provides comprehensive, expert-level guidance for all aspects of Python project management with Astral's uv. It automatically activates when you're working with Python projects and provides detailed, actionable guidance for initialization, dependency management, script creation, tool management, CI/CD integration, and troubleshooting.
