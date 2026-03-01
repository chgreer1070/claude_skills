---
name: Add UX Impact Assessment to SAM task template, grooming, and completion gates
description: "The SAM pipeline (task template, grooming, verification, completion) evaluates technical correctness but never evaluates experiential quality. Every gate checks 'does it work?' but none check 'would a human be satisfied using this?' This was exposed by critique of backlog issues #311/#312 where implementations were functionally correct but had 9 UX problems: abort-only flow (no interactive confirmation), magic numbers without tuning levers, lexical-only duplicate detection, fragile API search method, code duplication, ambiguous exit codes, no dry-run mode, missing context in output (issue number vs filename), and repeat penalty on override.\n\nChanges needed across 6 files:\n1. TASK_FILE_FORMAT.md — Add 'User Interaction Contract' section between Requirements and Acceptance Criteria (who uses this, interaction walkthrough for happy/blocked/error paths, override design with cost evaluation, output contract)\n2. groom-backlog-item/SKILL.md — Add Step 5.5 'User Journey Validation' after RT-ICA (discovery, trigger, friction audit, dead-end check, persona split for human vs agent consumers)\n3. TASK_FILE_FORMAT.md — Split Acceptance Criteria into Technical and Experiential subsections (experiential: actionable output, override cost, distinguishable exit codes, machine-parseable mode)\n4. complete-implementation/SKILL.md — Add Phase 2.5 'UX Walkthrough' between feature-verifier and integration-checker (execute interaction scenarios, evaluate actionability, override cost, follow-up task creation)\n5. verify/SKILL.md — Add Section 2b 'USABLE Check' after WORKS check (actionable output, sufficient context, proportional override, distinguishable failures, no repeat penalty)\n6. feature-verifier.md agent — Add 'Experiential Truths' to Step 2 (resolution time when blocked, direct links in output, no information re-provision on override, decision-ready output without follow-up commands)"
metadata:
  topic: add-ux-impact-assessment-to-sam-task-template-grooming-and-c
  source: 'Post-implementation critique of backlog #311 (fuzzy duplicate detection) and #312 (open PR check) — session observation 2026-03-01'
  added: '2026-03-01'
  priority: P1
  type: Feature
  status: open
  issue: '#314'
  last_synced: '2026-03-01T00:07:34Z'
---

**Research first**: How do other agent frameworks (GSD, BMAD-METHOD) evaluate UX quality in automated workflows? What heuristics exist for 'interaction cost' measurement in CLI tools?