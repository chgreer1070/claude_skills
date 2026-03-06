# backlog_core Async Pattern Analysis

**Analysis Date:** 2026-03-06
**Package:** backlog_core (FastMCP 3.x server for backlog MCP)

## Executive Summary

The backlog_core codebase is **synchronous throughout**. There are no async patterns currently implemented. The architecture uses FastMCP 3.x which is capable of async but does not require it. All I/O operations (GitHub API calls via PyGithub, file I/O) are synchronous blocking calls.

---

## Tool Function Signatures (server.py)

All 10 MCP tool functions are defined in `server.py:16-382` as synchronous functions decorated with `@mcp.tool()`. Each function:
1. Creates an `Output()` instance for message collection
2. Calls a corresponding `operations.*` function with the output instance
3. Returns a dict with `{**result, **out.to_dict()}` or error dict

### Tool 1: backlog_add

**Location:** `server.py:16-51`

```python
@mcp.tool()
def backlog_add(
    title: Annotated[str, Field(description="Item title")],
    priority: Annotated[str, Field(description="Priority level: P0, P1, P2, or Ideas")],
    description: Annotated[str, Field(description="Item description")],
    source: Annotated[str, Field(description="Where this item came from")] = "Not specified",
    type_: Annotated[str, Field(description="Item type: Feature, Bug, Refactor, Docs, or Chore", alias="type")] = "Feature",
    create_issue: Annotated[bool, Field(description="Create a GitHub issue for this item")] = True,
    force: Annotated[bool, Field(description="Skip fuzzy duplicate check")] = False,
) -> dict
```

**Calls:** `operations.add_item()`
**Return:** `dict` with file_path, title, priority, issue number (if created), messages, warnings

---

### Tool 2: backlog_list

**Location:** `server.py:54-94`

```python
@mcp.tool()
def backlog_list(
    with_status: Annotated[bool, Field(description="Include GitHub issue status for each item")] = False,
    from_github: Annotated[bool, Field(description="Refresh local cache from GitHub Issues before listing")] = False,
    label: Annotated[str | None, Field(description="Filter by GitHub label (e.g. 'priority:p1', 'type:bug')")] = None,
    section: Annotated[str | None, Field(description="Filter by priority section: P0, P1, P2, or Ideas (case-insensitive)")] = None,
    status: Annotated[str | None, Field(description="Filter by status value e.g. 'needs-grooming', 'status:in-progress'")] = None,
    title: Annotated[str | None, Field(description="Filter items whose title contains this substring (case-insensitive)")] = None,
) -> dict
```

**Calls:** `operations.list_items()`
**Return:** `dict` with items list (each containing title, priority, issue, plan), messages, warnings

---

### Tool 3: backlog_view

**Location:** `server.py:97-118`

```python
@mcp.tool()
def backlog_view(
    selector: Annotated[str, Field(description="Item selector: GitHub issue URL, #N, bare number, or title substring")],
    offset: Annotated[int, Field(ge=0, description="Skip N lines from body start (for pagination)")] = 0,
    limit: Annotated[int, Field(ge=0, description="Show at most N body lines (0 = all, no truncation)")] = 0,
) -> dict
```

**Calls:** `operations.view_item()`
**Return:** `dict` with title, priority, issue, plan, file_path, body, groomed content, messages, warnings

---

### Tool 4: backlog_sync

**Location:** `server.py:121-138`

```python
@mcp.tool()
def backlog_sync(
    dry_run: Annotated[bool, Field(description="Preview what would be synced without making changes")] = False,
) -> dict
```

**Calls:** `operations.sync_items()`
**Return:** `dict` with created and pushed counts, messages, warnings

---

### Tool 5: backlog_close

**Location:** `server.py:141-181`

```python
@mcp.tool()
def backlog_close(
    selector: Annotated[str, Field(description="Item selector: title substring, #N, bare number, or GitHub issue URL")],
    reason: Annotated[str, Field(description="Why the item is being dismissed. One of: duplicate, out_of_scope, superseded, wontfix, blocked")],
    reference: Annotated[str, Field(description="Related item reference: #N, URL, or title of the item this duplicates/is superseded by")] = "",
    comment: Annotated[str, Field(description="Additional context about why this item is being closed")] = "",
    cleanup: Annotated[bool, Field(description="Remove local file after close; index link becomes GitHub issue URL")] = False,
    force: Annotated[bool, Field(description="Close even if open PRs reference the issue")] = False,
) -> dict
```

**Calls:** `operations.close_item()`
**Return:** `dict` with closed item title, reason, messages, warnings

