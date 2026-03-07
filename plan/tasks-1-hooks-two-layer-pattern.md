---
description: "Add two-layer UserPromptSubmit recipe section to hooks-patterns SKILL.md"
version: "1.0"
feature_slug: "hooks-two-layer-pattern"
architecture_doc: "plan/architect-hooks-two-layer-pattern.md"
feature_context: "plan/feature-context-hooks-two-layer-pattern.md"
tasks:
  - T1: "Write two-layer pattern recipe section into hooks-patterns/SKILL.md"
  - T2: "Validate insertion — linting, plugin validator, structural checks"
task_exports:
  enabled: false
  directory: "TASK"
---

# Tasks: UserPromptSubmit Conditional Skill Invocation (Two-Layer Pattern)

## Context Manifest

- Architecture spec: [plan/architect-hooks-two-layer-pattern.md](./architect-hooks-two-layer-pattern.md)
- Feature context: [plan/feature-context-hooks-two-layer-pattern.md](./feature-context-hooks-two-layer-pattern.md)
- Target file: `plugins/plugin-creator/skills/hooks-patterns/SKILL.md`
- Insertion point: after line 351 (close of existing UserPromptSubmit example code fence)
- Pattern source: `research/prompt-engineering/claude-code-prompt-improver.md`
- Reference: `plugins/plugin-creator/skills/hooks-core-reference/SKILL.md`
- Key constraint: addition must stay under SK006/SK007 token threshold; extract to reference file if needed

---

## Priority 1 (Foundational)

---

### Task T1: Write two-layer pattern recipe section into hooks-patterns/SKILL.md

```yaml
task: T1
title: "Write two-layer pattern recipe section into hooks-patterns/SKILL.md"
status: not-started
agent: plugin-creator:contextual-ai-documentation-optimizer
dependencies: []
priority: 1
complexity: medium
accuracy-risk: medium
skills: ["plugin-creator:skill-creator"]
parallelize-with: []
reason: "Single task in priority 1; T2 depends on T1 output"
handoff: "Report: inserted section line range, word count, any deviations from architecture spec"
```

#### Context

This task inserts a new recipe section into an existing SKILL.md file. The architecture spec
(`plan/architect-hooks-two-layer-pattern.md`) defines the exact insertion point, section structure,
code examples, and acceptance criteria. The feature context
(`plan/feature-context-hooks-two-layer-pattern.md`) provides background on the two-layer pattern
and its source material.

The target file already has a `### Python: UserPromptSubmit Context and Validation (JSON Output)`
section ending at line 351. The new section inserts after that closing code fence and before
`### Python: PreToolUse Auto-Approval (JSON Output)` at line 353.

#### Objective

Insert a `### Python: UserPromptSubmit Conditional Skill Invocation (Two-Layer Pattern)` section
into `plugins/plugin-creator/skills/hooks-patterns/SKILL.md` that teaches the two-layer hook
architecture with a working code example, configuration snippet, and skill contract note.

#### Inputs

- `plan/architect-hooks-two-layer-pattern.md` — section structure, code pseudo-spec, acceptance
  criteria AC-1 through AC-8
- `plan/feature-context-hooks-two-layer-pattern.md` — pattern rationale, use scenarios, source
  citations
- `plugins/plugin-creator/skills/hooks-patterns/SKILL.md` — target file (read before editing)
- `research/prompt-engineering/claude-code-prompt-improver.md:30-79` — reference implementation
  for hook architecture, bypass prefixes, token overhead data
- `plugins/plugin-creator/skills/hooks-core-reference/SKILL.md:330-334` — stdout handling table
  confirming `additionalContext` mechanism

#### Requirements

1. Read the target file to identify the exact insertion point (after the closing code fence of
   the existing UserPromptSubmit example, before the PreToolUse heading)
2. Insert a new `###` section with the heading:
   `### Python: UserPromptSubmit Conditional Skill Invocation (Two-Layer Pattern)`
3. Include a token overhead blockquote before the code block stating ~189 tokens for clear
   prompts, ~31% reduction, citing prompt-improver v0.4.0 (2026-02-14)
