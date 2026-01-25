# Plugin-Creator vs Gastown Comparison

This document compares the plugin-creator agentic workflow with the [Gastown MEOW methodology](https://github.com/steveyegge/gastown).

---

## Executive Summary

| Aspect          | Plugin-Creator              | Gastown MEOW                        |
| --------------- | --------------------------- | ----------------------------------- |
| **Focus**       | Single plugin creation task | Multi-agent workspace orchestration |
| **Scale**       | 1-6 agents per task         | 20-30+ agents across projects       |
| **Persistence** | None (session-based)        | Git worktrees survive restarts      |
| **Coordinator** | Ephemeral orchestrator      | Persistent Mayor                    |
| **Work Items**  | Phases/tasks                | Beads/issues in convoys             |
| **Best For**    | Focused creation workflow   | Long-running distributed work       |

---

## Workflow Phase Comparison

### Plugin-Creator (7 Phases)

```mermaid
flowchart LR
    P0[Phase 0<br>RT-ICA] --> P1[Phase 1<br>Research]
    P1 --> P2[Phase 2<br>Design]
    P2 --> P3[Phase 3<br>Implement]
    P3 --> P4[Phase 4<br>Validate]
    P4 --> P5[Phase 5<br>Document]
    P5 --> P6[Phase 6<br>Verify]

    P0 -.-> |Explore| P1
    P1 -.-> |Plan| P2
    P4 -.-> |plugin-assessor| P4
    P5 -.-> |plugin-docs-writer| P5
```

### Gastown MEOW (7 Phases)

```mermaid
flowchart LR
    M1[Phase 1<br>Tell Mayor] --> M2[Phase 2<br>Mayor Analyzes]
    M2 --> M3[Phase 3<br>Convoy Creation]
    M3 --> M4[Phase 4<br>Spawn Agents]
    M4 --> M5[Phase 5<br>Distribute Work]
    M5 --> M6[Phase 6<br>Monitor Progress]
    M6 --> M7[Phase 7<br>Complete & Report]

    M4 -.-> |Polecats| M4
    M5 -.-> |via Hooks| M5
    M6 -.-> |Convoy queries| M6
```

---

## Conceptual Mapping

| Plugin-Creator Concept | Gastown Equivalent | Notes                                         |
| ---------------------- | ------------------ | --------------------------------------------- |
| Orchestrator           | Mayor              | Both coordinate work, but Mayor is persistent |
| Explore/Plan agents    | Polecats           | Ephemeral workers that complete tasks         |
| Phases (0-6)           | Convoys            | Bundled related work items                    |
| Individual tasks       | Beads/Issues       | Atomic work units                             |
| SKILL.md output        | Hook artifacts     | Persistent deliverables                       |
| RT-ICA checkpoint      | "Tell Mayor"       | Initial work decomposition                    |
| verify skill           | Completion report  | Final synthesis                               |

---

## Key Architectural Differences

### 1. Persistence Model

```mermaid
flowchart TD
    subgraph "Plugin-Creator: SESSION-BASED"
        PC1[Work in conversation context]
        PC2[Agent results returned directly]
        PC3[No survival across restarts]
        PC4[Files are only artifacts]
    end

    subgraph "Gastown: GIT WORKTREE-BASED"
        GT1[Each hook is a git worktree]
        GT2[Work survives crashes/restarts]
        GT3[Full version control of state]
        GT4[Rollback to any previous state]
        GT5[Multi-agent coordination via git]
    end
```

### 2. Coordinator Role

```mermaid
flowchart TD
    subgraph "Plugin-Creator Orchestrator"
        PCO1[Current Claude session]
        PCO2[Delegates via Task tool]
        PCO3[No persistent state]
        PCO4[Sequential workflow]
    end

    subgraph "Gastown Mayor"
        GTM1[Persistent Claude instance]
        GTM2[Full contextual awareness]
        GTM3[Continuous presence]
        GTM4[Massive parallelization]
    end
```

### 3. Work Tracking

```mermaid
flowchart LR
    subgraph "Plugin-Creator"
        PC1[Implicit tracking via conversation]
        PC2[TodoWrite for progress]
        PC3[No formal work IDs]
        PC4[Results inline]
    end

    subgraph "Gastown"
        GT1["Beads with unique IDs (gt-abc12)"]
        GT2[Convoys bundle beads]
        GT3[Status queries across work]
        GT4[Dashboard visibility]
    end
```

---

## What Plugin-Creator Could Learn from Gastown

### 1. Persistence Layer

```mermaid
flowchart TD
    CRASH[Session Crashes] --> CHECK{Checkpoint exists?}
    CHECK -->|No| RESTART[Start over]
    CHECK -->|Yes| RESUME[Resume from checkpoint]

    subgraph "Proposed Checkpoints"
        CP0[phase-0-rtica.json]
        CP1[phase-1-research.json]
        CP2[phase-2-design.json]
        CP4[phase-4-validation.json]
    end
```

### 2. Formal Work Items

```mermaid
flowchart TD
    CONVOY[Convoy: my-plugin-creation] --> B1[Bead pc-001<br>Research<br>status: complete]
    CONVOY --> B2[Bead pc-002<br>Design<br>status: in-progress]
    CONVOY --> B3[Bead pc-003<br>Implementation<br>status: pending]

    B1 --> |depends| B2
    B2 --> |depends| B3
```

### 3. Parallel Agent Spawning

```mermaid
flowchart TD
    PHASE1[Phase 1 Research] --> PAR{Parallel Spawn}
    PAR --> E1[Explore: Check existing]
    PAR --> E2[Explore: Domain knowledge]
    PAR --> GP[general-purpose: Official docs]

    E1 --> MERGE[Merge Results]
    E2 --> MERGE
    GP --> MERGE
```

---

## What Gastown Could Learn from Plugin-Creator

### 1. Domain-Specific Agents

```mermaid
flowchart LR
    subgraph "Plugin-Creator Specialized Agents"
        A1[Explore] --> A1T[Read-only discovery]
        A2[Plan] --> A2T[Architecture]
        A3[plugin-assessor] --> A3T[Quality review]
        A4[plugin-docs-writer] --> A4T[Documentation]
    end

    subgraph "Gastown"
        B1[Polecats] --> B1T[Generic workers]
    end
```

### 2. Verification Integration

```mermaid
flowchart TD
    IMPL[Implementation] --> V1[RT-ICA prereq check]
    V1 --> V2[Automated validation scripts]
    V2 --> V3[Official docs comparison]
    V3 --> V4[verify skill final gate]
    V4 --> COMPLETE[Complete with evidence]
```

---

## Hybrid Approach

```mermaid
flowchart TD
    subgraph "Gastown Layer"
        GL1[Mayor coordinates]
        GL2[Convoy tracks work]
        GL3[Hooks persist state]
        GL4["gt prime restores context"]
    end

    subgraph "Plugin-Creator Layer"
        PCL1[Specialized agents]
        PCL2[RT-ICA verification]
        PCL3[Official docs checks]
        PCL4[Advanced features guidance]
        PCL5[Validation scripts]
    end

    GL1 --> PCL1
    GL2 --> PCL2
    GL3 --> PCL5
    GL4 --> PCL3

    subgraph "Combined Benefits"
        CB1[Persistent state - Gastown]
        CB2[Domain-specific agents - Plugin-Creator]
        CB3[Formal work tracking - Gastown]
        CB4[Verification gates - Plugin-Creator]
        CB5[Scalable parallelism - Gastown]
        CB6[Anti-hallucination - Plugin-Creator]
    end
```

---

## Recommendation

| Use Case                                         | Recommended Approach    |
| ------------------------------------------------ | ----------------------- |
| Single plugin creation                           | Plugin-Creator workflow |
| Large-scale plugin dev (multiple plugins, teams) | Gastown integration     |
| Critical plugins                                 | Hybrid approach         |

**Single plugin**: Plugin-Creator provides focused guidance, verification, no infrastructure overhead.

**Large-scale**: Gastown provides persistence, parallel coordination, work tracking across projects.

**Critical**: Hybrid combines Gastown's persistence with Plugin-Creator's verification and specialized agents.

---

## Sources

- [Gastown Repository](https://github.com/steveyegge/gastown)
- [Plugin-Creator SKILL.md](../SKILL.md)
- [Plugin-Creator Workflow Diagram](./workflow-diagram.md)
