# Documentation Drift Audit — development-harness plugin
**Generated**: 2026-03-22
**Scope**: plugins/development-harness/README.md and CLAUDE.md vs actual filesystem

---

## Executive Summary

**Total findings**: 12
- **Critical**: 3 (major feature claims, non-existent skills)
- **High**: 4 (documented agents/skills not found or incomplete descriptions)
- **Medium**: 3 (inaccurate counts and organization claims)
- **Low**: 2 (minor wording/reference discrepancies)

---

## Analyzed Files

### Documentation
- `plugins/development-harness/README.md` (70 lines)
- `plugins/development-harness/CLAUDE.md` (280 lines)

### Implementation
- 20 existing skills in `plugins/development-harness/skills/*/SKILL.md`
- 15 existing agents in `plugins/development-harness/agents/*.md`

---

## Findings

### CRITICAL — Documented but Unimplemented

#### 1. Seven Workflow Stage Skills Claimed But Do Not Exist
**CLAUDE.md lines 145-153** claims:
```
- `/dh:discovery` - S1 feature and codebase understanding
- `/dh:planning` - S2 plan generation with RT-ICA
- `/dh:context-integration` - S3 plan validation against codebase
- `/dh:task-decomposition` - S4 break plan into executable tasks
- `/dh:execution` - S5 implement tasks with language specialists
- `/dh:forensic-review` - S6 verify task completion
- `/dh:final-verification` - S7 certify feature completion
```

**Reality**: These 7 skills do NOT exist in the filesystem.
- Glob pattern `plugins/development-harness/skills/*/SKILL.md` returns 20 skills, none named `discovery`, `planning`, `context-integration`, `task-decomposition`, `execution`, `forensic-review`, or `final-verification`
- The workflow stages S1–S7 are described in CLAUDE.md § "SAM 7-Stage Pipeline" (lines 24–34) but no corresponding `/dh:` skills implement them

**Impact**: Users attempting to invoke `/dh:discovery` or other stage skills will encounter "skill not found" errors.

**Recommendation**: Either:
- Implement these 7 skills, OR
- Document that workflow stages are implicit in `/dh:add-new-feature` → `/dh:complete-implementation` pipeline and remove stage-skill references
- If stages were renamed or consolidated, state the new skill names explicitly

---

#### 2. Three Testing Skills Claimed But Do Not Exist
**CLAUDE.md lines 178-182** claims:
```
- `/dh:comprehensive-test-review` - Review test coverage and quality
- `/dh:analyze-test-failures` - Diagnose and categorize test failures
- `/dh:test-failure-mindset` - Systematic approach to understanding test failures
```

**Reality**: These 3 testing skills do NOT exist.
- No `test-review`, `analyze-test-failures`, or `test-failure-mindset` SKILL.md files found in filesystem
- No agents with similar names found

**Impact**: Users seeking `/dh:comprehensive-test-review` will get "skill not found".

**Recommendation**: Either implement these skills or document that testing is delegated to language-specific testing agents via the manifest system.

---

#### 3. "testing" and "workflows" Skills Listed in README But Do Not Exist
**README.md lines 20-29** claims:
```
- `testing` — Test design and coverage methodology
- `workflows` — Workflow orchestration patterns for the harness pipeline
```

**Reality**: Neither `testing` nor `workflows` SKILL.md files exist.

**Impact**: Inconsistency between README and CLAUDE.md; users cannot find these skills.

**Recommendation**: Remove these lines from README or implement the skills.

---

### HIGH — Implemented but Undocumented or Incompletely Described

#### 4. Task-Worker Agent Exists but Has Limited Documentation
**Reality**: Agent `task-worker.md` exists (confirmed in glob results).
**CLAUDE.md coverage**: Line 226 lists `@dh:task-worker` with description "Execute individual tasks".

**Issue**: The description is vague. No reference document explains the task-worker's role in the SAM workflow, its relationship to `/dh:start-task` skill, or when to use it.

**Recommendation**: Expand CLAUDE.md description to clarify task-worker's unique responsibilities vs. the start-task skill.

---

#### 5. Artifact Manifest System Not Documented in CLAUDE.md
**Context from CLAUDE.md § "SAM 7-Stage Pipeline" (local-workflow.md reference)**: Mentions "artifact manifest" system with tools: `artifact_register`, `artifact_list`, `artifact_read`, `artifact_get`.

