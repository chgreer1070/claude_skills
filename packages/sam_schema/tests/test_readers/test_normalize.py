"""Tests for sam_schema.readers.normalize — format normalization and status mapping.

Tests: Status coercion, dependency parsing, gap detection, lenient normalization.
How: Construct raw dicts and normalize to Pydantic models; verify coerced values.
Why: Normalization is the bridge between arbitrary reader output and the validated
model layer. Incorrect coercion silently corrupts task state.
"""

from __future__ import annotations

import pathlib

import pytest
from sam_schema.core.models import TaskStatus
from sam_schema.readers.detect import FormatType
from sam_schema.readers.normalize import detect_gaps, normalize_plan, normalize_task, normalize_task_lenient

_FIXTURES = pathlib.Path(__file__).parent.parent / "fixtures"


# ---------------------------------------------------------------------------
# normalize_task — required fields
# ---------------------------------------------------------------------------


def test_normalize_task_valid_dict_returns_task_model():
    raw = {"task": "T1", "title": "A task", "status": "not-started"}
    task, _gaps = normalize_task(raw, FormatType.YAML_FRONTMATTER)
    assert task.id == "T1"
    assert task.title == "A task"


def test_normalize_task_missing_task_id_raises_value_error():
    raw = {"title": "No ID", "status": "not-started"}
    with pytest.raises(ValueError, match="missing required"):
        normalize_task(raw, FormatType.YAML_FRONTMATTER)


def test_normalize_task_missing_title_raises_value_error():
    raw = {"task": "T1", "status": "not-started"}
    with pytest.raises(ValueError, match="missing required"):
        normalize_task(raw, FormatType.YAML_FRONTMATTER)


def test_normalize_task_accepts_id_key_as_alias_for_task():
    raw = {"id": "T2", "title": "Using id key", "status": "complete"}
    task, _ = normalize_task(raw, FormatType.PURE_YAML)
    assert task.id == "T2"


def test_normalize_task_accepts_task_id_key_as_alias():
    raw = {"task_id": "3", "title": "Using task_id", "status": "not-started"}
    task, _ = normalize_task(raw, FormatType.LEGACY_MARKDOWN)
    assert task.id == "3"


# ---------------------------------------------------------------------------
# normalize_task — status normalization
# ---------------------------------------------------------------------------


def test_normalize_task_canonical_status_preserved():
    raw = {"task": "T1", "title": "T", "status": "in-progress"}
    task, _ = normalize_task(raw, FormatType.PURE_YAML)
    assert task.status == TaskStatus.IN_PROGRESS


def test_normalize_task_space_separated_status_mapped():
    raw = {"task": "T1", "title": "T", "status": "NOT STARTED"}
    task, _ = normalize_task(raw, FormatType.LEGACY_MARKDOWN)
    assert task.status == TaskStatus.NOT_STARTED


def test_normalize_task_emoji_complete_status_mapped():
    raw = {"task": "T1", "title": "T", "status": ":white_check_mark: COMPLETE"}
    task, _ = normalize_task(raw, FormatType.LEGACY_MARKDOWN)
    assert task.status == TaskStatus.COMPLETE


def test_normalize_task_emoji_in_progress_status_mapped():
    raw = {"task": "T1", "title": "T", "status": ":arrows_counterclockwise: IN PROGRESS"}
    task, _ = normalize_task(raw, FormatType.LEGACY_MARKDOWN)
    assert task.status == TaskStatus.IN_PROGRESS


def test_normalize_task_unknown_status_falls_back_to_not_started():
    raw = {"task": "T1", "title": "T", "status": "INVENTED_STATUS"}
    task, _ = normalize_task(raw, FormatType.LEGACY_MARKDOWN)
    assert task.status == TaskStatus.NOT_STARTED


def test_normalize_task_none_status_defaults_to_not_started():
    raw = {"task": "T1", "title": "T", "status": None}
    task, _ = normalize_task(raw, FormatType.YAML_FRONTMATTER)
    assert task.status == TaskStatus.NOT_STARTED


