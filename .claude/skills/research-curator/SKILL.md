---
name: research-curator
description: Add resources to the research directory with comprehensive documentation. Supports single URL, batch processing via --batch, re-research via --rerun, and validation via --validate. Triggers on "add to research", "document this tool", "research this", or URLs to novel agentic development resources.
argument-hint: '[url] [--batch url1 url2 ...] [--rerun category/name|all] [--validate category/name|all]'
user-invocable: true
---
> [!IMPORTANT]
> When provided a process map or Mermaid diagram, treat it as the authoritative procedure. Execute steps in the exact order shown, including branches, decision points, and stop conditions.
> A Mermaid process diagram is an executable instruction set. Follow it exactly as written: respect sequence, conditions, loops, parallel paths, and terminal states. Do not improvise, reorder, or skip steps. If any node is ambiguous or missing required detail, pause and ask a clarifying question before continuing.
> When interacting with a user, report before acting the interpreted path you will follow from the diagram, then execute.

# Research Curator -- Multi-Mode Orchestrator

Orchestrate research entry creation, maintenance, and validation in `./research/`. Spawns `@research-curator` agents for content work; handles coordination, README updates, and post-actions.

---

## Mode Routing

Parse `$ARGUMENTS` to select operating mode. Optional `--layer 0|1|2` filters discovery by SDLC layer when used with knowledge-explorer or refresh-research.

The following diagram is the authoritative procedure for mode routing. Execute steps in the exact order shown, including branches, decision points, and stop conditions.

```mermaid
flowchart TD
    Start(["Parse $ARGUMENTS"]) --> Q1{"Does $ARGUMENTS contain --batch?"}
    Q1 -->|"Yes — batch flag present"| Q1Layer{"Does $ARGUMENTS also contain --layer 0, 1, or 2?"}
    Q1 -->|"No — batch flag absent"| Q2{"Does $ARGUMENTS contain --rerun?"}
    Q1Layer -->|"Yes — layer filter present"| BatchLayer(["Execute Batch Mode with layer filter applied"])
    Q1Layer -->|"No — no layer filter"| Batch(["Execute Batch Mode"])
    Q2 -->|"Yes — rerun flag present"| Q2Layer{"Does $ARGUMENTS also contain --layer 0, 1, or 2?"}
    Q2 -->|"No — rerun flag absent"| Q3{"Does $ARGUMENTS contain --validate?"}
    Q2Layer -->|"Yes — layer filter present"| RerunLayer(["Execute Rerun Mode with layer filter applied"])
    Q2Layer -->|"No — no layer filter"| Rerun(["Execute Rerun Mode"])
    Q3 -->|"Yes — validate flag present"| Validate(["Execute Validate Mode"])
    Q3 -->|"No — no flags matched — $ARGUMENTS contains a URL only"| Default(["Execute Default Mode — single URL"])
```

---

## Research Directory

Single source of truth: `./research/` (repo-root relative).

Structure:

```text
./research/
  README.md              # Category tables with all entries
  {category}/            # One directory per category
    {resource-name}.md   # Individual research entries
```

Category selection follows the flowchart in [Entry Template](./references/entry-template.md). Create directories as needed.

---

<default_mode>

## Default Mode -- Single URL

Trigger: `$ARGUMENTS` contains a URL with no flags.

### Workflow

1. **Parse** -- extract the URL from `$ARGUMENTS`
2. **Spawn agent** -- invoke `@research-curator` via Agent tool with the URL

   ```text
   Agent tool parameters:
     agent: .claude/agents/research-curator.md
     prompt: "Research and create an entry for: {URL}"
   ```

