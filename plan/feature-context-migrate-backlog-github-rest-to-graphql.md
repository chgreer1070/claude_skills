# Feature Context: Migrate Backlog MCP GitHub Read Operations from REST to GraphQL

## Document Metadata

- **Generated**: 2026-03-17
- **Input Type**: simple_description (with detailed problem space research)
- **Source**: Feature request from orchestrator
- **Status**: DISCOVERY_COMPLETE
- **GitHub Issue**: #773

---

## Original Request

Migrate backlog MCP server's GitHub read operations from PyGithub REST API to PyGithub GraphQL API to eliminate N+1 query patterns. Problem zones identified:

- `create_issue_for_item()` lines 120-126: 3x `repo.get_label()` before `repo.create_issue()`
- `create_task_issue()` lines 540-542: same label prefetch pattern
- `fetch_open_issues_by_title()` line 349 + `batch_fetch_statuses()` line 239: full paginated fetch on `from_github=True` refresh

**Scope**: Primary file is `.claude/skills/backlog/backlog_core/github.py` (28 public functions, all REST internally). Secondary: `state_handler.py` direct REST calls at lines 34-37. 18 test files need GraphQL mock updates.

**Constraint**: Interface stability — public function signatures unchanged. No new dependencies (PyGithub >= 2.8.1 already in pyproject.toml with GraphQL support).

**Desired Outcome**: Single GraphQL query replaces N REST calls. `backlog_list(from_github=True)` issues 1 query instead of paginated REST. `backlog_view` fetches issue+labels+body+status in 1 call. All public interfaces unchanged.

---

## Core Intent Analysis

### WHO (Target Users)

- **Internal**: Backlog MCP server operations teams using `backlog_list(from_github=True)` refresh
- **Direct**: Functions in `github.py` called by `operations.py` and `backlog.py`
- **Secondary**: Test suite authors maintaining 18 test files with GitHub mocks

### WHAT (Desired Outcome)

Reduction of GitHub API round-trips from N REST calls to 1 GraphQL query per operation. Observable impact: faster backlog refresh when `from_github=True`, lower API quota consumption, cleaner code structure (label queries batched instead of sequential).

### WHEN (Trigger Conditions)

- User runs `backlog_list --sync` or equivalent (triggers `from_github=True` code path)
- Backlog item creation with labels
- Task issue creation with label assignment
- View enrichment that requires current issue state

### WHY (Problem Being Solved)

**N+1 Query Antipattern**: Current code fetches labels sequentially before creating issues, resulting in:
- 3 separate `get_label()` calls per issue created (lines 120-126)
- Full paginated issue list on refresh (line 349) followed by individual issue fetches (line 239)
- Network latency multiplied by number of labels/issues
- Higher GitHub API rate limit consumption

**Root Cause**: PyGithub REST client design naturally encourages sequential calls. GraphQL supports batching in single query.

---

## Codebase Research

### Similar Patterns Found

#### Pattern 1: Batch Operations Attempted

- **Location**: `batch_fetch_statuses()` in `github.py` (lines 227-255)
- **Relevance**: Already recognizes N+1 problem — function comment states "Single API call replaces N+1 per-item get_issue() calls"
- **Current Implementation**: Still uses REST `repo_obj.get_issues(state="open")` — single paginated call, but returns full Issue objects not minimal label data
- **Reusable**: Demonstrates awareness of batching need; GraphQL replacement can reuse the function signature and return type

#### Pattern 2: Label Prefetch Before Create

- **Location**: `create_issue_for_item()` lines 119-126 and `create_task_issue()` lines 540-542
- **Relevance**: Explicit label lookup loop before `create_issue()` — the exact N+1 antipattern
- **Pattern**: `for name in labels: label_objs.append(repo.get_label(name))`
- **Reusable**: GraphQL mutation can fetch/validate labels in same query as creation

### Existing Infrastructure

- **PyGithub graphql_query() API**: Available in version 2.8.1 (verified in pyproject.toml)
- **Available methods**:
  - `graphql_query(query_string)` — custom GraphQL queries
  - `graphql_node(node_id, query_fields)` — single-node fetch
  - `graphql_named_mutation(mutation_name, variables)` — write operations
- **No new dependencies**: PyGithub upgrade not required (already >= 2.8.1)

### Code References

- Primary file: `.claude/skills/backlog/backlog_core/github.py` — 28 public functions using REST
- Secondary file: `.claude/skills/backlog/backlog_core/state_handler.py` — `apply_github_transition()` has direct REST calls at lines 34-37
- Test files: 18 files (location pattern not specified in research — agents will discover)
- Interface contract: `backlog.py` and `operations.py` are callers with stable interface expectations

