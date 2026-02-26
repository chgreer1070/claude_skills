# Factor V — Build, Release, Run

**Principle**: Strictly separate build and run stages.

SOURCE: <https://www.12factor.net/build-release-run> (accessed 2026-02-26)

## The Three Stages

A codebase is transformed into a (non-development) deploy through three stages:

### 1. Build Stage

Transforms a code repo into an executable bundle (the **build**):

- Takes a version of the code at a commit specified by the deployment process
- Fetches vendor dependencies
- Compiles binaries and assets

### 2. Release Stage

Takes the build produced by the build stage and combines it with the deploy's current **config**. The resulting **release**:

- Contains both the build and the config
- Is ready for immediate execution in the execution environment

### 3. Run Stage

Runs the app in the execution environment by launching some set of the app's **processes** against a selected release. Also known as "runtime."

## Key Properties

### Strict Separation Is Enforced

It is impossible to make changes to the code at runtime, since there is no way to propagate those changes back to the build stage.

### Releases Are Immutable and Append-Only

- Every release has a **unique release ID** (e.g., timestamp `2011-04-06-20:32:17` or incrementing number `v100`)
- Releases are an **append-only ledger** — a release cannot be mutated once created
- Any change must create a **new release**

### Rollback

Deployment tools offer release management tools, notably the ability to roll back to a previous release.

Example: The Capistrano deployment tool stores releases in a `releases/` subdirectory, where the current release is a symlink. Its `rollback` command quickly reverts to a previous release.

### Initiators by Stage

| Stage | Who Initiates |
|-------|--------------|
| Build | App developers, whenever new code is deployed |
| Run | Can happen automatically (server restart, process manager, crash recovery) |

## Why Separation Matters

Runtime execution is restricted to the selected release — no ad-hoc code changes in production. Any fix requires a new build → release → deploy cycle, ensuring traceability and rollback capability.

SOURCE: <https://www.12factor.net/build-release-run> (accessed 2026-02-26)

## Modern Reinterpretation (2025)

- **Build stage → CI pipeline**: Docker image build replaces the original "executable bundle" concept.
  Images are immutable artifacts — equivalent to releases in the original model. A GitHub Actions or
  GitLab CI pipeline builds and pushes the image to a container registry.
- **Release stage → GitOps/Helm**: The release is now a Helm chart or Kustomize overlay combining
  the image (build) with environment-specific values (config). GitOps tools (ArgoCD, Flux) automate
  promotion of releases across environments.
- **Run stage → Kubernetes orchestration**: The platform runs immutable containers from the release
  image. Rollback is now container image tag rollback or Helm chart rollback — more reliable than the
  Capistrano symlink approach.
- **Capistrano is obsolete**: The canonical example is now GitHub Actions/GitLab CI → container
  registry → Kubernetes deployment, not a deployment tool managing symlinks on a server.
- The core principle (strict stage separation, immutable releases) is MORE enforced in
  containers/Kubernetes, not less — the platform physically prevents in-place code changes at runtime.

SOURCE: <https://12factor.net/blog/evolving-twelve-factor> (accessed 2026-02-26)
SOURCE: <https://12factor.net/build-release-run> (accessed 2026-02-26)
