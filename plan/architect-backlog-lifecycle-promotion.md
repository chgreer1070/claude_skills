# Architecture Spec: Promote backlog-lifecycle.draft.md to Canonical Reference

## Document Metadata

- **Generated**: 2026-03-01
- **Feature**: backlog-lifecycle-promotion
- **Issue**: #286
- **Type**: Documentation verification, promotion, and cross-referencing (no code changes)
- **Source**: [plan/feature-context-backlog-lifecycle-promotion.md](./feature-context-backlog-lifecycle-promotion.md)

---

## Overview

Validate a 674-line draft lifecycle document (`backlog-lifecycle.draft.md`) against live `backlog.py` behavior, resolve all 17 `[VERIFY]` annotations by executing the described commands and observing output, update draft content to match verified facts, rename the file from `.draft.md` to `.md`, and establish two-way cross-reference links between the promoted document and the 7+ skill/agent/script files it describes. The result is a canonical reference document that agents can cite without qualification.

---

## Scope

### In Scope

1. Execute the 25-item testing checklist (Section 7 of the draft) against live `backlog.py`
2. Resolve 17 `[VERIFY]` annotations (14 unique after deduplication) by running commands and observing output
3. Correct draft content wherever verification reveals inaccuracies; annotate gaps where features do not exist
4. Rename `.claude/docs/backlog-lifecycle.draft.md` to `.claude/docs/backlog-lifecycle.md` via `git mv`
5. Remove the DRAFT status banner (HTML comment line 1 and STATUS: DRAFT paragraph lines 4-6)
6. Convert SOURCE block backtick paths (lines 8-14) to proper markdown links
7. Add outbound markdown links from the lifecycle doc to all referenced skills, agents, and scripts
8. Add inbound markdown links to the lifecycle doc from: `work-backlog-item/SKILL.md`, `groom-backlog-item/SKILL.md`, `create-backlog-item/SKILL.md`, `backlog/SKILL.md`, `backlog/references/state-machine.md`, `backlog/references/item-schema.md`, `project_workflow.draft.md`
9. Update `domain-registry.md` entry from `.draft.md` (draft) to `.md` (canonical)
10. Run `uv run prek run --files <file>` on every modified file before committing

### Out of Scope

1. Modifying `backlog.py` behavior — script gaps discovered during testing become separate backlog items
2. Rewriting `state-machine.md` or `item-schema.md` (they remain canonical for their domains)
3. Fixing the stale `BACKLOG.md` references in `project_workflow.draft.md` (separate task)
4. Promoting `project_workflow.draft.md` (separate effort)
5. Converting the entire `domain-registry.md` to markdown links (only the lifecycle entry changes)

---

## Files to Modify

### Target File (rename)

| Current Path | New Path | Change |
|-------------|----------|--------|
| `.claude/docs/backlog-lifecycle.draft.md` | `.claude/docs/backlog-lifecycle.md` | `git mv`; remove DRAFT header; resolve `[VERIFY]` annotations; convert SOURCE backtick paths to markdown links; add outbound links |

### Files Receiving Inbound Links to Lifecycle Doc

| File | Relative Path to Lifecycle Doc | Where to Add |
|------|-------------------------------|-------------|
| `.claude/skills/backlog/SKILL.md` | `../../docs/backlog-lifecycle.md` | References section or context note near top |
| `.claude/skills/work-backlog-item/SKILL.md` | `../../docs/backlog-lifecycle.md` | GitHub Integration section or references list |
| `.claude/skills/groom-backlog-item/SKILL.md` | `../../docs/backlog-lifecycle.md` | Step 7 context or references list |
| `.claude/skills/create-backlog-item/SKILL.md` | `../../docs/backlog-lifecycle.md` | References section |
| `.claude/skills/backlog/references/state-machine.md` | `../../../docs/backlog-lifecycle.md` | "See Also" line after state diagram section |
| `.claude/skills/backlog/references/item-schema.md` | `../../../docs/backlog-lifecycle.md` | "See Also" line after completeness states section |
| `.claude/project_workflow.draft.md` | `./docs/backlog-lifecycle.md` | Data Architecture section |

### Registry Update

| File | Change |
|------|--------|
| `.claude/skills/backlog-tools-administrator/references/domain-registry.md` | Line listing `backlog-lifecycle.draft.md (draft)` -> `backlog-lifecycle.md (canonical)` |

---

## Risks

### Risk 1: `backlog pull` Subcommand May Not Exist

