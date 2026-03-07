# Feature Context: UserPromptSubmit Conditional Skill Invocation (Two-Layer Pattern)

## Document Metadata

- **Generated**: 2026-03-07
- **Input Type**: simple_description
- **Source**: Add a "UserPromptSubmit: Conditional Skill Invocation (Two-Layer Pattern)" recipe section to plugins/plugin-creator/skills/hooks-patterns/SKILL.md
- **Status**: DISCOVERY_COMPLETE

---

## Original Request

Add a "UserPromptSubmit: Conditional Skill Invocation (Two-Layer Pattern)" recipe section to
`plugins/plugin-creator/skills/hooks-patterns/SKILL.md`.

Key sources:
- `research/prompt-engineering/claude-code-prompt-improver.md` — primary pattern source
- `plugins/plugin-creator/skills/hooks-patterns/SKILL.md` — target file (line 306 is the insertion neighbourhood)
- `plugins/plugin-creator/skills/hooks-core-reference/SKILL.md` — additionalContext format (line 332)

---

## Core Intent Analysis

### WHO (Target Users)

Plugin developers reading `hooks-patterns` who want to build `UserPromptSubmit` hooks that
conditionally invoke a skill instead of applying a single fixed transformation to every prompt.

### WHAT (Desired Outcome)

A concrete, copy-pasteable recipe section in `hooks-patterns/SKILL.md` that teaches the
two-layer architectural pattern: a lightweight hook script evaluates the prompt, then either
proceeds immediately (cheap path) or invokes a skill (expensive path). The recipe must show
both layers working together — not just one in isolation.

### WHEN (Trigger Conditions)

A developer is building a `UserPromptSubmit` hook that:
- Needs conditional logic (not every prompt needs the same treatment)
- Wants to invoke a skill only for qualifying prompts
- Cares about token efficiency (avoiding skill overhead for the common case)

### WHY (Problem Being Solved)

The existing `hooks-patterns/SKILL.md` has a `UserPromptSubmit` code example at line 306
that shows context injection and blocking — but it treats the hook as a single-layer script.
It does not show the pattern where the hook's `additionalContext` instructs Claude to
conditionally invoke a skill. Plugin developers have no documented recipe for this architecture,
which is validated by the `claude-code-prompt-improver` open-source plugin (1,198 stars as of
2026-03-07) and achieves 31% token reduction over embedding all logic in the hook.

---

## Codebase Research

### Similar Patterns Found

#### Pattern 1: Existing UserPromptSubmit code example

- **Location**: `plugins/plugin-creator/skills/hooks-patterns/SKILL.md:306-351`
- **Relevance**: The insertion point. The existing Python example reads stdin JSON, checks
  for sensitive patterns (exit-code or JSON `decision: block`), then injects `additionalContext`
  via plain stdout or the JSON envelope. The new recipe section follows this section.
- **Reusable**: The JSON envelope structure (`hookSpecificOutput.additionalContext`) shown
  in the commented-out block at lines 342-348 is the exact mechanism the two-layer pattern uses.

#### Pattern 2: hooks-core-reference additionalContext output table

- **Location**: `plugins/plugin-creator/skills/hooks-core-reference/SKILL.md:330-334`
- **Relevance**: Confirms that `UserPromptSubmit` stdout is "Added to Claude's context" — this
  is the mechanism that makes the two-layer pattern work. The hook does not run the skill; it
  instructs Claude to run the skill via context injection.
- **Reusable**: The table row is citable in the new recipe section to explain why
  `additionalContext` reaches Claude.

#### Pattern 3: prompt-improver two-layer architecture

- **Location**: `research/prompt-engineering/claude-code-prompt-improver.md:30-79`
- **Relevance**: Complete working reference implementation. Hook layer (~70 lines Python) wraps
  prompt with evaluation instructions and outputs `{"hookSpecificOutput": {"hookEventName":
  "UserPromptSubmit", "additionalContext": "..."}}`. Skill layer invoked only when hook
  evaluation finds prompt vague. Bypass prefixes (`*`, `/`, `#`) handled in hook, not skill.
- **Reusable**: Architecture, bypass prefix pattern, token overhead measurements, and the
  four-phase skill workflow (Research → Questions → Clarify → Execute) are all documentable
  as recipe content.

### Existing Infrastructure

The target file `hooks-patterns/SKILL.md` already has:
- A `## Prompt-Based Hooks` section (lines 137-252) covering `type: prompt` LLM hooks
- A Python `UserPromptSubmit` code example section (lines 306-351) showing context injection
  and blocking via JSON output
- A `## Configuration Snippet Examples` section (lines 409-497) showing short JSON snippets

