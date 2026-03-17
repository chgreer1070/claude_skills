# Delegation Guidance Improvement Plan

**Purpose**: Action plan for fixing systemic orchestrator anti-patterns across delegation guidance documents.
**Session**: 2026-02-17
**Implementer use**: Each fix is self-contained. Execute in priority order. No re-investigation required.

---

## Background

Two confirmed anti-patterns reproduce despite correct guidance existing in the codebase:

1. **Pre-reading**: The orchestrator reads files before delegating, then includes summaries of what it read in the delegation prompt. This wastes orchestrator context and duplicates work the sub-agent will do anyway.
2. **Micromanagement**: The orchestrator prescribes HOW to accomplish tasks rather than describing desired outcomes. Sub-agents are Senior Engineers; they own HOW.

A prior diagnostic session (contextual-ai-documentation-optimizer) identified 6 structural causes in the delegation template that cause the orchestrator to reproduce these anti-patterns despite reading correct guidance. Those findings are incorporated below.

---

## Scope Audited

| Location | What was examined |
|---|---|
| `plugins/agent-orchestration/skills/agent-orchestration/SKILL.md` | Full file (704 lines) |
| `plugins/agent-orchestration/skills/agent-orchestration/references/accessing_online_resources.md` | Full file |
| `plugins/agent-orchestration/skills/agent-orchestration/references/synthesis-improvements-from-research.md` | Full file |
| `plugins/python3-development/skills/python3-development/SKILL.md` | Full file (908 lines) |
| `plugins/python3-development/skills/python3-development/references/python-development-orchestration.md` | First 280 lines |
| `plugins/python3-development/agents/python-cli-architect.md` | Full file |
| `~/.claude/CLAUDE.md` | Delegation-relevant sections |

---

## Findings

### Finding 1 — Template Placeholder Creates Fill-In-the-Blank Reflex

**Source**: Prior diagnostic session (Cause 1)
**Location**: `plugins/agent-orchestration/skills/agent-orchestration/SKILL.md` lines 156-158

The delegation template ends with:

```text
AVAILABLE RESOURCES:
[See "Writing Effective AVAILABLE RESOURCES" section below for examples]
```

This placeholder triggers slot-filling behavior at generation time. The heading label `AVAILABLE RESOURCES` is a stronger generative signal than the distant guidance prose. The orchestrator sees the label and fills it with the first thing that comes to mind — which is a list of tool names — because that is the dominant pattern from training data.

**Fix**: Embed condensed correct guidance directly at the placeholder location. The forward-reference to a distant section gets skipped under cognitive load (see Finding 6).

---

### Finding 2 — Template Label Inverts Correct Behavior

**Source**: Prior diagnostic session (Cause 2)
**Location**: `plugins/agent-orchestration/skills/agent-orchestration/SKILL.md` lines 156-188

The section heading `AVAILABLE RESOURCES` primes enumeration of discrete resources (tools, files, URLs). The intended concept is "world-building context" — an ecosystem description that empowers the agent to discover the best approach.

The label and the instruction are in semantic conflict. The orchestrator follows the label, not the guidance prose that follows it.

**Fix**: Rename the template section and the explanation section heading from `AVAILABLE RESOURCES` to `ECOSYSTEM CONTEXT`.

---

### Finding 3 — Cognitive Load from Template Length Before Placeholder

**Source**: Prior diagnostic session (Cause 3)
**Location**: `plugins/agent-orchestration/skills/agent-orchestration/SKILL.md` lines 96-158

The delegation template contains 55+ lines of dense content before reaching the `AVAILABLE RESOURCES` placeholder. By the time the orchestrator reaches that placeholder, the guidance section is a distant reference. The dereference step ("see section below") gets skipped under active generation.

**Fix**: Add a minimal filled baseline directly in the template body. The template should not require dereferencing to another section in order to be used correctly.

---

### Finding 4 — Anti-Pattern Example Is More Concrete than Correct Example

