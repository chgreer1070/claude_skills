---
name: groom-backlog-item
description: Groom backlog items — trigger /groom-backlog-item <title|section|all> — fact-checks item claims against primary sources, runs RT-ICA per item, then spawns @backlog-item-groomer agents. Writes groomed content into per-item files in .claude/backlog/. Use when preparing backlog items for planning or execution.
argument-hint: <item-title-or-section-or-all>
user-invocable: true
---

<groom_scope>$ARGUMENTS</groom_scope>

# Groom Backlog Item

Orchestrate autonomous backlog refinement: verify claims, clarify scope, estimate effort, map resources and dependencies, and clean stale items — making each item ready for the planning phase.

**Scope boundary**: Grooming answers "what needs to be done, is the problem clear, and what do we have to work with?" It does NOT answer "how should it be built." Architecture, task decomposition, and implementation design happen in the SAM planning phase (`/work-backlog-item` Step 6). Grooming produces a DEEP item (Detailed appropriately, Estimated, Emergent, Prioritized) — not a plan. The human provides direction and priorities; the agent does the research, fact-checking, and resource mapping autonomously.

## Arguments

`<groom_scope/>` accepts:

- **Title substring** — e.g., `Error Recovery` — grooms matching item (case-insensitive)
- **Section** — `P0`, `P1`, `P2`, or `Ideas` — grooms all items in that section
- **`all`** — grooms all items across P0, P1, P2, Ideas (parallel agents)

## Workflow

### Step 1: Parse Arguments and Load Backlog

Call `mcp__backlog__backlog_list()` and filter the returned dict's `items` list by argument type above.

### Step 2: Validity Check (Pre-Groom Gate)

Before fact-checking or grooming, verify each item is still valid work:

1. **Is the job still valid?** — Scope, priority, or context may have changed. Ask or infer: does this item still belong in the backlog?
2. **Is the work already done?** — Search for evidence that the feature was already implemented or the bug was already fixed, even if the issue is still open. Run the **Already Implemented Discovery** procedure:

   a. **Search for commits matching the item's topic** (use keywords from the title):

      ```bash
      git log --oneline --all -30 --grep="{keyword from title}"
      ```

   b. **Search for merged PRs matching the topic**:

      ```bash
      gh pr list -R Jamie-BitFlight/claude_skills --search "{keyword}" --state merged --json number,title,url,mergedAt --limit 5
      ```

   c. **Check if the described feature/fix exists in the codebase** — read the files at the suggested location and verify whether the described behavior is already present.

   If evidence shows the work is done:

   - **Comment evidence on the GitHub issue** (if one exists):

     ```bash
     gh issue comment N -R Jamie-BitFlight/claude_skills --body "This work was already completed via PR #{pr} / commit {sha}. Closing."
     ```

   - **Close the GitHub issue**:

     ```bash
     gh issue close N -R Jamie-BitFlight/claude_skills --reason completed
     ```

   - **Close the local backlog item**:

     Call `mcp__backlog__backlog_resolve(selector="{title}", summary="Already implemented via PR #{pr} / commit {sha}")`.

   - Report to the user and skip grooming for that item.

   If no evidence is found, proceed — the work is still needed.
3. **Is this local file stale?** — If the item has a GitHub issue (`metadata.issue` or index link `#N`), call `mcp__backlog__backlog_view(selector="#{N}")` and check the `state` field in the returned dict. If the issue is **closed**, the local file is a stale remnant of work already done. Do **not** groom. Instead, run the **Completed Issue Discovery** procedure:

   a. **Search for commits referencing the issue**:

      ```bash
      git log --oneline --all -20 --grep="#N"
      ```

   b. **Search for merged PRs referencing the issue**:

      ```bash
      gh pr list -R Jamie-BitFlight/claude_skills --search "#N" --state merged --json number,title,url,mergedAt --limit 5
      ```

   c. **Comment evidence on the issue** (if not already present):

      ```bash
      gh issue comment N -R Jamie-BitFlight/claude_skills --body "Completed via PR #M / commit {sha}"
      ```

   d. **Close the local backlog item with evidence**:

      Call `mcp__backlog__backlog_resolve(selector="{title}", summary="Completed via PR #{pr} / commit {sha}")`.

   If no commits or PRs reference the issue, report: "Issue #{N} is closed but no commit/PR evidence found. Recommend manual review." and skip grooming.
   Skip grooming for that item; move to the next.

