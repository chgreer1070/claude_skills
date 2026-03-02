# Feature Context: Audit Tests That Document Bugs as 'Limitations'

## Document Metadata

- **Generated**: 2026-03-02
- **Input Type**: existing_document (GitHub issue #335 description)
- **Source**: Issue #335 — "Audit tests that document bugs as 'limitations' — update after fixes"
- **Status**: DISCOVERY_COMPLETE

---

## Original Request

During backlog MCP scenario testing (#328), a prior bugfix to `_parse_frontmatter` (preserving nested metadata dicts) caused `test_parse_frontmatter_nested_meta_produces_empty_meta_dict` to fail. The test explicitly asserted the buggy behavior (`meta == {}`) with a comment calling it a 'documented limitation'. This pattern — tests that enshrine bugs as expected behavior — can mask regressions and block fixes.

Action: audit existing test suite for similar patterns where tests document current behavior as intentional limitations rather than testing correct behavior. Check for comments containing 'limitation', 'known issue', 'current behavior', 'workaround' that may be masking bugs.

---

## Core Intent Analysis

### WHO (Target Users)

Developers maintaining the claude_skills repository test suite. The action items are targeted at whoever owns each flagged test file.

### WHAT (Desired Outcome)

A verified list of every test file containing limitation/workaround patterns, each classified as either:

1. **Non-benign**: Tests asserting buggy behavior as correct — must be updated to assert correct behavior or marked with `pytest.mark.xfail` with an issue reference.
2. **Benign**: Tests that document a valid behavioral constraint (not a bug) — comments may need rewording but assertions are correct.

### WHEN (Trigger Conditions)

Triggered by the `_parse_frontmatter` bug fix in commit `0e0611f`, which broke a test written against the buggy behavior. This is a one-time audit triggered by discovering the pattern.

### WHY (Problem Being Solved)

Tests that enshrine bugs as expected behavior:

- Mask regressions (a re-introduced bug would make such a test pass silently)
- Block legitimate fixes (a correct fix causes the test to fail, signaling a false regression)
- Accumulate stale comments that mislead future readers about the true system behavior

---

## Codebase Research

### Similar Patterns Found

#### Pattern 1: Stale Module-Level Limitation Comment in test_backlog_core_parsing.py

- **Location**: `.claude/skills/backlog/tests/test_backlog_core_parsing.py:28-43`
- **Relevance**: The file's module-level docblock says "meta always comes back as {}" and that nested metadata fields "are NOT available through `_parse_frontmatter`'s meta return value." This matches the original bug that was fixed in commit `0e0611f`.
- **Current test assertion**: Line 300–310 — `test_parse_frontmatter_nested_meta_preserves_metadata` asserts the FIXED behavior (meta["source"] == "test-source", etc.), which is correct.
- **Problem**: The module comment (lines 28–43) still describes the old buggy behavior as fact. The comment contradicts the test assertion on line 300. A reader of the comment block alone would believe the bug is still present.
- **Assessment**: **Non-benign comment, benign assertion**. The assertion at line 300 is correct. The module-level comment block is stale and misleading — it needs to be updated to describe the current correct behavior.
- **Reusable**: The fix approach is purely comment-editing — no assertion changes needed.

#### Pattern 2: Tests Mocked "Because of Pre-existing Bug" in test_backlog_core_operations.py

- **Location**: `.claude/skills/backlog/tests/test_backlog_core_operations.py:285-286, 306-307, 489-492, 596-597`
- **Relevance**: Four test docstrings explain that `parse_backlog` or `find_item` is mocked specifically because `_parse_frontmatter` "has a pre-existing bug" that drops nested metadata fields (skip, issue). These are: `test_list_items_excludes_skip_items`, `test_list_items_with_status_enriches_from_batch_fetch`, `test_close_item_with_open_pr_raises_backlog_error`, `test_resolve_item_with_open_pr_raises_backlog_error`.
- **Assessment**: Requires verification. The stated bug in `_parse_frontmatter` has been fixed (commit `0e0611f`). If the fix is complete, the mocks may be unnecessary workarounds. However, the mocks may be legitimately providing test isolation (not just bug workarounds). The mock strategy needs to be evaluated against the current `_parse_frontmatter` implementation to determine if real parsing would now work.
- **Reusable**: The verification pattern is: attempt to remove mock and run with real parsing. If tests pass, mock was a workaround. If tests fail for reasons OTHER than the parser bug, mock is legitimate isolation.

#### Pattern 3: "Workaround" in agentskill-kaizen/tests/conftest.py

- **Location**: `plugins/agentskill-kaizen/tests/conftest.py:32-34`
- **Relevance**: A `# Workaround:` comment explains that FastMCP is replaced with a stub because FastMCP 3.x's `@mcp.tool` decorator triggers Pydantic TypeAdapter resolution at decoration time, which fails on Python 3.11 due to `from __future__ import annotations` deferring type evaluation.
- **Assessment**: **Benign**. This is a valid environmental constraint, not a bug in this codebase. The workaround is a legitimate test isolation pattern for an incompatibility between FastMCP and Python 3.11's annotation evaluation. The comment accurately documents the constraint and its reason.
- **Action needed**: None to the assertion. Comment wording is accurate.

#### Pattern 4: "scope limitation" in test_hook_validator.py

- **Location**: `plugins/plugin-creator/tests/test_hook_validator.py:75`
- **Relevance**: The docstring says "Tests: FileType detection scope limitation" for `test_js_outside_hooks_dir_not_detected_as_hook`.
- **Assessment**: **Benign**. The test asserts that `.js` files outside a `hooks/` directory return `FileType.UNKNOWN`. This is the correct designed behavior — only `.js/.cjs` files inside a `hooks/` directory are classified as `HOOK_SCRIPT`. The word "scope limitation" describes a feature boundary, not a bug. The assertion is correct.
- **Action needed**: Comment wording could be improved to say "Tests: FileType detection scope boundary" or "Tests: .js outside hooks/ correctly classified as UNKNOWN" — but this is cosmetic.

#### Pattern 5: "Bug workaround reversed" in test_frontmatter_validator.py

- **Location**: `plugins/plugin-creator/tests/test_frontmatter_validator.py:547-552`
- **Relevance**: Class `TestNameFieldRestoration` has docstring: "Test that the name field is restored during auto-fix (bug workaround reversed)." Documents that a Claude Code bug (2026-01-29) caused plugin skills with a `name` field to not appear as slash commands. Validators previously removed the `name` field as a workaround; they now add it back when absent.
- **Assessment**: **Benign**. The tests assert the fixed/restored behavior (name field is added when absent). The comment documents the history of why the behavior changed. The assertions are correct. No action needed on assertions.
- **Action needed**: None. The documentation is historically accurate and the assertions test current correct behavior.

#### Pattern 6: "Failing tests" file test_skills_array_bugs.py

- **Location**: `plugins/plugin-creator/tests/test_skills_array_bugs.py:1-5`
- **Relevance**: Module docstring explicitly says "Each test documents the DESIRED behaviour (what the code SHOULD do once fixed) and is written so it FAILS against the current buggy code. When the bugs are fixed the tests will pass without modification."
- **Assessment**: This is a special case. The file uses an unconventional pattern (tests written to FAIL intentionally) without `pytest.mark.xfail`. The issue stated "Correct convention is pytest.mark.xfail or TODO with issue reference." Whether these bugs (Bugs 1-4) have been fixed is not verifiable from static analysis alone — requires running the test suite.
- **Action needed**: Requires verification. Run `uv run pytest plugins/plugin-creator/tests/test_skills_array_bugs.py -v` to determine pass/fail state. If tests are now PASSING, the file comment is stale (and the workaround-style of writing intentionally-failing tests should be converted to normal test assertions or the file comment updated). If still FAILING, they should be converted to `pytest.mark.xfail(reason="...", strict=True)` with issue references.

### Existing Infrastructure

**pytest.mark.xfail**: Not currently used anywhere in the project test suite (verified by exhaustive grep across `.claude/skills/*/tests/**/*.py` and `plugins/*/tests/**/*.py`). The marker is available in pytest 8.4.1 (installed per `pyproject.toml:38`).

**`--strict-markers` in pytest config**: `pyproject.toml:58-65` configures `--strict-markers`. The marker `xfail` is a built-in pytest marker, not a custom one, so `--strict-markers` does not block its use. Custom markers are listed at lines 67-73 (demos, e2e, integration, slow, unit).

**No registered xfail markers**: Confirms `pytest.mark.xfail` is not currently part of the team's practice.

**Test runner**: `uv run pytest` per known context.

### Code References

- `.claude/skills/backlog/tests/test_backlog_core_parsing.py:28-43` — stale module comment describing bug as still present
- `.claude/skills/backlog/tests/test_backlog_core_parsing.py:300-310` — correct assertion for fixed behavior
- `.claude/skills/backlog/tests/test_backlog_core_operations.py:285-286` — mock justified by "pre-existing bug"
- `.claude/skills/backlog/tests/test_backlog_core_operations.py:306-307` — mock justified by "pre-existing bug"
- `.claude/skills/backlog/tests/test_backlog_core_operations.py:489-492` — mock justified by "pre-existing bug"
- `.claude/skills/backlog/tests/test_backlog_core_operations.py:596-597` — mock justified by "pre-existing bug"
- `plugins/agentskill-kaizen/tests/conftest.py:32-34` — workaround for FastMCP/Python 3.11 incompatibility (benign)
- `plugins/plugin-creator/tests/test_hook_validator.py:75` — "scope limitation" docstring (benign)
- `plugins/plugin-creator/tests/test_frontmatter_validator.py:547-552` — "bug workaround reversed" historical comment (benign)
- `plugins/plugin-creator/tests/test_skills_array_bugs.py:1-5` — intentionally-failing tests without xfail marker
- `.claude/skills/backlog/backlog_core/parsing.py:195-212` — current `_parse_frontmatter` implementation (bug fixed: line 204 preserves dict values)
- `pyproject.toml:57-73` — pytest configuration including `--strict-markers` and custom markers list

---

## Use Scenarios

### Scenario 1: Developer Fixes a Bug and a Test Breaks

**Actor**: Developer working on backlog_core
**Trigger**: Fixes `_parse_frontmatter` to preserve nested dicts; CI fails on a test asserting `meta == {}`
**Goal**: Understand whether the failing test is a correct regression signal or a stale limitation test
**Expected Outcome**: A clear distinction between "this test was asserting wrong behavior" (update it) vs "this test was correct and the fix broke something" (investigate)

### Scenario 2: Developer Reads a Test File's Comment Block

**Actor**: Developer reading `test_backlog_core_parsing.py` to understand `_parse_frontmatter`
**Trigger**: Needs to understand what the parser does with nested metadata
**Goal**: Learn correct behavior from the test documentation
**Expected Outcome**: The comment block accurately describes current behavior, not a fixed bug

### Scenario 3: CI Encounters a test_skills_array_bugs.py Failure

**Actor**: CI pipeline / reviewing developer
**Trigger**: A test in `test_skills_array_bugs.py` fails
**Goal**: Determine if this is a regression in auto_sync_manifests or a correctly-failing intentional test
**Expected Outcome**: With `pytest.mark.xfail`, CI can distinguish "expected failure" from "unexpected failure". Currently there is no signal difference.

### Scenario 4: Developer Removes a Mock "Because the Bug Is Fixed"

**Actor**: Developer improving `test_backlog_core_operations.py`
**Trigger**: Reads "parse_backlog is mocked because _parse_frontmatter has a pre-existing bug"
**Goal**: Verify the bug is fixed, remove the mock, let the test run against real parsing
**Expected Outcome**: Knows whether removing the mock is safe, and whether the comment is still accurate

---

## Gap Analysis

### Identified Gaps

| # | Category | Gap Description | Impact |
|---|----------|-----------------|--------|
| 1 | Behavior | Whether the `_parse_frontmatter` bug referenced in `test_backlog_core_operations.py` is fully fixed for ALL cases (skip field from nested metadata, issue field from nested metadata) — the fix is confirmed for `meta` dict extraction but `parse_item_file` uses `_fm_str(fm, meta, ...)` which looks in both `fm` and `meta`; need to verify the actual test scenarios work without mocks | If mocks are still necessary for non-bug reasons (e.g., filesystem isolation), removing them breaks tests for wrong reasons |
| 2 | Scope | Whether `test_skills_array_bugs.py` Bugs 1-4 are currently passing or failing — the module comment says they should fail against "current buggy code" but the bugs may have since been fixed | Cannot classify the file without running the tests |
| 3 | Behavior | What the team-agreed convention should be for tests written against known-buggy behavior going forward | Without a decision, new limitation tests will continue to be written inconsistently |
| 4 | Integration | Whether `pytest.mark.xfail` needs to be added to the custom markers list in `pyproject.toml` | `xfail` is a built-in marker so `--strict-markers` does not require registration, but this is worth confirming |

---

## Questions Requiring Resolution

### Q1: Are the mocks in test_backlog_core_operations.py still required after the bug fix?

- **Category**: Behavior
- **Gap**: Four tests mock `parse_backlog` or `find_item` with comment saying it's because `_parse_frontmatter` drops nested metadata. The bug is now fixed. Do the tests need these mocks, or were the mocks purely a bug workaround?
- **Question**: After the `_parse_frontmatter` fix (commit `0e0611f`), would `test_list_items_excludes_skip_items`, `test_list_items_with_status_enriches_from_batch_fetch`, `test_close_item_with_open_pr_raises_backlog_error`, and `test_resolve_item_with_open_pr_raises_backlog_error` pass without their mocks? Or do the mocks serve legitimate test isolation?
- **Options**:
  - A) Mocks are pure workarounds — remove them, update comments, let tests run against real parsing
  - B) Mocks serve dual purpose (bug workaround + isolation) — keep mocks but remove the "pre-existing bug" justification from comments
  - C) Mocks are still necessary because the fix is incomplete for those specific code paths
