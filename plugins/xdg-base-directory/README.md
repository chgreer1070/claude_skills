# XDG Base Directory

Standardized directory paths for configuration, data, cache, and state files following the XDG Base Directory Specification. Use when designing where user-specific files should live, migrating from `~/.appname` patterns, or implementing cross-platform file storage.

## Installation

**From Marketplace:**

```bash
/plugin marketplace add Jamie-BitFlight/claude_skills
/plugin install xdg-base-directory@jamie-bitflight-skills
```

**For Development:**

```bash
claude --plugin-dir /home/user/claude_skills/plugins/xdg-base-directory
```

## Capabilities

| Type | Name | Description |
|------|------|-------------|
| Skill | [xdg-base-directory](./skills/xdg-base-directory/SKILL.md) | When an application needs to store config, data, cache, or state files. When designing where user-specific files should live. When code writes to ~/.appname or hardcoded home paths. When implementing cross-platform file storage with platformdirs. |

## Quick Start

Ask Claude to implement XDG-compliant path management for your Python application:

```text
@xdg-base-directory
Create a paths.py module for my CLI app 'myapp' that stores:
- Configuration in the right XDG directory
- Downloaded models in the appropriate data directory
- Build cache in the cache directory
- Command history in the state directory

Use stdlib-only implementation (no external dependencies).
```

Claude will generate compliant path functions following the XDG Base Directory Specification v0.8, ensuring:
- Environment variable support (`$XDG_CONFIG_HOME`, etc.)
- Absolute path validation
- Proper fallback to specification defaults
- Appropriate directory selection based on data type

## License

See [LICENSE](../../LICENSE) for details.
