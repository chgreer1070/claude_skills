# Development-Harness Plugin Architecture

**Analysis Date:** 2026-03-18
**Plugin:** `development-harness`
**Version:** 0.1.0

## Executive Summary

The development-harness plugin implements a language-agnostic **Stateless Agent Methodology (SAM) 7-stage pipeline** that orchestrates feature development through structured phases. It composes with language-specific plugins via **language manifests** that declare specialist agents and quality gates. The harness owns process orchestration; language plugins own implementation specialists.

---

## Core Architecture

### Layer Model

```text
Layer 0 (Framework)
├── SAM 7-stage pipeline (stages S1–S7)
├── ARL human touchpoint gates
├── Artifact conventions & state management
├── RT-ICA information completeness framework
└── Generic stage agent dispatcher

Layer 1 (Language Plugin)
├── Language manifest (role fulfillment, quality gates, project detection)
├── Specialist agents (architect, test-designer, code-reviewer, design-spec)
├── Language-specific skills (optional stage-skill specializations)
└── Optional: Process flow override

Layer 2 (Stack Profile)
└── Stack-specific agent customizations (e.g., Typer CLI, FastAPI, etc.)
```

The harness (Layer 0) detects the project language, loads the language plugin's manifest (Layer 1), and resolves abstract roles to concrete agents before S1 begins.

---

## 7-Stage Pipeline

Each stage has a corresponding **workflow skill** under `plugins/development-harness/skills/workflows/`:

### Stage 1 — Discovery (`/development-harness:discovery`)

**Purpose:** Gather complete requirements before design.

**Location:** `plugins/development-harness/skills/workflows/discovery/SKILL.md`

**Process:**
1. Identify problem domain and clarifying questions (WHO, WHAT, WHEN, WHY — never HOW)
2. Gather references and examples
3. Document functional and non-functional requirements
4. Capture goals and anti-goals
5. Generate `ARTIFACT:DISCOVERY` document

**Output:** `.planning/harness/DISCOVERY.md`

**Human Touchpoint Gate:** Escalate if unbound constraints or domain knowledge gaps exist.

---

### Stage 2 — Planning + RT-ICA (`/development-harness:planning`)

**Purpose:** Transform discovery into actionable design with information completeness analysis.

**Location:** `plugins/development-harness/skills/workflows/planning/SKILL.md`

**Process:**
1. Run **RT-ICA assessment** (via `/development-harness:planner-rt-ica`) to verify prerequisites
2. Design solution architecture (approach, components, interactions, boundaries)
3. Generate acceptance tests in Given/When/Then format
4. Perform risk assessment
5. Generate `ARTIFACT:PLAN` with task skeletons and acceptance criteria

**Output:** `.planning/harness/PLAN.md`

**Gate Result:** APPROVED-FOR-PLANNING / APPROVED-WITH-GAPS / BLOCKED-FOR-PLANNING

---

### Stage 3 — Context Integration (`/development-harness:context-integration`)

**Purpose:** Ground abstract design in concrete codebase reality.

**Location:** `plugins/development-harness/skills/workflows/context-integration/SKILL.md`

**Process:**
1. Perform scope analysis per component: NEW / MODIFY / COMPLETE
2. Detect conflicts between plan and codebase patterns
3. Map existing resources the plan can reuse (utilities, patterns, test infrastructure)
4. Update plan with contextualization data (file paths, integration points, resource map)

**Output:** Contextualized `.planning/harness/PLAN.md` with Contextualization section appended

**Role Resolved:** Codebase analyzer (from language manifest)

---

### Stage 4 — Task Decomposition (`/development-harness:task-decomposition`)

**Purpose:** Break contextualized plan into independently executable task files.

**Location:** `plugins/development-harness/skills/workflows/task-decomposition/SKILL.md`

