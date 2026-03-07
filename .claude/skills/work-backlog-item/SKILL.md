---
name: work-backlog-item
description: "Use when working, planning, or closing a backlog item. Bridges backlog items to SAM planning with GitHub Issue/Project/Milestone tracking. No args: interactive browser. '#N': load from GitHub Issue #N. Title substring: auto-grooming, RT-ICA gate, GitHub sync, SAM planning. '--auto {title}': autonomous mode — no AskUserQuestion, derives data from research files, logs decisions. 'close {title}': dismiss without completion — reason required (duplicate, out_of_scope, superseded, wontfix, blocked). ADR-9. 'resolve {title}': mark DONE with evidence trail — summary required. ADR-9. 'setup-github': init labels, project, milestone. '--language' and '--stack' select Layer 1/2 profile. STOPS if item has Plan field or RT-ICA returns BLOCKED."
argument-hint: '[#N | --auto {title} | --language {lang} | --stack {stack} | item-title-substring | close {title} | resolve {title} | setup-github | --quick {title} | progress | resume [{title}]]'
user-invocable: true
---
# Work Backlog Item

Bridge a backlog item into the SAM planning pipeline via `/add-new-feature` (default). Optional `--language` and `--stack` select Layer 1/2 profiles — see [.claude/docs/sdlc-layers/](../../docs/sdlc-layers/).

**Phase separation**: Grooming (Step 3) is autonomous research — the agent verifies facts, maps resources, estimates effort, and surfaces blockers. Planning (Step 6) is solution design — architecture, tasks, implementation. The human sets priorities and resolves blockers; the agent handles research and fact-checking autonomously.

**SAM** — Stateless Agent Methodology. See [sam-definition.md](./references/sam-definition.md) for what SAM is and how to embody it. SAM lives in `../stateless-agent-methodology/` (or `bitflight-devops/stateless-agent-methodology` on GitHub).
Primary source of truth is **GitHub Issues** (labels + milestone = canonical status); `.claude/backlog/` per-item files are the local cache and are kept in sync.

When invoked with no arguments, shows an interactive browser. When invoked with `#N` or a title substring, proceeds directly to the planning workflow.

## Arguments

`$0` selects the operating mode; remaining positional args (`$1`, `$2`, ...) form the title or parameter:

| `$0` value | Remaining args | Mode |
|---|---|---|
| (empty) | — | Interactive browser |
| `#N` | — | Issue-first: load item from GitHub Issue #N |
| bare number (e.g. `249`) | — | Issue-first: load item from GitHub Issue #249 |
| GitHub issue URL | — | Issue-first: extract issue number from URL |
| `--auto` | `$1`+ = title (or empty → auto-select first open P0/P1 item) | Autonomous — no `AskUserQuestion` calls |
| `close` | `$1`+ = title, `#N`, number, or URL | Dismiss without completion (reason required). ADR-9 |
| `resolve` | `$1`+ = title, `#N`, number, or URL | Mark DONE — completed with evidence (summary required). ADR-9 |
| `setup-github` | — | Initialize labels, project, first milestone |
| `--quick` | `$1`+ = title | Skip grooming, RT-ICA, and SAM — quick one-file fix. Step Q |
| `progress` | — | Backlog health and active milestone progress report. Step P |
| `resume` | `$1`+ = title or `#N` (optional) | Resume status for an in-progress plan. Step R |
| (any other) | — | `$ARGUMENTS` treated as title substring → planning |

**Optional flags** (when `$0` is title substring or `--auto`): `--language <lang>` selects language plugin (default: python); `--stack <profile>` selects stack profile (e.g., python-fastapi, python-cli). See [.claude/docs/sdlc-layers/](../../docs/sdlc-layers/).

```text
/work-backlog-item                                    # interactive browser
/work-backlog-item #42                               # issue-first → planning
/work-backlog-item 42                                # issue-first (bare number) → planning
/work-backlog-item https://github.com/Jamie-BitFlight/claude_skills/issues/42  # URL → planning
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

Dispatch is determined by `$0` as listed in the Arguments table above. See each step below for the full procedure triggered by each mode.

**AUTO_MODE** — when set, all `AskUserQuestion` calls are replaced with evidence-derived decisions. See [auto-mode.md](./references/auto-mode.md) for the substitution table.

### Step 0: Interactive Browser (no arguments only)

**Trigger:** `$0` is empty (no arguments passed).

Full procedure (MCP error handling, display format, response handling): [step-procedures.md](./references/step-procedures.md#step-0-interactive-browser)

**Routing:** If `$0` is `close` or `resolve`, extract `$1`+ as the title and jump directly to Step 9.

### Step 1b: Issue-First Path (`#N`, bare number, or GitHub URL)

**Trigger:** `$0` matches `#[0-9]+`, is a bare number, or is a GitHub issue URL (`https://github.com/.../issues/N`).

<issue_first_procedure>

