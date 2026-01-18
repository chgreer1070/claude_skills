# Usage Examples

This document provides concrete, real-world examples of using the python3-development plugin for various development scenarios.

---

## Example 1: Building a CLI Tool with TDD

**Scenario**: Create a CLI tool that validates JSON files against JSON Schema, using Test-Driven Development approach.

**Steps**:

### 1. Orchestrator Reads Orchestration Guide (MANDATORY)

```text
Read("~/.claude/skills/python3-development/references/python-development-orchestration.md")

# Orchestrator states workflow pattern
"I have read the orchestration guide. Using TDD workflow with agents:
 @agent-python-pytest-architect → @agent-python-cli-architect → @agent-python-code-reviewer"
```

### 2. Design Tests First

```text
Task(
  agent="agent-python-pytest-architect",
  prompt="Design comprehensive test suite for JSON schema validator CLI.

  Requirements:
  - Validate JSON files against provided schema
  - Support multiple schema formats (Draft 7, Draft 2020-12)
  - Clear error messages with line numbers
  - Exit codes: 0 (valid), 1 (invalid), 2 (error)

  Scope: tests/test_validator.py only

  Success criteria:
  - Test cases cover valid JSON, invalid JSON, malformed JSON
  - Test cases cover schema validation errors with line numbers
  - Test cases verify exit codes
  - >90% coverage target defined"
)
```

### 3. Implement to Pass Tests

```text
Task(
  agent="agent-python-cli-architect",
  prompt="Implement JSON schema validator CLI to pass test suite.

  Context:
  - Test suite exists at tests/test_validator.py
  - Must use Typer for CLI, Rich for output
  - Must support JSON Schema Draft 7 and 2020-12

  Scope: packages/json_validator/cli.py only

  Success criteria:
  - All tests pass
  - >80% coverage achieved
  - Type-safe with mypy
  - PEP 723 metadata if needed"
)
```

### 4. Validate Quality Gates

```bash
# Format first (fixes many issues)
uv run ruff format packages/json_validator/ tests/

# Lint after formatting
uv run ruff check packages/json_validator/ tests/

# Type check
uv run mypy packages/json_validator/

# Run tests with coverage
uv run pytest --cov=packages/json_validator --cov-report=term-missing

# Or use pre-commit if configured
uv run pre-commit run --all-files
```

### 5. Code Review

```text
Task(
  agent="agent-python-code-reviewer",
  prompt="Review JSON schema validator implementation.

  Focus areas:
  - Error handling patterns (fail-fast vs graceful)
  - Type safety (generics, protocols)
  - CLI UX (help text, error messages)
  - Test coverage completeness

  Files: packages/json_validator/cli.py, tests/test_validator.py"
)
```

**Result**: Production-ready CLI tool with >90% test coverage, type-safe, following all standards.

---

## Example 2: Refactoring Legacy Code

**Scenario**: Refactor legacy Python 2.7 code to modern Python 3.11+ patterns while maintaining behavior.

**Code Before**:
```python
# legacy_processor.py (Python 2.7 style)
from typing import List, Dict, Optional

def process_data(items, config):
    # type: (List[Dict], Dict) -> Optional[List[Dict]]
    """Process items according to config."""
    results = []
    for item in items:
        if config.get('filter') and not item.get('active'):
            continue
        results.append({
            'id': item['id'],
            'status': item.get('status', 'unknown')
        })
    return results if results else None
```

**Steps**:

### 1. Write Tests First (Preserve Behavior)

```python
# tests/test_processor.py
from legacy_processor import process_data

def test_process_active_items():
    """Process keeps active items when filtering enabled."""
    items = [
        {"id": 1, "active": True, "status": "ready"},
        {"id": 2, "active": False, "status": "pending"},
    ]
    config = {"filter": True}

    result = process_data(items, config)

    assert len(result) == 1
    assert result[0]["id"] == 1
    assert result[0]["status"] == "ready"

def test_process_without_filter():
    """Process includes all items when filtering disabled."""
    items = [
        {"id": 1, "active": True, "status": "ready"},
        {"id": 2, "active": False, "status": "pending"},
    ]
    config = {"filter": False}

    result = process_data(items, config)

    assert len(result) == 2

def test_process_empty_returns_none():
    """Process returns None when no items match."""
    items = [{"id": 1, "active": False}]
    config = {"filter": True}

    result = process_data(items, config)

    assert result is None
```

