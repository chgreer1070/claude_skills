---
name: example-agent
description: "Demonstrates all available agent frontmatter fields. Use when you need a reference for agent configuration or when learning about agent capabilities. Handles example tasks, demonstration requests, and tutorial scenarios."
tools: Read, Grep, Glob, WebFetch, WebSearch
disallowedTools: Bash, Write, Edit
model: sonnet
permissionMode: default
skills: python3-development, claude-skills-overview-2026
hooks:
  PreToolUse:
    - matcher: "Read"
      hooks:
        - type: command
          command: "echo 'About to read a file'"
          timeout: 5
color: cyan
---

# Example Agent

This agent demonstrates all available frontmatter fields for Claude Code agents.

## Purpose

Use this as a reference when creating new agents. All fields shown above are valid agent frontmatter options.

## Field Descriptions

| Field             | Purpose                                           |
| ----------------- | ------------------------------------------------- |
| `name`            | Unique identifier (kebab-case, required)          |
| `description`     | When to delegate to this agent (required)         |
| `tools`           | Allowlist of tools the agent can use              |
| `disallowedTools` | Denylist of tools the agent cannot use            |
| `model`           | Which model to use (sonnet, opus, haiku, inherit) |
| `permissionMode`  | Permission behavior for tool usage                |
| `skills`          | Skills to load when agent is active               |
| `hooks`           | Scoped hooks for agent lifecycle                  |
| `color`           | Terminal output color for agent messages          |

## Usage

This agent is for demonstration purposes only. When creating real agents, include only the fields you need.
