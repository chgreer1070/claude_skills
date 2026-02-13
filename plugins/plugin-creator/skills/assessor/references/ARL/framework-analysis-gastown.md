# Framework Analysis: Gas Town

## Source Repository

`/home/ubuntulinuxqa2/repos/gastown/`

---

## A. System Overview

### What Is This System?

Gas Town is a multi-agent orchestration system for AI coding agents (primarily Claude Code, with support for Codex, Gemini, OpenCode, and others). It manages workspace state, agent identity, work assignment, and lifecycle across multiple concurrent AI agent sessions.

> "Gas Town is a workspace manager that lets you coordinate multiple Claude Code agents working on different tasks. Instead of losing context when agents restart, Gas Town persists work state in git-backed hooks, enabling reliable multi-agent workflows."
>
> -- README.md:7

The system is implemented as a Go CLI (`gt`) that works alongside a separate git-backed issue tracker called Beads (`bd`). Together they provide:

- Persistent agent identity and attribution
- Git worktree-based sandboxes for isolated agent work
- A merge queue (Refinery) for integrating agent output
- A watchdog chain (Daemon/Boot/Deacon) for autonomous recovery
- Convoy-based work tracking across multiple projects
- Molecule-based workflow orchestration (TOML formula templates)

### What Problem Does It Solve?

From README.md:3-17:

| Challenge                       | Gas Town Solution                            |
|---------------------------------|----------------------------------------------|
| Agents lose context on restart  | Work persists in git-backed hooks            |
| Manual agent coordination       | Built-in mailboxes, identities, and handoffs |
| 4-10 agents become chaotic      | Scale comfortably to 20-30 agents            |
| Work state lost in agent memory | Work state stored in Beads ledger            |

The deeper problems it addresses (from docs/why-these-features.md:7-15):

- **Accountability**: Which agent introduced this bug?
- **Quality**: Which agents are reliable? Which need tuning?
- **Efficiency**: How do you route work to the right agent?
- **Scale**: How do you coordinate agents across repos and teams?

### Core Philosophy

Gas Town treats AI agent work as **structured data**. Every action is attributed. Every agent has a track record. Every piece of work has provenance.

Five design principles (docs/why-these-features.md:253-258):

1. **Attribution is not optional.** Every action has an actor.
2. **Work is data.** Not just tickets -- structured, queryable data.
3. **History matters.** Track records determine trust.
4. **Scale is assumed.** Multi-repo, multi-agent, multi-org from day one.
5. **Verification over trust.** Quality gates are first-class primitives.

### Target Audience

Developers and teams running multiple AI coding agents across multiple repositories. The system is designed to scale from a single developer with a few agents to enterprise teams with 20-30+ concurrent agents across many projects.

---

## B. Autonomous Development Model

### How Does It Front-Load Human Effort?

Gas Town does NOT follow a traditional front-loading pattern (plan everything upfront, then execute autonomously). Instead, it uses a **Mayor-mediated decomposition** model:

1. **Human tells Mayor what to build** (natural language intent)
2. **Mayor decomposes** into issues (beads) and creates a convoy
3. **Mayor assigns** work to polecats (worker agents) via `gt sling`
4. **Workers execute autonomously** through molecule steps
5. **Refinery merges** completed work to main
6. **Mayor reports** progress back to human

The front-loading is minimal by design -- the human provides intent, the Mayor handles decomposition, and the system orchestrates execution.

From README.md:136-153 (basic workflow):

```
You -> Mayor: Tell Mayor what to build
Mayor -> Convoy: Create convoy with beads
Mayor -> Agent: Sling bead to agent
Agent -> Hook: Store work state
Agent -> Agent: Complete work
Agent -> Convoy: Report completion
Mayor -> You: Summary of progress
```

### Workflow Pipeline

Gas Town uses a multi-tier pipeline with distinct roles:

#### Stage 1: Intent Capture (Human -> Mayor)

Human describes what they want. Mayor is the primary interface.

#### Stage 2: Work Decomposition (Mayor)

Mayor creates beads (issues), organizes them into convoys, and selects formulas (workflow templates).

#### Stage 3: Work Assignment (Mayor -> Polecats)

Work is "slung" to polecat workers via `gt sling`. This:
- Allocates a polecat slot from the name pool
- Creates a git worktree (sandbox)
- Starts a Claude session in tmux
- Hooks a molecule (workflow instance) to the polecat

From docs/concepts/polecat-lifecycle.md:133-139:

