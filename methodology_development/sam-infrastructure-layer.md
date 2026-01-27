# SAM Infrastructure Layer Specification

## Overview

The SAM Infrastructure Layer provides persistent state management, agent coordination, and artifact lifecycle management for the Stateless Agent Methodology. It enables agents to work asynchronously across sessions while maintaining consistency, traceability, and recoverability.

**Core principle**: SAM treats Claude as a stateless function. The infrastructure layer compensates by externalizing all state to git, filesystem, and optional databases.

### Integration with 7-Stage SAM Pipeline

```text
┌─────────────────────────────────────────────────────────────┐
│                 SAM Infrastructure Layer                     │
│  ┌─────────────┬─────────────┬──────────────┬─────────────┐ │
│  │ Meta-Message│  Artifact   │ Git Worktree │ MCP Server  │ │
│  │   System    │   Storage   │  Integration │  Interface  │ │
│  └─────────────┴─────────────┴──────────────┴─────────────┘ │
└─────────────────────────────────────────────────────────────┘
                            ↓
    ┌──────────────────────────────────────────────────┐
    │         7-Stage SAM Pipeline                      │
    ├──────────────────────────────────────────────────┤
    │ 1. Discovery & Interview                          │
    │    ↓ (requirements.md, interviews/)               │
    │ 2. Context Gathering                              │
    │    ↓ (codebase-analysis/, patterns/)              │
    │ 3. Research & Learning                            │
    │    ↓ (research-{topic}.md)                        │
    │ 4. Design & Architecture                          │
    │    ↓ (architecture.md, adr-{id}.md)               │
    │ 5. Planning                                       │
    │    ↓ (plan.md, task-{id}.md)                      │
    │ 6. Implementation & Validation                    │
    │    ↓ (execution-log.md, test-results.md)          │
    │ 7. Delivery                                       │
    │    → (verification.md, release-notes.md)          │
    └──────────────────────────────────────────────────┘
```

**Data flow**:

1. Each stage produces artifacts stored in `.sam/artifacts/{stage}/`
2. Agents communicate via messages in `.sam/messages/`
3. Git worktrees isolate concurrent work per stage
4. MCP server exposes tools/resources for artifact access
5. SQLite index (optional) provides fast artifact search

## Architecture

### Component 1: Meta-Messaging System

**Purpose**: Enable async agent-to-agent communication and progress tracking across sessions

**Design**: Hybrid TodoWrite + mailbox system

#### Message Queue Structure

```text
.sam/messages/
├── inbox/              # Incoming messages per agent
│   ├── discovery/
│   │   └── msg-{id}.md
│   ├── context/
│   ├── research/
│   ├── design/
│   ├── planning/
│   ├── implementation/
│   └── delivery/
├── outbox/             # Sent messages per agent
│   └── [same structure]
└── archive/            # Processed messages
    └── {year}/{month}/
        └── msg-{id}.md
```

#### Message Schema

```yaml
---
id: msg-{{ timestamp }}-{{ uuid }}
from: {{ agent_name }}           # Sending agent
to: {{ agent_name | "broadcast" | "orchestrator" }}
type: {{ message_type }}         # See Message Types below
priority: {{ low | normal | high | critical }}
timestamp: {{ iso8601 }}
related_artifacts: [{{ artifact_id1 }}, {{ artifact_id2 }}]
stage: {{ 1-7 }}
status: {{ pending | delivered | acknowledged | archived }}
---

# {{ Message Subject }}

{{ markdown_body }}

## Metadata

- **Triggered by**: {{ event_or_condition }}
- **Expected action**: {{ action_required }}
- **Deadline**: {{ timestamp | "none" }}

## Related Context

{{ optional_context }}
```

#### Message Types

| Type                 | Purpose              | Sender → Receiver    | Example                                                     |
| -------------------- | -------------------- | -------------------- | ----------------------------------------------------------- |
| `progress`           | Progress update      | Agent → Orchestrator | "Context gathering 60% complete, 15 files analyzed"         |
| `checkpoint`         | Quality gate reached | Agent → Orchestrator | "Design validation gate: awaiting human approval"           |
| `blocking`           | Work blocked         | Agent → Orchestrator | "Cannot proceed: Auth method not specified in requirements" |
| `completion`         | Stage/task complete  | Agent → Orchestrator | "Discovery stage complete: 12 requirements documented"      |
| `delegation`         | Task assignment      | Orchestrator → Agent | "Begin context gathering for auth module"                   |
| `query`              | Information request  | Agent → Agent        | "Design agent: What auth patterns exist in codebase?"       |
| `response`           | Query answer         | Agent → Agent        | "Context agent: OAuth2 + JWT patterns found in 3 services"  |
| `validation_request` | Artifact validation  | Agent → Validator    | "Please review design-auth-service.md"                      |
| `validation_result`  | Validation outcome   | Validator → Agent    | "Design approved with 2 minor suggestions"                  |

#### TodoWrite Integration

**Progress tracking file**: `.sam/messages/todos/stage-{n}/progress.md`

```markdown
# Stage {{ stage_number }} Progress

## Tasks

- [x] Task 1: Interview stakeholders
  - Completed: 2025-01-27 14:30
  - Artifact: interview-001.md
- [ ] Task 2: Document requirements
  - Status: In progress (70%)
  - Blocker: None
  - Artifact: requirements.md (draft)

## Checkpoints

- [x] CHECKPOINT(human-verify): Stakeholder interviews complete
  - Verified: 2025-01-27 15:00
  - Approver: User
- [ ] CHECKPOINT(decision): Requirements prioritization
  - Pending: Awaiting user input on P0 vs P1 features

## Blockers

- None
```

#### Agent Subscription Model

**Configuration**: `.sam/config/subscriptions.yaml`

```yaml
subscriptions:
  # Discovery agents subscribe to orchestrator delegations
  discovery:
    subscribe_to:
      - type: delegation
        from: orchestrator
        stage: 1
    publish:
      - type: progress
        to: orchestrator
      - type: completion
        to: orchestrator

  # Context agents subscribe to discovery completion + design queries
  context:
    subscribe_to:
      - type: completion
        from: discovery
      - type: query
        from: design
        topic: "codebase patterns"
    publish:
      - type: progress
        to: orchestrator
      - type: response
        to: [design, planning]

  # Design agents subscribe to context completion + research results
  design:
    subscribe_to:
      - type: completion
        from: [context, research]
      - type: response
        from: context
    publish:
      - type: query
        to: context
      - type: validation_request
        to: validators
```

#### Message Delivery Protocol

1. **Send**: Agent writes message to recipient's `inbox/` directory
2. **Notify**: (Optional) Create `.sam/messages/.notify` flag file
3. **Read**: Recipient agent reads inbox on activation
4. **Acknowledge**: Recipient moves message from inbox to `archive/`
5. **Response**: If query, recipient sends response message

#### Persistence Strategy

**Primary**: Filesystem (markdown files)

**Advantages**:

- Human-readable message history
- Git versioning for message audit trail
- Simple grep/find for message search
- No database setup required

**Optional enhancement**: SQLite message index for fast queries

```sql
CREATE TABLE messages (
    id TEXT PRIMARY KEY,
    from_agent TEXT NOT NULL,
    to_agent TEXT NOT NULL,
    type TEXT NOT NULL,
    priority TEXT NOT NULL,
    stage INTEGER,
    timestamp TIMESTAMP NOT NULL,
    status TEXT NOT NULL,
    file_path TEXT NOT NULL,
    FOREIGN KEY (stage) REFERENCES stages(id)
);

CREATE INDEX idx_inbox ON messages(to_agent, status)
    WHERE status = 'pending';
CREATE INDEX idx_type ON messages(type, timestamp);
```

### Component 2: YAML Configuration System

**Purpose**: Declarative agent-task association, capability definition, and workflow specification

#### Agent Definition Schema

**File**: `.sam/agents/{agent-name}.yaml`

