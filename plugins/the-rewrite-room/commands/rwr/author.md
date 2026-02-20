---
description: "Author user-facing docs, validate GLFM formatting, or summarize files/URLs/images. Pass the task description or file path."
argument-hint: "<task description or file/URL to summarize>"
agent: rewrite-room-author
allowed-tools: Read, Grep, Glob, Bash, Task, Write, Edit
---

Route this authoring, formatting, or summarization task to the rewrite-room-author agent.

Task: $ARGUMENTS

The agent will determine whether this needs gitlab-docs-expert, documentation-expert, or one of the summarizer agents and delegate accordingly.
