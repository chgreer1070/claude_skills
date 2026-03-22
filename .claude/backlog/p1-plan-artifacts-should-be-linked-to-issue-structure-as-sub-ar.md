---
name: Plan artifacts should be linked to issue structure as sub-artifacts
description: 'Plan artifacts (feature-context, architect specs, task plans) must be linked to their parent GitHub Issue as sub-artifacts, making the issue the single entry point. Two critical constraints: (1) artifacts must always live in the root worktree path, never inside isolated worktree agent paths; (2) when a backend is available (GitHub now, GitLab/Linear/Supabase later), it is the central database — local files are cache only. Implementation: structured Artifact Manifest section in GitHub Issue body, producer agents register artifacts via MCP, consumer agents discover via MCP, backend abstraction layer for multi-provider support.'
metadata:
  topic: plan-artifacts-should-be-linked-to-issue-structure-as-sub-ar
  source: 'User vision statement 2026-03-21 — divergence #3 from canonical issue lifecycle'
  added: '2026-03-21'
  priority: P1
  type: Feature
  status: needs-grooming
  issue: '#965'
  last_synced: '2026-03-22T02:20:00Z'
  groomed: '2026-03-22'
  plan: plan/P965-artifact-manifest.yaml
---

## Story

As a **developer using Claude Code skills**, I want to **plan artifacts should be linked to issue structure as sub-artifacts** so that **the tooling becomes more capable and complete**.

## Description

Plan artifacts (feature-context-{slug}.md, architect-{slug}.md) are standalone files in plan/ with no formal link to the GitHub Issue structure. They should be linked as sub-artifacts of the parent issue, making the issue the single entry point for all related artifacts. This could mean: (1) storing plan artifacts under a path derived from the issue number, (2) adding artifact manifest to the issue body, or (3) attaching plan file paths as issue metadata.

## Acceptance Criteria

- [ ] Work matches description
- [ ] Plan or implementation complete

## Context

- **Source**: User vision statement 2026-03-21 — divergence #3 from canonical issue lifecycle
- **Priority**: P1
- **Added**: 2026-03-21
- **Research questions**: None

## RT-ICA

<div><sub>2026-03-21T23:20:39Z</sub>

## RT-ICA Final Assessment

**Title**: Plan artifacts should be linked to issue structure as sub-artifacts

**Goal**: Link plan artifacts (feature-context, architect specs, task files) to their parent GitHub Issue so the issue becomes the single entry point for all related artifacts.

**Assessment Date**: 2026-03-21

### Conditions Analysis

**Snapshot → Final Transitions:**

1. **Current plan artifact naming convention and directory structure** | Snapshot: DERIVABLE → Final: RESOLVED | Citation: Wave 1 fact-check verified 4 artifact types (feature-context-{slug}.md, plan/codebase/{FOCUS}.md, architect-{slug}.md, P{NNN}-{slug}.yaml); task files also support directory organization per local-workflow.md

2. **How SAM sam_create currently generates plan file paths** | Snapshot: DERIVABLE → Final: RESOLVED | Citation: add-new-feature skill orchestrates all artifact creation; swarm-task-planner generates `plan/P{NNN}-{slug}.yaml` (MCP schema uses P{NNN} plan identifiers per backlog_get_ready_sam_tasks output)

3. **How add-new-feature skill currently names/places artifacts** | Snapshot: DERIVABLE → Final: RESOLVED | Citation: Skill orchestration produces plan/feature-context-{slug}.md, plan/architect-{slug}.md, plan/codebase/{FOCUS}.md, plan/P{NNN}-{slug}.yaml per local-workflow.md § Phase 1

4. **Which linking approach the user prefers** | Snapshot: MISSING → Final: UNRESOLVED (narrowed by fact-check findings) | Citation: Fact-check eliminated approach 3a (path-derived breaks SAM addressing), partially endorsed approach 3b (manifest already implemented for Context Manifest), qualified approach 3c (GitHub custom fields in preview, org-level setup). Decision remains user-level choice between extending manifest (3b, zero infrastructure cost) vs. adopting custom metadata (3c, preview feature, org-level dependency)

