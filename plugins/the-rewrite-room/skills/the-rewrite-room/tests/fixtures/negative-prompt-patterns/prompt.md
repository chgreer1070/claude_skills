---
description: "Example skill with negative prompt patterns — prohibition-only instructions without positive alternatives"
allowed-tools: Read, Grep, Glob
---

# Example Skill with Negative Prompt Patterns

This fixture demonstrates prohibition-only patterns that the prompt-structure-validator should flag.

## Rules

- Never use `cat` for reading files
- Don't run `find` for file discovery
- Do not use `grep` from bash — use the Grep tool instead
- Never hardcode absolute paths in your output
- Don't skip validation steps
- Do not produce output without running tests first
- Never commit without checking git status first
- Do not write Python code directly — delegate to agents

## Output Format

- Never produce output without a STATUS block
- Don't omit the ARTIFACTS section
- Do not use vague language in the SUMMARY field

> **Test purpose**: This file contains 10 prohibition-only patterns (all "never", "don't",
> "do not" with no positive alternative provided). The prompt-structure-validator should
> flag these and suggest converting them to positive directives with rationale.
>
> Example conversion:
> - Before: "Never use `cat` for reading files"
> - After: "Use the Read tool to read files. Reason: Read handles encoding and pagination correctly."
