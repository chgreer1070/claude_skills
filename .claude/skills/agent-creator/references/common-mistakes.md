# Common Mistakes

10 documented failure patterns when creating agents.

---

## Mistake 1: Testing in Production

**Problem**: Creating agent and immediately using it for real work without testing

**Consequence**: Agent behaves unexpectedly, wrong tool access, poor output quality

**Solution**: Always test with simple example prompts first (see [Testing Your Agent](./testing-your-agent.md))

## Mistake 2: Over-Specifying vs Under-Specifying

**Problem**: Either writing 50-line descriptions with every possible detail, or 1-sentence vague descriptions

**Consequence**:

- Over-specified: Claude ignores most details, wasted tokens
- Under-specified: Agent never gets invoked or does wrong thing

**Solution**: Focus on:

- 2-3 action verbs for what it does
- 2-3 trigger phrases for when to use it
- 3-5 domain keywords
- Keep under 200 words

## Mistake 3: Forgetting Skills Are Not Inherited

**Problem**: Assuming agent inherits skills from parent conversation

**Consequence**: Agent lacks domain knowledge, produces poor results, misses patterns

**Solution**: Explicitly list all needed skills in frontmatter:

```yaml
# Wrong - assumes parent skills available
name: python-expert
description: Expert Python developer

# Right - explicitly loads skills
name: python-expert
description: Expert Python developer
skills: python-development, testing-patterns
```

## Mistake 4: Wrong Permission Mode for Task

**Problem**: Using `default` when `acceptEdits` would work, or `bypassPermissions` unnecessarily

**Consequence**:

- Too restrictive: Constant user prompts, slow workflow
- Too permissive: Accidental destructive operations

**Solution**: Match permission mode to agent's actual operations:

| Agent Type         | Permission Mode     | Reason                             |
| ------------------ | ------------------- | ---------------------------------- |
| Read-only analyzer | `dontAsk` or `plan` | Never modifies files               |
| Doc generator      | `acceptEdits`       | Edits expected, safe               |
| Code implementer   | `acceptEdits`       | Edits expected                     |
| Reviewer           | `dontAsk`           | Only reads code                    |
| Debugger           | `default`           | May need user approval for changes |

## Mistake 5: Not Testing Tool Restrictions

**Problem**: Restricting tools but not verifying agent can still complete its task

**Consequence**: Agent fails silently or produces "I cannot do that" errors

**Solution**:

1. List what the agent MUST do
2. Identify minimum tools needed
3. Test with those tools only
4. Add tools back if needed

```yaml
# Example: Agent that reviews code
# Needs: Read files, search patterns, find files
# Does NOT need: Write, Edit, Bash

tools: Read, Grep, Glob
permissionMode: dontAsk
```

## Mistake 6: Creating One Giant Agent

**Problem**: Single agent that "does everything" for a domain

**Consequence**:

- Poor delegation decisions (Claude doesn't know when to use it)
- Conflicting requirements (read-only vs write)
- Hard to maintain

**Solution**: Create focused agents with single responsibilities:

```yaml
# Wrong - one agent for everything
name: python-helper
description: Helps with Python code, testing, documentation, and debugging

# Right - separate focused agents
name: python-code-reviewer
description: Reviews Python code for quality issues

name: python-test-writer
description: Writes pytest tests for Python functions

name: python-doc-generator
description: Generates docstrings and README files
```

## Mistake 7: Copy-Pasting Without Adaptation

**Problem**: Copying example agent or template without customizing for specific needs

**Consequence**: Agent has wrong tools, wrong model, irrelevant instructions, poor performance

**Solution**: When using templates:

1. Read the entire template first
2. Identify sections that need customization
3. Update frontmatter to match your needs
4. Adapt workflow to your specific use case
5. Remove example placeholders and instructions
6. Test the adapted agent

## Mistake 8: Ignoring Output Format

**Problem**: Not specifying expected output structure for agents that produce reports

**Consequence**: Inconsistent outputs, hard to parse results, user confusion

**Solution**: Include explicit output format in agent body:

````markdown
## Output Format

Produce results in this structure:

```markdown
# Review Summary

## Critical Issues
- {issue with file:line reference}

## Recommendations
- {actionable improvement}

## Positive Findings
- {what was done well}
```
````

## Mistake 9: Not Documenting Custom Conventions

**Problem**: Creating agents that follow project-specific patterns without documenting them

**Consequence**: Future users or Claude don't understand agent's behavior

**Solution**: Add a "Conventions" or "Project Context" section:

```markdown
## Project Conventions

This codebase uses:
- `poe` task runner (not npm scripts)
- `basedpyright` (not ty/mypy)
- Test files end with `_test.py` (not `test_*.py`)
```

## Mistake 10: Skipping Validation Checklist

**Problem**: Saving agent immediately after writing without validation

**Consequence**: Invalid YAML, missing fields, broken references

**Solution**: Always use the validation checklist in Phase 6 of workflow before saving
