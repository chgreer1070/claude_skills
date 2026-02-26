# Anti-Patterns to Avoid

Common configuration mistakes with corrected alternatives.

---

## Vague Description

```yaml
# DON'T
description: Helps with code

# DO
description: Review Python code for PEP 8 compliance, type hint coverage,
  and async/await patterns. Use when working with Python files.
```

## Over-Broad Responsibilities

```yaml
# DON'T
name: everything-helper
description: Handles all code tasks

# DO - Create focused agents
name: code-reviewer
name: test-writer
name: documentation-generator
```

## Missing Tool Restrictions

```yaml
# DON'T - For read-only agent
# (tools field omitted, inherits write access)

# DO
tools: Read, Grep, Glob
permissionMode: dontAsk
```

## Assuming Skill Inheritance

```yaml
# DON'T - Skills are NOT inherited
# (hoping parent skills apply)

# DO - Explicitly load needed skills
skills: python-development, testing-patterns
```

## Wrong Model Choice

```yaml
# DON'T - Opus for simple search
model: opus
tools: Read, Grep, Glob

# DO
model: haiku  # Fast for simple operations
```
