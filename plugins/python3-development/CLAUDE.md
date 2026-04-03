# python3-development Plugin — AI-Facing Documentation

Python-specialist plugin for the development-harness SAM pipeline. Provides Python-specific
implementation agents (architect, test designer, code reviewer) and quality gates.

---

## Shared Workflow Components Moved to development-harness

SAM workflow skills and language-agnostic agents were consolidated into the `development-harness`
plugin. They are no longer present in `plugins/python3-development/`.

### Agents — invoke using the `@dh:` prefix

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
- `@dh:t0-baseline-capture`
- `@dh:tn-verification-gate`

### Skills — invoke using the `dh:` namespace

- `dh:implement-feature`
- `dh:start-task`
- `dh:complete-implementation`
- `dh:add-new-feature`
- `dh:subagent-contract`
- `dh:implementation-manager`

The canonical source files are in `plugins/development-harness/`.

---

## Key References

- Language manifest (library registry, modern patterns): `./skills/python3-development/references/language-manifest.md`

---

## Agents in This Plugin (Python-specific)

- `@python3-development:python-cli-architect` — implements Python CLI features (Typer/Rich)
- `@python3-development:python-cli-design-spec` — produces architecture specs for Python CLIs
- `@python3-development:python-pytest-architect` — writes pytest test suites
- `@python3-development:code-reviewer` — general code review with Python awareness, quality, and idioms
- `@python3-development:semantic-code-search` — semantic search over Python codebases