```yaml
agent:
  # Identity
  name: {{ agent_name }}
  persona: {{ role_description }}
  version: {{ semver }}

  # SAM stage association
  stage:
    primary: {{ 1-7 }}      # Primary stage for this agent
    secondary: [{{ 2, 3 }}] # Can assist in these stages

  # Capabilities
  capabilities:
    - {{ capability_1 }}    # e.g., "Requirements elicitation"
    - {{ capability_2 }}    # e.g., "Stakeholder interviewing"

  # Tool requirements
  tools:
    required:               # Must have access to these tools
      - Read
      - Grep
      - Glob
      - WebSearch
    optional:               # Nice to have
      - WebFetch
      - mcp__Ref__ref_search_documentation
    restricted:             # Must NOT have access
      - Write              # Discovery is read-only
      - Edit

  # Skills to auto-load
  skills:
    load:
      - research           # Load research skill on activation
      - scientific-thinking
    optional:
      - comprehensive-researcher  # Load if available

  # Model selection
  model:
    default: sonnet-4-5    # Default model for this agent
    reasoning: opus-4-5    # For complex reasoning tasks
    quick: haiku-4-5       # For simple operations
    selection_criteria:
      - use: opus-4-5
        when: "Task requires multi-step reasoning or architectural decisions"
      - use: haiku-4-5
        when: "Task is pure retrieval with no interpretation needed"

  # Git worktree configuration
  worktree:
    enabled: true
    branch_prefix: "sam/discovery"
    sparse_checkout:
      - .sam/artifacts/discovery/
      - docs/
      - requirements/
    identity:
      name: "SAM Discovery Agent"
      email: "discovery@sam.local"

  # Workflows
  workflows:
    - name: stakeholder_interview
      trigger:
        type: delegation
        from: orchestrator
        message_contains: "interview"
      steps:
        - name: prepare_questions
          action: "Read requirements template and prepare interview questions"
        - name: conduct_interview
          action: "Engage with user for stakeholder interview"
          checkpoint: human-verify
        - name: document_findings
          action: "Create interview-{id}.md artifact"
        - name: extract_requirements
          action: "Extract requirements from interview and update requirements.md"
        - name: notify_completion
          action: "Send completion message to orchestrator"

  # Output artifacts
  outputs:
    artifacts:
      - type: interview
        location: .sam/artifacts/discovery/interviews/
        schema: interview-schema.yaml
      - type: requirements
        location: .sam/artifacts/discovery/
        schema: requirements-schema.yaml
    messages:
      - type: progress
        frequency: "After each interview"
      - type: completion
        trigger: "All planned interviews complete"
      - type: blocking
        trigger: "Conflicting requirements detected"

  # Quality gates
  quality_gates:
    - name: requirements_completeness
      type: human-verify
      condition: "All P0 requirements have acceptance criteria"
    - name: requirements_consistency
      type: automated
      condition: "No conflicting requirements detected"
      validation_script: .sam/scripts/validate-requirements.py
```

#### Task-Agent Association Configuration

**File**: `.sam/config/pipeline.yaml`

```yaml
sam:
  version: "1.0"
  project: {{ project_name }}

  # Stage definitions
  stages:
    - id: 1
      name: "Discovery & Interview"
      description: "Gather requirements through stakeholder interviews"

      # Agent assignments
      agents:
        - name: discovery
          priority: primary
          activation: auto    # Auto-activate when stage starts
        - name: interview
          priority: secondary
          activation: on-demand  # Activate only if needed

      # Quality gates
      checkpoints:
        - type: human-verify
          name: requirements_review
          condition: "All requirements documented with acceptance criteria"
          blocking: true      # Stage cannot proceed until checkpoint passes
        - type: decision
          name: scope_finalization
          condition: "User approves requirement prioritization (P0/P1/P2)"
          blocking: true

      # Stage outputs
      outputs:
        required:
          - .sam/artifacts/discovery/requirements.md
          - .sam/artifacts/discovery/interviews/
        optional:
          - .sam/artifacts/discovery/personas.md

      # Next stage trigger
      completion_criteria:
        - "All P0 requirements documented"
        - "Requirements review checkpoint passed"
        - "Scope finalization decision made"

    - id: 2
      name: "Context Gathering"
      description: "Analyze codebase for existing patterns and constraints"

      agents:
        - name: context-gatherer
          priority: primary
          activation: auto
          inputs:
            - .sam/artifacts/discovery/requirements.md
        - name: codebase-analyzer
          priority: primary
          activation: auto
          parallelizable: true  # Can run in parallel with context-gatherer

      checkpoints:
        - type: decision
          name: analysis_depth
          condition: "User decides: shallow, medium, or deep codebase analysis"
          options:
            - shallow: "High-level architecture and entry points only"
            - medium: "Key modules and patterns (default)"
            - deep: "Comprehensive analysis including dependencies"

      outputs:
        required:
          - .sam/artifacts/context/codebase-analysis/
          - .sam/artifacts/context/patterns/
        optional:
          - .sam/artifacts/context/dependencies.md
          - .sam/artifacts/context/tech-stack.md

      completion_criteria:
        - "Codebase analysis complete for scope defined in requirements"
        - "Existing patterns documented"
        - "Technical constraints identified"

    # ... Stages 3-7 follow same pattern

  # Global configuration
  global:
    # Model selection policy
    model_policy:
      default_primary: sonnet-4-5
      default_secondary: haiku-4-5
      allow_override: true   # Agents can override per task

    # Tool restriction policy
    tool_policy:
      stages_1_to_3:         # Discovery, Context, Research
        mode: read-only
        allow: [Read, Grep, Glob, Bash(read-only), WebSearch, WebFetch]
        block: [Write, Edit, NotebookEdit]
        rationale: "Early stages are analysis-only, no code changes"
      stages_4_to_5:         # Design, Planning
        mode: design
        allow: [Read, Grep, Glob, Write(artifacts-only)]
        block: [Edit(source-code), NotebookEdit]
        rationale: "Design/planning can create artifacts, not modify source"
      stage_6:               # Implementation
        mode: implementation
        allow: [*]
        rate_limit:
          Write: 20/hour
          Edit: 50/hour
        rationale: "Implementation has full access with rate limits"
      stage_7:               # Delivery
        mode: verification
        allow: [Read, Grep, Glob, Bash(test-commands), Write(reports-only)]
        rationale: "Verification validates implementation, creates reports"

    # Checkpoint defaults
    checkpoint_defaults:
      human-verify:
        timeout: 24h        # Max time to wait for human approval
        escalation: notify  # Notify user after 24h
      decision:
        timeout: 48h
        escalation: notify
      human-action:
        timeout: none       # No timeout, wait indefinitely
```

#### Skill Loading Specification

**File**: `.sam/config/skill-loading.yaml`

```yaml
skill_loading:
  # Global skills (loaded for all agents)
  global:
    - CLAUDE                      # Core identity and protocols
    - subagent-contract          # Subagent boundaries and signaling
    - structured-context-protocol # SCP rule enforcement

  # Stage-specific skills
  stage_skills:
    1:  # Discovery
      - research
      - rt-ica                   # Information Completeness Assessment
    2:  # Context
      - research
      - scientific-thinking
    3:  # Research
      - research
      - comprehensive-researcher
      - scientific-thinking
    4:  # Design
      - how-to-delegate         # For orchestrating design review
      - documentation-expert    # For creating architecture docs
    5:  # Planning
      - how-to-delegate
      - gsd:plan-phase          # GSD planning patterns
    6:  # Implementation
      - python3-development     # If Python project
      - holistic-linting        # Code quality
      - commit-staged           # Git commit discipline
    7:  # Delivery
      - verify                  # Self-assessment before completion
      - am-i-complete          # Completion verification
      - is-it-done             # Final verification

  # Agent-specific skills (override stage defaults)
  agent_skills:
    discovery:
      - research
      - rt-ica
      - comprehensive-researcher  # Discovery benefits from deep research
    context-gatherer:
      - research
      - scientific-thinking
      - trace-protocol-investigator  # For systematic exploration
    codebase-analyzer:
      - code-analysis           # Custom skill for codebase analysis
      - scientific-thinking
```

#### Example Configuration Usage

**Orchestrator workflow**:

```python
# Pseudo-code: How orchestrator uses YAML config
def activate_stage(stage_id: int):
    config = load_yaml('.sam/config/pipeline.yaml')
    stage = config['stages'][stage_id - 1]

    # Check prerequisites
    if not check_completion_criteria(stage_id - 1):
        raise StageNotReadyError(f"Stage {stage_id - 1} not complete")

    # Activate agents
    for agent_config in stage['agents']:
        if agent_config['activation'] == 'auto':
            agent = load_agent_definition(agent_config['name'])
            activate_agent(agent, stage_inputs=stage.get('inputs', []))

    # Monitor checkpoints
    while not stage_complete(stage_id):
        check_quality_gates(stage['checkpoints'])
        monitor_agent_progress()

    # Verify outputs
    verify_outputs(stage['outputs']['required'])

    # Trigger next stage
    if all_criteria_met(stage['completion_criteria']):
        activate_stage(stage_id + 1)
```

### Component 3: Artifact Storage System

**Purpose**: Persistent, structured, version-controlled storage for all SAM process artifacts

#### Directory Structure

```text
.sam/
├── artifacts/
│   ├── discovery/
│   │   ├── requirements.md
│   │   ├── interviews/
│   │   │   ├── interview-001.md
│   │   │   ├── interview-002.md
│   │   │   └── ...
│   │   ├── personas/
│   │   │   └── persona-{role}.md
│   │   └── constraints.md
│   ├── context/
│   │   ├── codebase-analysis/
│   │   │   ├── analysis-{component}.md
│   │   │   ├── dependencies.md
│   │   │   └── entry-points.md
│   │   ├── patterns/
│   │   │   ├── pattern-{name}.md
│   │   │   └── anti-patterns.md
│   │   └── tech-stack.md
│   ├── research/
│   │   ├── research-{topic}.md
│   │   └── references/
│   │       └── reference-{id}.md
│   ├── design/
│   │   ├── architecture/
│   │   │   ├── architecture.md
│   │   │   ├── architecture-{component}.md
│   │   │   └── diagrams/
│   │   ├── decisions/
│   │   │   ├── adr-001-{title}.md  # Architecture Decision Records
│   │   │   └── ...
│   │   └── api-specs/
│   │       └── api-{service}.yaml
│   ├── planning/
│   │   ├── plan.md
│   │   ├── tasks/
│   │   │   ├── task-001.md
│   │   │   └── ...
│   │   └── dependencies.yaml
│   ├── implementation/
│   │   ├── execution-log.md
│   │   ├── commits/
│   │   │   └── commit-{sha}.md   # Detailed commit context
│   │   └── test-results/
│   │       └── test-run-{timestamp}.md
│   └── delivery/
│       ├── verification.md
│       ├── test-coverage.md
│       ├── release-notes.md
│       └── handoff.md
├── config/
│   ├── pipeline.yaml          # Stage configuration
│   ├── agents/                # Agent definitions
│   │   ├── discovery.yaml
│   │   └── ...
│   ├── subscriptions.yaml     # Message routing
│   ├── skill-loading.yaml     # Skill loading rules
│   └── worktrees.yaml        # Git worktree configuration
├── messages/                  # Meta-messaging (Component 1)
│   ├── inbox/
│   ├── outbox/
│   └── archive/
├── index.db                   # Optional SQLite index
└── scripts/                   # Validation and utility scripts
    ├── validate-requirements.py
    └── ...
```