---

### Tool 6: backlog_resolve

**Location:** `server.py:184-224`

```python
@mcp.tool()
def backlog_resolve(
    selector: Annotated[str, Field(description="Item selector: title substring, #N, bare number, or GitHub issue URL")],
    summary: Annotated[str, Field(description="What was done — 1-2 sentence completion summary (required)")],
    plan: Annotated[str | None, Field(description="Plan path or completion reference")] = None,
    method: Annotated[str | None, Field(description="How the work was done — approach taken")] = None,
    notes: Annotated[str | None, Field(description="Problems found, surprises, or other comments")] = None,
    follow_ups: Annotated[str | None, Field(description="Created follow-up tickets (comma-separated refs)")] = None,
    findings: Annotated[str | None, Field(description="Retrospective learnings from this work")] = None,
    cleanup: Annotated[bool, Field(description="Remove local file after resolve; index link becomes GitHub issue URL")] = False,
    force: Annotated[bool, Field(description="Resolve even if open PRs reference the issue")] = False,
) -> dict
```

**Calls:** `operations.resolve_item()`
**Return:** `dict` with resolved item title, summary, messages, warnings

---

### Tool 7: backlog_update

**Location:** `server.py:227-289`

```python
@mcp.tool()
def backlog_update(
    selector: Annotated[str, Field(description="Item selector: title substring, #N, bare number, or GitHub issue URL")],
    plan: Annotated[str | None, Field(description="Path to a plan file to attach to the item")] = None,
    status: Annotated[str | None, Field(description="Set item status (e.g. 'in-progress'). Updates GitHub issue labels when applicable.")] = None,
    create_issue: Annotated[bool, Field(description="Create a GitHub issue for this item if it lacks one (P0/P1 items only)")] = False,
    groomed_content: Annotated[str | None, Field(description="Groomed content to write into the item's per-item file. Replaces the entire groomed section.")] = None,
    section: Annotated[str | None, Field(description="Section name for incremental groomed content update (use with content parameter)")] = None,
    content: Annotated[str | None, Field(description="Content for the named section (use with section parameter for incremental updates)")] = None,
    title: Annotated[str | None, Field(description="New title for the item. Updates the local file name field and GitHub issue title if the item already has a linked issue.")] = None,
    description: Annotated[str | None, Field(description="New description text for the item. Updates the local file only — no GitHub sync.")] = None,
) -> dict
```

**Calls:** `operations.update_item()`
**Return:** `dict` with updated item title, applied changes, messages, warnings

---

### Tool 8: backlog_groom

**Location:** `server.py:292-323`

```python
@mcp.tool()
def backlog_groom(
    selector: Annotated[str, Field(description="Item selector: title substring, #N, bare number, or GitHub issue URL")],
    groomed_content: Annotated[str | None, Field(description="Full groomed content to write into the per-item file. Replaces the entire groomed section.")] = None,
    section: Annotated[str | None, Field(description="Section name for incremental update (use with content parameter)")] = None,
    content: Annotated[str | None, Field(description="Content for the named section (use with section parameter)")] = None,
) -> dict
```

**Calls:** `operations.groom_item()`
**Return:** `dict` with groomed item title, synced status, messages, warnings

---

### Tool 9: backlog_normalize

**Location:** `server.py:326-344`

```python
@mcp.tool()
def backlog_normalize(
    dry_run: Annotated[bool, Field(description="Preview normalization changes without modifying files")] = False,
) -> dict
```

**Calls:** `operations.normalize_items()`
**Return:** `dict` with count of normalized files, messages, warnings

---

### Tool 10: backlog_pull

**Location:** `server.py:347-381`

```python
@mcp.tool()
def backlog_pull(
    selector: Annotated[str | None, Field(description="Optional selector to pull a single issue: #N, bare number, GitHub URL, or title substring. When omitted, pulls all issues.")] = None,
    dry_run: Annotated[bool, Field(description="Preview what would be pulled without modifying local files")] = False,
    force: Annotated[bool, Field(description="Overwrite local content even if local version is newer or longer")] = False,
) -> dict
```

**Calls:** `operations.pull_by_selector()` or `operations.pull_items()`
**Return:** `dict` with count of pulled items (bulk) or file_path (single), messages, warnings

---

## GitHub API Boundary Functions (github.py)

All functions in `github.py` are **synchronous**. They use PyGithub 2.8.1+ which is a blocking sync library. Key functions:

### Connection Functions

