# Background and Historical Context

SOURCE: <https://www.12factor.net/> (accessed 2026-02-26)

## Origins

The twelve-factor methodology was developed by contributors at **Heroku** who had been directly involved in:

- Development and deployment of hundreds of apps
- Witnessing the development, operation, and scaling of hundreds of thousands of apps via the Heroku platform

The document synthesizes experience and observations on a wide variety of SaaS apps, triangulating ideal practices for app development.

## Motivation

To raise awareness of systemic problems in modern application development and provide a shared vocabulary for discussing those problems.

## Problems the Methodology Addresses

Three dynamics the methodology pays particular attention to:

1. Organic growth of an app over time
2. Dynamics of collaboration between developers working on the app's codebase
3. Avoiding the cost of software erosion

## 2025 Governance and Evolution

In November 2024, Heroku open-sourced the methodology at [github.com/heroku/12factor](https://github.com/heroku/12factor), establishing community governance to modernize the original principles.

The maintainers are pursuing a two-phase approach:

1. **Concept/example separation** (Issue #13) — separating timeless principles from implementation examples that have become outdated (e.g., Capistrano, foreman). This enables updating examples without changing the underlying factor.

2. **Substantive updates** — once separation is complete, addressing Kubernetes, containers, GitOps, and security patterns that weren't anticipated in the original 2011 methodology.

The key conceptual development is the "narrow conduit" framing — 12-factor defines the interface between application developers and the platform. That interface has evolved:

- 2011: Source code handed to an operations team
- 2015: Container images pushed to a registry
- 2025: Developers write Kubernetes/Helm templates directly

12-factor guidance must account for how this boundary is drawn differently across these eras.

SOURCE: <https://12factor.net/blog/narrow-conduits> (accessed 2026-02-26)
SOURCE: <https://12factor.net/blog/open-source-announcement> (accessed 2026-02-26)
SOURCE: <https://12factor.net/blog/evolving-twelve-factor> (accessed 2026-02-26)
