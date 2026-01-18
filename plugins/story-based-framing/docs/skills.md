# Skills Reference

This plugin provides one skill that implements the story-based framing technique for pattern detection across any domain.

## story-based-framing

**Location**: `skills/story-based-framing/SKILL.md`

**Description**: Uses narrative storytelling structure to describe patterns and anti-patterns for LLM agent detection across any domain. Achieves 70% faster pattern identification compared to checklist or formal specification approaches through the four-act structure: "The Promise" → "The Betrayal" → "The Consequences" → "The Source".

**User Invocable**: Yes

**Allowed Tools**: Not restricted (inherits default tools)

**Model**: Default (inherits session model)

### When to Use

Activate this skill when:

- Creating pattern descriptions for LLM agents to identify in any domain
- Documenting anti-patterns, failure modes, or problematic behaviors
- Delegating pattern-finding tasks to sub-agents
- Designing automated detection or review workflows
- Building checklists that need to prioritize distinctive criteria
- Teaching pattern recognition to humans or AI systems

The skill is **domain-independent** and applies to:

- **Software**: Code smells, architectural issues, security vulnerabilities
- **Business**: Process inefficiencies, communication breakdowns, requirement gaps
- **Security**: Misconfigurations, access control issues, compliance violations
- **UX/Design**: Dark patterns, accessibility issues, false affordances
- **Data**: Quality issues, pipeline failures, stale caches
- **Medical**: Diagnostic patterns, symptom clusters, treatment protocols
- **Operations**: Incident patterns, resource bottlenecks, failure cascades

### Activation

**Automatic**: Claude invokes this skill when detecting pattern description tasks

**Explicit invocation**:

```
@story-based-framing
```

**Programmatic invocation**:

```
Skill(command: "story-based-framing")
```

### Core Narrative Structure

The skill teaches and enforces a four-act structure for pattern descriptions:

#### Act 1: The Promise

**Purpose**: Establish what the system/process/code claims to do or appears correct initially.

**Search Impact**: Most distinctive criterion that filters 90% of non-matches immediately.

**Examples**:

- Code: "A generic class `Container(Generic[T])` promises to preserve type T throughout its operations"
- Business: "The approval workflow promises that all requests are reviewed within 24 hours"
- Security: "The firewall configuration claims to restrict access to authorized IP ranges only"

#### Act 2: The Betrayal

**Purpose**: Show where implementation/reality violates the promise.

**Search Impact**: Second most distinctive criterion that narrows to true matches.

**Examples**:

- Code: "But the constructor accepts `content: UnionType` instead of `content: T`"
- Business: "But requests from certain departments bypass the approval queue entirely"
- Security: "But the configuration includes a rule allowing 0.0.0.0/0 that overrides all restrictions"

#### Act 3: The Consequences

**Purpose**: Describe observable symptoms that result from the violation.

**Search Impact**: Verification criteria that confirm the pattern is present.

**Examples**:

- Code: "Methods contain `isinstance()` checks and `# type: ignore` comments"
- Business: "Audit logs show approval timestamps that don't match reality"
- Security: "Penetration tests successfully access restricted resources from unauthorized networks"

#### Act 4: The Source

**Purpose**: Explain why the pattern exists (root cause).

**Search Impact**: Context for understanding if pattern is isolated or systemic.

**Examples**:

- Code: "Values originate from heterogeneous storage where type information is lost"
- Business: "Legacy system integration predates the approval workflow"
- Security: "The 'allow all' rule was added during an emergency 2 years ago and never removed"

### Pattern Description Template

The skill provides this template for creating new patterns:

```markdown
# Pattern: {Memorable Descriptive Name}

## The Story

### Act 1: The Promise

{What the system/process/code claims to do or appears correct}

**Observable characteristics**: {What makes this look correct initially}

### Act 2: The Betrayal

{Where reality violates the promise}

**The breaking point**: {Specific moment/location/condition where correctness fails}

### Act 3: The Consequences

{Observable symptoms from the violation}

**Symptoms**:
- {Symptom 1}
- {Symptom 2}
- {Symptom 3}

### Act 4: The Source

{Why the pattern exists - root cause}

**Origin**: {Architectural decision, legacy constraint, incentive misalignment, etc.}

## The Fix

{Brief description of the correct solution}

**Resolution approach**: {How to address the root cause}
```

