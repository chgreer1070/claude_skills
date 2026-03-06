---
tasks:
  - task: "Fix stale '7 input shapes' count in test_fm009_guard docstring"
    status: pending
    parent_task: "plan/tasks-28-multi-ecosystem-plugin-creator-followup-3.md"
---

# Task: Fix Stale Input-Shape Count in test_fm009_guard Docstring

## Parent Task
- Original: `plan/tasks-28-multi-ecosystem-plugin-creator-followup-3.md`
- Review Date: 2026-03-06

## Status
- [ ] Pending

## Priority
Low

## Description

The `TestFM009Guard.test_fm009_guard` method docstring at line 128 of
`plugins/plugin-creator/tests/test_frontmatter_fixes.py` reads:

```text
Tests: _fix_unquoted_colons() state machine for 7 input shapes
```

There are now nine parametrized cases (case1–case9). The class docstring at line 31
was updated to "nine distinct input shapes" when case9 was added, but the method-level
docstring was not updated. The count "7 input shapes" was correct before case8 was
added in tasks-26; it was not incremented for case8 or case9.

## Acceptance Criteria
- [ ] Line 128–129 of `plugins/plugin-creator/tests/test_frontmatter_fixes.py` updated
      so the method docstring references "9 input shapes" (or is reworded to avoid
      a literal count that will drift again)
- [ ] Class docstring at line 31 and method docstring are consistent with each other
- [ ] `uv run pytest plugins/plugin-creator/tests/ -v` passes with no regressions

## Files to Modify
- `plugins/plugin-creator/tests/test_frontmatter_fixes.py:128-129` — update "7 input shapes"
  to "9 input shapes", or rephrase to avoid a count (e.g., "nine parametrized input shapes,
  enumerated in the parametrize decorator above")

## Verification Steps
1. `grep -n "input shapes" plugins/plugin-creator/tests/test_frontmatter_fixes.py` — confirm
   both occurrences reference the same count
2. `uv run pytest plugins/plugin-creator/tests/ -v` — all 13 tests pass

## References
- Method docstring location: `plugins/plugin-creator/tests/test_frontmatter_fixes.py:128`
- Class docstring (already correct): `plugins/plugin-creator/tests/test_frontmatter_fixes.py:31`
- Parent review: `plan/tasks-28-multi-ecosystem-plugin-creator-followup-3.md`
