---
name: python3-tools
description: Python tooling expertise for uv, Hatchling, ty type checker, pre-commit, TOML editing, and PyPI packaging. Activates on uv commands, pyproject.toml configuration, type checker setup, build system, git hooks, packaging, or release workflows.
user-invocable: false
---

# Python Tooling

Consult `python3-core` for standing defaults.

## uv Package Management

- `uv add` for dependencies (not `uv pip install`)
- `uv run` for execution (not `source .venv/bin/activate`)
- `uv sync --frozen` for CI; `uv sync --locked` to detect stale lockfiles
- PEP 723 shebang: `#!/usr/bin/env -S uv --quiet run --active --script`
- `uv venv --clear` to overwrite existing environments (since 0.10.0)

## Type Checker Detection

Check `.pre-commit-config.yaml` → CI config → `pyproject.toml`:

- **Default for new work**: ty (Astral)
- **Project runs mypy**: respect mypy.ini / `[tool.mypy]`; do not force ty
- **Project runs pyright/basedpyright**: respect that; do not force ty
- Do NOT infer active checker from presence of `[tool.mypy]` alone (may be stub config)

## Build Backend

Hatchling preferred:

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/my_package"]
```

## Pre-commit

Detect installed tool: read `.git/hooks/pre-commit` line 2 to identify pre-commit vs prek. Both use the same config file.

## TOML Editing

- `tomlkit` for read/write (preserves formatting) — open in text mode
- `tomllib` (stdlib) for read-only — `tomllib.load()` requires binary mode (`"rb"`), `tomllib.loads()` takes a string

## PyPI Packaging

```toml
# pyproject.toml
[project]
name = "my-package"
version = "0.1.0"
requires-python = ">=3.11"
classifiers = ["Typing :: Typed"]

[project.scripts]
my-cli = "my_package.cli:app"
```

## Standalone Tool Skills

Load these skills when the task is focused entirely on one tool:

- Load `python-engineering:uv` when the task involves uv commands, lockfiles, PEP 723 scripts, workspace configuration, Python version management, CI/CD integration, Docker setup with uv, or migration from pip/poetry/pyenv.
- Load `python-engineering:ty` when the task involves running ty type checks, configuring `ty.toml` or `[tool.ty]`, suppressing diagnostics, interpreting ty error codes, ty editor integration, or migrating from mypy/pyright to ty.
- Load `python-engineering:hatchling` when the task involves Hatchling build hooks, custom builders, wheel/sdist configuration, editable installs, VCS version sources, PEP 517/518/621/660 compliance, or setuptools migration.
- Load `python-engineering:toml-python` when the task requires advanced TOML manipulation: comment-preserving read-modify-write, atomic config updates, tomlkit API patterns, or XDG config file management.
- Load `python-engineering:pre-commit` when the task requires configuring hook stages, writing `.pre-commit-hooks.yaml` definitions, implementing `prepare-commit-msg` hooks, or distributing a tool as a pre-commit hook.
- Load `python-engineering:pypi-readme-creator` when the task involves creating or validating a PyPI README, choosing between Markdown and RST formats, configuring `readme` in `pyproject.toml`, or running `twine check`.

## References

- `references/tooling-defaults.md` — full tooling reference
- `references/compatibility-lanes.md` — version compatibility
