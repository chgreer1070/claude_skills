---
title: Architecture Spec — Research Freshness Delta Indicator
feature: research-freshness-delta
issue: "#444"
generated: 2026-03-06
scope: 3 documentation files, no Python code changes
---

# Architecture Spec: Research Freshness Delta Indicator

## Executive Summary

Three documentation files change. No Python scripts, no agent files, no new flags. The changes
convert freshness dates from stop conditions into informational delta output. Batch Mode in
`/research-curator` auto-reruns duplicate URLs instead of skipping them. The inventory table in
`/refresh-research` gains a "Days Old" column. Fresh entries skipped by `--stale` are enumerated
in the summary report. The entry template gains two clarifying notes about the semantics of
"Next Review Recommended" and the 3-month schedule baseline.

---

## 1. Summary of Changes

<!-- PENDING: summary-of-changes -->

---

## 2. File 1 — `.claude/skills/research-curator/SKILL.md`

<!-- PENDING: file1-spec -->

---

## 3. File 2 — `.claude/skills/refresh-research/SKILL.md`

<!-- PENDING: file2-spec -->

---

## 4. File 3 — `.claude/skills/research-curator/references/entry-template.md`

<!-- PENDING: file3-spec -->

---

## 5. Delta Computation

<!-- PENDING: delta-computation -->

---

## 6. Output Format Spec

<!-- PENDING: output-format-spec -->

---

## 7. Edge Cases

<!-- PENDING: edge-cases -->

---

## 8. What Does NOT Change

<!-- PENDING: what-does-not-change -->
