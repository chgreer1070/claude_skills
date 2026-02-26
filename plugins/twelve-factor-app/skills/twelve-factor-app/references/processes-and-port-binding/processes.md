# Factor VI — Processes

**Principle**: Execute the app as one or more stateless processes.

SOURCE: <https://www.12factor.net/processes> (accessed 2026-02-26)

## Core Rules

**Twelve-factor processes are stateless and share-nothing.**

Any data that needs to persist must be stored in a **stateful backing service**, typically a database.

## What the Filesystem Can Be Used For

The memory space or filesystem of a process can be used as a **brief, single-transaction cache**. Example: downloading a large file, operating on it, storing results in a database.

A twelve-factor app **never assumes** that anything cached in memory or on disk will be available on a future request or job because:

- With many processes of each type running, a future request is likely served by a different process
- A restart (triggered by code deploy, config change, or execution environment relocation) wipes all local state

## Asset Compilation

Asset packagers that use the filesystem as a cache (e.g., django-assetpackager) violate this principle. A twelve-factor app prefers compiling during the **build stage** instead. Asset packagers like Jammit and the Rails asset pipeline can be configured to package assets during the build stage.

## Violations — Sticky Sessions

**Sticky sessions** (caching user session data in memory of a process and expecting future requests from the same visitor to be routed to the same process) are a **violation of twelve-factor and should never be used or relied upon**.

Session state data belongs in a datastore that offers time-expiration, such as Memcached or Redis.

## Process Execution Contexts

| Context | Description |
|---------|-------------|
| Simplest case | Stand-alone script, developer's local laptop, launched via command line |
| Production | Many process types, instantiated into zero or more running processes |

SOURCE: <https://www.12factor.net/processes> (accessed 2026-02-26)

## Modern Reinterpretation (2025)

- **Stateless processes → Kubernetes Pods**: The process model maps directly to Pods. Kubernetes
  enforces statelessness by design — ephemeral containers, no persistent local state between Pod
  restarts.
- **Process manager → Kubernetes Deployment/ReplicaSet**: The platform handles process supervision,
  restart on failure, and horizontal scaling. No per-app process manager (Foreman, supervisord) is
  required.
- **Sidecar containers**: Modern applications run multiple containers per Pod (sidecar pattern for
  logging, service mesh, secrets injection). This extends "one process per container" to "one concern
  per container in a Pod".
- **Init containers**: Pre-run initialization (migrations, config bootstrapping) now runs as init
  containers — a formalization of Factor XII admin processes at the process level, guaranteed to
  complete before application containers start.
- The share-nothing principle is enforced architecturally by Kubernetes — no shared filesystem
  between Pods by default, and ephemeral storage is scoped to the Pod's lifetime.

SOURCE: <https://12factor.net/blog/evolving-twelve-factor> (accessed 2026-02-26)