---

## Use Scenarios

### Scenario 1: Backlog List with GitHub Sync

**Actor**: User running `backlog list --sync` or orchestrator via `backlog_list(from_github=True)`

**Trigger**: Refresh from GitHub to load latest issue statuses and labels

**Goal**: Get current state of all backlog items with metadata in minimal API calls

**Current Behavior**: 1 paginated REST call to fetch issues + N REST calls to fetch status labels per item

**Desired Behavior**: 1 GraphQL query fetching issue nodes with all label data in one payload

### Scenario 2: Create Issue with Labels

**Actor**: Backlog creation via `create_issue_for_item()` or `create_task_issue()`

**Trigger**: User creates new backlog item that maps to GitHub issue

**Goal**: Create issue and apply labels atomically

**Current Behavior**: 3x `get_label()` REST calls to validate/fetch label objects, then 1 `create_issue()` REST call with label objects = 4 round-trips

**Desired Behavior**: 1 GraphQL mutation that validates labels and creates issue in single query

### Scenario 3: View Enrichment

**Actor**: `view_enrich_from_github()` called to populate ViewItemResult with live issue data

**Trigger**: User requests backlog item details

**Goal**: Fetch issue title, body, labels, state, milestone in one operation

**Current Behavior**: Single `get_issue()` REST call (efficient but still REST)

**Desired Behavior**: Single GraphQL query (consistency with other operations)

---

## Gap Analysis

### Identified Gaps

| # | Category | Gap Description | Impact |
|---|----------|-----------------|--------|
| 1 | Scope | Which functions qualify for GraphQL migration vs. staying REST? | Determines effort scope; some operations may not benefit from batching |
| 2 | Behavior | How should GraphQL error handling differ from REST (404 label not found, permission errors, rate limits)? | Error handling paths must remain stable; users of library see same exceptions |
| 3 | Behavior | Should write operations (create_issue, label mutations) use GraphQL named mutations or remain REST? | Scope creep risk — user said "read operations" but create/edit touch REST/GraphQL boundary |
| 4 | Testing | What mock strategy for GraphQL responses? (Mock entire graphql_query() or mock at GitHub API transport layer?) | 18 test files need updates; strategy determines refactor complexity |
| 5 | Performance | What's the baseline performance of `batch_fetch_statuses()` on realistic backlog sizes (100-1000 items)? | Validates whether N+1 is actual bottleneck or theoretical; may inform prioritization |
| 6 | Backward Compat | Can function signatures stay identical when switching from REST to GraphQL responses? | PyGithub REST returns Issue/Label objects; GraphQL returns dicts — conversion layer needed |

---

## Questions Requiring Resolution

### Q1: Scope of GraphQL Migration — Read vs. Write vs. All

- **Category**: Scope
- **Gap**: User said "read operations" but some functions like `create_issue_for_item()` are writes that contain reads (label lookup). Request explicitly mentions `create_issue_for_item()` and `create_task_issue()` as N+1 problems.
- **Question**: Does "read operations" mean only query-only functions (fetch_open_issues, view_enrich)? Or include write operations that have embedded label reads?
- **Options**:
  - A) Read-only GraphQL queries only (batch_fetch_statuses, fetch_open_issues, view_enrich) — create/edit stay REST
  - B) Include write operations with embedded reads (create_issue_for_item, create_task_issue) — use GraphQL mutations
  - C) Full migration including issue.edit(), label management (apply_status_in_progress, etc.)
- **Why It Matters**: Option A is minimal, lower-risk. Option B addresses the stated N+1 problem. Option C is maximum scope but may introduce unforeseen complexity with mutations.
- **Resolution**: _pending_

### Q2: Error Handling Equivalence

- **Category**: Behavior
- **Gap**: PyGithub REST exceptions (GithubException with .status, .data) differ from GraphQL response error format. Users of public API expect specific exceptions.
- **Question**: When GraphQL query returns "Label not found" error vs. REST 404, should both paths raise identical GithubException to callers? Or accept new error types?
- **Options**:
  - A) Wrap GraphQL errors to raise identical GithubException — conversion layer in github.py
  - B) Let GraphQL errors bubble as different types — callers must handle both REST and GraphQL exceptions
  - C) Separate internal _graphql_* functions from public functions — only public ones guarantee exception compatibility
- **Why It Matters**: Interface stability constraint requires callers (operations.py, backlog.py) to see same exceptions. Silent divergence breaks contract.
- **Resolution**: _pending_

