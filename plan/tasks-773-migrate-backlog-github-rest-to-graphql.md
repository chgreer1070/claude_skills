---
plan_number: 773
slug: migrate-backlog-github-rest-to-graphql
goal: "Eliminate N+1 label-prefetch patterns in github.py by replacing per-label REST get_label() loops with a single GraphQL batch query, preserving all public function signatures and exception types"
feature: "Migrate Backlog MCP GitHub REST Label Loops to GraphQL"
status: not-started
issue: 773
created: "2026-03-17T00:00:00Z"
context: |
  Primary target: .claude/skills/backlog/backlog_core/github.py
  Two confirmed N+1 zones:
    - create_issue_for_item() lines 120-126: loop over 3 label names, each calls repo.get_label()
    - create_task_issue() lines 540-542: identical pattern
  Lines 239 and 349 are already batch-optimized — no changes needed there.
  state_handler.py makes no direct REST calls — no changes needed there.
  Interface contract: all 28 public function signatures are frozen. Callers in operations.py
  and backlog.py must see identical return types and exception types after migration.
  GraphQL support: PyGithub >= 2.8.1 (already in pyproject.toml) exposes gh.graphql_query().
  No new dependencies required.
  Architecture spec: plan/architect-migrate-backlog-github-rest-to-graphql.md
  Feature context: plan/feature-context-migrate-backlog-github-rest-to-graphql.md
  Codebase analysis: plan/codebase/architecture.md
  ADR-004: GraphQL errors array translated to GithubException inside private helpers.
  ADR-005: Per-function label-missing behavior preserved (skip+warn for create functions).
  Mock strategy: mock gh.graphql_query() at method level — consistent with existing REST mocks.
  Test coverage requirement: github.py >= 90%, new private functions 100% branch coverage.

acceptance_criteria:
  - "AC1: _resolve_labels_graphql() private function exists in github.py, accepts (gh, repo_owner, repo_name, label_names) and returns list[str] of existing label names"
  - "AC2: create_issue_for_item() no longer calls repo.get_label() in a loop — calls _resolve_labels_graphql() instead"
  - "AC3: create_task_issue() no longer calls repo.get_label() in a loop — calls _resolve_labels_graphql() instead"
  - "AC4: Public signatures of create_issue_for_item() and create_task_issue() are unchanged"
  - "AC5: GraphQL errors array in response raises GithubException (not raw dict) with status codes per ADR-004 translation table"
  - "AC6: Missing labels are silently omitted from returned list, and caller logs warning via output.warn() — identical to current REST behavior"
  - "AC7: uv run pytest .claude/skills/backlog/tests/ -x exits 0 with all tests passing"
  - "AC8: Coverage for github.py >= 90% line and branch"
  - "AC9: No new package dependencies added to pyproject.toml"

acceptance_criteria_structured:
  - criterion-id: AC-TESTS
    description: "Full test suite passes with no failures"
    check_command: "uv run pytest .claude/skills/backlog/tests/ -x -q 2>&1 | tail -5"
    pass_condition: "exit code 0"
  - criterion-id: AC-COVERAGE
    description: "github.py coverage >= 90% line and branch"
    check_command: "uv run pytest .claude/skills/backlog/tests/ --cov=.claude/skills/backlog/backlog_core/github --cov-report=term-missing --co -q 2>&1 | tail -10"
    pass_condition: "exit code 0 and coverage >= 90%"
  - criterion-id: AC-NO-GET-LABEL-LOOP
    description: "No get_label() loop present in create_issue_for_item or create_task_issue"
    check_command: "grep -n 'get_label' .claude/skills/backlog/backlog_core/github.py | grep -v '_resolve_labels_graphql' | grep -v '#'"
    pass_condition: "exit code 1 (no matches outside the private helper)"
  - criterion-id: AC-LINTING
    description: "Ruff and type checking pass on modified files"
    check_command: "uv run ruff check .claude/skills/backlog/backlog_core/github.py .claude/skills/backlog/tests/"
    pass_condition: "exit code 0"

