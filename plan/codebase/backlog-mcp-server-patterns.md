# Backlog FastMCP Server Patterns

**Analysis Date:** 2026-03-20
**Component:** Backlog MCP Server
**Location:** `plugins/development-harness/backlog_core/`

## Server Structure

**Entry Point:** `plugins/development-harness/backlog_core/server.py`

**Pattern:**
```python
from fastmcp import Context, FastMCP

mcp = FastMCP(
    "backlog",
    instructions="...",
    version="0.1.0",
)

@mcp.tool
async def tool_name(
    param: Annotated[str, Field(description="...")],
    optional_param: Annotated[bool, Field(...)] = False,
) -> dict:
    """Docstring."""
    out = Output()
    try:
        result = await asyncio.to_thread(
            operations.operation_name,
            param=param,
            optional_param=optional_param,
            output=out,
        )
        return {**result, **out.to_dict()}
    except BacklogError as e:
        return {"error": str(e), **out.to_dict()}
```

**Conventions:**

- Server name: `"backlog"`
- All tools are async functions decorated with `@mcp.tool`
- Parameters use `Annotated[Type, Field(description="...")]` for MCP schema
- All tools return `dict` (Pydantic models auto-serialize)
- Tools wrap blocking operations with `asyncio.to_thread()` to prevent blocking the event loop
- Each tool gets an `Output()` instance to collect messages/warnings
- Return format: `{**result, **out.to_dict()}` merges operation result with output dict
- Error handling: Catch `BacklogError` subclasses, return `{"error": str(e), **out.to_dict()}`

## Tool Registration

**Pattern:** 14 tools registered via `@mcp.tool` decorator (as of analysis date):

1. `backlog_add` — Create new backlog item with optional GitHub issue
2. `backlog_list` — List items with optional GitHub status refresh
3. `backlog_view` — View single item details with pagination
4. `backlog_sync` — Sync local items with GitHub Issues (with dry-run)
5. `backlog_close` — Close item with reason
6. `backlog_resolve` — Mark item resolved with summary
7. `backlog_update` — Update item fields (priority, type, plan path)
8. `backlog_groom` — Interactive grooming with reasoning capture
9. `backlog_normalize` — Normalize all items (with dry-run)
10. `backlog_pull` — Pull issue from GitHub to local file
11. `backlog_create_sam_task` — Create SAM task sub-issue
12. `backlog_get_sam_tasks` — Fetch SAM tasks for parent issue
13. `backlog_update_sam_task_status` — Update task status on GitHub
14. `backlog_get_ready_sam_tasks` — List ready tasks for a parent issue

**Common Parameters:**

