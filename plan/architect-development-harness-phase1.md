# Architecture Spec: Development Harness Phase 1 Completion

## Document Metadata

- **Type**: Documentation and configuration architecture (NOT a Python CLI project)
- **Feature Context**: [./feature-context-development-harness-phase1.md](./feature-context-development-harness-phase1.md)
- **Codebase Analysis**: [./codebase/DEVELOPMENT-HARNESS-ARCHITECTURE.md](./codebase/DEVELOPMENT-HARNESS-ARCHITECTURE.md)

---

## Resolved Design Decisions

| ID | Decision | Resolution |
|----|----------|------------|
| Q1 | Relationship between workflow skill names and manifest stage_skills keys | Two-layer naming is INTENTIONAL. Workflow skill directory names = bare stage names (cross-cutting, input 2 of generic-stage-agent). Manifest stage_skills keys = domain-prefixed names (language-specific, input 3). These are different layers. |
| Q2 | Valid domain prefixes | CLOSED LIST. Initial: `planning`, `design`, `implementation`, `testing`, `review`. New domains require explicit addition to the list. |
| Q3 | PoC guide format | EXECUTABLE. Shell commands with expected output the reader can run. |
| Q4 | Taxonomy document location | `plugins/development-harness/skills/development-harness/references/sdlc-stage-taxonomy.md` |

---

## Deliverable 1: SDLC Stage Naming Taxonomy Document

### File

`plugins/development-harness/skills/development-harness/references/sdlc-stage-taxonomy.md`

New file. No existing file to modify.

### Document Structure

The taxonomy document defines two naming layers, the closed domain list, standards mappings, and naming rules.

#### Section 1: Layer 1 -- Cross-Cutting Stage Names

Defines the 7 bare workflow skill names used as directory names under `plugins/development-harness/skills/workflows/`. These are the names passed as **input 2** (cross-cutting stage skill) to the generic stage agent.

**Fields per stage entry:**

```yaml
stage_id: S1  # sequential identifier
name: discovery  # bare name = directory name
skill_activation: /development-harness:discovery  # how to load it
purpose: <one-sentence description>
inputs: <what this stage receives>
outputs: <artifact it produces>
artifact_path: .planning/harness/DISCOVERY.md
```

**The 7 entries:**

| stage_id | name | artifact_path |
|----------|------|---------------|
| S1 | `discovery` | `.planning/harness/DISCOVERY.md` |
| S2 | `planning` | `.planning/harness/PLAN.md` |
| S3 | `context-integration` | `.planning/harness/PLAN.md` (amends S2) |
| S4 | `task-decomposition` | `.planning/harness/tasks/TASK-{NNN}.md` |
| S5 | `execution` | `.planning/harness/executions/EXECUTION-{NNN}.md` |
| S6 | `forensic-review` | `.planning/harness/reviews/REVIEW-{NNN}.md` |
| S7 | `final-verification` | `.planning/harness/VERIFICATION.md` |

#### Section 2: Layer 2 -- Domain-Prefixed Skill Names

Defines the `{domain}-{sdlc-stage}` naming pattern used in language manifest `stage_skills` keys. These are the names passed as **input 3** (domain skills) to the generic stage agent.

**Closed domain list:**

| Domain | Covers stages | Rationale |
|--------|--------------|-----------|
| `planning` | S2 planning, S3 context-integration, S4 task-decomposition | Pre-implementation planning activities |
| `design` | S1 discovery, S2 planning | Architectural and system design |
| `implementation` | S5 execution | Code writing and feature implementation |
| `testing` | S6 forensic-review, S7 final-verification | Verification and validation |
| `review` | S6 forensic-review | Code review and quality assessment |

**Pattern definition:**

```text
{domain}-{sdlc-stage}
```

Where:
- `{domain}` is one of the 5 closed-list values above
- `{sdlc-stage}` is one of the 7 bare stage names from Layer 1
- The combined key appears in the manifest `stage_skills` section
- Each combined key maps to a list of skill names to load

**Examples from the python3 manifest (validated against this pattern):**

