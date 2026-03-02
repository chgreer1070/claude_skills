# Task Plan: Backlog CLI-to-MCP Migration

**Feature**: migrate backlog to mcp server system
**Issue**: #329
**Architecture Spec**: [architect-backlog-mcp-migration.md](./architect-backlog-mcp-migration.md)
**Feature Context**: [feature-context-backlog-mcp-migration.md](./feature-context-backlog-mcp-migration.md)
**Codebase Analysis**: [codebase/backlog-mcp-migration-patterns.md](./codebase/backlog-mcp-migration-patterns.md)
**Migration Map**: [CLI_TO_MCP_MIGRATION.md](../.claude/skills/backlog/CLI_TO_MCP_MIGRATION.md)

---

## Task Summary Statistics

- Total tasks: 10
- Waves: 4 (Policy → Core Skills → Agents → Cleanup)
- Files affected: 13
- CLI invocations to migrate: ~34

---

## Task 1: Update CLAUDE.md Backlog Operations policy

**Status**: NOT STARTED
**Dependencies**: None
**Priority**: 1
**Complexity**: Low
**Agent**: contextual-ai-documentation-optimizer
**Skills**: ["backlog"]

### Description

Replace the `<backlog_operations>` section in `.claude/CLAUDE.md` (lines 210-224) with MCP-primary policy. The architecture spec ADR-2 mandates MCP-only for orchestrator skills, CLI retained for CI only. Use the migration template from the architecture spec section 1.1.

### Files

- `.claude/CLAUDE.md` — edit Backlog Operations section

### Acceptance Criteria

- [ ] `<backlog_operations>` section declares MCP tools as primary interface
- [ ] All 10 MCP tool names listed (`backlog_add` through `backlog_pull`)
- [ ] CLI fallback documented for CI/GitHub Actions only
- [ ] Capability gap fallback to `/backlog-tools-administrator` retained
- [ ] "GitHub Issues are the source of truth" policy unchanged

### Verification Steps

- [ ] `grep -c "backlog\.py" .claude/CLAUDE.md` returns count only in the CI fallback block
- [ ] `grep "mcp__backlog__" .claude/CLAUDE.md` shows at least one reference
- [ ] `uv run prek run --files .claude/CLAUDE.md` passes

---

## Task 2: Update cursor rules and migration map corrections

**Status**: NOT STARTED
**Dependencies**: None
**Priority**: 2
**Complexity**: Low
**Agent**: contextual-ai-documentation-optimizer
**Skills**: ["backlog"]

### Description

Two independent small fixes:
1. `.cursor/rules/backlog-before-work.mdc` line 12: replace `backlog update "{title}" --plan "{path}"` with `mcp__backlog__backlog_update(selector="{title}", plan="{path}")`.
2. `.claude/skills/backlog/CLI_TO_MCP_MIGRATION.md`: fix stale claims per ADR-4 and ADR-6:
   - Line 12: change "55 tests" to "382 tests", "NOT yet registered" to "registered"
   - Remove or mark `session-start-backlog.cjs` entry as "FILE DOES NOT EXIST"

### Files

- `.cursor/rules/backlog-before-work.mdc`
- `.claude/skills/backlog/CLI_TO_MCP_MIGRATION.md`

### Acceptance Criteria

- [ ] Cursor rule uses MCP tool reference instead of CLI
- [ ] Migration map test count reads "382 tests"
- [ ] Migration map registration status reads "registered in `.mcp.json`"
- [ ] `session-start-backlog.cjs` entry removed or marked nonexistent

### Verification Steps

- [ ] `grep "backlog\.py" .cursor/rules/backlog-before-work.mdc` returns 0 matches
- [ ] `grep "55 tests" .claude/skills/backlog/CLI_TO_MCP_MIGRATION.md` returns 0 matches
- [ ] `grep "NOT yet registered" .claude/skills/backlog/CLI_TO_MCP_MIGRATION.md` returns 0 matches

---

## Task 3: Migrate work-backlog-item SKILL.md (19 invocations)

**Status**: NOT STARTED
**Dependencies**: Task 1
**Priority**: 1
**Complexity**: High
**Agent**: contextual-ai-documentation-optimizer
**Skills**: ["backlog"]

### Description

Highest-density file. Replace all 19 CLI invocations in `.claude/skills/work-backlog-item/SKILL.md` with MCP tool calls using the ADR-1 format (prose instruction blocks with backtick tool names). Apply ADR-8 semantic correction: lines 195 and 301 use `close --reason` which must become `backlog_resolve`, not `backlog_close`.

