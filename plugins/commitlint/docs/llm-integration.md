# LLM Integration Guide

This guide explains how to integrate commitlint validation into AI-powered commit message generation tools.

## Overview

The commitlint plugin provides knowledge and patterns for:

1. **Rule Extraction** - Converting commitlint config into LLM prompt constraints
2. **Validation Loop** - Programmatic validation with retry logic
3. **Error Feedback** - Parsing and feeding validation errors back to LLMs
4. **Context Optimization** - Structuring constraints for effective LLM comprehension

## Architecture Pattern

```text
┌─────────────────┐
│   Git Diff      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐     ┌──────────────────┐
│ Extract Rules   │────▶│ Commitlint Config│
└────────┬────────┘     └──────────────────┘
         │
         ▼
┌─────────────────┐
│ Generate Prompt │
│ with Constraints│
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ LLM Generates   │
│ Commit Message  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Validate with │
│   Commitlint    │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌───────┐ ┌───────┐
│ Valid │ │Invalid│
└───┬───┘ └───┬───┘
    │         │
    │         ▼
    │    ┌─────────────────┐
    │    │ Feed Errors to  │
    │    │ LLM for Retry   │
    │    └────────┬────────┘
    │             │
    │    ┌────────┘
    │    │ (max 3 attempts)
    │    │
    └────┴──────▶ Return Message
```

## Step 1: Extract Rules from Config

### Using commitlint CLI

```python
import json
import subprocess
from pathlib import Path
from typing import Dict, Any

def load_commitlint_config(project_dir: Path) -> Dict[str, Any]:
    """
    Load resolved commitlint configuration including all extends.

    Returns the full config with all rules resolved.
    """
    result = subprocess.run(
        ['npx', 'commitlint', '--print-config'],
        capture_output=True,
        text=True,
        cwd=project_dir,
        check=True,
    )

    return json.loads(result.stdout)
```

### Using Node.js API

```javascript
import load from '@commitlint/load';

async function loadConfig() {
  const config = await load();
  return {
    rules: config.rules,
    parserPreset: config.parserPreset,
    extends: config.extends,
  };
}
```

## Step 2: Convert Rules to LLM Constraints

### Rule Extraction Function

```python
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class CommitConstraints:
    """Structured commit message constraints for LLM prompts."""
    allowed_types: List[str]
    allowed_scopes: Optional[List[str]]
    scope_required: bool
    max_header_length: int
    subject_case_forbidden: List[str]
    subject_must_not_end_with: Optional[str]
    body_required: bool
    body_max_line_length: Optional[int]


def extract_constraints(config: dict) -> CommitConstraints:
    """
    Extract LLM-friendly constraints from commitlint config.

    Args:
        config: Resolved commitlint configuration from --print-config

    Returns:
        Structured constraints object
    """
    rules = config.get('rules', {})

    # Extract type-enum (required types)
    allowed_types = ['feat', 'fix']  # defaults
    if 'type-enum' in rules:
        level, applicability, types = rules['type-enum']
        if level > 0 and applicability == 'always':
            allowed_types = types

    # Extract scope-enum (allowed scopes)
    allowed_scopes = None
    if 'scope-enum' in rules:
        level, applicability, scopes = rules['scope-enum']
        if level > 0 and applicability == 'always' and scopes:
            allowed_scopes = scopes

    # Check if scope is required
    scope_required = False
    if 'scope-empty' in rules:
        level, applicability = rules['scope-empty'][:2]
        if level > 0 and applicability == 'never':
            scope_required = True

    # Extract header-max-length
    max_header_length = 100  # default
    if 'header-max-length' in rules:
        level, _, length = rules['header-max-length']
        if level > 0:
            max_header_length = length

    # Extract subject-case forbidden patterns
    subject_case_forbidden = []
    if 'subject-case' in rules:
        level, applicability, cases = rules['subject-case']
        if level > 0 and applicability == 'never':
            subject_case_forbidden = cases if isinstance(cases, list) else [cases]

    # Extract subject-full-stop
    subject_must_not_end_with = None
    if 'subject-full-stop' in rules:
        level, applicability, char = rules['subject-full-stop']
        if level > 0 and applicability == 'never':
            subject_must_not_end_with = char

    # Check if body is required
    body_required = False
    if 'body-empty' in rules:
        level, applicability = rules['body-empty'][:2]
        if level > 0 and applicability == 'never':
            body_required = True

    # Extract body-max-line-length
    body_max_line_length = None
    if 'body-max-line-length' in rules:
        level, _, length = rules['body-max-line-length']
        if level > 0:
            body_max_line_length = length

    return CommitConstraints(
        allowed_types=allowed_types,
        allowed_scopes=allowed_scopes,
        scope_required=scope_required,
        max_header_length=max_header_length,
        subject_case_forbidden=subject_case_forbidden,
        subject_must_not_end_with=subject_must_not_end_with,
        body_required=body_required,
        body_max_line_length=body_max_line_length,
    )
```

