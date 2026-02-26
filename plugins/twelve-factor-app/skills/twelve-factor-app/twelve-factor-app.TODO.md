# Twelve Factor App — Research TODO

## Research Categories

- [ ] **Codebase and Dependencies**: Factors I and II — one codebase in version control with many deploys; explicit dependency declaration and isolation; no reliance on system-wide packages; dependency manifests and isolation tools
- [ ] **Configuration and Backing Services**: Factors III and IV — storing config in environment variables (not in code); backing services as attached resources accessed via URL or credentials from config; swappability of local vs. third-party services without code changes
- [ ] **Build, Release, Run**: Factor V — strict separation of build, release, and run stages; immutable releases with unique IDs; rollback capability; separation of code transforms from runtime execution
- [ ] **Processes and Port Binding**: Factors VI and VII — stateless share-nothing processes; no sticky sessions; filesystem as transient cache only; exporting services via port binding rather than relying on injected runtime servers
- [ ] **Concurrency and Disposability**: Factors VIII and IX — scale-out via the process model; process types and the process formation; fast startup and graceful shutdown; robustness against sudden death; SIGTERM handling
- [ ] **Dev/Prod Parity and Logs**: Factors X and XI — minimizing time, personnel, and tools gaps between environments; continuous deployment; backing service consistency across environments; logs as event streams to stdout; log routing and archival handled by execution environment
- [ ] **Admin Processes**: Factor XII — running admin or management tasks as one-off processes; same environment and codebase as regular processes; REPL-based interaction; avoiding one-off scripts not under version control
- [ ] **Methodology Overview and Context**: Introduction, background, and design philosophy — who the methodology is for; the SaaS deployment model; portability, resilience, and scalability goals; historical context from Heroku; relationship to patterns of enterprise application architecture
