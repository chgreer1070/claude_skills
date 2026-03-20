# Repository Discovery Patterns

**Analysis Date:** 2026-03-20
**Package:** claude_skills
**Focus:** Repo-discovery patterns for backlog #852 (hardcoded-repo-reference replacement)

---

## Current Hardcoded Pattern

**Hardcoded constant:** `DEFAULT_REPO = "Jamie-BitFlight/claude_skills"`

**Locations:**

1. `plugins/development-harness/backlog_core/models.py:60` — imported by multiple modules
2. `.claude/skills/gh/scripts/github_project_setup.py:55` — CLI tool for GitHub operations

**Usage in functions:**

All functions accepting `repo` parameter use the pattern:

```python
def function_name(repo: str = DEFAULT_REPO, ...) -> T:
    # PyGithub call:
    repository = gh.get_repo(repo)  # Format: "OWNER/REPO"
```

**Affected functions in development-harness plugin** (`plugins/development-harness/backlog_core/`):

- `github.py:123` — `get_github(repo: str = DEFAULT_REPO)`
- `github.py:147` — `try_get_github(repo: str = DEFAULT_REPO)`
- `github.py:210` — `fetch_issue_or_milestone(issue_num, repo=DEFAULT_REPO)`
- `github.py:239` — `list_issues(filters, repo=DEFAULT_REPO)`
- `github.py:269` — `check_open_prs_for_issue(issue_num, repo=DEFAULT_REPO)`
- `github.py:300` — `batch_fetch_statuses(items, repo=DEFAULT_REPO)`
- `github.py:331` — `fetch_item_status(item, repo=DEFAULT_REPO)`
- `github.py:351` — `apply_status_in_progress(item, repo=DEFAULT_REPO)`
- `github.py:370` — `apply_status_verified(item, repo=DEFAULT_REPO)`
- `github.py:436` — `view_enrich_from_github(result, issue_num, repo=DEFAULT_REPO)`
- `operations.py:196` — `_rename_item_title(item, title, repo=DEFAULT_REPO)`
- `operations.py:237` — `_apply_plan_to_item(item, plan, repo=DEFAULT_REPO)`
- `operations.py:913-2155` — 15+ additional functions with `repo=DEFAULT_REPO` parameter

---

## Repository Root Discovery Pattern

**Function:** `_resolve_repo_root()` in `plugins/development-harness/backlog_core/models.py:20-35`

```python
def _resolve_repo_root(project_dir: str | None = None) -> Path:
    """Return the repository root path.

    Args:
        project_dir: Explicit project directory path, typically passed via
            ``--project-dir`` CLI argument when the server is installed as a
            plugin (where ``__file__`` points to the plugin cache, not the
            user's project).  When ``None``, falls back to ``Path.cwd()``
            which is correct for in-repo development.

    Returns:
        Resolved Path to the repository root.
    """
    if project_dir:
        return Path(project_dir).resolve()
    return Path.cwd()
```

**Initialization pattern:**

```python
_REPO_ROOT = _resolve_repo_root()  # Module global, L38
BACKLOG_DIR = _REPO_ROOT / ".claude" / "backlog"  # L39

def init(project_dir: str | None) -> None:
    """Re-initialise module-level path constants from an explicit project directory."""
    global _REPO_ROOT, BACKLOG_DIR
    _REPO_ROOT = _resolve_repo_root(project_dir)  # L56
    BACKLOG_DIR = _REPO_ROOT / ".claude" / "backlog"  # L57
```

**Key insight:** The harness already supports dynamic project path resolution via `--project-dir` CLI argument. The `init()` function mutates module globals to accommodate plugin installations where `__file__` points to cache, not repo.

---

## Environment Variable Override Pattern

**Pattern observed:** One script uses `os.environ.get()` with fallback:

**Location:** `.claude/skills/daily-releases/scripts/list_daily_ranges.py:45`

```python
DEFAULT_REPO: str = os.environ.get("DEFAULT_REPO") or "Jamie-BitFlight/claude_skills"
```

**Same pattern in:**
- `.claude/skills/daily-releases/scripts/collect_day_dataset.py:51`

**Convention:** When env var `DEFAULT_REPO` is set, use it; otherwise fall back to hardcoded string.

---

## CLI Option Pattern (Typer)

**Pattern:** CLI tools expose `--repo` / `-R` option with default:

**Location:** `.claude/skills/gh/scripts/github_project_setup.py:125`

```python
@app.command()
def labels(
    repo: Annotated[str, typer.Option("--repo", "-R")] = DEFAULT_REPO,
    force: Annotated[bool, typer.Option("--force")] = False,
) -> None:
    """Create standard label taxonomy."""
    gh = get_github()
    repository = get_repo(gh, repo)
```

**Repeated in:** All 8 command functions in `github_project_setup.py` (lines 125, 156, 178, 197, 262, 653, 696, 741, 769)

**Also used in:**
- `.claude/skills/daily-releases/scripts/list_daily_ranges.py:330`
- `.claude/skills/daily-releases/scripts/publish_daily_release.py:113`
- `.claude/skills/daily-releases/scripts/cleanup_stale_releases.py:291`
- `.claude/skills/daily-releases/scripts/collect_day_dataset.py:552`

---

## SKILL.md Hardcoded References

**Count:** 15 SKILL.md files contain hardcoded `Jamie-BitFlight/claude_skills` references

**Files:**