**Process:**
1. Identify atomic work units (each: atomic, independent, verifiable, bounded)
2. Embed complete context per task (CLEAR structure: Context, Objective, Inputs, Requirements, Constraints, Outputs, Acceptance Criteria, Verification, Handoff)
3. Apply CLEAR ordering standard
4. Add CoVe (Chain of Verification) checks only when accuracy risk is medium/high
5. Map dependencies and parallelization opportunities
6. Assign roles (not specific agents) to each task

**Output:** Individual `ARTIFACT:TASK-{NNN}` files at `.planning/harness/tasks/TASK-{NNN}.md` with YAML frontmatter

**YAML Frontmatter Fields:**
```yaml
task: TASK-001
title: <imperative title>
status: not-started | in-progress | complete | blocked
role: architect | implementer | test-designer | code-reviewer | docs-writer
dependencies: [TASK-002, TASK-003]
priority: 1-5
complexity: low | medium | high
accuracy-risk: low | medium | high
parallelize-with: [TASK-004, TASK-005]
parallel-rationale: <why parallelization is safe>
```

**Human Touchpoint Gate:** Escalate if novel architecture, high complexity (>40% of tasks), or circular dependencies detected.

---

### Stage 5 — Execution (`/development-harness:execution`)

**Purpose:** Implement each task using language-appropriate specialists.

**Location:** `plugins/development-harness/skills/workflows/execution/SKILL.md`

**Process:**
1. Read task file (YAML frontmatter + CLEAR-structured body)
2. Resolve role to agent using language manifest
3. Dispatch to resolved agent in fresh session (task file IS the complete prompt)
4. Agent implements task and runs embedded verification steps
5. Run quality gates (format, lint, typecheck, test)
6. Collect execution results

**Output:** `ARTIFACT:EXECUTION-{NNN}` at `.planning/harness/executions/EXECUTION-{NNN}.md`

**Role Resolution:** Abstract role (from task YAML) → language manifest → concrete agent

**Key Constraint:** One task per agent, fresh session per execution. Task file is read-only.

---

### Stage 6 — Forensic Review (`/development-harness:forensic-review`)

**Purpose:** Independent verification that execution matches acceptance criteria.

**Location:** `plugins/development-harness/skills/workflows/forensic-review/SKILL.md`

**Process:**
1. Read execution artifact and original task + plan
2. Validate each acceptance criterion independently (claim + evidence + reproduction)
3. Fact-check codebase state against claimed changes
4. Run quality gates independently
5. Check for side effects
6. Categorize findings: BLOCKING vs ADVISORY

**Output:** `ARTIFACT:REVIEW-{NNN}` at `.planning/harness/reviews/REVIEW-{NNN}.md`

**Verdicts:**
- `COMPLETE` — All criteria met with evidence
- `NEEDS_WORK` — Routes back to S5 with specific findings

**Loop Limit:** 3 NEEDS_WORK cycles per task before human escalation

**Core Principle:** Producer and reviewer are always different agents. AI cannot self-evaluate objectively.

---

### Stage 7 — Final Verification (`/development-harness:final-verification`)

**Purpose:** Certify feature achieves original objectives from S1.

**Location:** `plugins/development-harness/skills/workflows/final-verification/SKILL.md`

**Process:**
1. Extract original goals from `ARTIFACT:DISCOVERY`
2. For each goal, identify required truths in codebase
3. Verify each truth via direct observation (file reads, test runs, integration checks)
4. Verify acceptance tests from `ARTIFACT:PLAN`
5. Run full quality gate suite (whole-feature, not per-task)
6. Measure non-functional requirements

**Output:** `ARTIFACT:VERIFICATION` at `.planning/harness/VERIFICATION.md`

**Verdicts:**
- `CERTIFIED` — All goals verified with evidence
- `NOT_CERTIFIED` — Gaps identified; routes to S4 for corrective tasks

**Core Principle:** Goal-backward verification (start from what SHOULD be true, verify it IS true). Prevents anchoring bias from implementation details.

**Loop Limit:** 2 NOT_CERTIFIED cycles before human escalation

---

## Stage Naming Convention

Workflow skills use stage names as directory names:

```text
plugins/development-harness/skills/workflows/
├── discovery/                    # S1
├── planning/                     # S2
├── context-integration/          # S3
├── task-decomposition/           # S4
├── execution/                    # S5
├── forensic-review/              # S6
└── final-verification/           # S7
```

Each directory contains `SKILL.md` (stage orchestration) and optional subdirectories for references or helpers.

---

## Language Manifest System

### Manifest Location & Discovery

Language manifests are YAML files discovered via a **5-level priority system** (`manifest_discovery.py`):

```text
Priority 1: Enterprise (managed settings — not yet implemented)
Priority 2: Personal (~/.claude/manifests/)
Priority 3: Project (.claude/manifests/)
Priority 4: Plugin (plugins/{plugin-name}/manifests/)
Priority 5: Skill (plugins/{plugin-name}/skills/{skill-name}/assets/)
```

**Discovery order:** Manifest discovery scans all levels, filters by project markers, and selects the best match based on:
1. Dependency match score (how many `required_dependencies` match project dependencies)
2. Priority level (higher priority wins on tie)

### Manifest Schema

Each manifest is a YAML file at `{location}/{manifest-name}/language-manifest.yaml`.

**Required Sections:**

#### 1. Role Fulfillment

Maps harness abstract roles to language-specific agents/skills:

```yaml
role_fulfillment:
  architect: @python3-development:python-cli-architect
  test_designer: @python3-development:python-pytest-architect
  code_reviewer: @python3-development:python-code-reviewer
  design_spec: @python3-development:python-cli-design-spec
  linting: /python3-development:modernpython
```

**Rules:**
- Agents use `@plugin:agent-name` syntax
- Skills use `/plugin:skill-name` syntax
- Omitted roles fall back to general-purpose
- All five roles should be declared for full specialization

#### 2. Quality Gates

Commands run at quality checkpoints:

```yaml
quality_gates:
  format: "uv run ruff format {files}"
  lint: "uv run ruff check {files}"
  typecheck: "uv run mypy {files}"
  test: "uv run pytest tests/ --tb=short"
  standards: /python3-development:modernpython
```

**Rules:**
- Commands are backtick-wrapped
- `{files}` placeholder replaced via Python `str.format()` with space-separated file paths
- `test` gate does NOT take `{files}` (runs entire test suite)
- `standards` gate is optional (references a skill for language-specific standards)
- Non-typed languages use `typecheck: (none)` to skip

#### 3. Project Detection

How the harness identifies the language:

```yaml
project_detection:
  markers: [pyproject.toml, setup.py, setup.cfg]
  source_patterns: [src/**/*.py, "**/*.py"]
  test_patterns: [tests/**/*.py, test_*.py, "*_test.py"]
  required_dependencies: []  # optional: filters candidates by dependency presence
```

**Rules:**
- Markers are filenames (not paths) found in project root
- Source/test patterns use glob syntax
- At least one marker must be declared

#### 4. Stage Skills (Language-Specific Specialization)

Optional mapping of harness stages to language-specific skill overrides:

```yaml
stage_skills:
  discovery: [python3-discovery]
  design: [python3-design]
  planning_context_integration: [python3-implementation]
  implementation: [python3-implementation]
  testing_verification: [python3-testing]
```

**Naming convention:**
- Stage names map to workflow skills: `discovery` → `/development-harness:discovery`
- Hyphenated stage names (e.g., `context-integration`) become snake_case: `context_integration`
- Language-specific override skills prefixed with language name + stage name

#### 5. Optional: Process Flow Override

Replace the default SAM pipeline with a custom flow:

```yaml
process_flow_override: |
  flowchart TD
    Start([Feature Request]) --> CustomS1[Custom Stage 1]
    ...
    CustomSN --> Done([Feature Complete])
```

**Rules:**
- Must be valid mermaid flowchart
- Must produce artifacts compatible with naming conventions
- Must include at least one human touchpoint gate
- Must end with a verification stage (CERTIFIED/NOT_CERTIFIED verdict)
- Write `(none — uses default harness flow)` to explicitly use default

