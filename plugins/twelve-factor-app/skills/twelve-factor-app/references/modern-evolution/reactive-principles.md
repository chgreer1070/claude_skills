# Reactive Principles — Parallel Framework for Distributed Systems

Documents the eight Reactive Principles published by the Reactive Foundation, their descriptions,
and their relationship to Twelve-Factor as a complementary framework addressing what 12-factor
assumes but does not specify.

---

## Overview

The Reactive Principles are a set of design principles for cloud-native applications published by
the Reactive Foundation. They address distributed systems concerns from a different angle than
Twelve-Factor: where 12-factor focuses on application structure and operational practices, the
Reactive Principles focus on behaviour under failure and uncertainty.

The two frameworks are not in competition. An application can comply with all twelve (or fifteen)
factors and still fail to handle distributed system realities that the Reactive Principles address.

SOURCE: [The Reactive Principles: Design Principles for Cloud Native Applications](https://www.reactiveprinciples.org/cloud-native/index.html) (accessed 2026-02-26)

---

## The Eight Reactive Principles

SOURCE: [The Reactive Principles](https://www.reactiveprinciples.org/principles/) (accessed 2026-02-26)

### 1. Stay Responsive

Systems must provide timely responses even under failure or load. Responsiveness is the cornerstone
of usability and utility — if a system does not respond in a timely manner, it is effectively
unavailable for the operation in question. This principle drives timeout management, circuit
breakers, and degraded-mode responses.

### 2. Accept Uncertainty

Distributed systems must handle network partitions and unreliable communication. The network is not
reliable; message delivery is not guaranteed; remote services may be unavailable. Applications must
design around uncertainty as the baseline condition rather than treating it as an exceptional case.
This drives patterns like idempotency, at-least-once delivery handling, and explicit failure modes.

### 3. Embrace Failure

Assume components will fail and design for recovery rather than prevention. Failure is not an
exceptional state in a distributed system — it is a routine operational event. Applications must
detect failures, contain their blast radius, and recover without human intervention. This principle
drives bulkhead patterns, fallback strategies, and health-check-driven restart policies.

### 4. Assert Autonomy

Components should be independent and self-contained. Autonomous components can evolve independently,
fail independently, and scale independently. This principle drives service boundary design — each
component should own its data, its business logic, and its failure domain without depending on
shared mutable state with other components.

### 5. Tailor Consistency

Different consistency models may be appropriate for different parts of the system. Strong
consistency has a cost in availability and latency; eventual consistency reduces that cost at the
price of accepting temporary divergence. Applications should choose the consistency model that
matches the business requirement for each operation rather than applying a single model uniformly
across all data.

### 6. Decouple Time

Asynchronous communication decouples temporal dependencies between services. Synchronous
request/response coupling means a caller must wait for a responder; if the responder is slow or
unavailable, the caller is blocked. Decoupling time through asynchronous messaging, event streams,
and reactive patterns allows services to operate at their own pace. This principle drives message
queue adoption, event-driven architectures, and back-pressure handling.

### 7. Decouple Space

Location-transparent communication enables flexible deployment and evolution. Services should not
depend on knowing the physical or network location of their dependencies. Location transparency
enables services to be relocated, replicated, or replaced without changing callers. This principle
drives service discovery, load balancing, and service mesh adoption.

### 8. Handle Dynamics

Systems must adapt to changing resources and load. Static resource allocation leads to either waste
(over-provisioning) or failure (under-provisioning). Reactive systems respond to load signals by
scaling out, shedding load gracefully, or adjusting processing rates. This principle drives
autoscaling, backpressure propagation, and adaptive concurrency controls.

---

## Relationship to Twelve-Factor

### What 12-Factor Assumes but Does Not Specify

The Twelve-Factor methodology establishes structural and operational practices (codebase, config,
processes, port binding, concurrency, disposability) that create a foundation for cloud deployment.
It does not address how the application behaves at runtime when distributed system conditions arise.

Specifically, 12-factor:

- Requires stateless processes (Factor VI) but does not specify how to handle state that must
  exist across requests (sessions, caches, coordination).
- Requires disposability and fast startup/shutdown (Factor IX) but does not specify how to handle
  in-flight requests during shutdown, or how to handle requests to a restarting instance.
- Requires logs as event streams (Factor XI) but does not specify what observability signals are
  needed to detect the failure conditions the Reactive Principles address.
- Does not address service-to-service communication failures, partial availability, or network
  partition handling at all.

### How the Frameworks Complement Each Other

A team applying both frameworks would use 12-factor to structure the application (what an app is
and how it deploys) and the Reactive Principles to govern runtime behaviour (how an app responds
to conditions it encounters in production).

- **12-factor Factor VI (Processes) + Reactive Principle 4 (Assert Autonomy)**: Stateless
  processes are a prerequisite for autonomous, independently scalable components.
- **12-factor Factor IX (Disposability) + Reactive Principle 3 (Embrace Failure)**: Graceful
  shutdown is the application-level expression of the broader principle that failure is routine.
- **12-factor Factor XI (Logs as Event Streams) + Reactive Principles 1 & 8 (Stay Responsive,
  Handle Dynamics)**: Structured logs and metrics are the observability foundation that enables
  detecting and responding to the conditions these principles address.
- **12-factor Factor IV (Backing Services) + Reactive Principle 2 (Accept Uncertainty)**: Treating
  backing services as attached resources is correct structural separation, but the application still
  needs to handle uncertainty in those service connections at runtime.

SOURCE: [The Reactive Principles: Cloud Native Applications](https://www.reactiveprinciples.org/cloud-native/index.html) (accessed 2026-02-26)
