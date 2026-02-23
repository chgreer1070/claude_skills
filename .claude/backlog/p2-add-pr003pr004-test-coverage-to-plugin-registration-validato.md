---
name: Add PR003/PR004 test coverage to plugin registration validator
description: '`PluginRegistrationValidator` defines PR003 (missing metadata fields: repository, homepage, author) and PR004 (repository URL mismatches git remote URL) at lines 276-277 of `plugin_validator.py`, and emits them at lines 2815 and 2834. Tests exist for PR001 (unregistered) and PR002 (missing file), but not PR003/PR004. Add tests to `plugins/plugin-creator/tests/test_plugin_registration_validator.py` covering: (1) PR003 emitted when metadata fields absent; (2) PR004 emitted when repo URL mismatches'
metadata:
  topic: add-pr003pr004-test-coverage-to-plugin-registration-validato
  source: Code review session 2026-02-21
  added: '2026-02-21'
  priority: P2
  type: Feature
  status: open
---
