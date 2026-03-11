"""Tests for manifest discovery across priority levels."""

from __future__ import annotations

from textwrap import dedent
from typing import TYPE_CHECKING

from manifest_discovery import (
    MANIFEST_FILENAME,
    DiscoveredManifest,
    PriorityLevel,
    detect_project_dependencies,
    discover_manifests,
    select_best_manifest,
)

if TYPE_CHECKING:
    from pathlib import Path


def _write_manifest(path: Path, name: str, markers: str = "pyproject.toml", required_dependencies: str = "") -> Path:
    """Helper to write a minimal manifest YAML."""
    deps_line = f"\n      required_dependencies: [{required_dependencies}]" if required_dependencies else ""
    content = dedent(f"""\
        name: {name}
        language: python
        version: "1.0"
        project_detection:
          markers: [{markers}]{deps_line}
    """)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


class TestDiscoverManifests:
    """Test manifest discovery from multiple priority levels."""

    def test_discover_from_plugin_level(self, tmp_path: Path) -> None:
        """Discover manifests from plugins/*/manifests/*/language-manifest.yaml."""
        plugin_dir = tmp_path / "plugins" / "python3-development" / "manifests" / "python3"
        _write_manifest(plugin_dir / MANIFEST_FILENAME, "python3")

        results = discover_manifests(
            project_root=tmp_path,
            plugin_dirs=[tmp_path / "plugins" / "python3-development"],
            project_markers={"pyproject.toml"},
        )
        assert len(results) >= 1
        names = [r.manifest.name for r in results]
        assert "python3" in names

    def test_discover_from_project_level(self, tmp_path: Path) -> None:
        """Discover manifests from .claude/manifests/*/language-manifest.yaml."""
        proj_dir = tmp_path / ".claude" / "manifests" / "custom"
        _write_manifest(proj_dir / MANIFEST_FILENAME, "custom")

        results = discover_manifests(project_root=tmp_path, plugin_dirs=[], project_markers={"pyproject.toml"})
        names = [r.manifest.name for r in results]
        assert "custom" in names

    def test_discover_filters_by_marker(self, tmp_path: Path) -> None:
        """Only discover manifests whose markers match the project."""
        plugin_dir = tmp_path / "plugins" / "ts" / "manifests" / "typescript"
        _write_manifest(plugin_dir / MANIFEST_FILENAME, "typescript", markers="package.json")

        results = discover_manifests(
            project_root=tmp_path,
            plugin_dirs=[tmp_path / "plugins" / "ts"],
            project_markers={"pyproject.toml"},  # No package.json
        )
        names = [r.manifest.name for r in results]
        assert "typescript" not in names

    def test_malformed_yaml_skipped_not_crash(self, tmp_path: Path) -> None:
        """I7: A malformed YAML manifest should be skipped, not crash discovery."""
        plugin_dir = tmp_path / "plugins" / "bad" / "manifests" / "broken"
        plugin_dir.mkdir(parents=True)
        (plugin_dir / MANIFEST_FILENAME).write_text("name: broken\n  bad: [unmatched\n")

        # Also add a valid manifest to prove discovery continues
        good_dir = tmp_path / "plugins" / "bad" / "manifests" / "good"
        _write_manifest(good_dir / MANIFEST_FILENAME, "good")

        results = discover_manifests(
            project_root=tmp_path, plugin_dirs=[tmp_path / "plugins" / "bad"], project_markers={"pyproject.toml"}
        )
        names = [r.manifest.name for r in results]
        assert "broken" not in names
        assert "good" in names

    def test_priority_ordering(self, tmp_path: Path) -> None:
        """Project-level manifests have higher priority than plugin-level."""
        plugin_dir = tmp_path / "plugins" / "py" / "manifests" / "python3"
        _write_manifest(plugin_dir / MANIFEST_FILENAME, "python3")

        proj_dir = tmp_path / ".claude" / "manifests" / "python3"
        _write_manifest(proj_dir / MANIFEST_FILENAME, "python3")

        results = discover_manifests(
            project_root=tmp_path, plugin_dirs=[tmp_path / "plugins" / "py"], project_markers={"pyproject.toml"}
        )
        # Both should be found; project-level has higher priority
        project_results = [r for r in results if r.priority == PriorityLevel.PROJECT]
        plugin_results = [r for r in results if r.priority == PriorityLevel.PLUGIN]
        assert len(project_results) >= 1
        assert len(plugin_results) >= 1
        assert project_results[0].priority.value < plugin_results[0].priority.value


