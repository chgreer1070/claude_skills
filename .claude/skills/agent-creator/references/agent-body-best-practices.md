# Agent Body Best Practices

Structure, XML tag usage, examples, output format specification, and output note patterns for agent body content.

---

## Identity Section

Start with a clear role statement:

```markdown
You are a {specific role} with expertise in {domain areas}. Your purpose is to {primary function}.
```

## Use XML Tags for Structure

Organize instructions using semantic XML tags:

- `<workflow>` - Step-by-step processes
- `<rules>` - Hard constraints and requirements
- `<quality>` - Quality standards and checks
- `<examples>` - Input/output demonstrations
- `<boundaries>` - What the agent must NOT do

## Include Concrete Examples

Show the expected pattern with actual input/output:

```markdown
<example>
**Input**: User requests review of authentication code
**Output**: Security analysis with specific vulnerability citations
</example>
```

## Specify Output Format

Define expected response structure:

````markdown
## Output Format

```markdown
# [Title]

## Summary
[1-2 sentences]

## Findings
[Categorized list]

## Recommendations
[Actionable items]
```
````

## End with Output Note

If the agent produces reports, add:

```markdown
## Important Output Note

Your complete output must be returned as your final response. The caller
cannot see your execution unless you return it.
```
