# Claude Code Skills — Official Reference

Authoritative specification for how Claude Code discovers, loads, configures, and invokes skills — the runtime environment this skill documents.

**Why read this**: This skill teaches you the skills system. This reference is the primary source from which that teaching derives. When the skill's content and the official docs disagree, the official docs win. Read this to verify claims, check for new features, and understand edge cases not covered in the skill body.

SOURCE: [Extend Claude with skills](https://code.claude.com/docs/en/skills.md) (accessed 2026-03-01)

---

## Bundled Skills

Bundled skills ship with Claude Code and are available in every session. Unlike built-in commands (which execute fixed logic), bundled skills are prompt-based: they give Claude a detailed playbook and let it orchestrate work using its tools.

- **`/simplify`**: Reviews recently changed files for code reuse, quality, and efficiency issues, then fixes them. Spawns three review agents in parallel (code reuse, code quality, efficiency), aggregates findings, and applies fixes. Pass optional text to focus on specific concerns: `/simplify focus on memory efficiency`.

- **`/batch <instruction>`**: Orchestrates large-scale changes across a codebase in parallel. Researches the codebase, decomposes work into 5–30 independent units, presents a plan for approval. Once approved, spawns one background agent per unit, each in an isolated git worktree. Each agent implements its unit, runs tests, and opens a pull request. Requires a git repository. Example: `/batch migrate src/ from Solid to React`.

- **`/debug [description]`**: Troubleshoots your current Claude Code session by reading the session debug log. Optionally describe the issue to focus the analysis.

Claude Code also includes a bundled developer platform skill that activates automatically when your code imports the Anthropic SDK.

---

## Skill File Format

### SKILL.md Structure

Every skill is a directory with `SKILL.md` as the entrypoint:

```text
my-skill/
├── SKILL.md           # Main instructions (required)
├── template.md        # Template for Claude to fill in
├── examples/
│   └── sample.md      # Example output showing expected format
└── scripts/
    └── validate.sh    # Script Claude can execute
```

Two parts: YAML frontmatter (between `---` markers) for metadata, and markdown content with instructions Claude follows when invoked.

### Frontmatter Reference

All fields are optional. Only `description` is recommended.

| Field                      | Required    | Description |
|:---------------------------|:------------|:------------|
| `name`                     | No          | Display name. If omitted, uses directory name. Lowercase letters, numbers, hyphens only (max 64 chars). |
| `description`              | Recommended | What the skill does and when to use it. If omitted, uses first paragraph of markdown content. |
| `argument-hint`            | No          | Hint shown during autocomplete. Example: `[issue-number]` or `[filename] [format]`. |
| `disable-model-invocation` | No          | `true` prevents Claude from automatically loading this skill. Default: `false`. |
| `user-invocable`           | No          | `false` hides from `/` menu. Default: `true`. |
| `allowed-tools`            | No          | Tools Claude can use without permission when skill is active. |
| `model`                    | No          | Model to use when this skill is active. |
| `context`                  | No          | `fork` runs in a forked subagent context. |
| `agent`                    | No          | Subagent type when `context: fork`. Options: `Explore`, `Plan`, `general-purpose`, or custom. Default: `general-purpose`. |
| `hooks`                    | No          | Hooks scoped to this skill's lifecycle. Events: `PreToolUse`, `PostToolUse`, `Stop`. |

---

## Where Skills Live

| Location   | Path                                     | Applies to                     |
|:-----------|:-----------------------------------------|:-------------------------------|
| Enterprise | Managed settings                         | All users in organization      |
| Personal   | `~/.claude/skills/<name>/SKILL.md`       | All your projects              |
| Project    | `.claude/skills/<name>/SKILL.md`         | This project only              |
| Plugin     | `<plugin>/skills/<name>/SKILL.md`        | Where plugin is enabled        |

**Precedence**: enterprise > personal > project. Plugin skills use `plugin-name:skill-name` namespace, so they cannot conflict.

### Automatic Discovery

- **Nested directories**: When editing files in `packages/frontend/`, Claude Code also looks for skills in `packages/frontend/.claude/skills/`. Supports monorepo setups.
- **`--add-dir` directories**: Skills in `.claude/skills/` within `--add-dir` directories are loaded with live change detection — editable during sessions without restart.
- **Commands compatibility**: Files in `.claude/commands/` still work and support the same frontmatter. If a skill and command share the same name, the skill takes precedence.

---

## String Substitutions

| Variable               | Description |
|:-----------------------|:------------|
| `$ARGUMENTS`           | All arguments passed. If not present in content, appended as `ARGUMENTS: <value>`. |
| `$ARGUMENTS[N]`        | Specific argument by 0-based index. |
| `$N`                   | Shorthand for `$ARGUMENTS[N]`. |
| `${CLAUDE_SESSION_ID}` | Current session ID. |

---

## Dynamic Context Injection

The `!`command`` syntax runs shell commands before skill content is sent to Claude. Command output replaces the placeholder — Claude receives actual data, not the command.

```yaml
---
name: pr-summary
description: Summarize changes in a pull request
context: fork
agent: Explore
allowed-tools: Bash(gh *)
---

## Pull request context
- PR diff: !`gh pr diff`
- PR comments: !`gh pr view --comments`
- Changed files: !`gh pr diff --name-only`

## Your task
Summarize this pull request...
```

Processing:
1. Each `!`command`` executes immediately (before Claude sees anything)
2. Output replaces the placeholder in skill content
3. Claude receives the fully-rendered prompt

To enable extended thinking in a skill, include the word "ultrathink" anywhere in skill content.

---

## Invocation Control

| Frontmatter                      | You can invoke | Claude can invoke | When loaded into context |
|:---------------------------------|:---------------|:------------------|:-------------------------|
| (default)                        | Yes            | Yes               | Description always in context, full skill loads when invoked |
| `disable-model-invocation: true` | Yes            | No                | Description NOT in context, full skill loads when you invoke |
| `user-invocable: false`          | No             | Yes               | Description always in context, full skill loads when invoked |

**Key distinction**: In a regular session, skill descriptions are loaded into context so Claude knows what's available, but full skill content only loads when invoked. Subagents with preloaded skills work differently — full skill content is injected at startup.

---

## Restrict Claude's Skill Access

Three methods:

1. **Disable all skills**: Deny the `Skill` tool in `/permissions`
2. **Allow/deny specific skills**: `Skill(commit)` for exact match, `Skill(deploy *)` for prefix match
3. **Hide individual skills**: `disable-model-invocation: true` in frontmatter

**Note**: `user-invocable` only controls menu visibility, not Skill tool access. Use `disable-model-invocation: true` to block programmatic invocation.

---

## Run Skills in a Subagent

`context: fork` runs the skill in isolation. The skill content becomes the subagent's prompt — it won't have access to conversation history.

**Warning**: `context: fork` only makes sense for skills with explicit instructions and a clear task. Guidelines without a task produce no meaningful output.

| Approach                     | System prompt                             | Task                        | Also loads       |
|:-----------------------------|:------------------------------------------|:----------------------------|:-----------------|
| Skill with `context: fork`   | From agent type (`Explore`, `Plan`, etc.) | SKILL.md content            | CLAUDE.md        |
| Subagent with `skills` field | Subagent's markdown body                  | Claude's delegation message | Preloaded skills + CLAUDE.md |

---

## Skill Budget and Truncation

- **Budget**: 2% of context window (fallback 16,000 characters) for skill metadata
- **Override**: `SLASH_COMMAND_TOOL_CHAR_BUDGET` environment variable
- **Check**: Run `/context` for warnings about excluded skills
- Truncated skills can still be invoked explicitly with `/skill-name`

---

## Troubleshooting

- **Not triggering**: Check description keywords, verify with "What skills are available?", invoke directly with `/skill-name`
- **Triggers too often**: Make description more specific, add `disable-model-invocation: true`
- **Claude doesn't see all skills**: Run `/context` to check budget warnings, set `SLASH_COMMAND_TOOL_CHAR_BUDGET` to override

---

## Related

- [Subagents](https://code.claude.com/docs/en/sub-agents.md) — delegate tasks to specialized agents
- [Plugins](https://code.claude.com/docs/en/plugins.md) — package and distribute skills
- [Hooks](https://code.claude.com/docs/en/hooks.md) — automate workflows around tool events
- [Memory](https://code.claude.com/docs/en/memory.md) — manage CLAUDE.md files
- [Permissions](https://code.claude.com/docs/en/permissions.md) — control tool and skill access