- **Why It Matters**: Keeping unnecessary mocks hides real behavior from tests; removing necessary mocks breaks tests or loses isolation
- **Resolution**: _pending_

### Q2: Are the Bugs 1-4 in test_skills_array_bugs.py now fixed (tests currently passing)?

- **Category**: Behavior
- **Gap**: The file says tests should FAIL against "current buggy code." If the bugs have been fixed since the file was written, the tests now pass — but the file header is misleading and the "intentional failure" pattern is no longer active.
- **Question**: Run `uv run pytest plugins/plugin-creator/tests/test_skills_array_bugs.py -v` — are any tests currently failing?
- **Options**:
  - A) All tests pass — bugs are fixed; update file header comment; normal tests
  - B) Some tests fail — those bugs are unfixed; apply `pytest.mark.xfail(reason="...", strict=True)` with issue references
  - C) All tests fail — all bugs are unfixed; apply `pytest.mark.xfail` to all or open issues
- **Why It Matters**: Without knowing current state, cannot determine the correct fix approach
- **Resolution**: _pending_

### Q3: What is the agreed team convention for tests written against known-buggy behavior?

- **Category**: Behavior
- **Gap**: The issue says "Correct convention is pytest.mark.xfail or TODO with issue reference" but this is not documented anywhere in the codebase.
- **Question**: Should the convention be:
  - A) `pytest.mark.xfail(reason="Bug #NNN: description", strict=True)` — test runs, expected to fail, turns into error if it unexpectedly passes
  - B) `pytest.mark.xfail(reason="Bug #NNN: description", strict=False)` — test runs, expected to fail, XPASS if it passes (not an error)
  - C) TODO comment with issue reference but no xfail marker (test is skipped or written differently)
