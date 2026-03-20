---
paths:
- '**/.claude-plugin/plugin.json'
- '**/plugin.json'
---

# Plugin.json Requirements

## Required Fields

- `name`: kebab-case, required

## Component Path Fields

| Field | Type | Example |
|-------|------|---------|
| `commands` | string or array | `"./custom/cmd.md"` or `["./cmd1.md"]` |
| `agents` | string or array | `"./custom/agents/"` or `["./agent.md"]` |
| `skills` | string or array | `"./custom/skills/"` |
| `hooks` | string or object | `"./hooks.json"` |
| `mcpServers` | string or object | `"./mcp-config.json"` |
| `outputStyles` | string or array | `"./styles/"` |
| `lspServers` | string or object | `"./.lsp.json"` |

## Path Rules

- All paths must start with `./`
- Custom paths supplement default directories — they do not replace them
- `agents` field must be an array of individual file paths — `["./agents/file.md"]` — not a directory string `"./agents/"`
- Plugins cannot reference files outside their directory (`../shared-utils` fails after installation)

## Validate After Editing

```bash
uvx skilllint@latest check {plugin-path}
claude plugin validate {plugin-directory}
```

## Common Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `agents: Invalid input` | Used `"./agents/"` instead of array | Change to `["./agents/file.md"]` |
| `name: Required` | Missing name field | Add `"name": "plugin-name"` |
| Invalid JSON syntax | Malformed JSON | Validate with `python3 -m json.tool plugin.json` |

**SOURCE:** Lines 75-91 of claude-plugins-reference-2026/SKILL.md; verified via `skilllint`
