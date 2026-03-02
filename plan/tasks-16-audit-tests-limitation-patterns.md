# Task Plan: Audit Tests That Document Bugs as 'Limitations' — Update After Fixes

**Issue**: #335
**Slug**: audit-tests-limitation-patterns
**Date**: 2026-03-02
**Architecture Spec**: plan/architect-audit-tests-limitation-patterns.md
**Feature Context**: plan/feature-context-audit-tests-limitation-patterns.md
**Codebase Analysis**: plan/codebase/TESTING.md

---

## Execution Strategy

Tasks 1 and 2 are comment-only edits to different files with no shared outputs — they run in parallel.
Task 3 requires a live test run before edits and operates on a third distinct file — it also runs in parallel with Tasks 1 and 2.
All three tasks have no mutual file conflicts. The full-suite regression check in each task's verification steps is the convergence point.

---

## SYNC CHECKPOINT (after all tasks complete)

**Convergence point**: Task 1 + Task 2 + Task 3 outputs

**Quality gates**:

- Zero `FAILED` results in targeted pytest runs for each file
- Task 3: no `XPASS` results (any XPASS means xfail was incorrectly applied — remove it)
- `uv run pytest -x --no-header` exits 0 (full suite, stops on first failure)

**Proceed**: Only after all three targeted pytest commands pass and the full suite is clean.

---

## Task 1: Update stale comment block in test_backlog_core_parsing.py

```yaml
---
task: "1"
title: Update stale limitation comment block in test_backlog_core_parsing.py
status: NOT STARTED
agent: python3-development:python-pytest-architect
skills:
  - python3-development:fastmcp-python-tests
  - python3-development:python3-review
dependencies: []
priority: 2
complexity: low
accuracy-risk: low
parallelize-with:
  - "2"
  - "3"
reason: Tasks 1, 2, and 3 each write to a distinct file. No shared output paths.
handoff: |
  Report: lines replaced (old text and new text), pytest output showing all tests still green,
  and confirmation that line 300 test assertions were not touched.
---
```

## Context

The module-level comment block in `.claude/skills/backlog/tests/test_backlog_core_parsing.py`
at lines 25-44 describes the nested-metadata stringification bug as if it is still present.
Commit `0e0611f` fixed `_parse_frontmatter` to preserve dict values. The test at line 300
(`test_parse_frontmatter_nested_meta_preserves_metadata`) already asserts the fixed behavior
correctly. The comment contradicts the test and misleads readers about current system behavior.

This task is a comment-only edit. No assertions, no test data constants, no imports are touched.

## Objective

Replace lines 25-44 with an accurate historical note that states the bug was fixed and explains
why other tests in the file continue to use flat frontmatter.

## Required Inputs

- File to edit: `.claude/skills/backlog/tests/test_backlog_core_parsing.py`
- Architecture spec for required comment structure: `plan/architect-audit-tests-limitation-patterns.md` (File 1 section, lines 44-64)
- Verification command: `uv run pytest .claude/skills/backlog/tests/test_backlog_core_parsing.py -v`

## Requirements

1. Read `.claude/skills/backlog/tests/test_backlog_core_parsing.py` lines 25-44 to confirm the current comment block content before editing.
2. Replace lines 25-44 with a comment block containing exactly:
   - One sentence: the nested-metadata stringification bug was fixed in commit `0e0611f`.
   - One sentence: tests below that use flat frontmatter were written before the fix; their coverage of flat-key parsing paths remains valid and intentional.
   - No statements about what is or is not accessible via `_parse_frontmatter`'s meta return value (those claims are now false).
3. Preserve all content outside lines 25-44 exactly — the module-level string constants (`_NESTED_META_FRONTMATTER`, `_FLAT_FRONTMATTER`, etc.) at line 46 onward must not be touched.
4. Preserve the test assertions at line 300 exactly — they are already correct.

## Constraints

- Do not modify any test assertion or test function body.
- Do not modify the module-level string constants (`_NESTED_META_FRONTMATTER`, `_FLAT_FRONTMATTER`, etc.).
- Do not add `pytest.mark.xfail` to any test in this file.
- Do not remove or reorder any imports.
- Scope is strictly lines 25-44 (the comment block between imports and the first module-level constant).

## Expected Outputs

- `.claude/skills/backlog/tests/test_backlog_core_parsing.py` — lines 25-44 replaced with accurate historical comment; all other content unchanged.

## Acceptance Criteria

