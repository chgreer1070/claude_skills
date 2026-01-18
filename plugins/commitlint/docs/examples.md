# Usage Examples

Concrete examples of using the commitlint plugin with Claude Code.

## Example 1: Setting Up Commitlint from Scratch

**Scenario**: You have a new Node.js project and want to enforce conventional commits.

**Steps**:

1. Activate the commitlint skill in your conversation:
   ```text
   @commitlint help me set up conventional commits for this project
   ```

2. Claude will guide you through installation:
   ```bash
   npm install -D @commitlint/cli @commitlint/config-conventional
   ```

3. Claude creates the configuration file:
   ```javascript
   // commitlint.config.js
   export default {
     extends: ['@commitlint/config-conventional'],
   };
   ```

4. Claude suggests adding a pre-commit hook:
   ```bash
   npm install -D husky
   npx husky init
   echo "npx commitlint --edit \$1" > .husky/commit-msg
   ```

**Result**: All commits are now validated against conventional commits format. Messages like `feat: add login` pass, while `Added login page` fail.

---

## Example 2: Configuring Custom Rules for Your Team

**Scenario**: Your team has specific requirements - only certain types are allowed, and header length should be 72 characters max.

**Conversation**:
```text
@commitlint configure commitlint with these requirements:
- Only allow types: feat, fix, docs, test
- Header must be 72 characters or less
- Require scope for all commits
```

**Result**:

Claude creates a custom configuration:

```javascript
// commitlint.config.js
export default {
  extends: ['@commitlint/config-conventional'],
  rules: {
    // Override type-enum to only allow specific types
    'type-enum': [2, 'always', ['feat', 'fix', 'docs', 'test']],

    // Reduce header length to 72
    'header-max-length': [2, 'always', 72],

    // Require scope
    'scope-empty': [2, 'never'],
  },
};
```

**Testing**:
```bash
# Pass
echo "feat(auth): add login form" | npx commitlint

# Fail - type not allowed
echo "chore: update deps" | npx commitlint

# Fail - no scope
echo "feat: add feature" | npx commitlint

# Fail - too long
echo "feat(ui): this is a very long commit message that exceeds the 72 character limit we set" | npx commitlint
```

---

## Example 3: Debugging Validation Errors

**Scenario**: Your commit message is being rejected and you don't understand why.

**Conversation**:
```text
@commitlint my commit "Fix: authentication bug" is being rejected by commitlint. Why?
```

**Claude's Analysis**:

The commitlint skill explains:

1. **Issue**: Type "Fix" uses capital "F"
2. **Rule**: `type-case` requires lowercase
3. **Solution**: Change to `fix: authentication bug`

**Additional Details**:
```text
@commitlint show me what the type-case rule does
```

Claude explains from the rule reference:
- Rule: `type-case`
- Config: `[2, 'always', 'lower-case']`
- Effect: Commit type must be lowercase
- Pass: `fix:`, `feat:`, `docs:`
- Fail: `Fix:`, `FEAT:`, `Docs:`

---

## Example 4: Extracting Rules for AI Commit Message Generator

**Scenario**: You're building a tool that uses an LLM to generate commit messages from git diffs. You need to extract commitlint rules to constrain the LLM.

**Conversation**:
```text
@commitlint I'm building a commit message generator. Read the commitlint config in this project and give me a structured set of constraints I can include in my LLM prompt.
```

**Claude's Response**:

After reading `commitlint.config.js`, Claude extracts:

```markdown
Commit Message Constraints:

1. **Required Format**: `type(scope): subject`

2. **Allowed Types** (from type-enum):
   - feat, fix, docs, style, refactor, perf, test, build, ci, chore, revert

3. **Type Constraints**:
   - Must be lowercase
   - Cannot be empty

4. **Subject Constraints**:
   - Cannot be empty
   - Cannot end with period
   - Cannot use sentence-case, start-case, pascal-case, or upper-case
   - Must be lowercase or mixed case (e.g., "add API endpoint")

5. **Header Length**: Maximum 100 characters (entire first line)

6. **Body** (optional):
   - If present, must have blank line before it
   - Lines should be 100 characters or less

7. **Footer** (optional):
   - If present, must have blank line before it
   - Lines should be 100 characters or less
```

**Implementation Code**:

Claude provides extraction code:

```python
import json
import subprocess
from pathlib import Path

def extract_commitlint_rules(project_dir: Path) -> dict:
    """Extract commitlint rules as structured data for LLM prompts."""

    # Get resolved config
    result = subprocess.run(
        ['npx', 'commitlint', '--print-config'],
        capture_output=True,
        text=True,
        cwd=project_dir,
    )

    config = json.loads(result.stdout)
    rules = config.get('rules', {})

    constraints = {}

    # Extract type-enum
    if 'type-enum' in rules and rules['type-enum'][0] > 0:
        constraints['allowed_types'] = rules['type-enum'][2]

    # Extract header-max-length
    if 'header-max-length' in rules and rules['header-max-length'][0] > 0:
        constraints['max_header_length'] = rules['header-max-length'][2]

    # Extract scope-enum if defined
    if 'scope-enum' in rules and rules['scope-enum'][0] > 0:
        scopes = rules['scope-enum'][2]
        if scopes:  # Only if not empty array
            constraints['allowed_scopes'] = scopes

    # Check if scope is required
    if 'scope-empty' in rules:
        level, applicability = rules['scope-empty'][:2]
        if level > 0 and applicability == 'never':
            constraints['scope_required'] = True

    return constraints

# Example usage
constraints = extract_commitlint_rules(Path('.'))
print(f"Allowed types: {', '.join(constraints['allowed_types'])}")
print(f"Max header length: {constraints['max_header_length']}")
```

---

## Example 5: Integrating Validation Loop

**Scenario**: Your commit message generator needs to validate output and retry if commitlint rejects it.

**Conversation**:
```text
@commitlint show me how to validate a generated commit message and retry with error feedback
```

**Claude's Implementation**:

```python
import subprocess
from typing import Tuple, List

async def validate_commit_message(
    message: str,
    project_dir: Path,
    max_retries: int = 3
) -> Tuple[bool, str, List[str]]:
    """
    Validate commit message with commitlint.

    Args:
        message: Generated commit message
        project_dir: Project directory with commitlint config
        max_retries: Maximum validation attempts

    Returns:
        Tuple of (success, final_message, error_history)
    """
    errors_history = []
    current_message = message

    for attempt in range(max_retries):
        # Run commitlint validation
        result = subprocess.run(
            ['npx', 'commitlint'],
            input=current_message,
            capture_output=True,
            text=True,
            cwd=project_dir,
        )

        if result.returncode == 0:
            return True, current_message, errors_history

        # Parse errors
        errors = parse_commitlint_errors(result.stdout, result.stderr)
        errors_history.append({
            'attempt': attempt + 1,
            'message': current_message,
            'errors': errors,
        })

        if attempt < max_retries - 1:
            # Regenerate with error context
            current_message = await regenerate_with_errors(
                current_message,
                errors,
            )

    # Max retries reached
    return False, current_message, errors_history


def parse_commitlint_errors(stdout: str, stderr: str) -> List[str]:
    """Extract error messages from commitlint output."""
    errors = []

    # Commitlint outputs errors in format:
    # ⧗   input: Fix: bug
    # ✖   type must be lower-case [type-case]
    for line in stdout.split('\n'):
        if '✖' in line:
            errors.append(line.replace('✖', '').strip())

    return errors


async def regenerate_with_errors(
    failed_message: str,
    errors: List[str],
) -> str:
    """
    Call LLM to regenerate commit message fixing validation errors.

    This is a placeholder - implement with your LLM client.
    """
    prompt = f"""
The commit message was rejected by commitlint:

Message: {failed_message}

Errors:
{chr(10).join(f'- {err}' for err in errors)}

Generate a corrected version that passes validation.
"""

    # Your LLM call here
    return await llm.generate(prompt)
```

**Usage Example**:

```python
# Generate initial message
message = await generate_commit_message(diff)

# Validate with retry loop
success, final_message, errors = await validate_commit_message(
    message,
    project_dir=Path('.'),
    max_retries=3,
)

if success:
    print(f"Valid message: {final_message}")
else:
    print(f"Failed after retries. Error history: {errors}")
```

---

## Example 6: CI/CD Integration

**Scenario**: Configure CI to reject pull requests with invalid commit messages.

**Conversation**:
```text
@commitlint show me how to validate commits in GitHub Actions
```

**Claude's Solution**:

```yaml
# .github/workflows/commitlint.yml
name: Lint Commit Messages

on:
  pull_request:
    types: [opened, synchronize, reopened]

jobs:
  commitlint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0  # Fetch all history for all branches

      - uses: actions/setup-node@v4
        with:
          node-version: '20'

      - name: Install dependencies
        run: npm ci

      - name: Validate PR commits
        run: |
          npx commitlint --from ${{ github.event.pull_request.base.sha }} --to ${{ github.event.pull_request.head.sha }} --verbose
```

**Alternative using commitlint action**:

```yaml
# .github/workflows/commitlint.yml
name: Lint Commit Messages

on: [pull_request]

jobs:
  commitlint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - uses: wagoid/commitlint-github-action@v6
```

---

## Example 7: Monorepo Scope Configuration

**Scenario**: Your monorepo has multiple packages and you want to restrict scopes to package names.

**Conversation**:
```text
@commitlint configure scopes for my monorepo packages: api, web, mobile, shared
```

**Result**:

```javascript
// commitlint.config.js
export default {
  extends: ['@commitlint/config-conventional'],
  rules: {
    // Restrict scopes to package names
    'scope-enum': [2, 'always', [
      'api',
      'web',
      'mobile',
      'shared',
    ]],

    // Require scope for all commits
    'scope-empty': [2, 'never'],
  },
};
```

**Valid commits**:
```
feat(api): add user authentication
fix(web): resolve routing issue
docs(shared): update component docs
```

**Invalid commits**:
```
feat(backend): add feature    # 'backend' not in scope-enum
feat: add feature             # scope required but missing
```

---

## Example 8: Custom Commit Types for Documentation

**Scenario**: Your documentation team wants their own commit type.

**Conversation**:
```text
@commitlint add a custom 'content' type for documentation updates
```

**Result**:

```javascript
// commitlint.config.js
export default {
  extends: ['@commitlint/config-conventional'],
  rules: {
    // Add 'content' to standard types
    'type-enum': [
      2,
      'always',
      [
        'build',
        'chore',
        'ci',
        'content',  // Custom type
        'docs',
        'feat',
        'fix',
        'perf',
        'refactor',
        'revert',
        'style',
        'test',
      ],
    ],
  },
};
```

**Usage**:
```bash
git commit -m "content: update API documentation"
git commit -m "content: add tutorial for new feature"
```

---

## Example 9: Relaxed Rules for Merge Commits

**Scenario**: You want to enforce rules for regular commits but skip validation for merge commits.

**Conversation**:
```text
@commitlint configure to skip validation for merge commits
```

**Result**:

```javascript
// commitlint.config.js
export default {
  extends: ['@commitlint/config-conventional'],

  // Ignore merge commits (default behavior includes this)
  ignores: [
    (commit) => commit.includes('Merge pull request'),
    (commit) => commit.includes('Merge branch'),
  ],

  // Keep default ignores (includes revert, version tags)
  defaultIgnores: true,
};
```

**What gets ignored by default**:
- `Merge pull request #123 from branch`
- `Merge branch 'feature' into main`
- `Revert "previous commit"`
- `v1.2.3` (version tags)

---

## Example 10: Testing Configuration Changes

**Scenario**: You've updated your commitlint config and want to test it before committing.

**Conversation**:
```text
@commitlint how do I test my config changes?
```

**Claude's Testing Guide**:

```bash
# Test with a sample message
echo "feat(api): add endpoint" | npx commitlint

# Test invalid message
echo "Added new feature" | npx commitlint

# View resolved configuration
npx commitlint --print-config

# Test last commit
npx commitlint --last

# Test range of commits
npx commitlint --from HEAD~5

# Verbose output for debugging
echo "feat: test" | npx commitlint --verbose
```

**Interactive testing script**:

```bash
#!/bin/bash
# test-commitlint.sh

test_cases=(
  "feat(api): add user endpoint"
  "fix: resolve bug"
  "docs: update README"
  "Added feature"  # Should fail
  "FIX: bug"       # Should fail - uppercase
  "feat(api): this is a very long commit message that definitely exceeds the maximum allowed length"  # Should fail
)

for msg in "${test_cases[@]}"; do
  echo "Testing: $msg"
  echo "$msg" | npx commitlint && echo "✓ Pass" || echo "✗ Fail"
  echo "---"
done
```

---

These examples demonstrate the breadth of commitlint plugin capabilities in Claude Code, from initial setup to advanced CI/CD integration and programmatic validation for AI-powered tools.
