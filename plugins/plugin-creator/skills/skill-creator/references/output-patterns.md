# Output Patterns

Use these patterns when skills need to produce consistent, high-quality output.

**NOTE:** These patterns are examples. Skills support string substitutions (`$ARGUMENTS`, `$N`, `${CLAUDE_SESSION_ID}`) and dynamic context injection (\`\!\`command\`\`) for even more powerful output customization. See main SKILL.md for details.

**SOURCE:** Based on Anthropic skill-creator examples (commit 69c0b1a) and [Skill authoring best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices) (accessed 2026-02-25).

## Template Pattern

Provide templates for output format. Match the level of strictness to your needs.

**For strict requirements (like API responses or data formats):**

```markdown
## Report structure

ALWAYS use this exact template structure:

# [Analysis Title]

## Executive summary
[One-paragraph overview of key findings]

## Key findings
- Finding 1 with supporting data
- Finding 2 with supporting data
- Finding 3 with supporting data

## Recommendations
1. Specific actionable recommendation
2. Specific actionable recommendation
```

**For flexible guidance (when adaptation is useful):**

```markdown
## Report structure

Here is a sensible default format, but use your best judgment:

# [Analysis Title]

## Executive summary
[Overview]

## Key findings
[Adapt sections based on what you discover]

## Recommendations
[Tailor to the specific context]

Adjust sections as needed for the specific analysis type.
```

## Examples Pattern

For skills where output quality depends on seeing examples, provide input/output pairs:

```markdown
## Commit message format

Generate commit messages following these examples:

**Example 1:**
Input: Added user authentication with JWT tokens
Output:
```

feat(auth): implement JWT-based authentication

Add login endpoint and token validation middleware

```

**Example 2:**
Input: Fixed bug where dates displayed incorrectly in reports
Output:
```

fix(reports): correct date formatting in timezone conversion

Use UTC timestamps consistently across report generation

```

Follow this style: type(scope): brief description, then detailed explanation.
```

Examples help Claude understand the desired style and level of detail more clearly than descriptions alone.

## Conditional Workflow Pattern

Guide Claude through decision points when tasks branch:

```markdown
## Document modification workflow

1. Determine the modification type:

   **Creating new content?** → Follow "Creation workflow" below
   **Editing existing content?** → Follow "Editing workflow" below

2. Creation workflow:
   - Use docx-js library
   - Build document from scratch
   - Export to .docx format

3. Editing workflow:
   - Unpack existing document
   - Modify XML directly
   - Validate after each change
   - Repack when complete
```

## Time-Sensitive Information Pattern

Never embed date-conditional logic directly in instructions — it becomes wrong as time passes. Instead, use the current method as the default and preserve legacy approaches in a labeled collapsible section:

```markdown
## Current method

Use the v2 API endpoint: `api.example.com/v2/messages`

## Old patterns

<details>
<summary>Legacy v1 API (deprecated 2025-08)</summary>

The v1 API used: `api.example.com/v1/messages`

This endpoint is no longer supported.
</details>
```

This keeps the main content clean while preserving historical context for debugging.

## Consistent Terminology

Choose one term per concept and use it throughout the skill. Inconsistency forces Claude to infer equivalence, which introduces errors.

- Good: Always "API endpoint", always "field", always "extract"
- Bad: Mix "API endpoint" / "URL" / "API route" / "path"
- Bad: Mix "field" / "box" / "element" / "control"