1. Lines 25-44 no longer contain any assertion that nested metadata fields are inaccessible via `_parse_frontmatter`.
2. The replacement comment mentions commit `0e0611f` as the fix.
3. The replacement comment explains that flat-frontmatter tests remain valid for their coverage of flat-key parsing paths.
4. `uv run pytest .claude/skills/backlog/tests/test_backlog_core_parsing.py -v` exits 0 with zero failures.
5. The test `test_parse_frontmatter_nested_meta_preserves_metadata` (line 300) still asserts `meta["source"] == "test-source"` — unchanged.

## Verification Steps

1. Read lines 25-50 of the edited file and confirm the new comment contains the commit reference and the flat-frontmatter explanation, with no false claims.
2. Read lines 295-315 of the edited file and confirm the test at line 300 is unchanged.
3. Run `uv run pytest .claude/skills/backlog/tests/test_backlog_core_parsing.py -v` and confirm exit code 0, zero `FAILED` lines.

---

## Task 2: Update "pre-existing bug" mock docstrings in test_backlog_core_operations.py

```yaml
---
task: "2"
title: Update four mock docstrings from bug-workaround justification to isolation-pattern justification in test_backlog_core_operations.py
status: NOT STARTED
agent: python3-development:python-pytest-architect
skills:
  - python3-development:fastmcp-python-tests
  - python3-development:python3-review
dependencies: []
priority: 2
complexity: low
accuracy-risk: low
parallelize-with:
  - "1"
  - "3"
reason: Tasks 1, 2, and 3 each write to a distinct file. No shared output paths.
handoff: |
  Report: each of the four docstring locations (line, function name), old Why: text, new Why: text,
  and pytest output showing all tests still green. Confirm mocks were not removed.
---
```

## Context

Four test docstrings in `.claude/skills/backlog/tests/test_backlog_core_operations.py` state
that `parse_backlog` or `find_item` is mocked because `_parse_frontmatter` "has a pre-existing bug"
that drops nested metadata. That bug was fixed in commit `0e0611f`. The mocks remain correct
for test isolation — they inject pre-constructed `BacklogItem` instances so each test focuses
on operation logic (`list_items`, `close_item`, `resolve_item`), not on the parser.

The stale `Why:` clause is the only change. The mock itself stays in place.

## Objective

Update the `Why:` sentence in each of the four docstrings to describe test isolation as the
reason for the mock, removing the now-false "pre-existing bug" justification.

## Required Inputs

- File to edit: `.claude/skills/backlog/tests/test_backlog_core_operations.py`
- Architecture spec for replacement pattern: `plan/architect-audit-tests-limitation-patterns.md` (File 2 section, lines 96-121)
- Four target locations (confirmed by reading the file):
  - Line 285: `test_list_items_excludes_skip_items` — field: `skip`
  - Line 306: `test_list_items_with_status_enriches_from_batch_fetch` — field: `issue`
  - Line 492: `test_close_item_with_open_pr_raises_backlog_error` — field: `issue`
  - Line 597: `test_resolve_item_with_open_pr_raises_backlog_error` — field: `issue`
- Verification command: `uv run pytest .claude/skills/backlog/tests/test_backlog_core_operations.py -v`

## Requirements

1. Read `.claude/skills/backlog/tests/test_backlog_core_operations.py` at each of the four target lines before editing to confirm the existing `Why:` text.
2. For each of the four docstrings, replace only the `Why:` clause. The replacement follows this pattern:

   Old pattern:

   ```text
   Why: <behavior description>.  parse_backlog/find_item is mocked because
        _parse_frontmatter has a pre-existing bug that drops the <field> field
        from nested metadata.
   ```

   New pattern:

   ```text
   Why: <behavior description>.  parse_backlog/find_item is mocked to inject
        a BacklogItem with a specific <field> value directly, isolating this test
        from parsing logic.
   ```

   The `<behavior description>` sentence and the `<field>` name come from each docstring's existing text — do not invent new behavior descriptions.

3. Preserve the `Tests:` and `How:` clauses in each docstring exactly.
4. Do not remove, modify, or reorder the mock calls themselves (`mocker.patch(...)` lines).
5. Apply the change to all four locations — do not skip any.

## Constraints

- Do not remove any mock (`mocker.patch(...)`) line.
- Do not modify test assertions, test data, or any code outside the four `Why:` clauses.
- Do not add `pytest.mark.xfail` to any test in this file.
- Scope is strictly the `Why:` sentence within each of the four identified docstrings.

