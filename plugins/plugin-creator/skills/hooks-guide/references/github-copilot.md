# GitHub Copilot Agent Hooks Reference

SOURCE: [Using hooks with GitHub Copilot agents](https://docs.github.com/en/copilot/how-tos/use-copilot-agents/coding-agent/using-hooks-with-github-copilot-agents) (accessed 2026-03-01)

## Table of Contents

1. [File Location](#file-location)
2. [Schema](#schema)
3. [Hook Events](#hook-events)
4. [Command Entry Fields](#command-entry-fields)
5. [Exit Codes](#exit-codes)
6. [Debugging](#debugging)
7. [Differences from Claude Code Hooks](#differences-from-claude-code-hooks)

---

## File Location

- Repository hooks: `.github/hooks/` directory on the repository's **default branch**
- GitHub Copilot CLI hooks: loaded from the current working directory
- Filename is user-chosen; must be valid JSON

The hooks configuration file must be present on the default branch to be used by the Copilot coding agent.

---

## Schema

Top-level structure requires `version: 1` and a `hooks` object with event arrays:

```json
{
  "version": 1,
  "hooks": {
    "sessionStart": [],
    "sessionEnd": [],
    "userPromptSubmitted": [],
    "preToolUse": [],
    "postToolUse": [],
    "errorOccurred": []
  }
}
```

Remove any event keys you do not plan to use from the `hooks` object.

---

## Hook Events

All event names are camelCase.

| Event                | When it fires                                    |
| :------------------- | :----------------------------------------------- |
| `sessionStart`       | When an agent session begins                     |
| `sessionEnd`         | When an agent session ends                       |
| `userPromptSubmitted`| When a user submits a prompt                     |
| `preToolUse`         | Before the agent uses a tool                     |
| `postToolUse`        | After the agent uses a tool                      |
| `errorOccurred`      | When an error occurs during agent execution      |

---

## Command Entry Fields

Each entry in an event array is a command object:

```json
{
  "type": "command",
  "bash": "<shell command or script path>",
  "powershell": "<powershell command or script path>",
  "cwd": "<working directory>",
  "env": {
    "KEY": "VALUE"
  },
  "timeoutSec": 30
}
```

| Field        | Required | Description                                                      |
| :----------- | :------- | :--------------------------------------------------------------- |
| `type`       | Yes      | Must be `"command"`                                              |
| `bash`       | No       | Shell command or script path for Unix/macOS                      |
| `powershell` | No       | PowerShell command or script path for Windows                    |
| `cwd`        | No       | Working directory for the command                                |
| `env`        | No       | Object of environment variable key/value pairs                   |
| `timeoutSec` | No       | Timeout in seconds. Default: 30                                  |

At least one of `bash` or `powershell` must be provided. Both can be provided for cross-platform hooks.

Example — log session start timestamp:

```json
"sessionStart": [
  {
    "type": "command",
    "bash": "echo \"Session started: $(date)\" >> logs/session.log",
    "powershell": "Add-Content -Path logs/session.log -Value \"Session started: $(Get-Date)\"",
    "cwd": ".",
    "timeoutSec": 10
  }
]
```

Example — call an external script with environment variable:

```json
"userPromptSubmitted": [
  {
    "type": "command",
    "bash": "./scripts/log-prompt.sh",
    "powershell": "./scripts/log-prompt.ps1",
    "cwd": "scripts",
    "env": {
      "LOG_LEVEL": "INFO"
    }
  }
]
```

---

## Exit Codes

No explicit non-zero exit code semantics are documented for GitHub Copilot hooks. Scripts must be executable (`chmod +x script.sh`) and have a proper shebang (e.g., `#!/bin/bash`).

JSON output from hooks must be on a single line:

- Unix: use `jq -c` to compact and validate
- Windows: use `ConvertTo-Json -Compress` in PowerShell

---

## Debugging

Enable verbose logging inside the hook script to inspect input data:

```bash
#!/bin/bash
set -x  # Enable bash debug mode
INPUT=$(cat)
echo "DEBUG: Received input" >&2
echo "$INPUT" >&2
# ... rest of script
```

Test hooks locally by piping test input:

```bash
# Create test input
echo '{"timestamp":1704614400000,"cwd":"/tmp","toolName":"bash","toolArgs":"{\"command\":\"ls\"}"}' | ./my-hook.sh

# Check exit code
echo $?

# Validate output is valid JSON
./my-hook.sh | jq .
```

---

## Differences from Claude Code Hooks

| Dimension              | GitHub Copilot                              | Claude Code                                                    |
| :--------------------- | :------------------------------------------ | :------------------------------------------------------------- |
| Event name casing      | camelCase (`preToolUse`, `sessionStart`)    | PascalCase (`PreToolUse`, `Stop`, `SubagentStop`)              |
| Command specification  | Dual keys: `bash` and `powershell`          | Single `command` key (shell-agnostic string)                   |
| Config file location   | `.github/hooks/<name>.json` on default branch | `hooks/hooks.json` (auto-discovered) or `settings.json`     |
| Version field          | `"version": 1` required                     | No version field                                               |
| Matcher concept        | None — hooks apply to all calls of that event type | `matcher` field filters by tool name or agent type        |
| Schema nesting         | Event key → array of command objects        | Event key → array of matcher groups → array of hook objects    |
