---
name: Redesign /work-milestone from TeamCreate to orchestrator-dispatched worktree agents
description: "Redesign /work-milestone to use orchestrator-dispatched worktree agents instead of TeamCreate teammates.\n\nVerified 2026-03-21: teammates spawned via TeamCreate lack the Agent tool and cannot spawn sub-agents. context:fork skills fall back to inline injection. This means the current /work-milestone design (spawn teammates that each run /work-backlog-item --auto) cannot work — the SAM pipeline requires agent delegation.\n\nNew architecture:\n1. Orchestrator creates integration branch (github_branches.py already exists)\n2. Orchestrator reads dispatch plan YAML from /groom-milestone\n3. For each wave, orchestrator spawns parallel Agent(isolation: 'worktree') calls — one per item\n4. Each worktree agent loads skills inline, does the work directly, commits to its worktree branch\n5. Orchestrator merges each worktree branch into integration branch\n6. After all waves complete, orchestrator lands integration branch to main\n\nNo TeamCreate needed. No nested agent spawning. Each worktree agent is a single-level worker.\n\nPre-req for milestone orchestration — blocks #921 (cross-item dependency analysis) and the overall milestone execution flow.\n\nEvidence:\n- Teammate Agent tool absence: verified via ToolSearch in test (returned only SendMessage, TaskCreate, TaskUpdate)\n- context:fork inline fallback: verified with /plugin-creator:arl — content injected inline, no fork\n- Official docs confirm: 'No nested teams: teammates cannot spawn their own teams or teammates'\n- Memory: project_teammate_capabilities.md"
metadata:
  topic: redesign-work-milestone-from-teamcreate-to-orchestrator-disp
  source: 'Session 2026-03-21: teammate capability testing revealed Agent tool unavailable to team members'
  added: '2026-03-21'
  priority: P0
  type: Refactor
  status: open
  issue: '#970'
  last_synced: '2026-03-21T21:43:17Z'
  groomed: '2026-03-21'
  plan: plan/P970-redesign-work-milestone-worktree-agents.yaml
---

## RT-ICA

<div><sub>2026-03-21T21:39:09Z</sub>

RT-ICA Snapshot: Redesign /work-milestone from TeamCreate to orchestrator-dispatched worktree agents
Goal: Replace TeamCreate teammate dispatch with Agent(isolation: "worktree") calls so each worker can run the full SAM pipeline
Conditions:
1. Teammate Agent tool absence verified | Status: AVAILABLE | Evidence: ToolSearch test 2026-03-21
2. Current /work-milestone SKILL.md content and structure | Status: DERIVABLE
3. Agent(isolation: "worktree") API behavior and lifecycle | Status: AVAILABLE | Evidence: docs read this session
4. Integration branch management functions exist (github_branches.py) | Status: AVAILABLE | Evidence: #919 resolved
5. Dispatch plan YAML schema and fields | Status: DERIVABLE
6. Worktree merge-back mechanism | Status: AVAILABLE | Evidence: docs read this session
7. How /work-backlog-item --auto runs inside a worktree agent | Status: DERIVABLE
8. What TeamCreate-specific code exists in work-milestone that needs replacing | Status: DERIVABLE
AVAILABLE count: 4
DERIVABLE count: 4
MISSING count: 0
Decision: APPROVED (all conditions AVAILABLE or DERIVABLE)
</div>

## Fact-Check

<div><sub>2026-03-21T21:39:55Z</sub>

**FACT-CHECK FINDINGS — All claims verified against primary sources:**

**Claim 1: "teammates spawned via TeamCreate lack the Agent tool"**
- **Status:** VERIFIED
- **Evidence:** project_teammate_capabilities.md line 13: "Tools teammates LACK: Agent tool. Teammates cannot spawn sub-agents or other teammates. Confirmed by ToolSearch returning no Agent tool, and by official docs: 'No nested teams: teammates cannot spawn their own teams or teammates.'"
- **Verification date:** 2026-03-21 (stated in memory file)

**Claim 2: "context:fork skills fall back to inline injection"**
- **Status:** VERIFIED
- **Evidence:** project_teammate_capabilities.md lines 17-18: "context: fork skills: fork does NOT execute — content is injected inline into the teammate's context instead of spawning a separate subagent. Verified with /plugin-creator:arl (has `context: fork`, no `disable-model-invocation`). The teammate reported: 'The skill content was injected inline into MY conversation context. It did NOT spawn a separate agent.'"
- **Verification date:** 2026-03-21

