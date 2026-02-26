---
name: twelve-factor-app
description: Reference guide for the Twelve-Factor App methodology — 15 principles (12 original + 3 modern extensions) for building portable, resilient, cloud-native applications. Use when evaluating application architecture, designing cloud-native services, reviewing codebases for methodology compliance, advising on configuration, scaling, observability, security, and deployment patterns. Incorporates the 2025 open-source community evolution and cloud-native reinterpretations of each factor.
---

# Twelve Factor App

The Twelve-Factor App is a methodology for building software-as-a-service applications that are portable, deployable on modern cloud platforms, and scalable without significant architectural changes. Originally published in 2011 by Adam Wiggins (Heroku), the methodology was open-sourced in November 2024 and is now actively maintained at [github.com/heroku/12factor](https://github.com/heroku/12factor) with community-driven updates for Kubernetes, containers, and GitOps workflows.

SOURCE: <https://12factor.net/blog/open-source-announcement> (accessed 2026-02-26)

## The Twelve Factors

| Factor | Principle |
|--------|-----------|
| I. Codebase | One codebase tracked in revision control, many deploys |
| II. Dependencies | Explicitly declare and isolate dependencies |
| III. Config | Store config in the environment |
| IV. Backing services | Treat backing services as attached resources |
| V. Build, release, run | Strictly separate build and run stages |
| VI. Processes | Execute the app as one or more stateless processes |
| VII. Port binding | Export services via port binding |
| VIII. Concurrency | Scale out via the process model |
| IX. Disposability | Maximize robustness with fast startup and graceful shutdown |
| X. Dev/prod parity | Keep development, staging, and production as similar as possible |
| XI. Logs | Treat logs as event streams |
| XII. Admin processes | Run admin/management tasks as one-off processes |

## Modern Extensions (Beyond 12-Factor)

Three additional factors are widely adopted in cloud-native practice, established by Kevin Hoffman's *Beyond the Twelve-Factor App* (O'Reilly, 2016) and formalized in the 15-factor methodology:

| Factor | Principle |
|--------|-----------|
| XIII. API-First | Design and publish the service API contract before implementing the backing logic |
| XIV. Telemetry | Treat observability (metrics, traces, structured logs) as a first-class operational requirement |
| XV. Authentication and Authorization | Elevate identity, authn, and authz to first-class concerns in service design |

SOURCE: <https://www.oreilly.com/library/view/beyond-the-twelve-factor/9781492042631/> (accessed 2026-02-26)

## Reference Categories

### Methodology Overview

Background, goals, target audience, and design philosophy.

- [./references/methodology-overview/index.md](./references/methodology-overview/index.md)

### Codebase and Dependencies (Factors I and II)

Version control discipline and explicit dependency management.

- [./references/codebase-and-dependencies/index.md](./references/codebase-and-dependencies/index.md)

### Configuration and Backing Services (Factors III and IV)

Environment-based config and treating backing services as swappable attached resources.

- [./references/configuration-and-backing-services/index.md](./references/configuration-and-backing-services/index.md)

### Build, Release, Run (Factor V)

Strict separation of the three stages that transform a codebase into a running deploy.

- [./references/build-release-run/index.md](./references/build-release-run/index.md)

### Processes and Port Binding (Factors VI and VII)

Stateless share-nothing process execution and self-contained service export via port binding.

- [./references/processes-and-port-binding/index.md](./references/processes-and-port-binding/index.md)

### Concurrency and Disposability (Factors VIII and IX)

Scaling via the process model and building robust disposable processes.

- [./references/concurrency-and-disposability/index.md](./references/concurrency-and-disposability/index.md)

### Dev/Prod Parity and Logs (Factors X and XI)

Minimizing environment gaps and treating logs as event streams.

- [./references/dev-prod-parity-and-logs/index.md](./references/dev-prod-parity-and-logs/index.md)

### Admin Processes (Factor XII)

Running one-off administrative and maintenance tasks as processes in the same environment as the app.

- [./references/admin-processes/index.md](./references/admin-processes/index.md)

### Modern Evolution

Open-source governance, narrow-conduit concept, 15-factor extensions, Reactive Principles, and monolith modernization patterns.

- [./references/modern-evolution/index.md](./references/modern-evolution/index.md)

## Quick Compliance Checklist

Use this to audit an application against the methodology:

- [ ] Single codebase in VCS; shared code extracted to libraries (I)
- [ ] All dependencies declared in manifest; isolation tool in use (II)
- [ ] All deploy-varying config in env vars; no config in code (III)
- [ ] Backing services accessed via URL/credentials from config; swappable without code changes (IV)
- [ ] Build, release, run stages strictly separated; releases immutable with unique IDs (V)
- [ ] Processes stateless and share-nothing; no sticky sessions; session state in external store (VI)
- [ ] App self-contained; webserver library bundled; service exported via port binding (VII)
- [ ] Scale via adding processes, not growing single process; no daemonizing or PID files (VIII)
- [ ] Fast startup; graceful SIGTERM handling; robust against sudden death (IX)
- [ ] Dev and prod use same backing service types; time/personnel/tools gaps minimized (X)
- [ ] All log output to stdout; no log file management in app code (XI)
- [ ] Admin tasks run as one-off processes against same release and config as regular processes (XII)
- [ ] Service API contract defined and documented before implementation (XIII)
- [ ] Metrics, distributed traces, and structured logs emitted; observability platform configured (XIV)
- [ ] Authentication and authorization handled as first-class concerns; no ad-hoc security (XV)
