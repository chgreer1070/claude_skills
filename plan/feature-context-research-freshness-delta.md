# Feature Context: Research Freshness as Delta Indicator

## Document Metadata

- **Generated**: 2026-03-06
- **Input Type**: simple_description
- **Source**: GitHub issue #444 — "Research freshness should be a delta indicator, not a blocker"
- **Status**: DISCOVERY_COMPLETE

---

## Original Request

The research-curator and refresh-research skills currently block re-research when entries haven't reached their "Next Review Recommended" date. This gate should be removed — freshness should be informational context (a delta), not a stop condition.

Problem observed 2026-03-06: `everything-claude-code` entry was 8 days old (researched 2026-02-26, next review 2026-05-26) but the project shipped TWO major releases (v1.7.0, v1.8.0), gained 10K stars, added new agents and skills, and completely repositioned itself.

---

## Core Intent Analysis

### WHO (Target Users)

- Users invoking `/research-curator` in batch mode who want to refresh an already-existing entry
- Users invoking `/refresh-research` with `--stale` (default) or `--all` who want full control over which entries get refreshed
- Automated pipelines running `/refresh-research --stale` or `/refresh-research --all` on a schedule

### WHAT (Desired Outcome)

Freshness dates (Last Verified, Next Review Recommended) should be displayed as contextual delta information alongside every research operation and refresh decision — not used as a gate that stops the operation. A user or automated caller should be able to re-research any entry at any time, regardless of its current review date. The freshness fields become "how stale is this?" context, not "should we proceed?" guards.

### WHEN (Trigger Conditions)

- When a user re-submits a URL to `/research-curator --batch` and the entry already exists
- When a user invokes `/refresh-research --all` and some entries are not yet past their review date
- When a user invokes `/refresh-research` (default `--stale`) but wants to override the staleness gate for a specific known-stale entry
- When an external event (major release, significant community growth) makes a "fresh" entry factually outdated before its review date

### WHY (Problem Being Solved)

The current freshness date is derived from a fixed 3-month schedule baked into the entry template (`./research-curator/references/entry-template.md:181`). This schedule is blind to real-world events. A project can ship two major releases and gain 10K stars within 8 days of its last research entry, yet the freshness gate blocks re-research for another ~82 days. The gate optimizes for avoiding redundant work but at the cost of correctness. The user's goal is accurate research, not minimized agent invocations.

---

## Codebase Research

### Similar Patterns Found

#### Pattern 1: Batch Mode Duplicate Skip in `/research-curator` SKILL.md

- **Location**: `.claude/skills/research-curator/SKILL.md:166`
- **Relevance**: This is Blocking Site #1. When an entry already exists for a URL, Batch Mode skips it with the message "skip with info message suggesting `--rerun` instead." This is a hard skip — the entry is not refreshed, not compared, and the user receives no staleness delta. The workaround (`--rerun`) requires the user to know the exact file path.
- **Reusable**: The duplicate detection check itself is useful. What changes is the action taken: instead of `skip with info message`, it should `proceed and report delta` (or at minimum, report freshness context and let the user decide).

#### Pattern 2: Staleness Flowchart `FRESH: skip` Terminal in `/refresh-research` SKILL.md

- **Location**: `.claude/skills/refresh-research/SKILL.md:31-39` (Step 1 Mermaid flowchart)
- **Relevance**: This is Blocking Site #2. The flowchart has two terminal outcomes from freshness evaluation: `STALE` (proceed) and `FRESH: skip`. The `FRESH: skip` terminal is an unconditional stop. Entries that are `FRESH` never reach Step 4 (agent spawning) under any invocation path except `--all`.
- **Reusable**: The staleness detection logic itself (parse frontmatter, compare dates, check 6-month threshold) is the right foundation for producing a delta. The delta replaces the binary skip/proceed decision.

#### Pattern 3: `--all` Flag as Existing Override

