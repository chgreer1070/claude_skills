# Feature Context: Backlog CLI-to-MCP Migration

## Document Metadata

- **Generated**: 2026-03-02
- **Input Type**: simple_description
- **Source**: Feature request describing migration of CLI shell-out patterns to MCP tool calls in skills, agents, and policy docs
- **Status**: DISCOVERY_COMPLETE

---

## Original Request

The backlog-mcp FastMCP server is implemented (10 tools, 382 tests passing) and registered in `.mcp.json`. A CLI-to-MCP migration map exists at `.claude/skills/backlog/CLI_TO_MCP_MIGRATION.md` identifying ~40 files and ~34 direct CLI invocations that need updating. The migration replaces `uv run .claude/skills/backlog/scripts/backlog.py <subcommand> <args>` CLI shell-out patterns in skill SKILL.md files, agent files, policy docs, and hooks with MCP tool call descriptions. The orchestrator accesses MCP tools via `mcp__backlog__<tool_name>` pattern. Tracked as Issue #329.

---

## Core Intent Analysis

### WHO (Target Users)

- **Primary**: The orchestrator agent (main Claude Code context) that reads skill and agent instructions and executes backlog operations
- **Secondary**: Skill and agent authors who maintain instruction files referencing backlog operations
- **Excluded**: GitHub Actions CI workflows (no MCP client available in CI)

### WHAT (Desired Outcome)

All skill SKILL.md files, agent `.md` files, policy documents, and hook scripts that currently instruct the orchestrator to shell out to `backlog.py` via `uv run` should instead describe backlog operations as MCP tool calls (e.g., `mcp__backlog__backlog_list(format="json")`). After migration, the orchestrator invokes backlog operations through the MCP protocol rather than subprocess execution. The CLI (`backlog.py`) continues to exist for CI/GitHub Actions and as a fallback.

### WHEN (Trigger Conditions)

- Any skill or agent referencing a `uv run .claude/skills/backlog/scripts/backlog.py` command is read by the orchestrator during session execution
- The `/work-backlog-item`, `/create-backlog-item`, `/groom-backlog-item`, or `/group-items-to-milestone` skills are invoked
- The `@backlog-item-groomer` agent is delegated to
- Session hooks fire (stop-backlog-reminder)
- Policy documents (CLAUDE.md) are read during session initialization

### WHY (Problem Being Solved)

1. **Protocol mismatch**: The orchestrator has native MCP tool access (`mcp__backlog__*` permissions are already granted in `.claude/settings.json:13`) but skills still instruct it to shell out via `Bash(uv run backlog.py ...)`. This forces a subprocess spawn, stdout capture, and text parsing for every backlog operation when a direct function call is available.
2. **Error surface**: CLI shell-outs can fail silently (exit code 0 with error output), produce unparseable output, or encounter PATH/environment issues. MCP tool calls return structured dict responses with explicit error keys.
3. **Maintenance burden**: Two interface descriptions (CLI syntax and MCP tool signatures) for the same 10 operations creates drift risk. The migration map already documents a stale test count discrepancy (migration map says 55 tests; actual is 382).
4. **Consistency**: The `@backlog-item-groomer` agent has already been partially migrated (uses `backlog_list` MCP tool at `.claude/agents/backlog-item-groomer.md:88`), creating an inconsistent state where some files use MCP and others use CLI.

---

## Codebase Research

### Similar Patterns Found

#### Pattern 1: Existing MCP tool usage in backlog-item-groomer

- **Location**: `.claude/agents/backlog-item-groomer.md:88`
- **Relevance**: This agent already calls `backlog_list` via MCP (`mcp__backlog__backlog_list`), demonstrating the target pattern for all other files
- **Reusable**: The calling convention used here (`Call the backlog_list MCP tool (via mcp__backlog__backlog_list)`) is the established pattern for migrated files

#### Pattern 2: MCP server registration in .mcp.json

- **Location**: `.mcp.json:25-28`
- **Relevance**: The backlog MCP server is already registered with `"command": "uv"` and `"args": ["run", "python", "-m", "backlog_core.server"]`. This prerequisite is complete.
- **Reusable**: Registration pattern matches other MCP servers in the file (Ref-local, context7-local, kernel-local)

#### Pattern 3: MCP permission grant in settings.json

- **Location**: `.claude/settings.json:13`
- **Relevance**: `"mcp__backlog__*"` is already in the allow list, meaning the orchestrator has permission to call all backlog MCP tools. No permission changes needed.
- **Reusable**: N/A (already done)

#### Pattern 4: CLI invocation pattern (current state being replaced)