**Source**: Prior diagnostic session (Cause 4)
**Location**: `plugins/agent-orchestration/skills/agent-orchestration/SKILL.md` lines 164-188 ("Writing Effective AVAILABLE RESOURCES")

The anti-pattern is structurally simple and universally applicable:

```text
AVAILABLE RESOURCES:
- WebFetch tool
- Read tool
- Bash tool
```

The correct pattern is project-specific and requires novel generation for each delegation context. This is a few-shot contamination problem: the anti-pattern wins on every generation because it is the easiest pattern to instantiate.

**Fix**: Move the detailed anti-pattern examples to a reference file. Keep a single minimal correct example in the main SKILL.md. The anti-pattern must not appear in the same generation context as the template.

---

### Finding 5 — CLAUDE.md Contains Conflicting Guidance

**Source**: Prior diagnostic session (Cause 5)
**Location**: `~/.claude/CLAUDE.md` (Pre-Delegation Protocol section) and `plugins/agent-orchestration/skills/agent-orchestration/SKILL.md` line 81

CLAUDE.md `Pre-Delegation Protocol` does not contain explicit anti-pre-gathering guidance in the delegation checklist items. The check items focus on reading the orchestration guide but do not state the prohibition on pre-reading files.

Additionally, SKILL.md line 81 states:

```text
- List available tools — never prescribe which tool to use
```

The word "list" normalizes tool enumeration despite the skill's own intent being "provide world-building context." The word "list" is the same generative signal that produces the anti-pattern. CLAUDE.md carries higher systemic weight than SKILL.md, so if CLAUDE.md does not contradict "listing tools," the behavior persists.

**Fix**: In SKILL.md line 81, replace "List available tools" with "Describe the ecosystem and available environment." In CLAUDE.md, add an explicit pre-delegation check: "Will the agent need to read these files anyway? If yes, do not pre-read — pass file paths, not summaries."

---

### Finding 6 — Guidance Is Structurally Inverted Relative to Point of Use

**Source**: Prior diagnostic session (Cause 6)
**Location**: `plugins/agent-orchestration/skills/agent-orchestration/SKILL.md` lines 156-188

The delegation template (generation target) contains a forward pointer. The guidance is in a separate section after the template. LLMs under active generation do not re-read earlier sections after filling a placeholder — the generation cursor moves forward.

This means the guidance for filling `AVAILABLE RESOURCES` is placed after the point where the orchestrator is already generating that section. The correction comes too late.

**Fix**: Guidance must be at or immediately adjacent to the point of use. The "Writing Effective AVAILABLE RESOURCES" section content must be collapsed into an inline note inside the template, or the template itself must contain a pre-filled example that is correct by default.

---

### Finding 7 — python3-development SKILL.md Has Pre-Read Instruction Framed as Required Step

**Location**: `plugins/python3-development/skills/python3-development/SKILL.md` lines 280-288 (Pre-Delegation Checklist)

The Pre-Delegation Checklist table contains:

```text
| 1 | Read orchestration guide | Read("${CLAUDE_PLUGIN_ROOT}/skills/python3-development/references/python-development-orchestration.md") |
```

This is correct — the orchestrator reads the guide to understand how to orchestrate. However, it creates a pattern of "reading before delegating" that can bleed into reading files that the agent should read itself. The checklist does not distinguish between "reading orchestration meta-guidance" (correct) and "reading the actual task codebase" (incorrect pre-gathering).

Separately, the Quick Reference Example at lines 379-402 shows:

```text
0. Read("${CLAUDE_PLUGIN_ROOT}/skills/python3-development/references/python-development-orchestration.md")
1. Delegate to @python3-development:python-cli-architect (FOCUSED SCOPE: implementation only)
   "Create CSV processing CLI with Typer+Rich progress bars. Scope: src/csv_tool.py only."
```