| Manifest key | Domain | SDLC Stage | Valid? |
|-------------|--------|------------|--------|
| `discovery` | (none) | `discovery` | Yes -- bare stage name is valid when no domain specialization needed |
| `design` | (none) | (none) | Yes -- bare domain name is valid for single-stage domains |
| `planning-context-integration` | `planning` | `context-integration` | Yes |
| `planning-task-decomposition` | `planning` | `task-decomposition` | Yes |
| `implementation` | (none) | (none) | Yes -- bare domain name |
| `testing-forensic-review` | `testing` | `forensic-review` | Yes |
| `testing-verification` | `testing` | `final-verification` | Partial -- should be `testing-final-verification` per naming rules |

**Rules for when to use bare vs. prefixed names:**

1. **Bare stage name** (e.g., `discovery`): Use when the domain skill applies to exactly one stage and that stage name alone is unambiguous
2. **Bare domain name** (e.g., `implementation`): Use when the domain covers exactly one stage in the manifest
3. **Domain-prefixed** (e.g., `planning-context-integration`): Required when a domain covers multiple stages in the same manifest, to disambiguate which stage the skill list applies to
4. **Adding a new domain**: Requires adding the domain to the closed list in this taxonomy document and updating the manifest schema validation

#### Section 3: IEEE 12207 / ISO 15288 / SAFe Mappings

Maps each of the 7 bare stage names to the closest equivalent in three recognized SDLC standards.

**Fields per mapping entry:**

| Stage | IEEE 12207 Process | ISO 15288 Process | SAFe Practice |
|-------|-------------------|-------------------|---------------|
| `discovery` | Stakeholder Needs Definition (6.4.1) | Stakeholder Needs and Requirements Definition (6.4.1) | Explore / Define |
| `planning` | System Requirements Analysis (6.4.2) | System Requirements Definition (6.4.2) | Plan / PI Planning |
| `context-integration` | Architecture Definition (6.4.3) | Architecture Definition (6.4.3) | Architect / Enable |
| `task-decomposition` | Implementation Planning (7.2.1) | Project Planning (6.3.1) | Plan / Iteration Planning |
| `execution` | Software Construction (7.1.5) | Implementation (6.4.7) | Implement / Build |
| `forensic-review` | Software Verification (7.2.4) | Verification (6.4.6) | Inspect / Review |
| `final-verification` | Software Validation (7.2.5) | Validation (6.4.8) | Demonstrate / Inspect & Adapt |

**Note**: These mappings are approximate. The SAM pipeline stages are composite activities that may span multiple processes in the formal standards. The mapping establishes terminology correspondence, not process equivalence.

#### Section 4: Naming Convention Rules

A numbered list of rules that consumers use to determine correct naming:

1. Workflow skill directories under `plugins/development-harness/skills/workflows/` use **bare stage names only** (Layer 1)
2. Language manifest `stage_skills` keys use **domain-prefixed names** when disambiguating, **bare names** when unambiguous (Layer 2)
3. The domain prefix must come from the **closed domain list** (Section 2)
4. Domain-prefixed keys use a single hyphen separator: `{domain}-{sdlc-stage}`
5. YAML keys in manifests use hyphens (not underscores): `planning-context-integration` not `planning_context_integration`
6. Skill names referenced in `stage_skills` values follow `{language}-{purpose}` convention (e.g., `python3-implementation`)
7. When extending a manifest via `extends:`, override keys must use the same naming convention as the base manifest
8. The generic stage agent resolves `stage_skills` keys by exact string match against the stage identifier passed in the dispatch prompt

---

## Deliverable 2: Naming Audit and Required Updates

### Files Under Audit

#### File 1: `plugins/python3-development/manifests/python3/language-manifest.yaml`

Current `stage_skills` keys and their audit status against the taxonomy:

| Current Key | Pattern Match | Audit Result |
|-------------|--------------|--------------|
| `discovery` | Bare stage name | COMPLIANT -- unambiguous single-stage |
| `design` | Bare domain name | COMPLIANT -- domain covers one stage in this manifest |
| `planning-context-integration` | `{domain}-{sdlc-stage}` | COMPLIANT |
| `planning-task-decomposition` | `{domain}-{sdlc-stage}` | COMPLIANT |
| `implementation` | Bare domain name | COMPLIANT -- domain covers one stage |
| `testing-forensic-review` | `{domain}-{sdlc-stage}` | COMPLIANT |
| `testing-verification` | `{domain}-{sdlc-stage}` | NEEDS REVIEW -- the stage name is `final-verification`, not `verification`. Key should be `testing-final-verification` if strict compliance is required. Alternatively, document `verification` as an accepted abbreviation. |

