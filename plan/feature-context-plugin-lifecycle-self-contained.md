# Feature Context: Plugin Lifecycle Self-Contained Steps

## Document Metadata

- **Generated**: 2026-03-04
- **Input Type**: simple_description
- **Source**: Feature request — GitHub Issue #427 acceptance criterion 5
- **Status**: DISCOVERY_COMPLETE

---

## Original Request

The plugin-creator plugin has a partially-implemented lifecycle skill at
`plugins/plugin-creator/skills/plugin-lifecycle/SKILL.md`. Acceptance criterion 5 of GitHub
Issue #427 is not met: "An orchestrator can follow the skill end-to-end and reach a
marketplace-ready plugin without consulting plugin-creator internals."

Two steps in the SKILL.md reference a deprecated skill's internal patterns ("inherited from
/plugin-creator:plugin-creator Phase 1 pattern" and "inherited from
/plugin-creator:plugin-creator Phase 2 pattern"), forcing orchestrators to consult the
deprecated plugin-creator SKILL.md to understand what to do.

The desired outcome: the plugin-lifecycle SKILL.md is fully self-contained — every step
specifies which agent to invoke, what context to pass, and what output to produce, with no
references to deprecated skill internals.

---

## Core Intent Analysis

### WHO (Target Users)

Orchestrators — the main Claude Code session reading and executing `plugin-lifecycle/SKILL.md`.
Not human users directly. The skill is machine-readable workflow documentation consumed by an AI
agent that follows its steps to build a plugin.

### WHAT (Desired Outcome)

Every step in `plugin-lifecycle/SKILL.md` is actionable without consulting any other skill or
agent file. Specifically, the two steps currently labeled "inherited from
`/plugin-creator:plugin-creator` Phase N pattern" are replaced with concrete delegation
instructions that name the agent, the context to pass, and the output to produce — following the
format defined in `.claude/rules/delegation-format.md`.

### WHEN (Trigger Conditions)

An orchestrator invokes `/plugin-lifecycle new <concept>` and reaches Phase 2 (Research) step 2
or Phase 3 (Design) step 2. Currently, it encounters a reference to a deprecated skill's
internals and cannot proceed without reading that deprecated skill.

### WHY (Problem Being Solved)

The plugin-lifecycle skill is supposed to replace plugin-creator as the primary entry point.
If it still forces orchestrators to read the deprecated skill, it has not actually replaced it
— it has only added a layer of indirection. Acceptance criterion 5 exists precisely to prevent
this: the lifecycle skill must be the single source of truth for the orchestrator.

---

## Codebase Research

### Gap Locations (Exact)

Both gaps are in `plugins/plugin-creator/skills/plugin-lifecycle/SKILL.md`:

**Gap 1 — Phase 2: Research, step 2** (`SKILL.md:126-128`):

```text
2. Task is ecosystem and pattern research with parallel research agents (inherited from
   `/plugin-creator:plugin-creator` Phase 1 pattern — 4-way parallel research covering
   ecosystem survey, Claude docs review, existing pattern analysis, reference implementations)
   Context to include in the prompt: feature context from step 1, plugin concept description
   Output: `.claude/plan/{plugin-name}/research-FINDINGS.md` — consolidated research findings
```

**Gap 2 — Phase 3: Design, step 2** (`SKILL.md:149-151`):

```text
2. Task is design plan creation (inherited from `/plugin-creator:plugin-creator` Phase 2 pattern)
   Context to include in the prompt: research-FINDINGS.md, rt-ica output, user discussion notes
   Output: `.claude/plan/{plugin-name}/design-PLAN.md` — design plan with XML task specs
   defining every skill, agent, and hook to create
```

### Similar Patterns Found

#### Pattern 1: Fully-specified Phase 2 Research in plugin-creator (deprecated)

