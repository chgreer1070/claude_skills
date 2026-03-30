"""Tests for backlog_core.github_sync — render, parse, and merge operations."""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure backlog_core is importable from the plugin root
_PLUGIN_ROOT = Path(__file__).parent.parent
if str(_PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(_PLUGIN_ROOT))

from backlog_core.github_sync import merge_item, parse_issue_body, render_issue_body
from backlog_core.models import BacklogItem, Entry, GroomedData, Section

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_item(
    *,
    title: str = "Test Item",
    description: str = "A test description.",
    priority: str = "P1",
    item_type: str = "Feature",
    status: str = "open",
    added: str = "2026-01-01",
    sections: dict | None = None,
) -> BacklogItem:
    """Build a BacklogItem for use in tests."""
    return BacklogItem(
        title=title,
        description=description,
        priority=priority,
        item_type=item_type,
        status=status,
        added=added,
        sections=sections or {},
    )


# ---------------------------------------------------------------------------
# render_issue_body — metadata block
# ---------------------------------------------------------------------------


class TestRenderIssueBodyMetadata:
    """render_issue_body: metadata HTML comment block."""

    def test_render_metadata_comment_present(self) -> None:
        """render_issue_body output contains the backlog-metadata comment block."""
        item = _make_item(priority="P0", item_type="Bug", status="open", added="2026-03-01")
        body = render_issue_body(item)
        assert "<!-- backlog-metadata:" in body
        assert "-->" in body

    def test_render_metadata_priority_field(self) -> None:
        """render_issue_body embeds priority in the metadata comment."""
        item = _make_item(priority="P0")
        body = render_issue_body(item)
        assert "priority: P0" in body

    def test_render_metadata_type_field(self) -> None:
        """render_issue_body embeds type in the metadata comment."""
        item = _make_item(item_type="Bug")
        body = render_issue_body(item)
        assert "type: Bug" in body

    def test_render_metadata_status_field(self) -> None:
        """render_issue_body embeds status in the metadata comment."""
        item = _make_item(status="in-progress")
        body = render_issue_body(item)
        assert "status: in-progress" in body

    def test_render_metadata_added_field(self) -> None:
        """render_issue_body embeds added date in the metadata comment."""
        item = _make_item(added="2026-03-15")
        body = render_issue_body(item)
        assert "added: 2026-03-15" in body


# ---------------------------------------------------------------------------
# render_issue_body — groomed section
# ---------------------------------------------------------------------------


class TestRenderIssueBodyGroomed:
    """render_issue_body: GroomedData section rendering."""

    def test_render_groomed_heading(self) -> None:
        """render_issue_body renders GroomedData with ## Groomed (date) heading."""
        groomed = GroomedData(date="2026-03-01", subsections={"Priority": "High"})
        item = _make_item(sections={"groomed": groomed})
        body = render_issue_body(item)
        assert "## Groomed (2026-03-01)" in body

    def test_render_groomed_subsection_as_h3(self) -> None:
        """render_issue_body renders GroomedData subsections as ### headings."""
        groomed = GroomedData(date="2026-03-01", subsections={"Priority": "High", "Impact": "Major"})
        item = _make_item(sections={"groomed": groomed})
        body = render_issue_body(item)
        assert "### Priority" in body
        assert "### Impact" in body

    def test_render_groomed_subsection_content(self) -> None:
        """render_issue_body includes subsection content under each ### heading."""
        groomed = GroomedData(date="2026-03-01", subsections={"Priority": "Critical path item."})
        item = _make_item(sections={"groomed": groomed})
        body = render_issue_body(item)
        assert "Critical path item." in body

    def test_render_groomed_canonical_order(self) -> None:
        """render_issue_body emits canonical subsections before extra ones."""
        groomed = GroomedData(
            date="2026-03-01",
            subsections={
                "Zebra": "last alphabetically",
                "Priority": "first canonically",
                "Impact": "second canonically",
            },
        )
        item = _make_item(sections={"groomed": groomed})
        body = render_issue_body(item)
        priority_pos = body.index("### Priority")
        impact_pos = body.index("### Impact")
        zebra_pos = body.index("### Zebra")
        assert priority_pos < impact_pos < zebra_pos


