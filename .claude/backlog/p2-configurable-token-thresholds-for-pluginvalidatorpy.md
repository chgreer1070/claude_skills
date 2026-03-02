---
name: Configurable Token Thresholds for plugin_validator.py
description: '`plugin_validator.py` token complexity thresholds (4400 warn, 8800 error) are hardcoded constants. Allow per-project or per-plugin configuration via a config file (e.g., `.claude-plugin/validator.json` or a `[tool.plugin-validator]` section in `pyproject.toml`) so different projects can set their own limits.'
metadata:
  topic: configurable-token-thresholds-for-pluginvalidatorpy
  source: Session 2026-02-18, token threshold analysis
  added: '2026-02-18'
  priority: P2
  type: Feature
  status: open
  issue: '#119'
---

## Story

As a **developer using Claude Code skills**, I want to **configurable token thresholds for plugin_validator.py** so that **the tooling becomes more capable and complete**.

## Description

`plugin_validator.py` token complexity thresholds (4400 warn, 8800 error) are hardcoded constants. Allow per-project or per-plugin configuration via a config file (e.g., `.claude-plugin/validator.json` or a `[tool.plugin-validator]` section in `pyproject.toml`) so different projects can set their own limits.

## Suggested Location

`plugins/plugin-creator/scripts/plugin_validator.py`

## Context

- **Source**: Session 2026-02-18, token threshold analysis
- **Priority**: P2
- **Added**: 2026-02-18
- **Research questions**: None