# Introduction — Goals and Design Philosophy

The Twelve-Factor App is a methodology for building software-as-a-service (SaaS) applications.

SOURCE: <https://www.12factor.net/> (accessed 2026-02-26)

## Goals

A twelve-factor app:

- Uses **declarative** formats for setup automation, minimizing onboarding time and cost for new developers
- Has a **clean contract** with the underlying OS, offering maximum portability between execution environments
- Is suitable for **deployment on modern cloud platforms**, eliminating the need for server and systems administration
- **Minimizes divergence** between development and production, enabling continuous deployment for maximum agility
- Can **scale up** without significant changes to tooling, architecture, or development practices

## Applicability

The methodology applies to apps written in **any programming language** using **any combination of backing services** (databases, queues, memory caches, etc.).

## Design Philosophy

The format is inspired by Martin Fowler's books *Patterns of Enterprise Application Architecture* and *Refactoring*.

The methodology provides:

- A shared vocabulary for systemic problems in modern application development
- Broad conceptual solutions with accompanying terminology
- A triangulation on ideal practices paying attention to organic app growth over time and developer collaboration dynamics

## Target Audience

- Developers building applications that run as a service
- Ops engineers who deploy or manage such applications

SOURCE: <https://www.12factor.net/> (accessed 2026-02-26)

## 2025 Update

In November 2024, Heroku open-sourced the methodology to community governance at [github.com/heroku/12factor](https://github.com/heroku/12factor). Active modernization is underway to address the cloud-native landscape that has emerged since 2011.

The goals of a twelve-factor app remain unchanged. The implementation guidance is being updated for:

- Container-native deployment (Docker images as the build artifact)
- Kubernetes as the target platform (replacing generic "cloud platform")
- GitOps workflows (replacing Capistrano-era deployment tools)
- Explicit security, observability, and API design requirements

SOURCE: <https://12factor.net/blog/evolving-twelve-factor> (accessed 2026-02-26)
