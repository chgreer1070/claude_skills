# Factor I — Codebase

**Principle**: One codebase tracked in revision control, many deploys.

SOURCE: <https://www.12factor.net/codebase> (accessed 2026-02-26)

## Core Rules

- A twelve-factor app is **always tracked in a version control system** (Git, Mercurial, Subversion)
- A **codebase** is any single repo (centralized VCS like Subversion) or any set of repos sharing a root commit (decentralized VCS like Git)
- There is always a **one-to-one correlation** between the codebase and the app

## Violations

| Situation | Problem | Correct Approach |
|-----------|---------|-----------------|
| Multiple apps sharing the same code | Violates one-to-one correlation | Factor shared code into libraries via the dependency manager |
| Multiple codebases for one app | This is a distributed system, not an app | Each component is its own app; each can individually comply with twelve-factor |

## Deploys vs. App

A **deploy** is a running instance of the app. Typical deploys:

- Production site
- One or more staging sites
- Every developer's local development environment

The codebase is the **same** across all deploys, though different versions may be active in each deploy. For example:

- Developer has commits not yet deployed to staging
- Staging has commits not yet deployed to production

All share the same codebase — this makes them identifiable as different deploys of the same app.

## 2026 Context: Monorepos and Containers

In 2026, monorepos (using Nx, Turborepo, Bazel) are common. A monorepo does not violate Factor I as long as each app within it has its own build pipeline and artifact. The deploy model has extended to:

```text
codebase → artifact (container image or zip) → deploy (prod, staging, dev)
```

The same artifact goes to staging and production, providing confidence that what was tested is what runs.

SOURCE: <https://lukasniessen.medium.com/the-12-factor-app-15-years-later-does-it-still-hold-up-in-2026-c8af494e8465> (accessed 2026-02-26)