### Generate LLM Prompt Section

```python
def format_constraints_for_prompt(constraints: CommitConstraints) -> str:
    """
    Format constraints as clear instructions for LLM.

    Returns markdown-formatted constraint list.
    """
    parts = ["# Commit Message Requirements\n"]

    # Format
    parts.append("## Format")
    if constraints.scope_required:
        parts.append("- REQUIRED format: `type(scope): subject`")
    elif constraints.allowed_scopes:
        parts.append("- Format: `type(scope): subject` (scope optional but must be from allowed list)")
    else:
        parts.append("- Format: `type(scope): subject` (scope optional)")

    # Types
    parts.append("\n## Type")
    parts.append(f"- MUST be one of: {', '.join(constraints.allowed_types)}")
    parts.append("- MUST be lowercase")

    # Scope
    if constraints.allowed_scopes:
        parts.append("\n## Scope")
        if constraints.scope_required:
            parts.append("- REQUIRED")
        parts.append(f"- MUST be one of: {', '.join(constraints.allowed_scopes)}")

    # Subject
    parts.append("\n## Subject")
    parts.append(f"- MUST NOT be empty")

    if constraints.subject_case_forbidden:
        forbidden = ', '.join(constraints.subject_case_forbidden)
        parts.append(f"- MUST NOT use: {forbidden}")
        parts.append("- Use lowercase or mixed case (e.g., 'add API endpoint')")

    if constraints.subject_must_not_end_with:
        parts.append(f"- MUST NOT end with '{constraints.subject_must_not_end_with}'")

    # Header length
    parts.append("\n## Header Length")
    parts.append(f"- Entire first line MUST be {constraints.max_header_length} characters or less")

    # Body
    if constraints.body_required or constraints.body_max_line_length:
        parts.append("\n## Body")
        if constraints.body_required:
            parts.append("- REQUIRED")
        parts.append("- MUST have blank line before body")
        if constraints.body_max_line_length:
            parts.append(f"- Lines MUST be {constraints.body_max_line_length} characters or less")

    return '\n'.join(parts)
```

### Example Output

```markdown
# Commit Message Requirements

## Format
- REQUIRED format: `type(scope): subject`

## Type
- MUST be one of: feat, fix, docs, test
- MUST be lowercase

## Scope
- REQUIRED
- MUST be one of: api, web, mobile, shared

## Subject
- MUST NOT be empty
- MUST NOT use: sentence-case, start-case, pascal-case, upper-case
- Use lowercase or mixed case (e.g., 'add API endpoint')
- MUST NOT end with '.'

## Header Length
- Entire first line MUST be 72 characters or less

## Body
- MUST have blank line before body
- Lines MUST be 100 characters or less
```

## Step 3: Validation Loop with Retry

### Core Validation Function

