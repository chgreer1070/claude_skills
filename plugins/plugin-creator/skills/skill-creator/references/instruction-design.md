# Instruction Design — Degrees of Freedom

## Table of Contents

- [Overview](#overview)
- [Degrees of Freedom Taxonomy](#degrees-of-freedom-taxonomy)
  - [High Freedom](#high-freedom--text-based-instructions)
  - [Medium Freedom](#medium-freedom--pseudocode-or-scripts-with-parameters)
  - [Low Freedom](#low-freedom--specific-scripts-few-or-no-parameters)
- [The Bridge Analogy](#the-bridge-analogy)
- [Calibrating Instructions to Freedom Level](#calibrating-instructions-to-freedom-level)
- [Examples by Freedom Level](#examples-by-freedom-level)

SOURCE: Anthropic skill-authoring best practices (docs.anthropic.com, accessed 2026-03-23)

---

## Overview

Match the level of specificity in your instructions to the task's fragility and variability.
Over-constraining a creative task removes useful judgment. Under-constraining a fragile task
invites inconsistency and errors.

---

## Degrees of Freedom Taxonomy

### High Freedom — text-based instructions

**When to use:**

- Multiple approaches are valid
- Decisions depend on context the skill cannot anticipate
- Heuristics guide the approach rather than a single correct answer

**How to write:** State goals and constraints. Let Claude determine the method.

### Medium Freedom — pseudocode or scripts with parameters

**When to use:**

- A preferred pattern exists but some variation is acceptable
- Configuration or context affects behavior
- The structure is fixed but the content is not

**How to write:** Provide the pattern with explicit parameters. Mark which parts are fixed and
which are configurable.

### Low Freedom — specific scripts, few or no parameters

**When to use:**

- Operations are fragile or error-prone
- Consistency is critical — deviation causes failures
- A specific sequence must be followed exactly

**How to write:** Provide exact commands or procedures. State explicitly that deviation is not
permitted.

---

## The Bridge Analogy

Think of Claude as a robot navigating terrain:

- **Narrow bridge with cliffs on both sides:** Only one safe path exists. Provide exact
  instructions, guardrails, and no room for interpretation. Example: database migrations that
  must run in a specific sequence with no flag variation.

- **Open field with no hazards:** Many routes lead to success. Give a general direction and
  trust Claude to find the best path. Example: code reviews where context and codebase
  conventions determine the right feedback.

The bridge requires low freedom. The field calls for high freedom. Applying bridge-level
constraints to a field task removes Claude's ability to adapt; applying field-level latitude
to a bridge task creates dangerous ambiguity.

---

## Calibrating Instructions to Freedom Level

| Freedom Level | Instruction Content | What to Omit |
|---|---|---|
| High | Goals, constraints, quality criteria | Step-by-step procedures, exact commands |
| Medium | Template or pattern, configurable parameters, which parts are fixed | Exact output, requirement to match exactly |
| Low | Exact commands or procedures, explicit "do not modify" statements | Any optional variation |

---

## Examples by Freedom Level

### High Freedom — code review

```markdown
## Code review process

1. Analyze the code structure and organization
2. Check for potential bugs or edge cases
3. Suggest improvements for readability and maintainability
4. Verify adherence to project conventions
```

The reviewer decides which issues to highlight, how deep to go, and what order to address
them — appropriate because the right review depends on context the skill cannot know in advance.

### Medium Freedom — generate report

````markdown
## Generate report

Use this template and customize as needed:

```python
def generate_report(data, format="markdown", include_charts=True):
    # Process data
    # Generate output in specified format
    # Optionally include visualizations
```
````

The structure is fixed (function signature, parameters) but content and output vary by input.
Claude adapts the implementation to the data while following the established pattern.

### Low Freedom — database migration

````markdown
## Database migration

Run exactly this script:

```bash
python scripts/migrate.py --verify --backup
```

Do not modify the command or add additional flags.
````

Migration commands are fragile — extra flags or altered sequences can corrupt data. No
variation is acceptable; the instruction removes all discretion intentionally.