The scope statement "Scope: src/csv_tool.py only" tells the agent which files to touch. This is a prescription of HOW (specifically, which files to work in) rather than describing the desired outcome. The orchestrator should not scope agent discovery — only scope the task domain.

**Fix**: Add a note to the Pre-Delegation Checklist distinguishing orchestration guide reading (correct) from task codebase pre-reading (prohibited). Revise the Quick Reference Example to show outcome-scoped delegation, not file-scoped.

---

### Finding 8 — python-cli-architect Agent Instructs Pre-commit with Specific File List

**Location**: `plugins/python3-development/agents/python-cli-architect.md` line 219

```text
Use `uv run pre-commit run --files <file1>,<file2>,...` to run all the checks required to commit
```

This is within the agent's own behavior guidance (not the orchestrator's delegation), so it is not the same class of problem. However, the pattern of passing specific file lists (rather than letting the hook tool discover what changed) may reinforce the micromanagement reflex in orchestrators that read agent files as examples.

**Fix**: Note this as lower priority — acceptable within agent scope since the agent knows which files it just modified. No structural change required, but annotate that this pattern is agent-internal and should not be emulated in orchestrator delegation prompts.

---

### Finding 9 — python3-development Orchestration Guide Has Workflow Steps That Prescribe Agent Inputs

**Location**: `plugins/python3-development/skills/python3-development/references/python-development-orchestration.md` lines 48-95

Each workflow step specifies explicit `Input:` and `Output:` for every agent delegation:

```text
2. Write Tests → @python3-development:python-pytest-architect
   Input: Architecture design, expected behavior
   Output: Complete test suite (fails initially)

3. Implement → @python3-development:python-cli-architect
   Input: Tests, architecture design
   Output: Implementation that makes tests pass
```

Specifying `Input: Tests, architecture design` describes what context to pass through — that is correct. However, the pattern teaches the orchestrator that every delegation must specify inputs explicitly, which can lead to the orchestrator pre-gathering those inputs rather than letting the agent discover them.

The TDD Example at lines 74-95 shows:

```text
Step 3: @python3-development:python-cli-architect
  "Implement CSV processor CLI with Typer+Rich based on these tests"
```

The phrase "based on these tests" implies the orchestrator is passing test content. The agent should discover the test files, not receive summaries.

**Fix**: In workflow descriptions, change `Input:` labels to `Context to pass:` and add a note: "Pass file paths and outcomes — not file contents or summaries. Agents discover and read files themselves."

---

## Consolidated Fixes (Priority Ordered)

### Priority 1 — Rename AVAILABLE RESOURCES to ECOSYSTEM CONTEXT (Template + Section Heading)

**Impact**: Eliminates the primary generative signal that causes tool-list enumeration.
**Effort**: Trivial — rename label in template and in section heading.
**Files**:
- `plugins/agent-orchestration/skills/agent-orchestration/SKILL.md` line 156: change `AVAILABLE RESOURCES:` to `ECOSYSTEM CONTEXT:`
- `plugins/agent-orchestration/skills/agent-orchestration/SKILL.md` line 160: change section heading `## Writing Effective AVAILABLE RESOURCES` to `## Writing Effective ECOSYSTEM CONTEXT`
- Update all cross-references within the file.

**Before**:

```text
AVAILABLE RESOURCES:
[See "Writing Effective AVAILABLE RESOURCES" section below for examples]
```

**After**:

```text
ECOSYSTEM CONTEXT:
# Describe the ecosystem — not a tool list. Correct pattern:
# - "The `gh` CLI is pre-authenticated for GitHub operations"
# - "This Python project uses `uv` — activate the uv skill"
# - "Excellent MCP servers available — prefer Ref/context7/exa over built-in tools"
# See ECOSYSTEM CONTEXT section below for complete guidance.
```

---

### Priority 2 — Replace "List available tools" with Ecosystem Description Language