4. **Is this item already groomed today?** — Check the item file's `groomed` frontmatter field. If it matches today's date AND the item has all required sections (Fact-Check, RT-ICA, groomed subsections), skip Steps 4–8 entirely. Go directly to Step 9 and apply only the specific change requested by the user — do not re-derive, re-fact-check, or re-groom. Re-running the full pipeline on an already-groomed item produces duplicate content and wastes tokens.

If any of checks 1–3 fail, skip grooming for that item and report. For items that pass checks 1–3, proceed to Step 3. For items that pass checks 1–3 but match check 4 (already groomed today), skip directly to Step 9.

### Step 3: Extract Item Details

For each target item, extract: title, description, research-first questions (if present), source, suggested location.

### Step 3.5: Impact Radius Analysis

**Purpose**: Before fact-checking or grooming, identify every system the item's scope touches. The planning phase uses this to create tasks for every affected component — not just the new code.

Two phases: build a systems inventory, then run an impact checklist on each system.

#### Phase 1: Build the Affected Systems Inventory

Starting from the files and functions already identified in the groomed content (Files, Evidence, Description, suggested_location sections), identify all systems that interact with the thing this item changes. A "system" is any file that produces, consumes, documents, configures, tests, or instructs the use of the affected interface.

Create a TodoItem for each system found. Each TodoItem includes: file path, role (producer / consumer / documentation / configuration / CI / agent-instruction), and connection (why this file is affected).

Start with the known systems from the groomed content:
- Files listed in the **Files** section
- Functions cited in the **Output / Evidence** section
- Path from **suggested_location**

Then expand by searching for:
- Files that import from or call into the known systems
- Documentation that describes the current behavior of these systems
- Agent or skill files that instruct the AI to use these systems
- Configuration files that reference these modules
- CI workflows that test these modules
- Test files that exercise these systems

Exclude archived and generated content from the inventory: `plan/` artifacts, `docs/plans/`, `.claude/archive/`, `.claude/grooming-sessions/`, test fixtures. Backlog item files (`.claude/backlog/*.md`) are informational — they describe the problem, not the system.

#### Phase 2: Impact Checklist (per system)

For each TodoItem in the inventory, answer these five questions:

1. **Will this file break when the item ships?** — Does it depend on an interface, format, or behavior that the item changes? If yes: what specifically breaks.
2. **Will this file become stale?** — Does it describe, document, or reference the current behavior? If yes: what section or claim becomes inaccurate.
3. **Does this file need a code change?** — Import update, API migration, format change, dependency update. If yes: what change.
4. **Does this file need a content update?** — Documentation rewrite, instruction update, example refresh. If yes: what section.
5. **Is there a test that covers this file's interaction with the changed interface?** — If no: flag as needing a new test.

Mark each TodoItem complete after answering. Any system with at least one "yes" answer goes into the Impact Radius output.

#### Output format

Write findings as an Impact Radius section:

```markdown
## Impact Radius

### Code — Producers (write the changed interface)
- `{path}::{function_name}` — {what it produces, what change is needed}

### Code — Consumers (read the changed interface)
- `{path}::{function_name}` — {what it consumes, what migration is needed}

### Code — Other References
- `{path}` — {import/constant/type reference, what change is needed}

### Documentation (will become stale)
- `{path}` — {what section becomes inaccurate}

### Configuration / CI
- `{path}` — {what change is needed}

### Agent Instructions (instruct AI to use current interface)
- `{path}` — {what instruction needs updating}

### Systems Inventory
{full list of TodoItems with roles and connections, for planner completeness verification}

### Ecosystem Completeness Checklist
- [ ] Every code producer updated or verified compatible
- [ ] Every code consumer migrated to new interface
- [ ] Every stale document updated
- [ ] Every agent instruction updated
- [ ] Old interface deprecated or removed (if replacing)
- [ ] CI/config files updated and validated
```

If a category has no affected files, write `None identified.` — do not omit the category.

**Carry forward**: Pass the Impact Radius section to Step 5 (RT-ICA) and Step 8 (groomer agent). Write it to the item file after Step 8 via `mcp__backlog__backlog_groom(selector="{title}", section="Impact Radius", content="{impact radius section}")`.

### Step 4: Fact-Check Item Claims

Invoke the `fact-check` skill on each target item to verify factual claims against primary sources **before** running RT-ICA or spawning groomer agents. This prevents unverified or refuted assertions from entering the planning context.

