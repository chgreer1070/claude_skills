---
task: T1
title: Execute Testing Checklist Against Live backlog.py
status: not-started
agent: general-purpose
dependencies: []
priority: 1
complexity: high
created: 2026-03-01T00:00:00Z
---

## Context

`backlog-lifecycle.draft.md` contains a 25-item testing checklist (Section 7) covering 7
categories: data architecture, state transitions, cleanup behavior, pull/bidirectional sync,
priority and label mapping, GitHub Action integration, and post-merge behavior. Three tests
(T20, T21, T22) are pre-confirmed by reading `.github/workflows/backlog-sync.yml`. The
remaining 22 require executing commands against the live `backlog.py` script and observing
output. This task produces the evidence base that Task 2 uses to resolve `[VERIFY]` annotations.

Fixes #286

## Objective

Execute all 25 test items from Section 7 of `.claude/docs/backlog-lifecycle.draft.md` against
the live `backlog.py` script, record pass/fail for each with actual command output, and capture
any discrepancies between documented and actual behavior.

## Requirements

1. Read `.claude/docs/backlog-lifecycle.draft.md` Section 7 to get the exact 25 test items
2. Run the verification strategy from `plan/architect-backlog-lifecycle-promotion.md` Section 1
   in the dependency-aware order defined there (help checks first, then test item creation, then
   behavioral observation, then file reads, then cleanup)
3. Create a throwaway test item via `uv run .claude/skills/backlog/scripts/backlog.py add` for
   behavioral tests; resolve it when done
4. For each of the 25 tests, record:
   - The command(s) run
   - The exact output (stdout + stderr + exit code)
   - Pass or Fail verdict against the pass condition defined in architect spec Section 2.4
5. Note which tests share state with `[VERIFY]` annotations (per architect spec Section 2.3)
6. For T20, T21, T22: mark CONFIRMED with evidence from `.github/workflows/backlog-sync.yml`
7. For T23 ("merge a PR with Fixes #N"): mark NOT TESTABLE with reason
8. Write results to `.claude/plan/testing-results-backlog-lifecycle.md`

## Constraints

- Do not modify `backlog.py` — only observe behavior
- Do not modify `.claude/docs/backlog-lifecycle.draft.md` in this task; that is Task 2
- Resolve the throwaway test item before this task is complete
- Use `uv run` for all Python script invocations
- Pass `-R Jamie-BitFlight/claude_skills` to every `gh` command (git remote is a local proxy)
- Run `uv run .claude/skills/backlog/scripts/backlog.py pull --help` first — its exit code
  gates tests T14-T16 and `[VERIFY]` annotations #9, #10

## Expected Outputs

- File created: `plan/testing-results-backlog-lifecycle.md`
- Content: 25-item table with columns: Test ID, Category, Command(s), Output, Pass/Fail, Notes
- Annotations for pre-confirmed tests (T20-T22) with the confirming evidence
- Annotation for T23 (NOT TESTABLE) with reason
- Note on whether `backlog pull` subcommand exists (gate for T14-T16)

## Acceptance Criteria

1. `plan/testing-results-backlog-lifecycle.md` exists
2. All 25 tests appear in the results file (T1-T25)
3. Each test has: command(s) run, output captured, and pass/fail recorded
4. T20, T21, T22 are marked CONFIRMED with citation of `backlog-sync.yml` line numbers
5. The throwaway test item is resolved before this task completes

## Verification Steps

```bash
# Confirm results file exists
ls plan/testing-results-backlog-lifecycle.md

# Confirm all 25 test IDs are present
grep -c "^| T[0-9]" plan/testing-results-backlog-lifecycle.md

# Confirm throwaway item is gone
uv run .claude/skills/backlog/scripts/backlog.py list | grep -c "lifecycle-verify-test"
```

## Handoff

Report to orchestrator:
- Path to `plan/testing-results-backlog-lifecycle.md`
- Whether `backlog pull` subcommand exists (exit code from `pull --help`)
- Count of tests that passed vs. failed vs. skipped
- List of any failed tests that reveal script gaps (these affect Task 2 content corrections)
- Whether the throwaway test item was successfully resolved

---
task: T2
title: Resolve All [VERIFY] Annotations
status: not-started
agent: general-purpose
dependencies: ["T1"]
priority: 1
complexity: high
created: 2026-03-01T00:00:00Z
---

## Context

`.claude/docs/backlog-lifecycle.draft.md` contains 17 `[VERIFY]` annotations (14 unique after
deduplication). Task 1 produced `plan/testing-results-backlog-lifecycle.md` with the observed
behavior for each annotation's verification method. This task uses those results to update the
draft content: remove annotation markers, correct inaccurate claims, add NOTE blocks for missing
features, and mark testing checklist items. The `backlog pull` subcommand status (from Task 1
handoff) determines whether Section 2 State 8, Section 7.4, and the sync direction table require
the planned-behavior treatment defined in architect spec Section 5.4.

## Objective

Resolve all 17 `[VERIFY]` annotations in `.claude/docs/backlog-lifecycle.draft.md` by applying
observed behavior from Task 1 results, leaving zero annotation markers and content that matches
verified facts.

## Requirements

1. Read `plan/testing-results-backlog-lifecycle.md` (Task 1 output)
2. Read `.claude/docs/backlog-lifecycle.draft.md` (all 674 lines)
3. For each `[VERIFY]` annotation:
   a. Apply the content cleanup rule from architect spec Section 5 that matches the result:
      - Verified true: remove marker, keep sentence, add citation if needed
      - Verified false/different: remove marker, correct the sentence, add NOTE if non-obvious
      - Feature gap discovered: remove marker, add NOTE block with "not implemented as of 2026-03-01"
