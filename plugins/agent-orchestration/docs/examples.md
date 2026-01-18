# Usage Examples

This document provides concrete, real-world examples of using the agent-orchestration plugin for effective task delegation.

---

## Example 1: Linting Task Delegation

**Scenario**: User requests "Fix all linting issues in the project"

**Correct Delegation**:

```text
Your ROLE_TYPE is sub-agent.

Run linting against the project. Resolve all issues at root cause.

OBSERVATIONS:
- User request: "Fix all linting issues"
- Project uses Python with ruff and mypy (observed in pyproject.toml)
- This is a skills repository with multiple skill directories

DEFINITION OF SUCCESS:
- Code quality checks (linting, formatting) performed and issues addressed per the holistic-linting skill
- All configured linting rules satisfied (ruff, mypy)
- Solutions follow existing project patterns
- Pre-commit hooks pass without errors

CONTEXT:
- Location: Project root directory
- Scope: All Python files in the project
- Constraints: None specified by user

YOUR TASK:
1. Run SlashCommand /is-it-done to understand completion criteria for linting tasks
2. Activate holistic-linting skill for comprehensive linting workflows
3. Run linting tools (ruff, mypy) to gather comprehensive error data
4. Research root causes for each error category
5. Implement fixes following project conventions
6. Re-run linting to verify all issues resolved
7. Verify /is-it-done checklist items satisfied with evidence

AVAILABLE RESOURCES:
- Python project using `uv` - activate uv skill, use `uv run python` instead of `python3`
- Linting configuration in pyproject.toml specifies rules and settings
- Check <functions> list for MCP tools - prefer specialists over built-in tools
- Full project context available including tests, configs, and documentation
```

**Why This Works**:
- Agent runs linting themselves, sees full context
- Agent can re-run tools during debugging
- No duplication of work between orchestrator and agent
- Clear success criteria with verification method

**Anti-Pattern to Avoid**:

```text
❌ INCORRECT: Pre-gathering errors

Orchestrator runs: ruff check .
Orchestrator sees: 244 errors
Orchestrator delegates: [pastes all 244 errors]

Problem: Wasted orchestrator context, duplicated agent work, caused context rot.
```

---

## Example 2: Bug Fix Delegation

**Scenario**: Authentication function fails with "KeyError: 'user_id'" when token is expired

**Correct Delegation**:

```text
Your ROLE_TYPE is sub-agent.

Fix authentication bug causing KeyError when token expires.

OBSERVATIONS:
- Error message: "KeyError: 'user_id'" (from user report)
- Occurs when authentication token is expired (reproduced in testing)
- Error location: src/auth/validator.py:87 (from stack trace)
- Expected behavior: Should return clear error message when token expired

DEFINITION OF SUCCESS:
- Function handles expired tokens gracefully
- Clear error message returned to caller
- No KeyError exceptions raised
- Test demonstrating fix: test_expired_token_handling passes
- All existing authentication tests still pass (no regressions)

CONTEXT:
- Location: src/auth/ directory
- Scope: Authentication token validation logic
- Related systems: User session management, API error handling
- Constraints: Must maintain backward compatibility with existing API

YOUR TASK:
1. Run SlashCommand /is-it-done to understand bug fix completion criteria
2. Reproduce the bug to confirm behavior
3. Investigate root cause (why KeyError instead of proper error handling)
4. Design fix that handles edge case properly
5. Implement fix following project error handling patterns
6. Write test demonstrating bug is fixed (test_expired_token_handling)
7. Run full authentication test suite to verify no regressions
8. Provide evidence: before/after test results showing fix

INVESTIGATION REQUIREMENTS:
- Trace issue from token validation → session lookup → error propagation
- Document why KeyError occurs (missing key handling in token decode)
- Identify both symptom (KeyError) AND root cause (no expiration check)
- Explain fix approach and why it addresses root cause

VERIFICATION REQUIREMENTS:
- Show test failing before fix (reproducing the bug)
- Show same test passing after fix
- Show full test suite results (no regressions)
- Show error message is clear and actionable for API consumers

AVAILABLE RESOURCES:
- Python project using `uv` - activate uv skill for testing
- Test fixtures in ./tests/fixtures/ for sample tokens
- Authentication module recently refactored (check git log for context)
- Full project context including related auth modules
```

