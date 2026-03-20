# python3-development Plugin — AI-Facing Documentation

Python-specialist plugin for the development-harness SAM pipeline. Provides Python-specific
implementation agents (architect, test designer, code reviewer) and quality gates.

---

## Shared Workflow Agents Moved to development-harness

The following agents were moved from this plugin to the `development-harness` plugin in the
deduplication refactor. They are no longer present in `plugins/python3-development/agents/`.

Invoke them using the `@dh:` prefix:

- `@dh:feature-researcher`
- `@dh:codebase-analyzer`
- `@dh:context-gathering`
- `@dh:context-refinement`
- `@dh:plan-validator`
- `@dh:feature-verifier`
- `@dh:integration-checker`
- `@dh:doc-drift-auditor`
- `@dh:swarm-task-planner`
- `@dh:ecosystem-researcher`

These agents are language-agnostic and owned by the harness. The canonical source files are
in `plugins/development-harness/agents/`.

---

## Agents in This Plugin (Python-specific)

- `@python3-development:python-cli-architect` — implements Python CLI features (Typer/Rich)
- `@python3-development:python-cli-design-spec` — produces architecture specs for Python CLIs
- `@python3-development:python-pytest-architect` — writes pytest test suites
- `@python3-development:python-code-reviewer` — reviews Python code for quality and idioms
- `@python3-development:code-reviewer` — general code review with Python awareness
- `@python3-development:t0-baseline-capture` — captures baseline metrics before implementation
- `@python3-development:tn-verification-gate` — verifies acceptance criteria post-implementation
- `@python3-development:semantic-code-search` — semantic search over Python codebases
