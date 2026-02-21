---
name: work-backlog-item
description: "Bridges BACKLOG.md to the SAM planning pipeline. No args: interactive browser. With title substring: auto-grooming, RT-ICA gate, SAM planning, plan reference recorded. 'close {title}': verifies plan checklist 100% complete, spawns acceptance-criteria agent, marks DONE on pass. 'resolve {title}': marks item no longer applicable with reason. STOPS if item has existing Plan field or RT-ICA returns BLOCKED."
argument-hint: '[item-title-substring | close {title} | resolve {title}]'
user-invocable: true
---
# Work Backlog Item

Bridge a `.claude/BACKLOG.md` item into the SAM planning pipeline via `/python3-development:add-new-feature`, then record the resulting plan file back in BACKLOG.md.

When invoked with no arguments, shows an interactive backlog browser. When invoked with a title substring, proceeds directly to the planning workflow.

## Arguments

`$ARGUMENTS` is one of:

- **Empty** — interactive browser
- **Title substring** — case-insensitive match against H3 headings; triggers planning workflow
- **`close {title}`** — verify and close a completed item
- **`resolve {title}`** — mark an item as no longer applicable (with reason)

```text
/work-backlog-item                         # interactive browser
/work-backlog-item Error Recovery          # direct match → planning
/work-backlog-item regex false positive    # planning
/work-backlog-item close Error Recovery    # verify and close
/work-backlog-item resolve commitlint      # mark no longer applicable
```

## Workflow

### Step 0: Interactive Browser (no arguments only)

**Trigger:** `$ARGUMENTS` is empty.

<step0_procedure>

1. Read `.claude/BACKLOG.md`. Parse all H3 headings (`### ...`) from P0, P1, P2, and Ideas sections. Record each item's priority section and title.

2. For each item, determine grooming status:
   - **Has plan** — item has a `**Plan**:` field in BACKLOG.md
   - **Groomed** — `.claude/grooming-reports/` contains a file whose content references the item title (search with Grep)
   - **Ungroomed** — neither condition above is true

3. Present a numbered list. Use these status indicators in user-visible output only:

   ```text
   Backlog Items:

   P0
     1. ✅ SAM: Error Recovery / Rollback Procedures
     2. 🔍 SAM: Regex False Positive Suppression

   P1
     3. 📋 SAM: Validate Task File Schema
     4. 📋 SAM: Implement Feature Dry-Run Mode

   P2
     5. 🔍 SAM: Context Window Budget Tracking

   Ideas
     6. 📋 SAM: Multi-Repo Support

   Status: ✅ = planned  🔍 = groomed  📋 = not yet groomed

   Options:
     [number]   — Select item to work on
     G [number] — Groom a specific item
     G all      — Groom all ungroomed items
     D [number] — Show full details for an item
   ```

4. Use `AskUserQuestion` to ask: "Which item would you like to work on next?"

5. Handle the response:
   - `[number]` — set `$ARGUMENTS` to that item's title and proceed to Step 1
   - `G [number]` — invoke `Skill(skill="groom-backlog-item", args="{item title}")` then re-display the list
   - `G all` — invoke `Skill(skill="groom-backlog-item", args="all")` then re-display the list
   - `D [number]` — display the full item description, research_first field, and grooming manifest if it exists in `.claude/grooming-reports/`, then re-display the list
   - `C [number]` — set `$ARGUMENTS` to `close {item title}` and proceed to Step 9
   - `R [number]` — set `$ARGUMENTS` to `resolve {item title}` and proceed to Step 9

</step0_procedure>

**Routing:** If `$ARGUMENTS` starts with `close` or `resolve`, extract the title substring and jump directly to Step 9.

### Step 1: Find the Backlog Item

Read `.claude/BACKLOG.md`. Search H3 headings (`### ...`) for case-insensitive match against `$ARGUMENTS`.

- Zero matches: report "No backlog item found matching: {$ARGUMENTS}" and stop.
- Multiple matches: list all matches and ask the user to pick one.

Record the priority section (P0, P1, P2, Ideas) the item belongs to.

### Step 2: Extract Item Fields

From the matched item, extract these fields (all are `**bold-key**: value` format on separate lines):

- `title` — the H3 heading text (required)
- `source` — `**Source**:` value (optional)
- `added` — `**Added**:` value (optional)
- `description` — `**Description**:` value (required)
- `research_first` — `**Research first**:` value (optional)
- `suggested_location` — `**Suggested location**:` value (optional)
- `plan` — `**Plan**:` value (optional)