# ---------------------------------------------------------------------------
# render_issue_body — struck entries
# ---------------------------------------------------------------------------


class TestRenderIssueBodyStruckEntries:
    """render_issue_body: struck entry rendering."""

    def test_render_struck_entry_details_wrapper(self) -> None:
        """render_issue_body wraps struck entries in <details><summary> block."""
        struck_entry = Entry(
            id="2026-01-01T10:00:00Z",
            content="old content",
            struck=True,
            struck_at="2026-01-02T10:00:00Z",
            struck_reason="superseded",
        )
        section = Section(entries=[struck_entry])
        item = _make_item(sections={"fact_check": section})
        body = render_issue_body(item)
        assert "<details>" in body
        assert "<summary>" in body
        assert "struck: 2026-01-02T10:00:00Z — superseded" in body

    def test_render_struck_entry_summary_format(self) -> None:
        """render_issue_body struck summary contains struck_at and struck_reason."""
        struck_entry = Entry(
            id="2026-01-01T10:00:00Z",
            content="fact content",
            struck=True,
            struck_at="2026-01-05T08:00:00Z",
            struck_reason="outdated",
        )
        section = Section(entries=[struck_entry])
        item = _make_item(sections={"rt_ica": section})
        body = render_issue_body(item)
        assert "struck: 2026-01-05T08:00:00Z — outdated" in body

    def test_render_active_entry_no_details_wrapper(self) -> None:
        """render_issue_body active entries are NOT wrapped in <details>."""
        active_entry = Entry(id="2026-01-01T10:00:00Z", content="current analysis")
        section = Section(entries=[active_entry])
        item = _make_item(sections={"fact_check": section})
        body = render_issue_body(item)
        assert "<details>" not in body
        assert "current analysis" in body


# ---------------------------------------------------------------------------
# parse_issue_body — round-trip
# ---------------------------------------------------------------------------


class TestParseIssueBodyRoundTrip:
    """parse_issue_body(render_issue_body(item)) round-trips correctly."""

    def test_round_trip_entry_count(self) -> None:
        """Round-trip preserves entry count in entry-bearing sections."""
        entries = [
            Entry(id="2026-01-01T10:00:00Z", content="entry one"),
            Entry(id="2026-01-02T10:00:00Z", content="entry two"),
        ]
        section = Section(entries=entries)
        item = _make_item(sections={"fact_check": section})
        parsed = parse_issue_body(render_issue_body(item))
        parsed_sec = parsed.sections.get("fact_check")
        assert isinstance(parsed_sec, Section)
        assert len(parsed_sec.entries) == 2

    def test_round_trip_entry_ids(self) -> None:
        """Round-trip preserves entry ids."""
        entries = [Entry(id="2026-01-01T10:00:00Z", content="alpha"), Entry(id="2026-01-03T12:00:00Z", content="beta")]
        section = Section(entries=entries)
        item = _make_item(sections={"rt_ica": section})
        parsed = parse_issue_body(render_issue_body(item))
        parsed_sec = parsed.sections.get("rt_ica")
        assert isinstance(parsed_sec, Section)
        parsed_ids = {e.id for e in parsed_sec.entries}
        assert "2026-01-01T10:00:00Z" in parsed_ids
        assert "2026-01-03T12:00:00Z" in parsed_ids

    def test_round_trip_groomed_subsection_keys(self) -> None:
        """Round-trip preserves GroomedData subsection keys."""
        groomed = GroomedData(
            date="2026-03-01", subsections={"Priority": "High", "Impact": "Major", "Benefits": "Efficiency"}
        )
        item = _make_item(sections={"groomed": groomed})
        parsed = parse_issue_body(render_issue_body(item))
        parsed_groomed = parsed.sections.get("groomed")
        assert isinstance(parsed_groomed, GroomedData)
        assert set(parsed_groomed.subsections.keys()) == {"Priority", "Impact", "Benefits"}

    def test_round_trip_metadata_priority(self) -> None:
        """Round-trip preserves priority from metadata comment."""
        item = _make_item(priority="P0", item_type="Bug", status="open", added="2026-01-10")
        parsed = parse_issue_body(render_issue_body(item))
        assert parsed.priority == "P0"

    def test_round_trip_metadata_type(self) -> None:
        """Round-trip preserves item type from metadata comment."""
        item = _make_item(item_type="Bug")
        parsed = parse_issue_body(render_issue_body(item))
        assert parsed.item_type == "Bug"

    def test_round_trip_description(self) -> None:
        """Round-trip preserves description text."""
        item = _make_item(description="Detailed description here.")
        parsed = parse_issue_body(render_issue_body(item))
        assert parsed.description == "Detailed description here."


