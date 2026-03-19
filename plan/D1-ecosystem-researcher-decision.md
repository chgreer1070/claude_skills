# D1 Decision: ecosystem-researcher-v1.1-rt-ica.md

**Task**: T1 — Ecosystem-researcher v1.1 Decision Gate
**Date**: 2026-03-19

---

## Decision: Option B

Delete `ecosystem-researcher-v1.1-rt-ica.md` as-is. No capability is lost.

---

## Rationale

The dh canonical version (`plugins/development-harness/agents/ecosystem-researcher.md`) explicitly
BLOCKs when no MCP research server is available — this is a deliberate design constraint, not an
omission. Adding `WebSearch`/`WebFetch` as fallback tools (Option A) would undermine that constraint
by allowing unverified research to proceed when authoritative sources are unavailable, which the dh
version's `<mcp_availability_check>` block explicitly prohibits. The v1.1 file is Python-project
framed but provides no functionality that the dh version does not cover when MCP servers are present;
its direct-web fallback is the anti-pattern that the dh design intentionally excludes. Retaining v1.1
as a renamed `python-ecosystem-researcher.md` (Option C) would preserve the anti-pattern in the
codebase under a different name, creating ongoing confusion about which agent to use.

---

## Grep Result (Zero References — Safe to Delete)

Command run:

```bash
grep -r "ecosystem-researcher-v1.1" plugins/ .claude/rules/ --include="*.md"
```

Result: **No matches found** in either `plugins/` or `.claude/rules/`.

The v1.1 file has no live references anywhere in the repository. Deletion has zero reference-update
impact.

---

## T2 Instruction

**Delete `ecosystem-researcher-v1.1-rt-ica.md`** alongside the 10 shared agents.

Exact command for T2:

```bash
git rm plugins/python3-development/agents/ecosystem-researcher-v1.1-rt-ica.md
```

This is a straight deletion — no dh-agent edit sub-step is required before deleting v1.1
(Option A sub-step is NOT needed).

Total deletion count for T2: **11 files** (10 shared agents + v1.1).

---

## T2 Requires dh-edit Sub-Step?

**No.** Option B requires no changes to `plugins/development-harness/agents/ecosystem-researcher.md`
before deletion. T2 proceeds directly to `git rm` for all 11 files.