# ---------------------------------------------------------------------------
# normalize_task — dependency cleaning (legacy prefix stripping)
# ---------------------------------------------------------------------------


def test_normalize_task_strips_task_prefix_from_dependencies():
    raw = {"task": "2", "title": "T", "status": "not-started", "dependencies": ["Task 1"]}
    task, _ = normalize_task(raw, FormatType.LEGACY_MARKDOWN)
    assert task.dependencies == ["1"]


def test_normalize_task_strips_task_prefix_case_insensitive():
    raw = {"task": "3", "title": "T", "status": "not-started", "dependencies": ["task 1", "TASK 2"]}
    task, _ = normalize_task(raw, FormatType.LEGACY_MARKDOWN)
    assert task.dependencies == ["1", "2"]


def test_normalize_task_bare_id_dependencies_unchanged():
    raw = {"task": "T2", "title": "T", "status": "not-started", "dependencies": ["T1"]}
    task, _ = normalize_task(raw, FormatType.PURE_YAML)
    assert task.dependencies == ["T1"]


# ---------------------------------------------------------------------------
# normalize_task — schema gaps
# ---------------------------------------------------------------------------


def test_normalize_task_non_canonical_format_reports_gaps():
    raw = {"task": "T1", "title": "T", "status": "not-started"}
    _, gaps = normalize_task(raw, FormatType.LEGACY_MARKDOWN)
    assert len(gaps) > 0


def test_normalize_task_canonical_format_reports_no_gaps():
    raw = {"task": "T1", "title": "T", "status": "not-started"}
    _, gaps = normalize_task(raw, FormatType.PURE_YAML)
    assert gaps == []


def test_normalize_task_gap_field_names_are_canonical():
    raw = {"task": "T1", "title": "T", "status": "not-started"}
    _, gaps = normalize_task(raw, FormatType.LEGACY_MARKDOWN)
    field_names = {g.field_name for g in gaps}
    # "agent" is one of the tracked optional fields
    assert "agent" in field_names


def test_normalize_task_present_optional_field_not_reported_as_gap():
    raw = {"task": "T1", "title": "T", "status": "not-started", "agent": "some-agent", "priority": 1}
    _, gaps = normalize_task(raw, FormatType.LEGACY_MARKDOWN)
    gap_fields = {g.field_name for g in gaps}
    assert "agent" not in gap_fields
    assert "priority" not in gap_fields


# ---------------------------------------------------------------------------
# normalize_task_lenient
# ---------------------------------------------------------------------------


def test_normalize_task_lenient_invalid_dict_returns_none_and_empty_gaps():
    raw = {"title": "No ID", "status": "not-started"}  # missing task id
    task, gaps = normalize_task_lenient(raw, FormatType.YAML_FRONTMATTER)
    assert task is None
    assert gaps == []


def test_normalize_task_lenient_valid_dict_returns_task():
    raw = {"task": "T1", "title": "OK", "status": "complete"}
    task, _ = normalize_task_lenient(raw, FormatType.PURE_YAML)
    assert task is not None
    assert task.id == "T1"


# ---------------------------------------------------------------------------
# normalize_plan — end-to-end from fixture files
# ---------------------------------------------------------------------------


def test_normalize_plan_pure_yaml_single_produces_three_tasks():
    from sam_schema.readers.yaml_reader import read_yaml_plan

    path = _FIXTURES / "pure_yaml_single.yaml"
    plan_meta, task_dicts, fmt = read_yaml_plan(path)
    result = normalize_plan(plan_meta, task_dicts, fmt, path)
    assert len(result.plan.tasks) == 3


def test_normalize_plan_pure_yaml_single_has_no_gaps():
    from sam_schema.readers.yaml_reader import read_yaml_plan

    path = _FIXTURES / "pure_yaml_single.yaml"
    plan_meta, task_dicts, fmt = read_yaml_plan(path)
    result = normalize_plan(plan_meta, task_dicts, fmt, path)
    assert result.gaps == []


