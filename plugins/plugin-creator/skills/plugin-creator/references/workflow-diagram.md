# Plugin Creator Workflow Diagram

This diagram shows the complete agentic workflow for creating Claude Code plugins.

---

## High-Level Flow

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                        PLUGIN CREATION WORKFLOW                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐             │
│   │ Phase 0  │───▶│ Phase 1  │───▶│ Phase 2  │───▶│ Phase 3  │             │
│   │ RT-ICA   │    │ Research │    │  Design  │    │  Impl    │             │
│   └──────────┘    └──────────┘    └──────────┘    └──────────┘             │
│        │               │               │               │                    │
│        ▼               ▼               ▼               ▼                    │
│   BLOCKED or     Explore Agent   Plan Agent     Scripts or                 │
│   APPROVED       WebFetch        Architecture   Manual                      │
│                                                                              │
│   ┌──────────┐    ┌──────────┐    ┌──────────┐                             │
│   │ Phase 4  │───▶│ Phase 5  │───▶│ Phase 6  │                             │
│   │ Validate │    │   Docs   │    │  Final   │                             │
│   └──────────┘    └──────────┘    └──────────┘                             │
│        │               │               │                                    │
│        ▼               ▼               ▼                                    │
│   Validation      plugin-docs-    verify Skill                             │
│   Scripts +       writer Agent    COMPLETE or                              │
│   plugin-assessor                 NOT COMPLETE                              │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Detailed Phase Breakdown

### Phase 0: RT-ICA Prerequisite Check

```text
┌─────────────────────────────────────────────────────────────────┐
│                    PHASE 0: RT-ICA CHECK                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   User Request                                                   │
│        │                                                         │
│        ▼                                                         │
│   ┌─────────────────┐                                           │
│   │ Invoke rt-ica   │                                           │
│   │ Skill           │                                           │
│   └────────┬────────┘                                           │
│            │                                                     │
│            ▼                                                     │
│   ┌─────────────────┐     ┌─────────────────┐                   │
│   │ Prerequisites   │─NO─▶│    BLOCKED      │                   │
│   │ Complete?       │     │ Request missing │                   │
│   └────────┬────────┘     │ information     │                   │
│            │YES           └─────────────────┘                   │
│            ▼                                                     │
│   ┌─────────────────┐                                           │
│   │    APPROVED     │                                           │
│   │ Continue to     │                                           │
│   │ Phase 1         │                                           │
│   └─────────────────┘                                           │
│                                                                  │
│   Prerequisites checked:                                         │
│   • Purpose clarity                                              │
│   • Target users                                                 │
│   • Component selection                                          │
│   • Existing solutions                                           │
│   • Source material                                              │
│   • Verification method                                          │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Phase 1: Research

```text
┌─────────────────────────────────────────────────────────────────┐
│                    PHASE 1: RESEARCH                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │                 PARALLEL RESEARCH TASKS                  │   │
│   └─────────────────────────────────────────────────────────┘   │
│                           │                                      │
│          ┌────────────────┼────────────────┐                    │
│          ▼                ▼                ▼                    │
│   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│   │ Task 1a:    │  │ Task 1b:    │  │ Task 1c:    │            │
│   │ Check       │  │ Gather      │  │ Fetch       │            │
│   │ Existing    │  │ Domain      │  │ Official    │            │
│   │ Solutions   │  │ Knowledge   │  │ Docs        │            │
│   └──────┬──────┘  └──────┬──────┘  └──────┬──────┘            │
│          │                │                │                    │
│          ▼                ▼                ▼                    │
│   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│   │  Explore    │  │  Explore    │  │ general-    │            │
│   │  Agent      │  │  Agent      │  │ purpose     │            │
│   └─────────────┘  └─────────────┘  └─────────────┘            │
│          │                │                │                    │
│          │                │                │                    │
│          └────────────────┼────────────────┘                    │
│                           ▼                                      │
│                  ┌─────────────────┐                            │
│                  │ Research Report │                            │
│                  │ • Similar plugins│                           │
│                  │ • Domain sources │                           │
│                  │ • Official schema│                           │
│                  └─────────────────┘                            │
│                                                                  │
│   Key Outputs:                                                   │
│   • Existing solutions with paths/URLs                          │
│   • Authoritative sources with access dates                     │
│   • Official schema fields verified                             │
│   • Discrepancies flagged                                       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Phase 2: Design

