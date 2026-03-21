---
name: Remove gh CLI usage from development-harness — use backlog MCP tools instead
description: '7 files in plugins/development-harness/ reference gh CLI commands (gh issue, gh pr, gh run, gh api). The development harness should use the backlog MCP tools (mcp__plugin_dh_backlog__*) as the primary interface for all GitHub operations, not gh CLI. Files found: backlog_core/github.py, skills/work-backlog-item/references/github-integration.md, skills/work-backlog-item/references/validation-plan.md, skills/backlog/README.md, skills/backlog/SKILL.md, tests/test_backlog_core_operations.py, docs/backlog-lifecycle.draft.md. The backlog_core/github.py implementation layer using PyGithub is fine — the issue is skill/agent instructions telling the orchestrator or agent to shell out to gh CLI instead of using the MCP tools that wrap PyGithub.'
metadata:
  topic: remove-gh-cli-usage-from-development-harness-use-backlog-mcp
  source: User observation during session 2026-03-21 — gh CLI should never be referenced in dh workflow instructions
  added: '2026-03-21'
  priority: P1
  type: Refactor
  status: open
  issue: '#968'
  last_synced: '2026-03-21T17:13:05Z'
  groomed: '2026-03-21'
  plan: plan/P793-remove-gh-cli-from-dh.yaml
---

## RT-ICA

<div><sub>2026-03-21T17:04:19Z</sub>

RT-ICA Snapshot: Remove gh CLI usage from development-harness
Goal: Replace all gh CLI references in development-harness skill/agent instruction files with backlog MCP tool calls
Conditions:
1. 7 identified files contain gh CLI references | Status: DERIVABLE | Need to verify each file actually contains gh CLI calls
2. Replacement MCP tools exist and are available | Status: AVAILABLE | MCP server is running with backlog_* tools
3. backlog_core/github.py uses PyGithub (not gh CLI) and should be preserved | Status: DERIVABLE | Need to verify this file's role
4. Scope is limited to instruction/documentation files, not runtime Python code | Status: DERIVABLE | Need to confirm no runtime gh subprocess calls exist
AVAILABLE count: 1
DERIVABLE count: 3
MISSING count: 0
</div>

## Fact-Check

<div><sub>2026-03-21T17:11:15Z</sub>

Fact-Check Summary: Remove gh CLI usage from development-harness

Claims checked: 7 files identified in issue description
VERIFIED: 3 | REFUTED: 3 | PARTIAL: 1

1. backlog_core/github.py — REFUTED. Uses PyGithub library (Github(auth=Auth.Token(...))), not gh CLI. The variable `gh` is a PyGithub instance. No subprocess/shell calls to gh CLI.
2. skills/backlog/README.md — VERIFIED. Lines 120, 389, 390 reference `gh label` and `gh issue edit` in anti-pattern warnings ("do not use"). Already correct intent but could mention MCP alternative.
3. skills/backlog/SKILL.md — VERIFIED. Line 221 references `gh issue edit` in anti-pattern warning. Same as README.
4. docs/backlog-lifecycle.draft.md — VERIFIED. Lines 46, 409 are anti-pattern warnings. Line 661 contains actual gh CLI verification command: `gh issue view N --json labels`.
5. skills/work-backlog-item/references/github-integration.md — PARTIAL. References `uv run .claude/skills/gh/scripts/github_project_setup.py` (Python script from /gh skill, not gh CLI binary). Also cross-references /gh skill docs.
6. skills/work-backlog-item/references/validation-plan.md — PARTIAL but counted as REFUTED for gh CLI scope. References `uv run .claude/skills/gh/scripts/github_project_setup.py` (Python script).
7. tests/test_backlog_core_operations.py — REFUTED. References are PyGithub mocks (mock_gh_issue, mock_try_gh), not gh CLI.

Additional files found:
8. skills/backlog/references/state-machine.md — Line 162: anti-pattern warning about `gh label`.
9. tests/test_repo_discovery.py — References gh CLI as a discovery fallback method in discover_repo(). Runtime code, not instruction text.

Conclusion: The actual scope is narrower than described. Most references are either PyGithub code (not gh CLI) or anti-pattern warnings that are already correct. The actionable items are: (a) strengthen anti-pattern warnings to mention MCP tools as the alternative, (b) replace the one gh CLI verification command in lifecycle draft, (c) evaluate whether github-integration.md and validation-plan.md gh skill script references should become MCP tool calls.
</div>

## Groomed (2026-03-21)

### Impact Radius

<div><sub>2026-03-21T17:11:32Z</sub>

Impact Radius: Remove gh CLI usage from development-harness

### Documentation (will become stale or needs update)

- `plugins/development-harness/skills/backlog/README.md` lines 120, 389, 390 — anti-pattern warnings mention `gh label` and `gh issue edit` without stating the MCP alternative
- `plugins/development-harness/skills/backlog/SKILL.md` line 221 — anti-pattern warning mentions `gh issue edit` without stating MCP alternative
- `plugins/development-harness/skills/backlog/references/state-machine.md` line 162 — anti-pattern warning mentions `gh label` without stating MCP alternative
- `plugins/development-harness/docs/backlog-lifecycle.draft.md` lines 46, 409 — anti-pattern warnings; line 661 contains actual `gh issue view N --json labels` verification command

### Agent Instructions (instruct AI to use current interface)

- `plugins/development-harness/skills/work-backlog-item/references/github-integration.md` — references `uv run .claude/skills/gh/scripts/github_project_setup.py` for milestone/label setup operations; could be replaced with MCP tool calls
- `plugins/development-harness/skills/work-backlog-item/references/validation-plan.md` — references `uv run .claude/skills/gh/scripts/github_project_setup.py issue list` for validation; could be replaced with MCP tool calls