If the item already has a `**Plan**:` field, report:

```text
This item already has a plan at {path}. Use /python3-development:implement-feature {path} to execute it.
```

Then stop.

### Step 3: Auto-Groom (if needed)

<groom_check>

1. Search `.claude/grooming-reports/` for files whose content references the item title (use Grep)
2. Search conversation context for a recent `groom-backlog-item` output matching this item.

If no grooming report exists:

```text
Skill(command: "groom-backlog-item", args: "{item title}")
```

Capture the grooming output — context manifest with Related Research, Supporting Skills, Related Agents, Prior Work, Dependencies, Blockers, Suggested First Steps.
</groom_check>

### Step 4: RT-ICA Checkpoint

<rtica_gate>
Before composing the feature request, verify the grooming context manifest contains an RT-ICA summary. If absent, perform RT-ICA now:

1. **Goal statement** — What completing this item achieves.
2. **Reverse prerequisites** — Conditions required for success (enumerate each).
3. **Availability check** — For each condition: AVAILABLE / DERIVABLE / MISSING.
4. **Decision** — APPROVED or BLOCKED.

**If BLOCKED:**

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

Build the `$ARGUMENTS` string for `add-new-feature`:

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
```

### Step 6: Invoke SAM Planning

```text
Skill(command: "python3-development:add-new-feature", args: "{composed feature request}")
```

This runs the full SAM workflow: discovery, codebase analysis, architecture spec, task decomposition, validation, context manifest.

### Step 7: Update Backlog with Plan Reference

After `add-new-feature` completes, identify the task file it created:

```text
Glob(pattern="plan/tasks-*-{slug}*")
```

Where `{slug}` is the item title lowercased with spaces replaced by hyphens.

Add a `**Plan**:` field to the backlog item in `.claude/BACKLOG.md`:

```text
### SAM: {item title}

**Source**: {source}
**Added**: {added date}
**Plan**: plan/tasks-{N}-{slug}.md
**Description**: {description}
```

Update `last-updated:` in the BACKLOG.md YAML frontmatter to today's date.

### Step 8: Report Next Steps

```text
Backlog item "{title}" is now planned.

- Plan file: plan/tasks-{N}-{slug}.md (or plan/tasks-{N}-{slug}/ directory)
- To execute:      /python3-development:implement-feature {slug}
- To check status: /python3-development:implementation-manager status . {slug}
- To close when done: /work-backlog-item close {slug}
```

### Step 9: Verify and Close

**Trigger:** `$ARGUMENTS` starts with `close` or `resolve`.

<step9_procedure>

Extract the operation and title substring from `$ARGUMENTS`:

- `close {title}` → verify implementation and mark COMPLETED
- `resolve {title}` → mark no longer applicable (no verification required)

#### 9a: Find Item

Read `.claude/BACKLOG.md`. Search H3 headings for case-insensitive match against `{title}`.

- Zero matches: report "No backlog item found matching: {title}" and stop.
- Multiple matches: list all matches and ask user to pick one.
- Item already in `## Completed` section: report "Item already closed on {Completed date}" and stop.

#### 9b: Resolve path (skip verification)

If operation is `resolve`:

1. Use `AskUserQuestion` to ask: "Why is this item no longer applicable?" (free text)
2. Update the matched item in `.claude/BACKLOG.md`:

```text
### {original title}

**Source**: {source}
**Added**: {added}
**Resolved**: {YYYY-MM-DD}
**Status**: RESOLVED — {user-provided reason}
**Description**: {description}
```

3. Update `last-updated:` in BACKLOG.md YAML frontmatter to today's date.
4. Report:

```text
Backlog item "{title}" resolved.
Reason: {reason}
```

Then stop.

#### 9c: Close path — checklist verification

If operation is `close`:

1. Extract `**Plan**:` field from the matched item. If absent:

```text
No plan file recorded for "{title}". Cannot verify checklist.
Either run /work-backlog-item {title} first to create a plan,
or use /work-backlog-item resolve {title} if no plan was needed.
```

Then stop.

2. Read the plan file. Count:
   - `total_tasks` — lines matching `- \[ \]` or `- \[x\]`
   - `checked_tasks` — lines matching `- \[x\]`

3. If `checked_tasks < total_tasks`:

```text
Checklist incomplete: {checked_tasks}/{total_tasks} tasks done.

Remaining:
{list of unchecked task lines}

Complete all tasks before closing this item.
```

