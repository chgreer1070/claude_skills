# Architecture Spec: Audit Tests That Document Bugs as Limitations

**Issue**: #335
**Date**: 2026-03-02
**Scope**: Surgical fix — 3 targeted file changes, no new infrastructure

---

## Executive Summary

Three test files contain stale or incorrectly structured documentation of known bugs. The fixes
are mechanical: a comment edit, a docstring update, and a test-state verification followed by
conversion to `pytest.mark.xfail`. No new fixtures, no new markers to register, no test logic
changes are required.

---

## System Context

The project's pytest configuration (`pyproject.toml`) uses:

- `asyncio_mode = "auto"` and `-n auto` (xdist)
- `--strict-markers` (custom markers must be declared; built-in markers including `xfail` are exempt)
- Test runner: `uv run pytest`

`pytest.mark.xfail` is a built-in pytest marker. It does not need to be registered in the
`markers` list in `pyproject.toml` before use. `--strict-markers` only blocks undeclared
*custom* markers, not built-ins.

---

## Affected Files and Required Changes

### File 1: `.claude/skills/backlog/tests/test_backlog_core_parsing.py`

**Lines 25-44** (the comment block between the imports and the first module-level constant)

**Current state**: The comment block asserts that `_parse_frontmatter` stringifies nested dicts,
making `meta` always return `{}`. This was the pre-fix behavior. Commit `0e0611f` fixed the
parser to preserve dict values. The test at line 300
(`test_parse_frontmatter_nested_meta_preserves_metadata`) already asserts the fixed behavior
correctly.

**Required change**: Replace lines 25-44 with a comment block that:

1. States the bug was fixed in commit `0e0611f`
2. Explains why other tests in the file still use flat frontmatter (they predate the fix and
   their coverage of flat-key paths is still valid — not because nested metadata is broken)
3. Does not assert that nested metadata is inaccessible (it is now accessible)

**What must NOT change**: The test assertions at line 300 are correct and must remain untouched.
The module-level string constants (`_NESTED_META_FRONTMATTER`, `_FLAT_FRONTMATTER`, etc.) must
remain untouched — they are used by the tests that follow.

**Target comment block structure** (implementer writes the actual prose):

```text
Lines 25-44 replacement:
- One sentence: the nested-metadata stringification bug was fixed in commit 0e0611f.
- One sentence: tests below that use flat frontmatter were written before the fix; their
  coverage of flat-key parsing paths remains valid and intentional.
- Remove all assertions about what is and is not accessible via _parse_frontmatter's meta
  return value, because those assertions are now false.
```

**Verification**: After the change, run:

```bash
uv run pytest .claude/skills/backlog/tests/test_backlog_core_parsing.py -v
```

All tests in this file must remain green.

---

### File 2: `.claude/skills/backlog/tests/test_backlog_core_operations.py`

**Four docstrings** at lines 285, 306, 492, 597

Each docstring contains a `Why:` sentence stating that `parse_backlog` or `find_item` is mocked
because `_parse_frontmatter` has a "pre-existing bug" that drops nested metadata.

**Required change**: Update only the `Why:` sentence in each of the four docstrings. The mock
itself stays — it serves legitimate test isolation (the test focuses on `list_items`/`close_item`/
`resolve_item` logic, not on the parser). The reason for the mock must change from "bug
workaround" to "test isolation".

**Decision rationale**: The mocks are not pure bug workarounds. Each test is asserting behavior
of an operation (skip filtering, batch fetch integration, PR guard) that depends on having a
`BacklogItem` with specific field values set (`skip=True`, `issue="#7"`, `issue="#5"`,
`issue="#8"`). Mocking `parse_backlog` or `find_item` to return pre-constructed `BacklogItem`
instances is the correct isolation pattern regardless of whether the parser bug exists. Removing
the mocks is out of scope for this task — the mock rationale comment is the only thing that is
stale.

**Replacement text pattern for each `Why:` sentence**:

The `Why:` clause must be changed from the pattern:

```text
Why: <test behavior description>.  parse_backlog/find_item is mocked because
     _parse_frontmatter has a pre-existing bug that drops the <field> field
     from nested metadata.
```

To the pattern:

```text
Why: <test behavior description>.  parse_backlog/find_item is mocked to inject
     a BacklogItem with a specific <field> value directly, isolating this test
     from parsing logic.
```

**Four locations to update**:

| Line | Function | Field referenced in bug comment |
|------|----------|---------------------------------|
| 285 | `test_list_items_excludes_skip_items` | `skip` |
| 306 | `test_list_items_with_status_enriches_from_batch_fetch` | `issue` |
| 492 | `test_close_item_with_open_pr_raises_backlog_error` | `issue` |
| 597 | `test_resolve_item_with_open_pr_raises_backlog_error` | `issue` |

**Verification**: After the change, run:

```bash
uv run pytest .claude/skills/backlog/tests/test_backlog_core_operations.py -v
```

All tests in this file must remain green.

---

### File 3: `plugins/plugin-creator/tests/test_skills_array_bugs.py`

**Current state**: The module docstring (lines 1-5) says tests are written to FAIL against the
current buggy code. The tests have no `pytest.mark.xfail` decoration. The actual pass/fail state
is unknown until the tests are run.

