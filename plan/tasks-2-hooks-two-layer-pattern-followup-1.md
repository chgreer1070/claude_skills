---
tasks:
  - task: "Fix version citation from v0.5.1 to v0.4.0 in two-layer pattern recipe"
    status: pending
    parent_task: "plan/tasks-1-hooks-two-layer-pattern.md"
---

# Task: Fix version citation in two-layer pattern token overhead blockquote

## Parent Task

- Original: `plan/tasks-1-hooks-two-layer-pattern.md`
- Review Date: 2026-03-07

## Status

- [ ] Pending

## Priority

Medium

## Description

The token overhead blockquote in the two-layer pattern recipe section cites `prompt-improver v0.5.1` but should cite `prompt-improver v0.4.0`. The source material (`research/prompt-engineering/claude-code-prompt-improver.md`) tags both the `~189 tokens` measurement and the `31% reduction` figure to the v0.4.0 release (lines 121 and 124). v0.5.1 is the current project version (line 7), not the version where the measurement was made. The task file AC-3 explicitly required `v0.4.0 (2026-02-14)`.

## Acceptance Criteria

- [ ] Line 362 of `plugins/plugin-creator/skills/hooks-patterns/SKILL.md` reads `prompt-improver v0.4.0, 2026-02-14` instead of `prompt-improver v0.5.1, 2026-02-14`
- [ ] No other content in the section is modified
- [ ] File passes `uv run prek run --files plugins/plugin-creator/skills/hooks-patterns/SKILL.md`

## Files to Modify

- `plugins/plugin-creator/skills/hooks-patterns/SKILL.md:362` - change `v0.5.1` to `v0.4.0`

## Verification Steps

1. Read line 362 of the file and confirm it contains `v0.4.0`
2. Run `uv run prek run --files plugins/plugin-creator/skills/hooks-patterns/SKILL.md` and confirm exit 0
3. Confirm the rest of the inserted section (lines 353-427) is unchanged

## References

- Source measurement: `research/prompt-engineering/claude-code-prompt-improver.md:121,124`
- Original task AC-3: `plan/tasks-1-hooks-two-layer-pattern.md:122-123`
- Related code: `plugins/plugin-creator/skills/hooks-patterns/SKILL.md:360-362`