4. If `backlog pull` does not exist, apply Section 5.4 treatment to: Section 2 State 8
   (add "(Planned)" to title and prepend NOTE), Section 3 data flow diagram (dashed PULL node),
   sync direction table (add "(planned)" suffix), Section 7.4 tests T14-T16 (mark SKIPPED)
5. Update the Section 7 testing checklist: change `- [ ]` to `- [x]` for each executed test,
   appending the pass/fail result; mark T20-T22 as CONFIRMED; mark T23 as NOT TESTABLE
6. Keep all NOTE blocks and SKIPPED markers in the file — do not delete sections
7. Annotation #7 (GH Action trigger): resolve as CONFIRMED (pre-verified before Task 1)

## Constraints

- Do not rename the file in this task; renaming is Task 3
- Do not remove the DRAFT header in this task; that is Task 3
- Do not add cross-reference markdown links in this task; that is Task 4
- Corrections to match observed behavior are in scope; adding new sections is out of scope
- Do not modify `backlog.py`

## Expected Outputs

- Modified file: `.claude/docs/backlog-lifecycle.draft.md`
- Zero `[VERIFY]` annotation markers remain
- Section 7 testing checklist: all 25 items marked with result (`[x]`)
- NOTE blocks added where features are missing or behaviors differ from documentation
- If `backlog pull` absent: Section 2 State 8 titled "(Planned)", Section 7.4 T14-T16 marked SKIPPED

## Acceptance Criteria

1. `grep -c "\[VERIFY\]" .claude/docs/backlog-lifecycle.draft.md` returns 0
2. All 25 Section 7 checklist items are checked (`- [x]`) with result notes
3. No content claims behaviors that Task 1 testing disproved
4. NOTE blocks are present wherever a script gap was discovered

## Verification Steps

```bash
# Confirm zero [VERIFY] markers remain
grep -c "\[VERIFY\]" .claude/docs/backlog-lifecycle.draft.md

# Confirm all checklist items are checked
grep -c "^\- \[x\]" .claude/docs/backlog-lifecycle.draft.md

# Confirm no unchecked checklist items remain in Section 7
grep -n "^\- \[ \]" .claude/docs/backlog-lifecycle.draft.md
```

## Handoff

Report to orchestrator:
- Count of `[VERIFY]` annotations resolved (should be 17)
- Count that resolved as: verified-true / verified-false / feature-gap
- Whether `backlog pull` treatment was applied (Section 5.4)
- Any annotations that could not be resolved and why

---
task: T3
title: Rename Draft File and Update References
status: not-started
agent: general-purpose
dependencies: ["T2"]
priority: 2
complexity: medium
created: 2026-03-01T00:00:00Z
---

## Context

With all `[VERIFY]` annotations resolved (Task 2), the draft is ready for promotion. This task
performs the rename via `git mv`, removes the DRAFT artifacts from the file content, and updates
all existing references to the old filename. The domain registry at
`.claude/skills/backlog-tools-administrator/references/domain-registry.md` is the primary
registry file that lists the draft path. A `grep` search will find any other references.

## Objective

Rename `.claude/docs/backlog-lifecycle.draft.md` to `.claude/docs/backlog-lifecycle.md` using
`git mv`, remove DRAFT header content, and update every reference to the old filename across
the repository.

## Requirements

1. Run `git mv .claude/docs/backlog-lifecycle.draft.md .claude/docs/backlog-lifecycle.md`
2. Remove from the promoted file (now `.claude/docs/backlog-lifecycle.md`):
   - Line 1: the HTML comment `<!-- DRAFT — 2026-02-27 — Pending verification against live
     script behavior -->`
   - The `**STATUS: DRAFT**` paragraph and its surrounding blank lines (lines 4-6 of original)
3. Convert the SOURCE block backtick paths (lines 8-14 of original, now near top of file) to
   proper markdown links. Use paths relative to `.claude/docs/` per architect spec Section 3.4:
   - `` `.claude/skills/backlog/SKILL.md` `` → `[backlog/SKILL.md](./../skills/backlog/SKILL.md)`
   - `` `.claude/skills/backlog/references/state-machine.md` `` →
     `[state-machine.md](./../skills/backlog/references/state-machine.md)`
   - `` `.claude/skills/backlog/references/item-schema.md` `` →
     `[item-schema.md](./../skills/backlog/references/item-schema.md)`
   - `` `.claude/skills/backlog/scripts/backlog.py` `` →
     `[backlog.py](./../skills/backlog/scripts/backlog.py)`
   - `` `.claude/skills/work-backlog-item/SKILL.md` `` →
     `[work-backlog-item/SKILL.md](./../skills/work-backlog-item/SKILL.md)`
   - `` `.claude/skills/create-backlog-item/SKILL.md` `` →
     `[create-backlog-item/SKILL.md](./../skills/create-backlog-item/SKILL.md)`
   - `` `.claude/skills/groom-backlog-item/SKILL.md` `` →
     `[groom-backlog-item/SKILL.md](./../skills/groom-backlog-item/SKILL.md)`
4. Search for all remaining references to `backlog-lifecycle.draft` across the repo using `Grep`
5. For each match found: update path from `backlog-lifecycle.draft.md` to `backlog-lifecycle.md`
   and update any status labels like `(draft)` to `(canonical)`
6. Update `.claude/skills/backlog-tools-administrator/references/domain-registry.md` entry
   per architect spec Section 4.3

## Constraints

- Use `git mv` (not file copy + delete) to preserve git history
- Do not edit `plan/feature-context-backlog-lifecycle-promotion.md` or
  `plan/architect-backlog-lifecycle-promotion.md` — these are plan artifacts that record
  historical state and intentionally reference the draft path
