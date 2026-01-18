# Commands Reference

The holistic-linting plugin provides one slash command for manual linting control and project configuration discovery.

---

## /lint

**Description**: Run linting and formatting on files or discover project linters

**Arguments**: `[path|init] [--force]`

**Model**: Inherits from session

**Color**: Orange

---

## Usage Modes

### Mode 1: Lint Files

Lint one or more files or directories:

```bash
/lint path/to/file.py
/lint path/to/directory/
/lint file1.py file2.py file3.py
```

**Behavior**:

1. Read `## LINTERS` section from `CLAUDE.md`
2. Match file extensions to formatters and linters
3. Run formatters first (auto-fix trivial issues)
4. Run linters second (report substantive issues)
5. If errors found, delegate to linting-root-cause-resolver agent
6. Verify resolution by re-running linters
7. Report completion status

**Example Output**:

```text
/lint src/auth.py

1. Reading ## LINTERS section from CLAUDE.md...
   ✓ Found formatters: ruff format [*.py]
   ✓ Found linters: ruff check [*.py], mypy [*.py], pyright [*.py]

2. Running formatter: uv run ruff format src/auth.py
   ✓ Formatted 1 file

3. Running linters:
   - uv run ruff check src/auth.py
     ✗ Found 2 errors (E501, F401)
   - uv run mypy src/auth.py
     ✗ Found 1 error (arg-type)

4. Launching linting-root-cause-resolver agent for src/auth.py...
   [Agent resolves all 3 issues]

5. Re-running linters:
   - uv run ruff check src/auth.py ✓
   - uv run mypy src/auth.py ✓
   - uv run pyright src/auth.py ✓

6. All linting errors resolved ✓
```

### Mode 2: Discover Project Linters

Scan the project and generate the `## LINTERS` section for `CLAUDE.md`:

```bash
/lint init
/lint init --force  # Overwrite existing LINTERS section
```

**Behavior**:

1. Check for existing `## LINTERS` section
2. If exists and no `--force`, show existing config and exit
3. Scan for linting configuration files:
   - `.pre-commit-config.yaml`
   - `pyproject.toml` (ruff, mypy, pyright, bandit)
   - `package.json` (eslint, prettier)
   - `.husky/` directory
   - `.eslintrc*`, `.prettierrc*`, `.markdownlint*` files
4. Identify configured formatters and linters
5. Generate `## LINTERS` section in standard format
6. Append to `CLAUDE.md` (or replace if `--force` provided)

**Example Output**:

```text
/lint init

1. Checking for existing ## LINTERS section in CLAUDE.md...
   Not found - proceeding with discovery

2. Scanning project configuration:
   ✓ Git repository detected
   ✓ Found .pre-commit-config.yaml (6 hooks)
   ✓ Found pyproject.toml with [tool.ruff], [tool.mypy], [tool.pyright]
   ✓ Found package.json with prettier, eslint
   ✓ Found .markdownlint.json

3. Generating LINTERS section...

## LINTERS

git pre-commit hooks: enabled
pre-commit tool: pre-commit

### Formatters

- ruff format [*.py]
- prettier [*.{ts,tsx,json,md}]
- markdownlint-cli2 [*.md]

### Static Checking and Linting

- ruff check [*.py]
- mypy [*.py]
- pyright [*.py]
- eslint [*.{ts,tsx}]
- markdownlint-cli2 [*.md]

4. Appended to CLAUDE.md ✓
```

---

## File Pattern Matching

When determining which linters apply to files, the command uses these standard patterns:

| File Type | Extension Pattern | Formatters | Linters |
|-----------|-------------------|------------|---------|
| Python | `*.py` | ruff format | ruff check, mypy, pyright, bandit |
| JavaScript/TypeScript | `*.{js,ts,jsx,tsx}` | prettier | eslint |
| Markdown | `*.{md,markdown}` | markdownlint-cli2 | markdownlint-cli2 |
| Shell | `*.{sh,bash,zsh,fish}` | shfmt | shellcheck |
| JSON | `*.json` | prettier | (none) |
| YAML | `*.{yml,yaml}` | prettier | (none) |

---

## Implementation Details

### Lint Mode Workflow

```text
[/lint <path>]
  → [Read ## LINTERS from CLAUDE.md]
  → [Match files to tools by extension]
  → [Run formatters (auto-fix phase)]
  → [Run linters (validation phase)]
  → [If errors: Delegate to linting-root-cause-resolver]
  → [Verify resolution]
  → [Report completion]
```

### Discovery Mode Workflow

```text
[/lint init]
  → [Check for existing ## LINTERS section]
  → [If exists and no --force: Show and exit]
  → [Scan configuration files]
  → [Identify formatters and linters]
  → [Generate ## LINTERS section]
  → [Append/replace in CLAUDE.md]
  → [Report completion]
```

---

## Scoped Operations

**IMPORTANT**: Always use scoped operations (`--files` or specific paths) rather than `--all-files` when running git hooks.