### 2. Run Tests (Baseline)

```bash
uv run pytest tests/test_processor.py -v
# All pass - behavior captured
```

### 3. Refactor to Modern Python

```python
# modern_processor.py (Python 3.11+ style)
from typing import TypedDict

class Item(TypedDict):
    id: int
    active: bool
    status: str

class ProcessedItem(TypedDict):
    id: int
    status: str

class Config(TypedDict, total=False):
    filter: bool

def process_data(items: list[Item], config: Config) -> list[ProcessedItem] | None:
    """Process items according to config.

    Args:
        items: List of items to process
        config: Configuration with optional 'filter' key

    Returns:
        List of processed items, or None if empty
    """
    results: list[ProcessedItem] = []

    for item in items:
        # Skip inactive items if filtering enabled
        if config.get("filter") and not item.get("active"):
            continue

        results.append({
            "id": item["id"],
            "status": item.get("status", "unknown"),
        })

    return results if results else None
```

### 4. Run Tests Again (Verify Behavior Preserved)

```bash
uv run pytest tests/test_processor.py -v
# All pass - behavior unchanged
```

### 5. Validate Quality Gates

```bash
uv run ruff format modern_processor.py tests/
uv run ruff check modern_processor.py tests/
uv run mypy modern_processor.py
uv run pytest --cov=modern_processor
```

**Changes Made**:
- Removed `typing.List`, `typing.Dict`, `typing.Optional` (use native `list`, `dict`, `|`)
- Changed `# type:` comments to inline annotations
- Used `TypedDict` for structured dictionaries
- Changed `None` return type from `Optional[List]` to `list | None`
- Added comprehensive docstrings

**Result**: Modern Python 3.11+ code with identical behavior, fully typed, passing all quality gates.

---

## Example 3: Fixing Linting Errors

**Scenario**: Resolve ruff and mypy errors in existing codebase after adding new feature.

**Initial Errors**:
```bash
$ uv run ruff check packages/
packages/auth/oauth.py:45:5: E501 Line too long (120 > 88 characters)
packages/auth/oauth.py:67:9: BLE001 Do not catch blind exception: `Exception`
packages/auth/oauth.py:89:1: D103 Missing docstring in public function

$ uv run mypy packages/
packages/auth/oauth.py:23: error: Need type annotation for "cache"
packages/auth/oauth.py:45: error: Argument 1 has incompatible type "str | None"; expected "str"
```

**Resolution**:

### 1. Format First (Fixes E501 Automatically)

```bash
uv run ruff format packages/auth/oauth.py
# Reformats to 88 character line length
```

### 2. Fix BLE001 (Blind Except)

**Before**:
```python
try:
    response = requests.get(url)
    return response.json()
except Exception as e:
    logger.error(f"Request failed: {e}")
    return None
```

**After** (specific exception):
```python
try:
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    return response.json()
except requests.RequestException as e:
    logger.error(f"Request failed: {e}")
    return None
```

**Rationale**: Catch specific exception type to avoid hiding programming errors.

### 3. Fix D103 (Missing Docstring)

**Before**:
```python
def exchange_code_for_token(code: str, redirect_uri: str) -> dict | None:
    # Implementation
    pass
```

**After**:
```python
def exchange_code_for_token(code: str, redirect_uri: str) -> dict | None:
    """Exchange authorization code for access token.

    Args:
        code: Authorization code from OAuth provider
        redirect_uri: Redirect URI used in authorization request

    Returns:
        Token dictionary with access_token and refresh_token, or None if exchange fails
    """
    # Implementation
    pass
```

### 4. Fix Mypy Type Errors

**Error**: "Need type annotation for cache"

**Before**:
```python
cache = {}
```

**After**:
```python
cache: dict[str, dict] = {}
```

**Error**: "Argument 1 has incompatible type 'str | None'; expected 'str'"

**Before**:
```python
def get_user_info(token: str | None) -> dict:
    return fetch_user_data(token)  # fetch_user_data expects str
```

**After** (type narrowing):
```python
def get_user_info(token: str | None) -> dict:
    if token is None:
        raise ValueError("Token is required")
    return fetch_user_data(token)  # Now narrowed to str
```

### 5. Verify All Checks Pass

```bash
uv run ruff check packages/auth/oauth.py
# ✅ All checks passed

uv run mypy packages/auth/oauth.py
# ✅ Success: no issues found

uv run pytest tests/test_oauth.py
# ✅ All tests pass
```

