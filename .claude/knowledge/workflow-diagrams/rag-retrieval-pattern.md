# RAG Retrieval Pattern

Context augmentation flow using skills, agents, and reference materials for knowledge retrieval.

---

## Overview

RAG (Retrieval-Augmented Generation) enhances responses by retrieving relevant context before generating. This pattern maps to repository assets.

```mermaid
flowchart LR
    QUERY["Query"]
    RETRIEVE["Retrieve<br/>Context"]
    AUGMENT["Augment<br/>Prompt"]
    GENERATE["Generate<br/>Response"]

    QUERY --> RETRIEVE --> AUGMENT --> GENERATE
```

---

## RAG Components in Repository

```mermaid
flowchart TB
    subgraph RETRIEVAL["Retrieval Layer"]
        R1["context-gathering agent<br/>Deep codebase research"]
        R2["Reference Skills<br/>(4 skills)"]
        R3["MCP Tools<br/>(context7, Ref, etc.)"]
    end

    subgraph AUGMENTATION["Augmentation Layer"]
        A1["Skills with references/<br/>Progressive disclosure"]
        A2["context-refinement agent<br/>Context manifest update"]
    end

    subgraph GENERATION["Generation Layer"]
        G1["Orchestrator<br/>Uses augmented context"]
        G2["Sub-agents<br/>Receive delegated context"]
    end

    RETRIEVAL --> AUGMENTATION --> GENERATION
```

---

## Reference Skills as Knowledge Base

```mermaid
flowchart TB
    subgraph SKILLS["Reference Skills"]
        S1["claude-skills-overview-2026<br/>Skills system documentation"]
        S2["claude-plugins-reference-2026<br/>Plugins system documentation"]
        S3["claude-commands-reference-2026<br/>Commands system documentation"]
        S4["claude-hooks-reference-2026<br/>Hooks system documentation"]
    end

    subgraph USAGE["Usage Patterns"]
        U1["Load via Skill() tool"]
        U2["Read references/ files on demand"]
        U3["Progressive disclosure"]
    end

    SKILLS --> U1
    U1 --> U2
    U2 --> U3
```

**Progressive Disclosure:**

```text
1. Load SKILL.md (core knowledge)
2. Follow links to references/ files (detailed knowledge)
3. Load only what's needed (context efficiency)
```

---

## Context-Gathering Agent Pattern

```mermaid
sequenceDiagram
    participant O as Orchestrator
    participant CG as context-gathering
    participant FS as File System
    participant TOOLS as External Tools

    O->>CG: Research request
    activate CG

    CG->>FS: Read relevant files
    FS-->>CG: File contents

    CG->>TOOLS: Search/fetch as needed
    TOOLS-->>CG: External data

    CG->>CG: Synthesize findings

    CG-->>O: DONE: Research summary
    deactivate CG

    O->>O: Use summary in context
```

**Why Use context-gathering:**

- Runs in separate context window
- Won't pollute orchestrator's context
- Can read extensively without token pressure
- Returns synthesized summary

---

## Retrieval Flow Detail

```mermaid
flowchart TB
    NEED["Knowledge<br/>needed"]

    Q1{"In loaded<br/>skills?"}
    Q2{"In reference<br/>files?"}
    Q3{"In codebase?"}
    Q4{"Needs external<br/>research?"}

    A1["Use loaded skill"]
    A2["Read reference file"]
    A3["Search/read codebase"]
    A4["Delegate to<br/>context-gathering"]

    NEED --> Q1
    Q1 -->|"Yes"| A1
    Q1 -->|"No"| Q2
    Q2 -->|"Yes"| A2
    Q2 -->|"No"| Q3
    Q3 -->|"Yes"| A3
    Q3 -->|"No"| Q4
    Q4 -->|"Yes"| A4
```

---

## MCP Tools for External Retrieval

```mermaid
flowchart TB
    subgraph MCP["MCP Tool Categories"]
        direction TB
        DOC["Documentation"]
        CODE["Code Search"]
        WEB["Web Search"]
    end

    subgraph TOOLS["Available Tools"]
        T1["mcp__Ref__ref_search_documentation"]
        T2["mcp__Ref__ref_read_url"]
        T3["mcp__context7__resolve-library-id"]
        T4["mcp__context7__query-docs"]
        T5["mcp__exa__get_code_context_exa"]
        T6["WebSearch"]
        T7["WebFetch"]
    end

    DOC --> T1 & T2 & T3 & T4
    CODE --> T5
    WEB --> T6 & T7
```

**Tool Selection:**

| Need                  | Tool                               |
| --------------------- | ---------------------------------- |
| Library documentation | context7 (resolve → query)         |
| Framework docs        | mcp**Ref**ref_search_documentation |
| Read specific URL     | mcp**Ref**ref_read_url             |
| Code examples         | mcp**exa**get_code_context_exa     |
| Current events/news   | WebSearch                          |
| Read web page         | WebFetch                           |

