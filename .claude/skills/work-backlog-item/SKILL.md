---
name: work-backlog-item
description: "Use when working, planning, or closing a backlog item. Bridges backlog items to SAM planning with GitHub Issue/Project/Milestone tracking. No args: interactive browser. '#N': load from GitHub Issue #N. Title substring: auto-grooming, RT-ICA gate, GitHub sync, SAM planning. '--auto {title}': autonomous mode — no AskUserQuestion, derives data from research files, logs decisions. 'close {title}': dismiss without completion — reason required (duplicate, out_of_scope, superseded, wontfix, blocked). ADR-9. 'resolve {title}': mark DONE with evidence trail — summary required. ADR-9. 'setup-github': init labels, project, milestone. '--language' and '--stack' select Layer 1/2 profile. STOPS if item has Plan field or RT-ICA returns BLOCKED."
argument-hint: '[#N | --auto {title} | --language {lang} | --stack {stack} | item-title-substring | close {title} | resolve {title} | setup-github]'
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

When `$0` is `--auto`, the following substitutions apply at every interactive decision point:

| Normal behaviour | `--auto` substitution |
|---|---|
| No title given (`$1` is empty) | Scan `.claude/backlog/` per-item files for P0 then P1 items that have status `needs-grooming` or `groomed` (not `done`, `resolved`, or `closed`). Log `[AUTO] No title — auto-selected: {title}`, use that item's title as the working title and proceed. If no open P0/P1 item exists, log `[AUTO] STOP — no open P0/P1 items found` and stop. |
| Step 1b: issue not found | Log `[AUTO] STOP — Issue #N not found`, stop |
| Step 1: zero matches → ask user to create | Auto-invoke `create-backlog-item --auto {title}`, log `[AUTO] No item found — invoking create-backlog-item --auto` |
| Step 1: multiple matches → ask user to pick | Log `[AUTO] Multiple matches — picking first: {title}`, proceed with first match |
| Step 2.5: offer GitHub issue for P0/P1 | Log `[AUTO] Skipping GitHub issue offer`, continue without issue |
| Step 2.5: ask milestone assignment | Log `[AUTO] Skipping milestone assignment`, skip |
| RT-ICA BLOCKED | Log `[AUTO] STOP — RT-ICA BLOCKED: {missing inputs}`, stop (cannot resolve without human) |
| Any other `AskUserQuestion` | Log `[AUTO] Decision: {chosen option} — reason: {evidence}`, proceed with logged choice |

`--auto` does NOT change the behaviour of Steps 3–8 (grooming, RT-ICA evaluation, SAM planning, backlog update) — those are already agent-executable without human input.

## Workflow

### Routing (evaluated first, before any step)

Dispatch based on `$0` (the first argument word) before executing any step:

| `$0` value | Title source | Route |
|---|---|---|
| (empty) | — | Step 0 — interactive browser |
| `#N` (starts with `#`) | issue number | Step 1b — Issue-first path |
| bare number (e.g. `249`) | issue number | Step 1b — Issue-first path |
| GitHub issue URL | issue number from URL | Step 1b — Issue-first path |
| `--auto` | `$1`+ joined (empty → auto-select first open P0/P1) | AUTO_MODE=true → Step 1 |
| `close` | `$1`+ joined (title, `#N`, number, or URL) | Step 9 (close path — dismiss without completion) |
| `resolve` | `$1`+ joined (title, `#N`, number, or URL) | Step 9 (resolve path — mark completed with evidence) |
| `setup-github` | — | setup-github command |
| (any other) | `$ARGUMENTS` | Title substring → Step 1 (interactive mode) |

**AUTO_MODE** — when set, all `AskUserQuestion` calls are replaced with evidence-derived decisions. See the `--auto mode rules` table in the Arguments section for each substitution.

### Step 0: Interactive Browser (no arguments only)

**Trigger:** `$0` is empty (no arguments passed).

<step0_procedure>

