# Tool Access Patterns

Common `tools` and `permissionMode` configurations for agent frontmatter.

---

## Read-Only Analysis

```yaml
tools: Read, Grep, Glob
permissionMode: dontAsk
```

## Code Modification

```yaml
tools: Read, Write, Edit, Bash, Grep, Glob
permissionMode: acceptEdits
```

## Git Operations Only

```yaml
tools: Bash(git:*)
```

## Specific Commands

```yaml
tools: Bash(npm:install), Bash(pytest:*)
```

## Full Access (Default)

```yaml
# Omit tools field - inherits all
```