- **Why It Matters**: Determines how `test_skills_array_bugs.py` and any future similar tests should be structured
- **Resolution**: _pending_

### Q4: Should the stale module-level comment block in test_backlog_core_parsing.py be updated or removed?

- **Category**: Behavior
- **Gap**: Lines 28-43 describe the bug as still present but line 300 tests the fixed behavior. The comment predates the fix.
- **Question**: Should the module comment be (a) updated to describe current correct behavior, (b) replaced with a shorter note saying "this bug was fixed in commit 0e0611f", or (c) removed entirely since the tests are self-documenting?
- **Options**:
  - A) Update comment to describe current correct behavior
  - B) Replace with brief historical note referencing the fix
  - C) Remove entirely — test names are self-documenting
- **Why It Matters**: Stale comments actively mislead readers about system behavior
- **Resolution**: _pending_

---

## Goals (Pending Resolution)

_These goals will be finalized after questions are resolved._

1. Produce a definitive list of every test in the project that documents a bug as expected behavior (non-benign limitation pattern), verified by inspection against current implementation.
2. For each non-benign instance: update assertions to test correct behavior, or apply `pytest.mark.xfail(strict=True)` with a GitHub issue reference if the bug is known-unfixed.
3. Update stale comments in test files that describe bugs as still present when the implementation has been fixed.
4. Document the team's agreed convention for handling tests against known-buggy behavior in a discoverable location (e.g., a CONTRIBUTING note or pytest markers doc).
5. Verify whether mock removals in `test_backlog_core_operations.py` are safe after the `_parse_frontmatter` fix.

---

## Next Steps

After questions are resolved:

1. Update "Resolution" fields in Questions section
2. Finalize Goals section
3. Proceed to RT-ICA assessment
4. Then proceed to architecture design
