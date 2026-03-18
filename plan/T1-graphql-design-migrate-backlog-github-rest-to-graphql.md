# T1 GraphQL Design: _resolve_labels_graphql

**Task**: T1 — Verify PyGithub GraphQL API and finalize _resolve_labels_graphql design
**Status**: COMPLETE
**Verified**: 2026-03-18
**PyGithub version confirmed**: 2.8.1

---

## 1. Confirmed graphql_query() Method Signature

**Location**: `Requester.graphql_query()` in PyGithub, NOT on `Github` directly.

SOURCE: Installed package at `.venv/lib/python3.11/site-packages/github/Requester.py`
Verified via: `inspect.getsource(Requester.Requester.graphql_query)`

```python
def graphql_query(
    self,
    query: str,
    variables: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    """
    Queries the GraphQL API.

    :param query: GraphQL query
    :param variables: GraphQL variables
    :return: ``(headers: dict, JSON Response: dict)``
    :raises: :class:`GithubException` for error status codes
    """
```

**Return value**: `(headers_dict, data_dict)` where `data_dict` contains the `"data"` key
on success. There is NO `"errors"` key in the return value — errors are RAISED as exceptions
before the function returns.

**Access from a `Github` instance**:

```python
gh.requester.graphql_query(query_string, {"owner": owner, "repo": repo})
```

`Github.requester` is a public property (type `Requester`) on the `Github` class.
SOURCE: `inspect.getsource(Github.requester.fget)` — confirmed public property.

**Access from a `Repository` instance** (important alternative):

```python
repo.requester.graphql_query(query_string, {"owner": owner, "repo": repo})
```

`Repository` inherits from `GithubObject`, which also exposes `requester` as a public
property. This means `_resolve_labels_graphql` can accept `repo: Repository` instead of
requiring a separate `gh: Github` parameter.
SOURCE: `inspect.getsource(GithubObject.requester.fget)` — same property defined on base class.

---

## 2. Error Handling: RAISES, Does Not Return Errors Dict

**Critical deviation from architecture spec Section 3 / ADR-004 framing.**

The architecture spec (Section 7.3) shows a mock pattern:

```python
# Architecture spec mock pattern — INCORRECT interpretation
gh_mock.graphql_query.return_value = {
    "errors": [{"message": "...", "type": "NOT_FOUND"}]
}
```

**This mock pattern is WRONG.** The actual `Requester.graphql_query` source raises
`GithubException` (or `UnknownObjectException`) before returning when `"errors"` is
present in the response. It never returns a dict containing `"errors"`.

**Actual behavior from source** (verified via `inspect.getsource`):

```python
# From Requester.graphql_query source:
if "errors" in data:
    if len(data["errors"]) == 1:
        error = data["errors"][0]
        if error.get("type") == "NOT_FOUND":
            raise github.UnknownObjectException(404, data, response_headers, error.get("message"))
    raise self.createException(400, response_headers, data)
return response_headers, data
```

**Consequence for implementation**: `_resolve_labels_graphql` does NOT need to check for
`"errors"` in the return value. It only needs to handle exceptions. The architecture spec's
ADR-004 error translation table still applies — but it describes what PyGithub RAISES, not
what the caller needs to translate.

**Revised ADR-004 error translation** (corrected from spec):

```text
GraphQL response condition                    | What PyGithub raises
----------------------------------------------+------------------------------------------
errors[0].type == "NOT_FOUND"                 | UnknownObjectException(404, data, ...)
errors array present, len == 1, other type    | createException(400, response_headers, data)
errors array present, len > 1                 | createException(400, response_headers, data)
HTTP 401                                      | BadCredentialsException(401, ...)
HTTP 403 + rate limit message                 | RateLimitExceededException(403, ...)
HTTP 403 + other                              | GithubException(403, ...)
```

**`_resolve_labels_graphql` error handling pattern**:

```python
def _resolve_labels_graphql(
    repo: Repository,
    repo_owner: str,
    repo_name: str,
    label_names: list[str],
) -> list[str]:
    # No need to check result["errors"] — PyGithub raises before returning
    # Callers wrap in try/except GithubException to handle all error types
    _headers, data = repo.requester.graphql_query(query, variables)
    # data always has "data" key here (no "errors" key ever returned)
    repo_data = data["data"]["repository"]
    ...
```

---

## 3. Architecture Spec Deviation: `gh: Github` Parameter Not Needed

The architecture spec declares `_resolve_labels_graphql` as:

```python
def _resolve_labels_graphql(
    gh: Github,
    repo_owner: str,
    repo_name: str,
    label_names: list[str],
) -> list[str]: ...
```

**Verified deviation**: The `gh: Github` parameter is unnecessary. Both `create_issue_for_item`
and `create_task_issue` already receive `repo: Repository`. Since `Repository.requester` is
a public property that provides access to `graphql_query()`, the helper can use `repo` directly.

**Recommended signature for T2 to implement**:

