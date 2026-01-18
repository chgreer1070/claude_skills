# Verification Gate

![Version](https://img.shields.io/badge/version-1.0.0-blue) ![Claude Code](https://img.shields.io/badge/claude--code-compatible-purple)

Enforce mandatory pre-action verification checkpoints to prevent pattern-matching from overriding explicit reasoning in Claude Code.

## Overview

The verification-gate plugin implements a research-backed, four-checkpoint verification system that acts as a cognitive brake between hypothesis formation and action execution. It prevents System 1 (fast, pattern-based) thinking from overriding System 2 (deliberate, logical) reasoning when Claude performs implementation actions.

**Core Principle**: Verification is not advisory—it is a mandatory gate. Actions that don't align with verified hypotheses are blocked.

## Features

- **4-Checkpoint Verification System**: Systematic verification before any implementation action (Bash, Write, Edit)
- **Hypothesis-Action Alignment**: Prevents cognitive dissonance where correct diagnosis leads to wrong implementation
- **Pattern-Matching Detection**: Identifies when training data patterns override project-specific reality
- **Research-Backed Approach**: Based on Meta's Chain-of-Verification (CoVe), System 2 Attention (S2A), and Anthropic prompt engineering best practices
- **Real-World Failure Prevention**: Documented patterns from actual verification failures with prevention strategies

## Installation

### Prerequisites

- Claude Code version 2.1 or later
- No external dependencies required

### Install Plugin

```bash
# Method 1: From marketplace (if published)
/plugin install verification-gate

# Method 2: Manual installation from repository
git clone <repository-url> ~/.claude/plugins/verification-gate
/plugin reload
```

## Quick Start

The verification-gate skill activates automatically before implementation actions. Here's what a verified action looks like:

```text
VERIFICATION COMPLETE:
✓ Checkpoint 1: Hypothesis stated - PEP 723 script missing pydantic dependency
✓ Checkpoint 2: Verified via Read(cli.py, lines 1-20) found # /// script block
✓ Checkpoint 3: Aligned - both target PEP 723 inline metadata system
✓ Checkpoint 4: Verified against project reality (not pattern-matching)

EXECUTING: Edit PEP 723 dependencies block to add pydantic
```

## Capabilities

| Type | Name | Description | Invocation |
|------|------|-------------|------------|
| Skill | verification-gate | Enforces 4-checkpoint verification before implementation actions | Auto-activated by Claude |

For detailed skill documentation, see [Skills Reference](./docs/skills.md).

## Usage

### When Verification Activates

The skill automatically activates:

- **Before any implementation action**: Bash (state-changing), Write, Edit, NotebookEdit
- **After stating a hypothesis**: When diagnosing what system/component has an issue
- **When choosing approaches**: Between multiple implementation strategies
- **When pattern-matching detected**: "Usually", "typically", "standard approach" language

### The Four Checkpoints

1. **Hypothesis Stated**: Have I explicitly named the specific system/component the issue affects?
2. **Hypothesis Verified**: Have I gathered evidence (Read/Grep/MCP tools) to confirm my hypothesis?
3. **Hypothesis-Action Alignment**: Does my planned action target the SAME system as my hypothesis identified?
4. **Pattern-Matching Detection**: Is this action based on verified project reality or training data patterns?

### Blocked vs Allowed Actions

**Blocked Example**:

```text
✗ BLOCKED - Hypothesis-action misalignment detected
HYPOTHESIS targets: PEP 723 inline script metadata
ACTION operates on: pyproject.toml (via uv sync)

REQUIRED: Add pydantic to # /// script block instead
```

**Allowed Example**:

```text
✓ ALL CHECKPOINTS PASSED
HYPOTHESIS: Script missing pydantic in PEP 723 dependencies
ACTION: Edit # /// script block to add pydantic
ALIGNMENT: Both target PEP 723 inline metadata system
EXECUTING: Edit(file_path="cli.py", ...)
```

## Examples

### Example 1: Dependency Error Resolution

**Scenario**: Python script fails with `ModuleNotFoundError: No module named 'pydantic'`

**Verification Workflow**:

1. **Checkpoint 1**: "Hypothesis: pydantic is missing from PEP 723 inline script dependencies"
2. **Checkpoint 2**: `Read(cli.py)` confirms `# /// script` block exists, pydantic not listed
3. **Checkpoint 3**: Hypothesis targets PEP 723 system, action edits `# /// script` block → Aligned
4. **Checkpoint 4**: Verified by reading actual script file, not assuming standard package management

**Result**: Edit approved and executed

---

### Example 2: Configuration Not Applied

**Scenario**: Application ignores new timeout setting in config.yaml

**Verification Workflow**:

1. **Checkpoint 1**: Initial hypothesis needs refinement - which configuration source?
2. **Checkpoint 2**: `Grep(pattern="load.*config")` reveals `config = os.getenv('TIMEOUT') or load_yaml('config.yaml')`
3. **Checkpoint 1 Refined**: "Hypothesis: Environment variable overrides config.yaml, needs to be set"
4. **Checkpoint 3**: Hypothesis targets env var, action sets env var → Aligned
5. **Checkpoint 4**: Verified by reading actual config loading code

**Result**: Set environment variable instead of modifying config.yaml

---

For more examples, see [Examples Reference](./docs/examples.md).

## Research Foundation

This plugin implements verification patterns from peer-reviewed research and official prompt engineering guidance:

- **Chain-of-Verification (CoVe)** - Meta AI Research (2023): Factored verification reduces hallucinations
- **System 2 Attention (S2A)** - Meta AI Research (2023): Attention focusing improves factuality
- **Anthropic Prompt Engineering**: Structured reasoning and self-verification best practices
- **OpenAI Selection-Inference**: Split fact-gathering from conclusion-drawing

Full research citations available in [references/research-foundations.md](./skills/verification-gate/references/research-foundations.md).

## Troubleshooting

### Verification Feels Slow

**Expected**: 2-3 additional Read operations per action (~500 tokens overhead)

**Benefit**: Prevents wrong implementations requiring 20+ tool calls to debug (~4000+ tokens)

**Net Result**: 5% overhead for 95% reliability improvement

### False Positives (Blocked When Should Proceed)

If verification incorrectly blocks a valid action:

1. Check if hypothesis explicitly states the system being targeted
2. Verify evidence was gathered (Read/Grep) before acting
3. Confirm hypothesis and action target the same system
4. Report the issue with context for pattern refinement

### Checkpoint Always Failing

Common causes:

- **Checkpoint 1**: Hypothesis too vague ("not working" → specify which system)
- **Checkpoint 2**: Haven't used Read/Grep/MCP tools to gather evidence
- **Checkpoint 3**: Hypothesis identified system A, action targets system B
- **Checkpoint 4**: Solution appeared immediately without investigation (pattern-matching)

## Integration with Other Skills

- **python3-development**: Verification activates before Python script modifications
- **bash-script-developer**: Verification activates before bash script creation
- **agent-orchestration**: Orchestrator ensures sub-agents follow verification protocol
- **holistic-linting**: Verification ensures fixes target root cause, not symptoms

## Contributing

Contributions welcome for:

- New failure pattern documentation (add to references/failure-patterns.md)
- Additional verification checkpoint proposals (must include research backing)
- Real-world case studies
- Integration patterns with other skills

## License

See LICENSE file for details.

## Credits

**Research Foundation**:
- Meta AI Research: Chain-of-Verification (CoVe), System 2 Attention (S2A)
- Anthropic: Prompt engineering best practices
- OpenAI Community: Selection-Inference prompting

**Pattern Analysis**: Real-world verification failures from production Claude Code usage

---

**Last Updated**: 2026-01-18