**Claim 3: "github_branches.py already exists"**
- **Status:** VERIFIED
- **Evidence:** Glob found: `/home/ubuntulinuxqa2/repos/claude_skills/plugins/development-harness/backlog_core/github_branches.py`
- **Verification method:** Glob pattern match on `plugins/development-harness/backlog_core/github_branches.py`

**Claim 4: "the SAM pipeline requires agent delegation"**
- **Status:** VERIFIED
- **Evidence:** implement-feature SKILL.md (lines 63-78) explicitly routes each ready task: "For each ready task: Route to the agent named in the task's `agent` field... Launch the agent with a prompt that invokes `start-task`" — the skill uses `Agent` tool delegation throughout the progress loop
- **Verification method:** Read implement-feature SKILL.md directly

**Claim 5: "Agent(isolation: 'worktree') creates isolated working copy"**
- **Status:** INCONCLUSIVE — Official docs claim verified this session (as stated in system reminder), but worktree settings not found in project configuration
- **Evidence:**
  - Glob for settings: Found `.claude/settings.json` and `.claude/settings.local.json`
  - Neither file contains `worktree` field or configuration
  - User notes reference "Agent(isolation: 'worktree')" in project_teammate_capabilities.md line 22, but no local worktree configuration discovered
- **Gap:** The claim references Claude Code feature documented externally, not configured in this project. Official docs confirm capability; project does not yet declare worktree settings.

**Summary:** Claims 1-4 fully verified against project source files. Claim 5 references official Claude Code capability (verified from docs as noted in system context) but has no local project configuration yet.
</div>

## Groomed (2026-03-21)


### Impact

<div><sub>2026-03-21T00:00:00Z</sub>

<div><sub>2026-03-21T21:40:35Z</sub>
</div>

<div><sub>2026-03-21T21:41:43Z</sub>

From the Impact Radius analysis:

**Primary (breaking change):**
- `plugins/development-harness/skills/work-milestone/SKILL.md` — Steps 4-7 (TeamCreate spawn, SendMessage monitoring, wave dispatch) are replaced entirely

**Dispatch schema (conditional, minor):**
- `dispatch_schema/core/models.py`, `yaml_reader.py`, `yaml_writer.py`, `validator.py` — Only if new agent/isolation fields are added to the dispatch plan format

**References and documentation:**
- `work-milestone/references/team-member-protocol.md` — Peer discovery and SendMessage target routing changes
- `work-milestone/references/merge-queue-protocol.md` — Agent completion signaling note
- `groom-milestone/references/dispatch-plan-schema.md` — Document any new dispatch plan fields

**Workflow documentation:**
- `.claude/rules/local-workflow.md` — Add forward reference clarifying milestone vs SAM phase 2 boundary

**Test suite (conditional):**
- `tests/test_dispatch_schema/` (4 files) — Only if schema changes
- `tests/test_scenarios.py` — Integration test for new dispatch pattern

**Not affected:**
- Backlog MCP server, GitHub branch APIs, quality gate execution spec, SAM task file schema, all agent files
</div>

### Reproducibility

<div><sub>2026-03-21T21:41:34Z</sub>

The failure is deterministic and observable in any TeamCreate session:

1. Create a team with TeamCreate
2. Send a teammate a message asking it to call the Agent tool (e.g., "call Agent to spawn a subagent")
3. The teammate responds with only the tools it has: SendMessage, TaskCreate, TaskUpdate, TaskList, TaskGet — no Agent tool
4. Attempt to invoke `Skill(skill="work-backlog-item", args="--auto")` inside the teammate — the SAM pipeline's implement-feature step internally calls Agent for each task; the teammate cannot do this

Reference: `.claude/memory/project_teammate_capabilities.md` — verified via ToolSearch on 2026-03-21; ToolSearch returned no Agent tool in teammate context. Official docs confirm: "No nested teams: teammates cannot spawn their own teams or teammates."

