---
name: Claude Skillz
description: Claude Skillz is a comprehensive repository of reusable skills, composable system prompts, and Claude Code plugins for AI-assisted software development. It provides a launcher utility for rapid...
license: None (Public repository)
metadata:
  topic: claude-skillz
  category: skill-generation-tools
  source_url: https://github.com/NTCoding/claude-skillz
  github: NTCoding/claude-skillz
  version: "1.2.0"
  verified: "2026-02-20"
  next_review: "2026-05-20"
---

## Overview

Claude Skillz is a comprehensive repository of reusable skills, composable system prompts, and Claude Code plugins for AI-assisted software development. It provides a launcher utility for rapid persona/model switching, 18+ behavioral skills for development practices, 12 pre-built personas, and 10 installable plugins including automatic code review, task verification, and continuous improvement tracking.

---

## Problem Addressed

| Problem | Solution |
|---------|----------|
| Repetitive system prompt configuration across sessions | Claude Launcher utility with fuzzy search and shortcuts for instant persona/model switching |
| Inconsistent behavior patterns across different Claude sessions | Composable skill system with @ references that load behavioral instructions at startup |
| Manual code review overhead in AI-assisted development | Automatic code review hook with configurable semantic rules triggered on session stop |
| Lost context and improvement opportunities across sessions | Track-and-improve plugin with automatic 5 Whys root cause analysis |
| Mixing persona identity with reusable behaviors | Separation between personas (who Claude is) and skills (behavioral instructions) |
| Token overhead from runtime skill loading | Pre-processing @ references at launch time (avoids 18k+ tokens of message history overhead) |

---

## Key Statistics

| Metric | Value | Date Gathered |
|--------|-------|---------------|
| GitHub Stars | 238 | 2026-02-20 |
| Forks | 33 | 2026-02-20 |
| Contributors | 1 | 2026-02-20 |
| Latest Release | No releases | 2026-02-20 |
| Last Updated | 2026-02-19 | 2026-02-20 |
| Created | 2025-11-14 | 2026-02-20 |

---

## Key Features

### Claude Launcher

- Interactive 2-step fuzzy search selection (persona → model) using fzf
- Order-independent shortcut syntax (`cl tdd opus` = `cl opus tdd`)
- Model-only shortcuts (`cl sonn` uses default persona)
- Frontmatter-based shortcuts (add custom personas by adding metadata)
- System prompt composability with @ skill references pre-processed at launch
- Conflict detection with prominent warnings
- Exports CLAUDE_PERSONA environment variable for shell status line display
- Zero Python dependencies (fzf optional for better UX)
- Auto-discovers from `~/.claude/system-prompts` (global) and project-local directories

### Development Skills (18 Skills)

**Research & Evidence:**
- independent-research - Research-driven investigation, never guess, validate before presenting
- confidence-honesty - Force honest confidence assessment with percentages and gap explanations

**Communication & Output:**
- concise-output - Signal-over-noise, eliminate verbose phrases, maximize information density
- critical-peer-personality - Professional skeptical communication, challenge constructively
- questions-are-not-instructions - Answer questions literally, do not interpret as hidden instructions

**Code & Design:**
- software-design-principles - Object calisthenics, dependency inversion, fail-fast error handling
- lightweight-implementation-analysis-protocol - Trace execution paths before implementing
- lightweight-design-analysis - Systematic review across 8 dimensions (naming, coupling, immutability, etc.)
- separation-of-concerns - Enforces strict separation with mandatory checklist
- tactical-ddd - Domain-driven design tactical patterns

**Development Processes:**
- tdd-process - Strict TDD state machine: red-green-refactor with 11 enforced rules
- writing-tests - Principles for effective tests with comprehensive edge case checklists
- observability-first-debugging - Systematic debugging with instrumentation-first approach
- fix-it-never-work-around-it - Force root cause fixes instead of workarounds