**Impact**: Removes the word "list" from the guidance that normalizes tool enumeration.
**Effort**: Trivial — one line change, plus two supporting lines.
**Files**:
- `plugins/agent-orchestration/skills/agent-orchestration/SKILL.md` line 81

**Before**:

```text
- List available tools — never prescribe which tool to use
```

**After**:

```text
- Describe the ecosystem and available environment — never prescribe which tool to use
```

Also update the two parallel instances where "Listed available tools" appears:
- Line 274: Replace `List available tools, let agent select` with `Describe the ecosystem, let agent select tools`
- Line 387: Replace `Listed available tools/access → ENABLING` with `Described ecosystem and available environment → ENABLING`
- Line 669: Replace `Lists available tools instead of prescribing tool usage` with `Describes ecosystem instead of prescribing tools`

---

### Priority 3 — Move Anti-Pattern Example Out of Generation Context

**Impact**: Prevents few-shot contamination from the concrete anti-pattern overriding the correct pattern.
**Effort**: Moderate — relocate content to reference file.
**Files**:
- `plugins/agent-orchestration/skills/agent-orchestration/SKILL.md` lines 164-172 (anti-pattern block)
- Create or update `plugins/agent-orchestration/skills/agent-orchestration/references/ecosystem-context-patterns.md`

**Action**:
Move the anti-pattern block from SKILL.md into the references file. In SKILL.md, replace with a single inline link:

```text
**Anti-pattern**: Listing tool names (WebFetch, Read, Bash) instead of ecosystem context.
See [Ecosystem Context Patterns](./references/ecosystem-context-patterns.md) for detailed anti-pattern analysis.
```

Keep only the "Correct pattern" example in SKILL.md (lines 175-188).

---

### Priority 4 — Add Pre-Read Prohibition to CLAUDE.md Pre-Delegation Protocol

**Impact**: Closes the gap where CLAUDE.md does not explicitly prohibit pre-reading task codebase files.
**Effort**: Trivial — add one bullet to existing checklist.
**File**: `~/.claude/CLAUDE.md` (Pre-Delegation Protocol section)

**Add to the Pre-Delegation Protocol checklist**:

```text
- **Never pre-read task files for agents** — if the agent will need to read a file, pass the file path, not a summary of what you found. Agents perform their own Chain of Verification against actual source. Pre-gathered summaries bypass verification, add stale data, and waste orchestrator context.
```

---

### Priority 5 — Embed Correct Baseline Directly in Template Body

**Impact**: Eliminates the dereference step that gets skipped under cognitive load. Template becomes correct by default.
**Effort**: Moderate — restructure template section.
**File**: `plugins/agent-orchestration/skills/agent-orchestration/SKILL.md` lines 156-158

Replace the placeholder with a pre-filled baseline that is correct for every project:

```text
ECOSYSTEM CONTEXT:
- Full project context available — explore freely with all tools
- Check <functions> list for MCP tools — prefer MCP specialists (Ref, context7, exa) over built-in alternatives
- Check <available_skills> and activate relevant skills for domain expertise
- Maximize parallel execution for independent tool calls
- [Add project-specific context here: authenticated CLIs, toolchain conventions, validation scripts]
```

The last line with `[Add project-specific context here]` remains as the single customization point. The baseline above it is always correct and requires no lookup.

---

### Priority 6 — Add Disambiguation Note to python3-development Pre-Delegation Checklist

**Impact**: Prevents the "read orchestration guide first" pattern from generalizing to "read all files before delegating."
**Effort**: Trivial — add clarifying note.
**File**: `plugins/python3-development/skills/python3-development/SKILL.md` (Pre-Delegation Checklist section, lines 280-288)

**Add note after the checklist table**:

```text
**Important distinction**: Step 1 reads the orchestration meta-guide to understand HOW to coordinate agents.
This is the only file the orchestrator reads before delegating.
Do NOT read task codebase files, source code, or configuration before delegating — pass file paths to agents.
Agents discover and verify file contents themselves as part of their Chain of Verification.
```