```python
import subprocess
from typing import Tuple, List, Dict, Any

@dataclass
class ValidationResult:
    """Result of commit message validation."""
    valid: bool
    message: str
    errors: List[str]
    attempt: int


async def validate_with_retry(
    initial_message: str,
    project_dir: Path,
    llm_client: Any,
    max_attempts: int = 3,
) -> ValidationResult:
    """
    Validate commit message with automatic retry on failures.

    Args:
        initial_message: First generated commit message
        project_dir: Project directory containing commitlint config
        llm_client: LLM client for regeneration
        max_attempts: Maximum number of generation attempts

    Returns:
        ValidationResult with final message and validation status
    """
    current_message = initial_message
    error_history = []

    for attempt in range(1, max_attempts + 1):
        # Validate current message
        result = subprocess.run(
            ['npx', 'commitlint'],
            input=current_message,
            capture_output=True,
            text=True,
            cwd=project_dir,
        )

        if result.returncode == 0:
            # Success
            return ValidationResult(
                valid=True,
                message=current_message,
                errors=[],
                attempt=attempt,
            )

        # Parse errors
        errors = parse_commitlint_output(result.stdout)
        error_history.append({
            'attempt': attempt,
            'message': current_message,
            'errors': errors,
        })

        if attempt < max_attempts:
            # Regenerate with error feedback
            current_message = await regenerate_with_feedback(
                llm_client=llm_client,
                failed_message=current_message,
                errors=errors,
                attempt=attempt,
            )

    # All attempts exhausted
    return ValidationResult(
        valid=False,
        message=current_message,
        errors=errors,
        attempt=max_attempts,
    )


def parse_commitlint_output(output: str) -> List[str]:
    """
    Parse commitlint output to extract error messages.

    Commitlint format:
    ⧗   input: Fix: bug
    ✖   type must be lower-case [type-case]
    ✖   subject may not be empty [subject-empty]
    """
    errors = []

    for line in output.split('\n'):
        # Look for error marker
        if '✖' in line:
            # Remove marker and clean up
            error = line.replace('✖', '').strip()
            if error:
                errors.append(error)

    return errors
```

### Regeneration with Feedback

```python
async def regenerate_with_feedback(
    llm_client: Any,
    failed_message: str,
    errors: List[str],
    attempt: int,
) -> str:
    """
    Call LLM to regenerate commit message addressing validation errors.

    Args:
        llm_client: Your LLM client (Anthropic, OpenAI, etc.)
        failed_message: The message that failed validation
        errors: List of validation errors from commitlint
        attempt: Current attempt number (for context)

    Returns:
        Regenerated commit message
    """
    error_context = '\n'.join(f'- {err}' for err in errors)

    # Build regeneration prompt
    prompt = f"""
The following commit message failed validation (attempt {attempt}):

```text
{failed_message}
```

Validation errors:
{error_context}

Generate a corrected commit message that addresses ALL validation errors.
Return ONLY the commit message, no explanation.
"""

    response = await llm_client.generate(prompt)

    # Extract just the commit message from response
    # (implementation depends on your LLM client)
    return response.strip()
```

## Step 4: Complete Integration Example

### Full Implementation