**Workflows & Tools:**
- switch-persona - Mid-conversation persona switching without restart
- lightweight-task-workflow - Task list state machine for multi-session work
- create-tasks - Convert requirements into actionable tasks with structured template
- data-visualization - Build charts, graphs, dashboards with visual execution guidance
- typescript-backend-project-setup - NX monorepo setup optimized for AI-assisted development

### System Prompts (12 Personas)

Pre-built personas ready to use via launcher shortcuts:

- `tdd` - Super TDD Developer
- `opt` - Claude Code Optimizer
- `prd` - PRD Expert
- `arc` - Strategic Architect
- `doc` - Documentation Expert
- `rct` - Super React Developer
- `inv` - Technical Investigator
- `wrt` - Writing Tool
- `tsc` - Super TypeScript Developer
- `viz` - Frontend Visualization Expert
- `uix` - UI/UX Design Leader
- `gen` - Generalist Robot (default)

### Plugins (10 Installable Plugins)

- task-check - Verify task completion before finishing, catches incomplete work
- automatic-code-review - Session stop hook with configurable semantic rules, auto-initializes
- full-codebase-review - Periodic full codebase review using automatic-code-review rules
- track-and-improve - Capture mistakes with automatic 5 Whys root cause analysis
- collaboration-modes - Define collaboration style: step-by-step, deep-think, pair programming
- learn-from-prs - Analyze PR feedback patterns to suggest local config updates
- challenge-that - Force critical evaluation from 5 adversarial perspectives
- architect-refine-critique - Three-phase design review producing ADR
- session-optimizer - Analyze session transcripts with 4 parallel subagents
- optimization-team - Two-agent team: researcher proposes, critic challenges

---

## Technical Architecture

### Composability System

System prompts follow a composable architecture where skills are behavioral instructions loaded at session startup:

```markdown
---
name: Persona Name
shortcut: xxx
---

[Persona identity and principles]

## Skills

- @../skill-name/SKILL.md
- @../another-skill/SKILL.md
```

**@ Reference Processing:**
1. Claude Launcher pre-processes @ references before launching Claude Code
2. Skills embedded directly into system prompt (not loaded via Read operations)
3. "Loaded Skills" manifest added at top showing what was loaded
4. Debug output saved to `/tmp/claude-launcher-debug.md` for verification

**Token Efficiency:**
- Pre-processing avoids 18k+ tokens of message history overhead
- Near-zero overhead vs monolithic prompts (1% difference)
- Skills remain composable and reusable across personas

### Skill Structure

Every skill follows this pattern:

```markdown
---
name: skill-name
description: "Activation triggers and behavior description"
version: 1.0.0
---

[Behavioral instructions written as imperatives]

## Mandatory Checklist

1. [ ] Verify [specific condition]
2. [ ] Verify [another condition]

Do not proceed until all checks pass.
```

**Key principles:**
- Write as instructions (imperatives), not descriptions
- Include activation triggers in frontmatter
- End with mandatory checklist for verification
- Never duplicate skill content in system prompts

### Plugin Architecture

Plugins use standard Claude Code plugin structure:

```text
plugin-name/
├── .claude-plugin/
│   └── manifest.json
├── commands/          # Slash commands
├── agents/           # Agent definitions
├── hooks/            # Lifecycle hooks
│   ├── hooks.json
│   └── tools/        # Hook scripts
└── README.md
```

Distributed via marketplace.json with plugin metadata (name, version, category, keywords).

### Marketplace Distribution

Repository serves as a Claude Code plugin marketplace installable via:

```bash
/plugin marketplace add ntcoding/claude-skillz
/plugin install <plugin-name>@claude-skillz
```

Marketplace metadata stored in `.claude-plugin/marketplace.json` with plugins array.

---

## Installation & Usage

### Claude Launcher Setup

```bash
# Alias in ~/.zshrc or ~/.bashrc
alias cl='python3 /path/to/claude-skillz/claude-launcher/claude-launcher.py'

# Optional: Install fzf for fuzzy search
brew install fzf  # macOS

# Set Claude binary path (for npm/nvm installations)
export CLAUDE_CMD="$(which claude)"
```

### Using Claude Launcher

