# Backlog Item End-to-End Lifecycle

**Purpose**: Authoritative process graph for the full journey of a backlog item — from idea capture through implementation, verification, and closure. This document connects the backlog management layer (item creation, grooming, research) to the SAM execution layer (planning, implementation, quality gates).

**Sources**:

- `plugins/development-harness/skills/create-backlog-item/SKILL.md`
- `plugins/development-harness/skills/groom-backlog-item/SKILL.md`
- `plugins/development-harness/skills/add-new-feature/SKILL.md`
- `plugins/development-harness/skills/work-backlog-item/SKILL.md`
- `plugins/development-harness/skills/implement-feature/SKILL.md`
- `plugins/development-harness/skills/start-task/SKILL.md`
- `plugins/development-harness/skills/complete-implementation/SKILL.md`
- `plugins/development-harness/docs/adr-9-close-resolve-semantics.md`

**Last verified**: 2026-03-25

---

## Overview

```mermaid
flowchart LR
    P1([Phase 1<br>Capture]) --> P2([Phase 2<br>Grooming])
    P2 --> P3([Phase 3<br>Research &<br>Architecture])
    P3 --> P4([Phase 4<br>Planning])
    P4 --> P5([Phase 5<br>Execution])
    P5 --> P6([Phase 6<br>Quality Gates])
    P6 --> P7([Phase 7<br>Closure])
    P2 -->|BLOCKED| P2
    P3 -->|BLOCKED| P3
    P5 -->|regression| P5
    P6 -->|BLOCKED| P6
    P7 -->|close| P7close([Dismissed])
    P7 -->|resolve| P7done([Done])
```

Phases 3 and 4 both execute inside the `/dh:add-new-feature` skill (invoked by `/dh:work-backlog-item`). The skill runs 6 sequential phases: discovery, codebase analysis, architecture, task decomposition, plan validation, and context manifest.

Each phase produces artifacts stored via the three-primitive model defined in [Backend Providers](./backend-providers.md): Work Items (IssueBackend) for coordination state, Sub-items (TaskBackend) for SAM task orchestration, and Documents (DocumentBackend) for durable handoff content between phases.

---

## Phase 1: Item Capture

**Entry precondition**: User identifies a feature, bug, or chore worth tracking.

**Skill**: `/dh:create-backlog-item`

**Actor**: Orchestrator (guided/quick mode) or orchestrator in auto mode.

```mermaid
flowchart TD
    Start([User invokes /dh:create-backlog-item]) --> Mode{Mode?}
    Mode -->|Guided| Q["Collect 6 fields via questions:<br>1. Title<br>2. Priority (P0/P1/P2/Idea)<br>3. Description + verbatim_user_report<br>4. Source<br>5. Type<br>6. How to reproduce (optional)"]
    Mode -->|Quick| QK["Collect Priority + Description only<br>verbatim_user_report = full argument string<br>Source = Session observation<br>Type = Feature"]
    Mode -->|--auto| Auto["Infer from description:<br>Priority from urgency keywords<br>(critical/required/must→P1, default P1)<br>Source = Agent task<br>Type = Feature"]

    Q --> Validate["Step 2: Validate inputs<br>Required: title, priority, description<br>Strip implementation instructions from description"]
    QK --> Validate
    Auto --> Validate

    Validate --> Dup{"Step 3: Duplicate detection<br>Scan backlog/ for case-insensitive<br>title overlap ≤ 2 token edit distance"}
    Dup -->|"Duplicate found (guided/quick)"| Confirm{"User confirms<br>proceed?"}
    Dup -->|"Duplicate found (--auto)"| Stop1(["STOP — duplicate detected<br>No file written"])
    Dup -->|No duplicate| Compose
    Confirm -->|No| Stop2(["STOP — user declined"])
    Confirm -->|Yes| Compose

    Compose["Step 4: Compose item block<br>Fields: Title, Source, Added (date),<br>Priority, Type, Description,<br>Verbatim user report (REQUIRED),<br>How to reproduce (if provided)"]
    Compose --> Create["Step 5: backlog_add MCP tool<br>Creates per-item file at<br>~/.dh/projects/{slug}/backlog/"]

    Create --> Issue{"GitHub Issue?"}
    Issue -->|"P0/P1 + user confirmed<br>or --auto + --create-issue"| GH["GitHub Issue created<br>issue field set in frontmatter"]
    Issue -->|"P2/Idea or user declined<br>or --auto without --create-issue"| NoGH["No GitHub Issue"]

    GH --> Done["Step 6: Confirm write<br>Show title, priority, date<br>Next steps:<br>  /dh:groom-backlog-item {title}<br>  /dh:work-backlog-item {title}"]
    NoGH --> Done
```

**Strip implementation instructions from description** (Step 2): **Why:** Implementation instructions in the description contaminate the problem statement. Grooming and architecture phases need to understand WHAT is broken, not HOW to fix it. The `verbatim_user_report` preserves the original words — including any solution suggestions — for reference.

**Key fields**:

- `verbatim_user_report` — REQUIRED, never omitted. The exact user words from Question 3 (guided) or the full argument string (quick/auto). Never edited, summarized, or reformatted. **Why:** The verbatim report is the only field that captures the user's mental model unfiltered. When grooming reveals a misunderstanding between what the user asked for and what the agent interpreted, it is the arbiter of original intent.
- `how_to_reproduce` — optional. Omitted entirely from the MCP call if user skipped or no reproduction steps found.