Then stop.

#### 9d: Close path — acceptance criteria verification

4. Spawn a verification agent:

```text
Task(
  subagent_type: "general-purpose",
  prompt: "You are verifying whether a completed backlog item genuinely satisfies its stated goal.

Backlog item title: {title}
Description and acceptance criteria:
{description text from BACKLOG.md}

Plan file: {plan file path}
Plan checklist: {checked_tasks}/{total_tasks} — 100% complete.

Your task:
1. Read the plan file to understand what was implemented.
2. Search git log for commits referencing this item (use: git log --oneline -20).
3. Read 2-3 key changed files to verify the implementation exists.
4. Assess: Does the implementation satisfy the stated goal? Is the product better for it?

Return:
- PASS or FAIL
- One sentence of evidence (file:line or commit SHA)
- Any gaps you found (if FAIL)"
)
```

5. Collect agent verdict:
   - **PASS**: proceed to 9e
   - **FAIL**: report gaps, do not close:

```text
Verification FAILED for "{title}".

Gaps found:
{agent findings}

Address these gaps before closing.
```

Then stop.

#### 9e: Write closing record

6. Update the matched item in `.claude/BACKLOG.md`:

```text
### {original title}

**Source**: {source}
**Added**: {added}
**Completed**: {YYYY-MM-DD}
**Status**: DONE — verified by checklist ({checked}/{total}) + acceptance criteria check
**Plan**: {plan file path}
**Description**: {description}
```

7. Update `last-updated:` and `last-completed:` in BACKLOG.md YAML frontmatter to today's date.

8. Report:

```text
Backlog item "{title}" closed.

- Checklist: {checked}/{total} tasks complete
- Acceptance criteria: PASS
- Status written to BACKLOG.md
```

</step9_procedure>

## Error Handling

- Item not found: list available items from BACKLOG.md with their priority sections
- Multiple matches: present numbered list, ask user to choose
- Grooming fails: proceed without grooming context, note the gap in the feature request
- RT-ICA returns BLOCKED: present missing inputs, wait for user, do not invoke `add-new-feature`
- `add-new-feature` fails: report the failure, do not update BACKLOG.md
- Plan file not found after planning: search `plan/` directory broadly, ask user to confirm the path
- Grooming reports directory does not exist: treat all items as ungroomed
- `close` with no `**Plan**:` field: report and offer `resolve` as alternative
- `close` with incomplete checklist: list remaining tasks, do not close
- `close` with verification FAIL: report gaps, do not close
- `close` on already-completed item: report closed date, do not re-close
- `resolve` with no reason provided: block until user provides reason (reason is required evidence)

## Example Sessions

### Planning (with argument)

```text
> /work-backlog-item Error Recovery

Found: "SAM: Error Recovery / Rollback Procedures" (P1)
No grooming manifest found. Running groom-backlog-item first...

[grooming output]

RT-ICA: APPROVED — all conditions available.
Composing feature request...
Invoking /python3-development:add-new-feature...

[SAM phases run]

Updated BACKLOG.md with Plan: plan/tasks-2-error-recovery.md

Next steps:
- To execute:      /python3-development:implement-feature error-recovery
- To check status: /python3-development:implementation-manager status . error-recovery
- To close when done: /work-backlog-item close error-recovery
```

### Closing a completed item

```text
> /work-backlog-item close validator UX

Found: "plugin-validator UX and coverage gaps" (P1)
Plan: plan/tasks-2-validator-ux-coverage.md
Checklist: 12/12 tasks complete

Spawning acceptance criteria verification agent...

Verdict: PASS
Evidence: Sub-issues 1-4 implemented in plugins/plugin-creator/scripts/plugin_validator.py
          commit 4a2f1b3 — "fix(validator): report unique files, add hook validation"

Backlog item "plugin-validator UX and coverage gaps" closed.
- Checklist: 12/12 tasks complete
- Acceptance criteria: PASS
- Status written to BACKLOG.md
```

### Resolving a no-longer-applicable item

```text
> /work-backlog-item resolve commitlint verify last flag

Found: "commitlint: Verify --last flag and exit codes against primary sources" (P1)
Why is this item no longer applicable?
> REFUTED by fact-check: --last flag is verified in commitlint source cli.ts. No fix needed.

Backlog item resolved.
  Resolved: 2026-02-21
  Status: RESOLVED — REFUTED by fact-check: --last flag verified against commitlint
          source cli.ts and official docs. No fix needed.
```