**Evidence**: The subcommand is listed in `backlog.py`'s module docstring (line 30) but is absent from the domain registry's subcommand inventory (`add, list, sync, close, resolve, update, groom, view`). The docstring may describe planned behavior not yet implemented.

**Mitigation**: Run `uv run .claude/skills/backlog/scripts/backlog.py pull --help` first. If non-zero exit, Section 2 State 8, Section 3 data flow diagram, Section 7.4 tests (T14-T16), and the sync direction table all require correction. Document as planned behavior with a NOTE block rather than deleting the section.

### Risk 2: [VERIFY] Annotations May Reveal Incorrect Documentation Requiring Content Rewrites

**Evidence**: 5 of 14 unique annotations require running commands and observing output — their resolution is unknown until execution. If `backlog groom` does not push to GitHub on every call, or if `--cleanup` flags do not exist, entire subsections of the draft require rewriting rather than annotation removal.

**Mitigation**: Apply the content cleanup rules in Section 5 of this spec. Corrections are in scope; feature additions are not. Script gaps become NOTE blocks and optional backlog items.

### Risk 3: Cross-Reference Paths Depend on Relative File Location

**Evidence**: Paths from `backlog/references/*.md` use three `../` segments to reach `.claude/docs/`, while paths from `.claude/skills/*/SKILL.md` use two. An off-by-one breaks link navigation in Claude Code.

**Mitigation**: Use the path convention table in Section 4.2 as the authoritative source. Verify each path with the `Read` tool before adding. Run the linter after modifications.

### Risk 4: `project_workflow.draft.md` Contains Known Stale References

**Evidence**: That file's header notes stale `BACKLOG.md` references in its Mermaid diagram nodes. Adding a cross-reference to `backlog-lifecycle.md` from a file with other known stale content may mislead agents that read it.

**Mitigation**: Add only the single lifecycle link to the Data Architecture section. Note in the link's surrounding text that `project_workflow.draft.md` is itself a draft. Do not fix the stale BACKLOG.md references in this task.

### Risk 5: Milestone Skill Files May Not Exist