```
gt sling
  -> Allocate slot from pool (Toast)
  -> Create sandbox (worktree on new branch)
  -> Start session (Claude in tmux)
  -> Hook molecule to polecat
```

#### Stage 4: Autonomous Execution (Polecats)

Each polecat works through molecule steps autonomously:

```
1. gt hook                    # What's hooked?
2. bd mol current             # Where am I?
3. Execute step
4. bd close <step> --continue # Close and advance
5. GOTO 2
```

From docs/concepts/propulsion-principle.md:64-69.

#### Stage 5: Self-Cleaning Completion (Polecat -> Refinery)

When work is done, the polecat runs `gt done`, which:
- Pushes branch to origin
- Submits to merge queue
- Nukes its own sandbox and session
- Exits immediately

From docs/concepts/polecat-lifecycle.md:155-163.

#### Stage 6: Integration (Refinery)

The Refinery processes the merge queue:
- Rebases and merges to main
- Closes the issue
- If conflict: spawns a FRESH polecat to re-implement (never sends work back)

#### Stage 7: Verification and Monitoring (Witness + Deacon)

- Witness monitors polecats per-rig, nudges stuck workers, handles pre-kill verification
- Deacon runs continuous patrol, monitors system health
- Daemon provides mechanical heartbeat every 3 minutes

### Human Decision Points vs Automated Decision Points

| Decision | Who Decides | Type |
|----------|-------------|------|
| What to build | Human | Strategic |
| How to decompose | Mayor (AI) | Automated |
| Which agent for which task | Mayor (AI) | Automated |
| Whether work is complete | Polecat self-reports via `gt done` | Automated |
| Whether code merges cleanly | Refinery (AI) | Automated |
| Whether stuck agent needs help | Witness (AI) | Automated |
| Unresolvable conflicts | Mayor -> Human escalation | Human |
| Design decisions | Escalation protocol | Human |
| Security/emergency issues | Direct to overseer | Human |

The escalation protocol (docs/design/escalation.md) provides structured paths when automated resolution fails, with tiered routing: Deacon -> Mayor -> Overseer (human).

### How Does It Handle Scope?

Gas Town is scope-agnostic. Work is decomposed into beads (atomic units) regardless of size:

- **Small task**: Single bead, single polecat, one molecule
- **Medium feature**: Multiple beads, convoy tracking, parallel polecats
- **Large project**: Multiple convoys, cross-rig tracking, federated workspaces

Convoys provide the scaling unit -- they group related beads and track completion across multiple rigs (projects).

---

## C. Key Concepts and Mechanisms

### Named Concepts

#### Roles (Agent Types)

| Role | Level | Description | Lifecycle |
|------|-------|-------------|-----------|
| **Mayor** | Town | Global coordinator, work decomposition | Singleton, persistent |
| **Deacon** | Town | Background supervisor daemon, continuous patrol | Singleton, persistent |
| **Boot** | Town | Ephemeral triage agent for Deacon health | Fresh each daemon tick |
| **Dog** | Town | Deacon helpers for infrastructure tasks | Ephemeral |
| **Witness** | Rig | Per-rig polecat lifecycle manager | One per rig, persistent |
| **Refinery** | Rig | Per-rig merge queue processor | One per rig, persistent |
| **Polecat** | Rig | Worker with persistent identity, ephemeral sessions | Session cycles on handoff |
| **Crew** | Rig | Persistent human workspace | Long-lived, user-managed |

Source: docs/overview.md:20-43, docs/design/architecture.md:62-81.

#### Work Units

| Concept | Description |
|---------|-------------|
| **Bead** | Git-backed atomic work unit (JSONL). The fundamental unit of tracking. |
| **Formula** | TOML-based workflow source template |
| **Protomolecule** | Frozen template ready for instantiation |
| **Molecule** | Active workflow instance with trackable steps |
| **Wisp** | Ephemeral molecule for patrol cycles (never synced) |
| **Digest** | Squashed summary of completed molecule |
| **Convoy** | Batch work tracker grouping related beads across rigs |
| **Hook** | Agent's primary work queue -- a pinned bead |

Source: docs/glossary.md:54-77.

#### Operations

| Operation | Description |
|-----------|-------------|
| **Slinging** | Assigning work to agents via `gt sling` |
| **Nudging** | Real-time messaging between agents via `gt nudge` |
| **Handoff** | Session refresh transferring work state via `/handoff` |
| **Seance** | Querying previous sessions for context via `gt seance` |
| **Patrol** | Ephemeral loop maintaining system heartbeat |
| **Propulsion** | The principle: "If work is on your hook, YOU RUN IT" |

