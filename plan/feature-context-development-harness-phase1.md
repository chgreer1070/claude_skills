# Feature Context: Development Harness Phase 1 Completion

## Document Metadata

- **Generated**: 2026-03-18
- **Input Type**: existing_document
- **Source**: GitHub Issue #581 — Development Harness Architecture Refactor, Phase 1 remaining deliverables
- **Status**: DISCOVERY_COMPLETE

---

## Original Request

Complete Phase 1 of the Development Harness Architecture Refactor (GitHub Issue #581). Phase 1 has three remaining deliverables:

1. SDLC stage naming taxonomy document — ratify the 7 existing stage names against IEEE 12207 / ISO 15288 / SAFe terminology, define the `{domain}-{sdlc-stage}` naming convention
2. Verify the nestable `{domain}-{sdlc-stage}` naming convention is correctly applied across existing workflow skills and manifests
3. End-to-end PoC validation guide — document how to dispatch a generic stage agent with a Python task

---

## Core Intent Analysis

### WHO (Target Users)

- Plugin authors who create language manifests that compose with the development harness
- The development harness orchestrator (the generic stage agent and dispatch logic) that resolves stage names at runtime
- Future contributors who need to understand why stages are named as they are

### WHAT (Desired Outcome)

Three artifacts that close out Phase 1:

1. A **taxonomy document** that maps the 7 SAM pipeline stage names to recognized SDLC standards (IEEE 12207, ISO 15288, SAFe) and formally defines the `{domain}-{sdlc-stage}` naming convention
2. A **naming audit result** confirming the convention is consistently applied (or listing corrections needed) across workflow skill directories and language manifest `stage_skills` keys
3. A **PoC validation guide** showing the concrete steps to dispatch the generic stage agent for a Python task end-to-end

### WHEN (Trigger Conditions)

- Phase 1 is substantially built but not formally closed
- The naming convention exists in practice (visible in the python3 manifest) but has no ratification document
- Contributors creating new language manifests have no reference guide for how dispatch works end-to-end

### WHY (Problem Being Solved)

- **Naming ambiguity**: The 7 workflow skill directory names and the manifest `stage_skills` keys use different naming schemes today. Without a ratified taxonomy, new language plugins will invent inconsistent names.
- **No validation guide**: The generic stage agent, manifest resolution scripts, and dispatch helper exist but have never been exercised as a documented end-to-end flow. Without a PoC guide, the system is untestable by anyone other than the original author.
- **Phase 1 closure**: Completing these deliverables formally closes Phase 1, enabling Phase 2 work to begin.

---

## Codebase Research

### Similar Patterns Found

#### Pattern 1: Workflow Skill Directory Naming

- **Location**: `plugins/development-harness/skills/workflows/*/SKILL.md` (7 directories)
- **Relevance**: These are the current stage names. Directory names are: `discovery`, `planning`, `task-decomposition`, `execution`, `context-integration`, `final-verification`, `forensic-review`
- **Reusable**: These names are the starting point for the taxonomy ratification

#### Pattern 2: Python3 Manifest Stage Skills Keys

- **Location**: `plugins/python3-development/manifests/python3/language-manifest.yaml:11-17`
- **Relevance**: The manifest uses a different naming scheme for stage_skills keys: `discovery`, `design`, `planning-context-integration`, `planning-task-decomposition`, `implementation`, `testing-forensic-review`, `testing-verification`
- **Reusable**: This demonstrates the `{domain}-{sdlc-stage}` convention in practice, but the domain prefixes (`planning-`, `testing-`) do not match the workflow skill directory names

#### Pattern 3: Default Development Flow Stage Descriptions

- **Location**: `plugins/development-harness/skills/development-harness/references/default-development-flow.md:33-197`
- **Relevance**: Defines the canonical 7-stage pipeline (S1-S7) with stage names, purposes, inputs, outputs, and skill references. Uses `/development-harness:{stage-name}` skill activation syntax.
- **Reusable**: The stage descriptions and skill references are the authoritative source for what each stage does

#### Pattern 4: Generic Stage Agent Dispatch Protocol

- **Location**: `plugins/development-harness/agents/generic-stage-agent.md:12-31`
- **Relevance**: Defines the 5 inputs the agent receives (stage workflow, cross-cutting skill, domain skills, task/artifact file, quality gate commands) and the execution protocol. This is the runtime contract the PoC guide must document.
- **Reusable**: The agent's input contract is the basis for the dispatch guide

#### Pattern 5: Python3-CLI Manifest Extends Pattern

- **Location**: `plugins/python3-development/manifests/python3-cli/language-manifest.yaml:1-13`
- **Relevance**: Shows the `extends: python3-development:python3` inheritance pattern where a stack-specific manifest overrides only certain stage_skills. Uses `design` and `implementation` as stage keys (no domain prefix).
- **Reusable**: Demonstrates that the naming convention must account for manifest inheritance

#### Pattern 6: Manifest Resolution Scripts

- **Location**: `plugins/development-harness/scripts/manifest_discovery.py`, `manifest_merge.py`, `manifest_resolver.py`, `manifest_schema.py`, `dispatch_helper.py`
- **Relevance**: These scripts implement the runtime resolution of manifests to agent dispatch. The PoC guide must show how these scripts participate in the flow.
- **Reusable**: The dispatch_helper.py is the bridge between manifest resolution and generic stage agent invocation

### Existing Infrastructure

The following components already exist and are relevant:

- **Language manifest schema reference**: `plugins/development-harness/skills/development-harness/references/language-manifest-schema.md` — defines the markdown-based manifest format (separate from the YAML manifests that actually exist)
- **Role resolution protocol**: `plugins/development-harness/skills/development-harness/references/role-resolution-protocol.md`
- **Artifact conventions**: `plugins/development-harness/skills/development-harness/references/artifact-conventions.md`
- **Human touchpoint model**: `plugins/development-harness/skills/development-harness/references/human-touchpoint-model.md`

### Code References

- `plugins/development-harness/skills/workflows/discovery/SKILL.md:1-6` — workflow skill frontmatter pattern (name: discovery, description includes "SAM Stage 1")
- `plugins/development-harness/skills/workflows/execution/SKILL.md:1-5` — workflow skill frontmatter pattern (name: execution, description includes "SAM Stage 5")
- `plugins/python3-development/manifests/python3/language-manifest.yaml:10-17` — stage_skills mapping with domain-prefixed keys
- `plugins/python3-development/manifests/python3-cli/language-manifest.yaml:11-13` — override stage_skills with non-prefixed keys (`design`, `implementation`)
- `plugins/development-harness/agents/generic-stage-agent.md:14-20` — the 5 dispatch inputs
- `plugins/development-harness/CLAUDE.md:23-30` — the 7-stage pipeline overview

---

## Use Scenarios

### Scenario 1: Plugin Author Creating a New Language Manifest

**Actor**: A developer creating a TypeScript language plugin
**Trigger**: They need to write a `language-manifest.yaml` with `stage_skills` keys that the harness can resolve
**Goal**: Know what stage names to use in the `stage_skills` mapping and what naming convention to follow
**Expected Outcome**: The taxonomy document tells them the canonical stage names and the `{domain}-{sdlc-stage}` convention so their manifest resolves correctly at runtime

### Scenario 2: Contributor Verifying the Harness Works End-to-End

**Actor**: A contributor who has never used the development harness
**Trigger**: They want to validate that the generic stage agent can be dispatched with a real Python task
**Goal**: Follow a step-by-step guide to dispatch a stage and observe the result
**Expected Outcome**: The PoC guide walks them through manifest resolution, skill loading, agent dispatch, and output artifact collection for a concrete Python example

### Scenario 3: Reviewer Auditing Naming Consistency

**Actor**: A code reviewer looking at a PR that adds or modifies stage references
**Trigger**: They need to verify that stage names in a manifest, workflow skill, or dispatch call follow the convention
**Goal**: Check the naming against a single authoritative reference
**Expected Outcome**: The taxonomy document serves as the canonical reference; the naming audit provides a checklist of what is compliant and what needs correction

---

## Gap Analysis

### Identified Gaps

| # | Category | Gap Description | Impact |
|---|----------|-----------------|--------|
| 1 | Scope | Naming mismatch between workflow skill dirs and manifest stage_skills keys. Workflow dirs: `context-integration`, `final-verification`. Manifest keys: `planning-context-integration`, `testing-verification`. No document explains whether both are valid or which is canonical. | Plugin authors cannot know which names to use in their manifests |
| 2 | Scope | The language-manifest-schema.md describes a markdown-based manifest format, but actual manifests are YAML files. The taxonomy document needs to account for the YAML `stage_skills` key naming, not just the markdown schema. | Schema documentation and reality diverge |
| 3 | Behavior | The python3-cli manifest uses non-prefixed keys (`design`, `implementation`) while the base python3 manifest uses domain-prefixed keys (`planning-context-integration`). The `extends` inheritance logic must handle both. It is unclear whether non-prefixed keys are intentional overrides or naming inconsistencies. | Manifest inheritance may silently fail if naming convention is ambiguous |
| 4 | Scope | IEEE 12207 / ISO 15288 / SAFe terminology mapping has not been researched or documented anywhere in the codebase. This is entirely new work. | Cannot ratify stage names without the standards research |
| 5 | Integration | The dispatch_helper.py and manifest_resolver.py exist but have no usage examples or integration tests. The PoC guide must describe the actual invocation path, which requires understanding how these scripts connect. | PoC guide cannot be written without verifying the scripts actually work together |
| 6 | Scope | The `{domain}-{sdlc-stage}` convention is mentioned in the feature request but not formally defined anywhere in the codebase. What constitutes a "domain"? What are the valid domains? | Without a formal definition, the convention is unenforceable |

---

## Questions Requiring Resolution

### Q1: What is the relationship between workflow skill names and manifest stage_skills keys?

- **Category**: Scope
- **Gap**: Workflow skill dirs use bare names (`context-integration`), manifest keys use domain-prefixed names (`planning-context-integration`). Are these intentionally different layers?
- **Question**: Are the workflow skill directory names the "cross-cutting stage skill" (input 2 of generic-stage-agent) while the manifest `stage_skills` keys name the "domain skills" (input 3)? Or should they use the same naming scheme?
- **Options**:
  - A) Two-layer naming: workflow skills are stage-level (bare), manifest skills are domain-level (prefixed). The dispatch maps one to the other.
  - B) Single naming: both should use the same names, and the current mismatch is a bug to fix.
