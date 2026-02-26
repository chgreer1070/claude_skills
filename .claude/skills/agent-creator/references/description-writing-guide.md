# Description Writing Guide

Required elements, templates, and patterns for writing effective agent `description` values.

---

The description is CRITICAL - Claude uses it to decide when to delegate.

## Required Elements

1. **Action verbs** - What the agent does: "Reviews", "Generates", "Debugs"
2. **Trigger phrases** - When to use: "Use when", "Invoke for", "Delegates to"
3. **Keywords** - Domain terms: "security", "performance", "documentation"

## Template

```text
{Action 1}, {Action 2}, {Action 3}. Use when {situation 1}, {situation 2},
or when working with {keywords}. {Optional: Proactive trigger instruction}.
```

## Good Example

```yaml
description: 'Expert code review specialist. Proactively reviews code for quality, security, and maintainability. Use immediately after writing or modifying code. Provides specific, actionable feedback on bugs, performance issues, and adherence to project patterns.'
```

## Bad Example

```yaml
description: Reviews code
```

## Proactive Agents

For agents that should be invoked automatically:

```yaml
description: '... Use IMMEDIATELY after code changes. Invoke PROACTIVELY when implementation is complete. DO NOT wait for user request.'
```