```python
import asyncio
from pathlib import Path
from typing import Optional

class CommitMessageGenerator:
    """Generate and validate commit messages using LLM and commitlint."""

    def __init__(self, llm_client: Any, project_dir: Path):
        self.llm_client = llm_client
        self.project_dir = project_dir
        self.constraints: Optional[CommitConstraints] = None

    async def initialize(self):
        """Load commitlint config and extract constraints."""
        config = load_commitlint_config(self.project_dir)
        self.constraints = extract_constraints(config)

    async def generate(
        self,
        diff: str,
        max_attempts: int = 3,
    ) -> ValidationResult:
        """
        Generate validated commit message from git diff.

        Args:
            diff: Output from git diff
            max_attempts: Maximum validation attempts

        Returns:
            ValidationResult with final message
        """
        if not self.constraints:
            await self.initialize()

        # Build initial prompt
        constraint_text = format_constraints_for_prompt(self.constraints)

        initial_prompt = f"""
Generate a commit message for the following changes.

{constraint_text}

## Changes

```diff
{diff}
```

Generate ONLY the commit message following ALL requirements above.
"""

        # Generate initial message
        initial_message = await self.llm_client.generate(initial_prompt)
        initial_message = initial_message.strip()

        # Validate with retry loop
        result = await validate_with_retry(
            initial_message=initial_message,
            project_dir=self.project_dir,
            llm_client=self.llm_client,
            max_attempts=max_attempts,
        )

        return result


# Usage example
async def main():
    from anthropic import AsyncAnthropic

    # Initialize
    client = AsyncAnthropic(api_key="your-key")
    generator = CommitMessageGenerator(
        llm_client=client,
        project_dir=Path('.'),
    )

    # Get diff
    diff_result = subprocess.run(
        ['git', 'diff', '--staged'],
        capture_output=True,
        text=True,
    )

    # Generate and validate
    result = await generator.generate(diff_result.stdout)

    if result.valid:
        print(f"✓ Valid message after {result.attempt} attempt(s):")
        print(result.message)
    else:
        print(f"✗ Failed after {result.attempt} attempts")
        print(f"Errors: {', '.join(result.errors)}")


if __name__ == '__main__':
    asyncio.run(main())
```

## Best Practices

### 1. Always Extract Rules First

Don't hardcode commitlint rules in your prompt. Always read the project's actual configuration:

```python
# ✓ Correct
config = load_commitlint_config(project_dir)
constraints = extract_constraints(config)
prompt = generate_prompt(constraints)

# ✗ Wrong
prompt = "Use types: feat, fix, docs..."  # Hardcoded
```

### 2. Use Structured Constraints

Structure makes it easier for LLMs to understand and follow rules:

```python
# ✓ Correct - Structured
"""
MUST: type in [feat, fix, docs]
MUST NOT: end with period
MAX: 72 characters
"""

# ✗ Less effective - Unstructured
"""
Use conventional commits format with these types...
"""
```

### 3. Provide Specific Error Feedback

When validation fails, give the LLM concrete information:

```python
# ✓ Correct - Specific
"""
Errors:
- type must be lower-case [type-case]
- subject may not be empty [subject-empty]

Your message: "Fix: "
Issue: Type "Fix" has capital F, subject is empty
"""

# ✗ Less effective - Vague
"""
The commit message is invalid. Try again.
"""
```

### 4. Limit Retry Attempts

Don't retry indefinitely - 3 attempts is usually sufficient:

```python
max_attempts = 3  # Usually sufficient

# Most failures resolve by attempt 2:
# - Attempt 1: Fix obvious errors (case, punctuation)
# - Attempt 2: Fix structural issues (missing scope, length)
# - Attempt 3: Edge cases
```

### 5. Cache Resolved Config

Load config once and reuse for multiple messages:

```python
# ✓ Correct - Cache
generator = CommitMessageGenerator(llm, project_dir)
await generator.initialize()  # Load config once

for diff in diffs:
    result = await generator.generate(diff)  # Reuse config

# ✗ Inefficient - Reload every time
for diff in diffs:
    config = load_commitlint_config(project_dir)  # Slow
    result = await generate(diff, config)
```

### 6. Handle Edge Cases

Account for projects without commitlint:

```python
def load_commitlint_config(project_dir: Path) -> Optional[dict]:
    """Load config, return None if not found."""
    try:
        result = subprocess.run(
            ['npx', 'commitlint', '--print-config'],
            capture_output=True,
            text=True,
            cwd=project_dir,
            check=True,
        )
        return json.loads(result.stdout)
    except (subprocess.CalledProcessError, FileNotFoundError):
        # No commitlint installed or no config
        return None
```

## Performance Optimization

### Parallel Processing