4. Include an abbreviated Python hook script (~30 lines, 25-35 acceptable) that demonstrates:
   - Reading stdin JSON and extracting the `prompt` field
   - Bypass prefix handling: `*` (strip and skip), `/` and `#` (pass through unchanged)
   - Building an evaluation_context string wrapping the original prompt
   - A comment noting `~189 tokens; instructs Claude to evaluate clarity, invoke skill only when vague`
   - The evaluation_context showing a conditional `Skill(skill='your-plugin:your-skill')` invocation
   - Output via JSON envelope: `{"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": ...}}`
5. Include a JSON configuration snippet showing the `hooks.json` entry for the hook
6. Include a skill contract note (prose paragraph) stating:
   - The invoked skill must assume the hook already evaluated the prompt
   - The skill must not re-evaluate clarity
   - The skill should proceed directly to its task

#### Constraints

- Do not modify any existing content in the target file — insert only
- Do not use markdown tables in the inserted section
- Do not use plain stdout for `additionalContext` output — use JSON envelope only
- Do not include a SKILL.md stub for the skill side — prose note only
- All code blocks must have language specifiers (`python`, `json`)
- Blank lines before and after every fenced code block (MD031)
- JSON envelope key names must match the existing commented-out block at lines 342-348:
  `hookSpecificOutput`, `hookEventName`, `additionalContext`

#### Expected Outputs

- Modified file: `plugins/plugin-creator/skills/hooks-patterns/SKILL.md`

#### Acceptance Criteria

1. New section appears after the closing code fence of `### Python: UserPromptSubmit Context and
   Validation (JSON Output)` and before `### Python: PreToolUse Auto-Approval (JSON Output)`
2. Section heading is exactly `### Python: UserPromptSubmit Conditional Skill Invocation (Two-Layer Pattern)`
3. Token overhead blockquote is present before the code block, states ~189 tokens, ~31% reduction,
   cites prompt-improver v0.4.0 (2026-02-14)
4. Python code block reads stdin with `json.load(sys.stdin)`, handles bypass prefixes (`*`, `/`, `#`),
   builds evaluation_context, outputs JSON envelope
5. Python code block is 25-35 lines
6. JSON configuration snippet present after the code block with `UserPromptSubmit` event and
   `type: command` hook entry
7. Skill contract prose paragraph present after configuration snippet, states skill must not
   re-evaluate clarity and should proceed directly
8. Blank lines surround every fenced code block; all code blocks have language specifiers
9. No markdown tables in the inserted section
10. JSON envelope key names match `hookSpecificOutput`, `hookEventName`, `additionalContext`

#### Verification Steps

1. Read the modified file and confirm the new section is between the two expected neighbor sections
2. Count lines in the Python code block — must be 25-35
3. Search the inserted section for the string `json.load(sys.stdin)` — must be present
4. Search for `hookSpecificOutput` in the new section — must appear in both the Python code and
   the JSON config snippet
5. Confirm no `|` table syntax exists in the inserted section
6. Confirm blank lines before and after every code fence in the inserted section

#### CoVe Checks

- Key claims to verify:
  - The token overhead figure is ~189 tokens for clear prompts
  - The reduction figure is ~31% vs. embedding evaluation logic directly
  - The version cited is prompt-improver v0.4.0 dated 2026-02-14
  - `additionalContext` in `UserPromptSubmit` stdout is "Added to Claude's context"
- Verification questions:
  1. Does `research/prompt-engineering/claude-code-prompt-improver.md:75-79` state 189 tokens
     and 31% reduction?
  2. Does `research/prompt-engineering/claude-code-prompt-improver.md` reference v0.4.0 and
     2026-02-14?
  3. Does `plugins/plugin-creator/skills/hooks-core-reference/SKILL.md:332` confirm
     UserPromptSubmit stdout is added to Claude's context?
  4. Do the JSON envelope key names in the existing commented block at lines 342-348 of the
     target file match `hookSpecificOutput`, `hookEventName`, `additionalContext`?
- Evidence to collect:
  - Quote the relevant lines from each source file before writing the recipe
  - If any number or version does not match, use the value from the source file
- Revision rule:
  - If any check fails, update the recipe content to match the primary source and note what changed

#### Handoff

