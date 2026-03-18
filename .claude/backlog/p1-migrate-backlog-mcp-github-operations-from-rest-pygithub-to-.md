---
name: Migrate backlog MCP GitHub read operations from PyGithub REST to PyGithub GraphQL API
description: "**Problem**: The backlog MCP server uses PyGithub's REST methods (repo.get_issues, repo.get_issue, issue.edit, etc.) for GitHub operations. PyGithub v2.x includes a GraphQL client (documented at https://pygithub.readthedocs.io/en/v2.8.1/graphql.html) that can fetch issue + labels + body + status in a single query instead of 2-3 REST round-trips. backlog_add has an N+1 pattern with up to 3 repo.get_label() prefetch calls per issue creation. from_github=True full refresh fetches the entire issue list via paginated REST.\n\n**Where it lives**: .claude/skills/backlog/backlog_core/github.py — single module owns GitHub I/O via PyGithub. The migration stays within PyGithub — replacing REST method calls with GraphQL queries using the same library's built-in GraphQL client.\n\n**Success looks like**: Read operations (list, view, batch status, reconciliation) use PyGithub's GraphQL client. Single query fetches issue + labels + body + status. Write operations (create, close, update labels) use GraphQL mutations where supported, REST where not. API call count reduced for common operations. No new dependencies — PyGithub is already installed.\n\n**How you'll know it's working**: backlog_list(from_github=True) makes 1 GraphQL query instead of N paginated REST calls. backlog_view returns labels+body+status in 1 call. backlog_add label prefetch eliminated.\n\n**Reference**: https://pygithub.readthedocs.io/en/v2.8.1/graphql.html — PyGithub's built-in GraphQL API documentation.\n\n**Audit reference**: .claude/reports/backlog-github-api-audit.md (per-operation REST breakdown from this session)"
metadata:
  topic: migrate-backlog-mcp-github-operations-from-rest-pygithub-to-
  source: Session observation — GraphQL audit revealed REST-only GitHub API usage with N+1 patterns
  added: '2026-03-17'
  priority: P1
  type: Refactor
  status: open
  issue: '#773'
  last_synced: '2026-03-17T20:42:40Z'
  groomed: '2026-03-17'
  plan: plan/tasks-773-migrate-backlog-github-rest-to-graphql.md
---

## RT-ICA

<div><sub>2026-03-17T20:39:17Z</sub>

RT-ICA Snapshot: Migrate backlog MCP GitHub read operations from PyGithub REST to GraphQL
Goal: Replace REST multi-call patterns in github.py with single GraphQL queries using PyGithub's built-in client.
Conditions:
1. PyGithub v2.x includes a built-in GraphQL client        | AVAILABLE (cited: pygithub.readthedocs.io/en/v2.8.1/graphql.html)
2. github.py is the single GitHub I/O module               | AVAILABLE (description states this)
3. Current REST operations list and call sites              | DERIVABLE (read github.py)
4. PyGithub GraphQL API syntax and query patterns           | DERIVABLE (fetch from docs URL)
5. Which operations to migrate vs. keep as REST             | DERIVABLE (analyze github.py + docs)
6. Callers/consumers of github.py public functions          | DERIVABLE (grep codebase)
7. Existing test coverage for github.py                     | DERIVABLE (search test files)
AVAILABLE: 2 | DERIVABLE: 5 | MISSING: 0
Decision: APPROVED (snapshot — pending swarm)
</div>

## Groomed (2026-03-17)

### Issue Classification

<div><sub>2026-03-17T20:40:13Z</sub>

### Impact Radius

<div><sub>2026-03-17T20:40:16Z</sub>

### Priority

<div><sub>2026-03-17T20:42:16Z</sub>

P1 — Correctness + Performance. N+1 REST calls on issue creation (3 round-trips per label) and full paginated REST refresh degrade latency for multi-label operations. GraphQL migration eliminates this at the PyGithub layer without changing public interface.
</div>

### Scope

<div><sub>2026-03-17T20:42:20Z</sub>

