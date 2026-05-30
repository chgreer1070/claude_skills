"""Tests for backlog_core.backends.beads_models.

Verifies Pydantic v2 boundary model validation, enum coercion, extra-field
handling (``extra="ignore"``), and parse function contracts.  Uses JSON
fixture files from ``tests/fixtures/beads/`` for realistic bd CLI output
shapes.  Hypothesis round-trip tests cover all enum combinations.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from backlog_core.backends.beads_models import (
    BeadsCommentRaw,
    BeadsDependencyRaw,
    BeadsId,
    BeadsIssueRaw,
    BeadsIssueType,
    BeadsLabelRaw,
    BeadsPriority,
    BeadsStatus,
    parse_dependency_list,
    parse_issue,
    parse_issue_list,
    parse_ready_list,
    parse_show_issue,
)
from hypothesis import given, settings, strategies as st
from pydantic import ValidationError

if TYPE_CHECKING:
    from backlog_core.backends.bd_runner import JsonValue

# ---------------------------------------------------------------------------
# Fixture helpers
# ---------------------------------------------------------------------------

_FIXTURES = Path(__file__).resolve().parent.parent / "tests" / "fixtures" / "beads"


def _load_json(filename: str) -> JsonValue:
    """Load a JSON fixture file from the beads fixtures directory."""
    return json.loads((_FIXTURES / filename).read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# BeadsId — NewType identity
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_beads_id_is_str_at_runtime() -> None:
    """BeadsId is a NewType; at runtime it is indistinguishable from str."""
    bid: BeadsId = BeadsId("bd-a3f8")
    assert isinstance(bid, str)
    assert bid == "bd-a3f8"


# ---------------------------------------------------------------------------
# BeadsIssueRaw — minimal valid construction
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_parse_issue_minimal_required_fields() -> None:
    """parse_issue accepts a dict containing only the five required fields."""
    data: dict[str, object] = {"id": "bd-a3f8", "title": "Test issue", "status": "open", "type": "task", "priority": 2}
    issue = parse_issue(data)

    assert issue.id == "bd-a3f8"
    assert issue.title == "Test issue"
    assert issue.status == BeadsStatus.OPEN
    assert issue.type == BeadsIssueType.TASK
    assert issue.priority == BeadsPriority.P2
    assert issue.description is None
    assert issue.closed_at is None


@pytest.mark.unit
def test_parse_issue_full_fields_from_fixture() -> None:
    """parse_issue parses all optional fields from the bd_show_issue fixture."""
    data = _load_json("bd_show_issue.json")
    issue = parse_issue(data)

    assert issue.id == "bd-a3f8"
    assert issue.title == "Fix authentication bug"
    assert issue.status == BeadsStatus.OPEN
    assert issue.type == BeadsIssueType.TASK
    assert issue.created_at == "2026-01-15T10:00:00Z"
    assert issue.updated_at == "2026-01-15T12:00:00Z"
    assert issue.closed_at is None


# ---------------------------------------------------------------------------
# Extra fields — silently dropped (extra="ignore")
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_parse_issue_drops_source_argv_and_unknown_fields() -> None:
    """_source_argv and unknown fields from bd --json are silently ignored."""
    data: dict[str, object] = {
        "id": "bd-a3f8",
        "title": "Has extra fields",
        "status": "open",
        "type": "task",
        "priority": 0,
        "_source_argv": ["bd", "show", "bd-a3f8", "--json"],
        "future_field_unknown": "some value",
    }
    issue = parse_issue(data)

    assert issue.id == "bd-a3f8"
    assert not hasattr(issue, "_source_argv")
    assert not hasattr(issue, "future_field_unknown")


# ---------------------------------------------------------------------------
# Enum coercion — Field(strict=False) on status / type / priority
# ---------------------------------------------------------------------------


@pytest.mark.unit
@pytest.mark.parametrize(
    ("raw_status", "expected"),
    [
        ("open", BeadsStatus.OPEN),
        ("in_progress", BeadsStatus.IN_PROGRESS),
        ("blocked", BeadsStatus.BLOCKED),
        ("hooked", BeadsStatus.HOOKED),
        ("deferred", BeadsStatus.DEFERRED),
        ("pinned", BeadsStatus.PINNED),
        ("closed", BeadsStatus.CLOSED),
    ],
)
def test_status_string_coerces_to_enum(raw_status: str, expected: BeadsStatus) -> None:
    """All BeadsStatus string values are coerced to the matching enum member."""
    data: dict[str, object] = {"id": "bd-a3f8", "title": "t", "status": raw_status, "type": "task", "priority": 0}
    assert parse_issue(data).status == expected


@pytest.mark.unit
@pytest.mark.parametrize(
    ("raw_type", "expected"),
    [
        ("task", BeadsIssueType.TASK),
        ("bug", BeadsIssueType.BUG),
        ("feature", BeadsIssueType.FEATURE),
        ("epic", BeadsIssueType.EPIC),
        ("chore", BeadsIssueType.CHORE),
        ("decision", BeadsIssueType.DECISION),
        ("molecule", BeadsIssueType.MOLECULE),
        ("gate", BeadsIssueType.GATE),
        ("event", BeadsIssueType.EVENT),
        ("message", BeadsIssueType.MESSAGE),
        ("merge-request", BeadsIssueType.MERGE_REQUEST),
    ],
)
def test_type_string_coerces_to_enum(raw_type: str, expected: BeadsIssueType) -> None:
    """All BeadsIssueType string values are coerced to the matching enum member."""
    data: dict[str, object] = {"id": "bd-a3f8", "title": "t", "status": "open", "type": raw_type, "priority": 0}
    assert parse_issue(data).type == expected


@pytest.mark.unit
@pytest.mark.parametrize(
    ("raw_priority", "expected"),
    [(0, BeadsPriority.P0), (1, BeadsPriority.P1), (2, BeadsPriority.P2), (3, BeadsPriority.P3), (4, BeadsPriority.P4)],
)
def test_priority_int_coerces_to_enum(raw_priority: int, expected: BeadsPriority) -> None:
    """All BeadsPriority integer values are coerced to the matching enum member."""
    data: dict[str, object] = {
        "id": "bd-a3f8",
        "title": "t",
        "status": "open",
        "type": "task",
        "priority": raw_priority,
    }
    assert parse_issue(data).priority == expected


# ---------------------------------------------------------------------------
# Validation errors — invalid inputs
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_parse_issue_rejects_invalid_id_pattern() -> None:
    """parse_issue raises ValidationError when id does not match the beads nanoid pattern."""
    data: dict[str, object] = {
        "id": "INVALID_ID_ALL_CAPS",
        "title": "t",
        "status": "open",
        "type": "task",
        "priority": 2,
    }
    with pytest.raises(ValidationError):
        parse_issue(data)


@pytest.mark.unit
def test_parse_issue_rejects_missing_required_field() -> None:
    """parse_issue raises ValidationError when title is absent."""
    data: dict[str, object] = {"id": "bd-a3f8", "status": "open", "type": "task", "priority": 2}
    with pytest.raises(ValidationError):
        parse_issue(data)


# ---------------------------------------------------------------------------
# Fixture-based list and status parsing
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_parse_issue_list_returns_two_items_from_fixture() -> None:
    """parse_issue_list parses a list of two issues from bd_list_epic_children."""
    data = _load_json("bd_list_epic_children.json")
    issues = parse_issue_list(data)

    assert len(issues) == 2
    assert issues[0].id == "bd-task1"
    assert issues[1].status == BeadsStatus.IN_PROGRESS


@pytest.mark.unit
def test_parse_ready_list_from_fixture() -> None:
    """parse_ready_list parses the ready issue list from bd_ready_parent."""
    data = _load_json("bd_ready_parent.json")
    issues = parse_ready_list(data)

    assert len(issues) == 1
    assert issues[0].id == "bd-epicX"
    assert issues[0].type == BeadsIssueType.EPIC


@pytest.mark.unit
def test_parse_issue_stores_metadata_field() -> None:
    """parse_issue preserves the metadata dict from bd_update_metadata."""
    data = _load_json("bd_update_metadata.json")
    issue = parse_issue(data)

    assert issue.metadata is not None
    assert "dh.artifacts" in issue.metadata


@pytest.mark.unit
def test_parse_issue_closed_status_and_timestamp_from_fixture() -> None:
    """parse_issue captures closed status and closed_at from bd_close_success."""
    data = _load_json("bd_close_success.json")
    issue = parse_issue(data)

    assert issue.status == BeadsStatus.CLOSED
    assert issue.closed_at == "2026-01-15T14:00:00Z"


@pytest.mark.unit
def test_parse_issue_in_progress_with_assignee_from_fixture() -> None:
    """parse_issue captures in_progress status and assignee from bd_claim_success."""
    data = _load_json("bd_claim_success.json")
    issue = parse_issue(data)

    assert issue.status == BeadsStatus.IN_PROGRESS
    assert issue.assignee == "jamie"


@pytest.mark.unit
def test_parse_issue_epic_type_from_fixture() -> None:
    """parse_issue parses epic type from bd_create_epic_success."""
    data = _load_json("bd_create_epic_success.json")
    issue = parse_issue(data)

    assert issue.type == BeadsIssueType.EPIC
    assert issue.id == "bd-epicX"


@pytest.mark.unit
def test_parse_issue_task_type_from_fixture() -> None:
    """parse_issue parses task type from bd_create_task_success."""
    data = _load_json("bd_create_task_success.json")
    issue = parse_issue(data)

    assert issue.type == BeadsIssueType.TASK
    assert issue.id == "bd-task1"


# ---------------------------------------------------------------------------
# Dependency list parsing
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_parse_dependency_list_inline_valid() -> None:
    """parse_dependency_list accepts a list of dependency dicts with optional fields."""
    data: list[object] = [
        {"id": "bd-f7ab", "title": "Dependency A", "status": "open"},
        {"id": "bd-e1c2"},  # title and status are optional
    ]
    deps = parse_dependency_list(data)

    assert len(deps) == 2
    assert deps[0].id == "bd-f7ab"
    assert deps[0].status == BeadsStatus.OPEN
    assert deps[1].title is None
    assert deps[1].status is None


@pytest.mark.unit
def test_parse_dependency_list_empty_list() -> None:
    """parse_dependency_list accepts an empty list and returns an empty list."""
    assert parse_dependency_list([]) == []


# ---------------------------------------------------------------------------
# BeadsDependencyRaw — direct model validation
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_beads_dependency_raw_id_only() -> None:
    """BeadsDependencyRaw accepts id as the sole field."""
    dep = BeadsDependencyRaw.model_validate({"id": "bd-a3f8"})
    assert dep.id == "bd-a3f8"
    assert dep.title is None
    assert dep.status is None


# ---------------------------------------------------------------------------
# BeadsCommentRaw — direct model validation
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_beads_comment_raw_minimal_fields() -> None:
    """BeadsCommentRaw accepts id and body as the minimum required fields."""
    comment = BeadsCommentRaw.model_validate({"id": "c001", "body": "LGTM"})
    assert comment.id == "c001"
    assert comment.body == "LGTM"
    assert comment.author is None


@pytest.mark.unit
def test_beads_comment_raw_all_fields() -> None:
    """BeadsCommentRaw stores author and created_at when present."""
    comment = BeadsCommentRaw.model_validate({
        "id": "c002",
        "body": "Approved",
        "author": "jamie",
        "created_at": "2026-01-15T10:00:00Z",
    })
    assert comment.author == "jamie"
    assert comment.created_at == "2026-01-15T10:00:00Z"


# ---------------------------------------------------------------------------
# BeadsLabelRaw — direct model validation
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_beads_label_raw_name_only() -> None:
    """BeadsLabelRaw accepts a bare label name with no color or description."""
    label = BeadsLabelRaw.model_validate({"name": "status:open"})
    assert label.name == "status:open"
    assert label.color is None
    assert label.description is None


@pytest.mark.unit
def test_beads_label_raw_with_color_and_description() -> None:
    """BeadsLabelRaw stores color and description when the bd output includes them."""
    label = BeadsLabelRaw.model_validate({"name": "priority:2", "color": "#00ff00", "description": "Medium priority"})
    assert label.color == "#00ff00"
    assert label.description == "Medium priority"


# ---------------------------------------------------------------------------
# BeadsIssueRaw — model type is accessible and usable directly
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_beads_issue_raw_model_validate() -> None:
    """BeadsIssueRaw.model_validate is the underlying mechanism for parse_issue."""
    data: dict[str, object] = {
        "id": "bd-a3f8",
        "title": "Direct validate",
        "status": "open",
        "type": "chore",
        "priority": 3,
    }
    issue = BeadsIssueRaw.model_validate(data)
    assert issue.type == BeadsIssueType.CHORE
    assert issue.priority == BeadsPriority.P3


# ---------------------------------------------------------------------------
# parse_show_issue — list-or-dict normalisation for bd show output
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_parse_show_issue_accepts_plain_dict() -> None:
    """parse_show_issue handles a plain dict — the historic mock-test shape."""
    data: dict[str, object] = {"id": "bd-a3f8", "title": "t", "status": "open", "type": "task", "priority": 2}
    issue = parse_show_issue(data)
    assert issue.id == "bd-a3f8"


@pytest.mark.unit
def test_parse_show_issue_unwraps_single_element_list() -> None:
    """parse_show_issue unwraps [dict] returned by bd show --json in production."""
    inner: dict[str, object] = {"id": "bd-a3f8", "title": "t", "status": "open", "type": "task", "priority": 2}
    issue = parse_show_issue([inner])
    assert issue.id == "bd-a3f8"


@pytest.mark.unit
def test_parse_show_issue_raises_on_empty_list() -> None:
    """parse_show_issue raises ValueError when bd show returns an empty array."""
    with pytest.raises(ValueError, match="empty list"):
        parse_show_issue([])


@pytest.mark.unit
def test_parse_show_issue_list_result_equals_dict_result() -> None:
    """Parsing [dict] and dict produce identical BeadsIssueRaw instances."""
    inner: dict[str, object] = {"id": "bd-a3f8", "title": "t", "status": "open", "type": "task", "priority": 2}
    from_list = parse_show_issue([inner])
    from_dict = parse_show_issue(inner)
    assert from_list == from_dict


@pytest.mark.unit
def test_parse_show_issue_propagates_validation_error_from_invalid_dict() -> None:
    """parse_show_issue raises ValidationError when the unwrapped dict is malformed."""
    invalid: dict[str, object] = {"id": "INVALID_ID", "title": "t", "status": "open", "type": "task", "priority": 2}
    with pytest.raises(ValidationError):
        parse_show_issue(invalid)


# ---------------------------------------------------------------------------
# bd CLI 1.0.4 compatibility — issue_type / owner field aliases
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_parse_issue_accepts_issue_type_key() -> None:
    """parse_issue accepts the bd 1.0.4 'issue_type' JSON key in place of 'type'.

    bd CLI 1.0.4 renamed the field from 'type' to 'issue_type'.
    AliasChoices("type", "issue_type") must accept both names.

    SOURCE: bd CLI 1.0.4 live output (verified 2026-05-29).
    """
    data: dict[str, object] = {
        "id": "cs-h0l",
        "title": "Test issue",
        "status": "open",
        "priority": 2,
        "issue_type": "task",
    }
    issue = parse_issue(data)
    assert issue.type == BeadsIssueType.TASK


@pytest.mark.unit
def test_parse_issue_accepts_owner_as_assignee() -> None:
    """parse_issue maps the bd 1.0.4 'owner' JSON key to the assignee field.

    bd CLI 1.0.4 uses 'owner' where the model field is 'assignee'.
    AliasChoices("assignee", "owner") must accept both names without data loss.

    SOURCE: bd CLI 1.0.4 live output (verified 2026-05-29).
    """
    data: dict[str, object] = {
        "id": "cs-9ds",
        "title": "field-check",
        "status": "open",
        "priority": 2,
        "issue_type": "story",
        "owner": "jamie@bitflight.io",
    }
    issue = parse_issue(data)
    assert issue.assignee == "jamie@bitflight.io"


@pytest.mark.unit
def test_parse_issue_list_from_bd_v1_0_4_fixture() -> None:
    """parse_issue_list parses real bd 1.0.4 output with issue_type and owner keys.

    Uses the bd_list_v1_0_4.json fixture captured from bd CLI 1.0.4.
    """
    data = _load_json("bd_list_v1_0_4.json")
    issues = parse_issue_list(data)

    assert len(issues) == 2
    assert issues[0].type == BeadsIssueType.TASK
    assert issues[0].assignee is None
    assert issues[1].type == BeadsIssueType.STORY
    assert issues[1].assignee == "jamie@bitflight.io"


@pytest.mark.unit
def test_parse_show_issue_from_bd_v1_0_4_fixture() -> None:
    """parse_show_issue unwraps and parses real bd 1.0.4 show output.

    Uses the bd_show_v1_0_4.json fixture captured from bd CLI 1.0.4.
    bd show wraps the response in a single-element list.
    """
    data = _load_json("bd_show_v1_0_4.json")
    issue = parse_show_issue(data)

    assert issue.id == "cs-9ds"
    assert issue.type == BeadsIssueType.STORY
    assert issue.assignee == "jamie@bitflight.io"


@pytest.mark.unit
@pytest.mark.parametrize(
    ("raw_type", "expected"),
    [("spike", BeadsIssueType.SPIKE), ("story", BeadsIssueType.STORY), ("milestone", BeadsIssueType.MILESTONE)],
)
def test_bd_1_0_4_issue_types_coerce_to_enum(raw_type: str, expected: BeadsIssueType) -> None:
    """bd 1.0.4 built-in issue types spike/story/milestone coerce to enum members.

    These types exist in bd CLI 1.0.4 but were absent from the original enum.

    SOURCE: ``bd issue types`` output, bd CLI 1.0.4 (verified 2026-05-29).
    """
    data: dict[str, object] = {"id": "cs-abc", "title": "t", "status": "open", "issue_type": raw_type, "priority": 2}
    assert parse_issue(data).type == expected


# ---------------------------------------------------------------------------
# Hypothesis — round-trip property test for all enum combinations
# ---------------------------------------------------------------------------


@pytest.mark.critical
@given(
    id_=st.from_regex(r"[a-z][a-z0-9]{1,6}-[A-Za-z0-9]{1,8}", fullmatch=True),
    title=st.text(min_size=1, max_size=60, alphabet=st.characters(min_codepoint=32, max_codepoint=126)),
    status=st.sampled_from(list(BeadsStatus)),
    type_=st.sampled_from(list(BeadsIssueType)),
    priority=st.sampled_from(list(BeadsPriority)),
)
@settings(max_examples=50)
def test_round_trip_parse_issue_all_enum_values(
    id_: str, title: str, status: BeadsStatus, type_: BeadsIssueType, priority: BeadsPriority
) -> None:
    """BeadsIssueRaw survives a round-trip through parse_issue for all enum combinations."""
    raw: dict[str, object] = {
        "id": id_,
        "title": title,
        "status": str(status),
        "type": str(type_),
        "priority": int(priority),
    }
    issue = parse_issue(raw)

    assert issue.id == id_
    assert issue.title == title
    assert issue.status == status
    assert issue.type == type_
    assert issue.priority == priority
