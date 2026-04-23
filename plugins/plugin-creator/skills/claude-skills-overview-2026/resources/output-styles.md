# Output Styles — Claude Code Reference

SOURCE: <https://code.claude.com/docs/en/output-styles.md> (accessed 2026-04-23)

Output styles allow Claude Code to operate as different types of agent while retaining core
capabilities (running scripts, reading/writing files, tracking TODOs).

---

## Built-in Output Styles

| Style | Behavior |
|-------|----------|
| `default` | Standard system prompt designed for software engineering tasks |
| `explanatory` | Adds "Insights" sections between engineering tasks — explains implementation choices and codebase patterns |
| `learning` | Collaborative, learn-by-doing mode — shares "Insights" while coding AND asks the user to contribute small strategic code pieces; adds `TODO(human)` markers in code |

---

## How Output Styles Work

- Output styles directly modify Claude Code's system prompt.
- Custom output styles exclude coding-related instructions (such as "verify code with tests")
  UNLESS `keep-coding-instructions: true` is set in the style's frontmatter.
- Custom instructions are appended to the END of the system prompt.
- All output styles trigger reminders for Claude to adhere to the output style instructions
  throughout the conversation.

---

## Activating an Output Style

```text
/output-style                    — opens the style selection menu (also accessible from /config)
/output-style explanatory        — switches directly to the named style
```

- Changes apply at the local project level.
- Saved in `.claude/settings.local.json` under the `outputStyle` field.
- Can also be set by directly editing the `outputStyle` field in any settings file.
- Style changes take effect at the start of the next session — they do not apply mid-conversation.
  The output style is set in the system prompt at session start; keeping the system prompt stable
  throughout a conversation allows prompt caching to reduce latency and cost.

SOURCE: <https://code.claude.com/docs/en/output-styles.md> (accessed 2026-04-23)

---

## Custom Output Styles

Markdown files with YAML frontmatter placed in:

- `~/.claude/output-styles/` — user level
- `.claude/output-styles/` — project level

### File Format

````markdown
---
name: My Custom Style
description: A brief description of what this style does
keep-coding-instructions: false
---

# Custom Style Instructions

You are an interactive CLI tool that helps users...
[custom instructions here]
````

### Frontmatter Fields

| Field | Purpose | Default |
|-------|---------|---------|
| `name` | Display name for the style; if omitted, inherits from the filename | Filename |
| `description` | Description shown in the `/output-style` UI | None |
| `keep-coding-instructions` | When `true`, retains the coding-related parts of Claude Code's default system prompt | `false` |

---

## Plugin Integration

Plugins can bundle output styles via the `outputStyles` field in `plugin.json`:

```json
{
  "outputStyles": ["./output-styles/my-style.md"]
}
```

The path is relative to `plugin.json`. The style file uses the same frontmatter format as
project- or user-level custom styles.

---

## Token Costs and Prompt Caching

Adding instructions to the system prompt increases input tokens. Prompt caching reduces this cost
after the first request in a session — the cached system prompt is not re-processed on subsequent
turns within the same session.

The built-in `explanatory` and `learning` styles produce longer responses than `default` by
design, which increases output tokens. For custom styles, output token usage depends on what your
instructions tell Claude to produce.

SOURCE: <https://code.claude.com/docs/en/output-styles.md> (accessed 2026-04-23)

---

## Comparison to Related Features

| Feature | Scope | Mechanism | Active When |
|---------|-------|-----------|-------------|
| **Output styles** | Main agent loop only; affects system prompt | Replaces or augments the default system prompt; coding instructions opt-in via `keep-coding-instructions` | Always active once selected |
| **CLAUDE.md** | Appended as a user message after the default system prompt | Does NOT replace the default system prompt; adds content on top | Always active (file is present) |
| **`--append-system-prompt`** | Appended to the system prompt | Appends to the existing system prompt; does not replace it | When flag is passed |
| **Agents** | Per-task invocation | Separate agent context; can include model, tools, and additional settings | Only when invoked for a specific task |
| **Skills** | Per-task or auto-loaded | Task-specific prompts invoked with `/skill-name` or triggered by relevance | When invoked or auto-matched; not always active |

### Key Distinctions

**Output styles vs CLAUDE.md:** Output styles can completely replace the coding-specific parts
of Claude Code's default system prompt. CLAUDE.md adds content as a user message following the
default system prompt — it does not replace any part of it.

**Output styles vs agents:** Output styles affect only the main agent loop and only the system
prompt. Agents are invoked for specific tasks and can configure model selection, tool access,
and additional context independently.

**Output styles vs skills:** Output styles modify HOW Claude responds (formatting, tone,
structure) and remain active for the duration of the session once selected. Skills are
task-specific prompts that are invoked on demand or auto-loaded when relevant — they are not
persistently active.
