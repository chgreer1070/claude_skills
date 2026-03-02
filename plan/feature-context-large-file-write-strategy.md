# Feature Context: Agent Large File Write Strategy

## Document Metadata

- **Generated**: 2026-03-02
- **Input Type**: existing_document
- **Source**: GitHub Issue #367, backlog item `.claude/backlog/p1-agent-large-file-write-strategy-incremental-section-by-secti.md`
- **Status**: DISCOVERY_COMPLETE

---

## Original Request

Sub-agents writing large files (>30K chars) via single Write calls timeout or get stuck. Need a strategy where agents write the file structure/skeleton first, then fill in content section-by-section using Edit calls. Observed during task planner writing 57,800 char task plan that stalled. The pattern should be documented as agent guidance and possibly enforced via hooks or delegation instructions.

**Source**: Session observation (commit 8beddfb), P1 priority.

---

## Core Intent Analysis

### WHO (Target Users)

1. **Sub-agents** that produce large document artifacts (task plans, architecture specs, codebase analyses, research documents, feature context documents). These agents run inside Claude Code via the Agent tool, delegated by the orchestrator.
2. **Agent authors** who write or maintain agent prompt files and need to know the large-file write pattern.
3. **The orchestrator** that delegates to sub-agents and needs assurance that large-file writes complete reliably.

### WHAT (Desired Outcome)

Sub-agents that produce documents exceeding a defined character threshold complete their file writes without stalling or timing out. The incremental write pattern (skeleton-first, then Edit-fill) is:

1. Documented as canonical guidance accessible to agents at runtime.
2. Adopted by at least one existing large-output agent as a demonstration.
3. Optionally enforceable via a PreToolUse hook that warns or blocks oversized Write calls.

### WHEN (Trigger Conditions)

- A sub-agent is about to write a file whose content exceeds the safe threshold (estimated 20K-30K characters).
- The swarm-task-planner, python-cli-design-spec, codebase-analyzer, ecosystem-researcher, or feature-researcher agents are producing consolidated output documents.
- Any new agent is being authored that will produce large single-file outputs.

### WHY (Problem Being Solved)

The Write tool has an observed failure mode where large single-call writes (57,800 characters in the observed case) cause the sub-agent to stall or timeout. This blocks the SAM workflow at the planning phase, requiring manual intervention. There is currently no documented strategy or guardrail to prevent this. The problem is structural: agents are instructed to write documents but given no guidance on size limits for individual Write calls.

---

## Codebase Research

### Similar Patterns Found

#### Pattern 1: Document Structure Policy in swarm-task-planner

- **Location**: `plugins/python3-development/agents/swarm-task-planner.md:166-196`
- **Relevance**: The swarm-task-planner already has a "Document Structure Policy" that splits plans into progressive disclosure directories when >= 500 lines. This is a related but different concern -- it addresses document organization, not the mechanics of how the Write tool call is made.
- **Reusable**: The 500-line threshold decision pattern could inform the character threshold decision. The progressive disclosure pattern (PLAN/ directory with multiple files) is a complementary strategy: splitting large outputs into multiple smaller files avoids the single-large-Write problem entirely.

#### Pattern 2: orchestrator-discipline PreToolUse hooks

- **Location**: `plugins/orchestrator-discipline/hooks.json:1-25`
- **Relevance**: Demonstrates a working PreToolUse hook pattern that intercepts tool calls (Read, Grep, Bash) with Node.js `.cjs` scripts and returns `hookSpecificOutput` with `permissionDecision`. This is the exact hook infrastructure a Write-size-guard would use.
- **Reusable**: The hook structure (matcher on tool name, Node.js command, JSON output with `permissionDecision`) is directly applicable. A similar hook matching `Write` could inspect `tool_input.content.length` and return `deny` or `additionalContext` warnings.

#### Pattern 3: PreToolUse event schema for Write tool

- **Location**: `plugins/plugin-creator/skills/hooks-guide/references/claude-code.md:279-285`
- **Relevance**: Documents the Write tool's `tool_input` schema for PreToolUse events: `{ file_path: string, content: string }`. A hook can read `content.length` to determine if the write exceeds the threshold. The `updatedInput` field in PreToolUse responses can modify tool input before execution, and `additionalContext` can inject guidance.
- **Reusable**: The `additionalContext` field is particularly relevant -- a hook could inject the incremental-write guidance into the agent's context when a large Write is attempted, rather than blocking the call outright.

#### Pattern 4: Hook language convention (Node.js .cjs)

