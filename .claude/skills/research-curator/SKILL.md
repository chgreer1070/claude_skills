---
name: research-curator
description: 'Manage research entries in ./research/ — create, refresh, and validate. Use when asked to add a tool, "document this", "research this", "refresh this research", "validate research entries", or given a tool URL. Modes: default (single URL), --batch (multiple URLs in parallel), --rerun (refresh stale entries), --validate (structural check and auto-fix).'
argument-hint: '[url] [--batch url1 url2 ...] [--rerun category/name|all] [--validate category/name|all]'
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

## Agent Result Relay Rules

These rules apply whenever this orchestrator receives results from any `@research-curator` agent. Violating them corrupts information before it reaches the user.

**Rule 1 — Preserve exact counts.** When an agent reports numbers, relay those exact numbers.

| Agent says | Relay as | Never relay as |
|---|---|---|
| "7 of 10 found" | "7 of 10 found" | "most found" |
| "3 errors, 2 warnings" | "3 errors, 2 warnings" | "several issues" |
| "0 results" | "0 results" | "nothing relevant" |

**Rule 2 — Preserve failure reasons.** Relay the specific reason; do not generalize.

| Agent says | Relay as | Never relay as |
|---|---|---|
| "HTTP 403 Forbidden" | "access denied (HTTP 403)" | "not available" |
| "Connection timeout" | "connection timed out" | "doesn't exist" |
| "File not found at path X" | "file not found at X" | "no such file" |
| "Rate limited" | "rate limited" | "unavailable" |

**Rule 3 — Reference files instead of re-summarizing.** When an agent wrote a file, include its path in the relay.

**Rule 4 — Relay structure, not interpretation.** When an agent returns a STATUS/ARTIFACTS/WARNINGS block, preserve that structure. Do not flatten it into a single sentence.