**Evidence**: `/group-items-to-milestone` and `/complete-milestone` are referenced in the draft (VERIFY #13 and #15) but do not appear in the domain registry's skill inventory.

**Mitigation**: Glob for these skills before resolving those annotations. If not found, resolve as "skill not yet implemented; behavior is undocumented" and reference `state-machine.md` for the defined terminal states.

---

## 1. Verification Strategy

17 `[VERIFY]` annotations exist in the draft. After deduplication (#4 duplicates #2, #5 duplicates #3), 14 unique verifications are needed. One (#7) is pre-resolved.

### 1.1 Resolvable by `--help` (6 annotations, 4 unique subcommands)

Run each command and capture output. No test item needed.

| # | Annotation | Command | Expected in Help Output |
|---|-----------|---------|------------------------|
| 1 | `pull` subcommand existence | `uv run .claude/skills/backlog/scripts/backlog.py pull --help` | Subcommand help text, or error "No such command 'pull'" |
| 2, 4 | `--cleanup` on `close` | `uv run .claude/skills/backlog/scripts/backlog.py close --help` | `--cleanup` in options list |
| 3, 5 | `--cleanup` on `resolve` | `uv run .claude/skills/backlog/scripts/backlog.py resolve --help` | `--cleanup` in options list |
| 6 | `--priority` on `update` | `uv run .claude/skills/backlog/scripts/backlog.py update --help` | `--priority` in options list |
| 10 | `--force` on `pull` | `uv run .claude/skills/backlog/scripts/backlog.py pull --help` | `--force` in options list (only if #1 shows `pull` exists) |

**Execution order**: Run #1 first. If `pull` does not exist, #9, #10, and tests T14-T16 are immediately resolved as "subcommand does not exist."

### 1.2 Resolvable by Running Commands Against a Test Item (5 annotations)

These require creating a throwaway item and observing behavior.

| # | Annotation | Verification Steps |
|---|-----------|-------------------|
| 8 | Whether `groom` pushes body to GH on every call | 1. Create test item with `backlog add --title "lifecycle-verify-test" --priority P1 --description "test" --create-issue`. 2. Run `backlog groom "lifecycle-verify-test" --section "Fact-Check" --content "test content"`. 3. Check issue body via `gh issue view N --json body -R Jamie-BitFlight/claude_skills`. 4. If body updated, annotation resolves to "syncs on every groom call." If not, "syncs only on explicit `backlog sync`." |
| 9 | Exact `pull` behavior | Only if #1 confirms `pull` exists. Run `backlog pull --dry-run` and observe output format. |
| 11 | Whether `groom` sets `metadata.status: groomed` | After the groom call in #8, read the local file frontmatter. Check if `metadata.status` changed from `needs-grooming` to `groomed`. |
| 12 | Sync skip logic for closed issues | 1. Close the test item: `backlog close "lifecycle-verify-test" --checklist-pass`. 2. Run `backlog sync --dry-run`. 3. Observe whether the closed item appears in planned actions. |
| 16 | Label atomicity | During step #8 or #11, run `gh issue view N --json labels -R Jamie-BitFlight/claude_skills` immediately after a status transition. If only one `status:*` label is present, transition is atomic. If two are present momentarily, it is non-atomic. Alternatively, read the label transition code in `backlog.py` to determine if `remove_labels` + `add_labels` happen in a single API call. |

### 1.3 Resolvable by Reading Other Files (2 annotations)

| # | Annotation | File to Read | Resolution |
|---|-----------|-------------|------------|
| 13 | Exact command invoked by `/group-items-to-milestone` | Search for `group-items-to-milestone` skill via `Glob("**/group-items-to-milestone/SKILL.md")`. If skill does not exist, annotation resolves to "skill not yet implemented; command is undocumented." |
| 15 | Whether `/complete-milestone` deletes local files or sets `status: closed` | Search for `complete-milestone` skill via `Glob("**/complete-milestone/SKILL.md")`. If skill does not exist, resolve from `state-machine.md` which states `done/resolved -> closed` is managed by `/complete-milestone`. Document as "behavior defined in state machine; implementation not verified." |

### 1.4 Pre-Resolved (1 annotation)

| # | Annotation | Resolution |
|---|-----------|------------|
| 7 | GH Action triggers `backlog sync` on `.claude/backlog/` changes | CONFIRMED by reading `.github/workflows/backlog-sync.yml`: triggers on `push` to `main` with `paths: [".claude/backlog/**"]`, runs `backlog.py sync`. |

### 1.5 Special Case: `backlog pull` Subcommand

Annotation #1 is the gate for annotations #9, #10, and tests T14-T16.

```text
Decision tree:
  Run: uv run .claude/skills/backlog/scripts/backlog.py pull --help
  ├─ Exit 0 (subcommand exists) → proceed with #9, #10, T14-T16
  └─ Non-zero / "No such command" → Document the gap:
       - Section 2 State 8 ("Pulling from GitHub") gets a NOTE:
         "The `pull` subcommand is not implemented as of 2026-03-01.
          This section documents planned behavior."
       - Section 3 data flow diagram: `PULL` node gets dashed borders
       - Section 7.4 tests (T14-T16): marked "SKIPPED — subcommand not implemented"
       - Sync direction table: "Pull" row gets "(planned)" suffix
```

### 1.6 Verification Execution Order

Dependency-aware order to minimize redundant work:

```text
Phase 1 — Help checks (no side effects, no test item needed):
  1. backlog pull --help          (gate for #9, #10, T14-T16)
  2. backlog close --help         (resolves #2, #4, T10)
  3. backlog resolve --help       (resolves #3, #5, T11)
  4. backlog update --help        (resolves #6, T19)
  5. backlog pull --help --force  (only if #1 passed; resolves #10)

Phase 2 — Test item creation:
  6. backlog add --title "lifecycle-verify-test" --priority P1 \
       --description "Throwaway item for lifecycle verification" \
       --create-issue -R Jamie-BitFlight/claude_skills

Phase 3 — Behavioral observation (uses test item):
  7. backlog groom + check GH body           (resolves #8)
  8. Read local file after groom              (resolves #11)
  9. gh issue view N --json labels            (resolves #16)
  10. backlog close + backlog sync --dry-run  (resolves #12)
  11. backlog pull --dry-run                  (resolves #9, only if pull exists)

Phase 4 — File reads:
  12. Search for group-items-to-milestone     (resolves #13)
  13. Search for complete-milestone           (resolves #15)

Phase 5 — Cleanup:
  14. backlog resolve "lifecycle-verify-test" --reason "Throwaway test item for lifecycle verification" \
        -R Jamie-BitFlight/claude_skills
```

---

## 2. Testing Strategy

25 tests in 7 categories. 3 are pre-resolved (T20, T21, T22). The remaining 22 require execution.

### 2.1 Execution Order (Dependency-Aware)

Tests are grouped into phases that share state. A single throwaway test item serves tests T1-T12, T17-T19, T23-T25.

```text
Phase A — No side effects (read-only, help checks):
  T10: backlog close --help → check --cleanup        (shares with VERIFY #2)
  T11: backlog resolve --help → check --cleanup      (shares with VERIFY #3)
  T19: backlog update --help → check --priority      (shares with VERIFY #6)
  T20: ALREADY CONFIRMED
  T21: ALREADY CONFIRMED
  T22: ALREADY CONFIRMED

Phase B — Test item creation (needed for all remaining tests):
  T1:  backlog add --no-create-issue → check no GH issue
  T2:  backlog add --create-issue → check metadata.issue written
       (Creates the test item used by subsequent phases)

Phase C — Sync behavior (uses item from Phase B):
  T3:  backlog sync → confirm skips items with existing metadata.issue
  T4:  backlog sync --dry-run → confirm no writes
  T17: backlog sync with a P2 item → confirm P2 skipped

Phase D — Grooming (uses item from Phase B):
  T5:  backlog groom --section → confirm append-not-overwrite
  T6:  metadata.groomed not set until all 7 sections present
  T8:  backlog close without --checklist-pass → confirm rejection

Phase E — Status transitions (uses item from Phase B):
  T7:  backlog update --status in-progress with/without --plan
  T18: gh issue view → confirm label atomicity (single status:* label)

Phase F — Close/resolve behavior:
  T8:  backlog close without --checklist-pass → rejected
  T9:  backlog resolve without --reason → rejected
  T12: backlog close --cleanup → observe file deletion (only if --cleanup exists)
  T13: /complete-milestone effect → resolved by file read, not execution

Phase G — Pull behavior (only if pull subcommand exists):
  T14: backlog pull --dry-run
  T15: backlog pull → metadata.status updated
  T16: backlog pull → local-only fields preserved

Phase H — Post-merge behavior:
  T23: Merge a PR with "Fixes #N" → confirm auto-close (observational; may not be executable in test)
  T24: backlog sync after close → confirm skipped
  T25: backlog list → confirm closed items excluded or marked
```

### 2.2 Tests Requiring a Throwaway Test Item

All tests in Phases B-F and H share a single throwaway item created in Phase B (T2). The item progresses through states during testing:

```text
T2:  Created (needs-grooming) → with GH issue
T3:  Sync tested (still needs-grooming)
T5:  Groom section added
T6:  Multiple groom sections added (not yet all 7)
T7:  Status updated to in-progress
T8:  Close attempted without checklist-pass (should fail)
T12: Close with --cleanup (if flag exists)
```

A second throwaway item is needed for:
- T1: Created with `--no-create-issue` (verify no GH API call)
- T17: Created as P2 (verify sync skips it)

### 2.3 Tests That Can Share State

| Shared State | Tests |
|-------------|-------|
| `--help` output from Phase A | T10, T11, T19 share with VERIFY #2, #3, #6 |
| Test item after creation | T2, T3, T4 |
| Test item after groom | T5, T6, T18 |
| Test item after status update | T7, T8 |
| Label observation via `gh issue view` | T18 shares with VERIFY #16 |
| Sync after close | T24 shares with VERIFY #12 |

### 2.4 Expected Outputs for Pass/Fail

| Test | Pass Condition | Fail Condition |
|------|---------------|----------------|
| T1 | No new issue appears in `gh issue list` after `backlog add --no-create-issue` | Issue created despite `--no-create-issue` |
| T2 | Local file contains `metadata.issue: '#N'` where N is a valid issue number | `metadata.issue` absent or empty |
| T3 | `backlog sync` output does not list the already-linked item | Item appears in sync output as "creating issue" |
| T4 | No files modified, no issues created; output shows "would create" or similar | Files modified or issues created |
| T5 | After adding "Fact-Check" section, prior "Description" section still present | Prior section overwritten |
| T6 | After adding 6 of 7 sections, `metadata.groomed` is absent; after 7th, it is set | `metadata.groomed` set with fewer than 7 sections |
| T7 | Either: `--status` and `--plan` are independent, OR error message indicates coupling | Silent failure (status set without plan, or vice versa, with no indication) |
| T8 | Command exits non-zero or prints error when `--checklist-pass` is omitted | Close succeeds without `--checklist-pass` |
| T9 | Command exits non-zero or prints error when `--reason` is omitted | Resolve succeeds without `--reason` |
| T10 | `--cleanup` appears in `backlog close --help` output | `--cleanup` absent from help |
| T11 | `--cleanup` appears in `backlog resolve --help` output | `--cleanup` absent from help |
| T12 | Local file deleted after `backlog close --cleanup` | File still exists |
| T13 | Determined by reading `/complete-milestone` skill (file read, not execution) | Skill not found |
| T14 | `backlog pull --dry-run` shows diff between GH and local state | Error or no output |
| T15 | `metadata.status` in local file matches GH label after pull | Status unchanged |
| T16 | `metadata.plan` and `metadata.groomed` retain their values after pull | Fields overwritten with empty values |
| T17 | P2 item absent from `backlog sync` output | P2 item appears as "creating issue" |
| T18 | Exactly one `status:*` label on issue at any point during transition | Two `status:*` labels observed simultaneously |
| T19 | `--priority` appears in `backlog update --help`, OR confirmed alternative path documented | No re-prioritization path exists |
| T23 | Issue state is `closed` after PR merge with `Fixes #N` | Issue remains open |
| T24 | Closed item not listed in `backlog sync` planned actions | Closed item appears in sync output |
| T25 | `backlog list` output excludes closed/resolved items or marks them distinctly | Closed items listed identically to open ones |

---

## 3. File Rename Strategy

### 3.1 Git Rename

```bash
git mv .claude/docs/backlog-lifecycle.draft.md .claude/docs/backlog-lifecycle.md
```

### 3.2 Remove DRAFT Status Header and Comment

Remove these lines from the promoted file:

- Line 1: `<!-- DRAFT — 2026-02-27 — Pending verification against live script behavior -->`
- Lines 4-6: The `**STATUS: DRAFT**` paragraph and its trailing blank line

Replace with nothing. The document title (`# Backlog Item Lifecycle`) on line 2 becomes line 1.

### 3.3 Update All Existing References to Old Filename

Files that reference `backlog-lifecycle.draft.md` (found via `Grep("backlog-lifecycle.draft")`):

| File | What to Change |
|------|---------------|
| `.claude/skills/backlog-tools-administrator/references/domain-registry.md` (line 72) | `backlog-lifecycle.draft.md` -> `backlog-lifecycle.md`; `(draft)` -> `(canonical)` |
| `plan/feature-context-backlog-lifecycle-promotion.md` | No change needed — this is a plan artifact that records historical state |
| Any other files found by grep | Update path from `.draft.md` to `.md` |

### 3.4 Convert SOURCE Block to Markdown Links

Lines 8-14 of the draft contain backtick-quoted file paths. Per CLAUDE.md file reference standards, these must become markdown links with `./` prefix. The paths are relative to `.claude/docs/backlog-lifecycle.md`:

| Current Text | Replacement |
|-------------|-------------|
| `` `.claude/skills/backlog/SKILL.md` `` | `[backlog/SKILL.md](./../skills/backlog/SKILL.md)` |
| `` `.claude/skills/backlog/references/state-machine.md` `` | `[state-machine.md](./../skills/backlog/references/state-machine.md)` |
| `` `.claude/skills/backlog/references/item-schema.md` `` | `[item-schema.md](./../skills/backlog/references/item-schema.md)` |
| `` `.claude/skills/backlog/scripts/backlog.py` `` | `[backlog.py](./../skills/backlog/scripts/backlog.py)` |
| `` `.claude/skills/work-backlog-item/SKILL.md` `` | `[work-backlog-item/SKILL.md](./../skills/work-backlog-item/SKILL.md)` |
| `` `.claude/skills/create-backlog-item/SKILL.md` `` | `[create-backlog-item/SKILL.md](./../skills/create-backlog-item/SKILL.md)` |
| `` `.claude/skills/groom-backlog-item/SKILL.md` `` | `[groom-backlog-item/SKILL.md](./../skills/groom-backlog-item/SKILL.md)` |

---

## 4. Cross-Reference Architecture

### 4.1 Outbound Links FROM `backlog-lifecycle.md`

The lifecycle doc at `.claude/docs/backlog-lifecycle.md` needs markdown links to these files. All paths are relative to `.claude/docs/`.

| Target File | Relative Path from `.claude/docs/` | Anchor Text | Where in Lifecycle Doc |
|------------|-------------------------------------|-------------|----------------------|
| `.claude/skills/backlog/references/state-machine.md` | `./../skills/backlog/references/state-machine.md` | "canonical state machine" | Section 2 intro or new "Related References" section at top |
| `.claude/skills/backlog/references/item-schema.md` | `./../skills/backlog/references/item-schema.md` | "item file schema" | Section 6 intro |
| `.claude/skills/backlog/scripts/backlog.py` | `./../skills/backlog/scripts/backlog.py` | "`backlog.py`" | Section 1 Layer 3 |
| `.claude/skills/work-backlog-item/SKILL.md` | `./../skills/work-backlog-item/SKILL.md` | "`/work-backlog-item`" | States 5, 6, 7 |
| `.claude/skills/groom-backlog-item/SKILL.md` | `./../skills/groom-backlog-item/SKILL.md` | "`/groom-backlog-item`" | State 3 |
| `.claude/skills/create-backlog-item/SKILL.md` | `./../skills/create-backlog-item/SKILL.md` | "`/create-backlog-item`" | State 1 |
| `.claude/project_workflow.draft.md` | `./../project_workflow.draft.md` | "project workflow" | Section 1 or Related References |
| `.github/workflows/backlog-sync.yml` | `./../../.github/workflows/backlog-sync.yml` | "backlog-sync GitHub Action" | Section 2 State 2 and Section 3 |

**Link syntax example** (from `.claude/docs/backlog-lifecycle.md`):

```markdown
For the canonical state diagram, see [state-machine.md](./../skills/backlog/references/state-machine.md).
```

### 4.2 Inbound Links TO `backlog-lifecycle.md`

Files that need to add a link pointing to the lifecycle doc. All paths are relative to the source file.

| Source File | Relative Path to Lifecycle Doc | Anchor Text | Where to Add |
|------------|-------------------------------|-------------|-------------|
| `.claude/skills/backlog/references/state-machine.md` | `./../../docs/backlog-lifecycle.md` | "full lifecycle data flow and sync behavior" | After the State Diagram section or in a new "See Also" line at the end |
| `.claude/skills/backlog/references/item-schema.md` | `./../../docs/backlog-lifecycle.md` | "lifecycle context of each field" | After "Item Completeness States" section or in a "See Also" line at the end |
| `.claude/skills/backlog/SKILL.md` | Path depends on file structure; from `.claude/skills/backlog/` it is `./../../docs/backlog-lifecycle.md` | "full item lifecycle documentation" | References section or top-level context note |
| `.claude/skills/work-backlog-item/SKILL.md` | `./../../docs/backlog-lifecycle.md` | "item lifecycle documentation" | GitHub Integration section or references list |
| `.claude/skills/groom-backlog-item/SKILL.md` | `./../../docs/backlog-lifecycle.md` | "lifecycle and sync behavior" | Step 7 context or references list |
| `.claude/skills/create-backlog-item/SKILL.md` | `./../../docs/backlog-lifecycle.md` | "item lifecycle from creation to close" | References section |
| `.claude/project_workflow.draft.md` | `./../docs/backlog-lifecycle.md` | "canonical data architecture reference" | Data Architecture section |

**Link syntax example** (from `.claude/skills/backlog/references/state-machine.md`):

```markdown
For full lifecycle data flow and sync behavior, see [backlog-lifecycle.md](./../../docs/backlog-lifecycle.md).
```

### 4.3 Domain Registry Update

File: `.claude/skills/backlog-tools-administrator/references/domain-registry.md`, line 72.

Current:

```text
- `.claude/docs/backlog-lifecycle.draft.md` — Lifecycle documentation (draft)
```

Updated:

```text
- `.claude/docs/backlog-lifecycle.md` — Lifecycle documentation (canonical)
```

### 4.4 Path Convention Summary

All paths follow CLAUDE.md file reference standards:

- Markdown link syntax: `[text](./path)`
- Relative paths start with `./`
- Paths relative to file containing the reference
- No backtick-only file paths for references (backticks used only in command examples)

---

## 5. Content Cleanup

### 5.1 Resolved [VERIFY] Annotations (Verified True)

When a `[VERIFY]` annotation is confirmed as accurate:

1. Remove the `[VERIFY: ...]` marker text
2. Keep the surrounding sentence intact
3. Add a citation where the verification source is not already obvious

**Example**:

Before:

```markdown
`backlog groom` syncs the groomed content to the issue body. [VERIFY: whether the
script pushes body to GH on every `groom` call or only on explicit sync]
```

After (if confirmed pushes on every groom call):

```markdown
`backlog groom` syncs the groomed content to the issue body on every call.
```

### 5.2 Resolved [VERIFY] Annotations (Verified False or Different)

When a `[VERIFY]` annotation reveals the documented behavior is wrong:

1. Remove the `[VERIFY: ...]` marker text
2. Correct the sentence to match observed behavior
3. Add a `NOTE:` block if the correction is non-obvious or represents a gap

**Example**:

Before:

```markdown
- `--force`: overwrites local changes without prompting [VERIFY]
```

After (if `--force` does not exist):

```markdown
**NOTE**: The `--force` flag is not implemented as of 2026-03-01.
```

### 5.3 Annotations That Reveal Script Gaps

When a `[VERIFY]` annotation reveals a missing feature (subcommand, flag, or behavior):

1. Remove the `[VERIFY: ...]` marker
2. Replace the description of the missing feature with a `NOTE` block:

```markdown
> **NOTE**: `backlog pull` is not implemented as of 2026-03-01. This section
> documents planned behavior described in the original design. Create a backlog
> item if this capability is needed.
```

3. Keep the section in the document (do not delete it) so the planned behavior remains documented
4. For the testing checklist, mark affected tests as `- [x] SKIPPED — {subcommand/flag} not implemented`

### 5.4 Special Case: `backlog pull` Section

If `backlog pull` does not exist:

- **Section 2 State 8** ("Pulling from GitHub"): Retain the section. Prepend a NOTE block indicating the subcommand is not implemented. Change the section title to `### State 8: Pulling from GitHub (Planned)`.
- **Section 3 data flow diagram**: Add `style PULL stroke-dasharray: 5 5` to the Mermaid diagram to render the PULL node with dashed borders.
- **Section 3 "Sync direction" table**: Change "Pull (GitHub -> local): `backlog pull`" to "Pull (GitHub -> local): `backlog pull` (planned — not yet implemented)".
- **Section 7.4 tests (T14-T16)**: Mark as `- [x] SKIPPED — backlog pull not implemented`.

### 5.5 Testing Checklist (Section 7) in Promoted File

After all tests are executed and [VERIFY] annotations resolved:

1. Check off each test: `- [ ]` becomes `- [x]` with a result note
2. For tests that fail (revealing script gaps), mark as `- [x] RESULT: {observed behavior}` and add a NOTE
3. For tests that cannot be executed (e.g., T23 requires actual PR merge), mark as `- [x] NOT TESTABLE in this session — {reason}`
4. Keep the testing checklist in the promoted file as a verification record

### 5.6 Remove DRAFT Artifacts

After all cleanup:

1. Delete the HTML comment on line 1
2. Delete the STATUS: DRAFT paragraph (lines 4-6)
3. Convert the SOURCE backtick paths to markdown links (per Section 3.4 of this spec)

---

## 6. Constraints

1. **File reference standards**: All file references use markdown link syntax with `./` prefix, paths relative to the file containing the reference. Per [CLAUDE.md File Reference Standards](./../../.claude/CLAUDE.md).

2. **Linting**: All modified files must pass `uv run prek run --files <file>` before the task is considered complete. This includes:
   - `.claude/docs/backlog-lifecycle.md` (the promoted file)
   - `.claude/skills/backlog/references/state-machine.md`
   - `.claude/skills/backlog/references/item-schema.md`
   - `.claude/skills/backlog/SKILL.md`
   - `.claude/skills/work-backlog-item/SKILL.md`
   - `.claude/skills/groom-backlog-item/SKILL.md`
   - `.claude/skills/create-backlog-item/SKILL.md`
   - `.claude/skills/backlog-tools-administrator/references/domain-registry.md`
   - `.claude/project_workflow.draft.md`

3. **No new files**: Only rename + edit existing files. The sole file operation that changes file count is the `git mv` (rename, not creation).

4. **Scope boundary**: Do not expand the lifecycle doc's content. Corrections from verification are in scope. Adding new sections, new features, or new architectural documentation is out of scope.

5. **Script immutability**: Do not modify `backlog.py` behavior. If verification reveals missing features, document the gap with a NOTE and optionally create a backlog item. The script is out of scope for this task.

6. **`project_workflow.draft.md` stale references**: That file contains stale `BACKLOG.md` references. Adding a cross-reference to `backlog-lifecycle.md` is in scope. Fixing the stale `BACKLOG.md` references in that file is out of scope (separate task).

7. **Test item cleanup**: The throwaway test item created during verification must be resolved (deleted or marked resolved) before the task is complete. Use `backlog resolve "lifecycle-verify-test" --reason "Throwaway test item for lifecycle verification"`.

---

## 7. Task Decomposition

Five sequential tasks. Each produces a concrete artifact that the next task consumes.

### Task 1: Execute Testing Checklist and Capture Results

**Scope**: Run the 25-item testing checklist (Section 7 of the draft) and the 14 unique `[VERIFY]` annotation verifications. Follow the dependency-aware execution order defined in Sections 1.6 and 2.1 of this spec.

**Execution**:

- Phase 1: Run `--help` on `pull`, `close`, `resolve`, `update` subcommands (resolves VERIFY #1-6, #10; tests T10, T11, T19)
- Phase 2: Create throwaway test item with `backlog add ... --create-issue`
- Phase 3: Run behavioral tests using the test item (resolves VERIFY #8, #11, #12, #16; tests T1-T9, T12, T17-T18, T23-T25)
- Phase 4: Run `backlog pull` tests (only if Phase 1 confirmed `pull` exists; tests T14-T16)
- Phase 5: Read milestone skill files for VERIFY #13, #15
- Phase 6: Clean up throwaway item via `backlog resolve "lifecycle-verify-test" --reason "..."`

**Output**: A results file at `plan/verify-results-backlog-lifecycle.md` containing one row per annotation and test: annotation/test ID, command run, observed output, resolution (CONFIRMED / CORRECTED / NOT IMPLEMENTED / NOT TESTABLE).

---

### Task 2: Resolve All [VERIFY] Annotations Based on Test Results

**Scope**: Edit `.claude/docs/backlog-lifecycle.draft.md` in-place (before rename) to resolve every annotation.

**Input**: `plan/verify-results-backlog-lifecycle.md` from Task 1.

**Execution**:

- For each VERIFY annotation: apply the rule from Section 5.1 (confirmed true), 5.2 (corrected), 5.3 (gap revealed), or 5.4 (`pull` special case)
- For each test in Section 7: change `- [ ]` to `- [x]` with a result note; mark SKIPPED where subcommand/flag is absent
- Remove the HTML comment (line 1) and STATUS: DRAFT paragraph (lines 4-6)
- Convert SOURCE backtick paths (lines 8-14) to markdown links per Section 3.4 of this spec

**Output**: `.claude/docs/backlog-lifecycle.draft.md` with zero `[VERIFY]` annotations remaining, DRAFT header removed, SOURCE block converted to markdown links.

---

### Task 3: Rename File and Update Existing References

**Scope**: Rename the file and update any existing references to the old `.draft.md` path.

**Execution**:

```bash
git mv .claude/docs/backlog-lifecycle.draft.md .claude/docs/backlog-lifecycle.md
```

Then grep for any remaining references to `backlog-lifecycle.draft`:

```bash
uv run python -c "
import subprocess, sys
result = subprocess.run(['grep', '-r', 'backlog-lifecycle.draft', '.claude', 'plan'], capture_output=True, text=True)
print(result.stdout)
"
```

Update each found reference to use `backlog-lifecycle.md`.

**Output**: `.claude/docs/backlog-lifecycle.md` exists; no files in the repo reference `backlog-lifecycle.draft.md` except historical plan artifacts (which are exempt per Section 3.3 of this spec).

---

### Task 4: Add Two-Way Cross-Reference Links in All Files

**Scope**: Add markdown links as specified in Sections 4.1 and 4.2 of this spec.

**Execution**:

1. Add outbound links FROM `backlog-lifecycle.md` to each target in the table in Section 4.1 — convert existing backtick references to markdown links at the point where each skill/script is first mentioned
2. Add inbound links TO `backlog-lifecycle.md` in each of the 7 source files listed in the Files to Modify table — use the `**Lifecycle reference**: See [Backlog Lifecycle](...)` pattern established by other skills
3. Update `domain-registry.md` entry per Section 4.3

**Output**: All 8 files modified; each contains exactly one navigable markdown link to/from the lifecycle doc (or more if multiple mentions exist).

---

### Task 5: Validate All Links and Run Linting

**Scope**: Verify that every added link resolves to an existing file, then run the linter on all modified files.

**Execution**:

For each markdown link added in Task 4, use the `Read` tool to confirm the target file exists at the specified relative path.

Then lint all modified files:

```bash
uv run prek run --files \
  .claude/docs/backlog-lifecycle.md \
  .claude/skills/backlog/SKILL.md \
  .claude/skills/work-backlog-item/SKILL.md \
  .claude/skills/groom-backlog-item/SKILL.md \
  .claude/skills/create-backlog-item/SKILL.md \
  .claude/skills/backlog/references/state-machine.md \
  .claude/skills/backlog/references/item-schema.md \
  .claude/skills/backlog-tools-administrator/references/domain-registry.md \
  .claude/project_workflow.draft.md
```

Fix any linting errors before committing. Common issues: missing blank lines around code fences (MD031), missing language specifiers on code fences, broken relative paths.

**Output**: All modified files pass `prek` with zero errors. All added links confirmed to resolve to existing files.
