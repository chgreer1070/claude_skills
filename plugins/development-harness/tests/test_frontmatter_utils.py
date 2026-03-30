"""Tests for backlog_core/frontmatter_utils.py — file I/O via python-frontmatter + ruamel.yaml."""

from __future__ import annotations

from typing import TYPE_CHECKING

import frontmatter as fm_lib
from backlog_core.frontmatter_utils import dump_frontmatter, load_frontmatter, loads_frontmatter, update_field

if TYPE_CHECKING:
    from pathlib import Path

# ---------------------------------------------------------------------------
# Shared fixture
# ---------------------------------------------------------------------------

_FRONTMATTER_MD = """\
---
name: Test Item
status: open
priority: P1
---
Body content here.
"""


# ---------------------------------------------------------------------------
# load_frontmatter (line 54)
# ---------------------------------------------------------------------------


class TestLoadFrontmatter:
    """Tests for load_frontmatter(path) -> frontmatter.Post."""

    def test_load_frontmatter_reads_metadata_from_file(self, tmp_path: Path) -> None:
        """Verify load_frontmatter reads a file and returns metadata dict.

        Tests: load_frontmatter file read path (line 54)
        How: Write a .md file with frontmatter; load; verify metadata
        Why: load_frontmatter is the file-path variant — distinct from loads_frontmatter
        """
        # Arrange
        md_file = tmp_path / "item.md"
        md_file.write_text(_FRONTMATTER_MD, encoding="utf-8")

        # Act
        post = load_frontmatter(md_file)

        # Assert
        assert post.metadata.get("name") == "Test Item"
        assert post.metadata.get("status") == "open"

    def test_load_frontmatter_reads_body_content(self, tmp_path: Path) -> None:
        md_file = tmp_path / "item.md"
        md_file.write_text(_FRONTMATTER_MD, encoding="utf-8")

        post = load_frontmatter(md_file)

        assert "Body content here." in post.content

    def test_load_frontmatter_accepts_string_path(self, tmp_path: Path) -> None:
        md_file = tmp_path / "item.md"
        md_file.write_text(_FRONTMATTER_MD, encoding="utf-8")

        # Path as string (not Path object)
        post = load_frontmatter(str(md_file))

        assert post.metadata.get("name") == "Test Item"


# ---------------------------------------------------------------------------
# dump_frontmatter (line 129)
# ---------------------------------------------------------------------------


class TestDumpFrontmatter:
    """Tests for dump_frontmatter(post) -> str."""

    def test_dump_frontmatter_produces_yaml_delimiters(self) -> None:
        """Verify dump_frontmatter serialises a Post to a string with --- delimiters.

        Tests: dump_frontmatter body (line 129)
        How: Create a Post; dump to string; verify --- delimiters present
        Why: Callers depend on dump_frontmatter producing valid frontmatter markdown
        """
        # Arrange
        post = fm_lib.Post("Body text", name="My Item", status="open")

        # Act
        result = dump_frontmatter(post)

        # Assert
        assert result.startswith("---")
        assert "---" in result[3:]

    def test_dump_frontmatter_includes_metadata_keys(self) -> None:
        post = fm_lib.Post("", name="My Item", priority="P0")

        result = dump_frontmatter(post)

        assert "name" in result
        assert "My Item" in result
        assert "P0" in result

    def test_dump_frontmatter_includes_body_content(self) -> None:
        post = fm_lib.Post("Body text here", name="Item")

        result = dump_frontmatter(post)

        assert "Body text here" in result


# ---------------------------------------------------------------------------
# update_field (lines 140-142)
# ---------------------------------------------------------------------------


class TestUpdateField:
    """Tests for update_field(path, key, value) -> None."""

    def test_update_field_modifies_existing_key(self, tmp_path: Path) -> None:
        """Verify update_field loads, sets a key, and writes back.

        Tests: update_field body (lines 140-142)
        How: Write a .md file; call update_field to change status; re-read; verify
        Why: update_field is the convenience helper for single-field updates
        """
        # Arrange
        md_file = tmp_path / "item.md"
        md_file.write_text(_FRONTMATTER_MD, encoding="utf-8")

        # Act
        update_field(md_file, "status", "done")

        # Assert
        post = loads_frontmatter(md_file.read_text(encoding="utf-8"))
        assert post.metadata.get("status") == "done"

    def test_update_field_adds_new_key(self, tmp_path: Path) -> None:
        # Arrange
        md_file = tmp_path / "item.md"
        md_file.write_text(_FRONTMATTER_MD, encoding="utf-8")

        # Act
        update_field(md_file, "issue", "#99")

        # Assert
        post = loads_frontmatter(md_file.read_text(encoding="utf-8"))
        assert post.metadata.get("issue") == "#99"

    def test_update_field_preserves_other_keys(self, tmp_path: Path) -> None:
        md_file = tmp_path / "item.md"
        md_file.write_text(_FRONTMATTER_MD, encoding="utf-8")

        update_field(md_file, "status", "done")

        post = loads_frontmatter(md_file.read_text(encoding="utf-8"))
        # Other keys must be preserved
        assert post.metadata.get("name") == "Test Item"
        assert post.metadata.get("priority") == "P1"
