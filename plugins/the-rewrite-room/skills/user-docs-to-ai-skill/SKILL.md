---
name: user-docs-to-ai-skill
description: Converts user-facing documentation (how-to guides, tutorials, API references, examples) into Claude Code skill directories — SKILL.md with valid frontmatter plus thematically grouped references/*.md files. Use when given a docs directory to transform into an AI skill, when building expert-level Claude knowledge from library or tool documentation, or when the user asks to create a skill from existing docs. Produces output equivalent in quality to fastmcp-creator.
allowed-tools: Read, Grep, Glob, Bash, Write, Edit, Task
---

# User Docs to AI Skill

Converts human-readable documentation into a Claude Code skill directory. The output is consumed by Claude, not humans — every word must serve AI comprehension, not user readability.

## Inputs

- `docs_path` — directory containing user-facing documentation (markdown, HTML, RST, plain text)
- `output_plugin` — name for the output plugin (e.g., `ty-skill`)
- `output_skill` — name for the skill within the plugin (usually same as plugin without `-skill` suffix)
- `net_new` — boolean; `true` = create from scratch, `false` = improve existing skill at output path

## Output Contract

Creates `plugins/{output_plugin}/skills/{output_skill}/` containing:

- `SKILL.md` — valid frontmatter + AI-facing workflow instructions + links to all reference files
- `references/` — thematically grouped knowledge files, each linked from SKILL.md

## Workflow

```mermaid
flowchart TD
    Start([Skill receives docs_path + output_plugin + output_skill]) --> Phase0[Phase 0 — Inventory]
    Phase0 --> Inv[Glob all files in docs_path\nCount by type: .md .html .rst .txt\nIdentify top-level sections and index files]
    Inv --> Phase1[Phase 1 — Extraction]
    Phase1 --> Extract[Apply extraction patterns per doc type\nSee extraction-patterns.md]
    Extract --> Phase15[Phase 1.5 — Workflow Identification]
    Phase15 --> WfDetect[Scan atoms for TYPE: pattern and TYPE: constraint atoms<br>that describe multi-step sequences or decision trees]
    WfDetect --> Q0{Any workflow-shaped atoms found?}
    Q0 -->|No| Classify
    Q0 -->|Yes — delegate each to process-siren| WfDelegate["Task: subagent_type='process-siren:process-siren'<br>Output: resources/workflows/{slug}.md"]
    WfDelegate --> Classify[Classify remaining atoms into themes\nEach theme becomes one reference file]
    Classify --> Phase2[Phase 2 — Structure]
    Phase2 --> Q1{net_new?}
    Q1 -->|true| Scaffold[Scaffold output directory\nplugins/output-plugin/skills/output-skill/\nplugins/output-plugin/.claude-plugin/plugin.json]
    Q1 -->|false| Merge[Read existing skill\nIdentify gaps vs extracted knowledge\nPlan surgical additions only]
    Scaffold --> Write[Phase 3 — Write]
    Merge --> Write
    Write --> RefFiles[Write references/*.md files\nOne file per theme — see skill-structure-guide.md]
    RefFiles --> SkillMD[Write SKILL.md\nFrontmatter + workflow + links to all reference files]
    SkillMD --> Phase4[Phase 4 — Verify]
    Phase4 --> QC[Apply quality-criteria.md checklist\nFix any failing criteria]
    QC --> Q2{All criteria pass?}
    Q2 -->|No| Fix[Fix failing items — re-run checklist]
    Fix --> Q2
    Q2 -->|Yes| Done([Done — report output path and file inventory])
```

## Phase 0 — Inventory

Run before any extraction. Do not skip.

1. `Glob("**/*", docs_path)` — list all files
2. Group by extension: `.md`, `.html`, `.rst`, `.txt`, other
3. Read the index file (`index.md`, `README.md`, `index.html`, or equivalent) to understand top-level structure
4. List all section headings from the index — these hint at reference file themes
5. Note total file count and estimated reading volume

Report the inventory before proceeding to Phase 1.

## Phase 1 — Extraction

Apply extraction patterns from [extraction-patterns.md](./references/extraction-patterns.md).