Reference the line-by-line replacement table in architecture spec section 2.1. Each bash code fence becomes a prose MCP tool instruction. Change "Parse the JSON output" to "Parse the returned dict" throughout.

### Files

- `.claude/skills/work-backlog-item/SKILL.md`

### Acceptance Criteria

- [ ] All 19 `uv run backlog.py` invocations replaced with MCP tool calls
- [ ] Lines 195, 301: `close --reason` replaced with `mcp__backlog__backlog_resolve` (ADR-8)
- [ ] No `-R Jamie-BitFlight/claude_skills` flags remain
- [ ] No `--format json` flags remain (MCP always returns dicts)
- [ ] ADR-1 format used: prose blocks for complex calls, inline for simple calls

### Verification Steps

- [ ] `grep -c "backlog\.py" .claude/skills/work-backlog-item/SKILL.md` returns 0
- [ ] `grep -c "uv run" .claude/skills/work-backlog-item/SKILL.md` returns 0 (for backlog calls)
- [ ] `grep "backlog_close.*reason" .claude/skills/work-backlog-item/SKILL.md` returns 0 (ADR-8 check)
- [ ] `uv run prek run --files .claude/skills/work-backlog-item/SKILL.md` passes

---

## Task 4: Migrate work-backlog-item reference files (8 invocations)

**Status**: NOT STARTED
**Dependencies**: Task 3
**Priority**: 2
**Complexity**: Medium
**Agent**: contextual-ai-documentation-optimizer
**Skills**: ["backlog"]

### Description

Migrate three reference files that mirror patterns from the main SKILL.md. These must be consistent with Task 3.

Files and invocation counts:
- `step-procedures.md` — 2 invocations (lines 12, 117)
- `github-integration.md` — 3 invocations (lines 36, 46, 61)
- `close-resolve-procedure.md` — 3 invocations (lines 36, 129, 135)

Non-backlog `gh` commands in these files remain unchanged.

### Files

- `.claude/skills/work-backlog-item/references/step-procedures.md`
- `.claude/skills/work-backlog-item/references/github-integration.md`
- `.claude/skills/work-backlog-item/references/close-resolve-procedure.md`

### Acceptance Criteria

- [ ] All 8 CLI invocations replaced with MCP tool calls
- [ ] `close-resolve-procedure.md` line 36: `resolve --reason` maps to `backlog_resolve`
- [ ] `github-integration.md`: non-backlog `gh` commands untouched
- [ ] Consistent format with Task 3 (same ADR-1 patterns)

### Verification Steps

- [ ] `grep -c "backlog\.py" .claude/skills/work-backlog-item/references/*.md` returns 0 for each file
- [ ] `grep "backlog_close.*reason" .claude/skills/work-backlog-item/references/*.md` returns 0
- [ ] `uv run prek run --files .claude/skills/work-backlog-item/references/step-procedures.md .claude/skills/work-backlog-item/references/github-integration.md .claude/skills/work-backlog-item/references/close-resolve-procedure.md` passes

---

## Task 5: Migrate groom-backlog-item SKILL.md (6 invocations + --help removal)

**Status**: NOT STARTED
**Dependencies**: Task 1
**Priority**: 2
**Complexity**: Medium
**Agent**: contextual-ai-documentation-optimizer
**Skills**: ["backlog"]

### Description

Replace 6 CLI invocations and apply two special changes:
1. ADR-8: Lines 65, 94 — `close --reason` becomes `backlog_resolve`
2. ADR-5: Lines 276-286 — remove `--help` verification guard, replace with MCP schema-enforced note and update/groom/sync disambiguation
3. Lines 288-313 (Step 9 patterns): rewrite incremental and full-body groom patterns to use MCP
4. Shorthand annotation blocks (lines 181-184, 202-211, 222-239, 294-303): use ADR-1 shorthand format

### Files

- `.claude/skills/groom-backlog-item/SKILL.md`

### Acceptance Criteria

- [ ] All 6 CLI invocations replaced with MCP tool calls
- [ ] `--help` verification guard removed and replaced with ADR-5 text
- [ ] Lines 65, 94: `close --reason` replaced with `backlog_resolve` (ADR-8)
- [ ] Step 9 groom patterns use MCP (both incremental and full-body)
- [ ] `--groomed-file` and stdin pipe patterns removed (CLI-only per ADR-2)

### Verification Steps

