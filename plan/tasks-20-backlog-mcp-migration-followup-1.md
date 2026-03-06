---
tasks:
  - task: "Migrate complete-implementation/SKILL.md and local-workflow.md CLI invocations to MCP"
    status: complete
    parent_task: "plan/tasks-17-backlog-mcp-migration.md"
---

# Task: Migrate complete-implementation and local-workflow CLI Invocations to MCP

## Parent Task

- Original: `plan/tasks-17-backlog-mcp-migration.md`
- Review Date: 2026-03-02

## Status

- [x] Complete

## Priority

High

## Description

The CLI-to-MCP migration (Tasks 1-10) missed two files that contain active `uv run backlog.py` invocations:

1. `.claude/skills/complete-implementation/SKILL.md` — 3 invocations at lines 112, 126, and 138. These drive the recursive follow-up routing step that runs after every feature implementation. Because this skill is loaded by the orchestrator, MCP tools are available and the CLI calls can be replaced per ADR-2.

2. `.claude/rules/local-workflow.md` — 4 references at lines 264, 265, 266, 373, and 374. These describe the same recursive follow-up routing behavior in the data-flow diagram and prose instructions. Lines 265, 266, 373, and 374 use `backlog update --plan` shorthand (not full CLI invocations) but lines 264 explicitly uses `backlog.py list --format json`. All five must use MCP or neutral prose.

Neither file appeared in the migration map Tier classification (Tiers 1-3). `complete-implementation` was created after the map's `CLI_TO_MCP_MIGRATION.md` was originally authored, and `local-workflow.md` was overlooked.

The `complete-implementation/SKILL.md` invocations also pass `--format json` and `-R Jamie-BitFlight/claude_skills`, both of which are dropped parameters that do not exist on MCP tools (task context lines 127-128).

### Specific replacements required

**`.claude/skills/complete-implementation/SKILL.md`**

- Line 112: `uv run .claude/skills/backlog/scripts/backlog.py list --format json -R Jamie-BitFlight/claude_skills`
  → Call the `mcp__backlog__backlog_list` tool. Parse the returned dict's `items` list.

- Line 126: `uv run .claude/skills/backlog/scripts/backlog.py update "{matched_item_title}" --plan "{followup_file_path}" -R Jamie-BitFlight/claude_skills`
  → Call the `mcp__backlog__backlog_update` tool with `selector="{matched_item_title}"` and `plan="{followup_file_path}"`. Check the returned dict for an `error` key.

- Line 138: `uv run .claude/skills/backlog/scripts/backlog.py update "{derived_title}" --plan "{followup_file_path}" -R Jamie-BitFlight/claude_skills`
  → Call the `mcp__backlog__backlog_update` tool with `selector="{derived_title}"` and `plan="{followup_file_path}"`. Check the returned dict for an `error` key.

- Lines 117, 143, 144: These lines reference `backlog.py list` and `backlog.py update` in error-handling prose. Update the error-handling descriptions to reference the MCP tool names (`backlog_list`, `backlog_update`).

**`.claude/rules/local-workflow.md`**

- Line 264: `backlog.py list --format json` → `mcp__backlog__backlog_list` tool
- Lines 265, 266: `backlog update --plan` shorthand → `mcp__backlog__backlog_update` with `plan=` parameter
- Lines 373, 374 (data flow diagram): `backlog update --plan {path}` → `backlog_update(selector=..., plan=...)` or neutral prose

## Acceptance Criteria

- [ ] `grep -c "backlog\.py" .claude/skills/complete-implementation/SKILL.md` returns 0
- [ ] `grep -c "backlog\.py" .claude/rules/local-workflow.md` returns 0
- [ ] No `-R Jamie-BitFlight/claude_skills` flags in either file
- [ ] No `--format json` flags in either file
- [ ] MCP calls use ADR-1 prose format (inline for 1-2 params, parameter table for 3+)
- [ ] Error-handling prose updated to reference MCP tool names
- [ ] `uv run prek run --files .claude/skills/complete-implementation/SKILL.md` passes

## Files to Modify

- `.claude/skills/complete-implementation/SKILL.md:112,117,126,138,143,144` — replace CLI invocations with MCP prose
- `.claude/rules/local-workflow.md:264,265,266,373,374` — replace CLI references with MCP equivalents

## Verification Steps

1. `grep -c "backlog\.py" .claude/skills/complete-implementation/SKILL.md` → must return 0
2. `grep -c "backlog\.py" .claude/rules/local-workflow.md` → must return 0
3. `grep "format.*json\|--format" .claude/skills/complete-implementation/SKILL.md` → must return 0
4. `uv run prek run --files .claude/skills/complete-implementation/SKILL.md` → must pass

## References

- Original review: `plan/tasks-20-backlog-mcp-migration-followup-1.md`
- Migration map: `.claude/skills/backlog/CLI_TO_MCP_MIGRATION.md`
- ADR-1 (prose format): `plan/architect-backlog-mcp-migration.md`
- ADR-2 (MCP-only for orchestrator): `plan/architect-backlog-mcp-migration.md`
- Dropped parameters: task context lines 127-128 in `plan/tasks-17-backlog-mcp-migration.md`