3. **Wait** for structured result (status, file path, category, key findings)
4. **Update README** -- add new entry to the appropriate category table in `./research/README.md`
5. **Post-actions** -- lint, commit, push (see [Post-Actions](#post-actions))

### Error Handling

- If agent returns `status: failed`, report the failure reason to user and stop
- Do not create partial entries or update README on failure

</default_mode>

---

<batch_mode>

## Batch Mode

Trigger: `$ARGUMENTS` contains `--batch`.

Full workflow defined in [Batch Mode reference](./references/batch-mode.md). Summary below.

### URL Parsing

Extract all tokens after `--batch` matching `https?://` as target URLs. Non-URL tokens ignored with warning.

### Wave Spawning

The following diagram is the authoritative procedure for batch wave spawning. Execute steps in the exact order shown, including branches, decision points, and stop conditions.

```mermaid
flowchart TD
    Start(["Parse deduplicated URLs from --batch"]) --> Count{"How many URLs remain after duplicate check?"}
    Count -->|"1 to 5 — fits in one wave"| Wave1["Spawn all URLs as Wave 1<br>up to 5 parallel @research-curator agents via Agent tool"]
    Count -->|"6 to 10 — fits in two waves"| W1a["Spawn Wave 1 — first 5 URLs<br>up to 5 parallel @research-curator agents"]
    Count -->|"11 or more — requires three or more waves"| WNa["Spawn Wave 1 — URLs 1 through 5<br>up to 5 parallel @research-curator agents"]
    Wave1 --> Collect["Collect structured results from all agents<br>(status, file path, category, key findings)"]
    W1a --> W1aDone["Wait for all Wave 1 agents to complete"]
    W1aDone --> W2a["Spawn Wave 2 — remaining URLs<br>up to 5 parallel @research-curator agents"]
    W2a --> Collect
    WNa --> WNaDone["Wait for current wave to complete"]
    WNaDone --> QMore{"More URLs remaining?"}
    QMore -->|"Yes — advance to next batch of 5"| WNa
    QMore -->|"No — all URLs processed"| Collect
    Collect --> Results{"Did any agent return status: failed?"}
    Results -->|"No — all succeeded"| UpdateAll["Update ./research/README.md<br>add all new entries to category tables"]
    Results -->|"Yes — one or more failed"| Partial["Update ./research/README.md<br>with successful entries only<br>Report each failure with reason to user"]
    UpdateAll --> PostActions(["Execute Post-Actions — lint, commit, push"])
    Partial --> PostActions
```

Each wave: spawn up to 5 `@research-curator` agents in parallel via Agent tool. Wait for all agents in the current wave before spawning the next.

### Duplicate Detection

Before spawning, check if `./research/` already contains an entry for the URL's resource. If found, skip with info message suggesting `--rerun` instead.

### Progress Reporting

After each wave:

```text
Wave N complete: M/N succeeded
  created -- category/resource-name.md
  created -- category/resource-name.md
  failed  -- https://url.com -- error: [reason]
```

After all waves:

```text
Batch complete: X/Y total succeeded
Files created: [list]
README updated: Yes
```

</batch_mode>

---

<rerun_mode>

## Rerun Mode

Trigger: `$ARGUMENTS` contains `--rerun`.

Re-research existing entries to refresh stale data.

### Target Parsing

The following diagram is the authoritative procedure for rerun mode. Execute steps in the exact order shown, including branches, decision points, and stop conditions.

```mermaid
flowchart TD
    Start(["Parse --rerun argument value"]) --> Q{"What is the --rerun target value?"}
    Q -->|"category/name — single entry path"| VerifyFile{"Does ./research/category/name.md exist?"}
    Q -->|"all — re-research every entry"| FindAll["Glob ./research/**/*.md<br>excluding README.md — collect all entry paths"]
    VerifyFile -->|"No — file not found"| Missing(["Report error: entry not found at path. Stop."])
    VerifyFile -->|"Yes — file exists"| ReadFile["Read ./research/category/name.md<br>extract current content and metadata"]
    ReadFile --> Spawn1["Spawn @research-curator via Agent tool<br>prompt: --rerun ./research/category/name.md"]
    Spawn1 --> UpdateDate["Update ./research/README.md<br>refresh freshness date for this entry"]
    FindAll --> WaveSpawn["Spawn @research-curator agents in waves of 5<br>each receives --rerun ./research/category/name.md<br>wait for each wave before spawning next"]
    WaveSpawn --> UpdateDates["Update ./research/README.md<br>refresh freshness dates for all re-researched entries"]
    UpdateDate --> PostActions(["Execute Post-Actions — lint, commit, push"])
    UpdateDates --> PostActions
```

### Single Entry Rerun

1. Verify `./research/{category}/{name}.md` exists
2. Spawn `@research-curator` via Agent tool:

   ```text
   prompt: "--rerun ./research/{category}/{name}.md"
   ```

3. Agent reads existing entry, re-gathers fresh data, updates content and freshness tracking
4. Update README with refreshed date

### All Entries Rerun

1. Glob `./research/**/*.md` excluding `README.md`
2. Spawn agents in waves of 5 (same pattern as Batch Mode)
3. Each agent receives `--rerun ./research/{category}/{name}.md`
4. Update README once after all waves complete

</rerun_mode>

---

<validate_mode>

## Validate Mode

Trigger: `$ARGUMENTS` contains `--validate`.

Run structural validation and fix error-severity issues.

### Validation Workflow

The following diagram is the authoritative procedure for validate mode. Execute steps in the exact order shown, including branches, decision points, and stop conditions.

```mermaid
flowchart TD
    Start(["Parse --validate argument value"]) --> Q{"What is the --validate target value?"}
    Q -->|"category/name — single entry path"| RunScript["Run validate_research.py --json<br>on ./research/category/name.md"]
    Q -->|"all — validate every entry"| RunScriptAll["Run validate_research.py --json<br>on ./research/ directory"]
    RunScript --> ParseJSON["Parse JSON output from validator<br>extract issues by severity: error, warning, info"]
    RunScriptAll --> ParseJSON
    ParseJSON --> HasErrors{"Does parsed output contain<br>any error-severity issues?"}
    HasErrors -->|"Yes — one or more errors found"| SpawnFix["Spawn @research-curator agents in waves of 5<br>each receives --fix flag and specific error details"]
    HasErrors -->|"No — zero error-severity issues"| ReportClean(["Report: all entries passed validation.<br>Include any warnings and info items. Stop."])
    SpawnFix --> ReportSummary["Report validation summary<br>(total scanned, passed, errors fixed, warnings noted)"]
    ReportSummary --> PostActions(["Execute Post-Actions — lint, commit, push"])
```

### Script Invocation

```bash
./scripts/validate_research.py --json ./research/{target}
```

The script is located at `.claude/skills/research-curator/scripts/validate_research.py` relative to the repo root. Invoke from the skill directory or use the full relative path.

### Issue Handling

Severity handling per [Validation Rules](./references/validation-rules.md):

- **error** -- spawn `@research-curator` with `--fix` flag and specific issues to fix
- **warning** -- include in report to user; do not auto-fix
- **info** -- include in report; no action needed

For error-severity fixes, spawn agents in waves of 5 (same pattern as Batch Mode).

### Summary Report

```text
Validation complete:
  Total scanned: N
  Passed: N
  Errors found: N (M auto-fixed)
  Warnings noted: N
```

</validate_mode>

---

<post_actions>

## Post-Actions

Shared by all modes. Execute after any mode completes successfully.

1. **README Update** -- add or update entries in `./research/README.md` category tables
2. **Lint** -- run formatting checks on all modified files:

   ```bash
   uv run prek run --files ./research/README.md [new-or-modified-files]
   ```

3. **Commit** -- stage and commit all research changes:

   ```bash
   git add ./research/
   git commit -m "docs(research): [action] [resource names]"
   ```

4. **Push** -- push to current branch:

   ```bash
   git push -u origin HEAD
   ```

Commit message actions by mode:

- Default -- `add {resource-name} research entry`
- Batch -- `add {N} research entries`
- Rerun -- `refresh {resource-name|N entries}`
- Validate -- `fix validation issues in {resource-name|N entries}`

</post_actions>

---

<output_format>

## Output Format

Report to user after any mode completes.

### Default Mode Output

```text
## Research Entry Created

**Resource**: {name}
**Category**: {category}
**File**: ./research/{category}/{filename}.md
**README Updated**: Yes

### Key Findings
- Finding 1
- Finding 2
- Finding 3

### Next Review
YYYY-MM-DD
```

### Batch Mode Output

```text
## Batch Research Complete

**Total**: X URLs processed
**Succeeded**: Y entries created
**Failed**: Z (with reasons)

### Entries Created
- ./research/{category}/{name}.md
- ./research/{category}/{name}.md

### Failures
- {URL} -- {reason}
```

### Rerun Mode Output

```text
## Research Entries Refreshed

**Refreshed**: N entries
**Changes Detected**: M entries had updated data

### Updated Entries
- ./research/{category}/{name}.md -- {what changed}
```

### Validate Mode Output

```text
## Validation Results

**Scanned**: N entries
**Passed**: N
**Errors Fixed**: N
**Warnings**: N

### Fixes Applied
- ./research/{category}/{name}.md -- {issue fixed}

### Warnings (manual review recommended)
- ./research/{category}/{name}.md -- {warning description}
```

</output_format>

---

## Reference Links

- [Entry Template](./references/entry-template.md) -- standard format for all research entries
- [Validation Rules](./references/validation-rules.md) -- checks and severity mapping for `--validate` mode
- [Batch Mode](./references/batch-mode.md) -- wave spawning workflow for `--batch` mode
- Agent: `@research-curator` at `.claude/agents/research-curator.md` -- single-entry research executor
