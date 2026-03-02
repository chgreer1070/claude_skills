---
tasks:
  - task: "Fix stale format=json MCP parameter entries in CLI_TO_MCP_MIGRATION.md mapping table"
    status: complete
    completed: 2026-03-02T08:15:00Z
    resolution: "Already fixed during quality gate Phase 4-6 of parent task. All format=\"json\" entries removed from CLI_TO_MCP_MIGRATION.md in commit 14c401e."
    parent_task: "plan/tasks-17-backlog-mcp-migration.md"
---

# Task: Fix Stale format=json MCP Parameter Entries in CLI_TO_MCP_MIGRATION.md

## Parent Task

- Original: `plan/tasks-17-backlog-mcp-migration.md`
- Review Date: 2026-03-02

## Status

- [ ] Pending

## Priority

Medium

## Description

The `.claude/skills/backlog/CLI_TO_MCP_MIGRATION.md` mapping tables contain stale entries that show `format="json"` as an MCP tool parameter. The `format` parameter does not exist on any MCP tool. Per the task context (line 128): "MCP tools always return structured dicts. No `format` parameter exists."

The actual `backlog_list` and `backlog_view` signatures in `server.py` confirm no `format` parameter:

- `backlog_list(with_status, from_github, label, section, status, title)` — no `format`
- `backlog_view(selector, offset, limit)` — no `format`

The migration map is used as a reference document for future migrations (Tiers 4-7 are still pending). Leaving incorrect MCP call syntax here risks propagating the error into future migration work.

### Affected lines in `.claude/skills/backlog/CLI_TO_MCP_MIGRATION.md`

**Section: "CLI → MCP Tool Mapping" table (lines 19-21)**

- Line 20: `'--format json' → 'format: "json"'` — this column entry is incorrect. Remove the `format` mapping entirely; the note should say `--format json` is dropped (MCP always returns structured dicts).
- Line 21: Same issue for `backlog view`.

**Section: "work-backlog-item SKILL.md mapping table" (lines 134-145)**

- Line 134: `backlog_list(format="json", with_status=true)` → `backlog_list(with_status=true)`
- Line 135: `backlog_view(selector="{$0}", format="json")` → `backlog_view(selector="{$0}")`
- Line 137: `backlog_list(format="json")` → `backlog_list()`
- Line 140: `backlog_view(selector="{$1}", format="json")` → `backlog_view(selector="{$1}")`
- Line 145: `backlog_view(selector="#{N}", format="json")` → `backlog_view(selector="#{N}")`

**Section: "step-procedures.md mapping table" (line 158)**

- Line 158: `backlog_list(format="json", with_status=true)` → `backlog_list(with_status=true)`

**Section: "groom-backlog-item SKILL.md mapping table" (lines 201, 203)**

- Line 201: `backlog_list(format="json")` → `backlog_list()`
- Line 203: `backlog_view(selector="#{N}", format="json")` → `backlog_view(selector="#{N}")`

**Lines 218 and 240 (MCP: inline examples in Tier 2 skill entries)**

- Line 218: `backlog_list(format="json")` → `backlog_list()`
- Line 240: `backlog_list(format="json")` → `backlog_list()`

Note: The universal flags table at the bottom of the document correctly states `--format json → omit — MCP always returns dicts`. The mapping table entries above are inconsistent with that statement.

## Acceptance Criteria

- [ ] All `format="json"` occurrences removed from MCP replacement entries in the mapping tables
- [ ] The universal flags table note about `--format json` being dropped is preserved (it is correct)
- [ ] The top-level mapping table row for `backlog list` and `backlog view` notes that `--format json` is dropped (no MCP parameter), consistent with the universal flags table
- [ ] `uv run prek run --files .claude/skills/backlog/CLI_TO_MCP_MIGRATION.md` passes

## Files to Modify

- `.claude/skills/backlog/CLI_TO_MCP_MIGRATION.md:20,21,134,135,137,140,145,158,201,203,218,240` — remove `format="json"` from MCP call entries

## Verification Steps

1. `grep 'format="json"' .claude/skills/backlog/CLI_TO_MCP_MIGRATION.md` → must return 0
2. `grep 'format: "json"' .claude/skills/backlog/CLI_TO_MCP_MIGRATION.md` → must return 0 (in the mapping column)
3. Confirm the "Universal CLI flags" section still states `--format json` maps to "omit"
4. `uv run prek run --files .claude/skills/backlog/CLI_TO_MCP_MIGRATION.md` → must pass

## References

- Original review: `plan/tasks-21-backlog-mcp-migration-followup-2.md`
- authoritative MCP signatures: `.claude/skills/backlog/backlog_core/server.py` (lines 55-75 for `backlog_list`)
- Task context dropped parameters: `plan/tasks-17-backlog-mcp-migration.md` line 128