The current `/work-milestone` SKILL.md Step 5 dispatches one TeamCreate member per parallel wave item, each expected to run `/work-backlog-item --auto`. Because `/work-backlog-item` → `/implement-feature` → Agent(task delegation) internally, the teammate hits a hard wall on the first task delegation attempt.
</div>

### Priority

<div><sub>2026-03-21T21:41:37Z</sub>

P0 — Blocks milestone orchestration entirely.

`/work-milestone` is the execution engine for the milestone workflow. Until it can actually run `/work-backlog-item --auto` per item, no milestone can be executed. This blocks:
- #921 (cross-item dependency analysis) — depends on a working execution loop to validate dependency handling
- The overall milestone execution flow in production use

No workaround exists: TeamCreate teammates structurally lack the Agent tool. The architecture must change.
</div>

### Scope

<div><sub>2026-03-21T21:41:54Z</sub>

**In scope:**
- Rewrite `work-milestone/SKILL.md` dispatch loop (Steps 4-7): replace TeamCreate + SendMessage with orchestrator-dispatched `Agent(isolation: "worktree")` calls, one per wave item, in parallel
- Update `work-milestone/references/team-member-protocol.md` to remove TeamCreate peer discovery patterns and clarify Agent isolation lifecycle
- Add completion-signaling note to `work-milestone/references/merge-queue-protocol.md`
- Update `groom-milestone/references/dispatch-plan-schema.md` if any new dispatch plan fields are introduced
- Update `.claude/rules/local-workflow.md` with forward reference distinguishing milestone dispatch from SAM phase 2
- Conditional dispatch schema updates (models, reader, writer, validator) only if schema additions are required

