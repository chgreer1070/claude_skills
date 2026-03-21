# Feature Context: Redesign /work-milestone from TeamCreate to Worktree Agents

**Backlog item**: #970
**Status**: in-progress
**Priority**: P0
**Date**: 2026-03-21

## Problem Statement

The current `/work-milestone` skill is designed around TeamCreate: it spawns a team of parallel members, each running `/work-backlog-item --auto` in an isolated worktree. This design is architecturally broken because TeamCreate teammates lack the Agent tool.

The SAM pipeline used by `/work-backlog-item --auto` requires agent delegation at multiple stages (feature-researcher, codebase-analyzer, python-cli-design-spec, swarm-task-planner, implementation agents, quality gate agents). Without the Agent tool, none of these delegations can execute. The teammate receives the skill content inline but cannot act on it.

**Verified constraints (2026-03-21)**:

- TeamCreate teammates have: Skill, SendMessage, TaskCreate/Update/List/Get, ToolSearch, Bash, Read, Write, Edit, Glob, Grep, and all MCP tools.
- TeamCreate teammates lack: the Agent tool. Confirmed by ToolSearch and by official docs: "No nested teams: teammates cannot spawn their own teams or teammates."
- `context: fork` skills loaded by teammates do not fork -- content is injected inline into the teammate's context instead of spawning a separate subagent. Verified with `/plugin-creator:arl`.
- `disable-model-invocation` skills are blocked entirely for teammates.

**Consequence**: `/work-milestone` in its current form cannot execute any backlog item that uses the SAM pipeline. Since all items go through `/work-backlog-item --auto` which delegates to specialist agents, the entire skill is non-functional.

## Desired Outcome

A working `/work-milestone` that executes groomed milestones with parallel item-level workers, where each worker can run the full SAM pipeline including agent delegation.

The redesigned skill should preserve the following properties from the current design:

- **Wave-based dispatch**: items execute in dependency-ordered waves from the dispatch plan produced by `/groom-milestone`
- **Isolated worktrees**: each item's work happens in a git worktree, preventing cross-item interference
- **Integration branch**: all item branches merge into a shared integration branch before landing to main
- **Merge queue with conflict classification**: serialized merging with trivial/medium/heavy conflict handling and assign_back for heavy conflicts
- **Quality gates**: pre_merge and post_merge gate commands from the dispatch plan
- **Inter-worker awareness**: workers that share file domains coordinate to avoid incompatible design choices
- **Blocker escalation**: workers can signal blockers to the orchestrator for user escalation
- **Design decision persistence**: durable decisions written to GitHub issue bodies via backlog_update

The redesigned skill should eliminate:

- TeamCreate as the parallelism mechanism (replaced by orchestrator-dispatched worktree agents)
- The requirement for nested agent spawning (each worktree agent is a single-level worker)
- SendMessage as the coordination channel (worktree agents cannot send messages to each other or the orchestrator)

## Stakeholders

- **User (Jamie)**: invokes `/work-milestone {N}` to execute a groomed milestone. Expects parallel execution, blocker escalation, and quality-gated landing to main.
- **Orchestrator**: the main Claude Code session that reads the dispatch plan and coordinates execution. Currently delegates to TeamCreate; will need to dispatch worktree agents directly.
- **Worktree agents**: isolated Agent(isolation: "worktree") instances. Each handles one backlog item end-to-end. They have the Agent tool and can delegate to specialist subagents.
- **SAM pipeline**: the existing `/work-backlog-item --auto` flow (groom, plan, implement, complete) that runs inside each worker. Must execute unchanged.
- **Backlog MCP / SAM MCP**: servers that manage item state and task plan state. Used by both the orchestrator and workers.
- **GitHub Issues**: source of truth for item lifecycle, design decisions, and completion status.

## Risks

### R1: Loss of real-time inter-worker coordination

TeamCreate teammates can SendMessage to each other for domain overlap detection and design alignment. Worktree agents (spawned via Agent tool) cannot communicate with each other mid-execution. Two agents working on overlapping file domains may make incompatible design choices without knowing about each other.

### R2: Orchestrator context window exhaustion

The orchestrator dispatches and monitors all worktree agents. With TeamCreate, the orchestrator delegates monitoring to the team infrastructure. With direct Agent dispatch, the orchestrator's context window accumulates all agent outputs and coordination decisions across potentially many items and waves.

### R3: Merge queue timing

TeamCreate workers signal COMPLETE via SendMessage, allowing the orchestrator to process merges as workers finish. With worktree agents, the orchestrator must wait for Agent calls to return. If agents are dispatched in parallel (multiple Agent calls), the orchestrator receives results as each completes but cannot interleave merge operations while other agents are still running -- unless it uses background dispatch.

### R4: Error recovery across worktrees

A worktree agent that fails partway through leaves behind a partially-implemented worktree branch. The orchestrator must detect this, assess what was completed, and decide whether to retry, assign-back, or skip. The current design handles this via SendMessage heartbeats -- that channel is unavailable.

