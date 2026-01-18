# Python3 Development

Python development skill providing workflows, best practices, and modern Python 3.11+ patterns for CLI applications, testing, and project management.

## Installation

**From Marketplace:**

```bash
/plugin marketplace add Jamie-BitFlight/claude_skills
/plugin install python3-development@jamie-bitflight-skills
```

**For Development:**

```bash
claude --plugin-dir /home/user/claude_skills/plugins/python3-development
```

## Capabilities

| Type | Name | Description |
|------|------|-------------|
| Skill | [python3-development](./skills/python3-development/SKILL.md) | Python development orchestration with TDD workflows, modern Python 3.11+ patterns (PEP 723, native generics, type-safe async), linting configuration, and project layout conventions |
| Command | [create-feature-task](./commands/development/create-feature-task.md) | Set up comprehensive feature development task with proper tracking |
| Command | [use-command-template](./commands/development/use-command-template.md) | Create new Claude Code command following established patterns |
| Command | [analyze-test-failures](./commands/testing/analyze-test-failures.md) | Analyze failing test cases with a balanced, investigative approach |
| Command | [comprehensive-test-review](./commands/testing/comprehensive-test-review.md) | Perform thorough test review following standard checklist |
| Command | [test-failure-mindset](./commands/testing/test-failure-mindset.md) | Set balanced investigative approach for test failures |

## Quick Start

**Activate the skill for Python development:**

```text
@python3-development
```

The skill automatically activates when working in Python projects, writing scripts, running tests, or encountering linting errors.

**Create a feature development task:**

```bash
/create-feature-task user authentication system
```

**Analyze test failures with investigative approach:**

```bash
/analyze-test-failures
```

**Review test coverage comprehensively:**

```bash
/comprehensive-test-review my_module
```

## What's Included

- **Workflow Patterns:** TDD, feature addition, refactoring, debugging, and code review
- **Modern Python:** Python 3.11+ patterns including PEP 723 inline metadata, native generics, and type-safe async
- **Reference Documentation:** 50+ modern library guides, tool registry, API specifications
- **Linting & Formatting:** Configuration and troubleshooting for ruff, mypy, and pre-commit
- **Project Conventions:** Extracted patterns from production projects
- **Testing Guidance:** Balanced approach to test failures and comprehensive test review checklists

## License

MIT
