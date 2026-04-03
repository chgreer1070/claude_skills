# Workflow Patterns

Use these patterns when skills need to guide Claude through multi-step processes.

**NOTE:** Workflows can use string substitutions (`$ARGUMENTS`, `$N`) for parameterized steps and dynamic context injection (\`\!\`command\`\`) to fetch live data during workflow execution. See main SKILL.md for details.

**SOURCE:** Based on Anthropic skill-creator examples (commit 69c0b1a) and [Skill authoring best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices) (accessed 2026-02-25).

---

## Contents

- [Template Pattern](#template-pattern)
- [Sequential Workflows](#sequential-workflows)
- [Checklist-Based Workflows](#checklist-based-workflows)
- [Conditional Workflows](#conditional-workflows)
- [Feedback Loops](#feedback-loops)
- [Examples Pattern](#examples-pattern)
- [Plan-Validate-Execute Pattern](#plan-validate-execute-pattern)

---

## Template Pattern

Provide templates for output format. Match the level of strictness to what Claude needs to produce.

**Strict template** — use when output must conform exactly (API responses, fixed data formats):

````markdown
## Report structure

ALWAYS use this exact template structure:

```markdown
# [Analysis Title]

## Executive summary
[One-paragraph overview of key findings]

## Key findings
- Finding 1 with supporting data
- Finding 2 with supporting data

## Recommendations
1. Specific actionable recommendation
2. Specific actionable recommendation
```
````

**Flexible template** — use when adaptation is useful (analytical output, variable context):

````markdown
## Report structure

Here is a sensible default format, but use your best judgment based on the analysis:

```markdown
# [Analysis Title]

## Executive summary
[Overview]

## Key findings
[Adapt sections based on what you discover]

## Recommendations
[Tailor to the specific context]
```

Adjust sections as needed for the specific analysis type.
````

The distinction matters: strict templates enforce structure; flexible templates calibrate style while allowing Claude to adapt when the situation warrants.

SOURCE: Anthropic skill-authoring best practices (docs.anthropic.com, accessed 2026-03-23)

---

## Sequential Workflows

For complex tasks, break operations into clear, sequential steps. It is often helpful to give Claude an overview of the process towards the beginning of SKILL.md:

```markdown
Filling a PDF form involves these steps:

1. Analyze the form (run analyze_form.py)
2. Create field mapping (edit fields.json)
3. Validate mapping (run validate_fields.py)
4. Fill the form (run fill_form.py)
5. Verify output (run verify_output.py)
```

## Checklist-Based Workflows

For multi-step workflows, provide a checklist the agent can copy and track. This works for both code-heavy and analysis-only workflows.

**Example 1: Analysis workflow (no code):**

````markdown
## Research synthesis workflow

Copy this checklist and track your progress:

```
Research Progress:
- [ ] Step 1: Read all source documents
- [ ] Step 2: Identify key themes
- [ ] Step 3: Cross-reference claims
- [ ] Step 4: Create structured summary
- [ ] Step 5: Verify citations
```

**Step 1: Read all source documents**
Review each document in the `sources/` directory...
````

**Example 2: Script-based workflow:**

````markdown
## PDF form filling workflow

Copy this checklist and check off items as you complete them:

```
Task Progress:
- [ ] Step 1: Analyze the form (run analyze_form.py)
- [ ] Step 2: Create field mapping (edit fields.json)
- [ ] Step 3: Validate mapping (run validate_fields.py)
- [ ] Step 4: Fill the form (run fill_form.py)
- [ ] Step 5: Verify output (run verify_output.py)
```
````

Checklists help both the agent and user track progress. Clear steps prevent skipping critical validation.

> **Tip:** If workflows become large or complicated with many steps, push them into separate files and tell Claude to read the appropriate file based on the task.

## Conditional Workflows

For tasks with branching logic, guide Claude through decision points:

```markdown
1. Determine the modification type:
   **Creating new content?** → Follow "Creation workflow" below
   **Editing existing content?** → Follow "Editing workflow" below

2. Creation workflow: [steps]
3. Editing workflow: [steps]
```

## Feedback Loops

Use run-validate-fix loops to catch errors early. The validator can be a script or a document — the loop pattern works equally well with both.

**Example 1: Style-guide compliance** (document-based validator, no code):

```markdown
## Content review process

1. Draft your content following the guidelines in STYLE_GUIDE.md
2. Review against the checklist:
   - Check terminology consistency
   - Verify examples follow the standard format
   - Confirm all required sections are present
3. If issues found:
   - Note each issue with specific section reference
   - Revise the content
   - Review the checklist again
4. Only proceed when all requirements are met
5. Finalize and save the document
```

The "validator" here is STYLE_GUIDE.md — Claude performs the check by reading and comparing. No scripts needed.

**Example 2: Document editing with validation script** (script-based validator):

```markdown
## Document editing process

1. Make your edits to `word/document.xml`
2. **Validate immediately**: `python ooxml/scripts/validate.py unpacked_dir/`
3. If validation fails:
   - Review the error message carefully
   - Fix the issues in the XML
   - Run validation again
4. **Only proceed when validation passes**
5. Rebuild: `python ooxml/scripts/pack.py unpacked_dir/ output.docx`
6. Test the output document
```

The validation loop catches errors early, before they propagate into the final output.

SOURCE: Anthropic skill-authoring best practices (docs.anthropic.com, accessed 2026-03-23)

---

## Examples Pattern

For skills where output quality depends on style and format, provide input/output pairs. This is the same technique as few-shot prompting — examples teach by demonstration rather than explicit rules.

````markdown
## Commit message format

Generate commit messages following these examples:

**Example 1:**
Input: Added user authentication with JWT tokens
Output:

```text
feat(auth): implement JWT-based authentication

Add login endpoint and token validation middleware
```

**Example 2:**
Input: Fixed bug where dates displayed incorrectly in reports
Output:

```text
fix(reports): correct date formatting in timezone conversion

Use UTC timestamps consistently across report generation
```

**Example 3:**
Input: Updated dependencies and refactored error handling
Output:

```text
chore: update dependencies and refactor error handling

- Upgrade lodash to 4.17.21
- Standardize error response format across endpoints
```

Follow this style: type(scope): brief description, then detailed explanation.
````

Examples help Claude understand the desired style and level of detail more clearly than descriptions alone. Use this pattern when you find yourself writing rules like "keep it concise" or "be specific" — an example shows what those rules mean in practice.

SOURCE: Anthropic skill-authoring best practices (docs.anthropic.com, accessed 2026-03-23)

---

## Plan-Validate-Execute Pattern

For batch operations, destructive changes, or high-stakes tasks, have Claude produce a plan in a structured format, validate that plan with a script, then execute.

**Why this pattern works:**
- Catches errors before changes are applied — non-existent fields, conflicting values, missed required fields
- Machine-verifiable: scripts provide objective verification
- Reversible planning: Claude iterates on the plan without touching originals
- Clear debugging: error messages point to specific problems

**Workflow shape:**

```text
analyze → create plan file → validate plan → execute → verify
```

The intermediate plan file is the key addition. Instead of executing directly from Claude's analysis, the plan is written to a structured file (e.g., `changes.json`) and validated before any changes are applied.

**When to use:** Batch operations, destructive changes, complex validation rules, high-stakes operations.

**Implementation tip:** Make validation scripts verbose with specific error messages:

```text
Field 'signature_date' not found. Available fields: customer_name, order_total, signature_date_signed
```

Specific error messages give Claude enough information to fix the plan without additional investigation.

SOURCE: Anthropic skill-authoring best practices (docs.anthropic.com, accessed 2026-03-23)