```bash
# Interactive 2-step selection
$ cl

# Direct shortcuts (order-independent)
$ cl tdd opus        # Super TDD Developer + Opus
$ cl opt sonn        # Claude Code Optimizer + Sonnet

# Model-only (uses generalist-robot)
$ cl sonn
$ cl opus
```

### Plugin Installation

**Via Marketplace:**

```bash
# Add marketplace (one-time)
/plugin marketplace add ntcoding/claude-skillz

# Install specific plugin
/plugin install automatic-code-review@claude-skillz
```

**Per-project:**

Add to project `.claude/settings.json`:

```json
{
  "plugins": [
    "automatic-code-review@claude-skillz"
  ]
}
```

### Skill Usage

Reference skills in system prompts with @ references:

```markdown
---
name: My Custom Persona
---

Your expertise areas...

## Skills

- @../tdd-process/SKILL.md
- @../software-design-principles/SKILL.md
```

Launcher pre-processes and embeds at launch time.

---

## Relevance to Claude Code Development

### Applications

- **Persona management** - Demonstrates rapid context switching pattern with launcher utility that could be adapted for claude_skills repository
- **Skill composability** - Shows effective @ reference pattern for loading behavioral instructions at startup with minimal token overhead
- **Hook-based automation** - Automatic code review and task verification hooks demonstrate session lifecycle integration
- **Marketplace distribution** - Reference implementation of Claude Code plugin marketplace structure and metadata

### Patterns Worth Adopting

- **Mandatory checklists at end of skills** - Makes behavioral instructions actionable and verifiable, prevents abstract guidance
- **State machine governance for processes** - TDD skill shows strict state announcement pattern ensuring consistent adherence to methodology
- **Pre-processing @ references** - Avoids 18k+ token overhead of runtime skill loading by embedding at launch time
- **Frontmatter-based shortcuts** - Enables user-defined shortcuts by parsing metadata, no code changes required
- **Instructive vs descriptive prompts** - Write system prompts as imperatives ("Research before recommending") not descriptions ("You are helpful")
- **Separation of persona and skills** - Personas define identity/expertise, skills define reusable behavioral patterns
- **Auto-initialization of plugin configs** - Hooks create default configuration files on first run with sensible defaults

### Integration Opportunities

- **Cross-reference skill collections** - claude_skills could reference compatible NTCoding skills as external marketplace
- **Adopt launcher pattern** - Create similar launcher for claude_skills with plugin/skill selection
- **Study hook implementations** - PostToolUse and Stop hooks show practical patterns for session lifecycle automation
- **Borrow skill patterns** - TDD state machine, observability-first debugging, lightweight design analysis are well-structured
- **Compare marketplace approaches** - Both repos implement marketplace.json pattern, study metadata differences
- **Skill verification** - Mandatory checklist pattern could improve claude_skills skill effectiveness

---

## References

- [GitHub Repository](https://github.com/NTCoding/claude-skillz) (accessed 2026-02-20)
- [GitHub API - Repository Metadata](https://api.github.com/repos/NTCoding/claude-skillz) (accessed 2026-02-20)
- [Repository README](https://raw.githubusercontent.com/NTCoding/claude-skillz/main/README.md) (accessed 2026-02-20)
- [CLAUDE.md - Composability Guidelines](https://raw.githubusercontent.com/NTCoding/claude-skillz/main/CLAUDE.md) (accessed 2026-02-20)
- [Claude Launcher Documentation](https://raw.githubusercontent.com/NTCoding/claude-skillz/main/claude-launcher/README.md) (accessed 2026-02-20)
- [TDD Process Skill Example](https://raw.githubusercontent.com/NTCoding/claude-skillz/main/tdd-process/SKILL.md) (accessed 2026-02-20)
- [Automatic Code Review Plugin](https://raw.githubusercontent.com/NTCoding/claude-skillz/main/automatic-code-review/README.md) (accessed 2026-02-20)
- [Marketplace Metadata](https://raw.githubusercontent.com/NTCoding/claude-skillz/main/.claude-plugin/marketplace.json) (accessed 2026-02-20)