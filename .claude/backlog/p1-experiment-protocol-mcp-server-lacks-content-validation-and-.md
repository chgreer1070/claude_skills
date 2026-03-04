---
name: Experiment protocol MCP server lacks content validation and enforcement
description: "The experiment-registry MCP server checks artefact key presence but never validates content, file existence, or artefact integrity. 8 gaps identified via /improve-processes analysis:\n\nCRITICAL — Gap 3: criteria_passed is a trust-based string self-report (state_manager.py:238). The iterate step completes when caller submits criteria_passed: 'true' — MCP does not independently verify rubric scores. Defeats the core anti-bias purpose.\n\nHIGH — Gap 1: No content validation. The validation field in experiment_core.json is decorative — never read or enforced. Empty artefacts pass.\n\nHIGH — Gap 4: No freeze enforcement on fixture/rubric/task-prompt. No content hashes tracked. Claude can silently modify frozen artefacts between iterations.\n\nHIGH — Gap 5: Rubric modifiable post-creation. Step ordering enforces rubric-before-baseline but content is not hash-locked. Post-hoc rubric modification is possible.\n\nMEDIUM — Gap 6: Iteration log content not validated. MCP cannot detect selective reporting.\n\nMEDIUM — Gap 7: No per-iteration output-iterN.md tracking. Iterate step requires only log.md, not output snapshots.\n\nLOW — Gap 2: No file existence check on artefact paths. Phantom paths reach retrospective-analyst.\n\nLOW — Gap 8: SKILL.md Phase 2 flowchart has no terminal-state guard before entering execution loop.\n\nSuccess: MCP mechanically enforces the methodology it claims to enforce — content validation, hash-based freeze, structured scoring instead of self-report.\n\nEvidence: Process gap analysis against state_manager.py, server.py, experiment_core.json, SKILL.md on branch feature/experiment-protocol-redesign."
metadata:
  topic: experiment-protocol-mcp-server-lacks-content-validation-and-
  source: Process analysis via /improve-processes
  added: '2026-03-04'
  priority: P1
  type: Bug
  status: open
  issue: '#431'
  last_synced: '2026-03-04T21:22:16Z'
---