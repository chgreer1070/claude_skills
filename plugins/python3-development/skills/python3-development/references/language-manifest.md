# Language Manifest: Python

## Role Fulfillment

- architect: @python3-development:python-cli-architect
- test-designer: @python3-development:python-pytest-architect
- code-reviewer: @python3-development:code-reviewer
- design-spec: @python3-development:python-cli-design-spec
- linting: /holistic-linting:linting-root-cause-resolver

## Quality Gates

- format: `uv run ruff format {files}`
- lint: `uv run ruff check {files}`
- typecheck: Prefer `uv run ty check {files}`. If the project already uses mypy (`[tool.mypy]`, dev dependency, or hooks), use `uv run mypy {files}` per project config instead — do not mandate switching to ty.
- test: `uv run pytest tests/ --tb=short`
- standards: /python3-development:modernpython

## Project Detection

- markers: pyproject.toml, setup.py, setup.cfg
- source-patterns: src/**/*.py, **/*.py
- test-patterns: tests/**/*.py, test_*.py, *_test.py

## Process Flow Override

(none — uses default harness flow)
