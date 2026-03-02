# Architecture Spec: Backlog CLI-to-MCP Migration

## Document Metadata

- **Generated**: 2026-03-02
- **Feature**: Backlog CLI-to-MCP Migration (Issue #329)
- **Type**: Content migration across instruction documents
- **Input**: [Feature Context](./feature-context-backlog-mcp-migration.md), [Codebase Analysis](./codebase/backlog-mcp-migration-patterns.md), [Migration Map](./../.claude/skills/backlog/CLI_TO_MCP_MIGRATION.md)

---

## Executive Summary

Replace CLI shell-out instructions (`uv run .claude/skills/backlog/scripts/backlog.py <subcommand>`) with MCP tool call references (`mcp__backlog__<tool_name>(...)`) across skill SKILL.md files, agent files, policy documents, and hooks. This is a content migration -- no Python code changes. The MCP server (10 tools, 382 tests) and permissions (`mcp__backlog__*` in `.claude/settings.json`) are already in place.

---

## Architecture Decisions

### ADR-1: MCP Tool Call Syntax in SKILL.md Files

**Status**: Decided

**Context**: SKILL.md files currently use bash code fences with `uv run backlog.py ...` commands. No SKILL.md file currently references MCP tools. Two agent files (`backlog-item-groomer.md`, `backlog-mcp-validator.md`) already use MCP tools with the `mcp__backlog__<tool_name>(params)` convention.

**Decision**: Use prose instruction blocks with the MCP tool name in backtick-code format, followed by a parameter table or inline parameter list.

**Format -- simple calls (3 or fewer parameters)**:

````markdown
Call the `mcp__backlog__backlog_list` tool with `with_status=true`.

Parse the returned dict. Each entry in `items` has `title`, `priority`, `issue`, `plan`, `status`, `milestone`, `file_path`, `groomed`.
````

**Format -- complex calls (4+ parameters or conditional construction)**:

````markdown
Call the `mcp__backlog__backlog_add` tool:

| Parameter | Value |
|-----------|-------|
| `title` | `"{title}"` |
| `priority` | `"{priority}"` |
| `description` | `"{description}"` |
| `source` | `"{source}"` |
| `type` | `"{type}"` |
| `create_issue` | `true` if P0/P1 and user confirmed; `false` if P2/Ideas or user declined |

Check the returned dict for `error` key. On success, the dict contains `file_path`, `title`, `priority`, `issue` (if created).
````

**Format -- shorthand in annotations and section headers**:

````markdown
mcp__backlog__backlog_groom(selector="{title}", section="Fact-Check", content="{summary}")
````

This shorthand is used in non-executable annotation blocks (Step 6 annotations in `groom-backlog-item/SKILL.md` lines 181-184, 202-211, 222-239, 294-303) where the inline form is clearer than a table.

**Rationale**:

1. The orchestrator reads SKILL.md as natural-language instructions. It does not execute bash code fences literally -- it interprets them as "run this via Bash tool." The same mechanism works for prose tool call instructions: the orchestrator interprets "Call `mcp__backlog__backlog_list`" as "invoke this MCP tool."
2. The `mcp__backlog__` prefix is the established naming convention (used in `.claude/settings.json` permissions, agent `tools` frontmatter, and `backlog-item-groomer.md` line 88).
3. Parameter tables match the complexity of multi-parameter calls with conditional logic, which bash code fences currently handle via prose interspersed with code.
4. The shorthand form maintains readability in annotation blocks where a table would be unnecessarily verbose.

**Rejected alternatives**:

- Bash-style function call syntax (`backlog_list(with_status=true)` without prefix): Ambiguous -- could be confused with a Python function call, a CLI subcommand, or a fictional notation. The `mcp__backlog__` prefix is unambiguous.
- JSON-style invocation blocks: Overly verbose for instruction documents. The orchestrator does not need JSON to invoke MCP tools.

### ADR-2: MCP-Only for Orchestrator Skills, CLI Retained for CI

**Status**: Decided

**Decision**: Skills and agents migrated to MCP-only instructions. No dual-mode fallback in skill files.

**Scope**:

- **MCP-only**: All SKILL.md files, agent `.md` files, policy documents, and hooks that instruct the orchestrator or sub-agents with MCP tool access
- **CLI retained**: `.github/workflows/backlog-sync.yml` (GitHub Actions has no MCP client), `backlog-tools-administrator/SKILL.md` verification commands (linting/testing are shell operations), and the CLI script itself (`backlog.py`)

**Rationale**:

1. The orchestrator always has MCP access (permission granted in `.claude/settings.json:13`).
2. Dual-mode instructions double the maintenance surface -- the exact problem this migration solves.
3. CLI fallback for the orchestrator is unnecessary: if the MCP server is down, the backlog operations are unavailable regardless of interface (both share `operations.py`).
4. Sub-agents that need backlog access (`@backlog-item-groomer`) already have MCP server registration in their agent frontmatter (`mcpServers:` block). See ADR-3.

### ADR-3: Sub-Agent MCP Access

**Status**: Decided

**Context**: Sub-agents spawned via the Agent tool do not inherit the orchestrator's MCP connections by default. However, agent files can declare their own `mcpServers:` block in frontmatter, which gives the sub-agent its own MCP server instance.

**Decision**: Sub-agents that need backlog access declare MCP server connections in their agent frontmatter. Skills loaded by the orchestrator use MCP directly. No dual-mode needed.

**Verification of which skills are sub-agent-loaded**:

| Skill | Loaded by | MCP access |
|-------|-----------|------------|
| `/work-backlog-item` | Orchestrator (user-invocable) | Yes -- orchestrator has `mcp__backlog__*` |
| `/create-backlog-item` | Orchestrator (user-invocable) | Yes |
| `/groom-backlog-item` | Orchestrator (user-invocable) | Yes |
| `/group-items-to-milestone` | Orchestrator (user-invocable) | Yes |
| `/backlog` | Orchestrator (invoked by other skills) | Yes |
| `/backlog-tools-administrator` | Orchestrator (user-invocable) | Yes (but verification commands stay CLI) |

No backlog skill is loaded exclusively by sub-agents. The `@backlog-item-groomer` agent is a sub-agent but it has its own `mcpServers:` block (`.claude/agents/backlog-item-groomer.md` lines 7-15) granting independent MCP access.

**Result**: All migration targets are orchestrator-level. MCP-only instructions are safe.

### ADR-4: Migration Map Disposition

**Status**: Decided

**Decision**: Update the migration map as files are migrated. Mark each file as DONE. Correct the two stale claims. Remove the `session-start-backlog.cjs` entry (file does not exist). After all migrations complete, add a header noting the map is a historical record of the completed migration.

**Rationale**: An uncorrected stale document creates confusion for future agents. The map serves as a progress tracker during migration and as a historical record afterward.

### ADR-5: `--help` Discovery Pattern Replacement

**Status**: Decided

**Context**: `groom-backlog-item/SKILL.md` line 276 instructs the orchestrator to verify CLI subcommand signatures with `backlog.py <subcommand> --help` before calling an unfamiliar subcommand. This guards against calling `sync` with a title argument (which silently fails).

**Decision**: Remove the `--help` verification step. Replace with a note that MCP tools have typed parameter schemas enforced by the protocol.

**Replacement text**:

````markdown
**MCP tool parameters are schema-enforced.** Unlike CLI subcommands, MCP tools reject invalid parameters
with a structured error. There is no need to verify signatures before calling. If unsure which tool to
use, check the tool name and parameters:

- `mcp__backlog__backlog_update` — updates an existing item (selector required)
- `mcp__backlog__backlog_groom` — writes groomed content (selector required)
- `mcp__backlog__backlog_sync` — syncs ALL items to GitHub (no selector — operates on entire backlog)
````

**Rationale**: The `--help` guard exists because CLI subcommands have different argument shapes and calling with wrong args can fail silently (exit code 0 with error on stderr). MCP tools return structured `{"error": "..."}` responses for invalid parameters. The guard is unnecessary.

### ADR-6: `session-start-backlog.cjs` Gap

**Status**: Documented

**Finding**: The migration map (Tier 1, item 4) references `.claude/hooks/session-start-backlog.cjs`. This file does not exist. A Glob search for `session-start*.cjs` returns no results. The `.claude/settings.json` hooks section has no SessionStart hook for backlog.

**Action**: Remove this entry from the migration map. No migration task exists for it. If a session-start hook is needed in the future, it should be created as a separate feature.

### ADR-7: Tier 4 Documentation Deferral

**Status**: Decided

**Decision**: Defer Tier 4 (`backlog-lifecycle.draft.md`, 14 CLI invocations) and Tier 5 (historical plan files) from this migration scope.

**Rationale**:

1. `backlog-lifecycle.draft.md` is explicitly marked `STATUS: DRAFT` with `[VERIFY]` annotations. It is not a canonical reference and is not read during normal skill/agent execution.
2. Historical plan files (Tier 5) are completed work records. Updating them provides no behavioral benefit.
3. Including Tier 4-5 adds ~55 more invocations to migrate with no change in runtime behavior.
4. A follow-up task can update Tier 4 when the draft is promoted to canonical status.

**Out-of-scope items from this decision**:

- `backlog-lifecycle.draft.md` (14 CLI refs) -- deferred
- `plan/architect-backlog-lifecycle-promotion.md` (7 refs) -- historical, skip
- `plan/tasks-11-backlog-lifecycle-promotion.md` (15+ refs) -- historical, skip
- `plan/tasks-7-backlog-gh-first-phase1.md` (6 refs) -- historical, skip
- `plan/feature-context-backlog-lifecycle-promotion.md` (10+ refs) -- historical, skip
- `plan/codebase/cross-references-backlog.md` (1 ref) -- historical, skip
- Tier 6 backlog item files (self-referential CLI references) -- not migration targets
- Tier 7 Python code (internal `backlog.py` imports) -- not migration targets

### ADR-8: `close --reason` Semantic Correction

**Status**: Decided

**Context**: Several skill files use `backlog.py close "{title}" --reason "..."`. The CLI `close` subcommand does NOT accept `--reason` -- only `resolve` does (confirmed: `backlog.py` line 1316 shows `--reason` on the `resolve` subcommand only). The migration map notes this: "use `backlog_resolve` for reason-based closes."

**Decision**: During migration, every `backlog.py close ... --reason` call is replaced with `mcp__backlog__backlog_resolve(selector=..., reason=...)`. This is a semantic correction, not just a syntax translation.

**Affected locations**:

- `work-backlog-item/SKILL.md` lines 195, 301
- `groom-backlog-item/SKILL.md` lines 65, 94

---

## CLI-to-MCP Parameter Mapping Reference

All 10 MCP tools with parameter mappings from CLI flags. Source: [server.py](./../.claude/skills/backlog/backlog_core/server.py).

| CLI Pattern | MCP Tool Call |
|---|---|
| `backlog list --format json --with-status` | `mcp__backlog__backlog_list(with_status=true)` |
| `backlog list --format json` | `mcp__backlog__backlog_list()` |
| `backlog list --format json --status resolved` | `mcp__backlog__backlog_list(status="resolved")` |
| `backlog view "{selector}" --format json` | `mcp__backlog__backlog_view(selector="{selector}")` |
| `backlog add --title T --priority P --description D --source S --type T` | `mcp__backlog__backlog_add(title=T, priority=P, description=D, source=S, type=T)` |
| `backlog add ... --no-create-issue` | `mcp__backlog__backlog_add(..., create_issue=false)` |
| `backlog close "{sel}" --plan P --checklist-pass` | `mcp__backlog__backlog_close(selector="{sel}", plan=P, checklist_pass=true)` |
| `backlog close "{sel}" --reason "..."` | `mcp__backlog__backlog_resolve(selector="{sel}", reason="...")` (ADR-8) |
| `backlog resolve "{sel}" --reason "..."` | `mcp__backlog__backlog_resolve(selector="{sel}", reason="...")` |
| `backlog update "{sel}" --plan P` | `mcp__backlog__backlog_update(selector="{sel}", plan=P)` |
| `backlog update "{sel}" --status in-progress` | `mcp__backlog__backlog_update(selector="{sel}", status="in-progress")` |
| `backlog update "{sel}" --create-issue` | `mcp__backlog__backlog_update(selector="{sel}", create_issue=true)` |
| `backlog update "{sel}" --section S --content C` | `mcp__backlog__backlog_update(selector="{sel}", section=S, content=C)` |
| `backlog groom "{sel}" --section S --content C` | `mcp__backlog__backlog_groom(selector="{sel}", section=S, content=C)` |
| `backlog groom "{sel}" --groomed-content BODY` | `mcp__backlog__backlog_groom(selector="{sel}", groomed_content=BODY)` |
| `backlog sync` | `mcp__backlog__backlog_sync()` |
| `backlog sync --dry-run` | `mcp__backlog__backlog_sync(dry_run=true)` |
| `backlog normalize --dry-run` | `mcp__backlog__backlog_normalize(dry_run=true)` |
| `backlog pull --dry-run` | `mcp__backlog__backlog_pull(dry_run=true)` |

**Dropped parameters**:

- `-R Jamie-BitFlight/claude_skills` -- MCP server uses `DEFAULT_REPO` constant; no parameter needed
- `--format json` -- MCP tools always return structured dicts; no format flag
- `--groomed-file` / stdin piping -- MCP callers provide content inline as strings (CLI-only parameters per DOCUMENTATION_DRIFT_AUDIT FIND-10, FIND-11)

---

## File-by-File Migration Strategy

### Migration Wave 1: Policy and Infrastructure

These files define the canonical interface rule. Updating them first establishes the migration direction for all downstream files.

#### 1.1 `.claude/CLAUDE.md` -- Backlog Operations Section (lines 210-224)

**Current state**: Mandates `backlog.py` as the single interface. Contains a bash code fence with `uv run .claude/skills/backlog/scripts/backlog.py add|list|sync|close|resolve|update ...`.

**Target state**: Declare MCP tools as primary interface. CLI as fallback for CI only.

**Changes**:

- Replace the `<backlog_operations>` section content
- Primary interface: `mcp__backlog__*` MCP tools (10 tools)
- Secondary interface: CLI (`backlog.py`) for CI/GitHub Actions and environments without MCP
- Keep the capability gap fallback referencing `/backlog-tools-administrator`
- Keep the "GitHub Issues are the source of truth" policy unchanged

**Migration template for CLAUDE.md**:

````markdown
<backlog_operations>

**Primary interface (MCP)**: Use `mcp__backlog__*` tools for all backlog and GitHub issue CRUD. GitHub Issues are the source of truth; `.claude/backlog/` per-item files are the local cache.

Available tools: `backlog_add`, `backlog_list`, `backlog_view`, `backlog_sync`, `backlog_close`, `backlog_resolve`, `backlog_update`, `backlog_groom`, `backlog_normalize`, `backlog_pull`.

All tools return a dict. Check for `error` key on failure. Success responses include `messages` and `warnings` lists.

**CI fallback (CLI)**: GitHub Actions and environments without an MCP client use the CLI:

```bash
uv run .claude/skills/backlog/scripts/backlog.py add|list|sync|close|resolve|update ...
```

Do not edit `.claude/backlog/*.md` files directly or use `gh issue edit` -- both bypass sync logic.

Skills `/create-backlog-item` and `/work-backlog-item` invoke these tools. See `/backlog` skill.

**Capability gap fallback**: If the MCP tools or CLI lack the needed operation, invoke `/backlog-tools-administrator` to close the gap.

</backlog_operations>
````

**Invocations replaced**: 1 (the bash code fence)

#### 1.2 `.claude/hooks/stop-backlog-reminder.cjs`

**Current state**: References `Skill(skill: "create-backlog-item")` and `Skill(skill: "work-backlog-item")`. No direct CLI invocations.

**Target state**: No change needed.

**Rationale**: This hook uses skill activation syntax, not CLI commands. The skills themselves will be migrated. The hook's instructions remain correct regardless of whether the skills use MCP or CLI internally.

#### 1.3 `.cursor/rules/backlog-before-work.mdc` (line 12)

**Current state**: Contains `backlog update "{title}" --plan "{path}"` as a prose shorthand.

**Target state**: Replace with MCP tool reference.

**Changes**:

- Replace `backlog update "{title}" --plan "{path}"` with `mcp__backlog__backlog_update(selector="{title}", plan="{path}")`

**Invocations replaced**: 1

#### 1.4 Migration Map Corrections

**File**: `.claude/skills/backlog/CLI_TO_MCP_MIGRATION.md`

**Changes**:

- Line 12: Change "Tests passing (55 tests), NOT yet registered in `.mcp.json`" to "Tests passing (382 tests), registered in `.mcp.json` (lines 25-28)"
- Tier 1 item 4 (`session-start-backlog.cjs`): Remove entry or mark as "FILE DOES NOT EXIST -- removed from scope"
- Add a header noting this is a progress tracker; mark completed items as DONE

---

### Migration Wave 2: Skill Files (Highest Impact)

These contain the actual CLI commands that the orchestrator executes. Ordered by invocation count (highest first).

#### 2.1 `.claude/skills/work-backlog-item/SKILL.md` -- 19 invocations

**Highest density file.** All 19 CLI calls are instructions to the orchestrator.

**Line-by-line replacements**:

| Line | Current CLI | Replacement |
|---|---|---|
| 97 | `backlog.py list --format json --with-status` | `mcp__backlog__backlog_list(with_status=true)` |
| 155 | `backlog.py view "{$0}" --format json` | `mcp__backlog__backlog_view(selector="{$0}")` |
| 195 | `backlog.py close "{title}" --reason "..."` | `mcp__backlog__backlog_resolve(selector="{title}", reason="...")` (ADR-8) |
| 233 | `backlog.py list --format json` | `mcp__backlog__backlog_list()` |
| 301 | `backlog.py close "{title}" --reason "..."` | `mcp__backlog__backlog_resolve(selector="{title}", reason="...")` (ADR-8) |
| 419 | `backlog.py update "{title}" --plan "..."` | `mcp__backlog__backlog_update(selector="{title}", plan="...")` |
| 453 | `backlog.py view "{$1}" --format json` | `mcp__backlog__backlog_view(selector="{$1}")` |
| 473 | `backlog.py resolve "{title or #N}" --reason "..."` | `mcp__backlog__backlog_resolve(selector="...", reason="...")` |
| 566 | `backlog.py update "{title}" --status in-progress` | `mcp__backlog__backlog_update(selector="{title}", status="in-progress")` |
| 584 | `backlog.py close "{title}" --plan "..." --checklist-pass` | `mcp__backlog__backlog_close(selector="{title}", plan="...", checklist_pass=true)` |
| 590 | `backlog.py close "#{N}" --plan "..." --checklist-pass` | `mcp__backlog__backlog_close(selector="#{N}", plan="...", checklist_pass=true)` |
| 641 | `backlog.py view "#{issue_number}" --format json` | `mcp__backlog__backlog_view(selector="#{issue_number}")` |
| 650 | `backlog.py update "{title}" --create-issue` | `mcp__backlog__backlog_update(selector="{title}", create_issue=true)` |
| 660 | `backlog.py update "{title}" --status in-progress` | `mcp__backlog__backlog_update(selector="{title}", status="in-progress")` |
| 685 | `backlog.py list` | `mcp__backlog__backlog_list()` |

Each bash code fence is replaced with the prose instruction format from ADR-1. The surrounding prose describing output parsing changes from "Parse the JSON output" to "Parse the returned dict."

#### 2.2 `.claude/skills/groom-backlog-item/SKILL.md` -- 6 invocations

| Line | Current CLI | Replacement |
|---|---|---|
| 25 | `backlog.py list --format json` | `mcp__backlog__backlog_list()` |
| 65 | `backlog.py close "{title}" --reason "..."` | `mcp__backlog__backlog_resolve(selector="{title}", reason="...")` (ADR-8) |
| 71 | `backlog.py view "#{N}" --format json` | `mcp__backlog__backlog_view(selector="#{N}")` |
| 94 | `backlog.py close "{title}" --reason "..."` | `mcp__backlog__backlog_resolve(selector="{title}", reason="...")` (ADR-8) |
| 195 | `backlog.py <subcommand> --help` | Remove; replace with ADR-5 text |
| 198/283 | `backlog.py update/groom --section --content` | `mcp__backlog__backlog_groom(selector=..., section=..., content=...)` |

**Additional changes**:

- Lines 276-286: Replace the `--help` verification guard with the ADR-5 replacement text
- Lines 288-313 (Step 9 preferred/alternative patterns): Rewrite to use MCP tool calls
  - Incremental: `mcp__backlog__backlog_groom(selector="{title}", section="Fact-Check", content="{summary}")`
  - Full body: `mcp__backlog__backlog_groom(selector="{title}", groomed_content="{full body}")`
  - Remove `--groomed-file` and stdin pipe patterns (CLI-only; ADR-2)
- Lines 181-184, 202-211, 222-239, 294-303 (shorthand annotation blocks): Use the shorthand format from ADR-1

#### 2.3 `.claude/skills/create-backlog-item/SKILL.md` -- 1 invocation

| Line | Current CLI | Replacement |
|---|---|---|
| 163-169 | `backlog.py add --title ... --priority ... --description ...` | `mcp__backlog__backlog_add(title=..., priority=..., description=..., source=..., type=..., create_issue=...)` |

**Additional changes**:

- Lines 174-179 (conditional GitHub Issue creation logic): Translate to `create_issue` parameter value:
  - P0/P1 with user confirmation: `create_issue=true` (default, so omit parameter)
  - P2/Ideas or user declined: `create_issue=false`
  - `--auto` without `--create-issue`: `create_issue=false`
- Remove `--research-first` handling note if MCP `backlog_add` does not have that parameter (confirmed: `server.py` does not expose `research_first`). Document this as a dropped parameter or note it must be embedded in description.

#### 2.4 `.claude/skills/group-items-to-milestone/SKILL.md` -- 1 invocation

| Line | Current CLI | Replacement |
|---|---|---|
| 37 | `backlog.py list --format json` | `mcp__backlog__backlog_list()` |

Simple replacement. The `gh api` and `gh issue` commands in this file are NOT backlog CLI calls and remain unchanged.

#### 2.5 `.claude/skills/backlog/SKILL.md` -- Documentation Rewrite

**Current state**: Documents CLI invocation syntax with bash code fences for all 6 original subcommands.

**Target state**: Rewrite to document MCP tool interface as primary, CLI as secondary (for CI).

**Structure**:

```text
# Backlog Tools

## Primary Interface (MCP)

[Table of 10 tools with parameter signatures]

## CI/CLI Interface

[Retained bash syntax for environments without MCP]

## Environment

[GITHUB_TOKEN requirement unchanged]

## Integration

[Updated to reference MCP tools]
```

#### 2.6 `.claude/skills/work-backlog-item/references/step-procedures.md` -- 2 invocations

| Line | Current CLI | Replacement |
|---|---|---|
| 12 | `backlog.py list --format json --with-status` | `mcp__backlog__backlog_list(with_status=true)` |
| 117 | `backlog.py update "{title}" --plan "..."` | `mcp__backlog__backlog_update(selector="{title}", plan="...")` |

#### 2.7 `.claude/skills/work-backlog-item/references/github-integration.md` -- 3 invocations

| Line | Current CLI | Replacement |
|---|---|---|
| 36 | `backlog.py update "{title}" --create-issue` | `mcp__backlog__backlog_update(selector="{title}", create_issue=true)` |
| 46 | `backlog.py update "{title}" --status in-progress` | `mcp__backlog__backlog_update(selector="{title}", status="in-progress")` |
| 61 | `backlog.py close "{title}" --plan "..." --checklist-pass` | `mcp__backlog__backlog_close(selector="{title}", plan="...", checklist_pass=true)` |

Non-backlog `gh` commands in this file (e.g., `gh issue view`) remain unchanged.

#### 2.8 `.claude/skills/work-backlog-item/references/close-resolve-procedure.md` -- 3 invocations

| Line | Current CLI | Replacement |
|---|---|---|
| 36 | `backlog.py resolve "{title or #N}" --reason "..."` | `mcp__backlog__backlog_resolve(selector="...", reason="...")` |
| 129 | `backlog.py close "{title}" --plan "..." --checklist-pass` | `mcp__backlog__backlog_close(selector="{title}", plan="...", checklist_pass=true)` |
| 135 | `backlog.py close "#{N}" --plan "..." --checklist-pass` | `mcp__backlog__backlog_close(selector="#{N}", plan="...", checklist_pass=true)` |

Non-backlog `gh` commands in this file remain unchanged.

---

### Migration Wave 3: Agent Files

#### 3.1 `.claude/agents/backlog-item-groomer.md` -- 1 remaining CLI invocation

**Current state**: Already mostly migrated. Has `mcpServers:` block and `mcp__backlog__*` in `tools` frontmatter. Line 88 already uses MCP.

**Remaining work**: Verify no residual CLI references. The codebase analysis found one remaining CLI call at line 79. If present, replace with MCP equivalent.

#### 3.2 `.claude/agents/backlog-mcp-validator.md` -- Documentation gap

**Current state**: Uses MCP tools exclusively. Lists `backlog_list` parameters as `with_status`, `from_github`, `label` but omits `section`, `status`, `title` filter parameters.

**Change**: Update the tool parameter reference to include all 6 `backlog_list` parameters. This is a documentation correction, not a CLI-to-MCP migration, but it should be done while touching agent files.

---

### Migration Wave 4: Administrator Skill

#### 4.1 `.claude/skills/backlog-tools-administrator/SKILL.md`

**Current state**: Describes a workflow for extending `backlog.py` when capabilities are missing. Step 3A delegates to `@python-cli-architect` for script fixes.

**Target state**: Update to describe extending both the CLI and the MCP server. Both are thin wrappers over `operations.py`, so the primary extension point is `operations.py`.

**Changes**:

- Line 9: Update "bypassing the backlog script" to "bypassing the backlog tools (MCP or CLI)"
- Step 3A: Add MCP server extension alongside CLI extension:
  - Primary: Extend `operations.py` with new function
  - Secondary: Add `@mcp.tool()` wrapper in `server.py` and CLI subcommand in `backlog.py`
  - Context to include: `server.py` (MCP tool definitions) alongside `backlog.py` (CLI definitions)
- Step 4 verification: Add MCP tool verification step (call the new tool, verify structured response)
- Classification flowchart: Update "backlog.py" references to "backlog tooling (MCP server or CLI)"

---

## Migration Order and Dependencies

```text
Wave 1: Policy & Infrastructure (no dependencies)
  1.1  .claude/CLAUDE.md                    -- sets migration direction
  1.3  .cursor/rules/backlog-before-work.mdc -- independent
  1.4  Migration map corrections            -- independent

Wave 2: Skill Files (depends on Wave 1 for policy alignment)
  2.1  work-backlog-item/SKILL.md           -- highest impact (19 invocations)
  2.6  work-backlog-item/references/step-procedures.md      -- references same patterns as 2.1
  2.7  work-backlog-item/references/github-integration.md   -- references same patterns as 2.1
  2.8  work-backlog-item/references/close-resolve-procedure.md -- references same patterns as 2.1
  2.2  groom-backlog-item/SKILL.md          -- 6 invocations + --help guard removal
  2.3  create-backlog-item/SKILL.md         -- 1 invocation
  2.4  group-items-to-milestone/SKILL.md    -- 1 invocation
  2.5  backlog/SKILL.md                     -- documentation rewrite (do last in wave 2)

Wave 3: Agent Files (depends on Wave 2 for consistent tool references)
  3.1  agents/backlog-item-groomer.md       -- cleanup remaining CLI ref
  3.2  agents/backlog-mcp-validator.md      -- documentation gap fix

Wave 4: Administrator Skill (depends on Waves 1-3 being complete)
  4.1  backlog-tools-administrator/SKILL.md -- extension workflow update
```

**Within Wave 2**, the `work-backlog-item` cluster (2.1 + 2.6-2.8) should be done together since the reference files mirror patterns in the main SKILL.md. The `backlog/SKILL.md` rewrite (2.5) should be last because it serves as documentation for the migrated interface.

---

## Verification Approach

### Per-File Verification

After migrating each file:

1. **No residual CLI references**: Grep the file for `backlog.py` and `uv run .claude/skills/backlog/scripts`. Zero matches expected (except in "CI fallback" sections explicitly retained).

   ```bash
   grep -c "backlog\.py\|uv run.*backlog/scripts" <migrated-file>
   ```

2. **MCP tool name correctness**: Every `mcp__backlog__backlog_` reference uses one of the 10 valid tool names: `add`, `list`, `view`, `sync`, `close`, `resolve`, `update`, `groom`, `normalize`, `pull`.

3. **Parameter correctness**: Each tool call uses valid parameter names from [server.py](./../.claude/skills/backlog/backlog_core/server.py). Common mistakes to check:
   - `format="json"` -- REMOVE (no `format` parameter on MCP tools)
   - `repo=` -- REMOVE (MCP server uses `DEFAULT_REPO` constant)
   - `reason=` on `backlog_close` -- WRONG (use `backlog_resolve` instead, per ADR-8)
   - `with_status` not `with-status` (Python parameter names use underscores)

4. **Markdown linting**: Run `uv run prek run --files <migrated-file>` to verify formatting.

### Cross-File Verification

After all waves complete:

1. **Repo-wide CLI reference audit**:

   ```bash
   grep -rn "uv run.*backlog/scripts/backlog.py" .claude/skills/ .claude/agents/ .claude/hooks/ .claude/CLAUDE.md .cursor/
   ```

   Expected matches: zero in migrated files. Matches in `.github/workflows/` are expected (CI stays CLI).

2. **MCP tool coverage**: Verify all 10 tools are referenced somewhere in the migrated skill ecosystem. Missing tools indicate potential documentation gaps.

3. **Test suite**: Run `uv run pytest .claude/skills/backlog/tests/` to confirm 382 tests still pass. The migration is content-only (no Python changes), so tests should be unaffected. This is a safety check.

4. **Semantic correctness**: Verify every `close --reason` pattern was converted to `backlog_resolve`, not `backlog_close` (ADR-8).

---

## Out-of-Scope Items

| Item | Reason |
|---|---|
| `.github/workflows/backlog-sync.yml` | CI has no MCP client; stays CLI |
| `.claude/docs/backlog-lifecycle.draft.md` (Tier 4, 14 refs) | Draft document; deferred per ADR-7 |
| Historical plan files (Tier 5, ~40 refs) | Completed work records; no behavioral impact |
| Backlog item files (Tier 6) | Self-referential; describe `backlog.py` as subject of work |
| Python code internals (Tier 7) | `backlog.py`, `operations.py`, `server.py`, tests |
| `session-start-backlog.cjs` | File does not exist (ADR-6) |
| `backlog_core/ARCHITECTURE.md` | MCP server internals; not a CLI-to-MCP migration target |
| Any Python implementation changes | This is a content migration; no code changes |
| MCP server registration (`.mcp.json`) | Already complete |
| MCP permissions (`.claude/settings.json`) | Already complete |

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Orchestrator misinterprets prose MCP instructions | Low | Medium | ADR-1 format follows established pattern from `backlog-item-groomer.md:88`; test with one skill first |
| `close --reason` not caught during migration | Medium | High | ADR-8 explicitly lists all 4 affected locations; verification step checks for `reason=` on `backlog_close` |
| Missing parameter in MCP call (e.g., forgetting `selector`) | Low | Low | MCP returns structured `{"error": "..."}` for missing required params; self-correcting |
| `--research-first` parameter lost in `create-backlog-item` | Medium | Low | Document that `research_first` must be embedded in `description` field for MCP calls |
| Markdown linting failures from format change | Medium | Low | Run `prek` on each file after migration |
| Migration map becomes stale during migration | Low | Low | Update map as each file completes (ADR-4) |

---

## Task Decomposition Guidance

This migration decomposes into independent file-level tasks within each wave. The following constraints apply:

- **Wave 1 tasks are parallelizable** (CLAUDE.md, `.cursor/rules`, migration map corrections have no dependencies on each other)
- **Wave 2 tasks within the `work-backlog-item` cluster (2.1 + 2.6-2.8) should be sequential** to maintain consistency between SKILL.md and its reference files
- **Wave 2 remaining tasks (2.2-2.5) are parallelizable** after 2.1 cluster completes
- **Wave 3 and 4 are sequential** (small scope, 1-2 files each)

**Estimated scope**: ~34 CLI invocations across 13 files (Tiers 1-3), plus 1 documentation rewrite (`backlog/SKILL.md`).

**Agent assignment guidance**: Each file migration is a documentation edit task. The implementing agent needs:

- This architecture spec (for ADR decisions and parameter mapping)
- The target file (for current content)
- The [server.py tool signatures](./../.claude/skills/backlog/backlog_core/server.py) (for parameter validation)
