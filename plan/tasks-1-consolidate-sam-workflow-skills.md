---
plan_number: 1
slug: consolidate-sam-workflow-skills
goal: Consolidate language-agnostic SAM workflow skills from python3-development
  to development-harness plugin
context: |
  This plan consolidates language-agnostic SAM workflow skills from the python3-development plugin
  to the development-harness (dh) plugin. Three backlog items: #957 (remove 5 duplicates),
  #958 (migrate hook scripts), #959 (migrate 4 skills + 2 agents). The architecture spec is at
  plan/architect-consolidate-sam-workflow-skills.md. The feature context is at
  plan/feature-context-consolidate-sam-workflow-skills.md.

  Phase ordering: A (delete duplicates) and B (migrate scripts) are independent and parallel.
  Phase B.5 (language manifest) is also independent. Phase C (migrate skills) depends on B.
  Phase D (update references) depends on A+B+C. Role resolution (T07, T08) depends on T03 (manifest) and T04 (skill moves).
acceptance_criteria:
- 'AC1: 5 duplicate skill directories removed from python3-development (clear-cove-task-design,
  generate-task, planner-rt-ica, validation-protocol, implementation-manager SKILL.md)'
- 'AC2: 3 hook scripts (task_status_hook.py, task_format.py, get_task_context.py)
  exist in dh implementation-manager/scripts/'
- 'AC3: 4 workflow skills (implement-feature, start-task, complete-implementation,
  add-new-feature) exist in dh skills/'
- 'AC4: 2 agents (t0-baseline-capture, tn-verification-gate) exist in dh agents/'
- 'AC5: subagent-contract skill exists in dh skills/'
- 'AC6: add-new-feature and complete-implementation use role resolution, not hardcoded
  agent names'
- 'AC7: python3-development language manifest exists with 5 role mappings'
- 'AC8: local-workflow.md has zero stale references to migrated python3-development
  paths'
- 'AC9: Both plugins pass skilllint validation with zero errors'
- 'AC10: sam CLI (uv run sam list) returns valid JSON'
status: not-started
tasks:
- task: T01
  title: Delete 5 duplicate skill directories from python3-development
  status: complete
  agent: python-cli-architect
  dependencies: []
  priority: 1
  complexity: low
  accuracy-risk: low
  skills: [python3-development]
  parallelize-with: [T02, T03]
  body: |
    ## Context

    The python3-development plugin contains 5 skill directories that are identical copies of skills already in development-harness. This task removes the duplicates per Phase A of the consolidation architecture spec at `plan/architect-consolidate-sam-workflow-skills.md`.

    ## Objective

    Delete 5 duplicate skill directories from python3-development, leaving the dh copies as canonical.

    ## Inputs

    - Architecture spec: `plan/architect-consolidate-sam-workflow-skills.md` (section 2, Phase A)
    - Deletion checklist: same file, section 5 "Phase A Deletions"

    ## Requirements

    1. Verify each dh canonical copy exists before deleting the python3-development copy
    2. Delete entire directories for: `clear-cove-task-design/`, `generate-task/`, `planner-rt-ica/`, `validation-protocol/`
    3. Delete ONLY `plugins/python3-development/skills/implementation-manager/SKILL.md` (keep the `scripts/` subdirectory -- it is needed until T02 completes)
    4. Use `git rm -r` for directory deletions to track in git

    ## Constraints

    - Do NOT delete `plugins/python3-development/skills/implementation-manager/scripts/` -- Phase B needs these files
    - Do NOT delete any files from the dh plugin
    - Do NOT modify any SKILL.md content -- pure deletion only

    ## Expected Outputs

    - 4 directories removed from `plugins/python3-development/skills/`
    - 1 file removed: `plugins/python3-development/skills/implementation-manager/SKILL.md`

    ## Acceptance Criteria

    1. `plugins/python3-development/skills/clear-cove-task-design/` does not exist
    2. `plugins/python3-development/skills/generate-task/` does not exist
    3. `plugins/python3-development/skills/planner-rt-ica/` does not exist
    4. `plugins/python3-development/skills/validation-protocol/` does not exist
    5. `plugins/python3-development/skills/implementation-manager/SKILL.md` does not exist
    6. `plugins/python3-development/skills/implementation-manager/scripts/` still exists (preserved for Phase B)
    7. `plugins/development-harness/skills/clear-cove-task-design/SKILL.md` exists (canonical copy verified)
    8. `plugins/development-harness/skills/generate-task/SKILL.md` exists (canonical copy verified)

    ## Verification Steps

    1. Run `ls plugins/python3-development/skills/ | sort` and confirm the 4 deleted directories are absent
    2. Run `test -f plugins/python3-development/skills/implementation-manager/SKILL.md && echo EXISTS || echo GONE` -- expect GONE
    3. Run `test -d plugins/python3-development/skills/implementation-manager/scripts && echo EXISTS || echo GONE` -- expect EXISTS
    4. Run `git status --short plugins/python3-development/skills/` and confirm deletions are staged
  started: '2026-03-21T14:21:04.199224+00:00'
