# Permission Mode Guide

Mode comparison for the `permissionMode` frontmatter field.

---

| Mode                | File Edits   | Bash Commands       | Use Case                     |
| ------------------- | ------------ | ------------------- | ---------------------------- |
| `default`           | Prompts      | Prompts             | Security-conscious workflows |
| `acceptEdits`       | Auto-accepts | Prompts destructive | Documentation writers        |
| `dontAsk`           | Auto-denies  | Auto-denies         | Read-only analyzers          |
| `bypassPermissions` | Skips all    | Skips all           | Trusted automation only      |
| `plan`              | Disabled     | Disabled            | Planning/research phases     |

**CRITICAL**: Use `bypassPermissions` sparingly and document why.