## Expected Outputs

- `.claude/skills/backlog/tests/test_backlog_core_operations.py` — four `Why:` clauses updated; all other content unchanged.

## Acceptance Criteria

1. All four docstrings no longer contain the phrase "pre-existing bug".
2. All four docstrings now explain the mock as an isolation pattern (injecting a `BacklogItem` with a specific field value).
3. The four `mocker.patch(...)` calls immediately following each docstring remain present and unchanged.
4. `uv run pytest .claude/skills/backlog/tests/test_backlog_core_operations.py -v` exits 0 with zero failures.
5. No other content in the file changed (confirm by reading the areas around each edit).

## Verification Steps

1. For each of the four locations, read 5 lines before and after the edit to confirm: `Why:` clause updated, `Tests:` and `How:` clauses unchanged, `mocker.patch(...)` unchanged.
2. Grep the file for "pre-existing bug" and confirm zero matches.
3. Run `uv run pytest .claude/skills/backlog/tests/test_backlog_core_operations.py -v` and confirm exit code 0, zero `FAILED` lines.

---

## Task 3: Verify and fix test_skills_array_bugs.py

```yaml
---
task: "3"
title: Observe test state, apply xfail to failing tests, and update module docstring in test_skills_array_bugs.py
status: NOT STARTED
agent: python3-development:python-pytest-architect
skills:
  - python3-development:fastmcp-python-tests
  - python3-development:python3-review
dependencies: []
priority: 2
complexity: medium
accuracy-risk: medium
parallelize-with:
  - "1"
  - "2"
reason: Tasks 1, 2, and 3 each write to a distinct file. No shared output paths.
handoff: |
  Report: pytest output from Phase A (raw pass/fail per test), list of tests that received xfail
  and list that did not, updated module docstring, and final pytest output showing zero FAILED
  and no XPASS results.
---
```

## Context

`plugins/plugin-creator/tests/test_skills_array_bugs.py` documents four bugs (Bugs 1-4) in
auto-discovery logic using an unconventional pattern: tests are written to fail against the
buggy code without `pytest.mark.xfail` decoration. The module docstring (lines 1-5) explicitly
states tests are "written so it FAILS against the current buggy code."

The actual pass/fail state of each test is unknown until the tests run — some bugs may have
been fixed since the file was written. This task observes actual state, applies the correct
`pytest.mark.xfail` pattern to still-failing tests, and updates the module docstring to reflect
reality.

`pytest.mark.xfail` is a built-in pytest marker. It does not require registration in
`pyproject.toml` markers list — `--strict-markers` only blocks undeclared custom markers.

## Objective

Ensure all tests in `test_skills_array_bugs.py` either pass normally (bug fixed) or are marked
`@pytest.mark.xfail(strict=True, reason="Bug N: ... See issue #335.")` (bug still present),
with zero `FAILED` results and zero `XPASS` results after changes.

## Required Inputs

- File to edit: `plugins/plugin-creator/tests/test_skills_array_bugs.py`
- Architecture spec for xfail pattern and decision rules: `plan/architect-audit-tests-limitation-patterns.md` (File 3 section, lines 134-206)
- Phase A command: `uv run pytest plugins/plugin-creator/tests/test_skills_array_bugs.py -v --no-header 2>&1`
- Test classes to classify:
  - `TestReconcileOnePluginDoesNotAddSkillsArrayForStandardPaths` (Bug 1, 2 tests)
  - `TestReconcileDoesNotAddCommandsArrayForInvocableStandardPathSkills` (Bug 2, 2 tests)
  - `TestUpdateComponentArraysDoesNotCreateSkillsArrayForStandardPaths` (Bug 3, 2 tests)
  - `TestPluginRegistrationValidatorDoesNotWarnAboutStandardPathSkills` (Bug 4, 3 tests)
  - `TestReconcileModeASkipsSkillsReconciliation` (Mode A extension, 1+ tests)
- Exception: `test_pr001_warning_still_fires_for_non_standard_path_skills` must never receive xfail regardless of observed state.

## Requirements

### Phase A — Observe

1. Run `uv run pytest plugins/plugin-creator/tests/test_skills_array_bugs.py -v --no-header 2>&1` and capture the complete output.
2. Record the PASSED / FAILED status of each individual test function from the output.

### Phase B — Apply the correct pattern per test

