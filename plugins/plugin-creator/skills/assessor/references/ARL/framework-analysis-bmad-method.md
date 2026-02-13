# Framework Analysis: BMAD-METHOD

**Repository**: `/home/ubuntulinuxqa2/repos/BMAD-METHOD/`
**Version**: v6 (beta), npm package `bmad-method`
**License**: MIT
**Analysis Date**: 2026-02-13

---

## A. System Overview

### What is BMAD-METHOD?

BMAD (Breakthrough Method of Agile AI-Driven Development) is a framework that structures AI-assisted software development into a phased workflow with specialized AI agent personas. It provides 12+ agent personas, 34+ workflows, and scale-adaptive intelligence that adjusts from bug fixes to enterprise systems.

> "Traditional AI tools do the thinking for you, producing average results. BMad agents and facilitated workflow act as expert collaborators who guide you through a structured process to bring out your best thinking in partnership with the AI."
>
> -- `README.md:14`

### Core Philosophy

BMAD treats the human as the domain expert and decision-maker, with AI agents serving as structured facilitators. The framework enforces a progressive document-building approach where each phase produces artifacts that become context for the next phase, ensuring agents "always know what to build and why."

> "The BMM system builds that context progressively across 4 distinct phases - each phase, and multiple workflows optionally within each phase, produce documents that inform the next, so agents always know what to build and why."
>
> -- `docs/reference/workflow-map.md:8`

### Target Audience and Use Case

- Individual developers using AI-powered IDEs (Claude Code, Cursor, Windsurf, etc.)
- Teams building software products of any scale
- Installed via `npx bmad-method install` into any project directory
- Supports multiple IDE targets with generated command files

### Problem It Solves

Without structured context, AI agents make inconsistent, conflicting decisions. BMAD solves this by:

1. Front-loading planning decisions into explicit documents
2. Providing specialized agent personas with domain expertise
3. Enforcing document-driven context passing between phases
4. Offering scale-adaptive workflows (Quick Flow for small tasks, full methodology for complex products)

---

## B. Autonomous Development Model

### Front-Loading Human Effort

BMAD is explicitly NOT an autonomous development system. It is a **human-in-the-loop facilitated workflow** that front-loads planning effort through structured conversation. The human participates at every step, with the AI agents facilitating through menus, questions, and structured elicitation.

> "YOU ARE FACILITATING A CONVERSATION With a user to produce a final document step by step. The whole process is meant to be collaborative helping the user flesh out their ideas. Do not rush or optimize and skip any section."
>
> -- `src/core/tasks/workflow.xml:231-232`

The framework's workflow engine enforces this explicitly:

> "Full user interaction and confirmation of EVERY step at EVERY template output - NO EXCEPTIONS except yolo MODE"
>
> -- `src/core/tasks/workflow.xml:107`

### The 4-Phase Pipeline

#### Phase 1: Analysis (Optional)

Explore the problem space before committing to planning.

| Workflow | Agent | Produces |
|----------|-------|----------|
| `brainstorming` | Mary (Analyst) | `brainstorming-report.md` |
| `research` (3 variants: market, domain, technical) | Mary (Analyst) | Research findings |
| `create-product-brief` | Mary (Analyst) | `product-brief.md` |

Source: `docs/reference/workflow-map.md:22-30`, `src/bmm/agents/analyst.agent.yaml`

#### Phase 2: Planning (Required for full method)

Define what to build and for whom.

| Workflow | Agent | Produces |
|----------|-------|----------|
| `create-prd` | John (PM) | `PRD.md` (12 steps) |
| `validate-prd` | John (PM) | Validation report (13 steps) |
| `create-ux-design` | Sally (UX Designer) | `ux-spec.md` (14 steps) |

Source: `docs/reference/workflow-map.md:33-39`

The PRD creation workflow is the most elaborate, with 12 steps covering discovery, success metrics, user journeys, domain analysis, innovation assessment, project type detection, scoping, functional requirements, non-functional requirements, and polish.

Source: `src/bmm/workflows/2-plan-workflows/create-prd/steps-c/` (12 step files)

#### Phase 3: Solutioning

Decide HOW to build it and break work into stories.