- [ ] `grep -c "backlog\.py" .claude/skills/groom-backlog-item/SKILL.md` returns 0
- [ ] `grep "\-\-help" .claude/skills/groom-backlog-item/SKILL.md` returns 0
- [ ] `grep "backlog_close.*reason" .claude/skills/groom-backlog-item/SKILL.md` returns 0
- [ ] `uv run prek run --files .claude/skills/groom-backlog-item/SKILL.md` passes

---

## Task 6: Migrate create-backlog-item and group-items-to-milestone (2 invocations)

**Status**: NOT STARTED
**Dependencies**: Task 1
**Priority**: 2
**Complexity**: Low
**Agent**: contextual-ai-documentation-optimizer
**Skills**: ["backlog"]

### Description

Two simple migrations:
1. `create-backlog-item/SKILL.md` line 163-169: replace `backlog.py add` with `mcp__backlog__backlog_add` using parameter table format (ADR-1 complex call). Translate conditional `--create-issue` logic to `create_issue` parameter. Note that `research_first` has no MCP parameter — must be embedded in `description`.
2. `group-items-to-milestone/SKILL.md` line 37: replace `backlog.py list --format json` with `mcp__backlog__backlog_list()`.

### Files

- `.claude/skills/create-backlog-item/SKILL.md`
- `.claude/skills/group-items-to-milestone/SKILL.md`

### Acceptance Criteria

- [ ] `create-backlog-item` uses `mcp__backlog__backlog_add` with parameter table
- [ ] `create_issue` parameter documented with conditional logic (P0/P1 vs P2/Ideas)
- [ ] `group-items-to-milestone` uses `mcp__backlog__backlog_list()`
- [ ] `research_first` gap documented (no MCP parameter; embed in description)

### Verification Steps

- [ ] `grep -c "backlog\.py" .claude/skills/create-backlog-item/SKILL.md` returns 0
- [ ] `grep -c "backlog\.py" .claude/skills/group-items-to-milestone/SKILL.md` returns 0
- [ ] `uv run prek run --files .claude/skills/create-backlog-item/SKILL.md .claude/skills/group-items-to-milestone/SKILL.md` passes

---

## Task 7: Rewrite backlog/SKILL.md documentation

**Status**: NOT STARTED
**Dependencies**: Task 1, Task 3
**Priority**: 2
**Complexity**: High
**Agent**: contextual-ai-documentation-optimizer
**Skills**: ["backlog"]

### Description

Full documentation rewrite of `.claude/skills/backlog/SKILL.md`. Currently documents CLI invocation syntax. Must be rewritten to document MCP tools as primary interface per ADR-2. Follow the structure from architecture spec section 2.5:
- Primary Interface (MCP): table of 10 tools with parameter signatures
- CI/CLI Interface: retained bash syntax for CI environments
- Environment: GITHUB_TOKEN requirement unchanged
- Integration: updated to reference MCP tools

Read `.claude/skills/backlog/backlog_core/server.py` for exact tool signatures and parameter types.

### Files

- `.claude/skills/backlog/SKILL.md`

### Acceptance Criteria

- [ ] MCP tools documented as primary interface with all 10 tools
- [ ] Each tool has parameter names, types, and descriptions from server.py
- [ ] CLI documented as secondary/CI-only interface
- [ ] Return value shapes documented (dict with `error` key on failure)
- [ ] `GITHUB_TOKEN` requirement documented

### Verification Steps

- [ ] All 10 tool names appear: `backlog_add`, `backlog_list`, `backlog_view`, `backlog_sync`, `backlog_close`, `backlog_resolve`, `backlog_update`, `backlog_groom`, `backlog_normalize`, `backlog_pull`
- [ ] `uv run prek run --files .claude/skills/backlog/SKILL.md` passes
- [ ] No orphaned CLI-only content (check for `uv run` outside the CI section)

---

## Task 8: Update agent files

**Status**: NOT STARTED
**Dependencies**: Task 3, Task 5
**Priority**: 3
**Complexity**: Low
**Agent**: contextual-ai-documentation-optimizer
**Skills**: ["backlog"]

### Description

Two agent files need minor updates:
1. `.claude/agents/backlog-item-groomer.md`: verify no residual CLI references remain. If line 79 still has a CLI call, replace with MCP equivalent. Already has `mcpServers:` block.
2. `.claude/agents/backlog-mcp-validator.md`: update `backlog_list` parameter reference to include all parameters (`with_status`, `from_github`, `label`, `section`, `status`, `title`).

### Files

- `.claude/agents/backlog-item-groomer.md`
- `.claude/agents/backlog-mcp-validator.md`

### Acceptance Criteria

