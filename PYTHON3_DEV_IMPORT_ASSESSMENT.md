# Python3-Development Plugin Import Assessment

**Date**: 2026-01-29
**Assessed By**: Plugin Assessor Agent
**Source**: gitlab-runner-management repository
**Target**: python3-development plugin

## Executive Summary

- **Overall Status**: ⚠️ Requires Corrections
- **Files Analyzed**: 19 (7 skills + 11 agents + 1 script utility)
- **Critical Issues**: 3
- **Warnings**: 8
- **Integration Status**: Partially integrated - needs path and reference updates

### Key Findings

1. **CRITICAL**: Missing `subagent-contract` skill referenced by 10 agents
2. **CRITICAL**: Hardcoded `packages/reset_all_tokens/` paths in scripts and documentation
3. **CRITICAL**: Package-specific context prevents reusability across Python projects
4. **WARNING**: Plugin integration complete in plugin.json but cross-references broken
5. **WARNING**: Skills reference external package structure not applicable to general Python development

## 1. Discovery Summary

| Category | Count | Status |
|----------|-------|--------|
| Development Skills | 6 | ✅ Registered in plugin.json |
| Implementation Manager Skill | 1 | ✅ Registered in plugin.json |
| Imported Agents | 11 | ✅ All registered in plugin.json |
| Scripts | 2 | ⚠️ Contain hardcoded paths |
| Missing Dependencies | 1 | ❌ subagent-contract skill |

**Development Skills**:
- `development/add-new-feature/SKILL.md`
- `development/implement-feature/SKILL.md`
- `development/start-task/SKILL.md`
- `development/complete-implementation/SKILL.md`
- `development/create-feature-task/SKILL.md`
- `development/use-command-template/SKILL.md`

**Implementation Manager**:
- `implementation-manager/SKILL.md`

**Imported Agents**:
- `context-refinement.md`
- `context-gathering.md`
- `code-reviewer.md`
- `codebase-analyzer.md`
- `feature-researcher.md`
- `feature-verifier.md`
- `integration-checker.md`
- `doc-drift-auditor.md`
- `plan-validator.md`
- `swarm-task-planner.md`
- `service-documentation.md`

## 2. Critical Issues

### Issue #1: Missing Skill Dependency - `subagent-contract`

**Severity**: CRITICAL
**Impact**: 10 agents cannot function without this skill

**Affected Agents**:
1. `codebase-analyzer.md` - line 6: `skills: subagent-contract`
2. `code-reviewer.md` - line 7: `skills: subagent-contract, python3-development, holistic-linting`
3. `context-gathering.md` - line 6: `skills: subagent-contract`
4. `context-refinement.md` - line 6: `skills: subagent-contract`
5. `doc-drift-auditor.md` - line 7: `skills: subagent-contract`
6. `feature-researcher.md` - line 6: `skills: subagent-contract`
7. `feature-verifier.md` - line 7: `skills: subagent-contract, python3-development`
8. `integration-checker.md` - line 5: `skills: subagent-contract`
9. `plan-validator.md` - line 6: `skills: subagent-contract`
10. `service-documentation.md` - line 7: `skills: subagent-contract`

**Evidence**: The skill `subagent-contract` does not exist in:
- `plugins/python3-development/skills/subagent-contract/` - NOT FOUND
- Searched across all plugins - NOT FOUND

**Recommendation**:
- **Option A**: Create the missing `subagent-contract` skill based on the output format patterns used in agents
- **Option B**: Remove the skill reference and update agents to work without it
- **Option C**: Import the skill from gitlab-runner-management repository if it exists there

### Issue #2: Hardcoded Repository Paths in Scripts

**Severity**: CRITICAL
**Impact**: Scripts will fail for any project that doesn't have `packages/reset_all_tokens/` structure

**Location**: `plugins/python3-development/skills/implementation-manager/scripts/implementation_manager.py`

**Line 508**:
```python
plan_dir = project_path / "packages" / "reset_all_tokens" / "plan"
```

**Problem**: This hardcodes the gitlab-runner-management repository structure

**Recommendation**: Make the plan directory configurable via:
1. Environment variable (e.g., `${CLAUDE_PROJECT_PLAN_DIR}`)
2. Command-line argument
3. Look for `plan/` directory relative to project root as fallback

