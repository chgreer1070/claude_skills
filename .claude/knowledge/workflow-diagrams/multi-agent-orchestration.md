# Multi-Agent Orchestration Sequence

Delegation flow with DONE/BLOCKED signaling between orchestrator and specialist agents.

---

## Overview

```mermaid
sequenceDiagram
    participant U as User
    participant O as Orchestrator
    participant S1 as Sub-Agent 1
    participant S2 as Sub-Agent 2

    U->>O: Request task
    O->>O: Plan decomposition
    O->>S1: Delegate subtask A
    activate S1
    S1->>S1: Execute autonomously
    S1-->>O: DONE + results
    deactivate S1
    O->>S2: Delegate subtask B
    activate S2
    S2->>S2: Execute autonomously
    S2-->>O: BLOCKED + reason
    deactivate S2
    O->>O: Handle blocked state
    O->>U: Report status
```

---

## Delegation Framework (WHERE-WHAT-WHY)

The `delegate` skill provides the core delegation template:

```mermaid
flowchart TB
    subgraph WHERE["WHERE (Context)"]
        W1["Working directory"]
        W2["Relevant files"]
        W3["System state"]
    end

    subgraph WHAT["WHAT (Task)"]
        T1["Concrete deliverable"]
        T2["Acceptance criteria"]
        T3["Constraints"]
    end

    subgraph WHY["WHY (Purpose)"]
        P1["Business context"]
        P2["How it fits larger goal"]
        P3["Success definition"]
    end

    WHERE --> DELEGATION["Complete Delegation"]
    WHAT --> DELEGATION
    WHY --> DELEGATION
```

**Key Principle:** Provide WHERE, WHAT, and WHY - never dictate HOW. The sub-agent determines implementation.

---

## Full Orchestration Sequence

```mermaid
sequenceDiagram
    participant U as User
    participant O as Orchestrator
    participant SK as Skills
    participant AG as Agents

    rect rgb(200, 230, 200)
        Note over O: PLANNING PHASE
        O->>SK: Load delegate skill
        SK-->>O: WHERE-WHAT-WHY template
        O->>SK: Load rt-ica skill
        SK-->>O: Prerequisites verified
    end

    rect rgb(200, 200, 230)
        Note over O: EXECUTION PHASE
        O->>AG: Agent(agent, prompt)
        activate AG
        AG->>SK: Load subagent-contract
        SK-->>AG: Role boundaries
        AG->>AG: Execute within scope
        alt Success
            AG-->>O: DONE: [deliverable]
        else Blocked
            AG-->>O: BLOCKED: [reason]
        end
        deactivate AG
    end

    rect rgb(230, 200, 200)
        Note over O: VERIFICATION PHASE
        O->>SK: Load /dh:verify-done skill
        SK-->>O: Completion checklist
        O->>O: Verify deliverable
    end

    O->>U: Report completion
```

---

## DONE/BLOCKED Signaling Protocol

From `subagent-contract` skill:

```mermaid
stateDiagram-v2
    [*] --> Working: Task received
    Working --> DONE: Deliverable complete
    Working --> BLOCKED: Cannot proceed

    DONE --> [*]: Return results
    BLOCKED --> [*]: Return reason

    state DONE {
        [*] --> Summarize
        Summarize --> Evidence
        Evidence --> [*]
    }

    state BLOCKED {
        [*] --> Identify
        Identify --> Explain
        Explain --> [*]
    }
```

### DONE Signal Format

```text
DONE:
- Summary: [What was accomplished]
- Deliverable: [Concrete output reference]
- Evidence: [Verification of completion]
```

### BLOCKED Signal Format

```text
BLOCKED:
- Blocker: [What prevents completion]
- Attempted: [What was tried]
- Needed: [What would unblock]
```

---

## Parallel vs Sequential Delegation

### Parallel Delegation

```mermaid
flowchart TB
    O["Orchestrator"]
    A1["Agent A"]
    A2["Agent B"]
    A3["Agent C"]
    COLLECT["Collect Results"]

    O -->|"Task A"| A1
    O -->|"Task B"| A2
    O -->|"Task C"| A3

    A1 -->|"DONE"| COLLECT
    A2 -->|"DONE"| COLLECT
    A3 -->|"BLOCKED"| COLLECT

    COLLECT --> O
```

**Use When:**

- Tasks are independent
- No data dependencies between tasks
- Context windows won't interfere

### Sequential Delegation

```mermaid
flowchart TB
    O["Orchestrator"]
    A1["Agent A"]
    A2["Agent B"]
    A3["Agent C"]

    O -->|"Task A"| A1
    A1 -->|"DONE + Data"| O
    O -->|"Task B + Data"| A2
    A2 -->|"DONE + Data"| O
    O -->|"Task C + Data"| A3
    A3 -->|"DONE"| O
```

**Use When:**

- Later tasks depend on earlier results
- Need to pass data between agents
- Must verify intermediate results

---

## Handling BLOCKED Agents