1. Call the `mcp__backlog__backlog_list` tool with `with_status=true`.

   **If this call fails with "No such tool available" or any tool-not-found error, STOP immediately and report:**

   ```text
   PROCESS ERROR — cannot proceed

   Task requested:  Interactive backlog browser
   Action taken:    mcp__backlog__backlog_list(with_status=true)
   Error received:  [exact error text from the failed call]
   Missing component: backlog MCP server (tools: mcp__backlog__backlog_list, mcp__backlog__backlog_view, etc.)
   Required action: Ensure the backlog MCP server is running and registered in your Claude Code MCP configuration before invoking this skill.
   ```

   Do NOT fall back to reading `.claude/backlog/` files directly. Do NOT delegate to the Explore agent to parse local files. The local files are a cache — they may be stale, incomplete, or missing entries that exist only in GitHub. Presenting them as the authoritative list without stating the MCP failure misleads the user.

   Parse the returned dict. Each entry in `items` has `section`, `title`, `issue`, `plan`, `status`, `milestone`, `file_path` (index format), `groomed` (true if item has groomed content).

2. **Groomed** = item has `groomed: true` in JSON, or `## Groomed` section in its per-item file (`.claude/backlog/{priority}-{slug}.md`). Read the item file; if groomed sections present, use them.

3. Present a numbered list. Use these status indicators in user-visible output only:

   ```text
   Backlog Items:

   P0
     1. ✅ SAM: Error Recovery / Rollback Procedures       [#12  status:in-progress  v1.0]
     2. 🔍 SAM: Regex False Positive Suppression           [#14  status:needs-grooming  v1.0]

   P1
     3. 📋 SAM: Validate Task File Schema                  [no issue]
     4. 📋 SAM: Implement Feature Dry-Run Mode             [no issue]

   P2
     5. 🔍 SAM: Context Window Budget Tracking             [#18  status:needs-grooming  —]

   Ideas
     6. 📋 SAM: Multi-Repo Support                         [no issue]

   Status: ✅ = planned/in-progress  🔍 = groomed/needs-grooming  📋 = not yet groomed

   Options:
     [number]   — Select item to work on
     G [number] — Groom a specific item
     G all      — Groom all ungroomed items
     D [number] — Show full details for an item
   ```

4. Use `AskUserQuestion` to ask: "Which item would you like to work on next?"

5. Handle the response:
   - `[number]` — use that item's title as the working title and proceed to Step 1
   - `G [number]` — invoke `Skill(skill="groom-backlog-item", args="{item title}")` then re-display the list
   - `G all` — invoke `Skill(skill="groom-backlog-item", args="all")` then re-display the list
   - `D [number]` — display the full item description, research_first field, and groomed content (if present in the item file under `## Groomed`), then re-display the list
   - `C [number]` — proceed to Step 9 (close path) with that item's title
   - `R [number]` — proceed to Step 9 (resolve path) with that item's title

</step0_procedure>

**Routing:** If `$0` is `close` or `resolve`, extract `$1`+ as the title and jump directly to Step 9.

### Step 1b: Issue-First Path (`#N`, bare number, or GitHub URL)

**Trigger:** `$0` matches `#[0-9]+`, is a bare number, or is a GitHub issue URL (`https://github.com/.../issues/N`).

<issue_first_procedure>

Fetch the issue using the `mcp__backlog__backlog_view` tool (accepts URLs, `#N`, and bare numbers):

Call the `mcp__backlog__backlog_view` tool with `selector="{$0}"`.

If the tool returns a dict with an `error` key, report and stop.
Parse the returned dict. If `state` is `closed`, run the **Completed Issue Discovery** procedure (see below) and stop.

#### Completed Issue Discovery

When an issue is found to be already closed (state `closed`), gather evidence of how it was completed before closing the local backlog item:

1. **Search for commits referencing the issue**:

   ```bash
   git log --oneline --all -20 --grep="#N"
   ```

