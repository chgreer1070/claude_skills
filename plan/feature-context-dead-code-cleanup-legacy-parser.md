# Feature Context: Dead Code Cleanup — Legacy Parser and Fenced YAML Recovery

## Document Metadata

- **Generated**: 2026-03-05
- **Input Type**: simple_description
- **Source**: Feature request — remove legacy markdown parser and fenced YAML recovery from implementation_manager
- **Status**: DISCOVERY_COMPLETE

---

## Original Request

Dead code cleanup: remove legacy markdown parser and fenced YAML recovery from implementation_manager.

The following code is dead (unreachable) because all task files now use directory format with bare YAML frontmatter:
- `FIELD_PARSERS` registry in `implementation_manager.py` (lines 601, 651)
- `_depth` recursion guard in `parse_task_content` (lines 658, 678, 703)
- Fenced YAML recovery code path in `parse_task_content` (lines 678–703)
- Legacy markdown parser code path in `implementation_manager.py`
- `_update_legacy_timestamp` function in `task_status_hook.py` (line 285)
- `_legacy_field_to_yaml` function in `task_status_hook.py` (line 357)
- Tests in `test_task_format_fenced_yaml.py` that test the above dead paths

---

## Core Intent Analysis

### WHO (Target Users)

Developers maintaining the implementation-manager scripts. The dead code creates maintenance burden and misleads anyone reading the codebase about what formats are actually supported.

### WHAT (Desired Outcome)

Remove all code that is unreachable under current operating conditions — specifically, code that handled legacy markdown task format and fenced YAML recovery — so the codebase reflects only what the system actually does.

### WHEN (Trigger Conditions)

The trigger is the completed migration: all task files now use the directory format with bare YAML frontmatter. Once that migration was complete, the code that handled the old formats became permanently unreachable. This is a post-migration cleanup.

### WHY (Problem Being Solved)

Dead code has concrete costs:
1. **Maintenance burden**: Future changes to parsing logic must navigate branches that are never exercised.
2. **Misleading documentation**: Function docstrings for `parse_task_content` describe "automatic format detection" including legacy markdown and fenced YAML recovery — this implies the system still supports those formats, which it does not.
3. **Test noise**: `test_task_format_fenced_yaml.py` tests code paths that are unreachable in production, inflating test count without covering real behavior.
4. **Risk of accidental resurrection**: The `_depth` recursion guard and fenced YAML re-parse loop create an internal recursive code path. Dead recursive code paths are non-obvious hazards if the code is ever modified nearby.

---

## Codebase Research

### Similar Patterns Found

#### Pattern 1: YAML-only path in `parse_task_file`

- **Location**: `plugins/python3-development/skills/implementation-manager/scripts/implementation_manager.py:749-753`
- **Relevance**: `parse_task_file` already routes to `_parse_task_directory` for directories (the current format) and falls through to `parse_task_content` for single files. The directory path is the live path; the single-file path feeds into the legacy branching that would be removed.
- **Reusable**: The directory-routing logic is the keeper; single-file content routing becomes a narrow fallback or can be simplified to only handle bare YAML.

#### Pattern 2: YAML-only branch in `add_timestamp_to_task`

- **Location**: `plugins/python3-development/skills/implementation-manager/scripts/task_status_hook.py:339-354`
- **Relevance**: `add_timestamp_to_task` has an explicit YAML branch (lines 339–345) and a legacy markdown fallback (lines 347–354). The legacy fallback calls `_update_legacy_timestamp` (line 354) and `_legacy_field_to_yaml` (line 344). Both callees are the dead functions identified in the request. The YAML branch is the live path.
- **Reusable**: The YAML branch at lines 339–345 is retained; the fallback block and both called functions are removed.

#### Pattern 3: `_parse_task_directory` as canonical entry point

- **Location**: `plugins/python3-development/skills/implementation-manager/scripts/implementation_manager.py:756-770`
- **Relevance**: This function handles the current directory-per-task format. It notes in its docstring that files without YAML frontmatter are "attempted with legacy parsing" — this is the surviving reference to the legacy path within the directory parser, and it may also become dead or need a comment update after cleanup.
- **Reusable**: The YAML frontmatter discovery loop within this function is the live parsing entry point.

