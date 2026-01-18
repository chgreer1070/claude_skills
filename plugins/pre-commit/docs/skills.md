# Skills Reference

This plugin provides one comprehensive skill for working with the pre-commit framework.

## pre-commit

**Location**: `skills/pre-commit/SKILL.md`

**Description**: When setting up automated code quality checks on git commit. When project has .pre-commit-config.yaml. When implementing git hooks for formatting, linting, or validation. When creating prepare-commit-msg hooks to modify commit messages. When distributing a tool as a pre-commit hook.

**User Invocable**: Yes (default)

**Model**: Inherits from session

**Allowed Tools**: Inherits from session

### When to Use

Activate this skill when you need to:

- **Configure git hooks** for automated code quality checks
- **Set up .pre-commit-config.yaml** in a repository
- **Implement custom hooks** for formatting, linting, or validation
- **Create prepare-commit-msg hooks** to rewrite or transform commit messages
- **Distribute a tool** as a pre-commit hook with `.pre-commit-hooks.yaml`
- **Troubleshoot hook installation** or execution issues
- **Work with prek** (Rust-based pre-commit alternative)

### Activation

The skill activates automatically when you mention pre-commit, work with pre-commit configuration files, or request git hook setup. You can also invoke it explicitly:

```
@pre-commit
```

or

```
Skill(command: "pre-commit")
```

### Core Knowledge Areas

#### 1. Hook Stages

Complete understanding of all git hook stages:

| Stage | When It Runs | Common Uses |
|-------|--------------|-------------|
| `pre-commit` | Before commit creation | Code formatting, linting, unit tests |
| `prepare-commit-msg` | Before message editor opens | Commit message rewriting |
| `commit-msg` | After message written | Message validation |
| `pre-push` | Before push to remote | Integration tests, security scans |
| `pre-merge-commit` | Before merge commit | Merge validation |
| `post-checkout` | After checkout | Environment setup |
| `post-commit` | After commit created | Notifications, logging |
| `post-merge` | After merge completes | Dependency updates |
| `manual` | Explicit invocation only | On-demand tasks |

**Critical Distinction**: The skill emphasizes that `prepare-commit-msg` can modify messages (runs before editor), while `commit-msg` can only validate (runs after editor).

#### 2. Configuration Schemas

**User Repository Configuration** (`.pre-commit-config.yaml`):
- Repository mappings with `repos`, `rev`, and `hooks`
- Default hook types for installation
- Hook overrides (stages, args, files, exclude, types)
- Execution control (fail_fast, always_run, pass_filenames)

**Hook Definition** (`.pre-commit-hooks.yaml`):
- Hook metadata (id, name, description)
- Entry points and language specification
- Stage configuration
- File pattern matching
- Argument passing behavior

#### 3. Hook Implementation Patterns

The skill provides **template code** for implementing `prepare-commit-msg` hooks:

```python
def main() -> int:
    """Entry point for pre-commit hook."""
    if len(sys.argv) < 2:
        print("Error: No commit message file provided", file=sys.stderr)
        return 1

    commit_msg_file = sys.argv[1]
    source = os.environ.get('PRE_COMMIT_COMMIT_MSG_SOURCE', '')

    with open(commit_msg_file, encoding='utf-8') as f:
        original_message = f.read()

    if not original_message.strip():
        return 0

    new_message = process_commit_message(original_message)

    with open(commit_msg_file, 'w', encoding='utf-8') as f:
        f.write(new_message)

    return 0
```

**Key Implementation Details**:
- Hook receives message file path as `sys.argv[1]`
- Environment variables: `PRE_COMMIT_COMMIT_MSG_SOURCE`, `PRE_COMMIT_COMMIT_OBJECT_NAME`
- Return 0 for success, non-zero to abort commit
- Must handle empty messages gracefully

#### 4. Common Patterns

**Language-Specific Formatters**:
- Python: black, ruff
- JavaScript/TypeScript: prettier, eslint
- Rust: fmt, clippy

**Multi-Stage Workflows**:
- Unit tests on `pre-commit`
- Integration tests on `pre-push`
- Message validation on `commit-msg`

**Hook Distribution**:
- Entry point configuration in `pyproject.toml`
- Hook definition with correct `pass_filenames` and `always_run` settings
- Version requirements specification

#### 5. Execution and Testing

**Manual Execution**:
```bash
# Run on staged files (preferred)
pre-commit run

# Run specific hook
pre-commit run hook-id

# Run on specific files (scoped operation)
pre-commit run --files path/to/file.py

# Run specific stage
pre-commit run --hook-stage prepare-commit-msg
```

