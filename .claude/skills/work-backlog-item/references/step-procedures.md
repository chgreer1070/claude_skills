# Step Procedures Reference

Detailed procedure content for Steps 0, Q, P, R, and the feature request template.

---

## Step 1b: Completed Issue Discovery

When an issue is found to be already closed (`state: closed`), gather evidence before closing the local backlog item:

1. **Search for commits referencing the issue**:

   ```bash
   git log --oneline --all -20 --grep="#N"
   ```

2. **Search for merged PRs via git history**:

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

   Call the `mcp__backlog__backlog_resolve` tool with `selector="{title}"` and
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

   Use `AskUserQuestion` to ask which action to take. In AUTO_MODE, log
   `[AUTO] STOP — Issue #N closed, no commit/PR evidence found` and stop.

---

## Step 2.3: Already Implemented Check

Before planning work, verify the described feature/fix hasn't already been implemented:

1. **Search for commits matching the item's topic** (use keywords from the title):

   ```bash
   git log --oneline --all -30 --grep="{keyword from title}"
   ```

2. **Search for merged PRs matching the topic**:

   ```bash
   git log --oneline --all -30 --grep="{keyword}"
   ```

3. **Spot-check the codebase** — read the file(s) at the suggested location and verify whether the described behavior already exists.

If evidence shows the work is already done:

- Call the `mcp__backlog__backlog_resolve` tool with `selector="{title}"` and
  `summary="Already implemented via PR #{pr} / commit {sha}"`.
- Report to the user and stop — no planning needed.

In AUTO_MODE: log `[AUTO] Work already implemented — closing #{N} with evidence: {sha/PR}` and stop.

If no evidence, proceed to Step 2.5 (GitHub Issue Sync).

---

## Step 0: Interactive Browser

1. Call the `mcp__backlog__backlog_list` tool with `with_status=true`.

   Parse the returned dict. Each entry in `items` has `section`, `title`, `issue`, `plan`, `status`, `milestone`, `file_path` (index format), `groomed` (true if item has groomed content).

2. **Groomed** = item has `groomed: true` in JSON, or `## Groomed` section in its per-item file (`.claude/backlog/{priority}-{slug}.md`). Read the item file; if groomed sections present, use them.

3. Present a numbered list. Use these status indicators in user-visible output only:

   <eg>
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
</eg>

4. Use `AskUserQuestion` to ask: "Which item would you like to work on next?"

5. Handle the response:
   - `[number]` — use that item's title as the working title and proceed to Step 1
   - `G [number]` — invoke `Skill(skill="groom-backlog-item", args="{item title}")` then re-display the list
   - `G all` — invoke `Skill(skill="groom-backlog-item", args="all")` then re-display the list
   - `D [number]` — display the full item description, research_first field, and groomed content (if present in the item file under `## Groomed`), then re-display the list
   - `C [number]` — proceed to Step 9 (close path) with that item's title
   - `R [number]` — proceed to Step 9 (resolve path) with that item's title

---

## Step 5: Feature Request Template

Build this string for `add-new-feature`:

<eg>
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
</eg>

If `--stack` was specified, append a "Stack profile" line. If `--language` was specified and is not `python`, invoke the corresponding language plugin (e.g., `/typescript-development:add-new-feature` for `typescript`).

---

## Step Q: Quick Mode

**Trigger:** `$0` is `--quick`. Skips grooming, RT-ICA, and SAM planning. For one-file fixes, broken links, and typo patches where full pipeline overhead is disproportionate.

1. Extract title from `$1`+ joined. Build slug: title lowercased, spaces → hyphens.

2. Find the item in `.claude/backlog/` per-item files (same logic as Step 1). If not found, create a minimal item with the title.

3. Extract the item's description and acceptance criteria if available.

4. Write the plan to `plan/quick/{slug}.md` with frontmatter `type: quick`, fields: `title`, `priority`, `issue`, `created`. Body sections: `## Task` (description), `## Steps` (1-3 checklist items derived from description), `## Done When` (acceptance_criteria if present, else goal from description).

5. Call the `mcp__backlog__backlog_update` tool with `selector="{title}"` and `plan="plan/quick/{slug}.md"` to record the plan.

6. Report:

   <eg>
   Quick plan created: plan/quick/{slug}.md
   Steps: {N} tasks

   To execute: /implement-feature plan/quick/{slug}.md
   To close:   /work-backlog-item close {title}
   </eg>

---

## Step P: Progress Report

**Trigger:** `$0` is `progress`.

1. Scan `.claude/backlog/` per-item files. Count items by priority (P0, P1, P2, Ideas) and status (done, resolved, closed).

2. Query GitHub for the active milestone:

   ```bash
   gh api repos/Jamie-BitFlight/claude_skills/milestones --jq '[.[] | select(.state=="open")] | sort_by(.due_on) | first'
   ```

   Extract: milestone number, title, open_issues, closed_issues.

3. For items in the active milestone, identify the highest-priority groomed item with no `**Plan**:` field — that is the recommended next action.

4. Display:

   <eg>
   Backlog Health — {YYYY-MM-DD}

   Active Milestone: #{N} {title}
     Closed:      {closed_issues} items
     Open:        {open_issues} items
     Progress:    [{####......}] {pct}%

   Overall Backlog:
     P0:    {n} items ({m} in milestone)
     P1:    {n} items ({m} in milestone, {k} groomed but unassigned)
     P2:    {n} items
     Ideas: {n} items

   Next recommended action:
     /work-backlog-item {title}  — {title} (P{x}, groomed, in active milestone)
   </eg>

   If no active milestone exists, omit the milestone section and show only Overall Backlog counts.

   If the backlog directory is empty, note: `(no backlog items found)`

---

## Step R: Resume Report

**Trigger:** `$0` is `resume`.

1. Extract title from `$1`+ joined. If `$1` starts with `#`, fetch title from GitHub Issue (same logic as Step 1b).

2. Find the item in `.claude/backlog/` per-item files. Extract `metadata.plan` field. If absent:

   <eg>
   No plan file recorded for "{title}".
   Run /work-backlog-item {title} to create a plan first.
   </eg>

   Then stop.

3. Read the plan file. Parse the checklist:
   - `total_tasks` — lines matching `- \[[ x]\]`
   - `checked_tasks` — lines matching `- \[x\]`
   - `last_checked` — last line matching `- \[x\]` (trim the `- [x]` prefix)
   - `first_unchecked` — first line matching `- \[ \]` (trim the `- [ ]` prefix)

4. Compute `completion_pct = checked_tasks * 100 / total_tasks` (integer).

5. Report:

   <eg>
   Resume: {title}
   Plan:   {plan file path}

   Progress: {checked_tasks}/{total_tasks} tasks ({completion_pct}%)

   Last completed:  {last_checked task text}
   Next to do:      {first_unchecked task text}

   To continue: /implement-feature {slug}
   To close:    /work-backlog-item close {title}
   </eg>

   If `checked_tasks == 0`, report "No tasks completed yet."
   If `checked_tasks == total_tasks`, report "All tasks complete — run /work-backlog-item close {title}."
