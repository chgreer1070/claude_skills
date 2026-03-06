---
tasks:
  - task: "Fix FM009 state-machine: mcp scalar (null/value) must not suppress subsequent Claude Code lines"
    status: pending
    parent_task: "plan/tasks-1-multi-ecosystem-plugin-creator.md"
---

# Task: Fix FM009 State-Machine Scalar Handling for mcp: null and mcp: inline-value

## Parent Task
- Original: `plan/tasks-1-multi-ecosystem-plugin-creator.md`
- Review Date: 2026-03-06

## Status
- [ ] Pending

## Priority
High

## Description

The FM009 state machine in `plugins/plugin-creator/scripts/plugin_validator.py` sets
`current_top_level_key = "mcp"` whenever it encounters a non-indented line matching
`mcp\s*:`. This is correct for block mappings (`mcp:\n  server:\n    ...`) but
incorrect for scalar forms (`mcp: null`, `mcp: false`, `mcp: "some value"`).

For scalar forms, the `mcp:` line has no indented children. Any subsequent
non-indented line would reset `current_top_level_key` correctly — but any subsequent
**indented** line (belonging to a different block-style top-level key that was written
without a blank line between them) would be incorrectly treated as inside the `mcp:`
block and skipped by the ecosystem guard.

Concrete failure scenario (no test currently exists for this):

```yaml
mcp: null
some-other-key:
  description: Fix: something that needs quoting
```

If `some-other-key:` introduces an indented block, the FM009 guard skips
`description: Fix: something that needs quoting` because `current_top_level_key`
is still `"mcp"` from the scalar line.

The fix requires distinguishing scalar vs. block top-level lines. A top-level line
with a non-empty value after the colon (other than whitespace) is a scalar — it
cannot have indented children. The state machine should reset `current_top_level_key`
to the scalar key's name after processing that line, not carry `mcp` forward.

The simplest correct fix: when setting `current_top_level_key`, also check whether
the line has a non-null scalar value (i.e., `key: value` where value is non-empty).
If it does, the key owns no indented children, so `current_top_level_key` should be
treated as exhausted after that line. One approach is to only enter the ecosystem
bypass when the matched top-level key has no inline value (pure block introducer).

## Acceptance Criteria
- [ ] A new unit test in `test_frontmatter_fixes.py` exercises the pattern:
      `mcp: null\ndescription: Fix: colon here\n` and asserts FM009 fires for
      the `description` field (not suppressed by the preceding `mcp: null`)
- [ ] The state machine in `plugin_validator.py:_fix_unquoted_colons` correctly
      identifies scalar top-level lines (`mcp: null`) as non-block and does not
      suppress FM009 for subsequent Claude Code fields
- [ ] Existing 26 tests continue to pass — no regression on block `mcp:` cases
- [ ] The existing `mcp_null_scalar` parametrize case (case5) still passes

## Files to Modify
- `plugins/plugin-creator/scripts/plugin_validator.py` — `_fix_unquoted_colons()`
  function, state-machine block near line 182–190
- `plugins/plugin-creator/tests/test_frontmatter_fixes.py` — add parametrize case
  for `mcp: null` followed by a Claude Code field with a colon

## Verification Steps
1. Write the failing test first; confirm it fails before the fix
2. Apply the state-machine fix
3. `uv run pytest plugins/plugin-creator/tests/ -v` — all tests pass including new case
4. `uv run plugins/plugin-creator/scripts/plugin_validator.py --fix` on a synthetic
   file containing `mcp: null\ndescription: Fix: test\n` and confirm description is quoted

## References
- State machine location: `plugins/plugin-creator/scripts/plugin_validator.py` — function
  `_fix_unquoted_colons`, approximately lines 164–210
- Related test: `test_frontmatter_fixes.py` — `TestFM009Guard` parametrize case
  `case5_mcp_null_scalar_no_crash_no_rewrite`
