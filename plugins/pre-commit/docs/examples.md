# Usage Examples

Concrete, real-world examples of using the pre-commit plugin with Claude Code.

## Example 1: Initial Pre-commit Setup for Python Project

**Scenario**: You're starting a new Python project and want to enforce code quality standards before every commit.

**User Request**:
```
"Set up pre-commit hooks for this Python project. I want black formatting, ruff linting, trailing whitespace removal, and YAML validation."
```

**Claude's Response**:

Claude creates `.pre-commit-config.yaml`:

```yaml
default_install_hook_types: [pre-commit]

repos:
  # Standard code quality hooks
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files

  # Python formatting with black
  - repo: https://github.com/psf/black
    rev: 23.12.1
    hooks:
      - id: black
        language_version: python3.11

  # Python linting with ruff
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.9
    hooks:
      - id: ruff
        args: [--fix]
```

Then runs:
```bash
pre-commit install
pre-commit run --all-files  # Initial formatting
```

**Result**: Every commit now automatically:
1. Removes trailing whitespace
2. Fixes end-of-file issues
3. Validates YAML syntax
4. Formats Python code with black
5. Lints Python code with ruff (with auto-fix)

---

## Example 2: Implementing Ticket Number Prefix Hook

**Scenario**: Your team requires all commit messages to include a ticket number like `[PROJ-123]`. You want to create a hook that automatically adds this prefix.

**User Request**:
```
"Create a prepare-commit-msg hook that reads the current branch name, extracts a ticket number like PROJ-123, and adds it as a prefix to commit messages."
```

**Claude's Response**:

Claude creates the hook implementation:

**File**: `src/ticket_prefix/hook.py`
```python
#!/usr/bin/env python3
"""Pre-commit hook to add ticket number prefix to commit messages."""
import os
import re
import subprocess
import sys


def get_branch_name() -> str:
    """Get current git branch name."""
    result = subprocess.run(
        ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
        capture_output=True,
        text=True,
        check=True
    )
    return result.stdout.strip()


def extract_ticket_number(branch_name: str) -> str | None:
    """Extract ticket number from branch name.

    Supports patterns like:
    - feature/PROJ-123-description
    - PROJ-456-bugfix
    - bugfix/TEAM-789
    """
    match = re.search(r'([A-Z]+-\d+)', branch_name)
    return match.group(1) if match else None


def main() -> int:
    """Entry point for pre-commit hook."""
    if len(sys.argv) < 2:
        print("Error: No commit message file provided", file=sys.stderr)
        return 1

    commit_msg_file = sys.argv[1]
    source = os.environ.get('PRE_COMMIT_COMMIT_MSG_SOURCE', '')

    # Skip if message comes from amend, merge, or template
    if source in ('merge', 'squash', 'commit'):
        return 0

    # Read current message
    with open(commit_msg_file, encoding='utf-8') as f:
        original_message = f.read()

    # Skip empty messages
    if not original_message.strip():
        return 0

    # Skip if already has ticket number
    if re.match(r'\[([A-Z]+-\d+)\]', original_message):
        return 0

    # Extract ticket from branch
    branch_name = get_branch_name()
    ticket_number = extract_ticket_number(branch_name)

    if not ticket_number:
        # No ticket found - allow commit but warn
        print(
            f"Warning: No ticket number found in branch '{branch_name}'",
            file=sys.stderr
        )
        return 0

    # Add ticket prefix
    new_message = f"[{ticket_number}] {original_message}"

    # Write modified message
    with open(commit_msg_file, 'w', encoding='utf-8') as f:
        f.write(new_message)

    print(f"Added ticket prefix: [{ticket_number}]")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

**File**: `.pre-commit-hooks.yaml`
```yaml
- id: ticket-prefix
  name: Add Ticket Number Prefix
  description: Automatically adds ticket number from branch name to commit messages
  entry: ticket-prefix
  language: python
  stages: [prepare-commit-msg]
  pass_filenames: false
  always_run: true
  minimum_pre_commit_version: '3.2.0'
```

**File**: `pyproject.toml` (entry point configuration)
```toml
[project.scripts]
ticket-prefix = "ticket_prefix.hook:main"
```

**Usage**: Users add to their `.pre-commit-config.yaml`:
```yaml
default_install_hook_types: [pre-commit, prepare-commit-msg]

repos:
  - repo: https://github.com/your-org/ticket-prefix
    rev: v1.0.0
    hooks:
      - id: ticket-prefix
