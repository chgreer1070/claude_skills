# Cross-Platform Hooks Common Schema

SOURCE: [Claude Code hooks reference](https://code.claude.com/docs/en/hooks-reference.md) (accessed 2026-03-01)
SOURCE: [GitHub Copilot agent hooks](https://docs.github.com/en/copilot/how-tos/use-copilot-agents/coding-agent/using-hooks-with-github-copilot-agents) (accessed 2026-03-01)

## Table of Contents

1. [Concept Map](#concept-map)
2. [Common Event Categories](#common-event-categories)
3. [Common Fields Across Platforms](#common-fields-across-platforms)
4. [Exit Code Conventions](#exit-code-conventions)
5. [Context Passing Patterns](#context-passing-patterns)
6. [JSON Output Control](#json-output-control)
7. [Platform Comparison Table](#platform-comparison-table)

---

## Concept Map

Both Claude Code and GitHub Copilot implement the same conceptual model:

```text
Agent lifecycle
    │
    ├── Event fires at a lifecycle point
    │       (e.g. "before tool runs", "session starts")
    │
    ├── Trigger: does a matcher match the event context?
    │       Claude Code: regex against tool_name, agent_type, etc.
    │       GitHub Copilot: no matcher — all hooks in the event array run
    │
    └── Command or script executes
            Receives context (stdin JSON or env vars)
            Returns decision via exit code and/or stdout JSON
```

A "hook" is the combination of the lifecycle event, the optional trigger condition (matcher), and the handler that runs. The handler receives context about what the agent is about to do or just did, and can allow, block, or annotate the action.

---

## Common Event Categories

The following event categories exist across both Claude Code and GitHub Copilot. Event names differ by platform — see the [Platform Comparison Table](#platform-comparison-table) for exact names.

### Session Lifecycle

Events that fire once at the start or end of an agent session.

| Category | Claude Code event | GitHub Copilot event | Purpose |
| :--- | :--- | :--- | :--- |
| Session start | `SessionStart` | `sessionStart` | Load context, configure environment |
| Session end | `SessionEnd` | `sessionEnd` | Cleanup, logging, reporting |

Session start hooks are well-suited for injecting dynamic context that cannot be expressed as static files (e.g., current open issues, recent git log). Static context belongs in configuration files — not hooks.

### Tool or Action Pre and Post

Events that fire before and after the agent performs an action.

| Category | Claude Code event | GitHub Copilot event | Purpose |
| :--- | :--- | :--- | :--- |
| Before tool use | `PreToolUse` | `preToolUse` | Validate, block, or modify actions |
| After tool use | `PostToolUse` | `postToolUse` | React to completed actions |

`PreToolUse` (and `preToolUse`) are the primary control points for policy enforcement — they can block the action before it occurs.

### User Input Submission

Events that fire when a user submits a prompt.

| Category | Claude Code event | GitHub Copilot event | Purpose |
| :--- | :--- | :--- | :--- |
| User prompt submitted | `UserPromptSubmit` | `userPromptSubmitted` | Filter, log, or block user input |

### Agent or Subagent Lifecycle

Events unique to Claude Code's multi-agent architecture. GitHub Copilot has no equivalent.

| Claude Code event | Purpose |
| :--- | :--- |
| `SubagentStart` | Fires when a subagent is spawned |
| `SubagentStop` | Fires when a subagent finishes — primary hook point for task completion tracking |
| `TeammateIdle` | Fires when an agent team teammate is about to go idle |
| `TaskCompleted` | Fires when a task is being marked complete |

### Additional Claude Code Events

Events with no GitHub Copilot equivalent:

| Event | Purpose |
| :--- | :--- |
| `PermissionRequest` | When a permission dialog appears — can auto-allow or deny |
| `PostToolUseFailure` | After a tool call fails |
| `Notification` | When Claude Code sends a notification |
| `Stop` | When Claude finishes responding |
| `ConfigChange` | When a configuration file changes mid-session |
| `WorktreeCreate` | When a worktree is being created |
| `WorktreeRemove` | When a worktree is being removed |
| `PreCompact` | Before context compaction |

### Additional GitHub Copilot Events

Events with no Claude Code equivalent:

| Event | Purpose |
| :--- | :--- |
| `errorOccurred` | When an error occurs during agent execution |

---

## Common Fields Across Platforms

### Timeout

Both platforms support per-hook timeout configuration.

| Platform | Field | Default | Notes |
| :--- | :--- | :--- | :--- |
| Claude Code | `timeout` | 600s (command), 30s (prompt), 60s (agent) | Seconds; per hook handler |
| GitHub Copilot | `timeoutSec` | 30 | Seconds; per command object |

### Working Directory

Both platforms allow hooks to specify the working directory in which commands execute.

| Platform | Field | Notes |
| :--- | :--- | :--- |
| Claude Code | Not a top-level field; handlers inherit Claude Code's current working directory. Use `$CLAUDE_PROJECT_DIR` or `${CLAUDE_PLUGIN_ROOT}` to reference paths. | Path available via `cwd` in stdin JSON |
| GitHub Copilot | `cwd` | Explicit working directory per command object |

### Environment Variables

Both platforms support passing environment variables to hook commands.

| Platform | Field | Notes |
| :--- | :--- | :--- |
| Claude Code | No `env` field in hook definition. Use `CLAUDE_ENV_FILE` in `SessionStart` hooks to persist variables for subsequent Bash commands. | `$CLAUDE_CODE_REMOTE` is set to `"true"` in remote web environments |
| GitHub Copilot | `env` | Object of key/value pairs on each command object |

---

## Exit Code Conventions

### Claude Code: Three-code system

```text
Exit 0    — Success. Claude Code parses stdout for JSON output.
Exit 2    — Blocking error. stderr is fed back to Claude as an error message.
            Effect varies by event (see table below).
Other     — Non-blocking error. stderr shown in verbose mode only.
            Execution continues.
```

Exit code 2 produces different effects depending on the event:

| Event | Can block? | Effect of exit 2 |
| :--- | :--- | :--- |
| `PreToolUse` | Yes | Blocks the tool call |
| `PermissionRequest` | Yes | Denies the permission |
| `UserPromptSubmit` | Yes | Blocks prompt and erases it |
| `Stop` | Yes | Prevents Claude from stopping |
| `SubagentStop` | Yes | Prevents the subagent from stopping |
| `TeammateIdle` | Yes | Teammate continues working |
| `TaskCompleted` | Yes | Prevents task completion |
| `ConfigChange` | Yes | Blocks the configuration change |
| `PostToolUse` | No | Shows stderr to Claude (tool already ran) |
| `PostToolUseFailure` | No | Shows stderr to Claude |
| `Notification` | No | Shows stderr to user only |
| `SubagentStart` | No | Shows stderr to user only |
| `SessionStart` | No | Shows stderr to user only |
| `SessionEnd` | No | Shows stderr to user only |
| `PreCompact` | No | Shows stderr to user only |
| `WorktreeCreate` | Yes | Any non-zero exit fails worktree creation |
| `WorktreeRemove` | No | Failures logged in debug mode only |

### GitHub Copilot: Binary system

```text
Exit 0      — Success.
Non-zero    — Failure. No documented semantic for specific non-zero codes.
```

GitHub Copilot's documentation does not assign specific meanings to individual non-zero exit codes. Scripts must be executable (`chmod +x`) and declare a shebang.

---

## Context Passing Patterns

### Claude Code: stdin JSON

Claude Code passes event context to hook commands as a JSON object on standard input.

All events receive these common fields:

```json
{
  "session_id": "abc123",
  "transcript_path": "/home/user/.claude/projects/.../transcript.jsonl",
  "cwd": "/home/user/my-project",
  "permission_mode": "default",
  "hook_event_name": "PreToolUse"
}
```

Event-specific fields are added to the same object. Example for `PreToolUse`:

```json
{
  "session_id": "abc123",
  "transcript_path": "/home/user/.claude/projects/.../transcript.jsonl",
  "cwd": "/home/user/my-project",
  "permission_mode": "default",
  "hook_event_name": "PreToolUse",
  "tool_name": "Bash",
  "tool_input": {
    "command": "npm test"
  }
}
```

Read stdin JSON in a shell script:

```bash
#!/bin/bash
INPUT=$(cat)
TOOL=$(echo "$INPUT" | jq -r '.tool_name')
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command')
```

### GitHub Copilot: Env vars and stdin (undocumented)

GitHub Copilot's official documentation shows a debugging pattern where scripts read from stdin via `cat`, suggesting JSON is also passed on stdin. The exact schema is not documented by GitHub as of 2026-03-01.

Example from GitHub Copilot debugging guide:

```bash
#!/bin/bash
set -x
INPUT=$(cat)
echo "DEBUG: Received input" >&2
echo "$INPUT" >&2
```

Test by piping sample JSON:

```bash
echo '{"timestamp":1704614400000,"cwd":"/tmp","toolName":"bash","toolArgs":"{\"command\":\"ls\"}"}' | ./my-hook.sh
```

---

## JSON Output Control

### Claude Code: Structured stdout JSON (exit 0 only)

When a Claude Code command hook exits with code 0, Claude Code reads its stdout as JSON. This provides finer-grained control than exit codes alone.

Universal fields (work across all events):

| Field | Default | Description |
| :--- | :--- | :--- |
| `continue` | `true` | If `false`, Claude stops processing entirely |
| `stopReason` | none | Message shown to user when `continue` is `false` |
| `suppressOutput` | `false` | If `true`, hides stdout from verbose mode |
| `systemMessage` | none | Warning message shown to the user |

Stop Claude entirely regardless of event type:

```json
{
  "continue": false,
  "stopReason": "Build failed, fix errors before continuing"
}
```

Block an action (for events that support top-level `decision`):

```json
{
  "decision": "block",
  "reason": "Test suite must pass before proceeding"
}
```

Use `hookSpecificOutput` for events requiring richer control (`PreToolUse`, `PermissionRequest`, `SessionStart`):

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "Destructive command blocked by hook"
  }
}
```

The `suppressOutput` field hides stdout from the verbose mode display (`Ctrl+O`). Use it when your hook emits diagnostic text that is useful during development but noisy in normal operation.

### GitHub Copilot: No documented JSON output protocol

GitHub Copilot's hook documentation does not describe a JSON stdout protocol analogous to Claude Code's. Output formatting notes focus on ensuring JSON output is on a single line when scripts do emit JSON — not on structured decision fields.

Compact JSON output utilities:

```bash
# Unix
jq -c . <<< "$JSON_OUTPUT"

# Windows PowerShell
$data | ConvertTo-Json -Compress
```

---

## Platform Comparison Table

| Dimension | Claude Code | GitHub Copilot |
| :--- | :--- | :--- |
| Event name casing | PascalCase (`PreToolUse`, `SessionStart`) | camelCase (`preToolUse`, `sessionStart`) |
| Config file location | `settings.json`, `.claude/settings.json`, `hooks/hooks.json` (plugins), or skill/agent frontmatter | `.github/hooks/<name>.json` on default branch |
| Version field | Not required | `"version": 1` required at top level |
| Matcher support | `matcher` field (regex) on each event group | None — all hooks in the event array always run |
| Schema nesting | Event key → array of matcher groups → array of hook objects | Event key → array of command objects |
| Command specification | Single `command` key (shell-agnostic string) | Dual keys: `bash` (Unix/macOS) and `powershell` (Windows) |
| Cross-platform commands | Not applicable (single string runs in current shell) | Provide both `bash` and `powershell` keys |
| Context to hook | stdin JSON — common fields plus event-specific fields | stdin (schema undocumented officially) |
| Exit code semantics | 0 (success), 2 (blocking error), other (non-blocking error) | 0 (success), non-zero (failure) |
| JSON stdout protocol | Documented — `continue`, `suppressOutput`, `decision`, `hookSpecificOutput` | Not documented |
| Timeout field name | `timeout` (seconds) | `timeoutSec` (seconds) |
| Working directory field | Not in hook definition; inherit from Claude Code or use env vars | `cwd` per command object |
| Environment variables | Via `CLAUDE_ENV_FILE` in `SessionStart`; no per-hook `env` field | `env` object per command object |
| Hook types | `command`, `prompt`, `agent` | `command` only |
| Subagent lifecycle events | Yes (`SubagentStart`, `SubagentStop`) | No |
| Matcher-free events | `UserPromptSubmit`, `Stop`, `TeammateIdle`, `TaskCompleted`, `WorktreeCreate`, `WorktreeRemove` | All events (no matcher concept) |
| Scripting languages | Any executable (shell, Python, Node, etc.) | Any executable; dual-key for cross-platform |