#### Artifact Schemas

**Base artifact schema** (inherited by all artifact types):

```yaml
---
# Required fields (all artifacts)
id: {{ uuid }}                          # Unique identifier
type: {{ artifact_type }}               # discovery | context | research | design | plan | task | execution | delivery
stage: {{ 1-7 }}                        # SAM stage that created this
created: {{ iso8601_timestamp }}
updated: {{ iso8601_timestamp }}
version: {{ semver }}

# Status tracking
status: {{ draft | in-progress | review | approved | completed | archived }}

# Relationships
created_by: {{ agent_name }}            # Agent that created artifact
related_artifacts: [{{ id1 }}, {{ id2 }}]  # Related artifact IDs
supersedes: {{ artifact_id | null }}    # If this replaces another artifact

# Categorization
tags: [{{ tag1 }}, {{ tag2 }}]
stage_phase: {{ discovery | context | research | design | plan | implement | deliver }}

# Optional fields
validated_by: {{ agent_name | null }}
validated_at: {{ iso8601_timestamp | null }}
validation_status: {{ pass | fail | pending | null }}
---

# {{ Artifact Title }}

{{ markdown_body }}
```

#### Artifact Type Schemas

**1. Requirements Artifact** (`.sam/artifacts/discovery/requirements.md`):

```yaml
---
id: req-{{ uuid }}
type: requirements
stage: 1
status: {{ draft | approved }}
priority_breakdown:
  p0: {{ count }}  # Must-have
  p1: {{ count }}  # Should-have
  p2: {{ count }}  # Nice-to-have
total_requirements: {{ count }}
---

# Requirements

## Functional Requirements

### FR-001: {{ Requirement Title }} [P0]

**Description**: {{ requirement_description }}

**Acceptance Criteria**:

- [ ] Criterion 1
- [ ] Criterion 2

**Source**: {{ interview-001.md | user_request }}

**Dependencies**: {{ FR-002, FR-003 }}

---

## Non-Functional Requirements

### NFR-001: {{ Requirement Title }} [P1]

...
```

**2. Codebase Analysis Artifact** (`.sam/artifacts/context/codebase-analysis/analysis-{component}.md`):

```yaml
---
id: ctx-{{ uuid }}
type: codebase-analysis
stage: 2
component: {{ component_name }}
files_analyzed: {{ count }}
patterns_identified: {{ count }}
---

# Codebase Analysis: {{ Component Name }}

## Overview

{{ component_description }}

## Architecture

{{ architecture_summary }}

## Key Files

| File | Purpose | Lines | Complexity |
|------|---------|-------|------------|
| {{ file1 }} | {{ purpose1 }} | {{ lines1 }} | {{ complexity1 }} |

## Patterns Identified

### Pattern: {{ pattern_name }}

**Location**: {{ files_or_directories }}

**Description**: {{ pattern_description }}

**Usage**: {{ usage_context }}

## Dependencies

- {{ dependency1 }}: {{ usage }}
- {{ dependency2 }}: {{ usage }}

## Technical Debt

- {{ debt_item_1 }}
- {{ debt_item_2 }}

## Recommendations

{{ recommendations_for_implementation }}
```

**3. Architecture Decision Record** (`.sam/artifacts/design/decisions/adr-{id}-{title}.md`):

```yaml
---
id: adr-{{ id }}
type: architecture-decision
stage: 4
status: {{ proposed | accepted | rejected | superseded }}
decision_date: {{ iso8601 }}
supersedes: {{ adr-id | null }}
---

# ADR-{{ id }}: {{ Decision Title }}

## Status

{{ proposed | accepted | rejected | superseded }}

## Context

{{ context_and_background }}

## Decision

{{ decision_made }}

## Consequences

### Positive

- {{ consequence_1 }}
- {{ consequence_2 }}

### Negative

- {{ consequence_1 }}
- {{ consequence_2 }}

### Neutral

- {{ consequence_1 }}

## Alternatives Considered

### Alternative 1: {{ name }}

**Pros**: {{ pros }}

**Cons**: {{ cons }}

**Why rejected**: {{ reason }}

## References

- {{ reference_1 }}
- {{ reference_2 }}
```

**4. Task Artifact** (`.sam/artifacts/planning/tasks/task-{id}.md`):

```yaml
---
id: task-{{ id }}
type: task
stage: 5
status: {{ pending | in-progress | blocked | completed }}
priority: {{ p0 | p1 | p2 }}
assigned_to: {{ agent_name | null }}
estimated_complexity: {{ low | medium | high }}
dependencies: [{{ task-id1 }}, {{ task-id2 }}]
blocks: [{{ task-id3 }}, {{ task-id4 }}]
---

# Task {{ id }}: {{ Task Title }}

## Description

{{ task_description }}

## Acceptance Criteria

- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Criterion 3

## Implementation Notes

{{ implementation_guidance }}

## Related Artifacts

- Requirements: {{ req-id }}
- Design: {{ adr-id }}

## Testing Requirements

{{ testing_requirements }}

## Blockers

{{ current_blockers | "None" }}
```

**5. Verification Artifact** (`.sam/artifacts/delivery/verification.md`):

```yaml
---
id: ver-{{ uuid }}
type: verification
stage: 7
verification_date: {{ iso8601 }}
verification_agent: {{ agent_name }}
overall_status: {{ pass | fail | partial }}
---

# Stage 7 Verification Report

## Requirements Verification

| Requirement | Status | Evidence |
|-------------|--------|----------|
| FR-001 | ✅ Pass | test-results/test-auth.md |
| FR-002 | ✅ Pass | test-results/test-user.md |

## Quality Gates

| Gate | Status | Notes |
|------|--------|-------|
| All tests passing | ✅ Pass | 95% coverage |
| No critical linting errors | ✅ Pass | ruff, mypy clean |
| Documentation complete | ⚠️ Partial | API docs pending |

## Artifacts Produced

| Artifact | Status | Location |
|----------|--------|----------|
| Requirements | ✅ Complete | discovery/requirements.md |
| Architecture | ✅ Complete | design/architecture.md |
| Implementation | ✅ Complete | src/ |
| Tests | ✅ Complete | tests/ |

## Known Issues

- {{ issue_1 }}
- {{ issue_2 }}

## Recommendations

{{ recommendations_for_next_iteration }}
```

#### Storage Backend Options

**Option 1: Filesystem only** (Recommended for most projects)

**Pros**:

- Zero setup - just create directories
- Human-readable markdown files
- Git versioning built-in
- Easy to edit in any editor
- grep/find for search

**Cons**:

- No built-in full-text search
- Manual relationship tracking
- No query language

**When to use**: Default choice for all projects

---

**Option 2: Filesystem + SQLite index** (Recommended for large projects)

**Pros**:

- Fast full-text search (FTS5)
- SQL queries for relationships
- Artifact dependency tracking
- Still human-readable on filesystem
- Single-file database (portable)

**Cons**:

- Requires schema setup
- Index must stay in sync with files
- Slightly more complex setup

**When to use**: Projects with 100+ artifacts or complex dependencies

**SQLite schema**:

```sql
-- Core artifact table
CREATE TABLE artifacts (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL,
    stage INTEGER NOT NULL,
    status TEXT NOT NULL,
    created TIMESTAMP NOT NULL,
    updated TIMESTAMP NOT NULL,
    version TEXT NOT NULL,
    file_path TEXT NOT NULL,
    created_by TEXT,
    validated_by TEXT,
    validated_at TIMESTAMP,
    validation_status TEXT,
    metadata JSON
);

-- Relationships
CREATE TABLE artifact_relationships (
    from_artifact TEXT NOT NULL,
    to_artifact TEXT NOT NULL,
    relationship_type TEXT NOT NULL,  -- related_to, supersedes, depends_on, blocks
    PRIMARY KEY (from_artifact, to_artifact, relationship_type),
    FOREIGN KEY (from_artifact) REFERENCES artifacts(id),
    FOREIGN KEY (to_artifact) REFERENCES artifacts(id)
);

-- Tags
CREATE TABLE artifact_tags (
    artifact_id TEXT NOT NULL,
    tag TEXT NOT NULL,
    PRIMARY KEY (artifact_id, tag),
    FOREIGN KEY (artifact_id) REFERENCES artifacts(id)
);

-- Full-text search
CREATE VIRTUAL TABLE artifacts_fts USING fts5(
    id UNINDEXED,
    type,
    content,
    tags,
    content=artifacts
);

-- Indexes
CREATE INDEX idx_stage ON artifacts(stage);
CREATE INDEX idx_type ON artifacts(type);
CREATE INDEX idx_status ON artifacts(status);
CREATE INDEX idx_created_by ON artifacts(created_by);
CREATE INDEX idx_created_timestamp ON artifacts(created);
```

