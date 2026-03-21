---
name: work-milestone
description: "Execute a groomed milestone with parallel workers in isolated worktrees. Reads dispatch plan YAML from /groom-milestone, creates integration branch, spawns TeamCreate teams per wave with one member per parallel item running /work-backlog-item --auto. Manages merge queue with slot serialization, conflict severity classification, assign_back on heavy conflicts. Inter-worker awareness via SendMessage, design decisions persisted to GitHub Issues. Discovery relay between waves. Lands integration branch to main when done. Args: {milestone-number}."
argument-hint: '{milestone-number}'
user-invocable: true
---

# /work-milestone

Execute a groomed milestone. Reads the dispatch plan produced by `/groom-milestone`, creates an integration branch, dispatches parallel workers per wave, serializes merges through a single merge slot, and lands the integration branch to main when all waves complete.

## Entry Conditions

- Milestone number provided as argument
- Dispatch plan exists: `plan/milestone-{N}-dispatch.yaml`
- All items in dispatch plan are groomed (`groomed: true`)
- Backlog MCP and sam CLI responding
- Clean git state on main

Run `/groom-milestone {N}` first if the dispatch plan is missing or stale.

## Main Workflow

```mermaid
flowchart TD
    Start(["Input: milestone number N"]) --> LoadPlan["Step 1: Load Dispatch Plan<br>Read plan/milestone-{N}-dispatch.yaml<br>via read_dispatch_plan.<br>Output: waves, conflict groups, quality gates"]

    LoadPlan --> Validate{"Step 2: Validate Plan<br>File exists?<br>All items still open?<br>Observable: file + backlog_list_issues(milestone=N)"}

    Validate -->|"Plan missing"| Block1(["BLOCKED — run /groom-milestone {N}"])
    Validate -->|"Items changed since groom"| Regroom["Re-run /groom-milestone {N}<br>to regenerate dispatch plan"]
    Validate -->|"Plan valid"| CreateBranch
    Regroom --> LoadPlan

    CreateBranch["Step 3: Create Integration Branch<br>Action: github_branches create<br>milestone/{N}-{slug} from main.<br>Push to origin."]

    CreateBranch --> WaveLoop["Step 4: Wave Dispatch Loop<br>Read next wave from dispatch plan"]

    WaveLoop --> WaveItems{"Wave has items?"}
    WaveItems -->|"No waves remain"| Land
    WaveItems -->|"Wave has 1 item"| SingleWorker["Spawn single agent<br>isolation: worktree<br>/work-backlog-item --auto {title}"]
    WaveItems -->|"Wave has 2+ items"| TeamSpawn["Step 5: TeamCreate<br>One member per parallel item.<br>Each member: isolation=worktree,<br>base=integration branch,<br>task=/work-backlog-item --auto {title}"]

    SingleWorker --> Monitor
    TeamSpawn --> Monitor

    Monitor["Step 6: Monitor Wave<br>Wait for SendMessage from workers.<br>Do NOT poll."]

    Monitor --> MsgType{"Message type?"}

    MsgType -->|"BLOCKER — needs user direction"| EscalateUser["Escalate to user.<br>Forward answer to worker<br>via SendMessage."]
    EscalateUser --> Monitor

    MsgType -->|"BLOCKER — env resource missing"| ReportEnv["Report missing resource to user.<br>Pause worker until available."]
    ReportEnv --> Monitor

    MsgType -->|"COMPLETE — item finished"| MergeSlot["Step 7: Merge Queue<br>Acquire merge slot (one at a time).<br>See merge-queue-protocol.md"]

    MergeSlot --> WaveCheck{"Wave complete?<br>All items merged or assigned-back?"}
    WaveCheck -->|"Items pending"| Monitor
    WaveCheck -->|"Wave done"| NextWave["Terminate wave team.<br>Update dispatch plan status.<br>Advance to next wave."]
    NextWave --> WaveLoop

    Land["Step 9: Land Integration Branch<br>Run full quality gate suite<br>(pre_merge + post_merge)<br>on integration branch."]

    Land --> FinalResult{"Final gates pass?"}
    FinalResult -->|"Fail"| FinalFix["Delegate fix to specialist agent<br>in worktree on integration branch.<br>Re-run gates after fix."]
    FinalFix --> Land

    FinalResult -->|"Pass"| MergeMain["Merge integration branch to main.<br>git switch main<br>git merge --no-ff milestone/{N}-{slug}<br>git push origin main"]

    MergeMain --> Complete["Step 10: Complete Milestone<br>Invoke /complete-milestone {N}.<br>Delete integration branch.<br>Terminate all workers."]

    Complete --> Done(["Exit: milestone complete"])
```

## Team Member Protocol

Each worker runs in an isolated worktree on the integration branch. Full protocol: [team-member-protocol.md](./references/team-member-protocol.md).

Summary of member responsibilities:

