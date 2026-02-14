---
description: 'Optimize CLAUDE.md, SKILL.md, agent definitions, and other AI-facing files for Claude comprehension and economy. Use when improving prompt effectiveness, reducing token waste, rewriting instructions for LLM consumption, or enhancing files with latest Claude Code features. Delegates to @claude-context-optimizer agent. Invoke with /optimize-claude-md <file-or-directory>.'
argument-hint: '<file-or-directory-path>'
user-invocable: true
disable-model-invocation: true
---

# Optimize AI-Facing Files

Delegate optimization of the target file(s) to the `@claude-context-optimizer` agent.

## Invocation

```text
/optimize-claude-md <path>
```

Where `<path>` is one of:

- A single file (e.g., `./CLAUDE.md`, `.claude/skills/my-skill/SKILL.md`, `.claude/agents/my-agent.md`)
- A skill directory (e.g., `.claude/skills/my-skill/`) — optimizes SKILL.md and all reference files
- A plugin directory (e.g., `plugins/my-plugin/`) — optimizes CLAUDE.md, all skills, and all agents

## Process

1. **Validate target exists** — Read the file or directory at `$ARGUMENTS`
2. **Determine scope** — single file, skill directory, or plugin directory
3. **Delegate to agent** — spawn `@claude-context-optimizer` via Task tool with:

<delegation_template>

```text
TARGET: {resolved path(s)}
FILE TYPE: {CLAUDE.md | SKILL.md | agent definition | reference file}

TASK:
1. Enable the prompt-optimization-claude-45 skill
2. Read the complete target file(s)
3. Analyze against the 7 optimization principles (positive framing, motivation, concrete examples, front-loaded priorities, concise language, explicit format control, strategic XML tagging)
4. Apply transformations — preserve original intent, improve execution economy
5. Present structured output: Analysis, Optimized Content, Changes Applied, Usage Notes

CONSTRAINTS:
- Preserve all original intent and functional behavior
- Maintain file structure conventions (frontmatter format, heading hierarchy)
- Apply compression only where it improves clarity — brevity is not the sole goal
- Verify technical terms are exact (tool names, file paths, command syntax)
- For SKILL.md files: keep description field under 1024 chars, check for YAML multiline indicator bugs
- For agent files: preserve required frontmatter fields (name, description)
- For CLAUDE.md files: front-load critical instructions, use decision flow diagrams for complex logic
```

</delegation_template>

4. **Review agent output** — verify the optimized content preserves intent before presenting to user
5. **Present diff** — show before/after comparison with principle citations for each change
6. **Apply on approval** — write optimized content only after user confirms

## Scope Expansion Rules

When target is a **skill directory**:

1. Optimize SKILL.md (primary)
2. Optimize each file in `references/` (secondary)
3. Verify cross-references between SKILL.md and reference files remain valid

When target is a **plugin directory**:

1. Optimize CLAUDE.md if present (primary)
2. List all skills and agents — ask user which to include
3. Optimize selected components sequentially
4. Verify plugin.json references remain consistent

## Edge Cases

- **File not found**: Report exact path checked, ask user to confirm
- **Binary or non-markdown file**: Skip with explanation
- **Already optimal**: Acknowledge effectiveness, suggest only minor refinements per agent constraint
- **Large file (>500 lines)**: Note token budget concern, recommend splitting via `/plugin-creator:refactor-skill` if SKILL.md
