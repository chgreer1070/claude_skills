# Monolith Modernization and Twelve-Factor as Migration Target

Documents the Strangler Fig pattern for incremental legacy modernization, the modular monolith as
a valid intermediate architecture, and how 12-factor compliance functions as the goal state for
extracted services.

---

## Section 1: The Strangler Fig Pattern

### Core Concept

The Strangler Fig pattern describes a strategy for gradually replacing a monolithic system by
extracting functionality piece by piece, while keeping the original system operational throughout
the transition. The name comes from the strangler fig tree, which grows around an existing tree
over time, eventually replacing it entirely.

Martin Fowler documented the original pattern in a widely cited reference:

SOURCE: [Martin Fowler: Strangler Fig](https://martinfowler.com/bliki/StranglerFigApplication.html) (accessed 2026-02-26)

The migration proceeds in three recurring steps:

- **Identify**: Select a bounded area of functionality in the monolith that can be extracted as a
  standalone service.
- **Extract**: Build the replacement service alongside the monolith. Route traffic for the selected
  functionality to the new service.
- **Remove**: Once the replacement is proven in production, remove the corresponding code from the
  monolith.

This cycle repeats until the monolith has been fully replaced or reduced to a residual core that is
either acceptable to leave or can be retired entirely.

### Contemporary Guidance (2024-2025)

**CircleCI (April 2025)**:

> "The Strangler Pattern offers a controlled, incremental approach to migration, enabling
> organizations to gradually replace functionality while keeping systems operational throughout
> the transition."

SOURCE: [CircleCI: Strangler pattern implementation for safe microservices transition](https://circleci.com/blog/strangler-pattern-implementation-for-safe-microservices-transition/) (accessed 2026-02-26)

**AWS Prescriptive Guidance**: AWS formally documents the Strangler Fig as an approved design
pattern for monolith migration, providing implementation guidance for cloud environments.

SOURCE: [AWS Prescriptive Guidance: Strangler fig pattern](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/strangler-fig.html) (accessed 2026-02-26)

**Thoughtworks (October 2023)**: Multi-part analysis of the Strangler Fig pattern as applied to
legacy modernization in contemporary enterprise contexts.

SOURCE: [Thoughtworks: Embracing the Strangler Fig pattern for legacy modernization](https://www.thoughtworks.com/en-gb/insights/articles/embracing-strangler-fig-pattern-legacy-modernization-part-one) (accessed 2026-02-26)

### How 12-Factor Principles Guide Seam Selection

Not all monolith seams make equally good extraction candidates. 12-factor principles provide useful
criteria for identifying high-value extraction targets:

- **Factor III (Config)**: If a subsystem requires configuration values that differ between
  environments, it is a strong extraction candidate — the monolith likely cannot express that
  separation cleanly.
- **Factor IV (Backing Services)**: Subsystems that access distinct backing services (a specific
  database schema, a dedicated message queue) have natural service boundaries.
- **Factor VI (Processes)**: Subsystems with distinct scaling profiles are strong candidates —
  extracting them as stateless services enables independent horizontal scaling.
- **Factor IX (Disposability)**: Subsystems that have long startup times, hold locks, or resist
  graceful shutdown should be extracted and refactored — these are operational liabilities in the
  monolith and will remain so unless addressed.

---

## Section 2: The Modular Monolith as a Valid Intermediate Step

### Modular Monolith Architecture

Not all applications should be decomposed into microservices. The modular monolith is a recognized
intermediate architectural form that applies internal modularity principles without the operational
overhead of distributed services.

A modular monolith has:

- Strict internal module boundaries (each module owns its data and exposes an interface)
- Single deployment artifact
- In-process communication between modules (no network overhead)
- Independent testability per module

The value proposition: teams get the design discipline of service-oriented thinking — clear
boundaries, explicit interfaces, independent evolution — without the distributed systems complexity
of network calls, service discovery, and distributed tracing.

### Martin Fowler's Patterns of Legacy Displacement (March 2024)

Martin Fowler published a complementary pattern framework specifically addressing the modernization
process:

> "When faced with the need to replace existing software systems, organizations often fall into a
> cycle of half-completed technology replacements. Our experiences have taught us a series of
> patterns that allow us to break this cycle."

The patterns address both the technical and organisational challenges of legacy displacement,
recognising that incomplete migrations create more complexity than the original monolith.

SOURCE: [Martin Fowler: Patterns of Legacy Displacement](https://martinfowler.com/tags/legacy%20modernization.html) (accessed 2026-02-26)

### When Modular Monolith Is Appropriate

The modular monolith is appropriate when:

- The team does not yet have operational maturity for distributed system debugging
- The domain boundaries are not yet well understood (premature extraction creates distributed
  monoliths — the worst of both worlds)
- The deployment frequency and scale requirements do not justify the operational overhead
- The application is being modernized incrementally and the modular monolith is a defined waypoint,
  not a final state

The key criterion: a modular monolith with clean internal boundaries is faster to extract into
services later than a monolith with tangled internal dependencies. Applying 12-factor principles
to the module boundaries (explicit config, stateless modules, event stream logging) prepares the
application for future extraction even when the extraction itself is deferred.

---

## Section 3: 12-Factor as Migration Target

### 12-Factor Compliance as the Goal State for Extracted Services

When a subsystem is extracted from a monolith, the target architecture for the resulting service
is 12-factor compliance. This provides a concrete, verifiable goal for each extraction cycle rather
than a vague "make it cloud-native" instruction.

Each extraction involves applying specific factors:

- **Factor I (Codebase)**: The extracted service gets its own repository (or well-defined monorepo
  module). The monolith no longer contains the extracted functionality.
- **Factor II (Dependencies)**: The service's dependencies are declared explicitly and isolated from
  the monolith's dependency tree.
- **Factor III (Config)**: All environment-specific values are externalised. Config that was
  previously hardcoded in the monolith or shared via a configuration file is moved to environment
  variables or a secrets manager.
- **Factor V (Build/Release/Run)**: The service has its own CI/CD pipeline, producing independent
  build artifacts and release deployments. It no longer deploys as part of the monolith's release.
- **Factor IX (Disposability)**: The service starts and shuts down cleanly. Graceful shutdown is
  implemented from the first extraction, not added later.

### Which Factors Matter Most During Migration

Three factors have disproportionate impact on migration success:

**Factor III (Config)**: Configuration externalisation is the most common blocker. Monolithic
applications often embed environment-specific values in code, property files, or shared
infrastructure. Extracting config as a distinct step before extracting the service boundary reduces
migration complexity significantly. When config is externalised in the monolith, the service
extraction is a structural operation; when it is not, each extraction requires concurrent
configuration and structural work.

**Factor V (Build/Release/Run)**: Independent build pipelines are the operational prerequisite for
independent deployment. Until a service has its own pipeline, it cannot be deployed independently
of the monolith, which means the extraction provides no deployment velocity benefit. Establishing
the pipeline as part of the extraction cycle — not after — is the correct sequencing.

**Factor IX (Disposability)**: Monolithic applications often have poor shutdown behaviour (threads
that don't terminate cleanly, in-flight requests that aren't drained, locks not released). When
a service is extracted, it enters a container orchestrator environment where it will be started,
stopped, and replaced frequently. Services that do not handle SIGTERM correctly will cause disruption
in production. Implementing graceful shutdown during extraction avoids operational problems that
are harder to debug after the fact.