- **Why It Matters**: The taxonomy document must define one canonical convention. If option A, the document must explain both layers. If option B, corrections are needed.
- **Resolution**: _pending_

### Q2: What are the valid "domain" prefixes in `{domain}-{sdlc-stage}`?

- **Category**: Scope
- **Gap**: The python3 manifest uses `planning-` and `testing-` as domain prefixes, but no document defines what domains exist or how to choose one.
- **Question**: Is the domain prefix drawn from a fixed list (e.g., `planning`, `design`, `implementation`, `testing`, `review`) or is it free-form per language plugin? Should it correspond to IEEE 12207 process groups?
- **Why It Matters**: Determines whether the taxonomy document defines a closed or open vocabulary for domains.
- **Resolution**: _pending_

### Q3: Should the PoC guide be executable (runnable commands) or descriptive (conceptual walkthrough)?

- **Category**: Behavior
- **Gap**: The feature request says "document how to dispatch a generic stage agent with a Python task" but does not specify format.
- **Question**: Should the PoC guide be a step-by-step runnable procedure (e.g., `uv run python scripts/dispatch_helper.py ...`) or a conceptual document showing the data flow with example inputs/outputs?
- **Options**:
  - A) Executable: shell commands the reader can run, with expected output
  - B) Descriptive: data flow diagram with example manifest, skill, and agent inputs
  - C) Both: a descriptive overview followed by a runnable example
