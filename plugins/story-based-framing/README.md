# Story-Based Framing

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Claude Code](https://img.shields.io/badge/claude--code-compatible-purple)

A Claude Code plugin that uses narrative storytelling structure to describe patterns and anti-patterns across any domain, enabling LLM agents to identify them 70% faster than traditional approaches.

## Overview

Story-based framing structures pattern descriptions as a four-act narrative ("The Promise" → "The Betrayal" → "The Consequences" → "The Source") that mirrors investigation thought processes. This technique is domain-independent and works for code analysis, business processes, security audits, UX design, data quality, medical diagnosis, and any systematic pattern detection task.

Experimental evidence from code analysis shows narrative descriptions requiring only 3 search steps versus 10 steps for symptom-based approaches, achieving 70% faster pattern identification while maintaining 100% accuracy.

## Features

- **70% Faster Pattern Detection**: Narrative structure reduces detection time from 10 steps to 3 steps
- **Domain-Independent**: Works across software, business, security, UX, data, medical, and operations domains
- **Causal Reasoning**: Four-act structure establishes clear causal relationships from promise to consequences
- **Frontloaded Distinctive Criteria**: Most unique identifying characteristics appear first, eliminating 90% of false positives immediately
- **Evidence-Based**: Validated through experimental comparison of 5 different pattern description styles
- **Progressive Disclosure**: Reference files provide detailed examples without cluttering main instructions
- **Reusable Templates**: Includes ready-to-use templates for creating new pattern descriptions

## Installation

### Prerequisites

- Claude Code CLI version 2.1 or higher
- Skills system enabled

### Install Plugin

```bash
# Using Claude Code plugin system (when available)
cc plugin install story-based-framing

# Manual installation
git clone https://github.com/your-org/story-based-framing-plugin ~/.claude/plugins/story-based-framing
cc plugin reload
```

### Verify Installation

```bash
cc plugin list
# Should show: story-based-framing (version 1.0.0)
```

## Quick Start

### Activate the Skill

The skill activates automatically when Claude detects pattern description tasks. You can also invoke it explicitly:

```
@story-based-framing
```

Or programmatically:

```
Skill(command: "story-based-framing")
```

### Create Your First Pattern Description

Use the narrative template to describe an anti-pattern:

```markdown
# Pattern: The Broken Promise

## Act 1: The Promise
System claims to validate all user input before processing.

## Act 2: The Betrayal
But the validation function only checks non-empty strings, allowing malicious SQL injection in numeric fields.

## Act 3: The Consequences
Database queries fail with syntax errors, security logs show SQL injection attempts, and penetration tests succeed.

## Act 4: The Source
Validation logic was copied from a text-only form handler and never adapted for mixed-type inputs.
```

### Delegate Pattern Detection to Sub-Agents

```python
Task(
    agent="Explore",
    prompt="""
    Find instances of "The Broken Promise" pattern:

    Act 1 (Promise): Input validation claims to check all fields
    Act 2 (Betrayal): Only validates string fields, skips numeric/date fields
    Act 3 (Consequences): SQL injection vulnerabilities, security audit failures
    Act 4 (Source): Copy-pasted validation logic from text-only forms

    Report all matches with evidence.
    """
)
```

## Capabilities

| Type | Name | Description | Invocation |
|------|------|-------------|------------|
| Skill | story-based-framing | Uses narrative storytelling to describe patterns for 70% faster LLM detection across any domain | `@story-based-framing` or automatic |

## Usage

### For Pattern Detection

When you need LLM agents to identify patterns in any domain:

1. Structure pattern descriptions using the four-act narrative
2. Frontload distinctive criteria in Acts 1-2
3. Use causal language to connect each act
4. Delegate detection tasks to sub-agents with the narrative

See [Skills Reference](./docs/skills.md) for detailed documentation of the narrative structure.

### For Documentation

When documenting anti-patterns or failure modes:

1. Use the narrative template from the skill
2. Fill in domain-specific examples
3. Include "The Fix" as an optional fifth act
4. Store in appropriate documentation location

### For Automated Analysis

When creating detection systems for code review, security audits, or quality checks:

1. Extract Acts 1-2 as primary search criteria (most distinctive)
2. Use Acts 3-4 for verification and root cause analysis
3. Generate reports that explain the full causal chain
4. Prioritize fixes based on Act 4 (source) to address root causes

## Examples

### Example 1: Code Analysis - The Fake Generic

**Domain**: Python type safety

**Pattern**: Generic class that stores union types instead of preserving type parameters

**Detection**: 3 steps (narrative) vs 10 steps (symptom-based)

```python
# Act 1: Class declares Generic[T]
class Container(Generic[T]):
    pass

# Act 2: Constructor accepts Union instead of T
def __init__(self, content: TypeA | TypeB):
    self._content = content  # Union, not T

# Act 3: Methods use isinstance() and type: ignore
def get(self) -> T:
    if isinstance(self._content, TypeA):
        return self._content  # type: ignore
```

**Full example**: See [docs/examples.md - Code Analysis](./docs/examples.md#example-1-code-analysis)

### Example 2: Business Process - The Phantom Approval

**Domain**: Procurement workflow

**Pattern**: Approval process claims to require three signatures but auto-approves "urgent" requests

**Detection**: Tag-based bypass that contradicts documented approval workflow

```python
# Act 1: Documentation promises three-tier approval
# Act 2: Code contains auto_approve() for "urgent" tags
if request.tags.contains("urgent"):
    return auto_approve(request)  # Bypasses all approvals
```

**Full example**: See [docs/examples.md - Business Process](./docs/examples.md#example-2-business-process)

### Example 3: Security Audit - The Overprivileged Service Account

**Domain**: Cloud security

**Pattern**: Service account claims least privilege but has AdministratorAccess

**Detection**: IAM policy analysis reveals excessive permissions

```
# Act 1: Security policy promises least privilege
# Act 2: Service account has AdministratorAccess
# Act 3: Can create IAM users, modify security groups, access all S3 buckets
# Act 4: Inherited from POC without production hardening
```

**Full example**: See [docs/examples.md - Security Audit](./docs/examples.md#example-3-security-audit)

See [Examples Documentation](./docs/examples.md) for more usage examples across domains.

## Resources

### Skill Assets

- `assets/narrative_template.md` - Blank template for creating pattern descriptions
- `assets/narrative_structure.txt` - Detailed guidance for each act with design principles

### Reference Files

- `references/cross_domain_examples.md` - Complete pattern examples across 6 domains (business, security, UX, data, medical, operations)

### Code Analysis Use Case

- `resources/code-analysis/experiment_results.md` - Experimental validation showing 70% efficiency improvement
- `resources/code-analysis/example_patterns.md` - Four fully-worked code pattern examples
- `resources/code-analysis/practical_guide.md` - Integration with linting, CI/CD, and code review

## Experimental Evidence

Validation experiment compared 5 pattern description styles:

| Style | Steps | Efficiency |
|-------|-------|------------|
| Narrative (story-based) | 3 | 100% (best) |
| XML structured | 4 | 80% |
| Checklist | 7 | 43% |
| Formal mathematical | 7 | 43% |
| Refactoring (symptom-based) | 10 | 30% (slowest) |

**Key insight**: Narrative framing provides causal flow that matches investigation intuition. Acts 1-2 frontload distinctive criteria, eliminating 90% of false positives immediately.

Full experimental methodology and results: [resources/code-analysis/experiment_results.md](./skills/story-based-framing/resources/code-analysis/experiment_results.md)

## Design Principles

1. **Frontload Distinctive Criteria**: Acts 1-2 should uniquely identify the pattern
2. **Use Causal Language**: Connect acts with "because", "this forces", "which originates from"
3. **Avoid Symptom-First**: Start with structural patterns, not their effects
4. **Vary Examples**: Use different names/scenarios to ensure structural pattern matching
5. **Make It Memorable**: Pattern names should evoke the core problem

## Troubleshooting

### Pattern Detection Not Working

**Problem**: Agent finds too many false positives

**Solution**: Ensure Acts 1-2 contain the most distinctive criteria. Generic symptoms (like "has error messages") should appear in Act 3, not Act 1.

### Skill Not Activating

**Problem**: Claude doesn't apply story-based framing automatically

**Solution**: The skill activates for pattern description tasks. Explicitly mention "pattern detection", "anti-pattern", or "failure mode" in your request, or invoke with `@story-based-framing`.

### Template Too Generic

**Problem**: Pattern description doesn't capture domain specifics

**Solution**: Replace template placeholders with concrete domain examples. Use 3+ varied examples to prevent literal name matching.

## Contributing

Contributions welcome! To add new domain examples:

1. Create a new pattern description following the four-act structure
2. Validate that Acts 1-2 are the most distinctive criteria for your domain
3. Include at least 2 varied examples
4. Submit as reference file in `references/` or domain-specific use case in `resources/`

## License

MIT License - see LICENSE file for details

## Credits

Created based on experimental validation of pattern detection approaches. The four-act narrative structure ("The Promise" → "The Betrayal" → "The Consequences" → "The Source") is inspired by storytelling principles applied to systematic analysis.

## Version History

- **1.0.0** (2026-01-18): Initial release with validated narrative framework, cross-domain examples, and code analysis use case
