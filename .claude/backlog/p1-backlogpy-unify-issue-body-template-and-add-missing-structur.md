---
name: 'backlog.py: unify issue body template and add missing structured fields'
description: "Three divergent build_story_body/build_issue_body functions exist: backlog.py (line 381), repair_from_original_register.py, and rebuild_issue_bodies.py. Each assembles GitHub issue bodies differently — different story sentences, different sections, different field mappings. backlog.py is the authoritative script but its build_issue_body uses first sentence of description for the story goal (produces bad English for multi-sentence descriptions) and has a generic benefit ('backlog items are tracked in GitHub'). Additionally, backlog.py add is missing CLI flags for --files, --suggested-location, and groomed content passthrough during issue creation. Fix: (1) backlog.py build_issue_body should use title for the story goal, type-specific role/benefit from ROLE_MAP/BENEFIT_MAP, (2) add --files and --suggested-location flags to backlog.py add, (3) repair scripts should import from backlog.py or be deleted (one-shot tools), (4) groom subcommand already syncs groomed content to issues — verify it works end-to-end."
metadata:
  topic: backlogpy-unify-issue-body-template-and-add-missing-structur
  source: Session observation — identified during repair of 60 truncated issue bodies
  added: '2026-02-26'
  priority: P1
  type: Refactor
  status: open
  issue: '#283'
---