- **Location**: `.claude/rules/language-conventions.md:13-15`, `plugins/plugin-creator/agents/hook-creator.md:14-16`
- **Relevance**: All Claude Code hooks must be Node.js CommonJS `.cjs` files. Any enforcement hook would follow this convention.
- **Reusable**: Template structure and constraint list from hook-creator agent.

#### Pattern 5: Rules file pattern

- **Location**: `.claude/rules/silent-failure-prevention.md`, `.claude/rules/delegation-format.md`
- **Relevance**: Both are `.claude/rules/` files that establish behavioral constraints for agents. They demonstrate the structure: frontmatter with `paths:` globs (optional), title, decision flowcharts, positive/negative examples, and clear scope statements. A new rule file for large-file write strategy would follow this pattern.
- **Reusable**: The flowchart pattern (mermaid decision tree), example format (Wrong/Right), and scoping conventions.

### Existing Infrastructure

#### Tool availability gap in large-output agents

Five agents identified as producing large document artifacts currently have `Write` in their tools but NOT `Edit`:

| Agent | Tools include Write? | Tools include Edit? | Location |
|-------|---------------------|--------------------|----|
| `swarm-task-planner` | Yes | **No** | `plugins/python3-development/agents/swarm-task-planner.md:4` |
| `python-cli-design-spec` | Yes | **No** | `plugins/python3-development/agents/python-cli-design-spec.md:4` |
| `codebase-analyzer` | Yes | **No** | `plugins/python3-development/agents/codebase-analyzer.md:4` |
| `ecosystem-researcher` | Yes | **No** | `plugins/python3-development/agents/ecosystem-researcher-v1.1-rt-ica.md:4` |
| `feature-researcher` | Yes | **No** | `plugins/python3-development/agents/feature-researcher.md:5` |

This is a prerequisite gap: the incremental Edit-fill strategy cannot work unless `Edit` is added to these agents' tool lists.

#### Observed failure artifact

- The file `plan/tasks-14-console-forwarding-mcp-server-plugin.md` is 821 lines with 16 task sections and YAML frontmatter. This is the artifact from the session where the 57.8K stall was observed (commit 8beddfb).

#### Hook enforcement infrastructure

- PreToolUse hooks can block tool calls (exit code 2) or inject context (exit 0 + `additionalContext`).
- The `Write` tool is a valid matcher for PreToolUse events (`plugins/plugin-creator/skills/hooks-guide/references/claude-code.md:279-285`).
- The `content` field in Write tool_input is accessible to the hook, allowing character count inspection.

### Code References

- `plugins/python3-development/agents/swarm-task-planner.md:4` - tools list (Write, no Edit)
- `plugins/python3-development/agents/swarm-task-planner.md:166-196` - Document Structure Policy (progressive disclosure at 500 lines)
- `plugins/python3-development/agents/python-cli-design-spec.md:4` - tools list (Write, no Edit)
- `plugins/python3-development/agents/codebase-analyzer.md:4` - tools list (Write, no Edit)
- `plugins/python3-development/agents/ecosystem-researcher-v1.1-rt-ica.md:4` - tools list (Write, no Edit)
- `plugins/python3-development/agents/feature-researcher.md:5` - tools list (Write, no Edit)
- `plugins/orchestrator-discipline/hooks.json:4-13` - PreToolUse hook example (Read|Grep matcher)
- `plugins/plugin-creator/skills/hooks-guide/references/claude-code.md:279-285` - Write tool PreToolUse input schema
- `plugins/plugin-creator/skills/hooks-guide/references/claude-code.md:686-708` - PreToolUse decision control (permissionDecision, additionalContext, updatedInput)
- `.claude/rules/delegation-format.md` - rule file structure example
- `.claude/rules/silent-failure-prevention.md` - rule file structure example
- `.claude/rules/language-conventions.md:13-15` - hooks must be Node.js .cjs
- `.claude/backlog/p1-agent-large-file-write-strategy-incremental-section-by-secti.md` - groomed backlog item with acceptance criteria
- `plan/tasks-14-console-forwarding-mcp-server-plugin.md` - the 821-line task file from the observed stall

---

## Use Scenarios

### Scenario 1: Task planner writing a large task plan

**Actor**: swarm-task-planner sub-agent
**Trigger**: Orchestrator delegates task plan creation for a complex feature with 10+ tasks. The resulting document exceeds 30K characters.
**Goal**: Complete the task plan file without stalling.
**Expected Outcome**: The agent writes a skeleton (YAML frontmatter, section headers for each task, sync checkpoint stubs), then fills each task section via Edit calls. The file is complete and the agent returns DONE.

