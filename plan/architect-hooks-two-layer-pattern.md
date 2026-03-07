# Architecture: UserPromptSubmit Conditional Skill Invocation (Two-Layer Pattern)

## Target File and Insertion Point

**File:** `plugins/plugin-creator/skills/hooks-patterns/SKILL.md`

**Insert after:** Line 351 (closing triple-backtick of `### Python: UserPromptSubmit Context and
Validation (JSON Output)`)

**Insert before:** Line 353 (`### Python: PreToolUse Auto-Approval (JSON Output)`)

**Section heading level:** `###` — matches all adjacent subsections inside `## Code Examples`

**Exact old_string anchor for Edit tool:**

```text
sys.exit(0)
```

Use the closing block of the existing UserPromptSubmit example as anchor:

```
sys.exit(0)
```

followed by the closing triple-backtick and blank line, then the `### Python: PreToolUse
Auto-Approval` heading. The Edit will insert the new section between those two headings.

---

## Section Header

```text
### Python: UserPromptSubmit Conditional Skill Invocation (Two-Layer Pattern)
```

---

## Section Structure

The section contains five elements in this order:

1. One-paragraph description of the two-layer pattern
2. Token overhead callout (inline, not a separate heading)
3. Hook script code block (Python, ~30 lines, abbreviated)
4. Hook configuration snippet (JSON)
5. Skill contract note (prose only — no SKILL.md stub)

---

## Token Overhead Documentation Format

Placed as a blockquote immediately before the code block. Cites the reference implementation
data from `research/prompt-engineering/claude-code-prompt-improver.md:75-79` and
`hooks-core-reference/SKILL.md:332`.

Format:

```text
> **Token overhead:** Clear prompts — ~189 tokens (evaluation wrapper only).
> Vague prompts — 189 tokens + skill load. ~31% reduction vs. embedding evaluation
> logic in the hook directly (prompt-improver v0.4.0, 2026-02-14).
```

---

## Hook Script Code Example

### Design Constraints

- Language: Python 3
- Length: approximately 30 lines (abbreviated from the ~70-line reference)
- Shows: stdin JSON read, bypass prefix handling, evaluation wrapper construction,
  JSON envelope output
- Omits: the full evaluation instruction text (replaced with a comment placeholder)
- Bypass prefix handling: present in code with inline comment — not in a separate note

### Code Structure (pseudo-specification for implementation agent)

The script must demonstrate these elements in this order:

```
[shebang + imports: json, sys]

[read stdin JSON; extract "prompt" field]

[bypass block]
  — if prompt starts with "*": strip prefix, print plain prompt string, exit 0
  — if prompt starts with "/" or "#": print plain prompt string, exit 0
  — comment: "# bypass: strip * prefix and skip evaluation"
  — comment: "# bypass: slash commands and memorize pass through unchanged"

[build evaluation_context string]
  — f-string wrapping original_prompt
  — comment: "# ~189 tokens; instructs Claude to evaluate clarity,
  #  invoke skill only when vague"
  — the string body is abbreviated: first line + "..." + last line
  — the abbreviated form must show the conditional skill invocation instruction:
    something like "If vague: use Skill(skill='your-plugin:your-skill')"

[output JSON envelope]
  output = {
    "hookSpecificOutput": {
      "hookEventName": "UserPromptSubmit",
      "additionalContext": evaluation_context,
    }
  }
  print(json.dumps(output))
  sys.exit(0)
```

### JSON Output Form

Use the full JSON envelope (`hookSpecificOutput.hookEventName.additionalContext`) — not plain
stdout. Rationale: the two-layer pattern relies on structured output to keep the
`additionalContext` channel distinct from any potential future `decision` field. This matches
the `hooks-core-reference/SKILL.md:332` table ("Added to Claude's context") and is consistent
with the commented-out block at `hooks-patterns/SKILL.md:342-348` now used in its uncommented
form.

---

## Hook Configuration Snippet

A JSON snippet showing the hooks.json entry for the hook script. Matches the pattern used in
`## Configuration Snippet Examples` but placed inline in the recipe rather than in that section.

Format:

```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python3 /path/to/your-hook.py"
          }
        ]
      }
    ]
  }
}
```

---

## Skill Contract Note

