# Feature Context: Backlog Lifecycle Promotion

SOURCE: Research conducted 2026-03-01 against `.claude/docs/backlog-lifecycle.draft.md` (674 lines),
`.claude/skills/backlog-tools-administrator/references/domain-registry.md`,
`.claude/skills/backlog/references/state-machine.md`,
`.claude/skills/backlog/references/item-schema.md`,
`.claude/skills/work-backlog-item/SKILL.md`,
`.claude/skills/groom-backlog-item/SKILL.md`,
`.claude/project_workflow.draft.md`,
`.github/workflows/backlog-sync.yml`.

Issue: #286

---

## Problem Statement

The backlog tooling ecosystem has a comprehensive lifecycle document (`backlog-lifecycle.draft.md`, 674 lines) that documents the full item lifecycle, data flow, state transitions, label mapping, and file structure. However, it remains in draft status with 17 unresolved `[VERIFY]` annotations and a 7-category testing checklist (25 individual test items). Until these annotations are resolved against live `backlog.py` behavior and cross-references are established, agents and skills cannot treat this document as canonical. The existing canonical references (`state-machine.md`, `item-schema.md`) cover subsets of the lifecycle but not the full data flow, sync behavior, or cleanup semantics that `backlog-lifecycle.draft.md` documents.

---

## Current State

### Draft File

- **Path**: `.claude/docs/backlog-lifecycle.draft.md`
- **Size**: 674 lines, 8 sections
- **Created**: 2026-02-27
- **Status**: DRAFT — derived from reading source files, not from observing live script behavior
- **Sources cited**: `backlog/SKILL.md`, `state-machine.md`, `item-schema.md`, `backlog.py` (lines 1-100), `work-backlog-item/SKILL.md`, `create-backlog-item/SKILL.md`, `groom-backlog-item/SKILL.md`

### Existing Canonical References

| Document | Path | Coverage |
|----------|------|----------|
| State machine | `.claude/skills/backlog/references/state-machine.md` | States, transitions, label taxonomy, critical constraints |
| Item schema | `.claude/skills/backlog/references/item-schema.md` | Frontmatter fields, body sections, completeness states |
| Domain registry | `.claude/skills/backlog-tools-administrator/references/domain-registry.md` | 31-file inventory of all backlog ecosystem files |

### Gaps the Draft Fills

The draft covers material not present in existing canonical references:

1. **Data architecture** (3-layer system: GitHub Issues, local files, `backlog.py`)
2. **Sync direction and timing** (push vs. pull, when items are local-only vs. synced)
3. **Detailed command signatures** for each state transition (`add`, `sync`, `groom`, `update`, `close`, `resolve`, `pull`)
4. **File structure annotated example** with every frontmatter and body field in context
5. **Cleanup behavior** (`--cleanup` flag semantics, local file deletion)
6. **GitHub Action integration** (automatic sync on push to `.claude/backlog/`)
7. **Post-merge behavior** (how `backlog sync` handles closed issues)

---

## [VERIFY] Annotation Catalog

17 annotations found across 7 sections. Categorized by verification method required.

### Category A: Script Flag/Subcommand Existence (run `--help` to verify)

