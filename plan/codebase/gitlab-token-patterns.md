# GitLab Token Resolution and Subprocess Patterns

**Analysis Date:** 2026-03-02
**Package:** claude_skills

---

## 1. `_resolve_token()` in `fetch_gitlab_mr.py`

**Location:** `.claude/skills/create-merge-request-changelog/scripts/fetch_gitlab_mr.py:91-115`

```python
def _resolve_token() -> str | None:
    """Resolve GitLab API token from environment or glab CLI config.

    Checks in order:
    1. GITLAB_TOKEN environment variable
    2. GITLAB_PRIVATE_TOKEN environment variable
    3. glab CLI config for the detected host
    """
    if token := os.environ.get("GITLAB_TOKEN") or os.environ.get("GITLAB_PRIVATE_TOKEN"):
        return token

    glab_path = shutil.which("glab")
    if not glab_path:
        return None

    try:
        result = subprocess.run(
            [glab_path, "config", "get", "token", "-h", _get_gitlab_host()],
            capture_output=True, text=True, check=True
        )
        return result.stdout.strip() or None
    except subprocess.CalledProcessError:
        return None
```

**Resolution order:**

1. `GITLAB_TOKEN` env var (walrus operator short-circuits on truthy value)
2. `GITLAB_PRIVATE_TOKEN` env var
3. `glab config get token -h {hostname}` — subprocess call to the glab CLI, scoped to the detected GitLab host

**Key behaviors:**

- Uses `shutil.which("glab")` before invoking subprocess — guards against `FileNotFoundError` and avoids shell injection by using the full resolved path
- Uses `check=True` — raises `subprocess.CalledProcessError` on non-zero exit (e.g., token not configured); caller catches and returns `None`
- Strips stdout whitespace; returns `None` on empty string
- Host is derived from git remote origin URL via `_parse_git_origin()` (`.claude/skills/create-merge-request-changelog/scripts/fetch_gitlab_mr.py:56-70`)
- `get_gitlab_client()` (line 118) raises `GitLabFetchError` if `_resolve_token()` returns `None`

---

## 2. `_resolve_token()` in `gitlab_context.py`

**Location:** `plugins/gitlab-skill/skills/gitlab-skill/scripts/gitlab_context.py:97-107`

```python
def _resolve_token() -> str | None:
    """Resolve GitLab API token from environment variables.

    Checks in order:
    1. GITLAB_TOKEN environment variable
    2. GITLAB_PRIVATE_TOKEN environment variable
    """
    return os.environ.get("GITLAB_TOKEN") or os.environ.get("GITLAB_PRIVATE_TOKEN") or None
```

**Key difference from `fetch_gitlab_mr.py`:** No `glab` CLI fallback. This script is a preprocessing context gatherer (`!` backtick-bang in SKILL.md) that must always exit 0. It never invokes subprocess for token resolution.

**`get_gitlab_client()` in this file** (line 110-124):

```python
def get_gitlab_client() -> gitlab_module.Gitlab:
    token = _resolve_token()
    if not token:
        msg = "No GitLab token found. Set GITLAB_TOKEN env var."
        raise RuntimeError(msg)
    return gitlab_module.Gitlab(f"https://{get_gitlab_host()}", private_token=token)
```

Raises `RuntimeError` (not `GitLabFetchError`). Callers in `main()` wrap all calls in `except Exception` with `# noqa: BLE001` — consistent with "always exit 0" contract (line 254).

**Comparison table:**

| Aspect | `fetch_gitlab_mr.py` | `gitlab_context.py` |
|--------|----------------------|---------------------|
| Env var 1 | `GITLAB_TOKEN` | `GITLAB_TOKEN` |
| Env var 2 | `GITLAB_PRIVATE_TOKEN` | `GITLAB_PRIVATE_TOKEN` |
| glab fallback | Yes (`glab config get token -h {host}`) | No |
| Error type | `GitLabFetchError` | `RuntimeError` |
| Exit behavior | `typer.Exit(code=1)` | Always exit 0 |

---

## 3. Subprocess Usage Patterns for External CLI Tools

The codebase has a consistent security pattern for all subprocess calls to external CLIs. Files using subprocess:

- `.claude/skills/create-merge-request-changelog/scripts/fetch_gitlab_mr.py`
- `.claude/skills/gh/scripts/github_project_setup.py`
- `.claude/skills/gh/scripts/setup_gh.py`
- `plugins/gitlab-skill/skills/gitlab-skill/scripts/get_gitlab_context.py`
- `plugins/holistic-linting/skills/holistic-linting/scripts/detect_hook_tool.py`
- `plugins/holistic-linting/skills/holistic-linting/scripts/lint_orchestrator.py`
- `plugins/plugin-creator/scripts/auto_sync_manifests.py`
- `plugins/plugin-creator/scripts/plugin_validator.py`
- `plugins/python3-development/skills/implementation-manager/scripts/get_task_context.py`

**Universal subprocess security pattern** (enforced by ruff rules `S404`, `S603` ignored in `pyproject.toml:239-240`):

```python
# Step 1: Resolve full path with shutil.which — never pass partial path to subprocess
tool_path = shutil.which("glab")
if not tool_path:
    return None  # graceful degradation

# Step 2: Call subprocess.run with:
#   - list of arguments (not string — prevents shell injection)
#   - capture_output=True, text=True
#   - NO shell=True
#   - timeout (when blocking)
result = subprocess.run(
    [tool_path, "config", "get", "token", "-h", host],
    capture_output=True, text=True, check=True
)
```

**Pattern variants by use case:**

**Variant A — Token/config query** (`fetch_gitlab_mr.py:109-114`): `check=True`, catch `CalledProcessError`, return `None` on failure.

**Variant B — Status/info query** (`get_gitlab_context.py:28-32`): `check=False`, test `returncode == 0`, return `None` if non-zero.

```python
result = subprocess.run([glab_path, *args], capture_output=True, text=True, check=False)
return result.stdout.strip() if result.returncode == 0 else None
```

**Variant C — Tool orchestration** (`lint_orchestrator.py:221`, `detect_hook_tool.py:83`): `check=False`, `timeout=60`, return the `ToolResult` or `returncode`.

```python
result = subprocess.run(cmd, check=False, capture_output=True, text=True, timeout=60)
```

**Variant D — Self-invocation** (`get_task_context.py:25-26`): Uses `sys.executable` as the interpreter path — avoids relying on PATH for the current Python binary.

```python
result = subprocess.run(
    [sys.executable, str(script_path), "list-features", "."],
    capture_output=True, text=True, check=False
)
```

**Module-level `shutil.which` caching** (`auto_sync_manifests.py:49-57`): Some scripts resolve tool paths at import time to a module-level constant:

```python
_NPX_PATH: str | None = shutil.which("npx")
_GIT_PATH: str | None = shutil.which("git")
```

---

## 4. python-gitlab Authentication Across the Codebase

Only two files use `python-gitlab` directly:

- `.claude/skills/create-merge-request-changelog/scripts/fetch_gitlab_mr.py`
- `plugins/gitlab-skill/skills/gitlab-skill/scripts/gitlab_context.py`

A third file (`plugins/gitlab-skill/skills/gitlab-skill/scripts/get_gitlab_context.py`) uses glab CLI subprocess calls only — no `python-gitlab`.

**Authentication constructor** (identical in both files using python-gitlab):

```python
gitlab.Gitlab(f"https://{hostname}", private_token=token)
```

Uses `private_token` keyword argument. No OAuth, no job token, no HTTP basic auth. Host is always constructed as `https://{hostname}` where hostname comes from parsing the git remote origin URL.

**Dependency declarations** (PEP 723 inline script metadata):

- `fetch_gitlab_mr.py` line 4: `# dependencies = ["typer>=0.21.0", "python-gitlab>=4.0.0", "gitpython>=3.1.0"]`
- `gitlab_context.py` line 4: `# dependencies = ["python-gitlab>=4.0.0", "gitpython>=3.1.0"]`

**Project-level dependency** (`pyproject.toml:41`): `"python-gitlab>=8.0.0"` in `[dependency-groups] dev`. The inline script metadata pins `>=4.0.0` (a lower bound) while the workspace dev group requires `>=8.0.0`.

**python-gitlab usage patterns in `fetch_gitlab_mr.py`:**

```python
gl = gitlab.Gitlab(f"https://{_get_gitlab_host()}", private_token=token)
project = gl.projects.get(_get_project_path())        # string path e.g. "group/project"
mr = project.mergerequests.get(mr_iid)               # integer IID
commits = list(mr.commits())
changes_data = mr.changes()                           # returns dict
result = project.ci_lint.create({"content": content}) # in gitlab_context.py
```

**Exception hierarchy used** (only in `fetch_gitlab_mr.py`):

```python
except gitlab.exceptions.GitlabGetError as e: ...    # 404 not found
except gitlab.exceptions.GitlabAuthenticationError as e: ...  # 401/403
except gitlab.exceptions.GitlabError as e: ...       # catch-all gitlab errors
```