| Workflow | Agent | Produces |
|----------|-------|----------|
| `create-architecture` | Winston (Architect) | `architecture.md` with ADRs (8 steps) |
| `create-epics-and-stories` | John (PM) | Epic files with stories (4 steps) |
| `check-implementation-readiness` | Multi-role | PASS/CONCERNS/FAIL decision (6 steps) |

Source: `docs/reference/workflow-map.md:42-49`

> "Phase 3 (Solutioning) translates what to build (from Planning) into how to build it (technical design). This phase prevents agent conflicts in multi-epic projects by documenting architectural decisions before implementation begins."
>
> -- `docs/explanation/why-solutioning-matters.md:9`

#### Phase 4: Implementation

Build it, one story at a time.

| Workflow | Agent | Produces |
|----------|-------|----------|
| `sprint-planning` | Bob (SM) | `sprint-status.yaml` |
| `create-story` | Bob (SM) | `story-[slug].md` |
| `dev-story` | Amelia (Dev) | Working code + tests |
| `code-review` | Amelia (Dev) | Approved or changes requested |
| `correct-course` | Bob (SM) / John (PM) | Updated plan or re-routing |
| `retrospective` | Bob (SM) | Lessons learned |

Source: `docs/reference/workflow-map.md:52-63`

### Human Decision Points vs Automated Decision Points

**Human decision points** (every step by default):

- After every `template-output` tag, the workflow engine halts and presents: `[a] Advanced Elicitation, [c] Continue, [p] Party-Mode, [y] YOLO the rest` (`src/core/tasks/workflow.xml:75-90`)
- All `ask` tags require human input before proceeding
- All optional steps require user consent (unless YOLO mode)
- Story selection for implementation
- Escalation decisions in Quick Flow
- Final sign-off on all artifacts

**Automated decision points**:

- Domain complexity detection from project signals (`src/bmm/workflows/2-plan-workflows/create-prd/data/domain-complexity.csv`)
- Project type classification from detection signals (`src/bmm/workflows/2-plan-workflows/create-prd/data/project-types.csv`)
- Quick Flow escalation threshold evaluation (`src/bmm/workflows/bmad-quick-flow/quick-dev/steps/step-01-mode-detection.md:66-81`)
- Sprint status detection and story file discovery
- Input file pattern resolution (sharded vs whole documents)

### Handling Scope: Quick Flow vs Full Method

BMAD offers three planning tracks:

| Track | Best For | Documents |
|-------|----------|-----------|
| Quick Flow | Bug fixes, small features, 1-15 stories | Tech-spec only |
| BMad Method | Products, platforms, 10-50+ stories | PRD + Architecture + UX |
| Enterprise | Compliance, multi-tenant, 30+ stories | PRD + Architecture + Security + DevOps |

Source: `docs/tutorials/getting-started.md:43-48`

Quick Flow provides a parallel track that bypasses Phases 1-3 entirely:

1. `quick-spec` -- conversational discovery, codebase scan, tech-spec generation (4 steps)
2. `quick-dev` -- implementation with self-check and adversarial review (6 steps)

Quick Flow includes built-in scope detection and escalation:

> "When you run quick-dev with a direct request, it evaluates signals like multi-component mentions, system-level language, and uncertainty about approach. If it detects the work is bigger than a quick flow: Light escalation - Recommends running quick-spec first. Heavy escalation - Recommends switching to the full BMad Method PRD process."
>
> -- `docs/explanation/quick-flow.md:68-72`

---

## C. Key Concepts and Mechanisms

### Named Concepts

#### Agents (Personas)

BMAD defines agents as specialized AI personas with distinct roles, communication styles, and principles. Each agent has:

- **metadata**: id, name, title, icon, module, capabilities
- **persona**: role, identity, communication_style, principles
- **critical_actions**: hard constraints on behavior
- **menu**: list of workflows the agent can execute, triggered by short codes

BMM module agents (source: `src/bmm/agents/`):

