---
description: 'Optimize CLAUDE.md, SKILL.md, agent definitions, and other AI-facing files for Claude comprehension and economy. Measures baseline metrics, delegates to @contextual-ai-documentation-optimizer agent with file-type-specific context, runs independent verification via second agent, measures post-optimization metrics, and presents comprehensive before/after report. Supports iterative mode for large targets. Use when improving prompt effectiveness, reducing token waste, rewriting instructions for LLM consumption, or enhancing files with latest Claude Code features. Invoke with /optimize-claude-md <file-or-directory>.'
argument-hint: '<file-or-directory-path>'
user-invocable: true
disable-model-invocation: true
---

# Optimize AI-Facing Files

Orchestrate multi-phase optimization of AI-facing documentation with measurement, delegation, verification, and comprehensive reporting.

## Invocation

```text
/optimize-claude-md <path>
```

Where `<path>` is one of:

- A single file (e.g., `./CLAUDE.md`, `.claude/skills/my-skill/SKILL.md`, `.claude/agents/my-agent.md`)
- A skill directory (e.g., `.claude/skills/my-skill/`) — optimizes SKILL.md and all reference files
- A plugin directory (e.g., `plugins/my-plugin/`) — optimizes CLAUDE.md, all skills, and all agents

## Process

### Phase 1: Validate Target

Read the file or directory at `$ARGUMENTS`. Verify existence. Determine scope (single file, skill directory, or plugin directory).

### Phase 2: Measure Baseline

**For all files**:

- Determine file type (CLAUDE.md, SKILL.md, agent definition, reference file)
- Measure token count: `uv run plugins/plugin-creator/scripts/plugin_validator.py --check <file>`
- Record baseline token count

**For SKILL.md files only**:

- Run completeness score evaluation (8-category assessment from /plugin-creator:audit-skill-completeness)
- Record baseline completeness score (format: X/24)

**Record metrics** for reporting.

### Phase 3: Delegate to @contextual-ai-documentation-optimizer

Spawn the optimization agent via Task tool with enhanced delegation template (see below). Pass file-type-specific context, baseline metrics, and constraints.

<delegation_template>

```text
TARGET: {resolved path(s)}
FILE TYPE: {CLAUDE.md | SKILL.md | agent definition | reference file}
BASELINE TOKEN COUNT: {N tokens}
BASELINE COMPLETENESS SCORE: {X/24} (SKILL.md only)

TASK:
1. Run RT-ICA pre-check — verify file type, intent, audience, constraints
2. Enable the prompt-optimization-claude-45 skill
3. Read the complete target file(s)
4. Analyze against the 8 optimization principles:
   - Positive framing (replace prohibitions with directives)
   - Motivation (explain why rules exist)
   - Concrete examples (show correct and incorrect patterns)
   - Front-loaded priorities (critical info first)
   - Concise language (economy without ambiguity)
   - Explicit format control (structure instructions clearly)
   - Strategic XML tagging (semantic boundaries for complex prompts)
   - Structural enforcement (decision flows, tables, checklists for determinism)
5. Apply transformations — preserve original intent, improve execution economy
6. Run CoVe post-check — generate falsifiable verification questions, answer independently
7. Report token impact for each transformation
8. Signal completion status: DONE or BLOCKED

CONSTRAINTS:
- Preserve all original intent and functional behavior
- Maintain file structure conventions (frontmatter format, heading hierarchy)
- Apply compression only where it improves clarity — brevity is not the sole goal
- Verify technical terms are exact (tool names, file paths, command syntax)
- Report token impact for each transformation
- For SKILL.md: evaluate against 8 completeness categories, keep description <1024 chars, no YAML multiline indicators
- For agent files: preserve required frontmatter fields (name, description)
- For CLAUDE.md: front-load critical instructions, use decision flow diagrams for complex logic
- Signal DONE when optimization complete, BLOCKED when missing required inputs

OUTPUT STRUCTURE:
- RT-ICA Pre-Check Results
- Analysis of Optimization Opportunities
- Optimized Content (complete file)
- Changes Applied with Principle Citations
- Token Impact Per Transformation
- CoVe Verification Results
- Status: DONE or BLOCKED (with blocking reason if BLOCKED)
```

</delegation_template>

### Phase 4: Handle Agent Response

**If agent signals BLOCKED**:

- Present the blocking reason to the user
- Ask for resolution (missing inputs, clarifications, or constraints)
- Wait for user input
- Re-delegate with additional context once blocker is resolved