- All file references in the promoted file must use `./` prefix per CLAUDE.md standards

## Expected Outputs

- File renamed: `.claude/docs/backlog-lifecycle.md` (git-tracked rename)
- DRAFT header removed from file content
- SOURCE block backtick paths converted to markdown links
- `.claude/skills/backlog-tools-administrator/references/domain-registry.md` updated
- Any other files referencing old filename updated

## Acceptance Criteria

1. `.claude/docs/backlog-lifecycle.md` exists
2. `.claude/docs/backlog-lifecycle.draft.md` no longer exists
3. `grep -r "backlog-lifecycle.draft" .claude/` returns no results (excluding plan/ artifacts)
4. File content contains no DRAFT HTML comment and no STATUS: DRAFT paragraph
5. SOURCE block paths in the promoted file are markdown links, not backtick-only paths

## Verification Steps

```bash
# Confirm rename
ls .claude/docs/backlog-lifecycle.md

# Confirm old file gone
ls .claude/docs/backlog-lifecycle.draft.md 2>&1

# Confirm no remaining draft references in .claude/ (plan/ artifacts are excluded)
grep -r "backlog-lifecycle.draft" .claude/ --exclude-dir=plan

# Confirm DRAFT comment removed
grep -c "DRAFT" .claude/docs/backlog-lifecycle.md

# Confirm SOURCE links are markdown (not backtick-only)
grep -n "backlog/SKILL.md" .claude/docs/backlog-lifecycle.md
```

## Handoff

Report to orchestrator:
- Confirmed rename path
- List of files updated (domain-registry.md plus any others found by grep)
- Whether any plan/ artifacts were intentionally left unchanged
- Result of DRAFT comment grep (should be 0)

---
task: T4
title: Add Two-Way Cross-Reference Links
status: not-started
agent: general-purpose
dependencies: ["T3"]
priority: 2
complexity: medium
created: 2026-03-01T00:00:00Z
---

## Context

The promoted file `.claude/docs/backlog-lifecycle.md` and seven surrounding skill files need
two-way markdown links established between them. The codebase analysis
(`plan/codebase/cross-references-backlog.md`) established the correct relative paths from each
source location. The architect spec (`plan/architect-backlog-lifecycle-promotion.md`) Sections
4.1 and 4.2 define the exact anchor text and placement for each link. The link convention from
`.claude/skills/*/SKILL.md` to `.claude/docs/` is `../../docs/backlog-lifecycle.md`.

## Requirements

1. Add outbound links FROM `.claude/docs/backlog-lifecycle.md` TO referenced skills/scripts.
   Read the file first to find natural placement points (Section 2 state descriptions, Section 6
   intro, Section 1 Layer 3 description). Per architect spec Section 4.1:
   - State machine: `[state-machine.md](./../skills/backlog/references/state-machine.md)` in
     Section 2 intro or new Related References section
   - Item schema: `[item-schema.md](./../skills/backlog/references/item-schema.md)` in Section 6
   - `backlog.py`: `[backlog.py](./../skills/backlog/scripts/backlog.py)` in Section 1 Layer 3
   - `/work-backlog-item`: `[work-backlog-item/SKILL.md](./../skills/work-backlog-item/SKILL.md)`
     in States 5, 6, 7 descriptions
   - `/groom-backlog-item`:
     `[groom-backlog-item/SKILL.md](./../skills/groom-backlog-item/SKILL.md)` in State 3
   - `/create-backlog-item`:
     `[create-backlog-item/SKILL.md](./../skills/create-backlog-item/SKILL.md)` in State 1
   - project workflow: `[project_workflow.draft.md](./../project_workflow.draft.md)` in Section 1
   - GitHub Action: `[backlog-sync.yml](./../../.github/workflows/backlog-sync.yml)` in Section 2
     State 2 and Section 3
2. Add inbound links TO `.claude/docs/backlog-lifecycle.md` FROM each source file below. Read
   each file first to find the correct placement. Use the one-line "Lifecycle reference" pattern
   from codebase analysis Section Recommendations #2:
   - `.claude/skills/backlog/SKILL.md`: add after first heading or in References section;
     path `../../docs/backlog-lifecycle.md`
   - `.claude/skills/work-backlog-item/SKILL.md`: add in GitHub Integration section or references
     list; path `../../docs/backlog-lifecycle.md`
   - `.claude/skills/groom-backlog-item/SKILL.md`: add in Step 7 context or references list;
     path `../../docs/backlog-lifecycle.md`
   - `.claude/skills/create-backlog-item/SKILL.md`: add in References section;
     path `../../docs/backlog-lifecycle.md`
   - `.claude/skills/backlog-tools-administrator/references/domain-registry.md`: update the
     lifecycle entry to use a markdown link; path `../../../docs/backlog-lifecycle.md`
   - `.claude/agents/backlog-item-groomer.md`: add lifecycle reference if this file exists;
     verify with `Glob` first
   - `.claude/project_workflow.draft.md`: add in Data Architecture section;
     path `./docs/backlog-lifecycle.md`; add note that `project_workflow.draft.md` is itself a
     draft (per architect spec Risk 4 mitigation)
3. For each inbound link, use the pattern:
   `**Lifecycle reference**: See [Backlog Lifecycle](../../docs/backlog-lifecycle.md) for the
   full item lifecycle, state transitions, and data architecture.`
4. Surround each added link with blank lines (MD031 compliance)
5. Do not add links to `.claude/CLAUDE.md` — that file is out of scope per architect spec

## Constraints