**Canonical status after this phase**: `needs-grooming`

**Failure paths**:

- Missing required field (title, priority, description) — STOP, report field name.
- Duplicate detected in auto mode — STOP, no file written.
- `GITHUB_TOKEN` not set for P0/P1 issue creation — per-item file still written; issue creation skipped with error report.

**Transition to next phase**: Text suggestion only ("Next steps: Groom: /dh:groom-backlog-item {title}"). No automatic invocation. The transition from capture to grooming is entirely implied — a human or orchestrator must decide to invoke the next step. (Confirmed: audit Finding 9 Gap A.)

---

## Phase 2: Grooming

**Entry precondition**: Item has status `needs-grooming` and is selected for detail work.

**Skill**: `/dh:groom-backlog-item`

**Actor**: Orchestrator dispatches a parallel grooming swarm (team mode) or sequential agents (fallback mode).

```mermaid
flowchart TD
    Start([Item selected for grooming]) --> S1["Step 1: backlog_list MCP<br>Filter items by scope argument"]
    S1 --> S2{"Step 2: Validity Check<br>4 sequential checks per item"}

    S2 --> C1{"C1: Is the job still valid?<br>Does this item still belong<br>in the backlog given current context?"}
    C1 -->|"No — scope/priority/context changed"| Skip(["Report invalid — skip this item"])
    C1 -->|Yes| C2{"C2: Evidence work already done?<br>git log + backlog_list_merged_prs + file read"}
    C2 -->|"Already done"| Skip
    C2 -->|Not done| C3{"C3: Has GitHub issue?<br>Check metadata.issue or index link"}
    C3 --> C4{"C4: Already groomed today?<br>groomed == today's date<br>AND all required sections present?"}
    C4 -->|Yes| Drift["Step 2.5: Drift Check<br>Mode A: Plan Drift<br>Mode B: Grooming Drift<br>Then STOP — do not proceed to Step 3"]
    C4 -->|No| S3["Step 3: Extract item details<br>title, description, research questions,<br>source, suggested_location"]

    S3 --> S35["Step 3.5: RT-ICA Initial Snapshot<br>(Actor: orchestrator or rtica-assessor)<br>Categorize info as:<br>AVAILABLE / DERIVABLE / MISSING<br>Write via backlog_groom section='RT-ICA'"]

    S35 --> S36["Step 3.6: Scope Sizing<br>Choose: MINIMAL / NARROW /<br>STANDARD / FULL<br>Sizes the swarm agents"]

    S36 --> Swarm

    subgraph Swarm [Steps 4-8: Parallel Grooming Swarm]
        direction TB
        W1["Wave 1 (parallel):<br>• fact-checker teammate<br>• impact-radius teammate"]
        W2["Wave 2 (blocked by Wave 1):<br>• rtica-assessor teammate<br>• issue-classifier teammate"]
        W3["Wave 3 (blocked by Wave 2):<br>• groomer teammate"]
        W1 --> W2
        W2 --> W3
    end

    Swarm --> S85["Step 8.5: RT-ICA Final Pass<br>(Actor: orchestrator or rtica-assessor)<br>Re-assess ALL conditions with full swarm output<br>Self-resolution pass: attempt tool-based resolution<br>for each MISSING/DERIVABLE condition<br>Replaces Step 3.5 snapshot"]

    S85 --> Decision{RT-ICA result?}
    Decision -->|"APPROVED — all AVAILABLE<br>or DERIVABLE resolved"| S9["Step 9: Write groomed content<br>via backlog_groom MCP calls<br>(one call per section, incremental)"]
    Decision -->|"BLOCKED — MISSING conditions<br>remain after self-resolution"| Block(["STOP — batch all MISSING<br>conditions and present to user<br>Wait for user answers<br>Re-check after responses"])

    S9 --> Done["Set groomed frontmatter field<br>(YYYY-MM-DD date)<br>Sync to GitHub issue body<br>if issue exists"]
```

**Swarm agents and their outputs**:

- **fact-checker** (Wave 1) — Verifies item claims against primary sources. Produces `Fact-Check Summary` with VERIFIED/REFUTED/INCONCLUSIVE counts and citations. REFUTED claims become MISSING conditions in RT-ICA. INCONCLUSIVE become DERIVABLE. Writes via `backlog_groom(section="Fact-Check")`.
- **impact-radius** (Wave 1) — Assesses blast radius. Writes via `backlog_groom(section="Impact Radius")`.
- **rtica-assessor** (Wave 2) — Runs RT-ICA analysis with swarm context. Blocked by fact-checker and impact-radius completion.
- **issue-classifier** (Wave 2) — Classifies the issue type. Writes via `backlog_groom(section="Issue Classification")`.
- **groomer** (Wave 3) — Reads all prior sections. Produces: Reproducibility, Priority, Impact, Benefits, Expected Behavior, Acceptance Criteria, Files, Resources, Dependencies, Effort. Each subsection written individually via `backlog_groom(section="{subsection name}")`.

**RT-ICA runs twice**: Step 3.5 (initial snapshot, item-level info only) and Step 8.5 (final pass, full swarm output). The Step 8.5 result replaces the Step 3.5 snapshot in the item file (same `section="RT-ICA"` call overwrites). **Why:** The initial snapshot calibrates swarm intensity — scope sizing (Step 3.6) uses the AVAILABLE/DERIVABLE/MISSING distribution to choose swarm intensity. The final pass incorporates swarm discoveries (fact-check results convert DERIVABLE to AVAILABLE, refuted claims convert AVAILABLE to MISSING).

