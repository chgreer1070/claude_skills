# Commands Reference

This plugin includes a `commands/` directory containing **reference material for creating slash commands**, not deployed commands themselves. These are templates, patterns, and procedural guides for command development.

## Important Distinction

**This directory contains**: Templates and reference material for *creating* commands

**NOT**: Actual deployed slash commands that Claude Code executes

**Deployed commands** (like `/modernpython` and `/shebangpython`) must be installed separately to `~/.claude/commands/` or `.claude/commands/`.

## Directory Structure

```text
commands/
├── README.md                          # Overview of command reference library
├── development/                       # Development workflow command templates
│   ├── config/
│   │   └── command-patterns.yml      # Command taxonomy and organization
│   ├── templates/
│   │   └── command-template.md       # Base template for new commands
│   ├── use-command-template.md       # Meta-command: generate commands
│   └── create-feature-task.md        # Structured feature development
└── testing/                           # Testing workflow command templates
    ├── analyze-test-failures.md      # Test failure investigation
    ├── comprehensive-test-review.md  # Test suite review
    └── test-failure-mindset.md       # Critical thinking for tests
```

## Configuration Files

### command-patterns.yml

**Location**: `commands/development/config/command-patterns.yml`

**Purpose**: Defines organizational structure for command development

**Contents**:
- **Command Categories**: Analysis, Development, Quality, Documentation, Operations
- **Workflow Chains**: Multi-step processes (Feature Development, Bug Fix, Code Review)
- **Context Sharing**: Information flow between commands
- **Cache Patterns**: TTL and invalidation rules
- **Risk Assessment**: Command classification by risk level

**Usage**: Consult this file when creating new commands to understand:
- Which category your command belongs to
- How it fits into existing workflow chains
- What risk level it represents
- What context it should preserve for downstream commands

---

## Command Templates

### command-template.md

**Location**: `commands/development/templates/command-template.md`

**Purpose**: Standard structure for creating new slash commands

**Structure**:
```markdown
---
description: Brief description for /help
argument-hint: [arg1] [arg2]
---

# Command Title

## Purpose
Single sentence describing what the command does

## Task
Detailed task description using $ARGUMENTS placeholder

## Execution Steps
1. Analysis phase
2. Implementation phase
3. Validation phase

## Context Preservation
What information to cache for later commands

## Expected Output
Format and structure of command output

## Integration Points
- Prerequisites: What must exist before running
- Follow-ups: Natural next commands
- Related: Similar or complementary commands
```

**Usage**: Copy this template when creating new commands

**Key Elements**:
- **Purpose**: Single-sentence description
- **Arguments**: Use `$ARGUMENTS` for all args, `$1`, `$2`, etc. for positional
- **Phased Execution**: Break into Analysis → Implementation → Validation
- **Context Rules**: Define what gets cached for reuse
- **Integration**: Connect to workflow chains

---

## Meta-Commands

### use-command-template.md

**Location**: `commands/development/use-command-template.md`

**Purpose**: Procedural guide for generating new commands from template

**Workflow**:
1. Parse command purpose from `$ARGUMENTS`
2. Select appropriate category and naming convention
3. Apply template structure with customizations
4. Configure integration with workflow chains
5. Create command file in appropriate location

**Example Usage** (conceptual):
```text
/development:use-command-template validate API endpoints for rate limiting

# Would generate:
# ~/.claude/commands/validate-api-rate-limits.md
# With appropriate structure for validation commands
```

---

## Testing Workflow Templates

### analyze-test-failures.md

**Location**: `commands/testing/analyze-test-failures.md`

**Purpose**: Critical thinking framework for balanced test failure investigation

**Key Principle**: Test failures can indicate bugs in EITHER the test OR the implementation. Avoid confirmation bias.

**Analysis Approach**:
1. **Gather Context**: Test code, implementation code, failure output
2. **Examine Test Logic**: Is the test correct? Does it test the right thing?
3. **Examine Implementation**: Does the code match intended behavior?
4. **Classification**: Test Bug | Implementation Bug | Ambiguous

