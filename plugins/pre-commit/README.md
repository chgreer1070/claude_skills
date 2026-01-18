# Pre-commit Plugin

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Claude Code](https://img.shields.io/badge/claude--code-compatible-purple)

Automate code quality checks, formatting, and linting using the pre-commit framework. This plugin provides comprehensive guidance for configuring git hooks, implementing commit message processing workflows, and distributing hooks as reusable tools.

## Features

- **Comprehensive Pre-commit Framework Knowledge** - Complete reference for `.pre-commit-config.yaml` and `.pre-commit-hooks.yaml` schemas
- **Commit Message Processing** - Detailed guidance for `prepare-commit-msg` and `commit-msg` hook stages
- **Hook Implementation Patterns** - Template code and best practices for creating custom hooks
- **Multi-Language Support** - Configuration patterns for Python, JavaScript, TypeScript, Rust, and more
- **prek Alternative Support** - Guidance for the faster Rust-based pre-commit alternative
- **Troubleshooting Guide** - Solutions for common hook installation and execution issues

## Installation

### Prerequisites

- Claude Code version 2.1+
- Git 2.24+ (for all hook stages)
- Pre-commit or prek tool installed in your environment

### Install Plugin

```bash
# Using Claude Code plugin system
/plugin install pre-commit

# Manual installation (if distributing as local plugin)
cp -r pre-commit ~/.claude/plugins/
cc plugin reload
```

## Quick Start

Once installed, the skill activates automatically when you:

- Work with `.pre-commit-config.yaml` files
- Implement git hooks for code quality
- Create `prepare-commit-msg` hooks for commit message processing
- Distribute tools as pre-commit hooks

Simply mention pre-commit in your request:

```
"Help me set up pre-commit hooks for Python formatting"
"Create a prepare-commit-msg hook to rewrite commit messages"
"Configure pre-commit for this repository"
```

## Capabilities

| Type | Name | Description | Invocation |
|------|------|-------------|------------|
| Skill | pre-commit | Configure git hooks using pre-commit framework for automated code quality checks, formatting, and commit message processing | Auto-activated or `@pre-commit` |

## Usage

### Setting Up Pre-commit Hooks

Ask Claude to configure pre-commit for your project:

```
"Set up pre-commit hooks for this Python project with black and ruff"
```

Claude will:
1. Create or update `.pre-commit-config.yaml`
2. Configure appropriate hooks for your language/framework
3. Install hooks with `pre-commit install`

### Implementing Commit Message Hooks

Request commit message processing workflows:

```
"Create a prepare-commit-msg hook that rewrites commit messages to conventional commits format"
```

Claude will:
1. Implement the hook with proper argument handling
2. Create `.pre-commit-hooks.yaml` definition
3. Configure `pass_filenames: false` and `always_run: true`
4. Set up entry points in `pyproject.toml`

### Working with Existing Configurations

Claude automatically applies pre-commit knowledge when you:

- Edit `.pre-commit-config.yaml` files
- Debug hook execution issues
- Update hook versions
- Configure hook stages and execution order

## Skills

### pre-commit

The pre-commit skill provides comprehensive knowledge of the pre-commit framework, including:

- Hook stage reference (pre-commit, prepare-commit-msg, commit-msg, pre-push, etc.)
- Configuration schemas for both `.pre-commit-config.yaml` and `.pre-commit-hooks.yaml`
- Implementation templates for custom hooks
- Environment variable handling
- Common patterns for formatters, linters, and validators
- Troubleshooting guidance

For detailed documentation, see [Skills Reference](./docs/skills.md).

## Examples

### Example 1: Basic Pre-commit Setup

**Scenario**: Set up pre-commit hooks for a Python project

**Request**:
```
"Configure pre-commit hooks for this Python project with trailing whitespace removal, YAML validation, and black formatting"
```

**Result**: Claude creates `.pre-commit-config.yaml`:

```yaml
default_install_hook_types: [pre-commit]

repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml

  - repo: https://github.com/psf/black
    rev: 23.12.1
    hooks:
      - id: black
        language_version: python3.11
```

Then runs `pre-commit install` to activate the hooks.

### Example 2: Commit Message Rewriting Hook

**Scenario**: Create a hook that transforms commit messages

**Request**:
```
"Create a prepare-commit-msg hook that adds a ticket number prefix to commit messages"
```

**Result**: Claude implements:

1. **Hook script** (`src/tool/hook.py`):
```python
import sys
import os

def main() -> int:
    if len(sys.argv) < 2:
        return 1

    commit_msg_file = sys.argv[1]

    with open(commit_msg_file, encoding='utf-8') as f:
        original = f.read()

    if not original.strip():
        return 0

    # Add ticket prefix
    modified = f"[TICKET-123] {original}"

    with open(commit_msg_file, 'w', encoding='utf-8') as f:
        f.write(modified)

    return 0

if __name__ == "__main__":
    sys.exit(main())
```

2. **Hook definition** (`.pre-commit-hooks.yaml`):
```yaml
- id: ticket-prefix
  name: Add Ticket Prefix
  entry: ticket-prefix
  language: python
  stages: [prepare-commit-msg]
  pass_filenames: false
  always_run: true
```

3. **Installation instructions** for users of the hook

### Example 3: Multi-Stage Hook Configuration

**Scenario**: Run different checks at different stages

**Request**:
```
"Configure pre-commit to run unit tests on commit and integration tests on push"
```

**Result**:
```yaml
repos:
  - repo: local
    hooks:
      - id: unit-tests
        name: Run Unit Tests
        entry: pytest tests/unit
        language: system
        stages: [pre-commit]
        types: [python]
        pass_filenames: false

      - id: integration-tests
        name: Run Integration Tests
        entry: pytest tests/integration
        language: system
        stages: [pre-push]
        pass_filenames: false
        always_run: true
```

For more examples, see [Examples Documentation](./docs/examples.md).

## Troubleshooting

### Hooks Not Running

If hooks aren't executing during commits:

1. **Verify hook installation**:
   ```bash
   ls -la .git/hooks/pre-commit
   ```

2. **Install specific hook type**:
   ```bash
   pre-commit install --hook-type prepare-commit-msg
   ```

3. **Check configuration**:
   - Ensure `stages` field matches the installed hook type
   - Verify `default_install_hook_types` in `.pre-commit-config.yaml`

### Hook Receives Wrong Arguments

For `prepare-commit-msg` and `commit-msg` hooks:

- **Problem**: Hook receives staged filenames instead of message file path
- **Solution**: Set `pass_filenames: false` in hook configuration

### Hook Skipped Without Matching Files

- **Problem**: Hook doesn't run when no files match its pattern
- **Solution**: Set `always_run: true` in hook configuration

### Using prek Instead of pre-commit

The skill covers both `pre-commit` (Python) and `prek` (Rust). Commands are identical:

```bash
# pre-commit commands
pre-commit install
pre-commit run

# prek commands (same syntax)
prek install
prek run
```

## Related Skills

- **conventional-commits**: Commit message format standards
- **commitlint**: Commit message validation rules

## Contributing

This plugin is part of the Claude Code skills repository. To contribute:

1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## References

- [Pre-commit Official Site](https://pre-commit.com/)
- [Git Hooks Documentation](https://git-scm.com/docs/githooks)
- [Pre-commit GitHub Repository](https://github.com/pre-commit/pre-commit)
- [prek (Rust Alternative)](https://github.com/j178/prek)

For complete documentation links and specifications, see the skill's [reference documentation](./skills/pre-commit/references/pre-commit-official-docs.md).
