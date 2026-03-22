---
name: Migrate milestone skills from gh CLI to project tooling
description: <div><sub>2026-03-20T23:38:51Z</sub>
metadata:
  topic: migrate-milestone-skills-from-gh-cli-to-project-tooling
  source: Milestone orchestration design — .claude/reports/milestone-orchestration-design-20260320.md
  added: '2026-03-20'
  priority: completed
  type: Refactor
  status: done
  issue: '#923'
  last_synced: '2026-03-21T23:10:01Z'
  groomed: '2026-03-21'
  plan: plan/P923-migrate-milestone-skills-gh-cli.yaml
---

## Groomed (2026-03-20)

### Fact-Check Update

<div><sub>2026-03-20T23:38:51Z</sub>

Fact-checker (2026-03-20) found that existing milestone skills (/create-milestone, /group-items-to-milestone, /start-milestone, /complete-milestone) already use PyGithub scripts as their primary path via github_project_setup.py. The gh CLI is used only as fallback. This item needs re-scoping — the migration claimed in the description is already partially done. Verify each skill individually to determine what remains.
</div>

### Impact Radius

<div><sub>2026-03-21T23:08:16Z</sub>

### Scope

<div><sub>2026-03-21T23:09:11Z</sub>

4 project-level SKILL.md files in `.claude/skills/` need all gh CLI calls replaced with backlog MCP tools and PyGithub subcommands:

- `.claude/skills/create-milestone/SKILL.md` — gh CLI primary for duplicate check (Step 2)
- `.claude/skills/start-milestone/SKILL.md` — gh CLI primary for discovery (Steps 1–2) and label creation
- `.claude/skills/complete-milestone/SKILL.md` — gh CLI used in majority of workflow (discovery, issue reassignment, issue close, next-milestone creation)
- `.claude/skills/group-items-to-milestone/SKILL.md` — gh CLI for discovery and milestone assignment

3 new PyGithub subcommands needed in `.claude/skills/gh/scripts/github_project_setup.py`:

- `issue set-milestone --issue N --milestone M`
- `issue remove-milestone --issue N`
- `issue close --number N [--comment "..."]`

