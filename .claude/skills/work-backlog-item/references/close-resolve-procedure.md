# Close / Resolve Procedure (ADR-9)

Full Step 9 workflow. Trigger: `$0` is `close` or `resolve`.

Extract the operation from `$0` and the argument from `$1`+:

- `$0` = `close`: `$1`+ = title, `#N`, bare number, or URL → dismiss without completion (reason required)
- `$0` = `resolve`: `$1`+ = title, `#N`, bare number, or URL → mark DONE with evidence trail (summary required)

## 9a: Find Item

Call the `mcp__backlog__backlog_view` tool with `selector="{$1}"` (accepts URLs, `#N`, bare numbers, and title substrings).

- If the returned dict contains an `error` key, report and stop.
- Extract `title` from the returned dict and use it as the working title.

If the view command found a local file (`file_path` in JSON), use it. Otherwise scan `.claude/backlog/` per-item files for a title match.

- Zero matches: report "No backlog item found matching: {$1}" and stop.
- Multiple matches: list all matches and ask user to pick one.
- Item already in `## Completed` section: report "Item already closed on {Completed date}" and stop.

## 9b: Close path — dismiss without completion

If operation is `close`:

1. Use `AskUserQuestion` to ask: "Why is this item being dismissed?" with options:
   - `duplicate` — Another item covers the same work
   - `out_of_scope` — Doesn't belong in this project
   - `superseded` — Replaced by a different item or approach
   - `wontfix` — Deliberate decision not to do this
   - `blocked` — Permanently blocked, cannot proceed

2. If the user selected `duplicate` or `superseded`, ask for a reference: "Which item does this duplicate / is this superseded by?" (free text — accepts `#N`, URL, or title).

3. Optionally ask for additional context: "Any additional comment?" (free text, can be skipped).

4. Call the `mcp__backlog__backlog_close` tool:

   - `selector`: `"{title}"` or `"#{N}"`
   - `reason`: `"{selected reason}"`
   - `reference`: `"{reference}"` (if provided)
   - `comment`: `"{comment}"` (if provided)

5. Check the returned dict for an `error` key. Report the result to the user.

Then stop.

## 9c: Resolve path — checklist verification

If operation is `resolve`:

1. Extract `**Plan**:` field from the matched item. If absent, skip to 9e (no plan = simple resolve with summary only).

2. Read the plan file. Count:
   - `total_tasks` — lines matching `- \[ \]` or `- \[x\]`
   - `checked_tasks` — lines matching `- \[x\]`

3. If `checked_tasks < total_tasks`:

<eg>
Checklist incomplete: {checked_tasks}/{total_tasks} tasks done.

Remaining:
{list of unchecked task lines}

Complete all tasks before resolving, or use /work-backlog-item close {title} to dismiss.
</eg>

Then stop.

## 9d: Resolve path — typed acceptance-criteria verification

4. Extract `**Acceptance Criteria**:` from the per-item file (`.claude/backlog/{priority}-{slug}.md`) or from the backlog item body. The field format is a bullet list following the header:

   ```markdown
   **Acceptance Criteria**:
   - {criterion 1}
   - {criterion 2}
   - {criterion 3}
   ```

   Parse each `-` line as a separate criterion.

5. Spawn a verification agent with subagent_type="general-purpose". Prompt must include: item title, plan file path, checklist status (100%), and each criterion listed individually as "Criterion N: {text}". Instruct the agent to: read the plan file, search `git log --oneline -20`, check relevant files for each criterion, and return per-criterion PASS/FAIL with file:line evidence. Required return format:

   <eg>
   [PASS] {criterion} — verified at {file}:{line} (or commit {sha})
   [FAIL] {criterion} — {gap description}
   Overall: PASS or FAIL (N/M criteria met)
   </eg>

   **If no acceptance criteria exist**: warn "No **Acceptance Criteria**: field found — falling back to description-based verification" and spawn agent with the description as the goal instead.

6. Parse the agent verdict:

   <eg>
   Acceptance Criteria Verification:

     [PASS] running X produces Y — verified at src/main.py:42
     [FAIL] file Z exists with field W — file exists but field W not found
     [PASS] test suite passes — confirmed via git log (commit abc123f)

   Overall: FAIL (2/3 criteria met)
   </eg>

7. Collect agent verdict:
   - **Overall PASS** (all criteria met): proceed to 9e
   - **Overall FAIL** (any criterion failed): report gaps, do not resolve:

<eg>
Verification FAILED for "{title}".

Per-criterion results:
{agent findings}

Address the failing criteria before resolving, or use /work-backlog-item close {title} to dismiss.
</eg>

Then stop.

## 9e: Check for open PR

8. If the item has a linked GitHub Issue (`#N`), check whether an open PR already references it:

```bash
git log --oneline -20 --grep="Fixes #N\|Closes #N"
```

- **Open PR found**: The PR body contains `Fixes #N` — the issue will auto-close on merge. Update only the local per-item file status (do NOT close the GitHub Issue):

  Call the `mcp__backlog__backlog_update` tool with `selector="{title}"` and `status="in-progress"`.

  Report:

  <eg>
  Backlog item "{title}" verified. GitHub Issue #{N} will auto-close when PR #{pr_number} merges.
  </eg>

  Then stop.

- **No open PR / no linked issue**: proceed to 9f.

## 9f: Invoke backlog resolve

9. Use `AskUserQuestion` to ask: "Summarize what was done (1-2 sentences):" (free text — this is the required `summary` field).

10. Optionally gather additional evidence fields (can be skipped for trivial items):
    - `method` — "How was the work done?"
    - `notes` — "Any problems found or surprises?"
    - `follow_ups` — "Any follow-up tickets created?" (comma-separated refs)
    - `findings` — "Any retrospective learnings?"

11. Call the `mcp__backlog__backlog_resolve` tool:

    - `selector`: `"{title}"` or `"#{N}"`
    - `summary`: `"{summary}"`
    - `plan`: `"{plan file path}"` (if present)
    - `method`: `"{method}"` (if provided)
    - `notes`: `"{notes}"` (if provided)
    - `follow_ups`: `"{follow_ups}"` (if provided)
    - `findings`: `"{findings}"` (if provided)

12. Check the returned dict for an `error` key. Report the result to the user.
