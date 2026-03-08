# OpenCode Plugin System

Reference for building and loading plugins in OpenCode. Plugins are JavaScript/TypeScript modules that hook into events and customize behavior.

SOURCE: <https://opencode.ai/docs/plugins.md> (accessed 2026-03-07)

---

## Loading Plugins

Two mechanisms:

**Local files** — auto-loaded at startup from:

- `.opencode/plugins/` — project-level
- `~/.config/opencode/plugins/` — global

**npm packages** — declare in `opencode.json`:

```json
{
  "$schema": "https://opencode.ai/config.json",
  "plugin": ["opencode-helicone-session", "opencode-wakatime", "@my-org/custom-plugin"]
}
```

npm plugins install automatically using Bun. Cached at `~/.cache/opencode/node_modules/`.

### Load Order

1. Global config (`~/.config/opencode/opencode.json`)
2. Project config (`opencode.json`)
3. Global plugin directory (`~/.config/opencode/plugins/`)
4. Project plugin directory (`.opencode/plugins/`)

---

## Plugin Structure

A plugin is a JS/TS module exporting one or more plugin functions. Each function receives a context object and returns a hooks object.

```js
export const MyPlugin = async ({ project, client, $, directory, worktree }) => {
  return {
    // hook implementations
  }
}
```

**Context object fields:**

- `project` — current project metadata
- `directory` — working directory
- `worktree` — git worktree info
- `client` — OpenCode SDK
- `$` — Bun shell API

**TypeScript type import:**

```ts
import type { Plugin } from "@opencode-ai/plugin"
```

---

## Available Hook Events

| Category | Events |
|----------|--------|
| Command | `command.executed` |
| File | `file.edited`, `file.watcher.updated` |
| Installation | `installation.updated` |
| LSP | `lsp.client.diagnostics`, `lsp.updated` |
| Message | `message.part.removed`, `message.part.updated`, `message.removed`, `message.updated` |
| Permission | `permission.asked`, `permission.replied` |
| Server | `server.connected` |
| Session | `session.created`, `session.compacted`, `session.deleted`, `session.diff`, `session.error`, `session.idle`, `session.status`, `session.updated` |
| Todo | `todo.updated` |
| Shell | `shell.env` |
| Tool | `tool.execute.after`, `tool.execute.before` |
| TUI | `tui.prompt.append`, `tui.command.execute`, `tui.toast.show` |

---

## Custom Tools

Custom tools override built-in tools of the same name.

```ts
import { type Plugin, tool } from "@opencode-ai/plugin"

export const CustomToolsPlugin: Plugin = async (ctx) => {
  return {
    tool: {
      mytool: tool({
        description: "This is a custom tool",
        args: { foo: tool.schema.string() },
        async execute(args, context) {
          return `Hello ${args.foo}`
        },
      }),
    },
  }
}
```

---

## Compaction Hooks

Compaction hooks run when the session context is compacted. Two modes:

```ts
"experimental.session.compacting": async (input, output) => {
  // Append additional context to the compaction prompt
  output.context.push(`## Custom Context\nAdditional state here...`)

  // OR replace the entire compaction prompt
  output.prompt = `Custom compaction prompt...`
}
```

---

## Comparison with Claude Code Plugins

| Feature | Claude Code | OpenCode |
|---------|------------|---------|
| Format | Markdown + YAML frontmatter | JS/TS modules |
| Distribution | `.claude-plugin/plugin.json` | npm packages or local files |
| Hook system | Event-based JSON stdin/stdout | Async function exports |
| Custom tools | MCP servers | Built-in via `tool()` helper |
| Compaction | `PreCompact` hook | `experimental.session.compacting` |
| Shell API | N/A | Bun shell (`$`) |
| Load config | `settings.json` | `opencode.json` |
| Cache location | `~/.claude/plugins/cache/` | `~/.cache/opencode/node_modules/` |

**Key architectural difference:** Claude Code hooks communicate via JSON on stdin/stdout and are process-isolated shell commands. OpenCode hooks are in-process async JavaScript functions with direct access to the SDK and Bun shell — no serialization boundary.

---

## `mcp:` Frontmatter Key

OpenCode uses the `mcp:` key in YAML frontmatter to configure MCP server connections. This key is ecosystem-owned by OpenCode and must be passed through verbatim by any Claude Code tooling that processes frontmatter — do not rewrite, normalize, reorder, or remove it.

Example (from a skill that surfaces data to both Claude Code and OpenCode):

```yaml
---
name: my-skill
description: Does something useful
mcp:
  server: my-mcp-server
  tools: [read_resource, write_resource]
---
```

Claude Code's `plugin_validator.py` treats `mcp:` as a pass-through key via `ecosystem_registry.py`.
