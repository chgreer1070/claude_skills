# TOML Python

Python TOML file handling with comment and formatting preservation using tomlkit.

## Installation

**From Marketplace:**

```bash
/plugin marketplace add Jamie-BitFlight/claude_skills
/plugin install toml-python@jamie-bitflight-skills
```

**For Development:**

```bash
claude --plugin-dir /home/user/claude_skills/plugins/toml-python
```

## Capabilities

| Type | Name | Description |
|------|------|-------------|
| Skill | [toml-python](./skills/toml-python/SKILL.md) | When reading or writing pyproject.toml or .toml config files in Python. When editing TOML while preserving comments and formatting. When designing configuration file format for a Python tool. When code uses tomlkit or tomllib. When implementing atomic config file updates. |

## Quick Start

The toml-python skill provides guidance on using tomlkit for TOML file operations in Python. It activates automatically when working with TOML configuration files.

**Example: Modify pyproject.toml while preserving comments**

```python
import tomlkit

# Read existing config
with open("pyproject.toml") as f:
    config = tomlkit.load(f)

# Modify values (comments and formatting preserved)
config["project"]["version"] = "2.0.0"

# Write back atomically
with open("pyproject.toml", "w") as f:
    tomlkit.dump(config, f)
```

The skill covers:
- Choosing between tomlkit (read/write) vs tomllib (read-only)
- Comment and formatting preservation
- Atomic file updates
- XDG Base Directory integration
- Error handling patterns

## License

See [LICENSE](../../LICENSE) for details.
