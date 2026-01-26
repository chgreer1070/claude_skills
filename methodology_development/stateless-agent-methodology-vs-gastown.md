# Stateless Agent Methodology vs Gas Town

A comparative analysis of two approaches to working effectively with LLM agents at different scales.

---

## Executive Summary

Both methodologies address LLM agent limitations but target fundamentally different scales and concerns. Both recognize that Claude is not a knowledge worker—Claude is a stateless computation engine.

| Aspect              | Stateless Agent Methodology                       | Gas Town                                          |
| ------------------- | ------------------------------------------------- | ------------------------------------------------- |
| **Origin**          | Theoretical framework from observed failure modes | Production multi-agent orchestration system       |
| **Scale**           | Single agent, sequential stages                   | 20-30+ concurrent agents across multiple projects |
| **Primary Problem** | Agent self-assessment failure                     | Agent coordination at enterprise scale            |
| **State Model**     | Stateless (complete context per stage)            | Persistent (git-backed work tracking)             |
| **Implementation**  | Conceptual methodology                            | Go CLI (`gt`) with full tooling                   |

---

## Problem Statement Comparison

### Stateless Agent Methodology

Focuses on **why individual agents fail**:

- Context degradation at ~80% window
- Training data bias in one-shot approaches
- Cannot perform JIT knowledge gap identification
- Optimizes for apparent completion over correct completion

### Gas Town

Focuses on **why multi-agent systems fail**:

- Agents lose context on restart
- Manual coordination doesn't scale
- Chaotic state in multi-agent environments
- Lost work when sessions crash
- No attribution or accountability

### Overlapping Concerns

| Concern       | Stateless Approach              | Gas Town Approach                   |
| ------------- | ------------------------------- | ----------------------------------- |
| Context loss  | Fresh context per phase         | Persistent hooks + handoff protocol |
| Work tracking | Task files with all constraints | Beads ledger (git-backed JSONL)     |
| Verification  | Independent forensic phase      | Witness agent + quality gates       |
| Coordination  | Orchestrator dispatches workers | Mail protocol + nudging system      |

---

## Architectural Comparison

### Stateless Agent Methodology: Linear Stages

```
Discovery → Planning (RT-ICA) → Context Integration → Task Decomposition → Execution → Forensic Review → Final Verification
(with Orchestration loop between Execution and Forensic Review)
```

Each stage:

- Receives complete context
- Produces artifacts for next stage
- No memory dependency between stages

### Gas Town: Persistent Mesh Architecture

```
                    ┌─────────┐
                    │  Mayor  │ (coordinates all)
                    └────┬────┘
         ┌───────────────┼───────────────┐
         ▼               ▼               ▼
    ┌─────────┐    ┌─────────┐    ┌─────────┐
    │  Rig A  │    │  Rig B  │    │  Rig C  │
    └────┬────┘    └────┬────┘    └────┬────┘
         │               │               │
    ┌────┴────┐    ┌────┴────┐    ┌────┴────┐
    │ Witness │    │ Witness │    │ Witness │
    │Refinery │    │Refinery │    │Refinery │
    │Polecats │    │Polecats │    │Polecats │
    └─────────┘    └─────────┘    └─────────┘
```

Core entities:

- **Mayor**: Chief coordinator with cross-rig visibility
- **Witness**: Per-rig monitor for agent health
- **Refinery**: Per-rig merge queue processor
- **Polecats**: Ephemeral worker agents
- **Deacon**: System daemon watchdog

---

## Core Concepts Mapping

| SAM Concept     | Gas Town Equivalent       | Key Difference                       |
| --------------- | ------------------------- | ------------------------------------ |
| Stage           | Molecule step             | Molecules can span agent restarts    |
| Task file       | Bead                      | Beads persist in git, not files      |
| Orchestrator    | Mayor                     | Mayor coordinates multiple rigs      |
| Execution agent | Polecat                   | Polecats are ephemeral by design     |
| Forensic agent  | Witness                   | Witness also handles nudging/cleanup |
| Task queue      | Hook                      | Hooks are pinned Beads per agent     |
| Artifact        | Bead closure + git commit | Everything attributed and tracked    |

---

## State Management Philosophy

### Stateless Agent Methodology

**Principle**: Statelessness is a feature, not a limitation.