**Out of scope:**
- Changes to `dispatch_schema` data model unless schema additions are strictly required by the new dispatch pattern
- Merge queue protocol changes beyond the completion-signaling note
- Changes to `groom-milestone` dispatch plan generation logic
- Any changes to backlog MCP server, GitHub branch APIs, SAM schema, or agent files
- Cross-item dependency analysis (#921) — separate item
- Merge queue implementation — separate concern
</div>

### Expected Behavior

<div><sub>2026-03-21T21:42:01Z</sub>

After this change, `/work-milestone` operates as follows:

1. Orchestrator reads the dispatch plan YAML produced by `/groom-milestone`
2. Orchestrator creates (or reuses) the integration branch via `github_branches.py`
3. For each wave in the dispatch plan, orchestrator identifies all parallel items in the wave
4. Orchestrator launches one `Agent(isolation: "worktree")` call per parallel item simultaneously — no TeamCreate, no teammate spawning
5. Each worktree agent receives its backlog item reference, loads the required skills inline, and runs `/work-backlog-item --auto` independently
6. Each worktree agent has full Agent tool access and can delegate to the SAM pipeline without restriction
7. Each worktree agent commits its changes to its worktree branch on completion
8. Orchestrator detects completion of all worktree agents in the wave (via Agent call return, not SendMessage)
9. Orchestrator merges each completed worktree branch into the integration branch
10. Steps 3-9 repeat for each subsequent wave, respecting wave ordering
11. After all waves complete, orchestrator lands the integration branch to main

No TeamCreate. No SendMessage team coordination. Each worktree agent is a single-level worker with no need to spawn further sub-agents for milestone coordination.
</div>

### Acceptance Criteria

<div><sub>2026-03-21T21:42:16Z</sub>

- [ ] `work-milestone/SKILL.md` dispatch loop (Steps 4-7) uses `Agent(isolation: "worktree")` — one call per parallel wave item — with no TeamCreate, SendMessage team, or teammate references remaining
- [ ] The rewritten SKILL.md can be read from top to bottom without requiring knowledge of TeamCreate or teammate concepts to understand the dispatch flow
- [ ] Each worktree agent is invoked with: backlog item reference, skills to load, and instructions to run `/work-backlog-item --auto`
- [ ] Each worktree agent has full Agent tool access (verified by the fact that Agent(isolation: "worktree") agents are first-class subagents, not teammates)
- [ ] Orchestrator merges completed worktree branches into integration branch after each wave completes — merge step is explicit in SKILL.md
- [ ] Dispatch plan YAML produced by `/groom-milestone` is consumed correctly by the new dispatch pattern — orchestrator reads wave items and routes them without TeamCreate
- [ ] `work-milestone/references/team-member-protocol.md` updated: TeamCreate-specific peer discovery patterns removed or replaced with Agent isolation equivalents
- [ ] `work-milestone/references/merge-queue-protocol.md` has a note clarifying completion signaling is via Agent call return, not SendMessage COMPLETE
- [ ] `.claude/rules/local-workflow.md` updated with forward reference distinguishing milestone phase 2 (worktree agent dispatch) from SAM phase 2 (implement-feature task loop)
- [ ] If dispatch schema fields are added: `groom-milestone/references/dispatch-plan-schema.md` documents them; schema tests updated
- [ ] `grep -r "TeamCreate\|SendMessage.*team\|teammate" plugins/development-harness/skills/work-milestone/` returns no results in the rewritten SKILL.md
</div>

### Files

<div><sub>2026-03-21T21:42:21Z</sub>

**Primary change (must modify):**
- `plugins/development-harness/skills/work-milestone/SKILL.md` — Replace dispatch loop Steps 4-7

**Reference updates (must modify):**
- `plugins/development-harness/skills/work-milestone/references/team-member-protocol.md`
- `plugins/development-harness/skills/work-milestone/references/merge-queue-protocol.md`
- `.claude/rules/local-workflow.md`

**Conditional (modify only if dispatch schema changes):**
- `plugins/development-harness/dispatch_schema/core/models.py`
- `plugins/development-harness/dispatch_schema/readers/yaml_reader.py`
- `plugins/development-harness/dispatch_schema/writers/yaml_writer.py`
- `plugins/development-harness/dispatch_schema/core/validator.py`
- `plugins/development-harness/skills/groom-milestone/references/dispatch-plan-schema.md`
- `plugins/development-harness/tests/test_dispatch_schema/test_models.py`
- `plugins/development-harness/tests/test_dispatch_schema/test_validator.py`
- `plugins/development-harness/tests/test_dispatch_schema/test_yaml_reader.py`
- `plugins/development-harness/tests/test_dispatch_schema/test_yaml_writer.py`

**Reference (read but do not modify):**
- `plugins/development-harness/backlog_core/github_branches.py` — integration branch management, used as-is
- `.claude/memory/project_teammate_capabilities.md` — evidence of teammate limitations
</div>

### Resources

<div><sub>2026-03-21T21:42:31Z</sub>

**Evidence (verified this session):**
- `.claude/memory/project_teammate_capabilities.md` — primary evidence file; documents ToolSearch test result, context:fork inline fallback test, and official docs quote

**Official documentation:**
- `https://docs.anthropic.com/en/docs/claude-code/sub-agents.md` — Agent tool, isolation modes, worktree lifecycle; confirmed "No nested teams" constraint

**Existing implementation to build on:**
- `plugins/development-harness/backlog_core/github_branches.py` — integration branch creation/management (verified present)
- `plugins/development-harness/skills/work-milestone/SKILL.md` — current implementation to replace
- `plugins/development-harness/skills/groom-milestone/SKILL.md` — dispatch plan producer; defines YAML consumed by work-milestone

**Dispatch schema:**
- `plugins/development-harness/dispatch_schema/` — full schema package; wave/item structure defined in `core/models.py`
</div>

### Dependencies

<div><sub>2026-03-21T21:42:36Z</sub>

**Resolved (no longer blocking):**
- #919 (integration branch management) — RESOLVED; `github_branches.py` exists and provides the branch creation/merge functions needed by the new orchestrator dispatch loop

**Active dependencies:**
- `dispatch_schema` package — must be stable before modifying dispatch plan consumption logic; confirm current schema supports wave ordering and parallel item identification
- `/groom-milestone` skill — must produce valid dispatch plan YAML before this skill can be fully tested end-to-end; groom-milestone is a prerequisite for integration testing

**Blocked by this item:**
- #921 (cross-item dependency analysis) — depends on a working execution loop to validate dependency handling semantics
</div>

### Effort

<div><sub>2026-03-21T21:42:40Z</sub>

Medium — 1 session.

The scope is well-defined: one SKILL.md rewrite (the dispatch loop, approximately 30-40 lines replacing Steps 4-7), two reference doc updates (team-member-protocol, merge-queue-protocol), and one workflow doc update (local-workflow.md). No new infrastructure is introduced — Agent(isolation: "worktree") is an existing Claude Code capability.

Conditional dispatch schema work is minor and only triggers if schema additions are required; current wave/item structure likely suffices.

The primary complexity is in the SKILL.md rewrite: getting the parallel Agent dispatch, wave ordering, and merge-back steps expressed precisely enough that an orchestrator executes them correctly. This is SKILL.md authoring work, not code development.
</div>


## Impact Radius — Redesign /work-milestone from TeamCreate to Agent(isolation: "worktree")

### Code — Producers (Files that implement dispatch plan execution)

**Primary Implementation:**
- `plugins/development-harness/skills/work-milestone/SKILL.md` — **BREAKING CHANGE.** Steps 4-7 (TeamCreate spawn, SendMessage monitoring, wave dispatch) must be replaced with Agent(isolation: "worktree") calls per item. Lines 42-72 of flowchart. Currently hardcoded: "Step 5: TeamCreate / One member per parallel item."

**Dispatch Plan Schema (unchanged structure, but dispatch plan model may require new field):**
- `plugins/development-harness/dispatch_schema/core/models.py` — Check if WaveItem or DispatchPlan models need `agent_name` or `isolation` fields to specify Agent(isolation: "worktree") vs other isolation modes
- `plugins/development-harness/dispatch_schema/__init__.py` — Entry point, likely needs no change if schema additions are backward-compatible
- `plugins/development-harness/dispatch_schema/readers/yaml_reader.py` — May need to handle new fields from dispatch plan YAML if added
- `plugins/development-harness/dispatch_schema/writers/yaml_writer.py` — May need to output new fields to dispatch plan YAML if added

**Supporting Modules:**
- `plugins/development-harness/dispatch_schema/core/validator.py` — Validates dispatch plan integrity. If schema changes, validator may need updates.
- `plugins/development-harness/dispatch_schema/gates.py` — Quality gate execution. No direct change needed unless gate runner moves inside worktree agents.

### Code — Consumers (Files that read or depend on work-milestone behavior)

**Direct Consumers:**
- `plugins/development-harness/skills/groom-milestone/SKILL.md` — Produces dispatch plans consumed by work-milestone. No functional change needed, but may need to document new `isolation` or `agent_name` fields in dispatch plan schema reference.
- `plugins/development-harness/skills/groom-milestone/references/dispatch-plan-schema.md` — Documents dispatch plan YAML structure. Will need to document new fields (if any) and removal of TeamCreate-specific sections.

**Backlog Core Server:**
- `plugins/development-harness/backlog_core/server.py` — Provides backlog_list_issues, backlog_update, and backlog_view APIs used by work-milestone workers. No change needed if API signatures stay stable. May need to verify timestamp handling for design decision persistence.

**Test Suite:**
- `plugins/development-harness/tests/test_dispatch_schema/test_models.py` — Tests dispatch plan model structure. Will need updates if schema changes (e.g., new agent or isolation fields).
- `plugins/development-harness/tests/test_dispatch_schema/test_validator.py` — Tests plan integrity validation. Updates needed if validation rules change.
- `plugins/development-harness/tests/test_dispatch_schema/test_yaml_reader.py` — Tests YAML deserialization. Updates if new fields added.
- `plugins/development-harness/tests/test_dispatch_schema/test_yaml_writer.py` — Tests YAML serialization. Updates if new fields added.
- `plugins/development-harness/tests/test_dispatch_schema/test_gates.py` — Tests quality gate execution. May need updates if gate runner refactors into worktree agents.
- `plugins/development-harness/tests/test_impact_radius_conflicts.py` — Tests conflict analysis. No direct change needed.
- `plugins/development-harness/tests/test_scenarios.py` — Integration tests. May need updates for new agent-based dispatch workflow.
- `plugins/development-harness/tests/test_operations_sam.py` — Tests SAM-related operations. No direct change needed.
- `plugins/development-harness/tests/test_live_validation.py` — Live validation testing. May need to verify worker isolation semantics.

### Documentation — Skill and Protocol References

**Skill Frontmatter & Description:**
- `plugins/development-harness/skills/work-milestone/SKILL.md` line 3 (description) — **Must update.** Currently: "... spawns TeamCreate teams per wave..." → Will change to: "... spawns Agent(isolation: worktree) per wave per parallel item..."

**Worker Protocol:**
- `plugins/development-harness/skills/work-milestone/references/team-member-protocol.md` — **Will need significant updates.** Currently documents:
  - Lines 2-3: Team member lifecycle in worktree (COMPATIBLE — isolation: worktree still applies)
  - Lines 85-128: SendMessage patterns for inter-worker communication (COMPATIBLE — Agent isolation doesn't block SendMessage)
  - Lines 85: "Announce to team via SendMessage" — SendMessage calls remain valid, routing target may change from team_name to orchestrator-pending peer discovery mechanism
  - Lines 116-128: Domain overlap detection and peer messaging — COMPATIBLE with agent isolation; may need to clarify how workers discover peers when not in a TeamCreate team
  - Domain Detection flowchart (lines 107-118) — COMPATIBLE; domain extraction logic unchanged
  - Blocker Types table (lines 125-133) — COMPATIBLE; blocker escalation via SendMessage still valid

**Merge Queue Protocol:**
- `plugins/development-harness/skills/work-milestone/references/merge-queue-protocol.md` — **Likely unchanged.** Merge slot lifecycle, conflict classification, and assign_back procedure are orthogonal to how workers are spawned. Verification: no TeamCreate or SendMessage references in this file. Single assumption: "signal COMPLETE" will now be via Agent completion signal, not SendMessage. Add note clarifying this.

**Dispatch Plan Schema Reference:**
- `plugins/development-harness/skills/groom-milestone/references/dispatch-plan-schema.md` — **Will need updates.** If groom-milestone produces a new field (agent name, isolation mode), document it here.

### Documentation — Architecture & Workflow

**Development Harness Plugin CLAUDE.md:**
- `plugins/development-harness/CLAUDE.md` — Documents 7-stage SAM pipeline. No direct reference to work-milestone; no change needed.

**Local Workflow Rules:**
- `.claude/rules/local-workflow.md` — **Comprehensive update needed.** Documents full Phase 2 execution loop. Current content:
  - Line 32 (Execution Loop, step 3): "Route to the agent named in the task's **Agent** field" — This applies to SAM phase 2, NOT milestone phase 2. Clarify boundary.
  - Phase 2a /start-task references TeamCreate implicitly (mentions "SubagentStop hook" and "team members"). **No change needed to Phase 2a** — it describes task execution, not milestone wave dispatch.
  - No explicit mention of milestone dispatch in local-workflow.md; primarily documents SAM task file format and execution. Will not break, but may need a forward reference to milestone skills.

**Research & Insights:**
- `research/insights/2026-03-21-zeroboot-improvements.md` — Contains references to worktree patterns and agent isolation. May be informational; no operational change required.
- `.claude/backlog/p0-redesign-work-milestone-from-teamcreate-to-orchestrator-disp.md` — **This is the backlog item itself.** Will be resolved by implementation.

### Configuration & CI

**Plugin Configuration:**
- `plugins/development-harness/plugin.json` — Likely contains agent/skill declarations. No change needed unless new agents are created (unlikely; refactoring uses existing Agent tool).

**Test Configuration:**
- `plugins/development-harness/tests/conftest.py` — Pytest fixtures. May need to set up Agent mock or isolation mode testing. Check what fixtures are currently used for dispatch plan tests.

**Pre-Commit Hooks:**
- `.pre-commit-config.yaml` (repo root) — No change needed unless new linting rules added.

### Agent Instructions & Templates

**Generic Stage Agent:**
- `plugins/development-harness/agents/generic-stage-agent.md` — Generic agent used by harness. No direct change needed; work-milestone may use this or a custom agent wrapper.

**Agent Files (no direct changes expected, but verify references):**
- `plugins/development-harness/agents/*.md` — Search for SendMessage, TeamCreate, team_name, wave patterns. **Found:** No SendMessage or TeamCreate references in agent files. Agents are executed BY work-milestone, not coordinating peers directly.

### Systems Inventory — Affected Modules

**Core Systems (No change expected):**
- SAM schema (core/dependencies.py, core/models.py for task files) — Orthogonal to milestone dispatch
- Backlog MCP server — Used for persistence, not changed
- GitHub branch APIs — Used for integration branch management, not changed
- Quality gate execution — May move into worktree agent, but gate command spec unchanged

**New Requirements (Introduced by redesign):**
1. **Agent(isolation: "worktree") capability** — Verify Claude Code supports this. If not, block task until feature exists.
2. **Peer discovery mechanism for SendMessage** — Currently workers announce via TeamCreate's team_name. New mechanism needed for workers to find peer SendMessage targets when isolated in separate worktrees.
3. **Orchestrator dispatch loop** — Replace TeamCreate spawn logic with Agent(isolation: "worktree") loop in work-milestone SKILL.md.
4. **Agent completion signaling** — Currently team members signal via SendMessage COMPLETE. New mechanism needed to signal completion from isolated agent back to orchestrator.

### Summary of Required Changes

**Files with code changes (5-7):**
- work-milestone SKILL.md — Major: replace dispatch loop
- dispatch_schema models.py (conditional) — Minor: add agent/isolation fields if needed
- dispatch_schema readers/writers (conditional) — Minor: handle new fields
- dispatch_schema validator.py (conditional) — Minor: validate new fields
- groom-milestone SKILL.md (minor) — Update description if dispatch schema changes

**Files with documentation updates (6-8):**
- team-member-protocol.md — Clarify peer discovery in non-TeamCreate scenario
- merge-queue-protocol.md — Add note on agent completion signaling
- dispatch-plan-schema.md — Document any new fields
- groom-milestone SKILL.md — Update references if schema changes
- local-workflow.md (optional) — Add clarification on milestone vs SAM phases
- work-milestone SKILL.md description — Update to remove TeamCreate reference

**Files with test updates (7-8):**
- test_dispatch_schema/test_models.py — Updates for new schema (if any)
- test_dispatch_schema/test_validator.py — Updates for new schema (if any)
- test_dispatch_schema/test_yaml_reader.py — Updates for new schema (if any)
- test_dispatch_schema/test_yaml_writer.py — Updates for new schema (if any)
- test_scenarios.py — May need integration test for new agent dispatch
- conftest.py — May need fixtures for Agent mock

**Files that remain unchanged:**
- Backlog core modules (server.py, operations.py)
- Quality gate execution (gates.py) — gate spec stays same; executor may move
- merge-queue-protocol.md — conflict handling logic unchanged
- local-workflow.md Phase 2a — SAM execution, separate from milestone phase 2
- All agent files (generic-stage-agent.md, etc.) — used BY harness, not modified


</div>

## RT-ICA

<div><sub>2026-03-21T21:43:17Z</sub>

RT-ICA Final: Redesign /work-milestone from TeamCreate to orchestrator-dispatched worktree agents
Goal: Replace TeamCreate teammate dispatch with Agent(isolation: "worktree") calls
Conditions:
1. Teammate Agent tool absence | Snapshot: AVAILABLE → Final: AVAILABLE | Evidence: ToolSearch test + memory file
2. Current work-milestone SKILL.md | Snapshot: DERIVABLE → Final: AVAILABLE | Evidence: impact-analyst read and mapped Steps 4-7
3. Agent(isolation: "worktree") API | Snapshot: AVAILABLE → Final: AVAILABLE | Evidence: official docs
4. github_branches.py exists | Snapshot: AVAILABLE → Final: AVAILABLE | Evidence: Glob match confirmed
5. Dispatch plan YAML schema | Snapshot: DERIVABLE → Final: AVAILABLE | Evidence: impact-analyst mapped dispatch_schema package
6. Worktree merge-back mechanism | Snapshot: AVAILABLE → Final: AVAILABLE | Evidence: official docs
7. work-backlog-item in worktree agent | Snapshot: DERIVABLE → Final: AVAILABLE | Evidence: fact-checker verified implement-feature uses Agent delegation
8. TeamCreate code to replace | Snapshot: DERIVABLE → Final: AVAILABLE | Evidence: impact-analyst identified TeamCreate spawn loop in Steps 4-7
Changes from snapshot:
- Conditions 2, 5, 7, 8: DERIVABLE → AVAILABLE (resolved by impact-analyst and fact-checker)
- Claim 5 (worktree isolation): INCONCLUSIVE on local config but feature is documented and available
AVAILABLE count: 8
DERIVABLE count: 0
MISSING count: 0
Decision: APPROVED
</div>