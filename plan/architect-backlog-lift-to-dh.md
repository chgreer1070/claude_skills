# Architecture Spec: Lift Backlog Skills to development-harness Plugin

## Executive Summary

Move three backlog intake skills (`create-backlog-item`, `groom-backlog-item`, `work-backlog-item`) from project-level `.claude/skills/` into `plugins/development-harness/skills/`. Update all project-level callers to use the `dh:` namespace prefix. Delete originals after move. This is a file-relocation task with caller updates, not a code implementation project.

## Resolved Design Decisions

| ID | Decision | Resolution |
|----|----------|------------|
| Q1 | Intra-plugin bare names | Work within dh plugin -- no updates needed |
| Q2 | Project-level callers | Need `dh:` prefix after move |
| Q3 | Original directories | Delete after confirming move |
| Q4 | Canonical prefix | `dh:` (plugin.json name) |
| Q5 | Plan artifacts | Left as-is (historical records) |

---

## Deliverable 1: Move Skill Directories

### Operations

```bash
# Copy skill directories preserving structure
cp -r .claude/skills/create-backlog-item/ plugins/development-harness/skills/create-backlog-item/
cp -r .claude/skills/groom-backlog-item/ plugins/development-harness/skills/groom-backlog-item/
cp -r .claude/skills/work-backlog-item/ plugins/development-harness/skills/work-backlog-item/

# Remove originals
rm -rf .claude/skills/create-backlog-item/
rm -rf .claude/skills/groom-backlog-item/
rm -rf .claude/skills/work-backlog-item/
```

### Files Moved

| Source | Destination | File Count |
|--------|-------------|------------|
| `.claude/skills/create-backlog-item/` | `plugins/development-harness/skills/create-backlog-item/` | 1 (SKILL.md) |
| `.claude/skills/groom-backlog-item/` | `plugins/development-harness/skills/groom-backlog-item/` | 3 (SKILL.md + 2 references) |
| `.claude/skills/work-backlog-item/` | `plugins/development-harness/skills/work-backlog-item/` | 9 (SKILL.md + 8 references) |

### Internal References -- No Changes Needed

Per Q1 resolution, these intra-plugin bare-name `Skill()` calls work without modification after the move:

- `work-backlog-item/SKILL.md:177` -- `Skill(skill: "create-backlog-item", args: "--auto {title}")`
- `work-backlog-item/SKILL.md:217` -- `Skill(skill: "groom-backlog-item", args: "{item title}")`
- `plugins/development-harness/skills/interop/SKILL.md:116` -- `Skill(skill="work-backlog-item", args="#N")`

All `./references/` relative links within each skill directory remain valid because the directory structure is preserved as-is.

---

## Deliverable 2: Update Project-Level Callers

### File 1: `plugins/python3-development/skills/complete-implementation/SKILL.md`

**Line 239 -- Skill() invocation:**

```text
# BEFORE
Skill(skill: "create-backlog-item", args: "--auto {derived_title}")

# AFTER
Skill(skill: "dh:create-backlog-item", args: "--auto {derived_title}")
```

**Line 250 -- prose reference:**

```text
# BEFORE
- If `mcp__backlog__backlog_update` fails after creation (title mismatch between what `create-backlog-item` produced and what `update` searched for):

# AFTER
- If `mcp__backlog__backlog_update` fails after creation (title mismatch between what `dh:create-backlog-item` produced and what `update` searched for):
```

**Line 251 -- prose reference:**

```text
# BEFORE
- If `create-backlog-item --auto` logs `[AUTO] STOP -- duplicate detected`:

# AFTER
- If `dh:create-backlog-item --auto` logs `[AUTO] STOP -- duplicate detected`:
```

### File 2: `.claude/CLAUDE.md`

**Line 32 -- Session Start procedures:**

```text
# BEFORE
4. Multi-step work identified: create backlog items via /create-backlog-item or process backlog items via /work-backlog-item — add items freely, they get groomed and checked later.

# AFTER
4. Multi-step work identified: create backlog items via /dh:create-backlog-item or process backlog items via /dh:work-backlog-item — add items freely, they get groomed and checked later.
```

**Line 226 -- Request Progression:**