- Each phase receives complete context
- No phase depends on agent "remembering"
- Task files contain all answers
- Fresh session = fresh context = no degradation

**Implementation**: Phase artifacts are the only state.

### Gas Town

**Principle**: State must survive agent death.

- Work persists in git-backed hooks
- Agents spawn fresh but find work waiting
- Handoff mechanism transfers context between sessions
- Seance system queries previous sessions for history

**Implementation**: Three persistence layers:

| Layer   | Component          | Lifecycle                  |
| ------- | ------------------ | -------------------------- |
| Session | Claude (tmux pane) | Ephemeral, cycles per step |
| Sandbox | Git worktree       | Persistent until nuke      |
| Slot    | Name from pool     | Persistent until nuke      |

### Key Insight

Stateless methodology says: "Don't rely on state—provide complete context."

Gas Town says: "State will be lost—persist it externally so agents can recover."

Both acknowledge the same problem; different solutions for different scales.

---

## Execution Models

### Stateless: Sequential Phases

```
Phase 1 completes → Artifact → Phase 2 starts → Artifact → Phase 3 starts ...
```

- One agent per phase (conceptually)
- Phases are independent units
- Sequential by design
- Parallelism not addressed

### Gas Town: Propulsion Loop

```
1. gt hook                    # What's hooked?
2. bd mol current             # Where am I in molecule?
3. Execute step
4. bd close <step> --continue # Close and auto-advance
5. GOTO 2
```

**GUPP (Gas Town Universal Propulsion Principle)**:

> "If there is work on your Hook, YOU MUST RUN IT."

- No confirmation needed
- No waiting for external input
- The hook IS the assignment
- Prevents stalling

### Parallelism Comparison

| Aspect              | Stateless               | Gas Town                                |
| ------------------- | ----------------------- | --------------------------------------- |
| Concurrent agents   | Not addressed           | 20-30+                                  |
| Work distribution   | Orchestrator dispatches | Slinging via `gt sling`                 |
| Dependency tracking | Phase order             | Formula dependencies + topological sort |
| Synchronization     | Phase boundaries        | Mail protocol + Convoy tracking         |

---

## Agent Coordination

### Stateless Methodology

Implicit coordination through artifacts:

1. Discovery agent produces requirements
2. Assessment agent reads requirements, produces design
3. Integration agent reads design, produces plan
4. Execution agent reads plan, produces code
5. Forensic agent reads code, produces report

**Coordination mechanism**: Artifacts passed between phases.

### Gas Town

Explicit coordination through mail protocol:

| Message      | Sender   | Receiver | Purpose                |
| ------------ | -------- | -------- | ---------------------- |
| POLECAT_DONE | Polecat  | Witness  | Signal work completion |
| MERGE_READY  | Witness  | Refinery | Branch ready for merge |
| MERGED       | Refinery | Witness  | Safe to cleanup        |
| MERGE_FAILED | Refinery | Witness  | Recovery needed        |

**Additional mechanisms**:

- **Nudging**: Real-time messaging via `gt nudge`
- **Handoff**: Session refresh via `/handoff`
- **Seance**: Query previous sessions via `gt seance`

---

## Work Decomposition

### Stateless Methodology

```
Feature → Requirements → Design → Tasks → Subtasks
```

Task files contain:

- Exact constraints
- Files to modify
- Style to follow
- Methodology to use
- Verification steps
- Definition of done

### Gas Town (MEOW - Molecular Expression of Work)

```
Epic → Feature → Task → Bead → Molecule Step
```

**Hierarchy**:

| Level    | Description         | Tracking                       |
| -------- | ------------------- | ------------------------------ |
| Epic     | Large goal          | Bead with children             |
| Feature  | Logical unit        | Bead with children             |
| Task     | Atomic work         | Bead                           |
| Molecule | Multi-step workflow | Persistent, survives restarts  |
| Step     | Single action       | Auto-advances via `--continue` |

**Formula types**:

- **Workflow**: Sequential steps with dependencies
- **Convoy**: Parallel legs with optional synthesis
- **Expansion**: Template-based parameterized workflows
- **Aspect**: Multi-aspect parallel analysis

---

## Attribution and Accountability

### Stateless Methodology

Not explicitly addressed. Implicit through:

- Task files record what was requested
- Forensic phase verifies completion
- Orchestrator tracks task status

