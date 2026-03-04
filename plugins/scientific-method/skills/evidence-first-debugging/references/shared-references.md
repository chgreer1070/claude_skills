# Evidence-First Debugging — Shared References

The three shared files below are loaded at the start of every investigation. This index
exists for progressive disclosure — a quick map before loading the full content.

## Investigation Template

[Unified Investigation Template](../../../shared/investigation-template.md)

The 15-section output structure (sections 0–14) used for all investigation output.
Load this first. All output must conform to this structure.

## Evidence Rules

[Evidence Rules](../../../shared/evidence-rules.md)

Evidence ID format (`[E1]`, `[E2]`, …), truncation disclosure requirements, and the
list of forbidden phrases that signal unsupported inference.

## Causality Gate

[Causality Gate](../../../shared/causality-check.md)

Classification rules for every action-result link in section 10. Valid classifications:
`causal-supported`, `correlated-only`, `unrelated`, `unknown`.

## Domain Extensions

Load the applicable extension when the investigation type matches. Extensions insert
additional sections immediately after section 2 (OBSERVATIONS).

- [Debugging Extensions](../../../shared/extensions/debugging-extensions.md) — for software bugs and crashes
- [Performance Extensions](../../../shared/extensions/performance-extensions.md) — for latency, throughput, or memory regressions