**Result**: Code passes all quality gates with issues fixed at root cause, no suppressions added.

---

## Example 4: Creating Executable Script with PEP 723

**Scenario**: Create a deployment script that uses external dependencies but remains a single portable file.

**Requirements**:
- Query GitLab API for deployment status
- Use `httpx` for async HTTP requests
- Use `rich` for progress indication
- Must be executable as single file (no virtual environment setup)

**Implementation**:

```python
#!/usr/bin/env -S uv --quiet run --active --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "httpx>=0.27.0",
#     "rich>=13.0.0",
# ]
# ///
"""Check deployment status across multiple environments.

This script queries GitLab API for deployment information and displays
a formatted summary of deployment statuses.
"""

import asyncio
import sys
from typing import TypedDict

import httpx
from rich.console import Console
from rich.table import Table

class Deployment(TypedDict):
    """Deployment information from GitLab API."""
    environment: str
    status: str
    ref: str
    created_at: str

async def fetch_deployments(project_id: int, token: str) -> list[Deployment]:
    """Fetch deployment information from GitLab API.

    Args:
        project_id: GitLab project ID
        token: GitLab API token

    Returns:
        List of deployment records
    """
    url = f"https://gitlab.com/api/v4/projects/{project_id}/deployments"
    headers = {"PRIVATE-TOKEN": token}

    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
        response.raise_for_status()
        return response.json()

def display_deployments(deployments: list[Deployment]) -> None:
    """Display deployments in formatted table.

    Args:
        deployments: List of deployment records
    """
    console = Console()
    table = Table(title="Deployment Status")

    table.add_column("Environment", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Ref", style="yellow")
    table.add_column("Created", style="blue")

    for dep in deployments:
        status_color = "green" if dep["status"] == "success" else "red"
        table.add_row(
            dep["environment"],
            f"[{status_color}]{dep['status']}[/]",
            dep["ref"],
            dep["created_at"][:10],  # Date only
        )

    console.print(table)

async def main() -> int:
    """Main entry point.

    Returns:
        Exit code: 0 for success, 1 for error
    """
    # Environment variables would be used in production
    project_id = 12345
    token = "your-token-here"

    try:
        deployments = await fetch_deployments(project_id, token)
        display_deployments(deployments)
        return 0
    except httpx.HTTPError as e:
        console = Console(stderr=True)
        console.print(f"[red]Error:[/] {e}", style="red")
        return 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
```

**Usage**:

```bash
# Make executable
chmod +x scripts/check-deployments.py

# Run directly (uv automatically installs dependencies on first run)
./scripts/check-deployments.py

# Or run with uv explicitly
uv run scripts/check-deployments.py
```

**First Run**:
```text
$ ./scripts/check-deployments.py
# uv installs httpx and rich automatically
# Then runs script
╭─────────── Deployment Status ────────────╮
│ Environment │ Status  │ Ref  │ Created   │
├─────────────┼─────────┼──────┼───────────┤
│ production  │ success │ main │ 2026-01-15│
│ staging     │ success │ dev  │ 2026-01-16│
╰─────────────┴─────────┴──────┴───────────╯
```

**Validation**:

```bash
# Validate shebang and PEP 723 metadata
/shebangpython scripts/check-deployments.py

# Output:
# ✅ Shebang correct for script with dependencies
# ✅ PEP 723 metadata present and valid
# ✅ Dependencies declared: httpx>=0.27.0, rich>=13.0.0
# ✅ File is executable
```

**Benefits**:
- Single portable file (no requirements.txt, no virtual environment)
- Dependencies declared inline (self-documenting)
- Works on any system with uv installed
- Fast execution (uv caches dependencies)

---

## Example 5: Agent Orchestration for Complex Feature

**Scenario**: Add user authentication with OAuth2 to existing CLI application, including database schema, API endpoints, and tests.

**Complexity**: Multiple components (database, API, CLI), requires architecture design, implementation, and testing.

**Orchestrator Workflow**:

### 1. Read Orchestration Guide (MANDATORY)

```text
Read("~/.claude/skills/python3-development/references/python-development-orchestration.md")

"I have read the orchestration guide. Using FEATURE ADDITION workflow with agents:
 @agent-spec-architect → @agent-spec-planner → @agent-python-cli-architect →
 @agent-python-pytest-architect → @agent-python-code-reviewer"
```

