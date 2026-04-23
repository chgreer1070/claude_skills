# Best Practices — Upstream Reference

Content sourced from the Agent Skills best-practices specification.

SOURCE: [best-practices.md](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices.md) (accessed 2026-04-23)

---

## Evaluation-First Methodology

Build evaluations BEFORE writing extensive documentation. This ensures the skill solves real problems rather than documenting imagined ones.

Recommended order:

1. Define 3–5 concrete input/output examples that represent the intended use case
2. Write a minimal SKILL.md that handles those examples
3. Run the examples and observe failures
4. Expand documentation based on observed failures, not anticipated ones

Skills written documentation-first accumulate guidance that was never needed and omit guidance that was discovered only during testing.

## Iterative Development with Paired Claude Instances

Hierarchical workflow for iterating on skills:

1. Claude A (expert role) — creates or edits the skill
2. Claude B (user role) — loads and uses the skill on real tasks
3. Observe where Claude B fails, takes wrong paths, or asks unnecessary questions
4. Return to Claude A with specific observations — not general impressions

This pattern surfaces failures that the skill author cannot see because they already know the correct path. Claude B starts cold and exposes gaps in the skill's instructions.

## Anti-Patterns Table

| Anti-pattern | Problem | Fix |
|---|---|---|
| Windows-style paths in examples (`C:\Users\...`) | Fails on macOS/Linux | Always use forward slashes in file paths, even on Windows |
| Offering too many options | Claude presents multiple approaches; user must choose | Provide one default approach with an explicit escape hatch for edge cases |
| Scripts that punt to Claude on error | Error handling delegated back to Claude increases failure surface | Handle errors explicitly in scripts — see "Solve, Don't Punt" below |
| Magic numbers in scripts | Constants without labels are unmaintainable | Use self-documenting constant names |
| Unverifiable intermediate outputs | Batch operations may partially fail silently | Use plan-validate-execute pattern — see below |

## MCP Tool Qualification

MCP tool references in skill content must use the fully qualified `ServerName:tool_name` format.

```text
# Correct
BigQuery:bigquery_schema
GitHub:create_issue
Slack:post_message

# Incorrect — unresolvable
bigquery_schema
create_issue
```

Unqualified tool names are ambiguous when multiple MCP servers are active. Claude may call the wrong tool or fail to resolve the reference.

SOURCE: [best-practices.md](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices.md) (accessed 2026-04-23)

## Solve, Don't Punt — Error Handling in Scripts

Scripts included in skills must handle error conditions explicitly rather than delegating error handling back to Claude.

**Wrong — punts to Claude:**

```python
result = run_query(sql)
if result.error:
    print(f"Error: {result.error}")
    # Claude must figure out what to do next
```

**Right — solves the error condition:**

```python
result = run_query(sql)
if result.error:
    if "table not found" in result.error:
        available = list_tables()
        print(f"Table not found. Available tables: {available}")
        sys.exit(2)  # Exit code 2 = blocking error with actionable output
    raise RuntimeError(f"Unrecoverable query error: {result.error}")
```

When a script exits with a clear error message and a meaningful exit code, Claude has something actionable to work with. When a script silently fails or prints a raw error, Claude must guess the recovery path.

## Plan-Validate-Execute Pattern

For skills that perform batch operations or make multiple irreversible changes, structure the workflow in three phases:

1. **Plan** — collect all intended operations and present them as a list before acting
2. **Validate** — confirm the list is correct (either user confirmation or automated check)
3. **Execute** — perform operations one at a time with per-operation status reporting

Verifiable intermediate outputs allow failures to be caught at the planning stage rather than mid-execution.

Example SKILL.md structure:

```markdown
Phase 1 — Plan: list all files to be modified and the change to be made to each.
Phase 2 — Validate: confirm the plan matches the user's intent before proceeding.
Phase 3 — Execute: apply each change; report success or failure per file.
```

## Observing Real Agent Behavior

As you iterate on skills, pay attention to how Claude actually uses them in practice. Watch for:

- Unexpected exploration paths — Claude looking for information not provided
- Missed connections — Claude not noticing a reference file that would help
- Overreliance on certain sections — one section bearing disproportionate load
- Ignored content — sections Claude never reads

Iterate based on these observations rather than assumptions. The only reliable signal is watching Claude B work through real tasks with the skill active.

SOURCE: [best-practices.md](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices.md) (accessed 2026-04-23)

## Package Dependencies for Code Execution Skills

For skills that run code in the code execution environment, explicitly list required packages in SKILL.md. Verify package availability in the code execution tool documentation before referencing them.

Packages that are available in your local environment may not be available in the code execution sandbox. Listing dependencies in SKILL.md allows the consumer to detect missing packages before running the skill.
