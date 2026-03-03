---
name: Multi-session build state lost during context compaction
description: "During the agentskill-kaizen build (8-phase `/plugin-dev:create-plugin` workflow), context compaction mid-build converted structured task state into a narrative summary. The resuming session had to reconstruct \"what's done vs pending\" from prose rather than a checklist. Background agent results that were already consumed and applied reappeared as late notifications after compaction, requiring manual deduplication (\"did I already handle this?\"). No persistent artifact tracked phase completion, commit SHAs per phase, deferred items, or agent result consumption status.\n**Observed symptoms**:\n- Phase completion status existed only in ephemeral context — lost on compaction\n- Background agent notifications arrived after their findings were already applied (3 duplicate notifications)\n- Plan committed early (`87a0b93`) diverged from actual implementation but was never updated\n- No mechanism to mark agent results as \"consumed\" — each notification required re-evaluation"
metadata:
  topic: multi-session-build-state-lost-during-context-compaction
  source: agentskill-kaizen plugin build (2026-02-18), 3 sessions with 1 compaction
  added: '2026-02-18'
  priority: P2
  type: Feature
  status: open
  issue: '#113'
  groomed: '2026-03-03'
---

## Story

As a **developer using Claude Code skills**, I want to **multi-session build state lost during context compaction** so that **the tooling becomes more capable and complete**.

## Description

During the agentskill-kaizen build (8-phase `/plugin-dev:create-plugin` workflow), context compaction mid-build converted structured task state into a narrative summary. The resuming session had to reconstruct "what's done vs pending" from prose rather than a checklist. Background agent results that were already consumed and applied reappeared as late notifications after compaction, requiring manual deduplication ("did I already handle this?"). No persistent artifact tracked phase completion, commit SHAs per phase, deferred items, or agent result consumption status.
**Observed symptoms**:
- Phase completion status existed only in ephemeral context — lost on compaction
- Background agent notifications arrived after their findings were already applied (3 duplicate notifications)
- Plan committed early (`87a0b93`) diverged from actual implementation but was never updated
- No mechanism to mark agent results as "consumed" — each notification required re-evaluation

## Context

- **Source**: agentskill-kaizen plugin build (2026-02-18), 3 sessions with 1 compaction
- **Priority**: P2
- **Added**: 2026-02-18
- **Research questions**: None

## Fact-Check

Claims checked: 5
VERIFIED: 4 | REFUTED: 0 | INCONCLUSIVE: 1

- VERIFIED: "8-phase /plugin-dev:create-plugin workflow" — agentskill-kaizen build is confirmed at plugins/agentskill-kaizen/ and plan at .claude/kaizen-plugin-plan.md documents phases 1-8
- VERIFIED: "context compaction converts structured task state into narrative summary" — documented Claude Code behavior; confirmed by related items #115 and #317 which describe the same compaction symptom
- VERIFIED: "background agent results reappeared as late notifications" — confirmed directly by item #115 (3 review agents: plugin-validator, 2× skill-reviewer; findings applied in commit 0d61480, redelivered in session 3)
- VERIFIED: "no persistent artifact tracked phase completion or agent result consumption" — codebase search found no mechanism; plan/ directory has feature-context for #117 addressing part of this problem
- INCONCLUSIVE: "plan committed early diverged from actual implementation" — the referenced commit SHA was local to the build session and is not in this repo; plan artifact divergence is confirmed separately by issue #117 and its feature-context at plan/feature-context-plan-artifact-lifecycle.md