### Design Principles

The skill enforces these principles when creating pattern descriptions:

#### 1. Frontload Distinctive Criteria

Place most unique characteristics in Acts 1-2 to eliminate 90%+ of false positives immediately.

**Poor ordering** (generic symptoms first):
1. "Has error messages"
2. "Has workarounds"
3. "Violates specification X"

**Good ordering** (distinctive structure first):
1. "Claims to implement specification X"
2. "But actually violates constraint Y"
3. "Resulting in error messages and workarounds"

#### 2. Use Causal Language

Connect each act with causal transitions that explain why the next act follows.

**Weak transitions**: "Additionally...", "Also...", "Furthermore..."

**Strong transitions**: "Because of this violation...", "This forces...", "Which originates from..."

#### 3. Provide Domain-Appropriate Examples

Include realistic examples using varied names/scenarios to avoid literal matching:

- Example 1: Manufacturing process, Product A, Factory 1
- Example 2: Software deployment, Service B, Region 2
- Example 3: Customer onboarding, User C, Channel 3

#### 4. Make It Memorable

Pattern names should evoke the core problem:

- Code: "The Fake Generic", "The Type Eraser"
- Business: "The Phantom Requirement", "The Meeting Creep"
- Security: "The Open Backdoor", "The Privileged Escalation"
- UX: "The Dark Pattern", "The False Affordance"

### Performance Data

Experimental validation shows narrative framing effectiveness:

| Description Style | Steps | Efficiency |
|-------------------|-------|------------|
| Narrative (this skill) | 3 | 100% (best) |
| XML structured | 4 | 80% |
| Checklist | 7 | 43% |
| Formal mathematical | 7 | 43% |
| Refactoring (symptom-based) | 10 | 30% (slowest) |

**Key finding**: Narrative approach requires 70% fewer steps than symptom-based approaches (3 vs 10 steps) while maintaining 100% accuracy.

### Comparison with Other Approaches

#### vs. Checklists

**Checklist**: Flat structure with no priority guidance (7 steps)

**Narrative**: Clear hierarchy, distinctive criteria first (3 steps)

#### vs. Formal Specifications

**Formal**: Notation overhead slows pattern recognition (7 steps)

**Narrative**: Direct mapping to observable behavior (3 steps)

#### vs. Symptom-Based

**Symptom**: Describes effects, not causes; overlapping symptoms (10 steps)

**Narrative**: Shows causal chain from root cause to symptoms (3 steps)

### Reference Files

The skill includes progressive disclosure through reference files:

#### cross_domain_examples.md

Complete pattern examples across 6 domains:

1. **Business Process**: "The Phantom Approval" (procurement workflow bypass)
2. **Security**: "The Overprivileged Service Account" (excessive IAM permissions)
3. **UX/Design**: "The Confirm-Shaming Dark Pattern" (deceptive cancellation flow)
4. **Data Quality**: "The Stale Cache Syndrome" (incorrect freshness claims)
5. **Medical Diagnosis**: "The Anchoring Bias" (diagnostic tunnel vision)
6. **Operations**: "The Alert Fatigue" (notification overload)

Each example follows the four-act structure with domain-specific details.

**Access**: Reference files load on demand when Claude needs domain-specific examples.

### Assets

#### narrative_template.md

Blank template for creating new pattern descriptions, includes:

- Four-act structure placeholders
- Code example sections (for technical patterns)
- Detection criteria checklist
- Impact assessment fields
- Related patterns section

**Use case**: Copy and customize for new patterns in any domain.

#### narrative_structure.txt

Detailed ASCII art guide explaining:

- Purpose of each act
- What to include in each section
- Search impact explanation
- Language to use vs. avoid
- Design principles summary
- Anti-patterns to avoid

**Use case**: Reference when teaching pattern creation or reviewing pattern quality.

### Advanced Techniques

#### Multi-Pattern Stories