- `get_github(repo: str) -> Repository` (`github.py:38-51`)
  - Authenticates with GITHUB_TOKEN, returns PyGithub Repository object
  - **Raises:** GitHubUnavailableError if token not set

- `try_get_github(repo: str) -> Repository | None` (`github.py:54-69`)
  - Graceful fallback, returns None if GitHub unavailable
  - Used for operations where local-only fallback is acceptable

### Issue CRUD Operations

- `create_issue_for_item(repo: Repository, item: BacklogItem, dry_run: bool = False, output: Output | None = None) -> int | None` (`github.py:77-109`)
  - Creates GitHub issue from BacklogItem
  - Returns issue number or None

- `close_github_issue(issue_ref: str, reason: str, *, reference: str = "", comment: str = "", repo: str = DEFAULT_REPO, output: Output | None = None) -> None` (`github.py:112-136`)
  - Closes issue as dismissed (not completed) with structured comment
  - Per ADR-9

- `resolve_github_issue(issue_ref: str, *, summary: str, method: str = "", notes: str = "", follow_ups: str = "", findings: str = "", repo: str = DEFAULT_REPO, output: Output | None = None) -> None` (`github.py:139-169`)
  - Closes issue as completed with structured evidence trail
  - Per ADR-9

### Status and Label Management

- `batch_fetch_statuses(items: list[BacklogItem], repo: str = DEFAULT_REPO) -> dict[int, IssueStatus]` (`github.py:208-236`)
  - **Single API call** replaces N+1 per-item get_issue() calls
  - Returns `{issue_number -> IssueStatus}` dict
  - Returns empty dict on GitHub unavailability

- `fetch_item_status(item: BacklogItem, repo: str = DEFAULT_REPO, output: Output | None = None) -> str` (`github.py:239-256`)
  - Single-item fallback (prefer batch_fetch_statuses)
  - Returns status label string or empty string

- `apply_status_in_progress(item: BacklogItem, repo: str = DEFAULT_REPO, output: Output | None = None) -> None` (`github.py:259-275`)
  - Sets GitHub issue label to status:in-progress
  - Removes status:needs-grooming if present

### Issue Queries

- `fetch_open_issues_by_title(repo: Repository) -> dict[str, int]` (`github.py:283-298`)
  - Fetches all open issues, returns `{normalized_title: issue_number}` map
  - Keeps lowest issue number for duplicates

### View Enrichment

- `view_enrich_from_github(result: ViewItemResult, issue_num: str, repo: str = DEFAULT_REPO) -> bool` (`github.py:306-331`)
  - Enriches ViewItemResult with live GitHub issue data
  - Returns True if data was fetched, False if unavailable/errored

### Issue Data Extraction

- `issue_to_local_fields(issue: Issue) -> IssueLocalFields` (`github.py:339-372`)
  - Extracts backlog-relevant fields from PyGithub Issue object
  - Maps GitHub labels to priority, type, status

### Groomed Content Sync

- `sync_groomed_to_github_issue(repo_obj: Repository, issue_num: int, groomed_content: str, section_name: str | None = None, output: Output | None = None) -> bool` (`github.py:380-413`)
  - Appends or merges groomed content into GitHub issue body
  - GitHub is canonical (source of truth)
  - Returns True if body was actually updated, False otherwise

### Issue Body Fetch

- `fetch_github_issue_body(repo_obj: Repository, issue_num: int, output: Output | None = None) -> str | None` (`github.py:421-437`)
  - Fetches GitHub issue body text
  - Returns issue body string or None on error

### PR Check

- `check_open_prs_for_issue(issue_num: int, repo: str = DEFAULT_REPO) -> list[PullRequestRef]` (`github.py:177-200`)
  - Searches for open PRs referencing issue number
  - Uses GitHub search API (`repo:owner/repo is:pr is:open #{num}`)
  - Returns list of PullRequestRef models
  - Returns empty list if no matches or GitHub unavailable

---

## Operations.py Functions Calling github.py

**Key operations.py functions that call github.py I/O boundary functions:**

1. `_create_issue_and_update_item()` (`operations.py:123-142`)
   - Calls: `get_github()`, `create_issue_for_item()`

2. `_rename_item_title()` (`operations.py:145-169`)
   - Calls: `try_get_github()`, then directly accesses `repository.get_issue()` and `issue.edit()`

3. `_ensure_github_issue()` (`operations.py:278-301`)
   - Calls: `try_get_github()`, `create_issue_for_item()`

4. `_write_groomed_to_github()` (`operations.py:304-336`)
   - Calls: `try_get_github()`, `sync_groomed_to_github_issue()`
   - Also directly calls `repository.get_issue()` and `issue.remove_from_labels()`

