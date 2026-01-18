# XDG Base Directory Plugin

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Claude Code](https://img.shields.io/badge/claude--code-compatible-purple)

Implements standardized directory paths for configuration, data, cache, and state files following the XDG Base Directory Specification v0.8.

## Features

- **XDG Specification Compliance** - Complete implementation of XDG Base Directory Specification v0.8
- **Python Implementations** - Stdlib-only and platformdirs-based patterns for Linux, macOS, and Windows
- **Directory Selection Guide** - Clear guidance on choosing config vs data vs cache vs state directories
- **Anti-Pattern Detection** - Identifies common mistakes like `~/.appname` hardcoding and relative path acceptance
- **Testing Strategies** - Manual and automated testing approaches for XDG compliance validation
- **Cross-Platform Support** - Guidance for Linux-only and multi-platform applications

## Installation

### Prerequisites

- Claude Code 2.1 or later
- For cross-platform support: `platformdirs` Python package (optional)

### Install Plugin

```bash
# From Claude Code
/plugin install xdg-base-directory

# Or manually
git clone <repository-url> ~/.claude/plugins/xdg-base-directory
/plugin reload
```

## Quick Start

The plugin automatically activates when you work with file storage, configuration management, or application architecture:

```python
# Claude will apply XDG guidance automatically when you:
# - Create CLI tools that store user-specific files
# - Design configuration file management
# - Write code that accesses ~/.appname paths
# - Implement cross-platform Python applications
```

**Example Task:**

> "Create a Python CLI tool that stores config in the right place"

Claude will automatically:
1. Use `$XDG_CONFIG_HOME` for configuration files
2. Validate paths are absolute per specification
3. Handle environment variable overrides correctly
4. Create appropriate directory structure

## Capabilities

| Type | Name | Description | Invocation |
|------|------|-------------|------------|
| Skill | xdg-base-directory | Implements XDG Base Directory Specification for config, data, cache, and state file management | Automatic when working with file storage |

## Usage

### When This Skill Activates

The xdg-base-directory skill automatically applies when:

- Creating CLI tools or applications that store user-specific files
- Implementing configuration file management for Linux/Unix applications
- Building cross-platform Python applications requiring standardized directory paths
- Migrating legacy applications from `~/.appname` to XDG-compliant paths
- Designing file storage architecture for Python packages
- Implementing proper environment variable handling for user directories
- Writing applications that respect user-configured directory preferences
- Testing applications with custom XDG directory overrides

### Directory Selection Guide

The skill helps you choose the appropriate directory based on data characteristics:

| Directory | Purpose | Default Path | Use For |
|-----------|---------|--------------|---------|
| `$XDG_CONFIG_HOME` | User configuration | `~/.config` | Settings, preferences, user configs |
| `$XDG_DATA_HOME` | User data files | `~/.local/share` | Databases, generated content, persistent data |
| `$XDG_STATE_HOME` | User state files | `~/.local/state` | Logs, history, undo buffers, recent files |
| `$XDG_CACHE_HOME` | User cache files | `~/.cache` | Temporary data, downloads, build artifacts |
| `$XDG_RUNTIME_DIR` | User runtime files | `/run/user/$UID` | Sockets, pipes, lock files, IPC |

### Python Implementation Patterns

The skill provides two implementation strategies:

**Stdlib-Only** (for Linux/Unix-only applications):

```python
from pathlib import Path
import os

def get_config_home() -> Path:
    """Get XDG_CONFIG_HOME path."""
    xdg = os.environ.get('XDG_CONFIG_HOME')
    if xdg and Path(xdg).is_absolute():
        return Path(xdg)
    return Path.home() / '.config'
```

**Cross-Platform with platformdirs** (for Linux/macOS/Windows):

```python
from platformdirs import user_config_dir, user_data_dir
from pathlib import Path

config_dir = Path(user_config_dir('myapp', 'myapp'))
data_dir = Path(user_data_dir('myapp', 'myapp'))
```

## Examples

See [docs/examples.md](./docs/examples.md) for concrete usage examples including:

- Building an XDG-compliant CLI tool
- Migrating a legacy `~/.appname` application
- Implementing cross-platform configuration management
- Testing XDG compliance

## Key Principles

The skill enforces these core XDG specification requirements:

1. **Absolute Paths Only** - Validate all XDG paths are absolute; ignore relative paths
2. **Environment Variable Priority** - Always check XDG environment variables before defaults
3. **Specification Compliance** - Follow XDG Base Directory Specification v0.8 exactly
4. **Directory Creation** - Create parent directories before writing files
5. **Appropriate Storage** - Use correct directory for data type (config vs data vs cache vs state)
6. **Runtime Directory Limits** - Avoid large files in `$XDG_RUNTIME_DIR` (tmpfs limits)
7. **Cross-Platform Awareness** - Use platformdirs for macOS/Windows support
8. **Search Path Handling** - Parse colon-separated search paths correctly
9. **No Default for Runtime** - `$XDG_RUNTIME_DIR` has no default; check for None
10. **Testing** - Validate XDG compliance with environment variable overrides

## Common Anti-Patterns

The skill detects and prevents these common mistakes:

| Anti-Pattern | Problem | Solution |
|--------------|---------|----------|
| `~/.appname` hardcoding | Violates XDG spec, clutters home directory | Use `~/.config/appname/` |
| Ignoring environment variables | Prevents user customization | Check `$XDG_CONFIG_HOME` first |
| Accepting relative paths | XDG spec mandates absolute paths only | Validate and reject relative paths |
| Missing directory creation | Write fails if parent doesn't exist | Use `mkdir(parents=True, exist_ok=True)` |
| Cache in config directory | Mixes regenerable data with configuration | Use `$XDG_CACHE_HOME` for cache |
| Large files in runtime dir | Often tmpfs-mounted with size limits | Use `$XDG_DATA_HOME` for large files |
| Not handling unset `XDG_RUNTIME_DIR` | Has no default value | Check for None before using |

## Troubleshooting

### My application doesn't respect XDG variables

Verify environment variables are set:

```bash
echo $XDG_CONFIG_HOME
echo $XDG_DATA_HOME
```

Check that your code validates absolute paths:

```python
# Correct validation
xdg = os.environ.get('XDG_CONFIG_HOME')
if xdg and Path(xdg).is_absolute():
    return Path(xdg)
return Path.home() / '.config'  # Fallback
```

### Files appear in wrong location

Check directory selection guide - ensure you're using the right XDG directory for your data type. Configuration goes in `$XDG_CONFIG_HOME`, cache in `$XDG_CACHE_HOME`, etc.

### Tests fail with custom XDG directories

Ensure tests use `monkeypatch` to set environment variables before importing your application code:

```python
def test_custom_config(monkeypatch):
    monkeypatch.setenv('XDG_CONFIG_HOME', '/tmp/test-config')
    # Now import and test
```

### XDG_RUNTIME_DIR is None

`$XDG_RUNTIME_DIR` has no default - it must be set by the system. Check for None before using:

```python
runtime_dir = get_runtime_dir()
if runtime_dir is None:
    raise RuntimeError("XDG_RUNTIME_DIR not set by system")
```

## Related Skills

- `toml-python` - TOML configuration file parsing and validation
- `python3-development` - Modern Python development patterns and best practices
- `uv` - Python package and project management

## License

[License information not specified]

## References

- [XDG Base Directory Specification v0.8](https://specifications.freedesktop.org/basedir-spec/latest/) - Official specification
- [ArchWiki: XDG Base Directory](https://wiki.archlinux.org/title/XDG_Base_Directory) - Implementation guide
- [platformdirs Python Library](https://github.com/tox-dev/platformdirs) - Cross-platform implementation
