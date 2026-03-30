---
name: work-backlog-item
description: "Use when working, planning, or closing a backlog item. Bridges backlog items to SAM planning with GitHub Issue/Project/Milestone tracking. No args: interactive browser. '#N': load from GitHub Issue #N. Title substring: auto-grooming, RT-ICA gate, GitHub sync, SAM planning. '--auto {title}': autonomous mode — no AskUserQuestion, derives data from research files, logs decisions. 'close {title}': dismiss without completion — reason required (duplicate, out_of_scope, superseded, wontfix, blocked). ADR-9. 'resolve {title}': mark DONE with evidence trail — summary required. ADR-9. 'setup-github': init labels, project, milestone. '--language' and '--stack' select Layer 1/2 profile. STOPS if item has Plan field or RT-ICA returns BLOCKED."
argument-hint: '[#N | --auto {title} | --language {lang} | --stack {stack} | item-title-substring | close {title} | resolve {title} [--force] | setup-github | --quick {title} | progress | resume [{title}]]'
user-invocable: true
---

<mode>$0</mode>
<item_ref>$1</item_ref>
<invocation_args>$ARGUMENTS</invocation_args>

# Work Backlog Item

Bridge a backlog item into the SAM planning pipeline via `/dh:add-new-feature` (default). Optional `--language` and `--stack` select Layer 1/2 profiles — see [sdlc-layers](../../docs/sdlc-layers/).

See the [Backlog Lifecycle reference](../../docs/backlog-lifecycle.md) for the complete state machine, handoff protocol, and data architecture.

**Phase separation**: Grooming (Step 3.1) is autonomous research — the agent verifies facts, maps resources, estimates effort, and surfaces blockers. Planning (Step 4.2) is solution design — architecture, tasks, implementation. The human sets priorities and resolves blockers; the agent handles research and fact-checking autonomously.

**SAM** — Stateless Agent Methodology. See [sam-definition.md](./references/sam-definition.md) for what SAM is and how to embody it. SAM lives in `../stateless-agent-methodology/` (or `bitflight-devops/stateless-agent-methodology` on GitHub).
Primary source of truth is **GitHub Issues** (labels + milestone = canonical status). Local per-item files are a read cache maintained by the MCP server.

When invoked with no arguments, shows an interactive browser. When invoked with `#N` or a title substring, proceeds directly to the planning workflow.

## Arguments

`<mode/>` selects the operating mode; remaining positional args (`<item_ref/>`, `$2`, ...) form the title or parameter:

| `<mode/>` value | Remaining args meaning |
|---|---|
| (empty) | — |
| `#N` / bare number / GitHub issue URL | issue number |
| `--auto` | `<item_ref/>`+ = title (or empty → auto-select first open P0/P1 item) |
| `close` / `resolve` | `<item_ref/>`+ = title, `#N`, number, or URL |
| `setup-github` | — |
| `--quick` | `<item_ref/>`+ = title |
| `progress` / `resume` | `<item_ref/>`+ = title or `#N` (optional for `resume`) |
| (any other) | `<invocation_args/>` treated as title substring |

**Optional flags** (when `<mode/>` is title substring or `--auto`): `--language <lang>` selects language plugin (default: python); `--stack <profile>` selects stack profile (e.g., python-fastapi, python-cli). See [sdlc-layers](../../docs/sdlc-layers/).

```text
/work-backlog-item                                    # interactive browser
/work-backlog-item #42                               # issue-first → planning
/work-backlog-item 42                                # issue-first (bare number) → planning
/work-backlog-item https://github.com/OWNER/REPO/issues/42  # URL → planning
/work-backlog-item Error Recovery                    # direct match → planning
/work-backlog-item --auto                            # autonomous → auto-select first open P0/P1
/work-backlog-item --auto vercel skills npm package  # autonomous → planning
/work-backlog-item close Error Recovery              # dismiss (reason required)
/work-backlog-item close #42                         # dismiss by issue number
/work-backlog-item resolve Error Recovery            # mark completed with evidence
/work-backlog-item resolve #42                       # mark completed by issue number
/work-backlog-item --language python --stack python-fastapi Add auth  # Layer 2 stack profile
```

### --auto mode rules

All interactive `AskUserQuestion` calls are replaced with evidence-derived decisions. Full substitution table: [auto-mode.md](./references/auto-mode.md)

## Workflow

### Routing (evaluated first, before any step)

Dispatch based on `<mode/>` (the first argument word) before executing any step:

```mermaid
flowchart TD
    Start(["<mode/> value"]) --> Q1{Value?}
    Q1 -->|"empty"| S0["Step 1.1 — interactive browser"]
    Q1 -->|"#N / bare number / GitHub issue URL"| S1b["Step 1.2 — Issue-first path<br>title source: issue number from input"]
    Q1 -->|"--auto"| Auto["AUTO_MODE=true → Step 1.3<br>title source: <item_ref/>+ joined<br>(empty → auto-select first open P0/P1)"]
    Q1 -->|"--quick"| SQ["Step Q — quick mode<br>load ./references/step-procedures.md#step-q-quick-mode<br>title source: <item_ref/>+ joined"]
    Q1 -->|"progress"| SP["Step P — progress report<br>load ./references/step-procedures.md#step-p-progress-report"]
    Q1 -->|"resume"| SR["Step R — resume report<br>load ./references/step-procedures.md#step-r-resume-report<br>title source: <item_ref/>+ joined (optional)"]
    Q1 -->|"close"| S9c["Step 5.1 — close path (dismiss without completion)<br>title source: <item_ref/>+ joined (title, #N, number, or URL)"]
    Q1 -->|"resolve"| S9r["Step 5.1 — resolve path (mark completed with evidence)<br>title source: <item_ref/>+ joined (title, #N, number, or URL)"]
    Q1 -->|"setup-github"| SGH["load ./references/github-integration.md#setup-github-command"]
    Q1 -->|"any other string"| S1["Title substring → Step 1.3 (interactive mode)<br>title source: <invocation_args/>"]
```

**AUTO_MODE** — set when `$0` is `--auto`. All `AskUserQuestion` calls are replaced with evidence-derived decisions. See [auto-mode.md](./references/auto-mode.md) for the substitution table.

## Phase 1: Locate

### Step 1.1: Interactive Browser (no arguments only)

**Trigger:** `<mode/>` is empty (no arguments passed).

