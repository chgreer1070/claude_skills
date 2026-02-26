# Factor XI — Logs

**Principle**: Treat logs as event streams.

SOURCE: <https://www.12factor.net/logs> (accessed 2026-02-26)

## Definition

Logs are the **stream of aggregated, time-ordered events** collected from the output streams of all running processes and backing services.

- Raw form: typically text format with one event per line
- Backtraces from exceptions may span multiple lines
- No fixed beginning or end — flow continuously as long as the app is operating

## Core Rules

A twelve-factor app:

- **Never concerns itself with routing or storage of its output stream**
- Should **not attempt to write to or manage logfiles**
- Each running process **writes its event stream, unbuffered, to `stdout`**

## Who Handles Routing and Storage?

The **execution environment** — not the app.

- **Local development**: developer views the stream in the foreground of their terminal
- **Staging or production**: each process' stream is captured by the execution environment, collated with all other streams from the app, and routed to one or more final destinations

Final destinations are **not visible to or configurable by the app** — completely managed by the execution environment.

## Log Routers

Open-source log routers available for this purpose:

- **Logplex** (Heroku)
- **Fluentd**

## Destinations and Uses

The event stream can be routed to:

- A file (for viewing or archival)
- Watched via realtime tail in a terminal (`tail -f`)
- A log indexing and analysis system such as **Splunk**
- A general-purpose data warehousing system such as **Hadoop/Hive**

These systems enable:

- Active alerting according to user-defined heuristics (e.g., error rate exceeding threshold)
- Visualizations (graphs of requests per second)
- Retrospective analysis (which customers hit a specific bug)

SOURCE: <https://www.12factor.net/logs> (accessed 2026-02-26)
