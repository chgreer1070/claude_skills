---
paths:
  - "**/SKILL.md"
  - "**/agents/**/*.md"
  - "**/commands/**/*.md"
---

# Frontmatter Requirements

## Skills

- `name`: Required — lowercase, hyphens, must match directory name, satisfies `^[a-z][a-z0-9-]*$`
- `description`: Optional (uses first paragraph if omitted)
- `tools`: Must be comma-separated string — `Read, Grep, Glob` — not a YAML array

## Agents

- `name`: Required — lowercase, hyphens, max 64 chars
- `description`: Required — include trigger keywords, max 1024 chars, no colons except in URLs
- `model`: Must be `sonnet`, `opus`, `haiku`, or `inherit` if specified
- `tools`: Must be comma-separated string (not YAML array)
- No YAML multiline indicators (`>-`, `|-`, `>`, `|`) in any field

## Commands

- `description`: Required
- `allowed-tools`: Must be comma-separated string (not YAML array)

## Validator Auto-Fix

Run after writing or editing any frontmatter file:

```bash
uvx skilllint@latest --fix {path}
```

The validator auto-adds `name:` derived from the directory name when absent (plugin skills only).

**SOURCE:** `skilllint` and [agentskills.io specification](https://agentskills.io/specification)

## Multi-Ecosystem Frontmatter Preservation

Skills and agents can target multiple tool ecosystems simultaneously. A SKILL.md that contains
`mcp:` at the top level of its frontmatter targets OpenCode in addition to Claude Code.

### Rule: Unknown Fields Are Not Errors

Do NOT strip, flag, or rewrite frontmatter fields that are unrecognized by the Claude Code
schema if those fields belong to a known ecosystem. Unknown fields are preservation targets,
not validation failures.

The authoritative list of known ecosystem fields is maintained in:

```text
plugins/plugin-creator/scripts/ecosystem_registry.py
```

Consult that file before treating any unfamiliar frontmatter key as an error.

### OpenCode — `mcp:` Field

The `mcp:` field is an OpenCode ecosystem field. Its presence signals that the file targets
OpenCode in addition to Claude Code.

Detection: if `mcp:` appears as a top-level key in a SKILL.md or agent frontmatter block,
the file is a multi-ecosystem target. Do not remove or restructure it.

Preservation rule — treat `mcp:` and its entire nested content as opaque:

- Read it to detect multi-ecosystem intent
- Copy it exactly when rewriting frontmatter
- Never rewrite, rename, or reorder sub-keys
- Never validate sub-key values against Claude Code schemas

```yaml
# Example: valid multi-ecosystem SKILL.md frontmatter
---
name: my-skill
description: Does something useful for both Claude Code and OpenCode users
mcp:
  server: ./scripts/mcp_server.py
  transport: stdio
  tools:
    - name: do_thing
      description: Performs the thing
---
```

The `mcp:` block above is owned by OpenCode. It is preserved verbatim regardless of whether
its sub-keys match any Claude Code schema.

### Adding New Ecosystems

When a new ecosystem field is encountered that is not yet in `ecosystem_registry.py`:

1. Check `ecosystem_registry.py` first — it may already be registered
2. If absent, flag the field as UNKNOWN rather than stripping it
3. Report the unknown field to the user so it can be added to the registry
4. Do not silently discard it

**SOURCE:** T4 of `plan/tasks-1-multi-ecosystem-plugin-creator.md`; ecosystem registry at `plugins/plugin-creator/scripts/ecosystem_registry.py`