2. **Search for merged PRs referencing the issue** — call the `mcp__backlog__backlog_view` tool with
   `selector="#{N}"`, then check the `body` field of the returned dict for `"Fixes #N"` or
   `"Closes #N"`.

   Or via git history:
   ```bash
   git log --oneline --all -20 --grep="Fixes #N\|Closes #N"
   ```

3. **Report findings**:

   If commits or PRs are found:

   ```text
   Issue #{N} is already closed.

   Evidence of completion:
   - PR #{pr}: {title} (merged {date})
     URL: {url}
   - Commit {sha}: {message}

   Closing local backlog item with evidence.
   ```

   Then call the `mcp__backlog__backlog_resolve` tool with `selector="{title}"` and
   `summary="Completed via PR #{pr} / commit {sha}"`.

   If no commits or PRs reference the issue:

   ```text
   Issue #{N} is already closed but no commits or PRs reference it.
   The issue may have been closed manually or via external process.

   Options:
   - close: Close the local backlog item (with manual reason)
   - resolve: Mark as no longer applicable
   - reopen: If the work was not actually done, reopen the issue
   ```

   Use `AskUserQuestion` to ask which action to take. In AUTO_MODE, log `[AUTO] STOP — Issue #N closed, no commit/PR evidence found` and stop.

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

Before planning work, verify the described feature/fix hasn't already been implemented while the issue remained open. This catches stale open issues where someone completed the work but forgot to close the ticket.

1. **Search for commits matching the item's topic** (use keywords from the title):

   ```bash
   git log --oneline --all -30 --grep="{keyword from title}"
   ```

2. **Search for merged PRs matching the topic** (via git log):

   ```bash
   git log --oneline --all -30 --grep="{keyword}"
   ```

3. **Spot-check the codebase** — read the file(s) at the suggested location and verify whether the described behavior already exists.

If evidence shows the work is already done:

- **Mark the item resolved** — call the `mcp__backlog__backlog_resolve` tool with
  `selector="{title}"` and `summary="Already implemented via commit {sha}"`.

- **If a PR is also found** — call the `mcp__backlog__backlog_resolve` tool with
  `selector="{title}"` and `summary="Already implemented via PR #{pr} / commit {sha}"`.

- Report to the user and stop — no planning needed.

In AUTO_MODE: log `[AUTO] Work already implemented — closing #{N} with evidence: {sha/PR}` and stop.

If no evidence of prior implementation is found, proceed to Step 2.5 (GitHub Issue Sync).

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

Build the feature request string for `add-new-feature`. If `--stack` was specified, append a "Stack profile" line to the feature request. If `--language` was specified and is not `python`, invoke the corresponding language plugin (e.g., `/typescript-development:add-new-feature` for `typescript`).

```text
## Backlog Item: {title}

**Source**: {source}
**Priority**: {priority section — P0/P1/P2/Ideas}
**Added**: {added date}

### Description

{description text}

### Research Questions

{research_first text, or "None" if absent}

### Suggested Location

{suggested_location text, or "To be determined during architecture phase" if absent}

### RT-ICA Assessment

**Decision**: APPROVED
**Goal**: {goal statement}
**Verified conditions**: {list of AVAILABLE items}
**Assumptions to confirm**: {list of DERIVABLE items, or "None"}

### Grooming Context

{full context manifest from Step 3, if available}

### Stack Profile (optional)

{stack profile name if --stack specified, e.g., python-fastapi}
```

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

`.claude/backlog/` per-item files are the local cache. GitHub Issues are the source of truth. They are linked — when you work a P0/P1 backlog item, a GitHub Issue is created and kept in sync.

```text
.claude/backlog/    →  GitHub Issue
  metadata.priority →  priority:* label
  Description       →  Issue body (story format)
  metadata.status   →  status:* label
  metadata.plan     →  Issue body Notes
  metadata.issue    ←  written back after creation
  metadata.status   →  Issue closed
```

Full step-by-step commands and example sessions: [github-integration.md](./references/github-integration.md)

### Commit Messages and PR Body — `Fixes #N`