| Agent Name | Role | Key Workflows |
|-----------|------|---------------|
| Mary (Analyst) | Strategic Business Analyst | Brainstorm, Research, Create Brief, Document Project |
| John (PM) | Product Manager | Create/Validate/Edit PRD, Create Epics, Implementation Readiness |
| Winston (Architect) | System Architect | Create Architecture, Implementation Readiness |
| Bob (SM) | Scrum Master | Sprint Planning, Create Story, Retrospective, Correct Course |
| Amelia (Dev) | Senior Software Engineer | Dev Story, Code Review |
| Quinn (QA) | QA Engineer | Test Automation |
| Barry (Quick Flow Solo Dev) | Full-Stack Developer | Quick Spec, Quick Dev, Code Review |
| Sally (UX Designer) | UX Designer | Create UX Design |
| Paige (Technical Writer) | Technical Writer | Document Project, Write Document, various utilities |
| BMad Master | Master Executor/Orchestrator | List Tasks, List Workflows, Party Mode orchestration |

Source: `docs/reference/agents.md:18-28`, individual agent YAML files

#### Workflows

Structured, multi-step processes executed by the workflow engine (`src/core/tasks/workflow.xml`). Two types:

1. **Template workflows** -- produce a document by progressively filling a template
2. **Action workflows** -- perform actions without producing a document (`template: false`)

Workflows are defined as YAML configuration files that reference:
- `instructions` (XML or markdown step files)
- `template` (output document template)
- `validation` (checklist for quality gates)
- `input_file_patterns` (smart document discovery)
- `config_source` (variable resolution)

Source: `src/core/tasks/workflow.xml:20-44`

#### The Workflow Engine

The core execution engine (`src/core/tasks/workflow.xml`, 234 lines) is an XML task that:

1. Loads and resolves workflow YAML configuration
2. Resolves variables from config sources and system
3. Loads instructions (step files)
4. Executes steps sequentially with user interaction
5. Handles `template-output` tags with mandatory pauses
6. Supports conditional execution, loops, and sub-workflow invocation
7. Implements the `discover_inputs` protocol for smart file loading

Key XML tags supported: `action`, `check`, `ask`, `goto`, `invoke-workflow`, `invoke-task`, `invoke-protocol`, `template-output`

Source: `src/core/tasks/workflow.xml:112-135`

#### YOLO Mode

A workflow execution mode that skips all confirmations and elicitation, "simulating the remaining discussions with a simulated expert user" to produce artifacts automatically. Activated per-workflow by user selection.

> "Skip all confirmations and elicitation, minimize prompts and try to produce all of the workflow automatically by simulating the remaining discussions with an simulated expert user"
>
> -- `src/core/tasks/workflow.xml:108-109`

#### Party Mode

Multi-agent collaboration in a single conversation. BMad Master orchestrates, picking relevant agents per message. Agents respond in character, can disagree and build on each other's ideas.

> "Run party-mode and you've got your whole AI team in one room - PM, Architect, Dev, UX Designer, whoever you need. BMad Master orchestrates, picking relevant agents per message."
>
> -- `docs/explanation/party-mode.md:10`

Source: `src/core/workflows/party-mode/` (3 step files)

#### Advanced Elicitation

A structured second-pass mechanism where the AI re-examines its output through a specific reasoning method. Available at every `template-output` point. Includes dozens of methods stored in `src/core/workflows/advanced-elicitation/methods.csv`:

- Pre-mortem Analysis
- First Principles Thinking
- Inversion
- Red Team vs Blue Team
- Socratic Questioning
- Constraint Removal
- Stakeholder Mapping
- Analogical Reasoning

Source: `docs/explanation/advanced-elicitation.md`, `src/core/workflows/advanced-elicitation/workflow.xml`

#### Adversarial Review

A review technique where the reviewer MUST find issues -- "no 'looks good' allowed." Zero findings triggers a halt. Used in code review, implementation readiness, spec validation, and quick-dev self-check.

> "The core rule: You must find issues. Zero findings triggers a halt - re-analyze or explain why."
>
> -- `docs/explanation/adversarial-review.md:16`

The code-review workflow description explicitly states:

> "Perform an ADVERSARIAL Senior Developer code review that finds 3-10 specific problems in every story. Challenges everything: code quality, test coverage, architecture compliance, security, performance. NEVER accepts 'looks good' - must find minimum issues"
>
> -- `src/bmm/workflows/4-implementation/code-review/workflow.yaml:3`

