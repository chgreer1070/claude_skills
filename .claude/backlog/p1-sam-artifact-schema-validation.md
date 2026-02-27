---
name: 'SAM: Artifact Schema Validation'
description: Define formal validation rules or JSON schemas for artifact formats. Currently only templates provided. Enable automated validation at stage boundaries.
metadata:
  topic: sam-artifact-schema-validation
  source: Gap analysis of SAM framework
  added: '2026-02-01'
  priority: completed
  type: Feature
  status: done
  issue: '#202'
  plan: N/A
---

**Suggested location**: [`sam-artifact-schemas/`](https://github.com/bitflight-devops/stateless-agent-methodology) (new directory with schema files)

**Research first**: How do GSD artifacts (STATE.md, ROADMAP.md) enforce structure? What validation approaches exist in BMAD-METHOD? JSON Schema vs YAML validation vs custom parsers?