Full procedure (MCP error handling, display format, response handling): [step-procedures.md](./references/step-procedures.md#step-1-1-interactive-browser)

**Routing:** If `<mode/>` is `close` or `resolve`, extract `<item_ref/>`+ as the title and jump directly to Step 5.1.

### Step 1.2: Issue-First Path (`#N`, bare number, or GitHub URL)

**Trigger:** `<mode/>` matches `#[0-9]+`, is a bare number, or is a GitHub issue URL (`https://github.com/.../issues/N`).

<issue_first_procedure>

Fetch the issue using the `mcp__plugin_dh_backlog__backlog_view` tool (accepts URLs, `#N`, and bare numbers):

Call the `mcp__plugin_dh_backlog__backlog_view` tool with `selector="{<mode/>}"`.

If the tool returns a dict with an `error` key, report and stop.
Parse the returned dict. If `state` is `closed`, run the **Completed Issue Discovery** procedure and stop. Full procedure (git commands, report template, AUTO_MODE behavior): [step-procedures.md](./references/step-procedures.md#step-1-2-completed-issue-discovery)

From the JSON response build the working item:

| Field | Source |
|---|---|
| `title` | `title` |
| `description` | `body` (full text) |
| `source` | `"GitHub Issue #N"` |
| `priority` | `priority` field (extracted from `priority:*` label) |
| `status` | `status` field (extracted from `status:*` label — canonical) |
| `milestone` | `milestone` |
| `plan` | `plan` field, or search `body` for `**Plan**:` line |

The `backlog_view` MCP tool merges local cache with live GitHub issue data. All fields needed for subsequent steps are available in the response — do not read local files directly.

Proceed to Step 2.4 (Set In-Progress Label) with the assembled item, then continue to Step 3.1.

</issue_first_procedure>

### Step 1.3: Find the Backlog Item

**Bypass:** If `<mode/>` is `#N`, a bare number, or a GitHub issue URL — skip this step entirely and go to Step 1.2. Issue-number and URL inputs resolve via `backlog_view` directly; no matching strategy is needed.

Title = `<item_ref/>`+ joined (args after the mode flag `<mode/>`). In interactive mode, title = full `<invocation_args/>`.

**AUTO_MODE with no title (`<item_ref/>` is empty):** apply the "No title given" substitution from the `--auto mode rules` table — scan P0 then P1 sections for the first open item, log and use its title. Skip items with `status: done` or `status: resolved` in their entry (these are filtered out by `backlog_list` already).

Before executing Step 1.3: load `./references/step-procedures.md`.

Record the priority section (P0, P1, P2, Ideas) the item belongs to.

### Step 1.4: Extract Item Fields

From the matched item's entry in the `mcp__plugin_dh_backlog__backlog_list` returned dict, extract `title`, `plan`, `section` (priority), `issue`, and `groomed`. For detailed fields not in the list response (`description`, `source`, `added`, `research_first`, `suggested_location`), call `mcp__plugin_dh_backlog__backlog_view(selector="{title}", summary=false)` to fetch the full item from the backend.

- `title` — the `title` field from list JSON (required)
- `plan` — the `plan` field from list JSON (optional)
- `description` — from `backlog_view` response `description` field (required)
- `source` — from `backlog_view` response `source` field (optional)
- `added` — from `backlog_view` response `added` field (optional)
- `research_first` — from `backlog_view` response body, `**Research first**:` line (optional)
- `suggested_location` — from `backlog_view` response body, `**Suggested location**:` line (optional)

If the item already has a `**Plan**:` field, extract the plan address from the YAML filename (e.g., `plan/P1079-machine-readable-inter-item-dependencies.yaml` → `P1079`). Report:

```text
This item already has a plan (P{NNN}). Use /dh:implement-feature P{NNN} to execute it.
```

Then stop.

After extracting fields, proceed to Step 2.1 (Already Implemented Check) before continuing.

## Phase 2: Validate

### Step 2.1: Already Implemented Check

Before planning, verify the feature/fix hasn't already been implemented (stale open issue). Full procedure (git commands, resolve calls, AUTO_MODE behavior): [step-procedures.md](./references/step-procedures.md#step-2-1-already-implemented-check)

### Step 2.2: GitHub Issue Sync

After Step 1.4, check for `**Issue**: #N` in the matched item. Full procedure (MCP tool calls, yes/no branching, issue creation): [github-integration.md](./references/github-integration.md#step-2-2-github-issue-sync)

**Note:** On the Issue-first path (Step 1.2), the `backlog_view` response already contains issue state — carry it forward without re-fetching.

### Step 2.3: Create GitHub Issue

Full procedure: [github-integration.md](./references/github-integration.md#step-2-3-create-github-issue)

### Step 2.4: Set In-Progress Label

Full procedure: [github-integration.md](./references/github-integration.md#step-2-4-set-in-progress-label)

**Two-part step:** (a) Always run `mcp__plugin_dh_backlog__backlog_update` with `status="in-progress"` for the current item. (b) Run `milestone start` only on explicit user intent to start the whole milestone — it bulk-transitions all open milestone issues, not just the current one.

### Step 2.5: Discovery Gate

Before grooming or planning, check whether a structured discovery artifact exists.

```mermaid
flowchart TD
    InProgress([Step 2.4 complete — label set]) --> HasIssue{"Item has GitHub<br>Issue number?"}
    HasIssue -->|"No"| SkipGate["Skip discovery gate<br>Proceed to Step 3.1"]
    HasIssue -->|"Yes — issue #{N}"| TypeCheck{"Labels include<br>'type:fix' or 'type:bug'?"}
    TypeCheck -->|"Yes — fix/bug type"| SkipGate
    TypeCheck -->|"No — feature/refactor/other"| CheckArtifact["artifact_list(<br>issue_number={N},<br>artifact_type='feature-context')"]
    CheckArtifact --> HasDiscovery{"count > 0?"}
    HasDiscovery -->|"Yes"| Proceed["Discovery exists<br>Proceed to Step 3.1"]
    HasDiscovery -->|"No"| InvokeDiscovery["Invoke: Skill(skill='dh:discovery')<br>Wait for user confirmation loop<br>Then proceed to Step 3.1"]
    SkipGate --> Continue([Step 3.1 — Auto-Groom])
    Proceed --> Continue
    InvokeDiscovery --> Continue
```

The discovery skill runs its full interactive confirmation loop (WHO/WHAT/WHEN/WHY gathering)
and registers the result as a `feature-context` artifact. After completion, Step 3.1 (Auto-Groom)
will detect the artifact and pass it to the grooming swarm.

## Phase 3: Prepare

### Step 3.1: Auto-Groom (if needed)

<groom_check>

1. **Check if item is groomed**: Check the `groomed` field in the JSON output. If `true`, call `mcp__plugin_dh_backlog__backlog_view(selector="{title}", summary=false)` — the response `sections` dict contains all groomed content (Reproducibility, Priority, Impact, Files, Dependencies, etc.). Use that content.
2. Search conversation context for a recent `groom-backlog-item` output matching this item.

If no groomed content exists:

```text
Skill(skill: "groom-backlog-item", args: "{item title}")
```

The groom skill writes groomed content via the backlog MCP server. After grooming completes, call `backlog_view` again to retrieve the groomed sections.
</groom_check>

### Step 3.2: RT-ICA Gate

#### RT-ICA Staleness Policy

> **RT-ICA Staleness Policy**: An RT-ICA result is stale and must be re-run if either condition
> is true: (a) the `Date:` header in the RT-ICA section is older than 7 calendar days, or
> (b) the item's `metadata.updated_at` field is newer than the RT-ICA section date. A stale
> RT-ICA result is treated as absent — `dh:rt-ica` is re-run before proceeding to Step 3.4.
> The 7-day threshold applies regardless of whether the item description has changed, because
> codebase context may have changed even if the item text has not.

```mermaid
flowchart TD
    RCheck(["Step 3.2: RT-ICA Freshness Check"]) --> Get["Read backlog_view(selector=title, summary=false).sections['RT-ICA']"]
    Get --> Absent{"sections['RT-ICA'] key present and non-empty?"}
    Absent -->|"No"| RunRTICA(["Run dh:rt-ica — section absent"])
    Absent -->|"Yes"| ParseDate["Extract date using regex 'Date: YYYY-MM-DD' from section<br>If no match: try first ISO date in top 3 lines of section"]
    ParseDate --> DateFound{"ISO date parseable?"}
    DateFound -->|"No — date not found"| RunRTICA
    DateFound -->|"Yes — date D extracted"| Check1{"D older than 7 calendar days?"}
    Check1 -->|"Yes"| RunRTICA
    Check1 -->|"No — within 7 days"| Check2{"backlog_view metadata.updated_at present<br>AND metadata.updated_at greater than D?"}
    Check2 -->|"updated_at greater than D"| RunRTICA
    Check2 -->|"updated_at less than or equal to D OR field absent"| UseCache(["RT-ICA is fresh — use cached result"])
```

When the flowchart routes to "Run dh:rt-ica":

```text
Skill(skill: "dh:rt-ica")
```

1. **Present and fresh** → use the APPROVED/BLOCKED decision from the cached result. Carry DERIVABLE items forward as "Assumptions to confirm" in the feature request.
2. **BLOCKED** → stop. Do not proceed to Step 3.4 until all MISSING conditions are resolved.

### Step 3.3: RT-ICA Date Stamp

After `dh:rt-ica` completes (or the existing result is confirmed fresh), write a parseable `Date:` header to the RT-ICA section before storing the result:

```text
RT-ICA Final: {item title}
Date: {YYYY-MM-DD}
Goal: {same as snapshot}
```

The `Date:` header is required for the freshness check in Step 3.2. If the RT-ICA result was retrieved from cache and already contains a `Date:` header, skip this step.

### Step 3.4: Feasibility Gate

**Trigger:** RT-ICA returned APPROVED (Step 3.2) and RT-ICA Date Stamp written (Step 3.3).

Load [feasibility-gate.md](./references/feasibility-gate.md) and evaluate all 4 criteria (technical feasibility, effort proportionality, blast radius, prior attempt check).

**BLOCKED at feasibility gate stops the workflow** — do not proceed to Phase 4. Report the BLOCKED output contract from the reference file and stop.

**PASS** → proceed to Step 4.1 (Compose Feature Request) with the feasibility assessment appended to the feature request.

## Phase 4: Plan

### Step 4.1: Compose Feature Request

Build the feature request string for `add-new-feature`. If `--stack` was specified, append a "Stack profile" line. If `--language` is not `python`, invoke the corresponding language plugin (e.g., `/typescript-development:add-new-feature`).

**Impact Radius requirement**: Before composing, extract the Impact Radius from the `backlog_view(selector=f"#{issue_number}", summary=false)` response. The `sections` dict in the response contains an `"Impact Radius"` key (populated by `groom-backlog-item` Step 3.5). Include it in the feature request so the planner creates tasks for every affected component.

**Ecosystem Completeness Constraint**: The plan produced by `add-new-feature` MUST include tasks for every item listed in the Impact Radius, or explicitly document why an item is excluded. A feature is not complete when the core code works — it is complete when:

- Every upstream producer of the changed interface is updated or verified compatible
- Every downstream consumer is migrated to use the new interface
- Every document listed as "will become stale" is updated
- The old interface is deprecated or removed (if this item replaces something)
- CI/config files listed in Impact Radius are updated and validated

If the `backlog_view` response `sections` dict has no `"Impact Radius"` key, trigger `groom-backlog-item` for that item before continuing (Step 3.1 already handles this for ungroomed items — this handles the case where grooming ran before Step 3.5 existed). Do not skip to Step 4.2 with a missing impact radius — the planner will produce an incomplete plan.

Template: [step-procedures.md](./references/step-procedures.md#step-4-1-feature-request-template)

### Step 4.2: Invoke SAM Planning

```text
Skill(skill: "add-new-feature", args: "{composed feature request}")
```

This runs the full SAM workflow: discovery, codebase analysis, architecture spec, task decomposition, validation, context manifest.

### Step 4.3: Update Backlog with Plan Reference

After `add-new-feature` completes, identify the task plan it created by calling `mcp__plugin_dh_sam__sam_list(search="{slug}")` where `{slug}` is the item title lowercased with spaces replaced by hyphens. The SAM MCP server manages plan storage — do not search the filesystem directly.

Call the `mcp__plugin_dh_backlog__backlog_update` tool to add the Plan:

| Parameter | Value |
|-----------|-------|
| `selector` | `"{title}"` |
| `plan` | `"plan/P{NNN}-{slug}.yaml"` (state-relative path) |

If the item has `**Issue**: #N`, record it in the plan file header comment. Do NOT include `Fixes #N`, `Closes #N`, or `Resolves #N` in task-level commit messages — issue closure is handled exclusively by `/complete-implementation` in its final commit step.

### Step 4.4: Simplify

Run the simplify skill only when source code was modified during this session. Planning-only sessions (plan artifacts, backlog items, documentation) do not need code review.

```mermaid
flowchart TD
    Q{"Run: git diff --stat HEAD<br>Any .py .js .ts .cjs .mjs files<br>in the diff?"}
    Q -->|"Yes — code was written"| Run["Skill(skill: 'simplify')"]
    Q -->|"No — only .md .yaml .json<br>backlog items, plan artifacts"| Skip["Skip — no code to review"]
```

### Step 4.5: Post-Planning Output

- **Interactive mode**: load `./references/step-procedures.md#step-4-5-post-planning-output` for the report template.
- **AUTO_MODE**: load `./references/step-procedures.md#step-4-5a-auto-mode-continuation` for the continuation procedure.

## Phase 5: Close/Resolve

### Step 5.1: Close or Resolve (ADR-9)

**Trigger:** `<mode/>` is `close` or `resolve`.

- `close` = dismiss without completion. Requires `reason` (duplicate, out_of_scope, superseded, wontfix, blocked). Optional `reference` and `comment`. Calls `mcp__plugin_dh_backlog__backlog_close`.
- `resolve` = mark DONE with evidence trail. Requires `summary`. Optional `plan`, `method`, `notes`, `follow_ups`, `findings`. Verifies checklist + acceptance criteria before resolving. For items with a `**Plan**:` field, also checks that the `status:verified` GitHub label is present (Step 5.4). Calls `mcp__plugin_dh_backlog__backlog_resolve`.
- `resolve --force` = bypass the `status:verified` gate (Step 5.4) and the open-PR gate (Step 5.7) with a warning. Use when label automation failed or when forcing a local-cache resolve while a PR is still open.

Full step-by-step procedure (5.2–5.7): [close-resolve-procedure.md](./references/close-resolve-procedure.md)

After `backlog_resolve` succeeds, query the milestone for remaining open issues. If `open_issues == 0`, emit the following NEXT token:

```text
NEXT: skill="complete-milestone" args="{milestone number}" condition="all milestone issues status:done OR status:resolved AND open_issues == 0"
```

## Reference Index

### GitHub Integration

GitHub Issues are the source of truth. The backlog MCP server manages local caching — skills interact via MCP tools only. See [github-integration.md](./references/github-integration.md) for step-by-step commands and example sessions. Note: `Fixes #N` trailers are restricted to the `/complete-implementation` final commit step only.

### setup-github Command

**Trigger:** `<mode/>` is `setup-github`. Full setup procedure and expected output: [github-integration.md](./references/github-integration.md#setup-github-command)

### Error Handling

See [error-handling.md](./references/error-handling.md) for all error conditions and handling instructions.

### Example Sessions

See [example-sessions.md](./references/example-sessions.md) for complete examples. GitHub-specific sessions (issue creation, setup-github): [github-integration.md](./references/github-integration.md)

### Validation Plan

See [validation-plan.md](./references/validation-plan.md) for V1–V6 verification commands and the full integration test sequence.
