# ARL Human-Probing Flow — Design

**Status:** Design (to be implemented)
**Purpose:** Capture invisible knowledge from the human when ARL identifies gaps. Add answers to local domain knowledge with staleness tracking.

---

## Triggers

| Trigger | Source | When |
|---------|--------|------|
| **User Frustration** | transcript-analysis Dimension 3 | "No,", "Don't", "Why did you" in transcripts |
| **Missing Hooks** | transcript-analysis Dimension 9 | Recurring manual corrections |
| **RT-ICA BLOCKED** | groom-backlog-item | Prerequisites MISSING |
| **Post-kaizen** | agentskill-kaizen | Deviations/hallucinations identified |
| **Grooming** | groom-backlog-item | Context manifest suggests invisible knowledge |

---

## Probe Design

**Question types:**
- Multi-choice with open-ended opportunities
- "What went wrong in the past?"
- "What do you think are essential documents or references?"
- "What could go wrong?" (risk elicitation)

**ARL Layer 2 Execution Model concepts:**
- Async feedback queue (non-blocking)
- AI user representatives
- Question-to-action-item conversion

---

## Project-Local Domain Knowledge Format

**Location:** `.claude/domain-knowledge/` (or `research/` with project scope)

**Structure:**
```yaml
---
topic: {kebab-case-topic}
source: human-probe | kaizen | grooming
verified: "YYYY-MM-DD"
next_review: "YYYY-MM-DD"
---

# {Topic}

{Content from human response}
```

**Staleness tracking:** Same as research entries — `verified`, `next_review`. Re-probe or refresh when `next_review < today`.

---

## Integration Points

| Integration | Flow |
|-------------|------|
| **groom-backlog-item** | Context manifest can include "suggested invisible knowledge prompts" — questions to ask human before planning |
| **work-backlog-item** | When RT-ICA blocks, offer probe questions; add answers to domain knowledge |
| **post-kaizen** | After agentskill-kaizen run, if deviations map to R1-R10, generate probe questions |
| **backlog-item-groomer** | Context manifest field: `invisible_knowledge_prompts: [question1, question2]` |

---

## Open Questions

1. **When does ARL probe?** After every kaizen run, on grooming, when RT-ICA blocks, when specific failure category detected, or on-demand?
2. **Project-local vs research/:** Where should human-probed knowledge live — `.claude/domain-knowledge/`, `research/` with project scope, or task/plan artifacts?