Primary: .claude/skills/backlog/backlog_core/github.py — migrate all 28 public functions from REST to GraphQL where supported.
Secondary: .claude/skills/backlog/backlog_core/state_handler.py — direct REST method calls need migration (MEDIUM impact, scope wider than originally described).
Tests: 18 test files — all REST mocks must be updated to GraphQL equivalents (HIGH effort).
Interface stability: operations.py and backlog.py callers are unaffected (public interface signatures unchanged).
Out of scope: write operations that have no GraphQL equivalent remain as REST.
</div>

### Acceptance Criteria

<div><sub>2026-03-17T20:42:24Z</sub>

- [ ] backlog_list(from_github=True) issues a single GraphQL query instead of paginated REST calls
- [ ] backlog_view fetches issue + labels + body + status in a single GraphQL call
- [ ] backlog_add N+1 label prefetch eliminated — labels created inline in GraphQL mutation
- [ ] state_handler.py direct REST calls migrated to GraphQL
- [ ] All 18 affected test files updated with GraphQL mocks
- [ ] No new dependencies — PyGithub >=2.8.1 already installed
- [ ] All existing tests pass after migration
- [ ] Public interface of github.py and state_handler.py unchanged (operations.py callers unaffected)
</div>

### Files

<div><sub>2026-03-17T20:42:28Z</sub>

Primary implementation:
- .claude/skills/backlog/backlog_core/github.py — main migration target (28 functions, REST → GraphQL)
- .claude/skills/backlog/backlog_core/state_handler.py — secondary migration (direct REST calls)

Test files to update (18 total — full list in Impact Radius section):
- .claude/skills/backlog/tests/test_*.py (18 files need GraphQL mock updates)

Reference:
- .claude/reports/backlog-github-api-audit.md — per-operation REST breakdown from audit session
- https://pygithub.readthedocs.io/en/v2.8.1/graphql.html — PyGithub GraphQL API documentation
</div>

### Effort

<div><sub>2026-03-17T20:42:31Z</sub>

**Estimate**: Medium-Large (3-5 implementation tasks)

Tasks breakdown:
- T1: Audit state_handler.py REST calls and design GraphQL query map (Medium)
- T2: Migrate read operations in github.py — list, view, batch status, reconciliation (Medium-Large)
- T3: Migrate write mutations — create, close, label updates (Medium)
- T4: Update 18 test files with GraphQL mocks (Large — mechanical but numerous)
- T5: Integration verification — run full backlog MCP test suite (Small)

**Complexity**: Medium — PyGithub GraphQL API is documented, interface signatures unchanged, but 18 test files need mock updates.
**Risk**: Low — no new dependencies, no public interface changes, scope bounded to two modules.
</div>

### Resources

<div><sub>2026-03-17T20:42:35Z</sub>

- PyGithub GraphQL docs: https://pygithub.readthedocs.io/en/v2.8.1/graphql.html
- PyGithub GitHub repo: https://github.com/PyGithub/PyGithub (graphql.py source)
- Audit report: .claude/reports/backlog-github-api-audit.md
- Primary target: .claude/skills/backlog/backlog_core/github.py
- Secondary target: .claude/skills/backlog/backlog_core/state_handler.py
</div>

### Dependencies

<div><sub>2026-03-17T20:42:40Z</sub>

- PyGithub >=2.8.1 (VERIFIED already installed — no new dependency)
- GitHub API GraphQL endpoint (existing — no new auth required)
- No blocked dependencies — ready to implement
</div>


## Impact Radius

### Code — Producers (provide the changed interface)

**`.claude/skills/backlog/backlog_core/github.py`** — Single module owning all GitHub API I/O. All 28 public functions use PyGithub REST methods internally:

REST calls to replace with GraphQL:
- `gh.search_issues(query)` → GraphQL search (line 214)
- `repo.get_issues(state=...)` → GraphQL issues query (line 239, 349)
- `repo.get_issue(num)` → GraphQL single-issue query (lines 145, 174, 270–271, 317, 373, 451, 600, 575)
- `repo.get_label(name)` → GraphQL label lookup (lines 123, 287–291, 321, 330, 542)
- `repo.create_label(...)` → GraphQL label creation (line 325)
- `issue.get_sub_issues()` → GraphQL sub-issues query (line 576)
- `issue.edit(...)`, `issue.create_comment(...)`, `issue.add_to_labels()`, `issue.remove_from_labels()` → GraphQL mutations (lines 152, 184, 288–291, 328–331, 465, 555, 623)