**Required action**: Decide whether `testing-verification` is an accepted abbreviation of `testing-final-verification` or a naming bug. If abbreviation: document in taxonomy Section 4 as an exception. If bug: rename key to `testing-final-verification` and update `dispatch_helper.py` stage resolution logic.

#### File 2: `plugins/python3-development/manifests/python3-cli/language-manifest.yaml`

Current `stage_skills` keys:

| Current Key | Pattern Match | Audit Result |
|-------------|--------------|--------------|
| `design` | Bare domain name | COMPLIANT -- this is an override of the base manifest's `design` key |
| `implementation` | Bare domain name | COMPLIANT -- override of base manifest's `implementation` key |

**Required action**: None. The non-prefixed keys are intentional overrides via the `extends: python3-development:python3` mechanism. Override keys must match the base manifest's key names exactly, which they do.

#### File 3: `plugins/development-harness/skills/development-harness/references/language-manifest-schema.md`

**Current state**: The schema document describes a markdown-based manifest format. It does not reference the taxonomy document or the `{domain}-{sdlc-stage}` naming convention. The `stage_skills` section (Section 4 of the schema doc, titled "Conventions") does not exist -- the schema has no `stage_skills` documentation at all.

**Required changes:**

1. Add a new section "Stage Skills (Optional)" between the existing "Project Detection" and "Conventions" sections
2. The new section must:
   - Reference the taxonomy document: `[SDLC Stage Naming Taxonomy](./sdlc-stage-taxonomy.md)`
   - Define the `stage_skills` YAML format (map of string keys to string arrays)
   - State that keys must follow the naming convention defined in the taxonomy
   - Include the python3 manifest's `stage_skills` block as a worked example
3. Add a "Sources" entry linking to the taxonomy document

#### File 4: `plugins/development-harness/agents/generic-stage-agent.md`

**Current state**: The agent document references "Cross-Cutting Stage Skill" (input 2) and "Domain Skills" (input 3) but does not name the stage naming convention or taxonomy document.

**Required changes:**

1. In the "Inputs You Receive" section, item 2 ("Cross-Cutting Stage Skill"), add a parenthetical: `(bare stage name from the SDLC taxonomy Layer 1)`
2. In item 3 ("Domain Skills"), add a parenthetical: `(domain-prefixed names from the SDLC taxonomy Layer 2, resolved via manifest stage_skills)`
3. No structural changes needed -- the agent's execution protocol is already correct

---

## Deliverable 3: Executable PoC Validation Guide

### File

`plugins/development-harness/docs/poc-validation-guide.md`

New file in the existing `docs/` directory.

### Document Structure

This is a user-facing document (not agent-facing). The reader is a contributor who wants to validate the harness works end-to-end. All commands are runnable from the repository root.

**Worked example**: Python3 language manifest + the `planning` stage (S2).

#### Section 1: Prerequisites

List what must be in place before running the PoC:

- `uv` installed (v0.10.0+)
- Repository cloned with plugins installed
- A Python project directory with `pyproject.toml` present (the repo itself qualifies)

#### Section 2: Discover the Manifest

**Command:**

```bash
uv run python plugins/development-harness/scripts/manifest_discovery.py \
  --project-dir . \
  --format json
```

**Expected output structure** (JSON):

```json
{
  "selected": {
    "name": "python3",
    "language": "python",
    "path": "plugins/python3-development/manifests/python3/language-manifest.yaml",
    "priority": "PLUGIN",
    "dependency_score": 0
  },
  "candidates": [
    {"name": "python3", "...": "..."},
    {"name": "python3-cli", "...": "..."}
  ]
}
```

**What to verify**: The `selected` manifest is `python3` (or `python3-cli` if `typer` is in project dependencies). The `priority` is `PLUGIN` (Level 4) since the manifest lives in the plugins directory.

#### Section 3: Resolve Roles

**Command:**

```bash
uv run python plugins/development-harness/scripts/manifest_resolver.py \
  --manifest plugins/python3-development/manifests/python3/language-manifest.yaml \
  --format json
```

**Expected output structure** (JSON):

