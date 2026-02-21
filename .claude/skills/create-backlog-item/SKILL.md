---
name: create-backlog-item
description: "Create a new item in .claude/BACKLOG.md. No args: guided intake via AskUserQuestion. With 'quick {title}': inline capture from user description. Writes item to correct priority section, updates frontmatter counts, offers GitHub Issue creation for P0/P1. Enforces required fields (title, priority, description) and duplicate detection before writing."
argument-hint: '[quick {title} | <empty for guided intake>]'
user-invocable: true
---
# Create Backlog Item

Capture a new backlog item and append it to `.claude/BACKLOG.md` in the correct priority section.

## Arguments

`$ARGUMENTS` is one of:

- **Empty** — guided intake via `AskUserQuestion` prompts
- **`quick {title}`** — skip title question, ask for description and priority only

```text
/create-backlog-item                        # guided intake
/create-backlog-item quick GitHub milestone skill  # quick entry
```

## Workflow

### Step 1: Collect Item Fields

**If `$ARGUMENTS` is empty (guided intake):**

Use `AskUserQuestion` with two questions:

```text
Question 1: "What is the title of this backlog item?"
  header: "Title"
  options: (free text — no options; user will type)

Question 2: "What priority?"
  header: "Priority"
  options:
    - label: "P0 — Must have"
    - label: "P1 — Should have"
    - label: "P2 — Nice to have"
    - label: "Idea — Not yet sized"
```

Then ask:

```text
Question 3: "Describe the item. Include: what the problem is, what success looks like, and any known constraints or research questions."
  header: "Description"
```

Then ask:

```text
Question 4: "What is the source or trigger for this item? (e.g., code review, user request, session observation — or press Enter to skip)"
  header: "Source"
  options:
    - label: "Code review"
    - label: "User request"
    - label: "Session observation"
    - label: "Research finding"
    - label: "Skip"
```

Then ask:

```text
Question 5: "What type of work is this?"
  header: "Type"
  options:
    - label: "Feature"
    - label: "Bug"
    - label: "Refactor"
    - label: "Docs"
    - label: "Chore"
```

**If `$ARGUMENTS` starts with `quick`:**

Extract title from remainder of `$ARGUMENTS`. Ask only:

- Priority (Question 2 above)
- Description (Question 3 above)

Source defaults to "Session observation". Type defaults to "Feature".

### Step 2: Validate Inputs

Required fields: `title`, `priority`, `description`.

- If any required field is missing or empty: report which field is missing and stop.
- `title` must be non-empty after trimming whitespace.
- `description` must be non-empty after trimming whitespace.

### Step 3: Duplicate Detection

Read `.claude/BACKLOG.md`. Search all H3 headings for case-insensitive overlap with `title`.

If a match is found within edit distance ≤ 2 tokens (same first 3 words), report:

```text
Possible duplicate: "{existing title}" already exists in {section}.
Proceed anyway? (y/n)
```

Use `AskUserQuestion` with Yes / No options. If No: stop.

### Step 4: Compose Item Block

Format today's date as `YYYY-MM-DD` (use system date).

```text
### {title}

**Source**: {source, or "Not specified" if skipped}
**Added**: {YYYY-MM-DD}
**Priority**: {P0|P1|P2|Idea}
**Type**: {type}
**Description**: {description}
```

If research questions were embedded in the description (lines starting with `?` or `Research:`), extract them into a separate `**Research first**:` field:

```text
**Research first**: {extracted questions}
```

### Step 5: Write to BACKLOG.md

Read `.claude/BACKLOG.md`.

Locate the correct section heading:

- P0 → `## P0 - Must Have`
- P1 → `## P1 - Should Have`
- P2 → `## P2 - Nice to Have`
- Idea → `## Ideas`

Insert the item block:

- If section contains `_(Empty)_`: replace that line with the item block.
- Otherwise: append the item block after the last `###` item in the section (before the next `---` or `##` heading).

Update the YAML frontmatter:

- Increment the count field for the relevant priority (`p0-count`, `p1-count`, `p2-count`, `ideas-count`).
- Set `last-updated` to today's date.

### Step 6: Confirm Write

Report:

```text
Backlog item created.

  Title:    {title}
  Priority: {priority}
  Section:  {section heading}
  Added:    {date}

Next steps:
  Groom:  /groom-backlog-item {title}
  Work:   /work-backlog-item {title}
```

### Step 7: GitHub Issue (P0 and P1 only)

If priority is P0 or P1, ask:

```text
Create a GitHub Issue for this item?
  options: Yes | No (skip)
```

If Yes:

Build a story-format issue body:

```markdown
## Story

As a developer using this repository, I want {one-line goal derived from description}.

## Description

{description}

## Acceptance Criteria

- [ ] {inferred criterion 1 from description}
- [ ] {inferred criterion 2 from description}

## Context

- Priority: {priority}
- Type: {type}
- Added: {date}
- Source: {source}
```

Run:

```bash
gh issue create \
  -R Jamie-BitFlight/claude_skills \
  --title "{title}" \
  --body "$(cat <<'EOF'
{issue body}
EOF
)" \
  --label "priority:{p0|p1|p2|idea}" \
  --label "type:{feature|bug|refactor|docs|chore}" \
  --label "status:needs-grooming"
```

Capture the returned issue number. Write `**Issue**: #{N}` back to the item in BACKLOG.md immediately after the `**Type**:` line.

If `gh` is not installed, report:

```text
gh not available. Run: uv run .claude/skills/gh/scripts/setup_gh.py
Issue creation skipped.
```

If label not found, create it on the fly:

```bash
gh label create "priority:{value}" --color "#e4e669" -R Jamie-BitFlight/claude_skills
```

then retry issue creation.

## Error Handling

- Missing required field: report field name, stop.
- Duplicate detected and user says No: stop without writing.
- BACKLOG.md section not found: report section heading expected, stop.
- GitHub issue creation fails: report error, write item to BACKLOG.md anyway (do not block local write).
- `gh` not installed: skip GitHub step silently after reporting setup command.

## Completion Criteria

- Item written to correct BACKLOG.md section
- Frontmatter counts updated
- `last-updated` set to today
- GitHub Issue created and `**Issue**: #N` written back (P0/P1 only, if user confirmed)
- Next-step commands shown to user