### Q3: Label Lookup Behavior on Non-Existent Labels

- **Category**: Behavior
- **Gap**: Current code treats missing labels differently: `create_issue_for_item()` logs warning and continues (lines 123-125), `apply_status_in_progress()` auto-creates labels (lines 325-327).
- **Question**: Should GraphQL migration preserve this inconsistent behavior, or standardize?
- **Options**:
  - A) Preserve each function's current behavior — migration is mechanical, no logic changes
  - B) Standardize: always skip missing labels (like create_issue_for_item)
  - C) Standardize: always auto-create missing labels (like apply_status_verified)
- **Why It Matters**: Users may depend on current "skip with warning" vs. "auto-create" behavior in create vs. status functions.
- **Resolution**: _pending_

### Q4: Test Mocking Strategy

- **Category**: Testing
- **Gap**: 18 test files need updates. Current strategy likely mocks PyGithub REST objects (Issue, Label). GraphQL queries return dict-like responses.
- **Question**: Should tests mock at the `graphql_query()` method level or at GitHub API HTTP transport level?
- **Options**:
  - A) Mock graphql_query() responses directly (higher-level, easier to write, specific to GraphQL)
  - B) Mock HTTP transport (lower-level, tests both REST and GraphQL paths, more brittle)
  - C) Hybrid: some tests use graphql_query() mocks, others use HTTP layer mocks
- **Why It Matters**: Test maintainability and coverage robustness differ significantly. GraphQL query mocks are easier to write but don't catch transport bugs.
- **Resolution**: _pending_

### Q5: Performance Measurement Baseline

- **Category**: Performance
- **Gap**: Research identifies N+1 as real but doesn't quantify impact on typical backlog sizes.
- **Question**: Should we establish performance baseline (time, API calls) for current REST implementation before migration?
- **Options**:
  - A) Yes — establish baseline, measure post-migration, require X% improvement
  - B) No — N+1 is obviously wrong, skip baseline measurement
  - C) Baseline for batch_fetch_statuses only (the explicit bottleneck at line 239)
- **Why It Matters**: Without baseline, can't verify migration actually solved the problem. May discover GraphQL isn't faster for small backlogs.
- **Resolution**: _pending_

### Q6: Backward Compatibility at Data Level

- **Category**: Backward Compat
- **Gap**: PyGithub REST returns typed objects (Issue.title, Issue.labels). GraphQL query responses are dicts. Return values to callers must be identical.
- **Question**: Can internal functions safely switch to GraphQL dict responses, or must conversion layer preserve REST object types?
- **Options**:
  - A) Direct GraphQL dict responses — callers adapted to dict access (breaking change in implementation detail)
  - B) Conversion layer inside github.py — GraphQL responses converted to same objects/dicts REST functions returned
  - C) Hybrid — some functions return dicts (internal only), others return objects (public only)
- **Why It Matters**: Caller code (operations.py, backlog.py, tests) accesses return values with field names. Must not break.
- **Resolution**: _pending_

---

## Goals (Pending Resolution)

These goals will be finalized after questions are resolved.

1. Eliminate N+1 label prefetch pattern in `create_issue_for_item()` and `create_task_issue()` via GraphQL mutation
2. Replace paginated REST list + sequential status fetches in `batch_fetch_statuses()` with single GraphQL query
3. Maintain public function signatures and exception types — zero breaking changes to callers
4. Reduce GitHub API rate limit consumption on backlog refresh (from_github=True) operations
5. Update all 18 test files to mock GraphQL responses with consistent strategy
6. Establish performance baseline before and after migration to validate improvement
7. Standardize error handling — all label lookup failures raise equivalent exceptions regardless of REST/GraphQL path

---

## Next Steps

After questions are resolved:

1. Update "Resolution" fields in Questions section with user answers
2. Finalize Goals section based on scope decision (Q1)
3. Proceed to architecture design phase
4. Design GraphQL query and mutation schemas needed
5. Plan test migration strategy (Q4)

---

## Notes for Orchestrator

**Research Quality**: User has provided excellent problem analysis with specific line numbers and identified patterns. No further codebase investigation needed at discovery stage. All gaps are genuine ambiguities, not missing information.

**Constraint Compliance**:
- Interface stability requirement is clear and mandatory
- No new dependencies (PyGithub already has GraphQL)
- 18 test files identified but locations not specified — agents will need to discover

**Risk Areas**:
- Error handling consistency (Q2) is critical for maintaining interface contract
- Label behavior inconsistency (Q3) may require small breaking change policy discussion
- Test strategy (Q4) determines implementation complexity significantly
