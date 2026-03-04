# Test Coverage Gaps

## Gap: plugin_validator.py — PR005 command-is-skill-directory check

**Files**: `plugins/plugin-creator/scripts/plugin_validator.py`
**Behavior to cover**: `PluginRegistrationValidator.validate()` should emit a PR005 error when
a path listed in the `commands` array of `plugin.json` is a directory that contains a `SKILL.md`
file. Tests should verify:
- A command entry pointing to a plain `.md` file produces no PR005 error.
- A command entry pointing to a directory without `SKILL.md` produces no PR005 error.
- A command entry pointing to a directory containing `SKILL.md` produces exactly one PR005 error
  with `severity="error"`, `code=ErrorCode.PR005`, and a suggestion referencing the `skills` array.
**Reason not written**: No existing test suite for `plugin_validator.py` was found in `tests/`.
Adding tests is out of scope for this surgical fix task; creating a test suite for the entire
validator from scratch exceeds the stated constraint of a surgical change only.

## Gap: bucket_day_data.py — core bucketing logic

**Files**: `.claude/skills/daily-releases/scripts/bucket_day_data.py`
**Behavior to cover**:
- `semantic_prefix()` with root-level file, 1-level path, 2-level path, and 3+-level path
- `build_file_groups()` groups files by prefix, accumulates token counts, maps commit SHAs
- `assign_buckets()` greedy fill: groups that fit stay in current bucket; overflow starts a new bucket; single group exceeding limit gets its own bucket
- `load_file_entries()` filters `is_source=false` and `is_excluded=true` entries out
- `load_commit_records()` returns correct `CommitRecord` instances
- `build_content_text()` renders `=== File: ===` and `=== Commits ===` sections correctly
- `count_tokens()` returns non-negative integer for arbitrary input strings
**Reason not written**: No existing test suite for the daily-releases scripts directory. Creating a full test suite from scratch is out of scope for the initial implementation task.

## Gap: implementation_manager.py — skills field support

**Files**: `plugins/python3-development/skills/implementation-manager/scripts/implementation_manager.py`
**Behavior to cover**:
- `parse_task_from_frontmatter()` with `skills: [skill1, skill2]` list in YAML frontmatter — returns `Task.skills == ["skill1", "skill2"]`
- `parse_task_from_frontmatter()` without `skills` field — returns `Task.skills == []` (backward compat)
- `_parse_yaml_skills()` with list input, string input, and `None` input
- `SkillsParser.parse()` with `**Skills**: skill1, skill2` legacy markdown format — sets `task_data["skills"]`
- `_create_empty_task_data()` returns `TaskData` with `skills == []`
- `_create_task_from_dict()` passes `skills` from `TaskData` to `Task`
- `ready-tasks` CLI command JSON output includes `"skills": [...]` for each ready task
**Reason not written**: No test suite exists for `implementation_manager.py`. Task 2.3 scope was limited to data model changes only; creating a full test suite from scratch exceeds the stated constraint.

## Gap: state_manager.py integration with validators

**Files**: `plugins/scientific-method/mcp/experiment-registry/state_manager.py`
**Behavior to cover**:
- `complete_step` returns `{"success": False, "validation_errors": [...]}` and does not mutate `state.artefacts` when any validator returns errors (pre-merge validation pattern)
- `_compute_frozen_hashes` stores SHA-256 hash in `state.artefact_integrity[key]` as `ArtefactIntegrity` after merge
- `_complete_iterate_step` derives `criteria_passed` from `rubric_scores.values()` (not from `artefacts["criteria_passed"]`) and stores `rubric_scores_iter{N}` as JSON in `state.artefacts`
- iterate-specific validators (`validate_iteration_output`, `validate_rubric_scores`) are only called when `step_id == "iterate"` — not for other steps
- `complete_step` returns `{"success": False, "blocked_on_human_input": True, ...}` when `human_input_required` and artefacts are missing
- Experiment reaches `status="complete"` when `all(rubric_scores.values())` is True on the iterate step
- Experiment reaches `status="inconclusive"` when `iteration_count >= max_iterations`

**Reason not written**: T4 scope is integration wiring only. Test creation is assigned to T6 per the task plan.

## Gap: server.py complete_step rubric_scores passthrough

**Files**: `plugins/scientific-method/mcp/experiment-registry/server.py`
**Behavior to cover**:
- `complete_step` MCP tool accepts `rubric_scores: dict[str, bool] | None` and passes it through to `manager.complete_step`
- MCP tool returns `{"success": False, "validation_errors": [...]}` when validation fails
- MCP tool raises `ToolError` when `step_id` does not match current step
**Reason not written**: T4 scope is integration wiring only. Test creation is assigned to T6 per the task plan.

## Gap: registry_loader.py_apply_extension merge of new fields

**Files**: `plugins/scientific-method/mcp/experiment-registry/registry_loader.py`
**Behavior to cover**:
- `_apply_extension` appends `ext.additional_validation_rules` to `step.validation_rules`
- `_apply_extension` merges `ext.additional_frozen_artefacts` into `step.frozen_artefacts` with order-preserving deduplication (via `dict.fromkeys`)
- Duplicate keys in `additional_frozen_artefacts` that already exist in `step.frozen_artefacts` are deduplicated (base key wins position)
**Reason not written**: T4 scope is integration wiring only. Test creation is assigned to T6 per the task plan.
