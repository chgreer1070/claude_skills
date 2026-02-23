## Story

As a **developer**, I want **the ARL human-probing skill/agent implemented** so that **agents can probe humans at ARL touchpoints when blocking on ambiguity or verification failure**.

## Description

Design exists in `arl-human-probing-design.md`; implementation is missing. Build the skill/agent that probes humans at ARL touchpoints (e.g., when agent blocks on ambiguity, when verification fails). Success: agent can invoke human-probing flow per design; groom-backlog-item integration works.

## Acceptance Criteria

- [ ] Skill/agent invokes human-probing flow per arl-human-probing-design.md
- [ ] groom-backlog-item integration works
- [ ] Design patterns (async feedback queue, AI user reps, question-to-action) implemented

## Context

- **Source**: Session observation — SDLC layer implementation (2026-02-23)
- **Priority**: P1
- **Added**: 2026-02-23
- **Research questions**: None
- **Suggested location**: New skill under `.claude/skills/` or `plugins/`; design at `.claude/docs/sdlc-layers/arl-meta-layer/arl-human-probing-design.md`
