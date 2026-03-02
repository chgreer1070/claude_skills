---
tasks:
  - task: "Fix SKILL.md intro paragraph that contradicts the new conditional routing logic"
    status: pending
    parent_task: "plan/tasks-1-followup-routing.md"
---

# Task: Fix SKILL.md Intro Paragraph Contradiction

## Parent Task

- Original: `plan/tasks-1-followup-routing.md`
- Review Date: 2026-03-02

## Status

- [ ] Pending

## Priority

High

## Description

The intro paragraph of `.claude/skills/complete-implementation/SKILL.md` (line 13) still says:

```text
You MUST validate that the implemented feature meets its goals and quality gates. This workflow
is recursive: if follow-up task files are created, re-run `implement-feature` on them and then
re-run this skill.
```

This sentence directly contradicts the routing logic added in the `## Recursive Follow-up Handling`
section (lines 75-168). The routing section correctly states that recursion is conditional (same
slug AND High priority), but the intro paragraph tells the orchestrator that recursion is
unconditional.

An orchestrator reads the skill document top-to-bottom. Encountering the unconditional recursion
statement at line 13 before reaching the conditional routing section at line 75 can cause the
orchestrator to apply the old (broken) behavior from Issue #381. The intro paragraph was not
updated as part of T1 because T1's constraint was "Replace ONLY the `## Recursive Follow-up
Handling` section (lines 75-83)". However, the intro paragraph now produces contradictory
instructions that defeat the purpose of the routing fix.

The fix is a single-sentence correction: replace "This workflow is recursive: if follow-up task
files are created, re-run `implement-feature` on them and then re-run this skill." with wording
that accurately describes the conditional routing behavior.

## Acceptance Criteria

- [ ] Line 13 of `.claude/skills/complete-implementation/SKILL.md` no longer says the workflow
      is unconditionally recursive
- [ ] The replacement sentence accurately describes that follow-up files are routed to backlog
      first, and recursion only proceeds when the slug matches AND priority is High
- [ ] All other content on line 13 and surrounding lines is unchanged
- [ ] `uv run prek run --files .claude/skills/complete-implementation/SKILL.md` exits code 0

## Files to Modify

- `.claude/skills/complete-implementation/SKILL.md:13` - Replace the sentence "This workflow is
  recursive: if follow-up task files are created, re-run `implement-feature` on them and then
  re-run this skill." with accurate wording describing conditional routing.

  Suggested replacement:

  ```text
  This workflow routes follow-up task files to the backlog before deciding on recursion: only
  follow-ups with the same feature slug AND High priority trigger immediate recursion; all others
  are deferred to the backlog.
  ```

## Verification Steps

1. Read `.claude/skills/complete-implementation/SKILL.md` lines 11-15 and confirm the intro
   no longer contains the word "recursive" in an unconditional context.
2. Run: `grep -n "This workflow is recursive" .claude/skills/complete-implementation/SKILL.md`
   Expected: zero matches.
3. Run: `grep -n "unconditional\|re-run.*them and then" .claude/skills/complete-implementation/SKILL.md`
   Expected: zero matches.
4. Run: `uv run prek run --files .claude/skills/complete-implementation/SKILL.md`
   Expected: exit code 0 with no errors.

## References

- Original review: code reviewer agent, 2026-03-02
- Related code: `.claude/skills/complete-implementation/SKILL.md`
- Parent task: `plan/tasks-1-followup-routing.md` (T1)
- Issue: #381
