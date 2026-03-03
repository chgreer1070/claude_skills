<p align="center">
  <img src="./assets/hero.png" alt="Holistic Linting" width="800" />
</p>

# Holistic Linting

Makes Claude automatically check and fix code quality issues before completing tasks.

## Why Install This?

When you ask Claude to write or modify code, Claude sometimes:

- Says "all done!" but leaves linting errors in the code
- Adds `# type: ignore` or `# noqa` comments to silence errors instead of fixing them
- Forgets to run formatters and linters before finishing
- Doesn't know which linters your project uses

This plugin makes Claude treat code quality checks as a required part of every task.

## What You Get

### Claude Improvements

With this plugin, Claude will:

**Automatically verify code quality** - Before marking any code task complete, Claude formats and lints the files it modified. No more "done!" messages with linting errors left behind.

**Investigate root causes** - When linting errors appear, Claude researches the rule documentation, examines the code context, and implements proper fixes instead of adding suppression comments.

**Use your project's linters** - Claude discovers which linters your project uses (ruff, mypy, pyright, eslint, prettier, etc.) by scanning your configuration files.

**Delegate systematically** - When you're in the interactive Claude Code CLI, Claude delegates linting resolution to specialized agents that handle formatting, linting, and fixes concurrently.

**Verify fixes work** - After implementing fixes, Claude re-runs linters to confirm issues are actually resolved.

### Commands

#### /lint [files...]

Shorthand for activating the holistic-linting skill:

```bash
/lint src/auth.py
/lint src/*.py
/lint path/to/directory/
```

Activates the full holistic-linting workflow — linter detection, formatting, linting, root-cause resolution via specialized agents, and verification. Equivalent to running `/holistic-linting:holistic-linting` directly with file path arguments.

### Specialized Agents

This plugin provides two agents that Claude delegates to when orchestrating linting work:

**linting-root-cause-resolver** - Investigates and fixes linting errors. Loads project context, researches rule documentation, follows Python 3.11+ standards, and rewrites code to address underlying issues. Never suppresses errors unless fundamentally unsolvable.

**post-linting-architecture-reviewer** - Reviews linting resolution quality after fixes are complete. Examines resolution artifacts, validates fixes align with codebase patterns, checks type safety improvements, and identifies opportunities for systemic improvements.

### Skills Included

This plugin provides three complementary skills that work together:

**holistic-linting** - Core skill providing linter detection, formatting workflows, and the rules knowledge base. Entry point for all linting operations.

**holistic-linting-orchestrator** - Delegation workflows for the interactive CLI. Guides Claude on when and how to delegate to linting agents for systematic resolution.

**holistic-linting-resolver** - Linter-specific resolution procedures for sub-agents. Provides systematic workflows for resolving ruff, mypy, and pyright errors with suppression gates and verification steps.

### Included Resources

**Rules Knowledge Base** - Complete documentation for 933+ ruff rules (19 families), mypy error codes (organized by category), and 65+ bandit security checks. Claude references these when researching fixes.

**Resolution Workflows** - Systematic procedures for resolving issues reported by ruff, mypy, pyright, and basedpyright. Includes suppression gates, verification steps, and root-cause analysis patterns.

## Installation

First, add the marketplace (one-time setup):

```bash
/plugin marketplace add Jamie-BitFlight/claude_skills
```

Then install the plugin:

```bash
/plugin install holistic-linting@jamie-bitflight-skills
```

## Usage

### Automatic Behavior

Just install it. Claude automatically checks code quality when finishing tasks involving code changes.

When Claude is orchestrating work (interactive CLI), it delegates to specialized agents that handle all formatting, linting, and resolution work.

When Claude is a sub-agent (delegated task), it formats and lints files it modified before marking the task complete.

### Manual Linting

Use `/lint` as a shorthand to activate the holistic-linting skill on specific files:

```bash
/lint src/auth.py src/utils.py
```

## Example

**Without this plugin**:

```
You: "Add authentication to the API"
Claude: [writes code]
Claude: "Done! I've added authentication middleware."
You: [runs ruff check]
You: "There are 5 linting errors..."
```

**With this plugin**:

```
You: "Add authentication to the API"
Claude: [writes code]
Claude: [automatically formats and lints modified files]
Claude: [finds 5 errors, investigates root causes, fixes them]
Claude: [verifies fixes by re-running linters]
Claude: "Done! I've added authentication middleware. All linting checks pass."
```

## Requirements

- Claude Code v2.0+
- Python projects: ruff, mypy, pyright, bandit, or similar linters
- JavaScript/TypeScript projects: eslint, prettier
- Shell scripts: shellcheck, shfmt
- Markdown: markdownlint
- Pre-commit framework: pre-commit or prek

## Supported Linters

**Python**: ruff, mypy, pyright, basedpyright, bandit

**JavaScript/TypeScript**: eslint, prettier

**Shell**: shellcheck, shfmt

**Markdown**: markdownlint

**Pre-commit hooks**: pre-commit, prek