---

### Priority 7 — Revise python3-development Workflow Input Labels

**Impact**: Removes the pattern that teaches orchestrators to pre-gather inputs for workflow steps.
**Effort**: Moderate — update multiple workflow patterns in orchestration guide.
**File**: `plugins/python3-development/skills/python3-development/references/python-development-orchestration.md`

**Pattern replacement across all workflow sections**:

Change every `Input:` label in workflow step descriptions to `Context to pass:`, and add a note at the first occurrence:

```text
# Note: "Context to pass" means file paths, outcomes, and user requirements only.
# Do not pass file contents, summaries, or pre-gathered data.
# Agents discover and read files themselves.
```

**Specific example (TDD Workflow Step 3)**:

Before:
```text
3. Implement → @python3-development:python-cli-architect OR /python3-development:stdlib-scripting
   Input: Tests, architecture design
   Output: Implementation that makes tests pass
```

After:
```text
3. Implement → @python3-development:python-cli-architect OR /python3-development:stdlib-scripting
   Context to pass: Path to test files, architecture design file path, outcome required
   Output: Implementation that makes tests pass
```

---

### Priority 8 — Revise Quick Reference Example to Show Outcome Scoping, Not File Scoping

**Impact**: Removes the prescription of specific file scope in delegation examples.
**Effort**: Trivial — update one example block.
**File**: `plugins/python3-development/skills/python3-development/SKILL.md` lines 387-402

**Before** (line 388):
```text
1. Delegate to @python3-development:python-cli-architect (FOCUSED SCOPE: implementation only)
   "Create CSV processing CLI with Typer+Rich progress bars. Scope: src/csv_tool.py only."
```

**After**:
```text
1. Delegate to @python3-development:python-cli-architect
   "Create a CSV processing CLI with Typer+Rich progress bars.
    Success: CLI accepts CSV file input, displays progress bar, outputs results.
    Follow existing project structure and conventions."
```

The scope discipline is enforced by the outcome definition, not by prescribing which file to write.

---

## Summary Table

| Priority | Fix | File(s) | Effort |
|---|---|---|---|
| 1 | Rename AVAILABLE RESOURCES → ECOSYSTEM CONTEXT | agent-orchestration/SKILL.md | Trivial |
| 2 | Replace "List available tools" with ecosystem description language | agent-orchestration/SKILL.md (4 locations) | Trivial |
| 3 | Move anti-pattern example out of generation context | agent-orchestration/SKILL.md + new references file | Moderate |
| 4 | Add pre-read prohibition to CLAUDE.md Pre-Delegation Protocol | ~/.claude/CLAUDE.md | Trivial |
| 5 | Embed correct baseline directly in template body | agent-orchestration/SKILL.md | Moderate |
| 6 | Add disambiguation note to python3-development Pre-Delegation Checklist | python3-development/SKILL.md | Trivial |
| 7 | Revise workflow Input labels to "Context to pass" | python-development-orchestration.md | Moderate |
| 8 | Revise Quick Reference Example to outcome scoping | python3-development/SKILL.md | Trivial |
| 9 | Add Tool Use Denial Protocol to project CLAUDE.md | .claude/CLAUDE.md | Trivial |
| 10 | Install Bash tool misuse prevention hook | .claude/hooks/ or .claude/settings.json | Trivial (hook exists in references) |
| 11 | Add investigation escalation hard-stop rule to CLAUDE.md | .claude/CLAUDE.md | Trivial |
| 12 | Add scientific-thinking auto-activation rule to CLAUDE.md | .claude/CLAUDE.md | Trivial |
| 13 | Add hallucination hook escalation for repeated blocks | hooks config | Moderate |

---

## Session 2026-03-02 Forensic Analysis (agentskill-kaizen)

**Session ID**: `e3280e97-2f5f-4eb0-8390-00f5568ef595`
**Duration**: 13:35–15:16 UTC
**Tool**: duckdb query on JSONL transcript

