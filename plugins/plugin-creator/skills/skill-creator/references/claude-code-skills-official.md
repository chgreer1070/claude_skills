# Claude Code Skills — Official Specification

The authoritative specification for skill file format, frontmatter fields, discovery rules, and invocation behavior — everything you need to create skills that work correctly in Claude Code.

**Why read this**: You're building skills. This reference is the primary source for how Claude Code processes the files you create. Frontmatter field names, loading behavior, budget limits, and discovery rules all come from here. When you need to verify a frontmatter field exists, check how `context: fork` actually works, or understand why a skill isn't triggering — this is where to look.

SOURCE: [Extend Claude with skills](https://code.claude.com/docs/en/skills.md) (accessed 2026-03-01)

---

## Table of Contents

- [Skill File Format](#skill-file-format)
- [Frontmatter Reference](#frontmatter-reference)
- [Where Skills Live](#where-skills-live)
- [String Substitutions](#string-substitutions)
- [Dynamic Context Injection](#dynamic-context-injection)
- [Invocation Control](#invocation-control)
- [Context Fork (Subagent Execution)](#context-fork-subagent-execution)
- [Skill Budget and Truncation](#skill-budget-and-truncation)
- [Supporting Files](#supporting-files)
- [Bundled Skills](#bundled-skills)
- [Troubleshooting](#troubleshooting)

---

## Skill File Format

Each skill is a directory with `SKILL.md` as the entrypoint:

```text
my-skill/
├── SKILL.md           # Main instructions (required)
├── template.md        # Template for Claude to fill in
├── examples/
│   └── sample.md      # Example output showing expected format
└── scripts/
    └── validate.sh    # Script Claude can execute
```

`SKILL.md` has two parts: YAML frontmatter (between `---` markers) for configuration, and markdown content with instructions Claude follows when the skill is invoked. The `name` field becomes the `/slash-command`, and the `description` helps Claude decide when to load the skill automatically.

Reference supporting files from `SKILL.md` so Claude knows what each file contains and when to load them:

```markdown
## Additional resources

- For complete API details, see [reference.md](reference.md)
- For usage examples, see [examples.md](examples.md)
```

**Tip**: Keep `SKILL.md` under 500 lines. Move detailed reference material to separate files.

---

## Frontmatter Reference

All fields are optional. Only `description` is recommended.

| Field                      | Required    | Description |
|:---------------------------|:------------|:------------|
| `name`                     | No          | Display name. If omitted, uses directory name. Lowercase letters, numbers, hyphens only (max 64 chars). |
| `description`              | Recommended | What the skill does and when to use it. Claude uses this to decide when to apply the skill. If omitted, uses first paragraph of markdown content. |
| `argument-hint`            | No          | Hint shown during autocomplete. Example: `[issue-number]` or `[filename] [format]`. |
| `disable-model-invocation` | No          | `true` prevents Claude from automatically loading this skill. For manual-only workflows. Default: `false`. |
| `user-invocable`           | No          | `false` hides from `/` menu. For background knowledge Claude loads automatically. Default: `true`. |
| `allowed-tools`            | No          | Tools Claude can use without permission when skill is active. Also restricts Claude to only those tools. |
| `model`                    | No          | Model to use when this skill is active. |
| `context`                  | No          | `fork` runs in a forked subagent context. |
| `agent`                    | No          | Subagent type when `context: fork`. Options: `Explore`, `Plan`, `general-purpose`, or custom agent from `.claude/agents/`. Default: `general-purpose`. |
| `hooks`                    | No          | Hooks scoped to this skill's lifecycle. See Hooks docs for format. |

### allowed-tools Behavior

When `allowed-tools` is **not specified**, the skill inherits tool capabilities from the parent agent. When **specified**, it acts as both:

- **Pre-approval**: Listed tools are granted without per-use permission prompts
- **Capability scoping**: Claude is restricted to only those tools, reducing context size

---

## Where Skills Live

| Location   | Path                                     | Applies to                     |
|:-----------|:-----------------------------------------|:-------------------------------|
| Enterprise | Managed settings                         | All users in organization      |
| Personal   | `~/.claude/skills/<name>/SKILL.md`       | All your projects              |
| Project    | `.claude/skills/<name>/SKILL.md`         | This project only              |
| Plugin     | `<plugin>/skills/<name>/SKILL.md`        | Where plugin is enabled        |

**Precedence**: enterprise > personal > project. Plugin skills use `plugin-name:skill-name` namespace and cannot conflict with other levels. If a skill and a command (`.claude/commands/`) share the same name, the skill takes precedence.

### Automatic Discovery

- **Nested directories**: Editing files in `packages/frontend/` also discovers skills in `packages/frontend/.claude/skills/`. Supports monorepo setups.
- **`--add-dir` directories**: Skills in added directories are loaded with live change detection — editable during sessions without restart.
- **Hot reload**: Changes apply immediately without restart.

---

## String Substitutions

| Variable               | Description |
|:-----------------------|:------------|
| `$ARGUMENTS`           | All arguments passed when invoking. If not present in content, appended as `ARGUMENTS: <value>`. |
| `$ARGUMENTS[N]`        | Access specific argument by 0-based index. |
| `$N`                   | Shorthand for `$ARGUMENTS[N]` (e.g., `$0`, `$1`). |
| `${CLAUDE_SESSION_ID}` | Current session ID. |
| `${CLAUDE_SKILL_DIR}`  | Absolute path to the directory containing the current SKILL.md file. For plugin skills, this is the skill's subdirectory within the plugin, not the plugin root. Use in bash injection commands to reference scripts or files bundled with the skill. |

**Example**:

```yaml
---
name: migrate-component
description: Migrate a component from one framework to another
---

Migrate the $0 component from $1 to $2.
Preserve all existing behavior and tests.
```

Running `/migrate-component SearchBar React Vue` replaces `$0` → `SearchBar`, `$1` → `React`, `$2` → `Vue`.

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

Processing order:

1. Each `!`command`` executes immediately (before Claude sees anything)
2. Output replaces the placeholder in skill content
3. Claude receives the fully-rendered prompt with actual data

This is preprocessing, not something Claude executes. Claude only sees the final result.

**Extended Thinking**: Include the word "ultrathink" anywhere in skill content to enable extended thinking mode.

---

## Invocation Control

| Frontmatter                      | You can invoke | Claude can invoke | Context loading |
|:---------------------------------|:---------------|:------------------|:----------------|
| (default)                        | Yes            | Yes               | Description always in context, full skill loads when invoked |
| `disable-model-invocation: true` | Yes            | No                | Description NOT in context, full skill loads when you invoke |
| `user-invocable: false`          | No             | Yes               | Description always in context, full skill loads when invoked |

### Restricting Claude's Skill Access

1. **Disable all skills**: Deny the `Skill` tool in `/permissions`
2. **Allow/deny specific skills**: `Skill(commit)` for exact match, `Skill(deploy *)` for prefix match
3. **Hide individual skills**: `disable-model-invocation: true` removes from context entirely

**Note**: `user-invocable` controls menu visibility only, not Skill tool access.

---

## Context Fork (Subagent Execution)

`context: fork` runs the skill in isolation. The skill content becomes the subagent's prompt — no access to conversation history.

**Warning**: Only makes sense for skills with explicit instructions and a clear task. Guidelines without a task produce no meaningful output.

| Approach                     | System prompt                             | Task                        | Also loads       |
|:-----------------------------|:------------------------------------------|:----------------------------|:-----------------|
| Skill with `context: fork`   | From agent type (`Explore`, `Plan`, etc.) | SKILL.md content            | CLAUDE.md        |
| Subagent with `skills` field | Subagent's markdown body                  | Claude's delegation message | Preloaded skills + CLAUDE.md |

The `agent` field determines the execution environment. Options: `Explore` (Haiku, read-only), `Plan` (inherits model, read-only), `general-purpose` (inherits model, full tools), or any custom subagent from `.claude/agents/`.

---

## Skill Budget and Truncation

- **Budget**: 2% of context window (fallback 16,000 characters) for skill metadata in `<available_skills>` block
- **Behavior when exceeded**:
  1. Skills are truncated from the `<available_skills>` block
  2. Truncated skills cannot be auto-invoked by Claude
  3. Users can still invoke truncated skills explicitly with `/skill-name`
- **Check**: Run `/context` for warnings about excluded skills
- **Override**: Set `SLASH_COMMAND_TOOL_CHAR_BUDGET` environment variable

---

## Supporting Files

`SKILL.md` should stay focused. Large reference docs, API specifications, or example collections should be in separate files — Claude accesses them only when needed.

Reference supporting files from `SKILL.md`:

```markdown
## Additional resources

- For complete API details, see [reference.md](reference.md)
- For usage examples, see [examples.md](examples.md)
```

---

## Bundled Skills

Five bundled skills ship with every Claude Code session:

| Skill | Purpose |
|:------|:--------|
| `/simplify [focus]` | Reviews changed files for reuse, quality, efficiency. Spawns 3 parallel review agents. |
| `/batch <instruction>` | Orchestrates large-scale parallel changes. One agent per unit in isolated worktrees. |
| `/debug [description]` | Troubleshoots current session by reading debug log. |
| `/loop [interval] <prompt>` | Runs a prompt repeatedly on an interval. Useful for polling deployments or periodically re-running tasks. |
| `/claude-api` | Loads Claude API reference material for your project's language and Agent SDK reference. Also activates automatically when code imports the Anthropic SDK. |

SOURCE: <https://code.claude.com/docs/en/skills.md> (section: "Bundled skills", accessed 2026-03-17)

---

## Troubleshooting

| Problem | Solution |
|:--------|:---------|
| Skill not triggering | Check description keywords match natural language. Verify with "What skills are available?" Try `/skill-name` directly. |
| Triggers too often | Make description more specific. Add `disable-model-invocation: true`. |
| Claude doesn't see all skills | Run `/context` for budget warnings. Set `SLASH_COMMAND_TOOL_CHAR_BUDGET`. |

---

## Related Documentation

- [Subagents](https://code.claude.com/docs/en/sub-agents.md) — delegate tasks to specialized agents
- [Plugins](https://code.claude.com/docs/en/plugins.md) — package and distribute skills
- [Hooks](https://code.claude.com/docs/en/hooks.md) — automate workflows around tool events
- [Memory](https://code.claude.com/docs/en/memory.md) — manage CLAUDE.md files
- [Permissions](https://code.claude.com/docs/en/permissions.md) — control tool and skill access
