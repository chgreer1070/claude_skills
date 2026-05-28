# Plugin Lifecycle — Artifact Templates

Templates used during plugin-lifecycle execution. Each phase that requires an artifact uses one of these formats. Consult this file when the orchestrator needs to write one of the named artifacts.

---

## Artifact Directory Layout

All work artifacts are stored in `.plugin-creator/plans/{plugin-name}/`:

```text
.plugin-creator/plans/{plugin-name}/
├── PROJECT.md                # Vision and goals
├── STATE.md                  # Current phase, decisions, blockers
├── discuss-CONTEXT.md        # Phase 0.5 output — user preferences (new path only)
├── research-FINDINGS.md      # Phase 2 output (new path only)
├── design-PLAN.md            # Phase 3 output (new path only)
├── assessment-REPORT.md      # Phase 1 output (existing path only)
├── validation-REPORT.md      # Phase 7 output
└── SUMMARY.md                # Completion record
```

`{plugin-path}/mission.json` — Phase 0.6 output — plugin mission statement with `status: "draft"` (new path); created by the `mission-statement` skill at the plugin root (not inside `.plugin-creator/plans/`).

Before starting any phase, read `STATE.md` if it exists to determine current progress. After completing each phase, update `STATE.md` with the phase completed and any decisions made.

---

## RT-ICA SUMMARY (Phase 0)

Used during Phase 0 RT-ICA Prerequisite Check. Verify every condition has status AVAILABLE or DERIVABLE before the gate returns APPROVED.

```text
RT-ICA SUMMARY

Goal:
- Create a Claude Code plugin for [purpose]

Success Output:
- Functional plugin that [specific outcome]

Conditions (reverse prerequisites):
1. Purpose clarity     | Requires: Clear problem statement      | Why: Determines plugin scope
2. Target users        | Requires: Who will use this            | Why: Shapes UX decisions
3. Component selection | Requires: Skills vs Agents vs Hooks    | Why: Architecture
4. Existing solutions  | Requires: Check for similar plugins    | Why: Avoid duplication
5. Source material     | Requires: Documentation/APIs to encode | Why: Content accuracy
6. Verification method | Requires: How to test the plugin works | Why: Quality gate

Verification:
- [Check each condition: AVAILABLE / DERIVABLE / MISSING]

Decision:
- [APPROVED / BLOCKED]
```

---

## Phase 0.5 Discussion Questions

Used during Phase 0.5 to identify gray areas and capture user preferences before research.

**For skill-focused plugins:**

- Activation triggers: When should Claude auto-load vs user-invoke?
- Tool restrictions: Full access or limited tools?
- Output format: Verbose explanations or terse instructions?
- Reference structure: Inline content or progressive disclosure?

**For agent-focused plugins:**

- Delegation scope: What tasks should agents handle?
- Return format: Summaries or detailed reports?
- Error handling: Retry, escalate, or fail fast?

**For hook-focused plugins:**

- Trigger events: Which tool/session events matter?
- Hook type: Command, prompt, or agent verification?
- Timeout handling: Fail silently or block?

---

## discuss-CONTEXT.md (Phase 0.5)

Save Phase 0.5 user preferences to `.plugin-creator/plans/{plugin-name}/discuss-CONTEXT.md` using this template:

```markdown
# Plugin Discussion: {plugin-name}
Date: {ISO timestamp}

## Scope Decisions
- {question}: {user preference}

## UX Preferences
- Invocation: {user-invoked | model-invoked | both}
- Verbosity: {terse | balanced | verbose}

## Technical Choices
- {choice}: {preference with rationale}
```

These preferences guide all subsequent research and planning phases.

---

## research-FINDINGS.md (Phase 2)

After all four researchers complete in Phase 2, consolidate their outputs into `.plugin-creator/plans/{plugin-name}/research-FINDINGS.md` using this template:

```markdown
# Research Findings: {plugin-name}
Date: {ISO timestamp}

## 1. Existing Solutions
{Researcher 1 findings}

## 2. Recommended Features
{Researcher 2 findings}

## 3. Architecture Patterns
{Researcher 3 findings}

## 4. Pitfalls & Requirements
{Researcher 4 findings}

## Synthesis
- Key insights: {combined learnings}
- Recommended approach: {synthesis}
```
