# Claude Code Hooks Reference

SOURCE: <https://code.claude.com/docs/en/hooks-reference.md> (accessed 2026-03-01)

## Table of Contents

1. [Event Reference](#event-reference)
2. [Hook Locations](#hook-locations)
3. [Matcher Patterns](#matcher-patterns)
4. [Hook Handler Fields](#hook-handler-fields)
5. [Common Input Schema](#common-input-schema)
6. [Exit Codes](#exit-codes)
7. [JSON Output Schema](#json-output-schema)
8. [Event Input Schemas](#event-input-schemas)
9. [Event Decision Control](#event-decision-control)
10. [Prompt Hooks](#prompt-hooks)
11. [Agent Hooks](#agent-hooks)
12. [Async Hooks](#async-hooks)
13. [Environment Variables](#environment-variables)
14. [Security](#security)
15. [Debug](#debug)

---

## Event Reference

| Event | When it fires | Matcher support |
|:---|:---|:---|
| `Setup` | Repository setup/maintenance (`--init`, `--init-only`, `--maintenance` flags) | `init`, `maintenance` |
| `SessionStart` | Session begins or resumes | `startup`, `resume`, `clear`, `compact` |
| `UserPromptSubmit` | User submits a prompt, before Claude processes it | none |
| `UserPromptExpansion` | User-typed slash command expands into a full prompt | command name |
| `PreToolUse` | Before a tool call executes | tool name |
| `PermissionRequest` | When a permission dialog appears | tool name |
| `PermissionDenied` | When auto mode classifier denies a tool call | tool name |
| `PostToolUse` | After a tool call succeeds | tool name |
| `PostToolUseFailure` | After a tool call fails | tool name |
| `Notification` | When Claude Code sends a notification | `permission_prompt`, `idle_prompt`, `auth_success`, `elicitation_dialog` |
| `InstructionsLoaded` | When CLAUDE.md or `.claude/rules/*.md` is loaded into context | none |
| `SubagentStart` | When a subagent is spawned | agent type |
| `SubagentStop` | When a subagent finishes | agent type |
| `Stop` | When Claude finishes responding | none |
| `TeammateIdle` | When an agent team teammate is about to go idle | none |
| `TaskCompleted` | When a task is being marked as completed | none |
| `ConfigChange` | When a configuration file changes during a session | `user_settings`, `project_settings`, `local_settings`, `policy_settings`, `skills` |
| `Elicitation` | When an MCP server requests user input mid-task | MCP server name |
| `ElicitationResult` | After user responds to MCP elicitation, before response sent to server | MCP server name |
| `WorktreeCreate` | When a worktree is being created | none |
| `WorktreeRemove` | When a worktree is being removed | none |
| `CwdChanged` | When the working directory changes | none |
| `FileChanged` | When a watched file changes on disk | literal filename (e.g. `.envrc\|.env`) |
| `PreCompact` | Before context compaction | `manual`, `auto` |
| `PostCompact` | After context compaction completes | `manual`, `auto` |
| `SessionEnd` | When a session terminates | `clear`, `logout`, `prompt_input_exit`, `bypass_permissions_disabled`, `other` |

SOURCE: [Claude Code Hooks](https://code.claude.com/docs/en/hooks.md) (accessed 2026-04-23)

For subagents, `Stop` hooks are automatically converted to `SubagentStop`.

---

## Hook Locations

| Location | Scope | Shareable |
|:---|:---|:---|
| `~/.claude/settings.json` | All projects | No |
| `.claude/settings.json` | Single project | Yes |
| `.claude/settings.local.json` | Single project | No |
| Managed policy settings | Organization-wide | Yes, admin-controlled |
| Plugin `hooks/hooks.json` | When plugin is enabled | Yes |
| Skill or agent frontmatter | While component is active | Yes |

Plugin hooks are auto-discovered from `hooks/hooks.json`. No `hooks` field required in `plugin.json`.

`allowManagedHooksOnly` blocks user, project, and plugin hooks. Only managed-level hooks remain active.

Claude Code captures a snapshot of hooks at startup. External edits require review in `/hooks` before taking effect.

Disable all hooks (not individual hooks): set `"disableAllHooks": true` in settings or use `/hooks` menu toggle.

---

## Matcher Patterns

The `matcher` field is a regex string. Omit, use `"*"`, or use `""` to match all occurrences.

| Event | Matcher filters |
|:---|:---|
| `PreToolUse`, `PostToolUse`, `PostToolUseFailure`, `PermissionRequest`, `PermissionDenied` | tool name |
| `UserPromptExpansion` | command name |
| `SessionStart` | how session started: `startup`, `resume`, `clear`, `compact` |
| `SessionEnd` | why session ended: `clear`, `logout`, `prompt_input_exit`, `bypass_permissions_disabled`, `other` |
| `Notification` | notification type: `permission_prompt`, `idle_prompt`, `auth_success`, `elicitation_dialog` |
| `SubagentStart`, `SubagentStop` | agent type: `Bash`, `Explore`, `Plan`, or custom agent names |
| `Setup` | `init` or `maintenance` |
| `PreCompact`, `PostCompact` | trigger: `manual`, `auto` |
| `ConfigChange` | source: `user_settings`, `project_settings`, `local_settings`, `policy_settings`, `skills` |
| `Elicitation`, `ElicitationResult` | MCP server name |
| `FileChanged` | literal filename pattern (e.g. `.envrc\|.env`); not regex |
| `UserPromptSubmit`, `Stop`, `TeammateIdle`, `TaskCompleted`, `WorktreeCreate`, `WorktreeRemove`, `CwdChanged`, `InstructionsLoaded` | no matcher support — always fires |

SOURCE: [Claude Code Hooks](https://code.claude.com/docs/en/hooks.md) (accessed 2026-04-23)

MCP tools follow the pattern `mcp__<server>__<tool>`:

- `mcp__memory__create_entities`
- `mcp__filesystem__read_file`
- `mcp__github__search_repositories`
- `mcp__memory__.*` — all tools from the `memory` server
- `mcp__.*__write.*` — any tool containing "write" from any server

---

## Hook Handler Fields

### Common Fields (all hook types)

| Field | Required | Default | Description |
|:---|:---|:---|:---|
| `type` | yes | — | `"command"`, `"prompt"`, or `"agent"` |
| `timeout` | no | 600 (command), 30 (prompt), 60 (agent) | Seconds before canceling |
| `statusMessage` | no | — | Custom spinner message while hook runs |
| `once` | no | `false` | Skills only: run once per session then remove |

### Command Hook Fields

| Field | Required | Description |
|:---|:---|:---|
| `command` | yes | Shell command to execute |
| `async` | no | If `true`, runs in background without blocking |

### Prompt and Agent Hook Fields

| Field | Required | Description |
|:---|:---|:---|
| `prompt` | yes | Prompt text. Use `$ARGUMENTS` as placeholder for hook input JSON |
| `model` | no | Model to use. Defaults to a fast model |

All matching hooks run in parallel. Identical handlers are deduplicated. Handlers run in the current directory with Claude Code's environment.

`$CLAUDE_CODE_REMOTE` is set to `"true"` in remote web environments; not set in local CLI.

---

## Common Input Schema

All hook events receive these fields on stdin as JSON:

| Field | Description |
|:---|:---|
| `session_id` | Current session identifier |
| `transcript_path` | Path to conversation JSON |
| `cwd` | Current working directory when the hook is invoked |
| `permission_mode` | Current permission mode: `"default"`, `"plan"`, `"acceptEdits"`, `"dontAsk"`, or `"bypassPermissions"` |
| `hook_event_name` | Name of the event that fired |

---

## Exit Codes

| Exit code | Meaning |
|:---|:---|
| `0` | Success. Claude Code parses stdout for JSON output |
| `2` | Blocking error. stderr is fed back as error message. JSON in stdout is ignored |
| other | Non-blocking error. stderr shown in verbose mode (`Ctrl+O`). Execution continues |

### Exit Code 2 Behavior Per Event

| Hook event | Can block? | What happens on exit 2 |
|:---|:---|:---|
| `PreToolUse` | Yes | Blocks the tool call |
| `PermissionRequest` | Yes | Denies the permission |
| `UserPromptSubmit` | Yes | Blocks prompt processing and erases the prompt |
| `UserPromptExpansion` | Yes | Blocks the expansion |
| `Stop` | Yes | Prevents Claude from stopping, continues the conversation |
| `SubagentStop` | Yes | Prevents the subagent from stopping |
| `TeammateIdle` | Yes | Prevents the teammate from going idle |
| `TaskCompleted` | Yes | Prevents the task from being marked as completed |
| `ConfigChange` | Yes | Blocks the configuration change (except `policy_settings`) |
| `Elicitation` | Yes | Blocks the elicitation dialog |
| `ElicitationResult` | Yes | Blocks the elicitation response |
| `WorktreeCreate` | Yes | Any non-zero exit code causes worktree creation to fail |
| `PostToolUse` | No | Shows stderr to Claude (tool already ran) |
| `PostToolUseFailure` | No | Shows stderr to Claude (tool already failed) |
| `PermissionDenied` | No | Shows stderr to user only |
| `Notification` | No | Shows stderr to user only |
| `SubagentStart` | No | Shows stderr to user only |
| `SessionStart` | No | Shows stderr to user only |
| `Setup` | No | Shows stderr to user only |
| `SessionEnd` | No | Shows stderr to user only |
| `CwdChanged` | No | Failures logged to debug only |
| `FileChanged` | No | Failures logged to debug only |
| `InstructionsLoaded` | No | Failures logged to debug only |
| `PreCompact` | No | Shows stderr to user only |
| `PostCompact` | No | Logged to debug only |
| `WorktreeRemove` | No | Failures are logged in debug mode only |
| `StopFailure` | No | Output and exit code are ignored (logging and alerts only) |

SOURCE: [Claude Code Hooks](https://code.claude.com/docs/en/hooks.md) (accessed 2026-04-23)

---

## JSON Output Schema

Exit 0 and print JSON to stdout for structured control. Choose one approach: exit codes alone, or exit 0 + JSON. JSON is only processed on exit 0.

### Universal JSON Output Fields

| Field | Default | Description |
|:---|:---|:---|
| `continue` | `true` | If `false`, Claude stops processing entirely. Takes precedence over event-specific decision fields |
| `stopReason` | none | Message shown to user when `continue` is `false`. Not shown to Claude |
| `suppressOutput` | `false` | If `true`, hides stdout from verbose mode output |
| `systemMessage` | none | Warning message shown to the user |

Stop Claude entirely regardless of event:

```json
{ "continue": false, "stopReason": "Build failed, fix errors before continuing" }
```

### Decision Control by Event

| Events | Decision pattern | Key fields |
|:---|:---|:---|
| `UserPromptSubmit`, `PostToolUse`, `PostToolUseFailure`, `Stop`, `SubagentStop`, `ConfigChange` | Top-level `decision` | `decision: "block"`, `reason` |
| `TeammateIdle`, `TaskCompleted` | Exit code only | Exit 2 blocks, stderr fed back as feedback |
| `PreToolUse` | `hookSpecificOutput` | `permissionDecision` (allow/deny/ask), `permissionDecisionReason` |
| `PermissionRequest` | `hookSpecificOutput` | `decision.behavior` (allow/deny) |
| `WorktreeCreate` | stdout path | Hook prints absolute path to created worktree. Non-zero exit fails creation |
| `WorktreeRemove`, `Notification`, `SessionEnd`, `PreCompact` | None | No decision control |

Top-level decision (used by `UserPromptSubmit`, `PostToolUse`, `PostToolUseFailure`, `Stop`, `SubagentStop`, `ConfigChange`):

```json
{
  "decision": "block",
  "reason": "Test suite must pass before proceeding"
}
```

---

## Event Input Schemas

### SessionStart

Additional fields beyond common input:

| Field | Description |
|:---|:---|
| `source` | `"startup"`, `"resume"`, `"clear"`, or `"compact"` |
| `model` | Model identifier |
| `agent_type` | Agent name if started with `claude --agent <name>` (optional) |

```json
{
  "session_id": "abc123",
  "transcript_path": "/Users/.../.claude/projects/.../00893aaf-19fa-41d2-8238-13269b9b3ca0.jsonl",
  "cwd": "/Users/...",
  "permission_mode": "default",
  "hook_event_name": "SessionStart",
  "source": "startup",
  "model": "claude-sonnet-4-6"
}
```

### UserPromptSubmit

Additional fields:

| Field | Description |
|:---|:---|
| `prompt` | Text the user submitted |

```json
{
  "session_id": "abc123",
  "transcript_path": "/Users/.../.claude/projects/.../00893aaf-19fa-41d2-8238-13269b9b3ca0.jsonl",
  "cwd": "/Users/...",
  "permission_mode": "default",
  "hook_event_name": "UserPromptSubmit",
  "prompt": "Write a function to calculate the factorial of a number"
}
```

### PreToolUse

Additional fields:

| Field | Description |
|:---|:---|
| `tool_name` | Name of the tool being called |
| `tool_input` | Arguments passed to the tool (schema depends on tool) |
| `tool_use_id` | Unique identifier for this tool use |

Tool-specific `tool_input` schemas:

#### Bash

| Field | Type | Example | Description |
|:---|:---|:---|:---|
| `command` | string | `"npm test"` | Shell command to execute |
| `description` | string | `"Run test suite"` | Optional description |
| `timeout` | number | `120000` | Optional timeout in milliseconds |
| `run_in_background` | boolean | `false` | Whether to run in background |

#### Write

| Field | Type | Example | Description |
|:---|:---|:---|:---|
| `file_path` | string | `"/path/to/file.txt"` | Absolute path to the file to write |
| `content` | string | `"file content"` | Content to write |

#### Edit

| Field | Type | Example | Description |
|:---|:---|:---|:---|
| `file_path` | string | `"/path/to/file.txt"` | Absolute path to the file to edit |
| `old_string` | string | `"original text"` | Text to find and replace |
| `new_string` | string | `"replacement text"` | Replacement text |
| `replace_all` | boolean | `false` | Whether to replace all occurrences |

#### Read

| Field | Type | Example | Description |
|:---|:---|:---|:---|
| `file_path` | string | `"/path/to/file.txt"` | Absolute path to the file to read |
| `offset` | number | `10` | Optional line number to start reading from |
| `limit` | number | `50` | Optional number of lines to read |

#### Glob

| Field | Type | Example | Description |
|:---|:---|:---|:---|
| `pattern` | string | `"**/*.ts"` | Glob pattern to match files against |
| `path` | string | `"/path/to/dir"` | Optional directory to search in |

#### Grep

| Field | Type | Example | Description |
|:---|:---|:---|:---|
| `pattern` | string | `"TODO.*fix"` | Regular expression pattern |
| `path` | string | `"/path/to/dir"` | Optional file or directory to search in |
| `glob` | string | `"*.ts"` | Optional glob pattern to filter files |
| `output_mode` | string | `"content"` | `"content"`, `"files_with_matches"`, or `"count"` |
| `-i` | boolean | `true` | Case insensitive search |
| `multiline` | boolean | `false` | Enable multiline matching |

#### WebFetch

| Field | Type | Example | Description |
|:---|:---|:---|:---|
| `url` | string | `"https://example.com/api"` | URL to fetch content from |
| `prompt` | string | `"Extract the API endpoints"` | Prompt to run on the fetched content |

#### WebSearch

| Field | Type | Example | Description |
|:---|:---|:---|:---|
| `query` | string | `"react hooks best practices"` | Search query |
| `allowed_domains` | array | `["docs.example.com"]` | Optional: only include results from these domains |
| `blocked_domains` | array | `["spam.example.com"]` | Optional: exclude results from these domains |

#### Task

| Field | Type | Example | Description |
|:---|:---|:---|:---|
| `prompt` | string | `"Find all API endpoints"` | The task for the agent to perform |
| `description` | string | `"Find API endpoints"` | Short description |
| `subagent_type` | string | `"Explore"` | Type of specialized agent to use |
| `model` | string | `"sonnet"` | Optional model alias |

### PermissionRequest

Additional fields:

| Field | Description |
|:---|:---|
| `tool_name` | Name of the tool requiring permission |
| `tool_input` | Arguments passed to the tool |
| `permission_suggestions` | Optional array of "always allow" options the user would normally see |

```json
{
  "session_id": "abc123",
  "transcript_path": "/Users/.../.claude/projects/.../00893aaf-19fa-41d2-8238-13269b9b3ca0.jsonl",
  "cwd": "/Users/...",
  "permission_mode": "default",
  "hook_event_name": "PermissionRequest",
  "tool_name": "Bash",
  "tool_input": {
    "command": "rm -rf node_modules",
    "description": "Remove node_modules directory"
  },
  "permission_suggestions": [
    { "type": "toolAlwaysAllow", "tool": "Bash" }
  ]
}
```

No `tool_use_id` field (unlike PreToolUse).

### PostToolUse

Additional fields:

| Field | Description |
|:---|:---|
| `tool_name` | Name of the tool that executed |
| `tool_input` | Arguments sent to the tool |
| `tool_response` | Result returned by the tool |
| `tool_use_id` | Unique identifier for this tool use |

```json
{
  "session_id": "abc123",
  "transcript_path": "/Users/.../.claude/projects/.../00893aaf-19fa-41d2-8238-13269b9b3ca0.jsonl",
  "cwd": "/Users/...",
  "permission_mode": "default",
  "hook_event_name": "PostToolUse",
  "tool_name": "Write",
  "tool_input": {
    "file_path": "/path/to/file.txt",
    "content": "file content"
  },
  "tool_response": {
    "filePath": "/path/to/file.txt",
    "success": true
  },
  "tool_use_id": "toolu_01ABC123..."
}
```

### PostToolUseFailure

Additional fields:

| Field | Description |
|:---|:---|
| `tool_name` | Name of the tool that failed |
| `tool_input` | Arguments sent to the tool |
| `tool_use_id` | Unique identifier for this tool use |
| `error` | String describing what went wrong |
| `is_interrupt` | Optional boolean: whether failure was caused by user interruption |

```json
{
  "session_id": "abc123",
  "transcript_path": "/Users/.../.claude/projects/.../00893aaf-19fa-41d2-8238-13269b9b3ca0.jsonl",
  "cwd": "/Users/...",
  "permission_mode": "default",
  "hook_event_name": "PostToolUseFailure",
  "tool_name": "Bash",
  "tool_input": {
    "command": "npm test",
    "description": "Run test suite"
  },
  "tool_use_id": "toolu_01ABC123...",
  "error": "Command exited with non-zero status code 1",
  "is_interrupt": false
}
```

### Notification

Additional fields:

| Field | Description |
|:---|:---|
| `message` | Notification text |
| `title` | Optional title |
| `notification_type` | Type: `permission_prompt`, `idle_prompt`, `auth_success`, `elicitation_dialog` |

```json
{
  "session_id": "abc123",
  "transcript_path": "/Users/.../.claude/projects/.../00893aaf-19fa-41d2-8238-13269b9b3ca0.jsonl",
  "cwd": "/Users/...",
  "permission_mode": "default",
  "hook_event_name": "Notification",
  "message": "Claude needs your permission to use Bash",
  "title": "Permission needed",
  "notification_type": "permission_prompt"
}
```

### SubagentStart

Additional fields:

| Field | Description |
|:---|:---|
| `agent_id` | Unique identifier for the subagent |
| `agent_type` | Agent name: `"Bash"`, `"Explore"`, `"Plan"`, or custom agent names |

```json
{
  "session_id": "abc123",
  "transcript_path": "/Users/.../.claude/projects/.../00893aaf-19fa-41d2-8238-13269b9b3ca0.jsonl",
  "cwd": "/Users/...",
  "permission_mode": "default",
  "hook_event_name": "SubagentStart",
  "agent_id": "agent-abc123",
  "agent_type": "Explore"
}
```

### SubagentStop

Additional fields:

| Field | Description |
|:---|:---|
| `stop_hook_active` | `true` when Claude Code is already continuing as a result of a stop hook |
| `agent_id` | Unique identifier for the subagent |
| `agent_type` | Agent name (used for matcher filtering) |
| `agent_transcript_path` | Path to the subagent's transcript in `subagents/` folder |
| `last_assistant_message` | Text content of the subagent's final response |

```json
{
  "session_id": "abc123",
  "transcript_path": "~/.claude/projects/.../abc123.jsonl",
  "cwd": "/Users/...",
  "permission_mode": "default",
  "hook_event_name": "SubagentStop",
  "stop_hook_active": false,
  "agent_id": "def456",
  "agent_type": "Explore",
  "agent_transcript_path": "~/.claude/projects/.../abc123/subagents/agent-def456.jsonl",
  "last_assistant_message": "Analysis complete. Found 3 potential issues..."
}
```

### Stop

Additional fields:

| Field | Description |
|:---|:---|
| `stop_hook_active` | `true` when Claude Code is already continuing as a result of a stop hook |
| `last_assistant_message` | Text content of Claude's final response |

```json
{
  "session_id": "abc123",
  "transcript_path": "~/.claude/projects/.../00893aaf-19fa-41d2-8238-13269b9b3ca0.jsonl",
  "cwd": "/Users/...",
  "permission_mode": "default",
  "hook_event_name": "Stop",
  "stop_hook_active": true,
  "last_assistant_message": "I've completed the refactoring. Here's a summary..."
}
```

### TeammateIdle

Additional fields:

| Field | Description |
|:---|:---|
| `teammate_name` | Name of the teammate about to go idle |
| `team_name` | Name of the team |

```json
{
  "session_id": "abc123",
  "transcript_path": "/Users/.../.claude/projects/.../00893aaf-19fa-41d2-8238-13269b9b3ca0.jsonl",
  "cwd": "/Users/...",
  "permission_mode": "default",
  "hook_event_name": "TeammateIdle",
  "teammate_name": "researcher",
  "team_name": "my-project"
}
```

### TaskCompleted

Additional fields:

| Field | Description |
|:---|:---|
| `task_id` | Identifier of the task being completed |
| `task_subject` | Title of the task |
| `task_description` | Detailed description. May be absent |
| `teammate_name` | Name of the teammate completing the task. May be absent |
| `team_name` | Name of the team. May be absent |

```json
{
  "session_id": "abc123",
  "transcript_path": "/Users/.../.claude/projects/.../00893aaf-19fa-41d2-8238-13269b9b3ca0.jsonl",
  "cwd": "/Users/...",
  "permission_mode": "default",
  "hook_event_name": "TaskCompleted",
  "task_id": "task-001",
  "task_subject": "Implement user authentication",
  "task_description": "Add login and signup endpoints",
  "teammate_name": "implementer",
  "team_name": "my-project"
}
```

### ConfigChange

Additional fields:

| Field | Description |
|:---|:---|
| `source` | Configuration type: `user_settings`, `project_settings`, `local_settings`, `policy_settings`, `skills` |
| `file_path` | Path to the specific file that was modified (optional) |

```json
{
  "session_id": "abc123",
  "transcript_path": "/Users/.../.claude/projects/.../00893aaf-19fa-41d2-8238-13269b9b3ca0.jsonl",
  "cwd": "/Users/...",
  "permission_mode": "default",
  "hook_event_name": "ConfigChange",
  "source": "project_settings",
  "file_path": "/Users/.../my-project/.claude/settings.json"
}
```

`policy_settings` changes cannot be blocked — hooks still fire but blocking decisions are ignored.

### WorktreeCreate

Additional fields:

| Field | Description |
|:---|:---|
| `name` | Slug identifier for the new worktree (user-specified or auto-generated, e.g., `bold-oak-a3f2`) |

```json
{
  "session_id": "abc123",
  "transcript_path": "/Users/.../.claude/projects/.../00893aaf-19fa-41d2-8238-13269b9b3ca0.jsonl",
  "cwd": "/Users/...",
  "hook_event_name": "WorktreeCreate",
  "name": "feature-auth"
}
```

The hook must print the absolute path to the created worktree directory on stdout. Claude Code uses this path as the working directory. Non-zero exit causes worktree creation to fail. Only `type: "command"` hooks are supported.

### WorktreeRemove

Additional fields:

| Field | Description |
|:---|:---|
| `worktree_path` | Absolute path to the worktree being removed |

```json
{
  "session_id": "abc123",
  "transcript_path": "/Users/.../.claude/projects/.../00893aaf-19fa-41d2-8238-13269b9b3ca0.jsonl",
  "cwd": "/Users/...",
  "hook_event_name": "WorktreeRemove",
  "worktree_path": "/Users/.../my-project/.claude/worktrees/feature-auth"
}
```

No decision control. Failures are logged in debug mode only. Only `type: "command"` hooks are supported.

### PreCompact

Additional fields:

| Field | Description |
|:---|:---|
| `trigger` | `"manual"` or `"auto"` |
| `custom_instructions` | Content passed to `/compact` for `manual`. Empty for `auto` |

```json
{
  "session_id": "abc123",
  "transcript_path": "/Users/.../.claude/projects/.../00893aaf-19fa-41d2-8238-13269b9b3ca0.jsonl",
  "cwd": "/Users/...",
  "permission_mode": "default",
  "hook_event_name": "PreCompact",
  "trigger": "manual",
  "custom_instructions": ""
}
```

### SessionEnd

Additional fields:

| Field | Description |
|:---|:---|
| `reason` | `"clear"`, `"logout"`, `"prompt_input_exit"`, `"bypass_permissions_disabled"`, or `"other"` |

```json
{
  "session_id": "abc123",
  "transcript_path": "/Users/.../.claude/projects/.../00893aaf-19fa-41d2-8238-13269b9b3ca0.jsonl",
  "cwd": "/Users/...",
  "permission_mode": "default",
  "hook_event_name": "SessionEnd",
  "reason": "other"
}
```

No decision control. Cannot block session termination.

### Setup

Additional fields:

| Field | Description |
|:---|:---|
| `trigger` | `"init"` (from `--init` or `--init-only`) or `"maintenance"` (from `--maintenance`) |

```json
{
  "session_id": "abc123",
  "transcript_path": "/Users/.../.claude/projects/.../00893aaf-19fa-41d2-8238-13269b9b3ca0.jsonl",
  "cwd": "/Users/...",
  "permission_mode": "default",
  "hook_event_name": "Setup",
  "trigger": "init"
}
```

Has access to `CLAUDE_ENV_FILE` for persisting environment variables. Output added to Claude's context. Exit code 2 shows stderr to user only (non-blocking).

### UserPromptExpansion

Additional fields:

| Field | Description |
|:---|:---|
| `expansion_type` | How the expansion was triggered |
| `command_name` | The slash command that was expanded |
| `command_args` | Arguments passed to the command |
| `command_source` | Source of the command definition |
| `prompt` | The original prompt before expansion |

```json
{
  "session_id": "abc123",
  "transcript_path": "/Users/.../.claude/projects/.../00893aaf-19fa-41d2-8238-13269b9b3ca0.jsonl",
  "cwd": "/Users/...",
  "permission_mode": "default",
  "hook_event_name": "UserPromptExpansion",
  "expansion_type": "skill",
  "command_name": "my-skill",
  "command_args": "",
  "command_source": "plugin",
  "prompt": "/my-skill"
}
```

Can block expansion (exit 2) or inject context. Fires before the expanded prompt reaches Claude.

### CwdChanged

Additional fields:

| Field | Description |
|:---|:---|
| `old_cwd` | The previous working directory |
| `new_cwd` | The new working directory |

```json
{
  "session_id": "abc123",
  "transcript_path": "/Users/.../.claude/projects/.../00893aaf-19fa-41d2-8238-13269b9b3ca0.jsonl",
  "cwd": "/Users/.../new-dir",
  "permission_mode": "default",
  "hook_event_name": "CwdChanged",
  "old_cwd": "/Users/.../old-dir",
  "new_cwd": "/Users/.../new-dir"
}
```

Has access to `CLAUDE_ENV_FILE`. Non-blocking — failures logged to debug only. Can return `watchPaths` in JSON output to update the list of files watched by `FileChanged` hooks.

### FileChanged

Additional fields:

| Field | Description |
|:---|:---|
| `file_path` | Absolute path to the file that changed |
| `event` | `"change"`, `"add"`, or `"unlink"` |

```json
{
  "session_id": "abc123",
  "transcript_path": "/Users/.../.claude/projects/.../00893aaf-19fa-41d2-8238-13269b9b3ca0.jsonl",
  "cwd": "/Users/...",
  "permission_mode": "default",
  "hook_event_name": "FileChanged",
  "file_path": "/Users/.../.envrc",
  "event": "change"
}
```

Has access to `CLAUDE_ENV_FILE`. Non-blocking — failures logged to debug only. Matcher uses literal filenames (not regex): e.g. `.envrc|.env`. Can return `watchPaths` in JSON output to update the watch list.

### PermissionDenied

Additional fields:

| Field | Description |
|:---|:---|
| `tool_name` | Name of the tool that was denied |
| `tool_input` | Arguments that were passed to the tool |

```json
{
  "session_id": "abc123",
  "transcript_path": "/Users/.../.claude/projects/.../00893aaf-19fa-41d2-8238-13269b9b3ca0.jsonl",
  "cwd": "/Users/...",
  "permission_mode": "default",
  "hook_event_name": "PermissionDenied",
  "tool_name": "Bash",
  "tool_input": {
    "command": "rm -rf /"
  }
}
```

Fires only when the auto mode classifier denies a tool call — not on manual denials or rule denials. Non-blocking. Can return `{ "retry": true }` in `hookSpecificOutput` to tell Claude it may retry the denied tool call.

### InstructionsLoaded

Additional fields:

| Field | Description |
|:---|:---|
| `file_path` | Path to the CLAUDE.md or rules file that was loaded |
| `memory_type` | Memory type identifier |
| `load_reason` | `"session_start"`, `"nested_traversal"`, `"path_glob_match"`, `"include"`, or `"compact"` |
| `globs` | Optional glob patterns that triggered the load |

```json
{
  "session_id": "abc123",
  "transcript_path": "/Users/.../.claude/projects/.../00893aaf-19fa-41d2-8238-13269b9b3ca0.jsonl",
  "cwd": "/Users/...",
  "permission_mode": "default",
  "hook_event_name": "InstructionsLoaded",
  "file_path": "/Users/.../.claude/CLAUDE.md",
  "memory_type": "project",
  "load_reason": "session_start"
}
```

Non-blocking — used for observability only (audit logging, compliance tracking). Failures logged to debug only.

### Elicitation

Additional fields:

| Field | Description |
|:---|:---|
| `server_name` | Name of the MCP server requesting input |
| `message` | The elicitation message shown to the user |
| `request_id` | Unique identifier for the elicitation request |

Can return a programmatic response via `hookSpecificOutput` with `action` (`"accept"`, `"decline"`, or `"cancel"`) and `content` (form field values) to respond without showing the dialog.

### ElicitationResult

Additional fields:

| Field | Description |
|:---|:---|
| `server_name` | Name of the MCP server that requested input |
| `action` | User's action: `"accept"`, `"decline"`, or `"cancel"` |
| `content` | Form field values from the user's response |

Fires after user responds, before the response is sent to the MCP server. Can observe, modify, or block the response.

SOURCE: [Claude Code Hooks](https://code.claude.com/docs/en/hooks.md) (accessed 2026-04-23)

---

## Event Decision Control

### PreToolUse Decision Control

Returns decision inside `hookSpecificOutput`. Deprecated: top-level `decision`/`reason` fields. Deprecated values `"approve"` and `"block"` map to `"allow"` and `"deny"`.

| Field | Description |
|:---|:---|
| `permissionDecision` | `"allow"` bypasses permission system, `"deny"` prevents tool call, `"ask"` prompts user to confirm, `"defer"` pauses and exits (non-interactive mode only) |
| `permissionDecisionReason` | For `"allow"` and `"ask"`: shown to user but not Claude. For `"deny"`: shown to Claude |
| `updatedInput` | Modifies tool input parameters before execution |
| `additionalContext` | String added to Claude's context before the tool executes |

`"defer"` is only valid in non-interactive mode (`-p` flag) and only when Claude makes a single tool call (not a batch). Deferring pauses tool execution and exits the process with `stop_reason: "tool_deferred"`. The calling process receives the deferred tool use, handles it externally, then resumes the session to retry. Use to integrate Claude Code into Agent SDK apps that need a custom UI for tool approval.

SOURCE: [Claude Code Hooks](https://code.claude.com/docs/en/hooks.md) (accessed 2026-04-23)

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "allow",
    "permissionDecisionReason": "My reason here",
    "updatedInput": {
      "field_to_modify": "new value"
    },
    "additionalContext": "Current environment: production. Proceed with caution."
  }
}
```

### PermissionRequest Decision Control

| Field | Description |
|:---|:---|
| `behavior` | `"allow"` grants permission, `"deny"` denies it |
| `updatedInput` | For `"allow"` only: modifies tool input parameters before execution |
| `updatedPermissions` | For `"allow"` only: applies permission rule updates (equivalent to user selecting "always allow") |
| `message` | For `"deny"` only: tells Claude why permission was denied |
| `interrupt` | For `"deny"` only: if `true`, stops Claude |

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PermissionRequest",
    "decision": {
      "behavior": "allow",
      "updatedInput": {
        "command": "npm run lint"
      }
    }
  }
}
```

### PostToolUse Decision Control

| Field | Description |
|:---|:---|
| `decision` | `"block"` prompts Claude with the `reason`. Omit to allow |
| `reason` | Shown to Claude when `decision` is `"block"` |
| `additionalContext` | Additional context for Claude |
| `updatedMCPToolOutput` | For MCP tools only: replaces tool output with provided value |

```json
{
  "decision": "block",
  "reason": "Explanation for decision",
  "hookSpecificOutput": {
    "hookEventName": "PostToolUse",
    "additionalContext": "Additional information for Claude"
  }
}
```

### PostToolUseFailure Decision Control

| Field | Description |
|:---|:---|
| `additionalContext` | Additional context for Claude alongside the error |

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PostToolUseFailure",
    "additionalContext": "Additional information about the failure for Claude"
  }
}
```

### UserPromptSubmit Decision Control

Two ways to add context on exit code 0:
- Plain text stdout: added as hook output in transcript
- JSON `additionalContext`: added more discretely

| Field | Description |
|:---|:---|
| `decision` | `"block"` prevents prompt processing and erases it from context |
| `reason` | Shown to user when `decision` is `"block"`. Not added to context |
| `additionalContext` | String added to Claude's context |

```json
{
  "decision": "block",
  "reason": "Explanation for decision",
  "hookSpecificOutput": {
    "hookEventName": "UserPromptSubmit",
    "additionalContext": "My additional context here"
  }
}
```

### SessionStart Decision Control

| Field | Description |
|:---|:---|
| `additionalContext` | String added to Claude's context. Multiple hooks' values are concatenated |

```json
{
  "hookSpecificOutput": {
    "hookEventName": "SessionStart",
    "additionalContext": "My additional context here"
  }
}
```

### Stop / SubagentStop Decision Control

| Field | Description |
|:---|:---|
| `decision` | `"block"` prevents Claude from stopping |
| `reason` | Required when `decision` is `"block"`. Tells Claude why it should continue |

```json
{
  "decision": "block",
  "reason": "Must be provided when Claude is blocked from stopping"
}
```

### Notification Decision Control

| Field | Description |
|:---|:---|
| `additionalContext` | String added to Claude's context |

Cannot block or modify notifications.

### SubagentStart Decision Control

Cannot block subagent creation.

| Field | Description |
|:---|:---|
| `additionalContext` | String added to the subagent's context |

```json
{
  "hookSpecificOutput": {
    "hookEventName": "SubagentStart",
    "additionalContext": "Follow security guidelines for this task"
  }
}
```

### ConfigChange Decision Control

| Field | Description |
|:---|:---|
| `decision` | `"block"` prevents configuration change from being applied |
| `reason` | Explanation shown to user when `decision` is `"block"` |

```json
{
  "decision": "block",
  "reason": "Configuration changes to project settings require admin approval"
}
```

### TeammateIdle and TaskCompleted Decision Control

Exit code 2 only — no JSON decision control. stderr is fed back to the model as feedback.

---

## Prompt Hooks

Events supporting `type: "prompt"` and `type: "agent"`:

- `PermissionRequest`
- `PostToolUse`
- `PostToolUseFailure`
- `PreToolUse`
- `Stop`
- `SubagentStop`
- `TaskCompleted`
- `UserPromptSubmit`

Events supporting only `type: "command"`:

- `ConfigChange`
- `Notification`
- `PreCompact`
- `SessionEnd`
- `SessionStart`
- `SubagentStart`
- `TeammateIdle`
- `WorktreeCreate`
- `WorktreeRemove`

### Prompt Hook Configuration

| Field | Required | Default | Description |
|:---|:---|:---|:---|
| `type` | yes | — | Must be `"prompt"` |
| `prompt` | yes | — | Prompt text. Use `$ARGUMENTS` as placeholder for hook input JSON. If `$ARGUMENTS` absent, input JSON is appended |
| `model` | no | fast model | Model to use for evaluation |
| `timeout` | no | 30 | Timeout in seconds |

```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "prompt",
            "prompt": "You are evaluating whether Claude should stop working. Context: $ARGUMENTS\n\nAnalyze the conversation and determine if:\n1. All user-requested tasks are complete\n2. Any errors need to be addressed\n3. Follow-up work is needed\n\nRespond with JSON: {\"ok\": true} to allow stopping, or {\"ok\": false, \"reason\": \"your explanation\"} to continue working.",
            "timeout": 30
          }
        ]
      }
    ]
  }
}
```

### Prompt Hook Response Schema

```json
{
  "ok": true,
  "reason": "Explanation for the decision"
}
```

| Field | Description |
|:---|:---|
| `ok` | `true` allows the action, `false` prevents it |
| `reason` | Required when `ok` is `false`. Explanation shown to Claude |

---

## Agent Hooks

Agent hooks (`type: "agent"`) spawn a subagent with tool access (Read, Grep, Glob). The subagent runs up to 50 turns, then returns a structured decision. Same response schema as prompt hooks.

### Agent Hook Configuration

| Field | Required | Default | Description |
|:---|:---|:---|:---|
| `type` | yes | — | Must be `"agent"` |
| `prompt` | yes | — | Prompt describing what to verify. Use `$ARGUMENTS` as placeholder |
| `model` | no | fast model | Model to use |
| `timeout` | no | 60 | Timeout in seconds |

```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "agent",
            "prompt": "Verify that all unit tests pass. Run the test suite and check the results. $ARGUMENTS",
            "timeout": 120
          }
        ]
      }
    ]
  }
}
```

---

## Async Hooks

Set `"async": true` on a `type: "command"` hook to run it in the background. Claude continues immediately. Only `type: "command"` hooks support `async`.

Set `"asyncRewake": true` instead of `"async": true` to run in the background and wake Claude when the process exits with code 2. On exit 2, stderr and stdout are delivered to Claude as a system reminder immediately, interrupting the idle state.

Async hooks cannot block or control behavior — `decision`, `permissionDecision`, `continue` fields have no effect.

After the background process exits, if stdout contains `systemMessage` or `additionalContext`, that content is delivered to Claude on the next conversation turn.

SOURCE: [Claude Code Hooks](https://code.claude.com/docs/en/hooks.md) (accessed 2026-04-23)

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write",
        "hooks": [
          {
            "type": "command",
            "command": "/path/to/run-tests.sh",
            "async": true,
            "timeout": 120
          }
        ]
      }
    ]
  }
}
```

### Async Hook Limitations

- Only `type: "command"` hooks support `async`. Prompt-based hooks cannot run asynchronously.
- Cannot block tool calls or return decisions.
- Output is delivered on the next conversation turn. If session is idle, response waits until next user interaction.
- Each execution creates a separate background process. No deduplication across multiple firings.

---

## Environment Variables

| Variable | Available in | Description |
|:---|:---|:---|
| `CLAUDE_PROJECT_DIR` | All hooks | Project root directory. Wrap in quotes for paths with spaces |
| `CLAUDE_PLUGIN_ROOT` | Plugin hooks | Plugin root directory for bundled scripts |
| `CLAUDE_ENV_FILE` | SessionStart, Setup, CwdChanged, FileChanged | File path for persisting environment variables to subsequent Bash commands |
| `CLAUDE_CODE_REMOTE` | All hooks | Set to `"true"` in remote web environments; not set in local CLI |

SOURCE: [Claude Code Hooks](https://code.claude.com/docs/en/hooks.md) (accessed 2026-04-23)

### Persist Environment Variables (SessionStart only)

Write `export` statements to `CLAUDE_ENV_FILE`. Use append (`>>`) to preserve variables set by other hooks:

```bash
#!/bin/bash

if [ -n "$CLAUDE_ENV_FILE" ]; then
  echo 'export NODE_ENV=production' >> "$CLAUDE_ENV_FILE"
  echo 'export DEBUG_LOG=true' >> "$CLAUDE_ENV_FILE"
  echo 'export PATH="$PATH:./node_modules/.bin"' >> "$CLAUDE_ENV_FILE"
fi

exit 0
```

---

## Configuration Structure

Three levels of nesting:

1. Hook event key (e.g., `PreToolUse`, `Stop`)
2. Matcher group array — each element has `matcher` and `hooks`
3. Hook handler array — each element has `type` and type-specific fields

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": ".claude/hooks/block-rm.sh"
          }
        ]
      }
    ]
  }
}
```

### Skill/Agent Frontmatter Format

```yaml
---
name: secure-operations
description: Perform operations with security checks
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "./scripts/security-check.sh"
---
```

### Plugin hooks.json Format

```json
{
  "description": "Automatic code formatting",
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/scripts/format.sh",
            "timeout": 30
          }
        ]
      }
    ]
  }
}
```

---

## Security

Hooks run with the system user's full permissions.

- Validate and sanitize inputs — never trust input data blindly
- Always quote shell variables: `"$VAR"` not `$VAR`
- Block path traversal: check for `..` in file paths
- Use absolute paths; use `"$CLAUDE_PROJECT_DIR"` for project root
- Skip sensitive files: `.env`, `.git/`, keys

---

## Debug

```bash
claude --debug
```

Toggle verbose mode: `Ctrl+O`

```text
[DEBUG] Executing hooks for PostToolUse:Write
[DEBUG] Getting matching hook commands for PostToolUse with query: Write
[DEBUG] Found 1 hook matchers in settings
[DEBUG] Matched 1 hooks for query "Write"
[DEBUG] Found 1 hook commands to execute
[DEBUG] Executing hook command: <Your command> with timeout 600000ms
[DEBUG] Hook command completed with status 0: <Your stdout>
```
