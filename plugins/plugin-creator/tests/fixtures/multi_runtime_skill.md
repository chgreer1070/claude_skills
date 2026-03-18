---
name: my-multi-runtime-skill
description: Does X when you need to Y
user-invocable: true
mcp:
  my-server:
    command: npx -y @scope/server-package
    args:
    - /tmp/workspace
  remote:
    url: https://api.example.com/mcp
    headers:
      Authorization: Bearer token123
---

# My Multi-Runtime Skill

This skill works in both Claude Code and OpenCode.
