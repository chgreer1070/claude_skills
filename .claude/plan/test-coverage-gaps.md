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
