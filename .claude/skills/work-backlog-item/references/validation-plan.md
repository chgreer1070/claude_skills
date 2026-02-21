# Validation Plan — GitHub Integration Workflow

Each step of the GitHub integration can be independently verified using `gh` CLI commands.

## V1: Label Setup Verification

```bash
# After /work-backlog-item setup-github:
gh label list -R Jamie-BitFlight/claude_skills --json name,color \
  --jq '.[] | select(.name | startswith("priority:","type:","status:")) | .name'

# Expected: 13 taxonomy labels present
```

## V2: Issue Creation Verification

```bash
# After working a P1 item:
gh issue list -R Jamie-BitFlight/claude_skills --state open \
  --json number,title,labels \
  --jq '.[] | {number,title,labels: [.labels[].name]}'

# Expected: issue with priority:p1, type:*, status:in-progress labels
```

```bash
# Verify **Issue**: #N written to BACKLOG.md:
grep -n "Issue" .claude/BACKLOG.md | head -10
```

## V3: Milestone Assignment Verification

```bash
gh api repos/Jamie-BitFlight/claude_skills/milestones \
  --jq '.[] | {number, title, open_issues}'

# Expected: milestone exists with open_issues incremented after item worked
```

## V4: In-Progress Label Verification

```bash
gh issue view <issue-number> -R Jamie-BitFlight/claude_skills \
  --json labels --jq '.labels[].name'

# Expected: status:in-progress present, status:needs-grooming absent
```

## V5: Closure Verification

```bash
# After /work-backlog-item close <title>:
gh issue view <issue-number> -R Jamie-BitFlight/claude_skills \
  --json state,comments --jq '{state, last_comment: .comments[-1].body}'

# Expected: state="closed", comment contains checklist summary
```

## V6: BACKLOG.md Consistency Check

```bash
grep -A 5 "### {item title}" .claude/BACKLOG.md
# Expected: Issue, Plan, Status fields all present and consistent
```

## Full Integration Test Sequence

```text
1. /work-backlog-item setup-github          → V1: 13 labels, 1 milestone, 1 project
2. /work-backlog-item clang-format yaml     → V2, V3, V4: issue created with labels
3. [implement the fix in code]
4. /work-backlog-item close clang-format    → V5, V6: issue closed, BACKLOG.md DONE
```

## PyGithub Validation (scripted)

```bash
uv run .claude/skills/gh/scripts/github_project_setup.py issue list --priority p1
# Expected: lists all open P1 issues with labels and milestone
```
