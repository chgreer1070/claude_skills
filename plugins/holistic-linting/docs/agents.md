# Agents Reference

The holistic-linting plugin provides two specialized agents for systematic linting error resolution and architectural validation.

---

## linting-root-cause-resolver

**Description**: Resolves linting and type checking errors by investigating root causes rather than silencing symptoms. Researches linting rules using linter-specific methods, reads code and architectural context, loads python3-development skill, and elegantly rewrites code to fix underlying issues.

**Model**: Inherits from session

**Permission Mode**: Default

**Color**: Orange

---

### When to Delegate

Delegate to this agent when:

- Ruff reports code quality issues (rule codes E, F, W, B, S, I, UP, etc.)
- MyPy reports type checking errors (attr-defined, arg-type, return-value, etc.)
- Pyright/basedpyright reports type safety issues (reportGeneralTypeIssues, reportOptionalMemberAccess, etc.)
- Multiple files need systematic linting resolution
- You need comprehensive investigation and resolution artifacts

**Trigger Examples**:

```text
Context: ruff reports code quality issues
User: "I'm getting ruff errors F401 (unused import) and E501 (line too long) in auth.py"
Action: Delegate to linting-root-cause-resolver
```

```text
Context: mypy reports type checking errors
User: "mypy is complaining about 'error: Incompatible return value type' in my API client"
Action: Delegate to linting-root-cause-resolver
```

```text
Context: pyright reports type safety issues
User: "pyright shows 'reportGeneralTypeIssues' error on line 45 of database.py"
Action: Delegate to linting-root-cause-resolver
```

---

### Delegation Pattern

**Single File**:

```text
Task(
  agent="linting-root-cause-resolver",
  prompt="Format, lint, and resolve any issues in src/auth.py"
)
```

**Multiple Files (Concurrent)**:

```text
Task(agent="linting-root-cause-resolver", prompt="Format, lint, and resolve any issues in src/auth.py")
Task(agent="linting-root-cause-resolver", prompt="Format, lint, and resolve any issues in src/models.py")
Task(agent="linting-root-cause-resolver", prompt="Format, lint, and resolve any issues in tests/test_auth.py")
```

**With Specific Context**:

```text
Task(
  agent="linting-root-cause-resolver",
  prompt="Ruff reports F401 (unused import) and mypy reports arg-type error in src/api_client.py. Investigate and fix root causes."
)
```

---

### What the Agent Does

**Mandatory First Step**: Load skills
1. Activate holistic-linting skill (contains complete resolution workflows)
2. Activate python3-development skill (ensures Python 3.11+ patterns)

**Resolution Process**:

The agent follows linter-specific workflows from the holistic-linting skill:

#### For Ruff Issues

1. Research rule: `ruff rule {RULE_CODE}`
2. Read affected code
3. Check architectural context (grep for usage patterns)
4. Implement elegant fix following python3-development patterns
5. Verify: `ruff check <file>`

#### For MyPy Issues

1. Research error code in local mypy documentation cache
2. Trace type flow through code
3. Check architectural context
4. Implement type annotation or implementation fix
5. Verify: `mypy <file>`

#### For Pyright Issues

1. Research diagnostic rule using MCP Ref tool or basedpyright docs
2. Read affected code and understand type inference
3. Check architectural context
4. Add type narrowing, annotations, or guards
5. Verify: `pyright <file>` or `basedpyright <file>`

---

### Output Artifacts

The agent produces structured artifacts for the post-linting-architecture-reviewer:

**Directory Structure**:

```text
.claude/
├── reports/
│   ├── linting-investigation-[topic]-[timestamp].md
│   └── linting-resolution-[topic]-[timestamp].md
├── artifacts/
│   └── linting-artifacts-[topic]-[timestamp].json
└── knowledge/
    └── (agent-internal notes, gitignored)
```

**Investigation Report** (`.claude/reports/linting-investigation-*.md`):