`gitlab_context.py` uses broad `except Exception` with `# noqa: BLE001` throughout `main()` — consistent with must-not-fail contract.

**`@lru_cache(maxsize=1)` usage:** Both files cache `_get_repo()` and `_parse_git_origin()` — git I/O is performed once per process invocation. This pattern is used exactly the same way in both files (`fetch_gitlab_mr.py:45-52,55-70` and `gitlab_context.py:41-84`).

---

## 5. Testing Patterns for These Scripts

**No tests exist** for the GitLab scripts directly:

- No `tests/` directory under `.claude/skills/create-merge-request-changelog/`
- No `tests/` directory under `plugins/gitlab-skill/`
- `pyproject.toml:91` sets `testpaths = ["**/tests"]` — these directories would be auto-discovered if they existed

**`pyproject.toml` adds these scripts to `pythonpath`** (lines 76-77, 81), enabling future tests to import their functions without path manipulation:

```toml
pythonpath = [
    "./.claude/skills/create-merge-request-changelog/scripts",
    "./plugins/gitlab-skill/skills/gitlab-skill/scripts",
    ...
]
```

**Established test patterns for subprocess-heavy scripts** (from `plugins/plugin-creator/tests/test_external_tools.py`):

Use `mocker.patch("module.shutil.which", ...)` and `mocker.patch("module.subprocess.run", ...)` with `pytest-mock`. The module-qualified patch target is required (e.g., `"plugin_validator.shutil.which"`, not `"shutil.which"`).

```python
def test_resolve_token_from_env(mocker: MockerFixture) -> None:
    mocker.patch.dict(os.environ, {"GITLAB_TOKEN": "test-token"})
    assert _resolve_token() == "test-token"

def test_resolve_token_glab_fallback(mocker: MockerFixture) -> None:
    mocker.patch.dict(os.environ, {}, clear=True)
    mocker.patch("fetch_gitlab_mr.shutil.which", return_value="/usr/bin/glab")
    mock_run = mocker.patch("fetch_gitlab_mr.subprocess.run")
    mock_run.return_value = mocker.Mock(stdout="mytoken\n")
    assert _resolve_token() == "mytoken"

def test_get_gitlab_client_raises_when_no_token(mocker: MockerFixture) -> None:
    mocker.patch("fetch_gitlab_mr._resolve_token", return_value=None)
    with pytest.raises(GitLabFetchError, match="No GitLab token"):
        get_gitlab_client()
```

**Test coverage gap** (`test_external_tools.py` tests the following exception types for subprocess calls):

- `subprocess.TimeoutExpired` — graceful failure, returns meaningful message
- `FileNotFoundError` — graceful degradation (returns skip/None)
- `OSError` — returns failure with error message
- Exit code 0 → success, non-zero → failure

Apply this same matrix to GitLab scripts when adding tests.

**Fixture patterns** (`pyproject.toml:57-73`): pytest configured with `-n auto` (parallel via `pytest-xdist`), `asyncio_mode = "auto"`, and strict markers. Tests for GitLab scripts should be marked `@pytest.mark.unit` and avoid network calls.

---

## Summary

Use these patterns when writing new GitLab-related code:

1. **Token resolution:** Use env vars first (`GITLAB_TOKEN`, `GITLAB_PRIVATE_TOKEN`). Add `glab` CLI fallback only for interactive CLI tools that can surface a meaningful error — not for preprocessing scripts that must exit 0.

2. **Subprocess calls:** Always use `shutil.which()` to get the full binary path before calling `subprocess.run`. Pass args as a list (not string). Never use `shell=True`. Set `capture_output=True, text=True`. Use `check=True` when a non-zero exit is an error; use `check=False` with `returncode` inspection for tools where non-zero is a valid "not found" signal.

3. **python-gitlab auth:** Construct `gitlab.Gitlab(f"https://{host}", private_token=token)`. Get project by string path `gl.projects.get("group/project")`. Catch specific exception subclasses from `gitlab.exceptions` in production code; use broad `except Exception` with `# noqa: BLE001` only in preprocessing scripts that must not fail.

4. **Testing:** Mock at the module level (`"module_name.shutil.which"`, `"module_name.subprocess.run"`). Cover all exception types: `CalledProcessError`, `TimeoutExpired`, `FileNotFoundError`, `OSError`. GitLab API tests should mock `gitlab.Gitlab` constructor and its return objects to avoid network calls.

---

_GitLab token and subprocess analysis: 2026-03-02_
