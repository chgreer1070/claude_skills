---
description: Shorthand for the holistic-linting skill. Activates the full linting ecosystem with optional file/directory path arguments.
argument-hint: <file-or-directory-paths>
---

# /lint

Activates the `/holistic-linting:holistic-linting` skill with optional path arguments.

## Instructions

1. Load the holistic-linting skill:

```claude
Skill(command: "holistic-linting:holistic-linting")
```

2. Follow the skill's workflow for the provided paths: `$ARGUMENTS`

If no arguments provided, apply the skill to all files modified in the current task.