**Result**: Agent reproduces bug, identifies root cause, implements proper error handling, verifies with tests, and provides complete evidence.

---

## Example 3: Feature Implementation Delegation

**Scenario**: User requests "Add dark mode toggle to application settings"

**Correct Delegation**:

```text
Your ROLE_TYPE is sub-agent.

Implement dark mode toggle in application settings.

OBSERVATIONS:
- User request: "Add dark mode toggle to application settings"
- Application uses React with styled-components (observed in package.json)
- Settings page exists at src/components/Settings.tsx
- No dark mode support currently implemented

DEFINITION OF SUCCESS:
- Toggle component appears in Settings page
- Clicking toggle switches between light and dark themes
- Theme preference persists across sessions (localStorage)
- All existing components render correctly in both themes
- User can switch themes without page reload
- Acceptance test: can toggle theme and see immediate visual change

CONTEXT:
- Location: src/components/ for UI, src/theme/ for theme logic
- Scope: Settings UI, theme provider, styled-components theme definitions
- Existing patterns: Component structure in src/components/, state management with React hooks
- Constraints: Must work with existing styled-components setup

YOUR TASK:
1. Run SlashCommand /is-it-done to understand feature completion criteria
2. Explore existing theme/styling implementation
3. Design theme switching architecture (context, state management, persistence)
4. Create theme definitions (light and dark color schemes)
5. Implement toggle component in Settings page
6. Add theme provider to wrap application
7. Update existing styled-components to use theme values
8. Implement localStorage persistence
9. Test theme switching in all major components
10. Verify /is-it-done criteria with evidence (screenshots, test results)

AVAILABLE RESOURCES:
- Node project using pnpm - use `pnpm` commands
- React DevTools available for component debugging
- Existing component patterns in src/components/ to follow
- styled-components documentation via MCP Ref tool (high-fidelity)
- Check <functions> list for MCP tools - prefer specialists
- Full project context including all components and styles
```

**Result**: Agent designs theme architecture, implements toggle UI, adds theme provider, updates components, tests thoroughly, provides evidence of working feature.

---

## Example 4: Pattern Expansion Scenario

**Scenario**: User says "Fix the walrus operator in _some_func()"

**User Means**: "Audit and fix ALL instances of this pattern in the file/module"

**Correct Delegation**:

```text
Your ROLE_TYPE is sub-agent.

Systematically apply walrus operator pattern across file.

OBSERVATIONS:
- User identified assign-then-check pattern at _some_func():45-47
- Pattern: variable assigned, then immediately checked in condition
- This suggests developer consistently missed walrus operator opportunities throughout development
- Code smell indicates systematic review needed across file/module

DEFINITION OF SUCCESS:
- Assign-then-check pattern eliminated from file scope
- All appropriate conditionals converted to walrus operator
- Similar patterns addressed in related code
- Code remains functionally equivalent (all tests pass)
- Improved readability by reducing variable scope and line count

CONTEXT:
- Location: src/utils/helpers.py (file containing _some_func)
- Scope: Entire file, focus on conditional blocks
- Pattern to find: variable = expression; if variable:
- Pattern to apply: if (variable := expression):
- Constraints: Maintain Python 3.8+ compatibility (walrus operator)

YOUR TASK:
1. Run SlashCommand /is-it-done to understand refactoring completion criteria
2. Fix the specific instance user identified at lines 45-47
3. Audit entire file for similar assign-then-check patterns
4. Identify all locations where walrus operator is appropriate
5. Apply walrus operator conversion to all discovered instances
6. Run tests to verify functional equivalence
7. Document pattern occurrences found and fixed (file:line references)
8. Verify /is-it-done checklist items satisfied

INVESTIGATION REQUIREMENTS:
- Search for pattern: assignment followed by if/while/for with that variable
- Distinguish appropriate uses (simplification) from inappropriate (readability loss)
- Consider whether walrus improves or harms readability in each case

VERIFICATION REQUIREMENTS:
- Show test results before refactoring (baseline)
- Show test results after refactoring (verification)
- List all locations where pattern was found and fixed
- Confirm no functional changes introduced

AVAILABLE RESOURCES:
- Python project using `uv` - activate uv skill for testing
- Python 3.11+ environment supports walrus operator
- Ruff linter configured to detect code quality issues
- Full test suite in ./tests/ to verify functional equivalence
```