---

**Option 3: Cloud database (Supabase/PostgreSQL)** (For team collaboration)

**Pros**:

- Multi-user concurrent access
- Real-time subscriptions
- Built-in auth and row-level security
- pgvector for semantic search
- Backup and replication

**Cons**:

- Requires cloud setup
- Network dependency
- Cost for cloud hosting
- More complex setup

**When to use**: Multi-developer teams with distributed work

**Schema**: Similar to SQLite but with PostgreSQL extensions

```sql
-- Enable vector extension for semantic search
CREATE EXTENSION vector;

-- Artifacts table (similar to SQLite)
CREATE TABLE artifacts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    type TEXT NOT NULL,
    stage INTEGER NOT NULL,
    status TEXT NOT NULL,
    created TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated TIMESTAMPTZ NOT NULL DEFAULT now(),
    version TEXT NOT NULL,
    file_path TEXT NOT NULL,
    created_by TEXT,
    validated_by TEXT,
    validated_at TIMESTAMPTZ,
    validation_status TEXT,
    content TEXT NOT NULL,
    embedding VECTOR(1536)  -- For semantic search
);

-- Semantic search index
CREATE INDEX idx_embedding ON artifacts
USING ivfflat (embedding vector_cosine_ops);
```

---

**Option 4: Git-based (Issues/Projects)** (Lightweight alternative)

**Pros**:

- No separate storage system
- Built-in GitHub/GitLab UI
- Issue templates for artifacts
- Built-in tagging and milestones
- Web-based collaboration

**Cons**:

- Tied to git platform
- API rate limits
- Less flexible schema
- Not ideal for large artifacts

**When to use**: Small projects on GitHub/GitLab with web-based workflow

**Mapping**:

- Artifacts → GitHub Issues with labels
- Stages → GitHub Milestones
- Relationships → Issue references
- Tags → Issue labels

---

**Hybrid approach** (Recommended for production):

- **Filesystem**: Primary storage for all artifacts
- **SQLite**: Local index for fast queries
- **Git**: Versioning and backup
- **Cloud (optional)**: Team collaboration and semantic search

**Sync strategy**:

```python
# Pseudo-code: Keep SQLite in sync with filesystem
def sync_artifact_to_index(artifact_path: str):
    """Sync artifact file to SQLite index"""
    content = read_file(artifact_path)
    metadata = parse_frontmatter(content)

    # Upsert to SQLite
    db.execute("""
        INSERT INTO artifacts (id, type, stage, status, file_path, content, ...)
        VALUES (?, ?, ?, ?, ?, ?, ...)
        ON CONFLICT(id) DO UPDATE SET
            updated = ?,
            status = ?,
            content = ?
    """, ...)

    # Update FTS index
    db.execute("""
        INSERT INTO artifacts_fts (id, type, content, tags)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET content = ?
    """, ...)
```

#### Retrieval API

**File-based retrieval** (no index):

```python
# Pseudo-code: Artifact retrieval without index
def get_artifact(artifact_id: str) -> dict:
    """Load artifact by ID (brute force search)"""
    for path in glob('.sam/artifacts/**/*.md'):
        content = read_file(path)
        metadata = parse_frontmatter(content)
        if metadata['id'] == artifact_id:
            return {**metadata, 'content': content, 'path': path}
    raise ArtifactNotFoundError(artifact_id)

def search_artifacts(query: str, filters: dict = None) -> list:
    """Search artifacts using grep"""
    results = grep(query, path='.sam/artifacts', recursive=True)
    artifacts = [load_artifact(path) for path in results]

    # Apply filters
    if filters:
        artifacts = [a for a in artifacts if matches_filters(a, filters)]

    return artifacts
```

**Index-based retrieval** (with SQLite):

```python
# Pseudo-code: Fast artifact retrieval with index
def get_artifact(artifact_id: str) -> dict:
    """Load artifact by ID (indexed)"""
    row = db.execute(
        "SELECT * FROM artifacts WHERE id = ?",
        (artifact_id,)
    ).fetchone()

    if not row:
        raise ArtifactNotFoundError(artifact_id)

    content = read_file(row['file_path'])
    return {**dict(row), 'content': content}

def search_artifacts_fts(query: str, filters: dict = None) -> list:
    """Full-text search with filters"""
    sql = """
        SELECT a.*
        FROM artifacts_fts fts
        JOIN artifacts a ON a.id = fts.id
        WHERE fts MATCH ?
    """
    params = [query]

    # Add filters
    if filters:
        if 'stage' in filters:
            sql += " AND a.stage = ?"
            params.append(filters['stage'])
        if 'type' in filters:
            sql += " AND a.type = ?"
            params.append(filters['type'])
        if 'status' in filters:
            sql += " AND a.status = ?"
            params.append(filters['status'])

    sql += " ORDER BY a.updated DESC LIMIT 50"

    rows = db.execute(sql, params).fetchall()
    return [dict(row) for row in rows]

def get_related_artifacts(artifact_id: str, relationship_type: str = None) -> list:
    """Get related artifacts via relationships table"""
    sql = """
        SELECT a.*
        FROM artifact_relationships r
        JOIN artifacts a ON a.id = r.to_artifact
        WHERE r.from_artifact = ?
    """
    params = [artifact_id]

    if relationship_type:
        sql += " AND r.relationship_type = ?"
        params.append(relationship_type)

    rows = db.execute(sql, params).fetchall()
    return [dict(row) for row in rows]
```

### Component 4: MCP Server Interface

**Purpose**: Expose SAM infrastructure as MCP tools, resources, and prompts for agent consumption

**Design**: FastMCP server implementing Model Context Protocol

#### Server Structure

```text
sam-mcp/
├── src/
│   ├── server.py           # Main MCP server
│   ├── tools/
│   │   ├── artifacts.py    # Artifact CRUD tools
│   │   ├── messages.py     # Message queue tools
│   │   └── worktrees.py    # Git worktree tools
│   ├── resources/
│   │   ├── artifacts.py    # Artifact resource provider
│   │   └── config.py       # Configuration resource provider
│   └── prompts/
│       ├── stages.py       # Stage-specific prompts
│       └── workflows.py    # Workflow guidance prompts
├── config/
│   └── server.yaml         # MCP server configuration
└── pyproject.toml
```

#### Tool Definitions

**Artifact CRUD tools**:

```python
# src/tools/artifacts.py
from fastmcp import FastMCP

mcp = FastMCP("SAM Infrastructure")

@mcp.tool()
def create_artifact(
    type: str,
    stage: int,
    content: str,
    metadata: dict = None
) -> dict:
    """
    Create a new SAM artifact.

    Args:
        type: Artifact type (requirements, codebase-analysis, task, etc.)
        stage: SAM stage number (1-7)
        content: Markdown content for artifact
        metadata: Optional frontmatter metadata

    Returns:
        Created artifact with ID and file path

    Examples:
        # Create requirements artifact
        create_artifact(
            type="requirements",
            stage=1,
            content="# Requirements\\n\\n## FR-001: User Auth\\n...",
            metadata={"priority_breakdown": {"p0": 5, "p1": 3}}
        )
    """
    artifact_id = generate_uuid()
    file_path = get_artifact_path(type, stage, artifact_id)

    # Construct frontmatter
    frontmatter = {
        "id": artifact_id,
        "type": type,
        "stage": stage,
        "status": "draft",
        "created": iso8601_now(),
        "updated": iso8601_now(),
        "version": "1.0.0",
        **(metadata or {})
    }

    # Write file
    write_artifact_file(file_path, frontmatter, content)

    # Update index if enabled
    if index_enabled():
        sync_to_index(file_path)

    return {
        "id": artifact_id,
        "file_path": file_path,
        "status": "created"
    }

@mcp.tool()
def update_artifact(
    artifact_id: str,
    content: str = None,
    metadata: dict = None,
    status: str = None
) -> dict:
    """
    Update existing artifact.

    Args:
        artifact_id: Artifact ID to update
        content: New markdown content (optional)
        metadata: Metadata fields to update (optional)
        status: New status (optional)

    Returns:
        Updated artifact info
    """
    artifact = get_artifact(artifact_id)

    # Update fields
    if content:
        artifact['content'] = content
    if metadata:
        artifact.update(metadata)
    if status:
        artifact['status'] = status

    artifact['updated'] = iso8601_now()
    artifact['version'] = increment_version(artifact['version'])

    # Write back
    write_artifact_file(artifact['file_path'], artifact, artifact['content'])

    # Update index
    if index_enabled():
        sync_to_index(artifact['file_path'])

    return {
        "id": artifact_id,
        "version": artifact['version'],
        "status": "updated"
    }

@mcp.tool()
def get_artifact(artifact_id: str) -> dict:
    """
    Retrieve artifact by ID.

    Args:
        artifact_id: Artifact ID

    Returns:
        Complete artifact with metadata and content
    """
    if index_enabled():
        return get_artifact_from_index(artifact_id)
    else:
        return get_artifact_from_filesystem(artifact_id)

@mcp.tool()
def search_artifacts(
    query: str = None,
    stage: int = None,
    type: str = None,
    status: str = None,
    tags: list = None,
    limit: int = 50
) -> list:
    """
    Search artifacts with filters.

    Args:
        query: Full-text search query (optional)
        stage: Filter by SAM stage (optional)
        type: Filter by artifact type (optional)
        status: Filter by status (optional)
        tags: Filter by tags (optional)
        limit: Max results (default: 50)

    Returns:
        List of matching artifacts

    Examples:
        # Find all P0 requirements
        search_artifacts(query="[P0]", type="requirements", stage=1)

        # Find all in-progress tasks
        search_artifacts(type="task", status="in-progress")
    """
    filters = {
        "stage": stage,
        "type": type,
        "status": status,
        "tags": tags
    }

    if index_enabled():
        return search_artifacts_fts(query, filters, limit)
    else:
        return search_artifacts_filesystem(query, filters, limit)

@mcp.tool()
def delete_artifact(artifact_id: str, archive: bool = True) -> dict:
    """
    Delete or archive artifact.

    Args:
        artifact_id: Artifact ID
        archive: If True, move to archive instead of deleting (default: True)

    Returns:
        Deletion status
    """
    artifact = get_artifact(artifact_id)

    if archive:
        # Move to archive
        archive_path = get_archive_path(artifact)
        move_file(artifact['file_path'], archive_path)
        status_msg = "archived"
    else:
        # Permanent delete
        delete_file(artifact['file_path'])
        status_msg = "deleted"

    # Update index
    if index_enabled():
        remove_from_index(artifact_id)

    return {"id": artifact_id, "status": status_msg}
```