**Important**: The skill warns against using `--all-files` except when explicitly requested, as it causes diff pollution and merge conflicts.

**Testing Hooks**:
```bash
# Test from local repository
pre-commit try-repo /path/to/hook-repo hook-id --verbose

# Test prepare-commit-msg hooks
pre-commit try-repo /path/to/repo hook-id \
    --commit-msg-filename .git/COMMIT_EDITMSG
```

#### 6. Troubleshooting

**Common Issues Covered**:

1. **Hook not running**: Verify installation with specific hook type
   ```bash
   pre-commit install --hook-type prepare-commit-msg
   ```

2. **Wrong arguments**: Set `pass_filenames: false` for message hooks

3. **Hook skipped**: Set `always_run: true` to run without matching files

4. **Mutable refs**: Use immutable refs (tags/SHAs) instead of branch names

5. **Execution order**: Group dependent hooks in same repository

#### 7. prek Alternative

The skill covers **prek**, a Rust-based reimplementation of pre-commit:

- **Faster execution** than Python pre-commit
- **Drop-in replacement** using same `.pre-commit-config.yaml`
- **Identical CLI** - all commands work the same way
- **Detection method**: Check `.git/hooks/pre-commit` second line

**Installation**:
```bash
uv tool install prek
# or
cargo install prek
```

All `pre-commit` commands work with `prek` by simple substitution.

### Environment Variables

**Pre-commit Framework**:
- `PRE_COMMIT_HOME`: Override cache location (default: `~/.cache/pre-commit`)
- `SKIP`: Skip specific hooks during execution

**Hook-Specific** (prepare-commit-msg only):
- `PRE_COMMIT_COMMIT_MSG_SOURCE`: Message source (message, template, merge, squash, commit)
- `PRE_COMMIT_COMMIT_OBJECT_NAME`: Commit SHA for amend operations

### Version Requirements

| Component | Minimum Version | Notes |
|-----------|-----------------|-------|
| pre-commit | 3.2.0 | Stage values match hook names |
| Python | 3.8+ | For pre-commit framework |
| Git | 2.24+ | Required for `pre-merge-commit` stage |

### Reference Files

The skill includes comprehensive reference documentation:

**[pre-commit-official-docs.md](../skills/pre-commit/references/pre-commit-official-docs.md)**: Complete collection of official documentation links including:
- Primary documentation URLs
- Git hooks specifications
- Configuration schema references
- Language support documentation
- CLI command references
- Hook repository collections
- Troubleshooting resources
- Community resources

Last verified: 2025-01-15

### Related Skills

The skill references other Claude Code skills for complementary functionality:

- **conventional-commits**: Commit message format standards
- **commitlint**: Commit message validation rules

Activate with:
```
Skill(command: "conventional-commits")
Skill(command: "commitlint")
```

### Complete Workflow Example

The skill provides a complete example of implementing a commit message rewriting tool:

**Repository Structure**:
```
commit-polish/
├── .pre-commit-hooks.yaml
├── pyproject.toml
└── src/
    └── commit_polish/
        ├── __init__.py
        └── hook.py
```

**Hook Definition**:
```yaml
- id: commit-polish
  name: Polish Commit Message
  description: Rewrites commit messages to conventional commits format
  entry: commit-polish
  language: python
  stages: [prepare-commit-msg]
  pass_filenames: false
  always_run: true
  minimum_pre_commit_version: '3.2.0'
```

**User Installation**:
```yaml
# .pre-commit-config.yaml
default_install_hook_types: [pre-commit, prepare-commit-msg]

repos:
  - repo: https://github.com/your-org/commit-polish
    rev: v1.0.0
    hooks:
      - id: commit-polish
```

This example demonstrates the complete lifecycle from hook development to user installation.

### Best Practices Encoded

The skill emphasizes several best practices:

1. **Immutable References**: Always use tags or SHAs for `rev`, never branch names
2. **Scoped Execution**: Prefer `pre-commit run --files` over `--all-files` to avoid diff pollution
3. **Correct Stage Selection**: Use `prepare-commit-msg` for rewriting, `commit-msg` for validation
4. **Proper Configuration**: Set `pass_filenames: false` and `always_run: true` for message hooks
5. **Version Pinning**: Specify `minimum_pre_commit_version` in hook definitions
6. **Testing Before Distribution**: Use `pre-commit try-repo` to test hooks locally

---

[← Back to README](../README.md)