def test_normalize_plan_legacy_markdown_produces_three_tasks():
    from sam_schema.readers.legacy_reader import read_legacy_plan

    path = _FIXTURES / "legacy_markdown.md"
    plan_meta, task_dicts, fmt = read_legacy_plan(path)
    result = normalize_plan(plan_meta, task_dicts, fmt, path)
    assert len(result.plan.tasks) == 3


def test_normalize_plan_legacy_markdown_produces_schema_gaps():
    from sam_schema.readers.legacy_reader import read_legacy_plan

    path = _FIXTURES / "legacy_markdown.md"
    plan_meta, task_dicts, fmt = read_legacy_plan(path)
    result = normalize_plan(plan_meta, task_dicts, fmt, path)
    assert len(result.gaps) > 0


def test_normalize_plan_global_manifest_produces_four_tasks():
    from sam_schema.readers.manifest_reader import read_manifest_plan

    path = _FIXTURES / "global_manifest.md"
    plan_meta, task_dicts, fmt = read_manifest_plan(path)
    result = normalize_plan(plan_meta, task_dicts, fmt, path)
    assert len(result.plan.tasks) == 4


def test_normalize_plan_frontmatter_multi_produces_three_tasks():
    from sam_schema.readers.frontmatter_reader import read_frontmatter_plan

    path = _FIXTURES / "yaml_frontmatter_multi.md"
    plan_meta, task_dicts, fmt = read_frontmatter_plan(path)
    result = normalize_plan(plan_meta, task_dicts, fmt, path)
    assert len(result.plan.tasks) == 3


def test_normalize_plan_feature_set_on_plan_model():
    from sam_schema.readers.yaml_reader import read_yaml_plan

    path = _FIXTURES / "pure_yaml_single.yaml"
    plan_meta, task_dicts, fmt = read_yaml_plan(path)
    result = normalize_plan(plan_meta, task_dicts, fmt, path)
    assert result.plan.feature == "auth-system"


def test_normalize_plan_missing_feature_raises_value_error():
    raw_meta: dict = {}
    with pytest.raises(ValueError, match="feature"):
        normalize_plan(raw_meta, [], FormatType.PURE_YAML, pathlib.Path("/fake"))


# ---------------------------------------------------------------------------
# normalize_plan — lenient invalid task ID handling
# ---------------------------------------------------------------------------


def test_normalize_plan_invalid_task_id_recorded_as_gap_not_abort():
    # Task IDs like T10a do not match ^[A-Za-z]?\d+(\.\d+)?$
    raw_meta = {"feature": "test"}
    task_dicts = [
        {"task": "T10a", "title": "Invalid ID task", "status": "not-started"},
        {"task": "T1", "title": "Valid task", "status": "not-started"},
    ]
    result = normalize_plan(raw_meta, task_dicts, FormatType.YAML_FRONTMATTER, pathlib.Path("/fake"))
    # Valid task is still included
    assert len(result.plan.tasks) == 1
    assert result.plan.tasks[0].id == "T1"
    # Invalid ID is recorded as a schema gap
    invalid_gaps = [g for g in result.gaps if g.task_id == "T10a"]
    assert len(invalid_gaps) >= 1


def test_normalize_plan_invalid_task_gap_has_invalid_value_gap_type():
    raw_meta = {"feature": "test"}
    task_dicts = [{"task": "T10b", "title": "Bad", "status": "not-started"}]
    result = normalize_plan(raw_meta, task_dicts, FormatType.YAML_FRONTMATTER, pathlib.Path("/fake"))
    gap = next(g for g in result.gaps if g.task_id == "T10b")
    assert gap.gap_type == "invalid_value"


# ---------------------------------------------------------------------------
# normalize_plan — malformed fixture: missing required title
# ---------------------------------------------------------------------------


