# Context Manifest: P970 — Redesign /work-milestone from TeamCreate to Worktree Agents

## How the Current /work-milestone Architecture Works

The /work-milestone skill executes a groomed milestone by reading a dispatch plan (produced by /groom-milestone) and coordinating parallel workers across multiple waves. When invoked with a milestone number, the orchestrator loads the dispatch plan YAML, which contains waves of backlog items, conflict groups serializing overlapping domains, and quality gate commands.

For each wave, the orchestrator spawns a TeamCreate team with one member per item. Each teammate runs /work-backlog-item --auto, which internally invokes the SAM pipeline. This pipeline reads or creates a SAM task plan, delegates to specialist agents (feature-researcher, architect, implementation agents, quality gate agents), and handles status tracking.

The critical architectural constraint discovered on 2026-03-21 is that TeamCreate teammates lack the Agent tool. Official Claude Code docs state: "Subagents cannot spawn other subagents." When a teammate attempts to run /work-backlog-item --auto, it fails on the first Agent delegation call. Skill content is injected inline into the teammate's context (verified via /plugin-creator:arl), but without the Agent tool, delegation cannot execute.

## The Redesign: Direct Execution Without Agent Nesting

The architect spec determines that Agent(isolation="worktree") subagents also cannot nest Agent calls. The solution is direct task execution using skill loading and inline task execution. The orchestrator pre-decomposes each item by reading its SAM task plan via sam_read() and building a complete agent prompt that includes the full task list with acceptance criteria. The worktree agent loads required skills, reads tasks from the prompt, and executes each task sequentially without delegating to subagents.

Why inter-worker communication is no longer needed: The dispatch plan from /groom-milestone already serializes items touching overlapping file domains into separate waves via conflict group analysis. Items within the same wave are guaranteed non-overlapping. Workers in the same wave do not need to coordinate at runtime. Cross-wave coordination is handled by the orchestrator through discovery relay, where after a wave completes, the orchestrator collects commit messages, changed files, and design notes from agents and feeds them into the next wave's agent prompts.

## Component Architecture from Architect Spec

### Component 1: Wave Dispatch via Agent(isolation="worktree")

The orchestrator iterates through waves. For each wave, it spawns one Agent(isolation="worktree") call per item, all launching in parallel. Pre-dispatch, the orchestrator reads each item's SAM task plan via sam_read(plan="P{N}"), reads the groomed description via backlog_view(selector="#{issue}"), extracts skills from task metadata, and assembles an agent prompt from a template.

### Component 2: Worktree Agent Prompt Template

Each agent receives a structured prompt containing item reference, groomed description, task list from SAM plan, skills to load, architecture spec reference, quality gate commands, prior wave discoveries, and completion protocol specifying structured output with STATUS (COMPLETE or PARTIAL), BRANCH name, TASKS_COMPLETED count, FILES_CHANGED list, COMMITS list, and NOTES for design decisions.

### Component 3: Worktree Branch Lifecycle

Agent(isolation="worktree") automatically creates a temporary git worktree branching from the orchestrator's current branch (which must be the integration branch milestone/{N}-{slug}). The agent commits changes to its worktree branch. Its completion report includes BRANCH={name}. The orchestrator merges branches into the integration branch sequentially.

### Component 4: Discovery Relay Between Waves

After all agents in a wave return, the orchestrator collects completion reports and builds a discovery relay document summarizing which files changed, key commits, and design notes. This relay is included in subsequent wave's agent prompts under "Prior Wave Context."

### Component 5: Conflict Handling

Conflicts are classified as trivial (whitespace, adjacent additions), medium (same function edited differently), or heavy (file restructured by both branches, 3+ files). Trivial conflicts are auto-resolved. Medium conflicts trigger a conflict-resolution agent in a worktree on the integration branch. Heavy conflicts create a backlog item for conflict resolution.

### Component 6: Completion and Landing

After all waves complete and branches are merged, the orchestrator runs the full quality gate suite. If gates fail, a fix agent is spawned in a worktree on the integration branch. Once gates pass, the integration branch is merged to main with a conventional commit.

## Dispatch Schema Architecture

The dispatch_schema package (plugins/development-harness/dispatch_schema/) produces the dispatch plan YAML. Key modules:

- **models.py** — Defines Pydantic models for dispatch plan structure (Wave, Item, ConflictGroup, QualityGates)
- **core/validator.py** — Validates plan integrity
- **readers/yaml_reader.py** — Reads dispatch plan YAML
- **writers/yaml_writer.py** — Writes dispatch plan YAML
- **gates.py** — Manages quality gate definitions

The dispatch plan schema does not change. Existing wave/item/conflict_group/depends_on fields contain all data needed.

## Integration Branch Management

The github_branches.py module (plugins/development-harness/backlog_core/) exposes the IntegrationBranch class handling:
- Creating integration branch from main
- Switching orchestrator's working tree to integration branch
- Merging worktree branches into integration branch
- Handling fast-forward vs merge commits
- Deleting integration branch after landing to main

