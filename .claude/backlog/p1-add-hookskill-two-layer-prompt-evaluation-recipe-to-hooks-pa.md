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
  last_synced: '2026-03-07T07:58:25Z'
  groomed: '2026-03-07'
  plan: plan/tasks-1-hooks-two-layer-pattern.md
---

## Fact-Check

Checked: 2026-03-07
Claims checked: 3
VERIFIED (3):
- UserPromptSubmit example exists at hooks-patterns/SKILL.md line 306
- hooks-core-reference/SKILL.md line 24 lists UserPromptSubmit with "Input validation" use case
- No two-layer/conditional Skill() invocation pattern exists in hooks-patterns or hooks-core-reference (grep confirmed)
REFUTED: 0 | INCONCLUSIVE: 0

## RT-ICA

RT-ICA: Add hook+skill two-layer prompt evaluation recipe to hooks-patterns
Goal: Document the hook→skill conditional invocation pattern so developers can implement two-layer prompt evaluation without reinventing it.
Conditions:
1. hooks-patterns/SKILL.md exists with UserPromptSubmit section | AVAILABLE | line 306 confirmed
2. Pattern is not yet documented | AVAILABLE | grep returned no two-layer/conditional Skill() hits
3. Source research material exists | AVAILABLE | research/prompt-engineering/claude-code-prompt-improver.md
4. additionalContext format known | AVAILABLE | hooks-core-reference line 332 confirms additionalContext flows to Claude's context
5. Token overhead measurement method | DERIVABLE | hook script size + context injection semantics
Decision: APPROVED
Missing: None

## Groomed (2026-03-07)

### Issue Classification

Type: procedural
Rationale: Adding documentation for a known, tested pattern. No defect or recurring failure. No root-cause analysis required.
Scenario target: Developer wants to implement hook-to-skill conditional invocation without researching the pattern from scratch.

### Priority

8/10 — The hook+skill two-layer pattern achieves 31% token reduction versus embedding evaluation logic directly in a hook. The pattern is already proven in production (severity1/claude-code-prompt-improver, 1,198 GitHub stars) and fills a gap in hooks-patterns/SKILL.md where only the flat UserPromptSubmit example exists. Plugin authors discovering this pattern independently will duplicate it suboptimally without the recipe.

### Impact

- Blocks: Plugin authors who want prompt quality control without paying per-prompt token overhead currently have no reference pattern. They either embed heavy logic in the hook (wasteful) or skip the pattern entirely.
- Bottleneck: The hooks-patterns/SKILL.md is the canonical recipe reference for hook implementations. Missing patterns here cause duplication or sub-optimal implementations across the plugin ecosystem.

### Scope

Single file modification: `plugins/plugin-creator/skills/hooks-patterns/SKILL.md`.

The new recipe must document three things derived from the research source (`research/prompt-engineering/claude-code-prompt-improver.md`):

1. Hook layer — reads stdin JSON `{"prompt": "..."}`, checks bypass prefixes (`*` skip evaluation, `/` slash commands, `#` memorize), outputs `additionalContext` via `hookSpecificOutput` JSON instructing Claude to call `Skill()` only when the prompt is evaluated as vague.
2. Token overhead documentation — clear prompts incur ~189 tokens (evaluation prompt only); vague prompts incur ~189 tokens + skill load. The v0.4.0 architecture achieves 31% token reduction versus embedding evaluation logic in the hook directly (~86 tokens saved per prompt; ~5.7k tokens per 30-message session vs ~8.3k previously).
3. Bypass prefix handling — `*` prefix strips the character and passes the cleaned prompt; `/` and `#` prefixes pass through unchanged with no evaluation.

The existing UserPromptSubmit example at line 306 (security pattern matching + additionalContext) is the anchor point. The new recipe follows that example as a more advanced variant showing the hook-delegates-to-skill pattern.

Out of scope: creating the skill itself, modifying any other file, adding hooks.json configuration examples.

### Acceptance Criteria

1. `plugins/plugin-creator/skills/hooks-patterns/SKILL.md` contains a new named recipe section for the hook+skill two-layer evaluation pattern, positioned after the existing "Python: UserPromptSubmit Context and Validation" example (line 306 area).
2. The recipe includes a Python code example showing: stdin JSON parse, bypass prefix check for `*`/`/`/`#`, and `hookSpecificOutput` JSON output with `additionalContext` that conditionally instructs Claude to call `Skill()` only when vague.
3. The recipe documents token overhead figures: ~189 tokens per clear prompt (evaluation only), ~189 tokens + skill load per vague prompt, and the 31% reduction versus embedded evaluation logic.
4. The recipe documents all three bypass prefix behaviors with examples matching the source: `*` strips prefix and skips evaluation, `/` and `#` pass through unchanged.
5. `uv run prek run --files plugins/plugin-creator/skills/hooks-patterns/SKILL.md` exits 0 (no lint errors introduced).
6. `uv run plugins/plugin-creator/scripts/plugin_validator.py plugins/plugin-creator/skills/hooks-patterns` exits without SK007 (token error threshold not breached by the addition — if SK006 triggers, the recipe must be extracted to a reference file instead).

### Resources

| Type | Item |
|------|------|
| Research source | `/home/ubuntulinuxqa2/repos/claude_skills/research/prompt-engineering/claude-code-prompt-improver.md` — full architecture, token metrics, bypass prefix behaviors, code structure |
| Target file | `plugins/plugin-creator/skills/hooks-patterns/SKILL.md` — existing UserPromptSubmit example at line 306 is the insertion anchor |
| Reference | `plugins/plugin-creator/skills/hooks-core-reference/SKILL.md` line 332 — confirms `additionalContext` flows to Claude's context window |
| External repo | `https://github.com/severity1/claude-code-prompt-improver` (v0.5.1, MIT) — production implementation the recipe documents |
| Validator | `plugins/plugin-creator/scripts/plugin_validator.py` — run after edit to check SK006/SK007 token thresholds |

### Dependencies

- Depends on: None. Research source is already written. Target file exists.
- Blocks: None identified in backlog.

### Effort

Small — single file edit, all source material pre-verified. Primary constraint is the SK006/SK007 token threshold check: if the recipe addition pushes hooks-patterns/SKILL.md over the warning threshold, the recipe must be written to a new reference file instead and linked from SKILL.md, which adds one additional file creation step.