5. **How backlog MCP tools currently store/retrieve plan references** | Snapshot: DERIVABLE → Final: RESOLVED | Citation: backlog_update(plan="...") stores paths in metadata.plan field; backlog_list output confirmed 10+ items with linked plans (e.g., issue #927: `plan: plan/P784-integration-branch-management-followup-2.yaml`); backlog_get_ready_sam_tasks returns parent_issue_number + task list (reverse lookup from plan available via sam_read)

6. **Whether GitHub Issue API supports custom metadata fields** | Snapshot: DERIVABLE → Final: RESOLVED | Citation: GitHub custom issue fields in public preview as of 2026-03-12; REST + GraphQL endpoints available at `/rest/issues/issue-field-values`; limit 25 custom fields per org; preview status means subject to change

### New Conditions Discovered

**Critical finding from fact-check (triggers new RT-ICA condition)**:

7. **Artifact taxonomy clarity** | Status: UNRESOLVED | Citation: Fact-check revealed backlog item conflates primary artifacts (feature-context, architect, tasks) with secondary outputs (T0/TN verification, codebase analysis). Current proposal does not define which should be linked to the issue. This affects scope: do we link 4 types or 6+ types? Does SAM enforce secondary artifact discovery?

**From fact-check impact radius**:

8. **SAM plan addressing migration path** | Status: UNRESOLVED | Citation: Fact-check found approach 3a (issue-number-derived paths) would break existing SAM MCP tools (sam_status, sam_ready, sam_read all use P{NNN} identifiers). If approach 3a is selected, requires SAM CLI refactor (high risk, not just data migration). If approach 3b/3c selected, no SAM changes needed.

**From fact-check premise refutation**:

9. **Premise accuracy** | Status: REFUTED | Citation: Fact-check demonstrated plan artifacts are NOT standalone — they already have formal links via backlog MCP `metadata.plan` field AND explicit artifact headers. This means the issue is not about "adding" links but about "enforcing consistency" and "discovering secondary artifacts". Scope should shift from "establish missing link" to "complete and validate existing link + handle secondary artifacts".

### Completion Checklist

- [x] All DERIVABLE conditions resolved with citations
- [x] MISSING condition narrowed via fact-check findings (user choice remains, but options are bounded)
- [x] New conditions identified (artifact taxonomy, SAM migration path, premise accuracy)
- [x] Decision gate assessed (design choice exists; requires user input on approach 3b vs 3c)

### Decision

**Status**: APPROVED FOR PLANNING (with design conditions)

**Rationale**:
- All information necessary to plan has been gathered
- The fact-check refuted the original premise (artifacts are NOT standalone), which means the actual problem is smaller in scope than stated
- Three feasible approaches exist; the user must choose between extending existing manifest (3b, implemented, zero risk) vs. adopting GitHub preview feature (3c, requires org setup, preview risk)
- Artifact taxonomy (condition 7) must be clarified before implementation to avoid scope creep
- SAM migration path (condition 8) depends on approach selection

**Recommendations**:
1. Clarify artifact taxonomy: primary (feature-context, architect, tasks) vs. secondary (T0/TN, codebase analysis, drift audit outputs) vs. transient (active-task context files)
2. Select linking approach: extend manifest in issue body (approach 3b) or adopt GitHub custom fields (approach 3c)
3. If 3a considered: requires SAM refactor; not recommended unless slug-based naming becomes a burden (current evidence shows no user complaints)
4. Plan should include validation layer to prevent orphaning of secondary artifacts

**Next Steps**: User decision on approach + artifact taxonomy definition → proceed to implementation planning
</div>

## Groomed (2026-03-21)

### Issue Classification

<div><sub>2026-03-21T23:16:40Z</sub>

### Impact

<div><sub>2026-03-21T00:00:00Z</sub>

<div><sub>2026-03-21T23:19:38Z</sub>
</div>

<div><sub>2026-03-21T23:22:00Z</sub>

**17 systems affected — classified by role**:

**Producers (create plan artifacts) — 4 agents**:
- `plugins/development-harness/agents/feature-researcher.md` — writes feature-context-{slug}.md
- `plugins/python3-development/agents/python-cli-design-spec.md` — writes architect-{slug}.md
- `plugins/development-harness/agents/swarm-task-planner.md` — writes tasks-{N}-{slug}.md (or directory)
- `plugins/development-harness/agents/codebase-analyzer.md` — writes plan/codebase/{FOCUS}.md (optional)
- (Secondary producers via existing hooks) `t0-baseline-capture` and `tn-verification-gate` agents

**Consumers (read plan artifacts) — 5 systems**:
- `packages/sam_schema/` (MCP server) — parses plan file paths, provides P{N} addressing
- `packages/backlog_core/` (MCP server) — stores/syncs plan field to GitHub
- `plugins/development-harness/skills/start-task/SKILL.md` — reads specific tasks from plan files
- `plugins/development-harness/skills/complete-implementation/SKILL.md` — reads tasks for quality gates
- `plugins/development-harness/skills/implementation-manager/scripts/task_status_hook.py` — updates task status in files

**Orchestrators (coordinate artifact creation/linking) — 4 skills**:
- `plugins/development-harness/skills/add-new-feature/SKILL.md` — names and creates all artifact paths
- `plugins/development-harness/skills/work-backlog-item/SKILL.md` — links plan to backlog via MCP
- `plugins/development-harness/skills/implement-feature/SKILL.md` — passes task file paths to execution loop
- `plugins/development-harness/skills/work-milestone/SKILL.md` — dispatches agents with plan references

**Documentation (will become stale without update) — 4 files**:
- `.claude/rules/local-workflow.md` § Phase 1 — documents artifact naming convention
- `plugins/development-harness/docs/plan-artifact-lifecycle.md` — describes mutability policy
- `plugins/development-harness/docs/workflow-architecture-diagram.md` — data flow diagram showing plan/ paths
- `plugins/development-harness/docs/TASK_FILE_FORMAT.md` — task file format specification

**Risk by implementation approach**:
- **Approach 3a (path-derived)**: HIGH RISK — requires refactoring SAM MCP addressing (sam_status, sam_ready, sam_read all hardcode P{NNN} plan identifiers). Breaking change to public MCP interface. Affects all downstream consumers.
- **Approach 3b (manifest in issue body)**: LOW RISK — extends existing Context Manifest section (already written by context-refinement agent). No MCP interface changes. Requires backlog MCP tool update to maintain manifest; minimal breaking changes.
- **Approach 3c (GitHub custom metadata)**: MEDIUM RISK — introduces GitHub API preview feature dependency; org-level configuration required. Requires backlog MCP to write/read custom fields via REST API (not currently supported). If GitHub custom fields exit preview, behavior may change.

**CI/Config impact**:
- No impact identified — plan/ directory is not referenced in GitHub Actions workflows

**Effort to update all 17 systems** (depends on approach):
- Approach 3b: ~2 days (modify backlog MCP tool + agent instructions)
- Approach 3a: ~5 days (refactor SAM + cascading updates to 9 downstream consumers)
- Approach 3c: ~3 days (add GitHub API support to backlog MCP + org-level setup docs)
</div>

### Reproducibility

<div><sub>2026-03-21T23:21:37Z</sub>

To observe the current state:

**Step 1: Verify that primary artifacts exist but lack discoverable links**
- Create a new feature via `/add-new-feature` skill
- The skill produces: `plan/feature-context-{slug}.md`, `plan/architect-{slug}.md`, `plan/P{NNN}-{slug}.yaml`
- Open the corresponding GitHub Issue for the feature
- Observation: The issue body contains `**Backlog item**: #{issue_number}` header BUT no manifest listing ALL artifacts (primary + secondary)
- Expected: A dedicated section enumerating all artifact paths (feature context, architect spec, task plan, codebase analysis if present, T0 baseline, TN verification)

**Step 2: Verify that secondary artifacts are undiscoverable**
- After running `/implement-feature` and `/complete-implementation` on a feature with acceptance criteria
- These steps produce additional artifacts: `plan/T0-baseline-{slug}.yaml`, `plan/TN-verification-{slug}.yaml`
- Navigate to the GitHub Issue
- Observation: No artifact manifest section exists; there is no programmatic way to discover T0/TN files except by knowing the naming convention and manually searching plan/
- Secondary artifact paths are not stored in backlog MCP `metadata.plan` field (only primary task plan is stored)

**Step 3: Verify that linking is inconsistent across systems**
- Query the backlog MCP: `backlog_list()` → returns `plan` field with one path (primary task file)
- Query SAM MCP: `sam_status(plan="P{N}")` → parses task file but does not return artifact manifest
- Observation: Two systems store partial artifact information (backlog MCP has one path, SAM has plan parsing) but neither exposes a complete artifact manifest
- There is no single MCP call that returns all artifacts for a given issue

**Current behavior — what works**:
- Backlog items store one plan path via `metadata.plan` field
- Plan artifacts include issue number in headers (e.g., `**Backlog item**: #965`)
- Task file contains Context Manifest section (per context-refinement agent)

**Current behavior — what's missing**:
- No programmatic discovery of secondary artifacts (T0/TN/analysis snapshots)
- No artifact manifest exposed via MCP query tools (backlog or SAM)
- No validation that all artifacts linked in issue metadata actually exist
</div>

### Priority

<div><sub>2026-03-21T23:21:45Z</sub>

**P1 — Blocking workflow completeness**

**Justification from project vision**:
- The canonical issue lifecycle vision expects GitHub Issues to serve as the single entry point to all work artifacts (source: project MEMORY § issue_lifecycle_vision)
- Currently: Issues are a partial entry point (coordination hub for backlog metadata) but require manual filesystem search to discover secondary artifacts
- Impact: Developers cannot answer "what artifacts exist for this issue?" without manual intervention

**User workflow blocked**:
- User completes feature implementation via `/complete-implementation`
- User wants to review all work products (feature context, architecture, task plan, verification results) in one place
- Current state: Must navigate issue → note the plan field → open plan file → guess secondary artifact paths
- Expected: All artifacts enumerated and discoverable from the issue

**Guardrail missing**:
- No validation prevents orphaning artifacts (if a developer renames an artifact file, there is no warning)
- No mechanism enforces that T0/TN verification artifacts are created alongside task plans
- No check ensures backlog item's `plan` field matches an actual file on disk

**Risk without P1 treatment**:
- As the workflow scales (more features, more artifacts per feature), developers will lose work because they cannot find it
- Artifact lifecycle becomes opaque — it is unclear whether a feature's T0 baseline still exists or was deleted
- SAM tools and backlog MCP tools operate independently; artifact discovery requires knowledge of both systems
</div>

### Scope

<div><sub>2026-03-21T23:22:12Z</sub>
<details><summary>struck: 2026-03-21T23:52:56Z — User provided critical architectural constraints about worktrees and backend-first design</summary>

**Reframed from original description**:

Original description conflated two different problems:
1. "Plan artifacts are standalone with no formal link" (REFUTED by fact-checker)
2. "Developers cannot discover all artifacts for an issue" (TRUE — the real problem)

**Actual scope — what needs to be fixed**:

Complete the existing **partial artifact linking** system by:

1. **Defining artifact taxonomy**: Distinguish primary artifacts (feature-context, architect, task plans) from secondary/transient outputs (T0/TN verification, codebase analysis snapshots, active-task context files, documentation drift audit reports)

2. **Enforcing consistency across MCP boundaries**: Currently, backlog MCP stores one plan path and SAM MCP parses another. No single source lists all artifacts.

3. **Adding secondary artifact registration**: Agents that produce secondary artifacts (t0-baseline-capture, tn-verification-gate, codebase-analyzer, doc-drift-auditor) must register their outputs in a manifest so consumers can discover them.

4. **Building artifact discovery interface**: Extend backlog MCP or SAM MCP (or create a new tool) to return a complete artifact manifest for a given issue/plan.

5. **Validating artifact lifecycle**: Add guardrails to detect orphaned artifacts (files in plan/ directory with no issue backlink) and broken references (issue pointing to a non-existent artifact).

**What is OUT of scope**:
- Changing the primary plan file naming convention (approach 3a is not recommended — too risky)
- Restructuring plan/ directory by issue number
- Requiring GitHub organization-level configuration (approach 3c is optional, not mandatory)

**What is IN scope**:
- Creating/extending a manifest section in issue bodies or backlog items
- Updating producer agents to register artifacts in the manifest
- Building a discovery MCP tool or extending existing tools
- Adding validation checks to prevent silent linkage loss
- Updating 17 affected systems (producers, consumers, orchestrators, documentation)
</details>
</div>

<div><sub>2026-03-21T23:52:56Z</sub>

### Research

<div><sub>2026-03-21T23:53:25Z</sub>

### Resources

<div><sub>2026-03-22T02:17:46Z</sub>

**Documentation References**:
- `.claude/rules/local-workflow.md` — canonical workflow definition; Phase 1 (Planning), Phase 2 (Execution), Phase 3 (Quality Gates); artifact naming and paths
- `plugins/development-harness/docs/plan-artifact-lifecycle.md` — artifact mutability policy; human-decision vs. generated artifacts; divergence annotation rules
- `plugins/development-harness/docs/workflow-architecture-diagram.md` — data flow showing producers, consumers, orchestrators, and artifact paths
- `plugins/development-harness/docs/artifact-manifest-backends.md` — ArtifactBackend Protocol reference; current GitHubArtifactProvider; future backend options (GitHub Issue Fields, Projects V2, Linear, GitLab, Supabase); provider implementation mapping
- `.claude/docs/TASK_FILE_FORMAT.md` — task file YAML/markdown format; Context Manifest section specification

**Research**:
- `research/task-management/artifact-manifest-backend-providers.md` — cross-platform comparison of structured metadata capabilities; source citations and API limits for GitHub, Linear, GitLab, Supabase

**MCP Server Documentation**:
- SAM MCP interface: `packages/sam_schema/` — tool definitions for sam_status, sam_ready, sam_read, sam_claim, sam_state; P{NNN} plan addressing
- Backlog MCP interface: `packages/backlog_core/` — tool definitions for backlog_list, backlog_view, backlog_update, backlog_groom, backlog_sync; metadata.plan field storage

**Agent Specifications**:
- Feature researcher: `plugins/development-harness/agents/feature-researcher.md` — output path, backlog item header
- Python CLI design spec: `plugins/python3-development/agents/python-cli-design-spec.md` — output path, artifact header
- Swarm task planner: `plugins/development-harness/agents/swarm-task-planner.md` — output path, P{NNN} naming convention, task file schema
- Codebase analyzer: `plugins/development-harness/agents/codebase-analyzer.md` — optional output path
- T0 baseline capture: `plugins/development-harness/agents/t0-baseline-capture.md` — acceptance criteria format, baseline file format
- TN verification gate: `plugins/development-harness/agents/tn-verification-gate.md` — comparison logic, verdict classification, verification file format

**Skill Specifications**:
- Add-new-feature skill: `plugins/development-harness/skills/add-new-feature/SKILL.md` — orchestration sequence, agent delegation, artifact path outputs
- Implement-feature skill: `plugins/development-harness/skills/implement-feature/SKILL.md` — execution loop, task dispatching, artifact path passing
- Start-task skill: `plugins/development-harness/skills/start-task/SKILL.md` — task claiming via MCP, artifact reading
- Complete-implementation skill: `plugins/development-harness/skills/complete-implementation/SKILL.md` — quality gate phases, artifact reading for code review

**Example Artifact Files** (for reference):
- `/home/ubuntulinuxqa2/repos/claude_skills/plan/feature-context-migrate-milestone-skills-gh-cli.md` — primary artifact with backlog item header
- `/home/ubuntulinuxqa2/repos/claude_skills/plan/architect-migrate-milestone-skills-gh-cli.md` — primary artifact with issue reference
- `/home/ubuntulinuxqa2/repos/claude_skills/plan/P964-backlog-yaml-migration-plan.yaml` — task plan file with P{NNN} naming

**External References**:
- GitHub custom issue fields: https://docs.github.com/en/issues/planning-and-tracking-with-issues/using-issues/managing-issue-fields-in-your-organization (for approach 3c)
- GitHub API custom fields REST endpoint: `/rest/issues/issue-field-values` (approach 3c)
- Backlog item view output from fact-checker: Issue #965 "Fact-Check Summary" section with evidence of current artifact linking state
</div>

<div><sub>2026-03-22T02:20:00Z</sub>

## Resources

- plugins/development-harness/docs/backend-providers.md — Backend provider reference for issues, plans, tasks, and artifacts across GitHub/Linear/GitLab/Supabase
- research/task-management/artifact-manifest-backend-providers.md — Detailed cross-platform research with citations
- plan/architect-artifact-manifest.md — Architecture spec for ArtifactBackend Protocol
- plan/feature-context-artifact-manifest.md — Problem space and desired outcomes
- plan/codebase/artifact-manifest-patterns.md — Existing codebase patterns
</div>


## Research

Industry patterns researched across Linear, Jira, Asana, and Monday.com (2026-03-21):

**Linear**: Resources section as manifest — each issue aggregates embedded documents, external links, and related items. Documents are first-class entities. MCP accesses artifacts through issue relationships.

**Jira**: Remote links separate ownership from reference. Artifact lives in authoritative system, issue maintains structured reference (URL + title + relationship type). Multiple issues can reference same artifact. Bidirectional inward/outward semantics.

**Monday**: Column-based metadata — relationships are first-class column types with queryable schemas. Connect Boards create bidirectional cross-item references.

**Asana** (cautionary): Embedding model creates redundancy, no back-references, dependencies and attachments orthogonal. Avoid this pattern.

**Selected approach**: Combine Linear's manifest concept (issue body as single entry point) with Jira's reference separation (artifacts stay in plan/, issue holds structured references) and Monday's structured metadata (type, path, status per artifact).

Full research files: /tmp/research-linear-artifacts.md, /tmp/research-jira-asana-monday-artifacts.md
</div>


## Scope

**Reframed from original description based on fact-checking and user architectural requirements.**

NOT "link standalone artifacts to issues" — artifacts are already partially linked via backlog `plan` field and headers.

The actual scope has two dimensions:

### Dimension 1: Worktree Safety
Plan artifacts MUST always live in the root worktree (main repo path). They must NEVER be created or modified inside a worktree agent's isolated path. When `Agent(isolation: "worktree")` runs, it gets a separate git copy — uncommitted files in `plan/` are invisible. Agents in worktrees must access plan artifacts via the backend (GitHub API), not the local filesystem.

### Dimension 2: Backend-First Architecture
When a backend is available (GitHub now, GitLab/Linear/Supabase later), it is the central database and tracker — not local files. Plan artifacts should be stored/referenced via backend features:
- GitHub Issues body sections and comments for artifact content
- GitHub Projects V2 fields for structured metadata
- GitHub sub-issues for task decomposition
- GitHub issue links for artifact relationships

Local `plan/` files become a cache/working copy, not the source of truth. The backlog MCP already follows this pattern (GitHub Issues = source of truth, `.claude/backlog/` = local cache).

### What's IN scope
- Artifact manifest in GitHub Issue body (structured section listing all artifacts with type, path/URL, status)
- Producer agents register artifacts in the manifest when creating them (via backlog MCP or GitHub API)
- Consumer agents discover artifacts via MCP call that reads the manifest from GitHub
- Root-worktree-only constraint enforced in producer agents and SAM tools
- Backend abstraction layer so the same interface works with GitHub, GitLab, Linear, Supabase

### What's OUT of scope
- Migrating existing plan files (backward compatibility maintained)
- Changing SAM P{N} addressing scheme
- Modifying worktree agent isolation mechanism itself
- Full implementation of GitLab/Linear/Supabase backends (design the abstraction, implement GitHub only)
</div>

### Expected Behavior

<div><sub>2026-03-21T23:22:26Z</sub>

**After implementation, the artifact lifecycle becomes visible and enforced**:

**User workflow (discovered artifacts)**:
1. User completes feature implementation via `/complete-implementation`
2. User navigates to the GitHub Issue for the feature
3. User opens the issue body and finds a new `## Artifact Manifest` section listing:
   - Feature context: `plan/feature-context-{slug}.md` (type: primary, status: present)
   - Architecture spec: `plan/architect-{slug}.md` (type: primary, status: present)
   - Task plan: `plan/P{NNN}-{slug}.yaml` (type: primary, status: present)
   - Codebase analysis: `plan/codebase/{FOCUS}.md` (type: secondary-optional, status: present)
   - T0 baseline: `plan/T0-baseline-{slug}.yaml` (type: secondary, status: present)
   - TN verification: `plan/TN-verification-{slug}.yaml` (type: secondary, status: present)
4. User can click each path and navigate directly to the artifact
5. User can verify completion status by checking if TN verification marks "PASS" or "REGRESSED"

**Orchestrator perspective (complete artifact tracking)**:
1. MCP call: `backlog_get_ready_sam_tasks(parent_issue_number=965)` returns task list
2. MCP call: NEW `backlog_get_artifact_manifest(parent_issue_number=965)` returns artifact list with file paths and status
3. SAM MCP call: `sam_status(plan="P{N}")` optionally extends output to include artifact manifest (backward compatible)
4. Validation: hook script checks that all artifacts in manifest exist on disk; warns if missing

**Guardrails enforced**:
- When a task completes (via `/start-task --complete`), the artifact manifest is updated automatically
- When secondary artifacts are created (T0 baseline, TN verification), they are registered in the manifest
- If a producer agent cannot create an artifact (e.g., optional codebase analysis is skipped), it registers the absence as "skipped"
- Manifest is synced to GitHub Issue body via backlog MCP `_sync_groomed_to_github_issue()` (existing mechanism)

**Consistency across systems**:
- Backlog MCP: stores artifact manifest in `metadata.artifacts` or issue body section
- SAM MCP: preserves plan-level addressing (P{NNN}); optionally exposes artifact list via extension
- Task execution hooks: automatically register completed tasks and secondary artifacts in manifest
- Add-new-feature skill: instructs producer agents to register artifacts; orchestrator confirms registration before signaling completion

**Discovery interface (new or extended tool)**:

Option A — Extend backlog MCP with artifact discovery:
```
backlog_get_artifact_manifest(parent_issue_number: int) -> {
  "artifacts": [
    {"path": "plan/feature-context-slug.md", "type": "primary", "status": "present", "created_at": "ISO timestamp"},
    {"path": "plan/architect-slug.md", "type": "primary", "status": "present", "created_at": "ISO timestamp"},
    {"path": "plan/T0-baseline-slug.yaml", "type": "secondary", "status": "present", "created_at": "ISO timestamp"},
    {"path": "plan/TN-verification-slug.yaml", "type": "secondary", "status": "present", "verdict": "PASS"},
  ],
  "manifest_version": "2024-03-21T10:30:00Z"
}
```

Option B — Extend SAM MCP:
```
sam_status(plan="P{N}", include_artifacts=true) -> {
  "plan": {...},
  "artifacts": [...],  # new optional field
  "manifest_version": "..."
}
```

Option C — Create dedicated artifact discovery tool in a new MCP server or as a sub-tool in backlog MCP.
</div>

### Acceptance Criteria

<div><sub>2026-03-21T23:22:52Z</sub>

- [ ] Artifact taxonomy is defined and documented: primary (feature-context, architect, task plan) vs. secondary (T0/TN, codebase analysis, drift audit) vs. transient (active-task context files)

- [ ] Linking approach is selected: approach 3b (manifest in issue body) or approach 3c (GitHub custom metadata). Approach 3a is explicitly rejected with documented rationale.

- [ ] All plan artifact types are listed in manifest: feature-context-{slug}.md, architect-{slug}.md, P{NNN}-{slug}.yaml, T0-baseline-{slug}.yaml, TN-verification-{slug}.yaml, plan/codebase/{FOCUS}.md (if present)

- [ ] Manifest is stored and synchronized: in issue body (3b) via backlog MCP `_sync_groomed_to_github_issue()`, OR via GitHub custom fields (3c) with REST/GraphQL API support in backlog MCP

- [ ] Producer agents register artifacts when created: feature-researcher, python-cli-design-spec, swarm-task-planner, codebase-analyzer, t0-baseline-capture, tn-verification-gate all call backlog_update() or equivalent to register artifacts

- [ ] Manifest is updated when tasks complete: task_status_hook.py or equivalent updates artifact manifest when SubagentStop fires (task marked COMPLETE)

- [ ] Consumers can discover all artifacts via single MCP call: new or extended backlog MCP tool (e.g., backlog_get_artifact_manifest) returns complete artifact list with paths and status

- [ ] Backward compatibility maintained: existing `plan` field in backlog items remains functional; SAM MCP plan addressing (P{NNN}) is unchanged

- [ ] Validation layer prevents orphaning: hook script or backlog tool warns if manifest references a non-existent file; alerts if artifact files exist on disk but are not registered in manifest

- [ ] Documentation updated: .claude/rules/local-workflow.md, plan-artifact-lifecycle.md, TASK_FILE_FORMAT.md, and workflow-architecture-diagram.md reflect new manifest structure

- [ ] All 17 affected systems pass integration tests: producers register correctly, consumers retrieve manifests, orchestrators link manifests to backlog items, SAM tools remain functional with existing code
</div>

### Files

<div><sub>2026-03-21T23:23:05Z</sub>

**Affected systems by file path**:

**MCP Servers — Core Producers/Consumers**:
- `packages/sam_schema/` — SAM MCP server; plan addressing, artifact exposure (extend status tool)
- `packages/backlog_core/` — Backlog MCP server; manifest storage and sync to GitHub

**Producer Agents — Create Artifacts**:
- `plugins/development-harness/agents/feature-researcher.md` — writes feature-context-{slug}.md
- `plugins/python3-development/agents/python-cli-design-spec.md` — writes architect-{slug}.md
- `plugins/development-harness/agents/swarm-task-planner.md` — writes tasks-{N}-{slug}.md
- `plugins/development-harness/agents/codebase-analyzer.md` — writes plan/codebase/{FOCUS}.md
- `plugins/development-harness/agents/t0-baseline-capture.md` — writes plan/T0-baseline-{slug}.yaml
- `plugins/development-harness/agents/tn-verification-gate.md` — writes plan/TN-verification-{slug}.yaml

**Consumer Skills — Read/Use Artifacts**:
- `plugins/development-harness/skills/add-new-feature/SKILL.md` — orchestrates creation, registers artifacts
- `plugins/development-harness/skills/work-backlog-item/SKILL.md` — links plan via backlog_update
- `plugins/development-harness/skills/implement-feature/SKILL.md` — passes task files to execution loop
- `plugins/development-harness/skills/start-task/SKILL.md` — reads task files by path
- `plugins/development-harness/skills/complete-implementation/SKILL.md` — reads task files for gates
- `plugins/development-harness/skills/work-milestone/SKILL.md` — dispatches agents with plan refs

**Automation/Hooks — Update Artifact Status**:
- `plugins/development-harness/skills/implementation-manager/scripts/task_status_hook.py` — updates task status in files
- `plugins/development-harness/skills/implementation-manager/` — context injection for active tasks

**Documentation — Stale After Changes**:
- `.claude/rules/local-workflow.md` — artifact naming convention, Phase 1 output paths, Phase 2 execution, Phase 3 quality gates
- `plugins/development-harness/docs/plan-artifact-lifecycle.md` — mutability policy for all artifact types
- `plugins/development-harness/docs/workflow-architecture-diagram.md` — data flow diagram showing plan/ directory and artifact paths
- `plugins/development-harness/docs/TASK_FILE_FORMAT.md` — task file format specification, Context Manifest section

**Configuration Files — May Need Updates**:
- `.pre-commit-config.yaml` — if new artifact types require validation steps (optional)
- GitHub Actions workflows — no known impact (plan/ not referenced in CI)

**Integration Point Files — Require Verification**:
- `plugins/development-harness/agents/context-refinement.md` — already writes Context Manifest section; must preserve when extending
- `plugins/development-harness/agents/plan-validator.md` — may validate artifact references; confirm no conflicts
- `plugins/development-harness/agents/feature-verifier.md` — may reference artifacts; confirm compatibility
</div>

### Resources

<div><sub>2026-03-21T23:23:17Z</sub>

**Documentation References**:
- `.claude/rules/local-workflow.md` — canonical workflow definition; Phase 1 (Planning), Phase 2 (Execution), Phase 3 (Quality Gates); artifact naming and paths
- `plugins/development-harness/docs/plan-artifact-lifecycle.md` — artifact mutability policy; human-decision vs. generated artifacts; divergence annotation rules
- `plugins/development-harness/docs/workflow-architecture-diagram.md` — data flow showing producers, consumers, orchestrators, and artifact paths
- `plugins/development-harness/docs/TASK_FILE_FORMAT.md` — task file YAML/markdown format; Context Manifest section specification

**MCP Server Documentation**:
- SAM MCP interface: `packages/sam_schema/` — tool definitions for sam_status, sam_ready, sam_read, sam_claim, sam_state; P{NNN} plan addressing
- Backlog MCP interface: `packages/backlog_core/` — tool definitions for backlog_list, backlog_view, backlog_update, backlog_groom, backlog_sync; metadata.plan field storage

**Agent Specifications**:
- Feature researcher: `plugins/development-harness/agents/feature-researcher.md` — output path, backlog item header
- Python CLI design spec: `plugins/python3-development/agents/python-cli-design-spec.md` — output path, artifact header
- Swarm task planner: `plugins/development-harness/agents/swarm-task-planner.md` — output path, P{NNN} naming convention, task file schema
- Codebase analyzer: `plugins/development-harness/agents/codebase-analyzer.md` — optional output path
- T0 baseline capture: `plugins/development-harness/agents/t0-baseline-capture.md` — acceptance criteria format, baseline file format
- TN verification gate: `plugins/development-harness/agents/tn-verification-gate.md` — comparison logic, verdict classification, verification file format

**Skill Specifications**:
- Add-new-feature skill: `plugins/development-harness/skills/add-new-feature/SKILL.md` — orchestration sequence, agent delegation, artifact path outputs
- Implement-feature skill: `plugins/development-harness/skills/implement-feature/SKILL.md` — execution loop, task dispatching, artifact path passing
- Start-task skill: `plugins/development-harness/skills/start-task/SKILL.md` — task claiming via MCP, artifact reading
- Complete-implementation skill: `plugins/development-harness/skills/complete-implementation/SKILL.md` — quality gate phases, artifact reading for code review

**Example Artifact Files** (for reference):
- `/home/ubuntulinuxqa2/repos/claude_skills/plan/feature-context-migrate-milestone-skills-gh-cli.md` — primary artifact with backlog item header
- `/home/ubuntulinuxqa2/repos/claude_skills/plan/architect-migrate-milestone-skills-gh-cli.md` — primary artifact with issue reference
- `/home/ubuntulinuxqa2/repos/claude_skills/plan/P964-backlog-yaml-migration-plan.yaml` — task plan file with P{NNN} naming

**External References**:
- GitHub custom issue fields: https://docs.github.com/en/issues/planning-and-tracking-with-issues/using-issues/managing-issue-fields-in-your-organization (for approach 3c)
- GitHub API custom fields REST endpoint: `/rest/issues/issue-field-values` (approach 3c)
- Backlog item view output from fact-checker: Issue #965 "Fact-Check Summary" section with evidence of current artifact linking state
</div>

### Dependencies

<div><sub>2026-03-21T23:23:31Z</sub>

**External/Infrastructure Dependencies**:
- None identified — all systems are internal to the project

**Internal Design Dependencies** (must be resolved before implementation):
1. **Artifact taxonomy definition** — BLOCKING: Must clarify primary (feature-context, architect, task plan) vs. secondary (T0/TN, codebase analysis) vs. transient (active-task context) before producer agents are updated. This classification affects scope and guides whether SAM enforces secondary artifact discovery.

2. **Linking approach selection** — BLOCKING: User must choose between:
   - Approach 3b: Manifest in issue body (low risk, zero infrastructure, compatible with existing backlog MCP)
   - Approach 3c: GitHub custom metadata fields (medium risk, org-level setup required, GitHub API preview feature)
   - Approach 3a: Issue-number-derived paths (high risk, SAM refactor required; NOT RECOMMENDED)

   **No implementation may proceed until approach is selected.**

3. **Manifest storage interface** — Dependent on approach selection:
   - If 3b: Must define manifest format for issue body section (YAML, Markdown table, or structured text)
   - If 3c: Must define custom field schema (single field with delimited paths, or multiple fields per artifact type)

**Task Dependencies Within Implementation**:
1. **Extend backlog MCP with artifact management** — prerequisite for all producer agents
   - Define manifest format and storage location
   - Implement backlog_update() or new backlog_register_artifact() to update manifest
   - Implement manifest sync to GitHub Issue body (approach 3b) or custom fields (approach 3c)

2. **Update producer agents** — depends on backlog MCP extension
   - Feature researcher: register feature-context artifact
   - Python CLI design spec: register architect artifact
   - Swarm task planner: register task plan artifact
   - Codebase analyzer: register (or skip) codebase analysis artifact
   - T0 baseline capture: register baseline artifact (existing hook may need update)
   - TN verification gate: register verification artifact (existing hook may need update)

3. **Update orchestrator skills** — depends on backlog MCP extension
   - Add-new-feature: confirm artifact registration after agents complete
   - Implement-feature: confirm artifact manifest is available for task execution
   - Complete-implementation: retrieve full artifact manifest before quality gate phase

4. **Build artifact discovery interface** — depends on backlog MCP and producer updates
   - Extend backlog MCP with backlog_get_artifact_manifest() or equivalent
   - OR extend SAM MCP with artifact exposure in sam_status output
   - Implement artifact validation (check file existence, warn on orphaned artifacts)

5. **Update documentation** — depends on all above
   - `.claude/rules/local-workflow.md` — document artifact taxonomy and manifest structure
   - `plan-artifact-lifecycle.md` — update artifact types and lifecycle
   - `TASK_FILE_FORMAT.md` — document manifest format
   - `workflow-architecture-diagram.md` — update data flow diagram to show manifest and secondary artifacts

6. **Integration testing** — depends on all implementations
   - Verify producers register artifacts correctly
   - Verify manifest syncs to GitHub Issue (or custom fields)
   - Verify consumers can discover all artifacts via MCP
   - Verify SAM tools remain functional with P{NNN} addressing unchanged

**Optional Enhancement Dependencies**:
- Hook script validation: Extend task_status_hook.py to validate artifact manifest consistency (optional guardrail)
- Orphan detection: Create a separate job/tool to scan plan/ directory and warn about unregistered artifacts (optional guardrail)
</div>

### Effort

<div><sub>2026-03-21T23:23:47Z</sub>

**Summary**: Medium effort — scope narrowed significantly by fact-checker findings. Original premise (artifacts are standalone) refuted; actual problem is completing partial linking system.

**Estimation by Phase** (assuming approach 3b: manifest in issue body — lowest risk):

**Phase 1: Design & Specification** (0.5 days)
- Define artifact taxonomy (primary/secondary/transient) — 1-2 hours
- Confirm manifest format for issue body section — 1 hour
- Document manifest schema (YAML structure or Markdown format) — 1 hour
- Effort: ~4 hours (lowest-risk design path)

**Phase 2: Backlog MCP Extension** (1.5 days)
- Add metadata.artifacts field (or extend metadata.plan) — 2-3 hours
- Implement backlog_register_artifact() or extend backlog_update() — 3-4 hours
- Implement manifest sync to GitHub Issue body via _sync_groomed_to_github_issue() — 2-3 hours
- Testing: register and verify manifest appears in issue — 1-2 hours
- Effort: ~9-12 hours

**Phase 3: Update 6 Producer Agents** (1.5 days)
- Feature researcher: add artifact registration call — 30 min
- Python CLI design spec: add artifact registration call — 30 min
- Swarm task planner: add artifact registration call — 30 min
- Codebase analyzer: add artifact registration call (handle optional) — 30 min
- T0 baseline capture: integrate with existing hook or add registration — 1 hour
- TN verification gate: integrate with existing hook or add registration — 1 hour
- Effort: ~5 hours (mostly copy-paste with minor customization)

**Phase 4: Update 4 Orchestrator Skills** (1 day)
- Add-new-feature: confirm artifact registration after agents complete — 2-3 hours
- Implement-feature: add artifact manifest check before/after execution loop — 2-3 hours
- Start-task: verify task files are discoverable via artifact manifest — 1 hour
- Complete-implementation: retrieve manifest before quality gate phase — 1 hour
- Effort: ~6-7 hours

**Phase 5: Artifact Discovery Interface** (1 day)
- Define backlog_get_artifact_manifest() MCP tool spec — 1-2 hours
- Implement tool in backlog MCP server — 3-4 hours
- Add validation layer (file existence checks) — 2 hours
- Test discovery interface with multiple artifact types — 1-2 hours
- Effort: ~7-8 hours

**Phase 6: Documentation Updates** (1 day)
- `.claude/rules/local-workflow.md`: add artifact taxonomy section, update Phase 1 output — 2-3 hours
- `plan-artifact-lifecycle.md`: add new artifact types, update diagram — 2-3 hours
- `TASK_FILE_FORMAT.md`: document manifest format — 1 hour
- `workflow-architecture-diagram.md`: update data flow — 1-2 hours
- Effort: ~6-7 hours

**Phase 7: Integration Testing** (0.5 days)
- Test end-to-end: feature creation → artifact registration → manifest visibility → discovery via MCP — 2-3 hours
- Test SAM tools remain compatible (sam_status, sam_ready, sam_read) — 1 hour
- Effort: ~3-4 hours

**Total Effort by Approach**:
- Approach 3b (manifest in issue body): **~45-55 hours** (5-7 days at 8 hours/day)
- Approach 3a (issue-number-derived paths): **~80-100 hours** (10-12 days) — SAM refactor adds 30-40 hours
- Approach 3c (GitHub custom metadata): **~60-70 hours** (7-9 days) — GitHub API integration adds 15-20 hours

**Critical Path** (if parallelized):
- Design & artifact taxonomy: 0.5 days (blocking)
- Backlog MCP extension: 1.5 days (blocking)
- Producer agents + Orchestrator skills: can run in parallel after backlog MCP is complete (2-3 days)
- Discovery interface: 1 day
- Documentation + testing: 1.5 days
- **Parallelized critical path: ~6-7 days** (vs. 5-7 days serialized — low parallelism benefit due to dependency chain)

**Risk Adjustment**:
- Approach 3b selected: **Medium Risk** — scope is clear, all systems known, backlog MCP already handles syncing
- Approach 3c selected: **Medium-High Risk** — GitHub API preview feature may change; requires org-level setup communication
- Approach 3a selected: **High Risk** — SAM refactor introduces breaking changes; not recommended

**Effort Recommendation**:
Proceed with approach 3b (manifest in issue body). Estimated effort: **5-7 days for complete implementation and documentation**. User decision on approach required before starting.
</div>



## Impact Radius

### Code — Producers (create plan artifacts)
- `plugins/development-harness/agents/feature-researcher.md` — produces feature-context-{slug}.md; output path would change
- `plugins/python3-development/agents/python-cli-design-spec.md` — produces architect-{slug}.md; output path would change
- `plugins/development-harness/agents/swarm-task-planner.md` — produces tasks-{N}-{slug}.md (or tasks-{slug}/ directory); output path would change
- `plugins/development-harness/agents/codebase-analyzer.md` — produces plan/codebase/{FOCUS}.md (optional); output path would change

### Code — Consumers (read plan artifacts)
- `packages/sam_schema/` — SAM MCP server; parses plan file paths, addresses plans as P{N}
- `packages/backlog_core/` — backlog MCP server; stores plan field per item, syncs to GitHub
- `plugins/development-harness/skills/start-task/SKILL.md` — reads task files by path
- `plugins/development-harness/skills/complete-implementation/SKILL.md` — reads task files for quality gates
- `plugins/development-harness/skills/implementation-manager/scripts/task_status_hook.py` — reads active-task context, updates task files

### Code — Other References
- `plugins/development-harness/skills/work-backlog-item/SKILL.md` — links plan path via backlog_update(plan=...)
- `plugins/development-harness/skills/add-new-feature/SKILL.md` — orchestrates artifact creation, names output paths
- `plugins/development-harness/skills/implement-feature/SKILL.md` — receives task file path for execution loop
- `plugins/development-harness/skills/work-milestone/SKILL.md` — dispatches worktree agents with plan references

### Documentation (will become stale)
- `.claude/rules/local-workflow.md` — documents artifact naming convention (plan/feature-context-{slug}.md, plan/architect-{slug}.md, plan/tasks-{N}-{slug}.md)
- `plugins/development-harness/docs/plan-artifact-lifecycle.md` — mutability policy for plan artifacts
- `plugins/development-harness/docs/workflow-architecture-diagram.md` — data flow showing plan/ paths
- `plugins/development-harness/docs/TASK_FILE_FORMAT.md` — task file format documentation

### Configuration / CI
- None identified — plan/ is not referenced in CI workflows

### Agent Instructions (instruct AI to use current interface)
- `plugins/development-harness/agents/feature-researcher.md` — instructs writing to plan/feature-context-{slug}.md
- `plugins/development-harness/agents/swarm-task-planner.md` — instructs writing to plan/tasks-{N}-{slug}.md
- `plugins/python3-development/agents/python-cli-design-spec.md` — instructs writing to plan/architect-{slug}.md
- `plugins/development-harness/agents/t0-baseline-capture.md` — reads plan/T0-baseline-{slug}.yaml
- `plugins/development-harness/agents/tn-verification-gate.md` — reads plan/TN-verification-{slug}.yaml

### Systems Inventory
| System | Role | Connection |
|--------|------|------------|
| SAM MCP server (sam_schema/) | Consumer | Parses plan paths, provides P{N} addressing |
| Backlog MCP server (backlog_core/) | Consumer | Stores plan field, syncs to GitHub |
| add-new-feature skill | Orchestrator | Names and creates all artifact paths |
| work-backlog-item skill | Orchestrator | Links plan to backlog item via MCP |
| implement-feature skill | Orchestrator | Receives task file path for execution |
| start-task skill | Consumer | Reads specific task from plan file |
| complete-implementation skill | Consumer | Reads task file for quality gates |
| work-milestone skill | Orchestrator | Dispatches agents with plan references |
| task_status_hook.py | Consumer | Updates task status in plan files |
| feature-researcher agent | Producer | Writes feature-context-{slug}.md |
| python-cli-design-spec agent | Producer | Writes architect-{slug}.md |
| swarm-task-planner agent | Producer | Writes tasks-{N}-{slug}.md |
| codebase-analyzer agent | Producer | Writes plan/codebase/{FOCUS}.md |
| t0-baseline-capture agent | Producer/Consumer | Writes T0-baseline-{slug}.yaml |
| tn-verification-gate agent | Producer/Consumer | Writes TN-verification-{slug}.yaml |
| local-workflow.md rule | Documentation | Describes naming convention |
| plan-artifact-lifecycle.md | Documentation | Mutability policy |

### Ecosystem Completeness Checklist
- [ ] Every code producer updated or verified compatible
- [ ] Every code consumer migrated to new interface
- [ ] Every stale document updated
- [ ] Every agent instruction updated
- [ ] Old interface deprecated or removed (if replacing)
- [ ] CI/config files updated and validated
</div>


## Issue Classification

**Type**: Missing-Guardrail with Unbounded-Design Characteristics

**Reasoning**:

This is not a defect (the system works) nor a recurring-pattern (users haven't reported data loss). It is a **missing guardrail** because:

- Plan artifacts exist as standalone files with no enforced connection to their parent GitHub Issue
- No validation prevents orphaning artifacts if filenames change or files are deleted
- No mechanism ensures discovery — a developer must know the naming convention (plan/feature-context-{slug}.md) to find artifacts tied to an issue

The issue also has **unbounded-design characteristics**:

- Three candidate linking approaches proposed (path-derived, manifest, metadata) without a specified winner
- "All related artifacts" undefined — does it include T0/TN verification artifacts? Codebase analysis snapshots? Documentation drift audit outputs?
- Integration points unclear: should SAM generate issue-aware paths? Should backlog MCP enforce artifact existence checks? Should add-new-feature skill create issue-aware directory structure?

## Root-Cause Analysis

**The canonical issue lifecycle vision** (from project MEMORY) expects GitHub Issues to be the single entry point to all work artifacts (sub-issues, plans, tasks, research). Currently:

- **Backlog items** have a `plan` field storing one file path
- **Plan artifacts** are stored by naming convention in plan/ directory
- **Sub-artifacts** (T0 baseline, TN verification, codebase analysis) are scattered across plan/ with no link back to the parent issue

**Missing guardrail 1**: No validation that artifacts named in the `plan` field actually exist, preventing silent linkage loss.

**Missing guardrail 2**: No directory structure or metadata field connecting T0/TN/analysis artifacts to the issue number, making them undiscoverable if the naming convention is forgotten.

**Missing guardrail 3**: No schema for what constitutes "all related artifacts" — the proposal conflates primary artifacts (architect, feature-context, tasks) with secondary outputs (baselines, verification, analysis).

## Decision Gate

Before implementation: specify which linking approach is canonical and define the artifact taxonomy (primary vs. secondary vs. transient). This determines whether backlog MCP or SAM CLI should enforce the structure.
</div>

## Fact-Check

<div><sub>2026-03-21T23:18:48Z</sub>

## Fact-Check Summary

**Checked**: 2026-03-21

### Claim 1: "Plan artifacts are standalone files in plan/ with no formal link to GitHub Issue structure"

**Status**: REFUTED

**Evidence**:
- The backlog MCP tool `backlog_update()` already supports a `plan` parameter that stores plan file paths in the `metadata.plan` field of backlog items
- Current usage: 10+ P1 backlog items already have plans linked via this field (verified via `backlog_list` output, e.g., issue #927 with `plan: plan/P784-integration-branch-management-followup-2.yaml`)
- Plan artifacts explicitly reference their parent issues in their headers:
  - Feature context (`plan/feature-context-{slug}.md`): includes `**Backlog item**: #{issue_number}` at line 3
  - Architecture spec (`plan/architect-{slug}.md`): includes `**Backlog item**: #{issue_number}` at line 3
- Source: `/home/ubuntulinuxqa2/repos/claude_skills/plan/feature-context-migrate-milestone-skills-gh-cli.md` (line 3), `/home/ubuntulinuxqa2/repos/claude_skills/plan/architect-migrate-milestone-skills-gh-cli.md` (line 3)

**Conclusion**: Plan artifacts are NOT standalone — they have formal links to GitHub Issues via both the backlog MCP metadata field and explicit header references.

---

### Claim 2: "feature-context-{slug}.md and architect-{slug}.md are the plan artifact types"

**Status**: VERIFIED (incomplete list)

**Evidence**:
- Confirmed artifact types from `/home/ubuntulinuxqa2/repos/claude_skills/plugins/development-harness/skills/add-new-feature/SKILL.md` (lines 16-19):
  1. `plan/feature-context-{slug}.md` (discovery)
  2. `plan/codebase/{FOCUS}.md` (optional codebase analysis)
  3. `plan/architect-{slug}.md` (architecture spec)
  4. `plan/P{NNN}-{slug}.yaml` (executable task plan with agents and verification)

**Conclusion**: The backlog item only listed 2 of 4 artifact types. Additionally, per `.claude/rules/local-workflow.md`, task plans can be organized as either a single file (`plan/tasks-{N}-{slug}.md`) or a directory with per-task files (`plan/tasks-{slug}/T*.md`).

---

### Claim 3: Three proposed approaches are feasible

**3a. Storing plan artifacts under a path derived from the issue number**

**Status**: FEASIBLE BUT BREAKS EXISTING WORKFLOWS

**Analysis**: Current SAM convention uses slug-based naming (e.g., `architect-migrate-milestone-skills-gh-cli.md`). Two files already use issue numbers:
- `/home/ubuntulinuxqa2/repos/claude_skills/plan/CONTEXT_MANIFEST-P970.md`
- `/home/ubuntulinuxqa2/repos/claude_skills/plan/integration-verification-P698.md`

However, switching ALL artifacts to issue-number-derived paths would break:
- Skill references to artifact paths in delegation prompts (e.g., `/implement-feature` resolves task file paths by slug)
- Agent specs that generate artifacts by slug (e.g., swarm-task-planner generates `plan/P{NNN}-{slug}.yaml`)
- The current `sam_status`, `sam_ready`, and `sam_read` MCP tools expect P{NNN} plan identifiers

**Conclusion**: Feasible only if coupled with a major refactor of SAM plan addressing — high risk.

---

**3b. Adding artifact manifest to the issue body**

**Status**: FEASIBLE AND ALREADY PARTIALLY IMPLEMENTED

**Evidence**:
- The backlog MCP system writes full GitHub Issue bodies including structured sections via `_sync_groomed_to_github_issue()`
- The `context-refinement` agent (Phase 6 of `/complete-implementation`) already updates issue bodies with a `## Context Manifest` section
- Source: `.claude/rules/local-workflow.md` lines 104-110

**Conclusion**: Feasible. Could be extended to include artifact manifest as a dedicated section in the issue body.

---

**3c. Attaching plan file paths as issue metadata**

**Status**: FEASIBLE — GitHub API supports custom issue fields

**Evidence**:
- GitHub issue fields (custom metadata) are in public preview as of 2026-03-12 (GitHub Changelog)
- API support: REST and GraphQL endpoints available at `/rest/issues/issue-field-values`
- Capability: Fields can be single-select text or free-form text; URLs are auto-detected
- Documentation: [GitHub Docs - Managing issue fields in your organization](https://docs.github.com/en/issues/planning-and-tracking-with-issues/using-issues/managing-issue-fields-in-your-organization)
- Constraint: Limit of 25 custom fields per organization
- Status: Feature is in public preview and subject to change; requires org-level setup

**Conclusion**: Feasible. Requires opt-in at organization level and introduces a GitHub API dependency for metadata reads (not currently used in backlog MCP).

---

### Claim 4: "The issue is the single entry point for all related artifacts"

**Status**: PARTIALLY TRUE (entry point exists but is hybrid)

**Current state**:
- GitHub Issues **are** the source of truth for backlog item metadata (issue lifecycle vision in memory)
- Backlog items link to plans via the `metadata.plan` field → users can navigate from issue to plan
- Workflows start from the backlog item (via `/dh:work-backlog-item` or backlog list) → users reference issue numbers
- Skills accept either task file paths OR feature slugs → no requirement to start from the issue

**Entry point architecture**:
1. User invokes `/add-new-feature` (skill entry point, not issue-based)
2. Skills generate plan artifacts and store plan path in backlog via `backlog_update(plan="...")`
3. User invokes `/implement-feature` (takes task file path or slug, not issue number)
4. Task execution queries ready tasks via `backlog_get_ready_sam_tasks(parent_issue_number=N)` IF issue number is known

**Conclusion**: Issues serve as a **coordination hub** (source of truth for metadata, link to plans), but are NOT the exclusive entry point. The workflow permits skill-first entry (path 1) and backlog-first entry (path 4). A stricter single-entry-point design would require all workflows to start from the issue.

---

## Summary Table

| Claim | Verified? | Status | Key Finding |
|-------|-----------|--------|-------------|
| Standalone artifacts with no links | REFUTED | ✗ | Links already exist via backlog MCP and artifact headers |
| featurectx + architect only artifact types | VERIFIED (incomplete) | ⚠ | Item omitted codebase analysis and task plan artifacts |
| Path-derived approach is feasible | FEASIBLE (high risk) | ⚠ | Requires SAM refactor; breaks plan addressing convention |
| Manifest in issue body is feasible | FEASIBLE (implemented) | ✓ | Already done for Context Manifest; can extend |
| Custom metadata is feasible | FEASIBLE (preview) | ✓ | GitHub fields in public preview; org-level setup required |
| Issue as single entry point | PARTIALLY TRUE | ⚠ | Issues are hub, not exclusive entry point; workflows permit multiple entry paths |


</div>