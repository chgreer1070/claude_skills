---
name: Enhance skill-research-process for CLI tool skills
description: 'The skill-research-process skill has sound research orchestration but lacks output specification for producing complete CLI tool skills. Three gaps identified via assessment against the uv skill: (1) No local directory input — passing a path like .claude/worktrees/ty/docs/ is treated as a tool name, triggering web searches instead of reading local docs. (2) No CLI reference file templates — no structural anchor ensuring standard reference types (cli_reference.md, configuration.md, migration-guid'
metadata:
  topic: enhance-skill-research-process-for-cli-tool-skills
  source: Session observation
  added: '2026-02-25'
  priority: P1
  type: Feature
  status: open
---

**Research first**: Read .claude/plan/skill-research-process-assessment.md for full gap analysis. Should output spec be embedded in skill-research-process or in a separate output-template skill? How should local path detection work vs tool-name lookup?