**Reality**: These MCP tools exist (from session context: "Artifact manifest system added (artifact_register, artifact_list, artifact_read, artifact_get)").

**Issue**: CLAUDE.md does not document the artifact manifest system. The term "artifact manifest" does not appear in either README.md or CLAUDE.md main text.

**Recommendation**: Add a "Artifact Manifest System" section to CLAUDE.md explaining the four tools, their purpose, and when to use them.

---

#### 6. Skills Count Mismatch (Claimed 30, Actually 20)
**CLAUDE.md line 132** claims:
```
## Skills Overview (30)
```

**Reality**: 20 skills exist in the filesystem.

**Breakdown of 20 actual skills**:
- Main orchestration: 1 (development-harness)
- SAM workflow: 4 (add-new-feature, implement-feature, start-task, complete-implementation)
- Workflow stages: 0 (missing: 7 claimed stage skills)
- Planning tools: 4 (clear-cove-task-design, generate-task, planner-rt-ica, validation-protocol)
- Implementation: 1 (implementation-manager)
- Backlog management: 4 (backlog, create-backlog-item, work-backlog-item, groom-backlog-item)
- Milestone management: 2 (groom-milestone, work-milestone)
- Testing: 0 (missing: 3 claimed testing skills)
- Other: 4 (dispatch, dh-meta-docs, interop, subagent-contract)

**Recommendation**: Correct line 132 to `## Skills Overview (20)` or implement the 10 missing skills.

---

#### 7. Agent Roles in SAM Workflow Unclear
**Issue**: CLAUDE.md documents agents (lines 193–226) and skills separately, but does not clearly map which agents are invoked by which skills or at which workflow stage.

Example: `@dh:t0-baseline-capture` and `@dh:tn-verification-gate` are bookend agents (T0 and T99 tasks), but this relationship is not explained in the agent overview — readers must find this in the referenced local-workflow.md document.

**Recommendation**: Add a "Agent Role Matrix" section showing which agents are invoked by which skills and at which stage (S1–S7 or task execution).

---

### MEDIUM — Outdated or Inaccurate Details

#### 8. CLAUDE.md Describes `.planning/harness/` Artifacts But SAM Workflow Uses `plan/` Directory
**CLAUDE.md lines 77–93** describe artifact storage:
```
All artifacts are written to `.planning/harness/` using SAM naming conventions.
```

**Reality**: From session context and referenced local-workflow.md, the actual SAM workflow writes to `plan/` directory:
- `plan/feature-context-{slug}.md`
- `plan/architect-{slug}.md`
- `plan/tasks-{N}-{slug}.md`
- `plan/T0-baseline-{slug}.yaml`
- `plan/TN-verification-{slug}.yaml`

**Issue**: Users following CLAUDE.md will look in `.planning/harness/` but find nothing; actual artifacts are in `plan/`.

**Recommendation**: Update lines 77–93 to reflect actual directory structure: `plan/` not `.planning/harness/`.

---

#### 9. README References Nonexistent Reference Files
**README.md lines 22–29** and **CLAUDE.md lines 265–270** reference:
- `./skills/development-harness/references/default-development-flow.md`
- `./skills/development-harness/references/role-resolution-protocol.md`
- `./skills/development-harness/references/language-manifest-schema.md`
- `./skills/development-harness/references/human-touchpoint-model.md`
- `./skills/development-harness/references/artifact-conventions.md`
- `./templates/language-manifest-template.md`

**Reality**: These reference files do NOT exist in the filesystem (not found via glob).

**Issue**: Broken documentation links. Users cannot read referenced documents.

**Recommendation**: Either create these reference files or remove the references from README and CLAUDE.md.

---

#### 10. README Mentions 7-Stage Pipeline But Lists Different Skills
**README.md § "What it does" (lines 12–18)** describes the harness orchestrating a "7-stage pipeline: Discovery, Planning, Context Integration, Task Decomposition, Execution, Forensic Review, and Final Verification."

