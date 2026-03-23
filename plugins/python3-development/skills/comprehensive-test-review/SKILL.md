---
name: comprehensive-test-review
description: Use when reviewing pytest test suites for coverage, isolation, mock usage, naming conventions, or completeness. Activates on requests like "review test coverage", "audit test quality", or "check tests for completeness". Performs thorough checklist-driven review for test isolation, mock correctness, AAA pattern adherence, and naming standards.
argument-hint: <test_file_or_directory>
user-invocable: true
---

# Comprehensive Test Review

Perform thorough test review for the specified test files or directories.

## When to Use

- Reviewing test coverage before a release
- Auditing test quality after major refactoring
- Checking tests for completeness and best practices
- Identifying gaps in test suites

## Testing Standards

Consult `../python3-development/references/python3-standards.md` when auditing against shared testing and quality rules. The checklist below summarizes this skill’s focus; it does not replace the full standards document.

**Coverage Requirements:**

- [ ] Minimum 80% line and branch coverage
- [ ] Critical paths have 95%+ coverage
- [ ] All public functions have at least one test
- [ ] Edge cases are explicitly tested

**Test Quality:**

- [ ] Tests follow AAA (Arrange-Act-Assert) pattern
- [ ] Test names describe behavior, not implementation
- [ ] Each test verifies one logical unit
- [ ] Tests are isolated and independent

**Mocking Standards:**

- [ ] Uses pytest-mock (MockerFixture), NOT unittest.mock
- [ ] Mocks are scoped appropriately
- [ ] No over-mocking of implementation details
- [ ] External dependencies are properly stubbed

**Type Safety:**

- [ ] All fixtures have complete type hints
- [ ] Test functions have `-> None` return type
- [ ] Using Python 3.11+ syntax (`str | None`, not `Optional[str]`)

### Additional Examination Points

Beyond the standard checklist:

- **Test Isolation**: No shared state between tests
- **Mock Appropriateness**: Mocking only external dependencies
- **Execution Time**: Identifying slow tests for optimization
- **Flaky Patterns**: Tests dependent on timing, order, or external state
- **Naming Clarity**: Test names that explain intent and expected behavior

## Analysis Process

1. **Gather test files** in specified path
2. **Run coverage analysis** with `uv run pytest --cov`
3. **Check each test** against the standard checklist
4. **Identify gaps** in coverage and quality
5. **Generate recommendations** prioritized by impact

## Output Format

Provide findings in this structure:

```markdown
## Test Review Summary

### Coverage Analysis
- Overall: X%
- Critical modules: Y%
- Gaps identified: [list]

### Quality Issues
**HIGH Priority:**
- [Issue with location and fix]

**MEDIUM Priority:**
- [Issue with recommendation]

**LOW Priority:**
- [Minor improvements]

### Recommendations
1. [Prioritized action items]
```

## Related Skills

- **python3-test-design**: Test architecture planning
- **python-pytest-architect**: Test implementation

## Related Agent

For implementing test improvements, use the `python-pytest-architect` agent.