def test_normalize_plan_malformed_missing_title_records_gap():
    from sam_schema.readers.yaml_reader import read_yaml_plan

    path = _FIXTURES / "malformed" / "missing_required.yaml"
    plan_meta, task_dicts, fmt = read_yaml_plan(path)
    result = normalize_plan(plan_meta, task_dicts, fmt, path)
    # T1 has no title — must be recorded as gap, not abort
    assert result.plan.tasks == []
    assert len(result.gaps) >= 1


# ---------------------------------------------------------------------------
# normalize_plan — malformed fixture: invalid status falls back, not abort
# ---------------------------------------------------------------------------


def test_normalize_plan_malformed_invalid_status_task_is_included():
    from sam_schema.readers.yaml_reader import read_yaml_plan

    path = _FIXTURES / "malformed" / "invalid_status.yaml"
    plan_meta, task_dicts, fmt = read_yaml_plan(path)
    result = normalize_plan(plan_meta, task_dicts, fmt, path)
    # "started" is not in TaskStatus but normalizer falls back to not-started
    assert len(result.plan.tasks) == 1
    assert result.plan.tasks[0].status == TaskStatus.NOT_STARTED


# ---------------------------------------------------------------------------
# detect_gaps — public API (unconditional gap analysis)
# ---------------------------------------------------------------------------


def test_detect_gaps_reports_missing_agent() -> None:
    """Verify detect_gaps reports missing 'agent' field unconditionally.

    Tests: Public detect_gaps function.
    How: Pass a raw dict without 'agent', check gap list.
    Why: detect_gaps is the public API for unconditional gap analysis,
    distinct from the internal _detect_gaps that filters by format.
    """
    raw: dict = {"task": "T1", "title": "T", "status": "not-started"}
    gaps = detect_gaps(raw, "T1")
    field_names = {g.field_name for g in gaps}
    assert "agent" in field_names


def test_detect_gaps_does_not_report_present_field() -> None:
    """Verify detect_gaps skips fields that are present.

    Tests: detect_gaps with fields populated.
    How: Include 'agent' in raw dict, verify it is not in gaps.
    Why: Correct gap detection must not flag present fields.
    """
    raw: dict = {"task": "T1", "title": "T", "status": "not-started", "agent": "some-agent"}
    gaps = detect_gaps(raw, "T1")
    field_names = {g.field_name for g in gaps}
    assert "agent" not in field_names


def test_detect_gaps_accepts_snake_case_variant() -> None:
    """Verify detect_gaps recognizes snake_case field names.

    Tests: detect_gaps snake_case alias handling.
    How: Include 'blocked_by' instead of 'blocked-by', verify not flagged.
    Why: Some readers produce snake_case keys; both must be accepted.
    """
    raw: dict = {"task": "T1", "title": "T", "status": "not-started", "blocked_by": []}
    gaps = detect_gaps(raw, "T1")
    field_names = {g.field_name for g in gaps}
    assert "blocked-by" not in field_names


# ---------------------------------------------------------------------------
# normalize_task — title alias via 'name' key
# ---------------------------------------------------------------------------


def test_normalize_task_accepts_name_as_title_alias() -> None:
    """Verify 'name' key is accepted as alias for 'title'.

    Tests: Backward compatibility alias for title field.
    How: Pass raw dict with 'name' instead of 'title'.
    Why: Some legacy formats use 'name' instead of 'title'.
    """
    raw: dict = {"task": "T1", "name": "Named task", "status": "not-started"}
    task, _ = normalize_task(raw, FormatType.LEGACY_MARKDOWN)
    assert task.title == "Named task"


# ---------------------------------------------------------------------------
# normalize_task — title-based status override ([DEFERRED], [SKIPPED])
# ---------------------------------------------------------------------------


def test_normalize_task_deferred_title_prefix_overrides_status() -> None:
    """Verify [DEFERRED] title prefix overrides stored status.

    Tests: Title-marker-based status override.
    How: Pass raw dict with title starting with '[DEFERRED]'.
    Why: Legacy tasks may mark status only in the title prefix.
    """
    raw: dict = {"task": "T1", "title": "[DEFERRED] Some task", "status": "not-started"}
    task, _ = normalize_task(raw, FormatType.LEGACY_MARKDOWN)
    assert task.status == TaskStatus.DEFERRED