# ---------------------------------------------------------------------------
# merge_item — struck wins over active
# ---------------------------------------------------------------------------


class TestMergeItemStruckWins:
    """merge_item: struck entry wins over active entry for the same id."""

    def test_local_struck_remote_active_keeps_struck(self) -> None:
        """When local has struck and remote has same id active, merged is struck."""
        eid = "2026-01-01T10:00:00Z"
        local_entries = [
            Entry(id=eid, content="fact", struck=True, struck_at="2026-01-02T00:00:00Z", struck_reason="wrong")
        ]
        remote_entries = [Entry(id=eid, content="fact")]
        local = _make_item(sections={"fact_check": Section(entries=local_entries)})
        remote = _make_item(sections={"fact_check": Section(entries=remote_entries)})
        merged = merge_item(local, remote)
        merged_sec = merged.sections.get("fact_check")
        assert isinstance(merged_sec, Section)
        assert len(merged_sec.entries) == 1
        assert merged_sec.entries[0].struck is True

    def test_remote_struck_local_active_keeps_struck(self) -> None:
        """When remote has struck and local has same id active, merged is struck."""
        eid = "2026-01-05T08:00:00Z"
        local_entries = [Entry(id=eid, content="claim")]
        remote_entries = [
            Entry(id=eid, content="claim", struck=True, struck_at="2026-01-06T00:00:00Z", struck_reason="debunked")
        ]
        local = _make_item(sections={"fact_check": Section(entries=local_entries)})
        remote = _make_item(sections={"fact_check": Section(entries=remote_entries)})
        merged = merge_item(local, remote)
        merged_sec = merged.sections.get("fact_check")
        assert isinstance(merged_sec, Section)
        assert merged_sec.entries[0].struck is True


# ---------------------------------------------------------------------------
# merge_item — unique remote entries preserved
# ---------------------------------------------------------------------------


class TestMergeItemUniqueEntries:
    """merge_item: entries unique to remote appear in merged result."""

    def test_remote_only_entry_preserved(self) -> None:
        """Entry present only in remote is included in merged result."""
        local_entries = [Entry(id="2026-01-01T10:00:00Z", content="local fact")]
        remote_entries = [
            Entry(id="2026-01-01T10:00:00Z", content="local fact"),
            Entry(id="2026-01-02T10:00:00Z", content="remote-only fact"),
        ]
        local = _make_item(sections={"fact_check": Section(entries=local_entries)})
        remote = _make_item(sections={"fact_check": Section(entries=remote_entries)})
        merged = merge_item(local, remote)
        merged_sec = merged.sections.get("fact_check")
        assert isinstance(merged_sec, Section)
        assert len(merged_sec.entries) == 2
        entry_ids = {e.id for e in merged_sec.entries}
        assert "2026-01-02T10:00:00Z" in entry_ids

    def test_local_only_entry_preserved(self) -> None:
        """Entry present only in local is included in merged result."""
        local_entries = [
            Entry(id="2026-01-01T10:00:00Z", content="local only"),
            Entry(id="2026-01-03T10:00:00Z", content="shared"),
        ]
        remote_entries = [Entry(id="2026-01-03T10:00:00Z", content="shared")]
        local = _make_item(sections={"rt_ica": Section(entries=local_entries)})
        remote = _make_item(sections={"rt_ica": Section(entries=remote_entries)})
        merged = merge_item(local, remote)
        merged_sec = merged.sections.get("rt_ica")
        assert isinstance(merged_sec, Section)
        assert len(merged_sec.entries) == 2