**Output Format**:
```markdown
## Analysis: test_authentication.py::test_oauth_flow

**Failure Output**: [exact error message]

**Classification**: [Test Bug | Implementation Bug | Ambiguous]

**Evidence**:
- Test expectation: [what test expects]
- Implementation behavior: [what code does]
- Reasoning: [why classified this way]

**Recommendation**: [fix test | fix implementation | investigate further]
```

**Why This Matters**: Prevents rushing to "fix the code" when the test itself is wrong

---

### comprehensive-test-review.md

**Location**: `commands/testing/comprehensive-test-review.md`

**Purpose**: Systematic test suite quality review

**Review Dimensions**:
- Coverage completeness (happy path, edge cases, error conditions)
- Test quality (isolation, clarity, maintainability)
- Assertion appropriateness (meaningful, specific)
- Test organization (naming, grouping, fixtures)
- Performance considerations (slow tests, unnecessary setup)

---

### test-failure-mindset.md

**Location**: `commands/testing/test-failure-mindset.md`

**Purpose**: Mindset and heuristics for test failure analysis

**Core Questions**:
1. What does the test expect?
2. What does the implementation do?
3. Which one is correct?
4. How do we know?

**Heuristics**:
- New test + old code = likely test bug
- Old test + new code = likely implementation bug
- Changed test + changed code = investigate both
- Flaky test = likely test bug (timing, ordering, state)

---

## Using Command Templates

### Creating a New Command

**Step 1: Consult Patterns**

Read `command-patterns.yml` to understand:
- Command categories and naming conventions
- Existing workflow chains
- Risk levels and safeguards

**Step 2: Copy Template**

Start with `command-template.md`:
```bash
cp commands/development/templates/command-template.md ~/.claude/commands/my-new-command.md
```

**Step 3: Customize**

Replace placeholders:
- Update frontmatter (description, argument-hint)
- Define purpose (single sentence)
- Specify task with `$ARGUMENTS` placeholder
- Define execution phases
- Specify context preservation rules
- Define integration points

**Step 4: Deploy**

Place in appropriate location:
- **User commands**: `~/.claude/commands/` (personal, not shared)
- **Project commands**: `.claude/commands/` (team-shared via git)
- **NOT**: This plugin's `commands/` directory (reference only)

### Naming Conventions

Use verb-noun format:

**Analysis Commands**:
- `analyze-*` - Investigate and report
- `scan-*` - Search for patterns
- `validate-*` - Check correctness

**Development Commands**:
- `create-*` - Generate new artifacts
- `implement-*` - Write code
- `fix-*` - Repair defects

**Quality Commands**:
- `test-*` - Run tests
- `review-*` - Assess quality
- `refactor-*` - Improve structure

**Operations Commands**:
- `deploy-*` - Release to environment
- `migrate-*` - Transform data/schema
- `cleanup-*` - Remove obsolete artifacts

### Integration with Workflows

Commands chain together in workflows:

**Feature Development Chain**:
```text
create-feature-task         # Initialize structured task
  ↓
study-current-repo          # Understand codebase
  ↓
implement-feature           # Write code
  ↓
create-test-plan            # Design tests
  ↓
comprehensive-test-review   # Validate quality
  ↓
gh-create-pr                # Submit for review
```

**Bug Fix Chain**:
```text
analyze-test-failures       # Investigate failure
  ↓
fix-implementation          # Repair code
  ↓
validate-fix                # Verify resolution
  ↓
update-tests                # Add regression test
```

**Context Flow**: Each command produces context that subsequent commands use.

---

## Command Patterns Configuration

### Categories

**Analysis**: Investigate, scan, validate, analyze
- Risk: Low (read-only)
- Context: Preserves findings for downstream commands
- Examples: analyze-dependencies, scan-security

**Development**: Create, implement, fix, refactor
- Risk: High (modifies code)
- Context: Preserves implementation decisions
- Examples: implement-feature, fix-bug

**Quality**: Test, review, audit
- Risk: Medium (runs code, may modify tests)
- Context: Preserves quality metrics
- Examples: comprehensive-test-review, validate-coverage

**Documentation**: Document, generate-docs, update-readme
- Risk: Low (modifies docs only)
- Context: Preserves documentation decisions
- Examples: generate-api-docs, update-changelog

