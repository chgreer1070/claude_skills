<p align="center">
  <img src="./assets/hero.png" alt="Verification Gate" width="800" />
</p>

# Verification Gate

Makes Claude investigate before acting instead of jumping to pattern-matched solutions.

## Why Install This?

Claude sometimes identifies the problem correctly but applies the wrong fix. This happens when Claude recognizes an error pattern and immediately applies a "standard solution" from its training data without checking if that solution matches your specific project setup.

Examples of what goes wrong without this plugin:

- You get "module not found" on a PEP 723 script. Claude runs `uv sync` (which targets `pyproject.toml`, not the PEP 723 inline dependencies)
- Your config is not loading. Claude modifies the config file without checking that your app reads environment variables instead
- A package will not import. Claude runs `pip install` globally when your script uses a virtualenv
- A build fails. Claude applies a fix from its training data before reading the actual error output

## How It Works

This plugin installs a skill that enforces four mandatory checkpoints before any implementation action (Bash, Write, Edit):

**Checkpoint 1: Hypothesis Stated** — Claude must state a specific, falsifiable hypothesis about what is wrong and what system it targets.

**Checkpoint 2: Hypothesis Verified** — Claude must gather evidence (read files, check docs, run read-only commands) that confirms or refutes the hypothesis. Cannot proceed on a guess.

**Checkpoint 3: Hypothesis-Action Alignment** — Claude verifies that the proposed fix actually targets the same system the hypothesis identified. Blocks "correct diagnosis, wrong fix" errors.

**Checkpoint 4: Pattern-Matching Detection** — Claude checks whether it is about to apply a "common solution" without verifying that pattern applies here. Forces a project-specific check.

Only when all four checkpoints pass does Claude execute. If any checkpoint fails, Claude halts and reports what it needs before it can proceed.

## What Changes

With this plugin installed, Claude will:

- Read relevant files before trying to fix things
- State a specific hypothesis before gathering evidence
- Verify the diagnosis with file reads, not assumptions
- Check that the fix targets the same system as the diagnosis
- Detect when it is about to apply a training-data pattern to a context it has not verified

This makes Claude slower to start but much more accurate — fewer debugging cycles overall.

## Installation

First, add the marketplace (one-time setup):

```bash
/plugin marketplace add Jamie-BitFlight/claude_skills
```

Then install the plugin:

```bash
/plugin install verification-gate@jamie-bitflight-skills
```

## Usage

Just install it — it works automatically. You will notice the difference when Claude:

- Reads files before running commands
- States what it thinks the problem is before gathering evidence
- Explains what system it is targeting before making changes
- Pauses and reports what it needs when it cannot verify something

## Example

**Without this plugin:**

```
You: This PEP 723 script can't find the pydantic module
Claude: I'll install the dependencies
Claude: [Runs uv sync immediately]
Result: Doesn't work - uv sync operates on pyproject.toml, not PEP 723
```

**With this plugin:**

```
You: This PEP 723 script can't find the pydantic module
Claude: Hypothesis: pydantic is missing from the script's inline dependencies.
        Verifying — need to check whether this script uses PEP 723 metadata.
Claude: [Reads the script file]
Claude: Confirmed: PEP 723 inline dependencies block present. pydantic is not listed.
        Fix target: the # /// script block in the file. Running uv add --script.
Claude: [Runs: uv add --script example.py pydantic]
Result: Works correctly
```

Another example:

**Without this plugin:**

```
You: The app can't connect to the database
Claude: [Immediately edits database config file]
Result: Config change ignored — app reads DATABASE_URL from environment variables
```

**With this plugin:**

```
You: The app can't connect to the database
Claude: Hypothesis: database connection string is misconfigured.
        Need to verify which configuration system the app uses.
Claude: [Reads app.py, config.py, checks for dotenv or os.environ usage]
Claude: App reads DATABASE_URL from environment, not config file.
        Fix target: environment variable, not config file.
Claude: [Checks .env file, identifies missing variable]
```

## Skill

The plugin installs the `verification-gate` skill, which activates automatically when Claude is about to execute implementation actions. The skill enforces the four-checkpoint protocol and integrates with `CLAUDE.md` verification rules.

## Trade-offs

- Claude will be slower to start (2-4 extra file reads before each action)
- Claude will explain its reasoning more (adds verbosity)
- Fixes will be more accurate (fewer debugging cycles)
- Overall time saved despite the slower start

## Requirements

- Claude Code v2.0+