**Why Scoping Matters**:

```bash
# ✅ Good - Only formats files in current branch
uv run ./scripts/detect-hook-tool.py run --files src/auth.py

# ❌ Bad - Formats entire repository
uv run ./scripts/detect-hook-tool.py run --all-files
```

**Problems with `--all-files`**:
- **Diff pollution**: Unrelated formatting changes appear in merge requests
- **Merge conflicts**: Changes to files not part of your feature
- **Broken git blame**: History attribution lost for mass-formatted files

**When to use `--all-files`**: ONLY when explicitly requested by the user for repository-wide cleanup.

---

## Git Hook Tool Detection

For projects with `.pre-commit-config.yaml`, the command uses `detect-hook-tool.py` to identify and run the correct tool:

```bash
# Detect tool (outputs 'prek' or 'pre-commit')
uv run ./scripts/detect-hook-tool.py

# Run detected tool with arguments
uv run ./scripts/detect-hook-tool.py run --files path/to/file.py

# Check different repository on specific files
uv run ./scripts/detect-hook-tool.py --directory /path/to/repo run --files path/to/file.py
```

**Detection Logic**: Reads `.git/hooks/pre-commit` line 2, token 5 to identify the tool. Defaults to `prek` if file missing.

**Note**: prek is a Rust-based drop-in replacement for pre-commit. Both tools use the same `.pre-commit-config.yaml` and have identical CLI interfaces.

---

## Error Handling

### If CLAUDE.md Doesn't Exist

- **In lint mode**: Warn and suggest running `/lint init`
- **In init mode**: Create CLAUDE.md with LINTERS section

### If Tools Aren't Installed

Show which tools are missing and suggest installation:

```text
Missing tools:
  - ruff: Install with `uv add --dev ruff`
  - mypy: Install with `uv add --dev mypy`
  - pyright: Install with `uv add --dev pyright`
```

### If Linting Errors Persist

Show remaining errors and ask user:

```text
Remaining errors after agent resolution:
  - src/auth.py:45 - E501 line too long

Continue investigation or accept current state?
```

---

## Examples

### Example 1: Lint Single File

```bash
/lint src/auth.py
```

**Flow**:
1. Read CLAUDE.md LINTERS section
2. Identify Python formatters and linters
3. Format: `ruff format src/auth.py`
4. Lint: `ruff check`, `mypy`, `pyright` on src/auth.py
5. Find 3 errors (2 ruff, 1 mypy)
6. Delegate to linting-root-cause-resolver
7. Agent resolves all issues
8. Verify: All linters pass
9. Report completion ✓

### Example 2: Lint Multiple Files

```bash
/lint src/auth.py src/models.py tests/test_auth.py
```

**Flow**:
1. Read CLAUDE.md LINTERS section
2. Format all 3 files
3. Lint all 3 files (find errors in 2 files)
4. Launch concurrent agents:
   - Agent 1: src/auth.py
   - Agent 2: src/models.py
5. Both agents complete successfully
6. Verify: All files clean
7. Report completion ✓

### Example 3: Discover Linters (First Time)

```bash
/lint init
```

**Flow**:
1. Check CLAUDE.md - no LINTERS section found
2. Scan project configuration
3. Find pre-commit, pyproject.toml, package.json configs
4. Generate LINTERS section with 3 formatters, 5 linters
5. Append to CLAUDE.md
6. Report completion ✓

### Example 4: Re-Discover Linters (Force)

```bash
/lint init --force
```

**Flow**:
1. Check CLAUDE.md - LINTERS section exists
2. `--force` provided, remove existing section
3. Re-scan project configuration
4. Generate updated LINTERS section
5. Replace in CLAUDE.md
6. Report completion ✓

### Example 5: Lint Directory

```bash
/lint src/
```

**Flow**:
1. Read CLAUDE.md LINTERS section
2. Find all Python files in src/
3. Format all files
4. Lint all files
5. Launch concurrent agents for files with errors
6. Verify all files clean
7. Report completion ✓

---

## Integration with holistic-linting Skill

The `/lint` command complements the holistic-linting skill:

- **Skill**: Automatic linting during normal development workflow
- **Command**: Manual linting invocation and configuration discovery

**When to Use Command**:
- Setting up linting for a new project (`/lint init`)
- Quick manual lint check on specific files
- Verifying linting configuration without full workflow

**When Skill Activates Automatically**:
- During normal code editing and implementation
- When Claude completes tasks involving file modifications
- Automatically when project has linting configuration

---

## Notes

- The `/lint` command respects the holistic-linting skill philosophy: format first, lint second, resolve systematically
- Orchestrators should launch concurrent linting-root-cause-resolver agents when multiple files have errors
- Sub-agents should use this command on touched files before completing tasks
- The init mode creates a "cache" in CLAUDE.md to avoid repeated configuration discovery overhead
- Use scoped operations to prevent diff pollution from mass formatting

---

[← Back to README](../README.md)