```python
def _resolve_labels_graphql(
    repo: Repository,
    repo_owner: str,
    repo_name: str,
    label_names: list[str],
) -> list[str]:
    """Resolve label names via a single GraphQL query.

    Returns the subset of label_names that exist in the repository.
    Raises GithubException for auth/network/permission failures.
    Missing individual labels are silently omitted (matches current REST behavior).

    Args:
        repo: PyGithub Repository object (provides requester access for GraphQL).
        repo_owner: GitHub repository owner (org or user name).
        repo_name: GitHub repository name (without owner prefix).
        label_names: List of label name strings to resolve.

    Returns:
        List of label name strings that exist in the repository.

    Raises:
        GithubException: If the GraphQL request fails (auth, network, permissions).
    """
```

**How to extract `repo_owner` and `repo_name` from `repo: Repository`**:

The `Repository` object has `.owner.login` and `.name` attributes. Callers can pass these
directly, or `_resolve_labels_graphql` can derive them from `repo.full_name.split("/", 1)`.
T2 should choose whichever is simpler given the call site.

---

## 4. Confirmed: create_issue() Accepts String Labels

**Verified** via `inspect.signature(Repository.create_issue)`:

```python
(self, title: 'str', body: 'Opt[str]' = NotSet, assignee: 'NamedUser | Opt[str]' = NotSet,
 milestone: 'Opt[Milestone]' = NotSet,
 labels: 'list[Label] | Opt[list[str]]' = NotSet,
 assignees: 'Opt[list[str]] | list[NamedUser]' = NotSet) -> 'Issue'
```

The `labels` parameter is typed as `list[Label] | Opt[list[str]]` — it accepts EITHER
`Label` objects OR plain strings.

SOURCE: Installed package `github/Repository.py`, verified via `inspect.signature()`.

**Consequence**: After `_resolve_labels_graphql` returns `list[str]`, callers pass those
strings directly to `repo.create_issue(labels=resolved_names)`. No conversion to Label
objects is needed. The architecture spec (Section 5.4) is correct on this point.

---

## 5. Finalized GraphQL Query Template

**Design**: Dynamic alias pattern for 3–5 labels per issue creation call.

```python
_LABEL_RESOLUTION_QUERY_TEMPLATE = """\
query ResolveLabelsBatch($owner: String!, $repo: String!) {{
  repository(owner: $owner, name: $repo) {{
{aliases}
  }}
}}"""

_LABEL_ALIAS_TEMPLATE = '    label{i}: label(name: "{name}") {{ name }}'
```

**Query generation** (for T2 to implement):

```python
aliases = "\n".join(
    _LABEL_ALIAS_TEMPLATE.format(i=i, name=name)
    for i, name in enumerate(label_names)
)
query = _LABEL_RESOLUTION_QUERY_TEMPLATE.format(aliases=aliases)
variables = {"owner": repo_owner, "repo": repo_name}
```

**Why double braces `{{` and `}}`**: Python `.format()` requires escaping literal braces.
The generated query contains single braces as valid GraphQL syntax.

**Security note**: Label names must NOT be interpolated via f-string or `.format()` into
the query string. They are embedded as string literals in the alias lines — which is
acceptable ONLY because label names come from the application's own label list (not user
input) and are short alphanumeric strings. For full safety, T2 should validate label names
against `[a-zA-Z0-9:_\-]` before embedding.

**The `id` field is NOT needed**: The architecture spec query template includes `name id`
per alias. Since `create_issue(labels=list[str])` accepts plain name strings, the node ID
is not used. Only `name` is needed:

```graphql
label0: label(name: "status:needs-grooming") { name }
```

**Example generated query for `["status:needs-grooming", "priority:p1", "type:feature"]`**:

```graphql
query ResolveLabelsBatch($owner: String!, $repo: String!) {
  repository(owner: $owner, name: $repo) {
    label0: label(name: "status:needs-grooming") { name }
    label1: label(name: "priority:p1") { name }
    label2: label(name: "type:feature") { name }
  }
}
```

**Parsing the response** (from `data` returned by `repo.requester.graphql_query`):

```python
_headers, data = repo.requester.graphql_query(query, variables)
repo_node = data["data"]["repository"]
resolved = []
for i, name in enumerate(label_names):
    alias = f"label{i}"
    node = repo_node.get(alias)
    if node is not None:
        resolved.append(node["name"])
    # else: label missing — silently omit (matches current REST behavior)
return resolved
```

---

## 6. Lines to Change in github.py

### create_issue_for_item() — lines 119–126

**Current code** (lines 119–126):

```python
labels = ["status:needs-grooming", priority_gh, type_gh]
label_objs = []
for name in labels:
    try:
        label_objs.append(repo.get_label(name))
    except GithubException:
        out.warn(f"  WARNING: label '{name}' not found")
issue = repo.create_issue(title=issue_title, body=body, labels=label_objs)
```

**After migration**:

```python
labels = ["status:needs-grooming", priority_gh, type_gh]
owner, repo_name = repo.full_name.split("/", 1)
try:
    resolved_labels = _resolve_labels_graphql(repo, owner, repo_name, labels)
    missing = set(labels) - set(resolved_labels)
    for name in missing:
        out.warn(f"  WARNING: label '{name}' not found")
except GithubException:
    resolved_labels = labels  # fallback: pass all names, let GitHub ignore unknowns
issue = repo.create_issue(title=issue_title, body=body, labels=resolved_labels)
```

**Note on fallback**: The architecture spec section 7.3 test case 4 mentions "falls back to
REST get_label() loop (graceful degradation path)". The fallback above passes all label name
strings directly — simpler than re-implementing the REST loop, and `create_issue()` with
string labels silently ignores unknown labels on GitHub's side. T2 decides the exact fallback
strategy — this is a design note, not a constraint.

### create_task_issue() — lines 539–544

**Current code** (lines 539–544):

```python
label_objs = []
for name in labels or []:
    try:
        label_objs.append(repo.get_label(name))
    except GithubException:
        out.warn(f"  WARNING: label '{name}' not found, skipping")
```

**After migration**:

```python
label_names = labels or []
if label_names:
    owner, repo_name_str = repo.full_name.split("/", 1)
    try:
        resolved_labels = _resolve_labels_graphql(repo, owner, repo_name_str, label_names)
        missing = set(label_names) - set(resolved_labels)
        for name in missing:
            out.warn(f"  WARNING: label '{name}' not found, skipping")
    except GithubException:
        resolved_labels = label_names  # fallback
else:
    resolved_labels = []
# Then: repo.create_issue(title=title, body=body, labels=resolved_labels)
```

---

## 7. Mock Pattern Correction for T4 (Tests)

The architecture spec (Section 7.3) shows this mock pattern for GraphQL — which is WRONG
because `graphql_query` raises exceptions, it does not return `{"errors": [...]}`:

```python
# WRONG — graphql_query never returns an errors dict
gh_mock.graphql_query.return_value = {
    "errors": [{"message": "...", "type": "NOT_FOUND"}]
}
```

**Correct mock patterns for T4**:

```python
# Mock target: repo_mock.requester.graphql_query (NOT gh_mock.graphql_query)
from unittest.mock import MagicMock
from github.Repository import Repository
from github import GithubException, UnknownObjectException

repo_mock = MagicMock(spec=Repository)

# Success: all labels found
repo_mock.requester.graphql_query.return_value = (
    {},  # headers dict
    {
        "data": {
            "repository": {
                "label0": {"name": "status:needs-grooming"},
                "label1": {"name": "priority:p1"},
                "label2": None,  # label not found
            }
        }
    },
)

# NOT_FOUND error (single error with type NOT_FOUND)
repo_mock.requester.graphql_query.side_effect = UnknownObjectException(
    404, {"errors": [{"type": "NOT_FOUND", "message": "Could not resolve to a Repository"}]}, {}
)

# Auth/network failure
repo_mock.requester.graphql_query.side_effect = GithubException(
    401, {"message": "Bad credentials"}, {}
)
```

---

## 8. Summary of Deviations from Architecture Spec

| Spec claim | Verified reality | Impact on T2 |
|---|---|---|
| `graphql_query` is on `Github` object | It is on `Requester`; accessed via `gh.requester.graphql_query()` or `repo.requester.graphql_query()` | Use `repo.requester.graphql_query()` — no `gh: Github` param needed |
| Returns `{"errors": [...]}` on error | Raises `GithubException` or `UnknownObjectException` — never returns errors dict | No `"errors"` key check needed in implementation |
| Mock as `gh_mock.graphql_query.return_value = {"errors": [...]}` | Must mock `repo_mock.requester.graphql_query.side_effect = GithubException(...)` | T4 test mocks must use `side_effect`, not `return_value` for error cases |
| `_resolve_labels_graphql(gh, owner, name, labels)` with `gh: Github` | `repo.requester` provides same access; use `_resolve_labels_graphql(repo, owner, name, labels)` | Signature change: replace `gh: Github` with `repo: Repository` |
| Query template includes `id` field per alias | `id` is unused (create_issue accepts strings); only `name` needed | Simplify query: `label{i}: label(name: "...") {{ name }}` |

---

## 9. Verification Commands

```bash
# Confirm PyGithub version
uv run python -c "import importlib.metadata; print(importlib.metadata.version('PyGithub'))"
# Expected: 2.8.1

# Confirm graphql_query signature
uv run python -c "from github import Requester; import inspect; print(inspect.signature(Requester.Requester.graphql_query))"
# Expected: (self, query: 'str', variables: 'dict[str, Any]') -> 'tuple[dict[str, Any], dict[str, Any]]'

# Confirm repo.requester access
uv run python -c "from github.GithubObject import GithubObject; print(type(GithubObject.requester))"
# Expected: <class 'property'>

# Confirm create_issue labels parameter accepts strings
uv run python -c "from github.Repository import Repository; import inspect; print(inspect.signature(Repository.create_issue))"
# Expected: includes labels: 'list[Label] | Opt[list[str]]'
```
