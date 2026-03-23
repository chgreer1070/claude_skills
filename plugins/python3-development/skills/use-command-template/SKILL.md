---
name: use-command-template
argument-hint: <skill_purpose_description>
user-invocable: true
description: Use when creating new Claude Code skills following established patterns and templates. Activates on "create a new skill", "add a skill to plugin", or "write skill from template" requests. Note — commands are deprecated; this skill creates SKILL.md files instead. Produces correctly structured skill files with valid frontmatter and body.
---

# Use Skill Template

Create a new Claude Code skill following established patterns.

**Note**: Commands have been deprecated in favor of skills. This skill creates properly formatted SKILL.md files.

## Execution Steps

Consult `../python3-development/references/python3-standards.md` when applying shared architecture, typing, testing, or CLI rules; full standards, graphs, and amendment process are documented there.

### 1. Determine Skill Type

- Parse skill purpose from arguments
- Identify appropriate category (testing/development/analysis/quality)
- Choose suitable skill name (kebab-case format)

### 2. Apply Template

Create SKILL.md with required structure:

```markdown
---
name: skill-name
description: 'This skill should be used when the user asks to "specific trigger 1", "specific trigger 2", "specific trigger 3". Brief description of what the skill does.'
version: "1.0.0"
last_updated: "YYYY-MM-DD"
user-invocable: true  # if user can invoke directly
argument-hint: "<argument_description>"  # if accepts arguments
---

# Skill Title

Brief overview of the skill's purpose.

## When to Use

- Trigger condition 1
- Trigger condition 2
- Trigger condition 3

## Process/Instructions

### Step 1: First Action
{Details}

### Step 2: Second Action
{Details}

## Output Format

{Expected output structure}

## Related Skills

- **related-skill-1**: Description
- **related-skill-2**: Description
```

### 3. Skill Directory Structure

Create skill in appropriate location:

```text
plugins/{plugin-name}/skills/{skill-name}/
└── SKILL.md
```

Skills must be directly under `skills/` — subdirectory nesting is not supported and causes skills to silently fail to register. Do not add a `skills` key to `plugin.json` — auto-discovery handles registration.

## Best Practices

**Naming:**

- Use kebab-case for directory and skill names
- Use clear verb-noun format when applicable
- Keep names concise but descriptive

**Description:**

- Use third person: "This skill should be used when..."
- Include specific trigger phrases users would say
- List 3-5 concrete examples of when to invoke

**Content:**

- Keep skills focused on single responsibility
- Include at least one example usage
- Define clear output format
- Reference related skills

## Example Usage

```text
/python3-development:use-command-template analyze API endpoints for rate limiting
/python3-development:use-command-template validate database migrations for safety
/python3-development:use-command-template generate Pydantic classes from schema
```

## Migration Note

If migrating from old command format:

| Old Format      | New Format                                 |
| --------------- | ------------------------------------------ |
| `title:`        | `name:`                                    |
| `command_type:` | (removed - use directory structure)        |
| `related_docs:` | (use markdown links in content)            |
| `@include`      | (copy content directly or use references/) |
