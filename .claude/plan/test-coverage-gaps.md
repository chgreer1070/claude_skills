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
