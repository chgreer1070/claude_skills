# Task Plan: GitHub Projects V2 Status Field Updates

**Backlog Item**: github_project_setup.py: add GitHub Projects V2 status field updates
**Issue**: #236
**Priority**: P2
**Created**: 2026-02-28

## Goal

Add `project update-status` subcommand to `github_project_setup.py` that uses the GraphQL API
to set the `Status` field on project items. Integrate with `milestone_start` and `milestone_close`
so label transitions also update the kanban board.

## Architecture

### New Components

1. **`project_app` Typer sub-app** — registered on `app` as `project`
2. **`_gh_graphql(query)` helper** — execute GraphQL via `gh` CLI (pattern from `sync_issues_to_project.py`)
3. **`_discover_project_fields(owner, project_number)` helper** — dynamic field/option ID discovery
4. **`_find_project_item(project_id, issue_node_id)` helper** — find or add issue to project
5. **`_update_project_status(...)` internal function** — reusable by both subcommand and milestone functions

### Integration Points

- `milestone_start()` → after label transitions, call `_update_project_status` with "In Progress"
- `milestone_close()` → after label transitions, call `_update_project_status` with "Done"
- Both get optional `--project-number` and `--owner` params

## Tasks

- [x] 1. Add `_gh_graphql()` helper function (adapted from sync_issues_to_project.py)
- [x] 2. Add `_discover_project_fields()` — GraphQL query for project ID, Status field ID, option IDs
- [x] 3. Add `_find_project_item()` — find existing project item for an issue
- [x] 4. Add `_update_project_status()` — internal function to update Status field
- [x] 5. Add `project_app` Typer sub-app with `update-status` command
- [x] 6. Add `--project-number` and `--owner` options to `milestone_start` and `milestone_close`
- [x] 7. Integrate `_update_project_status` calls into `milestone_start` after label transitions
- [x] 8. Integrate `_update_project_status` calls into `milestone_close` after label transitions
- [x] 9. Add `--dry-run` support to `project update-status`
- [x] 10. Run linting (`uv run prek run --files`)
- [x] 11. Test CLI help output and argument parsing
- [x] 12. Commit and push (PR #299)

## Acceptance Criteria

1. `project update-status` subcommand exists in github_project_setup.py
2. Uses GraphQL `updateProjectV2ItemFieldValue` mutation
3. Field ID and option ID discovery via `projectV2Fields` query
4. Accepts valid status values (Backlog, Grooming, In Progress, In Review, Done)
5. `--dry-run` flag shows changes without applying
6. `milestone_start` and `milestone_close` call `update_status` after label transitions
