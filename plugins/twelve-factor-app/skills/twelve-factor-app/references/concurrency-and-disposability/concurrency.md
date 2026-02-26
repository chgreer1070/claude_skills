# Factor VIII — Concurrency

**Principle**: Scale out via the process model.

SOURCE: <https://www.12factor.net/concurrency> (accessed 2026-02-26)

## Core Model

The twelve-factor app draws inspiration from the **Unix process model for service daemons**. This model lets developers allocate different workloads to specific process types.

## Process Types

Each type of work is handled by a **process type**:

| Process Type | Handles |
|-------------|---------|
| `web` | HTTP requests |
| `worker` | Long-running background tasks |
| `clock` | Scheduled jobs |

The set of running processes across all types is the **process formation**.

## Why Scale Out Instead of Up?

The share-nothing, horizontally partitionable nature of twelve-factor processes facilitates **simple and reliable scaling** by adding more processes — not by growing a single larger VM.

- Vertical scaling (growing an individual VM) has limitations
- Horizontal scaling (adding more processes) is the twelve-factor approach

Individual processes can still use internal multiplexing via threads or async/event-driven models, but the primary scaling mechanism is adding processes.

## Contrast with Traditional Approaches

| Traditional | Twelve-Factor |
|-------------|--------------|
| PHP: child processes of Apache, started based on request volume | Process types as first-class citizens |
| Java: massive JVM uberprocess managing concurrency internally through threads | Separate, visible process types |
| Running processes minimally visible to developers | Process formation is explicit and developer-managed |

## Process Management

Twelve-factor app processes should **not daemonize** or write PID files.

Instead, rely on:

- The operating system's process manager (e.g., `systemd`)
- Cloud platform-based distributed process managers
- `Foreman` during development

These tools manage output streams, handle crashed processes, and address user-initiated restarts and shutdowns.

SOURCE: <https://dev.to/lsfernandes92/the-twelve-factor-app-concurrency-5d3l> (accessed 2026-02-26)
SOURCE: <https://www.12factor.net/concurrency> (accessed 2026-02-26)
