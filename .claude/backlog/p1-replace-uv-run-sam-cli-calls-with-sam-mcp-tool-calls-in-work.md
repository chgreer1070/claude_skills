---
name: Replace uv run sam CLI calls with SAM MCP tool calls in workflow skills
description: 'The workflow skills (complete-implementation, implement-feature, start-task) tell the orchestrator to run uv run sam CLI commands and pass the output to agents. This wastes orchestrator context and creates an unnecessary intermediary. The sam MCP server (mcp__plugin_dh_sam__*) provides the same operations as MCP tools — agents with MCP access can call sam_read, sam_status, sam_ready directly. Two changes needed: (1) Add mcp__plugin_dh_sam__* tools to the allowed-tools (skills) or tools (agents) frontmatter of every workflow skill and agent that needs SAM access. (2) Rewrite skill instructions to tell agents to use SAM MCP tools directly instead of orchestrator-fetched CLI output. The CLI (uv run sam) becomes fallback-only for when MCP is unavailable.'
metadata:
  topic: replace-uv-run-sam-cli-calls-with-sam-mcp-tool-calls-in-work
  source: 'User observation during #933 implementation — agents should use MCP directly, not orchestrator-fetched CLI output'
  added: '2026-03-21'
  priority: P1
  type: Refactor
  status: open
  issue: '#967'
  last_synced: '2026-03-21T17:12:57Z'
  groomed: '2026-03-21'
  plan: plan/P794-sam-mcp-migration.yaml
---

## RT-ICA

<div><sub>2026-03-21T17:04:17Z</sub>

RT-ICA Snapshot: Replace uv run sam CLI calls with SAM MCP tool calls in workflow skills
Goal: Replace all uv run sam CLI patterns in workflow skills with SAM MCP tool calls so agents use MCP directly
Conditions:
1. Which workflow skills contain uv run sam patterns | Status: DERIVABLE
2. Which agents need SAM MCP tools in their frontmatter | Status: DERIVABLE
3. SAM MCP tool names and signatures | Status: AVAILABLE (sam_read, sam_status, sam_ready, sam_claim, sam_state, sam_list, sam_create, sam_update)
4. Whether agents already have MCP tool access | Status: DERIVABLE
5. CLI-to-MCP mapping (which CLI commands map to which MCP tools) | Status: DERIVABLE
AVAILABLE count: 1
DERIVABLE count: 4
MISSING count: 0
</div>

## Groomed (2026-03-21)

### Impact Radius

<div><sub>2026-03-21T17:10:55Z</sub>

### Code — Producers (SAM MCP server tools)
- `plugins/development-harness/mcp/` — SAM MCP server implementation providing sam_read, sam_status, sam_ready, sam_claim, sam_state, sam_list, sam_create, sam_update tools. No changes needed — these are the target interface.

### Code — Consumers (files using uv run sam CLI that must migrate to MCP)

**Agent files:**
- `plugins/python3-development/agents/code-reviewer.md:208,243,265` — uses `uv run sam create` for follow-up plan creation. Replace with `mcp__plugin_dh_sam__sam_create` tool calls. Add SAM MCP tools to agent frontmatter `tools:` field.
- `plugins/development-harness/agents/context-gathering.md:24,113` — uses `uv run sam read` and `uv run sam update`. Replace with `mcp__plugin_dh_sam__sam_read` and `mcp__plugin_dh_sam__sam_update`. Add SAM MCP tools to agent frontmatter `tools:` field.
- `plugins/development-harness/agents/swarm-task-planner.md:266` — uses `uv run sam create` with stdin pipe. Replace with `mcp__plugin_dh_sam__sam_create`. Add SAM MCP tools to agent frontmatter `tools:` field.
- `plugins/development-harness/agents/context-refinement.md:28,67,134` — uses `uv run sam read` and `uv run sam update` with --append-section. Replace with `mcp__plugin_dh_sam__sam_read` and `mcp__plugin_dh_sam__sam_update`. Add SAM MCP tools to agent frontmatter `tools:` field.

**Skill files:**
- `plugins/development-harness/skills/implement-feature/SKILL.md:34,44,60` — uses `uv run sam status` and `uv run sam ready`. Replace with `mcp__plugin_dh_sam__sam_status` and `mcp__plugin_dh_sam__sam_ready`.
- `plugins/development-harness/skills/start-task/SKILL.md:37,47,76` — uses `uv run sam state`, `uv run sam read`, `uv run sam claim`. Replace with `mcp__plugin_dh_sam__sam_state`, `mcp__plugin_dh_sam__sam_read`, `mcp__plugin_dh_sam__sam_claim`.
- `plugins/development-harness/skills/complete-implementation/SKILL.md:124,136` — uses `uv run sam status` and `uv run sam read`. Replace with `mcp__plugin_dh_sam__sam_status` and `mcp__plugin_dh_sam__sam_read`.
- `plugins/development-harness/skills/implementation-manager/SKILL.md:13,22,31,54,87,111,119,129,204,205` — uses all sam CLI commands extensively. Replace with corresponding MCP tool calls. Note: line 13 uses `!` backtick command substitution which cannot call MCP tools — keep CLI as fallback here.

