# Skills Reference

This plugin provides a single skill that enforces mandatory verification before implementation actions.

---

## verification-gate

**Location**: `skills/verification-gate/SKILL.md`

**Description**: Enforce mandatory pre-action verification checkpoints to prevent pattern-matching from overriding explicit reasoning. Use this skill when about to execute implementation actions (Bash, Write, Edit) to verify hypothesis-action alignment. Blocks execution when hypothesis unverified or action targets different system than hypothesis identified. Critical for preventing cognitive dissonance where correct diagnosis leads to wrong implementation.

**User Invocable**: Yes (default)

**Model Invocation**: Enabled (Claude can auto-activate via Skill tool)

**Allowed Tools**: Inherits from parent context (no restrictions)

**Model**: Inherits from parent context (no override)

**Context**: Inline (runs in main conversation context)

### When to Use

Claude automatically activates this skill:

**Before Implementation Actions**:
- Any `Bash` command that modifies system state
- Any `Write` operation creating new files
- Any `Edit` operation modifying existing files
- Any `NotebookEdit` operation

**After Hypothesis Formation**:
- When stating what system/component has an issue
- When diagnosing error messages or failures
- When choosing between multiple implementation approaches

**Pattern-Matching Detection**:
- Language like "usually", "typically", "standard approach"
- Solutions appearing immediately without investigation
- Recognizing error patterns and jumping to common solutions

### Activation

**Automatic** (Claude decides based on context):

```text
# Claude detects implementation action pending
# Skill activates automatically
```

**Manual** (user or Claude explicit invocation):

```text
@verification-gate
```

Or via Skill tool:

```text
Skill(command: "verification-gate")
```

### The Four Checkpoints

This skill implements a mandatory gate with four sequential checkpoints. All must pass before execution proceeds.

#### Checkpoint 1: Hypothesis Stated

**Requirement**: Explicitly state what system/component the issue affects.

**Test**:
- Can I name the specific system? (e.g., "PEP 723 inline metadata", "Docker network configuration")
- Have I written this hypothesis explicitly in my response?

**Blocks If**: Hypothesis too vague or not stated

**Example Block**:

```text
BLOCKED - Hypothesis not stated
REQUIRED: State hypothesis explicitly before proceeding
EXAMPLE: "Hypothesis: The issue affects [specific system/component]"
```

---

#### Checkpoint 2: Hypothesis Verified

**Requirement**: Gather evidence to confirm or refute hypothesis.

**Verification Methods**:
- Read relevant files to confirm system state
- Check official documentation (use MCP tools: Ref, exa)
- Test or execute commands to observe behavior
- Grep for configuration or implementation details

**Test**:
- Have I used Read/Grep/MCP tools to gather evidence?
- Can I cite specific files, line numbers, or outputs?

**Blocks If**: No evidence gathered, acting on assumptions

**Example Block**:

```text
BLOCKED - Hypothesis not verified
REQUIRED: Gather evidence before proceeding
NEXT STEPS:
1. Identify what evidence would confirm/refute hypothesis
2. Use appropriate tools to gather that evidence
3. Document findings with file paths and line numbers
4. Revise hypothesis if evidence contradicts it
```

---

#### Checkpoint 3: Hypothesis-Action Alignment

**Requirement**: Planned action must target the SAME system as hypothesis identified.

**Alignment Template**:

```text
┌─────────────────────────────────────────────────────────┐
│ HYPOTHESIS SYSTEM: [What system does hypothesis        │
│                     identify as problem location?]      │
├─────────────────────────────────────────────────────────┤
│ ACTION SYSTEM:     [What system does planned action     │
│                     operate on or modify?]              │
├─────────────────────────────────────────────────────────┤
│ ALIGNMENT CHECK:   [Same system = ✓ Proceed]           │
│                    [Different systems = ✗ BLOCKED]      │
└─────────────────────────────────────────────────────────┘
```

**Common Misalignments**:

| Hypothesis System | Wrong Action System | Why Blocked |
|-------------------|---------------------|-------------|
| PEP 723 inline metadata | `uv sync` (pyproject.toml) | Different dependency systems |
| Docker container config | Host network settings | Different network layers |
| Git repository state | File system permissions | Different system domains |
| Python virtual environment | Global pip install | Different installation scopes |

**Blocks If**: Hypothesis and action target different systems

**Example Block**:

```text
✗ BLOCKED - Hypothesis-action misalignment detected
HYPOTHESIS targets: PEP 723 inline script metadata
ACTION operates on: pyproject.toml dependencies

REQUIRED: Either:
1. Revise action to target same system as hypothesis
2. Revise hypothesis after gathering new evidence
3. Report that systems are unrelated and task needs clarification
```

---

#### Checkpoint 4: Pattern-Matching Detection

**Requirement**: Action must be based on verified project reality, not training data patterns.