Citations:
- plugins/agentskill-kaizen/ — plugin existence
- .claude/kaizen-plugin-plan.md — 8-phase structure
- .claude/backlog/p2-background-agent-result-deduplication-after-compaction.md — agent result redelivery (item #115)
- plan/feature-context-plan-artifact-lifecycle.md — plan artifact divergence (issue #117)

## RT-ICA

Goal: Provide a persistent, session-agnostic build state artifact that survives context compaction and lets a resuming session accurately reconstruct phase completion status, consumed agent results, and diverged plan artifacts.

Conditions:
1. Context compaction converts structured state to prose (Claude Code native behavior) | Status: AVAILABLE | Info needed: None
2. No existing persistent phase/state tracking mechanism in the repo | Status: AVAILABLE | Info needed: None (confirmed by codebase search)
3. Agent result notifications lack a 'consumed' marking mechanism | Status: AVAILABLE | Info needed: None (confirmed by item #115)
4. Related items #114, #115, #317, #117 expose the same problem class from different angles | Status: AVAILABLE | Info needed: Cross-item dependency map
5. Sessions framework (.claude/commands/sessions.md) and @logging agent exist | Status: DERIVABLE | Info needed: Whether they cover multi-phase build state or only single-session logs
6. Plan artifact lifecycle policy (issue #117) partially addresses plan divergence | Status: DERIVABLE | Info needed: Whether #117 scope covers phase completion tracking or is limited to plan divergence

Decision: APPROVED
Missing: None

## Groomed (2026-03-03)

### Reproducibility

1. Run the `/plugin-dev:create-plugin` 8-phase workflow across multiple sessions (minimum 2 sessions with 1 context compaction event).
2. In Session 1, complete several phases. Allow background review agents (e.g., plugin-validator, skill-reviewer) to complete and have their findings applied to commits.
3. Let context compaction fire mid-build (naturally, by filling the context window on a long build).
4. Start Session 2. Attempt to answer: Which phases are complete? Which are pending? Which background agent results have already been applied?
5. Observe that the only source of truth is the compaction-produced prose summary; no durable checklist or agent-result ledger exists.

The same pattern reproduces on any multi-session workflow using `/implement-feature` or `/work-backlog-item` that spans a compaction event.

### Output / Evidence

- **Phase state**: Resuming session must reconstruct completion status from compaction prose — no checklist survives.
- **Duplicate agent notifications**: 3 `<task-notification>` messages from plugin-validator and 2× skill-reviewer reappeared in Session 3 after their findings were already applied in commit `0d61480` (item #115). Each required manual re-evaluation ("was this already handled?").
- **Plan drift**: `.claude/kaizen-plugin-plan.md` (8-phase structure) was not updated after implementation decisions diverged during Phase 5 (confirmed by issue #117 and `plan/feature-context-plan-artifact-lifecycle.md`).
- **No consumed-marker mechanism**: `.claude/hooks/` contains `stop-backlog-reminder.cjs`, `run-commands-try-all.cjs`, and `validate-delegation.cjs` — no pre-compact hook exists. `settings.json` registers only a `Setup` hook.
- **No phase-state file**: Full codebase search found no artifact tracking completed phases, task IDs, or agent result consumption status for any workflow.

### Priority

**7/10** — Affects every multi-session, multi-phase workflow in the repo. Compaction is a routine event for long builds, not an edge case. Four distinct symptoms (#113, #114, #115, #317) have already been filed against the same absent mechanism, indicating the gap is structurally recurring rather than incidental.

### Impact

- **Blocked workflows**: `/plugin-dev:create-plugin`, `/implement-feature`, `/work-backlog-item` — any workflow spanning more than one session or triggering compaction.
- **Resuming sessions** waste time reconstructing state from prose and re-evaluating already-consumed agent results.
- **Plan artifacts** diverge silently from implementation, making plan files unreliable after compaction (overlap with issue #117).
- **Developer trust**: Repeated duplicate notifications erode confidence in the agent result delivery system.

### Expected Behavior

When context compaction fires mid-build, a durable state artifact already exists in the repository (not in context). A session starting after compaction reads that artifact and knows — without re-reading the full message history — which phases are complete, which background agent results have been consumed and applied, and what the next pending step is. Background agent `<task-notification>` messages that have already been applied do not require re-evaluation; their consumed status is visible in the artifact.

### Acceptance Criteria

1. After a compaction event in a multi-phase build, a resuming session can enumerate which phases are complete and which are pending by reading a file in the repository — not from prose context alone.
2. Background agent results that were applied before compaction are distinguishable from results that have not yet been evaluated. The resuming session does not re-evaluate results that are already marked consumed.
3. When a resuming session starts, the phase completion state it reconstructs from the durable artifact matches the actual state of the codebase (committed files, passing validations) for the phases recorded as complete.
4. The state artifact is updated before or at the point of compaction — it is not written only at session end and therefore cannot be lost by an unexpected compaction.
5. Any workflow that spans two or more sessions leaves a state artifact that a third session (with no shared context with sessions 1 or 2) can read to reconstruct progress.
6. The mechanism does not require manual intervention from the human operator to function — it is triggered automatically as part of normal workflow execution.

### Issue Classification

**Type**: recurring-pattern
**Rationale**: The same problem class — state that exists only in ephemeral context being lost on compaction or session restart — appears in at least 4 separate backlog items (#113 this item, #114 intra-phase parallelism tracking, #115 agent result deduplication, #317 structured session work logs). Each item describes a different symptom of the same root absence: no durable, session-agnostic state artifact for multi-phase builds.
**Analysis Method**: 6-sigma
**Scenario Target**: Multi-phase build (agentskill-kaizen, 3 sessions, 1 compaction) with no persistent state → resuming session reconstructs status from prose + duplicate agent notifications

### Root-Cause Analysis

**Method**: 6-sigma
**Classification**: recurring-pattern

#### Measurement

- **Frequency**: 4 symptom occurrences in the same event batch (agentskill-kaizen build, Feb 2026):
  - #113 (this) — phase completion state lost at compaction
  - #114 — intra-phase parallelism tracking absent; no per-sub-task completion gate
  - #115 — background agent result notifications re-delivered post-compaction; no consumed marker
  - #317 — no pre-compact hook to snapshot work log before compression fires
- **Common factors**: All symptoms stem from the same absent mechanism — a durable, session-agnostic build state file that survives context compaction. All occurred in multi-session, multi-phase workflows.
- **Affected scope**: Any workflow spanning more than one session or triggering compaction: `/plugin-dev:create-plugin`, `/implement-feature`, `/work-backlog-item`. The agentskill-kaizen build is the observed instance; the gap is structural.

#### Analysis

- **Root cause pattern**: SAM workflow and plugin-dev workflow store all phase/task state exclusively in the in-context message history. No hook, script, or skill writes a durable mid-workflow state artifact. When compaction fires, the message history is summarised into prose and the structured state (checklist, phase marker, agent task IDs) is lost.
- **Missing guardrail**: A pre-compact hook that snapshots current workflow state into a durable file before compaction runs. The `.claude/hooks/` directory exists and the hook infrastructure is active (3 existing hooks), but no pre-compact hook is registered. `settings.json` has no `PreCompact` entry.

#### Improvement

- **Proposed guardrail**: A pre-compact state snapshot mechanism that writes a durable file recording (1) completed phases/tasks as a checklist, (2) consumed agent result task IDs, (3) active plan file path and known divergences, and (4) next pending phase/task. Session start reads the most recent state file and injects it as context before reasoning begins.
- **Verification**: After a simulated compaction in a test session, a resuming session can read the state file and answer — without re-reading the full message history — which phases are done, which agent results were consumed, and what the next task is.

### Resources

| Type | Item |
|------|------|
| Agent | `@logging` — `.claude/agents/logging.md` — produces structured work logs from transcripts at compaction |
| Skill | `session-historian` — `.claude/skills/session-historian/` — searches JSONL transcripts; consumer of session summaries |
| Skill | `work-backlog-item` — `.claude/skills/work-backlog-item/` — multi-session workflow entry point |
| Skill | `implement-feature` — `.claude/skills/implement-feature/` — multi-phase orchestration workflow |
| Hooks | `.claude/hooks/` — active hook directory (3 hooks present); no pre-compact hook registered |
| Config | `.claude/settings.json` — `hooks` block; `Setup` hook registered; no `PreCompact` entry |
| Prior work | `plan/feature-context-plan-artifact-lifecycle.md` — feature context for issue #117 (plan divergence; overlapping scope) |
| Prior work | `plan/tasks-6-plan-artifact-lifecycle.md` — task plan for issue #117 |
| Prior work | `.claude/kaizen-plugin-plan.md` — 8-phase build plan; exhibits the problem |

### Dependencies

**This item depends on:**
- **#317** (`p1-structured-session-work-logs-with-pre-compact-and-session-st.md`) — defines the pre-compact hook and work log convention this item's state artifact would build on; the two items share the same missing infrastructure layer.

**This item overlaps with:**
- **#115** (`p2-background-agent-result-deduplication-after-compaction.md`) — the consumed-marker sub-problem; a state artifact solving #113 would subsume or directly enable the solution to #115.
- **#114** (`p2-plugin-dev-create-plugin-workflow-lacks-intra-phase-parallel.md`) — intra-phase parallelism tracking; a phase-state artifact is a prerequisite for tracking sub-task completion within a phase.
- **#117** — plan divergence; a state artifact tracking active plan file path and known divergences provides the hook point for #117's freshness check.

**This item would unblock:**
- Any grooming or planning work on #114 and #115 that requires a shared persistent state artifact as a foundation.

### Effort

**Medium** — The hook infrastructure and logging agent already exist. The gap is the absence of a registered pre-compact hook, a defined state file schema, and a session-start read step. No new scripting language or framework is required. Coordination with #317 (which targets the same hook slot) is needed to avoid conflicting implementations.