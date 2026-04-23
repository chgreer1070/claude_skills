# Plugin User Configuration — Complete Reference

The `userConfig` field in `plugin.json` declares values that users are prompted to configure when they enable the plugin. Sensitive values are stored in the system keychain; non-sensitive values are stored in `settings.json`.

SOURCE: [Plugins Reference](https://code.claude.com/docs/en/plugins-reference.md) lines 998-1085 (accessed 2026-04-23)

---

## plugin.json Declaration

```json
{
  "name": "my-plugin",
  "userConfig": {
    "api_key": {
      "type": "string",
      "title": "API Key",
      "description": "Your service API key",
      "sensitive": true,
      "required": true
    },
    "endpoint": {
      "type": "string",
      "title": "API Endpoint",
      "description": "Base URL for API requests",
      "default": "https://api.example.com",
      "required": false
    },
    "max_results": {
      "type": "number",
      "title": "Maximum Results",
      "description": "Maximum number of results to return per query",
      "default": 10,
      "min": 1,
      "max": 100
    },
    "data_dir": {
      "type": "directory",
      "title": "Data Directory",
      "description": "Local directory for storing plugin data"
    },
    "tags": {
      "type": "string",
      "title": "Default Tags",
      "description": "Comma-separated tags to apply",
      "multiple": true
    }
  }
}
```

---

## userConfig Field Schema

Each key in `userConfig` maps to a configuration entry with the following fields:

| Field | Required | Type | Description |
| ----- | -------- | ---- | ----------- |
| `type` | Yes | string | Value type: `string`, `number`, `boolean`, `directory`, or `file` |
| `title` | Yes | string | Human-readable label shown during prompt |
| `description` | No | string | Additional context shown to the user |
| `sensitive` | No | boolean | If `true`, value stored in system keychain; default `false` |
| `required` | No | boolean | If `true`, user must provide a value to enable the plugin |
| `default` | No | any | Default value (must match `type`) |
| `multiple` | No | boolean | If `true`, user can provide multiple values |
| `min` | No | number | Minimum value (for `type: "number"` only) |
| `max` | No | number | Maximum value (for `type: "number"` only) |

### Storage by `sensitive`

| `sensitive` value | Storage location |
| ----------------- | ---------------- |
| `true` | System keychain (OS credential manager) |
| `false` (default) | `settings.json` in the appropriate scope |

---

## Substitution Syntax

Use `${user_config.KEY}` anywhere that supports variable substitution:

- MCP server `command`, `args`, and `env` fields
- LSP server `command` and `args` fields
- Hook and monitor `command` fields
- Skill and agent content (for non-sensitive values)

```json
{
  "mcpServers": {
    "my-service": {
      "command": "${CLAUDE_PLUGIN_ROOT}/server",
      "env": {
        "API_KEY": "${user_config.api_key}",
        "ENDPOINT": "${user_config.endpoint}"
      }
    }
  }
}
```

---

## Channels Field

The `channels` field in `plugin.json` declares message channel bindings that connect MCP servers to user-configured values.

SOURCE: [Plugins Reference](https://code.claude.com/docs/en/plugins-reference.md) lines 1087-1118 (accessed 2026-04-23)

```json
{
  "name": "my-plugin",
  "channels": [
    {
      "server": "my-mcp-server",
      "userConfig": {
        "bot_token": {
          "type": "string",
          "title": "Bot Token",
          "description": "Authentication token for the channel bot",
          "sensitive": true,
          "required": true
        }
      }
    }
  ]
}
```

Each channel object binds an MCP server to per-channel user configuration. The user is prompted for the channel-specific values when they enable the plugin. This is used for chat integration patterns (e.g., Slack, Teams bots).