- task: T02
  title: Migrate hook scripts from python3-development to dh and clean stale pyc
  status: complete
  agent: python-cli-architect
  dependencies: []
  priority: 1
  complexity: medium
  accuracy-risk: medium
  skills: [python3-development]
  parallelize-with: [T01]
  body: |
    ## Context

    Three hook scripts in `plugins/python3-development/skills/implementation-manager/scripts/` are language-agnostic SAM infrastructure. They must move to the equivalent dh location. Two additional files (`implementation_manager.py` and `test_task_parsing.py`) are superseded by the sam CLI and should be deleted. Stale `.pyc` files in dh must be cleaned first.

    ## Objective

    Move 3 hook scripts to dh, delete 2 obsolete scripts, clean stale pyc files, and delete the now-empty python3-development implementation-manager directory.

    ## Inputs

    - Architecture spec: `plan/architect-consolidate-sam-workflow-skills.md` (section 2, Phase B)
    - Source directory: `plugins/python3-development/skills/implementation-manager/scripts/`
    - Destination directory: `plugins/development-harness/skills/implementation-manager/scripts/`

    ## Requirements

    1. Delete `plugins/development-harness/skills/implementation-manager/scripts/__pycache__/` (stale pyc files)
    2. Move `task_status_hook.py` from python3-development to dh implementation-manager/scripts/
    3. Move `task_format.py` from python3-development to dh implementation-manager/scripts/
    4. Move `get_task_context.py` from python3-development to dh implementation-manager/scripts/
    5. Delete `plugins/python3-development/skills/implementation-manager/scripts/implementation_manager.py` (superseded by sam CLI)
    6. Delete `plugins/python3-development/skills/implementation-manager/scripts/test_task_parsing.py` (test for old CLI)
    7. Verify no remaining references to `implementation_manager.py` in the codebase before deleting
    8. Delete the now-empty `plugins/python3-development/skills/implementation-manager/` directory (SKILL.md already removed by T01)
    9. Use `git mv` for moves to preserve history

    ## Constraints

    - Do NOT modify script contents during the move -- pure file relocation
    - Do NOT delete any script that still has active callers (verify first)
    - The sam CLI must still function after the move (it imports from sam_schema, not from these script paths directly, but verify)

    ## Expected Outputs

    - 3 scripts in `plugins/development-harness/skills/implementation-manager/scripts/`
    - `plugins/python3-development/skills/implementation-manager/` directory fully removed
    - No stale `__pycache__/` in dh scripts directory

    ## Acceptance Criteria

    1. `plugins/development-harness/skills/implementation-manager/scripts/task_status_hook.py` exists
    2. `plugins/development-harness/skills/implementation-manager/scripts/task_format.py` exists
    3. `plugins/development-harness/skills/implementation-manager/scripts/get_task_context.py` exists
    4. `plugins/python3-development/skills/implementation-manager/` directory does not exist
    5. No `__pycache__` directory under `plugins/development-harness/skills/implementation-manager/scripts/`
    6. `uv run sam list` returns valid JSON without errors

    ## Verification Steps

    1. Run `ls plugins/development-harness/skills/implementation-manager/scripts/` and confirm 3 scripts present
    2. Run `test -d plugins/python3-development/skills/implementation-manager && echo EXISTS || echo GONE` -- expect GONE
    3. Run `uv run sam list --format json` and confirm valid JSON output
    4. Run `rg "implementation_manager\.py" plugins/ .claude/ --files-with-matches` and confirm zero matches (no stale references)

    ## CoVe Checks

    - Key claims to verify:
      - `implementation_manager.py` is truly superseded by sam CLI with no remaining callers
      - `task_format.py` is not imported by sam_schema from its current path
    - Verification questions:
      1. Does any Python file import from `plugins/python3-development/skills/implementation-manager/scripts/task_format`?
      2. Does the sam CLI or sam_schema package import task_format from the plugin scripts path?
      3. Are there any hook configurations that reference the python3-development path to task_status_hook.py?
    - Evidence to collect:
      - `rg "from.*task_format import" plugins/ src/`
      - `rg "task_status_hook" plugins/ .claude/ --files-with-matches`
    - Revision rule: If any import references the old path, update the import path before deleting the source.
  started: '2026-03-21T14:27:07.262225+00:00'
- task: T03
  title: Check for python3-development language manifest and create if missing
  status: complete
  agent: python-cli-architect
  dependencies: []
  priority: 1
  complexity: medium
  accuracy-risk: medium
  skills: [python3-development]
  parallelize-with: [T01, T02]
  body: |
    ## Context

    The Voltron role resolution protocol requires each language plugin to provide a language manifest declaring role-to-agent mappings. The migrated skills (`add-new-feature`, `complete-implementation`) need this manifest to resolve abstract roles (`design-spec`, `code-reviewer`) to concrete Python agents.

    ## Objective

    Verify the python3-development language manifest exists; create it if missing, following the schema at `plugins/development-harness/skills/development-harness/references/language-manifest-schema.md`.

    ## Inputs

    - Schema: `plugins/development-harness/skills/development-harness/references/language-manifest-schema.md`
    - Role mappings from architecture spec section 1.3: architect->python-cli-architect, test-designer->python-pytest-architect, code-reviewer->code-reviewer, design-spec->python-cli-design-spec, linting->null
    - Possible locations: `plugins/python3-development/skills/python3-development/references/language-manifest.md` or `plugins/python3-development/references/language-manifest.md`

    ## Requirements

    1. Search for existing language manifest in python3-development plugin
    2. If found, verify it contains all 5 role mappings from the architecture spec
    3. If not found, create it at the appropriate location following the schema
    4. Validate the manifest against the schema document

    ## Constraints

    - The manifest must follow the exact schema format from the dh reference document
    - Do NOT invent role mappings beyond what the architecture spec defines
    - Do NOT modify the schema document itself

    ## Expected Outputs

    - Language manifest file in the python3-development plugin

    ## Acceptance Criteria

    1. A language manifest file exists in the python3-development plugin
    2. Manifest contains role mapping for architect -> python-cli-architect
    3. Manifest contains role mapping for test-designer -> python-pytest-architect
    4. Manifest contains role mapping for code-reviewer -> code-reviewer
    5. Manifest contains role mapping for design-spec -> python-cli-design-spec
    6. Manifest format validates against the schema reference document

    ## Verification Steps

    1. Read the manifest file and confirm all 5 role mappings are present
    2. Compare structure against the schema at `plugins/development-harness/skills/development-harness/references/language-manifest-schema.md`
    3. Run `uv run prek run --files {manifest_path}` to validate formatting

    ## CoVe Checks

    - Key claims to verify:
      - The language manifest schema document exists at the referenced path
      - No existing manifest already exists that would be overwritten
    - Verification questions:
      1. Does `plugins/development-harness/skills/development-harness/references/language-manifest-schema.md` exist and what format does it specify?
      2. Does any file matching `*language-manifest*` already exist under `plugins/python3-development/`?
    - Evidence to collect:
      - `fdfind language-manifest plugins/python3-development/`
      - Read the schema document to confirm format expectations
    - Revision rule: If a manifest already exists with different role mappings, report the discrepancy instead of overwriting.
  started: '2026-03-21T14:21:50.631381+00:00'