- **Location**: `.claude/skills/refresh-research/SKILL.md:16` (Arguments section)
- **Relevance**: `--all` already bypasses the staleness filter (Step 2: "keep all entries (no staleness filter)"). This proves the intent exists — users should be able to refresh regardless of staleness. The gap is that `--all` is all-or-nothing; there's no way to say "refresh this specific known-stale entry that the date gate thinks is fresh."
- **Reusable**: The `--all` bypass pattern is the correct model to extend or generalize.

#### Pattern 4: Freshness Tracking Section in Entry Template

- **Location**: `.claude/skills/research-curator/references/entry-template.md:168-175`
- **Relevance**: The Freshness Tracking table (`Last Verified`, `Version at Verification`, `Next Review Recommended`) is the data structure that feeds both blocking sites. These fields exist to inform humans and agents — they were not designed as hard gates. The feature request repositions them as context, not control flow.
- **Reusable**: The three-field structure is the right vehicle for delta presentation. The delta could surface as "last verified N days ago, review due in M days, version at verification was X."

### Existing Infrastructure

- **`--rerun` mode** in `@research-curator` agent (`.claude/agents/research-curator.md:51-55`): already re-gathers from primary sources and updates content. This is the refresh mechanism. The gap is not in the refresh logic itself but in whether the caller (skill or user) can reach `--rerun` without being stopped by the freshness gate.
- **`--dry-run` flag** in `/refresh-research` (`.claude/skills/refresh-research/SKILL.md:19`): shows what would be refreshed without acting. Could be extended to show freshness deltas for all entries regardless of staleness status.
- **Inventory table** built in Step 1 of `/refresh-research` (`.claude/skills/refresh-research/SKILL.md:42`): already computes `Last Verified`, `Next Review`, and `Stale?` per entry. This table is the natural place to add a computed "days until/since review" delta column.

### Code References

- `.claude/skills/research-curator/SKILL.md:163-167` — Batch Mode duplicate detection and skip logic
- `.claude/skills/refresh-research/SKILL.md:30-40` — Staleness flowchart with `FRESH: skip` terminal
- `.claude/skills/refresh-research/SKILL.md:50-58` — Step 2 scope filter, `--all` vs `--stale` logic
- `.claude/skills/refresh-research/SKILL.md:158-159` — Error handling: "All entries are fresh. Nothing to refresh." stop condition
- `.claude/skills/research-curator/references/entry-template.md:168-183` — Freshness Tracking fields and schedule (3-month review, 6-month stale threshold)
- `.claude/agents/research-curator.md:51-55` — `--rerun` mode workflow (re-gather, re-extract, update)

---

## Use Scenarios

### Scenario 1: Known Major Release in a Fresh Entry

**Actor**: Developer tracking fast-moving AI tooling
**Trigger**: Hears that a tool released v2.0 with breaking API changes; checks the research entry; sees it was researched 3 weeks ago (next review 9 weeks away)
**Goal**: Immediately refresh the entry to capture the v2.0 changes before using the tool in a project
**Expected Outcome**: Re-research proceeds. Freshness context shown ("last verified 21 days ago, was v1.8, next review originally due in 63 days") as informational delta, not as a blocker. Entry is updated with v2.0 data.

### Scenario 2: Batch Re-Research of Multiple URLs

**Actor**: User running weekly discovery sweep
**Trigger**: Runs `/research-curator --batch url1 url2 url3` where two of the URLs already have entries researched 6 weeks ago
**Goal**: Refresh all three with current data in one command
**Expected Outcome**: All three entries researched. For existing entries, current freshness delta reported ("entry exists, last verified 42 days ago"). No skip. No "use --rerun instead" deflection.

### Scenario 3: Automated Nightly Stale Refresh

**Actor**: CI pipeline running `/refresh-research --stale` nightly
**Trigger**: Scheduled job
**Goal**: Refresh any entry that has real staleness, get no-ops for entries that are genuinely current
**Expected Outcome**: Entries past their review date are refreshed (same as today). Entries not past their review date are skipped. Summary shows "N refreshed, M skipped (fresh)" with per-entry deltas visible in `--dry-run` or verbose output. The distinction between "skipped because fresh" and "refreshed because stale" is preserved — only the behavior of explicitly requesting a fresh entry changes.