```json
{
  "roles": {
    "architect": "@python3-development:python-cli-architect",
    "test_designer": "@python3-development:python-pytest-architect",
    "code_reviewer": "@python3-development:python-code-reviewer",
    "design_spec": "@python3-development:python-cli-design-spec"
  },
  "quality_gates": {
    "format": "uv run ruff format {files}",
    "lint": "uv run ruff check {files}",
    "typecheck": "uv run mypy {files}",
    "test": "uv run pytest tests/ --tb=short",
    "standards": "/python3-development:modernpython"
  },
  "stage_skills": {
    "discovery": ["python3-discovery"],
    "design": ["python3-design"],
    "planning-context-integration": ["python3-implementation"],
    "planning-task-decomposition": ["python3-planning-task-decomposition"],
    "implementation": ["python3-implementation"],
    "testing-forensic-review": ["python3-testing-forensic-review"],
    "testing-verification": ["python3-testing"]
  }
}
```

**What to verify**: All 5 roles are resolved. Quality gates contain runnable commands. Stage skills map keys to skill name arrays.

#### Section 4: Build the Dispatch Prompt

**Command:**

```bash
uv run python plugins/development-harness/scripts/dispatch_helper.py \
  --manifest plugins/python3-development/manifests/python3/language-manifest.yaml \
  --stage planning \
  --task-file .planning/harness/DISCOVERY.md \
  --stage-workflow-skill "development-harness:planning" \
  --cross-cutting-skill "development-harness:planning" \
  --output-artifact .planning/harness/PLAN.md
```

**Expected output**: A formatted dispatch prompt containing all 5 inputs:

```text
# Stage Dispatch: planning
**Language:** python | **Stack:** base | **Manifest:** python3

## Input 1: Stage Workflow
Load the stage workflow skill: `Skill(skill="development-harness:planning")`

## Input 2: Cross-Cutting Stage Skill
Load: `Skill(skill="development-harness:planning")`

## Input 3: Domain Skills
- Load: `Skill(skill="python3-design")`

## Input 4: Task/Artifact File
Read this file for your task context: `.planning/harness/DISCOVERY.md`

## Input 5: Quality Gates
Run ALL of these before declaring completion:
- Format: `uv run ruff format {files}`
- Lint: `uv run ruff check {files}`
- Typecheck: `uv run mypy {files}`
- Test: `uv run pytest tests/ --tb=short`
- Standards: Load skill `/python3-development:modernpython`

## Output Artifact
Write your output artifact to: `.planning/harness/PLAN.md`
```

**What to verify**: The prompt assembles all 5 inputs correctly. Domain skills for the `planning` stage are resolved from `stage_skills.design` (the `design` key, since `planning` is used as the stage but `design` is the domain skill key that maps to it). The cross-cutting skill and stage workflow skill both reference the harness planning skill.

**Note on stage-to-key resolution**: The dispatch helper receives `--stage planning` and must look up the corresponding `stage_skills` key. For the `planning` stage, the relevant key is `design` (bare domain name covering S2). This mapping logic is in `dispatch_helper.py` -- the PoC guide should document what key was resolved and why.

#### Section 5: Dispatch the Generic Stage Agent

This step describes how the dispatch prompt from Step 4 would be passed to the generic stage agent. Since agent dispatch requires a Claude Code session, this section describes the invocation pattern rather than a runnable command:

```text
Task(
  subagent_type="development-harness:generic-stage-agent",
  prompt=<output from Step 4>
)
```

**What to verify**: The generic stage agent would:
1. Load `Skill(skill="development-harness:planning")` (inputs 1 and 2)
2. Load `Skill(skill="python3-design")` (input 3)
3. Read `.planning/harness/DISCOVERY.md` (input 4)
4. Follow the planning workflow mermaid step by step
5. Run all quality gates before completion
6. Write output to `.planning/harness/PLAN.md`

#### Section 6: Expected Output

The agent produces `.planning/harness/PLAN.md` containing:
- Solution architecture derived from discovery artifact
- Acceptance tests in Given/When/Then format
- Risk assessment
- Task skeletons for S4 decomposition
- RT-ICA gate result: APPROVED-FOR-PLANNING / APPROVED-WITH-GAPS / BLOCKED-FOR-PLANNING

---

## File Change List

### New Files

| File | Deliverable | Content |
|------|-------------|---------|
| `plugins/development-harness/skills/development-harness/references/sdlc-stage-taxonomy.md` | 1 | Taxonomy document with 4 sections: Layer 1 stage names, Layer 2 domain-prefixed names, IEEE/ISO/SAFe mappings, naming rules |
| `plugins/development-harness/docs/poc-validation-guide.md` | 3 | Executable PoC guide with 6 sections: prerequisites, discover, resolve, dispatch prompt, agent invocation, expected output |