The orchestrator must be on the integration branch before spawning worktree agents.

## Work-Milestone SKILL.md Current Structure

The current SKILL.md is a TeamCreate-based orchestrator that loads the dispatch plan, validates it, creates the integration branch, enters a wave loop, spawns TeamCreate per wave, monitors via SendMessage, manages merge queue, and lands to main.

### Files to Modify

1. **SKILL.md** (core rewrite) — Remove TeamCreate, replace with Agent(isolation="worktree") dispatch. Replace SendMessage monitoring with "wait for Agent returns". Replace merge queue with sequential merge of worktree branches.

2. **references/team-member-protocol.md** (rename to worktree-worker-protocol.md) — Remove M2-M7, M10-M12 lifecycle steps. Retain M1, M4, M8, M9. Add sections for Completion Report Format, Blocker Handling, Skill Loading, Direct Task Execution.

3. **references/merge-queue-protocol.md** (update) — Replace SendMessage references with Agent return signaling. Update assign_back: no PR creation, create backlog item instead. Retain all conflict classification logic.

4. **references/dispatch-plan-schema.md** (add notes) — Add "Execution Model" section explaining isolation mode is always "worktree", agent type not configurable per item, skills come from SAM task plan, conflict groups handle serialization.

5. **.claude/rules/local-workflow.md** (add forward reference) — Add note clarifying boundary between SAM task execution (single item) and milestone dispatch (multiple items with worktree agents).

## Skill Loading in Worktree Agents

Each SAM task optionally declares a skills field. The orchestrator aggregates these and includes them in the agent prompt. The agent loads each skill at startup via Skill(skill="skill-name"). If a skill fails, the agent warns and continues.

## SAM Task Status Tracking

Worktree agents should call SAM MCP tools as they progress:
- sam_claim(plan="P{N}", task="T{M}") before starting each task
- sam_state(plan="P{N}", task="T{M}", status="complete") after each task completes

This keeps SAM state consistent.

## Quality Gates Execution

Pre-merge and post-merge quality gate commands from the dispatch plan run inside the worktree agent's isolated copy. The agent has a full copy of pyproject.toml, uv.lock, and other config files. If a gate fails, the agent reports failure with STATUS=PARTIAL and the blocker description.

## Error Handling and Partial Completion

When a worktree agent returns with STATUS=PARTIAL, some tasks completed but others were blocked. The completion report includes TASKS_COMPLETED, TASKS_BLOCKED, BLOCKER description, commits, and files changed. The orchestrator merges the completed work and creates a backlog item for blocked tasks.

## Primary Files to Rewrite

1. plugins/development-harness/skills/work-milestone/SKILL.md — Core dispatch logic rewrite
2. plugins/development-harness/skills/work-milestone/references/team-member-protocol.md — Rename to worktree-worker-protocol.md and rewrite
3. plugins/development-harness/skills/work-milestone/references/merge-queue-protocol.md — Update signaling and assign_back
4. plugins/development-harness/skills/work-milestone/references/dispatch-plan-schema.md — Add clarifying notes
5. .claude/rules/local-workflow.md — Add forward reference

## Supporting Context Files

1. plan/architect-redesign-work-milestone-worktree-agents.md — Architecture spec with 6 components and revised workflow
2. plan/feature-context-redesign-work-milestone-worktree-agents.md — Feature context with problem and risks
3. .claude/projects/-home-ubuntulinuxqa2-repos-claude-skills/memory/project_teammate_capabilities.md — Verified teammate limitations
4. plugins/development-harness/dispatch_schema/ — Dispatch plan schema package (no changes)
5. plugins/development-harness/backlog_core/github_branches.py — Integration branch management module

## Implementation Constraints

1. **No schema changes** — dispatch_schema and its models remain unchanged
2. **/work-backlog-item --auto unchanged** — skill not modified, worktree agents execute tasks directly
3. **/groom-milestone unchanged** — dispatch plan generation unaffected
4. **Subagent nesting prohibition** — Official Claude Code constraint, hard limitation
5. **Worktree branches local-only** — Never pushed to origin

## Open Questions for Implementers

1. **Worktree base branch** — Does Agent(isolation="worktree") use orchestrator's current branch or HEAD? Design assumes orchestrator switches to integration branch before spawning agents.

2. **Worktree branch name discovery** — If agent fails to output structured completion report, how does orchestrator identify which branch to merge? Architect spec suggests using git worktree list or git branch --list.

3. **Parallel Agent call limits** — Are there limits on concurrent Agent invocations? A wave with 10 items would spawn 10 parallel calls.

4. **Agent context window for large items** — Large task plans may exceed agent's context window. Mitigation: write task plan to file and instruct agent to read it.

5. **Quality gate execution in worktree** — Some gates may depend on virtualenv state. Design assumes uv run inside worktree creates or reuses per-worktree virtualenv.

6. **SAM task status tracking** — Worktree agents should call sam_claim and sam_state to keep task status consistent. Recommendation: include this in agent prompt template.