- **Location**: `plugins/plugin-creator/skills/plugin-creator/SKILL.md:265-337`
- **Relevance**: This is the "Phase 1 pattern" that Gap 1 references. It defines the 4-way
  parallel research pattern with four specific agent invocations, each with its own prompt
  focus (existing solutions, Claude Code features, architecture patterns, pitfalls/docs),
  output file path, and merge instruction.
- **Reusable**: The four researcher roles, agent types (`plugin-creator:plugin-assessor` x3,
  `general-purpose` x1), individual output file names
  (`research-1-existing.md`, `research-2-features.md`, `research-3-architecture.md`,
  `research-4-pitfalls.md`), and merge instruction into `research-FINDINGS.md` can be
  inlined into the plugin-lifecycle SKILL.md.

#### Pattern 2: Design phase (Plan + Plan-Checker loop) in plugin-creator (deprecated)

- **Location**: `plugins/plugin-creator/skills/plugin-creator/SKILL.md:343-434`
- **Relevance**: This is the "Phase 2 pattern" that Gap 2 references. It defines a two-step
  design loop: (2a) delegate to a `Plan` agent to generate XML task specs, then (2b) delegate
  to a `general-purpose` agent as plan-checker, looping until PASS. Includes the XML task spec
  format expected in `design-PLAN.md`.
- **Reusable**: The Plan agent invocation, plan-checker agent invocation, the PASS/FAIL loop,
  the XML task spec format (`<task id='N'><name>`, `<files>`, `<action>`, `<verify>`, `<done>`),
  and the save format for `design-PLAN.md`.

#### Pattern 3: Correct delegation format — other steps in plugin-lifecycle

- **Location**: `plugins/plugin-creator/skills/plugin-lifecycle/SKILL.md:103-105` (Phase 1),
  `SKILL.md:170-182` (Phase 4), `SKILL.md:205-214` (Phase 5 routing), `SKILL.md:234-243`
  (Phase 6), `SKILL.md:258-274` (Phase 7)
- **Relevance**: These steps in the same file demonstrate the correct format — each names the
  skill or agent to invoke (`Skill(skill="...")` or `subagent_type="..."`), states context to
  include, and states the output artifact. The two gap steps need to match this format.
- **Reusable**: The formatting pattern itself.

#### Pattern 4: Delegation format standard

- **Location**: `.claude/rules/delegation-format.md:38-62`
- **Relevance**: Defines the canonical format for delegation steps:
  `N. Task is [description] with subagent_type="plugin:agent-name"` / `Context to include in the
  prompt: [specific file paths or data]` / `Output: [specific artifact, file path, format]`.
  This is the standard the two gap steps must conform to.
- **Reusable**: The three-line format itself.

### Phase-to-Skill Mapping Table (Already Exists)

- **Location**: `plugins/plugin-creator/skills/plugin-lifecycle/SKILL.md:287-307`
- **Relevance**: The table at lines 293 and 297 already acknowledges the gaps:
  - `| 2: Research | Parallel research agents | Inherited from plugin-creator Phase 1 |`
  - `| 3: Design | (design plan step) | Inherited from plugin-creator Phase 2 |`
  These table rows will also need updating once the steps are expanded.

### Existing Infrastructure

The deprecated `plugin-creator/SKILL.md` contains the full pattern text that needs to be
extracted and inlined. No new agents or skills need to be created — the agents already exist
(`plugin-creator:plugin-assessor`, `general-purpose`, `Plan`). The work is documentation
extraction and reformatting, not new implementation.

---

## Use Scenarios

### Scenario 1: Orchestrator follows new plugin creation end-to-end

**Actor**: Orchestrator (Claude Code session)
**Trigger**: User runs `/plugin-lifecycle new my-plugin-concept`
**Goal**: Complete all phases and produce a marketplace-ready plugin
**Expected Outcome**: The orchestrator reads Phase 2 step 2 and knows exactly which agent to
spawn, what prompt to give it, and what file to expect as output — without ever opening
`plugin-creator/SKILL.md`

### Scenario 2: Human author updates plugin-lifecycle documentation

