---
name: Resolve manifest drift to make CI sync check blocking
description: 'Ran `auto_sync_manifests.py --reconcile` to sync all 22 plugin.json manifests with on-disk skills, commands, and agents (153 drift entries fixed). Split the `validate-plugins` CI job into two: `validate-plugins` (plugin-validator, stays in `allowed-failures`) and `manifest-sync` (now blocking in quality gate). Version bumps applied to all affected plugins.'
metadata:
  topic: resolve-manifest-drift-to-make-ci-sync-check-blocking
  source: CI pipeline run 22018867027 on claude/fix-ci-pipeline-RJ0Tw (2026-02-14)
  added: '2026-02-23'
  priority: completed
  type: Feature
  status: done
---