The new recipe section slots naturally after line 306's Python example. It is a distinct
pattern (conditional skill invocation via `additionalContext`) not currently represented.

### Code References

- `plugins/plugin-creator/skills/hooks-patterns/SKILL.md:306` — Python UserPromptSubmit
  example; insertion neighbourhood for the new recipe
- `plugins/plugin-creator/skills/hooks-patterns/SKILL.md:341-348` — commented-out JSON
  envelope block; the two-layer pattern uses the non-commented form of this output
- `plugins/plugin-creator/skills/hooks-core-reference/SKILL.md:332` — stdout handling table;
  UserPromptSubmit stdout "Added to Claude's context"
- `research/prompt-engineering/claude-code-prompt-improver.md:40-44` — hook output JSON
  structure (`hookSpecificOutput.hookEventName.additionalContext`)
- `research/prompt-engineering/claude-code-prompt-improver.md:75-79` — token overhead data
  (clear path: ~189 tokens, vague path: 189 + skill load)

---

## Use Scenarios

### Scenario 1: Prompt clarity gating

**Actor**: Plugin developer building a prompt-improvement plugin
**Trigger**: They want prompts to be clarified before Claude executes them, but only when
genuinely vague — not on every prompt
**Goal**: Hook evaluates clarity, clear prompts get zero skill overhead, vague prompts get
research-grounded clarifying questions
**Expected Outcome**: Recipe shows a hook script that wraps the prompt with evaluation
instructions and outputs `additionalContext` instructing Claude to invoke a skill only when
vague. Includes the skill-side contract (assumes evaluation already done).

### Scenario 2: Context-conditional enrichment

**Actor**: Plugin developer building a project-context injector
**Trigger**: Some prompts benefit from injected context (e.g., "what changed recently?") while
others do not (e.g., "fix TypeError at line 42")
**Goal**: Hook detects prompt type and conditionally instructs Claude to invoke an enrichment
skill
**Expected Outcome**: Recipe provides a generalizable pattern — hook = lightweight classifier
+ additionalContext emitter; skill = heavy logic loaded only when needed.

### Scenario 3: Bypass prefix pattern

**Actor**: Developer who wants users to be able to opt out of hook evaluation
**Trigger**: User prefixes prompt with `*` to skip processing
**Goal**: Hook strips prefix and passes prompt through unchanged
**Expected Outcome**: Recipe shows bypass prefix handling as a best practice alongside the
two-layer architecture.

---

## Gap Analysis

### Identified Gaps

| # | Category | Gap Description | Impact |
|---|----------|-----------------|--------|
| 1 | Scope | The request says "add a recipe section" but does not specify exactly where in the file to insert it — before or after the existing Python example at line 306, or as a new `##` section at the end of `## Code Examples` | Recipe could land in the wrong location within the file, breaking the narrative flow |
| 2 | Behavior | The recipe must include a Python hook script example. The primary source shows ~70 lines. No guidance on whether the recipe should show the full script, an abbreviated version, or a structural skeleton | Recipe may be too long (token pressure on skill) or too short (not useful) |
| 3 | Behavior | No specification on whether the recipe should include the skill-side example (SKILL.md frontmatter + body stub) or only the hook-side script | Recipe teaches half the pattern if skill-side is omitted |
| 4 | Scope | Bypass prefix handling (`*`, `/`, `#`) is present in the reference implementation but not mentioned in the feature request. Unclear if the recipe should include it | Omitting bypass makes the recipe incomplete for real-world use; including it expands scope |
| 5 | Integration | The existing `## Code Examples` section header at line 255 groups Python and Node.js examples. The new recipe is architecturally distinct (two-layer pattern, not a single hook). Unclear if it belongs inside that section or as a new top-level `##` section | Placement affects how developers discover the pattern |
| 6 | Behavior | The `additionalContext` can be emitted as plain stdout or as the full JSON envelope. The existing example shows both (plain stdout used, JSON commented out). The two-layer recipe should clarify which form is canonical for conditional skill invocation | Developer confusion if the recipe uses a different form than the adjacent example |

---

## Questions Requiring Resolution

### Q1: Insertion location within the file

- **Category**: Integration
- **Gap**: The request says "especially line 306" but does not specify before/after or whether
  the recipe is a new `###` subsection under `## Code Examples` or a new `##` section
- **Question**: Should the two-layer pattern recipe be added as a new `### Python: UserPromptSubmit
  Conditional Skill Invocation (Two-Layer Pattern)` subsection immediately after the existing
  Python UserPromptSubmit example at line 306, or as a standalone `## UserPromptSubmit:
  Conditional Skill Invocation` section at a different location in the file?