```text
# BEFORE
2. **Backlog**: Create via `create-backlog-item` or match via `work-backlog-item` before starting.

# AFTER
2. **Backlog**: Create via `dh:create-backlog-item` or match via `dh:work-backlog-item` before starting.
```

**Line 256 -- Backlog Operations:**

```text
# BEFORE
Skills `/create-backlog-item` and `/work-backlog-item` invoke these tools. See `/backlog` skill.

# AFTER
Skills `/dh:create-backlog-item` and `/dh:work-backlog-item` invoke these tools. See `/backlog` skill.
```

### File 3: `.claude/hooks/stop-backlog-reminder.cjs`

**Line 8:**

```text
# BEFORE
New ideas or deferred work discovered this session? → Skill(skill: "create-backlog-item", args: "--auto {title}") to add and track.

# AFTER
New ideas or deferred work discovered this session? → Skill(skill: "dh:create-backlog-item", args: "--auto {title}") to add and track.
```

**Line 9:**

```text
# BEFORE
Completed items? → Skill(skill: "work-backlog-item", args: "close {title}") to verify and close.

# AFTER
Completed items? → Skill(skill: "dh:work-backlog-item", args: "close {title}") to verify and close.
```

### File 4: `plugins/development-harness/skills/create-backlog-item/SKILL.md` (post-move)

**Lines 197-198 -- next-step suggestions:**

```text
# BEFORE
/groom-backlog-item {title}
/work-backlog-item {title}

# AFTER
/dh:groom-backlog-item {title}
/dh:work-backlog-item {title}
```

Note: These are user-facing next-step suggestions. After the move, the skill lives inside dh, so the user-facing slash commands need the `dh:` prefix to resolve correctly from project-level context.

---

## Deliverable 3: Validation

### Check 1: No bare-name references remain in live files

```bash
# Must return zero matches (exclude plan/ directory which contains historical records)
grep -r 'Skill(skill.*[":].*create-backlog-item' --include='*.md' --include='*.cjs' --exclude-dir=plan . | grep -v 'dh:create-backlog-item'
grep -r 'Skill(skill.*[":].*groom-backlog-item' --include='*.md' --include='*.cjs' --exclude-dir=plan . | grep -v 'dh:groom-backlog-item'
grep -r 'Skill(skill.*[":].*work-backlog-item' --include='*.md' --include='*.cjs' --exclude-dir=plan . | grep -v 'dh:work-backlog-item'
```

### Check 2: Skill directories exist in destination

```bash
# All three must exist
test -f plugins/development-harness/skills/create-backlog-item/SKILL.md
test -f plugins/development-harness/skills/groom-backlog-item/SKILL.md
test -f plugins/development-harness/skills/work-backlog-item/SKILL.md
```

### Check 3: Originals removed

```bash
# All three must NOT exist
test ! -d .claude/skills/create-backlog-item
test ! -d .claude/skills/groom-backlog-item
test ! -d .claude/skills/work-backlog-item
```

### Check 4: Reference file integrity

```bash
# Verify reference files survived the move
test -f plugins/development-harness/skills/groom-backlog-item/references/issue-classification.md
test -f plugins/development-harness/skills/groom-backlog-item/references/groomer-agent.md
test -f plugins/development-harness/skills/work-backlog-item/references/validation-plan.md
test -f plugins/development-harness/skills/work-backlog-item/references/sam-definition.md
test -f plugins/development-harness/skills/work-backlog-item/references/example-sessions.md
test -f plugins/development-harness/skills/work-backlog-item/references/error-handling.md
test -f plugins/development-harness/skills/work-backlog-item/references/auto-mode.md
test -f plugins/development-harness/skills/work-backlog-item/references/step-procedures.md
test -f plugins/development-harness/skills/work-backlog-item/references/github-integration.md
test -f plugins/development-harness/skills/work-backlog-item/references/close-resolve-procedure.md
```

### Check 5: Linting

```bash
uv run prek run --files plugins/development-harness/skills/create-backlog-item/SKILL.md
uv run prek run --files plugins/development-harness/skills/groom-backlog-item/SKILL.md
uv run prek run --files plugins/development-harness/skills/work-backlog-item/SKILL.md
uv run prek run --files plugins/python3-development/skills/complete-implementation/SKILL.md
uv run prek run --files .claude/CLAUDE.md
uv run prek run --files .claude/hooks/stop-backlog-reminder.cjs
```