```text
┌─────────────────────────────────────────────────────────────────┐
│                    PHASE 2: DESIGN                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   Research Report                                                │
│        │                                                         │
│        ▼                                                         │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │              DESIGN TASKS (SEQUENTIAL)                   │   │
│   └─────────────────────────────────────────────────────────┘   │
│        │                                                         │
│        ▼                                                         │
│   ┌─────────────────┐                                           │
│   │ Task 2a:        │                                           │
│   │ Architecture    │◀──── Plan Agent                           │
│   │ Planning        │                                           │
│   └────────┬────────┘                                           │
│            │                                                     │
│            ▼                                                     │
│   ┌─────────────────┐                                           │
│   │ Architecture    │                                           │
│   │ • ASCII diagram │                                           │
│   │ • Component list│                                           │
│   │ • File tree     │                                           │
│   │ • Dependencies  │                                           │
│   └────────┬────────┘                                           │
│            │                                                     │
│            ▼                                                     │
│   ┌─────────────────┐                                           │
│   │ Task 2b:        │                                           │
│   │ Skill Content   │◀──── Plan Agent (per skill)               │
│   │ Planning        │                                           │
│   └────────┬────────┘                                           │
│            │                                                     │
│            ▼                                                     │
│   ┌─────────────────┐                                           │
│   │ Content Outlines│                                           │
│   │ • SKILL.md      │                                           │
│   │ • Reference list│                                           │
│   │ • Frontmatter   │                                           │
│   └─────────────────┘                                           │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Phase 3: Implementation

```text
┌─────────────────────────────────────────────────────────────────┐
│                   PHASE 3: IMPLEMENTATION                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   Design Documents                                               │
│        │                                                         │
│        ▼                                                         │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │            IMPLEMENTATION OPTIONS                        │   │
│   └─────────────────────────────────────────────────────────┘   │
│        │                           │                             │
│        ▼                           ▼                             │
│   ┌─────────────┐           ┌─────────────┐                     │
│   │  Option A   │           │  Option B   │                     │
│   │ Scaffolding │           │   Manual    │                     │
│   │   Script    │           │  Creation   │                     │
│   └──────┬──────┘           └──────┬──────┘                     │
│          │                         │                             │
│          ▼                         ▼                             │
│   ┌─────────────┐           ┌─────────────┐                     │
│   │ uv run      │           │ Create dirs │                     │
│   │ create_     │           │ Write files │                     │
│   │ plugin.py   │           │ manually    │                     │
│   └──────┬──────┘           └──────┬──────┘                     │
│          │                         │                             │
│          └──────────┬──────────────┘                            │
│                     ▼                                            │
│            ┌─────────────────┐                                  │
│            │ Plugin Created  │                                  │
│            │ .claude-plugin/ │                                  │
│            │ skills/         │                                  │
│            │ agents/         │                                  │
│            │ hooks/          │                                  │
│            └─────────────────┘                                  │
│                                                                  │
│   Consider Advanced Features:                                    │
│   • Dynamic context injection (!`command`)                      │
│   • Subagent execution (context: fork)                          │
│   • Visual output (bundled scripts)                             │
│   • Hook automation                                              │
│   • MCP/LSP integration                                          │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Phase 4: Validation

```text
┌─────────────────────────────────────────────────────────────────┐
│                    PHASE 4: VALIDATION                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   Created Plugin                                                 │
│        │                                                         │
│        ▼                                                         │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │              VALIDATION TASKS (PARALLEL)                 │   │
│   └─────────────────────────────────────────────────────────┘   │
│        │                           │                             │
│        ▼                           ▼                             │
│   ┌─────────────┐           ┌─────────────┐                     │
│   │ Task 4a:    │           │ Task 4b:    │                     │
│   │ Automated   │           │ Verify vs   │                     │
│   │ Validation  │           │ Official    │                     │
│   │ Scripts     │           │ Docs        │                     │
│   └──────┬──────┘           └──────┬──────┘                     │
│          │                         │                             │
│          ▼                         ▼                             │
│   ┌─────────────┐           ┌─────────────┐                     │
│   │ create_     │           │ general-    │                     │
│   │ plugin.py   │           │ purpose     │                     │
│   │ validate    │           │ Agent       │                     │
│   │ +           │           │ + WebFetch  │                     │
│   │ validate_   │           └──────┬──────┘                     │
│   │ frontmatter │                  │                             │
│   └──────┬──────┘                  │                             │
│          │                         │                             │
│          └──────────┬──────────────┘                            │
│                     ▼                                            │
│            ┌─────────────────┐                                  │
│            │ Task 4c:        │                                  │
│            │ Quality         │◀──── plugin-assessor Agent       │
│            │ Assessment      │                                  │
│            └────────┬────────┘                                  │
│                     │                                            │
│                     ▼                                            │
│            ┌─────────────────┐                                  │
│            │ Validation      │                                  │
│            │ Report          │                                  │
│            │ • Schema OK?    │                                  │
│            │ • Frontmatter?  │                                  │
│            │ • Quality score │                                  │
│            └─────────────────┘                                  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Phase 5: Documentation

```text
┌─────────────────────────────────────────────────────────────────┐
│                   PHASE 5: DOCUMENTATION                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   Validated Plugin                                               │
│        │                                                         │
│        ▼                                                         │
│   ┌─────────────────┐                                           │
│   │ Delegate to     │                                           │
│   │ plugin-docs-    │                                           │
│   │ writer Agent    │                                           │
│   └────────┬────────┘                                           │
│            │                                                     │
│            ▼                                                     │
│   ┌─────────────────┐                                           │
│   │ Documentation   │                                           │
│   │ Generated:      │                                           │
│   │ • README.md     │                                           │
│   │ • docs/skills.md│                                           │
│   │ • Config guide  │                                           │
│   └─────────────────┘                                           │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Phase 6: Final Verification