1. `.claude/skills/group-items-to-milestone/SKILL.md`
2. `.claude/skills/gh/SKILL.md`
3. `.claude/skills/complete-milestone/SKILL.md`
4. `.claude/skills/create-milestone/SKILL.md`
5. `.claude/skills/start-milestone/SKILL.md`
6. `.claude/skills/gh/references/labels.md`
7. `.claude/skills/gh/references/issue-stories.md`
8. `.claude/skills/gh/references/milestones.md`
9. `.claude/skills/gh/references/projects-v2.md`
10. `.claude/skills/daily-releases/SKILL.md`

**Usage pattern in SKILL.md files:**

- In code fences: `gh <command> -R Jamie-BitFlight/claude_skills`
- In inline commands: `uv run script.py --repo Jamie-BitFlight/claude_skills`
- In mermaid diagrams: Hardcoded in example workflows
- In narrative documentation: Reference examples showing full GitHub URLs

**Replacement strategy:** SKILL.md files cannot use `os.environ.get()` or dynamic resolution (no runtime code execution in documentation). Viable approaches:

1. **Backtick command substitution:** `!`uv run python -c 'import os; print(os.environ.get("DEFAULT_REPO", "Jamie-BitFlight/claude_skills"))'`` (if supported by SKILL.md loader)
2. **`${CLAUDE_PROJECT_REPO}` env var:** If Claude Code provides this at skill load time
3. **User-facing placeholder:** `gh <command> -R {YOUR_REPO}` with instructions to substitute
4. **Indirect reference:** Link to a JSON/YAML file that stores the repo value, loaded at runtime

---

## FastMCP Server Context

**Location:** `plugins/development-harness/backlog_core/`

**Current approach:**

1. Module loads `DEFAULT_REPO` constant at import time
2. Server can call `init(project_dir)` at startup if launched with `--project-dir` flag
3. All tool functions accept `repo: str = DEFAULT_REPO` parameter, allowing callers to override

**Existing MCP tool patterns:**

All tools that interact with GitHub accept the repo parameter:

```python
# backlog_core/github.py
def get_github(repo: str = DEFAULT_REPO, timeout: int = 15) -> Repository:
    g = get_github_client()
    return g.get_repo(repo)  # PyGithub call
```

**Server startup:** When FastMCP server initializes, it reads CLI args. If `--project-dir` is passed, the server should call `models.init(project_dir)` before any tools run. This mutates `_REPO_ROOT` and `BACKLOG_DIR` module globals.

---

## Git Remote URL Patterns

**Observation:** The codebase does not currently parse git remote URLs for repo discovery. All discovery relies on hardcoded constants or explicit CLI parameters.

**Existing remote URL formats in tests/production:**

- HTTPS: `https://github.com/Jamie-BitFlight/claude_skills.git`
- SSH: `git@github.com:Jamie-BitFlight/claude_skills.git`
- Proxy (test environment): `http://127.0.0.1:{port}/Jamie-BitFlight/claude_skills.git`

**Parsing opportunity:** Extract owner/repo from git remote via `git config --get origin.url`, parse with regex matching:

```python
# Extract OWNER/REPO from various URL formats
def extract_repo_from_remote(remote_url: str) -> str | None:
    """Extract 'OWNER/REPO' from git remote URL.

    Handles:
    - https://github.com/OWNER/REPO.git
    - git@github.com:OWNER/REPO.git
    - http://127.0.0.1:PORT/OWNER/REPO.git
    """
    # Pattern: (https://|git@).*?([^/]+)/([^/]+?)(?:\.git)?/?$
    # Capture groups: [1]=OWNER, [2]=REPO
```

---

## Proposed Discovery Hierarchy

**Recommended resolution order (from highest to lowest precedence):**

1. **CLI argument override** (`--repo OWNER/REPO`)
2. **Environment variable** (`DEFAULT_REPO` env var, if set)
3. **Git remote URL** (parse `.git/config` origin.url)
4. **Fallback constant** (`"Jamie-BitFlight/claude_skills"`)

**Implementation location:**

Create a utility function in `plugins/development-harness/backlog_core/models.py`:

```python
def resolve_repo_slug(explicit_repo: str | None = None) -> str:
    """Resolve repository slug with hierarchical fallback.

    Args:
        explicit_repo: Explicit repo passed by caller (highest precedence)

    Returns:
        Repository slug in 'OWNER/REPO' format.

    Precedence:
        1. explicit_repo parameter (caller override)
        2. DEFAULT_REPO env var (if set)
        3. Extract from git remote origin.url
        4. Hardcoded DEFAULT_REPO constant
    """
```

---

## Test Coverage

**File:** `plugins/development-harness/tests/test_backlog_core_models.py`

**Current test:**

```python
def test_default_repo_format(self):
    assert isinstance(DEFAULT_REPO, str)
    assert "/" in DEFAULT_REPO
```

**Gap:** No tests verify:
- Environment variable override behavior
- Git remote URL parsing
- Hierarchical resolution precedence
- Fallback behavior when git remote is unavailable

---

## Summary

**Current state:**

- Hardcoded `DEFAULT_REPO` constant in 2 core modules
- 15+ SKILL.md files with hardcoded references
- Function signatures support optional `repo` parameter override
- Repository root discovery already supports dynamic `--project-dir` via `init()` function
- One script already uses `os.environ.get()` pattern

**Replacement opportunities:**

1. **Python code:** Add `resolve_repo_slug()` utility function, update all `DEFAULT_REPO` references to use it
2. **SKILL.md files:** Replace hardcoded references with dynamic mechanism (backtick substitution, env var placeholder, or user instructions)
3. **Git remote:** Add optional parsing of `.git/config` for automatic repo discovery
4. **Tests:** Expand coverage for hierarchical resolution and fallback cases

**Key constraint:** SKILL.md files do not support Python code execution — replacements must use documented substitution mechanisms (backtick commands, env vars, placeholders).

---

*Pattern analysis: 2026-03-20*