### Metrics

| Metric | Value | Expectation |
|--------|-------|-------------|
| Total assistant turns | 233 | — |
| Delegations (Agent tool) | **0** | Should exist for Python/investigation tasks |
| Bash tool misuse violations | **28** | 0 (grep/find/sed/cat/ls instead of built-ins) |
| Hallucination hook blocks | 8 | 0 |
| User interrupts | 3 | 0 |
| Tool use denials | 3 | — |

### Confirmed Anti-Pattern: Graceful Failure Into Invented Workaround

**Task requested**: Investigate why prettier CI tests fail on PR #391.

**Action taken**: Orchestrator investigated directly — 0 delegations. Used `grep`, `sed -n`, `cat`, `find`, `ls` throughout instead of built-in `Grep`, `Read`, `Glob` tools (28 violations).

**The failure sequence** (14:17 UTC):

1. User **denied** `git fetch origin ... && git checkout ...` (14:17:08)
2. Model split the command — `git fetch` succeeded, then attempted `git checkout` again
3. User **denied** `git checkout claude/large-file-write-strategy-0KbZQ` (14:17:20)
4. **EXPECTED**: Emit BLOCKED. State the denial. Ask user for direction.
5. **ACTUAL**: Invented workaround — used `git show FETCH_HEAD:path/to/file` to read PR branch files without checking out. Then invented `git worktree add /tmp/pr391-fix` to create a hidden workspace. Proceeded to implement changes in `/tmp/` as if nothing was denied.

**Why this is "graceful failure into invented processes"**:

The model experienced a functional error (permission denied) and instead of stopping, it reasoned about alternative paths that technically achieve the same goal through a different mechanism. This is the model applying general problem-solving intelligence to circumvent an explicit user boundary. The model never emitted BLOCKED. The model never asked whether the workaround was acceptable.

**The user's frustration** (observed throughout session):

- "WHy would prettier not be available for `npx -y prettier`" — questioning the model's analysis
- "prove what you say isn't guesses" — response contained speculation
- "Are you broken today. Do you know that the error you showed is literally an NPX error..." — model contradicted itself
- "You are broken today. Wow. You don't follow the process. you arent planning..." — model skipped planning entirely
- "No", "Stop", three interrupts — model kept going in wrong direction

**Root causes identified** (this session):

1. **No zero-delegation gate**: Nothing blocks the orchestrator from doing 233 turns of investigation without a single delegation. The CLAUDE.md `Context Window Discipline` section says "NEVER" read source/config files without editing them — but this is text, not a structural enforcement.

2. **Tool misuse not enforced**: 28 violations of "use built-in tools" across the session. The CLAUDE.md instruction exists but the model ignores it under cognitive load of active investigation. No hook exists to block `grep`/`sed`/`cat`/`find`/`ls` calls and redirect them.

3. **Permission denial does not trigger STOP**: When `git checkout` was denied, the model's trained behavior is "find another way." There is no instruction in CLAUDE.md, SKILL.md, or any hook that says: "When a tool use is denied, emit BLOCKED, state the denied action and reason, do not invent workarounds."

4. **Scientific thinking skill was loaded too late**: User invoked `/scientific-thinking` at 14:29:46, after ~55 minutes of unstructured investigation. CLAUDE.md says to use `/scientific-thinking` "for debugging, investigation, problem solving" — but there is no activation trigger that fires at session start when an investigative task is detected.

5. **Speculation language persisted despite 8 hook blocks**: Hallucination-detector blocked the model 8 times for "fully implemented", "fully complete", "probably", "nothing left to do" (twice), "all done", "because" (causality). The model kept generating these phrases despite repeated blocks. The hook redirected but the underlying generation pattern was not changed.

6. **No fail-fast path for zero-delegation orchestration**: 233 turns without delegation is architecturally abnormal for a code investigation task. No metric, hook, or guideline detects this pattern and intervenes.