### Documentation (will become stale)
- `.claude/rules/local-workflow.md:134,142,144,178,204,297-308,316` — canonical workflow documentation. 16 occurrences of `uv run sam`. Update to show MCP as primary, CLI as fallback.
- `plugins/development-harness/docs/workflow-architecture-diagram.md:100,122,210` — already shows both CLI and MCP. Update to make MCP primary.
- `plugins/development-harness/docs/TASK_FILE_FORMAT.md:16-27,55-62` — has CLI examples and MCP mapping table. Update CLI examples to MCP-first.

### Configuration / CI
- None identified. SAM MCP server is already configured in plugin MCP setup.

### Agent Instructions (instruct AI to use current interface)
- All agent files listed above contain instructions for agents to use `uv run sam` CLI. These instructions must be rewritten to use MCP tool calls.

### Systems Inventory
1. `plugins/python3-development/agents/code-reviewer.md` — consumer (sam create)
2. `plugins/development-harness/agents/context-gathering.md` — consumer (sam read, sam update)
3. `plugins/development-harness/agents/swarm-task-planner.md` — consumer (sam create)
4. `plugins/development-harness/agents/context-refinement.md` — consumer (sam read, sam update)
5. `plugins/development-harness/skills/implement-feature/SKILL.md` — consumer (sam status, sam ready)
6. `plugins/development-harness/skills/start-task/SKILL.md` — consumer (sam state, sam read, sam claim)
7. `plugins/development-harness/skills/complete-implementation/SKILL.md` — consumer (sam status, sam read)
8. `plugins/development-harness/skills/implementation-manager/SKILL.md` — consumer (all sam commands)
9. `.claude/rules/local-workflow.md` — documentation
10. `plugins/development-harness/docs/workflow-architecture-diagram.md` — documentation
11. `plugins/development-harness/docs/TASK_FILE_FORMAT.md` — documentation

### Ecosystem Completeness Checklist
- [ ] Every code producer updated or verified compatible — SAM MCP server already provides all tools
- [ ] Every code consumer migrated to new interface — 4 agents + 4 skills to update
- [ ] Every stale document updated — 3 docs to update
- [ ] Every agent instruction updated — 4 agents need instruction rewrites
- [ ] Old interface deprecated or removed (if replacing) — CLI becomes fallback, not removed
- [ ] CI/config files updated and validated — no CI changes needed
</div>

### Issue Classification

<div><sub>2026-03-21T17:11:28Z</sub>

**Type**: `procedural` — well-scoped refactor with clear before/after state. No root cause analysis needed.

**Rationale**: The CLI interface works correctly. The change is a migration from one working interface (CLI via Bash) to a better one (MCP tools directly). This is a procedural refactor — find patterns, replace with equivalent MCP calls, update documentation.
</div>

### Scope

<div><sub>2026-03-21T17:11:38Z</sub>

Replace `uv run sam` CLI patterns with `mcp__plugin_dh_sam__*` MCP tool calls in 4 agent files, 4 skill files, and 3 documentation files. Add SAM MCP tools to agent frontmatter `tools:` fields. CLI becomes fallback-only.

**In scope**: Agent files, skill SKILL.md files, workflow documentation
**Out of scope**: SAM MCP server implementation (already complete), hook scripts (use Python API not CLI), sam CLI itself (retained as fallback)
</div>

### Files

<div><sub>2026-03-21T17:11:55Z</sub>

**Agent files to modify (add MCP tools to frontmatter + rewrite CLI instructions):**
- `plugins/python3-development/agents/code-reviewer.md`
- `plugins/development-harness/agents/context-gathering.md`
- `plugins/development-harness/agents/swarm-task-planner.md`
- `plugins/development-harness/agents/context-refinement.md`

**Skill files to modify (rewrite CLI instructions to MCP):**
- `plugins/development-harness/skills/implement-feature/SKILL.md`
- `plugins/development-harness/skills/start-task/SKILL.md`
- `plugins/development-harness/skills/complete-implementation/SKILL.md`
- `plugins/development-harness/skills/implementation-manager/SKILL.md`

**Documentation files to update:**
- `.claude/rules/local-workflow.md`
- `plugins/development-harness/docs/workflow-architecture-diagram.md`
- `plugins/development-harness/docs/TASK_FILE_FORMAT.md`
</div>

### Dependencies