### Scenario 2: Architecture spec exceeding threshold

**Actor**: python-cli-design-spec sub-agent
**Trigger**: Orchestrator delegates architecture specification for a feature with multiple components, command hierarchies, data models, and diagrams.
**Goal**: Produce the complete architecture document without timeout.
**Expected Outcome**: The agent writes the document structure (TOC, component section headers, diagram placeholders), then populates each section incrementally. The output file matches the same structure as if written in a single call.

### Scenario 3: Hook warns agent about oversized Write

**Actor**: Any sub-agent attempting a Write call with content exceeding the threshold
**Trigger**: PreToolUse hook fires on a Write call and inspects `tool_input.content.length`.
**Goal**: The agent receives guidance to use the incremental pattern instead.
**Expected Outcome**: The hook either (a) injects `additionalContext` explaining the skeleton-first pattern and allows the Write (soft warning), or (b) denies the Write and tells the agent to use the incremental approach (hard block). The agent adjusts its approach.

### Scenario 4: Agent author creating a new large-output agent

**Actor**: Developer or agent-creator designing a new agent that will produce consolidated document output
**Trigger**: Reading agent authoring guidance before writing the agent file.
**Goal**: Know the large-file write strategy exists and incorporate it into the new agent's prompt.
**Expected Outcome**: The guidance document or rule is discoverable in `.claude/rules/` and referenced from delegation-format.md or CLAUDE.md. The agent author includes `Edit` in the tools list and references the incremental pattern in the agent's writing instructions.

---

## Gap Analysis

### Identified Gaps

| # | Category | Gap Description | Impact |
|---|----------|-----------------|--------|
| 1 | Behavior | Exact character threshold for "large file" is not empirically determined. 57.8K failed; the safe upper bound for a single Write call is unknown. | If threshold is too high, stalls recur. If too low, agents use the slower incremental path unnecessarily. |
| 2 | Scope | Whether the hook enforcement is a hard block (deny Write) or soft warning (inject additionalContext). | Hard block changes agent behavior forcibly but may cause agents without Edit tool to fail entirely. Soft warning relies on agent compliance. |
| 3 | Integration | Five large-output agents lack `Edit` in their tools list. Adding Edit is a prerequisite for the incremental strategy. | Without Edit, agents literally cannot perform the skeleton+Edit-fill pattern even if instructed to. |
| 4 | Scope | Whether the guidance applies only to planning/synthesis agents or to ALL agents with Write access. | Narrow scope is simpler but misses edge cases. Broad scope requires updating many agent files. |
| 5 | Behavior | Whether the progressive disclosure pattern (multiple smaller files) is an alternative to the Edit-fill pattern, or if both should coexist as options. | The swarm-task-planner already has a split-to-directory policy at 500 lines. This could be a competing strategy. |
| 6 | Integration | Where exactly the guidance should be injected -- new `.claude/rules/` file, CLAUDE.md section, agent-level instruction, or all three. | Rules files apply via path globs; agent instructions are agent-specific. The guidance needs to reach agents at runtime. |
| 7 | Scope | Whether the hook should exist as a plugin hook (orchestrator-discipline or new plugin), project-level hook (.claude/settings.json), or skill/agent frontmatter hook. | Plugin hooks are portable. Project hooks are local. Frontmatter hooks apply only when that skill/agent is active. |

---

## Questions Requiring Resolution

### Q1: What is the safe character threshold for a single Write call?

- **Category**: Behavior
- **Gap**: Gap #1 -- 57.8K failed, but the actual limit is unknown.
- **Question**: What character count should trigger the incremental write strategy? Should this be tested empirically (e.g., 20K, 25K, 30K) or set conservatively?
- **Options**:
  - A) Conservative: 20K characters (well below the observed failure point)
  - B) Moderate: 30K characters (roughly half the observed failure size)
  - C) Empirical: Test multiple sizes and set threshold based on observed reliability
- **Why It Matters**: The threshold determines how frequently the incremental pattern is used. Too low = unnecessary overhead on medium files. Too high = stalls recur.
- **Resolution**: _pending_

### Q2: Should the hook enforcement be a hard block or soft warning?

- **Category**: Behavior
- **Gap**: Gap #2 -- hard vs. soft enforcement changes agent interaction model.
- **Question**: When a Write call exceeds the threshold, should the PreToolUse hook deny the Write (forcing the agent to adapt) or allow it with injected guidance?
- **Options**:
  - A) Hard block: Exit 2, deny the Write, return error message with instructions to use skeleton+Edit pattern
  - B) Soft warning: Exit 0, allow the Write, inject `additionalContext` with guidance (agent may or may not adapt)
  - C) Staged: Start with soft warning, graduate to hard block after agents are updated with Edit tool
