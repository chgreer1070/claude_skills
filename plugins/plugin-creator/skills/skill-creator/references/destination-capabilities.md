# Destination Capabilities Reference

Destination affects which frontmatter fields work and what runtime capabilities are available. Choose destination before writing frontmatter.

| Destination | `hooks` in frontmatter | `permissionMode` | `context: fork` Agent tool | `/skill-name` in `-p` mode |
|---|---|---|---|---|
| Plugin (`plugins/*/skills/`) | Executed at plugin trust level | FORBIDDEN — silently ignored | NOT available | NOT available |
| Plugin (`plugins/*/agents/`) | FORBIDDEN — prevents startup | FORBIDDEN — silently ignored | N/A | NOT available |
| Project (`.claude/skills/`) | Executed at project trust level | Supported | NOT available | NOT available |
| User (`~/.claude/skills/`) | Executed at user trust level | Supported | NOT available | NOT available |

For plugin agent security restrictions (forbidden frontmatter fields), see the [Plugin Agent Security Restrictions](../claude-plugins-reference-2026/SKILL.md) section in `claude-plugins-reference-2026` — that is the canonical source.

**Headless / `-p` mode (any destination):**

ALL `/skill-name` invocations are unavailable when Claude Code runs in headless mode (`-p` flag or Agent SDK CLI). Skills cannot be called from automation via slash syntax. The full workflow must be embedded directly in the prompt instead.

SOURCE: [headless.md](https://code.claude.com/docs/en/headless.md) (accessed 2026-04-23)

**`context: fork` skills (any destination):**

The Agent tool is NOT available inside a forked context — the skill cannot delegate to subagents. For hierarchical delegation, the parent must run in main context (no `context: fork`).

SOURCE: [Claude Code Skills Documentation](https://code.claude.com/docs/en/skills.md) — "Context Fork Behavior" section (accessed 2026-04-23)
