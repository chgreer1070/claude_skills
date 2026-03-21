# Feature Context: Remove gh CLI from development-harness

## Problem

6 markdown files in `plugins/development-harness/` reference `gh` CLI commands (`gh issue`, `gh label`, `gh issue edit`, `gh issue view`). The development harness should use the backlog MCP tools (`mcp__plugin_dh_backlog__*`) as the primary interface for all GitHub operations. The `gh` CLI is non-portable and bypasses the backlog MCP server's sync logic.

## Scope (verified via fact-check)

Only documentation/instruction markdown files need changes. PyGithub code in `github.py` and test mocks are NOT `gh` CLI and are excluded.

Two categories of change:

- **Category A**: Anti-pattern warnings that mention `gh` CLI commands — strengthen to name MCP tools as the replacement
- **Category B**: `gh` skill script references (`uv run .claude/skills/gh/scripts/github_project_setup.py`) — replace with MCP tool calls where equivalents exist

## Files in Scope

1. `plugins/development-harness/skills/backlog/README.md` (lines 120, 389, 390) — anti-pattern warnings
2. `plugins/development-harness/skills/backlog/SKILL.md` (line 221) — anti-pattern warning
3. `plugins/development-harness/skills/backlog/references/state-machine.md` (line 162) — anti-pattern warning
4. `plugins/development-harness/docs/backlog-lifecycle.draft.md` (lines 46, 409, 661) — warnings + verification command
5. `plugins/development-harness/skills/work-backlog-item/references/github-integration.md` (lines 3, 46, 65, 108, 200) — gh skill script refs
6. `plugins/development-harness/skills/work-backlog-item/references/validation-plan.md` (lines 3, 72) — gh skill script refs

## Files Excluded

- `backlog_core/github.py` — PyGithub library code, not `gh` CLI
- `tests/test_backlog_core_operations.py` — PyGithub mock tests
- `tests/test_repo_discovery.py` — runtime repo discovery infrastructure

## Desired Outcome

- Anti-pattern warnings mention both what NOT to do (`gh` CLI) and what TO do (MCP tools)
- `gh` skill script references replaced with MCP tool equivalents
- No Python code changes

## GitHub Issue

Issue #968
