# Layer 2 Overview

Stack profiles extend Layer 1 (language manifests) with architecture patterns, toolchain configuration, and reference examples. They are **optional** — a project can use Layer 0 + Layer 1 only.

---

## Inheritance

```
Layer 0 (SDLC-agnostic).claude/docs/sdlc-layers/layer-0/)
    ↓
Layer 1 (Language manifest)
    ↓
Layer 2 (Stack profile) — optional
```

---

## When to Use Stack Profiles

- **Stack-specific**: Python + FastAPI (web API), Python + Tornado (async), TypeScript + React (frontend)
- **Goal-specific**: CLI tool, web API, library, MCP server
- **Workflow-specific**: documentation-authoring, backlog_management, changelog_generation

---

## Stack Profile Composition

Stack profiles support `extends` for inheritance:

```yaml
stack: daily_releases
extends: changelog_generation
```

---

## Research Mapping

Stack profiles reference research entries:

- `api-frameworks/fastapi.md` → python-fastapi
- `api-frameworks/tornado.md` → python-tornado
- `developer-tools/copier-astral.md` → python-cli (project scaffold)