### Gas Town

Comprehensive attribution system (BD_ACTOR format):

```
mayor                           # Town-level
deacon                          # Town-level
gastown/witness                 # Rig-level
gastown/refinery                # Rig-level
gastown/crew/joe                # Crew member
gastown/polecats/toast          # Polecat worker
```

**Three-level attribution**:

1. **Git commits**: `GIT_AUTHOR_NAME` tracks who did work
2. **Beads records**: `created_by`/`updated_by` fields
3. **Event logging**: All events include actor attribution

**Benefits**:

- Compliance audits
- Agent capability tracking (CV growth)
- Performance management
- Skill-based routing

---

## Failure Handling

### Stateless Methodology

| Failure Mode                  | Mitigation                       |
| ----------------------------- | -------------------------------- |
| Training data hallucination   | Task files contain all facts     |
| Skipping prerequisites        | Assessment phase blocks planning |
| Apparent vs actual completion | Forensic phase verification      |
| Context degradation           | Fresh context per phase          |

**Recovery**: Manual intervention via orchestrator.

### Gas Town

| Failure Mode    | Mitigation                                 |
| --------------- | ------------------------------------------ |
| Agent crash     | Hook persists, work recoverable            |
| Stalled session | Witness nudges or respawns                 |
| Zombie agent    | Witness cleanup protocol                   |
| Merge conflict  | Refinery retry with intelligent resolution |
| Lost context    | Handoff protocol + seance history          |

**Polecat states**:

| State   | Description                  | Recovery         |
| ------- | ---------------------------- | ---------------- |
| Working | Actively executing           | Normal operation |
| Stalled | Session stopped mid-work     | Witness nudge    |
| Zombie  | Completed but failed to exit | Witness cleanup  |

**Key insight**: No idle state. Polecats work or die.

---

## Verification Models

### Stateless: Independent Forensic Phase

```
Execution → Forensics → Complete/Incomplete → (loop if incomplete)
```

- Forensic agent validates against plan
- Reports status objectively
- Orchestrator creates follow-up tasks

### Gas Town: Multi-Layer Verification

```
                    ┌─────────────┐
                    │   Deacon    │ (system health)
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
         ┌─────────┐ ┌─────────┐ ┌─────────┐
         │ Witness │ │ Witness │ │ Witness │ (per-rig)
         └────┬────┘ └────┬────┘ └────┬────┘
              │            │            │
              ▼            ▼            ▼
         ┌─────────┐ ┌─────────┐ ┌─────────┐
         │Refinery │ │Refinery │ │Refinery │ (merge gates)
         └─────────┘ └─────────┘ └─────────┘
```

- **Witness**: Monitors polecats, handles failures
- **Refinery**: Merge queue with quality gates
- **Deacon**: System-wide watchdog

**NDI (Nondeterministic Idempotence)**: Ensures useful outcomes even with unreliable processes through persistent Beads and oversight agents.

---

## Scale Comparison

| Dimension         | Stateless Methodology   | Gas Town                 |
| ----------------- | ----------------------- | ------------------------ |
| Agents            | 7 stages + loop         | 20-30+ concurrent        |
| Projects          | Single feature          | Multiple rigs (projects) |
| Organization      | Single team             | Federation across orgs   |
| State persistence | None (intentional)      | Git-backed everything    |
| Tooling           | None (methodology only) | Full CLI (`gt`, `bd`)    |
| Runtime           | Any LLM agent           | Claude Code / Codex      |

---

## Enterprise Features (Gas Town Only)

Features not addressed by Stateless Methodology:

| Feature                  | Gas Town Implementation                   |
| ------------------------ | ----------------------------------------- |
| **Federation**           | Register and query remote workspaces      |
| **Model A/B testing**    | Deploy different LLMs on comparable tasks |
| **Capability routing**   | Match work to agents by proven skills     |
| **Agent CVs**            | Track record of completed work            |
| **Real-time feed**       | Stream of system state changes            |
| **Cross-org visibility** | Multi-team coordination                   |

---

## Complementary Insights

### What Gas Town Validates from Stateless Methodology

1. **Externalized assessment**: Witness/Deacon separate from execution
2. **Complete context per unit**: Hooks contain all work state
3. **Fresh sessions work**: Polecats spawn fresh, find work waiting
4. **Verification independence**: Refinery gates separate from execution