When implementing a backlog item that has a linked GitHub Issue (`**Issue**: #N`), **every commit and the PR description MUST reference the issue** so GitHub auto-closes it on merge:

- **Commit messages**: end the subject line with `(fixes #N)` or add a `Fixes #N` footer in the body:
  ```text
  fix(perl-development): replace shell injection in run_command (fixes #80)
  ```
  or
  ```text
  fix(perl-development): replace shell injection in run_command

  Fixes #80
  ```
- **PR description**: include at least one `Fixes #N` line in the PR body so GitHub links and auto-closes the issue when the PR is merged.
- When a PR fixes **multiple issues**, list each on a separate line:
  ```text
  Fixes #80
  Fixes #83
  ```
- Use `Fixes` (not `Closes`) for bugs and security issues; either works for feature work.

This convention ensures issues are automatically closed on merge without manual intervention.

### Step 2.5: GitHub Issue Sync

After Step 2, check for `**Issue**: #N` field in the matched item.

- Found: verify issue state — call the `mcp__backlog__backlog_view` tool with `selector="#{issue_number}"`
- Not found + P0/P1: offer to create a GitHub Issue (proceed to Step 2.5a)
- Not found + P2/Ideas: skip silently

### Step 2.5a: Create GitHub Issue

Call the `mcp__backlog__backlog_update` tool with `selector="{title}"` and `create_issue=true`.

Check the returned dict for an `error` key. On success, the tool creates the issue and writes `issue: '#N'` back to the per-item file frontmatter.

### Step 2.7: Set In-Progress Label

If the item has `**Issue**: #N`, call the `mcp__backlog__backlog_update` tool with `selector="{title}"` and `status="in-progress"`.

If the item is in a milestone with other issues, also run `milestone start` for the milestone:

```bash
uv run .claude/skills/gh/scripts/github_project_setup.py milestone start \
  --number {milestone_number} --repo Jamie-BitFlight/claude_skills
```

### setup-github Command

**Trigger:** `$0` is `setup-github`. Initializes label taxonomy, first milestone, and GitHub Project.

```bash
uv run .claude/skills/gh/scripts/github_project_setup.py labels --repo Jamie-BitFlight/claude_skills
uv run .claude/skills/gh/scripts/github_project_setup.py milestone create \
  --title "v1.0 — Skills Foundation" --due 2026-03-31 --repo Jamie-BitFlight/claude_skills
```

Full setup steps and expected output: [github-integration.md](./references/github-integration.md)

## Error Handling

- `#N` / URL / bare number not found: report and list available items — call the `mcp__backlog__backlog_list` tool
- `#N` already closed: run Completed Issue Discovery (search commits/PRs for evidence, close local item with reference, or ask user)
- `close #N` / `resolve #N` — issue not found: report and stop
- Item not found: list available items from `.claude/backlog/` per-item files with their priority sections
- Multiple matches: present numbered list, ask user to choose
- Grooming fails: proceed without grooming context, note the gap in the feature request
- RT-ICA returns BLOCKED: present missing inputs, wait for user, do not invoke `add-new-feature`
- `add-new-feature` fails: report the failure, do not update per-item file
- Plan file not found after planning: search `plan/` directory broadly, ask user to confirm the path
- Grooming reports directory does not exist: treat all items as ungroomed
- `close` with invalid reason: reject and show valid reasons (duplicate, out_of_scope, superseded, wontfix, blocked)
- `close` on already-completed item: report closed date, do not re-close
- `resolve` with no `**Plan**:` field: skip checklist verification, proceed to summary collection
- `resolve` with incomplete checklist: list remaining tasks, do not resolve (offer `close` as alternative)
- `resolve` with verification FAIL: report gaps, do not resolve
- `resolve` with no summary provided: block until user provides summary (summary is required evidence)
- GitHub issue creation fails: report error, continue with per-item-file-only workflow; do not block SAM planning
- `GITHUB_TOKEN` not set: backlog MCP tools report an error; local-only operations still work
- Label not found during issue create: `github_project_setup.py` creates it automatically
- Milestone not found: skip milestone assignment; do not fail