**Result**: Agent finds 8 instances of assign-then-check pattern, applies walrus operator systematically, verifies tests pass, documents all changes.

**Anti-Pattern to Avoid**:

```text
❌ INCORRECT: Micromanaged delegation

OBSERVATIONS:
- Walrus operator opportunity at _some_func():45-47

YOUR TASK:
1. Create helper at line 120
2. Replace lines 127-138 with call
3. Replace lines 180-191 with call

Problem: Orchestrator already did investigation, agent becomes code-editing tool without context.
```

---

## Example 5: Investigation Delegation

**Scenario**: CI pipeline fails with "Docker container exited with code 137"

**Correct Delegation**:

```text
Your ROLE_TYPE is sub-agent.

Investigate why CI pipeline Docker container exits with code 137.

OBSERVATIONS:
- CI pipeline failure: Docker container exited with code 137
- Occurs during test execution stage (observed in pipeline logs)
- Started happening after recent dependency updates (git log shows update commit)
- Exit code 137 indicates container was killed (128 + SIGKILL signal 9)
- Local tests pass successfully, only fails in CI environment

DEFINITION OF SUCCESS:
- Root cause identified with supporting evidence
- Explanation of why code 137 occurs (memory, timeout, or other)
- Solution proposed with rationale
- Solution tested in CI environment
- Pipeline passes successfully without code 137 errors

CONTEXT:
- Location: .github/workflows/test.yml (GitHub Actions pipeline)
- Scope: Docker container configuration, resource limits, test execution
- Environment: GitHub Actions runners, Docker-in-Docker setup
- Related systems: Test suite, Docker compose, CI infrastructure

YOUR TASK:
1. Run SlashCommand /is-it-done to understand investigation completion criteria
2. Research exit code 137 meaning (SIGKILL, likely resource exhaustion)
3. Access CI logs via GitHub Actions API or `gh` CLI
4. Analyze container resource usage during test execution
5. Compare local vs CI environment differences
6. Investigate recent dependency updates for memory-hungry changes
7. Trace issue through: test execution → container resources → runner limits
8. Identify root cause with evidence
9. Propose solution based on findings
10. Test solution in CI environment
11. Verify pipeline passes with evidence

INVESTIGATION REQUIREMENTS:
- Document investigation at each layer: test → container → runner → infrastructure
- Identify symptom (exit 137) AND root cause (memory limit, timeout, etc.)
- Explain why addressing root cause instead of patching symptom
- Provide evidence: logs, metrics, resource usage data

VERIFICATION REQUIREMENTS:
- Show CI logs demonstrating code 137 error
- Show evidence of root cause (memory usage, timing, etc.)
- Show solution implementation
- Show CI pipeline passing after fix

AVAILABLE RESOURCES:
- `gh` CLI pre-authenticated for GitHub Actions logs and API access
- Docker logs accessible via GitHub Actions workflow outputs
- Check <functions> list for GitHub MCP tools - use for API queries
- Recent dependency changes in git history (git log, git diff)
- CI configuration in .github/workflows/
- Full project context including test suite and Docker configs
```

**Result**: Agent discovers CI runners have 7GB memory limit, test suite + dependencies exceed limit, proposes splitting tests or increasing runner size, implements solution, verifies pipeline passes.

---

## Example 6: Documentation Task Delegation

**Scenario**: User requests "Document the new API endpoints in README"

**Correct Delegation**:

```text
Your ROLE_TYPE is sub-agent.

Document new API endpoints in README.md.

OBSERVATIONS:
- User request: "Document the new API endpoints"
- New endpoints added in recent commit: POST /api/users, GET /api/users/:id, DELETE /api/users/:id
- Endpoints defined in src/routes/users.ts (observed in codebase)
- Existing README.md has API documentation section at lines 45-120
- Documentation style: endpoint, method, parameters, response format, example

DEFINITION OF SUCCESS:
- All three new endpoints documented in README.md
- Documentation follows existing format and style
- All code examples execute successfully (tested)
- All commands/curl examples work as documented
- Parameter descriptions are accurate and complete
- Response format examples match actual API responses

CONTEXT:
- Location: README.md API Documentation section
- Scope: Three new user management endpoints
- Existing patterns: See lines 45-120 for documentation format
- Constraints: Must follow existing style and format

YOUR TASK:
1. Run SlashCommand /is-it-done to understand documentation completion criteria
2. Read endpoint implementations to understand parameters, responses, error handling
3. Write documentation for each endpoint following existing format
4. Create curl examples for each endpoint
5. Test each curl example to verify it works
6. Capture actual API responses for example sections
7. Add parameter validation descriptions
8. Document error responses and status codes
9. Verify all code examples execute successfully
10. Provide evidence: terminal output of all examples working

INVESTIGATION REQUIREMENTS:
- Extract accurate parameter names, types, and requirements from code
- Test all documented examples to ensure accuracy
- Verify error cases documented match actual behavior
- Check authentication requirements for each endpoint

VERIFICATION REQUIREMENTS:
- Show terminal output of each curl example executing
- Show actual API responses (not assumed/fabricated)
- Demonstrate error cases work as documented
- Confirm documentation matches implementation

AVAILABLE RESOURCES:
- API server can be started with `pnpm dev` (development environment)
- curl available for testing endpoints
- Existing endpoint documentation as reference (README.md lines 45-120)
- OpenAPI spec in ./openapi.yaml may have additional details
- Full project context including route handlers and validators
```

**Result**: Agent reads endpoint implementations, tests each endpoint, captures real responses, writes accurate documentation, verifies all examples work.

**Anti-Pattern to Avoid**:

```text
❌ INCORRECT: Documentation without verification

Agent writes documentation from code review only, doesn't test examples.
Result: curl examples have wrong parameter names, response formats are assumed not actual.

Problem: Documentation claims completion without execution verification.
```

---

## Example 7: Refactoring Task Delegation

**Scenario**: User requests "Refactor duplicate validation logic into shared utility"

**Correct Delegation**:

```text
Your ROLE_TYPE is sub-agent.

Refactor duplicate validation logic into shared utility module.

OBSERVATIONS:
- User identified duplicated validation at auth.py:45, api.py:89, handlers.py:123
- All three locations validate email format using similar regex patterns
- Duplication indicates opportunity for DRY (Don't Repeat Yourself) improvement
- Pattern suggests systematic search for other validation duplicates

DEFINITION OF SUCCESS:
- Validation logic extracted to shared utility module
- All three identified locations use shared utility
- Tests pass before and after refactoring (functional equivalence)
- No behavior changes introduced
- Code coverage maintained or improved
- Similar validation patterns identified and refactored if found

CONTEXT:
- Location: src/utils/ for shared utilities, existing validation code in auth.py, api.py, handlers.py
- Scope: Email validation logic, potentially other validation patterns
- Existing patterns: Utilities in src/utils/ follow specific structure
- Constraints: Must maintain exact validation behavior (backward compatibility)

YOUR TASK:
1. Run SlashCommand /is-it-done to understand refactoring completion criteria
2. Run full test suite to establish baseline (tests must pass before refactoring)
3. Extract validation logic to src/utils/validators.py
4. Create comprehensive tests for new utility function
5. Replace duplicated code in auth.py, api.py, handlers.py with utility calls
6. Search entire codebase for other validation duplicates
7. Run test suite to verify functional equivalence (same tests pass)
8. Verify no behavior changes with before/after comparison
9. Provide evidence: test results showing functional equivalence

INVESTIGATION REQUIREMENTS:
- Identify exact validation behavior to preserve
- Search for other validation patterns that could be refactored
- Determine if validation utilities module exists or needs creation
- Document all locations where validation was found and refactored

VERIFICATION REQUIREMENTS:
- Show baseline test results before refactoring
- Show test results after refactoring match baseline
- Show all tests still pass (no regressions)
- Demonstrate functional equivalence (same inputs produce same outputs)

AVAILABLE RESOURCES:
- Python project using `uv` - activate uv skill for testing
- Test suite in ./tests/ covers validation scenarios
- Existing utilities in src/utils/ as reference for structure
- Ruff and mypy configured for code quality checks
- Full project context including all validation call sites
```

**Result**: Agent extracts validation utility, refactors three locations, finds two more duplicate validations, refactors those too, verifies all tests pass, documents changes.

---

## Example 8: Effective AVAILABLE RESOURCES