**Message queue tools**:

```python
# src/tools/messages.py
@mcp.tool()
def send_message(
    from_agent: str,
    to_agent: str,
    message_type: str,
    subject: str,
    content: str,
    priority: str = "normal",
    related_artifacts: list = None
) -> dict:
    """
    Send message to agent inbox.

    Args:
        from_agent: Sending agent name
        to_agent: Receiving agent name (or "broadcast" or "orchestrator")
        message_type: progress | checkpoint | blocking | completion | delegation | query | response
        subject: Message subject line
        content: Markdown message body
        priority: low | normal | high | critical (default: normal)
        related_artifacts: List of related artifact IDs (optional)

    Returns:
        Message ID and delivery status
    """
    message_id = f"msg-{iso8601_now()}-{generate_uuid()}"

    message = {
        "id": message_id,
        "from": from_agent,
        "to": to_agent,
        "type": message_type,
        "priority": priority,
        "timestamp": iso8601_now(),
        "related_artifacts": related_artifacts or [],
        "status": "pending",
        "subject": subject,
        "content": content
    }

    # Write to inbox
    inbox_path = f".sam/messages/inbox/{to_agent}/{message_id}.md"
    write_message_file(inbox_path, message)

    # Copy to sender's outbox
    outbox_path = f".sam/messages/outbox/{from_agent}/{message_id}.md"
    write_message_file(outbox_path, message)

    # Create notify flag if needed
    if priority in ["high", "critical"]:
        create_notify_flag(to_agent)

    return {
        "message_id": message_id,
        "status": "delivered",
        "inbox": inbox_path
    }

@mcp.tool()
def read_inbox(agent_name: str, message_type: str = None) -> list:
    """
    Read messages from agent inbox.

    Args:
        agent_name: Agent name
        message_type: Filter by message type (optional)

    Returns:
        List of inbox messages
    """
    inbox_path = f".sam/messages/inbox/{agent_name}/"
    messages = []

    for file_path in glob(f"{inbox_path}*.md"):
        message = parse_message_file(file_path)
        if message_type is None or message['type'] == message_type:
            messages.append(message)

    # Sort by priority and timestamp
    messages.sort(key=lambda m: (
        {"critical": 0, "high": 1, "normal": 2, "low": 3}[m['priority']],
        m['timestamp']
    ))

    return messages

@mcp.tool()
def acknowledge_message(message_id: str, agent_name: str) -> dict:
    """
    Acknowledge message (moves to archive).

    Args:
        message_id: Message ID
        agent_name: Agent name (for inbox path)

    Returns:
        Acknowledgment status
    """
    inbox_path = f".sam/messages/inbox/{agent_name}/{message_id}.md"
    archive_path = f".sam/messages/archive/{iso8601_date()}/{message_id}.md"

    move_file(inbox_path, archive_path)

    return {
        "message_id": message_id,
        "status": "acknowledged",
        "archived_to": archive_path
    }
```

**Git worktree tools**:

```python
# src/tools/worktrees.py
@mcp.tool()
def setup_stage_worktree(stage: int, project_path: str) -> dict:
    """
    Setup isolated git worktree for SAM stage.

    Args:
        stage: SAM stage number (1-7)
        project_path: Path to project repository

    Returns:
        Worktree path and configuration
    """
    config = load_agent_config(stage)
    branch_name = f"sam/stage-{stage}"
    worktree_path = f"{project_path}/.sam/worktrees/stage-{stage}"

    # Create worktree (force if exists)
    run_git_command([
        "worktree", "add", "--force", worktree_path, branch_name
    ], cwd=project_path)

    # Configure sparse checkout
    sparse_paths = config['worktree']['sparse_checkout']
    setup_sparse_checkout(worktree_path, sparse_paths)

    # Set agent identity
    identity = config['worktree']['identity']
    run_git_command(["config", "user.name", identity['name']], cwd=worktree_path)
    run_git_command(["config", "user.email", identity['email']], cwd=worktree_path)

    return {
        "worktree_path": worktree_path,
        "branch": branch_name,
        "identity": identity,
        "sparse_checkout": sparse_paths
    }

@mcp.tool()
def sync_worktree(worktree_path: str) -> dict:
    """
    Sync worktree with remote (pull with rebase).

    Args:
        worktree_path: Path to worktree

    Returns:
        Sync status
    """
    # Check for uncommitted changes
    status = run_git_command(["status", "--porcelain"], cwd=worktree_path)
    if status.strip():
        raise WorktreeNotCleanError("Uncommitted changes detected")

    # Pull with rebase
    result = run_git_command(["pull", "--rebase"], cwd=worktree_path)

    return {
        "worktree": worktree_path,
        "status": "synced",
        "output": result
    }

@mcp.tool()
def get_worktree_status(worktree_path: str) -> dict:
    """
    Get git status of worktree.

    Args:
        worktree_path: Path to worktree

    Returns:
        Status dict with uncommitted, stash, unpushed, clean flags
    """
    # Check uncommitted changes
    uncommitted = bool(
        run_git_command(["status", "--porcelain"], cwd=worktree_path).strip()
    )

    # Check stash
    stash = bool(
        run_git_command(["stash", "list"], cwd=worktree_path).strip()
    )

    # Check unpushed commits
    unpushed = bool(
        run_git_command([
            "log", "@{upstream}..", "--oneline"
        ], cwd=worktree_path).strip()
    )

    clean = not (uncommitted or stash or unpushed)

    return {
        "worktree": worktree_path,
        "uncommitted": uncommitted,
        "stash": stash,
        "unpushed": unpushed,
        "clean": clean
    }
```

#### Resource Definitions

**Artifact resources**:

```python
# src/resources/artifacts.py
@mcp.resource("sam://artifacts/{stage}/{type}")
def get_stage_artifacts(stage: int, type: str) -> str:
    """
    Get all artifacts of given type for stage.

    URI: sam://artifacts/{stage}/{type}

    Examples:
        sam://artifacts/1/requirements
        sam://artifacts/2/codebase-analysis
        sam://artifacts/4/architecture
    """
    artifacts = search_artifacts(stage=stage, type=type)
    return json.dumps(artifacts, indent=2)

@mcp.resource("sam://artifacts/{artifact_id}")
def get_artifact_resource(artifact_id: str) -> str:
    """
    Get artifact by ID.

    URI: sam://artifacts/{artifact_id}
    """
    artifact = get_artifact(artifact_id)
    return artifact['content']

@mcp.resource("sam://config/pipeline")
def get_pipeline_config() -> str:
    """
    Get SAM pipeline configuration.

    URI: sam://config/pipeline
    """
    config = load_yaml('.sam/config/pipeline.yaml')
    return yaml.dump(config)
```

#### Prompt Definitions

**Stage guidance prompts**:

```python
# src/prompts/stages.py
@mcp.prompt("sam-stage-1-discovery")
def stage_1_discovery_prompt() -> str:
    """
    Guidance for SAM Stage 1: Discovery & Interview.

    Returns comprehensive prompt for discovery agents with:
    - Stage objectives
    - Required artifacts
    - Quality gates
    - Workflow steps
    """
    return """
# SAM Stage 1: Discovery & Interview

## Objective

Gather complete, unambiguous requirements through stakeholder interviews and document them with clear acceptance criteria.

## Your Role

You are the Discovery Agent. Your expertise is requirements elicitation and stakeholder communication.

## Workflow

1. **Prepare interview questions**
   - Review requirements template
   - Identify knowledge gaps
   - Prepare structured questions

2. **Conduct interviews**
   - Engage stakeholders systematically
   - Document responses verbatim
   - Clarify ambiguities immediately

3. **Extract requirements**
   - Parse interviews for functional/non-functional requirements
   - Assign priorities (P0/P1/P2)
   - Write clear acceptance criteria

4. **Validate completeness**
   - Check all P0 requirements have acceptance criteria
   - Verify no conflicting requirements
   - Request human review

## Required Artifacts

- `requirements.md`: Master requirements document
- `interviews/interview-{id}.md`: Interview transcripts
- `constraints.md`: Technical and business constraints

## Quality Gates

- ✅ All P0 requirements documented
- ✅ Each requirement has 2+ acceptance criteria
- ✅ No conflicting requirements detected
- ✅ Human review checkpoint passed

## Tools Available

- `create_artifact()`: Create requirements artifacts
- `send_message()`: Send progress updates
- `Read`, `Grep`, `Glob`: Read project documentation
- `WebSearch`, `WebFetch`: Research domain concepts

## Example Output

See artifact schema: sam://artifacts/1/requirements
"""

@mcp.prompt("sam-stage-6-implementation")
def stage_6_implementation_prompt() -> str:
    """
    Guidance for SAM Stage 6: Implementation & Validation.
    """
    return """
# SAM Stage 6: Implementation & Validation

## Objective

Implement planned tasks with atomic commits, comprehensive tests, and continuous validation.

## Your Role

You are the Implementation Agent. Your expertise is coding, testing, and integration.

## Workflow

1. **Load context**
   - Read plan.md and task definitions
   - Read architecture decisions (ADRs)
   - Understand acceptance criteria

2. **Implement with discipline**
   - One task per commit
   - Write tests before/during implementation
   - Follow architecture patterns
   - Document as you code

3. **Validate continuously**
   - Run tests after each change
   - Check linting (ruff, mypy)
   - Verify acceptance criteria

4. **Commit atomically**
   - Commit format: `task(task-id): Description`
   - One logical change per commit
   - Tests must pass before commit

## Required Artifacts

- `execution-log.md`: Implementation progress
- `test-results/test-run-{timestamp}.md`: Test run reports
- `commits/commit-{sha}.md`: Detailed commit context

## Quality Gates

- ✅ All planned tasks implemented
- ✅ Test coverage ≥ 80%
- ✅ No linting errors
- ✅ All acceptance criteria met

## Tools Available

- `Write`, `Edit`, `NotebookEdit`: Code modification
- `Bash`: Run tests, linters, git commands
- `create_artifact()`: Create execution logs
- `send_message()`: Report progress/blockers

## Git Workflow

- Work in isolated worktree: `.sam/worktrees/stage-6`
- Commit format: `task(123): Add JWT middleware`
- Push to branch: `sam/stage-6-implementation`
"""
```

#### Integration with Existing SAM

**1. Skill integration**: SAM skills load MCP server on activation

```yaml
# In existing SAM skills (e.g., discovery skill)
skills:
  - name: discovery
    mcp_servers:
      - sam-infrastructure  # Auto-load SAM MCP server
    tools_required:
      - sam-mcp:create_artifact
      - sam-mcp:send_message
      - sam-mcp:search_artifacts
```

**2. Agent integration**: Agents use MCP tools for infrastructure operations

```python
# Pseudo-code: Discovery agent uses SAM infrastructure
def discovery_workflow():
    # Read inbox for delegation message
    messages = read_inbox("discovery", message_type="delegation")

    for msg in messages:
        # Conduct interview
        interview_transcript = conduct_stakeholder_interview()

        # Create interview artifact
        create_artifact(
            type="interview",
            stage=1,
            content=interview_transcript,
            metadata={"stakeholder": "Product Manager"}
        )

        # Extract requirements
        requirements = extract_requirements_from_interview(interview_transcript)

        # Update requirements artifact
        update_artifact(
            artifact_id="req-main",
            content=requirements
        )

        # Send progress message
        send_message(
            from_agent="discovery",
            to_agent="orchestrator",
            message_type="progress",
            subject="Interview complete",
            content="Stakeholder interview completed, requirements updated"
        )

        # Acknowledge delegation message
        acknowledge_message(msg['id'], "discovery")
```

### Component 5: Git Worktree Integration

**Purpose**: Isolate concurrent stage work, enable state recovery, and preserve agent attribution

**Design**: Gastown-inspired worktree management with SAM-specific extensions

#### Worktree Lifecycle

**1. Setup phase** (on stage activation):

```text
.sam/worktrees/
├── stage-1-discovery/          # Stage 1 worktree
│   ├── .git -> ../../.git/worktrees/stage-1-discovery/
│   ├── .sam/                   # SAM artifacts only
│   ├── docs/                   # Sparse checkout: docs only
│   └── requirements/           # Sparse checkout: requirements only
├── stage-2-context/            # Stage 2 worktree
│   ├── .git -> ../../.git/worktrees/stage-2-context/
│   ├── .sam/
│   └── src/                    # Sparse checkout: source code
└── stage-6-implementation/     # Stage 6 worktree
    ├── .git -> ../../.git/worktrees/stage-6-implementation/
    ├── .sam/
    ├── src/                    # Full checkout
    └── tests/                  # Full checkout
```

**2. Work phase** (during stage execution):

- Auto-sync before work starts (pull with rebase)
- Agent makes changes in isolated worktree
- Commits use conventional format: `<type>(<scope>): <message>`
- Git identity set to agent name for attribution

**3. Completion phase** (stage done):

- Verify worktree is clean (no uncommitted changes)
- Merge stage branch to main
- Archive or cleanup worktree

#### Worktree Configuration

**File**: `.sam/config/worktrees.yaml`

```yaml
worktrees:
  stage-1-discovery:
    branch: sam/stage-1-discovery
    base_branch: main
    sparse_checkout:
      include:
        - .sam/artifacts/discovery/
        - docs/
        - requirements/
      exclude:
        - .sam/artifacts/context/    # Don't need other stage artifacts
        - .sam/artifacts/design/
        - src/                       # Don't need source code
        - tests/                     # Don't need tests
    identity:
      name: SAM Discovery Agent
      email: discovery@sam.local
    auto_sync: true
    auto_cleanup: false  # Keep worktree after stage complete

  stage-2-context:
    branch: sam/stage-2-context
    base_branch: sam/stage-1-discovery  # Build on discovery work
    sparse_checkout:
      include:
        - .sam/artifacts/context/
        - .sam/artifacts/discovery/  # Read discovery artifacts
        - src/
        - docs/
      exclude:
        - tests/
    identity:
      name: SAM Context Agent
      email: context@sam.local
    auto_sync: true
    auto_cleanup: false

  stage-6-implementation:
    branch: sam/stage-6-implementation
    base_branch: sam/stage-5-planning  # Build on planning work
    sparse_checkout:
      include:
        - "*"  # Full checkout for implementation
    identity:
      name: SAM Implementation Agent
      email: implementation@sam.local
    auto_sync: true
    auto_cleanup: false
```

#### Auto-Sync Workflow

**Trigger**: Before stage activation or on explicit sync request

```python
# Pseudo-code: Auto-sync workflow
def sync_stage_worktree(stage: int, project_path: str):
    """Sync worktree before starting work"""
    worktree_path = f"{project_path}/.sam/worktrees/stage-{stage}"

    # Check status
    status = get_worktree_status(worktree_path)

    if status['uncommitted']:
        raise WorktreeNotCleanError(
            "Cannot sync: uncommitted changes detected. "
            "Commit or stash changes first."
        )

    if status['stash']:
        print("Warning: Stashed changes detected")

    # Fetch latest from remote
    run_git_command(["fetch", "origin"], cwd=worktree_path)

    # Get current branch
    branch = get_current_branch(worktree_path)

    # Check if remote branch exists
    remote_exists = check_remote_branch(f"origin/{branch}", worktree_path)

    if remote_exists:
        # Pull with rebase
        result = run_git_command(["pull", "--rebase", "origin", branch], cwd=worktree_path)

        # Check for conflicts
        if "CONFLICT" in result:
            raise MergeConflictError(
                "Rebase conflicts detected. Manual resolution required."
            )
    else:
        # First push - no remote branch yet
        print(f"No remote branch {branch} found, will push on first commit")

    return {"status": "synced", "worktree": worktree_path}
```

#### Commit Message Convention

**Format**: `<type>(<scope>): <message>`

**Types**:

| Type         | Purpose                  | Stage |
| ------------ | ------------------------ | ----- |
| `discovery`  | Discovery work           | 1     |
| `context`    | Context analysis         | 2     |
| `research`   | Research findings        | 3     |
| `design`     | Design decisions         | 4     |
| `plan`       | Planning artifacts       | 5     |
| `task`       | Task implementation      | 6     |
| `verify`     | Verification results     | 7     |
| `checkpoint` | Quality gate checkpoints | Any   |

**Scopes**:

