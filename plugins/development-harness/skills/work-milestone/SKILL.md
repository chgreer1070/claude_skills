---
name: work-milestone
description: "Execute a groomed milestone with parallel worktree agents. Use when running a milestone after /groom-milestone has produced a dispatch plan. Reads dispatch plan, creates integration branch, dispatches one Agent(isolation: worktree) per wave item with issue number and integration branch — agents self-discover task plans and AC via SAM MCP. Sequentially merges worktree branches, relays wave discoveries to subsequent waves, then lands integration branch to main. Args: {milestone-number}."
argument-hint: '{milestone-number}'
user-invocable: true
---

# /work-milestone

Execute a groomed milestone. Reads the dispatch plan produced by `/groom-milestone`, creates an integration branch, dispatches parallel worktree agents per wave, sequentially merges their branches, and lands the integration branch to main when all waves complete.

## Entry Conditions

- Milestone number provided as argument
- Dispatch plan exists: `plan/milestone-{N}-dispatch.yaml`
- All items in dispatch plan are groomed (`groomed: true`)
- Backlog MCP and SAM MCP responding
- Clean git state on main

Run `/groom-milestone {N}` first if the dispatch plan is missing or stale.

## Main Workflow

```mermaid
flowchart TD
    Start(["Input: milestone number N"]) --> LoadPlan["Step 1: Load Dispatch Plan<br>Read plan/milestone-{N}-dispatch.yaml<br>Output: waves, conflict groups, quality gates"]

    LoadPlan --> Validate{"Step 2: Validate Plan<br>File exists?<br>All items still open?<br>Observable: file + backlog_list_issues(milestone=N)"}

    Validate -->|"Plan missing"| Block1(["BLOCKED — run /groom-milestone {N}"])
    Validate -->|"Items changed since groom"| Regroom["Re-run /groom-milestone {N}"]
    Validate -->|"Plan valid"| CreateBranch
    Regroom --> LoadPlan

    CreateBranch["Step 3: Create Integration Branch<br>github_branches create<br>milestone/{N}-{slug} from main.<br>Switch to integration branch locally."]

    CreateBranch --> WaveLoop["Step 4: Wave Dispatch Loop<br>Read next wave from dispatch plan"]

    WaveLoop --> WaveItems{"Wave has items?"}
    WaveItems -->|"No waves remain"| Land

    WaveItems -->|"Yes"| SpawnAgents["Step 5: Spawn Worktree Agents<br>For each item: Agent(isolation: worktree)<br>with issue number + integration branch.<br>Agent self-discovers task plan and AC via SAM MCP.<br>All items in wave launch in parallel via TeamCreate."]

    SpawnAgents --> WaitReturn["Step 6: Wait for All Agents<br>Agent calls are synchronous.<br>Collect structured completion reports<br>from each agent output."]

    WaitReturn --> ParseResults["Step 6a: Parse Completion Reports<br>Extract STATUS, BRANCH, FILES_CHANGED,<br>COMMITS, NOTES from each agent."]

    ParseResults --> MergeLoop["Step 6b: Merge Worktree Branches<br>Sequential merge into integration branch.<br>One at a time, in return order."]

    MergeLoop --> MergeResult{"Any merge conflicts?"}
    MergeResult -->|"All clean"| WaveComplete
    MergeResult -->|"Trivial/Medium conflict"| Resolve["Auto-resolve or spawn<br>conflict-resolution agent"]
    Resolve --> ResolveGates{"Resolution gates pass?"}
    ResolveGates -->|"Yes"| WaveComplete
    ResolveGates -->|"No"| EscalateConflict["Create backlog item<br>for conflict resolution.<br>Add to milestone."]

    MergeResult -->|"Heavy conflict (3+ files)"| EscalateConflict

    WaveComplete["Step 6c: Wave Complete<br>All branches merged.<br>Delete worktree branches."]

    WaveComplete --> DiscoveryRelay["Step 6d: Discovery Relay<br>Build relay document from agent outputs.<br>Include FILES_CHANGED, COMMITS, NOTES<br>in next wave agent prompts."]

    DiscoveryRelay --> PartialCheck{"Any agents returned PARTIAL?"}
    PartialCheck -->|"Yes"| HandlePartial["Create backlog items for<br>blocked tasks. Add to milestone."]
    PartialCheck -->|"No"| NextWaveCheck

    HandlePartial --> NextWaveCheck{"More waves?"}
    NextWaveCheck -->|"Yes"| WaveLoop
    NextWaveCheck -->|"No"| Land

    Land["Step 8: Land Integration Branch<br>Run full quality gate suite<br>pre_merge + post_merge"]

    Land --> FinalResult{"Gates pass?"}
    FinalResult -->|"Fail"| FinalFix["Spawn fix agent in worktree<br>on integration branch."]
    FinalFix --> Land

    FinalResult -->|"Pass"| MergeMain["Step 9: Merge to Main<br>git switch main<br>git merge --no-ff milestone/{N}-{slug}<br>git push origin main"]

    MergeMain --> Complete["Step 10: Complete Milestone<br>/complete-milestone {N}.<br>Delete integration branch."]

    Complete --> Done(["Exit: milestone complete"])
```