When generating messages for multiple commits:

```python
async def generate_batch(
    generator: CommitMessageGenerator,
    diffs: List[str],
) -> List[ValidationResult]:
    """Generate multiple commit messages in parallel."""
    tasks = [generator.generate(diff) for diff in diffs]
    results = await asyncio.gather(*tasks)
    return results
```

### Config Caching

Cache resolved config across sessions:

```python
import pickle
from datetime import datetime, timedelta

class ConfigCache:
    """Cache resolved commitlint config."""

    def __init__(self, cache_file: Path):
        self.cache_file = cache_file
        self.cache_ttl = timedelta(hours=1)

    def get(self) -> Optional[dict]:
        """Get cached config if valid."""
        if not self.cache_file.exists():
            return None

        data = pickle.loads(self.cache_file.read_bytes())

        if datetime.now() - data['timestamp'] > self.cache_ttl:
            return None

        return data['config']

    def set(self, config: dict):
        """Cache config with timestamp."""
        data = {
            'config': config,
            'timestamp': datetime.now(),
        }
        self.cache_file.write_bytes(pickle.dumps(data))
```

## Testing Your Integration

### Unit Tests

```python
import pytest

@pytest.mark.asyncio
async def test_valid_message_passes():
    """Test that valid message passes validation."""
    result = await validate_with_retry(
        initial_message="feat(api): add user endpoint",
        project_dir=Path('test-project'),
        llm_client=mock_llm,
        max_attempts=3,
    )

    assert result.valid
    assert result.attempt == 1
    assert result.errors == []


@pytest.mark.asyncio
async def test_invalid_message_retries():
    """Test that invalid message triggers retry."""
    result = await validate_with_retry(
        initial_message="Fix: bug",  # Invalid: capital F
        project_dir=Path('test-project'),
        llm_client=mock_llm,
        max_attempts=3,
    )

    # Should retry and fix
    assert result.valid
    assert result.attempt > 1
```

### Integration Tests

```bash
#!/bin/bash
# test-integration.sh

# Test with real commitlint
test_case() {
  local message="$1"
  local should_pass="$2"

  echo "Testing: $message"

  if echo "$message" | npx commitlint; then
    if [ "$should_pass" = "true" ]; then
      echo "✓ Correctly passed"
    else
      echo "✗ Should have failed"
      exit 1
    fi
  else
    if [ "$should_pass" = "false" ]; then
      echo "✓ Correctly failed"
    else
      echo "✗ Should have passed"
      exit 1
    fi
  fi
}

test_case "feat(api): add endpoint" "true"
test_case "Fix: bug" "false"
test_case "feat: this is a very long commit message that exceeds the maximum allowed header length" "false"
```

## Troubleshooting

### Issue: Config not loading

**Symptom**: `load_commitlint_config()` returns error

**Solutions**:
1. Ensure `@commitlint/cli` is installed: `npm install -D @commitlint/cli`
2. Verify config file exists: `ls commitlint.config.*`
3. Test config loads: `npx commitlint --print-config`

### Issue: Validation always fails

**Symptom**: All messages rejected even when they look correct

**Debug steps**:
```python
# Add verbose output
result = subprocess.run(
    ['npx', 'commitlint', '--verbose'],
    input=message,
    capture_output=True,
    text=True,
    cwd=project_dir,
)

print("STDOUT:", result.stdout)
print("STDERR:", result.stderr)
print("Return code:", result.returncode)
```

### Issue: LLM not fixing errors

**Symptom**: Same errors on every retry attempt

**Solutions**:
1. Make error feedback more specific
2. Include examples in retry prompt:
   ```python
   prompt = f"""
   Error: type must be lower-case

   Wrong: "Fix: bug"
   Correct: "fix: bug"

   Fix your message: {failed_message}
   """
   ```
3. Use more capable model for regeneration

---

This integration pattern provides robust, validated commit message generation with proper error handling and retry logic.