### Existing Infrastructure

- `has_yaml_frontmatter` and `parse_task_from_frontmatter` in `task_format.py` are the live parsing utilities and are unaffected.
- `update_yaml_field` in `task_status_hook.py` is the live timestamp-update utility and is unaffected.
- `detect_fenced_yaml` is called only from the dead fenced YAML recovery code path in `parse_task_content`. Its fate depends on whether it is called anywhere else.

### Code References

- `implementation_manager.py:601-610` — `FIELD_PARSERS` registry (8 parser instances, populated but only used by `_parse_line` which is only called from the legacy branch)
- `implementation_manager.py:642-655` — `_parse_line` function (only caller is legacy branch in `parse_task_content`)
- `implementation_manager.py:658` — `parse_task_content` signature with `_depth: int = 0`
- `implementation_manager.py:678-703` — fenced YAML detection and recursive re-parse
- `implementation_manager.py:705-727` — legacy markdown loop using `task_header_pattern` and `_parse_line`
- `task_status_hook.py:282` — `_LEGACY_INSERT_AFTER_FIELDS` constant (only used by `_update_legacy_timestamp`)
- `task_status_hook.py:285-316` — `_update_legacy_timestamp` function
- `task_status_hook.py:347-354` — legacy markdown fallback block in `add_timestamp_to_task`
- `task_status_hook.py:357-372` — `_legacy_field_to_yaml` function

---

## Use Scenarios

### Scenario 1: Developer reads parse_task_content to understand supported formats

**Actor**: Developer new to the codebase
**Trigger**: Needs to understand what task file formats the system supports
**Goal**: Get an accurate picture of supported input formats
**Expected Outcome**: After cleanup, the function handles only bare YAML frontmatter. The docstring no longer describes legacy markdown or fenced YAML recovery. The developer gets an accurate understanding on first read.

### Scenario 2: Developer modifies parsing logic near the dead recursion guard

**Actor**: Developer adding a new field to task parsing
**Trigger**: Adding a new metadata field to YAML frontmatter tasks
**Goal**: Extend parsing without introducing bugs
**Expected Outcome**: After cleanup, there is no recursive `_depth` guard or fenced YAML re-parse loop to confuse the modification. The function is linear and the risk of accidentally touching the recursion path is eliminated.

### Scenario 3: CI runs the test suite

**Actor**: CI pipeline
**Trigger**: Pull request or commit
**Goal**: Verify implementation-manager scripts function correctly
**Expected Outcome**: After cleanup, `test_task_format_fenced_yaml.py` (which tests the now-removed paths) is deleted. Test count reflects only live behavior. No tests reference removed symbols.

---

## Gap Analysis

### Identified Gaps

| # | Category | Gap Description | Impact |
|---|----------|-----------------|--------|
| 1 | Scope | `detect_fenced_yaml` in `task_format.py` — is it called from anywhere other than the dead fenced YAML recovery path? | If it has other callers, it must be retained; if not, it is also dead and should be removed. |
| 2 | Scope | `_parse_line` and the 8 `FieldParser` subclasses — are they used outside the legacy markdown loop? | If they are test-only or exclusively used by the legacy path, all 8 classes and `_parse_line` are removable. If any parser is reused elsewhere, that usage must be identified. |
| 3 | Scope | `_LEGACY_INSERT_AFTER_FIELDS` constant in `task_status_hook.py:282` — only used by `_update_legacy_timestamp`. Removal is implied but not explicitly stated in the request. | Minor — but omitting it leaves a dead constant that references legacy field names. |
| 4 | Scope | `update_task_status` in `task_status_hook.py` has a legacy markdown fallback parallel to `add_timestamp_to_task`. It may contain the same dead-branch pattern. | If present, that fallback is equally dead and should be in scope. |
| 5 | Behavior | `_parse_task_directory` docstring says "Files without YAML frontmatter are attempted with legacy parsing." After removal, this statement becomes inaccurate. | The docstring must be updated to reflect the post-cleanup behavior. |
| 6 | Integration | `test_task_format_fenced_yaml.py` deletion — should the file be deleted entirely, or should surviving tests be extracted first? | If the file contains any tests covering live behavior (e.g., testing `has_yaml_frontmatter`), those must be preserved, not deleted with the file. |