**Rule 5 — Distinguish observations from conclusions.** "Config has no timeout field" (observation) is different from "timeout defaults to 30s" (agent's conclusion). Keep them distinct.

### Pre-Relay Quality Checklist

Before reporting results to the user after any mode completes, verify:

- [ ] All numbers from agent output are preserved in relay
- [ ] All failure reasons are preserved verbatim (not generalized)
- [ ] File paths are included if agent wrote output files
- [ ] "Not found" has not been upgraded to "doesn't exist"
- [ ] "Inaccessible" has not been upgraded to "unavailable" or "nonexistent"
- [ ] Structured sections (STATUS, ARTIFACTS, WARNINGS) are preserved
- [ ] Agent observations are distinguished from agent conclusions

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
4. **Apply relay rules** -- verify pre-relay checklist before proceeding
5. **Spawn insight agent** (concurrent with step 6) -- if research status is not `failed`, spawn `@research-insight-extractor`:

   ```text
   Agent tool parameters:
     agent: .claude/agents/research-insight-extractor.md
     prompt: "Extract improvements from {file-path-from-agent-result}"
   ```

6. **Update README** (concurrent with insight agent) -- add new entry to `./research/README.md`
7. **Wait for insight agent result** -- collect the structured return block
8. **Surface immediate items** -- if the insight result contains an `IMMEDIATE_ATTENTION:` section, report each listed item to the user immediately:

   ```text
   New backlog item requiring attention: #{issue} {title}
   {one-sentence reason from insight result}
   ```

   If no `IMMEDIATE_ATTENTION` section: report only the count — "N improvements added to backlog from {resource-name}."

9. **Post-actions** -- lint, commit, push (see [Post-Actions](#post-actions))

### Error Handling

- If agent returns `status: failed`, relay the exact failure reason to user and stop
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

Spawn up to 5 `@research-curator` agents per wave via Agent tool. Wait for all agents in the current wave before spawning the next. After all waves complete, spawn `@research-insight-extractor` for each successful entry (concurrent, up to 5). See [Batch Mode reference](./references/batch-mode.md) for the complete wave spawning diagram.

### Duplicate Detection

Before spawning, check if `./research/` already contains an entry for the URL's resource. If found, skip with info message suggesting `--rerun` instead.

### Progress Reporting

After each wave, relay exact counts and exact failure reasons from agent output:

```text
Wave N complete: M/N succeeded
  created -- category/resource-name.md
  created -- category/resource-name.md
  failed  -- https://url.com -- {exact reason from agent}
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
    Spawn1 --> RelayCheck1["Apply pre-relay quality checklist"]
    RelayCheck1 --> UpdateDate["Update ./research/README.md<br>refresh freshness date for this entry"]
    FindAll --> WaveSpawn["Spawn @research-curator agents in waves of 5<br>each receives --rerun ./research/category/name.md<br>wait for each wave before spawning next"]
    WaveSpawn --> RelayCheck2["Apply pre-relay quality checklist<br>to all wave results"]
    RelayCheck2 --> UpdateDates["Update ./research/README.md<br>refresh freshness dates for all re-researched entries"]
    UpdateDate --> SpawnInsight1["Spawn @research-insight-extractor<br>prompt: 'Extract improvements from ./research/category/name.md'"]
    SpawnInsight1 --> WaitInsight1["Wait for insight result<br>Check for IMMEDIATE_ATTENTION items<br>Notify user if any present"]
    WaitInsight1 --> PostActions(["Execute Post-Actions — lint, commit, push"])
    UpdateDates --> SpawnInsightsN["Spawn @research-insight-extractor for each updated entry<br>(concurrent, up to 5)"]
    SpawnInsightsN --> WaitInsightsN["Wait for all insight results<br>Collect IMMEDIATE_ATTENTION items<br>Notify user of any P1 items"]
    WaitInsightsN --> PostActions
```

### Single Entry Rerun

1. Verify `./research/{category}/{name}.md` exists
2. Spawn `@research-curator` via Agent tool:

   ```text
   prompt: "--rerun ./research/{category}/{name}.md"
   ```

3. Agent reads existing entry, re-gathers fresh data, updates content and freshness tracking
4. Apply pre-relay quality checklist to agent result
5. Update README with refreshed date

### All Entries Rerun

1. Glob `./research/**/*.md` excluding `README.md`
2. Spawn agents in waves of 5 (same pattern as Batch Mode)
3. Each agent receives `--rerun ./research/{category}/{name}.md`
4. Apply pre-relay quality checklist after each wave
5. Update README once after all waves complete

</rerun_mode>

---

<validate_mode>

## Validate Mode

Trigger: `$ARGUMENTS` contains `--validate`.

Run structural validation and fix error-severity issues.

### What Gets Checked

The validator script (`validate_research.py`) checks each entry file against the rules in [Validation Rules](./references/validation-rules.md). It emits JSON with three severity levels:

- **error** -- structural violations that make entries unusable (missing required fields, broken links, malformed frontmatter). Auto-fixed by spawning `@research-curator` with `--fix` and the specific issue list.
- **warning** -- quality issues that don't break entries (stale dates, thin summaries). Reported to user; not auto-fixed.
- **info** -- informational observations (entry age, word count). Reported to user; no action.

### Validation Workflow

The following diagram is the authoritative procedure for validate mode. Execute steps in the exact order shown, including branches, decision points, and stop conditions.

```mermaid
flowchart TD
    Start(["Parse --validate argument value"]) --> Q{"What is the --validate target value?"}
    Q -->|"category/name — single entry path"| RunScript["Run validate_research.py --json<br>on ./research/category/name.md"]
    Q -->|"all — validate every entry"| RunScriptAll["Run validate_research.py --json<br>on ./research/ directory"]
    RunScript --> ParseJSON["Parse JSON output<br>Extract issues keyed by severity: error, warning, info<br>Count totals per severity"]
    RunScriptAll --> ParseJSON
    ParseJSON --> HasErrors{"Does parsed output contain<br>any error-severity issues?"}
    HasErrors -->|"Yes — N error-severity issues found"| SpawnFix["Spawn @research-curator agents in waves of 5<br>Each agent receives --fix flag<br>PLUS the exact error list for that entry from JSON output<br>(not a summary — the raw issue text)"]
    HasErrors -->|"No — zero error-severity issues"| ReportClean(["Report: all entries passed. Include exact warning and info counts. Stop."])
    SpawnFix --> RelayCheck["Apply pre-relay quality checklist<br>to all fix-agent results"]
    RelayCheck --> ReportSummary["Report validation summary with exact counts<br>(total scanned, passed, errors fixed, warnings noted, info items)"]
    ReportSummary --> PostActions(["Execute Post-Actions — lint, commit, push"])
```

### Script Invocation

```bash
uv run .claude/skills/research-curator/scripts/validate_research.py --json ./research/{target}
```

### Fix Agent Delegation

When spawning a fix agent, pass the exact error text from the JSON output — not a paraphrase. The agent receives:

```text
prompt: "--fix ./research/{category}/{name}.md
Issues to fix (from validator JSON):
  - {exact issue text from JSON}
  - {exact issue text from JSON}"
```

### Issue Handling

Severity handling per [Validation Rules](./references/validation-rules.md):

- **error** -- spawn `@research-curator` with `--fix` flag and the exact issue list extracted from JSON
- **warning** -- include exact warning text in report to user; do not auto-fix
- **info** -- include exact info text in report; no action needed

For error-severity fixes, spawn agents in waves of 5 (same pattern as Batch Mode).

### Summary Report

Report exact counts from the validator JSON output — do not paraphrase:

```text
Validation complete:
  Total scanned: N
  Passed: N
  Errors found: N (M auto-fixed)
  Warnings noted: N
  Info items: N
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

3. **Commit** -- stage and commit all research and insight changes:

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

Report to user after any mode completes. All counts and failure reasons MUST be relayed exactly as received from agents — apply the pre-relay quality checklist before writing this output.

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
**Failed**: Z

### Entries Created
- ./research/{category}/{name}.md
- ./research/{category}/{name}.md

### Failures
- {URL} -- {exact reason from agent output}
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
**Info**: N

### Fixes Applied
- ./research/{category}/{name}.md -- {exact issue fixed, from validator JSON}

### Warnings (manual review recommended)
- ./research/{category}/{name}.md -- {exact warning text}
```

</output_format>

---

## Reference Links

- [Entry Template](./references/entry-template.md) -- standard format for all research entries
- [Validation Rules](./references/validation-rules.md) -- checks and severity mapping for `--validate` mode
- [Batch Mode](./references/batch-mode.md) -- wave spawning workflow for `--batch` mode
- Agent: `@research-curator` at `.claude/agents/research-curator.md` -- single-entry research executor
- Agent: `@research-insight-extractor` at `.claude/agents/research-insight-extractor.md` -- extracts backlog improvements from research entries

SOURCE: Agent result relay rules and pre-relay checklist adapted from `plugins/summarizer/skills/agent-result-relay/SKILL.md` (accessed 2026-03-06).