### Scenario 4: `--all` Refresh with Delta Reporting

**Actor**: User preparing a comprehensive research update before a major project kick-off
**Trigger**: Runs `/refresh-research --all`
**Goal**: Re-verify every entry; see which ones had meaningful changes vs. no changes
**Expected Outcome**: All entries refreshed. Per-entry delta shows "Updated (v1.7→v1.8, +10K stars)" vs. "Unchanged (confirmed current)". Today this already works since `--all` bypasses the staleness filter; the scenario highlights that the delta reporting is already partially in place via the "Updated / Unchanged / Failed" outcome categories in Step 4 wave results.

---

## Gap Analysis

### Identified Gaps

| # | Category | Gap Description | Impact |
|---|----------|-----------------|--------|
| 1 | Behavior | Batch Mode in `/research-curator` SKILL.md unconditionally skips existing entries; no delta shown | User cannot refresh a known-stale entry via `--batch`; must know file path to use `--rerun` |
| 2 | Behavior | `FRESH: skip` terminal in `/refresh-research` Step 1 flowchart is unconditional; no escape except `--all` | A "fresh" entry with a known breaking upstream change cannot be targeted for refresh without `--all` (which refreshes everything) |
| 3 | Scope | `--stale` default behavior: unclear whether it should change at all, or only behavior for explicit single-entry requests should change | If `--stale` continues to skip fresh entries by date, the fix may only apply to explicit re-invocations (batch URL, single `--rerun`) |
| 4 | Behavior | No delta is surfaced when an entry is skipped due to freshness; user receives no actionable information | User cannot tell how stale the entry is or when it will be eligible for refresh |
| 5 | User | `--rerun` workaround requires the user to know the exact file path (`./research/category/name.md`); batch URL re-submission should not require this knowledge | Friction cost proportional to number of URLs being re-researched |
| 6 | Integration | Scope of change: does the fix apply to `/refresh-research` SKILL.md, `/research-curator` SKILL.md, or both? | Two separate files have independent skip logic; partial fix leaves one blocking site intact |
| 7 | Scope | The `--stale` automation use case (scenario 3): should `/refresh-research --stale` behavior change at all, or should it remain date-gated for automated runs while only interactive/explicit re-research becomes ungated? | If `--stale` changes behavior, automation pipelines relying on it as a guard may over-refresh |

---

## Questions Requiring Resolution

### Q1: Should `--stale` default behavior change?

- **Category**: Scope
- **Gap**: Gap #3 and Gap #7 — `--stale` is used in automation as a cost control (don't re-research entries that are likely still accurate). Removing the freshness gate here may cause automation to over-refresh.
- **Question**: Should the `FRESH: skip` gate be removed for all invocations of `/refresh-research`, or only when the user explicitly targets a specific entry (e.g., `--category`, a specific entry path) or passes a new explicit override flag?
- **Options**:
  - A) Remove the gate entirely — `--stale` and `--all` behave identically (both refresh everything)
  - B) Keep the gate for `--stale` (automation-safe), remove it only for `--all` (explicit intent)
  - C) Add a new `--force` flag that bypasses the date gate for any scope, leaving existing flags unchanged
  - D) Keep `--stale` gated, but change the skip action: instead of silently skipping, report the freshness delta for skipped entries
- **Why It Matters**: The answer determines whether the fix is additive (new flag) or a behavior change to existing flags. Automation pipelines using `--stale` may break under option A.
- **Resolution**: _pending_

### Q2: Should Batch Mode in `/research-curator` auto-rerun existing entries or require explicit intent?

