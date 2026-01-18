# Hatchling

Comprehensive documentation for Hatchling, the modern Python build backend that implements PEP 517/518/621/660 standards. Use when working with Python packaging, pyproject.toml configuration, build system setup, and package distribution.

## Installation

**From Marketplace:**

```bash
/plugin marketplace add Jamie-BitFlight/claude_skills
/plugin install hatchling@jamie-bitflight-skills
```

**For Development:**

```bash
claude --plugin-dir /home/user/claude_skills/plugins/hatchling
```

## Capabilities

| Type | Name | Description |
|------|------|-------------|
| Skill | [hatchling](./skills/hatchling/SKILL.md) | Comprehensive documentation for Hatchling, the modern Python build backend. Covers configuration, build system setup, Python packaging, pyproject.toml, project metadata, dependencies, entry points, build hooks, version management, wheel and sdist builds, package distribution, setuptools migration, and troubleshooting. |

## Quick Start

Activate the skill when working with Hatchling-based Python projects:

```text
@hatchling
Help me configure Hatchling for a new Python package with CLI entry points and version management
```

The skill provides:
- **Project Configuration** - Package metadata, dependencies, entry points, dynamic fields
- **Build System Setup** - PEP 517/518 compliance, reproducible builds, environment variables
- **Build Targets** - Wheel and source distribution customization
- **Build Hooks** - Dynamic code execution during builds
- **Version Management** - Multiple version sources with automatic injection
- **File Selection** - Git-aware VCS integration with glob patterns
- **Migration Guides** - Converting from setuptools to Hatchling

## Common Use Cases

**Setting up a new package:**
```text
@hatchling
Configure pyproject.toml for a new CLI tool with dependencies on requests and click
```

**Troubleshooting builds:**
```text
@hatchling
Why is my package failing to build with "No such file or directory: pyproject.toml"?
```

**Adding build hooks:**
```text
@hatchling
How do I add a custom build hook to compile Cython extensions?
```

## License

Version 1.0.0