**Metadata written**: `groomed` frontmatter field set to `YYYY-MM-DD` (not nested under `metadata.`). No explicit GitHub label transition is documented in the skill source — the only documented state change is the `groomed` frontmatter field.

**Failure paths**:

- Validity check fails (C1-C4) — item skipped with report.
- RT-ICA BLOCKED — STOP, present MISSING conditions to user, wait for answers.
- No validation step exists between groomer output and Step 9 write (audit Finding 6 — groomer output written directly, no quality gate on groomer sections).

**Transition to next phase**: No explicit invocation of the next skill. The groomed item is available for `/dh:work-backlog-item` to pick up. Transition from grooming to milestone grouping is not mentioned (audit Finding 9 Gap B).

**Missing reference files**: The SKILL.md references `./references/issue-classification.md` and `./references/groomer-agent.md` — neither file exists on disk.

**Recommended completeness check before Phase 3**: The RT-ICA presence check in `work-backlog-item` Step 4 does not verify full grooming completeness. The recommended approach before entering Phase 3 is to verify presence of the RT-ICA section AND the Acceptance Criteria section AND the Description section. An item missing acceptance criteria would enter planning with incomplete information, producing a plan that cannot be validated against its own acceptance criteria.

---

## Phase 3: Research and Architecture

**Entry precondition**: Item is groomed. `/dh:work-backlog-item` has been invoked, which performs an RT-ICA checkpoint (Step 4) and composes a feature request (Step 5) before invoking `/dh:add-new-feature` via `Skill()` call (Step 6).

**Skill**: `/dh:add-new-feature` (Phases 1-3 of 6 internal phases)

**Actor**: Orchestrator invokes `/dh:add-new-feature`; each internal phase delegates to a specialist agent sequentially.

Phases 3 and 4 of the lifecycle both execute inside `/dh:add-new-feature`. The skill runs 6 sequential phases internally: Pre-Phase (artifact discovery), Phase 1 (feature research), Phase 2 (codebase analysis), Phase 3 (architecture), Phase 4 (task decomposition), Phase 5 (plan validation), Phase 6 (context manifest).

```mermaid
flowchart TD
    Start(["work-backlog-item Step 4:<br>RT-ICA Checkpoint"]) --> RTICA{"RT-ICA summary<br>present in groomed content?"}
    RTICA -->|Present| UseIt["Use existing RT-ICA"]
    RTICA -->|Absent| RunIt["Perform RT-ICA inline<br>(4-step: goal, prerequisites,<br>availability, decision)"]
    UseIt --> Gate{RT-ICA decision?}
    RunIt --> Gate
    Gate -->|BLOCKED| Block(["STOP — present unresolved<br>conditions to user<br>Do not invoke add-new-feature"])
    Gate -->|APPROVED| Compose["work-backlog-item Step 5:<br>Compose feature request<br>Carry DERIVABLE items as<br>'Assumptions to confirm'"]
    Compose --> Invoke["work-backlog-item Step 6:<br>Skill(skill='add-new-feature',<br>args='{composed feature request}')<br>Direct skill call — not a suggestion"]

    Invoke --> PrePhase{"Pre-Phase:<br>Artifact Discovery<br>artifact_list(issue_number=N)<br>Existing artifacts?"}
    PrePhase -->|Yes| Append["Append prior_artifacts block<br>to each phase delegation prompt"]
    PrePhase -->|No| Ph1
    Append --> Ph1

    Ph1["Phase 1: Feature Research<br>Agent: @dh:feature-researcher<br>Output: plan/feature-context-{slug}.md<br>Constraint: WHAT/WHY only — no HOW<br>Artifact registered: feature-context"]

    Ph1 --> Ph2{"Phase 2: Codebase Analysis<br>Agent: @dh:codebase-analyzer<br>Optional — orchestrator judgment<br>Focus: patterns, architecture,<br>testing, conventions"}
    Ph2 -->|Invoked| Ph2Out["Output: plan/codebase/{FOCUS}.md<br>per focus area<br>Constraint: WHAT exists today only<br>Artifact registered: codebase-analysis"]
    Ph2 -->|Skipped| Ph3
    Ph2Out --> Ph3

    Ph3["Phase 3: Architecture Design<br>Agent: resolved from language manifest<br>(pyproject.toml → @python3-development:python-cli-design-spec)<br>Input: feature-context + optional codebase analysis<br>Output: plan/architect-{slug}.md<br>Constraint: HOW only — interfaces, contracts, models<br>Artifact registered: architect"]
```

**Agent selection for architecture**: The skill does NOT hardcode `@python3-development:python-cli-design-spec`. It resolves the `design-spec` role from the language manifest at runtime based on project detection markers (`pyproject.toml` → Python, `package.json` → TypeScript, `Cargo.toml` → Rust, none → general-purpose fallback).

**Artifact registration**: Each phase calls `artifact_register` after writing its file, with `issue_number`, `artifact_type`, `path` (state-relative), and `agent` fields.