- All paths must use `./` prefix and be relative to the file containing the reference
- Verify each target file exists with `Read` before adding the link
- Do not add more than one lifecycle reference per file
- Do not restructure files — add links at natural section boundaries only
- `project_workflow.draft.md` stale BACKLOG.md references are out of scope; add only the single
  lifecycle link to the Data Architecture section

## Expected Outputs

- `.claude/docs/backlog-lifecycle.md`: outbound markdown links to 8 target files added
- `.claude/skills/backlog/SKILL.md`: inbound link added
- `.claude/skills/work-backlog-item/SKILL.md`: inbound link added
- `.claude/skills/groom-backlog-item/SKILL.md`: inbound link added
- `.claude/skills/create-backlog-item/SKILL.md`: inbound link added
- `.claude/skills/backlog-tools-administrator/references/domain-registry.md`: lifecycle entry
  updated to markdown link
- `.claude/project_workflow.draft.md`: inbound link added in Data Architecture section
- `.claude/agents/backlog-item-groomer.md`: inbound link added if file exists

## Acceptance Criteria

1. Every file in the inbound list has a markdown link to `backlog-lifecycle.md`
2. `backlog-lifecycle.md` has markdown links to all 8 outbound targets
3. All paths use `./` prefix relative to the file containing the reference
4. No link points to `backlog-lifecycle.draft.md` (old filename)

## Verification Steps

```bash
# Confirm outbound links exist in lifecycle doc
grep -c "]\(./" .claude/docs/backlog-lifecycle.md

# Confirm each inbound file has the lifecycle link
grep -l "backlog-lifecycle.md" \
  .claude/skills/backlog/SKILL.md \
  .claude/skills/work-backlog-item/SKILL.md \
  .claude/skills/groom-backlog-item/SKILL.md \
  .claude/skills/create-backlog-item/SKILL.md \
  .claude/skills/backlog-tools-administrator/references/domain-registry.md \
  .claude/project_workflow.draft.md

# Confirm no link points to old draft filename
grep -r "backlog-lifecycle.draft.md" .claude/skills/ .claude/docs/
```

## Can Parallelize With

None — depends on T3 (file must be renamed before links point to correct path)

## Handoff

Report to orchestrator:
- List of files modified with inbound links added
- List of outbound links added to backlog-lifecycle.md (count and targets)
- Whether `.claude/agents/backlog-item-groomer.md` was found and linked
- Any files that could not be linked and why

---
task: T5
title: Validate Links and Run Linting
status: not-started
agent: general-purpose
dependencies: ["T3", "T4"]
priority: 3
complexity: low
created: 2026-03-01T00:00:00Z
---

## Context