- **Location**: `.claude/skills/work-backlog-item/SKILL.md:97` (and 18 more locations in same file)
- **Relevance**: Shows the current pattern: bash code fence with `uv run .claude/skills/backlog/scripts/backlog.py list --format json --with-status -R Jamie-BitFlight/claude_skills`. This is the pattern that every migration target needs to replace.
- **Reusable**: The migration map at `.claude/skills/backlog/CLI_TO_MCP_MIGRATION.md` already has line-by-line mappings for all 34 Tier 1-3 invocations.

#### Pattern 5: MCP tool signatures in server.py

- **Location**: `.claude/skills/backlog/backlog_core/server.py:16-347`
- **Relevance**: All 10 tools are defined with full Pydantic `Annotated[..., Field(...)]` parameter signatures. Each tool returns a dict with result data plus `Output.to_dict()` (messages/warnings). Error cases return `{"error": str(e)}`.
- **Reusable**: Tool signatures define the exact parameter names and types that skill/agent files need to reference.

### Existing Infrastructure

The following infrastructure is already in place and does NOT need modification:

| Component | Location | Status |
|-----------|----------|--------|
| MCP server (10 tools) | `.claude/skills/backlog/backlog_core/server.py` | Complete, 382 tests passing |
| Operations layer (shared backend) | `.claude/skills/backlog/backlog_core/operations.py` | Unchanged by migration |
| .mcp.json registration | `.mcp.json:25-28` | Complete |
| MCP permissions | `.claude/settings.json:13` | Complete (`mcp__backlog__*`) |
| CLI script (CI fallback) | `.claude/skills/backlog/scripts/backlog.py` | Retained for CI |
| Migration map | `.claude/skills/backlog/CLI_TO_MCP_MIGRATION.md` | Complete with line-level mappings |
| Test suite | `.claude/skills/backlog/tests/` | 382 tests passing |
| Backlog item | `.claude/backlog/p1-migrate-backlog-to-mcp-server-system.md` | Issue #329, groomed |

### Code References

- `.claude/skills/backlog/CLI_TO_MCP_MIGRATION.md:1-354` - Complete migration map with tier-by-tier inventory
- `.claude/skills/backlog/backlog_core/server.py:16-347` - All 10 MCP tool definitions
- `.claude/CLAUDE.md:210-224` - Backlog Operations policy section (migration target)
- `.claude/hooks/stop-backlog-reminder.cjs:1-13` - Session stop hook (migration target)
- `.claude/skills/work-backlog-item/SKILL.md:97` - Highest-density CLI invocation file (19 invocations)
- `.claude/skills/work-backlog-item/references/step-procedures.md:12` - CLI invocation in reference
- `.claude/skills/work-backlog-item/references/github-integration.md:36` - CLI invocation in reference
- `.claude/skills/work-backlog-item/references/close-resolve-procedure.md:36` - CLI invocation in reference
- `.claude/skills/create-backlog-item/SKILL.md:163` - CLI invocation for `backlog add`
- `.claude/skills/groom-backlog-item/SKILL.md:25` - CLI invocation (6 total in file)
- `.claude/skills/group-items-to-milestone/SKILL.md:37` - CLI invocation for `backlog list`
- `.claude/skills/backlog/SKILL.md:12` - CLI documentation (needs rewrite)
- `.claude/skills/backlog-tools-administrator/SKILL.md:9` - References backlog.py as extension target
- `.claude/agents/backlog-item-groomer.md:88` - Already migrated to MCP (partial)
- `.claude/settings.json:13` - MCP permission already granted
- `.mcp.json:25-28` - MCP server already registered

---

## Use Scenarios

### Scenario 1: Skill-driven backlog list operation

**Actor**: Orchestrator agent executing `/work-backlog-item` with no arguments (Step 0)
**Trigger**: User invokes `/work-backlog-item` to browse backlog items
**Goal**: List all backlog items with status to present an interactive browser
**Expected Outcome**: The skill instructions tell the orchestrator to call `mcp__backlog__backlog_list(with_status=true)` and parse the returned dict directly, instead of shelling out to `backlog.py list --format json --with-status` and parsing stdout

### Scenario 2: Skill-driven backlog close operation

**Actor**: Orchestrator agent executing `/work-backlog-item` close path
**Trigger**: User confirms completion checklist for a backlog item
**Goal**: Mark a backlog item as DONE and close its GitHub issue
**Expected Outcome**: The skill instructions tell the orchestrator to call `mcp__backlog__backlog_close(selector="{title}", plan="{plan path}", checklist_pass=true)` and check the returned dict for success/error, instead of running a bash command

### Scenario 3: Agent-delegated backlog list in groomer

**Actor**: `@backlog-item-groomer` agent (sub-agent, not orchestrator)
**Trigger**: Groomer agent needs to list backlog items to identify dependencies
**Goal**: Retrieve current backlog items for cross-referencing
**Expected Outcome**: Agent instructions reference MCP tool call (this is already done at `.claude/agents/backlog-item-groomer.md:88`)

### Scenario 4: CI/GitHub Actions sync