Create pattern families with shared narrative universe:

**Pattern Family**: "Communication Breakdown"
- Pattern 1: "The Missing Context" (information promised but not delivered)
- Pattern 2: "The Assumed Knowledge" (sender assumes receiver knows background)
- Pattern 3: "The Delayed Feedback" (response promised quickly but arrives late)

#### Nested Narratives

Handle complex patterns with sub-patterns:

**Main Story**: "The Broken Promise"
- Sub-Story A: "Promise breaks due to configuration error"
- Sub-Story B: "Promise breaks due to integration issue"
- Sub-Story C: "Promise breaks due to resource constraint"

#### Comparative Narratives

Distinguish patterns with subtle differences:

**Pattern A**: "The False Promise" (claims X but delivers Y - complete violation)

**Pattern B**: "The Partial Promise" (claims X and delivers some X but not all - partial delivery)

**Key Difference**: Act 2 betrayal point distinguishes them.

### Practical Usage

#### For Automated Detection

When creating prompts for LLM-based detection agents:

```markdown
Search for instances of "{Pattern Name}" in {domain}:

**The Promise**: {What appears correct initially}
**The Betrayal**: {Where reality violates the promise}
**The Consequences**: {Observable symptoms}
**The Source**: {Why this exists}

Report: {identifier}, {location}, evidence for each act.
```

#### For Sub-Agent Delegation

When delegating pattern-finding to sub-agents:

```python
Task(
    agent="Explore",
    prompt="""
    Locate instances matching this pattern:

    Act 1 (The Promise): {What should be true}
    Act 2 (The Betrayal): {What actually happens}
    Act 3 (The Consequences): {Observable symptoms}
    Act 4 (The Source): {Why this exists}

    Report all matches with evidence.
    """
)
```

#### For Documentation

Store completed pattern descriptions in appropriate location:

- Code patterns → `docs/anti-patterns/`
- Business processes → `docs/process-issues/`
- Security issues → `docs/security-findings/`
- UX problems → `docs/ux-debt/`

### Domain-Specific Resources

#### Code Analysis

Complete use case with experimental validation, located in `resources/code-analysis/`:

**experiment_results.md**: Experimental methodology, 5-agent comparison, statistical validation

**example_patterns.md**: Four fully-worked code patterns:
- The Fake Generic (union-polluted Generic[T])
- The Type Eraser (unnecessary cast() usage)
- The Any Spreader (Any type propagation)
- The Mutable Default (mutable default argument)

**practical_guide.md**: Integration with:
- Automated linting detection
- Code review automation
- Refactoring prioritization
- Architecture analysis
- CI/CD workflows

#### Other Domains

Additional domain use cases can be added to `resources/` as needed to demonstrate versatility.

### Hooks

This skill has no configured hooks. All tool access inherits from session defaults.

### Integration Points

The skill integrates with:

- **Sub-agents**: Provide narrative descriptions in delegation prompts
- **Documentation systems**: Generate consistent anti-pattern docs
- **Detection tools**: Structure detection criteria for automated systems
- **Review workflows**: Create explanatory comments that show causation

### Limitations

- Requires understanding of causal reasoning (Acts must connect logically)
- Pattern quality depends on correctly identifying distinctive criteria
- Works best when patterns have clear promise/betrayal structure
- Less effective for patterns without causal relationships

### Best Practices

1. **Always frontload distinctive criteria** in Acts 1-2
2. **Use varied examples** to prevent literal name matching
3. **Connect acts causally** with "because", "this forces", "which originates"
4. **Test pattern descriptions** by having agents search with them
5. **Iterate based on false positives** - tighten Acts 1-2 if too many matches

### Success Metrics

Track effectiveness of patterns created with this skill:

- **Detection speed**: Steps required to find pattern instances
- **False positive rate**: Percentage of incorrect matches
- **Developer understanding**: Survey scores on pattern comprehension
- **Fix accuracy**: Percentage of fixes that address root cause (Act 4)

Target: 3-5 steps, <15% false positives, >90% comprehension, >85% root cause fixes.

---

[Back to README](../README.md)