```

**Result**: When committing from branch `feature/PROJ-123-new-feature`:
```bash
git commit -m "Add user authentication"
# Message becomes: "[PROJ-123] Add user authentication"
```

---

## Example 3: Multi-Language Project Configuration

**Scenario**: Your project uses Python, TypeScript, and Docker. You want pre-commit hooks for all languages with appropriate formatting and linting.

**User Request**:
```
"Configure pre-commit for a project with Python (black, ruff), TypeScript (prettier, eslint), and Dockerfiles (hadolint). Also check for secrets and large files."
```

**Claude's Response**:

```yaml
default_install_hook_types: [pre-commit]
fail_fast: false  # Check all hooks even if one fails

repos:
  # General file checks
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-json
      - id: check-added-large-files
        args: ['--maxkb=1000']
      - id: check-merge-conflict
      - id: detect-private-key

  # Secret detection
  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.4.0
    hooks:
      - id: detect-secrets
        args: ['--baseline', '.secrets.baseline']

  # Python formatting
  - repo: https://github.com/psf/black
    rev: 23.12.1
    hooks:
      - id: black
        language_version: python3.11

  # Python linting
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.9
    hooks:
      - id: ruff
        args: [--fix]
        types_or: [python, pyi, jupyter]

  # TypeScript/JavaScript formatting
  - repo: https://github.com/pre-commit/mirrors-prettier
    rev: v3.1.0
    hooks:
      - id: prettier
        types_or: [javascript, jsx, ts, tsx, json, yaml, markdown, css, scss]

  # TypeScript/JavaScript linting
  - repo: https://github.com/pre-commit/mirrors-eslint
    rev: v8.56.0
    hooks:
      - id: eslint
        files: \.[jt]sx?$
        types: [file]
        additional_dependencies:
          - eslint@8.56.0
          - '@typescript-eslint/parser@6.19.0'
          - '@typescript-eslint/eslint-plugin@6.19.0'

  # Dockerfile linting
  - repo: https://github.com/hadolint/hadolint
    rev: v2.12.0
    hooks:
      - id: hadolint
        args: ['--ignore', 'DL3008']  # Allow apt-get without versions
```

**Result**: Comprehensive quality checks across all languages in the project.

---

## Example 4: Staged Testing Workflow

**Scenario**: You want to run different test suites at different stages - unit tests before commit, integration tests before push.

**User Request**:
```
"Set up pre-commit to run pytest unit tests on every commit, but only run the slower integration tests before pushing to remote."
```

**Claude's Response**:

```yaml
default_install_hook_types: [pre-commit, pre-push]

repos:
  # Unit tests on pre-commit stage
  - repo: local
    hooks:
      - id: pytest-unit
        name: Run Unit Tests
        entry: uv run pytest tests/unit -v
        language: system
        stages: [pre-commit]
        types: [python]
        pass_filenames: false
        verbose: true

  # Integration tests on pre-push stage
  - repo: local
    hooks:
      - id: pytest-integration
        name: Run Integration Tests
        entry: uv run pytest tests/integration -v
        language: system
        stages: [pre-push]
        pass_filenames: false
        always_run: true
        verbose: true

  # Type checking on both stages
  - repo: local
    hooks:
      - id: mypy
        name: Type Check with mypy
        entry: uv run mypy src/
        language: system
        stages: [pre-commit]
        types: [python]
        pass_filenames: false
```

Installation:
```bash
pre-commit install  # Installs pre-commit hook
pre-commit install --hook-type pre-push  # Installs pre-push hook
```

**Result**:
- **On commit**: Unit tests and type checking run (fast feedback)
- **On push**: Integration tests run (final validation before remote)

---

## Example 5: Custom Commit Message Format Enforcement

**Scenario**: Your team uses a specific commit message format with emoji prefixes and semantic categories.

**User Request**:
```
"Create a prepare-commit-msg hook that transforms simple commit messages into our format: [category] emoji description. Categories are feat, fix, docs, refactor. Emojis are ✨ for feat, 🐛 for fix, 📝 for docs, ♻️ for refactor."
```

**Claude's Response**:

**File**: `src/commit_format/hook.py`
```python
#!/usr/bin/env python3
"""Format commit messages with category and emoji."""
import os
import re
import sys

CATEGORY_EMOJI = {
    'feat': '✨',
    'fix': '🐛',
    'docs': '📝',
    'refactor': '♻️',
    'test': '🧪',
    'chore': '🔧',
}


def detect_category(message: str) -> str:
    """Detect category from message content."""
    message_lower = message.lower()

    if any(word in message_lower for word in ['add', 'implement', 'create', 'new']):
        return 'feat'
    elif any(word in message_lower for word in ['fix', 'bug', 'issue', 'resolve']):
        return 'fix'
    elif any(word in message_lower for word in ['doc', 'readme', 'comment']):
        return 'docs'
    elif any(word in message_lower for word in ['refactor', 'restructure', 'reorganize']):
        return 'refactor'
    elif any(word in message_lower for word in ['test', 'spec']):
        return 'test'
    else:
        return 'chore'