- **Options**:
  - A) New `###` subsection inside `## Code Examples`, after line 351
  - B) New standalone `##` section after `## Code Examples` and before `## Configuration Snippet Examples`
  - C) New standalone `##` section at the end of the file, before `## Sources`
- **Why It Matters**: Determines surrounding context and section heading level in the diff
- **Resolution**: _pending_

### Q2: Hook script completeness

- **Category**: Behavior
- **Gap**: The reference implementation hook is ~70 lines. No guidance on full vs. abbreviated
- **Question**: Should the recipe hook script example be (A) the full ~70-line script mirroring
  the prompt-improver implementation, (B) an abbreviated ~30-line version showing the essential
  structure, or (C) a structural skeleton with comments marking omitted sections?
- **Options**:
  - A) Full script (~70 lines)
  - B) Abbreviated functional version (~30 lines)
  - C) Skeleton with placeholder comments
- **Why It Matters**: Full scripts are copy-pasteable but add token weight to the skill; skeletons
  are lighter but require developers to fill in logic
- **Resolution**: _pending_

### Q3: Include skill-side content

- **Category**: Scope
- **Gap**: The "two-layer pattern" requires both a hook script and a skill. The request names
  the hook layer but is silent on whether to show the skill layer
- **Question**: Should the recipe section include a SKILL.md frontmatter stub and body outline
  showing what the invoked skill must assume and do, or only the hook-side Python script?
- **Options**:
  - A) Hook script only
  - B) Hook script + skill SKILL.md stub (frontmatter + abbreviated body)
- **Why It Matters**: Without the skill-side stub, developers must infer the skill contract from
  the hook's `additionalContext` text — a gap that causes implementation errors
- **Resolution**: _pending_

### Q4: Include bypass prefix pattern

- **Category**: Scope
- **Gap**: Bypass prefixes (`*` for skip, `/` for slash commands, `#` for memorize) are in
  the reference implementation but unmentioned in the request
- **Question**: Should bypass prefix handling be included in the recipe's hook script example,
  or documented only as a "Best Practices" note, or omitted entirely?
- **Options**:
  - A) Include in the hook script code
  - B) Include as a "Best Practice" callout after the code
  - C) Omit — out of scope for this recipe
- **Why It Matters**: Bypass enables user override; without it, the hook cannot be safely
  disabled on a per-prompt basis
- **Resolution**: _pending_

### Q5: Plain stdout vs. JSON envelope for additionalContext

- **Category**: Behavior
- **Gap**: The existing example at lines 339-348 shows plain stdout as the primary form and
  JSON envelope as a comment. The two-layer pattern relies on `hookSpecificOutput.additionalContext`
  for structured conditional instructions. Unclear which form the recipe should use as canonical
- **Question**: Should the recipe demonstrate `additionalContext` via (A) plain stdout string,
  (B) the full JSON envelope `{"hookSpecificOutput": {"hookEventName": "UserPromptSubmit",
  "additionalContext": "..."}}`, or (C) both with explanation of when each applies?
- **Options**:
  - A) Plain stdout only
  - B) JSON envelope only
  - C) Both with explanation
- **Why It Matters**: The JSON envelope is required when the hook also needs to emit a `decision`
  or other fields; plain stdout is sufficient for context-only injection. The recipe must not
  contradict the adjacent existing example
- **Resolution**: _pending_

---

## Goals (Pending Resolution)

_These goals will be finalized after questions Q1–Q5 are resolved._

1. Add a recipe section to `hooks-patterns/SKILL.md` at the location determined by Q1 that
   demonstrates the two-layer `UserPromptSubmit` pattern
2. The recipe hook script must show: reading stdin JSON, evaluating the prompt, emitting
   `additionalContext` that either proceeds immediately or instructs Claude to invoke a skill
3. The recipe must cite the token efficiency data from the reference implementation
   (~189 tokens overhead for clear prompts; skill overhead incurred only for qualifying prompts)
4. The recipe must be consistent with the `additionalContext` output form documented in
   `hooks-core-reference/SKILL.md:332` and the JSON envelope shown at `hooks-patterns/SKILL.md:342-348`
5. If Q3 resolves to include the skill-side stub, document the skill contract: what the skill
   assumes has been evaluated by the hook and what it must not re-evaluate

---

## Next Steps

After questions are resolved:

1. Update "Resolution" fields in Questions section above
2. Finalize Goals section
3. Proceed to RT-ICA assessment
4. Then proceed to architecture/design for the exact diff against `hooks-patterns/SKILL.md`
