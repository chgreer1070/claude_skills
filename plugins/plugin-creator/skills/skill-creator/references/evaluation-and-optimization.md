# Skill Evaluation and Optimization

Post-creation workflow for testing, improving, and optimizing skills using A/B evaluation, grading, and description tuning.

**SOURCE:** Adapted from the official Anthropic skill-creator ([anthropics/skills](https://github.com/anthropics/skills)) with additions for this repository's conventions. Accessed 2026-03-06.

## Table of Contents

- [Step 7: Test Cases](#step-7-test-cases)
- [Step 8: Running and Evaluating Test Cases](#step-8-running-and-evaluating-test-cases)
- [Step 9: Improving the Skill](#step-9-improving-the-skill)
- [Advanced: Blind Comparison](#advanced-blind-comparison)
- [Step 10: Description Optimization](#step-10-description-optimization)
- [Reference Files](#reference-files)

## Step 7: Test Cases

After writing the skill draft, come up with 2-3 realistic test prompts — the kind of thing a real user would actually say. Share them with the user: "Here are a few test cases I'd like to try. Do these look right, or do you want to add more?" Then run them.

Save test cases to `evals/evals.json`. Don't write assertions yet — just the prompts. You'll draft assertions in the next step while the runs are in progress.

```json
{
  "skill_name": "example-skill",
  "evals": [
    {
      "id": 1,
      "prompt": "User's task prompt",
      "expected_output": "Description of expected result",
      "files": []
    }
  ]
}
```

See [schemas.md](./schemas.md) for the full schema (including the `assertions` field, which you'll add later).

Skills with objectively verifiable outputs (file transforms, data extraction, code generation, fixed workflow steps) benefit from test cases. Skills with subjective outputs (writing style, art) often don't need them. Suggest the appropriate default based on the skill type, but let the user decide.

> Scripts in this section use `uv run` — if `uv` is not installed, read `.claude/rules/uv-run-fallback.md` for install instructions and pip fallback procedure.

## Step 8: Running and Evaluating Test Cases

This section is one continuous sequence — don't stop partway through.

Put results in `<skill-name>-workspace/` as a sibling to the skill directory. Within the workspace, organize results by iteration (`iteration-1/`, `iteration-2/`, etc.) and within that, each test case gets a directory (`eval-0/`, `eval-1/`, etc.). Don't create all of this upfront — just create directories as you go.

### Step 8a: Spawn all runs (with-skill AND baseline) in the same turn

For each test case, launch TWO parallel runs:

- **with-skill**: `claude -p "{prompt}" --allowedTools "..." --permission-mode acceptEdits`
- **without-skill (baseline)**: Same prompt, same tools, but WITHOUT the skill installed

Use `--output-format stream-json` and `--verbose` to capture full transcripts. Run all test cases in parallel using the Agent tool.

Save outputs:

```text
iteration-1/
  eval-0/
    with-skill/transcript.json
    without-skill/transcript.json
  eval-1/
    ...
```

### Step 8b: While runs are in progress, draft assertions

While waiting for runs to complete, write assertions for each test case. Good assertions test meaningful outcomes — they should be hard to satisfy without actually doing the work correctly.

Add assertions to `evals/evals.json`:

```json
{
  "assertions": [
    {
      "type": "file_exists",
      "path": "output/report.md"
    },
    {
      "type": "file_contains",
      "path": "output/report.md",
      "pattern": "Summary"
    },
    {
      "type": "custom",
      "description": "Report includes at least 3 sections with headers"
    }
  ]
}
```

### Step 8c: As runs complete, capture timing data

Record execution time and token usage for each run. Save to the eval directory as `metrics.json`.

### Step 8d: Grade, aggregate, and launch the viewer

1. For each completed eval, spawn the **grader agent** (read `agents/grader.md`):

   ```text
   Task is grading eval results with subagent_type="general-purpose"
   Context to include in the prompt: agents/grader.md, evals/evals.json (assertions),
     iteration-N/eval-M/with-skill/transcript.json, iteration-N/eval-M/without-skill/transcript.json
   Output: iteration-N/eval-M/grading.json
   ```

2. Aggregate all grading results using the benchmark script:

   ```bash
   uv run scripts/aggregate_benchmark.py iteration-1/
   ```

3. Generate the eval viewer for the user to review:

   ```bash
   uv run eval-viewer/generate_review.py --static iteration-1/eval-review.html iteration-1/
   ```

   Open the HTML file so the user can see real examples before you attempt any improvements.

**IMPORTANT:** Generate the eval viewer BEFORE evaluating results yourself. Get examples in front of the user as soon as possible.

### Step 8e: Read the feedback

Check for `feedback.json` from the viewer's "Submit All Reviews" button. The user may have flagged specific issues, approved results, or added notes. Incorporate this feedback into your improvement plan.

## Step 9: Improving the Skill

### How to think about improvements

The most common failure modes and what to do about them:

**Wrong approach taken.** The skill chose strategy A when strategy B was clearly better. Fix: add decision guidance for when to use which approach. Don't just add rules — add the reasoning, so the skill can generalize.

**Missing information.** The skill didn't know about a constraint, API, or pattern it needed. Fix: add the missing knowledge to a reference file and point to it from SKILL.md.

**Correct approach but poor execution.** The skill knew what to do but made errors in the details — wrong API call, missing edge case, formatting issues. Fix: add a script for the deterministic/error-prone parts, or add concrete examples showing the correct pattern.

**Did something unnecessary.** The skill did extra work that wasn't needed or actively harmful. Fix: add explicit guidance about what NOT to do and why.

**For each issue, consider:**

- Is this a knowledge gap (add reference)?
- Is this a reliability gap (add script)?
- Is this a judgment gap (add decision guidance)?
- Is this a scope gap (add boundaries)?

### The iteration loop

```mermaid
flowchart TD
    I1["Review eval results and user feedback"] --> I2
    I2["Identify failure modes and root causes"] --> I3
    I3["Make targeted changes to SKILL.md,<br>scripts, or references"] --> I4
    I4["Re-run test cases (Step 8)"] --> I5
    I5["Compare with previous iteration"] --> IQ{"Improvement<br>sufficient?"}
    IQ -->|"No — regressions or<br>new failures found"| I2
    IQ -->|"Yes — all tests pass<br>or user satisfied"| Done(["Skill is stable"])
```

## Advanced: Blind Comparison

For significant skill changes, use blind A/B comparison to avoid confirmation bias. Spawn the **comparator agent** (read `agents/comparator.md`) with outputs from both versions. The comparator doesn't know which version is "old" or "new" — it evaluates purely on quality.

Then spawn the **analyzer agent** (read `agents/analyzer.md`) to understand WHY the winner won, producing actionable improvement suggestions.

## Step 10: Description Optimization

The description field in SKILL.md frontmatter is the primary mechanism that determines whether Claude invokes a skill. After creating or improving a skill, offer to optimize the description for better triggering accuracy.

### How skill triggering works

Claude sees all skill descriptions in the `<available_skills>` block. When a user message comes in, Claude reads the descriptions and decides which (if any) skills to invoke. The description must contain enough signal for Claude to make the right call — invoke when relevant, skip when not.

A good description balances:

- **Precision**: Doesn't trigger on unrelated requests
- **Recall**: Triggers on all relevant requests
- **Specificity**: Distinguishes this skill from similar ones

### Step 10a: Generate trigger eval queries

Create an eval set with positive (should trigger) and negative (should NOT trigger) queries:

```json
[
  {"query": "Create a new skill for handling PDF files", "should_trigger": true},
  {"query": "How do I rotate a PDF?", "should_trigger": false},
  {"query": "Build a slash command for deployment", "should_trigger": true},
  {"query": "What's the weather today?", "should_trigger": false}
]
```

Aim for 15-20 queries minimum, roughly 60% positive and 40% negative. Include edge cases — queries that are close to the boundary.

### Step 10b: Review with user

Present the eval set to the user for review using the HTML template:

1. Read the template from `assets/eval_review.html`
2. Replace the placeholders:
   - `__EVAL_DATA_PLACEHOLDER__` with the JSON array of eval items
   - `__SKILL_NAME_PLACEHOLDER__` with the skill's name
   - `__SKILL_DESCRIPTION_PLACEHOLDER__` with the skill's current description
3. Write to a temp file and open it
4. The user can edit queries, toggle should-trigger, add/remove entries, then click "Export Eval Set"

This step matters — bad eval queries lead to bad descriptions.

### Step 10c: Run the optimization loop

Tell the user: "This will take some time — I'll run the optimization loop in the background and check on it periodically."

Save the eval set to the workspace, then run in the background:

```bash
uv run scripts/run_loop.py \
  --eval-set <path-to-trigger-eval.json> \
  --skill-path <path-to-skill> \
  --model <model-id-powering-this-session> \
  --max-iterations 5 \
  --verbose
```

Use the model ID from your system prompt (the one powering the current session) so the triggering test matches what the user actually experiences.

While it runs, periodically tail the output to give the user updates on which iteration it's on and what the scores look like.

This handles the full optimization loop automatically. It splits the eval set into 60% train and 40% held-out test, evaluates the current description (running each query 3 times to get a reliable trigger rate), then calls Claude with extended thinking to propose improvements based on what failed. It re-evaluates each new description on both train and test, iterating up to 5 times. When it's done, it opens an HTML report in the browser showing the results per iteration and returns JSON with `best_description` — selected by test score rather than train score to avoid overfitting.

### Step 10d: Apply the result

Review the `best_description` from the optimization output. Update the SKILL.md frontmatter with the optimized description. Run `quick_validate.py` to confirm it's valid.

## Reference Files

The `agents/` directory contains instructions for specialized subagents. Read them when you need to spawn the relevant subagent.

- [agents/grader.md](../agents/grader.md) — How to evaluate assertions against outputs
- [agents/comparator.md](../agents/comparator.md) — How to do blind A/B comparison between two outputs
- [agents/analyzer.md](../agents/analyzer.md) — How to analyze why one version beat another

The `references/` directory has additional documentation:

- [schemas.md](./schemas.md) — JSON structures for evals.json, grading.json, etc.
- [claude-code-skills-official.md](./claude-code-skills-official.md) — Official Claude Code skills specification
- [workflows.md](./workflows.md) — Workflow design patterns for multi-step skills

The `eval-viewer/` directory contains the interactive eval review viewer:

- `eval-viewer/viewer.html` — Interactive HTML viewer for eval results
- `eval-viewer/generate_review.py` — Generates standalone HTML review from eval data

The `assets/` directory contains templates:

- `assets/eval_review.html` — HTML template for reviewing and editing trigger eval sets