<div><sub>2026-03-21T17:12:04Z</sub>

- SAM MCP server must be running and registered — AVAILABLE (already configured in plugin)
- MCP tool signatures must match CLI functionality — VERIFIED (TASK_FILE_FORMAT.md documents the mapping)
- No blocking dependencies on other backlog items
</div>

### Priority

<div><sub>2026-03-21T17:12:15Z</sub>

P1 — reduces orchestrator context waste and eliminates unnecessary CLI intermediary for agent-to-SAM communication
</div>

### Decision

<div><sub>2026-03-21T17:12:37Z</sub>

CLI-to-MCP mapping (verified from TASK_FILE_FORMAT.md lines 55-62) --

uv run sam list maps to mcp__plugin_dh_sam__sam_list
uv run sam create maps to mcp__plugin_dh_sam__sam_create
uv run sam read maps to mcp__plugin_dh_sam__sam_read
uv run sam update maps to mcp__plugin_dh_sam__sam_update
uv run sam claim maps to mcp__plugin_dh_sam__sam_claim
uv run sam state maps to mcp__plugin_dh_sam__sam_state
uv run sam ready maps to mcp__plugin_dh_sam__sam_ready
uv run sam status maps to mcp__plugin_dh_sam__sam_status

Special case -- implementation-manager/SKILL.md line 13 uses command substitution at skill load time. MCP tools cannot be called at load time. This must remain CLI with a comment noting the exception.

Agent frontmatter tools to add -- each agent that needs SAM access gets the specific MCP tools it uses added to its tools field. Not all agents need all 8 tools.
</div>


## Fact-Check

<div><sub>2026-03-21T17:11:19Z</sub>

Claims checked: 3 | VERIFIED: 3 | REFUTED: 0 | INCONCLUSIVE: 0

1. **Claim: SAM MCP server provides equivalent operations to CLI**
   Status: VERIFIED
   Evidence: MCP server instructions list tools sam_read, sam_status, sam_ready, sam_claim, sam_state, sam_list, sam_create, sam_update. TASK_FILE_FORMAT.md lines 55-62 explicitly document the CLI-to-MCP mapping with "mirrors" notation.

2. **Claim: Workflow skills tell orchestrator to run uv run sam CLI commands**
   Status: VERIFIED
   Evidence: grep found uv run sam patterns in 4 skill files (implement-feature, start-task, complete-implementation, implementation-manager) and 4 agent files (code-reviewer, context-gathering, swarm-task-planner, context-refinement).

3. **Claim: Agents with MCP access can call SAM tools directly**
   Status: VERIFIED
   Evidence: Agent frontmatter supports `tools:` field for MCP tool access. Adding `mcp__plugin_dh_sam__sam_read` etc. to the tools list would grant agents direct access. Currently NO agents have SAM MCP tools in their frontmatter — all use CLI via Bash.
</div>

## RT-ICA

<div><sub>2026-03-21T17:12:57Z</sub>

RT-ICA Final -- Replace uv run sam CLI calls with SAM MCP tool calls in workflow skills
Goal -- Replace all uv run sam CLI patterns in workflow skills with SAM MCP tool calls so agents use MCP directly

Conditions:
1. Which workflow skills contain uv run sam patterns -- Snapshot: DERIVABLE -> Final: AVAILABLE -- Citation: grep found patterns in 4 skill files and 4 agent files (see Impact Radius)
2. Which agents need SAM MCP tools in their frontmatter -- Snapshot: DERIVABLE -> Final: AVAILABLE -- Citation: grep confirmed 4 agents (code-reviewer, context-gathering, swarm-task-planner, context-refinement) currently have NO SAM MCP tools in frontmatter
3. SAM MCP tool names and signatures -- Snapshot: AVAILABLE -> Final: AVAILABLE -- Citation: MCP server instructions + TASK_FILE_FORMAT.md lines 55-62
4. Whether agents already have MCP tool access -- Snapshot: DERIVABLE -> Final: AVAILABLE -- Citation: grep of agent frontmatter tools fields confirmed none have SAM MCP tools
5. CLI-to-MCP mapping -- Snapshot: DERIVABLE -> Final: AVAILABLE -- Citation: TASK_FILE_FORMAT.md lines 55-62 documents all 8 mappings with "mirrors" notation
6. (new) Command substitution limitation -- Final: AVAILABLE -- Citation: implementation-manager SKILL.md line 13 uses load-time command substitution which cannot call MCP tools. CLI fallback required for this case.

Changes from snapshot:
- Conditions 1,2,4,5: DERIVABLE -> AVAILABLE (resolved by grep and file analysis)
- Condition 6: (new) AVAILABLE (discovered during impact analysis)

AVAILABLE count: 6
DERIVABLE count: 0
MISSING count: 0
Decision: APPROVED
</div>