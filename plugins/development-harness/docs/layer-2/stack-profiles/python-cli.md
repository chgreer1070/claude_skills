# Stack Profile: Python CLI

**Stack ID**: python-cli
**Language**: python
**Extends**: (none)

---

## Architecture Patterns

- Typer or argparse for CLI interface
- Entry point in pyproject.toml
- src/ layout for package distribution

---

## Toolchain Presets

### pyproject.toml

```toml
[project.scripts]
{package-name} = "{package}.cli:main"

[project.optional-dependencies]
dev = [
    "typer>=0.12.0",
    "ruff>=0.8.0",
    "pytest>=8.0",
]
```

---

## Reference Examples

- research/developer-tools/copier-astral.md (project scaffold)
- Standard layout: src/{package}/cli.py, src/{package}/__main__.py

---

## Research References

- research/developer-tools/copier-astral.md

---

## Output Contract

| Field | Description |
|-------|-------------|
| STATUS | DONE \| BLOCKED \| FAILED |
| SUMMARY | Brief outcome |
| ARTIFACTS | Produced files |
| VALIDATION | What was verified |
| NOTES | Optional context |