class TestDetectProjectDependencies:
    """Test dependency detection from project files."""

    def test_pyproject_toml_deps(self, tmp_path: Path) -> None:
        """Extract dependencies from pyproject.toml."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text(
            dedent("""\
            [project]
            dependencies = ["typer>=0.9", "rich", "httpx>=0.24"]
        """)
        )
        deps = detect_project_dependencies(tmp_path)
        assert "typer" in deps
        assert "rich" in deps
        assert "httpx" in deps

    def test_no_pyproject(self, tmp_path: Path) -> None:
        """Return empty set when no pyproject.toml exists."""
        deps = detect_project_dependencies(tmp_path)
        assert deps == set()


class TestSelectBestManifest:
    """Test manifest selection by specificity scoring."""

    def test_higher_dep_match_wins(self, tmp_path: Path) -> None:
        """Manifest matching more required_dependencies scores higher."""
        from manifest_schema import LanguageManifest, ProjectDetection

        base = DiscoveredManifest(
            manifest=LanguageManifest(
                name="python3",
                language="python",
                version="1.0",
                project_detection=ProjectDetection(markers=["pyproject.toml"]),
            ),
            path=tmp_path / "base.yaml",
            priority=PriorityLevel.PLUGIN,
        )
        cli = DiscoveredManifest(
            manifest=LanguageManifest(
                name="python3-cli",
                language="python",
                version="1.0",
                project_detection=ProjectDetection(markers=["pyproject.toml"], required_dependencies=["typer"]),
            ),
            path=tmp_path / "cli.yaml",
            priority=PriorityLevel.PLUGIN,
        )
        winner = select_best_manifest([base, cli], actual_deps={"typer", "rich"})
        assert winner is not None
        assert winner.manifest.name == "python3-cli"

    def test_priority_breaks_tie(self, tmp_path: Path) -> None:
        """When scores tie, higher priority level wins."""
        from manifest_schema import LanguageManifest, ProjectDetection

        plugin_m = DiscoveredManifest(
            manifest=LanguageManifest(
                name="python3",
                language="python",
                version="1.0",
                project_detection=ProjectDetection(markers=["pyproject.toml"]),
            ),
            path=tmp_path / "plugin.yaml",
            priority=PriorityLevel.PLUGIN,
        )
        project_m = DiscoveredManifest(
            manifest=LanguageManifest(
                name="python3",
                language="python",
                version="1.0",
                project_detection=ProjectDetection(markers=["pyproject.toml"]),
            ),
            path=tmp_path / "project.yaml",
            priority=PriorityLevel.PROJECT,
        )
        winner = select_best_manifest([plugin_m, project_m], actual_deps=set())
        assert winner is not None
        assert winner.priority == PriorityLevel.PROJECT

    def test_empty_list_returns_none(self) -> None:
        winner = select_best_manifest([], actual_deps=set())
        assert winner is None

    def test_same_name_dedup_before_scoring(self, tmp_path: Path) -> None:
        """C2: Same-name manifests should be deduped by priority before scoring.

        Project-level python3 (0 deps matched) should shadow plugin-level python3
        even though plugin-level would otherwise participate in scoring.
        """
        from manifest_resolver import _dedup_by_name_priority
        from manifest_schema import LanguageManifest, ProjectDetection

        project_m = DiscoveredManifest(
            manifest=LanguageManifest(
                name="python3",
                language="python",
                version="1.0",
                project_detection=ProjectDetection(markers=["pyproject.toml"]),
            ),
            path=tmp_path / "project.yaml",
            priority=PriorityLevel.PROJECT,
        )
        plugin_m = DiscoveredManifest(
            manifest=LanguageManifest(
                name="python3",
                language="python",
                version="1.0",
                project_detection=ProjectDetection(markers=["pyproject.toml"], required_dependencies=["ruff"]),
            ),
            path=tmp_path / "plugin.yaml",
            priority=PriorityLevel.PLUGIN,
        )
        deduped = _dedup_by_name_priority([project_m, plugin_m])
        assert len(deduped) == 1
        assert deduped[0].priority == PriorityLevel.PROJECT