**Suggested Fix**:
```python
# Option 1: Environment variable with fallback
plan_subdir = os.getenv("PLAN_SUBDIR", "plan")
plan_dir = project_path / plan_subdir

# Option 2: Search for plan directory
def find_plan_dir(project_path: Path) -> Path | None:
    # Try common locations
    candidates = [
        project_path / "plan",
        project_path / "plans",
        project_path / ".claude" / "plan",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None
```

### Issue #3: Package-Specific Context in Agents

**Severity**: CRITICAL
**Impact**: Agents are not reusable for general Python development

**Affected Files**: ALL agents contain `reset_all_tokens` specific documentation

**Examples**:

**context-gathering.md** (lines 13-46):
```markdown
You are part of the `/add-new-feature` → `/implement-feature` → `/start-task` workflow for the **reset_all_tokens** package.

**Core Implementation Files**:
- `cli/commands.py` - Existing command patterns and orchestration
- `cli/host_parsing.py` - Host parsing and validation utilities
- `core/*.py` - Business logic modules (runner.py, health.py, compliance_operations.py, etc.)
- `ssh/*.py` - SSH protocols, auth, and command execution
- `compliance/*.py` - Pure compliance checking functions
- `config_management/*.py` - Config pull/push/diff operations
```

**doc-drift-auditor.md** (lines 32-50):
```markdown
For the `reset_all_tokens` package, audit these documentation files:
- `CLAUDE.md` - Root project instructions
- `packages/reset_all_tokens/CLAUDE.md` - Package-specific documentation
- `packages/reset_all_tokens/architecture.md` - Architecture reference
```

**Recommendation**:
1. **Generalize agent documentation** - Remove reset_all_tokens specific references
2. **Use template variables** - Replace hardcoded paths with `${PROJECT_ROOT}`, `${PLAN_DIR}`, etc.
3. **Make agents project-agnostic** - Focus on Python development patterns, not specific package structures

## 3. Warnings

### Warning #1: Skill Reference Format

**Location**: `code-reviewer.md` line 7
**Reference**: `skills: subagent-contract, python3-development, holistic-linting`

**Issue**: `holistic-linting` exists as a separate plugin, not within python3-development

**Status**: ⚠️ May work if plugin is loaded, but reference format unclear

**Recommendation**: Verify skill reference format for cross-plugin dependencies

### Warning #2: Agent Skill References

**Pattern**: Many agents reference `python3-development` as a skill

**Locations**:
- `code-reviewer.md` line 7: `skills: subagent-contract, python3-development, holistic-linting`
- `feature-verifier.md` line 7: `skills: subagent-contract, python3-development`

**Issue**: `python3-development` is a plugin name, not a skill name. The skill is at `plugins/python3-development/skills/python3-development/SKILL.md`

**Status**: ⚠️ May work but unclear if plugin names can be used as skill references

**Recommendation**: Use explicit skill path or verify that plugin names resolve to main skill

### Warning #3: External Repository Structure Assumptions

**Pattern**: Skills assume `plan/` directory exists with SAM-style task files

**Locations**:
- All development skills reference `plan/feature-context-{slug}.md`
- All development skills reference `plan/tasks-{N}-{slug}.md`
- Scripts look for task files in `plan/` directory

**Issue**: This workflow pattern may not apply to all Python projects

**Recommendation**:
1. Document that these skills require SAM workflow adoption
2. Provide guidance on setting up `plan/` directory structure
3. Consider making workflow optional or configurable

### Warning #4: Hook Script Paths

**Status**: ✅ Correctly implemented

**Evidence**: Skills use `${CLAUDE_PLUGIN_ROOT}` correctly

**Examples**:
- `implement-feature/SKILL.md` line 13: `command: "python3 \"${CLAUDE_PLUGIN_ROOT}/skills/implementation-manager/scripts/task_status_hook.py\""`
- `start-task/SKILL.md` line 14: `command: "python3 \"${CLAUDE_PLUGIN_ROOT}/skills/implementation-manager/scripts/task_status_hook.py\""`

**No action needed** - hooks are properly configured for plugin portability

### Warning #5: Missing Back-References

**Pattern**: Reference files don't link back to parent SKILL.md

**Status**: ⚠️ Not applicable - these skills don't use progressive disclosure pattern

**Note**: All skills are single-file SKILL.md without external references/

### Warning #6: Agent Tool Restrictions

**Pattern**: Many agents specify explicit tool allowlists

**Examples**:
- `codebase-analyzer.md` line 4: `tools: Read, Bash, Grep, Glob, Write, mcp__git-forensics__*, mcp__Ref__*, mcp__exa__*`
- `feature-researcher.md` line 5: `tools: Read, Grep, Glob, Write, mcp__Ref__*, mcp__exa__*, mcp__sequential_thinking__*`

**Issue**: These tools reference MCP servers that may not be available in all installations

**Recommendation**: Document MCP server requirements or make them optional

### Warning #7: Permission Mode Usage

**Pattern**: Some agents use elevated permission modes

**Examples**:
- `code-reviewer.md` line 5: `permissionMode: acceptEdits`
- `service-documentation.md` line 5: `permissionMode: acceptEdits`

**Status**: ⚠️ Acceptable for their use case (code review, documentation updates)

**Note**: These agents are designed to make edits automatically - permission mode is appropriate

### Warning #8: Model Specifications

**Pattern**: Agents specify specific Claude models

**Examples**:
- `context-gathering.md` line 4: `model: sonnet`
- `context-refinement.md` line 4: `model: sonnet`
- `feature-verifier.md` line 5: `model: opus`
- `plan-validator.md` line 6: `model: opus`

**Status**: ⚠️ May fail if specified model is unavailable

**Recommendation**: Consider using `inherit` or document model requirements

## 4. Skills Assessment Details

### add-new-feature

**Location**: `plugins/python3-development/skills/development/add-new-feature/SKILL.md`
**Status**: ✅ Valid frontmatter, ⚠️ Package-specific

**Frontmatter**:
```yaml
name: add-new-feature
description: "SAM-style feature initiation workflow..."
version: "1.0.0"
user-invocable: true
argument-hint: "<feature description or existing doc path>"
```

**Issues**:
- Lines 16-18: References specific directory structure (`plan/feature-context-{slug}.md`, `plan/codebase/{FOCUS}.md`)
- Lines 34, 40, 63, 80: Delegates to agents (feature-researcher, codebase-analyzer, python-cli-design-spec, swarm-task-planner)
- Agent references may not exist in this plugin

**Recommendations**:
1. Verify all referenced agents exist
2. Make directory paths configurable
3. Document SAM workflow requirements

### implement-feature

**Location**: `plugins/python3-development/skills/development/implement-feature/SKILL.md`
**Status**: ✅ Valid frontmatter, ✅ Hooks configured correctly

**Frontmatter**:
```yaml
name: implement-feature
description: "Execute a SAM task plan..."
version: "1.0.0"
user-invocable: true
argument-hint: "<task-file-path or feature-slug>"
hooks:
  SubagentStop:
    - hooks:
        - type: command
          command: "python3 \"${CLAUDE_PLUGIN_ROOT}/skills/implementation-manager/scripts/task_status_hook.py\""
```

**Hook Configuration**: ✅ CORRECT - uses `${CLAUDE_PLUGIN_ROOT}`

**Issues**:
- Lines 36, 48, 54: Uses implementation_manager.py script with hardcoded paths
- Line 64: References `start-task` skill (exists)
- Line 76: References `complete-implementation` skill (exists)

### start-task

**Location**: `plugins/python3-development/skills/development/start-task/SKILL.md`
**Status**: ✅ Valid frontmatter, ✅ Hooks configured correctly

**Frontmatter**:
```yaml
name: start-task
description: "Start or complete a specific task inside a SAM task file..."
version: "1.0.0"
user-invocable: true
argument-hint: "<task-file-path> [--task <task-id>] [--complete <task-id>]"
hooks:
  PostToolUse:
    - matcher: "Write|Edit|Bash"
      hooks:
        - type: command
          command: "python3 \"${CLAUDE_PLUGIN_ROOT}/skills/implementation-manager/scripts/task_status_hook.py\""
```

**Hook Configuration**: ✅ CORRECT - uses `${CLAUDE_PLUGIN_ROOT}`

**Issues**:
- Line 58: Creates context file at `.claude/context/active-task-${CLAUDE_SESSION_ID}.json`
- Assumes project has `.claude/` directory

### complete-implementation

**Location**: `plugins/python3-development/skills/development/complete-implementation/SKILL.md`
**Status**: ✅ Valid frontmatter, ⚠️ Agent dependencies

**Frontmatter**:
```yaml
name: complete-implementation
description: "Holistic completion workflow..."
version: "1.0.0"
user-invocable: true
argument-hint: "<task-file-path>"
```

**Issues**:
- Lines 23, 29, 35, 41, 47, 53: References multiple agents (code-reviewer, feature-verifier, integration-checker, doc-drift-auditor, service-documentation, context-refinement)
- All referenced agents exist in plugin.json ✅
- Line 63: References `implement-feature` skill recursively

### create-feature-task

**Location**: `plugins/python3-development/skills/development/create-feature-task/SKILL.md`
**Status**: ⚠️ Conflicts with SAM workflow

**Frontmatter**:
```yaml
name: create-feature-task
description: "This skill should be used when the user asks to create a feature task..."
version: "1.0.0"
user-invocable: true
argument-hint: "<feature_name_and_description>"
```

**Issues**:
- Line 31: Creates task at `.claude/tasks/{feature-name}.md`
- Line 102: References `python-cli-architect` agent (exists)
- This skill creates DIFFERENT task format than SAM workflow
- May conflict with `add-new-feature` skill

**Recommendation**:
- Clarify relationship between this skill and SAM workflow
- Document when to use each
- Consider consolidating or renaming for clarity

### use-command-template

**Location**: `plugins/python3-development/skills/development/use-command-template/SKILL.md`
**Status**: ✅ Valid, ℹ️ Informational

**Frontmatter**:
```yaml
name: use-command-template
description: "This skill should be used when the user asks to create a new skill..."
version: "1.0.0"
user-invocable: true
argument-hint: "<skill_purpose_description>"
```

**Purpose**: Provides template for creating new skills

**Issues**: None - informational skill for skill creation

### implementation-manager

**Location**: `plugins/python3-development/skills/implementation-manager/SKILL.md`
**Status**: ⚠️ Documentation references hardcoded paths

**Frontmatter**:
```yaml
name: implementation-manager
description: "Query and manage feature implementation task status..."
user-invocable: false
disable-model-invocation: false
```

**Issues**:
- Line 20: Example shows `packages/reset_all_tokens/plan/` path
- Line 34: Example path `packages/reset_all_tokens/plan/tasks-1-prepare-host.md`
- Documentation is specific to reset_all_tokens package

**Note**: The skill itself just provides CLI tools, documentation is the issue

## 5. Agents Assessment

All 11 agents are properly registered in plugin.json ✅

### Common Issues Across Agents:

1. **All reference `subagent-contract` skill** - Missing dependency ❌
2. **Many contain `reset_all_tokens` specific documentation** - Reduces reusability ⚠️
3. **Use STATUS/DONE/BLOCKED output format** - Consistent pattern ✅
4. **Specify explicit tool restrictions** - May fail if MCP tools unavailable ⚠️

### Individual Agent Notes:

**context-gathering.md**: Heavily tailored to reset_all_tokens package structure
**context-refinement.md**: References specific package modules
**code-reviewer.md**: References reset_all_tokens architecture
**codebase-analyzer.md**: Designed for reset_all_tokens package exploration
**feature-researcher.md**: Package-agnostic, most reusable ✅
**feature-verifier.md**: Package-agnostic verification logic ✅
**integration-checker.md**: Package-agnostic integration checks ✅
**doc-drift-auditor.md**: Contains reset_all_tokens specific paths
**plan-validator.md**: Package-agnostic plan validation ✅
**swarm-task-planner.md**: References clear-cove-task-design skill (exists) ✅
**service-documentation.md**: References reset_all_tokens documentation structure

## 6. Scripts Assessment

### implementation_manager.py

**Location**: `plugins/python3-development/skills/implementation-manager/scripts/implementation_manager.py`
**Status**: ❌ Contains hardcoded repository paths

**Line 508**: Hardcoded path
```python
plan_dir = project_path / "packages" / "reset_all_tokens" / "plan"
```

**Recommendation**: Make configurable (see Issue #2)

### task_status_hook.py

**Location**: `plugins/python3-development/skills/implementation-manager/scripts/task_status_hook.py`
**Status**: ✅ Package-agnostic, works with any task file path

**No issues found** - Script uses paths from hook input, not hardcoded

## 7. Action Items

### Critical (Must Fix)

- [ ] **Action 1**: Create `subagent-contract` skill or remove references from 10 agents
  - **Files**: All agents in plugins/python3-development/agents/ except swarm-task-planner.md
  - **Line**: `skills: subagent-contract` in frontmatter
  - **Fix**: Either create the skill or remove the reference line

- [ ] **Action 2**: Fix hardcoded path in implementation_manager.py
  - **File**: `plugins/python3-development/skills/implementation-manager/scripts/implementation_manager.py`
  - **Line**: 508
  - **Fix**: Replace with configurable path logic

- [ ] **Action 3**: Generalize agent documentation
  - **Files**: All agents containing `reset_all_tokens` references
  - **Fix**: Replace package-specific examples with generic Python project examples

### Recommended (Should Fix)

- [ ] **Action 4**: Document SAM workflow requirements
  - **File**: Create `plugins/python3-development/README.md` or similar
  - **Content**: Explain SAM workflow, required directory structure, how to set up

- [ ] **Action 5**: Clarify create-feature-task vs add-new-feature
  - **Files**:
    - `plugins/python3-development/skills/development/create-feature-task/SKILL.md`
    - `plugins/python3-development/skills/development/add-new-feature/SKILL.md`
  - **Fix**: Add documentation explaining when to use each

- [ ] **Action 6**: Verify cross-plugin skill references
  - **Test**: Load plugin and verify `holistic-linting` skill is accessible
  - **Document**: Note external plugin dependencies in plugin README

- [ ] **Action 7**: Document MCP server requirements
  - **Agents**: codebase-analyzer, feature-researcher, others using MCP tools
  - **Fix**: Add note about optional MCP servers to agent descriptions

- [ ] **Action 8**: Test agent delegation chains
  - **Verify**: All agent names referenced in skills actually exist
  - **Missing**: python-cli-design-spec (referenced but not in plugin)

### Optional (Nice to Have)

- [ ] **Action 9**: Add progressive disclosure for long agent documentation
  - **Candidates**: swarm-task-planner.md (383 lines)
  - **Fix**: Split into main SKILL.md + references/ for detailed patterns

- [ ] **Action 10**: Standardize model specifications
  - **Files**: All agents with `model: sonnet` or `model: opus`
  - **Consider**: Using `inherit` or documenting model requirements

## 8. Integration Verification

### Plugin.json Registration: ✅ COMPLETE

All skills and agents are properly registered in:
`plugins/python3-development/.claude-plugin/plugin.json`

**Skills registered**: 17 ✅
**Agents registered**: 11 ✅

### Cross-References: ⚠️ PARTIALLY BROKEN

**Working References**:
- `implement-feature` → `start-task` ✅
- `implement-feature` → `complete-implementation` ✅
- `complete-implementation` → `implement-feature` (recursive) ✅
- `swarm-task-planner` → `clear-cove-task-design` ✅

**Broken References**:
- All agents → `subagent-contract` ❌
- `add-new-feature` → `python-cli-design-spec` ❌ (agent not in plugin)
- `code-reviewer` → `holistic-linting` ⚠️ (external plugin)

## 9. Recommendations Summary

### Immediate Actions (Before Release)

1. **Remove `subagent-contract` references** from all agent frontmatter
2. **Fix hardcoded paths** in implementation_manager.py
3. **Generalize documentation** to remove reset_all_tokens specific content

### Short-Term Actions (For Usability)

1. **Document SAM workflow** requirements and setup
2. **Create missing agents** (python-cli-design-spec) or remove references
3. **Test delegation chains** to verify all agent references work

### Long-Term Improvements (For Maintainability)

1. **Create subagent-contract skill** if the pattern is valuable
2. **Add progressive disclosure** for long agent documentation
3. **Standardize on model specifications** and document requirements

## Conclusion

The imported skills and agents are **structurally integrated** into the python3-development plugin (all registered in plugin.json with correct paths), but have **semantic issues** that prevent them from working in a general Python development context:

1. **Dependency on non-existent skill** (subagent-contract)
2. **Hardcoded paths** specific to gitlab-runner-management repo
3. **Package-specific documentation** that assumes reset_all_tokens structure

These issues are **fixable** with the action items above. The skills and agents have solid architecture and well-defined patterns - they just need to be generalized for broader use.

**Recommendation**: Apply Critical action items before marking plugin as production-ready.
