# Factor X — Dev/Prod Parity

**Principle**: Keep development, staging, and production as similar as possible.

SOURCE: <https://www.12factor.net/dev-prod-parity> (accessed 2026-02-26)

## The Three Gaps

Historically, there have been substantial gaps between development and production across three areas:

| Gap | Traditional App | Twelve-Factor App |
|-----|----------------|-------------------|
| Time gap | Weeks between dev and deploy | Hours (deploy code written hours or minutes ago) |
| Personnel gap | Developers write code, ops engineers deploy it | Developers who wrote code are closely involved in deploying and watching its behavior |
| Tools gap | Different stacks (Nginx/SQLite/macOS in dev, Apache/MySQL/Linux in prod) | Development and production as similar as possible |

## Core Rule

The twelve-factor app is designed for **continuous deployment** by keeping the gap between development and production small.

## Backing Services: A Critical Parity Area

Backing services are where dev/prod divergence most commonly occurs. Many languages offer libraries with adapters for different service types:

| Type | Language | Library | Adapters |
|------|----------|---------|---------|
| Database | Ruby/Rails | ActiveRecord | MySQL, PostgreSQL, SQLite |
| Queue | Python | Celery | RabbitMQ, Beanstalkd, Redis |
| Cache | Ruby/Rails | ActiveSupport::CacheStore | Memory, filesystem, Memcached |

The developer resisting backing service parity often claims lightweight local adapters (SQLite in dev vs. PostgreSQL in prod) are sufficient. This is a mistake — subtle incompatibilities surface at deploy time and cause outages.

**Twelve-factor strongly favors using the same type and version of backing service between development and production.**

## Implementation

Modern tooling makes parity straightforward:

- **Docker Compose** runs a complete local environment using the same container images as production
- **Vagrant** / VMs run local environments that closely mimic production
- Package managers (Homebrew, apt) make it easy to install backing services locally

The resistance ("it's inconvenient to use PostgreSQL locally") is minimal compared to the cost of prod-only bugs discovered post-deploy.

SOURCE: <https://www.12factor.net/dev-prod-parity> (accessed 2026-02-26)

## Modern Reinterpretation (2025)

- **Container images solve the "same backing service types" problem**: A Postgres container in dev is
  identical to Postgres in prod. The original friction of "use SQLite locally, Postgres in prod" has
  been eliminated for teams using containers.
- **Kubernetes parity gap**: Full cluster feature parity (networking policies, service mesh, resource
  constraints, observability tooling) is harder to achieve locally. Tools like k3d, minikube, and
  Kind bring Kubernetes locally but not all cluster features replicate faithfully.
- **GitOps closes the config gap**: When infrastructure is declared in Git and applied by ArgoCD/Flux,
  the same manifests deploy to dev, staging, and prod — minimizing config drift between environments.
- **The personnel gap remains real**: CI/CD still runs unattended; developers must still test on
  production-like environments to catch issues that arise only at scale or with full cluster
  networking.
- Containers have improved Factor X compliance significantly compared to the 2011 baseline, but full
  parity requires explicit effort — particularly for networking and observability tooling.

SOURCE: <https://12factor.net/blog/evolving-twelve-factor> (accessed 2026-02-26)
SOURCE: <https://12factor.net/dev-prod-parity> (accessed 2026-02-26)