- For stages 1-5: Artifact ID (e.g., `req-001`, `adr-003`)
- For stage 6: Task ID (e.g., `task-123`)
- For checkpoints: Checkpoint type (e.g., `human-verify`, `decision`)

**Examples**:

```text
discovery(req-001): Add authentication requirement
context(ctx-auth): Document existing OAuth2 patterns
research(res-jwt): Compare JWT vs session-based auth
design(adr-003): Choose JWT for stateless authentication
plan(task-045): Break down JWT implementation into 5 tasks
task(task-045): Add JWT middleware to auth service
verify(test-auth): All authentication tests passing
checkpoint(human-verify): Design review complete
```

#### State Recovery from Commits

**Scenario**: Session interrupted, need to resume work

```python
# Pseudo-code: Recover state from git history
def recover_stage_state(stage: int, project_path: str) -> dict:
    """Recover stage state from commit history"""
    worktree_path = f"{project_path}/.sam/worktrees/stage-{stage}"

    # Get commit history for this stage
    commits = run_git_command([
        "log",
        "--pretty=format:%H|%s|%an|%ai",
        "-n", "100"
    ], cwd=worktree_path).strip().split('\n')

    state = {
        'stage': stage,
        'completed_tasks': [],
        'checkpoints': [],
        'blockers': [],
        'last_activity': None
    }

    for commit in commits:
        sha, message, author, timestamp = commit.split('|')

        # Parse conventional commit
        match = re.match(r'^(\w+)\(([^)]+)\): (.+)$', message)
        if not match:
            continue

        commit_type, scope, description = match.groups()

        # Record activity
        if state['last_activity'] is None:
            state['last_activity'] = timestamp

        # Track task completions
        if commit_type == 'task':
            state['completed_tasks'].append({
                'task_id': scope,
                'description': description,
                'sha': sha,
                'timestamp': timestamp
            })

        # Track checkpoints
        elif commit_type == 'checkpoint':
            state['checkpoints'].append({
                'type': scope,
                'description': description,
                'sha': sha,
                'timestamp': timestamp,
                'status': 'passed'  # If commit exists, checkpoint passed
            })

    return state
```

#### Conflict Resolution Protocol

**Policy**: Different strategies per stage and file type

```yaml
# .sam/config/conflict-resolution.yaml
conflict_resolution:
  # SAM artifacts never conflict (isolated by stage)
  auto_resolve:
    - path: .sam/artifacts/discovery/
      strategy: ours  # Discovery writes to isolated directory
    - path: .sam/artifacts/context/
      strategy: ours  # Context writes to isolated directory
    - path: .sam/messages/
      strategy: ours  # Messages are append-only

  # Source code requires human review
  human_required:
    - path: src/
      reason: "Source code conflicts need careful merge"
    - path: tests/
      reason: "Test conflicts need understanding of test intent"

  # Documentation can often be auto-merged
  try_auto_merge:
    - path: docs/
      strategy: recursive
      options: [patience, diff-algorithm=histogram]

  # Configuration files are critical
  human_required:
    - path: "*.yaml"
      reason: "Config changes may have side effects"
    - path: "*.toml"
      reason: "Config changes may have side effects"
```

**Workflow**:

```python
# Pseudo-code: Conflict resolution
def handle_merge_conflict(worktree_path: str, file_path: str):
    """Handle merge conflict based on policy"""
    policy = load_conflict_policy()

    # Check auto-resolve rules
    for rule in policy['auto_resolve']:
        if file_path.startswith(rule['path']):
            strategy = rule['strategy']
            run_git_command([
                "checkout", f"--{strategy}", file_path
            ], cwd=worktree_path)
            run_git_command(["add", file_path], cwd=worktree_path)
            return {"status": "auto_resolved", "strategy": strategy}

    # Check try-auto-merge rules
    for rule in policy['try_auto_merge']:
        if file_path.startswith(rule['path']):
            try:
                run_git_command([
                    "merge-file",
                    "--theirs",
                    file_path
                ], cwd=worktree_path)
                return {"status": "auto_merged"}
            except GitError:
                pass  # Fall through to human required

    # Human resolution required
    for rule in policy['human_required']:
        if file_path.startswith(rule['path']):
            raise HumanResolutionRequired(
                f"Conflict in {file_path}: {rule['reason']}"
            )

    # Default: Human required
    raise HumanResolutionRequired(
        f"Unknown conflict in {file_path}, manual resolution needed"
    )
```

#### Identity Preservation

**Purpose**: Git history shows which agent did what work

```python
# Pseudo-code: Set agent identity per worktree
def setup_agent_identity(worktree_path: str, agent_name: str):
    """Set git identity for agent in worktree"""
    config = load_agent_config(agent_name)
    identity = config['worktree']['identity']

    # Set user name and email (worktree-local)
    run_git_command([
        "config", "--worktree",
        "user.name", identity['name']
    ], cwd=worktree_path)

    run_git_command([
        "config", "--worktree",
        "user.email", identity['email']
    ], cwd=worktree_path)

    # Optional: Set custom commit template
    template_path = f".sam/config/commit-templates/{agent_name}.txt"
    if file_exists(template_path):
        run_git_command([
            "config", "--worktree",
            "commit.template", template_path
        ], cwd=worktree_path)
```

**Example git log**:

```text
commit a1b2c3d (sam/stage-6-implementation)
Author: SAM Implementation Agent <implementation@sam.local>
Date:   Mon Jan 27 14:30:00 2025 -0800

    task(task-045): Add JWT authentication middleware

commit e4f5g6h
Author: SAM Design Agent <design@sam.local>
Date:   Mon Jan 27 12:00:00 2025 -0800

    design(adr-003): Choose JWT for stateless authentication

commit i7j8k9l
Author: SAM Context Agent <context@sam.local>
Date:   Mon Jan 27 10:15:00 2025 -0800

    context(ctx-auth): Document existing OAuth2 patterns
```

## Implementation Roadmap

### Phase 1: Core Infrastructure (Weeks 1-2)

**Goal**: Establish filesystem-based artifact storage and basic message queue

**Deliverables**:

1. `.sam/` directory structure creation
2. Artifact schemas for all 7 stages
3. Filesystem-based artifact CRUD
4. Message queue (inbox/outbox/archive)
5. Basic YAML configuration loading

**Validation**:

- Can create, read, update, delete artifacts
- Can send/receive messages
- Can load agent definitions from YAML

### Phase 2: Git Worktree Integration (Weeks 3-4)

**Goal**: Implement gastown-inspired worktree management

**Deliverables**:

1. Worktree creation with sparse checkout
2. Agent identity configuration per worktree
3. Auto-sync workflow (pull with rebase)
4. Commit message parsing
5. State recovery from git history

**Validation**:

- Can create isolated worktrees per stage
- Commits show agent attribution
- Can recover state after interruption
- Auto-sync works without conflicts

### Phase 3: MCP Server (Weeks 5-6)

**Goal**: Expose infrastructure via MCP protocol

**Deliverables**:

1. FastMCP server implementation
2. Tool definitions (artifact CRUD, messaging, worktree)
3. Resource definitions (artifact access, config)
4. Prompt definitions (stage guidance)
5. Integration with existing SAM skills

**Validation**:

- Can call SAM tools from Claude
- Can access SAM resources
- Can load SAM prompts
- Skills successfully use MCP tools

### Phase 4: SQLite Index (Weeks 7-8)

**Goal**: Add optional SQLite index for fast queries

**Deliverables**:

1. SQLite schema definition
2. Sync mechanism (filesystem → SQLite)
3. Full-text search (FTS5)
4. Relationship tracking
5. Migration tool (existing artifacts → index)

**Validation**:

- Index stays in sync with filesystem
- Full-text search is fast (<100ms)
- Can query artifact relationships
- Migration handles 1000+ artifacts

### Phase 5: Agent Integration (Weeks 9-10)

**Goal**: Integrate SAM infrastructure with existing agents

**Deliverables**:

1. Update SAM skills to use MCP tools
2. Update agent definitions with worktree config
3. Add message subscription logic to agents
4. Implement checkpoint protocol
5. Update orchestrator to use infrastructure

**Validation**:

- Agents successfully create artifacts
- Agents send/receive messages
- Checkpoints block progress correctly
- Orchestrator coordinates multi-agent work

### Phase 6: Tooling & Documentation (Weeks 11-12)

**Goal**: Provide CLI tools and comprehensive docs

**Deliverables**:

1. `sam` CLI tool for infrastructure management
   - `sam init` - Initialize SAM infrastructure
   - `sam status` - Show project status
   - `sam stage` - Activate stage
   - `sam sync` - Sync all worktrees
   - `sam verify` - Validate artifact integrity
2. User documentation
3. Agent development guide
4. Troubleshooting guide
5. Migration guide (existing projects → SAM)

**Validation**:

- CLI works on new project
- Documentation covers all features
- Migration guide tested on 3 projects

## Backend Options Analysis