**Required change**: Two-phase approach.

#### Phase A — Observe current state

Run the file in isolation with verbose output to determine which tests pass and which fail:

```bash
uv run pytest plugins/plugin-creator/tests/test_skills_array_bugs.py -v --no-header 2>&1
```

Record the actual pass/fail status of each test class:

- `TestReconcileOnePluginDoesNotAddSkillsArrayForStandardPaths` (Bug 1, 2 tests)
- `TestReconcileDoesNotAddCommandsArrayForInvocableStandardPathSkills` (Bug 2, 2 tests)
- `TestUpdateComponentArraysDoesNotCreateSkillsArrayForStandardPaths` (Bug 3, 2 tests)
- `TestPluginRegistrationValidatorDoesNotWarnAboutStandardPathSkills` (Bug 4, 3 tests)
- `TestReconcileModeASkipsSkillsReconciliation` (Mode A extension, 1+ tests)

Note: `test_pr001_warning_still_fires_for_non_standard_path_skills` (line 472) explicitly
states it is expected to PASS even against buggy code — it tests the negative case. Do not
mark it xfail regardless of observation results.

#### Phase B — Apply the correct pattern based on observed state

**Case: A test is currently FAILING (bug still present)**

Apply `pytest.mark.xfail` with `strict=True` and a `reason` that references the issue number:

```python
@pytest.mark.xfail(
    strict=True,
    reason="Bug N: <one-line description>. See issue #335.",
)
def test_reconcile_leaves_plugin_json_unchanged_when_all_skills_at_standard_path(
    self, tmp_path: Path
) -> None:
```

`strict=True` means:
- If the test fails (expected): marked XFAIL in output — no CI failure
- If the test unexpectedly passes (bug fixed): marked XPASS and treated as an error — CI fails,
  signaling the team to remove the xfail decoration and update the module docstring

**Case: A test is currently PASSING (bug already fixed)**

Do not add `xfail`. The test is working correctly as a normal regression test. No change to
assertions. The module-level docstring is the only thing that is stale for these tests.

**Module docstring update**: After classifying all tests, update the module docstring (lines 1-5)
to accurately reflect the current state:

- If all bugs are fixed: Change docstring to describe the file as a regression test suite for
  previously-present bugs (reference commit or issue that fixed each bug).
- If some bugs remain: Change docstring to describe which bugs are fixed (normal tests) and
  which are pending (xfail tests).
- Remove the statement "written so it FAILS against the current buggy code" — this is only
  accurate for tests that are currently failing, and those will now have individual xfail
  decorators making the module-level claim redundant.

**Verification**: After the change, run:

```bash
uv run pytest plugins/plugin-creator/tests/test_skills_array_bugs.py -v --no-header
```

Expected outcome: Zero `FAILED` results. Tests that had bugs still present appear as `XFAIL`.
Tests whose bugs were fixed appear as `PASSED`. No `XPASS` results (that would mean a bug was
fixed but the xfail decorator was incorrectly applied — remove xfail from any XPASS test).

---

## Verification: Full Suite

After all three file changes are complete, run the full test suite to confirm no regressions:

```bash
uv run pytest -x --no-header
```

All tests must pass. Zero failures. xfail tests appear as XFAIL (not failures). The `-x` flag
stops on first failure to aid diagnosis.

---

## `pytest.mark.xfail` Conventions (for future reference)

This task establishes the team convention:

| Scenario | Convention |
|----------|-----------|
| Bug is known and confirmed unfixed | `@pytest.mark.xfail(strict=True, reason="Bug N: description. See issue #NNN.")` |
| Bug is fixed; test now passes normally | No marker; test is a normal regression test |
| Environmental constraint (not a bug) | Comment in docstring; no xfail |
| Feature boundary (intentional design) | Comment in docstring; no xfail |

`strict=True` is mandatory for unfixed-bug tests. Without `strict=True`, an unexpected pass
(`XPASS`) is silently recorded and does not fail CI. With `strict=True`, an unexpected pass
fails CI, ensuring the team removes the stale xfail decoration when the bug is fixed.

No registration in `pyproject.toml` markers list is required. `xfail` is a built-in pytest
marker. `--strict-markers` applies only to custom markers.

---

## Out of Scope

- Removing mocks from `test_backlog_core_operations.py` (mocks serve valid isolation; removal
  is a separate refactoring concern)
- Adding `xfail` to the project's `pyproject.toml` markers list (not required for built-ins)
- Documenting the convention in a `CONTRIBUTING.md` or separate doc (separate task if desired)
- Addressing pre-existing anti-patterns identified in `plan/codebase/TESTING.md` (duplicate
  `_call` helpers, redundant `@pytest.mark.asyncio`, `sys.path.insert` patterns) — these are
  out of scope for this surgical fix

---

## Execution Order

Tasks can be executed in any order. Each change is independent. Recommended order for
efficiency:

1. File 1 (comment edit in `test_backlog_core_parsing.py`) — lowest risk, no logic change
2. File 2 (four docstring edits in `test_backlog_core_operations.py`) — low risk, comment only
3. File 3 (observe then patch `test_skills_array_bugs.py`) — requires runtime observation first

Run the targeted pytest command after each file change before moving to the next.