**Actor**: GitHub Actions workflow (`backlog-sync.yml`)
**Trigger**: Push to main branch with changes in `.claude/backlog/`
**Goal**: Sync backlog items with GitHub Issues
**Expected Outcome**: CI continues to use `uv run .claude/skills/backlog/scripts/backlog.py sync` because GitHub Actions has no MCP client. No change to this file.

### Scenario 5: Policy document read during session initialization

**Actor**: Orchestrator agent reading CLAUDE.md at session start
**Trigger**: Every new Claude Code session
**Goal**: Understand the canonical interface for backlog operations
**Expected Outcome**: CLAUDE.md Backlog Operations section describes MCP tools as primary interface, CLI as fallback for CI. The capability gap fallback references `/backlog-tools-administrator` for extending both MCP and CLI.

### Scenario 6: Backlog item creation via skill

**Actor**: Orchestrator executing `/create-backlog-item`
**Trigger**: User or agent identifies new work to track
**Goal**: Create a per-item file and optionally a GitHub issue
**Expected Outcome**: The skill instructions tell the orchestrator to call `mcp__backlog__backlog_add(title=..., priority=..., description=..., source=..., type=..., create_issue=true)` instead of building a `uv run backlog.py add` command with flags

---

## Gap Analysis

### Identified Gaps

| # | Category | Gap Description | Impact |
|---|----------|-----------------|--------|
| 1 | Scope | `session-start-backlog.cjs` is referenced in the migration map (Tier 1, item 4) but does NOT exist in `.claude/hooks/` directory. Only `stop-backlog-reminder.cjs` and `run-commands-try-all.cjs` exist. | Migration map is partially stale. One migration target does not exist, reducing scope by 1 file. |
| 2 | Scope | The migration map (line 12) states "NOT yet registered in `.mcp.json`" but `.mcp.json:25-28` shows the backlog server IS registered. The map is stale on this point. | No functional impact but the migration map should be corrected as part of this work. |
| 3 | Behavior | The `groom-backlog-item/SKILL.md` uses `backlog.py <subcommand> --help` as a discovery/verification pattern (line 195). There is no MCP equivalent for `--help` flag discovery. | Need to define what replaces the `--help` discovery pattern. Options: (A) remove the pattern since MCP tool schemas are self-describing, (B) add a note that MCP tools have discoverable parameters, (C) keep CLI `--help` as a verification fallback. |
| 4 | Integration | `backlog-tools-administrator/SKILL.md` defines a workflow for extending `backlog.py` when capabilities are missing. After migration, capability gaps could exist in either CLI or MCP server. The administrator workflow needs to address both. | Without updating, the administrator skill will only guide CLI extensions, not MCP server extensions. |
| 5 | Scope | Tier 4 (documentation/drafts): `.claude/docs/backlog-lifecycle.draft.md` has 14 CLI invocations. The migration map says "lower priority." | Need confirmation: should Tier 4 files be migrated in this work or deferred? |
| 6 | Integration | The `groom-backlog-item/SKILL.md` uses `backlog.py` CLI for closing stale items in Step 2 validity check (lines 65, 94) AND for grooming in Step 9 (lines 280-283). These are instructions for the ORCHESTRATOR, which has MCP access. But `gh issue close` and `gh issue comment` (lines 58-60) are separate non-backlog operations that remain as-is. | Mixed migration: some commands in the validity check migrate (backlog.py calls), some stay (gh calls). |
| 7 | User | Sub-agents spawned by the orchestrator do NOT have MCP tool access (per subagent contract). When a skill is loaded by a sub-agent rather than the orchestrator, MCP tool call instructions are inactionable. | Need to verify: are any of the migrated skill files loaded by sub-agents (not the orchestrator)? If so, those files need dual-mode instructions or the migration should note that sub-agents cannot use MCP tools. |

---

## Questions Requiring Resolution

### Q1: Should Tier 4 documentation files be migrated in this scope?

- **Category**: Scope
- **Gap**: `.claude/docs/backlog-lifecycle.draft.md` has 14 CLI invocations (Gap #5)
- **Question**: Should the backlog-lifecycle draft documentation (Tier 4, 14 CLI invocations) be migrated to MCP references as part of this work, or should it be deferred to a separate effort?
- **Options**:
  - A) Include Tier 4 in this migration for consistency
  - B) Defer Tier 4 -- it is a draft document and lower priority
- **Why It Matters**: Including it adds ~14 more invocations to migrate; excluding it leaves a known inconsistency in a document that may be referenced.
- **Resolution**: _pending_

### Q2: How should the `--help` discovery pattern be replaced?

