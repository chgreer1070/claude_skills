# Verification Gate

Enforce mandatory pre-action verification checkpoints to prevent pattern-matching from overriding explicit reasoning. Blocks execution when hypothesis unverified or action targets different system than hypothesis identified.

## Installation

**From Marketplace:**

```bash
/plugin marketplace add Jamie-BitFlight/claude_skills
/plugin install verification-gate@jamie-bitflight-skills
```

**For Development:**

```bash
claude --plugin-dir /path/to/verification-gate
```

## Capabilities

| Type | Name | Description |
|------|------|-------------|
| Skill | [verification-gate](./skills/verification-gate/SKILL.md) | Enforce mandatory pre-action verification checkpoints to prevent pattern-matching from overriding explicit reasoning. Use this skill when about to execute implementation actions (Bash, Write, Edit) to verify hypothesis-action alignment. Blocks execution when hypothesis unverified or action targets different system than hypothesis identified. Critical for preventing cognitive dissonance where correct diagnosis leads to wrong implementation. |

## Quick Start

The verification-gate skill activates automatically before implementation actions (Bash, Write, Edit) to enforce a 4-checkpoint verification process:

**Example scenario:** You observe `ModuleNotFoundError: No module named 'pydantic'`

```text
✓ Checkpoint 1: State hypothesis
  "Hypothesis: pydantic is missing from PEP 723 inline script dependencies"

✓ Checkpoint 2: Verify with evidence
  Read script file → confirm # /// script block exists
  Check current dependencies → pydantic not listed

✓ Checkpoint 3: Verify hypothesis-action alignment
  Hypothesis system: PEP 723 inline metadata (# /// script)
  Planned action: Add pydantic to # /// script block
  → ALIGNED (both target same system)

✓ Checkpoint 4: Pattern-matching check
  Verified against project reality (Read tool used)
  Not assuming "dependencies usually work this way"

VERIFICATION COMPLETE → Execute action
```

**What it prevents:**
- Hypothesis identifies PEP 723 issue → Action runs `uv sync` (wrong system)
- Solution appears reflexively without reading project files
- Pattern-matching from training data overrides project reality

## Version

1.0.0