Source: docs/glossary.md:72-91.

### State Management Across Agent Handoffs

Gas Town uses a three-layer architecture for polecats that separates persistent from ephemeral state:

| Layer | Component | Lifecycle | Persistence |
|-------|-----------|-----------|-------------|
| **Identity** | Agent bead, CV chain, work history | Permanent | Never dies |
| **Sandbox** | Git worktree, branch, hook assignment | Per assignment | Created on sling, nuked on done |
| **Session** | Claude instance, context window | Per step/handoff | Cycles frequently |

Source: docs/concepts/polecat-lifecycle.md:59-66.

State survives handoffs because:

1. **Git commits persist** in the sandbox worktree
2. **Molecule state persists** in the beads database (Dolt SQL server)
3. **Hook assignment persists** across sessions
4. **Context is recovered** via `gt prime` at session start (SessionStart hook)
5. **Handoff mail** carries context from old session to new

From docs/concepts/polecat-lifecycle.md:253-265:

```
# Session ends (handoff, crash, compaction)
# Work is NOT lost because:
# - Git commits persist in sandbox
# - Staged changes persist in sandbox
# - Molecule state persists in beads
# - Hook persists across sessions
```

### Quality Gates and Verification

Quality assurance operates at multiple levels:

1. **Polecat level**: Must run lint/format/tests before committing (templates/polecat-CLAUDE.md:199-213)
2. **Self-cleaning model**: Polecat pushes branch and submits to merge queue via `gt done`
3. **Witness verification**: Pre-kill checklist verifies clean git state, issue closure, recovery status (templates/witness-CLAUDE.md:90-128)
4. **Refinery merge queue**: Rebases, reviews, and merges to main
5. **Structured validation**: Attribution and quality signals recorded as data (docs/why-these-features.md:180-197)

### Convergence: Knowing When "Done"

Gas Town uses multiple convergence signals:

1. **Molecule step completion**: Each step closed with `bd close <step> --continue`
2. **`gt done` signal**: Polecat self-reports completion, triggers sandbox nuke
3. **Convoy tracking**: Convoy lands when ALL tracked issues close
4. **Event-driven completion**: Issue close propagates to convoy check (docs/design/convoy-lifecycle.md:46-59)
5. **Redundant observers**: Daemon, Witness, and Deacon all check convoy completion independently

The convoy lifecycle design (docs/design/convoy-lifecycle.md:36-41) explicitly addresses convergence:

> Convoy completion should be:
> 1. Event-driven: Triggered by issue close, not polling
> 2. Redundantly observed: Multiple agents can detect and close
> 3. Manually overridable: Humans can force-close

### Error, Failure, and Recovery

Gas Town has a multi-layer recovery architecture:

#### Three-Tier Watchdog Chain

From docs/design/watchdog-chain.md:9-16:

```
Daemon (Go process)          <- Dumb transport, 3-min heartbeat
    |
    +-> Boot (AI agent)       <- Intelligent triage, fresh each tick
            |
            +-> Deacon (AI agent)  <- Continuous patrol, long-running
                    |
                    +-> Witnesses & Refineries  <- Per-rig agents
```

The key insight is that the daemon is mechanical (can not reason), but health decisions need intelligence (is the agent stuck or just thinking?). Boot bridges this gap as an ephemeral AI triage agent.

#### Polecat Failure States

Polecats have exactly three states -- there is NO idle state (docs/concepts/polecat-lifecycle.md:13-21):

| State | Description | Recovery |
|-------|-------------|----------|
| **Working** | Normal operation | N/A |
| **Stalled** | Session stopped mid-work (crash, timeout) | Witness nudges, then respawns |
| **Zombie** | `gt done` failed during cleanup | Witness nukes after verification |

#### Escalation Protocol

Structured tiered escalation (docs/design/escalation.md:111-132):

```
Worker encounters issue
    -> gt escalate --type <category>
    -> [Deacon receives]
        +-- Can resolve? -> Updates issue, re-slings work
        +-- Cannot resolve? -> Forward to Mayor
            +-- Can resolve? -> Updates issue, re-slings
            +-- Cannot resolve? -> Forward to Overseer (human)
```

Categories: decision, help, blocked, failed, emergency, gate_timeout, lifecycle.

#### Merge Conflict Recovery

From docs/concepts/polecat-lifecycle.md:168-172:

> If conflict: spawn FRESH polecat to re-implement (never send work back to original polecat -- it is gone)