| Factor                 | Filesystem      | Filesystem + SQLite | Cloud (Supabase)       | Git Issues            |
| ---------------------- | --------------- | ------------------- | ---------------------- | --------------------- |
| **Setup complexity**   | Minimal (mkdir) | Low (schema setup)  | Medium (cloud account) | Low (git platform)    |
| **Search performance** | Slow (grep)     | Fast (<100ms)       | Very fast (indexed)    | Slow (API calls)      |
| **Multi-user**         | Via git         | Via git             | Native                 | Native                |
| **Offline work**       | ✅ Full         | ✅ Full             | ❌ Requires network    | ❌ Requires network   |
| **Storage cost**       | Free (disk)     | Free (disk)         | $25/mo (500MB)         | Free (public repos)   |
| **Human readability**  | ✅ Markdown     | ✅ Markdown         | ⚠️ Database            | ✅ Web UI             |
| **Version control**    | ✅ Git          | ✅ Git              | ⚠️ Manual              | ✅ Git                |
| **Query capability**   | ❌ grep only    | ✅ SQL              | ✅ SQL + pgvector      | ⚠️ GitHub API         |
| **Semantic search**    | ❌ No           | ❌ No               | ✅ pgvector            | ❌ No                 |
| **Best for**           | Small projects  | Medium projects     | Team collaboration     | GitHub-based workflow |

**Recommendation matrix**:

| Project Size              | Team Size      | Recommendation                        |
| ------------------------- | -------------- | ------------------------------------- |
| Small (<50 artifacts)     | 1 developer    | Filesystem only                       |
| Medium (50-500 artifacts) | 1-3 developers | Filesystem + SQLite                   |
| Large (500+ artifacts)    | 3+ developers  | Filesystem + SQLite + Cloud backup    |
| Enterprise                | 10+ developers | Cloud (Supabase) with semantic search |

## Integration with Existing SAM

### Artifact Flow Between Stages

```text
Stage 1 (Discovery)
    ↓ produces
    requirements.md, interviews/
    ↓ consumed by
Stage 2 (Context)
    ↓ produces
    codebase-analysis/, patterns/
    ↓ consumed by
Stage 3 (Research)
    ↓ produces
    research-{topic}.md
    ↓ consumed by
Stage 4 (Design)
    ↓ produces
    architecture.md, adr-{id}.md
    ↓ consumed by
Stage 5 (Planning)
    ↓ produces
    plan.md, task-{id}.md
    ↓ consumed by
Stage 6 (Implementation)
    ↓ produces
    execution-log.md, commits/
    ↓ consumed by
Stage 7 (Delivery)
    ↓ produces
    verification.md, release-notes.md
```

### Verification Gates and Checkpoints

**Integration points** between stages:

```yaml
# Example: Integration between Stage 1 and Stage 2
stage_integration:
  from_stage: 1  # Discovery
  to_stage: 2    # Context

  # Verify Stage 1 outputs before Stage 2 starts
  verification:
    required_artifacts:
      - .sam/artifacts/discovery/requirements.md
    quality_checks:
      - name: requirements_completeness
        command: .sam/scripts/validate-requirements.py
        expected: exit_code=0
      - name: checkpoint_passed
        condition: "checkpoint(human-verify) in messages"

  # Hand off artifacts to Stage 2
  handoff:
    artifacts:
      - from: .sam/artifacts/discovery/requirements.md
        to: .sam/artifacts/context/requirements-snapshot.md
        action: copy  # Snapshot for reference
    message:
      type: delegation
      from: orchestrator
      to: context
      content: |
        Discovery complete. Requirements documented in requirements.md.
        Begin context gathering for components mentioned in requirements.
```

### Orchestrator Integration

**How orchestrator uses infrastructure**:

```python
# Pseudo-code: Orchestrator workflow
class SAMOrchestrator:
    def __init__(self, project_path: str):
        self.project_path = project_path
        self.config = load_yaml('.sam/config/pipeline.yaml')
        self.current_stage = self.detect_current_stage()

    def detect_current_stage(self) -> int:
        """Detect current stage based on artifacts and messages"""
        for stage_num in range(7, 0, -1):  # Check from Stage 7 backward
            if self.stage_complete(stage_num):
                return stage_num
        return 1  # Default to Stage 1 if nothing complete

    def stage_complete(self, stage: int) -> bool:
        """Check if stage completion criteria met"""
        stage_config = self.config['stages'][stage - 1]

        # Check required artifacts exist
        for artifact_path in stage_config['outputs']['required']:
            if not file_exists(artifact_path):
                return False

        # Check checkpoints passed
        for checkpoint in stage_config['checkpoints']:
            if checkpoint.get('blocking'):
                if not self.checkpoint_passed(checkpoint):
                    return False

        # Check completion message received
        messages = read_inbox('orchestrator', message_type='completion')
        stage_complete_msg = any(
            msg['stage'] == stage for msg in messages
        )

        return stage_complete_msg

    def activate_stage(self, stage: int):
        """Activate a SAM stage"""
        stage_config = self.config['stages'][stage - 1]

        # Setup worktrees for stage agents
        for agent_config in stage_config['agents']:
            agent_name = agent_config['name']
            setup_stage_worktree(stage, self.project_path)
            sync_worktree(f".sam/worktrees/stage-{stage}")

        # Activate agents
        for agent_config in stage_config['agents']:
            if agent_config['activation'] == 'auto':
                self.activate_agent(agent_config, stage)

        # Monitor progress
        self.monitor_stage_progress(stage)

    def activate_agent(self, agent_config: dict, stage: int):
        """Activate agent for stage"""
        agent_name = agent_config['name']

        # Send delegation message
        send_message(
            from_agent='orchestrator',
            to_agent=agent_name,
            message_type='delegation',
            subject=f'Begin Stage {stage}',
            content=f'Activate {agent_name} for stage {stage} work'
        )

        # Launch agent subprocess
        # (Actual agent activation via Task tool in real implementation)
        launch_agent(agent_name, stage_config['inputs'])

    def monitor_stage_progress(self, stage: int):
        """Monitor stage progress via messages"""
        while not self.stage_complete(stage):
            # Read progress messages
            messages = read_inbox('orchestrator', message_type='progress')
            for msg in messages:
                log_progress(msg)
                acknowledge_message(msg['id'], 'orchestrator')

            # Check for blocking messages
            blocking = read_inbox('orchestrator', message_type='blocking')
            if blocking:
                self.handle_blockers(blocking)

            # Check checkpoints
            self.check_quality_gates(stage)

            time.sleep(5)  # Poll every 5 seconds

    def handle_blockers(self, blocking_messages: list):
        """Handle blocking issues"""
        for msg in blocking_messages:
            # Notify user
            print(f"BLOCKED: {msg['subject']}")
            print(f"Agent: {msg['from']}")
            print(f"Details: {msg['content']}")

            # Wait for user action
            user_input = input("Action taken? (y/n): ")
            if user_input.lower() == 'y':
                # Send unblock message
                send_message(
                    from_agent='orchestrator',
                    to_agent=msg['from'],
                    message_type='response',
                    subject='Blocker resolved',
                    content='User has resolved the blocking issue'
                )
                acknowledge_message(msg['id'], 'orchestrator')

    def check_quality_gates(self, stage: int):
        """Check quality gate checkpoints"""
        stage_config = self.config['stages'][stage - 1]

        for checkpoint in stage_config['checkpoints']:
            if not self.checkpoint_passed(checkpoint):
                self.wait_for_checkpoint(checkpoint)

    def checkpoint_passed(self, checkpoint: dict) -> bool:
        """Check if checkpoint passed"""
        checkpoint_type = checkpoint['type']
        condition = checkpoint['condition']

        # Check for checkpoint message
        messages = read_inbox('orchestrator', message_type='checkpoint')
        for msg in messages:
            if msg['subject'].startswith(checkpoint['name']):
                acknowledge_message(msg['id'], 'orchestrator')
                return True

        return False

    def wait_for_checkpoint(self, checkpoint: dict):
        """Wait for checkpoint to pass"""
        checkpoint_type = checkpoint['type']

        if checkpoint_type == 'human-verify':
            print(f"Checkpoint: {checkpoint['name']}")
            print(f"Condition: {checkpoint['condition']}")
            user_input = input("Approve? (y/n): ")
            if user_input.lower() == 'y':
                # Record checkpoint pass
                create_artifact(
                    type='checkpoint',
                    stage=self.current_stage,
                    content=f"Checkpoint {checkpoint['name']} approved by user"
                )
        elif checkpoint_type == 'decision':
            print(f"Decision required: {checkpoint['name']}")
            # Present options to user
            # Record decision
        elif checkpoint_type == 'human-action':
            print(f"Action required: {checkpoint['name']}")
            input("Press Enter when complete...")
```

## Next Steps

With this infrastructure layer specification complete, the next steps are:

1. **Prototype Phase 1** (Core Infrastructure):

   - Implement filesystem artifact storage
   - Implement message queue
   - Test with simple SAM workflow (Stages 1-2)

2. **Validate Design**:

   - Run prototype on 2-3 real projects
   - Gather feedback on agent experience
   - Iterate on artifact schemas and message types

3. **Implement Phases 2-6**:

   - Follow implementation roadmap
   - Validate each phase before proceeding
   - Document lessons learned

4. **Create SAM Meta-Template**:
   - Use this infrastructure to create meta-SAM
   - Apply SAM methodology to SAM development itself
   - Close the meta-circular loop

This infrastructure layer will transform SAM from a conceptual methodology into a production-ready system with persistent state, multi-agent coordination, and comprehensive traceability.