```mermaid
flowchart TD
    BLOCKED["Agent returns BLOCKED"]

    Q1{"Can orchestrator<br/>resolve blocker?"}
    Q2{"Alternative<br/>agent available?"}
    Q3{"Can decompose<br/>differently?"}

    RESOLVE["Provide missing info<br/>Re-delegate"]
    ALTERNATE["Delegate to<br/>different agent"]
    REPLAN["Revise plan<br/>New decomposition"]
    ESCALATE["Escalate to user"]

    BLOCKED --> Q1
    Q1 -->|"Yes"| RESOLVE
    Q1 -->|"No"| Q2
    Q2 -->|"Yes"| ALTERNATE
    Q2 -->|"No"| Q3
    Q3 -->|"Yes"| REPLAN
    Q3 -->|"No"| ESCALATE

    RESOLVE --> RETRY["Re-delegate"]
    ALTERNATE --> RETRY
    REPLAN --> RETRY
```

---

## Agent Selection Guide

```mermaid
flowchart TD
    TASK["Task to delegate"]

    Q1{"Research or<br/>context needed?"}
    Q2{"Code quality<br/>review?"}
    Q3{"Plugin<br/>assessment?"}
    Q4{"Documentation<br/>generation?"}
    Q5{"Skill<br/>refactoring?"}
    Q6{"Agent prompt<br/>improvement?"}

    A1["context-gathering"]
    A2["code-review"]
    A3["plugin-assessor"]
    A4["plugin-docs-writer"]
    A5["skill-refactorer"]
    A6["subagent-refactorer"]
    A7["subagent-generator"]

    TASK --> Q1
    Q1 -->|"Yes"| A1
    Q1 -->|"No"| Q2
    Q2 -->|"Yes"| A2
    Q2 -->|"No"| Q3
    Q3 -->|"Yes"| A3
    Q3 -->|"No"| Q4
    Q4 -->|"Yes"| A4
    Q4 -->|"No"| Q5
    Q5 -->|"Yes"| A5
    Q5 -->|"No"| Q6
    Q6 -->|"Yes"| A6
    Q6 -->|"Create new"| A7
```

---

## Complete Orchestration Example

```mermaid
sequenceDiagram
    participant U as User
    participant O as Orchestrator
    participant CG as context-gathering
    participant CR as code-review
    participant PD as plugin-docs-writer

    U->>O: "Review and document the new plugin"

    Note over O: Phase 1: Plan
    O->>O: Load delegate skill
    O->>O: Decompose into 3 subtasks

    Note over O: Phase 2: Context
    O->>CG: Research plugin structure
    activate CG
    CG-->>O: DONE: Plugin analysis
    deactivate CG

    Note over O: Phase 3: Review
    O->>CR: Review plugin code quality
    activate CR
    CR-->>O: DONE: Quality report
    deactivate CR

    Note over O: Phase 4: Document
    O->>PD: Generate documentation
    activate PD
    PD-->>O: DONE: README + docs
    deactivate PD

    Note over O: Phase 5: Verify
    O->>O: Load /dh:verify-done skill
    O->>O: Check all deliverables

    O->>U: Complete: Plugin reviewed & documented
```

---

## Role Boundaries (subagent-contract)

```mermaid
flowchart TB
    subgraph ORCHESTRATOR["Orchestrator Responsibilities"]
        O1["Task decomposition"]
        O2["Agent selection"]
        O3["WHERE-WHAT-WHY context"]
        O4["Result verification"]
        O5["User communication"]
    end

    subgraph SUBAGENT["Sub-Agent Responsibilities"]
        S1["Implementation decisions"]
        S2["Tool selection"]
        S3["Execution within scope"]
        S4["DONE/BLOCKED signaling"]
        S5["Deliverable creation"]
    end

    subgraph BOUNDARY["Boundary Rules"]
        B1["Orchestrator: WHAT to achieve"]
        B2["Sub-agent: HOW to achieve"]
        B3["No scope creep"]
        B4["No assumption escalation"]
    end

    ORCHESTRATOR --> BOUNDARY
    SUBAGENT --> BOUNDARY
```

**Key Boundaries:**

| Orchestrator Does        | Sub-Agent Does                    |
| ------------------------ | --------------------------------- |
| Defines task scope       | Implements within scope           |
| Provides context         | Uses context appropriately        |
| Sets acceptance criteria | Meets criteria or signals BLOCKED |
| Handles blocked states   | Explains blockers clearly         |
| Verifies completion      | Provides evidence                 |

---

## Anti-Patterns

| Pattern            | Problem                       | Correct Approach                   |
| ------------------ | ----------------------------- | ---------------------------------- |
| Micro-managing HOW | Removes agent autonomy        | Specify WHAT, let agent decide HOW |
| Ignoring BLOCKED   | Leaves task incomplete        | Handle or escalate blocked states  |
| No verification    | May accept bad results        | Always verify deliverables         |
| Vague delegation   | Agent can't determine success | Include clear acceptance criteria  |
| Context overload   | Wastes context window         | Provide minimal sufficient context |

---

## Navigation

- **Previous:** [Asset Decision Tree](./asset-decision-tree.md)
- **Next:** [Simple Task Workflow](./simple-task-workflow.md)
- **Back to:** [Index](./README.md)