Tasks 3 and 4 modified the following files: `.claude/docs/backlog-lifecycle.md`,
`.claude/skills/backlog/SKILL.md`, `.claude/skills/work-backlog-item/SKILL.md`,
`.claude/skills/groom-backlog-item/SKILL.md`, `.claude/skills/create-backlog-item/SKILL.md`,
`.claude/skills/backlog-tools-administrator/references/domain-registry.md`,
`.claude/project_workflow.draft.md`, and potentially `.claude/agents/backlog-item-groomer.md`.
All must pass `uv run prek run --files` (the repo's linter) and all markdown links must resolve
to existing files. This is the final quality gate before the issue can be closed.

## Objective

Run `uv run prek run --files` on every modified file, verify all markdown links resolve to
existing files, and fix any linting errors or broken links found.

## Requirements

1. Run `uv run prek run --files <file>` on each modified file individually. The files to check
   (from architect spec Section 6 Constraint 2):
   - `.claude/docs/backlog-lifecycle.md`
   - `.claude/skills/backlog/references/state-machine.md` (if modified in T4)
   - `.claude/skills/backlog/references/item-schema.md` (if modified in T4)
   - `.claude/skills/backlog/SKILL.md`
   - `.claude/skills/work-backlog-item/SKILL.md`
   - `.claude/skills/groom-backlog-item/SKILL.md`
   - `.claude/skills/create-backlog-item/SKILL.md`
   - `.claude/skills/backlog-tools-administrator/references/domain-registry.md`
   - `.claude/project_workflow.draft.md`
   - `.claude/agents/backlog-item-groomer.md` (if modified in T4)
2. For each file, extract all markdown links `[text](path)` and verify the target file exists
   using `Read` (attempting to read each target path)
3. Fix any linting errors: MD031 (blanks around fences), MD040 (code fence language specifiers),
   MD009 (trailing spaces), or any other violations reported by `prek`
4. Fix any broken markdown links by correcting the relative path
5. Re-run linting after each fix to confirm resolution
6. Run linting on all files together as a final check

## Constraints

- Do not modify file content beyond fixing linting errors and broken links
- Do not add new content or cross-references (that was Task 4)
- Verify only files modified in Tasks 3 and 4; do not run linting on unrelated files

## Expected Outputs

- All modified files pass `uv run prek run --files <file>` with exit code 0
- All markdown links in modified files resolve to existing files

## Acceptance Criteria

1. `uv run prek run --files .claude/docs/backlog-lifecycle.md` exits 0
2. `uv run prek run --files .claude/skills/backlog/SKILL.md` exits 0
3. `uv run prek run --files .claude/skills/work-backlog-item/SKILL.md` exits 0
4. `uv run prek run --files .claude/skills/groom-backlog-item/SKILL.md` exits 0
5. `uv run prek run --files .claude/skills/create-backlog-item/SKILL.md` exits 0
6. `uv run prek run --files .claude/skills/backlog-tools-administrator/references/domain-registry.md` exits 0
7. `uv run prek run --files .claude/project_workflow.draft.md` exits 0
8. No broken markdown links in any modified file

## Verification Steps

```bash
# Run linting on all modified files
uv run prek run --files \
  .claude/docs/backlog-lifecycle.md \
  .claude/skills/backlog/SKILL.md \
  .claude/skills/work-backlog-item/SKILL.md \
  .claude/skills/groom-backlog-item/SKILL.md \
  .claude/skills/create-backlog-item/SKILL.md \
  .claude/skills/backlog-tools-administrator/references/domain-registry.md \
  .claude/project_workflow.draft.md

# Confirm no remaining draft filename references
grep -r "backlog-lifecycle.draft" .claude/ --include="*.md" | grep -v "plan/"

# Confirm lifecycle doc has no [VERIFY] markers
grep "\[VERIFY\]" .claude/docs/backlog-lifecycle.md
```

## Handoff

Report to orchestrator:
- Exit codes from each `prek run` invocation
- Any linting errors found and how they were fixed
- Any broken links found and how they were corrected
- Final confirmation that all files pass linting and all links resolve

## Context Manifest

### How the Backlog Lifecycle Currently Works

The backlog ecosystem is a three-layer system where all backlog item operations are mediated through the `backlog.py` script. The architecture is described comprehensively in `.claude/docs/backlog-lifecycle.draft.md` — the document being promoted in this task.

**Layer 1: GitHub Issues (canonical source of truth)**

GitHub Issues store the authoritative item status via labels. Status is encoded as `status:*` labels (exactly one per item at any time), and priority is encoded as `priority:*` labels (P0, P1, P2, or Ideas). When a local file and its linked issue disagree on status or priority, the GitHub issue wins — this is the ground truth.

**Layer 2: Local cache (.claude/backlog/*.md files)**

Per-item markdown files exist in `.claude/backlog/` using the naming pattern `{priority}-{slug}.md` (e.g., `p1-fix-error-recovery.md`). These files contain YAML frontmatter with metadata (name, description, source, added date, priority, type, status, groomed date, issue number, milestone, plan path) and markdown body sections (Description, Acceptance Criteria, Research First, Suggested Location, Fact-Check, RT-ICA, Groomed sections). These files are written exclusively by the `backlog.py` script and serve as a cache for agent consumption to avoid GitHub API saturation during sessions. They are never edited directly by skills or agents — all reads and writes go through the script.

**Layer 3: backlog.py script (sole interface)**

The script at `./.claude/skills/backlog/scripts/backlog.py` is the ONLY interface for reading and writing backlog items. It handles:

- Creating per-item files with correct frontmatter (via `backlog add`)
- Creating and closing GitHub Issues (via `backlog add --create-issue`, `backlog sync`, `backlog close`, `backlog resolve`)
- Syncing groomed content to issue bodies (via `backlog groom`)
- Writing label transitions (via implicit operations during `add`, `sync`, `groom`, `update`, `close`, `resolve`)
- Writing `metadata.issue` back to the local file frontmatter after issue creation
- Pulling external GitHub state back to local files (via `backlog pull`)

All skills that work with backlog items invoke this script: `/create-backlog-item` invokes `backlog add`, `/groom-backlog-item` invokes `backlog groom`, `/work-backlog-item` invokes `backlog list`, `backlog update`, `backlog close`, and `backlog resolve`. The GitHub Actions workflow at `.github/workflows/backlog-sync.yml` monitors `.claude/backlog/` file changes and automatically runs `backlog sync` when new P0/P1 items are committed.

### Item State Machine and Transitions

Items flow through 8 distinct states managed by the script:

1. **State 1: Created (local only)** — `/create-backlog-item` collects fields and invokes `backlog add`, creating a per-item file with `status: needs-grooming`. For P0/P1 items, a GitHub Issue may be created immediately with `--create-issue`.

2. **State 2: Synced to GitHub** — `backlog sync` scans `.claude/backlog/` for P0/P1 items without a `metadata.issue` field, creates a GitHub Issue for each, and writes `metadata.issue: '#N'` back to the file. The GitHub Action on `.claude/backlog/` changes automatically triggers this sync.

3. **State 3: Groomed** — `/groom-backlog-item` orchestrates fact-checking and autonomously writes groomed sections via `backlog groom`. After all 7 required sections (Fact-Check, RT-ICA, Reproducibility, Dependencies, Skills, Agents, Prior Work) are present, `metadata.groomed` is set and the GitHub label transitions from `status:needs-grooming` to `status:groomed`.

4. **State 4: In Milestone** — `/group-items-to-milestone` assigns the item to a GitHub milestone, writing `metadata.milestone: {N}` and updating the label to `status:in-milestone`.

5. **State 5: In Progress** — `/work-backlog-item` after RT-ICA approval creates a SAM task file and invokes `backlog update` to set `metadata.plan: path/to/tasks-{N}-{slug}.md` and `status: in-progress`. The script updates the GitHub label accordingly.

6. **State 6: Done (closed)** — `/work-backlog-item close` verifies the task checklist is 100% complete and acceptance criteria pass, then invokes `backlog close --checklist-pass` to set `metadata.status: done` and close the GitHub issue. The `--cleanup` flag (if it exists) deletes the local file; otherwise the file remains with `status: done`.

7. **State 7: Resolved (won't-fix)** — Any skill or `/work-backlog-item resolve` invokes `backlog resolve` when an item is invalid, obsolete, or superseded. The script sets `metadata.status: resolved`, closes the GitHub issue with an optional resolution comment, and optionally deletes the local file with `--cleanup`.

8. **State 8: Pulling from GitHub** — `backlog pull` (if it exists as a subcommand) syncs external GitHub changes back to local files. The draft indicates it should fetch current issue state and overwrite or merge local file bodies with current issue bodies, updating `metadata.status` to match GitHub label state.

### Critical Architectural Constraints

**Source of truth precedence**: When a local cache file and its GitHub issue disagree, the GitHub issue is authoritative. The script enforces this by always reading GitHub labels as the canonical status and merging or overwriting local content.

**Label atomicity**: Status transitions must remove the old `status:*` label and add the new one in a single API call to prevent momentary states where two `status:*` labels exist. The draft claims this is atomic; Task 1 verifies this by reading the label code or observing label transitions.

**Metadata write-back pattern**: When `backlog add --create-issue` or `backlog sync` creates a GitHub Issue, the script writes the new issue number back to `metadata.issue` in the local file frontmatter. This is a bidirectional write that links the two layers in a single operation.

**Grooming completeness**: An item is considered "fully groomed" only when all 7 required sections are present AND `metadata.groomed` is set. Partial grooming (some sections present) is not considered groomed, and `/groom-backlog-item` resumes from the first missing section on re-run.

**No direct edits policy**: Skills and agents never directly edit `.claude/backlog/*.md` files or invoke GitHub API (`gh issue edit`) directly. All mutations go through `backlog.py`. This ensures consistent metadata handling and prevents races between the script and manual edits.

### What Gets Verified in This Task

The draft document describes 8 states, transitions, and behaviors. Seventeen `[VERIFY]` annotations mark claims that require confirmation against live script behavior. The architect spec (Section 1) organizes these into categories:

- **6 annotations resolvable by `--help` output**: Checking whether `backlog pull`, `--cleanup`, `--force`, and `--priority` flags exist in the script's help text.
- **5 annotations resolvable by running test commands**: Creating a throwaway item, executing grooming and state transitions, and observing actual file changes and GitHub label updates.
- **2 annotations resolvable by searching for related skills**: Looking for `/group-items-to-milestone` and `/complete-milestone` skills to understand milestone management.
- **1 annotation pre-resolved**: GitHub Action trigger confirmed by reading `.github/workflows/backlog-sync.yml`.

### Files Involved in This Task

**Source file being promoted:**
- `.claude/docs/backlog-lifecycle.draft.md` (674 lines) — contains 8 state descriptions, data architecture explanation, lifecycle flow diagram, label/priority mapping table, testing checklist with 25 items across 7 categories, and 17 `[VERIFY]` annotations

**Script being tested:**
- `.claude/skills/backlog/scripts/backlog.py` (100+ lines) — implements `add`, `list`, `sync`, `close`, `resolve`, `update`, `groom`, `normalize`, and possibly `pull` subcommands; uses `github.Github`, `typer`, `frontmatter`, and `ruamel.yaml` libraries

**Skills receiving inbound links (Task 4):**
- `.claude/skills/backlog/SKILL.md` — describes the script's subcommands and invocation
- `.claude/skills/work-backlog-item/SKILL.md` — orchestrates item grooming and planning workflow
- `.claude/skills/groom-backlog-item/SKILL.md` — manages fact-checking and grooming orchestration
- `.claude/skills/create-backlog-item/SKILL.md` — creates new items with optional GitHub issues
- `.claude/skills/backlog-tools-administrator/references/domain-registry.md` — lists all backlog-related skills and scripts

**Reference files within backlog ecosystem (Task 4 outbound links):**
- `.claude/skills/backlog/references/state-machine.md` — defines formal state transitions (read by architect spec)
- `.claude/skills/backlog/references/item-schema.md` — documents per-item file frontmatter structure
- `.claude/skills/backlog/scripts/backlog.py` — script that implements all operations

**Workflow file (Task 1 pre-verification):**
- `.github/workflows/backlog-sync.yml` — GitHub Action that triggers `backlog sync` on `.claude/backlog/` changes

**Other files receiving inbound links:**
- `.claude/agents/backlog-item-groomer.md` — agent spawned by `/groom-backlog-item` (may or may not exist)
- `.claude/project_workflow.draft.md` — project-level workflow that references backlog (receives one lifecycle link)

**Related planning artifacts (read-only, NOT to be edited):**
- `plan/feature-context-backlog-lifecycle-promotion.md` — discovery analysis
- `plan/codebase/cross-references-backlog.md` — codebase analysis with path conventions
- `plan/architect-backlog-lifecycle-promotion.md` — architecture specification with verification strategy

### Testing Strategy (Task 1)

Task 1 executes the 25-item testing checklist from Section 7 of the draft. The items are organized into 7 categories:

1. **Data Architecture (4 tests)**: Verifying `backlog add` behavior with/without `--create-issue`, `backlog sync` deduplication, and dry-run support.

2. **State Transitions (5 tests)**: Checking whether `backlog groom` appends without overwriting, `metadata.groomed` is set only after all 7 sections, `backlog update` behavior, and enforcement of required flags like `--checklist-pass`.

3. **Cleanup Behavior (4 tests)**: Testing whether `--cleanup` flag exists on `backlog close` and `backlog resolve`, and whether `/complete-milestone` deletes local files or sets `status: closed`.

4. **Pull/Bidirectional Sync (3 tests)**: Verifying `backlog pull --dry-run` output, `metadata.status` updates, and preservation of `metadata.plan` and `metadata.groomed` fields.

5. **Priority and Label Mapping (3 tests)**: Confirming P2/Ideas items never get GitHub issues, label transitions are atomic, and `--priority` flag exists for re-prioritization.

6. **GitHub Action Integration (3 tests)**: Reading `.github/workflows/backlog-sync.yml` to confirm trigger definition and command execution.

7. **Post-Merge Behavior (3 tests)**: Testing issue closure after PR merge and subsequent `backlog sync` behavior.

The verification strategy (architect spec Section 1) orders tests to run `--help` commands first (which gate other tests), then creates a single throwaway test item (`lifecycle-verify-test`) for behavioral tests, and cleans it up before the task completes. Tests T20, T21, T22 (GitHub Action tests) are pre-confirmed by reading the workflow file. Test T23 (PR merge) is marked NOT TESTABLE because it requires an actual PR merge.

### Path Conventions (Task 4 cross-referencing)

When adding inbound and outbound markdown links, paths must be relative and use `./` prefix per CLAUDE.md standards:

**From skill SKILL.md to `.claude/docs/`:**
- Path: `../../docs/backlog-lifecycle.md` (from `.claude/skills/{name}/SKILL.md` up two levels to `.claude/`, then into `docs/`)

**From skill reference files to `.claude/docs/`:**
- Path: `../../../docs/backlog-lifecycle.md` (from `.claude/skills/{name}/references/*.md` up three levels to repository root, then into `.claude/docs/`)

**From domain registry to `.claude/docs/`:**
- Path: `../../../docs/backlog-lifecycle.md` (from `.claude/skills/backlog-tools-administrator/references/domain-registry.md`)

**From project workflow to `.claude/docs/`:**
- Path: `./docs/backlog-lifecycle.md` (from `.claude/project_workflow.draft.md` at `.claude/` level, down into `docs/`)

**From lifecycle doc outbound to skills:**
- Path: `./../skills/{name}/SKILL.md` or `./../skills/{name}/references/*.md` (from `.claude/docs/backlog-lifecycle.md`)

**From lifecycle doc to workflow:**
- Path: `./../../.github/workflows/backlog-sync.yml` (from `.claude/docs/` to repository root `.github/`)

All paths must be verified to exist with the `Read` tool before adding links. The architect spec Section 4.2 provides an authoritative path reference table.

### Content Cleanup Rules (Task 2)

When Task 1 produces test results, Task 2 uses them to resolve `[VERIFY]` annotations. The architect spec Section 5 defines cleanup rules:

- **Annotation verified true**: Remove the `[VERIFY]` marker, keep the sentence, add a citation if the claim is not obvious.
- **Annotation verified false/different**: Remove the marker, correct the sentence to match observed behavior, add a NOTE block if the correction is non-obvious or surprising.
- **Feature gap discovered**: Remove the marker, add a NOTE block stating "not implemented as of 2026-03-01" and describing the gap.
- **Special case — `backlog pull` subcommand**: If Task 1 finds that `pull` does not exist, apply Section 5.4 treatment to Section 2 State 8 (add "(Planned)" to title and prepend NOTE), the data flow diagram (dashed PULL node), sync direction table (add "(planned)" suffix), and Section 7.4 tests T14-T16 (mark SKIPPED).

The cleanup rules ensure that the final promoted document contains only verified, accurate claims or clearly marked future/planned features.

### Renaming Strategy (Task 3)

Task 3 renames the file from `backlog-lifecycle.draft.md` to `backlog-lifecycle.md` using `git mv` to preserve history. The DRAFT artifacts are then removed:

- Line 1: HTML comment `<!-- DRAFT — 2026-02-27 — Pending verification against live script behavior -->` deleted.
- Lines 4-6: The `**STATUS: DRAFT**` paragraph and surrounding blank lines deleted.
- Lines 8-14: The SOURCE block backtick paths are converted to proper markdown links using the path conventions above.

After the rename, any file in the codebase referencing the old `backlog-lifecycle.draft.md` path (excluding plan artifacts) must be updated to point to `backlog-lifecycle.md`. The `domain-registry.md` entry changes from `(draft)` to `(canonical)` status.

### Cross-Reference Linking Strategy (Task 4)

Task 4 establishes two-way markdown links:

**Outbound links FROM `.claude/docs/backlog-lifecycle.md`:**
- State machine reference file — linked in Section 2 intro or new Related References section
- Item schema reference file — linked in Section 6 (Item File Structure)
- `backlog.py` script — linked in Section 1 Layer 3 description
- `/work-backlog-item` skill — linked in States 5, 6, 7 descriptions
- `/groom-backlog-item` skill — linked in State 3 description
- `/create-backlog-item` skill — linked in State 1 description
- Project workflow draft — linked in Section 1 overview
- GitHub Actions workflow — linked in Section 2 State 2 and Section 3 data flow

**Inbound links TO `.claude/docs/backlog-lifecycle.md` FROM:**
- `.claude/skills/backlog/SKILL.md` — added in References section or context note
- `.claude/skills/work-backlog-item/SKILL.md` — added in GitHub Integration section or references
- `.claude/skills/groom-backlog-item/SKILL.md` — added in Step 7 context or references
- `.claude/skills/create-backlog-item/SKILL.md` — added in References section
- `.claude/skills/backlog/references/state-machine.md` — "See Also" section after state diagram
- `.claude/skills/backlog/references/item-schema.md` — "See Also" section after completeness states
- `.claude/skills/backlog-tools-administrator/references/domain-registry.md` — lifecycle entry updated to markdown link
- `.claude/agents/backlog-item-groomer.md` — added if file exists (verify with Glob first)
- `.claude/project_workflow.draft.md` — added in Data Architecture section with note that file is a draft

Each inbound link uses the standard pattern:
```markdown
**Lifecycle reference**: See [Backlog Lifecycle](../../docs/backlog-lifecycle.md) for the full item lifecycle, state transitions, and data architecture.
```

Links are surrounded with blank lines for MD031 compliance.

### Linting and Validation (Task 5)

After Tasks 3 and 4, all modified files must pass `uv run prek run --files <file>` with exit code 0. Files to lint:
- `.claude/docs/backlog-lifecycle.md`
- `.claude/skills/backlog/SKILL.md`
- `.claude/skills/work-backlog-item/SKILL.md`
- `.claude/skills/groom-backlog-item/SKILL.md`
- `.claude/skills/create-backlog-item/SKILL.md`
- `.claude/skills/backlog-tools-administrator/references/domain-registry.md`
- `.claude/project_workflow.draft.md`
- `.claude/agents/backlog-item-groomer.md` (if modified)
- `.claude/skills/backlog/references/state-machine.md` (if modified)
- `.claude/skills/backlog/references/item-schema.md` (if modified)

Common linting issues to watch for: MD031 (blanks around code fences), MD040 (code fence language specifiers), MD009 (trailing spaces), and broken markdown links. All markdown links must resolve to existing files — verify by attempting to read each target path.

### Key Implementation Details

**Test item naming and cleanup (Task 1):**
Create a single throwaway item with `uv run .claude/skills/backlog/scripts/backlog.py add --title "lifecycle-verify-test" --priority P1 --description "test" --create-issue`. After all behavioral tests complete, resolve this item with `backlog resolve "lifecycle-verify-test" --reason "Test item for lifecycle verification" --cleanup` before Task 1 completes. Verify deletion with `uv run .claude/skills/backlog/scripts/backlog.py list | grep -c "lifecycle-verify-test"` (should return 0).

**GitHub token and repository reference (Task 1 commands):**
`GITHUB_TOKEN` environment variable is required for any `backlog.py` command that touches GitHub. All `gh` commands must include `-R Jamie-BitFlight/claude_skills` because the git remote is a local proxy, not the live GitHub URL.

**`backlog pull` subcommand gate (Task 1):**
Run `uv run .claude/skills/backlog/scripts/backlog.py pull --help` first. If exit code is non-zero (command not found), tests T14-T16 (pull tests) are immediately marked SKIPPED, and Task 2 must apply the "planned behavior" treatment to State 8, the data flow diagram, and the sync direction table.

**Deduplication of [VERIFY] annotations (Task 2):**
17 annotations exist but only 14 are unique. Annotation #4 is a duplicate of #2, and #5 is a duplicate of #3. When resolving, each unique annotation is resolved once, and duplicate markers are removed from all affected locations in the text.

### Documentation Dependencies

- **Architect spec (read-only)**: `plan/architect-backlog-lifecycle-promotion.md` defines the exact verification strategy (Section 1), content cleanup rules (Section 5), file modification list (Section 2), and path conventions (Section 4). This is the authoritative guide for Tasks 1–5.
- **Codebase analysis (read-only)**: `plan/codebase/cross-references-backlog.md` provides the path reference table and link conventions. Use this as the primary source for correct relative paths.
- **Feature context (read-only)**: `plan/feature-context-backlog-lifecycle-promotion.md` contains the original discovery analysis and annotation catalog. Reference this if understanding the rationale for any annotation.

### Error Prevention Checklist

Before completing each task:

**Task 1**: Verify that the throwaway test item is resolved and deleted (grep should return 0). Confirm all 25 test results are in `plan/testing-results-backlog-lifecycle.md`. Check whether `backlog pull` exists (this gates Task 2 decisions).

**Task 2**: Run `grep -c "\[VERIFY\]" .claude/docs/backlog-lifecycle.draft.md` and confirm it returns 0. Verify all 25 Section 7 checklist items are marked `[x]` with result notes. Check that no content claims behaviors Task 1 testing disproved.

**Task 3**: Confirm old file is gone (`ls .claude/docs/backlog-lifecycle.draft.md` should error). Run `grep -r "backlog-lifecycle.draft" .claude/ --exclude-dir=plan` and confirm zero results (plan artifacts are intentionally excluded). Verify DRAFT HTML comment and STATUS: DRAFT paragraph are removed from the promoted file.

**Task 4**: For each inbound file, verify the lifecycle link was added using `grep -l "backlog-lifecycle.md"`. For the promoted file, count outbound links and verify they point to correct relative paths. Confirm no link points to the old `backlog-lifecycle.draft.md` filename.

**Task 5**: Run `uv run prek run --files` on each modified file and confirm all exit codes are 0. Attempt to read each markdown link target to verify it exists. Confirm the promoted file has zero `[VERIFY]` markers and zero unchecked Section 7 checklist items.

### Key Technical Reference

**backlog.py command structure:**
```bash
uv run .claude/skills/backlog/scripts/backlog.py <subcommand> [options]
```

Subcommands visible in help/docstring: `add`, `list`, `view`, `sync`, `close`, `resolve`, `update`, `groom`, `normalize`, `pull`. Help flags: `--help` on subcommand shows options and descriptions.

**Per-item file frontmatter structure:**
```yaml
---
name: "Item title"
description: "One-sentence summary"
metadata:
  topic: "kebab-case-slug"
  source: "Trigger or discovery method"
  added: YYYY-MM-DD
  priority: P0|P1|P2|Ideas
  type: Feature|Bug|Refactor|Docs|Chore
  status: needs-grooming|groomed|blocked|in-milestone|in-progress|done|resolved|closed
  groomed: YYYY-MM-DD (set only when all 7 sections present)
  issue: '#N' (GitHub issue number, written back by script)
  milestone: N (GitHub milestone number)
  plan: path/to/tasks-{N}-{slug}.md
---
```

**GitHub label format:**
- Status labels: `status:needs-grooming`, `status:groomed`, `status:blocked`, `status:in-milestone`, `status:in-progress`, `status:done`, `status:resolved`, `status:closed` (exactly one per issue)
- Priority labels: `priority:P0`, `priority:P1`, `priority:P2`, `priority:Ideas` (one per issue)
- Type labels: `type:feature`, `type:bug`, `type:refactor`, `type:docs`, `type:chore` (one per issue)