### Modified Files

| File | Deliverable | Change Description |
|------|-------------|--------------------|
| `plugins/development-harness/skills/development-harness/references/language-manifest-schema.md` | 2 | Add "Stage Skills (Optional)" section with taxonomy reference, YAML format definition, naming convention pointer, and worked example |
| `plugins/development-harness/agents/generic-stage-agent.md` | 2 | Add taxonomy layer references as parentheticals in inputs 2 and 3 descriptions |
| `plugins/python3-development/manifests/python3/language-manifest.yaml` | 2 | CONDITIONAL: Rename `testing-verification` to `testing-final-verification` if the audit decision is "naming bug" (not abbreviation). If accepted as abbreviation, no change -- document exception in taxonomy instead. |

### Files NOT Modified (Audit Result: Compliant)

| File | Reason |
|------|--------|
| `plugins/python3-development/manifests/python3-cli/language-manifest.yaml` | Override keys (`design`, `implementation`) are intentional and match base manifest keys |
| `plugins/development-harness/scripts/dispatch_helper.py` | No changes needed unless `testing-verification` is renamed, in which case the stage lookup logic may need updating |

---

## Acceptance Criteria

### Deliverable 1: Taxonomy Document

- [ ] File exists at `plugins/development-harness/skills/development-harness/references/sdlc-stage-taxonomy.md`
- [ ] Section 1 lists all 7 bare stage names with `stage_id`, `name`, `skill_activation`, `purpose`, `inputs`, `outputs`, `artifact_path`
- [ ] Section 2 defines the closed domain list (`planning`, `design`, `implementation`, `testing`, `review`) with coverage rationale
- [ ] Section 2 includes the `{domain}-{sdlc-stage}` pattern definition and rules for bare vs. prefixed usage
- [ ] Section 3 maps all 7 stages to IEEE 12207, ISO 15288, and SAFe equivalents
- [ ] Section 4 lists numbered naming convention rules (at least rules 1-8 from this spec)

### Deliverable 2: Naming Audit

- [ ] `testing-verification` vs `testing-final-verification` decision is resolved and documented
- [ ] `language-manifest-schema.md` contains a "Stage Skills" section referencing the taxonomy
- [ ] `generic-stage-agent.md` inputs 2 and 3 contain taxonomy layer references
- [ ] No manifest key uses a domain prefix outside the closed list

### Deliverable 3: PoC Validation Guide

- [ ] File exists at `plugins/development-harness/docs/poc-validation-guide.md`
- [ ] Step 2 (`manifest_discovery.py`) command is runnable and produces JSON output
- [ ] Step 3 (`manifest_resolver.py`) command is runnable and produces JSON output
- [ ] Step 4 (`dispatch_helper.py`) command is runnable and produces a formatted dispatch prompt
- [ ] All commands use `uv run python` invocation syntax
- [ ] Expected output blocks are present for each step
- [ ] The worked example uses the `python3` manifest and `planning` stage

### Cross-Cutting

- [ ] All new markdown files have language specifiers on code fences
- [ ] All file references use `[text](./relative/path)` markdown link syntax
- [ ] The taxonomy document is linked from `language-manifest-schema.md` Sources section

---

## Open Decision: `testing-verification` Key

The `testing-verification` key in `plugins/python3-development/manifests/python3/language-manifest.yaml` does not strictly follow the `{domain}-{sdlc-stage}` pattern because the stage name is `final-verification`, not `verification`.

**Option A -- Accept as abbreviation**: Document `verification` as an accepted short form of `final-verification` in taxonomy Section 4. Add a rule: "When the stage name is unambiguous within a domain, the `final-` prefix may be dropped." No file changes to the manifest.

**Option B -- Rename to strict compliance**: Change key from `testing-verification` to `testing-final-verification` in the manifest YAML. Update `dispatch_helper.py` if it does exact string matching on this key. Update PoC guide expected output.

**Recommendation**: Option A. The abbreviation is unambiguous -- there is no other `verification` stage that `testing-verification` could be confused with. Renaming would be a breaking change for any consumer already referencing this key.

**This decision must be made by the product owner before implementation begins.**