### Code — Not Affected (PyGithub, not gh CLI)

- `plugins/development-harness/backlog_core/github.py` — uses PyGithub library, NOT gh CLI. No changes needed.
- `plugins/development-harness/tests/test_backlog_core_operations.py` — tests PyGithub mocks. No changes needed.

### Code — Out of Scope (runtime discovery)

- `plugins/development-harness/tests/test_repo_discovery.py` — tests gh CLI as a repo discovery fallback. This is runtime infrastructure, not workflow instruction. Separate concern.

### Systems Inventory

1. backlog/README.md — documentation — anti-pattern warnings need MCP alternative added
2. backlog/SKILL.md — agent instruction — anti-pattern warning needs MCP alternative added
3. backlog/references/state-machine.md — documentation — anti-pattern warning needs MCP alternative added
4. docs/backlog-lifecycle.draft.md — documentation — anti-pattern warnings + one gh CLI command to replace
5. work-backlog-item/references/github-integration.md — agent instruction — gh skill script refs to evaluate
6. work-backlog-item/references/validation-plan.md — agent instruction — gh skill script refs to evaluate

### Ecosystem Completeness Checklist

- [ ] Every anti-pattern warning updated to mention MCP tool alternative
- [ ] gh CLI verification command in lifecycle draft replaced with MCP equivalent
- [ ] github-integration.md gh skill script references evaluated and replaced where MCP tools exist
- [ ] validation-plan.md gh skill script references evaluated and replaced where MCP tools exist
- [ ] No new gh CLI references introduced
</div>

### Issue Classification

<div><sub>2026-03-21T17:11:42Z</sub>

Issue Classification: procedural

This is a documentation/instruction refactoring task — replacing references to `gh` CLI with references to backlog MCP tools in skill and documentation files. No runtime code changes needed. No root-cause analysis required.
</div>

### Reproducibility

<div><sub>2026-03-21T17:11:59Z</sub>

Reproducible via grep for gh CLI patterns in plugins/development-harness/ markdown files (excluding .venv). Confirms references in 6 documentation/instruction files. PyGithub code in github.py and test mocks are NOT gh CLI references.
</div>

### Priority

<div><sub>2026-03-21T17:12:08Z</sub>

P1 — Skill instructions directing agents to use gh CLI instead of MCP tools causes non-portable behavior and bypasses the backlog MCP server's sync logic.
</div>

### Scope

<div><sub>2026-03-21T17:12:22Z</sub>

Scope is NARROWER than originally described. Of 7 files listed, 3 are excluded (PyGithub code, test mocks). Actual scope: 6 markdown files needing text edits. Two categories of change: (A) strengthen anti-pattern warnings to name MCP tools as the replacement, (B) replace gh skill script references with MCP tool calls where equivalents exist.

Files in scope:
1. skills/backlog/README.md — 3 lines (anti-pattern warnings)
2. skills/backlog/SKILL.md — 1 line (anti-pattern warning)
3. skills/backlog/references/state-machine.md — 1 line (anti-pattern warning)
4. docs/backlog-lifecycle.draft.md — 3 lines (warnings + verification command)
5. skills/work-backlog-item/references/github-integration.md — gh skill script refs
6. skills/work-backlog-item/references/validation-plan.md — gh skill script refs

Files excluded:
- backlog_core/github.py — PyGithub library code, not gh CLI
- tests/test_backlog_core_operations.py — PyGithub mock tests
- tests/test_repo_discovery.py — runtime repo discovery infrastructure (separate concern)
</div>

### Dependencies

<div><sub>2026-03-21T17:12:34Z</sub>

No external dependencies. All replacement MCP tools already exist and are operational via the backlog MCP server (backlog_view, backlog_list, backlog_update, backlog_list_labels, backlog_list_milestones, backlog_list_issues, backlog_sync).
</div>

### Files

<div><sub>2026-03-21T17:12:43Z</sub>

Files to modify:
- plugins/development-harness/skills/backlog/README.md (lines 120, 389, 390)
- plugins/development-harness/skills/backlog/SKILL.md (line 221)
- plugins/development-harness/skills/backlog/references/state-machine.md (line 162)
- plugins/development-harness/docs/backlog-lifecycle.draft.md (lines 46, 409, 661)
- plugins/development-harness/skills/work-backlog-item/references/github-integration.md (lines 46, 65, 108, 200)
- plugins/development-harness/skills/work-backlog-item/references/validation-plan.md (line 72)
</div>

## RT-ICA

<div><sub>2026-03-21T17:13:05Z</sub>

RT-ICA Final: Remove gh CLI usage from development-harness
Goal: Replace all gh CLI references in development-harness skill/agent instruction files with backlog MCP tool calls
Conditions:
1. Files containing gh CLI references identified | Snapshot: DERIVABLE -> Final: AVAILABLE | Citation: grep found 6 files with actual gh CLI text references (3 originally listed files were PyGithub code, not gh CLI)
2. Replacement MCP tools exist and are available | Snapshot: AVAILABLE -> Final: AVAILABLE | Citation: MCP server running with backlog_* tools confirmed
3. backlog_core/github.py uses PyGithub not gh CLI | Snapshot: DERIVABLE -> Final: AVAILABLE | Citation: grep shows Github(auth=Auth.Token(...)) at lines 248, 270, 393 -- PyGithub library
4. Scope limited to instruction/documentation files | Snapshot: DERIVABLE -> Final: AVAILABLE | Citation: fact-check confirmed only markdown files need changes; Python files are PyGithub or test mocks
Changes from snapshot:
- All 3 DERIVABLE conditions resolved to AVAILABLE via grep verification
- No new MISSING conditions discovered
Decision: APPROVED
</div>