**Storage**: Feature context and architecture specs are registered as Documents via the artifact manifest system. See [Backend Providers — SAM Storage Model](./backend-providers.md#sam-storage-model) for the document lifecycle.

**All paths are state-relative**: Resolved via `dh_paths.plan_dir()` → `~/.dh/projects/{project-slug}/plan/`. NOT repo-relative.

**No feasibility gate exists** between RT-ICA APPROVED and SAM planning invocation. The transition from "do we have enough information?" to "start planning" is direct — no assessment of technical feasibility, effort/value, risk, or alternative approaches (audit Finding 1).

---

## Phase 4: Planning

**Entry precondition**: Architecture document (`plan/architect-{slug}.md`) exists. Still inside `/dh:add-new-feature` (Phases 4-6 of 6 internal phases).

**Skill**: `/dh:add-new-feature` (Phases 4-6)

**Actor**: Orchestrator delegates to specialist agents sequentially.

```mermaid
flowchart TD
    Ph4["Phase 4: Task Decomposition<br>Agent: @dh:swarm-task-planner<br>Input: architect-{slug}.md + feature-context<br>Output: plan/P{NNN}-{slug}.yaml via sam_create<br>Every task has: status, dependencies,<br>priority, complexity, agent, AC (3+),<br>verification steps (3+)"]

    Ph4 --> Bookend{"acceptance-criteria-structured<br>non-empty?"}
    Bookend -->|Yes| T0TN["swarm-task-planner generates<br>T0 (baseline) + TN (verification)<br>bookend tasks inside the plan<br>T0: priority 1, deps []<br>TN: deps = all non-bookend task IDs"]
    Bookend -->|No| NoBookend["No bookend tasks generated"]
    T0TN --> Register
    NoBookend --> Register

    Register["Artifact registered: task-plan<br>(auto-registered by sam_create when issue set)"]
    Register --> Ph5

    Ph5["Phase 5: Plan Validation<br>Agent: @dh:plan-validator<br>Checks: AC coverage, dependency DAG,<br>agent assignments, verification steps,<br>impact radius coverage"]
    Ph5 --> ValResult{Validator returns?}
    ValResult -->|READY| Ph6
    ValResult -->|"BLOCKED — specific gaps listed"| Fix(["Fix identified gaps<br>Re-run Phase 4<br>before retrying Phase 5"])

    Ph6["Phase 6: Context Manifest<br>Agent: @dh:context-gathering<br>Writes context manifest INTO the plan<br>via sam_update (not a separate file)<br>Maps each task to files, artifacts,<br>external context it needs"]

    Ph6 --> Link["work-backlog-item Step 7:<br>backlog_update(selector='{title}',<br>plan='plan/P{NNN}-{slug}.yaml')<br>Links plan to backlog item"]
    Link --> Done(["add-new-feature complete<br>Report slug + task file path<br>Next: /dh:implement-feature"])
```

**Storage**: The SAM plan is created via `sam_create`, which maps to TaskBackend operations (Work Item for the plan, Sub-items for tasks). See [Backend Providers — TaskBackend Protocol](./backend-providers.md#taskbackend-protocol-912--to-be-created).

**plan-validator returns READY or BLOCKED** (not PASS/BLOCKED as previously documented). BLOCKED includes specific gaps that must be fixed before retrying.

**T0 baseline is a bookend task during EXECUTION, not during planning**. The `swarm-task-planner` generates T0 and TN as tasks inside `P{NNN}-{slug}.yaml` with appropriate priority and dependency settings. They dispatch automatically during execution via normal SAM readiness ordering — T0 fires first (priority 1, no deps), TN fires last (depends on all implementation tasks). No special handling is needed in the dispatch loop.

**context-gathering writes into the plan YAML** via `sam_update`, not to a separate file. The plan file path remains `~/.dh/projects/{project-slug}/plan/P{NNN}-{slug}.yaml`.

**Status advance**: `backlog_update(selector="{title}", plan="plan/P{NNN}-{slug}.yaml")` links the SAM plan file to the GitHub issue. The `status` field transition to `in-progress` happens via `work-backlog-item` Step 7.

**Failure paths**:

- plan-validator returns BLOCKED — re-run Phase 4 (task decomposition) to fix gaps before retrying Phase 5.
- No specific fix protocol is defined for BLOCKED plans beyond "fix the identified gaps." The recommended approach is to re-invoke `swarm-task-planner` with the validator's BLOCKED output (listing specific gaps) as additional context, so the planner can address each gap directly rather than regenerating from scratch.

---

## Phase 5: Execution

**Entry precondition**: SAM plan exists and is linked to the backlog item. `/dh:add-new-feature` has completed.

**Skill**: `/dh:implement-feature`

**Actor**: Orchestrator runs the dispatch loop; specialist agents execute individual tasks via `/dh:start-task`.

```mermaid
flowchart TD
    Start(["Orchestrator invokes<br>/dh:implement-feature"]) --> Status["sam_status(plan='P{N}')<br>Query plan status"]

    Status --> Ready{"Fetch ready tasks<br>(ONCE per batch)<br>backlog_get_ready_sam_tasks<br>or sam_ready"}
    Ready -->|"No ready tasks —<br>all tasks terminal"| Complete
    Ready -->|"1 task ready"| Single["Dispatch via single Agent call<br>Skill(skill='start-task',<br>args='{task_file_path} --task {T}')"]
    Ready -->|"2+ tasks ready"| Team["TeamCreate(team_name='impl-{slug}')<br>Spawn one teammate per ready task<br>Each calls start-task"]

    Single --> Hook
    Team --> Hook

    Hook["SubagentStop hook fires:<br>task_status_hook.py marks<br>task COMPLETE in plan YAML<br>Syncs to GitHub sub-issue<br>if github_issue field set"]

    Hook --> Concerns{"Agent returned<br>&lt;concerns&gt; block?"}
    Concerns -->|Yes| Log["Append concerns to backlog<br>via backlog_groom"]
    Concerns -->|No| BatchDone
    Log --> BatchDone

    BatchDone{"All tasks in batch<br>complete?"}
    BatchDone -->|No| Wait["Wait for remaining agents"]
    BatchDone -->|Yes| Status
    Wait --> BatchDone

    Complete(["Completion Gate:<br>All tasks show COMPLETE"])
    Complete --> Invoke["Invoke directly:<br>Skill(skill='complete-implementation',<br>args='{task_file_path}')<br>Explicit invocation — not a suggestion"]
```

**start-task internal procedure** (Actor: specialist agent):

1. `sam_read(plan="P{N}", task="T{M}")` — returns `TaskAssignment` JSON
2. Optionally discovers plan artifacts via `artifact_list` + `artifact_read`
3. Selects task (from `--task` argument or first `not-started` with resolved deps)
4. Loads task-level skills via `Skill(skill="{skill-name}")` for each name in `task.skills`
5. `sam_claim(plan="P{N}", task="T{M}")` — if `claimed: false`, STOP (do not implement). **Storage**: Task claiming uses atomic `sam_claim` which maps to TaskBackend's `claim_task` — an atomic conditional write preventing concurrent claims. See [Backend Providers — TaskBackend Protocol](./backend-providers.md#taskbackend-protocol-912--to-be-created).
6. Writes active-task context file to `~/.dh/projects/{project-slug}/context/active-task-{CLAUDE_SESSION_ID}.json` (required for hook-driven updates)
7. Implements against acceptance criteria and verification steps
8. Commits (prohibition on `Fixes #N` trailers — only `/dh:complete-implementation` Final Step may include these)

**Hook mechanisms**:

- `SubagentStop` hook (on `/dh:implement-feature`) — marks task COMPLETE after sub-agent finishes, syncs to GitHub sub-issue
- `PostToolUse` hook (on `/dh:start-task`, matcher: Write|Edit|Bash) — records `last-activity` timestamp on every tool call during task execution. Uses the active-task context file to know which task to update.

**Bookend task dispatch**:

- T0 dispatches first (priority 1, no dependencies) — runs `t0-baseline-capture` agent, writes `T0-baseline-{slug}.yaml`
- TN dispatches last (depends on all non-bookend tasks) — runs `tn-verification-gate` agent, writes `TN-verification-{slug}.yaml`
- Both write to `~/.dh/projects/{project-slug}/plan/`
- When parent story issue number is known, `artifact_register` instructions are added to bookend task delegation prompts

**complete-implementation is explicitly invoked** when all tasks show COMPLETE. The skill uses `Skill(skill="complete-implementation", args="{task_file_path}")` — a direct invocation, not a text suggestion.

**BLOCKED task handling**: NOT FOUND in source. Neither `implement-feature` nor `start-task` documents an explicit procedure for BLOCKED tasks. The completion gate triggers only when all tasks are COMPLETE. No documented escalation path or loop-exit condition for BLOCKED tasks exists in these skill files.

**Recommended BLOCKED task escalation**: When `sam_status` shows tasks in BLOCKED state after multiple dispatch cycles with no progress, the recommended approach is for the orchestrator to escalate to the user with: the blocked task list, each task's blocking reason (from the task body or status output), and a request for direction. The dispatch loop should not spin indefinitely on BLOCKED tasks — if a full dispatch cycle produces no state changes (no tasks transition from BLOCKED to another state), the orchestrator should break the loop and report. This guidance is not currently codified in the skill files; it is a documented recommendation for orchestrator behavior.

**Failure paths**:

- `sam_claim` returns `claimed: false` — agent stops, does not implement (another agent is running this task)
- TN verification with `status: regressed` on any criterion — detected in Phase 6 pre-phase, not in the execution loop itself

---

## Phase 6: Quality Gates

**Entry precondition**: All SAM execution tasks reach terminal status (COMPLETE).

**Skill**: `/dh:complete-implementation`

**Actor**: Orchestrator invokes the skill; it delegates to 6 specialist agents sequentially via start-task.

### Pre-Phases (before QG dispatch)

```mermaid
flowchart TD
    Start(["/dh:complete-implementation invoked"]) --> TN{"Pre-Phase 1 — TN Verification Check<br>Read TN-verification-{slug}.yaml<br>Aggregate — FAIL if any record<br>has status = regressed"}
    TN -->|"Any regressed"| TNBlock(["STOP — list each criterion<br>with check_command, T0/TN stdout<br>Block completion"])
    TN -->|"All passed or file absent"| Artifact

    Artifact{"Pre-Phase: Artifact Discovery<br>(when parent issue number known)<br>artifact_list(issue_number=N)<br>Pass manifest to QG agents"}

    Artifact --> Concerns{"Pre-Phase 1b: Process Concerns<br>backlog_view — look for<br>## Concerns with unchecked items"}
    Concerns -->|"Unchecked concerns exist"| Verify["For each concern:<br>Verify by reading file/running check<br>If verified: check off + create backlog item<br>If not verified: check off as 'Not confirmed'<br>Update via backlog_groom section='Concerns'"]
    Concerns -->|"No concerns section"| QGCreate
    Verify --> QGCreate
```

### Quality Gate Plan Creation and Dispatch

```mermaid
flowchart TD
    QGCreate{"Check for existing QG plan<br>sam_list(search='qg-{slug}')"}
    QGCreate -->|"No existing plan"| Build["build_quality_gate_plan(<br>slug, issue, impl_plan_address)<br>from sam_schema.core.quality_gates<br><br>sam_create(slug='qg-{slug}',<br>goal='Quality gate enforcement',<br>tasks_yaml, issue)"]
    QGCreate -->|"Existing plan —<br>some tasks remain"| Reset["Reset BLOCKED tasks to not-started<br>via sam_state per task<br>Re-enter dispatch loop"]
    QGCreate -->|"Existing plan —<br>all tasks terminal"| Gate

    Build --> Loop
    Reset --> Loop

    subgraph Loop [SAM Dispatch Loop]
        Claim["sam_claim + start-task<br>per ready task"] --> T1
        T1["T1: code-reviewer<br>Deps: none"]
        T1 -->|complete| T2["T2: feature-verifier<br>Deps: T1"]
        T2 -->|complete| T3["T3: integration-checker<br>Deps: T2"]
        T3 -->|complete| T4["T4: doc-drift-auditor<br>Deps: T3"]
        T4 --> T4Post{"T4 output:<br>drift found?"}
        T4Post -->|"Drift found"| T5["T5: service-docs-maintainer<br>Deps: T4"]
        T4Post -->|"No drift"| SkipT5["sam_state(plan, task='T5',<br>status='skipped')"]
        T5 --> T6["T6: context-refinement<br>Deps: T5"]
        SkipT5 --> T6
    end

    Loop --> Gate{"Completion Verification Gate<br>sam_status(plan='{QG}')<br>All 6 tasks terminal?"}
    Gate -->|"All complete/skipped<br>(only T5 may be skipped)"| Followup
    Gate -->|"Any non-terminal<br>or unauthorized skip"| Block(["COMPLETION BLOCKED<br>Report failed tasks<br>To resume: re-run<br>/complete-implementation"])

    Followup{"Recursive Follow-up<br>Routing"}
    Followup --> Detect["Detect follow-up files from<br>T1 ARTIFACTS output or glob:<br>P*-{slug}-followup-*.yaml"]
    Detect --> Route["For each follow-up:<br>1. Derive search slug from filename<br>2. Search backlog via backlog_list<br>3. If match: backlog_update with plan<br>4. If no match: create-backlog-item --auto"]

    Route --> Recurse{"Recursion gate:<br>BOTH conditions required"}
    Recurse -->|"ADR-3: slug matches parent<br>AND ADR-2: Priority = High"| Immediate["Recurse immediately:<br>Skill('implement-feature', followup)<br>Then re-run complete-implementation"]
    Recurse -->|"Either not met"| Defer(["Defer follow-up<br>Output: 'to resume:<br>/dh:work-backlog-item &lt;title&gt;'"])

    Immediate --> Label
    Defer --> Label

    Label["Apply status:verified label<br>backlog_update(selector, verified=True)"]
    Label --> Final["Final commit and push<br>Final Handoff Output:<br>'Clear context and run:<br>/dh:work-backlog-item &lt;next-item&gt;'"]
```

**Input modes**: The skill accepts either a plan file path (SAM path → 6-task QG) or an issue number (proportional path → 3-task QG when issue has no linked plan).

**Proportional Quality Gate path** (issue-only, no linked plan):

- 3 tasks: T1 code-reviewer, T2 test verification, T3 acceptance check
- Plan created via `build_proportional_quality_gate_plan(slug=f"issue-{N}", ...)` with `pqg-` prefix
- All 3 tasks required — no skip whitelist
- No recursive follow-up handling (explicitly skipped)
- `status:verified` applied directly via `backlog_update(selector="#{N}", verified=True)`

**T5 skip condition**: After T4 completes, orchestrator inspects T4 output for `## Findings` section. If "No documentation drift detected" or empty findings → skip T5 via `sam_state(status='skipped')`. Otherwise T5 proceeds. **Why:** Documentation update has no value when no drift exists. Other QG tasks (code review, feature verification, integration check) always have verification value even if the implementation is perfect — but running `service-docs-maintainer` on a codebase with no drift would produce no changes.

**Recursive follow-up routing** requires BOTH conditions: (1) the follow-up slug matches the parent feature slug (ADR-3), and (2) the follow-up priority is High (ADR-2). **Why:** Slug matching prevents unrelated bugs found during review from hijacking the current feature's quality gates. Priority gating prevents low-priority same-feature follow-ups from delaying completion.

**complete-implementation does NOT invoke work-backlog-item close/resolve**. After quality gates pass, it: (1) applies `status:verified` label, (2) commits and pushes, (3) outputs a handoff message telling the user to run `/dh:work-backlog-item <next-item>`. The explicit instruction to resolve the current item is absent from the output (audit Finding 9 Gap D — partially resolved).

**Recommended resolve handoff**: After applying `status:verified`, the best path is for the orchestrator to output: "Resolve the current item: `/dh:work-backlog-item resolve {current-item-title}`" before any "work next item" instruction. This ensures the verified item transitions to closure rather than lingering in a verified-but-not-resolved state.

**Failure paths**:

- TN regression detected — STOP, block completion with per-criterion details
- Any QG task non-terminal or unauthorized skip (skip on task other than T5) — COMPLETION BLOCKED, report failed tasks, user re-runs the skill
- BLOCKED tasks on resume are reset to `not-started` via `sam_state`, then loop re-enters

---

## Phase 7: Closure

**Entry precondition**: `status:verified` label applied (for SAM items via `/dh:complete-implementation`). Or: user decides to dismiss an item at any point.

**Skill**: `/dh:work-backlog-item` (Step 9 — close or resolve sub-commands)

**Actor**: Orchestrator, with user input for reason/summary.

### Semantics (ADR-9)

ADR-9 inverted the close/resolve semantics from ADR-8 to match natural language:

- **close** = dismissed without completion. Item will NOT be worked. Terminal, no work done.
- **resolve** = completed with evidence trail. Work IS done. Terminal.

Both operations close the GitHub Issue. The distinction lives in the structured comment and optionally in labels.

```mermaid
flowchart TD
    Start(["work-backlog-item<br>close or resolve"]) --> Find["Step 9a: Find Item<br>backlog_view(selector='{arg}')<br>Extract title"]
    Find --> FindErr{"Error?"}
    FindErr -->|"Zero matches"| Stop1(["STOP — No item found"])
    FindErr -->|"Multiple matches"| Pick["List all — ask user to pick"]
    FindErr -->|"Already completed"| Stop2(["STOP — already closed"])
    FindErr -->|"Single match"| Route{close or resolve?}

    Route -->|close| Close
    Route -->|resolve| Resolve

    subgraph Close [Close Path — Dismiss Without Completion]
        C1["Ask user: Why dismissed?<br>Options: duplicate, out_of_scope,<br>superseded, wontfix, blocked"]
        C1 --> C2{"duplicate or<br>superseded?"}
        C2 -->|Yes| Ref["Ask: Which item does this<br>duplicate / is superseded by?"]
        C2 -->|No| C3
        Ref --> C3["Optional: additional comment"]
        C3 --> CCall["backlog_close(<br>selector, reason,<br>reference, comment)<br>No checklist verification<br>No AC verification<br>No status:verified check"]
    end

    subgraph Resolve [Resolve Path — 5 Verification Gates]
        R1{"9b.5 — status:verified gate<br>(SAM items only — has Plan field)"}
        R1 -->|"Label present"| R2
        R1 -->|"Label absent + --force"| R2
        R1 -->|"Label absent, no --force"| RBlock(["STOP — options:<br>1. Run /complete-implementation<br>2. Re-run with --force<br>3. Close instead"])

        R2{"9c: Checklist verification<br>(plan items only)<br>Read plan, count tasks<br>checked_tasks == total_tasks?"}
        R2 -->|"Incomplete"| RBlock2(["STOP — list unchecked tasks"])
        R2 -->|"100% or no plan"| R3

        R3{"9d: AC verification<br>Spawn general-purpose agent<br>Verify each criterion with<br>file:line evidence<br>Return [PASS]/[FAIL] per criterion"}
        R3 -->|"Overall FAIL"| RBlock3(["STOP — report gaps"])
        R3 -->|"Overall PASS"| R4

        R4{"9e: Open PR check<br>git log --grep='Fixes #N|Closes #N'"}
        R4 -->|"Open PR found"| PRWait(["Update local status only<br>GitHub Issue will auto-close<br>when PR merges — STOP"])
        R4 -->|"No open PR"| R5

        R5["9f: backlog_resolve(<br>selector, summary (required),<br>plan, method, notes,<br>follow_ups, findings)"]
    end
```

**close metadata** (ADR-9): `{"status": "closed", "close_reason": "{reason}"}`. GitHub comment: `Closed ({reason}). Reference: {reference}. {comment}`. GitHub issue state: `closed`.

**resolve metadata** (ADR-9): `{"status": "done", "priority": "completed", "plan": "{plan}"}`. GitHub comment: structured markdown with non-empty sections only. GitHub issue state: `closed`.

**"Already implemented" discovery** during grooming should use `resolve(summary="Already implemented via PR #N / commit {sha}")`, not `close` (per ADR-9 Consequences).

**complete-milestone is NOT referenced** anywhere in `work-backlog-item/SKILL.md`. The transition from resolve to milestone closure is not documented (audit Finding 9 Gap E).

**Failure paths**:

- Resolve without `status:verified` and no `--force` — STOP with 3 options
- Checklist incomplete — STOP with unchecked task list
- AC verification FAIL — STOP with per-criterion gap report
- Open PR detected — defer GitHub issue close to PR merge, update local status only

**`--cleanup` flag**: Both `backlog_close` and `backlog_resolve` accept `cleanup: bool` to remove local file after operation. Documented in ADR-9 tool params but NOT exercised in the current Step 9 procedure.

**`--force` flag**: Bypasses `status:verified` gate (9b.5) and open PR gate (9e).

---

## Unimplemented Extensions and Known Gaps

### Gap 1: No Batch Section Write for Grooming (Audit F6, session observation)

Each grooming section requires a separate `backlog_groom` call with `section` and `content`. No single-call API writes all sections atomically. This makes the grooming process chatty (7+ sequential MCP calls) and complicates failure recovery if interrupted mid-way.

### Gap 2: Description / Groomed Section Overlap (Session observation)

The item's initial `## Description` body and the groomed `### Output / Evidence` / `### Decision` subsections frequently contain overlapping content. No deduplication or handoff mechanism exists.

### Gap 3: No Auto-Advance After Grooming (Session observation)

After `backlog_groom` writes all sections and sets the `groomed` frontmatter field, no automatic label transition occurs. The skill source does not document an explicit `status:groomed` label change — only the frontmatter field is set.

### Gap 4: No Machine-Readable Parent/Child Links (Session observation)

The GraphQL `addSubIssue` mutation is implemented in `backlog_core/github.py` and used for SAM task sub-issues. However, no general `backlog_link_parent` MCP tool exists for arbitrary backlog-to-backlog item linking. Inter-item dependencies in groomed items are prose-only (the `### Dependencies` section lists titles or issue numbers as text).

### Gap 5: Compaction Recovery (Tracked: #1069)

When the orchestrator runs `/dh:implement-feature` and spawns a team via `TeamCreate`, the team's state is held only in the orchestrator's context window. If auto-compaction fires, the orchestrator loses awareness of running teammates and abandons them.

Target fix: Write team state to beads (`bd`) after `TeamCreate`. `PreCompact` hook folds active beads into compact summary. `SessionStart` hook restores. On recovery, `bd list --status=in_progress` resumes from last known state.

### Gap 6: Proactive Handoff Flush (Tracked: #1070)

At 40% context pressure, write a structured handoff before compaction rather than losing state. Not yet implemented.

### Audit Finding F1: No Feasibility Assessment Step (Severity: High)

No gate exists between RT-ICA APPROVED and SAM planning invocation for technical feasibility, effort/value assessment, risk assessment, or alternative evaluation. RT-ICA checks information completeness, not feasibility. Source: audit Finding 1 (2026-03-02).

### Audit Finding F2: Discussion Phase Absent (Severity: Medium)

No skill provides a structured discussion or interview step between creation and grooming. ARL human-probing design doc exists but is not implemented (marked "Status: Design"). Source: audit Finding 2 (2026-03-02).

### Audit Finding F3: RT-ICA Staleness (Severity: Low-Medium)

No staleness check on RT-ICA results. If groomed in a previous session and codebase changed, old RT-ICA may be stale — yet `work-backlog-item` accepts without re-verification. No defined policy for when RT-ICA should be re-run vs. accepted from cache. Source: audit Finding 3 (2026-03-02).

### Audit Finding F4: Vague "Is Job Valid?" Condition (Severity: Medium)

`groom-backlog-item` Step 2, check C1: "Is the job still valid?" — no observable fact or concrete check specified. What signals indicate invalid scope is not defined. Source: audit Finding 4 (2026-03-02).

### Audit Finding F6: No Feedback Loop on Groomer Agent Quality (Severity: Medium)

Groomer output is written directly to the item file in Step 9. No quality check, no section completeness validation, no rejection/retry path if output is incomplete or includes implementation details. Source: audit Finding 6 (2026-03-02).

### Audit Finding F7: Auto-Mode P1 Default (Severity: Low)

`create-backlog-item` auto mode defaults to P1 when no urgency keywords match. Most items default to P1 regardless of actual importance. Source: audit Finding 7 (2026-03-02).

### Audit Finding F8: Fact-Check Auto-Commits and Pushes (Severity: Low)

`fact-check` SKILL.md Step 6 auto-commits and pushes without user confirmation. No other skill in the chain auto-pushes. Source: audit Finding 8 (2026-03-02).

### Audit Finding F9: Implied Handoffs (Severity: High)

Six critical transitions between skills are implied (text suggestions) but not explicitly invoked:

- **Gap A**: `create-backlog-item` → `groom-backlog-item` — text output only
- **Gap B**: `groom-backlog-item` → `group-items-to-milestone` — not mentioned
- **Gap C**: `group-items-to-milestone` → `start-milestone` — not mentioned
- **Gap D**: `complete-implementation` → `work-backlog-item resolve` — partially resolved. `complete-implementation` outputs a handoff to the next item but not an explicit resolve instruction for the current item. This document now recommends adding the resolve instruction (see Phase 6, "Recommended resolve handoff")
- **Gap E**: `work-backlog-item resolve` → `complete-milestone` — not mentioned (`complete-milestone` not referenced in skill)
- **Gap F**: `fact-check` → back to `groom-backlog-item` — implicit session coupling

Source: audit Finding 9 (2026-03-02).

### Audit Finding F10: Draft Lifecycle Doc Not Promoted (Severity: Medium) — Addressed

A draft lifecycle doc existed but was not referenced by any skill. This document (the one you are reading) was created to address this gap and supersedes the draft. Source: audit Finding 10 (2026-03-02).

### Missing Reference Files (Session observation 2026-03-25)

`groom-backlog-item/SKILL.md` references `./references/issue-classification.md` and `./references/groomer-agent.md` — neither file exists on disk. The `references/` directory under `groom-backlog-item/` does not exist.

### BLOCKED Task Handling Undocumented (Session observation 2026-03-25)

Neither `implement-feature` nor `start-task` documents an explicit procedure for BLOCKED tasks during execution. The completion gate triggers only on COMPLETE. No escalation path or loop-exit condition for mixed terminal states (COMPLETE + BLOCKED) exists in these skill files.

---

## Related Documents

- [Backlog Item Lifecycle (Draft — superseded by this document)](./backlog-lifecycle.draft.md)
- [Workflow Architecture Diagram (SAM pipeline detail)](./workflow-architecture-diagram.md)
- [Plan Artifact Lifecycle Policy](./plan-artifact-lifecycle.md)
- [Backend Providers](./backend-providers.md)
- [ADR-9: Close/Resolve Semantics](./adr-9-close-resolve-semantics.md)
- [Process Audit (2026-03-02)](./process-audit-backlog-lifecycle-2026-03-02.md)
