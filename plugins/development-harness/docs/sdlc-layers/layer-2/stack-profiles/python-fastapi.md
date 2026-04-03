# Stack Profile: Python + FastAPI

**Stack ID**: python-fastapi
**Language**: python
**Extends**: (none)

---

## Architecture Patterns

- Layered structure: routers → services → models
- Pydantic models for request/response validation
- Dependency injection for services
- Async route handlers for I/O-bound operations

---

## Toolchain Presets

### pyproject.toml

```toml
[project]
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.32.0",
    "pydantic>=2.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "httpx>=0.27.0",
    "ruff>=0.8.0",
]
```

---

## Reference Examples

- research/api-frameworks/fastapi.md
- Standard layout: `app/routers/`, `app/services/`, `app/models/`

---

## Research References

- research/api-frameworks/fastapi.md

---

## Output Contract

| Field | Description |
|-------|-------------|
| STATUS | DONE \| BLOCKED \| FAILED |
| SUMMARY | Brief outcome |
| ARTIFACTS | Produced files |
| VALIDATION | What was verified |
| NOTES | Optional context |