### Check 6: Broader bare-name sweep

```bash
# Catch /create-backlog-item and /work-backlog-item slash references in live files
# (excluding plan/ and .claude/backlog/)
grep -rn '/create-backlog-item\|/groom-backlog-item\|/work-backlog-item' --include='*.md' --include='*.cjs' --exclude-dir=plan --exclude-dir=.claude/backlog . | grep -v 'dh:' | grep -v 'plan/'
```

Any matches from Check 6 are additional callers that need the `dh:` prefix.

---

## NOT In Scope

- `plugins/development-harness/skills/interop/SKILL.md` -- bare name works within dh (Q1)
- `work-backlog-item/SKILL.md` internal `Skill()` calls to `create-backlog-item` and `groom-backlog-item` -- bare names work within dh (Q1)
- `plan/*.md` files -- historical records, not live call sites (Q5)
- `.claude/skills/backlog/` -- MCP server stays project-level
- `plugins/development-harness/plugin.json` -- auto-discovery handles new skill directories, no manifest edit needed

---

## Execution Order

```text
1. Copy directories (Deliverable 1, copy phase)
2. Verify copies exist (Check 2 + Check 4)
3. Update callers (Deliverable 2, all 4 files)
4. Delete originals (Deliverable 1, remove phase)
5. Run validation suite (Deliverable 3, all checks)
6. Commit
```

Copies are verified before originals are deleted. Caller updates happen before deletion so that at no point during execution do bare-name references point to nonexistent skills.

---

## Post-Implementation Annotations

_Added by context-refinement agent on 2026-03-18_

### Design Refinements

1. **Internal relative links broken by path depth change**: The spec claimed "All `./references/` relative
   links within each skill directory remain valid because the directory structure is preserved." This was
   true for intra-skill links but false for cross-directory upward-traversal links. Moving from
   `.claude/skills/{skill}/` (depth 2) to `plugins/development-harness/skills/{skill}/` (depth 4) added
   two directory levels, breaking any link that used `../../` to reach `.claude/docs/` or
   `.claude/skills/`. Three LK001 links in `work-backlog-item/SKILL.md` and one link in
   `references/github-integration.md` were fixed during T01.
   - Original: "All `./references/` relative links within each skill directory remain valid because the
     directory structure is preserved as-is."
   - Actual: Intra-skill links survived; cross-directory upward links required depth correction (+2
     `../` segments per hop). Linting (LK001) was used to identify and fix all broken links.
   - Recorded in: `plan/tasks-2-backlog-lift-to-dh.md`

2. **complete-implementation/SKILL.md had more bare references than spec enumerated**: The spec
   enumerated 3 change locations in `complete-implementation/SKILL.md` (lines 239, 250, 251). The
   actual implementation found 7 locations requiring `dh:` prefix updates (1 `Skill()` call + 6 prose
   references at lines 239, 250, 251, 274, 287, 358, 371). The spec's grep-based validation check
   (Deliverable 3, Check 1) would have caught the additional instances; the enumeration in Deliverable 2
   was incomplete.
   - Original: "Line 239 -- Skill() invocation" + "Line 250 -- prose reference" + "Line 251 -- prose
     reference" (3 total changes listed)
   - Actual: 7 change locations. The grep check in Check 1 was the correct validation mechanism.
   - Recorded in: `plan/tasks-2-backlog-lift-to-dh.md`

3. **create-backlog-item/SKILL.md updates not listed in T02 task scope**: The spec correctly identified
   lines 197-198 of `create-backlog-item/SKILL.md` as requiring `dh:` prefix updates under "File 4" in
   Deliverable 2. However, the T02 task description's enumeration of files did not surface this
   prominently, causing it to be missed during T02 and caught post-review. The update was made correctly;
   the sequencing was sub-optimal.
   - Original: Spec listed 4 files in Deliverable 2; T02 task description listed 4 files.
   - Actual: The File 4 entry was present in the spec but absent from the T02 task body's enumeration,
     causing the implementing agent to skip it.
   - Recorded in: `plan/tasks-2-backlog-lift-to-dh.md`
