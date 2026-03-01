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

### Key Files

- `.claude/docs/backlog-lifecycle.draft.md` — Source draft (674 lines, 17 `[VERIFY]` annotations,
  25-item Section 7 testing checklist)
- `.claude/skills/backlog/scripts/backlog.py` — Live script to test against
- `.github/workflows/backlog-sync.yml` — Workflow confirming T20, T21, T22 pre-resolved
- `plan/feature-context-backlog-lifecycle-promotion.md` — Discovery: annotation catalog,
  testing checklist catalog, cross-reference plan, risks
- `plan/codebase/cross-references-backlog.md` — Codebase analysis: link conventions,
  correct relative paths from each source location
- `plan/architect-backlog-lifecycle-promotion.md` — Architecture spec: verification strategy
  (Section 1), testing strategy (Section 2), rename strategy (Section 3), cross-reference
  architecture (Section 4), content cleanup rules (Section 5), constraints (Section 6)
- `.claude/docs/TASK_FILE_FORMAT.md` — Task file format reference

### Architecture Decisions

- `backlog pull` subcommand status is an execution gate: check `pull --help` exit code first
- Testing and verification share a single throwaway test item to minimize side effects
- `project_workflow.draft.md` gets only the lifecycle link; its stale BACKLOG.md references
  are out of scope
- Plan artifacts (`plan/feature-context-*.md`, `plan/architect-*.md`) intentionally retain
  old draft filename references — do not edit them

### Path Reference Table (from codebase analysis)

| Source file | Path to `backlog-lifecycle.md` |
|---|---|
| `.claude/skills/*/SKILL.md` | `../../docs/backlog-lifecycle.md` |
| `.claude/skills/backlog/references/*.md` | `../../../docs/backlog-lifecycle.md` |
| `.claude/skills/backlog-tools-administrator/references/*.md` | `../../../docs/backlog-lifecycle.md` |
| `.claude/project_workflow.draft.md` | `./docs/backlog-lifecycle.md` |
| `.claude/docs/backlog-lifecycle.md` back-links | `../skills/{name}/SKILL.md` |