**If agent signals DONE**:

- Proceed to Phase 5 (Independent Verification)

### Phase 5: Independent Verification

Spawn a SECOND agent (general-purpose, NOT the same agent that optimized) to verify optimization quality.

**Verification Template**:

```text
ORIGINAL FILE: {path to original}
OPTIMIZED FILE: {path to optimized version}

TASK:
Compare the original and optimized files. Verify:

1. Original intent preserved — no functional behaviors lost
2. Technical terms exact — tool names, file paths, command syntax unchanged
3. Structural conventions maintained — frontmatter format, heading hierarchy intact
4. No regressions introduced — edge cases still handled, constraints still enforced

CONSTRAINTS:
- You have NO context from the optimization process
- Base verification ONLY on comparing the two files
- Report any regressions, ambiguities, or losses of specificity
- Signal PASS if optimization preserves all original intent
- Signal REGRESSION if any functional behavior was lost or technical terms changed incorrectly

OUTPUT:
- Verification Status: PASS or REGRESSION
- Regressions Found (if any) with line number references
- Preserved Behaviors (summary)
```

**Handle verification result**:

- If PASS: proceed to Phase 6
- If REGRESSION: present regression details to user, offer to revise or keep original

### Phase 6: Measure Output

**For all files**:

- Measure post-optimization token count using same tool
- Calculate delta: `(post - baseline) / baseline * 100`

**For SKILL.md files only**:

- Run post-optimization completeness score
- Calculate delta: `post - baseline` (absolute change)

**Record metrics** for reporting.

### Phase 7: Present Comprehensive Report

Report to user with structure:

```text
## Optimization Report: {filename}

### Baseline Metrics
- Token Count: {N tokens}
- Completeness Score: {X/24} (SKILL.md only)

### Post-Optimization Metrics
- Token Count: {M tokens} ({+/-Y%})
- Completeness Score: {Z/24} (delta: {+/-D}) (SKILL.md only)

### Changes Applied
{List of transformations with principle citations from agent report}

### CoVe Verification Results
{Agent's falsifiable verification questions and answers}

### Independent Verification
- Status: {PASS | REGRESSION}
- {Regression details if any}

### Structural Upgrade Candidates
{Sections that could benefit from decision flows, tables, checklists}

### Before/After Diff
{Diff output showing exact changes}

### Recommendation
{Proceed with optimization | Revise based on regressions | Keep original}
```

### Phase 8: Apply on Approval

Write optimized content ONLY after user confirms. Do not auto-apply.

## Iterative Mode for Large Targets

For files >300 lines or plugin directories, offer iterative optimization:

**Pass 1: Structural Changes**

- Reorganize sections for front-loaded priorities
- Split large sections to references/ subdirectory
- Add decision flow diagrams, tables, checklists
- Measure token count after structural changes

**Pass 2: Content Optimization**

- Apply positive framing (replace prohibitions with directives)
- Add motivations and concrete examples
- Compress verbose explanations without losing clarity
- Measure token count after content changes

**Pass 3: Polish**

- Optimize frontmatter (description compression, argument hints)
- Verify cross-references between files
- Ensure format consistency (code fence language specifiers, markdown links)
- Final measurement

**Convergence**: Terminate when completeness score stops improving between passes (delta <1 point) or token reduction plateaus (delta <2%).

## Scope Expansion Rules

When target is a **skill directory**:

1. Optimize SKILL.md (primary)
2. Optimize each file in `references/` (secondary)
3. Verify cross-references between SKILL.md and reference files remain valid

When target is a **plugin directory**:

1. Optimize CLAUDE.md if present (primary)
2. List all skills and agents — ask user which to include
3. Apply iterative mode: one pass per selected component
4. Verify plugin.json references remain consistent

## Edge Cases

- **File not found**: Report exact path checked, ask user to confirm
- **Binary or non-markdown file**: Skip with explanation
- **Already optimal**: Acknowledge effectiveness, suggest only minor refinements per agent constraint
- **Large file (>300 lines)**: Offer iterative mode with multi-pass optimization
- **Agent returns BLOCKED**: Present blocking reason to user with specific questions
- **Independent verification finds regression**: Report regression, offer to revise or keep original
- **Token count increases**: Report reason (added examples, motivations, or structure), verify completeness score improved to justify expansion
- **Completeness score decreases**: Signal regression, recommend keeping original or revising optimization strategy