---

## Complete RAG Sequence

```mermaid
sequenceDiagram
    participant U as User
    participant O as Orchestrator
    participant SK as Skills
    participant AG as Agents
    participant MCP as MCP Tools

    U->>O: Question requiring context

    Note over O: 1. Check loaded skills
    O->>SK: Already loaded?
    SK-->>O: Partial match

    Note over O: 2. Load additional skill
    O->>SK: Skill(skill: "relevant-skill")
    SK-->>O: Skill loaded

    Note over O: 3. Check references
    O->>SK: Read ./references/detail.md
    SK-->>O: Reference content

    alt Still need more context
        Note over O: 4a. Codebase search
        O->>O: Grep/Glob/Read
    else Need external docs
        Note over O: 4b. External retrieval
        O->>MCP: context7 or Ref tools
        MCP-->>O: Documentation
    else Need extensive research
        Note over O: 4c. Delegate research
        O->>AG: context-gathering
        AG-->>O: Research summary
    end

    Note over O: 5. Generate response
    O->>O: Combine all context
    O->>U: Informed response
```

---

## Context Manifest Pattern

The `context-refinement` agent maintains a context manifest in task files:

```mermaid
flowchart TB
    subgraph MANIFEST["Context Manifest"]
        M1["Key files identified"]
        M2["Dependencies discovered"]
        M3["Patterns noted"]
        M4["Constraints documented"]
    end

    subgraph UPDATE["Update Triggers"]
        U1["New discovery during work"]
        U2["Context compaction needed"]
        U3["Task phase transition"]
    end

    subgraph USE["Usage"]
        US1["Quick context restoration"]
        US2["Sub-agent delegation"]
        US3["Session continuity"]
    end

    UPDATE --> MANIFEST --> USE
```

---

## Retrieval Efficiency Strategies

### 1. Progressive Loading

```mermaid
flowchart LR
    L1["Load SKILL.md<br/>(overview)"]
    L2["Load specific<br/>reference"]
    L3["Load additional<br/>details"]

    L1 -->|"Need more"| L2 -->|"Need more"| L3
```

**Don't:** Load all references upfront
**Do:** Load only what's needed for current question

### 2. Context Window Management

```mermaid
flowchart TD
    FULL["Context window<br/>getting full"]

    O1["Delegate to agent<br/>(separate window)"]
    O2["Summarize and<br/>compact context"]
    O3["Use context manifest<br/>for quick restore"]

    FULL --> O1
    FULL --> O2
    FULL --> O3
```

### 3. Caching Pattern (Gap)

```text
Currently: No context caching
Future: Could cache frequently-accessed context
```

---

## Asset-to-RAG Mapping

| RAG Stage               | Assets                                         |
| ----------------------- | ---------------------------------------------- |
| **Query Understanding** | rt-ica (clarify requirements)                  |
| **Retrieval**           | context-gathering, reference skills, MCP tools |
| **Augmentation**        | context-refinement, skill loading              |
| **Generation**          | Orchestrator with augmented context            |

---

## Example: Library Documentation Lookup

```mermaid
sequenceDiagram
    participant U as User
    participant O as Orchestrator
    participant C7 as context7

    U->>O: "How do I use FastMCP Image type?"

    O->>C7: resolve-library-id("fastmcp")
    C7-->>O: libraryId: "/jlowin/fastmcp"

    O->>C7: query-docs("/jlowin/fastmcp", "Image type")
    C7-->>O: Documentation excerpt

    O->>U: [Response using retrieved docs]
```

---

## Example: Codebase Pattern Research

```mermaid
sequenceDiagram
    participant U as User
    participant O as Orchestrator
    participant CG as context-gathering

    U->>O: "How are errors handled in this codebase?"

    O->>CG: Research error handling patterns
    activate CG

    CG->>CG: Search for try/except patterns
    CG->>CG: Read error handler files
    CG->>CG: Find custom exception classes
    CG->>CG: Note logging patterns

    CG-->>O: DONE: Error handling summary
    deactivate CG

    O->>U: [Comprehensive error handling overview]
```

---

## Gaps in Current RAG Implementation

| Gap                  | Impact                        | Recommendation                                      |
| -------------------- | ----------------------------- | --------------------------------------------------- |
| No context caching   | Repeated lookups              | See [gap-recommendations](./gap-recommendations.md) |
| No semantic search   | Keyword-only matching         | Consider embedding-based search                     |
| No retrieval ranking | May get less relevant results | Add relevance scoring                               |

---

## Navigation

- **Previous:** [Investigation Workflow](../../../plugins/scientific-method/shared/investigation-workflow.md)
- **Next:** [Gap Recommendations](./gap-recommendations.md)
- **Back to:** [Index](./README.md)