Interface is stable (function signatures unchanged) — migration is internal to method implementations.

### Code — Consumers (read the changed interface)

**`.claude/skills/backlog/backlog_core/operations.py`** — Imports 15 github.py functions (lines 27–45):
- `apply_status_in_progress`, `apply_status_verified`, `batch_fetch_statuses` — status management
- `check_open_prs_for_issue`, `close_github_issue`, `create_issue_for_item`, `create_task_issue` — issue CRUD
- `fetch_github_issue_body`, `fetch_open_issues_by_title` — queries
- `get_github`, `get_task_issues`, `issue_to_local_fields` — utilities
- `resolve_github_issue`, `sync_groomed_to_github_issue`, `try_get_github`, `update_task_status` — core operations
- `view_enrich_from_github` — view enrichment

**No changes needed** — operations.py calls these functions without introspection on REST vs GraphQL. All error handling (GithubException) remains valid.

**`.claude/skills/backlog/scripts/backlog.py`** — CLI entry point. Imports 4 functions + operations module (lines 76–80, 74):
- `create_issue_for_item`, `fetch_open_issues_by_title`, `issue_to_local_fields` from github.py
- `backlog_core.operations` (which imports github.py)

**No changes needed** — backlog.py is a thin CLI wrapper over operations. No direct REST dependencies.

**`.claude/skills/backlog/scripts/state_handler.py`** — State machine validation. Imports GithubException, provides `apply_github_transition()` function that calls repo/issue methods (lines 34–37):
- Calls `repo.get_issue(issue_num)`
- Calls `issue.edit()` and label operations

**Needs update** — `apply_github_transition()` currently uses REST `.edit()` and label methods. Migration path: replace with GraphQL mutation calls or refactor to use github.py's `apply_status_*` functions instead of direct repo/issue method calls.

### Code — Other References

**`.claude/skills/backlog/backlog_core/models.py`** — Type definitions. Imports `GithubException` from PyGithub (used in error handling).

**No changes needed** — exception types remain the same.

**`.claude/skills/backlog/backlog_core/parsing.py`** — Parsing utilities. No direct github.py imports.

**No changes needed**.

**`.claude/skills/backlog/backlog_core/entry_blocks.py`** — Entry block utilities. No github.py imports.

**No changes needed**.

### Documentation (will become stale)

**`.claude/skills/backlog/backlog_core/ARCHITECTURE.md`** — Architecture overview.

**Audit required** — check for REST API implementation details, performance assumptions (N+1 queries), rate-limit behavior. GraphQL batching will change some characteristics.

**`.claude/skills/backlog/CLI_TO_MCP_MIGRATION.md`** — Migration guide.

**Audit required** — check for REST-specific behavior notes.

**`.claude/skills/backlog/SKILL.md`** — Skill frontmatter and references.

**Audit required** — check for REST API examples or constraints.

**`.claude/skills/backlog/references/*.md`** — Reference files.

**Audit required** — check each reference file in `./references/` for REST-specific implementation details.

### Configuration / CI

**`.github/workflows/backlog-sync.yml`** (line 37) — Calls `uv run .claude/skills/backlog/scripts/backlog.py sync`.

**No changes needed** — CLI interface is stable. Workflow will work without modification.

### Agent Instructions (instruct AI to use current interface)

**Skill documentation**: `/backlog` skill documentation in SKILL.md and agent files.

**Audit required** — check skill frontmatter and any agent instructions that describe github.py functions or REST behavior.

### Systems Inventory

