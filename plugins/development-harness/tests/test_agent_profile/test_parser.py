"""Unit tests for agent_profile.parser module."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from agent_profile.models import AgentMetadata
from agent_profile.parser import parse_agent_file, parse_skill_frontmatter, read_skill_content

if TYPE_CHECKING:
    from pathlib import Path

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _agent_file(tmp_path: Path, name: str, frontmatter: str, body: str = "Body content.") -> Path:
    path = tmp_path / f"{name}.md"
    path.write_text(f"---\n{frontmatter}---\n{body}\n", encoding="utf-8")
    return path


def _skill_dir(tmp_path: Path, name: str, skill_content: str = "Skill body.", frontmatter: str = "") -> Path:
    sdir = tmp_path / name
    sdir.mkdir(parents=True, exist_ok=True)
    skill_md = sdir / "SKILL.md"
    if frontmatter:
        skill_md.write_text(f"---\n{frontmatter}---\n{skill_content}\n", encoding="utf-8")
    else:
        skill_md.write_text(skill_content, encoding="utf-8")
    return sdir


# ---------------------------------------------------------------------------
# parse_agent_file — skills normalization
# ---------------------------------------------------------------------------


class TestParseAgentFileSkillsNormalization:
    def test_yaml_list_skills(self, tmp_path: Path) -> None:
        path = _agent_file(tmp_path, "agent", "name: agent\ndescription: d\nskills:\n  - skill-a\n  - skill-b\n")
        meta, _ = parse_agent_file(path)
        assert meta.skills == ["skill-a", "skill-b"]

    def test_comma_separated_skills(self, tmp_path: Path) -> None:
        path = _agent_file(tmp_path, "agent", "name: agent\ndescription: d\nskills: skill-a, skill-b\n")
        meta, _ = parse_agent_file(path)
        assert meta.skills == ["skill-a", "skill-b"]

    def test_single_skill_string(self, tmp_path: Path) -> None:
        path = _agent_file(tmp_path, "agent", "name: agent\ndescription: d\nskills: skill-a\n")
        meta, _ = parse_agent_file(path)
        assert meta.skills == ["skill-a"]

    def test_no_skills_field_returns_empty_list(self, tmp_path: Path) -> None:
        path = _agent_file(tmp_path, "agent", "name: agent\ndescription: d\n")
        meta, _ = parse_agent_file(path)
        assert meta.skills == []

    def test_skills_strips_whitespace(self, tmp_path: Path) -> None:
        path = _agent_file(tmp_path, "agent", "name: agent\ndescription: d\nskills:  skill-a ,  skill-b \n")
        meta, _ = parse_agent_file(path)
        assert meta.skills == ["skill-a", "skill-b"]


# ---------------------------------------------------------------------------
# parse_agent_file — metadata fields
# ---------------------------------------------------------------------------


class TestParseAgentFileMetadata:
    def test_returns_agent_metadata_instance(self, tmp_path: Path) -> None:
        path = _agent_file(tmp_path, "a", "name: a\ndescription: desc\n")
        meta, _ = parse_agent_file(path)
        assert isinstance(meta, AgentMetadata)

    def test_extracts_name_and_description(self, tmp_path: Path) -> None:
        path = _agent_file(tmp_path, "a", "name: my-agent\ndescription: My description\n")
        meta, _ = parse_agent_file(path)
        assert meta.name == "my-agent"
        assert meta.description == "My description"

    def test_extracts_model_when_present(self, tmp_path: Path) -> None:
        path = _agent_file(tmp_path, "a", "name: a\ndescription: d\nmodel: claude-sonnet-4-6\n")
        meta, _ = parse_agent_file(path)
        assert meta.model == "claude-sonnet-4-6"

    def test_model_is_none_when_absent(self, tmp_path: Path) -> None:
        path = _agent_file(tmp_path, "a", "name: a\ndescription: d\n")
        meta, _ = parse_agent_file(path)
        assert meta.model is None

    def test_extracts_color_when_present(self, tmp_path: Path) -> None:
        path = _agent_file(tmp_path, "a", "name: a\ndescription: d\ncolor: '#FF6B35'\n")
        meta, _ = parse_agent_file(path)
        assert meta.color == "#FF6B35"

    def test_color_is_none_when_absent(self, tmp_path: Path) -> None:
        path = _agent_file(tmp_path, "a", "name: a\ndescription: d\n")
        meta, _ = parse_agent_file(path)
        assert meta.color is None

    def test_returns_body_string(self, tmp_path: Path) -> None:
        path = _agent_file(tmp_path, "a", "name: a\ndescription: d\n", body="The agent body here.")
        _, body = parse_agent_file(path)
        assert "The agent body here." in body

    def test_empty_body_returns_empty_string(self, tmp_path: Path) -> None:
        path = tmp_path / "a.md"
        path.write_text("---\nname: a\ndescription: d\n---\n", encoding="utf-8")
        _, body = parse_agent_file(path)
        assert isinstance(body, str)


# ---------------------------------------------------------------------------
# parse_agent_file — error cases
# ---------------------------------------------------------------------------


class TestParseAgentFileErrors:
    def test_raises_file_not_found_for_missing_file(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            parse_agent_file(tmp_path / "nonexistent.md")

    def test_raises_value_error_for_no_frontmatter(self, tmp_path: Path) -> None:
        path = tmp_path / "no-fm.md"
        path.write_text("Just a body, no frontmatter at all.\n", encoding="utf-8")
        with pytest.raises(ValueError, match="frontmatter"):
            parse_agent_file(path)


# ---------------------------------------------------------------------------
# parse_skill_frontmatter
# ---------------------------------------------------------------------------


class TestParseSkillFrontmatter:
    def test_extracts_skills_list(self, tmp_path: Path) -> None:
        sdir = _skill_dir(tmp_path, "sk", frontmatter="skills:\n  - sub-skill-a\n  - sub-skill-b\n")
        result = parse_skill_frontmatter(sdir / "SKILL.md")
        assert result == ["sub-skill-a", "sub-skill-b"]

    def test_extracts_requires_field(self, tmp_path: Path) -> None:
        sdir = _skill_dir(tmp_path, "sk", frontmatter="requires: sub-skill-a\n")
        result = parse_skill_frontmatter(sdir / "SKILL.md")
        assert result == ["sub-skill-a"]

    def test_skills_takes_precedence_over_requires(self, tmp_path: Path) -> None:
        sdir = _skill_dir(tmp_path, "sk", frontmatter="skills:\n  - skills-field\nrequires: requires-field\n")
        result = parse_skill_frontmatter(sdir / "SKILL.md")
        assert result == ["skills-field"]

    def test_no_frontmatter_returns_empty_list(self, tmp_path: Path) -> None:
        sdir = _skill_dir(tmp_path, "sk", skill_content="Just content, no FM.")
        result = parse_skill_frontmatter(sdir / "SKILL.md")
        assert result == []

    def test_frontmatter_without_skills_field_returns_empty(self, tmp_path: Path) -> None:
        sdir = _skill_dir(tmp_path, "sk", frontmatter="description: A skill\n")
        result = parse_skill_frontmatter(sdir / "SKILL.md")
        assert result == []

    def test_raises_file_not_found_for_missing_skill_md(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            parse_skill_frontmatter(tmp_path / "nonexistent" / "SKILL.md")


# ---------------------------------------------------------------------------
# read_skill_content
# ---------------------------------------------------------------------------


class TestReadSkillContent:
    def test_reads_skill_md_content(self, tmp_path: Path) -> None:
        sdir = _skill_dir(tmp_path, "sk", skill_content="The skill content.")
        content, _ = read_skill_content(sdir)
        assert "The skill content." in content

    def test_returns_empty_references_when_no_references_dir(self, tmp_path: Path) -> None:
        sdir = _skill_dir(tmp_path, "sk")
        _, refs = read_skill_content(sdir)
        assert refs == {}

    def test_reads_reference_files(self, tmp_path: Path) -> None:
        sdir = _skill_dir(tmp_path, "sk")
        refs_dir = sdir / "references"
        refs_dir.mkdir()
        (refs_dir / "guide.md").write_text("Guide text.", encoding="utf-8")
        (refs_dir / "api.md").write_text("API text.", encoding="utf-8")
        _, refs = read_skill_content(sdir)
        assert "guide.md" in refs
        assert refs["guide.md"] == "Guide text."
        assert "api.md" in refs
        assert refs["api.md"] == "API text."

    def test_reference_files_sorted_lexicographically(self, tmp_path: Path) -> None:
        sdir = _skill_dir(tmp_path, "sk")
        refs_dir = sdir / "references"
        refs_dir.mkdir()
        (refs_dir / "z-last.md").write_text("Z", encoding="utf-8")
        (refs_dir / "a-first.md").write_text("A", encoding="utf-8")
        _, refs = read_skill_content(sdir)
        keys = list(refs.keys())
        assert keys == sorted(keys)

    def test_only_md_files_included_in_references(self, tmp_path: Path) -> None:
        sdir = _skill_dir(tmp_path, "sk")
        refs_dir = sdir / "references"
        refs_dir.mkdir()
        (refs_dir / "guide.md").write_text("Guide.", encoding="utf-8")
        (refs_dir / "ignore.txt").write_text("Not included.", encoding="utf-8")
        _, refs = read_skill_content(sdir)
        assert "guide.md" in refs
        assert "ignore.txt" not in refs

    def test_raises_file_not_found_for_missing_skill_md(self, tmp_path: Path) -> None:
        empty_dir = tmp_path / "empty-skill"
        empty_dir.mkdir()
        with pytest.raises(FileNotFoundError):
            read_skill_content(empty_dir)


# ---------------------------------------------------------------------------
# Parameterized: skills normalization edge cases
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("skills_yaml", "expected"),
    [
        ("skills: []", []),
        ("skills:\n  - a\n", ["a"]),
        ("skills: a, b, c", ["a", "b", "c"]),
        ("skills:\n  - a\n  - b\n  - c\n", ["a", "b", "c"]),
        ("skills: single", ["single"]),
    ],
)
def test_skills_normalization_variants(tmp_path: Path, skills_yaml: str, expected: list[str]) -> None:
    path = tmp_path / "agent.md"
    path.write_text(f"---\nname: a\ndescription: d\n{skills_yaml}\n---\nBody.\n", encoding="utf-8")
    meta, _ = parse_agent_file(path)
    assert meta.skills == expected
