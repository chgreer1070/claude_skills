# Pre-commit

Configure and implement git hooks using pre-commit or prek for automated code quality checks, formatting, linting, and commit message processing.

## Installation

**From Marketplace:**

```bash
/plugin marketplace add Jamie-BitFlight/claude_skills
/plugin install pre-commit@jamie-bitflight-skills
```

**For Development:**

```bash
claude --plugin-dir /home/user/claude_skills/plugins/pre-commit
```

## Capabilities

| Type | Name | Description |
|------|------|-------------|
| Skill | [pre-commit](./skills/pre-commit/SKILL.md) | When setting up automated code quality checks on git commit. When project has .pre-commit-config.yaml. When implementing git hooks for formatting, linting, or validation. When creating prepare-commit-msg hooks to modify commit messages. When distributing a tool as a pre-commit hook. |

## Quick Start

Activate the skill when working with pre-commit hooks:

```
@pre-commit
```

**Example: Creating a prepare-commit-msg hook**

```python
#!/usr/bin/env python3
"""Hook entry point for prepare-commit-msg stage."""
import sys

def main() -> int:
    """Entry point for pre-commit hook."""
    if len(sys.argv) < 2:
        print("Error: No commit message file provided", file=sys.stderr)
        return 1

    commit_msg_file = sys.argv[1]

    # Read current message
    with open(commit_msg_file, encoding='utf-8') as f:
        original_message = f.read()

    # Process message
    new_message = process_commit_message(original_message)

    # Write back modified message
    with open(commit_msg_file, 'w', encoding='utf-8') as f:
        f.write(new_message)

    return 0

def process_commit_message(message: str) -> str:
    """Transform the commit message."""
    # Your transformation logic here
    return message

if __name__ == "__main__":
    sys.exit(main())
```

Configure in `.pre-commit-hooks.yaml`:

```yaml
- id: commit-polish
  name: Polish Commit Message
  entry: commit-polish
  language: python
  stages: [prepare-commit-msg]
  pass_filenames: false
  always_run: true
```

## License

See individual skill files for license information.