Return:
- Line range of the inserted section in the modified file
- Word count of the inserted content
- Any deviations from the architecture spec and why
- Evidence from CoVe checks (quoted source lines for token data and version)

---

## Priority 2 (Validation — depends on T1)

---

### Task T2: Validate insertion — linting, plugin validator, structural checks

```yaml
task: T2
title: "Validate insertion — linting, plugin validator, structural checks"
status: not-started
agent: plugin-creator:contextual-ai-documentation-optimizer
dependencies: ["T1"]
priority: 2
complexity: low
accuracy-risk: low
skills: ["plugin-creator:skill-creator"]
parallelize-with: []
reason: "Depends on T1 completing the file edit"
handoff: "Report: all validation results (pass/fail per check), any fixes applied"
```

#### Context

T1 inserted a new recipe section into `plugins/plugin-creator/skills/hooks-patterns/SKILL.md`.
This task validates the insertion meets formatting, linting, and plugin validator requirements.

#### Objective

Confirm the modified `hooks-patterns/SKILL.md` passes all linting and validation checks, and
fix any issues found.

#### Inputs

- Modified file: `plugins/plugin-creator/skills/hooks-patterns/SKILL.md` (output of T1)
- Architecture spec acceptance criteria AC-1 through AC-9:
  `plan/architect-hooks-two-layer-pattern.md`

#### Requirements

1. Run pre-commit linting on the modified file
2. Run the plugin validator on the hooks-patterns skill directory
3. Verify the section heading level is `###` (not `##` or `####`)
4. Verify no SK007 (token budget) errors from the plugin validator
5. If any check fails, fix the issue in the file and re-run the failing check

#### Constraints

- Do not modify content meaning when fixing formatting issues — preserve the recipe's
  technical accuracy
- Do not add or remove recipe content — only fix formatting and structural issues
- If a fix would change technical content, report it as a blocker instead of fixing

#### Expected Outputs

- Validated file: `plugins/plugin-creator/skills/hooks-patterns/SKILL.md` (possibly with
  minor formatting fixes)

#### Acceptance Criteria

1. `uv run prek run --files plugins/plugin-creator/skills/hooks-patterns/SKILL.md` exits 0
2. `uv run plugins/plugin-creator/scripts/plugin_validator.py plugins/plugin-creator/skills/hooks-patterns/`
   exits with no SK007 errors
3. The section heading `### Python: UserPromptSubmit Conditional Skill Invocation (Two-Layer Pattern)`
   is present and uses exactly three `#` characters
4. All code blocks in the inserted section have language specifiers
5. Blank lines exist before and after every fenced code block in the inserted section

#### Verification Steps

1. Run: `uv run prek run --files plugins/plugin-creator/skills/hooks-patterns/SKILL.md` —
   confirm exit code 0
2. Run: `uv run plugins/plugin-creator/scripts/plugin_validator.py plugins/plugin-creator/skills/hooks-patterns/` —
   confirm no SK007 in output
3. Search the file for `### Python: UserPromptSubmit Conditional Skill Invocation` — confirm
   exactly one match and it starts with `### ` (three hashes + space)
4. Read the inserted section and confirm every code fence opening has a language specifier
   immediately after the triple backticks
5. Read the inserted section and confirm blank lines before and after every code fence

#### Handoff

Return:
- Pass/fail result for each validation check
- If fixes were applied: what was changed and why
- If any check cannot pass: what is blocked and what is needed

---

## Sync Checkpoints

### SYNC CHECKPOINT 1: Post-T1 Review

- Convergence point: T1 output (modified SKILL.md)
- Quality gates:
  - New section exists at correct insertion point
  - Section contains all five elements (description, token callout, hook script, config snippet,
    skill contract note)
  - Code example is 25-35 lines
- Proceed to T2 after T1 acceptance criteria confirmed

### SYNC CHECKPOINT 2: Final Validation

- Convergence point: T2 output (validated SKILL.md)
- Quality gates:
  - Pre-commit linting passes
  - Plugin validator passes (no SK007)
  - All structural checks pass
- Reflection questions:
  - Does the recipe read naturally in context with the adjacent sections?
  - Are there any contradictions with the existing UserPromptSubmit example?
- Feature complete after T2 acceptance criteria confirmed