Source: `docs/explanation/adversarial-review.md`

#### Domain-Complexity Detection

CSV-driven lookup that classifies projects by domain (healthcare, fintech, govtech, etc.) and adjusts workflow depth accordingly. Each domain entry specifies:

- Detection signals (keywords)
- Complexity level (low/medium/high)
- Key concerns
- Required knowledge areas
- Suggested workflow paths
- Web search triggers
- Special sections to add

Source: `src/bmm/workflows/2-plan-workflows/create-prd/data/domain-complexity.csv` (15 domain entries)

#### Project Type Detection

Similar CSV-driven classification for project types (API backend, mobile app, SaaS B2B, CLI tool, web app, etc.) that determines which PRD sections to include or skip.

Source: `src/bmm/workflows/2-plan-workflows/create-prd/data/project-types.csv` (11 project types)

### State Management Across Agent Handoffs

BMAD manages state through **documents on disk**, not in-memory state:

1. **Planning artifacts directory** -- PRD, architecture, UX spec, epics
2. **Implementation artifacts directory** -- sprint status, story files, reviews
3. **Project knowledge directory** -- long-term project documentation
4. **project-context.md** -- codebase conventions and rules

The sprint-status.yaml file acts as the central coordination mechanism for implementation:

```yaml
development_status:
  epic-1: backlog
  1-1-user-authentication: done
  1-2-account-management: ready-for-dev
  epic-1-retrospective: optional
```

Status flow for stories: `backlog -> ready-for-dev -> in-progress -> review -> done`

Source: `src/bmm/workflows/4-implementation/sprint-planning/sprint-status-template.yaml`

The `input_file_patterns` mechanism in workflow YAML files provides smart document discovery with three strategies:

- **FULL_LOAD** -- load all files in a directory
- **SELECTIVE_LOAD** -- load specific files based on context
- **INDEX_GUIDED** -- load index.md, analyze structure, intelligently load relevant docs

Source: `src/core/tasks/workflow.xml:138-221`

Each workflow recommends running in a **fresh chat/context** to avoid context pollution:

> "Always start a fresh chat for each workflow. This prevents context limitations from causing issues."
>
> -- `docs/tutorials/getting-started.md:76`

### Quality Gates and Verification

#### Implementation Readiness Check (Phase 3 Gate)

A 6-step adversarial assessment that validates PRD, Architecture, and Epics/Stories for completeness and alignment before Phase 4 starts. Produces a readiness report with READY/NEEDS WORK/NOT READY status.

Steps:
1. Document Discovery
2. PRD Analysis
3. Epic Coverage Validation
4. UX Alignment
5. Epic Quality Review
6. Final Assessment

Source: `src/bmm/workflows/3-solutioning/check-implementation-readiness/` (6 step files + workflow.md)

#### Code Review (Phase 4 Gate)

Adversarial code review that loads architecture and story file as context, constructs a diff, and forces finding 3-10 problems.

Source: `src/bmm/workflows/4-implementation/code-review/workflow.yaml`

#### Dev Story Self-Check (Phase 4 Internal)

Before code review, the dev-story workflow performs a self-audit:
- All tasks verified complete
- All tests passing
- All acceptance criteria satisfied
- Patterns followed

Source: `src/bmm/workflows/bmad-quick-flow/quick-dev/steps/step-04-self-check.md`

#### PRD Validation (Phase 2 Gate)

A 13-step validation workflow that checks:
- Format detection
- Parity check
- Density validation
- Brief coverage validation
- Measurability validation
- Traceability validation
- Implementation leakage validation
- Domain compliance validation
- Project type validation
- SMART validation
- Holistic quality validation
- Completeness validation

Source: `src/bmm/workflows/2-plan-workflows/create-prd/steps-v/` (13 step files)

### Convergence: Knowing When "Done"

BMAD uses explicit status tracking and checklists rather than automated convergence detection:

- Sprint status YAML tracks story states through the `backlog -> ready-for-dev -> in-progress -> review -> done` pipeline
- Each workflow step has explicit SUCCESS/FAILURE METRICS sections
- The dev-story workflow has a critical rule: "Absolutely DO NOT stop because of 'milestones', 'significant progress', or 'session boundaries'. Continue in a single execution until the story is COMPLETE" (`src/bmm/workflows/4-implementation/dev-story/instructions.xml:11-12`)
- Implementation readiness check produces READY/NEEDS WORK/NOT READY verdict
- Code review produces approved or changes-requested outcome
- Epic completion triggers retrospective

### Error, Failure, and Recovery

#### Correct Course Workflow

For significant mid-sprint changes, the `correct-course` workflow loads all planning documents, analyzes impact, proposes solutions, and routes for implementation.

Source: `src/bmm/workflows/4-implementation/correct-course/workflow.yaml`

#### Escalation in Quick Flow

Quick-dev detects scope creep through signal analysis and offers escalation:
- Level 0-2: Recommend tech-spec first
- Level 3+: Recommend full BMad Method PRD process

Source: `src/bmm/workflows/bmad-quick-flow/quick-dev/steps/step-01-mode-detection.md:66-146`

#### Step-Level Recovery

Each step file includes explicit FAILURE MODES sections listing what can go wrong and how to detect it. For example, the adversarial review step lists:

> "Missing baseline_commit (can't construct accurate diff), Not including new untracked files in diff, Invoking task without providing diff input, Accepting zero findings without questioning"
>
> -- `src/bmm/workflows/bmad-quick-flow/quick-dev/steps/step-05-adversarial-review.md:100-104`

#### Document-Level Recovery

Since all state is in documents on disk, recovery from context loss is straightforward -- restart a fresh chat, load the relevant documents, and continue. The `step-01b-continue.md` files in several workflows handle session resumption.

---

## D. Front-Loading Pattern

### Information Captured Upfront

BMAD captures the following before any code is written:

1. **Module configuration** (`config.yaml`):
   - Project name, user name, skill level
   - Communication language, document output language
   - Artifact directory paths

   Source: `src/bmm/module.yaml`

2. **Product Brief** (Phase 1, optional):
   - Problem statement, vision, target users
   - Success metrics, scope boundaries

3. **PRD** (Phase 2, 12-step facilitated creation):
   - User personas and journeys
   - Functional requirements (FRs)
   - Non-functional requirements (NFRs)
   - Success metrics and KPIs
   - Domain-specific concerns
   - Innovation assessment
   - Project type classification
   - Scoping decisions

4. **UX Specification** (Phase 2, optional, 14 steps):
   - Core experience definition
   - Emotional response design
   - Design system and visual foundation
   - User journeys and component strategy
   - Responsive and accessibility requirements

5. **Architecture Document** (Phase 3, 8 steps):
   - Technology selection with ADRs (Architecture Decision Records)
   - Design patterns and conventions
   - Directory structure
   - Integration points

6. **Epics and Stories** (Phase 3, 4 steps):
   - Work breakdown from PRD+Architecture
   - BDD acceptance criteria (Given/When/Then)
   - Source hints linking back to PRD/Architecture sections

7. **Implementation Readiness Report** (Phase 3 gate):
   - Cross-document alignment validation
   - Gap analysis

8. **Project Context** (brownfield projects):
   - Existing codebase conventions and rules
   - All implementation workflows load this if it exists

### Artifacts Produced During Planning

| Artifact | Source Phase | Key Content |
|----------|-------------|-------------|
| `brainstorming-report.md` | Phase 1 | Ideas, techniques used, organized findings |
| `research-*.md` | Phase 1 | Market/domain/technical research findings |
| `product-brief.md` | Phase 1 | Strategic vision and scope |
| `PRD.md` | Phase 2 | Full requirements with FRs/NFRs |
| `ux-spec.md` | Phase 2 | UX design specification |
| `architecture.md` | Phase 3 | Technical decisions with ADRs |
| `epics.md` or `epics/*.md` | Phase 3 | Work breakdown with stories |
| `implementation-readiness-report.md` | Phase 3 | Alignment validation |
| `sprint-status.yaml` | Phase 4 | Sprint tracking |
| `story-*.md` | Phase 4 | Individual story files with tasks |
| `project-context.md` | Cross-phase | Codebase conventions |