**Detection Questions**:
1. Did I read any files in THIS project to verify this approach?
2. Did I check official documentation for THIS version/tool?
3. Is my action based on what THIS project actually uses?
4. Or is my action based on common patterns from training data?

**Pattern-Matching Indicators**:
- Solution appears immediately without investigation
- Executing command within 1-2 tool calls of error observation
- Not using Read/Grep/MCP tools to verify before acting
- Thinking "this is the standard way to do X" without checking project

**Blocks If**: Pattern-matching detected without project verification

**Example Block**:

```text
⚠ PATTERN-MATCHING WARNING
I am using training data patterns without project verification.

REQUIRED actions:
1. State: "I am pattern-matching from training data without verification"
2. Read relevant files to understand current project setup
3. Check project documentation or configuration
4. Verify approach against project reality
5. Return to Checkpoint 2 with gathered evidence
```

---

### Execution Decision

After completing all four checkpoints:

**✓ All Checkpoints Passed**:

```text
VERIFICATION COMPLETE:
✓ Checkpoint 1: Hypothesis stated - [brief hypothesis]
✓ Checkpoint 2: Verified via [files/docs read]
✓ Checkpoint 3: Aligned - both target [system name]
✓ Checkpoint 4: Verified against project reality

EXECUTING: [action description]
```

**✗ Any Checkpoint Failed**:

```text
EXECUTION BLOCKED
Failed checkpoint: [number and name]
Reason: [specific failure reason]
Required before proceeding: [specific next steps]
```

### Reference Files

This skill includes comprehensive reference documentation:

#### [./references/research-foundations.md](../plugins/verification-gate/skills/verification-gate/references/research-foundations.md)

Authoritative research backing the verification gate approach:

- **Chain-of-Verification (CoVe)**: Meta AI Research methodology for factored verification
- **System 2 Attention (S2A)**: Meta AI attention focusing research
- **Anthropic Best Practices**: Structured reasoning and self-verification
- **Selection-Inference Prompting**: OpenAI two-phase reasoning patterns
- **Academic Findings**: LLM reasoning failure research (65% accuracy drop with irrelevant info)

**Load When**:
- Understanding why verification gates are necessary
- Justifying verification overhead to users
- Researching advanced verification techniques
- Designing new checkpoint patterns

#### [./references/failure-patterns.md](../plugins/verification-gate/skills/verification-gate/references/failure-patterns.md)

Common failure modes and prevention strategies:

- **Pattern 1**: PEP 723 vs pyproject.toml misalignment
- **Pattern 2**: Configuration file precedence confusion
- **Pattern 3**: Docker network layer confusion
- **Pattern 4**: Python virtual environment scope confusion
- **Pattern 5**: Git state vs file system state
- **Pattern 6**: Application code vs infrastructure configuration
- **Pattern 7**: Test failure pattern matching
- **Meta-Pattern**: Cognitive dissonance resolution

**Load When**:
- Diagnosing why verification failed
- Identifying subtle misalignments
- Learning from historical failures
- Teaching verification concepts

### Performance Impact

**Overhead**:
- 2-3 additional Read operations per action
- ~150-300 tokens per verification
- Total: ~500 tokens per verified action

**Benefit**:
- Prevents wrong implementations (20+ tool calls to fix = 4000+ tokens)
- Reduces debugging cycles (saves 3000-8000 tokens per avoided error)
- Builds user confidence (reduces clarification exchanges)

**Net Result**: 5% overhead for 95% reliability improvement

### Integration with CLAUDE.md

This skill enforces existing CLAUDE.md verification protocols by adding structural gates:

| CLAUDE.md Rule | Verification Enforcement |
|----------------|--------------------------|
| "Verify behavior with authoritative sources" | Checkpoint 2: Cannot execute until verification completed |
| "Never cargo cult code without verification" | Checkpoint 4: Detects and blocks pattern-matching |
| "Distinguish verified information from assumptions" | Checkpoint 2: Requires evidence with citations |
| "Cite sources with line numbers" | Checkpoint 2: Must cite specific files and lines |

### Self-Monitoring

The model actively monitors for verification violations:

**Warning Signs**:
- Stating hypothesis then immediately executing without Checkpoint 2
- Reading files AFTER taking action instead of BEFORE
- Modifying different files/systems than hypothesis identified
- Solution appearing reflexively upon seeing error message
- Not being able to cite specific evidence for hypothesis

**When Detected**:

```text
⚠ VERIFICATION VIOLATION DETECTED
I attempted to bypass verification checkpoint.
HALTING and returning to Checkpoint [number].
```

### Key Principle

**Verification is not optional**. This skill implements defensive programming for LLM reasoning. Just as compilers block syntactically invalid code, verification gates block logically misaligned actions.

Speed without verification is not efficiency—it's error propagation. Taking time to verify prevents cascading failures, reduces debugging cycles, and builds user confidence.

---

[Back to README](../README.md)