def format_message(message: str) -> str:
    """Format message with category and emoji."""
    # Check if already formatted
    if re.match(r'\[(feat|fix|docs|refactor|test|chore)\]', message):
        return message

    # Extract conventional commit if present
    conv_match = re.match(r'^(feat|fix|docs|refactor|test|chore):\s*(.+)', message)
    if conv_match:
        category = conv_match.group(1)
        description = conv_match.group(2)
    else:
        category = detect_category(message)
        description = message.strip()

    emoji = CATEGORY_EMOJI.get(category, '📦')
    return f"[{category}] {emoji} {description}"


def main() -> int:
    """Entry point for pre-commit hook."""
    if len(sys.argv) < 2:
        return 1

    commit_msg_file = sys.argv[1]
    source = os.environ.get('PRE_COMMIT_COMMIT_MSG_SOURCE', '')

    # Skip merge commits
    if source in ('merge', 'squash'):
        return 0

    with open(commit_msg_file, encoding='utf-8') as f:
        original_message = f.read()

    if not original_message.strip():
        return 0

    # Format the message
    formatted_message = format_message(original_message)

    with open(commit_msg_file, 'w', encoding='utf-8') as f:
        f.write(formatted_message)

    return 0


if __name__ == "__main__":
    sys.exit(main())
```

**File**: `.pre-commit-hooks.yaml`
```yaml
- id: commit-format
  name: Format Commit Messages
  description: Adds semantic category and emoji to commit messages
  entry: commit-format
  language: python
  stages: [prepare-commit-msg]
  pass_filenames: false
  always_run: true
```

**Result**: Commit message transformations:
```
"Add user authentication"     → "[feat] ✨ Add user authentication"
"fix: resolve login bug"      → "[fix] 🐛 resolve login bug"
"Update README"               → "[docs] 📝 Update README"
"Restructure database layer"  → "[refactor] ♻️ Restructure database layer"
```

---

## Example 6: Debugging Hook Execution

**Scenario**: A hook isn't running as expected and you need to troubleshoot.

**User Request**:
```
"My commit-polish hook isn't running. Help me debug it."
```

**Claude's Response**:

Claude runs diagnostic commands:

```bash
# Check if hook is installed
ls -la .git/hooks/prepare-commit-msg
# Shows: .git/hooks/prepare-commit-msg exists

# Check hook content
head -5 .git/hooks/prepare-commit-msg
# Shows: #!/usr/bin/env bash
# ... pre-commit.com ...

# Check configuration
cat .pre-commit-config.yaml | grep -A10 commit-polish
# Shows hook is configured for prepare-commit-msg stage

# Test hook manually
echo "test message" > /tmp/test-msg
pre-commit run commit-polish --hook-stage prepare-commit-msg \
    --commit-msg-filename /tmp/test-msg --verbose
# Shows: Hook execution and any errors

# Check if hook type is installed
grep prepare-commit-msg .git/hooks/prepare-commit-msg
# Confirms: prepare-commit-msg hook is present
```

**Issue Found**: Hook configured but `prepare-commit-msg` hook type wasn't installed.

**Solution**:
```bash
pre-commit install --hook-type prepare-commit-msg
```

Alternatively, add to `.pre-commit-config.yaml` to avoid future issues:
```yaml
default_install_hook_types: [pre-commit, prepare-commit-msg]
```

---

## Example 7: Migrating to prek

**Scenario**: Your CI/CD pipeline is slow and you want to try prek (Rust-based pre-commit) for faster execution.

**User Request**:
```
"How do I switch from pre-commit to prek? Will I need to change my configuration?"
```

**Claude's Response**:

No configuration changes needed! prek is a drop-in replacement.

**Installation**:
```bash
# Install prek
uv tool install prek

# Uninstall old pre-commit hooks
pre-commit uninstall
pre-commit uninstall --hook-type prepare-commit-msg

# Install with prek (same commands!)
prek install
prek install --hook-type prepare-commit-msg

# Verify installation
cat .git/hooks/pre-commit | head -5
# Now shows: github.com/j178/prek
```

**All commands work identically**:
```bash
# Before (pre-commit)
pre-commit run
pre-commit run --all-files
pre-commit autoupdate

# After (prek) - same syntax
prek run
prek run --all-files
prek autoupdate
```

**Result**: Faster hook execution with no configuration changes. Your `.pre-commit-config.yaml` remains unchanged.

---

[← Back to README](../README.md) | [View Skills Reference](./skills.md)