**Actor**: Plugin author editing `plugin-lifecycle/SKILL.md`
**Trigger**: Reviews the file to verify it meets Issue #427 criterion 5
**Expected Outcome**: No step contains "inherited from" or references to another skill's phases.
Every delegation step has an agent, context, and output.

### Scenario 3: Orchestrator hits the Phase 3 Design step

**Actor**: Orchestrator mid-workflow
**Trigger**: Reaches Phase 3 step 2 after research is complete
**Expected Outcome**: The step tells the orchestrator exactly how to invoke the plan generation
agent (which agent type), what inputs to pass (research-FINDINGS.md, rt-ica output, user
discussion notes), what the output format should be (XML task specs in design-PLAN.md), and what
the plan-checker verification loop looks like — all without external lookup.

---

## Gap Analysis

### Identified Gaps

| # | Category | Gap Description | Impact |
|---|----------|-----------------|--------|
| 1 | Integration | Phase 2 step 2 (`SKILL.md:126-128`) says "inherited from plugin-creator Phase 1 pattern" instead of specifying agents, context, and output for the 4-way parallel research | Orchestrator cannot execute Phase 2 research without reading deprecated plugin-creator SKILL.md |
| 2 | Integration | Phase 3 step 2 (`SKILL.md:149-151`) says "inherited from plugin-creator Phase 2 pattern" instead of specifying the Plan agent + plan-checker loop with XML task spec format | Orchestrator cannot execute Phase 3 design without reading deprecated plugin-creator SKILL.md |
| 3 | Integration | Phase-to-skill mapping table (`SKILL.md:293, 297`) still shows "Inherited from plugin-creator Phase N" in the Invocation column | Table is misleading even after body text is fixed |
| 4 | Scope | Whether discussion/preferences capture (Phase 0.5 in plugin-creator) is intentionally absent from plugin-lifecycle or was dropped | If absent intentionally, no gap; if dropped accidentally, orchestrator misses user preference capture before research |

---

## Questions Requiring Resolution

### Q1: Is the 4-way parallel research pattern in the deprecated skill the complete specification for Gap 1?

- **Category**: Integration
- **Gap**: Gap 1 needs to inline the Phase 1 research pattern from plugin-creator. The pattern
  at `plugin-creator/SKILL.md:265-337` shows four parallel agent invocations. Is this the
  authoritative source, or has the pattern evolved since the plugin-lifecycle was written?
- **Question**: Should the plugin-lifecycle Phase 2 step 2 be an exact transcription of the
  four-researcher parallel pattern from `plugin-creator/SKILL.md:265-337` (with output paths
  adapted to the `.claude/plan/{plugin-name}/` artifact directory), or is there a newer version
  of this pattern that should be used instead?
- **Options**:
  - A) Inline the pattern as-is from plugin-creator (adapting paths)
  - B) There is a newer pattern elsewhere that should be used
- **Why It Matters**: The wrong source produces a research phase that uses stale agent types or
  outdated prompts
- **Resolution**: _pending_

### Q2: Is the Plan agent + plan-checker loop in plugin-creator the complete specification for Gap 2?

- **Category**: Integration
- **Gap**: Gap 2 needs to inline the Phase 2 design pattern from plugin-creator. The pattern at
  `plugin-creator/SKILL.md:343-434` shows a Plan agent + general-purpose plan-checker loop. Is
  this the authoritative source?
- **Question**: Should the plugin-lifecycle Phase 3 step 2 inline the Plan agent delegation and
  plan-checker loop from `plugin-creator/SKILL.md:343-434`, or should a different approach
  (e.g., a dedicated design agent) be used?
- **Options**:
  - A) Inline Plan agent + plan-checker loop from plugin-creator as the design step
  - B) A different agent or approach should be used in plugin-lifecycle
- **Why It Matters**: Using the wrong agent type or skipping the plan-checker gate allows
  unverified design plans into Phase 4 (Create)
- **Resolution**: _pending_