### R5: Dispatch plan contract change

The dispatch plan YAML produced by `/groom-milestone` may encode assumptions about TeamCreate (team member names, SendMessage payloads, blocker types). Changing the execution model may require corresponding changes to the dispatch plan schema and the groom-milestone skill.

### R6: Team member protocol invalidation

The current team-member-protocol.md (M1-M12 lifecycle) is built around SendMessage, peer announcements, domain overlap detection, and design alignment. All of these depend on inter-agent communication that worktree agents lack. The protocol must be redesigned or replaced.

## Dependencies

### Upstream (things this redesign depends on)

- **`/groom-milestone` dispatch plan**: the dispatch plan format may need schema changes to support the new execution model. Currently at `plugins/development-harness/skills/groom-milestone/SKILL.md`.
- **`dispatch_schema` module**: provides `analyze_impact_radius_conflicts()`, `write_dispatch_plan()`, and `validate_plan_integrity()`. Schema changes may be needed.
- **`/work-backlog-item --auto`**: the per-item execution flow. Must work unchanged inside a worktree agent. Currently uses the SAM pipeline with agent delegation.
- **`Agent(isolation: "worktree")` capability**: Claude Code's worktree isolation feature. Must support branching from a specified base branch (integration branch), not just main.
- **`github_branches.py`**: integration branch creation and management. Already exists and is functional.

### Downstream (things that depend on this redesign)

- **#921 (cross-item dependency analysis)**: blocked by this redesign. Cannot analyze cross-item dependencies if items cannot execute in parallel.
- **Milestone orchestration flow**: the end-to-end flow from `/groom-milestone` through `/work-milestone` to `/complete-milestone`.
- **merge-queue-protocol.md**: the merge queue protocol references TeamCreate and SendMessage. Must be updated.
- **team-member-protocol.md**: the M1-M12 lifecycle protocol is entirely TeamCreate-based. Must be redesigned or replaced.

## Open Questions

### Q1: How do worktree agents coordinate on shared domains?

TeamCreate members use SendMessage for real-time domain overlap detection and design alignment. Worktree agents have no inter-agent communication channel. Options include: pre-dispatch coordination by the orchestrator, serializing conflicting items into separate waves, or accepting that conflicts will be caught at merge time. Each option has different trade-offs for parallelism, merge conflict frequency, and design coherence.

### Q2: What is the parallelism model for Agent(isolation: "worktree") calls?

Can the orchestrator launch multiple Agent(isolation: "worktree") calls simultaneously? If so, how does it receive and process completions? Does it block until all return, or can it process them as they arrive? The answer affects merge queue timing and error recovery.

### Q3: Can Agent(isolation: "worktree") branch from a non-main base?

The current design requires worktree agents to branch from the integration branch (`milestone/{N}-{slug}`), not from main. If worktree isolation only supports branching from the current branch or main, an alternative approach is needed.

### Q4: How does the orchestrator detect partial failures?

If a worktree agent crashes or times out, the orchestrator needs to know what was completed. Without SendMessage heartbeats, the orchestrator must inspect the worktree branch state (commits, task file status) after agent termination. What signals indicate partial vs. complete work?

### Q5: Should the dispatch plan schema change?

The dispatch plan currently encodes wave assignments and conflict groups. Should it also encode the new execution model's parameters (e.g., which items can safely run in parallel without pre-coordination, vs. which require serialization due to domain overlap)? Or should the orchestrator make these decisions at execution time using the conflict group data?

### Q6: What happens to design decision persistence?

Currently, workers persist design decisions to GitHub issue bodies via `backlog_update` and broadcast them to peers via SendMessage. With worktree agents, `backlog_update` still works (agents have MCP access), but there is no broadcast. Should the orchestrator read design decisions from issues between agent completions and relay relevant ones to subsequent agents?

### Q7: How does the merge queue interact with parallel agent dispatch?

With TeamCreate, the orchestrator can merge a completed worker's branch while other workers continue. With parallel Agent calls, the orchestrator may be blocked waiting for Agent returns. Should merges happen after each agent returns (sequential within a wave), or should all agents in a wave complete before any merging begins (batch merge)?

## Source Material

- Backlog item #970: verified teammate capability limitations and proposed architecture direction
- Current `/work-milestone`: `plugins/development-harness/skills/work-milestone/SKILL.md`
- `/groom-milestone`: `plugins/development-harness/skills/groom-milestone/SKILL.md`
- Team member protocol: `plugins/development-harness/skills/work-milestone/references/team-member-protocol.md`
- Merge queue protocol: `plugins/development-harness/skills/work-milestone/references/merge-queue-protocol.md`
- Teammate capabilities: `.claude/projects/-home-ubuntulinuxqa2-repos-claude-skills/memory/project_teammate_capabilities.md`
- Claude Code sub-agents docs: verified 2026-03-21, confirms "No nested teams" constraint