### Existing Language Manifests

#### Python

**Location:** `plugins/python3-development/manifests/python3/language-manifest.yaml`

**Stage Skills Mapped:**
- `discovery` → `python3-discovery` skill
- `design` → `python3-design` skill
- `planning-context-integration` → `python3-implementation` skill
- `planning-task-decomposition` → `python3-planning-task-decomposition` skill
- `implementation` → `python3-implementation` skill
- `testing-forensic-review` → `python3-testing-forensic-review` skill
- `testing-verification` → `python3-testing` skill

**Quality Gates:**
- format: `uv run ruff format {files}`
- lint: `uv run ruff check {files}`
- typecheck: `uv run mypy {files}`
- test: `uv run pytest tests/ --tb=short`
- standards: `/python3-development:modernpython`

#### Python Typer CLI (Stack Profile)

**Location:** `plugins/python3-development/manifests/python3-cli/language-manifest.yaml`

**Extends:** `python3-development:python3` (inheritance model)

**Key Difference:**
- `extends: python3-development:python3` indicates this is a specialized variant
- Overrides `design` → `python3-design-cli` skill
- Overrides `implementation` → `python3-implementation-cli` skill
- Stack field: `stack: typer-cli`

**Discovery:** Detected when both `pyproject.toml` AND `typer` dependency are present.

---

## Generic Stage Agent

**Location:** `plugins/development-harness/agents/generic-stage-agent.md`

### Purpose

The generic-stage-agent is the **execution dispatcher** for stages when language plugins do not provide a stage-specific skill. It accepts:

1. **Stage Workflow** — A mermaid flowchart defining the stage's steps, loops, exit conditions
2. **Cross-Cutting Stage Skill** — A harness workflow skill (e.g., `/development-harness:discovery`)
3. **Domain Skills** — Language-specific skills resolved from manifest
4. **Task/Artifact File** — Input from the previous stage
5. **Quality Gate Commands** — Shell commands from language manifest

### Dispatch Protocol

1. Load all skills (cross-cutting + domain)
2. Read task/artifact file
3. Follow stage workflow flowchart mechanically
4. Apply domain knowledge from loaded skills at each step
5. Run quality gate commands (mandatory)
6. Write output artifact to specified path

### Key Constraint

The generic-stage-agent **never skips steps in the workflow flowchart**. If a step is unclear, read the loaded skill documentation first.

---

## Manifest Utility Scripts

**Location:** `plugins/development-harness/scripts/`

### `manifest_discovery.py`

Discovers language manifests across 5 priority levels.

**Key Functions:**
- `discover_manifests()` — Find all matching manifests across priority levels
- `detect_project_dependencies()` — Extract package names from `pyproject.toml`
- `select_best_manifest()` — Choose highest-scoring manifest by dependency match + priority

**Priority Order:** ENTERPRISE (1) > PERSONAL (2) > PROJECT (3) > PLUGIN (4) > SKILL (5)

### `manifest_resolver.py`

Resolves abstract roles to concrete agents at runtime.

**Key Functions:**
- Role mapping: `architect` → agent from manifest, etc.
- Fallback: general-purpose agent if role not declared

### `manifest_merge.py`

Merges manifests when inheritance (`extends` field) is used.

**Use Case:** `python3-cli` manifest extends `python3` manifest; merge combines both declarations.

### `manifest_schema.py`

YAML schema validation and dataclass definitions.

**Validates:**
- Structure (required sections present)
- Role syntax (`@plugin:agent` or `/plugin:skill` format)
- Gate commands (backtick-wrapped, recognizable commands)
- Markers (at least one)
- Flow override (valid mermaid if present)

---

## State Management & Artifact Conventions

### Artifact Directory

All artifacts written to `.planning/harness/` using **stage prefixes**:

```text
.planning/harness/
├── DISCOVERY.md                    # S1 output
├── PLAN.md                         # S2 output (updated by S3)
├── tasks/
│   ├── TASK-001.md                # S4 output (one per task)
│   ├── TASK-002.md
│   └── ...
├── executions/
│   ├── EXECUTION-001.md           # S5 output
│   ├── EXECUTION-002.md
│   └── ...
├── reviews/
│   ├── REVIEW-001.md              # S6 output
│   ├── REVIEW-002.md
│   └── ...
└── VERIFICATION.md                 # S7 output
```

### Naming Pattern

`{stage-prefix}-{scope-or-id}.md`

**Stage Prefixes:**
- `discovery` → S1
- `plan` → S2
- `context` → S3 (amends S2 artifact)
- `task` → S4
- `execution` → S5
- `review` → S6
- `verification` → S7

### Cross-Reference Tokens

Each artifact includes `ARTIFACT:{TYPE}({ID})` tokens linking to predecessor/successor artifacts.

**Example:** Task file references `ARTIFACT:PLAN(auth-feature)` and execution artifact references `ARTIFACT:TASK(001)`.

---

## Role Resolution at Runtime

### Resolution Process

```text
1. Detect project language (scan markers: pyproject.toml, package.json, etc.)
2. Find language manifest (search plugins, project, personal directories)
3. Parse Role Fulfillment section
4. Map abstract roles to concrete agents/skills
5. Load quality gates from manifest
6. Begin S1 with resolved agents
```

### Multi-Language Disambiguation

When multiple language markers exist, count source files per language and select the language with the most source files as primary.

### Fallback Behavior

If no language manifest found:
- All roles default to general-purpose agent
- Quality gates inferred from file types (ruff if Python, eslint if JS/TS, etc.)

---

## Key Data Structures (Python)

**Classes in `manifest_schema.py`:**

- `ProjectDetection` — Markers, source/test patterns, required dependencies
- `QualityGates` — format, lint, typecheck, test, standards commands
- `RoleFulfillment` — Mapping of roles to agents/skills
- `LanguageManifest` — Complete manifest with all sections
- `ManifestValidationError` — Schema validation failures

**Classes in `manifest_discovery.py`:**

- `PriorityLevel` — IntEnum for discovery priority levels
- `DiscoveredManifest` — Manifest found at a specific priority level

---

## Dependencies Between Layers

```text
Stage S1 (Discovery)
  └─→ Loads: `/development-harness:discovery` skill
  └─→ Resolves: `architect` role from manifest
  └─→ Dispatches to: Resolved architect agent

Stage S2 (Planning)
  └─→ Loads: `/development-harness:planning` skill
  └─→ Loads: `/development-harness:planner-rt-ica` for prerequisite verification
  └─→ Reads: `ARTIFACT:DISCOVERY` from S1
  └─→ Outputs: `ARTIFACT:PLAN`

Stage S3 (Context Integration)
  └─→ Loads: `/development-harness:context-integration` skill
  └─→ Resolves: `architect` or `codebase-analyzer` role
  └─→ Reads: `ARTIFACT:PLAN` from S2
  └─→ Outputs: Contextualized `ARTIFACT:PLAN`

Stage S4 (Task Decomposition)
  └─→ Loads: `/development-harness:task-decomposition` skill
  └─→ Loads: `/development-harness:clear-cove-task-design` for task format
  └─→ Reads: Contextualized `ARTIFACT:PLAN` from S3
  └─→ Outputs: `ARTIFACT:TASK-{NNN}` files

Stage S5 (Execution)
  └─→ Reads: `ARTIFACT:TASK-{NNN}`
  └─→ Resolves: Role from task YAML → agent via manifest
  └─→ Loads: Domain skills from manifest
  └─→ Runs: Quality gates from manifest
  └─→ Outputs: `ARTIFACT:EXECUTION-{NNN}`

Stage S6 (Forensic Review)
  └─→ Reads: `ARTIFACT:EXECUTION-{NNN}` + `ARTIFACT:TASK-{NNN}` + `ARTIFACT:PLAN`
  └─→ Independent verification (different agent than S5)
  └─→ Runs: Quality gates independently
  └─→ Outputs: `ARTIFACT:REVIEW-{NNN}` with COMPLETE or NEEDS_WORK

Stage S7 (Final Verification)
  └─→ Reads: All `ARTIFACT:REVIEW-{NNN}` + `ARTIFACT:DISCOVERY` + `ARTIFACT:PLAN`
  └─→ Goal-backward verification
  └─→ Runs: Full quality gate suite
  └─→ Outputs: `ARTIFACT:VERIFICATION` with CERTIFIED or NOT_CERTIFIED
```