- task: T04
  title: Move 4 workflow skills from python3-development to dh
  status: complete
  agent: python-cli-architect
  dependencies: [T02]
  priority: 2
  complexity: high
  accuracy-risk: medium
  skills: [python3-development]
  parallelize-with: [T05, T06]
  body: |
    ## Context

    Four SAM workflow skills must move from python3-development to development-harness. These skills reference hook scripts (migrated in T02) via relative paths. The `implement-feature` skill has a hardcoded repo-relative hook path that must change to use `${CLAUDE_SKILL_DIR}`.

    This task was merged from skill directory moves AND hook path updates since both modify the same SKILL.md files.

    ## Objective

    Move 4 skill directories to dh and update the implement-feature hook path to use `${CLAUDE_SKILL_DIR}` instead of a hardcoded repo-relative path.

    ## Inputs

    - Architecture spec: `plan/architect-consolidate-sam-workflow-skills.md` (section 2 Phase C.1, section 3)
    - Source: `plugins/python3-development/skills/{implement-feature,start-task,complete-implementation,add-new-feature}/`
    - Destination: `plugins/development-harness/skills/`

    ## Requirements

    1. Move `plugins/python3-development/skills/implement-feature/` to `plugins/development-harness/skills/implement-feature/`
    2. Move `plugins/python3-development/skills/start-task/` to `plugins/development-harness/skills/start-task/`
    3. Move `plugins/python3-development/skills/complete-implementation/` to `plugins/development-harness/skills/complete-implementation/`
    4. Move `plugins/python3-development/skills/add-new-feature/` to `plugins/development-harness/skills/add-new-feature/`
    5. In `implement-feature/SKILL.md`, update the SubagentStop hook path from `python3 "./plugins/python3-development/skills/implementation-manager/scripts/task_status_hook.py"` to `python3 "${CLAUDE_SKILL_DIR}/../implementation-manager/scripts/task_status_hook.py"`
    6. Verify `start-task/SKILL.md` hook path `${CLAUDE_SKILL_DIR}/../../implementation-manager/scripts/task_status_hook.py` still resolves correctly in dh directory structure
    7. Use `git mv` for all moves to preserve history

    ## Constraints

    - Do NOT modify skill content beyond the hook path fix in implement-feature
    - Do NOT rename any skill directories
    - Role resolution changes are handled by T07 and T08 -- this task is moves only plus hook path fix

    ## Expected Outputs

    - 4 skill directories under `plugins/development-harness/skills/`
    - Source directories removed from python3-development
    - Updated hook path in `implement-feature/SKILL.md`

    ## Acceptance Criteria

    1. `plugins/development-harness/skills/implement-feature/SKILL.md` exists
    2. `plugins/development-harness/skills/start-task/SKILL.md` exists
    3. `plugins/development-harness/skills/complete-implementation/SKILL.md` exists
    4. `plugins/development-harness/skills/add-new-feature/SKILL.md` exists
    5. None of the 4 skill directories exist under `plugins/python3-development/skills/`
    6. `implement-feature/SKILL.md` hook path references `${CLAUDE_SKILL_DIR}` not `./plugins/python3-development/`
    7. `start-task/SKILL.md` hook path is unchanged (relative path still valid)

    ## Verification Steps

    1. Run `ls plugins/development-harness/skills/{implement-feature,start-task,complete-implementation,add-new-feature}/SKILL.md` -- all 4 must exist
    2. Run `rg "python3-development/skills/implement-feature" plugins/` -- zero matches
    3. Run `rg 'CLAUDE_SKILL_DIR' plugins/development-harness/skills/implement-feature/SKILL.md` -- must show the updated hook path
    4. Run `rg 'python3-development.*task_status_hook' plugins/development-harness/` -- zero matches

    ## CoVe Checks

    - Key claims to verify:
      - The `${CLAUDE_SKILL_DIR}/../implementation-manager/scripts/task_status_hook.py` path resolves correctly from implement-feature/ to implementation-manager/scripts/
      - The start-task hook path still traverses correctly in dh
    - Verification questions:
      1. From `plugins/development-harness/skills/implement-feature/`, does `../implementation-manager/scripts/task_status_hook.py` resolve to the correct file?
      2. From `plugins/development-harness/skills/start-task/SKILL.md`, does the existing CLAUDE_SKILL_DIR-based path still work?
    - Evidence to collect:
      - Check actual relative path traversal from each skill directory to the scripts directory
    - Revision rule: If path traversal does not resolve, adjust the relative path components.
  started: '2026-03-21T14:30:36.439678+00:00'