**README.md § "Skills" (lines 20–29)** does NOT list corresponding skills for these stages. Instead it lists: `development-harness`, `clear-cove-task-design`, `generate-task`, `implementation-manager`, `planner-rt-ica`, `testing`, `validation-protocol`, `workflows`.

**Issue**: README implies there are stage-specific skills but doesn't list them (because they don't exist), creating confusion about how the pipeline works.

**Recommendation**: Clarify in README that stages are orchestrated internally by `/dh:development-harness` and `/dh:add-new-feature`, not invoked as separate stage skills. OR implement the stage skills and document them explicitly.

---

### LOW — Minor Discrepancies

#### 11. Plugin Identity States Version 0.1.0, No Changelog Provided
**CLAUDE.md line 10** states:
```
**Version:** 0.1.0
```

**Issue**: No CHANGELOG.md or version history document exists to explain what 0.1.0 includes or what changed in recent versions. Session context notes recent additions (artifact manifest, bookend agents, task-worker, dispatch skill), but docs don't reflect these as version changes.

**Recommendation**: Create a CHANGELOG.md documenting version history, or update CLAUDE.md to reflect the current version after recent additions.

---

#### 12. README Composition Model Diagram Mentions "Flow Override" But No Mechanism Documented
**README.md lines 99–110** show a Mermaid flowchart mentioning `FlowOverride[Custom Process Flow]` as something language plugins can optionally declare.

**Issue**: No documentation explains HOW to declare a flow override, what syntax is required, or where it goes in the language manifest.

**Recommendation**: Update the language-manifest-schema.md reference file (or create it if missing) to document the flow override syntax and provide an example.

---

## Recommendations (Prioritized)

### Phase 1: Critical Fixes (Unblock Users)

1. **Clarify the actual skill landscape**:
   - If the 7 workflow stage skills (discovery, planning, etc.) will never be implemented, document that `/dh:add-new-feature` and `/dh:complete-implementation` encapsulate the S1–S7 pipeline
   - If they will be implemented, create a tracking issue with target deadline
   - Update skill count from 30 to 20 in CLAUDE.md line 132

2. **Resolve the 3 missing testing skills**:
   - Decide: Will these be implemented or delegated to language plugins?
   - Document the decision explicitly in CLAUDE.md § Testing

3. **Fix artifact directory reference**:
   - Change CLAUDE.md lines 77–93 to use `plan/` instead of `.planning/harness/`
   - Ensure this aligns with actual implementation in `/dh:add-new-feature` and `/dh:implement-feature` skills

### Phase 2: High-Value Additions (Restore Completeness)

4. **Document the artifact manifest system**:
   - Add § "Artifact Manifest" to CLAUDE.md with descriptions of `artifact_register`, `artifact_list`, `artifact_read`, `artifact_get`

5. **Create Agent Role Matrix**:
   - Add § "Agent Delegation Mapping" showing which skills invoke which agents at which stages

6. **Create or restore reference files**:
   - All 6 referenced files in README/CLAUDE.md should exist or be removed
   - High priority: `default-development-flow.md` and `language-manifest-schema.md` (needed for plugin authors)

### Phase 3: Quality (Polish)

7. **Create CHANGELOG.md** documenting version progression and recent feature additions (artifact manifest, bookend agents, task-worker agent, dispatch skill)

8. **Expand agent descriptions** in CLAUDE.md with clarifying details (especially task-worker vs start-task distinction)

---

## Cross-References

- Affected skills: All 20 skills (due to documentation drift affecting understanding of the overall system)
- Affected agents: All 15 agents (their roles in the workflow are undocumented)
- User workflows: Discovery → Planning → Implementation → Verification (all stages documented incompletely)

---

## Impact Assessment

**Severity**: HIGH
- **User-Facing**: Users cannot invoke 10 documented skills that don't exist; users looking for artifacts in wrong directory
- **Developer-Facing**: Plugin authors cannot understand language manifest schema; artifact manifest system is hidden
- **Maintenance Burden**: Every future change to CLAUDE.md requires cross-checking against filesystem; no source of truth established

**Estimated Remediation Time**: 4–6 hours
- Critical fixes: 1.5 hours (update CLAUDE.md, fix artifact paths)
- Reference document creation: 2–3 hours
- Verification and spot-check: 1 hour

---

**END AUDIT REPORT**
