# Common Agent Patterns

Frontmatter examples for common agent archetypes.

---

## Read-Only Analyzer

```yaml
name: code-analyzer
description: Analyze code without modifications. Use for security audits.
tools: Read, Grep, Glob
permissionMode: dontAsk
model: sonnet
```

## Documentation Writer

```yaml
name: docs-writer
description: Generate documentation from code. Use when creating READMEs.
tools: Read, Write, Edit, Grep, Glob
permissionMode: acceptEdits
model: sonnet
```

## Debugger

```yaml
name: debugger
description: Debug runtime errors. Use when encountering exceptions.
tools: Read, Edit, Bash, Grep, Glob
model: opus  # Complex reasoning needed
```

## Research Agent

```yaml
name: researcher
description: Research codebase patterns. Use before major changes.
model: haiku  # Fast for exploration
tools: Read, Grep, Glob
permissionMode: plan  # Read-only mode
```

## Skill-Enhanced Agent

```yaml
name: python-expert
description: Python development specialist with deep async knowledge.
skills: python-development, async-patterns
model: sonnet
```