- task: T05
  title: Move t0-baseline-capture and tn-verification-gate agents to dh
  status: complete
  agent: python-cli-architect
  dependencies: [T02]
  priority: 2
  complexity: low
  accuracy-risk: low
  skills: [python3-development]
  parallelize-with: [T04, T06]
  body: |
    ## Context

    Two bookend agents (t0-baseline-capture, tn-verification-gate) are language-agnostic SAM infrastructure. They run check commands and record results -- no Python-specific knowledge needed.

    ## Objective

    Move 2 agent files from python3-development to development-harness.

    ## Inputs

    - Architecture spec: `plan/architect-consolidate-sam-workflow-skills.md` (section 2, Phase C.2)

    ## Requirements

    1. Move `plugins/python3-development/agents/t0-baseline-capture.md` to `plugins/development-harness/agents/t0-baseline-capture.md`
    2. Move `plugins/python3-development/agents/tn-verification-gate.md` to `plugins/development-harness/agents/tn-verification-gate.md`
    3. Use `git mv` to preserve history
    4. If agent frontmatter contains `skills:` entries referencing python3-development namespace, note for T11

    ## Constraints

    - Do NOT modify agent content -- pure file relocation
    - Do NOT move any Python-specific agents

    ## Expected Outputs

    - `plugins/development-harness/agents/t0-baseline-capture.md`
    - `plugins/development-harness/agents/tn-verification-gate.md`
    - Source files removed from python3-development

    ## Acceptance Criteria

    1. `plugins/development-harness/agents/t0-baseline-capture.md` exists
    2. `plugins/development-harness/agents/tn-verification-gate.md` exists
    3. `plugins/python3-development/agents/t0-baseline-capture.md` does not exist
    4. `plugins/python3-development/agents/tn-verification-gate.md` does not exist

    ## Verification Steps

    1. Run `ls plugins/development-harness/agents/t0-baseline-capture.md plugins/development-harness/agents/tn-verification-gate.md` -- both exist
    2. Run `ls plugins/python3-development/agents/t0-baseline-capture.md 2>&1` -- file not found
    3. Run `git status --short plugins/` -- shows renames
  started: '2026-03-21T14:31:00.660191+00:00'
- task: T06
  title: Move subagent-contract skill to dh
  status: complete
  agent: python-cli-architect
  dependencies: [T02]
  priority: 2
  complexity: low
  accuracy-risk: low
  skills: [python3-development]
  parallelize-with: [T04, T05]
  body: |
    ## Context

    The subagent-contract skill exists in both python3-development and plugin-creator. The python3-development copy moves to dh so migrated agents can resolve it locally. The plugin-creator copy is independent.

    ## Objective

    Move the subagent-contract skill directory from python3-development to development-harness.

    ## Inputs

    - Architecture spec: `plan/architect-consolidate-sam-workflow-skills.md` (section 1.2)

    ## Requirements

    1. Move `plugins/python3-development/skills/subagent-contract/` to `plugins/development-harness/skills/subagent-contract/`
    2. Use `git mv` to preserve history
    3. Verify `plugins/plugin-creator/skills/subagent-contract/` is NOT affected

    ## Constraints

    - Do NOT touch the plugin-creator copy of subagent-contract
    - Do NOT modify content -- pure file relocation

    ## Expected Outputs

    - `plugins/development-harness/skills/subagent-contract/SKILL.md`
    - `plugins/python3-development/skills/subagent-contract/` removed

    ## Acceptance Criteria

    1. `plugins/development-harness/skills/subagent-contract/SKILL.md` exists
    2. `plugins/python3-development/skills/subagent-contract/` does not exist
    3. `plugins/plugin-creator/skills/subagent-contract/SKILL.md` still exists (untouched)

    ## Verification Steps

    1. Run `test -f plugins/development-harness/skills/subagent-contract/SKILL.md && echo OK` -- expect OK
    2. Run `test -d plugins/python3-development/skills/subagent-contract && echo EXISTS || echo GONE` -- expect GONE
    3. Run `test -f plugins/plugin-creator/skills/subagent-contract/SKILL.md && echo OK` -- expect OK
  started: '2026-03-21T14:31:33.966541+00:00'
- task: T07
  title: Replace hardcoded agent in add-new-feature with role resolution
  status: complete
  agent: python-cli-architect
  dependencies: [T03, T04]
  priority: 2
  complexity: medium
  accuracy-risk: medium
  skills: [python3-development]
  parallelize-with: [T08]
  body: |
    ## Context

    The add-new-feature skill (at `plugins/development-harness/skills/add-new-feature/SKILL.md` after T04) hardcodes `python-cli-design-spec` as the Phase 3 agent. After migration to the language-agnostic dh plugin, this must use the Voltron role resolution protocol.

    ## Objective

    Replace the hardcoded python-cli-design-spec reference with an abstract role resolution instruction.

    ## Inputs

    - Target file: `plugins/development-harness/skills/add-new-feature/SKILL.md`
    - Role resolution protocol: `plugins/development-harness/skills/development-harness/references/role-resolution-protocol.md`
    - Architecture spec section 4

    ## Requirements

    1. Read `add-new-feature/SKILL.md` and locate all references to `python-cli-design-spec`
    2. Replace each hardcoded agent reference with instructions to resolve the `design-spec` role from the active language manifest
    3. Include fallback: "If no language manifest is active, use the general-purpose agent"

    ## Constraints

    - Do NOT change anything unrelated to the agent reference replacement
    - Do NOT remove any other Phase 3 instructions
    - The replacement must reference the Voltron role resolution protocol

    ## Expected Outputs

    - Modified `plugins/development-harness/skills/add-new-feature/SKILL.md` with role resolution

    ## Acceptance Criteria

    1. `rg "python-cli-design-spec" plugins/development-harness/skills/add-new-feature/` returns zero matches
    2. The SKILL.md contains "design-spec" as an abstract role reference
    3. The SKILL.md contains a fallback instruction for when no language manifest is active

    ## Verification Steps

    1. Run `rg "python-cli-design-spec" plugins/development-harness/skills/add-new-feature/` -- zero matches
    2. Run `rg "design-spec" plugins/development-harness/skills/add-new-feature/SKILL.md` -- at least one match
    3. Run `rg "general-purpose" plugins/development-harness/skills/add-new-feature/SKILL.md` -- at least one match
    4. Run `uv run prek run --files plugins/development-harness/skills/add-new-feature/SKILL.md` -- passes

    ## CoVe Checks

    - Key claims to verify:
      - The current SKILL.md actually references python-cli-design-spec
      - The role resolution protocol document defines the design-spec role
    - Verification questions:
      1. Does add-new-feature/SKILL.md currently contain the literal string python-cli-design-spec?
      2. Does the role resolution protocol reference document define design-spec?
    - Evidence to collect:
      - `rg "python-cli-design-spec" plugins/development-harness/skills/add-new-feature/`
      - `rg "design-spec" plugins/development-harness/skills/development-harness/references/role-resolution-protocol.md`
    - Revision rule: If already abstracted, report as no-op. If role not defined in protocol, add it.
  started: '2026-03-21T14:33:45.125304+00:00'
