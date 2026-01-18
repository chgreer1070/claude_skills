# uv

Expert guidance for Astral's uv - an extremely fast Python package and project manager. Use when working with Python projects, managing dependencies, creating scripts with PEP 723 metadata, installing tools, managing Python versions, or configuring package indexes. Covers project initialization, dependency management, virtual environments, tool installation, workspace configuration, CI/CD integration, and migration from pip/poetry.

## Installation

**From Marketplace:**

```bash
/plugin marketplace add Jamie-BitFlight/claude_skills
/plugin install uv@jamie-bitflight-skills
```

**For Development:**

```bash
claude --plugin-dir /home/user/claude_skills/plugins/uv
```

## Capabilities

| Type | Name | Description |
|------|------|-------------|
| Skill | [uv](./skills/uv/SKILL.md) | Expert guidance for Astral's uv - an extremely fast Python package and project manager. Use when working with Python projects, managing dependencies, creating scripts with PEP 723 metadata, installing tools, managing Python versions, or configuring package indexes. |

## Quick Start

Initialize a new Python project with uv:

```bash
# Create a new application project
uv init myapp

# Navigate into the project
cd myapp

# Add dependencies
uv add requests httpx

# Run your project
uv run python -m myapp
```

For comprehensive uv guidance, activate the skill:

```text
@uv
Help me set up a Python project with dependencies
```

## Features

- **Project Initialization** - Create new Python projects with recommended structure
- **Dependency Management** - Add, remove, and update dependencies with lockfile support
- **PEP 723 Scripts** - Create portable single-file scripts with inline metadata
- **Tool Installation** - Install and run CLI tools like ruff, black, and httpie
- **Python Version Management** - Install and manage Python interpreters
- **Virtual Environments** - Fast virtual environment creation and management
- **Package Indexes** - Configure PyPI alternatives and private registries
- **CI/CD Integration** - Optimize build caching and reproducible deployments
- **Migration Support** - Move from pip, pip-tools, poetry, or conda

## License

Version 1.0.0