### 2. Architecture Design

```text
Task(
  agent="agent-spec-architect",
  prompt="Design architecture for OAuth2 authentication in CLI application.

  Requirements:
  - Support multiple OAuth2 providers (Google, GitHub, GitLab)
  - Store tokens securely in local keyring
  - Refresh tokens automatically
  - CLI commands: login, logout, whoami

  Scope: Architecture design only (no implementation)

  Success criteria:
  - Database schema defined
  - API flow documented
  - Security considerations addressed
  - Component boundaries clear"
)
```

**Output**:
```text
# OAuth2 Architecture

## Components
1. Auth Provider (packages/auth/provider.py)
   - Abstract base class for OAuth2 providers
   - Concrete implementations: GoogleProvider, GitHubProvider, GitLabProvider

2. Token Store (packages/auth/token_store.py)
   - Uses keyring library for secure token storage
   - Handles token refresh logic

3. CLI Commands (packages/cli/auth_commands.py)
   - login: Initiates OAuth2 flow, stores tokens
   - logout: Revokes tokens, clears storage
   - whoami: Displays current user info

## Database Schema
- tokens table: provider, access_token, refresh_token, expires_at
- users table: id, email, provider, provider_id

## Security
- Tokens stored in OS keyring (not filesystem)
- PKCE flow for public clients
- Token refresh before expiry
- Secure redirect URI validation
```

### 3. Task Breakdown

```text
Task(
  agent="agent-spec-planner",
  prompt="Create detailed implementation plan for OAuth2 authentication.

  Context:
  - Architecture design complete (see above)

  Scope: Task breakdown only (no implementation)

  Success criteria:
  - Tasks ordered by dependency
  - Each task has clear deliverable
  - Test requirements specified"
)
```

**Output**:
```text
# OAuth2 Implementation Plan

## Phase 1: Foundation (2-3 hours)
1. Setup: Install dependencies (httpx, keyring, authlib)
2. Database: Create schema and migrations
3. Tests: Write database schema tests

## Phase 2: Core Auth (4-5 hours)
4. Token Store: Implement secure token storage
5. Tests: Token store unit tests
6. Provider Base: Abstract OAuth2 provider class
7. Tests: Provider interface tests

## Phase 3: Provider Implementations (3-4 hours each)
8. Google Provider: Implement OAuth2 flow
9. Tests: Google provider integration tests
10. GitHub Provider: Implement OAuth2 flow
11. Tests: GitHub provider integration tests

## Phase 4: CLI Integration (2-3 hours)
12. CLI Commands: Implement login, logout, whoami
13. Tests: CLI command tests with mocked providers

## Phase 5: Validation (1-2 hours)
14. Integration Tests: End-to-end OAuth2 flow
15. Security Review: Token storage, PKCE, redirect validation
```

### 4. Implementation (Focused Delegations)

**Phase 1: Database**
```text
Task(
  agent="agent-python-cli-architect",
  prompt="Implement database schema for OAuth2 token storage.

  Context:
  - Schema defined in architecture (tokens, users tables)
  - Use SQLAlchemy with Alembic migrations

  Scope:
  - packages/auth/models.py (Token, User models)
  - alembic/versions/001_create_auth_tables.py

  Success criteria:
  - Models have correct fields and relationships
  - Migration creates tables correctly
  - Type-safe with mypy"
)
```

**Phase 2: Token Store**
```text
Task(
  agent="agent-python-cli-architect",
  prompt="Implement secure token storage using keyring.

  Context:
  - Token model exists (packages/auth/models.py)
  - Must store tokens in OS keyring (not filesystem)

  Scope: packages/auth/token_store.py only

  Success criteria:
  - Store, retrieve, delete tokens
  - Token refresh logic
  - Type-safe with protocols"
)

# Immediately after implementation
Task(
  agent="agent-python-pytest-architect",
  prompt="Create test suite for token store.

  Scope: tests/auth/test_token_store.py only

  Success criteria:
  - Test store/retrieve/delete operations
  - Test token refresh logic
  - Mock keyring for isolation
  - >90% coverage"
)
```

**Phase 3-4: Providers and CLI** (similar pattern for each component)

### 5. Quality Validation

```bash
# After each phase, validate quality gates
uv run ruff format packages/ tests/
uv run ruff check packages/ tests/
uv run mypy packages/
uv run pytest --cov
```

