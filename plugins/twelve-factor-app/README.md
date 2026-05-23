<p align="center">
  <img src="./assets/hero.png" alt="twelve-factor-app" width="800" />
</p>

# twelve-factor-app

Gives Claude deep knowledge of the Twelve-Factor App methodology — 12 original principles plus 3 modern extensions — for building portable, cloud-native applications. Use it when reviewing architecture, auditing codebases for compliance, or advising on deployment and configuration patterns.

## What It Does

The Twelve-Factor App is a set of principles for building software-as-a-service applications that are portable across execution environments, deployable on modern cloud platforms, scalable without significant change, and maintainable by different developers over time.

This plugin provides comprehensive coverage of all 15 factors with guidance on applying them in modern environments: Kubernetes, containers, GitOps, and 2025 community extensions. Claude can review your application against any factor, explain trade-offs, and suggest compliant patterns.

## The Factors

**Codebase & Dependencies**
- **I. Codebase** — One codebase per app tracked in version control; many deploys
- **II. Dependencies** — Declare and isolate all dependencies explicitly

**Configuration & Backing Services**
- **III. Config** — Store config in the environment, not in code
- **IV. Backing Services** — Treat databases, queues, and caches as attached resources

**Build, Release & Run**
- **V. Build, Release, Run** — Strictly separate build and run stages

**Processes & Concurrency**
- **VI. Processes** — Execute the app as one or more stateless processes
- **VII. Port Binding** — Export services via port binding
- **VIII. Concurrency** — Scale out via the process model
- **IX. Disposability** — Maximize robustness with fast startup and graceful shutdown

**Observability & Parity**
- **X. Dev/Prod Parity** — Keep development, staging, and production as similar as possible
- **XI. Logs** — Treat logs as event streams
- **XII. Admin Processes** — Run admin tasks as one-off processes

**Modern Extensions (2025)**
- **XIII. API First** — Design services around explicit API contracts
- **XIV. Telemetry** — Built-in metrics, tracing, and structured logging
- **XV. Auth & Security** — Security as a first-class factor, not an afterthought

## Installation

```bash
/plugin marketplace add Jamie-BitFlight/claude_skills
/plugin install twelve-factor-app@jamie-bitflight-skills
```

## Usage

```text
/twelve-factor-app "review this service's configuration handling against Factor III"
/twelve-factor-app "explain Factor XII (admin processes) for a Kubernetes deployment"
/twelve-factor-app "audit this application for twelve-factor compliance"
/twelve-factor-app "how should I handle database migrations in a twelve-factor app?"
```

## When to Use

- Reviewing application architecture for cloud-native readiness
- Auditing a codebase for methodology compliance before a production migration
- Advising on configuration management (Factor III is the most commonly violated)
- Designing deployment pipelines with proper build/release/run separation
- Explaining the methodology to a team new to cloud-native development
- Evaluating how Kubernetes or GitOps workflows map to twelve-factor principles

## Requirements

- Claude Code v2.0+