### Planning Completeness Decision

BMAD uses the **Implementation Readiness Check** as its explicit "planning complete enough" gate:

> "Validate that PRD, Architecture, Epics and Stories are complete and aligned before Phase 4 implementation starts, with a focus on ensuring epics and stories are logical and have accounted for all requirements and planning."
>
> -- `src/bmm/workflows/3-solutioning/check-implementation-readiness/workflow.md:8`

The check produces a READY/NEEDS WORK/NOT READY verdict. However, the human decides whether to proceed even with a NEEDS WORK result.

For Quick Flow, planning completeness is simpler: the tech-spec includes a review step where the user signs off before implementation begins.

---

## E. Unique Innovations

### Distinctive Patterns

#### 1. Scale-Domain-Adaptive Planning

BMAD automatically adjusts planning depth based on two CSV-driven classification systems:

- **Domain complexity** (15 domains: healthcare, fintech, govtech, aerospace, etc.) -- determines required knowledge areas, key concerns, special document sections, and web search triggers
- **Project type** (11 types: API backend, mobile app, SaaS B2B, etc.) -- determines which PRD sections to include or skip

> "Automatically adjusts planning depth and needs based on project complexity, domain and type - a SaaS Mobile Dating App has different planning needs from a diagnostic medical system"
>
> -- `README.md:17`

This is a data-driven approach rather than hardcoded logic, making it extensible via CSV editing.

Source: `src/bmm/workflows/2-plan-workflows/create-prd/data/domain-complexity.csv`, `src/bmm/workflows/2-plan-workflows/create-prd/data/project-types.csv`

#### 2. Multi-Agent Persona System with Character Persistence

Each agent has a distinct name, personality, communication style, and domain expertise:

- Mary (Analyst): "Speaks with the excitement of a treasure hunter - thrilled by every clue"
- John (PM): "Asks 'WHY?' relentlessly like a detective on a case"
- Winston (Architect): "Speaks in calm, pragmatic tones, balancing 'what could be' with 'what should be'"
- Amelia (Dev): "Ultra-succinct. Speaks in file paths and AC IDs - every statement citable"
- Bob (SM): "Crisp and checklist-driven. Every word has a purpose, every requirement crystal clear"
- Barry (Quick Flow): "Direct, confident, and implementation-focused. Uses tech slang"

This persona system creates differentiated interaction styles for different project phases.

Source: Individual agent YAML files in `src/bmm/agents/`

#### 3. Party Mode (Multi-Perspective Simulation)

The ability to bring multiple agent personas into a single conversation for collaborative discussion. BMad Master orchestrates which agents respond to each message.

> "Agents respond in character, agree, disagree, and build on each other's ideas."
>
> -- `docs/explanation/party-mode.md:10`

This creates simulated multi-stakeholder discussions within a single AI session.

Source: `src/core/workflows/party-mode/` (3 step files)

#### 4. Advanced Elicitation at Every Decision Point

Every `template-output` point in every workflow offers the option to run structured reasoning methods against the just-generated content. This creates a systematic "rethink" capability embedded in the workflow engine itself.

Source: `src/core/tasks/workflow.xml:75-90`, `src/core/workflows/advanced-elicitation/`

#### 5. YOLO Mode as Escape Hatch

The ability to switch from fully interactive to fully autonomous mid-workflow, simulating an expert user's responses for the remainder. This provides a graceful degradation from human-in-the-loop to autonomous when the user decides the quality is sufficient.

Source: `src/core/tasks/workflow.xml:108-109`

#### 6. Document Sharding with Smart Loading

Large documents can be split into multiple files (sharding), and the workflow engine has three loading strategies (FULL_LOAD, SELECTIVE_LOAD, INDEX_GUIDED) to efficiently load only what's needed for each workflow step.

Source: `src/core/tasks/workflow.xml:138-221`, `docs/how-to/shard-large-documents.md`

#### 7. Mandatory Adversarial Review

The code review workflow requires finding 3-10 issues in every review. Zero findings is treated as a failure mode, not a success. This addresses the well-known "looks good to me" rubber-stamp problem in AI code review.

