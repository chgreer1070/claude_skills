# Workflow Patterns

Use these patterns when skills need to guide Claude through multi-step processes.

**NOTE:** Workflows can use string substitutions (`$ARGUMENTS`, `$N`) for parameterized steps and dynamic context injection (\`\!\`command\`\`) to fetch live data during workflow execution. See main SKILL.md for details.

**SOURCE:** Based on Anthropic skill-creator examples (commit 69c0b1a) and [Skill authoring best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices) (accessed 2026-02-25).

---

## Contents

- [Sequential Workflows](#sequential-workflows)
- [Checklist-Based Workflows](#checklist-based-workflows)
- [Conditional Workflows](#conditional-workflows)
- [Feedback Loops](#feedback-loops)

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

Use run-validate-fix loops to catch errors early. This pattern greatly improves output quality.

**Non-code example (style guide compliance):**

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
```

**Code example (document editing):**

```markdown
## Document editing process

1. Make edits to `word/document.xml`
2. **Validate immediately**: `python scripts/validate.py unpacked_dir/`
3. If validation fails:
   - Review the error message
   - Fix the issues
   - Run validation again
4. **Only proceed when validation passes**
5. Rebuild: `python scripts/pack.py unpacked_dir/ output.docx`
```
