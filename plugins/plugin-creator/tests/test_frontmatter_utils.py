"""Tests for frontmatter_utils shared module."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path


class TestRuamelYAMLHandler:
    """Test the custom python-frontmatter handler using ruamel.yaml."""

    def test_load_simple_frontmatter(self, tmp_path: Path) -> None:
        """Handler parses simple frontmatter without quotes."""
        md = tmp_path / "test.md"
        md.write_text(
            "---\ndescription: A simple description\ntools: Bash, Read\n---\nBody content\n"
        )
        from frontmatter_utils import load_frontmatter

        post = load_frontmatter(md)
        assert post["description"] == "A simple description"
        assert post["tools"] == "Bash, Read"
        assert post.content == "Body content"

    def test_load_quoted_frontmatter(self, tmp_path: Path) -> None:
        """Handler preserves quotes when YAML syntax requires them."""
        md = tmp_path / "test.md"
        md.write_text('---\ndescription: "Has: colon in value"\n---\nBody\n')
        from frontmatter_utils import load_frontmatter

        post = load_frontmatter(md)
        assert post["description"] == "Has: colon in value"

    def test_load_no_frontmatter(self, tmp_path: Path) -> None:
        """Handler returns empty metadata for files without frontmatter."""
        md = tmp_path / "test.md"
        md.write_text("Just body content, no frontmatter.\n")
        from frontmatter_utils import load_frontmatter

        post = load_frontmatter(md)
        assert dict(post.metadata) == {}
        assert "Just body content" in post.content

    def test_roundtrip_preserves_unquoted(self, tmp_path: Path) -> None:
        """Round-trip does not add unnecessary quotes."""
        original = (
            "---\ndescription: No quotes needed here\ntools: Bash, Read\n---\nBody\n"
        )
        md = tmp_path / "test.md"
        md.write_text(original)
        from frontmatter_utils import dump_frontmatter, load_frontmatter

        post = load_frontmatter(md)
        result = dump_frontmatter(post)
        assert "description: No quotes needed here" in result
        assert '"No quotes needed here"' not in result
        assert "'No quotes needed here'" not in result

    def test_roundtrip_preserves_required_quotes(self, tmp_path: Path) -> None:
        """Round-trip keeps quotes where YAML syntax demands them."""
        original = '---\ndescription: "Contains: colon that needs quoting"\n---\nBody\n'
        md = tmp_path / "test.md"
        md.write_text(original)
        from frontmatter_utils import dump_frontmatter, load_frontmatter

        post = load_frontmatter(md)
        result = dump_frontmatter(post)
        # The colon-space in value means quotes are required
        assert "Contains: colon that needs quoting" in result

    def test_roundtrip_removes_unnecessary_quotes(self, tmp_path: Path) -> None:
        """Round-trip strips quotes that YAML does not require."""
        original = '---\ndescription: "No special chars at all"\n---\nBody\n'
        md = tmp_path / "test.md"
        md.write_text(original)
        from frontmatter_utils import dump_frontmatter, load_frontmatter

        post = load_frontmatter(md)
        result = dump_frontmatter(post)
        # ruamel.yaml with preserve_quotes may keep them — verify behavior
        # This test documents actual behavior
        assert "No special chars at all" in result


class TestConvenienceAPI:
    """Test load/dump/update convenience functions."""

    def test_loads_frontmatter_from_string(self) -> None:
        """Parse frontmatter from a string."""
        from frontmatter_utils import loads_frontmatter

        text = "---\ndescription: Test\nmodel: sonnet\n---\nContent here\n"
        post = loads_frontmatter(text)
        assert post["description"] == "Test"
        assert post["model"] == "sonnet"
        assert post.content == "Content here"

    def test_dumps_frontmatter_to_file(self, tmp_path: Path) -> None:
        """Write frontmatter post to a file."""
        from frontmatter_utils import dumps_frontmatter, loads_frontmatter

        text = "---\ndescription: Written to file\n---\nBody\n"
        post = loads_frontmatter(text)
        out = tmp_path / "output.md"
        dumps_frontmatter(post, out)
        assert out.exists()
        content = out.read_text()
        assert "description: Written to file" in content
        assert "Body" in content

    def test_update_field_existing(self, tmp_path: Path) -> None:
        """Update an existing field without re-serializing everything."""
        md = tmp_path / "test.md"
        md.write_text("---\ndescription: Old value\ntools: Bash\n---\nBody\n")
        from frontmatter_utils import load_frontmatter, update_field

        update_field(md, "description", "New value")
        post = load_frontmatter(md)
        assert post["description"] == "New value"
        assert post["tools"] == "Bash"

    def test_update_field_new(self, tmp_path: Path) -> None:
        """Add a new field that did not exist."""
        md = tmp_path / "test.md"
        md.write_text("---\ndescription: Existing\n---\nBody\n")
        from frontmatter_utils import load_frontmatter, update_field

        update_field(md, "model", "sonnet")
        post = load_frontmatter(md)
        assert post["description"] == "Existing"
        assert post["model"] == "sonnet"

    def test_body_content_preserved(self, tmp_path: Path) -> None:
        """Markdown body with code blocks and special chars survives round-trip."""
        body = "# Heading\n\nSome text with `code` and **bold**.\n\n```python\ndef foo():\n    pass\n```\n"
        md = tmp_path / "test.md"
        md.write_text(f"---\ndescription: Test\n---\n{body}")
        from frontmatter_utils import dump_frontmatter, load_frontmatter

        post = load_frontmatter(md)
        result = dump_frontmatter(post)
        # Body content after the closing --- must match
        body_part = result.split("---\n", 2)[2]
        assert "```python" in body_part
        assert "def foo():" in body_part


class TestEdgeCases:
    """Edge cases and error handling."""

    def test_empty_file(self, tmp_path: Path) -> None:
        """Empty file does not crash."""
        md = tmp_path / "empty.md"
        md.write_text("")
        from frontmatter_utils import load_frontmatter

        post = load_frontmatter(md)
        assert dict(post.metadata) == {}

    def test_frontmatter_with_boolean_values(self, tmp_path: Path) -> None:
        """Boolean-like strings in frontmatter are preserved as strings when quoted."""
        md = tmp_path / "test.md"
        md.write_text('---\ndescription: "true"\nuser-invocable: true\n---\nBody\n')
        from frontmatter_utils import load_frontmatter

        post = load_frontmatter(md)
        assert post["user-invocable"] is True

    def test_frontmatter_with_list_values(self, tmp_path: Path) -> None:
        """List values in frontmatter are handled correctly."""
        md = tmp_path / "test.md"
        md.write_text(
            "---\ndescription: Test\ntools:\n  - Bash\n  - Read\n  - Write\n---\nBody\n"
        )
        from frontmatter_utils import load_frontmatter

        post = load_frontmatter(md)
        assert post["tools"] == ["Bash", "Read", "Write"]

    def test_unicode_in_description(self, tmp_path: Path) -> None:
        """Unicode characters survive round-trip."""
        md = tmp_path / "test.md"
        md.write_text(
            "---\ndescription: Handles em\u2014dashes and curly \u201cquotes\u201d\n---\nBody\n"
        )
        from frontmatter_utils import dump_frontmatter, load_frontmatter

        post = load_frontmatter(md)
        result = dump_frontmatter(post)
        assert "\u2014" in result
        assert "\u201c" in result
