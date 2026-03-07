---
name: Add hook+skill two-layer prompt evaluation recipe to hooks-patterns
description: "## Current state\n\nThe `hooks-patterns` SKILL.md contains a `UserPromptSubmit` example (line 306, 'Python: UserPromptSubmit Context and Validation') that demonstrates JSON output and context injection. However, this example only shows how to validate and add context to a prompt. It does not demonstrate the pattern of:\n1. Evaluating prompt clarity within the hook (lightweight, ~189 tokens)\n2. Conditionally invoking a skill only when the prompt is vague (via `additionalContext` instructing Claude to call `Skill()`)\n3. Providing bypass prefixes to skip evaluation entirely\n\nThe `hooks-core-reference` SKILL.md lists `UserPromptSubmit` as an event (line 24) with use case 'Input validation' but does not document the hook-to-skill conditional invocation pattern.\n\n## Target state\n\nThe `hooks-patterns` SKILL.md includes a new recipe section titled 'UserPromptSubmit: Conditional Skill Invocation (Two-Layer Pattern)' that demonstrates:\n1. A hook script that reads stdin JSON, checks for bypass prefixes (e.g., `*`, `/`), wraps the prompt with a clarity evaluation instruction, and outputs `additionalContext` that tells Claude to invoke a specific skill only if the prompt is vague\n2. The corresponding skill structure (SKILL.md with research and question-generation phases)\n3. Token overhead measurement: documenting the hook's token cost for the common case (clear prompts)\n\n## Measurable signal\n\n`hooks-patterns/SKILL.md` contains a section header matching 'Conditional Skill Invocation' or 'Two-Layer Pattern'. The section includes a code example showing `UserPromptSubmit` hook output with `additionalContext` that references `Skill()` invocation. The section documents bypass prefix handling."
metadata:
  topic: add-hookskill-two-layer-prompt-evaluation-recipe-to-hooks-pa
  source: 'Research entry: ./research/prompt-engineering/claude-code-prompt-improver.md -- pattern: hook-based architecture with two-layer evaluation'
  added: '2026-03-07'
  priority: P1
  type: Feature
  status: open
  issue: '#505'
  last_synced: '2026-03-07T06:32:40Z'
---