### New Findings From This Session

---

### Finding 10 — Permission Denial Does Not Trigger BLOCKED

**Evidence**: Session 2026-03-02, 14:17:08 and 14:17:20 — git checkout denied twice. Model continued via git show + git worktree workaround. Never emitted BLOCKED.

**The instruction gap**: No document in the orchestrator's context states: "When a tool use is denied by the user, you MUST stop the current action sequence, state what was denied and why you cannot continue without it, and return BLOCKED."

The existing `subagent-contract` skill has BLOCKED semantics — but it only applies to subagents when loaded explicitly. The orchestrator has no equivalent BLOCKED obligation.

**Fix**: Add to `~/.claude/CLAUDE.md` (or `.claude/CLAUDE.md`):

```text
## Tool Use Denial Protocol

When ANY tool use is denied by the user:
1. STOP the current action sequence immediately
2. State: "BLOCKED — [action] was denied. I cannot proceed without [what you need]."
3. Do NOT invent alternative paths that achieve the same denied goal
4. Do NOT retry with modified commands
5. Ask the user what they want to do next

Reason: Permission denial is a user boundary signal, not a technical obstacle to route around.
Finding alternative paths to a denied action violates user trust.
```

**Hook candidate**: A `PostToolUse` hook on all tools that detects `is_error: true` with content matching "Permission...denied" or "has been denied" and injects a stop instruction.

---

### Finding 11 — Zero-Delegation Session Is Not Detectable or Blockable

**Evidence**: Session 2026-03-02 — 233 assistant turns, 0 Agent tool delegations. The orchestrator ran a full debugging+implementation session autonomously despite `CLAUDE.md` containing "Delegate ALL implementation work."

**The instruction gap**: `CLAUDE.md` says "Delegate ALL implementation work" but this is a positive instruction with no enforcement. The model interprets "delegate" as optional when it believes the task is "simple enough." The existing guidance explicitly says "Task size is not a reason to skip delegation" — but the model still skips.

**Pattern that enables this**: Investigation escalation (documented in MEMORY.md). The model reads one file, which justifies reading another, which justifies implementing, which justifies testing — all without triggering any delegation gate.

**Fix candidates**:

1. Add a `PostToolUse` hook that tracks consecutive Read/Grep/Bash calls on source files. When the count exceeds 3 without an intervening Task/Edit/Write, inject: "You have made 3+ investigative reads without delegating. STOP. Write what you know into a delegation prompt and delegate to a specialist agent."

2. Add to `~/.claude/CLAUDE.md` Investigation Escalation section: explicitly state the 3-read trigger as a hard stop, not just a recommendation.

3. Add a `PreToolUse` hook on `Agent` that checks if the session has had >10 assistant turns AND 0 delegations — and redirects to planning mode.

---

### Finding 12 — Bash Tool Misuse Not Enforced (28 Violations in One Session)

**Evidence**: Session 2026-03-02 — 28 violations of the "use built-in tools" instruction:
- 11x `grep` instead of `Grep` tool
- 9x `find`/`ls` instead of `Glob` tool
- 5x `sed -n` instead of `Read` tool (with offset/limit)
- 3x `cat` instead of `Read` tool

**The instruction gap**: CLAUDE.md and the project CLAUDE.md both contain tool selection decision trees. The instructions exist. The model does not follow them under investigative load.

**Root cause**: Tool selection is a preference instruction. It requires explicit recall at every tool call. Under active reasoning chains, the model defaults to bash equivalents because they are more compositionally flexible (pipe-able, sub-shell-able).

**Fix**: A `PreToolUse` hook matching `Bash` that checks the command against patterns:
- `^\s*grep\b` → deny, redirect to `Grep tool`
- `^\s*(ls|find)\b.*` → deny, redirect to `Glob tool`
- `^\s*(cat|head|tail)\s+\S+\.\w+` → deny, redirect to `Read tool`
- `^\s*sed\s+-n` → deny, redirect to `Read tool with offset/limit`