```text
Skill(skill: "fact-check", args: "{item title}")
```

The `fact-check` skill spawns `@fact-checker` agents that MUST retrieve evidence via `WebFetch`, `WebSearch`, or `gh`. Training data recall is not accepted as evidence.

After each run, collect the verdict summary:

```text
Fact-Check Summary: {item title}
Claims checked: {N}
VERIFIED: {N} | REFUTED: {N} | INCONCLUSIVE: {N}
Refuted claims:      [{list of claim texts — each becomes a MISSING condition in Step 5}]
Inconclusive claims: [{list of claim texts — flag as unverified DERIVABLE in Step 5}]
Citations:           [{VERIFIED claims cite their primary sources}]
```

**Multiple items** — invoke `fact-check` for each item sequentially (respect the wave-of-5 concurrency limit inside `fact-check` itself). Do not batch items into a single `fact-check` call.

Pass the fact-check summary forward to Step 5.

### Step 5: RT-ICA Assessment Per Item

Perform Reverse Thinking — Information Completeness Assessment using both the item details **and** the fact-check verdicts from Step 4. This directs the groomer's discovery toward filling gaps rather than broad search.

For each item, produce:

```text
RT-ICA: {item title}
Goal: {one sentence — what completing this item achieves}
Conditions:
1. {condition} | Status: {AVAILABLE|DERIVABLE|MISSING} | Info needed: {what}
...
Decision: {APPROVED|BLOCKED}
Missing: {list of missing inputs, or "None"}
```

- **AVAILABLE**: Explicitly stated in item description or research questions AND fact-check verdict (Step 4) is VERIFIED or not applicable
- **DERIVABLE**: Safely inferable from codebase context (state basis); fact-check verdict is INCONCLUSIVE
- **MISSING**: Not present, not safely inferable — OR fact-check verdict is REFUTED (the stated condition is false and the correct state is unknown)

REFUTED claims from Step 4 MUST be listed as MISSING conditions. A REFUTED claim is not a valid basis for any AVAILABLE or DERIVABLE status.

Pass the RT-ICA summary, fact-check summary, and Impact Radius section to the groomer alongside item details.

**ARL human-probing integration:** When RT-ICA returns BLOCKED or MISSING conditions, the context manifest can include `invisible_knowledge_prompts` — questions to ask the human before planning (e.g., "What went wrong in the past?", "What references are essential?"). See [.claude/docs/sdlc-layers/arl-human-probing-design.md](../../docs/sdlc-layers/arl-human-probing-design.md).

### Step 6: Issue Classification

Classify the issue type to determine analysis depth and verification criteria. Done by the orchestrator — requires reasoning about the problem's nature. See the flowchart and write template in [issue-classification.md](./references/issue-classification.md).

| Type | Analysis Method |
|------|----------------|
| `procedural` | none |
| `recurring-pattern` | 6-sigma |
| `defect` | 5-whys |
| `missing-guardrail` | none |
| `unbounded-design` | design-framing |

Write classification to the item via `mcp__backlog__backlog_groom(selector, section="Issue Classification", content=...)`. Full template with `scenario-target` field: [issue-classification.md](./references/issue-classification.md).

### Step 7: Root-Cause Analysis (Conditional)

**Only for `defect` or `recurring-pattern`**. Skip for `procedural`, `missing-guardrail`, and `unbounded-design`.

- **defect**: invoke `Skill(skill="find-cause", args="{description}")` and write 5-whys evidence chain
- **recurring-pattern**: search `mcp__backlog__backlog_list(status="resolved")` for recurrence frequency and write 6-sigma measurement

Full procedures and write templates: [issue-classification.md](./references/issue-classification.md)

### Step 8: Spawn Groomer Agents

**IMPORTANT**: Use `Agent(subagent_type: "backlog-item-groomer")`. Do NOT groom inline — always delegate.

- **Single item**: spawn one agent
- **Multiple items**: parallel agents (max 5 concurrent; batch in waves if more)

Full prompt templates: [groomer-agent.md](./references/groomer-agent.md)

Pass RT-ICA context, fact-check verdicts, classification, RCA output, Impact Radius section, and file paths (not pasted content) to the groomer.

### Step 9: Write Groomed Content to Item Files

For each item, write groomed content into the per-item file via the backlog MCP tools.