# ---------------------------------------------------------------------------
# merge_item — groomed subsection content
# ---------------------------------------------------------------------------


class TestMergeItemGroomed:
    """merge_item: groomed subsection with longer remote content is kept."""

    def test_longer_remote_subsection_wins(self) -> None:
        """Remote groomed subsection content replaces local when it is longer."""
        local_groomed = GroomedData(date="2026-03-01", subsections={"Priority": "High"})
        remote_groomed = GroomedData(
            date="2026-03-01", subsections={"Priority": "High — needs immediate attention due to customer SLA impact."}
        )
        local = _make_item(sections={"groomed": local_groomed})
        remote = _make_item(sections={"groomed": remote_groomed})
        merged = merge_item(local, remote)
        merged_groomed = merged.sections.get("groomed")
        assert isinstance(merged_groomed, GroomedData)
        assert "SLA impact" in merged_groomed.subsections.get("Priority", "")

    def test_longer_local_subsection_kept(self) -> None:
        """Local groomed subsection content is kept when it is longer than remote."""
        local_groomed = GroomedData(
            date="2026-03-01",
            subsections={"Impact": "Very significant — affects all downstream pipelines and reporting."},
        )
        remote_groomed = GroomedData(date="2026-03-01", subsections={"Impact": "Significant."})
        local = _make_item(sections={"groomed": local_groomed})
        remote = _make_item(sections={"groomed": remote_groomed})
        merged = merge_item(local, remote)
        merged_groomed = merged.sections.get("groomed")
        assert isinstance(merged_groomed, GroomedData)
        impact = merged_groomed.subsections.get("Impact", "")
        assert "downstream pipelines" in impact

    def test_remote_only_subsection_added(self) -> None:
        """Subsection present only in remote is included in merged result."""
        local_groomed = GroomedData(date="2026-03-01", subsections={"Priority": "High"})
        remote_groomed = GroomedData(
            date="2026-03-01", subsections={"Priority": "High", "Impact": "Remote-only impact."}
        )
        local = _make_item(sections={"groomed": local_groomed})
        remote = _make_item(sections={"groomed": remote_groomed})
        merged = merge_item(local, remote)
        merged_groomed = merged.sections.get("groomed")
        assert isinstance(merged_groomed, GroomedData)
        assert "Impact" in merged_groomed.subsections


# ---------------------------------------------------------------------------
# Import / circular-dependency check
# ---------------------------------------------------------------------------


class TestImportNoCycles:
    """github_sync.py imports do not create circular dependencies."""

    def test_importable(self) -> None:
        """github_sync module is importable without errors."""
        import backlog_core.github_sync  # noqa: F401

    def test_public_functions_importable(self) -> None:
        """All three public functions are importable from backlog_core.github_sync."""
        from backlog_core.github_sync import merge_item, parse_issue_body, render_issue_body

        assert callable(render_issue_body)
        assert callable(parse_issue_body)
        assert callable(merge_item)

    def test_models_not_imported_from_github_sync(self) -> None:
        """models.py does not import from github_sync (no cycle)."""
        import sys

        # Reload models to inspect its import graph
        models_mod = sys.modules.get("backlog_core.models")
        if models_mod is not None:
            source_file = getattr(models_mod, "__file__", "") or ""
            content = Path(source_file).read_text(encoding="utf-8") if source_file else ""
            assert "github_sync" not in content, "models.py must not import github_sync"
