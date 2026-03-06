---
tasks:
  - task: "Fix flawed FM009 stdout assertion in test_frontmatter_fixes.py integration test"
    status: pending
    parent_task: "plan/tasks-1-multi-ecosystem-plugin-creator.md"
---

# Task: Fix Flawed FM009 Stdout Assertion in Integration Test

## Parent Task
- Original: `plan/tasks-1-multi-ecosystem-plugin-creator.md`
- Review Date: 2026-03-06

## Status
- [ ] Pending

## Priority
High

## Description

`plugins/plugin-creator/tests/test_frontmatter_fixes.py` line 251 contains a logic bug
that makes the assertion always pass regardless of actual output:

```python
assert "mcp" not in result.stdout.lower().split("fm009")[1:], (
    "FM009 should not reference any mcp: field.\nstdout:\n" + result.stdout
)
```

`str.split("fm009")` returns a list of substrings. The `in` operator on a list checks
list membership — it tests whether the string `"mcp"` equals any element in the list.
No split segment will ever equal the literal string `"mcp"`, so this assertion is a
no-op: it passes unconditionally, providing no test coverage of its intent.

The intended check is: after the first occurrence of "fm009" in stdout, the string "mcp"
should not appear as a substring. The correct form uses substring search:

```python
post_fm009 = result.stdout.lower().partition("fm009")[2]
assert "mcp" not in post_fm009, (
    "FM009 should not reference any mcp: field.\nstdout:\n" + result.stdout
)
```

## Acceptance Criteria
- [ ] Line 251 in `plugins/plugin-creator/tests/test_frontmatter_fixes.py` uses substring
      search (not list membership) to verify "mcp" does not appear after "fm009" in stdout
- [ ] The corrected assertion fails when the validator incorrectly emits FM009 for an mcp: field
- [ ] All 26 existing tests continue to pass after the fix

## Files to Modify
- `plugins/plugin-creator/tests/test_frontmatter_fixes.py:251` — replace `split("fm009")[1:]`
  with `partition("fm009")[2]` and use substring `in` check

## Verification Steps
1. `uv run pytest plugins/plugin-creator/tests/test_frontmatter_fixes.py -v` — all tests pass
2. Temporarily introduce a deliberate FM009 mcp: emission in the validator, confirm the
   corrected assertion fails as expected, then revert

## References
- Bug location: `plugins/plugin-creator/tests/test_frontmatter_fixes.py:251`
- Test class: `TestFM009IntegrationFixture.test_fix_on_multi_runtime_skill_preserves_mcp_block`