- task: T08
  title: Replace hardcoded agent in complete-implementation with role resolution
  status: complete
  agent: python-cli-architect
  dependencies: [T03, T04]
  priority: 2
  complexity: medium
  accuracy-risk: medium
  skills: [python3-development]
  parallelize-with: [T07]
  body: |
    ## Context

    The complete-implementation skill (at `plugins/development-harness/skills/complete-implementation/SKILL.md` after T04) hardcodes `code-reviewer` as the Phase 1 agent. After migration to dh, this must use the Voltron role resolution protocol.

    ## Objective

    Replace the hardcoded code-reviewer agent reference with an abstract role resolution instruction.

    ## Inputs

    - Target file: `plugins/development-harness/skills/complete-implementation/SKILL.md`
    - Role resolution protocol: `plugins/development-harness/skills/development-harness/references/role-resolution-protocol.md`
    - Architecture spec section 4

    ## Requirements

    1. Read `complete-implementation/SKILL.md` and locate all references to code-reviewer that are hardcoded agent delegations
    2. Replace with instructions to resolve the code-reviewer role from the active language manifest
    3. Include fallback: "If no language manifest is active, use the general-purpose agent"
    4. Preserve the role name "code-reviewer" as the abstract identifier

    ## Constraints

    - Do NOT change anything unrelated to the agent reference replacement
    - Do NOT remove any other Phase 1 instructions

    ## Expected Outputs

    - Modified `plugins/development-harness/skills/complete-implementation/SKILL.md` with role resolution

    ## Acceptance Criteria

    1. The SKILL.md no longer hardcodes a specific plugin's code-reviewer agent for delegation
    2. The SKILL.md instructs the orchestrator to resolve the code-reviewer role from the language manifest
    3. The SKILL.md contains a fallback instruction for when no language manifest is active

    ## Verification Steps

    1. Read `complete-implementation/SKILL.md` and confirm Phase 1 references "code-reviewer role" not a hardcoded plugin agent
    2. Run `rg "general-purpose" plugins/development-harness/skills/complete-implementation/SKILL.md` -- at least one match
    3. Run `uv run prek run --files plugins/development-harness/skills/complete-implementation/SKILL.md` -- passes

    ## CoVe Checks

    - Key claims to verify:
      - The current SKILL.md actually hardcodes a code-reviewer agent delegation
    - Verification questions:
      1. Does complete-implementation/SKILL.md reference python3-development:code-reviewer or just code-reviewer as a hardcoded agent?
      2. Is there a distinction between the agent name and the abstract role in the current text?
    - Evidence to collect:
      - `rg "code-reviewer" plugins/development-harness/skills/complete-implementation/SKILL.md`
    - Revision rule: If already abstracted, report as no-op.
  started: '2026-03-21T14:34:52.809976+00:00'
- task: T09
  title: Update .claude/rules/local-workflow.md for new dh locations
  status: complete
  agent: python-cli-architect
  dependencies: [T01, T02, T04, T05, T06, T07, T08]
  priority: 3
  complexity: high
  accuracy-risk: medium
  skills: [python3-development]
  parallelize-with: [T10, T11]
  body: |
    ## Context

    `.claude/rules/local-workflow.md` is the primary reference document for the SAM workflow with 30+ references to skill and script paths that now point to python3-development but must point to development-harness after migration.

    ## Objective

    Update all path references in local-workflow.md from python3-development locations to development-harness locations for all migrated components.

    ## Inputs

    - Target file: `.claude/rules/local-workflow.md`
    - Architecture spec section 2 (all directory mappings)
    - Architecture spec section 6.6 (reference integrity search patterns)

    ## Requirements

    1. Update all paths referencing `python3-development/skills/implement-feature` to `development-harness/skills/implement-feature`
    2. Update all paths referencing `python3-development/skills/start-task` to `development-harness/skills/start-task`
    3. Update all paths referencing `python3-development/skills/complete-implementation` to `development-harness/skills/complete-implementation`
    4. Update all paths referencing `python3-development/skills/add-new-feature` to `development-harness/skills/add-new-feature`
    5. Update all paths referencing `python3-development/skills/implementation-manager/scripts/` to `development-harness/skills/implementation-manager/scripts/`
    6. Update all paths referencing `python3-development/agents/t0-baseline-capture` to `development-harness/agents/t0-baseline-capture`
    7. Update all paths referencing `python3-development/agents/tn-verification-gate` to `development-harness/agents/tn-verification-gate`
    8. Update Agent File Locations tables to reflect new plugin assignments
    9. Preserve all non-migrated references to python3-development (Python-specific agents remain there)

    ## Constraints

    - Do NOT update references to Python-specific agents (python-cli-architect, python-pytest-architect, etc.)
    - Do NOT change the document structure or add/remove sections

    ## Expected Outputs

    - Updated `.claude/rules/local-workflow.md` with all migrated component paths pointing to dh

    ## Acceptance Criteria

    1. `rg "python3-development/skills/implement-feature" .claude/rules/local-workflow.md` returns zero matches
    2. `rg "python3-development/skills/start-task" .claude/rules/local-workflow.md` returns zero matches
    3. `rg "python3-development/skills/complete-implementation" .claude/rules/local-workflow.md` returns zero matches
    4. `rg "python3-development/skills/add-new-feature" .claude/rules/local-workflow.md` returns zero matches
    5. `rg "python3-development/skills/implementation-manager/scripts" .claude/rules/local-workflow.md` returns zero matches
    6. `rg "python3-development/agents/t0-baseline" .claude/rules/local-workflow.md` returns zero matches
    7. References to Python-specific agents still point to python3-development

    ## Verification Steps

    1. Run each of the 6 rg commands in acceptance criteria -- all return zero matches
    2. Run `rg "python-cli-architect" .claude/rules/local-workflow.md` -- still has matches
    3. Run `rg "development-harness/skills/implement-feature" .claude/rules/local-workflow.md` -- has matches
    4. Run `uv run prek run --files .claude/rules/local-workflow.md` -- passes

    ## CoVe Checks

    - Key claims to verify:
      - All 30+ references are accounted for by the search patterns
    - Verification questions:
      1. Are there references using variant path formats (with ./ prefix, relative paths)?
    - Evidence to collect:
      - `rg "python3-development" .claude/rules/local-workflow.md --count` before and after
    - Revision rule: If variant path formats exist, add them to the update list.
  started: '2026-03-21T14:39:50.767390+00:00'