## Dispatch Step (Step 5 Detail)

All items in a wave are independent by construction (guaranteed non-overlapping by the conflict group analysis in the dispatch plan). Use `TeamCreate` to launch them in parallel — teams are the standard mechanism for parallel wave dispatch.

```text
TeamCreate(team_name: "wave-{N}-{milestone-slug}")
```

Spawn one worktree agent per wave item as a teammate. Each teammate receives a minimal reference prompt (see template below) and operates autonomously. The orchestrator waits for all teammates to complete, then merges branches sequentially.

The worktree isolation is orthogonal to team coordination: `Agent(isolation: "worktree")` provides filesystem isolation per item; `TeamCreate` provides the parallel dispatch and coordination mechanism. Both apply simultaneously.

The orchestrator passes only references to the worktree agent. The agent self-discovers everything else.

**What the orchestrator passes:**

- Issue number (from dispatch plan wave item)
- Integration branch name (from dispatch plan)
- Discovery relay content from prior waves (orchestrator-accumulated, empty for wave 1)
- Quality gate commands (from dispatch plan `quality_gates.pre_merge`)

**What the agent discovers autonomously:**

- Groomed description and acceptance criteria — via `backlog_view(selector="#{issue}")`
- Plan artifacts (architect spec, feature context, etc.) — via `artifact_list(issue_number={issue})` then `artifact_read(issue_number={issue}, artifact_type="architect")` for content
- SAM task plan and task list — via `sam_read(plan="P{N}")` if a plan exists
- Skills to load — from `skills` field in SAM task metadata

## Worktree Agent Prompt Template

Each worktree agent receives a minimal reference prompt. The agent reads item data directly via MCP. The agent has no Agent tool — it cannot delegate to subagents. All work is executed directly.

```text
## Your Task

You are executing backlog item #{issue}: "{title}" inside an isolated git worktree
on the integration branch `{integration_branch}`.

You have NO Agent tool — you cannot delegate to subagents. Execute all work directly.
Commit your changes frequently using conventional commits: `type(scope): description`.

## Self-Discovery Steps

Before starting work:

1. Read the backlog item: `backlog_view(selector="#{issue}")` — extract description and acceptance criteria.
2. Discover plan artifacts via MCP:
   - Call `artifact_list(issue_number={issue})` to get all registered artifacts for this issue.
   - If artifacts exist: call `artifact_read(issue_number={issue}, artifact_type="architect")` to read the architecture spec content. Repeat for `"feature-context"` or other types as needed.
   - If `artifact_list` returns empty (pre-manifest issue with no registered artifacts): fall back to filesystem paths from the SAM plan or backlog item.
3. Check for a SAM plan: `sam_status(plan="P{issue}")` or search `sam_list()` by title.
   - If a plan exists: `sam_read(plan="P{plan_id}")` — extract task list, skills, and architect spec path.
   - If no plan exists: work from acceptance criteria directly.
4. Load all skills listed in the SAM task metadata:
   - For each skill name found: `Skill(skill="{skill_name}")`
   - If a skill fails to load, warn and continue.

## Filesystem Restriction

You are running in an isolated git worktree. Do NOT access `plan/` files via the filesystem — they may not exist in your worktree checkout. Use MCP tools exclusively for plan artifact discovery and content retrieval:
- `artifact_list(issue_number={issue})` — discover what artifacts exist
- `artifact_read(issue_number={issue}, artifact_type="...")` — read artifact content via the MCP server (which reads from the root worktree, not your checkout)

## Quality Gates

Before signaling completion, run these commands and fix any failures:
{for each command in pre_merge_gates}
- `{command}`
{end for}

## Prior Wave Context

{discovery_relay_content — empty for wave 1}

## Completion Protocol

When all tasks are complete and quality gates pass:
1. Ensure all changes are committed
2. Output a structured completion report:

   STATUS: COMPLETE
   BRANCH: {your worktree branch name}
   TASKS_COMPLETED: {count}
   FILES_CHANGED: {list of files}
   COMMITS: {list of commit hashes and messages}
   NOTES: {any design decisions or deviations}

If you encounter a blocker you cannot resolve:
1. Complete as many tasks as possible
2. Commit all completed work
3. Output:

   STATUS: PARTIAL
   BRANCH: {your worktree branch name}
   TASKS_COMPLETED: {count of completed}
   TASKS_BLOCKED: {count and IDs of blocked tasks}
   BLOCKER: {description of what blocked progress}
   FILES_CHANGED: {list of files}
   COMMITS: {list of commit hashes and messages}
```