- `selector: Annotated[str, Field(description="Item selector: ...")]` — flexible locator (title substring, #N, GitHub URL)
- `ctx: Context` — FastMCP context (passed by server for tools that need it: `sync`, `groom`, `normalize`, `pull`)
- `dry_run: bool` — Preview mode for write operations (used by: `sync`, `normalize`)

## Return Format Pattern

**All tools return a dict with:**

```python
{
    "result_field": "...",           # Operation-specific data
    "issue_number": N,               # If GitHub issue involved
    "file_path": "...",              # If local file involved
    "messages": ["msg1", "msg2"],    # Info messages
    "warnings": ["warn1"],           # Warning messages
    "error": "error text"            # Present only on error
}
```

**Output class** (`models.py`):

```python
class Output(BaseModel):
    """Structured output collector."""
    messages: list[str] = []
    warnings: list[str] = []

    def to_dict(self) -> dict:
        return {"messages": self.messages, "warnings": self.warnings}
```

Tools call `out.messages.append()` and `out.warnings.append()` during execution to accumulate output.

## GitHub API Integration

**Location:** `plugins/development-harness/backlog_core/github.py`

**Pattern:**

```python
def get_github(repo: str = DEFAULT_REPO, timeout: int = 15) -> Repository:
    """Get a PyGithub Repository object.

    Raises:
        GitHubUnavailableError: If GITHUB_TOKEN missing or API unreachable.
    """
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise GitHubUnavailableError("GITHUB_TOKEN not set")
    g = Github(auth=Auth.Token(token), timeout=timeout)
    return g.get_repo(repo)
```

**Authentication:**

- Token source: `GITHUB_TOKEN` environment variable
- Auth method: `Auth.Token(token)` from PyGithub
- Timeout: 15 seconds (configurable)
- Error handling: Raises `GitHubUnavailableError` if token missing or API fails

**Existing Operations:**

- `create_issue_for_item(repo, item, dry_run, output)` — Create GitHub issue from BacklogItem
- `fetch_github_issue_body(repo, issue_number)` — Get issue body as markdown
- `fetch_open_issues_by_title(repo, title_pattern)` — Search issues by title regex
- `close_github_issue(repo, issue_number, reason, output)` — Close issue with reason comment
- `resolve_github_issue(repo, issue_number, summary, output)` — Add resolution comment
- `apply_status_in_progress(repo, issue_number, output)` — Add "in-progress" label
- `apply_status_verified(repo, issue_number, output)` — Add "verified" label
- `batch_fetch_statuses(repo, issue_numbers)` — Fetch multiple issue statuses efficiently
- `check_open_prs_for_issue(repo, issue_number)` — Find related PRs

**GraphQL Usage:**

- `_resolve_labels_graphql(repo, repo_owner, repo_name, label_names)` — Batch resolve label existence via GraphQL
- Pattern: Single query with aliased label lookups — more efficient than REST API per-label
- Location: `plugins/development-harness/backlog_core/github.py:48-80` — `_LABEL_RESOLUTION_QUERY_TEMPLATE`

## Repository Discovery

**Pattern:**

```python
def _resolve_repo_root(project_dir: str | None = None) -> Path:
    """Return repository root path."""
    if project_dir:
        return Path(project_dir).resolve()
    return Path.cwd()

# Module-level initialization
_REPO_ROOT = _resolve_repo_root()
BACKLOG_DIR = _REPO_ROOT / ".claude" / "backlog"
DEFAULT_REPO = discover_repo()  # Dynamic discovery

def init(project_dir: str | None = None, repo: str | None = None) -> None:
    """Re-initialize module-level constants at server startup."""
    global _REPO_ROOT, BACKLOG_DIR, DEFAULT_REPO
    _REPO_ROOT = _resolve_repo_root(project_dir)
    BACKLOG_DIR = _REPO_ROOT / ".claude" / "backlog"
    # ... update DEFAULT_REPO
```

**How discovery works:**

1. **Explicit parameter:** `--project-dir` CLI argument (needed when server runs as plugin)
2. **Fallback:** `Path.cwd()` for in-repo development
3. **Repo slug:** `discover_repo()` called at startup to resolve `owner/repo` from git remote

**Server startup** (`server.py:23-46`):

```python
def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Backlog MCP server")
    parser.add_argument(
        "--project-dir",
        type=str,
        default=None,
        help="Absolute path to the user's project root..."
    )
    namespace, _ = parser.parse_known_args(sys.argv[1:])
    return namespace

_args = _parse_args()
_init_models(_args.project_dir)
```

## Exception Hierarchy

**Location:** `plugins/development-harness/backlog_core/models.py`

```python
class BacklogError(Exception):
    """General backlog operation error."""

class ItemNotFoundError(BacklogError):
    """Raised when backlog item cannot be found by selector."""

class DuplicateItemError(BacklogError):
    """Raised when fuzzy duplicate detected during creation."""

class GitHubUnavailableError(BacklogError):
    """Raised when GITHUB_TOKEN missing or GitHub API unreachable."""

class ValidationError(BacklogError):
    """Raised on input validation failure."""

class RepoDiscoveryError(Exception):
    """Raised when all repository discovery methods fail."""
```

**Pattern:**

- All backlog-specific errors inherit from `BacklogError`
- Caught in tool functions with `except BacklogError as e: return {"error": str(e), ...}`
- `RepoDiscoveryError` is separate (not caught by backlog tools, raises at startup)

## Model Types

**Key Pydantic models** (all in `models.py`):

- `BacklogItem` — Parsed item from local file (title, priority, type, source, body, issue_number)
- `Output` — Accumulator for messages/warnings (used by all operations)
- `SamTask` — SAM task structure (task_id, parent_issue_number, status, dependencies, etc.)
- `IssueStatus` — GitHub issue status (open, closed, draft, merged, etc.)
- `IssueLocalFields` — Fields synced FROM GitHub TO local file

## Test Patterns

**Location:** `plugins/development-harness/tests/test_backlog_core_server.py`

**Test structure:**

- Import `from backlog_core import operations, models`
- Mock PyGithub with `mocker.patch("github.Github")` or similar
- Test operations independently first (in separate test files)
- Mock `operations.*` calls in server tests
- Assert return dict structure: `assert response["messages"]`, `assert not response.get("error")`

## Key Implementation Notes

### How to Add a New GitHub API Tool

**Steps:**

1. **Add operation function** to `operations.py`:
   ```python
   def my_operation(repo: str = DEFAULT_REPO, param: str = "", output: Output | None = None) -> dict:
       out = output or Output()
       try:
           gh_repo = get_github(repo)
           result = gh_repo.get_issues(state="open", labels=param)
           # ... process
           return {"items": result, "count": len(result)}
       except GithubException as e:
           raise BacklogError(f"GitHub API error: {e}")
   ```

2. **Add tool function** to `server.py`:
   ```python
   @mcp.tool
   async def backlog_my_operation(
       param: Annotated[str, Field(description="...")] = "",
   ) -> dict:
       """Docstring."""
       out = Output()
       try:
           result = await asyncio.to_thread(
               operations.my_operation,
               param=param,
               output=out,
           )
           return {**result, **out.to_dict()}
       except BacklogError as e:
           return {"error": str(e), **out.to_dict()}
   ```

3. **Add tests**:
   - Mock `get_github` or individual PyGithub calls
   - Test success path (returns dict with expected keys)
   - Test error path (returns `{"error": "...", ...}`)
   - Assert output messages are collected

### Projects V2 Integration Readiness

**Current state:**

- PyGithub is used for standard REST API operations
- GraphQL is already in use for label resolution (`_resolve_labels_graphql`)
- PyGithub's `requester` can be accessed for raw GraphQL queries

**To add Projects V2 support:**

1. Create `_projects_v2_graphql()` helper in `github.py` following the `_resolve_labels_graphql` pattern
2. Query Projects V2 items via GraphQL (not available in REST API)
3. Return results as list of dicts with id, title, status fields
4. Wrap in operation function + tool in server

**GraphQL requester pattern:**

```python
repo = get_github()
# repo._requester provides GraphQL capability
# Follow _resolve_labels_graphql pattern for query + mutation patterns
```

---

_Architecture analysis: 2026-03-20_
