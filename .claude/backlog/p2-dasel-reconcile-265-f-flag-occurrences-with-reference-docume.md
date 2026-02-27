---
name: 'dasel: Reconcile 265 `-f` flag occurrences with reference documentation'
description: Reference documentation states dasel uses a specific flag pattern, but 265 occurrences of the `-f` flag across the skill contradict this documentation. The hook file exists on disk but is not registered in the plugin manifest (`plugin.json`). Run `auto_sync_manifests.py --reconcile` to fix manifest drift, and audit `-f` flag usage against official dasel documentation.
metadata:
  topic: dasel-reconcile-265-f-flag-occurrences-with-reference-docume
  source: Plugin code review session 2026-02-21
  added: '2026-02-21'
  priority: P2
  type: Feature
  status: open
  issue: '#95'
---