### Template Variables

| Variable | Source | How Orchestrator Obtains It |
|---|---|---|
| `issue` | Dispatch plan wave item | `wave.items[i].issue` |
| `title` | Dispatch plan wave item | `wave.items[i].title` |
| `integration_branch` | Dispatch plan | `milestone.integration_branch` |
| `pre_merge_gates` | Dispatch plan | `quality_gates.pre_merge` commands |
| `discovery_relay_content` | Orchestrator state | Collected from prior wave agent outputs |

All other data (description, AC, task list, skills, architect spec, plan artifacts) is discovered by the agent via MCP after spawning. The issue number is used both for `backlog_view` and for `artifact_list`/`artifact_read` queries.

## Agent Result Handling

```mermaid
flowchart TD
    Result(["Agent returned"]) --> Status{"Agent output indicates success?"}
    Status -->|"STATUS: COMPLETE — tasks done, changes committed"| Merge["Proceed to merge"]
    Status -->|"STATUS: PARTIAL — some tasks done, some blocked"| Partial["Merge completed work.<br>Create backlog item for remaining tasks.<br>Add to current milestone."]
    Status -->|"Failure — no useful work done"| Failure["Log failure context.<br>Escalate to user:<br>item title, error, agent output summary."]
```

## Discovery Relay Between Waves

After all wave agents return, the orchestrator builds a relay document from their completion reports. This is injected as `discovery_relay_content` in the next wave's agent prompts.

```text
## Prior Wave Results

### Wave 1 Results

#### Item: #{issue1} — {title1}
- Status: COMPLETE
- Files changed: {file_list}
- Key commits:
  - {hash}: {message}
- Design notes: {notes_if_any}

#### Item: #{issue2} — {title2}
- Status: COMPLETE
- Files changed: {file_list}
- Key commits:
  - {hash}: {message}
```

Items in the same wave are guaranteed non-overlapping by the dispatch plan's conflict group analysis. The relay provides cross-wave awareness for items with `depends_on` relationships or shared conflict groups.

For milestones with 5+ waves, cap the relay at the most recent 3 waves.

## Merge Conflict Classification

| Conflict scope | Classification | Action |
|---|---|---|
| 0 files | Clean | Merge immediately |
| 1-2 files — whitespace or adjacent additions | Trivial | Auto-resolve, run gates |
| 1-2 files — same function edited differently | Medium | Spawn conflict-resolution agent |
| 1-2 files — file restructured by both worktrees | Heavy | Create backlog item for conflict resolution |
| 3+ files | Heavy | Abort merge, create backlog item |

Conflict resolution agent receives both branches' diffs and resolves in-place on the integration branch. No PRs are created for worktree branches — they are local-only, never pushed to origin.

## Tools Used

| Tool | Purpose |
|---|---|
| `read_dispatch_plan` | Read `plan/milestone-{N}-dispatch.yaml` |
| `TeamCreate` | Spawn parallel wave workers (standard parallel dispatch mechanism) |
| `Agent(isolation: "worktree")` | Provide filesystem isolation per wave item (used inside TeamCreate) |
| `backlog_view` | Read item description, AC, design decisions |
| `artifact_list` | Discover plan artifacts registered for an issue |
| `artifact_read` | Read plan artifact content from root worktree via MCP |
| `sam_read` | Read SAM task plan for an item |
| `sam_status` / `sam_list` | Check whether item has a SAM plan |
| `github_branches create` | Create integration branch |
| `github_branches merge` | Merge worktree branch into integration branch |
| `github_branches delete` | Delete integration branch after landing |
| `run_quality_gates` | Execute gate commands from dispatch plan |
| `backlog_list_issues(milestone=N)` | Validate plan against current item state |

## Error Conditions

- **Dispatch plan missing**: BLOCKED — direct to `/groom-milestone {N}`
- **Items changed since groom**: re-run `/groom-milestone {N}` to regenerate plan
- **Backlog MCP unavailable**: PROCESS ERROR — report with exact error text
- **SAM MCP unavailable**: PROCESS ERROR — report with exact error text
- **Integration branch already exists**: check for stale branch (no commits in 7+ days) — offer to delete and recreate, or resume
- **Agent returned PARTIAL status**: create backlog items for blocked tasks, add to milestone, continue with other agents
- **All quality gates fail on integration branch**: escalate to user before landing
- **Main diverged during milestone work**: rebase integration branch onto main before landing

## References

- [Worktree Worker Protocol](./references/worktree-worker-protocol.md) — full worker lifecycle: setup, direct task execution, quality gates, completion report format, blocker handling, skill loading
- [Merge Queue Protocol](./references/merge-queue-protocol.md) — merge slot lifecycle, conflict classification, conflict-resolution agent, quality gate commands