Extraction produces a structured list of knowledge atoms:

```text
ATOM: <one-sentence fact, constraint, parameter, or pattern>
TYPE: <command | parameter | constraint | pattern | error | example>
SOURCE: <filename:section>
```

Collect atoms into a flat list first. Do not group yet — grouping happens in Phase 2.

## Phase 1.5 — Workflow Identification

Runs after Phase 1 extraction, before Phase 2 grouping. Identifies workflow-shaped atoms and converts them to validated Mermaid diagrams via `process-siren`.

See [workflow-identification.md](./references/workflow-identification.md) for detection criteria, delegation prompt construction, and blocking-condition responses.

### Identify Workflow-Shaped Atoms

Scan the flat atom list produced in Phase 1. An atom is workflow-shaped when it meets any of:

- Describes a multi-step sequence with order-dependent steps
- Contains decision conditions with observable branch outcomes
- Involves multiple actors or system states with explicit transitions
- Has a defined terminal outcome (success, failure, or completion state)

Simple sequential prose ("first do X, then do Y") without branching is NOT workflow-shaped — leave it as atoms for thematic grouping.

### Delegate Each Workflow to process-siren

For each identified workflow-shaped atom cluster, delegate via Task tool:

```text
Task: subagent_type="process-siren:process-siren"
Context to include in the prompt:
  - The raw prose or atom text verbatim
  - What the workflow represents (1 sentence of context)
  - Output file path: plugins/{output_plugin}/skills/{output_skill}/resources/workflows/{slug}.md
Output: resources/workflows/{slug}.md — validated Mermaid flowchart file
```

Derive `{slug}` from the workflow topic (e.g., `installation-flow`, `error-recovery`, `auth-decision`).

### When process-siren Blocks

process-siren blocks when it detects undefined actors, vague conditions, or missing terminal states. Respond by:

1. Returning to the source docs for the specific missing element
2. Extracting the clarifying detail and re-delegating with updated prose
3. If the source docs do not resolve the gap — write a stub file at the output path containing `<!-- TODO: manual-workflow-needed — [describe the gap] -->` and continue

### Reference Workflow Files from SKILL.md

After all workflow files are written, add a `## Workflows` section to the output SKILL.md listing each file:

```text
## Workflows

- [Workflow Name](./resources/workflows/slug.md)
```

## Phase 2 — Thematic Grouping

Group atoms into themes. Each theme becomes one reference file.

Rules:

- A theme is a coherent knowledge domain (e.g., "configuration options", "error messages", "CLI commands")
- Maximum 6 themes. If more exist, merge related ones.
- Minimum 3 atoms per theme. If fewer, merge into an adjacent theme.
- Theme names map directly to reference filenames — see [skill-structure-guide.md](./references/skill-structure-guide.md)

## Phase 3 — Write Reference Files

For each theme, write `references/{theme-slug}.md`.

Follow the format rules in [skill-structure-guide.md](./references/skill-structure-guide.md).

Write all reference files before writing SKILL.md.

## Phase 4 — Write SKILL.md

After all reference files exist:

1. Write frontmatter — see frontmatter rules in [skill-structure-guide.md](./references/skill-structure-guide.md)
2. Write workflow section as a Mermaid flowchart covering the primary task types the skill handles
3. Write one section per reference file linking to it with `[text](./references/filename.md)`
4. Confirm every reference file is linked from SKILL.md

## Phase 5 — Quality Verification

Apply the checklist in [quality-criteria.md](./references/quality-criteria.md) before declaring done.

If any item fails, fix it and re-run the checklist. Do not declare done with failing criteria.

## Reference Files

- [extraction-patterns.md](./references/extraction-patterns.md) — how to extract AI-usable knowledge from each doc type
- [workflow-identification.md](./references/workflow-identification.md) — detecting workflow-shaped content, constructing process-siren delegation prompts, and responding to blocking conditions
- [skill-structure-guide.md](./references/skill-structure-guide.md) — output skill directory structure, frontmatter rules, reference file format
- [quality-criteria.md](./references/quality-criteria.md) — measurable criteria and common failure modes
