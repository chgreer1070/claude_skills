---
description: "Optimize AI-facing prompts, CLAUDE.md, SKILL.md, or agent definitions using Anthropic best practices. Pass the file path as argument."
argument-hint: "<file path to optimize>"
agent: rewrite-room-optimizer
allowed-tools: Read, Grep, Glob, Bash, Task, Write, Edit
---

Route this optimization task to the rewrite-room-optimizer agent.

Target: $ARGUMENTS

The agent will determine whether this needs the contextual-ai-documentation-optimizer or subagent-refactorer and delegate accordingly.
