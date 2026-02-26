# Factor III — Config

**Principle**: Store config in the environment.

SOURCE: <https://www.12factor.net/config> (accessed 2026-02-26)

## What Is Config?

Config is everything that is **likely to vary between deploys** (staging, production, developer environments). Includes:

- Per-deploy values such as the canonical hostname for the deploy
- Credentials to external services such as Amazon S3 or Twitter
- Resource handles to the database, Memcached, and other backing services

Config does **not** include internal application config such as `config/routes.rb` in Rails or how code modules are connected in Spring — this type does not vary between deploys and belongs in the code.

## Core Rule

**Store config in environment variables (env vars).**

Litmus test: could the codebase be made open source at any moment, without compromising any credentials? If yes, config is correctly factored out.

## Why Not Config Files?

| Approach | Problem |
|----------|---------|
| Constants in code | Violates twelve-factor; requires code change per deploy |
| Config files not in version control (e.g., `config/database.yml`) | Easy to accidentally commit; scattered formats; language/framework-specific |
| Env vars | Easy to change between deploys without changing code; no risk of accidental commit |

## Advantages of Env Vars

- Easy to change between deploys without changing any code
- Little chance of being checked into the code repo accidentally
- Language/framework-agnostic standard

## Anti-Pattern: Config Grouping

Some apps batch env vars into named groups (environments like "development", "test", "production"). This is a violation because it does not scale cleanly — as more deploys are added, new environment names are needed, creating management complexity.

Twelve-factor requires config to be **orthogonal** across deploys — each deploy manages its own complete set of env vars.

SOURCE: <https://www.12factor.net/config> (accessed 2026-02-26)

## Modern Reinterpretation (2025)

- **Env vars → Kubernetes ConfigMaps and Secrets**: Environment variables remain the delivery
  mechanism, but the source is now Kubernetes ConfigMaps/Secrets rather than shell `.env` files or
  platform config UIs.
- **Secrets management**: The env var model has been extended with dedicated secrets management
  (Vault, AWS Secrets Manager, SOPS/Sealed Secrets for GitOps). Secrets are still injected as env
  vars at runtime but the source is a secrets store, not a human-set env var.
- **Supply chain security**: Kubernetes 1.28+ supports workload identity and SPIFFE/SPIRE for
  service-to-service auth — config now includes cryptographic identity, not just key-value env vars.
- **External Secrets Operator (ESO)**: Bridges secrets management systems with Kubernetes Secrets
  objects, maintaining the "config comes from the environment" principle while adding secret rotation.
- The core principle (no config in code, config varies by deploy) remains unchanged and is now better
  enforced by the platform — Kubernetes enforces that Pods cannot access Secrets they are not
  explicitly granted.

SOURCE: <https://12factor.net/blog/evolving-twelve-factor> (accessed 2026-02-26)
SOURCE: <https://12factor.net/config> (accessed 2026-02-26)