- **Why It Matters**: Hard block with current agents (that lack Edit tool) will cause failures. Soft warning may be ignored.
- **Resolution**: _pending_

### Q3: Should all five large-output agents get Edit added to their tools, or only the task planner?

- **Category**: Scope
- **Gap**: Gap #3 -- prerequisite for the incremental strategy.
- **Question**: The acceptance criteria say "at least one existing large-output agent updated to demonstrate the pattern." Should Edit be added to all five identified agents (swarm-task-planner, python-cli-design-spec, codebase-analyzer, ecosystem-researcher, feature-researcher) or just the swarm-task-planner initially?
- **Options**:
  - A) All five agents in both python3-development and development-harness plugins
  - B) Only swarm-task-planner (both plugins) as the demonstration case
  - C) swarm-task-planner + python-cli-design-spec (the two largest output producers)
- **Why It Matters**: More agents updated = broader protection. Fewer = simpler initial scope and lower risk of unintended Edit usage.
- **Resolution**: _pending_

### Q4: Is the multi-file split (progressive disclosure) an alternative strategy or complementary?

- **Category**: Scope
- **Gap**: Gap #5 -- the swarm-task-planner already splits to directories at 500 lines.
- **Question**: The task planner's Document Structure Policy already prescribes splitting into a PLAN/ directory at >= 500 lines. Is the skeleton+Edit-fill pattern intended as an ALTERNATIVE to splitting, a COMPLEMENT (use both), or a REPLACEMENT for when splitting is not feasible?
- **Options**:
  - A) Complementary: prefer splitting when possible, use skeleton+Edit when a single file is required
  - B) Alternative: agents choose whichever strategy fits
  - C) Primary: skeleton+Edit is the canonical approach; splitting is a separate concern
- **Why It Matters**: If splitting is preferred, the guidance should say "split first, Edit-fill as fallback." If skeleton+Edit is primary, the Document Structure Policy may need updating.
- **Resolution**: _pending_

### Q5: Where should the guidance live?

- **Category**: Integration
- **Gap**: Gap #6 -- multiple potential locations.
- **Question**: Should the incremental write strategy be documented as a new `.claude/rules/` file, a section in CLAUDE.md, inline in each agent's prompt, or some combination?
- **Options**:
  - A) New `.claude/rules/large-file-write-strategy.md` with `paths:` targeting agent files
  - B) New section in CLAUDE.md under a "Tool Usage" heading
  - C) Both a rule file AND inline guidance in affected agent prompts
  - D) A skill that agents can load when they need to write large files
- **Why It Matters**: Rules files with `paths:` globs are auto-loaded by Claude Code when matching files are relevant. CLAUDE.md applies globally. Agent-inline instructions are most reliable but require per-agent maintenance.
- **Resolution**: _pending_

### Q6: Should the hook be implemented now or deferred?

- **Category**: Scope
- **Gap**: Gap #7 -- hook adds enforcement but also complexity.
- **Question**: Is the PreToolUse hook part of the initial implementation scope, or should it be deferred until the guidance-only approach is validated?
- **Options**:
  - A) Include hook in initial scope (guidance + hook together)
  - B) Defer hook -- implement guidance and agent updates first, add hook enforcement later if compliance is insufficient
- **Why It Matters**: The hook requires Node.js development, testing, and a hook deployment decision (plugin vs. project vs. frontmatter). Guidance-only is lighter weight and may be sufficient.
- **Resolution**: _pending_

---

## Goals (Pending Resolution)

_These goals will be finalized after questions are resolved._

1. Canonical guidance document exists describing the skeleton-first, Edit-fill pattern for large file writes, with concrete examples and a defined character threshold.
2. The guidance specifies when to use skeleton+Edit-fill vs. multi-file splitting vs. single Write.
3. At least one large-output agent (swarm-task-planner at minimum) is updated with `Edit` in its tools list and incremental write instructions in its prompt.
4. The guidance is discoverable by agents at runtime (via `.claude/rules/` file, CLAUDE.md reference, or skill loading).
5. (Conditional on Q6) A PreToolUse hook exists that detects oversized Write calls and either warns or blocks with guidance.
6. The strategy is testable: a sub-agent writing >30K characters completes without stalling.

---

## Next Steps

After questions are resolved:

1. Update "Resolution" fields in Questions section
2. Finalize Goals section
3. Proceed to RT-ICA assessment
4. Then proceed to architecture design
