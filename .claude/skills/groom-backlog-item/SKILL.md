---
description: Groom backlog items by discovering related research, skills, plugins, and prior work. Accepts item title substring, priority section, or "all" to groom multiple items in parallel. Produces context manifests to prepare for working on items.
argument-hint: <item-title-or-section-or-all>
user-invocable: true
---

# Groom Backlog Item

Prepare backlog items for work by discovering related context.

## Arguments

`$ARGUMENTS` can be:

- **Item title substring**: e.g., "Error Recovery" - grooms matching item
- **Section**: e.g., "P1" or "P2" or "Ideas" - grooms all items in section
- **"all"**: grooms all items (uses parallel agents)

## Workflow

### Step 1: Parse Arguments and Load Backlog

Read `.claude/BACKLOG.md` and identify target items.

**If title substring**: Find items whose title contains the substring (case-insensitive)
**If section**: Collect all items under that priority section
**If "all"**: Collect all items from P0, P1, P2, Ideas

### Step 2: Extract Item Details

For each target item, extract:

- Title
- Description
- Research first questions (if present)
- Source
- Suggested location

### Step 3: RT-ICA Assessment

Before grooming, run an RT-ICA (Reverse Thinking - Information Completeness Assessment) on each item.

For each item, reverse-think from the goal to identify:

- **Goal statement**: What completing this item achieves
- **Conditions**: Prerequisites that must be true (functional requirements, integration points, environment needs, data requirements, dependencies)
- **Availability**: For each condition — AVAILABLE (in backlog description), DERIVABLE (inferable from codebase context), or MISSING

Produce a compact RT-ICA summary per item:

```text
RT-ICA: {item title}
Goal: {one sentence}
Conditions:
1. {condition} | Status: {AVAILABLE|DERIVABLE|MISSING} | Info needed: {what}
...
Decision: {APPROVED|BLOCKED}
Missing: {list of missing inputs, if any}
```

This RT-ICA summary becomes input to the groomer agent, directing its discovery search toward filling MISSING and validating DERIVABLE conditions.

### Step 4: Spawn Groomer Agents

**For single item**: Run `@backlog-item-groomer` inline, passing the RT-ICA summary alongside item details.

**For multiple items**: Spawn parallel agents using Task tool:

```text
Task(
  subagent_type: "general-purpose",
  prompt: "Act as @backlog-item-groomer. Groom this item: {item details}\n\nRT-ICA Assessment:\n{rt-ica summary}",
  model: "haiku"
)
```

Spawn up to 5 agents in parallel. If more than 5 items, batch in waves.

### Step 5: Collect Results

Gather context manifests from all agents.

### Step 6: Produce Summary Report

Create a grooming report:

```markdown
# Backlog Grooming Report

**Date**: {YYYY-MM-DD}
**Items groomed**: {count}
**Arguments**: {original arguments}

## Summary

| Item | RT-ICA | Research Found | Skills | Agents | Blockers |
|------|--------|----------------|--------|--------|----------|
| {title} | {APPROVED/BLOCKED} | {count} | {count} | {count} | {count} |

## Individual Manifests

### {Item 1 title}
{manifest from agent}

### {Item 2 title}
{manifest from agent}

...

## RT-ICA Results

### BLOCKED Items (missing information)
- {item title}: {list of missing inputs}

### APPROVED Items (ready to plan)
- {item title}: {count} conditions verified, {count} assumptions to confirm

## Cross-Item Findings

### Shared Dependencies
- {items that multiple backlog items depend on}

### Suggested Groupings
- {items that could be worked together}

### Research Gaps
- {topics needing research-and-compare runs — skill moved to [stateless-agent-methodology](https://github.com/bitflight-devops/stateless-agent-methodology) repo}
```

### Step 7: Save Report (Optional)

If grooming multiple items, offer to save report to:

```text
.claude/grooming-reports/grooming-{YYYY-MM-DD}.md
```

## Example Usage

```text
# Groom a specific item
/groom-backlog-item Error Recovery

# Groom all P1 items
/groom-backlog-item P1

# Groom everything
/groom-backlog-item all
```

## Success Criteria

- [ ] Target items identified from arguments
- [ ] RT-ICA assessment completed for each item
- [ ] Groomer agent(s) spawned with RT-ICA context
- [ ] Context manifests collected
- [ ] RT-ICA results section included in report
- [ ] Summary report produced
- [ ] Cross-item findings identified (if multiple items)