- **Why It Matters**: Executable guides require verifying the scripts work. Descriptive guides can be written from the code contracts alone.
- **Resolution**: _pending_

### Q4: Where should the taxonomy document live?

- **Category**: Integration
- **Gap**: No existing file or placeholder for an SDLC naming taxonomy in the codebase.
- **Question**: Should the taxonomy document be placed in `plugins/development-harness/skills/development-harness/references/` (alongside the existing schema and flow docs), in `plugins/development-harness/docs/`, or in `.claude/docs/sdlc-layers/`?
- **Options**:
  - A) `plugins/development-harness/skills/development-harness/references/sdlc-stage-taxonomy.md` — co-located with other harness reference docs
  - B) `plugins/development-harness/docs/sdlc-stage-taxonomy.md` — plugin docs directory
  - C) `.claude/docs/sdlc-layers/layer-0/sdlc-stage-taxonomy.md` — layer 0 documentation
- **Why It Matters**: Location determines discoverability and which agents/skills can reference it at load time.
- **Resolution**: _pending_

---

## Goals (Pending Resolution)

_These goals will be finalized after questions are resolved._

1. **Taxonomy document produced** — a single reference document mapping SAM stage names to IEEE 12207 / ISO 15288 / SAFe terminology, formally defining the `{domain}-{sdlc-stage}` naming convention with valid domains and examples
2. **Naming audit completed** — a checklist or table showing each workflow skill directory name, each manifest stage_skills key, and whether each conforms to the ratified convention (with corrections listed for any that do not)
3. **PoC validation guide produced** — a document showing how to dispatch the generic stage agent for a Python task, covering manifest resolution, skill loading, agent input assembly, and expected output
4. **Phase 1 formally closed** — all three deliverables committed to the repository and referenced from the development-harness documentation

---

## Next Steps

After questions are resolved:

1. Update "Resolution" fields in Questions section
2. Finalize Goals section
3. Proceed to RT-ICA assessment
4. Then proceed to architecture design