```text
┌─────────────────────────────────────────────────────────────────┐
│                  PHASE 6: FINAL VERIFICATION                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   Documented Plugin                                              │
│        │                                                         │
│        ▼                                                         │
│   ┌─────────────────┐                                           │
│   │ Invoke verify   │                                           │
│   │ Skill           │                                           │
│   └────────┬────────┘                                           │
│            │                                                     │
│            ▼                                                     │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │              VERIFICATION CHECKLIST                      │   │
│   ├─────────────────────────────────────────────────────────┤   │
│   │ □ Works Check    - validation scripts passed            │   │
│   │ □ Quality Gates  - plugin-assessor no critical issues   │   │
│   │ □ Docs Check     - README.md exists and accurate        │   │
│   │ □ Honesty Check  - all claims cite sources              │   │
│   └─────────────────────────────────────────────────────────┘   │
│            │                                                     │
│            ▼                                                     │
│   ┌─────────────────┐     ┌─────────────────┐                   │
│   │  All Passed?    │─NO─▶│ NOT COMPLETE    │                   │
│   │                 │     │ Fix issues,     │                   │
│   └────────┬────────┘     │ return to       │                   │
│            │YES           │ relevant phase  │                   │
│            ▼              └─────────────────┘                   │
│   ┌─────────────────┐                                           │
│   │    COMPLETE     │                                           │
│   │ Plugin ready    │                                           │
│   │ for distribution│                                           │
│   └─────────────────┘                                           │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Agent Delegation Summary

```text
┌─────────────────────────────────────────────────────────────────┐
│                    AGENT DELEGATION MAP                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   Phase      Agent Type           Task                          │
│   ─────      ──────────           ────                          │
│                                                                  │
│   Research   Explore              Code discovery                │
│              Explore              Domain knowledge              │
│              general-purpose      Official docs fetch           │
│                                                                  │
│   Design     Plan                 Architecture planning         │
│              Plan                 Content structure             │
│                                                                  │
│   Validate   (scripts)            Schema validation             │
│              general-purpose      Docs verification             │
│              plugin-assessor      Quality assessment            │
│                                                                  │
│   Document   plugin-docs-writer   README generation             │
│                                                                  │
│                                                                  │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │         ORCHESTRATOR NEVER DOES DIRECTLY:               │   │
│   ├─────────────────────────────────────────────────────────┤   │
│   │ ✗ Read docs yourself (delegate to Explore)              │   │
│   │ ✗ Grep/search yourself (delegate to Explore)            │   │
│   │ ✗ Assume from training data (delegate WebFetch)         │   │
│   │ ✗ Manually check fields (run validation scripts)        │   │
│   │ ✗ Review your own work (delegate to plugin-assessor)    │   │
│   │ ✗ Write README yourself (delegate to plugin-docs-writer)│   │
│   └─────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Failure Recovery Paths

```text
┌─────────────────────────────────────────────────────────────────┐
│                   FAILURE RECOVERY PATHS                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   Phase 0 BLOCKED                                                │
│        │                                                         │
│        └──▶ Request missing info ──▶ Re-run RT-ICA              │
│                                                                  │
│   Phase 1 Incomplete Research                                    │
│        │                                                         │
│        └──▶ Spawn additional Explore agents                     │
│        └──▶ Fetch more official docs                            │
│                                                                  │
│   Phase 4 Validation Failures                                    │
│        │                                                         │
│        ├──▶ Schema errors ──▶ Fix plugin.json ──▶ Re-validate   │
│        ├──▶ Frontmatter ──▶ Fix SKILL.md ──▶ Re-validate        │
│        └──▶ Quality issues ──▶ Improve content ──▶ Re-assess    │
│                                                                  │
│   Phase 6 NOT COMPLETE                                           │
│        │                                                         │
│        └──▶ Identify failing check                              │
│        └──▶ Return to relevant phase                            │
│        └──▶ Fix and re-verify                                   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Source

This workflow diagram documents the agentic plugin creation process defined in [SKILL.md](../SKILL.md).
