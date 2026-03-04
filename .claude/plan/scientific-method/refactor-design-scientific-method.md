# Refactoring Design Map: Scientific Method Plugin

## Overview

This design covers 5 targeted fixes to bring the `scientific-method` plugin to marketplace-ready
status. The fixes address one portability defect (cross-repo navigation links), one agent
frontmatter gap, and three documentation improvements. No structural reorganization is required.

## Source Assessment

- Plugin: `./plugins/scientific-method`
- Overall Score: 82/100
- Total Refactoring Targets: 5

---

## Structure Fixes

### Navigation Links Removal

**Source**: `./plugins/scientific-method/shared/investigation-workflow.md`
**Lines**: 389-393 (Navigation section at end of file)
**Issue**: Cross-repo relative paths (`../../../.claude/knowledge/...`) that break for marketplace users
**Severity**: Important

**Transformation**:

Remove the entire `## Navigation` section (lines 389-393). This section contains 3 links to files
outside the plugin boundary:

```text
- ../../../.claude/knowledge/workflow-diagrams/simple-task-workflow.md  (BREAKS on marketplace)
- ../../../.claude/knowledge/workflow-diagrams/rag-retrieval-pattern.md (BREAKS on marketplace)
- ../../../.claude/knowledge/workflow-diagrams/README.md                (BREAKS on marketplace)
```

The section to remove is:

```markdown
## Navigation

- **Previous:** [Simple Task Workflow](../../../.claude/knowledge/workflow-diagrams/simple-task-workflow.md)
- **Next:** [RAG Retrieval Pattern](../../../.claude/knowledge/workflow-diagrams/rag-retrieval-pattern.md)
- **Back to:** [Index](../../../.claude/knowledge/workflow-diagrams/README.md)
```

The preceding `---` separator on line 388 should also be removed since it no longer separates
anything meaningful at end-of-file.

**Verification**: After fix, no links in `investigation-workflow.md` should traverse outside
`plugins/scientific-method/`. Run `InternalLinkValidator` via plugin_validator to confirm.

---

## Agent Optimizations

### retrospective-analyst Tools Field

**Source**: `./plugins/scientific-method/agents/retrospective-analyst.md`
**Issue**: Missing `tools` field in frontmatter — agent writes 3 files but declares no tool constraints
**Severity**: Low

**Current frontmatter**:

```yaml
---
name: retrospective-analyst
description: Spawned after an investigation reaches resolved-verified status — analyzes the iteration log to produce a mermaid investigation timeline, result analysis (what worked, what did not, pattern observations), and a retrospective with lessons learned and rubric update recommendations. Use when an investigation is complete and the user wants structured analysis and visualization.
---
```

**Transformation**:

Add `tools: [Read, Write]` after the `description` field:

```yaml
---
name: retrospective-analyst
description: Spawned after an investigation reaches resolved-verified status — analyzes the iteration log to produce a mermaid investigation timeline, result analysis (what worked, what did not, pattern observations), and a retrospective with lessons learned and rubric update recommendations. Use when an investigation is complete and the user wants structured analysis and visualization.
tools: [Read, Write]
---
```

The agent reads investigation inputs and writes 3 output files to `.claude/retrospectives/`. Read
and Write are the exact tools required — nothing more.

**Verification**: Frontmatter contains `tools:` field after fix. Plugin validator FrontmatterValidator
passes.

---

## Documentation Improvements

### README Version Sync

**Source**: `./plugins/scientific-method/README.md`
**Issue**: README shows `Version 1.1.0` but `plugin.json` declares `1.2.0`
**Severity**: Low

**Transformation**:

Update the version reference in `README.md` from `1.1.0` to `1.2.0`. The canonical version
source is `plugin.json` — `1.2.0` is the correct value.

**Verification**: README.md version string matches `plugin.json` version field (`1.2.0`).

---

### experiment-protocol Downstream Integration Note

**Source**: `./plugins/scientific-method/skills/experiment-protocol/SKILL.md`
**Issue**: Skill produces an iteration log consumed by `retrospective-analyst` but makes no
mention of this downstream connection
**Severity**: Low

**Transformation**:

Add a `## Downstream Integration` section near the end of SKILL.md (before any closing section,
after the main workflow steps). Content:

```markdown
## Downstream Integration

The iteration log produced by this skill is the primary input to the `retrospective-analyst`
agent. When an investigation reaches `status: resolved-verified`, the `SubagentStop` hook
notifies the user to invoke `retrospective-analyst`. That agent reads:

- The complete investigation output (all 14 sections of the Unified Investigation Template)
- The iteration log written during experiment-protocol sessions

This produces three structured artefacts in `.claude/retrospectives/`: an investigation timeline,
a result analysis, and a retrospective with lessons learned.
```

**Verification**: SKILL.md contains a reference to `retrospective-analyst` and describes the
iteration log handoff.

---

### experiment-protocol Non-Standard Markup

**Source**: `./plugins/scientific-method/skills/experiment-protocol/SKILL.md`
**Lines**: 87-113, 128-147 (two `<eg>...</eg>` blocks)
**Issue**: Non-standard XML tags not recognized by Claude Code or markdown renderers
**Severity**: Low

**Transformation**:

Replace each `<eg>` / `</eg>` wrapper pair with standard markdown subsection headings. The
content inside the tags is unchanged — only the wrapper tags are replaced.

Block 1 (lines 87-113) — replace `<eg>` and `</eg>` tags:

```text
BEFORE:
<eg>

**Correct fixture — neutral input only:**
...content...
**Wrong fixture — criteria embedded:**
...content...

</eg>

AFTER (remove the <eg> and </eg> tags, leaving content and blank lines intact):

**Correct fixture — neutral input only:**
...content...
**Wrong fixture — criteria embedded:**
...content...
```

Block 2 (lines 128-147) — same pattern, remove `<eg>` opening and `</eg>` closing tags, leave
all content intact.

The `**Correct fixture**` / `**Wrong fixture**` and `**Example:**` bold headings already provide
sufficient semantic structure — no replacement heading is needed. The tags are pure wrappers with
no retained value.

**Verification**: No `<eg>` or `</eg>` tags remain in SKILL.md. Content of both example blocks
is unchanged. File passes markdown linting (`uv run prek run --files` on the file).

---

## Dependency Map

```text
Fix 1 — navigation links removal (investigation-workflow.md)        — independent
Fix 2 — agent tools field (retrospective-analyst.md)                — independent
Fix 3 — README version sync (README.md)                             — independent
Fix 4 — downstream integration note (experiment-protocol/SKILL.md)  — same file as Fix 5
Fix 5 — non-standard markup cleanup (experiment-protocol/SKILL.md)  — same file as Fix 4

Fix 4 and Fix 5 touch the same file. Combine into a single edit pass to avoid
conflicting edits and reduce round trips.
```

---

## Parallelization Opportunities

- **Group A** (fully parallel): Fix 1, Fix 2, Fix 3 — all different files, zero shared state
- **Group B** (single pass): Fix 4 + Fix 5 — same file (`experiment-protocol/SKILL.md`),
  combine into one edit session

Recommended execution order:

1. Launch Group A fixes in parallel (3 independent file edits)
2. After Group A completes, run Group B as a single combined edit pass on `experiment-protocol/SKILL.md`
3. Run `uv run prek run --files` on all modified files after both groups complete
4. Run plugin validator on `plugins/scientific-method` to confirm InternalLinkValidator passes