| File Path | Role | Connection | Impact |
|-----------|------|-----------|--------|
| `.claude/skills/backlog/backlog_core/github.py` | GitHub API interface (REST → GraphQL migration target) | Owns all GH I/O | HIGH — all changes here |
| `.claude/skills/backlog/backlog_core/operations.py` | High-level CRUD layer | Imports 15 functions from github.py | MEDIUM — no code changes, but integration testing required |
| `.claude/skills/backlog/scripts/backlog.py` | CLI entry point | Imports 4 functions + operations module | LOW — thin wrapper, no code changes |
| `.claude/skills/backlog/scripts/state_handler.py` | State machine | Direct repo/issue method calls (not via github.py) | MEDIUM — needs refactor to use github.py or migrate REST calls |
| `tests/test_backlog_core_github.py` | Unit tests for github.py | Mocks all PyGithub objects | HIGH — all tests will need updates for GraphQL |
| `tests/test_backlog_core_operations.py` | Integration tests | Mocks github.py functions | MEDIUM — may need mock updates if function signatures change |
| `tests/test_reconciliation.py` | Sync tests | Uses operations module | LOW — no changes if operations stable |
| `tests/test_backlog_gh_first.py` | GitHub-first flow tests | Mocks github.py | HIGH — tests will need mock updates |
| `tests/test_scenarios.py` | End-to-end scenarios | Uses full stack | MEDIUM — integration testing required |
| `tests/test_server_sam.py` | MCP server tests (SAM operations) | Uses github.py SAM functions | MEDIUM — tests use mock objects |
| `tests/test_operations_sam.py` | SAM CRUD tests | Uses operations module SAM functions | MEDIUM — tests use mock objects |
| `.github/workflows/backlog-sync.yml` | CI sync workflow | Runs backlog.py sync | LOW — no workflow changes needed |

### Ecosystem Completeness Checklist

