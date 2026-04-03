---
description: "Convert user-facing documentation into an AI-readable Claude skill. Pass a GitHub URL or local path to the docs directory."
argument-hint: "<github-url or /path/to/docs> [output_skill_name]"
agent: rewrite-room-doc-converter
allowed-tools: Read, Grep, Glob, Bash, Task, Write, Edit, mcp__file-reader__read_file
---

Route this doc-to-skill conversion task to the rewrite-room-doc-converter agent.

Task: $ARGUMENTS

The agent follows the user-docs-to-ai-skill SOP — it will resolve the source path,
inventory documentation, extract content, and produce a skill directory.