- task: T10
  title: Update python3-development CLAUDE.md skill and agent inventory
  status: complete
  agent: python-cli-architect
  dependencies: [T01, T02, T04, T05, T06]
  priority: 3
  complexity: medium
  accuracy-risk: low
  skills: [python3-development]
  parallelize-with: [T09, T11]
  body: |
    ## Context

    The python3-development plugin CLAUDE.md contains skill and agent inventory sections that list components now migrated to dh or deleted.

    ## Objective

    Update python3-development CLAUDE.md to remove references to migrated/deleted skills and agents, keeping only Python-specific components.

    ## Inputs

    - Target file: `plugins/python3-development/CLAUDE.md`
    - Architecture spec section 2 (all deletions and moves)
    - Architecture spec section 8 (files NOT in scope -- what stays)

    ## Requirements

    1. Remove inventory entries for: clear-cove-task-design, generate-task, planner-rt-ica, validation-protocol, implementation-manager
    2. Remove inventory entries for: implement-feature, start-task, complete-implementation, add-new-feature, subagent-contract
    3. Remove inventory entries for agents: t0-baseline-capture, tn-verification-gate
    4. Add a note that SAM workflow skills are now in the development-harness plugin
    5. Keep all Python-specific entries (orchestrate, python-cli-architect, etc.)

    ## Constraints

    - Do NOT remove references to Python-specific components
    - Do NOT change the CLAUDE.md structure beyond inventory updates

    ## Expected Outputs

    - Updated `plugins/python3-development/CLAUDE.md` reflecting only retained components

    ## Acceptance Criteria

    1. No inventory entries for the 5 deleted duplicate skills
    2. No inventory entries for the 4 migrated workflow skills
    3. No inventory entries for the 2 migrated agents
    4. A cross-reference note pointing to dh for SAM workflow skills
    5. Python-specific components still listed

    ## Verification Steps

    1. Run `rg "implement-feature|start-task|complete-implementation|add-new-feature" plugins/python3-development/CLAUDE.md` -- only cross-reference note
    2. Run `rg "clear-cove-task-design|generate-task|planner-rt-ica|validation-protocol" plugins/python3-development/CLAUDE.md` -- zero matches
    3. Run `rg "orchestrate|python-cli-architect" plugins/python3-development/CLAUDE.md` -- still has matches
  started: '2026-03-21T14:35:03.642964+00:00'
- task: T11
  title: Update python3-development commands references and agent frontmatter
    skill namespaces
  status: complete
  agent: python-cli-architect
  dependencies: [T04, T05, T06]
  priority: 3
  complexity: medium
  accuracy-risk: medium
  skills: [python3-development]
  parallelize-with: [T09, T10]
  body: |
    ## Context

    The python3-development plugin has command files and agent frontmatter that reference migrated skills using the python3-development: namespace prefix. This task merges command reference updates and agent frontmatter skill namespace updates.

    ## Objective

    Update or remove stale skill namespace references in python3-development commands and agent frontmatter.

    ## Inputs

    - Architecture spec section 2 Phase D
    - `plugins/python3-development/commands/development/create-feature-task.md`
    - `plugins/python3-development/commands/development/config/command-patterns.yml`
    - Agent files in `plugins/python3-development/agents/` and `plugins/development-harness/agents/`

    ## Requirements

    ### Command reference updates
    1. Read `create-feature-task.md` and update references to migrated skills
    2. Read `command-patterns.yml` and update references to migrated skills
    3. Update namespace from `python3-development:` to `dh:` for migrated skills

    ### Agent frontmatter skill namespace updates
    4. Search all agent files for skills: entries referencing python3-development:subagent-contract or python3-development:implementation-manager
    5. Update to dh:subagent-contract or dh:implementation-manager as appropriate

    ## Constraints

    - Do NOT delete command files unless entirely about migrated skills with no remaining purpose
    - Do NOT modify agent logic -- only namespace prefixes in frontmatter

    ## Expected Outputs

    - Updated command files with correct skill namespace references
    - Updated agent frontmatter with correct skill namespace references

    ## Acceptance Criteria

    1. `rg "python3-development:implement-feature|python3-development:start-task|python3-development:complete-implementation|python3-development:add-new-feature" plugins/` returns zero matches
    2. `rg "python3-development:subagent-contract" plugins/` returns zero matches
    3. `rg "python3-development:implementation-manager" plugins/` returns zero matches (for skill references)

    ## Verification Steps

    1. Run the 3 rg commands in acceptance criteria -- all zero matches
    2. Run `rg "dh:implement-feature|dh:start-task|dh:add-new-feature|dh:complete-implementation" plugins/` -- should have matches
    3. Run `uv run prek run --files plugins/python3-development/commands/development/create-feature-task.md` -- passes

    ## CoVe Checks

    - Key claims to verify:
      - The command files actually reference migrated skills
      - Agent frontmatter actually uses python3-development: prefixed skill names
    - Verification questions:
      1. Does create-feature-task.md exist and reference any migrated skill names?
      2. Do any agent .md files contain skills: entries with python3-development: prefix?
    - Evidence to collect:
      - `rg "python3-development:" plugins/python3-development/commands/`
      - `rg "python3-development:" plugins/*/agents/ --files-with-matches`
    - Revision rule: If files do not contain expected references, report as no-op.
  started: '2026-03-21T14:35:02.430755+00:00'