5. `_handle_update_groomed()` (`operations.py:339-367`)
   - Calls: `_ensure_github_issue()`, `_write_groomed_to_github()`

6. `_pull_if_issue_selector()` (`operations.py:398-410`)
   - Calls: `get_github()`, `pull_single_issue()` (not shown in github.py exports)

**Public operations functions that interact with GitHub (inferred from imports):**

From `operations.py:17-31`, these github.py functions are imported and used by public operations:
- `apply_status_in_progress`
- `batch_fetch_statuses`
- `check_open_prs_for_issue`
- `close_github_issue`
- `create_issue_for_item`
- `fetch_github_issue_body`
- `fetch_open_issues_by_title`
- `get_github`
- `issue_to_local_fields`
- `resolve_github_issue`
- `sync_groomed_to_github_issue`
- `try_get_github`
- `view_enrich_from_github`

---

## Async Pattern Status

### Current State: No Async

**Finding:** Zero `async def` functions in the entire codebase.

- `server.py`: All 10 tool functions are synchronous `def`
- `github.py`: All 18+ functions are synchronous `def`
- `operations.py`: All helper and public functions are synchronous `def`
- `models.py`: Data classes only (Pydantic BaseModel, no async)

### I/O Blocking Points

**File I/O:** Synchronous pathlib `Path.read_text()`, `Path.write_text()`

**GitHub API:** PyGithub 2.8.1+ is a **blocking sync library**. All repository operations block the calling thread:
- `repo.create_issue()`
- `repo.get_issue()`
- `issue.edit()`
- `issue.create_comment()`
- `gh.search_issues()` (paginated lazy evaluation)
- `repo.get_issues()` (paginated lazy evaluation)

**No concurrent requests:** Single-threaded sequential calls to GitHub API.

---

## Dependency Versions (pyproject.toml)

**Runtime Dependencies:**

```toml
[project]
name = "backlog-core"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "fastmcp>=3.0.2",
    "pygithub>=2.8.1",
    "pydantic>=2.12.3",
    "python-frontmatter>=1.1.0",
]
```

### Async-Relevant Versions

| Dependency | Version | Async Capability | Status |
|---|---|---|---|
| fastmcp | >=3.0.2 | Capable (supports async servers) | Not used |
| pygithub | >=2.8.1 | Sync only | Blocking I/O |
| pydantic | >=2.12.3 | N/A (data validation) | Irrelevant |
| python-frontmatter | >=1.1.0 | Sync only | Blocking I/O |

**Note:** No `pytest-asyncio`, `anyio`, or other async testing/runtime libraries present.

---

## Architecture Notes for Async Migration

### Current Design Pattern

```
server.py (FastMCP 3.x synchronous tools)
  ↓ (calls)
operations.py (high-level CRUD, pure Python)
  ↓ (calls)
github.py (PyGithub blocking I/O)
```

### Blocking Chain

1. **Server → Operations:** All calls synchronous
2. **Operations → GitHub:** All calls through PyGithub (blocking)
3. **File I/O:** pathlib blocking reads/writes

### Migration Implications

If async were desired:

1. **FastMCP 3.x tools** can be async (framework supports both)
2. **PyGithub limitation**: No async version. Would require:
   - Switch to `aiohttp`-based client (e.g., `gidgethub`, `httpx` + custom GitHub API wrapper)
   - Rewrite all github.py functions with `async def` and `await`
3. **File I/O:** Use `aiofiles` for async pathlib equivalents
4. **operations.py:** Would need `async def` wrappers around all I/O calls

### Current Sufficiency

The synchronous design is **sufficient** for the MCP use case:
- MCP clients call tools serially (not concurrent)
- No high-frequency polling needed
- File system and GitHub API calls are inherently sequential per operation
- FastMCP 3.x handles multiplexing via JSON-RPC protocol, not Python async

---

## Recommendations

### No Action Required For

- Current workload (single-client serial operations)
- Code clarity (synchronous is simpler to understand and debug)
- PyGithub compatibility (well-tested blocking library)

### Consider Async If

- Multiple concurrent backlog operations needed (unlikely in MCP context)
- GitHub API rate limiting becomes a bottleneck
- Need to serve many simultaneous MCP clients with shared GitHub token

### Decision Point

Async migration is **architectural** (requires new GitHub client library), not a simple refactoring. Current sync design is appropriate for the project scope.

---

*Analysis completed: 2026-03-06*
*backlog_core version: 0.1.0*
*FastMCP version requirement: >=3.0.2*