Prose only — no SKILL.md stub. One short paragraph after the configuration snippet stating:

- The invoked skill must assume the hook has already evaluated the prompt
- The skill must not re-evaluate clarity
- The skill should proceed directly to its task (e.g., research, questions, enrichment)
- This prevents double-evaluation overhead and is the defining contract of the two-layer pattern

This satisfies the "skill-side" documentation requirement without adding a SKILL.md stub that
would expand scope and add token weight to the skill.

---

## Acceptance Criteria

The implementation agent verifies each criterion before marking the task complete.

### AC-1: Insertion location

- [ ] New section appears after the closing ` ``` ` of `### Python: UserPromptSubmit Context
  and Validation (JSON Output)` and before `### Python: PreToolUse Auto-Approval (JSON Output)`
- [ ] Section heading is `###` (not `##` or `####`)
- [ ] A blank line separates the new section from both neighbors

### AC-2: Section heading text

- [ ] Heading reads exactly: `### Python: UserPromptSubmit Conditional Skill Invocation
  (Two-Layer Pattern)`

### AC-3: Hook script

- [ ] Code block language specifier is `python`
- [ ] Script reads stdin with `json.load(sys.stdin)`
- [ ] Bypass prefix `*` is handled: prefix stripped, plain prompt printed, exit 0
- [ ] Bypass prefixes `/` and `#` are handled: prompt printed unchanged, exit 0
- [ ] Bypass logic includes inline comment identifying each bypass reason
- [ ] Evaluation wrapper is a string built around the original prompt
- [ ] A comment on or adjacent to the evaluation_context construction reads approximately:
  `# ~189 tokens; instructs Claude to evaluate clarity, invoke skill only when vague`
- [ ] The evaluation_context string shows a conditional skill invocation instruction
  (e.g., `Skill(skill='your-plugin:your-skill')`) even if abbreviated with `...`
- [ ] Output is the JSON envelope form:
  `{"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": ...}}`
- [ ] Script is approximately 30 lines (25-35 is acceptable)

### AC-4: Token overhead blockquote

- [ ] Blockquote present before the code block
- [ ] States ~189 tokens for clear prompts
- [ ] States ~31% reduction vs. embedding evaluation logic directly
- [ ] Cites prompt-improver v0.4.0 and date 2026-02-14

### AC-5: Hook configuration snippet

- [ ] JSON snippet present after the code block
- [ ] Shows `UserPromptSubmit` event key
- [ ] Shows `type: command` hook entry
- [ ] Code block language specifier is `json`

### AC-6: Skill contract note

- [ ] Prose paragraph present after the configuration snippet
- [ ] States the skill must not re-evaluate clarity
- [ ] States the skill should proceed directly to its task

### AC-7: Consistency with adjacent examples

- [ ] JSON envelope structure matches the commented-out block at lines 342-348 of the
  target file (same key names: `hookSpecificOutput`, `hookEventName`, `additionalContext`)
- [ ] No plain stdout used for `additionalContext` in this recipe
- [ ] No contradiction of the `hooks-core-reference/SKILL.md:332` stdout handling table

### AC-8: Formatting

- [ ] Blank line before and after every fenced code block (MD031 compliance)
- [ ] All code blocks have language specifiers
- [ ] No markdown tables in the inserted section

### AC-9: Validator pass

- [ ] `uv run plugins/plugin-creator/scripts/plugin_validator.py
  plugins/plugin-creator/skills/hooks-patterns/` exits with no SK007 errors after insertion

---

## Source Citations

- `research/prompt-engineering/claude-code-prompt-improver.md:30-79` — architecture,
  bypass prefixes, JSON output structure, token overhead data
- `research/prompt-engineering/claude-code-prompt-improver.md:75-79` — token overhead
  numbers (189 tokens, 31% reduction)
- `plugins/plugin-creator/skills/hooks-patterns/SKILL.md:306-351` — existing
  UserPromptSubmit example; JSON envelope comment at lines 342-348
- `plugins/plugin-creator/skills/hooks-core-reference/SKILL.md:330-334` — stdout
  handling table confirming UserPromptSubmit stdout "Added to Claude's context"
- `plan/feature-context-hooks-two-layer-pattern.md` — resolved design questions (Q1-Q5)