- task: T12
  title: Run plugin validator on both plugins and fix any errors
  status: complete
  agent: python-cli-architect
  dependencies: [T01, T02, T04, T05, T06, T07, T08, T09, T10, T11]
  priority: 3
  complexity: low
  accuracy-risk: low
  skills: [python3-development]
  parallelize-with: []
  body: |
    ## Context

    After all migrations and reference updates, both plugins must pass the plugin validator. This is the final quality gate.

    ## Objective

    Run the plugin validator on both plugins and fix any errors introduced by the migration.

    ## Requirements

    1. Run `uvx skilllint@latest check plugins/development-harness`
    2. Run `uvx skilllint@latest check plugins/python3-development`
    3. If either fails with errors (not warnings), fix the errors
    4. Re-run until both pass

    ## Constraints

    - Pre-existing warnings are acceptable -- only fix errors introduced by the migration
    - Do NOT modify plugin structure to suppress warnings

    ## Expected Outputs

    - Both plugins pass validation with zero errors

    ## Acceptance Criteria

    1. `uvx skilllint@latest check plugins/development-harness` exits with code 0
    2. `uvx skilllint@latest check plugins/python3-development` exits with code 0
    3. Any errors found are fixed, not suppressed

    ## Verification Steps

    1. Run `uvx skilllint@latest check plugins/development-harness` -- exit code 0
    2. Run `uvx skilllint@latest check plugins/python3-development` -- exit code 0
    3. Run `uv run sam list` -- valid JSON
  started: '2026-03-21T15:18:55.848065+00:00'
- task: T13
  title: Run stale reference search across entire repo
  status: complete
  agent: python-cli-architect
  dependencies: [T09, T10, T11]
  priority: 3
  complexity: low
  accuracy-risk: low
  skills: [python3-development]
  parallelize-with: [T12]
  body: |-
    ## Context

    The architecture spec defines 6 reference integrity search patterns (section 6.6) that must return zero matches after migration. This task runs those searches and fixes any remaining stale references.

    ## Objective

    Search for and eliminate all stale references to migrated component paths across the entire repository.

    ## Requirements

    1. Run `rg "python3-development/skills/implement-feature" plugins/ .claude/` -- must be zero matches
    2. Run `rg "python3-development/skills/start-task" plugins/ .claude/` -- must be zero matches
    3. Run `rg "python3-development/skills/complete-implementation" plugins/ .claude/` -- must be zero matches
    4. Run `rg "python3-development/skills/add-new-feature" plugins/ .claude/` -- must be zero matches
    5. Run `rg "python3-development/agents/t0-baseline" plugins/ .claude/` -- must be zero matches
    6. Run `rg "python3-development/agents/tn-verification" plugins/ .claude/` -- must be zero matches
    7. If any matches found, fix them by updating to the correct dh path

    ## Constraints

    - Only update paths for migrated components
    - This task searches beyond T09/T10/T11 to catch any missed references

    ## Expected Outputs

    - Zero stale references to migrated component paths in the repository

    ## Acceptance Criteria

    1. All 6 search patterns return zero matches
    2. Any fixes applied are correct path updates, not deletions

    ## Verification Steps

    1. Run all 6 rg commands -- all return empty output
    2. Run `rg "python3-development/skills/implementation-manager/scripts" plugins/ .claude/` -- also zero matches
    3. Run `rg "python3-development/skills/subagent-contract" plugins/ .claude/` -- zero matches
  started: '2026-03-21T15:18:50.871045+00:00'

---

## Context Manifest

Generated by context-gathering agent on 2026-03-21

### How This Currently Works: SAM Workflow Skill Consolidation

When users invoke the SAM workflow to implement features (via `/implement-feature`, `/add-new-feature`, `/start-task`, or `/complete-implementation`), they trigger code paths scattered across two plugins: python3-development and development-harness. The python3-development plugin contains 5 skill directories (clear-cove-task-design, generate-task, planner-rt-ica, validation-protocol, and implementation-manager) that are identical copies of skills already in development-harness. Additionally, language-agnostic hook scripts (task_status_hook.py, task_format.py, get_task_context.py) currently live in python3-development/skills/implementation-manager/scripts/, but belong in the dh plugin as SAM infrastructure.

The current state creates maintenance problems: changes to SAM infrastructure require updating two locations, plugins drift out of sync, and the python3-development plugin is burdened with language-agnostic code it shouldn't own.

The consolidation task reorganizes these scattered components into a single source of truth in the development-harness plugin:

1. **Phase A (Deletion)**: Remove 5 duplicate skill directories from python3-development (clear-cove-task-design/, generate-task/, planner-rt-ica/, validation-protocol/) and the implementation-manager SKILL.md file, while preserving the implementation-manager/scripts/ directory temporarily for Phase B.

2. **Phase B (Script Migration)**: Move 3 hook scripts (task_status_hook.py, task_format.py, get_task_context.py) from python3-development/skills/implementation-manager/scripts/ to development-harness/skills/implementation-manager/scripts/. Delete two superseded files (implementation_manager.py and test_task_parsing.py). Clean stale .pyc files in dh.

3. **Phase B.5 (Language Manifest)**: Create a python3-development language manifest (agents.yaml) with 5 role mappings (feature-researcher, codebase-analyzer, python-cli-design-spec, swarm-task-planner, plan-validator) to enable role resolution in skills that reference agent names.