**Scenario**: Delegating Python package publishing task with comprehensive ecosystem context

**Correct AVAILABLE RESOURCES Section**:

```text
AVAILABLE RESOURCES:
- The `gh` CLI is pre-authenticated for GitHub operations (releases, tags, API queries)
- Excellent MCP servers are installed for specialized tasks - check your <functions> list and prefer MCP tools over built-in alternatives:
  - `Ref` for documentation (high-fidelity verbatim source, unlike WebFetch which returns AI summaries)
  - `context7` for library API docs (current versions, comprehensive)
  - `exa` for web research (curated, high-quality sources)
  - `PyPI` MCP server for package info and version checks
- This Python project uses `uv` exclusively - activate the `uv` skill and use:
  - `uv run python` instead of `python3`
  - `uv pip` instead of `pip`
  - `uv build` for creating distributions
  - `uv publish` for uploading to PyPI
- Build system is `hatchling` - activate the `hatchling` skill for:
  - Build configuration guidance
  - Version management patterns
  - Package metadata best practices
- PyPI credentials configured in `~/.pypirc` for authenticated uploads
- Version management follows semantic versioning (check CHANGELOG.md for patterns)
- Package validation script at `./scripts/validate-package.sh` - run before publishing
- Previous publishing documentation in `.claude/reports/publishing-checklist.md`
- CI/CD pipeline in .github/workflows/publish.yml automates releases (reference for manual process)
- Full project context available including tests, configs, and documentation
```

**Why This Works**:
1. **Describes capabilities, not constraints** - Agent learns ecosystem without feeling limited
2. **Provides tool selection guidance** - Explains when to prefer MCP tools and why
3. **References skills to activate** - Points to specialized knowledge packages
4. **Points to project resources** - Scripts, checklists, previous patterns
5. **Explains conventions** - `uv` commands, version management, validation steps
6. **Enables discovery** - Full context available for agent exploration

**Anti-Pattern to Avoid**:

```text
❌ INCORRECT: Reductive tool list

AVAILABLE RESOURCES:
- Bash tool
- Read tool
- Write tool

Problem: Agent has 50+ tools but thinks only these three are available. Misses specialized MCP servers like Ref, PyPI tools, and ecosystem-specific capabilities.
```

---

## Example 9: Post-Completion Verification

**Scenario**: Agent claims "Linting issues fixed, task complete"

**Orchestrator Verification Protocol**:

```text
I cannot accept task completion without verification evidence. According to the post-completion validation protocol for style/linting tasks, I need:

1. Terminal output showing linter execution (ruff, mypy)
2. Evidence all linting rules pass (not just exit code 0)
3. Test suite results proving no functionality broken
4. Pre-commit hook results if configured

Please execute these verification steps and provide the terminal output.
```

**Agent Provides Evidence**:

```text
Verification evidence:

1. Linting results:
$ uv run ruff check .
All checks passed! ✅

$ uv run mypy .
Success: no issues found in 45 source files ✅

2. Test suite:
$ uv run pytest
==================== 127 passed in 12.34s ====================

3. Pre-commit hooks:
$ pre-commit run --all-files
ruff.....................................................Passed
mypy.....................................................Passed
pytest-check.............................................Passed

All verification complete.
```

**Orchestrator Acceptance**:

```text
Verification evidence accepted:

- Linting: ✅ Verified via ruff and mypy output (all checks passed)
- Tests: ✅ Verified via pytest (127 passed, 0 failed)
- Pre-commit: ✅ Verified via pre-commit run (all hooks passed)

Task completion confirmed. All linting issues resolved at root cause.
```

---

## Key Takeaways

1. **Observations, Not Assumptions** - State what you've observed, not what you think
2. **Success Criteria, Not Steps** - Define WHAT must work, not HOW to implement
3. **World-Building, Not Tool Lists** - Describe ecosystem capabilities, not restrictive tool inventories
4. **Pattern Expansion** - Treat single instances as representative of broader patterns
5. **Evidence Required** - Completion claims must include terminal output, test results, demonstrations
6. **No Pre-Gathering** - Don't run commands to collect data before delegating; agents gather their own data
7. **High-Fidelity Tools** - Use Ref for technical docs, not WebFetch summaries
8. **Trust Agent Expertise** - Enable discovery and investigation, don't prescribe solutions