- **Category**: Behavior
- **Gap**: `groom-backlog-item/SKILL.md:195` uses `backlog.py <subcommand> --help` for signature verification before calling an unfamiliar subcommand (Gap #3)
- **Question**: What should replace the CLI `--help` verification pattern in MCP-migrated instructions? MCP tools have self-describing schemas, but there is no explicit "check signature before calling" equivalent.
- **Options**:
  - A) Remove the `--help` verification step entirely -- MCP tool schemas are enforced by the protocol, so calling with wrong parameters returns a clear error
  - B) Replace with a note that MCP tools have typed parameters and invalid calls return structured errors
  - C) Keep CLI `--help` as an explicit verification fallback alongside MCP instructions
- **Why It Matters**: The `--help` pattern exists because `sync` vs `update` vs `groom` have different signatures and calling with wrong args fails silently in CLI. MCP eliminates this class of error, so the pattern may be unnecessary.
- **Resolution**: _pending_

### Q3: Should the migration map itself be updated as part of this work?

- **Category**: Scope
- **Gap**: The migration map has two stale claims: "NOT yet registered in .mcp.json" (line 12) and "55 tests" (line 12). `session-start-backlog.cjs` is listed but does not exist (Gaps #1, #2).
- **Question**: Should the migration map (`.claude/skills/backlog/CLI_TO_MCP_MIGRATION.md`) be updated/corrected as files are migrated, or should it be left as a historical record of the pre-migration state?
- **Options**:
  - A) Update the migration map as each file is migrated (mark as DONE, correct stale claims)
  - B) Leave it as-is as a historical snapshot; it served its purpose
  - C) Delete the migration map after migration is complete
- **Why It Matters**: If left stale, the map could confuse future agents. If updated, it becomes a progress tracker.
- **Resolution**: _pending_

### Q4: Are any migration-target skill files loaded by sub-agents?

- **Category**: Integration
- **Gap**: Sub-agents do not have MCP tool access (Gap #7). If a skill file that instructs "call mcp__backlog__backlog_list" is loaded by a sub-agent, the instruction is inactionable.
- **Question**: Among the Tier 2-3 migration targets, are any loaded exclusively by sub-agents rather than the orchestrator? Specifically: do `/work-backlog-item`, `/create-backlog-item`, `/groom-backlog-item`, or `/group-items-to-milestone` ever run as sub-agent context (not orchestrator skills)?
- **Options**:
  - A) All these skills are orchestrator-level only -- migrate fully to MCP
  - B) Some skills are loaded by sub-agents -- those need dual-mode instructions (MCP primary, CLI fallback)
- **Why It Matters**: If a sub-agent reads "call mcp__backlog__backlog_list", it cannot execute that instruction. The migration would break those workflows.
- **Resolution**: _pending_

### Q5: What should happen to the `backlog-tools-administrator` extension workflow?

- **Category**: Integration
- **Gap**: The administrator skill workflow describes extending `backlog.py` CLI when capabilities are missing (Gap #4). After migration, gaps could be in the MCP server.
- **Question**: Should the backlog-tools-administrator skill be updated to describe extending the MCP server (not just CLI), or is it sufficient to note that CLI and MCP share the operations layer so extending operations.py covers both?
- **Options**:
  - A) Update the administrator to describe MCP server extension (add `@mcp.tool()` decorator workflow alongside CLI subcommand workflow)
  - B) Note that both CLI and MCP are thin wrappers over `operations.py`, so the administrator only needs to extend `operations.py` and the wrappers follow
- **Why It Matters**: The administrator is the escalation path when backlog tooling has a capability gap. If it only knows about CLI extension, MCP-specific gaps (e.g., missing MCP tool, wrong parameter type) would not be handled.
- **Resolution**: _pending_

---

## Goals (Pending Resolution)

_These goals will be finalized after questions are resolved._

1. Replace all CLI shell-out instructions (`uv run backlog.py ...`) in Tier 1-3 files with MCP tool call references (`mcp__backlog__<tool_name>(...)`)
2. Update CLAUDE.md Backlog Operations policy to declare MCP as primary interface, CLI as fallback for CI
3. Update `stop-backlog-reminder.cjs` hook to reference MCP tool names
4. Rewrite `backlog/SKILL.md` documentation to describe MCP tool interface as primary, CLI as secondary
5. Update `backlog-tools-administrator/SKILL.md` to address MCP server extension (pending Q5 resolution)
6. Correct stale claims in migration map (pending Q3 resolution)
7. Confirm no sub-agent breakage from MCP-only instructions (pending Q4 resolution)
8. Optionally migrate Tier 4 draft documentation (pending Q1 resolution)
9. Verify 382 tests remain passing after all file modifications
10. Close the original idea backlog item (`idea-convert-backlogpy-into-an-mcp-server-using-fastmcp-skill.md`) upon completion

---

## Next Steps

After questions are resolved:

1. Update "Resolution" fields in Questions section
2. Finalize Goals section
3. Proceed to RT-ICA assessment
4. Then proceed to architecture design