- [ ] All 28 github.py functions converted to GraphQL (or remain unchanged if they already wrap REST safely)
- [ ] `state_handler.py::apply_github_transition()` refactored to use github.py functions or updated to GraphQL mutations
- [ ] All GithubException error handling validated to work with GraphQL errors
- [ ] PyGithub GraphQL client imports added and tested
- [ ] All test mocks updated to reflect GraphQL call patterns (query structure, response shape)
- [ ] `test_backlog_core_github.py` updated with GraphQL test fixtures
- [ ] `test_backlog_gh_first.py` integration tests re-run against GraphQL
- [ ] Documentation (ARCHITECTURE.md, references/*.md) audited for REST-specific claims
- [ ] Skill documentation reviewed for interface changes or examples
- [ ] CI workflow backlog-sync.yml verified to work with updated CLI
- [ ] Performance characteristics documented (GraphQL batching, rate limits, response times vs REST)
- [ ] Backwards compatibility notes added if any internal function signatures changed

</div>


## Issue Classification

**Type**: refactor

**Justification**: Existing REST API implementation works correctly but is inefficient. Migration to GraphQL consolidates multiple round-trips (N+1 label fetches, paginated requests) into single queries, improving response time and reducing API overhead.

## Root-Cause Analysis

N/A — not required for refactor classification. This is code restructuring for performance improvement, not a defect or process failure.
</div>

## Fact-Check

<div><sub>2026-03-17T20:40:27Z</sub>

## Fact-Check Results

| Claim | Status | Evidence |
|-------|--------|---------|
| PyGithub v2.x has built-in GraphQL client | VERIFIED | PyGithub v2.8.1 docs: `graphql_query()`, `graphql_node()`, `graphql_named_mutation()` methods available. SOURCE: https://pygithub.readthedocs.io/en/v2.8.1/graphql.html (accessed 2026-03-17) |
| backlog_add N+1 pattern with up to 3 repo.get_label() calls | VERIFIED | `.claude/skills/backlog/backlog_core/github.py:120-126` — `create_issue_for_item()` loops through 3 labels, calling `repo.get_label(name)` per label before `repo.create_issue()`. Also `create_task_issue()` at lines 540-542 has same pattern. |
| from_github=True REST pagination via get_issues() | VERIFIED | `fetch_open_issues_by_title()` at line 349 and `batch_fetch_statuses()` at line 239 both use `repo.get_issues(state="open")` which materializes paginated REST calls on iteration. |
| Single GraphQL query replaces 2-3 REST calls | VERIFIED | PyGithub v2.8.1 GraphQL API supports `graphql_query()` for custom queries enabling single fetch of `{ number title labels state body milestone }`, eliminating separate `get_issue()`, `get_label()`, `get_milestone()` calls. |
| GraphQL mutations supported | VERIFIED | PyGithub v2.8.1 Requester class includes `graphql_named_mutation()` (line 807) and `graphql_named_mutation_class()` (line 835) for write operations. |
| PyGithub already installed | VERIFIED | `.claude/skills/backlog/pyproject.toml:7` — `"pygithub>=2.8.1"` in dependencies. No new dependency required. |

**Verification Summary**: All claims VERIFIED. 6/6 accurate.

**Key Technical Findings**:
- PyGithub v2.8.1 GraphQL support includes query and mutation methods with both raw and typed class responses
- Current REST implementation has three N+1 problem zones: label prefetching in `create_issue_for_item()` and `create_task_issue()`, and label fetches in status update operations
- Migration would consolidate 2-3 REST API calls per operation into single GraphQL queries/mutations
- No blocking issues: PyGithub already in dependencies, migration is scoped to `backlog_core/github.py`
</div>

## RT-ICA

<div><sub>2026-03-17T20:41:14Z</sub>

## RT-ICA Final: Migrate backlog MCP GitHub read operations from PyGithub REST to GraphQL

**Goal**: Replace REST multi-call patterns in `github.py` and `state_handler.py` with single GraphQL queries using PyGithub's built-in client (`graphql_query()`, `graphql_node()`, mutation methods).

**Decision**: APPROVED — all conditions AVAILABLE or DERIVABLE (no MISSING). No blockers to implementation.

### Condition Assessment

| # | Condition | Snapshot | Final | Evidence | Change |
|---|-----------|----------|-------|----------|--------|
| 1 | PyGithub v2.x includes built-in GraphQL client | DERIVABLE | **AVAILABLE** | fact-checker verified `graphql_query()`, `graphql_node()`, `graphql_named_mutation()` in PyGithub v2.8.1+ | Resolved by fact-check |
| 2 | `github.py` is the single GitHub I/O module | AVAILABLE | **REFUTED** | impact-analyst found `state_handler.py` also contains direct REST calls — scope is wider than snapshot assumed | Scope widened |
| 3 | REST operations list and line numbers | DERIVABLE | **AVAILABLE** | impact-analyst identified N+1 patterns at lines 120–126 (2 REST calls), 239/349 (pagination), 540–542 (2 REST calls) | Resolved by analysis |
| 4 | PyGithub GraphQL API syntax and patterns | DERIVABLE | **AVAILABLE** | fact-checker confirmed GraphQL query syntax, mutation support, and PyGithub's GraphQL client API surface | Resolved by fact-check |
| 5 | Which operations to migrate vs keep as REST | DERIVABLE | **DERIVABLE** | Single GraphQL query can replace 2–3 REST calls; migration candidates: N+1 patterns (lines 120–126, 540–542), paginated issue lists (lines 239, 349) | Assess during implementation |
| 6 | Callers/consumers of `github.py` public functions | DERIVABLE | **AVAILABLE** | impact-analyst identified `operations.py` imports 15 functions with stable interface — no consumer code changes needed | Resolved by analysis |
| 7 | Existing test coverage for `github.py` | DERIVABLE | **AVAILABLE** | impact-analyst found 18 test files; all mock REST calls and will require GraphQL mock updates | Resolved by analysis |
| 8 | `state_handler.py` REST call scope (new condition) | N/A | **DERIVABLE** | impact-analyst noted MEDIUM impact; need to identify which functions in `state_handler.py` have direct REST calls | New discovery |
| 9 | Test mock strategy for GraphQL (new condition) | N/A | **DERIVABLE** | PyGithub test patterns exist; need to determine mock strategy for GraphQL vs REST mocking across 18 test files | New discovery |

### Key Changes from Snapshot

- **Condition 1**: DERIVABLE → AVAILABLE (fact-checker verified PyGithub v2.8.1+ has GraphQL client)
- **Condition 2**: AVAILABLE → REFUTED (scope includes `state_handler.py`, not just `github.py`)
- **Conditions 3, 4, 6, 7**: DERIVABLE → AVAILABLE (all resolved by swarm analysis)
- **Conditions 8, 9**: NEW discoveries from impact analysis and test coverage audit

### Implementation Readiness

- ✓ Dependency available: PyGithub v2.8.1+ already installed
- ✓ Performance gain validated: single GraphQL query replaces 2–3 REST calls
- ✓ Interface stable: consumers in `operations.py` do not require code changes
- ✓ Migration scope identified: `github.py` (28 public functions, N+1 patterns), `state_handler.py` (direct REST calls, MEDIUM impact)
- ✓ Test coverage scope: 18 files, all require GraphQL mock updates
- ⚠ Remaining: determine `state_handler.py` REST scope and GraphQL mock strategy
</div>