```markdown
# Linting Investigation Report - 2026-01-18

## Issues Analyzed
- src/auth.py:45 - F401: 'os' imported but unused
- src/auth.py:89 - E501: line too long (102 > 88)
- src/auth.py:120 - mypy error: Incompatible return value type

## Investigation Process
1. Researched F401 using `ruff rule F401`
   - Rule prevents namespace clutter and typo hiding
   - Fix: Remove unused import or use it

2. Researched E501 using `ruff rule E501`
   - Rule enforces line length limit (88 chars default)
   - Fix: Break line or suppress if string literal

3. Researched mypy return-value error code
   - Function signature: def get_token() -> str:
   - Actual return: return {"token": "..."}
   - Type mismatch: dict returned instead of str

## Root Causes Identified
1. os module imported but never used (copy-paste artifact)
2. Long line from complex f-string (line 89)
3. Function signature wrong - should return dict, not str (line 120)
```

**Resolution Summary** (`.claude/reports/linting-resolution-*.md`):

```markdown
# Linting Resolution: auth.py - 2026-01-18

### Linting Resolution: F401 - Unused Import

**Investigation Summary:**
- Original assumption: os module needed for environment variables
- Actual finding: os module never referenced in file
- Pattern discovered: Other files use os.environ, this one doesn't

**Architectural Insights:**
- Authentication module doesn't access environment directly
- Config module handles all environment variable access
- This enforces separation of concerns

**Review Focus Areas:**
1. Verify no other unused imports in authentication modules
2. Check if config module pattern is documented in CLAUDE.md
3. Ensure consistent environment variable access pattern

**Follow-up Tasks:**
- [ ] Document config module pattern in CLAUDE.md
- [ ] Check other auth files for similar unused imports

---

### Linting Resolution: mypy return-value - Type Annotation Mismatch

**Investigation Summary:**
- Original assumption: Function returns string token
- Actual finding: Function returns complete token response dict
- Pattern discovered: All API methods return structured dicts

**Architectural Insights:**
- API layer returns raw response dictionaries
- Service layer extracts specific values
- This follows API client pattern in CLAUDE.md

**Review Focus Areas:**
1. Verify all API methods have correct return type annotations
2. Check consistency of dict structure across API methods
3. Validate service layer properly extracts values

**Follow-up Tasks:**
- [ ] Add TypedDict for token response structure
- [ ] Review other API method return types
```

---

### Final Handoff

After completing resolution, the agent recommends:

```text
"I've completed linting resolution following the [Ruff/Mypy/Pyright] workflow from the holistic-linting skill. All artifacts are documented in .claude/reports/. I recommend using the post-linting-architecture-reviewer agent to perform comprehensive architectural review based on these findings."
```

---

## post-linting-architecture-reviewer

**Description**: Performs architectural review after linting-root-cause-resolver completes. Verifies resolution quality by examining artifacts in `.claude/reports/` and `.claude/artifacts/`. Checks that fixes align with codebase patterns, validates architectural implications, and identifies systemic improvements.

**Model**: Haiku (fast read-only analysis)

**Permission Mode**: Default

**Color**: Yellow

---

### When to Delegate

Delegate to this agent when:

- linting-root-cause-resolver has completed and created artifacts
- You need architectural validation of linting resolutions
- You want to identify systemic improvements based on linting patterns
- You need verification that fixes align with codebase conventions

**Trigger Examples**:

```text
Context: linting-root-cause-resolver completed and created artifacts
User: "Perform architectural review based on linting resolution artifacts"
Action: Delegate to post-linting-architecture-reviewer
```

```text
Context: Type errors resolved in GitLab service
User: "Review the architecture after those GitLab API fixes"
Action: Delegate to post-linting-architecture-reviewer
```

---

### Delegation Pattern

**After Single File Resolution**:

```text
Task(
  agent="post-linting-architecture-reviewer",
  prompt="Review linting resolution for src/auth.py"
)
```

**After Multi-File Resolution**:

```text
Task(
  agent="post-linting-architecture-reviewer",
  prompt="Review linting resolution artifacts from auth module refactoring"
)
```

**With Specific Focus**:

```text
Task(
  agent="post-linting-architecture-reviewer",
  prompt="Review type safety architecture after resolving mypy errors in API client"
)
```

---

### What the Agent Does

**Prerequisites Verification**:

The agent first checks for resolution artifacts:

```bash
ls -la .claude/reports/linting-investigation-*.md
ls -la .claude/reports/linting-resolution-*.md
ls -la .claude/artifacts/linting-artifacts-*.json
```

If artifacts missing: STOP and inform user to run linting-root-cause-resolver first.

**Review Process**:

1. **Load Resolution Context**
   - Read investigation report (root cause analysis)
   - Read resolution summary (patterns discovered)
   - Read structured artifacts (review data)
   - Identify modified files list

2. **Verify Resolution Quality**
   - Check fixes address root causes (not symptom suppression)
   - Verify solutions align with discovered codebase patterns
   - Confirm type safety maintained or improved
   - Validate no new technical debt introduced
   - Ensure python3-development skill standards followed

3. **Architectural Impact Analysis**

   Review broader implications across dimensions:

   - **Design Principles**: SRP, separation of concerns, dependency injection
   - **Code Organization**: Service layer usage, file/class size, module boundaries
   - **Type Safety**: Enum usage, error handling, API response handling
   - **Code Quality**: String centralization, documentation, CLAUDE.md conventions
   - **Testing**: Unit testability, edge case coverage, mocking
   - **Performance/Security**: Async patterns, resource management, data protection
   - **State Management**: Stateless design, encapsulation, side effect isolation

4. **Output Structured Review**

   Save to `.claude/reports/architectural-review-[timestamp].md` with:
   - Resolution verification results (PASS/ISSUES FOUND)
   - Architectural findings by impact area
   - Concrete code solutions following codebase patterns
   - Implementation steps and testing requirements
   - Systemic improvements applicable across codebase
   - Knowledge capture for reusable patterns

---

### Output Structure

**Architectural Review Report** (`.claude/reports/architectural-review-*.md`):

```markdown
# Post-Linting Architectural Review - 2026-01-18

## Resolution Context
- Files reviewed: src/auth.py, src/models.py
- Issues resolved: 7 (F401, E501, mypy arg-type, mypy return-value)
- Patterns discovered:
  - Config module handles all environment access
  - API methods return structured dicts
  - Service layer extracts specific values
- Artifacts reviewed:
  - .claude/reports/linting-investigation-auth-20260118.md
  - .claude/reports/linting-resolution-auth-20260118.md

## Verification Results

### Resolution Quality: PASS

✓ All fixes address root causes (no symptom suppression)
✓ Solutions align with discovered codebase patterns
✓ Type safety improved (added TypedDict for API responses)
✓ No new technical debt introduced
✓ Python 3.11+ standards followed (native generics, | union syntax)

## Architectural Findings

### Type Safety - API Response Handling - Priority: High

**Original Issue**: mypy return-value error at auth.py:120
**Pattern Applied**: API methods return structured dicts, service layer extracts values
**Finding**: Inconsistent return type annotations across API methods create type safety gaps

**Proposed Solution**:

```python
from typing import TypedDict

class TokenResponse(TypedDict):
    token: str
    expires_in: int
    refresh_token: str

class UserResponse(TypedDict):
    id: str
    email: str
    name: str

def get_token() -> TokenResponse:
    return {"token": "...", "expires_in": 3600, "refresh_token": "..."}

def get_user() -> UserResponse:
    return {"id": "...", "email": "...", "name": "..."}
```

**Implementation**:

1. Create `src/types/api_responses.py` with TypedDict definitions
2. Update all API methods in `src/api_client.py` to use typed returns
3. Update service layer methods to leverage precise types
4. Run mypy to verify type flow correctness

**Testing Requirements**:
- Unit tests for API client methods with typed returns
- Integration tests verifying service layer extraction logic

### Code Organization - Environment Variable Access - Priority: Medium

**Original Issue**: F401 unused os import in auth.py
**Pattern Applied**: Config module centralizes environment access
**Finding**: Pattern exists but not documented, leading to inconsistent usage

**Proposed Solution**:

Document in CLAUDE.md:

```markdown
## Architecture Patterns