**MCP tool parameters are schema-enforced.** Unlike CLI subcommands, MCP tools reject invalid parameters
with a structured error. There is no need to verify signatures before calling. If unsure which tool to
use, check the tool name and parameters:

- `mcp__backlog__backlog_update` — updates an existing item (selector required)
- `mcp__backlog__backlog_groom` — writes groomed content (selector required)
- `mcp__backlog__backlog_sync` — creates GitHub issues for items missing them and pushes groomed content (no selector — operates on entire backlog)

Prefer incremental updates so sections (Fact-Check, RT-ICA, groomed subsections) are written as they become available. GitHub is canonical: when the item has an issue, the MCP tool syncs groomed content to the GitHub issue body.

**Preferred: incremental section updates**

After each step, call `mcp__backlog__backlog_groom` with `section` and `content`:

```text
# After Step 4 (fact-check)
mcp__backlog__backlog_groom(selector="{item title}", section="Fact-Check", content="{fact-check summary}")

# After Step 5 (RT-ICA)
mcp__backlog__backlog_groom(selector="{item title}", section="RT-ICA", content="{rt-ica summary}")

# After Step 8 (groomer output) — subsection or full groomed body
mcp__backlog__backlog_groom(selector="{item title}", section="Reproducibility", content="{reproducibility section}")
# ... or for full groomed body:
mcp__backlog__backlog_groom(selector="{item title}", groomed_content="{full groomed body}")
```

**Alternative: full content**

```text
mcp__backlog__backlog_groom(selector="{item title}", groomed_content="{full groomed body}")
```

Note — `--groomed-file {path}` and stdin pipe (`< {file}`) patterns have no MCP equivalent.
Provide groomed content inline via the `groomed_content` parameter.

**Valid section names** — top-level: `Fact-Check`, `RT-ICA`, `Impact Radius`. Groomed subsections: `Reproducibility`, `Priority`, `Impact`, `Scope`, `Output / Evidence`, `Dependencies`, `Research`, `Skills`, `Agents`, `Prior Work`, `Files`, `Decision`, `Issue Classification`, `Root-Cause Analysis`.

The backlog script updates `.claude/backlog/{priority}-{slug}.md` with merged sections, sets `groomed` in frontmatter, and syncs to the GitHub issue when the item has one.

**Bulk grooming (multiple items)** — when grooming 2+ items, optionally persist a session summary to `.claude/grooming-sessions/{YYYY-MM-DD}.md`:

```markdown
# Grooming Session {YYYY-MM-DD}

**Items groomed**: {count}
**Arguments**: {original arguments}

## Summary

| Item | Fact-Check | RT-ICA | Written |
|------|------------|--------|---------|
| {title} | {V}/{R}/{I} | {APPROVED/BLOCKED} | ✓ |

## Cross-Item Findings

### Shared Dependencies
- {items multiple backlog items depend on}

### Suggested Groupings
- {items that could be worked together}

### Research Gaps
- {topics needing research}
```

Per-item groomed content lives in each item file; this session file holds only metadata and cross-item findings.

## Example Invocations

```text
/groom-backlog-item Error Recovery
/groom-backlog-item P1
/groom-backlog-item all
```

## Completion Criteria

- Validity check (job still valid, problem reproducible, local file not stale) before grooming
- Impact Radius analysis performed (Step 3.5): documents, upstream producers, downstream consumers, config/CI files identified
- Impact Radius section written to item file via `mcp__backlog__backlog_groom(section="Impact Radius", content=...)`
- Fact-check run for each item before RT-ICA (training data not used as evidence)
- Fact-check verdicts passed into RT-ICA conditions (REFUTED → MISSING)
- RT-ICA summary included for each item
- Groomer agent(s) spawned via `Agent(subagent_type: "backlog-item-groomer")` — NOT groomed inline
- Groomer agent(s) received RT-ICA context, fact-check verdicts, Impact Radius section, and file paths (not pasted content)
- Groomed content written via `mcp__backlog__backlog_groom` (prefer `section`/`content` parameters for incremental updates; `groomed_content` for full body)
- When item has GitHub issue, groomed content synced to issue body
- Bulk session summary optionally saved to `.claude/grooming-sessions/{date}.md` when grooming multiple items
- Issue classification assigned for each item (Step 6)
- Root-cause analysis performed for `defect` and `recurring-pattern` items (Step 7)
- Classification and analysis passed to groomer agent as context (Step 8)