## Example Sessions

### Issue-first planning (`#N`)

```text
> /work-backlog-item #131

Loading GitHub Issue #131...
  Title:     plugin-validator: UX and coverage gaps
  Labels:    priority:p1, status:needs-grooming
  Milestone: v1.1 — Quality Gates
  State:     open

Matched per-item file for additional context: ✓
No groomed content in item file. Running groom-backlog-item first...

[groomed content written to item file]

RT-ICA: APPROVED — all conditions available.
Setting status:in-progress on issue #131...
  ✓ status:needs-grooming → status:in-progress

Composing feature request...
Invoking /add-new-feature...

[SAM phases run]

Updated per-item file with Plan: plan/tasks-2-validator-ux-coverage.md

Next steps:
- To execute:      /implement-feature validator-ux-coverage
- To close when done: /work-backlog-item close plugin-validator UX and coverage gaps
```

### Planning (with title substring)

```text
> /work-backlog-item Error Recovery

Found: "SAM: Error Recovery / Rollback Procedures" (P1)
No groomed content in item file. Running groom-backlog-item first...

[groomed content written to item file]

RT-ICA: APPROVED — all conditions available.
Composing feature request...
Invoking /add-new-feature...

[SAM phases run]

Updated per-item file with Plan: plan/tasks-2-error-recovery.md

Next steps:
- To execute:      /implement-feature error-recovery
- To check status: /implementation-manager status . error-recovery
- To close when done: /work-backlog-item close error-recovery
```

### Resolving a completed item (by title)

```text
> /work-backlog-item resolve validator UX

Found: "plugin-validator UX and coverage gaps" (P1)
Plan: plan/tasks-2-validator-ux-coverage.md
Checklist: 12/12 tasks complete

Spawning acceptance criteria verification agent...

Verdict: PASS
Evidence: Sub-issues 1-4 implemented in plugins/plugin-creator/scripts/plugin_validator.py
          commit 4a2f1b3 — "fix(validator): report unique files, add hook validation"

Summarize what was done:
> Implemented all 4 sub-issues: unique file reporting, hook validation, coverage gaps filled.

Backlog item "plugin-validator UX and coverage gaps" resolved.
- Summary: Implemented all 4 sub-issues: unique file reporting, hook validation, coverage gaps filled.
- Checklist: 12/12 tasks complete
- Acceptance criteria: PASS
- GitHub Issue #131 closed with evidence trail
```

### Resolving a completed item (by issue number)

```text
> /work-backlog-item resolve #131

Fetching GitHub Issue #131...
  Title: plugin-validator UX and coverage gaps
  State: open

Found per-item file match: "plugin-validator UX and coverage gaps" (P1)
Plan: plan/tasks-2-validator-ux-coverage.md
Checklist: 12/12 tasks complete

Spawning acceptance criteria verification agent...

Verdict: PASS
Evidence: commit 4a2f1b3 — "fix(validator): report unique files, add hook validation"

Summarize what was done:
> All validator sub-issues implemented and tested.

Backlog item "plugin-validator UX and coverage gaps" resolved.
- Summary: All validator sub-issues implemented and tested.
- GitHub Issue #131 closed with evidence trail
```

### Closing (dismissing) an item

```text
> /work-backlog-item close commitlint verify last flag

Found: "commitlint: Verify --last flag and exit codes against primary sources" (P1)
Why is this item being dismissed?
> out_of_scope
Any additional comment?
> REFUTED by fact-check: --last flag verified against commitlint source cli.ts. No fix needed.

Backlog item closed.
  Closed: 2026-02-21
  Reason: out_of_scope
  Comment: REFUTED by fact-check: --last flag verified against commitlint
           source cli.ts and official docs. No fix needed.
```

GitHub-specific example sessions (issue creation flow and setup-github): [github-integration.md](./references/github-integration.md)

---

## Validation Plan

See [validation-plan.md](./references/validation-plan.md) for V1–V6 verification commands and the full integration test sequence.