---

## Where to Add New Code

### New Language Plugin

1. Create `plugins/{language-name}-development/` directory
2. Add language manifest at `plugins/{language-name}-development/manifests/{stack-variant}/language-manifest.yaml`
3. Declare Role Fulfillment section with specialist agents
4. Declare Quality Gates section with format/lint/typecheck/test commands
5. Declare Project Detection section with language markers
6. Optionally declare stage-specific skills overrides in `stage_skills` section
7. Optionally declare Process Flow Override for custom pipeline

### New Stage Workflow Skill

1. Create `plugins/development-harness/skills/workflows/{stage-name}/SKILL.md`
2. Define role and when-to-use section
3. Include mermaid process flowchart showing steps and loops
4. Define step-by-step process sections
5. Define input/output format and file locations
6. Include human touchpoint gate conditions
7. Include success criteria

### Stage-Specific Language Skill

Language plugins can add specializations for specific stages:

1. Create `plugins/{language}/skills/{language}-{stage-name}/SKILL.md`
2. Declare in manifest under `stage_skills` section
3. Reference in stage orchestration when the stage loads skills

### New Quality Gate Command

Add to language manifest `quality_gates` section. Commands execute at S5/S6/S7 quality checkpoints.

---

## Known Gaps & Observations

### Currently Implemented

✓ SAM 7-stage pipeline framework
✓ 7 workflow skills (discovery through final-verification)
✓ Generic stage agent dispatcher
✓ Language manifest schema and discovery system
✓ Python and Python CLI language manifests
✓ Manifest utilities (discovery, merge, schema validation)
✓ Role resolution protocol
✓ ARL touchpoint gates (between S1–S2, S4–S5)

### Not Yet Implemented / Observed

- Enterprise-level manifests (Priority 1 in discovery system — reserved for future)
- Process flow overrides — schema defined, no examples in codebase yet
- Multi-language stack profiles (e.g., Python backend + TypeScript frontend)
- Stage-specific skill overrides — manifests support `stage_skills` mapping but unclear if fully wired
- Integration with GitHub issues or backlog systems for touchpoint escalation
- Context file management for cross-stage state (task claims, active task tracking)

### Potential Issues

- **No dispatch helper for non-Python languages** — `dispatch_helper.py` appears Python-specific; unclear if generic-stage-agent works equally well for other languages
- **Manifest extends mechanism** — `python3-cli` uses `extends: python3-development:python3` but merge logic in `manifest_merge.py` may not fully implement inheritance chain resolution
- **Quality gate command templating** — `{files}` placeholder uses `str.format()`, but no validation that commands handle empty/missing `{files}` gracefully

---

## References

- Default Development Flow: `plugins/development-harness/skills/development-harness/references/default-development-flow.md`
- Role Resolution Protocol: `plugins/development-harness/skills/development-harness/references/role-resolution-protocol.md`
- Language Manifest Schema: `plugins/development-harness/skills/development-harness/references/language-manifest-schema.md`
- Language Manifest Template: `plugins/development-harness/templates/language-manifest-template.md`
- Main Harness Skill: `plugins/development-harness/skills/development-harness/SKILL.md`
- SAM Methodology: https://github.com/bitflight-devops/stateless-agent-methodology
- ARL Framework: `plugins/plugin-creator/skills/arl/`

---

*Architecture analysis: 2026-03-18*
