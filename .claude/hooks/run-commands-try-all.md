# run-commands-try-all

Cross-platform hook that runs a list of commands, continues on failure, and shows errors.

## Usage

### 1. Commands as arguments (typical)

Add to `.claude/settings.json`:

```json
{
  "hooks": {
    "Setup": [
      {
        "matcher": "init|maintenance",
        "hooks": [
          {
            "type": "command",
            "command": "node \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/run-commands-try-all.cjs \"uv self update\" \"uv run prek install -t pre-commit -t commit-msg -t pre-rebase -t post-merge\""
          }
        ]
      }
    ]
  }
}
```

### 2. Commands from stdin JSON

For hook events that pass JSON, the script accepts a `commands` array:

```json
{ "commands": ["uv self update", "uv run prek install"] }
```

### Behavior

- **Windows**: runs each command via `cmd /c`
- **Linux/macOS**: runs each command via `sh -c`
- **On failure**: writes error to stderr and continues to the next command
- **Exit code**: always 0 (never blocks the hook)
