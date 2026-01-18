# Reference Documentation

Supporting documentation files included with the prompt-optimization-claude-45 skill.

---

## Overview

The skill uses progressive disclosure to keep the main SKILL.md concise while providing detailed supporting documentation. Reference files are loaded on demand when deeper information is needed.

---

## context-windows.md

**Location**: `skills/prompt-optimization-claude-45/context-windows.md`

**Purpose**: Token budget management strategies and context window optimization techniques.

### What It Covers

**Token Budget Awareness**:
- Claude 4.5 Sonnet: ~200K tokens
- Claude 4.5 Opus: ~200K tokens
- Effective context management strategies

**Context Window Optimization**:
- Front-loading critical instructions
- Progressive disclosure patterns
- When to split into multiple files
- Context compaction triggers

**Memory Management**:
- Which instructions to keep in main context
- When to use reference files
- How to structure for context efficiency

### When to Reference

Use this file when:
- CLAUDE.md files exceed 500 lines
- Context window warnings appear
- Optimizing for token efficiency
- Designing multi-file skill structures

---

## whats-new-claude-4.5.md

**Location**: `skills/prompt-optimization-claude-45/whats-new-claude-4.5.md`

**Purpose**: Claude 4.5 model capabilities, changes from previous versions, and optimization opportunities specific to this model family.

### What It Covers

**New Capabilities**:
- Parallel tool usage (multiple simultaneous tool calls)
- Improved instruction following precision
- Enhanced conciseness in responses
- Better error recovery

**Behavioral Changes**:
- More direct communication style
- Reduced hedging language
- Better handling of complex multi-step tasks
- Improved code generation quality

**Optimization Opportunities**:
- Structuring instructions for parallel execution
- Using direct action language
- Leveraging extended thinking for complex reasoning
- Reducing unnecessary summarization prompts

**Migration Guidance**:
- Converting Claude 3.x prompts to Claude 4.5 style
- Removing workarounds for previous limitations
- Updating communication style expectations

### When to Reference

Use this file when:
- Creating new CLAUDE.md files for Claude 4.5
- Migrating existing prompts from Claude 3.x
- Optimizing for Claude 4.5 specific capabilities
- Understanding behavioral differences between versions

---

## references/accessing_online_resources.md

**Location**: `skills/prompt-optimization-claude-45/references/accessing_online_resources.md`

**Purpose**: Web resource access patterns for accurate data retrieval.

**Note**: This file is a symbolic link to the agent-orchestration plugin's reference documentation.

### What It Covers

**Web Access Tools**:
- WebFetch for content retrieval
- WebSearch for current information
- MCP servers for external data

**Best Practices**:
- When to use each tool
- How to verify information freshness
- Citing sources in documentation
- Handling rate limits and errors

**Verification Patterns**:
- Cross-referencing multiple sources
- Checking official documentation first
- Using precise technical terminology
- Avoiding paraphrasing verified terms

### When to Reference

Use this file when:
- Verifying technical terms before documenting
- Researching best practices from official sources
- Citing external documentation
- Optimizing prompts that reference web resources

---

## File Organization Strategy

### Progressive Disclosure Pattern

```
SKILL.md (main file, <100 lines)
├── Quick overview and principles
├── Links to detailed references
└── When to use this skill

references/ (detailed documentation)
├── context-windows.md (token optimization)
├── whats-new-claude-4.5.md (model-specific)
└── accessing_online_resources.md (verification)
```

### Why This Structure

**Context Efficiency**: Main SKILL.md loads every time. Reference files load only when needed.

**Maintainability**: Detailed documentation in separate files is easier to update without touching core skill logic.

**Scalability**: New reference files can be added without bloating the main skill file.

**Navigation**: Markdown links allow Claude to click through to needed details progressively.

---

## Usage in Skill

The main SKILL.md references these files at relevant points:

```markdown
> [Web resource access, definitive guide for getting accurate data for high quality results](./references/accessing_online_resources.md)
```

**Format**: Markdown links with relative paths starting with `./`

**Benefit**: Claude can follow links to load additional context when specific details are needed, without loading everything upfront.

---

## Creating New Reference Files

When adding new reference documentation to the skill:

### 1. Determine Scope

**Main SKILL.md**: Core principles and workflows (<100 lines)

**Reference File**: Detailed patterns, examples, checklists (50-200 lines each)

### 2. Structure the File

```markdown
# Reference Topic

## Overview
Brief description of what this covers

## When to Use
Specific situations where this reference applies

## Detailed Content
Core information organized under descriptive headings

## Examples
Concrete before/after patterns

## Related References
Links to other relevant files
```

### 3. Link from SKILL.md

Add reference link at appropriate point in main skill:

```markdown
For detailed compression techniques, see [compression-patterns.md](./references/compression-patterns.md).
```

### 4. Update Plugin Documentation

Add entry to this references.md file documenting the new reference.

---

## Reference File Guidelines

### Content Standards

**Specificity**: Provide concrete, actionable patterns (not vague guidance)

**Examples**: Include 3-5 diverse examples for complex patterns

**Motivation**: Explain WHY patterns work (not just what they are)

**Structure**: Use markdown headings to create clear sections

**Length**: Target 50-200 lines per file (split if larger)

### Formatting Standards

**Code Fences**: Always include language specifiers
```markdown
```yaml
---
example: yaml
---
```
```

**Links**: Use relative paths starting with `./`
```markdown
[Other Reference](./other-reference.md)
```

**Tables**: For structured comparisons
```markdown
| Pattern | Problem | Solution |
|---------|---------|----------|
```

**XML Tags**: For example boundaries
```markdown
<example>
concrete example here
</example>
```

### Citation Standards

**Sources**: Cite all external references with URLs and access dates

**Official Docs**: Prioritize Anthropic official documentation

**Community Practices**: Distinguish opinion from specification

**Example**:
```markdown
## Sources

- [Be clear and direct](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/be-clear-and-direct.md) (accessed 2026-01-15)
- [Claude 4.5 Release Notes](https://platform.claude.com/docs/en/about-claude/models/whats-new-claude-4-5.md) (accessed 2026-01-15)
```

---

## Maintenance

### When to Update References

**Model Updates**: When new Claude versions release, update whats-new-claude-4.5.md

**Best Practice Changes**: When Anthropic updates official guidelines, review and update affected references

**Community Feedback**: When users report unclear sections, clarify in reference files

**New Patterns**: When discovering new optimization patterns, add to appropriate reference or create new file

### Version Control

Reference files are part of the plugin and version-controlled with the skill:

```
plugins/prompt-optimization-claude-45/
├── .claude-plugin/
│   └── plugin.json (version: 1.0.0)
└── skills/
    └── prompt-optimization-claude-45/
        ├── SKILL.md
        ├── context-windows.md
        ├── whats-new-claude-4.5.md
        └── references/
            └── accessing_online_resources.md
```

When updating references, increment plugin version in plugin.json according to semantic versioning:
- **Major**: Breaking changes to skill behavior
- **Minor**: New reference files or significant additions
- **Patch**: Clarifications, fixes, minor updates

---

## Summary

Reference files provide detailed supporting documentation through progressive disclosure:

| File | Purpose | When to Use |
|------|---------|-------------|
| context-windows.md | Token budget management | Optimizing large CLAUDE.md files |
| whats-new-claude-4.5.md | Model-specific capabilities | Creating Claude 4.5 prompts |
| accessing_online_resources.md | Web resource verification | Documenting with citations |

This structure keeps the main SKILL.md concise (<100 lines) while providing deep information on demand through markdown links. Claude loads reference files progressively as needed, maintaining context efficiency.
