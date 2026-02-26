# Factor IX — Disposability

**Principle**: Maximize robustness with fast startup and graceful shutdown.

SOURCE: <https://www.12factor.net/disposability> (accessed 2026-02-26)

## Core Rule

Twelve-factor app processes are **disposable** — they can be started or stopped at a moment's notice.

This enables:

- Fast elastic scaling
- Rapid deployment of code or config changes
- Robustness of production deploys

## Fast Startup

Processes should minimize startup time. Ideally, a process takes **a few seconds** from launch command to ready state.

Short startup time provides:

- More agility for the release process and scaling up
- Robustness — process manager can more easily move processes to new physical machines

## Graceful Shutdown — Web Processes

When a web process receives `SIGTERM`:

1. Cease to listen on the service port (refuse any new requests)
2. Allow any current requests to finish
3. Exit

Implicit model: HTTP requests are short (no more than a few seconds). For long polling, the client should seamlessly attempt to reconnect when the connection is lost.

## Graceful Shutdown — Worker Processes

When a worker process receives `SIGTERM`:

1. Return the current job to the work queue

Examples by queueing backend:

| Backend | Mechanism |
|---------|-----------|
| RabbitMQ | Worker sends a `NACK` |
| Beanstalkd | Job returned to queue automatically when worker disconnects |
| Delayed Job | Worker must release its lock on the job record |

Implicit model: all jobs are **reentrant** (typically achieved by wrapping results in a transaction, or making the operation idempotent).

## Robustness Against Sudden Death

Processes should also be robust against **sudden death** (failure in the underlying hardware — less common than graceful shutdown, but possible).

Recommended approach: use a **robust queueing backend** such as Beanstalkd, which returns jobs to the queue when clients disconnect or time out.

Design principle: **crash-only design** — architect to handle unexpected, non-graceful terminations.

SOURCE: <https://www.12factor.net/disposability> (accessed 2026-02-26)