This is a key design decision: failed merges never go "back" to the original worker. A new polecat re-implements on the new baseline.

#### Nondeterministic Idempotence (NDI)

From docs/glossary.md:13-14:

> The overarching goal ensuring useful outcomes through orchestration of potentially unreliable processes. Persistent Beads and oversight agents (Witness, Deacon) guarantee eventual workflow completion even when individual operations may fail or produce varying results.

This is the system's fundamental resilience principle: any worker can continue any molecule, steps are atomic checkpoints, and state transitions are git commits.

---

## D. Front-Loading Pattern

### Information Captured Upfront

Gas Town captures minimal upfront information -- it is NOT a heavy front-loading system. The human provides:

1. **Natural language intent** -- "Tell Mayor what you want to build"
2. **Repository context** -- which rig (project) to work in
3. **Optional constraints** -- specific model preferences, deadlines, notification targets

The Mayor handles decomposition into structured work items.

### Artifacts Produced During Planning

1. **Beads (issues)** -- Atomic work units with titles, descriptions, and metadata
2. **Convoys** -- Batch tracking units grouping related beads
3. **Molecules** -- Workflow instances created from formula templates
4. **Mail** -- Assignment notifications sent to agents

### How Planning Becomes "Complete Enough"

Gas Town does not have a formal "planning complete" gate. The Mayor decomposes work and starts slinging it to polecats immediately. The system is designed for:

- **Progressive elaboration** -- work can be added to convoys at any time
- **Parallel execution** -- multiple polecats work simultaneously
- **Self-correcting** -- the escalation protocol handles gaps discovered during execution

The "Shiny" workflow formula defines a canonical polecat work pattern: design -> implement -> review -> test -> submit. But this is a per-issue workflow, not a project-level planning gate.

---

## E. Unique Innovations

### 1. The Propulsion Principle (GUPP)

> "If there is work on your Hook, YOU MUST RUN IT."

From docs/glossary.md:10-11:

> Gas Town Universal Propulsion Principle. This principle ensures agents autonomously proceed with available work without waiting for external input. GUPP is the heartbeat of autonomous operation.

This is a distinctive design: agents do not wait for confirmation, approval, or further instructions. The hook IS the assignment. This eliminates a massive class of coordination overhead.

### 2. Three-Layer Polecat Architecture

The separation of Identity (permanent) / Sandbox (per-assignment) / Session (per-step) is distinctive. It allows:

- Session cycling without losing work
- Persistent skill tracking across ephemeral workers
- Clean sandbox lifecycle (created on sling, nuked on done)
- No "idle pool" -- polecats exist only while working

### 3. Self-Cleaning Worker Model

Polecats are responsible for their own cleanup via `gt done`. From docs/concepts/polecat-lifecycle.md:35-49:

> Polecats are responsible for their own cleanup. When a polecat completes its work unit, it:
> 1. Signals completion via `gt done`
> 2. Exits its session immediately (no idle waiting)
> 3. Requests its own nuke (self-delete)

This removes dependency on the Witness/Deacon for cleanup and eliminates the "idle polecat" failure mode.

### 4. Intelligent Watchdog Chain

The three-tier Daemon/Boot/Deacon chain is distinctive:

- **Daemon** (Go process): Mechanical heartbeat, cannot reason
- **Boot** (AI agent): Ephemeral triage, fresh each tick, decides if Deacon should wake
- **Deacon** (AI agent): Continuous patrol, monitors workers

From docs/design/watchdog-chain.md:21-23:

> Key insight: The daemon is mechanical (cannot reason), but health decisions need intelligence (is the agent stuck or just thinking?). Boot bridges this gap.

The key innovation is using an ephemeral AI agent (Boot) for intelligent triage without the cost of keeping a full AI running constantly.

### 5. Molecule-Based Workflow System

The Formula -> Protomolecule -> Molecule pipeline (from docs/concepts/molecules.md:7-16):

```
Formula (source TOML) --- "Ice-9"
    |
    v  bd cook
Protomolecule (frozen template) --- Solid
    |
    +-> bd mol pour --> Mol (persistent) --- Liquid --> bd squash --> Digest
    |
    +-> bd mol wisp --> Wisp (ephemeral) --- Vapor --> bd squash / bd burn
```

This provides reusable, versioned workflow templates that instantiate into trackable work with per-step progress. The chemistry metaphors (cook, pour, squash, burn) create a memorable ontology.

### 6. Universal Attribution via BD_ACTOR

Every action in the system is attributed to a specific agent identity. From docs/concepts/identity.md:43-47:

```
Git commits:    gastown/polecats/toast <owner@example.com>
Beads records:  created_by: gastown/crew/joe
Event logs:     actor: gastown/polecats/nux
```

This enables A/B model testing, capability-based routing, and compliance auditing -- all as emergent properties of attribution.

### 7. Git-Backed Persistent State

All state (beads, molecules, convoys, agent identity) is stored in git-backed databases. State transitions are git commits. This provides:

- Built-in versioning and rollback
- Multi-agent coordination through shared state
- Crash recovery (state survives agent restarts)
- Audit trail

The storage layer uses Dolt SQL Server (a git-for-data database), giving SQL query capability over git-versioned data.

### 8. The Seance System

Agents can query their predecessors for context:

From docs/glossary.md:86-87:

> Seance: Communicating with previous sessions via `gt seance`. Allows agents to query their predecessors for context and decisions from earlier work.

```bash
gt seance --talk <id> -p "Where is X?"  # One-shot question to predecessor
```

This is a distinctive approach to context recovery across session boundaries.

### 9. Formula Resolution with Three-Tier Precedence

From docs/formula-resolution.md:24-47:

```
TIER 1: PROJECT (rig-level)   -- most specific wins
TIER 2: TOWN (user-level)     -- Mol Mall installs, user customizations
TIER 3: SYSTEM (embedded)     -- compiled into gt binary, fallback
```

This allows project-specific workflows to override town-level defaults, which override system defaults.

### 10. Cross-Rig Work Tracking

Convoys live at the town level (hq-* prefix) but track issues from any rig. This enables unified tracking of work that spans multiple repositories.

### Known Limitations and Gaps

1. **Tmux dependency for Full Stack Mode**: The daemon and agent sessions require tmux. Without it, the system operates in degraded mode with mechanical-only health checks.

2. **Convoy completion is partially poll-based**: The design document (docs/design/convoy-lifecycle.md:8-11) identifies this as a structural gap:
   > The `???` is "Deacon patrol runs `gt convoy check`" -- a poll-based single point of failure. When Deacon is down, convoys don't close.

3. **No formal planning gate**: The system does not have a mechanism for determining when planning is "complete enough" before starting execution. The Mayor starts slinging work immediately after decomposition.

4. **Formula ecosystem is nascent**: Mol Mall (the formula marketplace) is designed but not yet launched. Currently formulas are local TOML files.

5. **Federation is future**: Cross-organization formula sharing and federated workspaces via HOP (Highway Operations Protocol) are designed but not implemented.

6. **Agent intelligence limits**: The system relies on AI agents making correct decisions (e.g., knowing when to handoff, when to escalate). Agent reliability is managed through monitoring and nudging, not prevented structurally.

7. **Single-runtime constraint per session**: Each polecat session runs one AI runtime. The system supports multiple runtimes (Claude, Codex, Gemini) but not within a single agent session.

---

## Summary: Key Takeaways for Autonomous Refinement System Design

### What Gas Town Does Well

1. **Structured attribution** creates a foundation for quality measurement and routing
2. **Three-layer polecat architecture** cleanly separates identity, workspace, and session concerns
3. **Self-cleaning model** eliminates idle worker states and their associated failure modes
4. **Intelligent watchdog chain** provides autonomous recovery with escalation paths to humans
5. **Git-backed everything** provides crash recovery, audit trails, and versioning for free
6. **Molecule workflow system** provides reusable, trackable, step-based execution with propulsion
7. **Escalation protocol** provides structured paths from automated to human decision-making

### What Gas Town Does Not Do

1. Does not front-load planning extensively -- decomposition happens on the fly
2. Does not verify agent output quality structurally (relies on self-reported completion + Refinery merge)
3. Does not have iterative refinement loops -- work goes forward, never back
4. Does not have formal convergence criteria beyond "all issues closed"
5. Does not grade or score output quality -- tracks completion metrics, not quality metrics

### Design Patterns Worth Adopting

- **The Propulsion Principle**: Eliminate waiting. Work on hook = execute immediately.
- **Three-layer lifecycle**: Separate what persists (identity/CV) from what cycles (session) from what is assignment-scoped (sandbox).
- **Self-cleaning workers**: Workers own their cleanup. No idle state. Done means gone.
- **Tiered watchdog chain**: Mechanical heartbeat -> intelligent triage -> continuous patrol.
- **Nondeterministic idempotence**: Any worker can continue any molecule. Steps are atomic checkpoints.
- **Universal attribution**: Every action has an actor. Build quality metrics as emergent property.