### Q3: Was the Discussion phase (Phase 0.5 in plugin-creator) intentionally dropped from plugin-lifecycle?

- **Category**: Scope
- **Gap**: `plugin-creator/SKILL.md:214-260` defines a "Phase 0.5: Discussion" that captures
  user preferences (invocation style, verbosity, tool restrictions, error handling) into
  `discuss-CONTEXT.md` before research begins. This phase is absent from plugin-lifecycle.
- **Question**: Is the absence of Phase 0.5 (Discussion) from plugin-lifecycle intentional — the
  lifecycle was designed to skip user preference capture — or was it accidentally omitted when
  the skill was written?
- **Options**:
  - A) Intentionally absent — plugin-lifecycle does not require a discussion phase
  - B) Accidentally omitted — it should be added as a step in Phase 2 before step 1
- **Why It Matters**: If omitted, research proceeds without user preferences, potentially
  producing a design that mismatches what the user wants; this is out of scope for this feature
  request unless the answer is B
- **Resolution**: _pending_

### Q4: Should the Phase-to-Skill mapping table be updated as part of this work?

- **Category**: Scope
- **Gap**: The mapping table at `SKILL.md:287-307` has two rows that show "Inherited from
  plugin-creator Phase N" in the Invocation column. These will be misleading after the body
  text is fixed.
- **Question**: Is updating the mapping table rows for Phase 2 Research (parallel agents) and
  Phase 3 Design (plan agent) in scope for this feature?
- **Options**:
  - A) Yes — the table should be updated to show correct invocation syntax for each agent
  - B) No — the table is informational only and the body text fix is sufficient
- **Why It Matters**: Leaving stale table rows creates the same confusion the body-text fix
  is meant to eliminate
- **Resolution**: _pending_

---

## Goals (Pending Resolution)

_These goals will be finalized after questions are resolved._

1. Replace `SKILL.md:126-128` (Phase 2 step 2) with a fully-specified delegation step naming
   the parallel research agents, their individual prompts, output file paths, and the merge
   instruction — conforming to the format in `.claude/rules/delegation-format.md`
2. Replace `SKILL.md:149-151` (Phase 3 step 2) with a fully-specified delegation step naming
   the design plan agent and plan-checker agent, the loop condition, and the XML task spec
   format expected in `design-PLAN.md` — conforming to the format in
   `.claude/rules/delegation-format.md`
3. Update the Phase-to-Skill mapping table rows for Phase 2 and Phase 3 to show correct
   invocation references (pending Q4 resolution)
4. After edits, verify that no step in the file contains the string "inherited from" or
   references `plugin-creator` as a source of behavioral instructions

---

## Next Steps

After questions are resolved:

1. Update "Resolution" fields in Questions section
2. Finalize Goals section
3. Proceed to RT-ICA assessment
4. Then proceed to architecture design (the design work here is documentation editing, not
   software architecture — the architect agent will specify exact text replacements)

---

## Code References

- `plugins/plugin-creator/skills/plugin-lifecycle/SKILL.md:126-128` — Gap 1: Phase 2 step 2 with "inherited from" reference
- `plugins/plugin-creator/skills/plugin-lifecycle/SKILL.md:149-151` — Gap 2: Phase 3 step 2 with "inherited from" reference
- `plugins/plugin-creator/skills/plugin-lifecycle/SKILL.md:293` — Table row: Phase 2 Research / Inherited from plugin-creator Phase 1
- `plugins/plugin-creator/skills/plugin-lifecycle/SKILL.md:297` — Table row: Phase 3 Design / Inherited from plugin-creator Phase 2
- `plugins/plugin-creator/skills/plugin-creator/SKILL.md:265-337` — Source pattern for Gap 1 (4-way parallel research)
- `plugins/plugin-creator/skills/plugin-creator/SKILL.md:343-434` — Source pattern for Gap 2 (Plan + plan-checker loop)
- `.claude/rules/delegation-format.md:38-62` — Canonical format for delegation steps