Out of scope:
- `dh` plugin (already migrated in #968)
- The `gh` skill itself — it remains available as a general-purpose tool; this item only removes milestone skill dependencies on it
- `milestone get` subcommand (covered by `backlog_list_milestones` + client-side filter; no new subcommand needed)
</div>

### Acceptance Criteria

<div><sub>2026-03-21T23:09:18Z</sub>

All criteria must pass before this item is resolved.

1. `grep -r "gh api\|gh issue\|gh label\|gh project" .claude/skills/create-milestone .claude/skills/start-milestone .claude/skills/complete-milestone .claude/skills/group-items-to-milestone` returns 0 matches

2. `grep -r "setup_gh\b" .claude/skills/create-milestone .claude/skills/start-milestone .claude/skills/complete-milestone .claude/skills/group-items-to-milestone` returns 0 matches

3. Each of the 4 skills uses only `backlog_*` MCP tools or `github_project_setup.py` subcommands for all GitHub operations — no direct `gh` CLI invocations remain

4. `github_project_setup.py` exposes three new subcommands, each callable from the command line:
   - `uv run .claude/skills/gh/scripts/github_project_setup.py issue set-milestone --issue N --milestone M` exits 0 and sets the milestone on issue N
   - `uv run .claude/skills/gh/scripts/github_project_setup.py issue remove-milestone --issue N` exits 0 and clears the milestone on issue N
   - `uv run .claude/skills/gh/scripts/github_project_setup.py issue close --number N` exits 0 and closes issue N

5. pytest unit tests covering each of the 3 new subcommands pass (mock PyGithub calls; no live API calls required)

6. Each of the 4 skills can be invoked in a Claude Code session and reaches its main workflow step without failing on a missing `gh` dependency
</div>

### Files

<div><sub>2026-03-21T23:09:24Z</sub>

**Modify — SKILL.md rewrites (4 files):**

- `.claude/skills/create-milestone/SKILL.md`
- `.claude/skills/start-milestone/SKILL.md`
- `.claude/skills/complete-milestone/SKILL.md`
- `.claude/skills/group-items-to-milestone/SKILL.md`

**Modify — PyGithub script (1 file):**

- `.claude/skills/gh/scripts/github_project_setup.py` — add `issue set-milestone`, `issue remove-milestone`, `issue close` subcommands

**Add — tests (1 file, new or extend existing):**

- `.claude/skills/gh/tests/test_github_project_setup.py` — unit tests for the 3 new subcommands (create if absent, extend if present)

**Read-only / no changes required:**

- `plugins/development-harness/skills/groom-milestone/SKILL.md` — invokes skills via `Skill()`, unaffected
- `plugins/development-harness/skills/work-milestone/SKILL.md` — invokes skills via `Skill()`, unaffected
- `plugins/development-harness/tests/test_scenarios.py` — mocks PyGithub and MCP, not gh CLI; no changes needed
- `.claude/skills/gh/references/milestones.md` — gh CLI reference docs; consider archival after migration but not a blocker
</div>

### Dependencies

<div><sub>2026-03-21T23:09:30Z</sub>

**Available — no action needed:**

- Backlog MCP tools (`backlog_list_milestones`, `backlog_create_milestone`, `backlog_list_issues`, `backlog_comment_issue`) — live in the running MCP server; confirmed available via fact-check
- PyGithub library — already installed and used in `github_project_setup.py`

**Needs work — prerequisite within this item:**

- `github_project_setup.py` subcommands `issue set-milestone`, `issue remove-milestone`, `issue close` — do not yet exist (confirmed by fact-check grep). Must be implemented and tested before the 4 SKILL.md rewrites that call them can be completed. Implement the script changes first, then rewrite the skills.

**No external blockers.** #968 is already resolved; the dh plugin is already gh-free.
</div>

### Effort

<div><sub>2026-03-21T23:09:35Z</sub>

**Medium.**

- 3 new PyGithub subcommands in `github_project_setup.py` — each follows existing patterns (`issue create`, `issue list`); straightforward Typer command additions with `issue.edit()` / `issue.close()` calls
- Unit tests for the 3 new subcommands — mock-based; follows existing test patterns
- 4 SKILL.md rewrites — replace gh CLI call sequences with MCP tool calls and `uv run github_project_setup.py` invocations; content-heavy but mechanically clear given the fact-check per-file breakdown
- No schema changes, no CI changes, no downstream plugin changes

Sequencing constraint: script changes must land before SKILL.md rewrites that reference the new subcommands. Both can be delegated in parallel if the SKILL.md agent treats the new subcommand names as inputs rather than verifying their existence at write time.
</div>


## Files Modified

### Direct Changes (4 skills)

1. **.claude/skills/create-milestone/SKILL.md**
   - Remove `gh api` call for milestone list (Step 2: duplicate check)
   - Replace with `backlog_list_milestones(state="open")`
   - Remove "gh not installed" error handling

2. **.claude/skills/start-milestone/SKILL.md**
   - Remove `gh api` calls for milestone get + list issues (Step 1-2)
   - Replace milestone get: use `backlog_list_milestones()` + client-side filter
   - Replace list issues: use `backlog_list_issues(milestone="{title}")`
   - Remove `gh label create` (handled by PyGithub script)
   - Remove `gh` fallback in Step 5 (PyGithub is primary)
   - Remove "gh not installed" error handling

3. **.claude/skills/complete-milestone/SKILL.md**
   - Replace `gh api` milestone get: use `backlog_list_milestones()` + filter
   - Replace `gh issue list`: use `backlog_list_issues(milestone=, state=)`
   - Replace `gh api POST milestones`: use `backlog_create_milestone()`
   - Requires new PyGithub subcommands: `issue set-milestone`, `issue remove-milestone`, `issue close`
   - Remove `gh` fallback in Step 4
   - Remove "gh not installed" error handling

4. **.claude/skills/group-items-to-milestone/SKILL.md**
   - Replace `gh api` milestone get: use `backlog_list_milestones()` + filter
   - Requires new PyGithub subcommand: `issue set-milestone` (assign issues to milestone)
   - Remove "gh not installed" error handling

### Indirect Changes (PyGithub script)

5. **.claude/skills/gh/scripts/github_project_setup.py**
   - Add subcommand: `issue set-milestone --issue N --milestone M`
   - Add subcommand: `issue remove-milestone --issue N`
   - Add subcommand: `issue close --number N [--comment "..."]`
   - Optional: add subcommand `milestone get --number N` (alternative: use backlog MCP + client-side filter)

## External References (Read-Only Impact)

### Plugin Skills (documentation/awareness only — no changes needed)

- **plugins/development-harness/skills/groom-milestone/SKILL.md** — documents milestone grooming workflow; will reference updated MCP tools after migration
- **plugins/development-harness/skills/work-milestone/SKILL.md** — documents milestone orchestration; will benefit from cleaner gh-free implementation in `.claude/skills/` below it

### Documentation Files (reference updates)

- **.claude/skills/gh/references/milestones.md** — documents gh CLI milestone commands; becomes deprecated after migration (consider archival)

### Backlog MCP Server (source of truth for MCP tools)

- **plugins/development-harness/skills/backlog/SKILL.md** — documents MCP interface; these four skills will be primary consumers of `backlog_list_milestones`, `backlog_create_milestone`, `backlog_list_issues`

## Impact Assessment — 5-Question Checklist

### 1. What breaks if I don't migrate?

**Technical debt accumulates**: Dual code paths (PyGithub + fallback gh CLI) become harder to maintain. The gh skill was already identified as a target for removal in #968 (resolved for development-harness plugin). Leaving fallback paths in `.claude/skills/` prevents full cleanup and creates maintenance confusion (which path do users rely on?).

### 2. What breaks if I do migrate incompletely (partial)?

**User experience inconsistency**: If some milestone skills are converted and others remain on gh CLI, users encounter mixed error messages and different dependency requirements. Partial migration also defeats the purpose of centralizing on project tooling.

**Migration scope is atomic**: All four skills must be migrated together because they all call the same underlying milestone operations. Partial conversion leaves dangling references.

### 3. Are there downstream consumers that depend on current gh CLI behavior?

**No direct downstream consumers in `.claude/skills/`** — the four milestone skills are leaf nodes in the skill dependency graph. No other project-level skills invoke them or depend on their error handling behavior.

**Plugin-level skills (`groom-milestone`, `work-milestone`) are stable consumers** — they invoke these four skills via `Skill()` calls, not by reading their implementation. They will continue to work after migration without modification.

### 4. What changes in the gh skill's responsibility if this migration completes?

**gh skill becomes optional for milestone operations**. Currently, milestone skills fall back to `gh` when PyGithub fails. After migration, all milestone operations are served by:
- Backlog MCP (for read operations: list, get)
- PyGithub script (for write operations: create, close, status transitions)

The gh skill is no longer a fallback path for milestone work. This does NOT break the gh skill itself — it simply removes one use case.

### 5. Are there tests or CI workflows that validate milestone skill behavior?

**Integration tests exist**: plugins/development-harness/tests/test_scenarios.py includes milestone workflow scenarios. These tests mock PyGithub and MCP responses, not gh CLI calls — they will continue to pass after migration without modification.

**No gh-specific linting or CI checks** — the pre-commit hooks and GitHub Actions workflows validate SKILL.md syntax and schema, not gh CLI availability. No CI changes needed.

## Summary

**Direct scope**: 4 project-level skills, 1 PyGithub script
**Indirect scope**: Plugin documentation (read-only), backlog MCP server (primary consumer)
**Atomic change**: All four skills must migrate together; no partial migrations
**No breaking changes**: Downstream skill consumers (groom-milestone, work-milestone) are unaffected
**CI impact**: None — existing tests and workflows continue without modification
</div>


## RT-ICA

<div><sub>2026-03-21T23:10:01Z</sub>

RT-ICA Final: Migrate milestone skills from gh CLI to project tooling
Goal: Replace gh CLI calls in 4 project-level milestone skills with backlog MCP tools and PyGithub
Conditions:
1. Which skills use gh CLI | Snapshot: AVAILABLE → Final: AVAILABLE | Evidence: grep confirmed 4 skills
2. Specific gh commands used | Snapshot: AVAILABLE → Final: AVAILABLE | Evidence: grep output
3. MCP/PyGithub equivalents | Snapshot: DERIVABLE → Final: AVAILABLE | Evidence: fact-checker verified 8+ existing equivalents, 3 missing subcommands identified (issue set-milestone, issue remove-milestone, issue close)
4. #968 scope boundary | Snapshot: AVAILABLE → Final: AVAILABLE | Evidence: #968 covered dh plugin, #923 covers project-level .claude/skills/
Changes from snapshot:
- Condition 3: DERIVABLE → AVAILABLE (resolved by fact-checker with file:line citations)
- Claim "PyGithub is primary path" REFUTED — gh CLI is primary for discovery/issue work
AVAILABLE: 4, DERIVABLE: 0, MISSING: 0
Decision: APPROVED
</div>

## Fact-Check

<div><sub>2026-03-20T23:38:51Z</sub>

Fact-checker (2026-03-20) found that existing milestone skills (/create-milestone, /group-items-to-milestone, /start-milestone, /complete-milestone) already use PyGithub scripts as their primary path via github_project_setup.py. The gh CLI is used only as fallback. This item needs re-scoping — the migration claimed in the description is already partially done. Verify each skill individually to determine what remains.
</div>

<div><sub>2026-03-21T23:08:20Z</sub>

## Verification Results

**Claim 1: "70% of gh usage has existing MCP/PyGithub equivalents"**

Status: **VERIFIED**

Evidence: Research report documents 8+ existing equivalents across Backlog MCP tools and PyGithub subcommands:
- MCP: `backlog_list_milestones`, `backlog_create_milestone`, `backlog_list_issues`, `backlog_comment_issue`
- PyGithub: `milestone {create,list,start,close}`, `issue {create,list}`, `project update-status`

SOURCE: `.claude/reports/milestone-gh-migration-analysis-20260321.md` (lines 15-36), `.claude/skills/gh/scripts/github_project_setup.py` (docstring lines 20-26)

---

**Claim 2: "3 missing operations need new PyGithub subcommands: issue set-milestone, issue remove-milestone, issue close"**

Status: **VERIFIED**

Evidence: Grepped `github_project_setup.py` for subcommands. Script defines:
- `issue create` (line 694-736)
- `issue list` (line 739-764)

Subcommands NOT present:
- `issue set-milestone` — NOT FOUND
- `issue remove-milestone` — NOT FOUND
- `issue close` — NOT FOUND

Milestone/issue assignment performed inline via `issue.edit(milestone=...)` (e.g., line 732), not via dedicated subcommand.

SOURCE: `.claude/skills/gh/scripts/github_project_setup.py` (lines 1-800)

---

**Claim 3: "PyGithub is already the primary path"**

Status: **REFUTED — Claim overstates PyGithub adoption**

Evidence by skill:

1. **create-milestone**: PyGithub primary for create step (line 48-56, "preferred"). But gh CLI primary for duplicate detection (line 38-39, Step 2 is first check).

2. **start-milestone**: PyGithub marked "preferred" (line 73) for bulk transition, but only after gh CLI is used for discovery (lines 29-30, 38-45).

3. **complete-milestone**: Contains 10+ gh CLI calls across discovery (lines 29-30, 38-45), issue reassignment (lines 90-91, 106-107), issue close (lines 113-114). PyGithub script marked "preferred" only for final milestone close (line 119). **Majority of workflow uses gh CLI.**

4. **group-items-to-milestone**: PyGithub for issue creation (line 71-78), but gh API calls for milestone assignment (lines 90-91). Discovery uses gh API (line 30-31).

**Finding**: PyGithub is marked "preferred" for heavy operations (mutations), but gh CLI is woven throughout discovery, filtering, and issue-level operations. The research report's claim that "PyGithub is already the primary path" is inaccurate. Accurate statement would be: "PyGithub handles milestone mutations (start/close), but gh CLI remains primary for discovery and issue-level assignment."

SOURCE:
- `.claude/skills/create-milestone/SKILL.md` (lines 38-56)
- `.claude/skills/start-milestone/SKILL.md` (lines 29-98)
- `.claude/skills/complete-milestone/SKILL.md` (lines 29-140)
- `.claude/skills/group-items-to-milestone/SKILL.md` (lines 30-92)
</div>