Fetch the issue using the `mcp__backlog__backlog_view` tool (accepts URLs, `#N`, and bare numbers):

Call the `mcp__backlog__backlog_view` tool with `selector="{$0}"`.

If the tool returns a dict with an `error` key, report and stop.
Parse the returned dict. If `state` is `closed`, run the **Completed Issue Discovery** procedure and stop. Full procedure (git commands, report template, AUTO_MODE behavior): [step-procedures.md](./references/step-procedures.md#step-1b-completed-issue-discovery)

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
| `file_path` | `file_path` (local per-item file, if matched) |

The `view` command automatically merges local per-item data with live GitHub issue data. If `file_path` is present, the local file supplements any missing fields (e.g. `research_first`, `suggested_location`). If no local file exists, the GitHub Issue data is sufficient.

Proceed to Step 2.7 (Set In-Progress Label) with the assembled item, then continue to Step 3.

</issue_first_procedure>

### Step 1: Find the Backlog Item

Call the `mcp__backlog__backlog_list` tool and search the `title` field of each entry in the returned dict for a case-insensitive match against the title. Title = `$1`+ joined (args after the mode flag `$0`). In interactive mode, title = full `$ARGUMENTS`.

**AUTO_MODE with no title (`$1` is empty):** apply the "No title given" substitution from the `--auto mode rules` table — scan P0 then P1 sections for the first open item, log and use its title. Skip items with `status: done` or `status: resolved` in their entry (these are filtered out by `backlog_list` already).

- **Zero matches (interactive mode):** report "No backlog item found matching: {title}" and offer to create one via `/create-backlog-item`.
- **Zero matches (AUTO_MODE):** log `[AUTO] No item found — invoking create-backlog-item --auto {title}`, invoke `Skill(skill: "create-backlog-item", args: "--auto {title}")`, then re-run Step 1.
- **Multiple matches (interactive mode):** list all matches and ask the user to pick one.
- **Multiple matches (AUTO_MODE):** log `[AUTO] Multiple matches — picking first: {title}`, proceed with first match.

Record the priority section (P0, P1, P2, Ideas) the item belongs to.

### Step 2: Extract Item Fields

From the matched item's entry in the `mcp__backlog__backlog_list` returned dict, extract `title`, `plan`, `section` (priority), `issue`, `groomed`, and `file_path`. For detailed fields not in the dict (`description`, `source`, `added`, `research_first`, `suggested_location`), read the per-item file at `file_path`.

- `title` — the `title` field from JSON (required)
- `source` — not in JSON; read from per-item file frontmatter `metadata.source` if needed (optional)
- `added` — not in JSON; read from per-item file frontmatter `metadata.added` if needed (optional)
- `description` — not in JSON; read from per-item file frontmatter `description` (required)
- `research_first` — not in JSON; read from per-item file body `**Research first**:` line (optional)
- `suggested_location` — not in JSON; read from per-item file body `**Suggested location**:` line (optional)
- `plan` — the `plan` field from JSON (optional)

If the item already has a `**Plan**:` field, report:

```text
This item already has a plan at {path}. Use /implement-feature {path} to execute it.
```

Then stop.

After extracting fields, proceed to Step 2.3 (Already Implemented Check) before continuing.

### Step 2.3: Already Implemented Check

Before planning, verify the feature/fix hasn't already been implemented (stale open issue). Full procedure (git commands, resolve calls, AUTO_MODE behavior): [step-procedures.md](./references/step-procedures.md#step-23-already-implemented-check)

### Step 3: Auto-Groom (if needed)

<groom_check>

1. **Check if item is groomed**: Check the `groomed` field in the JSON output. If `true`, read the per-item file at `file_path` for the groomed content under `## Groomed`. Use that content.
2. Search conversation context for a recent `groom-backlog-item` output matching this item.

If no groomed content exists in the item file:

```text
Skill(skill: "groom-backlog-item", args: "{item title}")
```

The groom skill writes groomed content into the per-item file. Capture the groomed output (Reproducibility, Resources, Dependencies, Blockers, etc.) for use in the feature request.
</groom_check>

### Step 4: RT-ICA Checkpoint

<rtica_gate>
Before composing the feature request, verify the groomed content (from item file or groom-backlog-item output) contains an RT-ICA summary. If absent, perform RT-ICA now:

1. **Goal statement** — What completing this item achieves.
2. **Reverse prerequisites** — Conditions required for success (enumerate each).
3. **Availability check** — For each condition: AVAILABLE / DERIVABLE / MISSING.
4. **Decision** — APPROVED or BLOCKED.

**If BLOCKED:**

When RT-ICA blocks, optionally offer ARL human-probing questions (e.g., "What went wrong in the past?", "What references are essential?") to capture invisible knowledge. Add answers to `.claude/domain-knowledge/` with staleness tracking. See [.claude/docs/sdlc-layers/arl-human-probing-design.md](../../docs/sdlc-layers/arl-human-probing-design.md).

Present a structured summary to the user:

```text
RT-ICA: BLOCKED

Missing inputs that prevent SAM planning:
- {missing condition 1}
- {missing condition 2}

Provide these inputs before proceeding. SAM planning will not be invoked with known gaps.
```

Wait for user response. Do not invoke Step 5 until BLOCKED is resolved.

**If APPROVED:**

Proceed to Step 5. Carry DERIVABLE items forward as "Assumptions to confirm" in the RT-ICA section of the feature request.
</rtica_gate>

### Step 5: Compose Feature Request

Build the feature request string for `add-new-feature`. If `--stack` was specified, append a "Stack profile" line. If `--language` is not `python`, invoke the corresponding language plugin (e.g., `/typescript-development:add-new-feature`).

Template: [step-procedures.md](./references/step-procedures.md#step-5-feature-request-template)

### Step 6: Invoke SAM Planning

```text
Skill(skill: "add-new-feature", args: "{composed feature request}")
```

This runs the full SAM workflow: discovery, codebase analysis, architecture spec, task decomposition, validation, context manifest.

### Step 7: Update Backlog with Plan Reference

After `add-new-feature` completes, identify the task file it created:

```text
Glob(pattern="plan/tasks-*-{slug}*")
```

Where `{slug}` is the item title lowercased with spaces replaced by hyphens.

Call the `mcp__backlog__backlog_update` tool to add the Plan:

| Parameter | Value |
|-----------|-------|
| `selector` | `"{title}"` |
| `plan` | `"plan/tasks-{N}-{slug}.md"` |

If the item has `**Issue**: #N`, record it in the plan file header comment and include `Fixes #N` in any commit message produced during implementation.

### Step 8: Report Next Steps

```text
Backlog item "{title}" is now planned.

- Plan file: plan/tasks-{N}-{slug}.md (or plan/tasks-{N}-{slug}/ directory)
- To execute:      /implement-feature {slug}
- To check status: /implementation-manager status . {slug}
- To close when done: /work-backlog-item close {slug}
```

**Do NOT close the GitHub Issue directly.** Include `Fixes #N` in commit messages and the PR body — the issue auto-closes when the PR merges. Only use `/work-backlog-item resolve` for post-merge verification and local bookkeeping. Use `/work-backlog-item close` only for dismissals (duplicate, out_of_scope, etc.). Never call `mcp__backlog__backlog_resolve` before the PR has merged.

### Step 9: Close or Resolve (ADR-9)

**Trigger:** `$0` is `close` or `resolve`.

- `close` = dismiss without completion. Requires `reason` (duplicate, out_of_scope, superseded, wontfix, blocked). Optional `reference` and `comment`. Calls `mcp__backlog__backlog_close`.
- `resolve` = mark DONE with evidence trail. Requires `summary`. Optional `plan`, `method`, `notes`, `follow_ups`, `findings`. Verifies checklist + acceptance criteria before resolving. Calls `mcp__backlog__backlog_resolve`.

Full step-by-step procedure (9a–9f): [close-resolve-procedure.md](./references/close-resolve-procedure.md)

## GitHub Integration

`.claude/backlog/` per-item files are the local cache. GitHub Issues are the source of truth. See [github-integration.md](./references/github-integration.md) for step-by-step commands, commit message conventions (`Fixes #N`), and example sessions.

### Step 2.5: GitHub Issue Sync

After Step 2, check for `**Issue**: #N` in the matched item. Full procedure (gh commands, yes/no branching, issue creation): [github-integration.md](./references/github-integration.md#step-25-github-issue-sync)

**Note:** On the Issue-first path (Step 1b), the `backlog_view` response already contains issue state — carry it forward without re-fetching.

### Step 2.5a: Create GitHub Issue

Full procedure: [github-integration.md](./references/github-integration.md#step-25a-create-github-issue)

### Step 2.7: Set In-Progress Label

Full procedure: [github-integration.md](./references/github-integration.md#step-27-set-in-progress-label)

**Two-part step:** (a) Always run `mcp__backlog__backlog_update` with `status="in-progress"` for the current item. (b) Run `milestone start` only on explicit user intent to start the whole milestone — it bulk-transitions all open milestone issues, not just the current one.

### setup-github Command

**Trigger:** `$0` is `setup-github`. Full setup procedure and expected output: [github-integration.md](./references/github-integration.md#setup-github-command)

## Error Handling

See [error-handling.md](./references/error-handling.md) for all error conditions and handling instructions.

## Example Sessions

See [example-sessions.md](./references/example-sessions.md) for complete examples. GitHub-specific sessions (issue creation, setup-github): [github-integration.md](./references/github-integration.md)

---

## Validation Plan

See [validation-plan.md](./references/validation-plan.md) for V1–V6 verification commands and the full integration test sequence.
