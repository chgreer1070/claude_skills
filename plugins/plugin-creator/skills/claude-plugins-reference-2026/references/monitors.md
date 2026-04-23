# Plugin Monitors — Complete Reference

Monitors are background processes that run for the lifetime of a Claude Code session. Each line written to a monitor's stdout is delivered as a notification to Claude.

SOURCE: [Plugins Reference](https://code.claude.com/docs/en/plugins-reference.md) lines 1087-1132 (accessed 2026-04-23)

---

## Availability Constraints

- Require Claude Code v2.1.105 or later
- Run only in interactive CLI sessions
- Run unsandboxed at the same trust level as hooks
- Skipped on hosts where the Monitor tool is unavailable

---

## Configuration Location

Monitors are declared in one of two places:

1. `monitors/monitors.json` file in the plugin root
2. Inline `monitors` array in `plugin.json`

### Inline in plugin.json

```json
{
  "name": "my-plugin",
  "monitors": [
    {
      "name": "file-watcher",
      "command": "${CLAUDE_PLUGIN_ROOT}/scripts/watch-files.sh",
      "description": "Watches for file changes and notifies Claude",
      "when": "always"
    }
  ]
}
```

### As monitors/monitors.json

```json
[
  {
    "name": "build-watcher",
    "command": "${CLAUDE_PLUGIN_ROOT}/scripts/watch-build.sh",
    "description": "Monitors build output and surfaces errors",
    "when": "on-skill-invoke:my-build-skill"
  }
]
```

Reference from `plugin.json`:

```json
{
  "name": "my-plugin",
  "monitors": "./monitors/monitors.json"
}
```

---

## Monitor Object Schema

| Field | Required | Type | Description |
| ----- | -------- | ---- | ----------- |
| `name` | Yes | string | Unique identifier within the plugin |
| `command` | Yes | string | Shell command to run as background process |
| `description` | Yes | string | Human-readable description of what the monitor does |
| `when` | No | string | Activation condition (see below) |

### `when` Field Values

| Value | Meaning |
| ----- | ------- |
| `always` (default) | Monitor starts when the plugin is active, runs for the entire session |
| `on-skill-invoke:<skill-name>` | Monitor starts the first time the named skill is invoked; runs for the rest of the session |

---

## Variable Substitution in Commands

Monitor `command` fields support the same substitution variables as hooks:

| Variable | Value |
| -------- | ----- |
| `${CLAUDE_PLUGIN_ROOT}` | Absolute path to the plugin directory |
| `${CLAUDE_PLUGIN_DATA}` | Persistent plugin data directory (survives updates) |
| `${user_config.KEY}` | User-configured value for `KEY` (see `userConfig` field) |
| `${ENV_VAR}` | Any environment variable from the shell |

---

## Behavior Details

- Each stdout line from the monitor process is delivered to Claude as a notification
- Monitors start automatically when the plugin becomes active (based on `when`)
- A monitor crashing does not terminate the session — Claude Code restarts it
- Monitor stderr is not delivered to Claude; use stdout for all notifications
- Monitors run at the same privilege level as hooks (unsandboxed)