Source: `src/bmm/workflows/4-implementation/code-review/workflow.yaml:3`

#### 8. Modular Extension System

BMAD supports official and community modules that extend the base framework:
- BMad Builder (BMB) -- for creating custom agents/workflows/modules
- Test Architect (TEA) -- enterprise test strategy
- Game Dev Studio (BMGD) -- game development
- Creative Intelligence Suite (CIS) -- brainstorming and innovation

The `/bmad-help` command evolves based on installed modules, providing context-aware guidance that accounts for all available capabilities.

Source: `docs/reference/modules.md`, `README.md:72-84`

#### 9. IDE-Agnostic Installation with IDE-Specific Generation

The installer generates IDE-specific command files from the same source definitions, supporting Claude Code, Cursor, Windsurf, Gemini, Kiro, OpenCode, and others through templates.

Source: `tools/cli/installers/lib/ide/templates/combined/` (27 template files for various IDEs)

#### 10. Continuous Execution in Dev-Story

The dev-story workflow explicitly mandates that the AI should NOT stop for "milestones" or "significant progress" -- it must continue until the entire story is complete:

> "Absolutely DO NOT stop because of 'milestones', 'significant progress', or 'session boundaries'. Continue in a single execution until the story is COMPLETE (all ACs satisfied and all tasks/subtasks checked) UNLESS a HALT condition is triggered or the USER gives other instruction."
>
> -- `src/bmm/workflows/4-implementation/dev-story/instructions.xml:11-12`

### Known Limitations and Gaps

#### 1. No True Autonomous Loop

BMAD is fundamentally human-in-the-loop. Even YOLO mode simulates human responses rather than implementing genuine autonomous refinement cycles. There is no mechanism for the system to detect when its output is insufficient and automatically iterate without human intervention.

#### 2. Context Window as Primary Constraint

The framework's recommendation to "always start a fresh chat for each workflow" reveals the fundamental context window limitation. State passes between workflows only through documents on disk, not through any persistent runtime state.

#### 3. Single-Session Agent Execution

Each agent runs in a single conversation session. There is no multi-agent orchestration where multiple AI instances collaborate in real-time. Party Mode simulates multiple agents but runs in a single LLM context.

#### 4. No Automated Quality Metrics

Quality gates (implementation readiness, code review) produce human-readable reports but no machine-parseable quality scores. There is no automated pass/fail threshold -- the human always makes the final call.

#### 5. File-System-Only Tracking

Sprint status tracking is file-system-only (`sprint-status.yaml`). The YAML comments note "Future will support other options from config of mcp such as jira, linear, trello" but this is not yet implemented.

Source: `src/bmm/workflows/4-implementation/sprint-planning/workflow.yaml:24`

#### 6. No Learning/Memory Across Projects

BMAD captures project-specific context but has no mechanism for learning across projects. Lessons learned in retrospectives are documented but not automatically applied to future projects.

#### 7. Workflow Rigidity vs Adaptability Trade-off

While domain and project type detection adapt the PRD creation workflow, the overall 4-phase pipeline is fixed. Teams with non-standard workflows must either fit into the framework's phases or use Quick Flow for everything.

---

## Summary Table: Relevance to Autonomous Refinement

| Aspect | BMAD-METHOD Approach | Relevance to ARL |
|--------|---------------------|------------------|
| **Autonomy level** | Human-in-the-loop with YOLO escape hatch | Baseline for comparison -- what structured human interaction looks like |
| **Quality gates** | Adversarial review, implementation readiness check | Pattern for quality verification -- mandatory finding of issues |
| **State management** | Documents on disk, sprint-status.yaml | Artifact-based state passing between autonomous stages |
| **Convergence** | Explicit checklists and status tracking | Task-level completion tracking, not output-quality convergence |
| **Scope adaptation** | CSV-driven domain/project classification | Data-driven planning depth adjustment |
| **Error recovery** | Correct-course workflow, escalation in Quick Flow | Manual recovery patterns, no automatic retry |
| **Front-loading** | 4-phase progressive context building | How to structure planning artifacts for autonomous consumption |
| **Multi-perspective** | Party Mode, Advanced Elicitation | Systematic "rethink" mechanisms at decision points |