```mermaid
flowchart TD
    Spawn(["Worker spawned in worktree"]) --> Announce["Announce to team via SendMessage:<br>item title, domain, files_planned"]
    Announce --> DomainCheck{"Domain overlaps a peer?"}
    DomainCheck -->|"No"| Work
    DomainCheck -->|"Yes"| Align["Initial alignment via SendMessage.<br>Write resolution into issue body<br>via backlog_update."]
    Align --> Work
    Work["/work-backlog-item --auto {title}"] --> Broadcast["Broadcast state on each task transition:<br>current task + files_touched"]
    Broadcast --> Done{"Item complete?"}
    Done -->|"No"| Work
    Done -->|"Yes"| Verify["Run quality gates locally.<br>Commit all changes."]
    Verify --> Signal["SendMessage to orchestrator:<br>COMPLETE + worktree branch +<br>integration HEAD at verify time +<br>final files_touched"]
    Signal --> Await(["Await merge outcome or termination"])
```

## Inter-Worker Awareness

Workers share two types of information through different channels:

```mermaid
flowchart TD
    Event(["Worker event"]) --> Type{"Information type?"}
    Type -->|"High-frequency, ephemeral:<br>files touched, current task,<br>alignment checks, blocker reports"| Team["SendMessage via TeamCreate<br>Real-time coordination"]
    Type -->|"Durable, auditable:<br>design decisions, alignment<br>resolutions, conflict outcomes"| Issue["backlog_update via MCP<br>Appended to issue body<br>Section: Design Decision - {ISO} - {slug}"]
```

### Design Alignment Protocol

When two workers share a domain (same plugin directory or overlapping file paths), they coordinate before proceeding:

```mermaid
flowchart TD
    Register(["Worker registers files_touched"]) --> Check{"Any peer shares<br>this domain?"}
    Check -->|"No overlap"| Continue(["Work independently"])
    Check -->|"Overlap"| ReadPeer["Read peer's manifest:<br>files_touched, design_decisions, current_task"]
    ReadPeer --> Impact{"Design impact?<br>Shared interfaces, models, config?"}
    Impact -->|"No — independent concerns"| LogAwareness["Log overlap assessed as independent.<br>Continue working."]
    LogAwareness --> Continue
    Impact -->|"Yes — shared interface or pattern"| Coordinate["SendMessage to peer:<br>what you are building,<br>interface/pattern you plan to use,<br>what you need from their side"]
    Coordinate --> Response{"Peer response?"}
    Response -->|"Compatible"| RecordAlign["Both workers append alignment note<br>to issue body via backlog_update."]
    RecordAlign --> Continue
    Response -->|"Incompatible"| EscalateDesign["Both workers SendMessage to orchestrator:<br>conflicting approaches + trade-offs.<br>Both pause on the conflicting area.<br>Continue on non-conflicting tasks."]
    EscalateDesign --> WaitDecision["Wait for orchestrator to forward<br>user's design decision."]
    WaitDecision --> Continue
```

## Merge Queue

One merge proceeds at a time. The orchestrator holds the merge slot. Conflict classification and assign_back details: [merge-queue-protocol.md](./references/merge-queue-protocol.md).

Conflict severity at a glance:

| Conflict scope | Classification | Action |
|---|---|---|
| 0 files | Clean | Merge immediately |
| 1-2 files — whitespace or adjacent additions | Trivial | Auto-resolve, run gates |
| 1-2 files — same function edited differently | Medium | Auto-resolve attempt, run gates |
| 1-2 files — file refactored by both worktrees | Heavy | assign_back, create PR + resolution task |
| 3+ files | Heavy | assign_back, create PR + resolution task |

## Tools Used

| Tool | Purpose |
|---|---|
| `read_dispatch_plan` | Read `plan/milestone-{N}-dispatch.yaml` |
| `TeamCreate` | Spawn parallel workers per wave |
| `SendMessage` | Worker state broadcasts and blocker reports |
| `github_branches create` | Create integration branch |
| `github_branches merge` | Merge worktree branch into integration branch |
| `github_branches delete` | Delete integration branch after landing |
| `run_quality_gates` | Execute gate commands from dispatch plan |
| `backlog_list_issues(milestone=N)` | Validate plan against current item state |
| `backlog_update(selector, section, content)` | Persist design decisions to issue body |
| `backlog_view` | Read item state and design decisions |

## Error Conditions

- **Dispatch plan missing**: BLOCKED — direct to `/groom-milestone {N}`
- **Items changed since groom**: re-run `/groom-milestone {N}` to regenerate plan
- **Backlog MCP unavailable**: PROCESS ERROR — report with exact error text
- **sam CLI unavailable**: PROCESS ERROR — report with exact error text
- **Integration branch already exists**: check for stale branch (no commits in 7+ days) — offer to delete and recreate, or resume
- **Worker no heartbeat**: report crashed worker to user; identify last known task from context file
- **All quality gates fail on integration branch**: escalate to user before landing
- **Main diverged during milestone work**: rebase integration branch onto main before landing

## References

- [Team Member Protocol](./references/team-member-protocol.md) — full M1-M12 worker lifecycle, state broadcast fields, blocker types
- [Merge Queue Protocol](./references/merge-queue-protocol.md) — merge slot lifecycle, conflict classification, assign_back procedure, gate commands
