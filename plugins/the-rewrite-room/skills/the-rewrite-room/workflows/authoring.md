---
workflow: authoring
canonical_skill: prompt-optimization-claude-45
canonical_path: plugins/prompt-optimization-claude-45/skills/prompt-optimization-claude-45/SKILL.md
version: "1.0"
output_contract: status-block-v1
---

# Authoring Workflow

## Purpose

Audience-appropriate rewriting for human-facing content. Applies tone, style, structure, and clarity transformations. Converts prohibition-heavy text to positive directives. Compresses verbose content without information loss.

This workflow is for HUMAN-FACING content (README, user docs, release notes). For AI-facing content (CLAUDE.md, SKILL.md, agent definitions), route to prompt-optimization instead.

## Entrypoint Contract

### Required Inputs

- Source text or file path
- Target audience (human user, developer, technical writer)
- Transformation goal (improve clarity, reduce length, change tone, reframe prohibitions)

### Optional Inputs

- Target length (approximate)
- Style constraints (formal, conversational, technical)

## Steps

1. **Load prompt-optimization-claude-45 skill** — `Skill(command: "prompt-optimization-claude-45:prompt-optimization-claude-45")`
2. **Read source in full** — do not summarize before rewriting
3. **Apply transformation** — tone, structure, audience framing, positive directives
4. **Run prompt-structure-validator** — check that prohibitions have been converted to positive alternatives
5. **Produce output with diff** — show before/after for user review

## Validation Gates

- SOFT STOP — prohibition pattern remains without positive alternative: flag for review
- SOFT STOP — word count increased by more than 20%: flag for compression review
- NO HARD STOPS — authoring is advisory; user reviews and approves output

## Output Contract

```text
STATUS: DONE|BLOCKED|FAILED
SUMMARY: [what was rewritten and key changes made]
ARTIFACTS:
  - path/to/rewritten-file.md
VALIDATION:
  - prompt-structure-validator: PASS|FAIL
NOTES: [only if needed]
```

## Disambiguation

If the source is a CLAUDE.md, SKILL.md, or agent definition file, this task belongs in the prompt-optimization workflow, not authoring. Authoring applies to human-readable documentation — README files, user guides, release notes, API reference prose.

If uncertain, ask the user: "Is this content read by humans (authoring) or by the AI model (prompt-optimization)?"