4. **Phase C (Skill Moves)**: Copy 4 workflow skills (implement-feature, start-task, complete-implementation, add-new-feature) and 2 agents (t0-baseline-capture, tn-verification-gate) to development-harness, plus the subagent-contract skill.

5. **Phase D (Reference Updates)**: Update `.claude/rules/local-workflow.md` to reference dh paths instead of python3-development paths. Update skill frontmatter to use role resolution instead of hardcoded agent names (add `agent_role_mapping_file:` field).

6. **Phase E (Validation)**: Run skilllint on both plugins to ensure zero validation errors and verify the sam CLI produces valid JSON.

The execution loop for this plan spans 8 tasks with parallelization: T01 and T02 run in parallel (independent deletions/migrations), T03 (language manifest) is also independent. T04 (skill moves) depends on T02 (scripts must be in dh first). T05-T08 (reference updates and validation) depend on all prior phases.

### For New Feature Implementation: What Needs to Connect

The consolidation affects three major subsystems that implementations will interact with:

**1. Hook Scripts (task_status_hook.py, task_format.py, get_task_context.py)**
These execute during `/implement-feature` and `/start-task` workflows. Currently in python3-development/skills/implementation-manager/scripts/, they must move to development-harness/skills/implementation-manager/scripts/ during Phase B. After migration, the hook registration in SKILL.md files will reference the new dh paths. Any task that reads/updates task file status depends on these hooks working correctly.

**2. Workflow Skills (implement-feature, start-task, complete-implementation, add-new-feature)**
These currently exist in both plugins (duplicates). The canonical source becomes development-harness after Phase C. They reference agents by name (feature-researcher, codebase-analyzer, t0-baseline-capture, tn-verification-gate, etc.). After Phase D, skills will use role resolution instead of hardcoded agent names — the `agent_role_mapping_file` field in YAML frontmatter will route agent references to plugin-specific manifests.

**3. Local Workflow Documentation (.claude/rules/local-workflow.md)**
This orchestration guide currently has two categories of path references: (a) agent file locations (plugins/python3-development/agents/*, plugins/development-harness/agents/*), and (b) skill script locations (task_status_hook.py, task_format.py). Phase D updates section "Agent File Locations" and "Supporting Scripts" to reflect the new consolidation (agents migrate to dh, hooks migrate to dh). Any reference to python3-development paths for language-agnostic SAM code must be updated to development-harness paths.

**4. Plugin Manifests (plugin.json, CLAUDE.md files)**
The python3-development CLAUDE.md currently documents SAM workflow integration. After consolidation, that documentation moves to development-harness CLAUDE.md. The python3-development plugin will remove SAM skill/agent references and retain only language-specific components (python-cli-architect, python-pytest-architect, code-reviewer, etc.). Phase B.5 adds agents.yaml to python3-development as a language manifest enabling role resolution.

### Technical Reference Details

**Key Files Modified Across Phases**

Phase A (Deletions):
- `plugins/python3-development/skills/clear-cove-task-design/` — DELETE entire directory
- `plugins/python3-development/skills/generate-task/` — DELETE entire directory
- `plugins/python3-development/skills/planner-rt-ica/` — DELETE entire directory
- `plugins/python3-development/skills/validation-protocol/` — DELETE entire directory
- `plugins/python3-development/skills/implementation-manager/SKILL.md` — DELETE file only (preserve scripts/ subdirectory)

Phase B (Hook Script Migration):
- SOURCE: `plugins/python3-development/skills/implementation-manager/scripts/task_status_hook.py`, `task_format.py`, `get_task_context.py`
- DESTINATION: `plugins/development-harness/skills/implementation-manager/scripts/` (must exist after T02)
- DELETE: `plugins/python3-development/skills/implementation-manager/scripts/implementation_manager.py`, `test_task_parsing.py`
- CLEAN: `.pyc` files in `plugins/development-harness/skills/implementation-manager/`

Phase B.5 (Language Manifest):
- CREATE: `plugins/python3-development/agents.yaml` with 5 role mappings

Phase C (Skill Moves):
- COPY: `plugins/python3-development/skills/{implement-feature,start-task,complete-implementation,add-new-feature}/` → development-harness equivalents (verify canonical dh copies exist first)
- COPY: `plugins/python3-development/agents/{t0-baseline-capture,tn-verification-gate}/` → development-harness equivalents
- COPY: `plugins/python3-development/skills/subagent-contract/` → development-harness equivalents

Phase D (Reference Updates):
- UPDATE: `.claude/rules/local-workflow.md` — Replace all python3-development SAM paths with development-harness paths (sections: Agent File Locations, Supporting Scripts)
- UPDATE: `plugins/development-harness/skills/{add-new-feature,complete-implementation}/SKILL.md` — Add `agent_role_mapping_file: plugins/development-harness/agents-manifest.yaml` and replace hardcoded agent names with role references

Phase E (Validation):
- RUN: `uv run skilllint check plugins/python3-development/` — expect zero errors
- RUN: `uv run skilllint check plugins/development-harness/` — expect zero errors
- RUN: `uv run sam list` — expect valid JSON output

**Backlog Items**

- #957: Consolidate SAM workflow skills — remove 5 duplicate skill directories from python3-development
- #958: Consolidate SAM workflow skills — migrate hook scripts from python3-development to dh
- #959: Consolidate SAM workflow skills — migrate 4 skills + 2 agents to dh, update references, validate

**Architecture Documents**

- `plan/architect-consolidate-sam-workflow-skills.md` — Phase definitions, role resolution design, detailed task breakdown
- `plan/feature-context-consolidate-sam-workflow-skills.md` — Problem statement, impact analysis, implementation constraints

**Task Dependency DAG**

Phases: A (Deletion) and B (Script Migration) are independent and parallel. B.5 (Language Manifest) is also independent. C (Skill Moves) depends on B. D (Reference Updates) depends on A+B+C. E (Validation) depends on D. Role resolution (T07, T08) depends on T03 (manifest) and T04 (skill moves).