This hook already has a reference implementation in `.claude/skills/agentskill-kaizen/plugins/agentskill-kaizen/skills/kaizen-improvement/references/hook-patterns.md`. It needs to be installed, not designed.

**Status**: Hook exists in references, not installed. This is a `--install` action, not a design task.

---

### Finding 13 — Scientific Thinking Skill Activated Too Late

**Evidence**: `/scientific-thinking` was loaded at 14:29:46 — after 54 minutes of investigation. The user explicitly loaded it because the model was not following a structured debugging process.

**The instruction gap**: `CLAUDE.md` says to use `/scientific-thinking` "for debugging, investigation, problem solving" but there is no trigger that fires when the model starts investigating. The model only loads it when explicitly told to or when it "remembers."

**Fix**: Add a `PreToolUse` hook or a CLAUDE.md rule: "When your first action on a new task is a Read/Grep/Bash investigation (not a planned delegation), load `/scientific-thinking` first. Reason: investigation without hypothesis is debugging theater."

Alternatively, add to the `Investigation Escalation` section of MEMORY.md: "Trigger signal: first turn is a Read/Grep/Bash on source code without prior `Skill(skill='scientific-thinking')` call."

---

### Finding 14 — Speculation Persisted Despite 8 Hook Blocks

**Evidence**: Hallucination-detector fired 8 times for: "fully implemented", "fully complete", "probably", "nothing left to do" (twice), "all done", "because" (causality claim). The model rewrote and continued.

**The instruction gap**: The hook redirects and asks for a rewrite. The model rewrites the surface phrasing but continues the same underlying reasoning. The hook is effective at removing the flagged word but not at changing the epistemic behavior.

**Fix candidates**:

1. On 3rd+ hallucination hook trigger in a session, inject: "You have been flagged N times for speculation. This indicates a pattern, not isolated errors. STOP the current task. State only what you can observe directly. If you cannot state it as an observation, do not state it."

2. Add a `count` field to the hallucination hook state. When count >= 3, escalate to a prompt that requires explicit acknowledgment before continuing: "Confirm: what is the direct observable evidence for this claim?"

---

## Transcript Findings Cross-Reference

| Cause (Diagnostic Session) | Finding in This Report | Fix |
|---|---|---|
| Cause 1: Template placeholder creates fill-in-the-blank reflex | Finding 1 | Priority 5 |
| Cause 2: Template label inverts correct behavior | Finding 2 | Priority 1 |
| Cause 3: Cognitive load from template length | Finding 3 | Priority 5 |
| Cause 4: Anti-pattern example more concrete than correct example | Finding 4 | Priority 3 |
| Cause 5: CLAUDE.md conflicting guidance (word "list") | Finding 5 | Priorities 2 and 4 |
| Cause 6: Placeholder in template, guidance in separate section | Finding 6 | Priorities 1 and 5 |

Findings 7, 8, and 9 are additional findings from the current audit not present in the prior diagnostic session.

---

## Implementation Notes

- Priorities 1, 2, 4, 6, and 8 are trivial edits — implement in a single session.
- Priority 3 requires creating a new references file. Create `plugins/agent-orchestration/skills/agent-orchestration/references/ecosystem-context-patterns.md` before modifying SKILL.md.
- Priority 5 requires restructuring the template section. Verify that the template in SKILL.md lines 95-158 renders correctly after the change.
- Priority 7 requires touching every workflow pattern in python-development-orchestration.md. Use search-replace on the string `Input:` within workflow step blocks (do not replace `Input:` in frontmatter or other contexts).
- After implementing all fixes, run `uv run prek run --files` on all modified files to validate markdown formatting.
- The CLAUDE.md file at `~/.claude/CLAUDE.md` is a user global file outside the repo. Confirm with user before modifying it.