tasks:
  - task: T0
    title: "T0: Capture baseline state"
    status: complete
    agent: t0-baseline-capture
    dependencies: []
    priority: 1
    complexity: low
    is-bookend: true
    bookend-type: t0-baseline
    accuracy-risk: low
    skills: []
    body: |
      ## Context
      T0 runs before any implementation work. It captures the current pass/fail state of every
      structured acceptance criterion so TN can detect regressions after implementation.

      ## Objective
      Run all structured acceptance criteria commands and record baseline results in
      plan/T0-baseline-migrate-backlog-github-rest-to-graphql.yaml.

      ## Inputs
      - Plan file: plan/tasks-773-migrate-backlog-github-rest-to-graphql.md
      - acceptance_criteria_structured entries: AC-TESTS, AC-COVERAGE, AC-NO-GET-LABEL-LOOP, AC-LINTING

      ## Requirements
      1. For each criterion in acceptance_criteria_structured, run its check_command via Bash
      2. Record exit code, stdout, stderr, and timestamp per criterion
      3. Write results to plan/T0-baseline-migrate-backlog-github-rest-to-graphql.yaml

      ## Expected Outputs
      - plan/T0-baseline-migrate-backlog-github-rest-to-graphql.yaml

      ## Acceptance Criteria
      1. plan/T0-baseline-migrate-backlog-github-rest-to-graphql.yaml exists
      2. File contains one entry per structured criterion with exit code, stdout, stderr, timestamp

      ## Verification Steps
      1. cat plan/T0-baseline-migrate-backlog-github-rest-to-graphql.yaml and confirm criteria_count matches plan

  - task: T1
    title: "Verify PyGithub GraphQL API and finalize _resolve_labels_graphql design"
    status: complete
    agent: python3-development:python-cli-architect
    dependencies: ["T0"]
    priority: 1
    complexity: medium
    accuracy-risk: high
    skills: ["python3-development"]
    parallelize-with: []
    body: |
      ## Context
      The architecture spec at plan/architect-migrate-backlog-github-rest-to-graphql.md
      specifies a private helper _resolve_labels_graphql() that uses PyGithub's
      gh.graphql_query() to batch-resolve label names in one round-trip. Before
      implementing, verify the exact PyGithub 2.8.1 graphql_query() method signature,
      return type, and error behavior against actual source. The spec notes an important
      design detail: GitHub GraphQL does not support bulk label lookup by list — the
      approach uses dynamic aliases (label0: label(name: "...") { name id }) generated
      per label name. This task confirms that design is correct and produces a verified
      function signature + query template for T2 to implement.

      This task is RESEARCH AND DESIGN ONLY. Do not modify github.py.

      ## Objective
      Confirm PyGithub graphql_query() signature, return type, and error conventions;
      produce a verified design document at plan/T1-graphql-design-migrate-backlog-github-rest-to-graphql.md
      containing the finalized function signature, query template string, and error
      translation table ready for T2 to implement.

      ## Inputs
      - Architecture spec: plan/architect-migrate-backlog-github-rest-to-graphql.md (sections 4.3, 5.2, ADR-004)
      - Codebase analysis: plan/codebase/architecture.md (Existing GraphQL Usage section)
      - PyGithub source: inspect installed package at site-packages to verify graphql_query method

      ## Requirements
      1. Inspect PyGithub's MainClass.py (or equivalent) to find graphql_query() method signature — confirm
         parameter names, types, and return type using the installed package
      2. Verify graphql_query() return type: confirm it returns a dict with "data" key on success
         and "errors" key on failure (not raising by default)
      3. Confirm PyGithub version >= 2.8.1 is installed: read pyproject.toml or run
         uv run python -c "import github; print(github.__version__)"
      4. Verify dynamic alias query pattern is valid GraphQL: confirm that generating
         label0: label(name: "x") { name id } per label name is supported by GitHub GraphQL
         API v4 (check GitHub GraphQL docs or the spec's Section 4.3 rationale)
      5. Verify that repo.create_issue(labels=[...]) accepts plain strings (not Label objects)
         by inspecting PyGithub Repository.create_issue signature in installed package
      6. Write design document at plan/T1-graphql-design-migrate-backlog-github-rest-to-graphql.md
         containing:
         - Confirmed graphql_query() signature with source reference
         - Verified query template string for dynamic alias label resolution
         - Confirmed create_issue() accepts string labels (with source reference)
         - Error translation table from ADR-004 (confirmed or corrected based on PyGithub behavior)
         - Any deviations from the architecture spec with justification

      ## Constraints
      - Do NOT modify any source files — this task is research and design only
      - Do NOT assume PyGithub API details from training data — verify from installed package source
      - Do NOT include T0/TN error trailer in commits

      ## Expected Outputs
      - plan/T1-graphql-design-migrate-backlog-github-rest-to-graphql.md

      ## Acceptance Criteria
      1. Design document exists at plan/T1-graphql-design-migrate-backlog-github-rest-to-graphql.md
      2. Document contains graphql_query() signature with a file path or line reference to PyGithub source
      3. Document contains a complete, syntactically valid GraphQL query template for dynamic alias label resolution
      4. Document states whether create_issue() accepts string labels (yes/no + source reference)
      5. Document contains the finalized error translation table (NOT_FOUND→404, FORBIDDEN→403, RATE_LIMITED→429, other→502)

      ## Verification Steps
      1. Read plan/T1-graphql-design-migrate-backlog-github-rest-to-graphql.md and confirm all five
         acceptance criteria sections are present
      2. Run: uv run python -c "from github import Github; import inspect; print(inspect.signature(Github.graphql_query))"
         and confirm output matches the signature in the design doc
      3. Run: uv run python -c "import github; print(github.__version__)"
         and confirm version is >= 2.8.1

      ## CoVe Checks
      Accuracy risk is HIGH because PyGithub API details differ across versions and training data may be stale.

      Key claims to verify:
      - graphql_query() exists on Github object in version >= 2.8.1
      - graphql_query() returns dict (not raises) when GraphQL errors array is present
      - create_issue() labels parameter accepts plain strings

      Verification questions:
      1. Does inspect.signature(Github.graphql_query) show the parameters the spec claims?
      2. Does gh.graphql_query() return {"errors": [...]} on error, or raise an exception?
      3. Does Repository.create_issue() signature show labels: list[str | Label]?

      Evidence to collect:
      - Run inspect.signature() on both methods and include output in design doc
      - Check PyGithub source under site-packages for graphql_query implementation

      Revision rule:
      If graphql_query() raises on errors (instead of returning {"errors": [...]}), revise
      the error handling section of the design doc to wrap in try/except GithubException instead.
      Document the deviation from the architecture spec explicitly.

      ## Handoff
      Return: STATUS: DONE + path to plan/T1-graphql-design-migrate-backlog-github-rest-to-graphql.md
      Include: which (if any) architecture spec details were corrected by live verification

  - task: T2
    title: "Implement _resolve_labels_graphql() private helper in github.py"
    status: complete
    agent: python3-development:python-cli-architect
    dependencies: ["T0", "T1"]
    priority: 2
    complexity: medium
    accuracy-risk: medium
    skills: ["python3-development"]
    body: |
      ## Context
      T1 produced a verified design document at
      plan/T1-graphql-design-migrate-backlog-github-rest-to-graphql.md containing
      the confirmed PyGithub graphql_query() signature, query template, and error
      translation table. This task implements the _resolve_labels_graphql() private
      helper in github.py using that verified design. The helper will be called by T3
      to replace the N+1 label lookup loops.

      ## Objective
      Add _resolve_labels_graphql() to .claude/skills/backlog/backlog_core/github.py
      as a private function that resolves a list of label names in one GraphQL round-trip.

      ## Inputs
      - Design document: plan/T1-graphql-design-migrate-backlog-github-rest-to-graphql.md (PRIMARY — use this, not training data)
      - Architecture spec: plan/architect-migrate-backlog-github-rest-to-graphql.md (sections 4.1, 4.3, 5.1, 5.2, ADR-004, ADR-005)
      - Target file: .claude/skills/backlog/backlog_core/github.py

      ## Requirements
      1. Add module-level constant _LABEL_RESOLUTION_QUERY containing the GraphQL query
         string — use the exact template from the T1 design document; never f-string user
         data into the query string (security: ADR section 6)
      2. Add TypedDict classes _LabelNode and _GraphQLLabelResponse as internal types
         (not exported) — definitions from architecture spec section 5.2
      3. Implement _resolve_labels_graphql(gh, repo_owner, repo_name, label_names):
         - If label_names is empty, return [] immediately without making a GraphQL call
         - Deduplicate label_names before building the query
         - Build dynamic alias query: label0: label(name: "...") { name id } per unique name
         - Call gh.graphql_query() using the verified signature from T1 design doc
         - On response with "errors" key: translate to GithubException using the ADR-004
           error translation table (NOT_FOUND→404, FORBIDDEN→403, RATE_LIMITED→429,
           INSUFFICIENT_SCOPES→403, other→502)
         - Filter null aliases (labels not found) from result — return only existing label names
         - Return list[str] of existing label names (not Label objects, not node IDs)
         - Non-GithubException exceptions propagate unchanged
      4. Place the function immediately before create_issue_for_item() in the file
      5. Run uv run ruff check .claude/skills/backlog/backlog_core/github.py to confirm
         no lint errors introduced

      ## Constraints
      - Do NOT modify create_issue_for_item() or create_task_issue() — that is T3's scope
      - Do NOT export _resolve_labels_graphql() — it must remain private (single underscore prefix)
      - Do NOT add any new import not already in the file except from typing import TypedDict
        (if not already present)
      - Query strings MUST be module-level constants — never constructed via f-string with user data
      - Do NOT use fallback to REST on GraphQL failure (ADR section 10 "Graceful Degradation"):
        if GraphQL fails, raise — do not silently retry with get_label()

      ## Expected Outputs
      - .claude/skills/backlog/backlog_core/github.py (modified: new private function + constant + TypedDicts)

      ## Acceptance Criteria
      1. _resolve_labels_graphql function exists in github.py with signature:
         (gh: Github, repo_owner: str, repo_name: str, label_names: list[str]) -> list[str]
      2. _LABEL_RESOLUTION_QUERY constant exists at module level — no f-string interpolation
      3. Empty input returns [] without calling graphql_query()
      4. Response with "errors" key raises GithubException (not returns raw dict)
      5. Null aliases (missing labels) are filtered — function returns only names that exist
      6. uv run ruff check .claude/skills/backlog/backlog_core/github.py exits 0

      ## Verification Steps
      1. grep -n "_resolve_labels_graphql" .claude/skills/backlog/backlog_core/github.py
         — confirms function and usage are present
      2. grep -n "_LABEL_RESOLUTION_QUERY" .claude/skills/backlog/backlog_core/github.py
         — confirms module-level constant exists
      3. uv run ruff check .claude/skills/backlog/backlog_core/github.py
         — exits 0
      4. uv run python -c "
         from .claude.skills.backlog.backlog_core.github import _resolve_labels_graphql
         print('imported OK')
         " — or equivalent import check confirms function is importable

      ## CoVe Checks
      Accuracy risk is MEDIUM because the implementation relies on PyGithub graphql_query()
      return shape verified in T1, and error handling must match ADR-004 exactly.

      Key claims to verify:
      - graphql_query() return shape on success: {"data": {"repository": {...}}}
      - graphql_query() return shape on error: {"errors": [{...}]} (not raises)
      - GraphQL error "type" field names match ADR-004 table (NOT_FOUND, FORBIDDEN, etc.)

      Verification questions:
      1. Does the T1 design document confirm graphql_query() returns {"errors": [...]} (not raises)?
      2. Does the error translation code handle the case where errors[0] has no "type" key?
      3. Does _resolve_labels_graphql return [] when all aliases are null?

      Evidence to collect:
      - Read T1 design doc to confirm graphql_query() error behavior before writing translation code
      - Grep github.py after implementation for any f-string containing query variables

      Revision rule:
      If T1 design doc states graphql_query() raises on error (not returns {"errors": [...]}),
      wrap the call in try/except GithubException instead of inspecting the response dict.
      Update the implementation accordingly and note the deviation.

      ## Handoff
      Return: STATUS: DONE
      Include: confirmation that ruff exits 0 and function signature matches T1 design doc

  - task: T3
    title: "Migrate create_issue_for_item() and create_task_issue() label loops to _resolve_labels_graphql()"
    status: complete
    agent: python3-development:python-cli-architect
    dependencies: ["T0", "T2"]
    priority: 3
    complexity: medium
    accuracy-risk: medium
    skills: ["python3-development"]
    body: |
      ## Context
      This task was merged from two planned changes to avoid edit conflicts on
      .claude/skills/backlog/backlog_core/github.py:
        Scope A — Migrate create_issue_for_item() lines 120-126
        Scope B — Migrate create_task_issue() lines 540-542
      Both scopes replace the same N+1 pattern (per-label repo.get_label() loop)
      with a call to _resolve_labels_graphql() implemented in T2.

      T2 is complete: _resolve_labels_graphql() is available in github.py.

      Current pattern in both functions:
        label_objs = []
        for name in labels:
            try:
                label_objs.append(repo.get_label(name))
            except GithubException:
                out.warn(f"  WARNING: label '{name}' not found")
        # Then: repo.create_issue(..., labels=label_objs)

      Target pattern (same for both functions):
        existing_label_names = _resolve_labels_graphql(gh, owner, repo_name, labels)
        # Warn for each name in labels not in existing_label_names
        for name in labels:
            if name not in existing_label_names:
                out.warn(f"  WARNING: label '{name}' not found")
        # Then: repo.create_issue(..., labels=existing_label_names)

      Architecture spec section 5.4 confirms repo.create_issue() accepts string labels.

      ## Objective
      Replace the per-label get_label() loops in both create_issue_for_item() and
      create_task_issue() with a single call to _resolve_labels_graphql() per function,
      preserving all public signatures, return types, and warning behavior.

      ## Inputs
      - Target file: .claude/skills/backlog/backlog_core/github.py (modified by T2)
      - Architecture spec: plan/architect-migrate-backlog-github-rest-to-graphql.md (sections 4.1, 5.4, ADR-005)
      - T1 design doc: plan/T1-graphql-design-migrate-backlog-github-rest-to-graphql.md (to confirm create_issue() accepts strings)

      ## Requirements

      ### Scope A: create_issue_for_item() lines 120-126
      1. Read the current implementation of create_issue_for_item() to identify the exact
         label loop block and the gh (Github) object available in scope
      2. Extract repo_owner and repo_name from the repo string (format: "owner/repo") to
         pass to _resolve_labels_graphql()
      3. Replace the label_objs loop with: existing_label_names = _resolve_labels_graphql(gh, owner, repo_name, labels)
      4. After the call, log output.warn() for each label in labels not returned by _resolve_labels_graphql
         — this preserves current "label not found" warning behavior (ADR-005)
      5. Pass existing_label_names (list[str]) to repo.create_issue(labels=existing_label_names)
      6. Public function signature (repo, item, dry_run, output) must remain unchanged

      ### Scope B: create_task_issue() lines 540-542
      7. Read the current implementation of create_task_issue() to identify the exact
         label loop block and the gh (Github) object available in scope
      8. Apply the identical replacement pattern as Scope A:
         - Extract owner/repo_name from repo string
         - Call _resolve_labels_graphql(gh, owner, repo_name, labels or [])
         - Log output.warn() for each missing label name
         - Pass existing_label_names to repo.create_issue(labels=...)
      9. Public function signature must remain unchanged
      10. Handle labels=None gracefully (pass empty list to _resolve_labels_graphql)

      ### Both scopes
      11. Run uv run ruff check .claude/skills/backlog/backlog_core/github.py after changes
      12. Confirm no calls to repo.get_label() remain inside create_issue_for_item or create_task_issue
          (grep to verify)

      ## Constraints
      - Do NOT change public function signatures
      - Do NOT change return types — create_issue_for_item returns int | None, create_task_issue returns int | None
      - Do NOT add a REST fallback if _resolve_labels_graphql raises — let the exception propagate
      - Do NOT modify any function other than create_issue_for_item and create_task_issue
      - Do NOT add new imports not required by the changes

      ## Expected Outputs
      - .claude/skills/backlog/backlog_core/github.py (modified: both label loops replaced)

      ## Acceptance Criteria
      1. grep -n "get_label" github.py | grep -v "_resolve_labels_graphql" | grep -v "#"
         returns no matches inside create_issue_for_item or create_task_issue
      2. _resolve_labels_graphql is called in both create_issue_for_item() and create_task_issue()
      3. output.warn() is still called for each label name not returned by _resolve_labels_graphql
      4. Signatures of create_issue_for_item() and create_task_issue() are unchanged
      5. uv run ruff check .claude/skills/backlog/backlog_core/github.py exits 0

      ## Verification Steps
      1. grep -n "get_label" .claude/skills/backlog/backlog_core/github.py
         — only match should be in _resolve_labels_graphql definition and docstring (not in the two migrated functions)
      2. grep -n "_resolve_labels_graphql" .claude/skills/backlog/backlog_core/github.py
         — should show the definition line plus two call sites (one per function)
      3. uv run ruff check .claude/skills/backlog/backlog_core/github.py
         — exits 0

      ## CoVe Checks
      Accuracy risk is MEDIUM because the gh object availability inside create_issue_for_item()
      and create_task_issue() must be confirmed from source before writing the replacement.

      Key claims to verify:
      - A Github (gh) object is available in scope inside create_issue_for_item()
      - A Github (gh) object is available in scope inside create_task_issue()
      - repo string format is "owner/name" — split by "/" gives exactly two parts

      Verification questions:
      1. Is `gh` (or equivalent) already in scope, or does it need to be obtained via get_github()?
      2. Does the repo parameter follow "owner/name" format consistently?

      Evidence to collect:
      - Read the function bodies of create_issue_for_item() and create_task_issue() before writing
        any changes — confirm gh object availability and repo string format

      Revision rule:
      If gh is not in scope, obtain it via get_github(repo) at the start of the function
      body (before the label resolution call). Document this addition in the handoff.

      ## Handoff
      Return: STATUS: DONE
      Include:
      - Confirmation that ruff exits 0
      - How gh was obtained in each function (was it already in scope, or was get_github() called?)
      - grep output showing no get_label() calls remain in the two migrated functions

  - task: T4
    title: "Write tests for _resolve_labels_graphql() and update tests for migrated functions"
    status: complete
    agent: python3-development:python-pytest-architect
    dependencies: ["T0", "T3"]
    priority: 4
    complexity: high
    accuracy-risk: medium
    skills: ["fastmcp-python-tests", "python3-development"]
    body: |
      ## Context
      T3 is complete: create_issue_for_item() and create_task_issue() now call
      _resolve_labels_graphql() instead of repo.get_label() loops. Tests in
      .claude/skills/backlog/tests/ still mock repo.get_label() for these functions
      and will fail. This task:
        1. Creates test_graphql_helpers.py with full unit tests for _resolve_labels_graphql()
        2. Updates existing test_backlog_core_github.py (and any other affected test files)
           to replace repo.get_label() mock setup with gh.graphql_query() mock setup
           for tests covering create_issue_for_item() and create_task_issue()

      The architecture spec section 7.3 defines the exact GraphQL mock pattern to use.

      ## Objective
      Produce a passing test suite with >= 90% coverage on github.py and 100% branch
      coverage on _resolve_labels_graphql(), using gh.graphql_query() mocks consistently.

      ## Inputs
      - Architecture spec: plan/architect-migrate-backlog-github-rest-to-graphql.md (sections 7.2, 7.3, 7.5 — mock patterns and test cases)
      - Implementation: .claude/skills/backlog/backlog_core/github.py (read to understand _resolve_labels_graphql behavior)
      - Existing tests: .claude/skills/backlog/tests/ (discover all files; update only those testing create_issue_for_item or create_task_issue)
      - Codebase analysis: plan/codebase/architecture.md (Test Mock Conventions section)

      ## Requirements

      ### New file: test_graphql_helpers.py
      1. Create .claude/skills/backlog/tests/test_graphql_helpers.py
      2. Use pytest-mock MockerFixture for all mocks (not unittest.mock directly)
      3. Implement ALL 8 test cases from architecture spec section 7.3:
         - all labels found — returns full list of names
         - some labels missing (null aliases) — returns only found labels, no exception
         - no labels in input — returns empty list, graphql_query NOT called
         - GraphQL errors array present — raises GithubException with correct status
         - graphql_query raises GithubException(401) — propagates unchanged
         - graphql_query raises GithubException(403) — propagates unchanged
         - empty repository response — returns empty list
         - duplicate label names in input — deduplicated before query, deduplicated in result
      4. Add @pytest.mark.unit and @pytest.mark.graphql markers to all tests in this file
      5. For the "errors array" test, verify GithubException status codes per ADR-004:
         NOT_FOUND→404, FORBIDDEN→403, RATE_LIMITED→429, other→502

      ### Existing tests: update for migrated functions
      6. Discover all test files that currently set up repo.get_label mock for
         create_issue_for_item() or create_task_issue() tests — grep for both patterns
      7. For each affected test, replace repo.get_label mock setup with gh.graphql_query mock:
         - Success case: gh_mock.graphql_query.return_value = {"data": {"repository": {"label0": {"name": "...", "id": "..."}, ...}}}
         - Missing label: set alias value to None in the mock response dict
         - Failure case: gh_mock.graphql_query.side_effect = GithubException(401, {...})
      8. Ensure gh_mock is available in test fixtures where repo_mock is already present
         — either add gh_mock to existing fixtures or create new ones
      9. Tests for functions that were NOT migrated (close_github_issue, resolve_github_issue,
         batch_fetch_statuses, fetch_open_issues_by_title, etc.) must NOT be modified

      ### Coverage gate
      10. After all changes, run:
          uv run pytest .claude/skills/backlog/tests/ --cov=.claude/skills/backlog/backlog_core/github --cov-report=term-missing
          and confirm coverage >= 90%

      ## Constraints
      - Use pytest-mock MockerFixture, NEVER unittest.mock directly
      - Do NOT mock at HTTP transport level — mock at graphql_query() method level
      - Do NOT modify tests for functions not touched by T2 or T3
      - Do NOT write tests that call live GitHub API (no integration tests without @pytest.mark.integration)
      - Test files must not contain bare print() statements — use capsys or logging

      ## Expected Outputs
      - .claude/skills/backlog/tests/test_graphql_helpers.py (new)
      - .claude/skills/backlog/tests/test_backlog_core_github.py (modified: updated mocks for migrated functions)
      - Any other test files in .claude/skills/backlog/tests/ that covered create_issue_for_item or create_task_issue (modified)

      ## Acceptance Criteria
      1. .claude/skills/backlog/tests/test_graphql_helpers.py exists with all 8 test cases
      2. All 8 test cases from architecture spec section 7.3 are present and named descriptively
      3. uv run pytest .claude/skills/backlog/tests/ -x -q exits 0 (no failures)
      4. uv run pytest .claude/skills/backlog/tests/ --cov=.claude/skills/backlog/backlog_core/github --cov-report=term-missing shows github.py >= 90% coverage
      5. No test file uses unittest.mock directly — all mocks via MockerFixture

      ## Verification Steps
      1. uv run pytest .claude/skills/backlog/tests/ -x -q
         — exits 0, all tests pass
      2. uv run pytest .claude/skills/backlog/tests/ --cov=.claude/skills/backlog/backlog_core/github --cov-report=term-missing
         — confirms coverage >= 90%
      3. grep -rn "unittest.mock" .claude/skills/backlog/tests/
         — returns no matches (all mocks use pytest-mock)
      4. grep -c "def test_" .claude/skills/backlog/tests/test_graphql_helpers.py
         — returns >= 8

      ## CoVe Checks
      Accuracy risk is MEDIUM because the GraphQL mock response shape must exactly match
      what _resolve_labels_graphql() expects, and the existing test fixture structure
      must be understood before modification.

      Key claims to verify:
      - gh object (Github instance) is accessible in existing test fixtures
      - Mock response shape {"data": {"repository": {"label0": {...}}}} matches what the
        implementation parses in T2

      Verification questions:
      1. Do existing conftest.py fixtures provide a gh_mock (Github) object, or only repo_mock?
      2. Does the implementation in T2 access response["data"]["repository"] or response.get("data", {}).get("repository")?

      Evidence to collect:
      - Read .claude/skills/backlog/tests/conftest.py to understand existing fixture structure
      - Read _resolve_labels_graphql() implementation to confirm response parsing path

      Revision rule:
      If conftest.py has no gh_mock fixture, add one as a pytest fixture in test_graphql_helpers.py
      (and optionally in conftest.py if shared). Document the fixture addition in the handoff.

      ## Handoff
      Return: STATUS: DONE
      Include:
      - pytest exit code and summary line (passed/failed/errors count)
      - Coverage percentage for github.py
      - List of test files modified (not new)
      - Whether conftest.py was modified

  - task: T5
    title: "Integration verification — run full test suite and confirm acceptance criteria"
    status: complete
    agent: python3-development:python-cli-architect
    dependencies: ["T0", "T4"]
    priority: 5
    complexity: low
    accuracy-risk: low
    skills: ["python3-development"]
    body: |
      ## Context
      T4 is complete: tests written and passing in isolation. This task runs the full
      test suite with coverage, checks linting on all modified files, and confirms
      all plan-level acceptance criteria are met. It also verifies the no-get_label-loop
      criterion (AC-NO-GET-LABEL-LOOP) from the structured acceptance criteria.

      ## Objective
      Confirm all 9 plan acceptance criteria are satisfied; produce a verification
      report at plan/T5-verification-migrate-backlog-github-rest-to-graphql.md.

      ## Inputs
      - Modified implementation: .claude/skills/backlog/backlog_core/github.py
      - Test suite: .claude/skills/backlog/tests/
      - Plan acceptance criteria: plan/tasks-773-migrate-backlog-github-rest-to-graphql.md (acceptance_criteria section)

      ## Requirements
      1. Run: uv run pytest .claude/skills/backlog/tests/ -x -q
         — record exit code and summary
      2. Run: uv run pytest .claude/skills/backlog/tests/ --cov=.claude/skills/backlog/backlog_core/github --cov-report=term-missing
         — record coverage percentage for github.py
      3. Run: uv run ruff check .claude/skills/backlog/backlog_core/github.py .claude/skills/backlog/tests/
         — record exit code
      4. Run: grep -n "get_label" .claude/skills/backlog/backlog_core/github.py | grep -v "_resolve_labels_graphql" | grep -v "#"
         — confirm exit code 1 (no matches outside helper)
      5. Check pyproject.toml to confirm no new packages were added (diff against original)
      6. Write plan/T5-verification-migrate-backlog-github-rest-to-graphql.md with:
         - Pass/fail status for each of the 9 acceptance criteria (AC1–AC9)
         - Command output evidence for each criterion
         - Overall verdict: PASS (all 9 pass) or FAIL (list failing criteria)

      ## Constraints
      - Do NOT modify any source or test files — this task is verification only
      - If any criterion fails, report FAIL and list root cause — do not attempt fixes

      ## Expected Outputs
      - plan/T5-verification-migrate-backlog-github-rest-to-graphql.md

      ## Acceptance Criteria
      1. Verification report exists at plan/T5-verification-migrate-backlog-github-rest-to-graphql.md
      2. Report contains Pass/Fail status for all 9 plan acceptance criteria
      3. Report overall verdict is PASS

      ## Verification Steps
      1. cat plan/T5-verification-migrate-backlog-github-rest-to-graphql.md
         — confirms report exists and verdict is PASS
      2. If verdict is FAIL: report blocked tasks and failing criteria to orchestrator

      ## Handoff
      Return: STATUS: DONE + path to verification report
      Include: overall verdict (PASS or FAIL) and list of any failing criteria

  - task: T99
    title: "TN: Verify implementation against baseline"
    status: not-started
    agent: tn-verification-gate
    dependencies: ["T1", "T2", "T3", "T4", "T5"]
    priority: 5
    complexity: low
    is-bookend: true
    bookend-type: tn-verification
    accuracy-risk: low
    skills: []
    body: |
      ## Context
      TN runs after all implementation tasks complete. It re-runs every structured
      acceptance criterion and compares results against the T0 baseline to detect regressions.

      ## Objective
      Re-run acceptance criteria and compare against T0 baseline; write verdict to
      plan/TN-verification-migrate-backlog-github-rest-to-graphql.yaml.

      ## Inputs
      - Plan file: plan/tasks-773-migrate-backlog-github-rest-to-graphql.md
        (acceptance_criteria_structured entries: AC-TESTS, AC-COVERAGE, AC-NO-GET-LABEL-LOOP, AC-LINTING)
      - T0 baseline: plan/T0-baseline-migrate-backlog-github-rest-to-graphql.yaml

      ## Requirements
      1. For each criterion in acceptance_criteria_structured, run its check_command via Bash
      2. Compare exit code against T0 baseline using the 4-cell status matrix:
         - T0 pass + TN pass = passed
         - T0 pass + TN fail = regressed (blocks)
         - T0 fail + TN fail = pre-existing-fail
         - T0 fail + TN pass = newly-passing
      3. Write per-criterion verdict and list of BookendVerification records to
         plan/TN-verification-migrate-backlog-github-rest-to-graphql.yaml
      4. Overall verdict is PASS only when no criterion has status "regressed"

      ## Expected Outputs
      - plan/TN-verification-migrate-backlog-github-rest-to-graphql.yaml

      ## Acceptance Criteria
      1. plan/TN-verification-migrate-backlog-github-rest-to-graphql.yaml exists
      2. No criterion has status "regressed"

      ## Verification Steps
      1. cat plan/TN-verification-migrate-backlog-github-rest-to-graphql.yaml
         and confirm no criterion has status: regressed

---

## Context Manifest

Generated by context-gathering agent on 2026-03-17

### How This Currently Works: Backlog MCP GitHub Label Integration

When a user creates a backlog item or task issue via the MCP server, the request flows through the backlog operations layer into the GitHub I/O module. The architecture routes all PyGithub interactions through a single module: `.claude/skills/backlog/backlog_core/github.py`, which contains 28 public functions managing GitHub issue lifecycle (create, read, update, close, resolve, query, enrich).

**Current label resolution pattern (the N+1 problem)**:

When `create_issue_for_item()` (lines 120-126) or `create_task_issue()` (lines 540-542) need to label a new issue, they loop over label names and call `repo.get_label(name)` for each one. Each call makes a separate REST API round-trip to validate the label exists. For example:

```
create_issue_for_item() called with labels=["status:needs-grooming", "type:feature", "priority:high"]
Loop iteration 1: repo.get_label("status:needs-grooming")   — REST call #1
Loop iteration 2: repo.get_label("type:feature")           — REST call #2
Loop iteration 3: repo.get_label("priority:high")          — REST call #3
repo.create_issue(labels=[Label1, Label2, Label3])          — REST call #4
Total: 4 round-trips for one issue creation
```

If a user creates 100 backlog items in one session, that's 300 label lookups (assuming 3 labels per item) — O(N*M) where N=items and M=labels. The current REST approach fetches full Label objects from GitHub on every call; there is no per-session caching.

**Other zones audited** (per codebase analysis):

- Lines 239 (`batch_fetch_statuses`): Already optimized — single `get_issues(state="open")` REST call materializes all issues at once
- Lines 349 (`fetch_open_issues_by_title`): Already optimized — lazy pagination, no secondary per-item calls
- `state_handler.py`: Makes no direct REST calls; delegates entirely to `github.py` functions

**Existing error handling** (context for migration):

When a label is not found, `create_issue_for_item()` catches `GithubException(404)` and logs a warning via `output.warn()`. The exception is not re-raised; instead, the loop continues and the missing label is silently omitted from the label list passed to `repo.create_issue()`. This behavior must be preserved in the GraphQL migration — missing labels are silently filtered and a warning is logged for each one not found.

**Interface contract** (immutable):

All 28 public functions in `github.py` have frozen signatures. Callers in `operations.py` and `backlog.py` see identical parameter names, return types, and exception types before and after migration. All `GithubException` patterns are preserved — new internal code must translate GraphQL errors (which return `{"errors": [...]}` dicts instead of raising) into equivalent `GithubException` objects matching the HTTP status codes (404, 401, 403, 429, etc.).

### For New Feature Implementation: GraphQL Migration Scope

The migration targets only the two genuine N+1 zones identified during codebase analysis:

**In-scope for Phase 1 (primary deliverable)**:

1. **New private function `_resolve_labels_graphql()`** — accepts (gh: Github, repo_owner: str, repo_name: str, label_names: list[str]), returns list[str] of existing label names. Uses a single GraphQL query with dynamic aliases (label0: label(name: "...") { name id }, label1: label(name: "...") { name id }, etc.) to validate all labels in one round-trip. Filters null aliases (missing labels) and returns only the subset that exist. Raises `GithubException` on GraphQL errors (per ADR-004 translation table: NOT_FOUND→404, FORBIDDEN→403, RATE_LIMITED→429, INSUFFICIENT_SCOPES→403, other→502).

2. **Modify `create_issue_for_item()` lines 120-126** — replace the per-label `get_label()` loop with a single call to `_resolve_labels_graphql(gh, repo_owner, repo_name, label_names)`. Preserve warning behavior: for each label name NOT returned by the GraphQL call, log `output.warn(f"  WARNING: label '{name}' not found")`. Pass the returned list of existing label names directly to `repo.create_issue(labels=existing_label_names)`.

3. **Modify `create_task_issue()` lines 540-542** — apply identical transformation as item creation. Extract repo_owner and repo_name from repo parameter (format: "owner/name"), call `_resolve_labels_graphql()`, log warnings, pass result to `repo.create_issue()`.

**Out-of-scope (deferred or no-change)**:

- `batch_fetch_statuses()` (line 239): Already optimized for REST; Phase 2 (field projection via GraphQL) is deferred
- `fetch_open_issues_by_title()` (line 349): Already optimized; no change needed
- `state_handler.py`: Makes no direct REST calls; benefits automatically from improvements to github.py
- Other 24 public functions: No changes needed

### Technical Reference Details

**File structure and dependencies**:

- Primary target: `.claude/skills/backlog/backlog_core/github.py` (28 public functions, ~600 lines)
- Secondary files (test updates only): `.claude/skills/backlog/tests/` (18 existing test files)
- Calling code (read-only): `.claude/skills/backlog/backlog_core/operations.py`, `.claude/skills/backlog/backlog_core/backlog.py`
- Configuration: `pyproject.toml` (PyGithub >= 2.8.1 already specified)

**Existing imports in github.py**:

```python
from github import Github, Repository, Issue, Label
from github.GithubException import GithubException
from dataclasses import dataclass
from datetime import datetime
# etc.
```

**New imports needed**:

```python
from typing import TypedDict  # for _LabelNode, _GraphQLLabelResponse type hints
```

**Function signatures (public, frozen)**:

```python
def create_issue_for_item(
    repo: str,
    item: BacklogItem,
    dry_run: bool = False,
    output: Output | None = None,
) -> int | None: ...

def create_task_issue(
    repo: str,
    parent_issue_number: int,
    task: dict[str, str],
    description: str,
    acceptance_criteria: list[str],
    labels: list[str] | None = None,
    output: Output | None = None,
) -> int | None: ...
```

**New private function signature**:

```python
def _resolve_labels_graphql(
    gh: Github,
    repo_owner: str,
    repo_name: str,
    label_names: list[str],
) -> list[str]: ...
```

**GraphQL query template** (module-level constant):

The query is built dynamically with aliases label0, label1, etc. for each input label name. Query string is never f-string-interpolated with user data (security: ADR-006 in architecture spec). Based on architecture spec section 4.3, the pattern uses dynamic field aliases:

```graphql
query ResolveLabelsBatch($owner: String!, $repo: String!) {
  repository(owner: $owner, name: $repo) {
    label0: label(name: "status:needs-grooming") { name id }
    label1: label(name: "type:feature") { name id }
    label2: label(name: "priority:high") { name id }
  }
}
```

**Type aliases for GraphQL response parsing** (internal to github.py):

```python
from typing import TypedDict

class _LabelNode(TypedDict):
    name: str
    id: str

class _GraphQLLabelResponse(TypedDict):
    data: dict[str, dict[str, _LabelNode | None]]
```

**Error handling — ADR-004 translation table**:

When GraphQL response contains `{"errors": [{"type": "NOT_FOUND", ...}]}`, translate to `GithubException(404, ...)` before raising. Other type mappings:
- NOT_FOUND → 404
- FORBIDDEN → 403
- INSUFFICIENT_SCOPES → 403
- RATE_LIMITED → 429
- (other) → 502

**Test strategy**:

- Mock `gh.graphql_query()` method directly (not HTTP transport)
- Pattern: `gh_mock.graphql_query.return_value = {"data": {"repository": {"label0": {"name": "...", "id": "..."}, "label1": None, ...}}}`
- Coverage requirement: 90% line and branch coverage for github.py; 100% branch coverage for new private functions
- Test file: New `.claude/skills/backlog/tests/test_graphql_helpers.py` for `_resolve_labels_graphql()` unit tests
- Existing test updates: Modify mock setup in affected tests covering create_issue_for_item and create_task_issue to mock graphql_query instead of get_label

**Acceptance criteria** (from task file):

AC1-AC9 define the implementation contract:
- AC1: `_resolve_labels_graphql()` exists with correct signature
- AC2-AC3: Both create functions call the new helper instead of get_label() loops
- AC4: Public signatures unchanged
- AC5: GraphQL errors raise GithubException per translation table
- AC6: Missing labels silently omitted and warned (behavior preserved)
- AC7: Full test suite passes
- AC8: github.py coverage >= 90%
- AC9: No new package dependencies

**Test acceptance criteria** (structured):

- AC-TESTS: `uv run pytest .claude/skills/backlog/tests/ -x` exits 0
- AC-COVERAGE: github.py coverage >= 90%
- AC-NO-GET-LABEL-LOOP: No grep matches for get_label() outside _resolve_labels_graphql helper
- AC-LINTING: `uv run ruff check` exits 0 on modified files

**Key design decisions from architecture spec**:

- ADR-001: Targeted migration — only label N+1 zones (Phase 1), defer batch_fetch_statuses field projection (Phase 2)
- ADR-002: Private helper functions, not public GraphQL API — preserves interface stability
- ADR-003: Mock graphql_query() at method level (consistent with existing REST mock patterns)
- ADR-004: Translate GraphQL errors to GithubException with correct status codes
- ADR-005: Preserve per-function label behavior (missing label handling unchanged)
- ADR-006: state_handler.py requires no changes (delegates to github.py)
