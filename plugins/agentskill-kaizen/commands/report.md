---
name: report
description: Generate summary report from existing analysis in .planning/kaizen/
argument-hint: '[--latest] [--all]'
allowed-tools: Read,Write,Glob,Grep
---

Generate a summary report from existing kaizen analysis files. Does not run new analysis — reads previously generated findings.

## Arguments

- `--latest` — Summarize only the most recent analysis file. Default behavior when no flag provided.
- `--all` — Aggregate findings across all analysis files in `.planning/kaizen/`.

## Execution Steps

1. **Find analysis files.** Glob for `.planning/kaizen/analysis-*.md` and `.planning/kaizen/exploration-*.md`.

2. **Select scope.** With `--latest`, use the most recent file by date. With `--all`, read all files.

3. **Extract findings.** From each analysis file, extract:
   - Anti-patterns with frequency counts
   - Severity distribution (critical / warning / info)
   - Affected sessions
   - Recommended improvement types

4. **Generate summary report.** Write to `.planning/kaizen/report-{YYYY-MM-DD}.md` with:
   - Executive summary — top 5 findings by frequency × impact
   - Trend analysis (if `--all`) — are patterns improving or worsening over time?
   - Improvement backlog — prioritized list of proposed changes
   - Metrics — total sessions analyzed, total findings, breakdown by dimension

5. **Display key findings.** Show the executive summary to the user inline.

## Output

Report written to `.planning/kaizen/report-{YYYY-MM-DD}.md`.