3. For each test that is currently FAILING (bug still present):
   - Add `@pytest.mark.xfail(strict=True, reason="Bug N: <one-line description from module docstring>. See issue #335.")` decorator immediately before the `def test_...` line.
   - Use the Bug number (1, 2, 3, or 4) that the test class documents.
   - Do not alter any assertion inside the test body.

4. For each test that is currently PASSING (bug already fixed):
   - Do not add any decorator.
   - Do not modify any assertion.

5. Do not apply xfail to `test_pr001_warning_still_fires_for_non_standard_path_skills` under any circumstances — this test explicitly documents the negative case and is expected to pass even against buggy code.

### Module docstring update

6. Update the module docstring (lines 1-5) based on observed state:
   - If all bugs fixed: describe the file as a regression test suite for previously-present bugs; reference issue #335.
   - If some bugs remain: describe which bugs are fixed (normal tests) and which are pending (xfail tests with issue #335 reference).
   - If all bugs remain: describe all as pending xfail tests with issue #335 reference.
   - Remove the sentence "written so it FAILS against the current buggy code" — tests now have individual xfail decorators where applicable, making this module-level claim redundant.

## Constraints

- Do not modify any assertion inside any test body.
- Do not remove any test function.
- Do not add `xfail` to `test_pr001_warning_still_fires_for_non_standard_path_skills`.
- Use `strict=True` on all xfail decorators — `strict=False` is not acceptable for this convention (per architecture spec).
- The `reason=` string must reference issue #335 and identify the bug number.
- Do not add xfail registration to `pyproject.toml` — it is a built-in marker and does not require registration.

## Expected Outputs

- `plugins/plugin-creator/tests/test_skills_array_bugs.py` — xfail decorators added to still-failing tests; module docstring updated to reflect actual state; test bodies and non-failing tests unchanged.

## Acceptance Criteria

1. `uv run pytest plugins/plugin-creator/tests/test_skills_array_bugs.py -v --no-header` exits 0.
2. Zero `FAILED` results in the output.
3. Zero `XPASS` results in the output (any XPASS means xfail was applied to a passing test — remove that decorator).
4. Every test that was FAILED in Phase A now appears as `XFAIL` in the final run.
5. Every test that was PASSED in Phase A still appears as `PASSED` in the final run (no regression).
6. `test_pr001_warning_still_fires_for_non_standard_path_skills` has no xfail decorator and appears as `PASSED`.
7. Module docstring no longer contains the sentence "written so it FAILS against the current buggy code".
8. Module docstring accurately describes which bugs are fixed and which remain pending.

## Verification Steps

1. Run Phase A command and record full output: `uv run pytest plugins/plugin-creator/tests/test_skills_array_bugs.py -v --no-header 2>&1`
2. After edits, run: `uv run pytest plugins/plugin-creator/tests/test_skills_array_bugs.py -v --no-header`
3. Confirm exit code 0, zero `FAILED`, zero `XPASS`.
4. Read the module docstring (lines 1-10) and confirm it no longer contains "written so it FAILS".
5. Grep the file for `xfail` and confirm every occurrence has `strict=True` and a reason referencing `#335`.
6. Grep the file for `test_pr001_warning_still_fires_for_non_standard_path_skills` context and confirm no `xfail` decorator is present for that function.

## CoVe Checks

- Key claims to verify:
  - `pytest.mark.xfail` does not require registration in `pyproject.toml` under `--strict-markers`
  - `strict=True` causes XPASS to fail CI (the expected behavior for bug-tracking xfail tests)
- Verification questions:
  1. Does `pyproject.toml` list `xfail` under `markers`? (Expected: No — it is a built-in marker and should not appear there.)
  2. Does adding `@pytest.mark.xfail(strict=True)` to a currently-passing test cause the test run to show an error rather than XPASS? (Expected: Yes — `strict=True` makes unexpected passes into failures.)
- Evidence to collect:
  - Read `pyproject.toml` lines 57-73 and confirm `xfail` is absent from the `markers` list.
  - After applying at least one xfail decorator, run the targeted pytest command and observe the output to confirm XFAIL (not FAILED) appears for that test.
- Revision rule:
  - If `pyproject.toml` inspection reveals `xfail` must be registered (unexpected finding), add the registration before proceeding and note the change in handoff.
  - If any decorated test shows XPASS instead of XFAIL, the bug was fixed — remove that xfail decorator and reclassify the test as PASSED.
