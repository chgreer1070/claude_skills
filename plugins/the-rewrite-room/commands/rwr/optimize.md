---
description: Optimize AI-facing prompts, CLAUDE.md, SKILL.md, or agent definitions using Anthropic best practices. Pass the file path as argument.
argument-hint: <file path to optimize>
agent: rewrite-room-optimizer
allowed-tools: Read, Grep, Glob, Bash, Task, Write, Edit
---

Route this optimization task to the rewrite-room-optimizer agent.

Target: $ARGUMENTS

The agent will determine whether this needs the contextual-ai-documentation-optimizer or subagent-refactorer and delegate accordingly.

Routing within `contextual-ai-documentation-optimizer`:
- Optimize existing content (improve clarity, fix structure, apply Anthropic prompt engineering principles) → `plugin-creator:contextual-ai-documentation-optimizer`
- Audit quality (read-only, no writes, score against completeness categories) → `/plugin-creator:audit-skill-completeness` skill directly
- Sync content against upstream docs (add NEW/fix STALE from live sources) → general-purpose agent with drift report until `skill-content-updater` lands (backlog #1899)
- Write/rewrite description field only → `/plugin-creator:write-frontmatter-description` skill directly