### 6. Final Code Review

```text
Task(
  agent="agent-python-code-reviewer",
  prompt="Comprehensive review of OAuth2 implementation.

  Focus areas:
  - Security: Token storage, PKCE flow, redirect validation
  - Error handling: Network failures, token expiry, invalid state
  - Type safety: Protocol usage, generic types
  - Test coverage: Unit, integration, edge cases

  Files:
  - packages/auth/provider.py
  - packages/auth/token_store.py
  - packages/auth/providers/*.py
  - packages/cli/auth_commands.py
  - tests/auth/**/*.py"
)
```

**Result**: Complete OAuth2 implementation with:
- 3 provider implementations (Google, GitHub, GitLab)
- Secure token storage
- Full CLI integration
- >90% test coverage
- Security-reviewed
- Type-safe
- Passes all quality gates

**Time**: 15-20 hours total, broken into focused 2-5 hour tasks

---

## Example 6: Type-Safe Configuration Management

**Scenario**: Replace dictionary-based configuration with type-safe structure using TypedDict and validation.

**Before** (Untyped):
```python
def load_config(path: str):
    with open(path) as f:
        return json.load(f)

config = load_config("config.json")
# config is dict[str, Any] - no type safety
db_host = config["database"]["host"]  # Might KeyError, might be wrong type
```

**After** (Type-Safe):
```python
from typing import TypedDict
from pathlib import Path
import tomllib

class DatabaseConfig(TypedDict):
    """Database connection configuration."""
    host: str
    port: int
    database: str
    user: str
    password: str

class LoggingConfig(TypedDict, total=False):
    """Logging configuration with optional fields."""
    level: str  # Optional
    file: str   # Optional

class AppConfig(TypedDict):
    """Application configuration."""
    database: DatabaseConfig
    logging: LoggingConfig
    debug: bool

def load_config(path: Path) -> AppConfig:
    """Load and validate configuration file.

    Args:
        path: Path to TOML configuration file

    Returns:
        Validated configuration

    Raises:
        ValueError: If configuration is invalid or missing required fields
        FileNotFoundError: If configuration file doesn't exist
    """
    with path.open("rb") as f:
        data = tomllib.load(f)

    # Validate structure
    if not isinstance(data.get("database"), dict):
        raise ValueError("Missing 'database' configuration")

    db = data["database"]
    if not all(k in db for k in ("host", "port", "database", "user", "password")):
        raise ValueError("Incomplete database configuration")

    # Type narrowing with validation
    config: AppConfig = {
        "database": {
            "host": str(db["host"]),
            "port": int(db["port"]),
            "database": str(db["database"]),
            "user": str(db["user"]),
            "password": str(db["password"]),
        },
        "logging": {
            "level": str(data.get("logging", {}).get("level", "INFO")),
            "file": str(data.get("logging", {}).get("file", "")),
        },
        "debug": bool(data.get("debug", False)),
    }

    return config

# Usage with type safety
config = load_config(Path("config.toml"))
# config is AppConfig - mypy knows all fields

db_host: str = config["database"]["host"]  # ✅ Type-safe
db_port: int = config["database"]["port"]  # ✅ Type-safe
log_level: str = config["logging"]["level"]  # ✅ Type-safe

# Mypy catches errors at compile time
db_host = config["database"]["invalid_key"]  # ❌ Mypy error: invalid key
db_port = config["database"]["host"]  # ❌ Mypy error: str assigned to int
```

**Benefits**:
- IDE autocomplete for configuration keys
- Mypy validates all configuration access at compile time
- Clear documentation of configuration structure
- Runtime validation with meaningful error messages

---

## Summary

These examples demonstrate:

1. **TDD Workflow**: Tests first, implementation second, validation third
2. **Refactoring**: Preserve behavior while modernizing patterns
3. **Linting Resolution**: Format first, fix issues at root cause
4. **PEP 723 Scripts**: Portable single-file scripts with dependencies
5. **Agent Orchestration**: Break complex features into focused delegations
6. **Type Safety**: Use TypedDict, protocols, and type narrowing for robust code

**Common Pattern** across all examples:
1. **Plan** (architecture, tests, workflow pattern)
2. **Implement** (focused scope, clear success criteria)
3. **Validate** (quality gates: format, lint, type check, test)
4. **Review** (code review agent, security considerations)