**Operations**: Deploy, migrate, cleanup
- Risk: Very High (modifies production)
- Context: Preserves operation results
- Examples: deploy-staging, migrate-database

### Risk Levels

**Low Risk**: Read-only operations, documentation
- No approval required
- Can run automatically

**Medium Risk**: Test modifications, non-critical code
- Review recommended
- Can fail safely

**High Risk**: Code modifications, refactoring
- Approval recommended
- Requires validation

**Very High Risk**: Production operations, destructive actions
- Approval required
- Must have rollback plan

---

## Best Practices

### Command Design

1. **Single Responsibility**: Each command focuses on one clear task
2. **Clear Naming**: Descriptive verb-noun pairs
3. **Example Usage**: Include 3+ concrete examples
4. **Context Definition**: Specify what gets cached
5. **Integration Points**: Define prerequisites and follow-ups

### Command Organization

1. **Category Alignment**: Place in appropriate category subdirectory
2. **Workflow Awareness**: Consider how commands chain
3. **Risk Classification**: Mark high-risk commands appropriately
4. **Documentation**: Keep patterns file updated

### Command Implementation

1. **Argument Handling**: Use `$ARGUMENTS` for all, `$1`/`$2` for positional
2. **Phased Execution**: Break into Analysis → Implementation → Validation
3. **Error Handling**: Define failure modes and recovery
4. **Output Format**: Structured, parseable output

---

## Relationship to Python Development Skill

These command templates support the orchestration patterns described in the python3-development skill:

```text
User Request
    ↓
Orchestrator (uses skill + commands)
    ↓
├─→ @agent-python-cli-architect (implementation)
├─→ @agent-python-pytest-architect (testing)
└─→ @agent-python-code-reviewer (review)
    ↓
Apply standards: /modernpython, /shebangpython (actual deployed commands)
```

**Commands complement agents**:
- **Agents**: Implement code, write tests, review quality
- **Commands**: Provide standards, validation, and workflow structure

---

## External Commands Referenced

The python3-development skill references these external commands (must be installed separately):

### /modernpython

**Location**: `~/.claude/commands/modernpython.md` (not included in this plugin)

**Purpose**: Comprehensive reference guide for Python 3.11+ patterns

**Usage**: Load as reference when writing code
```text
/modernpython [file-path]
```

**Provides**:
- Python 3.11-3.14 feature examples
- PEP citations with research tool guidance
- Legacy patterns to avoid
- Modern alternatives
- Framework-specific guides (Typer, Rich, pytest)

---

### /shebangpython

**Location**: `~/.claude/commands/shebangpython.md` (not included in this plugin)

**Purpose**: Validate and correct shebang for Python scripts

**Usage**: Validate script shebang and PEP 723 metadata
```text
/shebangpython scripts/deploy.py
```

**Actions**:
- Analyzes imports to determine dependency type
- **Corrects shebang** to match script type (edits file)
- **Adds PEP 723 metadata** if external dependencies detected (edits file)
- **Removes PEP 723 metadata** if stdlib-only (edits file)
- Sets execute bit if needed

**Validates**:
- Stdlib-only scripts: `#!/usr/bin/env python3` (no PEP 723)
- Scripts with dependencies: `#!/usr/bin/env -S uv --quiet run --active --script` + PEP 723
- Package executables: `#!/usr/bin/env python3` (dependencies via package)
- Library modules: No shebang (not executable)

---

## Summary

The `commands/` directory in this plugin provides:

**Reference Material**:
- Command structure templates
- Command patterns configuration
- Meta-command generation guides
- Specialized workflow templates

**NOT Included**:
- Actual deployed slash commands
- Commands that Claude Code executes
- `/modernpython` or `/shebangpython` (install separately)

**Usage**:
1. Review `command-patterns.yml` for taxonomy
2. Copy `command-template.md` as starting point
3. Customize for specific command purpose
4. Deploy to `~/.claude/commands/` or `.claude/commands/`
5. Integrate into workflow chains

**Related Documentation**:
- [Skills Reference](./skills.md) - python3-development skill details
- [Examples](./examples.md) - Command usage examples in workflows
- [commands/README.md](../commands/README.md) - Detailed command library overview
