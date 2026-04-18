# Python Development Rules

## uv Workspace — All Python Sub-Projects Must Be Workspace Members

Every Python sub-project in this repo (any directory with its own `pyproject.toml`) MUST be
declared as a member of the root uv workspace.

**Why**: Independent sub-projects produce their own `uv.lock` files. Separate lock files mean
separate dependency trees, separate Dependabot alerts, and inconsistent resolution of shared
packages like `fastmcp`, `cryptography`, and `pydantic`.

**Rule**: When adding any new Python sub-project (new `pyproject.toml`), immediately add it to
the `[tool.uv.workspace] members` list in the root `pyproject.toml`.

```toml
[tool.uv.workspace]
members = [
    "plugins/development-harness",
    "plugins/scientific-method/mcp/experiment-registry",
    # add new sub-projects here
]
```

After adding a member, run `uv lock` from the repo root to regenerate the single root `uv.lock`
and delete the sub-project's standalone `uv.lock` if one exists.

**Check**: `git ls-files | grep uv.lock` should return only `uv.lock` (the root lock file).
Any additional `uv.lock` entry is a policy violation.