### What Gas Town Adds

1. **Persistence layer**: Work survives agent death
2. **Attribution system**: Who did what, when, why
3. **Scale mechanism**: Coordination for dozens of agents
4. **Recovery protocols**: Nudge, handoff, seance
5. **Quality routing**: Match work to capable agents

### What Stateless Methodology Clarifies

1. **Why agents fail**: Core dysfunction analysis
2. **Theoretical foundation**: Principles behind the patterns
3. **Minimal viable process**: 7 stages + orchestration loop without tooling overhead
4. **Agent-agnostic**: Not tied to specific runtime

---

## Synthesis: When to Use Each

### Use Stateless Agent Methodology When

- Working with single agent or small team
- Need conceptual framework before tooling
- Target runtime is not Claude Code
- Emphasizing principles over implementation
- Teaching/explaining LLM agent design

### Use Gas Town When

- Coordinating 5+ concurrent agents
- Need attribution and accountability
- Enterprise compliance requirements
- Multi-project orchestration
- Recovery from agent failures is critical
- Scale is the primary concern

### Use Both When

- Designing new multi-agent systems
- Need theoretical grounding + practical implementation
- Building custom orchestration (use stateless principles, gas town patterns)
- Debugging coordination failures (stateless explains why, gas town shows how)

---

## Architectural Pattern Comparison

### Stateless: Pipeline Architecture

```
┌────────┐    ┌────────┐    ┌────────┐    ┌────────┐
│Discover│───▶│  Plan  │───▶│Execute │───▶│ Verify │
│        │    │        │    │        │    │        │
│Complete│    │Complete│    │Complete│    │Complete│
│context │    │context │    │context │    │context │
└────────┘    └────────┘    └────────┘    └────────┘
     │             │             │             │
     ▼             ▼             ▼             ▼
 ┌───────┐    ┌───────┐    ┌───────┐    ┌───────┐
 │Artifact│   │Artifact│   │Artifact│   │Artifact│
 └───────┘    └───────┘    └───────┘    └───────┘
```

### Gas Town: Mesh + Queue Architecture

```
                    ┌─────────────────┐
                    │     Deacon      │
                    │  (watchdog)     │
                    └────────┬────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
        ▼                    ▼                    ▼
   ┌─────────┐         ┌─────────┐         ┌─────────┐
   │  Mayor  │────────▶│ Convoy  │◀────────│  Mail   │
   │(coord)  │         │(batch)  │         │(queue)  │
   └────┬────┘         └────┬────┘         └────┬────┘
        │                   │                   │
   ┌────┴────┐         ┌────┴────┐         ┌────┴────┐
   │   Rig   │         │   Rig   │         │   Rig   │
   │┌───────┐│         │┌───────┐│         │┌───────┐│
   ││Witness││         ││Witness││         ││Witness││
   │├───────┤│         │├───────┤│         │├───────┤│
   ││Refnry ││         ││Refnry ││         ││Refnry ││
   │├───────┤│         │├───────┤│         │├───────┤│
   ││Polcats││         ││Polcats││         ││Polcats││
   │└───────┘│         │└───────┘│         │└───────┘│
   └─────────┘         └─────────┘         └─────────┘
```

---

## Conclusion

The Stateless Agent Methodology and Gas Town represent **different points on the complexity spectrum**.

| Dimension  | Stateless         | Gas Town               |
| ---------- | ----------------- | ---------------------- |
| Complexity | Low (conceptual)  | High (production)      |
| Scale      | 1-5 agents        | 20-30+ agents          |
| State      | None (deliberate) | Persistent (essential) |
| Focus      | Why agents fail   | How to coordinate many |
| Value      | Principles        | Implementation         |

**Key insight**: Stateless methodology explains _why_ certain patterns work. Gas Town implements those patterns _at scale_ with the additional machinery needed for enterprise coordination.

They are not alternatives—they are **different abstraction levels** of the same fundamental understanding: LLM agents cannot self-assess, so systems must externalize assessment, provide complete context, and verify independently.

- **Stateless Agent Methodology** = Theory for single-agent reliability
- **Gas Town** = Implementation for multi-agent coordination

Together they span from "why does this work?" to "how do I run 30 agents across 5 projects?"