| # | Line | Annotation | Verification Method |
|---|------|-----------|-------------------|
| 1 | 41 | `[VERIFY: pull subcommand behavior]` — whether `backlog pull` exists and refreshes stale local files | `uv run .claude/skills/backlog/scripts/backlog.py pull --help` |
| 2 | 246 | `[VERIFY: whether backlog close has --cleanup flag]` — optional cleanup flag on close | `uv run .claude/skills/backlog/scripts/backlog.py close --help` |
| 3 | 274 | `[VERIFY: cleanup flag presence on resolve]` — whether `--cleanup` exists on resolve | `uv run .claude/skills/backlog/scripts/backlog.py resolve --help` |
| 4 | 378 | `[VERIFY: flag exists]` — `backlog close --cleanup` flag existence (duplicate of #2) | Same as #2 |
| 5 | 379 | `[VERIFY: flag exists]` — `backlog resolve --cleanup` flag existence (duplicate of #3) | Same as #3 |
| 6 | 421 | `[VERIFY: whether backlog update supports --priority flag]` — re-prioritization support | `uv run .claude/skills/backlog/scripts/backlog.py update --help` |

### Category B: Script Behavior Observation (run command and observe output)

| # | Line | Annotation | Verification Method |
|---|------|-----------|-------------------|
| 7 | 119-121 | `[VERIFY] The GitHub Action triggers backlog sync when .claude/backlog/ files are changed` | Read `.github/workflows/backlog-sync.yml` — **ALREADY VERIFIED**: workflow triggers on `push` to `main` with path `.claude/backlog/**`, runs `backlog.py sync`. This annotation can be resolved as CONFIRMED. |
| 8 | 165-166 | `[VERIFY: whether the script pushes body to GH on every groom call or only on explicit sync]` | Run `backlog.py groom` with a test item that has a linked issue, then check issue body via `gh issue view` |
| 9 | 291 | `[VERIFY: exact pull behavior — inferred from docstring]` — full pull behavior | Run `backlog.py pull --dry-run` and observe output |
| 10 | 297 | `[VERIFY]` — whether `--force` flag exists on `pull` and its behavior | `uv run .claude/skills/backlog/scripts/backlog.py pull --help` and test with `--force` |
| 11 | 484 | `[VERIFY: whether groom sets status or only update does]` — does `backlog groom` set `metadata.status: groomed` directly | Run `backlog.py groom` on an item and read the file afterward to check `metadata.status` |
| 12 | 551 | `[VERIFY: exact skip logic in sync]` — how `backlog sync` handles items whose linked issues are already closed | Run `backlog.py sync` when a closed issue exists, observe if it skips or errors |

### Category C: External System Behavior (requires GitHub API observation or milestone skill)

| # | Line | Annotation | Verification Method |
|---|------|-----------|-------------------|
| 13 | 190 | `[VERIFY: exact command invoked by /group-items-to-milestone]` — what command the milestone skill uses | Read `/group-items-to-milestone` SKILL.md (if it exists) or search for the skill |
| 14 | 365 | `[VERIFY: GH Action timing]` — timing between file creation and GH Action trigger | Observe via `gh run list` after a push to `.claude/backlog/` on main |
| 15 | 380-381 | `[VERIFY: whether local files are deleted or only status is set to closed after /complete-milestone]` — milestone completion cleanup behavior | Read `/complete-milestone` SKILL.md or observe behavior |

### Category D: Atomicity / API Behavior

| # | Line | Annotation | Verification Method |
|---|------|-----------|-------------------|
| 16 | 661 | `[VERIFY with gh issue view N --json labels]` — whether label transitions are atomic (old removed + new added in same API call) | Read `backlog.py` label transition code, or run a status transition and observe label state mid-operation |

### Summary by Unique Annotation

After deduplication (#4 duplicates #2, #5 duplicates #3), there are **14 unique verifications** needed:

- **6** can be resolved by running `--help` on script subcommands
- **5** require running commands and observing output
- **2** require reading other skill files (milestone skills)
- **1** is already resolvable from reading the workflow file (annotation #7 — CONFIRMED)

---

## Testing Checklist Catalog

Section 7 of the draft contains 25 individual test items organized in 7 categories. Each is a `- [ ]` checkbox.

### 7.1 Data Architecture (4 tests)

| # | Test | What It Validates |
|---|------|------------------|
| T1 | `backlog add --no-create-issue` produces no GitHub API call | P2/Ideas items stay local-only at creation |
| T2 | `backlog add --create-issue` writes `metadata.issue: '#N'` | Issue number writeback on explicit creation |
| T3 | `backlog sync` skips items with existing `metadata.issue` | Sync idempotency — no duplicate issues |
| T4 | `backlog sync --dry-run` shows planned actions without writing | Dry-run safety for sync |

### 7.2 State Transitions (5 tests)

| # | Test | What It Validates |
|---|------|------------------|
| T5 | `backlog groom --section` appends without overwriting | Incremental grooming does not destroy existing sections |
| T6 | `metadata.groomed` set only after all 7 sections present | Groomed status gate — partial grooming is not groomed |
| T7 | `backlog update --status in-progress` with/without prior `--plan` | Whether status and plan are independent or coupled |
| T8 | `backlog close` without `--checklist-pass` is rejected | Close safety gate |
| T9 | `backlog resolve` without `--reason` is rejected | Resolve requires explicit reason |

### 7.3 Cleanup Behavior (4 tests)

| # | Test | What It Validates |
|---|------|------------------|
| T10 | `--cleanup` flag exists on `backlog close` | Cleanup flag existence (maps to VERIFY #2/#4) |
| T11 | `--cleanup` flag exists on `backlog resolve` | Cleanup flag existence (maps to VERIFY #3/#5) |
| T12 | `backlog close --cleanup` deletes vs. marks local file | Actual cleanup behavior |
| T13 | `/complete-milestone` effect on local files | Milestone completion cleanup (maps to VERIFY #15) |

### 7.4 Pull / Bidirectional Sync (3 tests)

| # | Test | What It Validates |
|---|------|------------------|
| T14 | `backlog pull --dry-run` shows GH vs. local diff | Pull dry-run works |
| T15 | `backlog pull` overwrites `metadata.status` from GH label | Pull updates status correctly |
| T16 | `backlog pull` does not overwrite `metadata.plan` or `metadata.groomed` with empty values | Pull preserves local-only fields |

### 7.5 Priority and Label Mapping (3 tests)

| # | Test | What It Validates |
|---|------|------------------|
| T17 | P2/Ideas items never get GH issues via `backlog sync` | Priority-based sync filtering |
| T18 | Label transitions are atomic (old removed + new added in same call) | Label atomicity (maps to VERIFY #16) |
| T19 | `backlog update --priority` exists or confirm re-prioritization path | Priority change support (maps to VERIFY #6) |

### 7.6 GitHub Action Integration (3 tests)

| # | Test | What It Validates |
|---|------|------------------|
| T20 | GH Action triggers on `.claude/backlog/` file changes | Workflow trigger config (maps to VERIFY #7 — CONFIRMED by reading `backlog-sync.yml`) |
| T21 | Action calls `backlog sync` (not a different command) | Correct command in workflow (CONFIRMED: line 36 of `backlog-sync.yml`) |
| T22 | Action runs with GITHUB_TOKEN available | Token availability in workflow (CONFIRMED: line 34 of `backlog-sync.yml`) |

### 7.7 Post-Merge Behavior (3 tests)

| # | Test | What It Validates |
|---|------|------------------|
| T23 | After merging a PR that fixes `#N`, issue is closed on GH | GitHub auto-close via `Fixes #N` |
| T24 | `backlog sync` after merge skips closed items | Sync skip logic (maps to VERIFY #12) |
| T25 | `backlog list` excludes or marks closed/resolved items | List filtering behavior |

### Pre-Resolved Tests

Tests T20, T21, and T22 can be resolved immediately by reading `.github/workflows/backlog-sync.yml`:

- **T20**: CONFIRMED — triggers on `push` to `main` with `paths: [".claude/backlog/**"]`
- **T21**: CONFIRMED — step runs `uv run .claude/skills/backlog/scripts/backlog.py sync -R Jamie-BitFlight/claude_skills`
- **T22**: CONFIRMED — `GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}` set in env

---

## Cross-Reference Plan

### Files That Need to Link TO `backlog-lifecycle.md`

| File | Current State | Link to Add |
|------|--------------|-------------|
| `.claude/skills/work-backlog-item/SKILL.md` | References `state-machine.md`, `item-schema.md`, `github-integration.md` but not the lifecycle doc | Add link in GitHub Integration section or as a top-level reference |
| `.claude/skills/groom-backlog-item/SKILL.md` | References `backlog-item-groomed-schema.md` but not the lifecycle doc | Add link in Step 7 (write groomed content) where sync behavior is discussed |
| `.claude/skills/backlog-tools-administrator/references/domain-registry.md` | Lists `backlog-lifecycle.draft.md` under "Documentation and Schema" | Update path from `.draft.md` to `.md` after rename |
| `.claude/project_workflow.draft.md` | Contains a Data Architecture section that overlaps with lifecycle doc content | Add link to lifecycle doc in Data Architecture section as the canonical reference |
| `.claude/skills/backlog/references/state-machine.md` | Standalone state machine reference; no link to lifecycle doc | Add link: "For full lifecycle data flow and sync behavior, see backlog-lifecycle.md" |
| `.claude/skills/backlog/references/item-schema.md` | Standalone schema reference; no link to lifecycle doc | Add link: "For lifecycle context of each field, see backlog-lifecycle.md" |
| `.claude/skills/backlog/SKILL.md` | Script documentation skill | Add link as a reference for understanding the full lifecycle |

### Links That `backlog-lifecycle.md` Needs BACK

| Target | Link Purpose |
|--------|-------------|
| `.claude/skills/backlog/references/state-machine.md` | Canonical state diagram (already referenced in draft source list but not as a markdown link) |
| `.claude/skills/backlog/references/item-schema.md` | Canonical frontmatter schema |
| `.claude/skills/work-backlog-item/SKILL.md` | `/work-backlog-item` skill (referenced as trigger in multiple states) |
| `.claude/skills/groom-backlog-item/SKILL.md` | `/groom-backlog-item` skill (referenced as trigger in State 3) |
| `.claude/skills/create-backlog-item/SKILL.md` | `/create-backlog-item` skill (referenced as trigger in State 1) |
| `.claude/skills/backlog/scripts/backlog.py` | The sole interface script |
| `.claude/project_workflow.draft.md` | The overall workflow diagram |
| `.github/workflows/backlog-sync.yml` | GitHub Action that triggers sync |

### Domain Registry Update

The domain registry at `.claude/skills/backlog-tools-administrator/references/domain-registry.md` lists the file as:

```text
- `.claude/docs/backlog-lifecycle.draft.md` — Lifecycle documentation (draft)
```

After promotion, this entry must be updated to:

```text
- `.claude/docs/backlog-lifecycle.md` — Lifecycle documentation (canonical)
```

---

## Scope

### In Scope

1. Run the 25-item testing checklist against live `backlog.py` behavior (section 7)
2. Resolve all 17 `[VERIFY]` annotations (14 unique) by executing described commands and observing results
3. Update draft content based on verification results (correct inaccuracies, confirm behaviors)
4. Rename `.claude/docs/backlog-lifecycle.draft.md` to `.claude/docs/backlog-lifecycle.md`
5. Remove the DRAFT status banner (lines 1, 4-6) and `[VERIFY]` annotations from the promoted file
6. Add two-way cross-references:
   - 7 files linking TO `backlog-lifecycle.md`
   - 8 back-links FROM `backlog-lifecycle.md` to referenced files
7. Update domain registry path entry
8. Convert source list (lines 8-14) to proper markdown links per repo file reference standards

### Out of Scope

1. Rewriting the state machine or item schema references (they remain canonical for their domains)
2. Implementing any missing `backlog.py` features discovered during verification (script gaps become separate backlog items)
3. Promoting `project_workflow.draft.md` (separate effort; that file has its own stale BACKLOG.md references noted in its header)
4. Modifying `backlog.py` behavior — this task is documentation verification and promotion only
5. Resolving the stale BACKLOG.md references in `project_workflow.draft.md` (noted in that file's header as a future pass)

---

## Questions / Risks

### Questions

1. **Does `backlog pull` exist?** — The draft describes it (section 2, State 8) but it is not listed in the domain registry's subcommand list (`add, list, sync, close, resolve, update, groom, view`). If `pull` does not exist, section 2 State 8 and section 7.4 (3 tests) are documenting a non-existent feature and must be removed or flagged as "planned but not implemented."

2. **Do `/group-items-to-milestone` and `/complete-milestone` skills exist?** — The draft references them (States 4 and 6) but they are not listed in the domain registry. The `project_workflow.draft.md` describes them in its milestone lifecycle subgraph. Their existence determines whether VERIFY #13 and #15 can be resolved.

3. **Overlap with `project_workflow.draft.md`** — The workflow file's Data Architecture section (lines 372-392) and the lifecycle doc's section 1 cover the same 3-layer architecture. After promotion, which is canonical for data architecture? Recommendation: lifecycle doc is canonical for data architecture; workflow doc links to it.

### Risks

1. **Script gaps discovered during testing** — If verification reveals that claimed behaviors (e.g., `--cleanup`, `--force`, `pull` subcommand) do not exist in `backlog.py`, the draft content must be corrected to reflect actual behavior. This could reduce the document's scope significantly if multiple features are unimplemented.

2. **Cross-reference maintenance burden** — Adding links to 7+ files creates coupling. If file paths change, all cross-references break. Mitigation: use relative markdown links per repo standards and verify with linting.

3. **`project_workflow.draft.md` stale references** — That file still references `BACKLOG.md` (removed) in multiple mermaid diagram nodes. Adding a cross-reference to `backlog-lifecycle.md` from a file with known stale content could confuse agents. Recommendation: note this as a prerequisite or parallel task.