- [ ] `backlog-item-groomer.md` has zero `backlog.py` references
- [ ] `backlog-mcp-validator.md` documents all `backlog_list` parameters
- [ ] Both agents maintain valid frontmatter

### Verification Steps

- [ ] `grep -c "backlog\.py" .claude/agents/backlog-item-groomer.md` returns 0
- [ ] `grep "section\|status\|title" .claude/agents/backlog-mcp-validator.md` shows filter params documented
- [ ] `uv run prek run --files .claude/agents/backlog-item-groomer.md .claude/agents/backlog-mcp-validator.md` passes

---

## Task 9: Update backlog-tools-administrator SKILL.md

**Status**: NOT STARTED
**Dependencies**: Task 1, Task 7
**Priority**: 3
**Complexity**: Medium
**Agent**: contextual-ai-documentation-optimizer
**Skills**: ["backlog"]

### Description

Update `.claude/skills/backlog-tools-administrator/SKILL.md` to describe extending both CLI and MCP server per architecture spec section 4.1:
- Line 9: update "bypassing the backlog script" to "bypassing the backlog tools (MCP or CLI)"
- Step 3A: add MCP server extension alongside CLI extension (primary: `operations.py`, secondary: `server.py` + `backlog.py`)
- Step 4 verification: add MCP tool verification step
- Classification flowchart: update `backlog.py` references to "backlog tooling"

CLI verification commands (linting/testing) stay as bash — these are shell operations per ADR-2.

### Files

- `.claude/skills/backlog-tools-administrator/SKILL.md`

### Acceptance Criteria

- [ ] Extension workflow describes both MCP and CLI paths
- [ ] Primary extension point identified as `operations.py`
- [ ] MCP tool verification step added
- [ ] CLI verification commands (linting, pytest) retained as bash
- [ ] Classification flowchart updated

### Verification Steps

- [ ] `grep "operations.py" .claude/skills/backlog-tools-administrator/SKILL.md` finds reference to primary extension point
- [ ] `grep "server.py" .claude/skills/backlog-tools-administrator/SKILL.md` finds MCP server reference
- [ ] `uv run prek run --files .claude/skills/backlog-tools-administrator/SKILL.md` passes

---

## Task 10: Final verification and cleanup

**Status**: NOT STARTED
**Dependencies**: Task 1, Task 2, Task 3, Task 4, Task 5, Task 6, Task 7, Task 8, Task 9
**Priority**: 1
**Complexity**: Medium
**Agent**: general-purpose
**Skills**: ["backlog"]

### Description

Cross-file verification and cleanup after all migrations complete:

1. **Repo-wide CLI reference audit**: `grep -rn "uv run.*backlog/scripts/backlog.py" .claude/skills/ .claude/agents/ .claude/hooks/ .claude/CLAUDE.md .cursor/` — expect zero matches in migrated files (matches in `.github/workflows/` are expected).
2. **MCP tool coverage**: verify all 10 tools are referenced somewhere in the migrated skill ecosystem.
3. **ADR-8 semantic check**: `grep -rn "backlog_close.*reason" .claude/skills/ .claude/agents/` — expect zero matches.
4. **Test suite**: `uv run pytest .claude/skills/backlog/tests/` — 382 tests still pass (safety check, no Python changes made).
5. **Close idea item #331**: resolve the "Convert backlog.py into MCP server" backlog item with reference to this migration.
6. **Update migration map**: mark all Tier 1-3 items as DONE, add completion header.
7. Commit with `Fixes #329` in the message.

### Files

- All migrated files (read-only verification)
- `.claude/skills/backlog/CLI_TO_MCP_MIGRATION.md` (mark items DONE)
- `.claude/backlog/idea-convert-backlogpy-into-an-mcp-server-using-fastmcp-skill.md` (close)

### Acceptance Criteria

- [ ] Zero residual `backlog.py` CLI references in migrated Tier 1-3 files
- [ ] All 10 MCP tool names referenced in skill ecosystem
- [ ] Zero `backlog_close` calls with `reason` parameter (ADR-8)
- [ ] 382 tests pass
- [ ] Idea item #331 closed/resolved
- [ ] Migration map marked complete

### Verification Steps

- [ ] `grep -rn "uv run.*backlog/scripts/backlog.py" .claude/skills/ .claude/agents/ .claude/CLAUDE.md .cursor/` returns 0 matches
- [ ] `uv run pytest .claude/skills/backlog/tests/ -q` shows 382 passed
- [ ] `grep -rn "backlog_close.*reason" .claude/skills/ .claude/agents/` returns 0 matches
- [ ] Git commit includes `Fixes #329`