---

## Questions Requiring Resolution

### Q1: Scope of `detect_fenced_yaml`

- **Category**: Scope
- **Gap**: `detect_fenced_yaml` is imported and called from the dead fenced YAML recovery code path. It may or may not exist in `task_format.py` and may have other callers.
- **Question**: Should `detect_fenced_yaml` be removed as part of this cleanup, or retained?
- **Options**:
  - A) Remove it — it is only called from the dead recovery path
  - B) Retain it — it has callers outside the dead path
- **Why It Matters**: Removing a function with live callers breaks the system. Retaining a function with no callers leaves more dead code.
- **Resolution**: _pending_

### Q2: Scope of `FieldParser` subclasses

- **Category**: Scope
- **Gap**: Eight `FieldParser` subclasses (`StatusParser`, `DependenciesParser`, `AgentParser`, `PriorityParser`, `ComplexityParser`, `StartedParser`, `CompletedParser`, `SkillsParser`) feed `FIELD_PARSERS`. They are only used by `_parse_line`, which is only called from the legacy markdown loop.
- **Question**: Are these 8 classes and `_parse_line` in scope for removal?
- **Options**:
  - A) Yes — they are exclusively legacy infrastructure
  - B) No — at least one class is used outside the legacy path
- **Why It Matters**: Removing them eliminates ~150 lines of dead class definitions. Leaving them leaves the dead registry intact.
- **Resolution**: _pending_

### Q3: `update_task_status` legacy fallback

- **Category**: Scope
- **Gap**: The request explicitly lists `add_timestamp_to_task`'s legacy fallback as dead. `update_task_status` in `task_status_hook.py` likely has a parallel legacy fallback for status updates.
- **Question**: Is the legacy fallback branch in `update_task_status` also in scope for this cleanup?
- **Options**:
  - A) Yes — it is the same pattern and equally dead
  - B) No — include it in a separate cleanup pass
- **Why It Matters**: Cleaning one branch but not the other leaves the codebase inconsistently cleaned.
- **Resolution**: _pending_

### Q4: Handling of tests in `test_task_format_fenced_yaml.py`

- **Category**: Behavior
- **Gap**: The request says to remove tests that test the dead paths. The file may also contain tests that incidentally test live behavior (e.g., testing `has_yaml_frontmatter` or `parse_task_from_frontmatter` using the fenced YAML scenario as a fixture).
- **Question**: Should the entire file be deleted, or should it be audited for any tests covering live behavior before deletion?
- **Options**:
  - A) Audit first — extract and relocate any tests covering live behavior, then delete
  - B) Delete entirely — the file was created specifically for fenced YAML and contains no live-behavior coverage
- **Why It Matters**: Deleting tests that cover live behavior reduces test coverage for still-active code.
- **Resolution**: _pending_

---

## Goals (Pending Resolution)

_These goals will be finalized after questions are resolved._

1. Remove the legacy markdown parsing code path from `parse_task_content` in `implementation_manager.py`, leaving only the YAML frontmatter path.
2. Remove the fenced YAML recovery code path (including the `_depth` recursion guard) from `parse_task_content`.
3. Remove `_update_legacy_timestamp` and `_legacy_field_to_yaml` from `task_status_hook.py`.
4. Remove the legacy markdown fallback block in `add_timestamp_to_task`.
5. Remove `_LEGACY_INSERT_AFTER_FIELDS` constant.
6. Update all docstrings that describe multi-format detection to reflect YAML-only behavior.
7. Delete or prune `test_task_format_fenced_yaml.py` so no tests reference removed symbols.
8. Confirm whether `detect_fenced_yaml` and the 8 `FieldParser` classes have live callers before removing them.

---

## Next Steps

After questions are resolved:

1. Update "Resolution" fields in Questions section
2. Finalize Goals section
3. Proceed to RT-ICA assessment
4. Then proceed to architecture design