- **Category**: Behavior
- **Gap**: Gap #1 — current Batch Mode skips existing entries with "use --rerun instead". The question is whether the fix means "always rerun" or "rerun if the user explicitly asked for it (i.e., they submitted the URL again)."
- **Question**: When a user submits a URL to `--batch` that already has an entry, should the skill (a) automatically rerun it, (b) show the freshness delta and ask for confirmation, or (c) show the delta in the skip message so the user can decide whether to `--rerun`?
- **Options**:
  - A) Auto-rerun (submit URL = intent to refresh)
  - B) Show delta, prompt user for confirmation per entry
  - C) Show delta in skip message, user manually decides (no behavior change to the skip action, only to the information reported)
- **Why It Matters**: Option A may surprise users who just want to check if an entry exists. Option C is the minimal change (information only, no flow change).
- **Resolution**: _pending_

### Q3: What delta fields should be surfaced and in what format?

- **Category**: Behavior
- **Gap**: Gap #4 — when freshness is informational, what information exactly should be shown?
- **Question**: What data should appear in the delta indicator? Candidates: days since last verified, days until/since review date, version at last verification, current star count comparison. Should this appear in the skip/info message only, or also in the Summary Report table?
- **Options**:
  - A) Minimal: "last verified N days ago, next review was {date}" in the skip/info message
  - B) Full: add a computed `Days Since Verified` and `Days Until Review` column to the inventory table in Step 1
  - C) Version-aware: include `Version at Last Verification` so the user can spot version drift without re-researching
- **Why It Matters**: The format determines how much new text surfaces in output and whether agents downstream need to parse it.
- **Resolution**: _pending_

### Q4: Does the `@research-curator` agent itself need any changes?

- **Category**: Integration
- **Gap**: The blocking occurs in the skill orchestrators (SKILL.md files), not in the agent. The agent's `--rerun` mode already works. Confirming this scope boundary matters.
- **Question**: Is the fix entirely in the two SKILL.md files (`/research-curator` Batch Mode and `/refresh-research` Step 1), with no changes needed to `.claude/agents/research-curator.md`?
- **Options**:
  - A) Yes — agent is unchanged; only skill orchestration logic changes
  - B) No — the agent needs to return freshness delta in its result block so the orchestrator can surface it
- **Why It Matters**: Option B means the agent's Return Format needs a new field, which broadens the scope.
- **Resolution**: _pending_

### Q5: Should freshness delta appear in `--dry-run` output?

- **Category**: Behavior
- **Gap**: `/refresh-research --dry-run` currently shows what would be refreshed (filtered target list). It does not show deltas for skipped fresh entries.
- **Question**: Should `--dry-run` show the full inventory including fresh entries with their deltas, so users can audit the complete freshness state before deciding to use `--all` or a targeted flag?
- **Options**:
  - A) Yes — `--dry-run` shows all entries with freshness deltas regardless of staleness filter
  - B) No — `--dry-run` only shows what the current invocation scope would target (unchanged behavior)
- **Why It Matters**: If `--dry-run` shows deltas for all entries, it becomes a freshness audit tool regardless of which refresh command follows.
- **Resolution**: _pending_

---

## Goals (Pending Resolution)

_These goals will be finalized after questions are resolved._

1. Remove or bypass the `FRESH: skip` terminal in `/refresh-research` Step 1 for at least some invocation paths (scope to be determined by Q1)
2. Remove or modify the Batch Mode duplicate-skip in `/research-curator` so freshness delta is shown rather than a hard stop (scope to be determined by Q2)
3. Surface a freshness delta (days since verified, days until/since review) wherever a skip or info message currently appears (format to be determined by Q3)
4. Preserve the `--stale` automation use case — date-gated refreshes should remain available for cost-controlled automated runs (Q1 resolution must not break this)
5. Ensure `--rerun` remains a valid explicit path and is not made redundant or ambiguous by the new behavior

---

## Next Steps

After questions are resolved:

1. Update "Resolution" fields in Questions section
2. Finalize Goals section
3. Proceed to RT-ICA assessment
4. Then proceed to architecture design
