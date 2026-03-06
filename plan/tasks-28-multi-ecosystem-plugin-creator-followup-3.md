---
tasks:
  - task: "Fix and test FM009 state-machine: mcp scalar followed by orphaned indented line still suppresses FM009"
    status: pending
    parent_task: "plan/tasks-26-multi-ecosystem-plugin-creator-followup-2.md"
---

# Task: FM009 State-Machine Orphaned-Indent Gap — Production Bug Unfixed

## Parent Task
- Original: `plan/tasks-26-multi-ecosystem-plugin-creator-followup-2.md`
- Review Date: 2026-03-06

## Status
- [ ] Pending

## Priority
High

## Description

The implementation for tasks-26 added case8 to `test_frontmatter_fixes.py` and concluded the
state machine was already correct. The conclusion is wrong for one untested input shape.

### The Untested Failure Path

Case8 uses:

```text
mcp: null
some-other-key:
  description: Fix: colon here
```

The intervening non-indented line `some-other-key:` resets `current_top_level_key` before the
indented `description:` line is processed. FM009 fires correctly. The test passes.

The task description in tasks-26 (lines 29-32) documents a different and stricter failure: an
**indented line directly after `mcp: null` with no intervening top-level key**:

```text
mcp: null
  orphaned-indent: Fix: colon
```

Tracing the state machine in `plugin_validator.py:_fix_unquoted_colons` (lines 176-204):

1. `mcp: null` — matches `_TOP_LEVEL_KEY_RE`, sets `current_top_level_key = "mcp"`, skipped as
   ecosystem-owned.
2. `  orphaned-indent: Fix: colon` — indented, does NOT match the non-indented guard, so
   `current_top_level_key` remains `"mcp"`. Still ecosystem-owned. FM009 is suppressed.
   The unquoted colon is NOT fixed. **This is the bug.**

### Why This Matters

This input shape is the mechanistic failure the task was designed to fix. The scalar `mcp: null`
cannot have indented children in valid YAML — any subsequent indented line belongs to the
enclosing scope or is malformed. The state machine should not continue to treat such lines as
inside the `mcp:` block.

The production code at `plugin_validator.py:182-190` was not changed, and no test covers
the orphaned-indent shape. The bug reported in tasks-26's description remains in production.

## Acceptance Criteria
- [ ] A new failing test is added FIRST, confirming the orphaned-indent path fails before any
      production code change:
      `"mcp: null\n  orphaned-indent: Fix: colon\n"` must assert `check_fm009_fires=True`
- [ ] The state machine in `plugin_validator.py:_fix_unquoted_colons` is updated so that a
      scalar top-level line (`key: <non-empty-value>`) does not suppress FM009 for subsequent
      indented lines (the key owns no block children)
- [ ] The new test passes after the production fix
- [ ] All 12 existing tests continue to pass — no regression on block `mcp:` cases or case8
- [ ] A synthetic end-to-end check confirms: running `plugin_validator.py --fix` on a file
      containing `mcp: null\n  orphaned-indent: Fix: colon\n` quotes the colon value

## Files to Modify
- `plugins/plugin-creator/tests/test_frontmatter_fixes.py` — add case9 parametrize entry for
  the orphaned-indent shape (write this failing test first)
- `plugins/plugin-creator/scripts/plugin_validator.py` — `_fix_unquoted_colons()` state machine,
  lines 182-190: detect scalar top-level lines (non-empty value after the colon) and mark the
  key as exhausted so subsequent indented lines are not treated as its children

## Verification Steps
1. Add the case9 test without any production code change; confirm `pytest` fails on case9
2. Update the state machine in `plugin_validator.py`
3. `uv run pytest plugins/plugin-creator/tests/ -v` — all 13 tests pass
4. Synthetic check:
   ```bash
   printf -- '---\nmcp: null\n  orphaned-indent: Fix: colon\n---\n# body\n' > /tmp/test_skill.md
   uv run plugins/plugin-creator/scripts/plugin_validator.py --fix /tmp/test_skill.md
   grep 'orphaned-indent' /tmp/test_skill.md
   # Expected: orphaned-indent: "Fix: colon"
   ```

## References
- Failing path documented: `plan/tasks-26-multi-ecosystem-plugin-creator-followup-2.md` lines 29-32
- State machine location: `plugins/plugin-creator/scripts/plugin_validator.py` lines 176-208
  (function `_fix_unquoted_colons`)
- Existing test file: `plugins/plugin-creator/tests/test_frontmatter_fixes.py`
- Case8 (passing, but insufficient): `case8_mcp_scalar_null_fm009_fires_for_subsequent_fields`
