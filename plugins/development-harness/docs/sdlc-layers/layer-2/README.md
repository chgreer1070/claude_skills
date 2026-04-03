# Layer 2: Stack/Goal-Specific

Stack profiles extend language manifests with architecture patterns, toolchain config, and reference examples. They are **optional** — a project can use Layer 0 + Layer 1 only.

---

## What Belongs Here

| Content | Description |
|---------|-------------|
| **Architecture patterns** | e.g., FastAPI layered structure, Tornado async patterns |
| **Toolchain configuration** | pyproject.toml presets, package.json templates |
| **Reference implementations** | Example projects, task templates |
| **Stack research** | Links to research/ entries (api-frameworks/fastapi.md, etc.) |
| **Stack profiles** | Named profiles (python-fastapi, python-cli, documentation-authoring) |

---

## Documents

| Document | Purpose |
|----------|---------|
| [layer-2-overview.md](./layer-2-overview.md) | Stack profiles extend language manifests |
| [stack-profile-schema.md](./stack-profile-schema.md) | Schema for stack profiles |
| [stack-profile-template.md](./stack-profile-template.md) | For authors adding new stacks |

---

## Pilot Profiles

| Profile | Path | Description |
|---------|------|-------------|
| python-fastapi | [stack-profiles/python-fastapi.md](./stack-profiles/python-fastapi.md) | Python + FastAPI web API |
| python-cli | [stack-profiles/python-cli.md](./stack-profiles/python-cli.md) | Python CLI tool |
