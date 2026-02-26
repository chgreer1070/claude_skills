# Factor II — Dependencies

**Principle**: Explicitly declare and isolate dependencies.

SOURCE: <https://www.12factor.net/dependencies> (accessed 2026-02-26)

## Core Rules

- A twelve-factor app **never relies on implicit existence of system-wide packages**
- Declares all dependencies **completely and exactly** via a dependency declaration manifest
- Uses a **dependency isolation tool** during execution to ensure no implicit dependencies leak in from the surrounding system
- Full explicit dependency specification applied **uniformly to both production and development**

## Declaration + Isolation Must Be Used Together

Only one of the two (declaration without isolation, or isolation without declaration) is **not sufficient** to satisfy twelve-factor.

## Tools by Language

| Language | Declaration Tool | Isolation Tool |
|----------|-----------------|----------------|
| Ruby | Bundler (`Gemfile`) | `bundle exec` |
| Python | Pip (`requirements.txt`) | Virtualenv |
| C | Autoconf | Static linking |
| JavaScript/Node | npm/yarn (`package.json`) | `node_modules` scoped to app |
| Python (modern) | uv (`pyproject.toml`) | uv venv |

SOURCE: <https://www.12factor.net/dependencies> (accessed 2026-02-26)

## Benefits

- **Simplifies new developer onboarding**: Developer checks out codebase, installs language runtime + dependency manager, runs one deterministic build command — all needed dependencies are set up
- **No implicit system tool leakage**: Even system tools like `curl` or `ImageMagick` must be vendored if used, ensuring no assumption about tool presence on the execution environment

## 2026 Context: Containers

When an app runs in a Docker container, the container is the isolation boundary — everything the app needs is inside it. Package managers handle declaration; containers handle isolation. This makes explicit dependency isolation the default rather than an extra step.

SOURCE: <https://lukasniessen.medium.com/the-12-factor-app-15-years-later-does-it-still-hold-up-in-2026-c8af494e8465> (accessed 2026-02-26)

## Modern Reinterpretation (2025)

- **Container images = complete dependency isolation**: The Docker image contains the runtime, OS
  libraries, and application dependencies as a single immutable artifact. No "no system-wide
  packages" concern — the container IS the isolation boundary.
- **Multi-stage builds**: Separate build dependencies from runtime dependencies. Only
  production-necessary deps end up in the final image, reducing attack surface and image size.
- **Supply chain security (SLSA, SBOM)**: Modern dependency management extends to supply chain —
  Software Bill of Materials (SBOM) generation, SLSA provenance attestations, container image signing
  (Sigstore/cosign).
- **The "mommy server" problem is solved**: The original concern about implicit system-wide tools is
  eliminated by containers. New concerns emerge instead — base image bloat and unvetted transitive
  dependencies in container layers.
- Runtime sidecar dependencies (service mesh, logging agents) are declared in Kubernetes manifests —
  extending dependency declaration to infrastructure-level dependencies, not just application-level
  packages.

SOURCE: <https://12factor.net/blog/evolving-twelve-factor> (accessed 2026-02-26)
SOURCE: <https://12factor.net/dependencies> (accessed 2026-02-26)