### Environment Variable Access

**PRINCIPLE**: Centralize all environment variable access in config module.

**PATTERN**:
- Config module (`src/config.py`) reads `os.environ` once at startup
- Other modules import from config, never use os.environ directly
- Benefits: Testability, type safety, single source of truth

**EXAMPLE**:

```python
# ✅ Correct: Use config module
from src.config import settings
api_key = settings.API_KEY

# ❌ Wrong: Direct os.environ access
import os
api_key = os.environ["API_KEY"]
```
```

**Implementation**:

1. Add Environment Variable Access section to CLAUDE.md
2. Audit all modules for direct os.environ usage
3. Refactor violations to use config module
4. Add linting rule to catch future violations

## Systemic Improvements

1. **Add TypedDict for all API responses** - Priority: High, Effort: Medium
   - Creates type safety across API/service boundary
   - Prevents similar mypy errors in future
   - Enables IDE autocomplete for response fields

2. **Document architecture patterns in CLAUDE.md** - Priority: Medium, Effort: Low
   - Prevents rediscovering patterns through linting errors
   - Accelerates onboarding for new code
   - Provides authoritative reference for AI agents

3. **Create pre-commit hook for environment variable usage** - Priority: Low, Effort: Low
   - Catches direct os.environ usage before commit
   - Enforces config module pattern automatically

## Knowledge Capture

Documented in `.claude/knowledge/linting-patterns.md`:

- **Pattern**: API methods return TypedDict for type safety
- **Resolution Strategy**: Research error code → Trace type flow → Add precise annotation
- **Architectural Insight**: Centralized env var access improves testability and type safety
```

---

### Integration with Resolver Phase

This agent completes a two-phase workflow:

```text
Phase 1 (linting-root-cause-resolver):
  → Investigate root causes
  → Create artifacts
  → Fix issues at source
  → Verify with linters

Phase 2 (post-linting-architecture-reviewer):
  → Load resolver artifacts
  → Verify resolution quality
  → Validate architecture
  → Identify systemic improvements
```

The resolver artifacts are the authoritative context. The reviewer's role is verification and systemic improvement identification, not re-investigation.

---

### Permission Behavior

Both agents use default permission mode - they will request permission for file modifications and tool usage as needed.

---

## Installation

Install agents to your preferred scope using the provided script:

```bash
# Install to user scope (~/.claude/agents/)
python holistic-linting/scripts/install-agents.py --scope user

# Install to project scope (<git-root>/.claude/agents/)
python holistic-linting/scripts/install-agents.py --scope project

# Overwrite existing agent file
python holistic-linting/scripts/install-agents.py --scope user --force
```

---

## Agent Workflow Example

**Complete two-phase workflow**:

```text
1. Orchestrator completes implementation:
   → [User: "Add JWT authentication"]
   → [Orchestrator: Implements auth.py]

2. Orchestrator delegates to resolver:
   → Task(agent="linting-root-cause-resolver", prompt="Format, lint, and resolve any issues in auth.py")

3. Resolver executes:
   → Loads holistic-linting and python3-development skills
   → Formats: ruff format auth.py
   → Lints: ruff check + mypy + pyright
   → Finds 5 issues (2 ruff, 3 mypy)
   → Researches each rule/error code
   → Implements elegant fixes
   → Verifies: All linters pass
   → Creates artifacts in .claude/reports/

4. Orchestrator delegates to reviewer:
   → Task(agent="post-linting-architecture-reviewer", prompt="Review linting resolution for auth.py")

5. Reviewer executes:
   → Loads resolution artifacts
   → Verifies resolution quality: PASS
   → Analyzes architectural implications
   → Identifies 2 systemic improvements
   → Creates review report in .claude/reports/

6. Orchestrator reads review:
   → Read(".claude/reports/architectural-review-20260118.md")
   → Confirms clean resolution and notes improvements
   → Task complete ✓
```

---

[← Back to README](../README.md)