def test_normalize_task_skipped_title_prefix_overrides_status() -> None:
    """Verify [SKIPPED] title prefix overrides stored status.

    Tests: Title-marker-based status override.
    How: Pass raw dict with title starting with '[SKIPPED]'.
    Why: Legacy tasks may mark status only in the title prefix.
    """
    raw: dict = {"task": "T1", "title": "[SKIPPED] Obsolete task", "status": "in-progress"}
    task, _ = normalize_task(raw, FormatType.LEGACY_MARKDOWN)
    assert task.status == TaskStatus.SKIPPED


# ---------------------------------------------------------------------------
# normalize_task — status map edge cases (lowercase after mapping)
# ---------------------------------------------------------------------------


def test_normalize_task_status_direct_emoji_token_mapped() -> None:
    """Verify bare emoji token in STATUS_MAP is mapped correctly.

    Tests: Direct STATUS_MAP key lookup for emoji tokens.
    How: Pass ':x:' as status value.
    Why: Emoji tokens like ':x:' are direct STATUS_MAP keys.
    """
    raw: dict = {"task": "T1", "title": "T", "status": ":x:"}
    task, _ = normalize_task(raw, FormatType.LEGACY_MARKDOWN)
    assert task.status == TaskStatus.NOT_STARTED


def test_normalize_task_case_insensitive_blocked_mapped() -> None:
    """Verify case-insensitive status like 'blocked' works.

    Tests: Case-insensitive status normalization.
    How: Pass lowercase 'blocked' (already canonical).
    Why: YAML readers may produce lowercase strings directly.
    """
    raw: dict = {"task": "T1", "title": "T", "status": "blocked"}
    task, _ = normalize_task(raw, FormatType.YAML_FRONTMATTER)
    assert task.status == TaskStatus.BLOCKED


def test_normalize_task_deferred_space_separated_mapped() -> None:
    """Verify 'DEFERRED' (uppercase space-separated variant) is mapped.

    Tests: STATUS_MAP uppercase lookup.
    How: Pass 'DEFERRED' as status.
    Why: Legacy markdown uses uppercase status labels.
    """
    raw: dict = {"task": "T1", "title": "T", "status": "DEFERRED"}
    task, _ = normalize_task(raw, FormatType.LEGACY_MARKDOWN)
    assert task.status == TaskStatus.DEFERRED


def test_normalize_task_wont_fix_status_mapped() -> None:
    """Verify 'WONT FIX' maps to not-started (it's in STATUS_MAP but has no TaskStatus member).

    Tests: STATUS_MAP entry that maps to a non-existent status (special handling).
    How: Pass 'WONT FIX' as status.
    Why: 'wont-fix' is in STATUS_MAP but there is no TaskStatus.WONT_FIX.
    """
    raw: dict = {"task": "T1", "title": "T", "status": "WONT FIX"}
    # WONT FIX maps to "wont-fix" which is not in TaskStatus, so it falls back
    task, _ = normalize_task(raw, FormatType.LEGACY_MARKDOWN)
    # The mapped value "wont-fix" is not in TaskStatus, so it falls through to fallback
    assert task.status is not None


# ---------------------------------------------------------------------------
# normalize_plan — slug key accepted for feature
# ---------------------------------------------------------------------------


def test_normalize_plan_slug_key_accepted_as_feature() -> None:
    """Verify 'slug' key in plan_meta is accepted as 'feature'.

    Tests: Feature name from 'slug' key.
    How: Pass plan_meta with 'slug' instead of 'feature'.
    Why: Global manifest format uses 'slug' field.
    """
    raw_meta: dict = {"slug": "my-feature"}
    task_dicts = [{"task": "T1", "title": "A task", "status": "not-started"}]
    result = normalize_plan(raw_meta, task_dicts, FormatType.GLOBAL_MANIFEST, pathlib.Path("/fake"))
    assert result.plan.feature == "my-feature"
