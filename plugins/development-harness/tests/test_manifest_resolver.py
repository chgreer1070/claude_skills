"""Tests for the full manifest resolution pipeline.

Note: Imports resolve via [tool.pytest.ini_options] pythonpath in pyproject.toml.
"""

from __future__ import annotations

from pathlib import Path
from textwrap import dedent
from typing import NoReturn

import pytest
from _pytest.outcomes import Skipped

from manifest_resolver import resolve_for_project


def _skip_test(reason: str) -> NoReturn:
    """Skip a test by raising Skipped directly.

    Workaround: ty cannot resolve the _WithException Protocol descriptor
    that pytest uses on pytest.skip(). This helper provides an equivalent
    call with a signature ty can verify.
    """
    raise Skipped(reason)


def _setup_project(tmp_path: Path) -> Path:
    """Create a mock Python/Typer project."""
    project = tmp_path / "myproject"
    project.mkdir()
    (project / "pyproject.toml").write_text(
        dedent("""\
        [project]
        dependencies = ["typer>=0.9", "rich"]
    """)
    )
    return project


def _setup_manifests(tmp_path: Path) -> Path:
    """Create base and CLI manifests in a plugin dir."""
    plugin_dir = tmp_path / "plugins" / "python3-development"
    base_dir = plugin_dir / "manifests" / "python3"
    base_dir.mkdir(parents=True)
    (base_dir / "language-manifest.yaml").write_text(
        dedent("""\
        name: python3
        language: python
        version: "1.0"
        project_detection:
          markers: [pyproject.toml]
        stage_skills:
          discovery: [python3-discovery]
          implementation: [python3-implementation]
        quality_gates:
          lint: "uv run ruff check {files}"
          test: "uv run pytest tests/"
    """)
    )

    cli_dir = plugin_dir / "manifests" / "python3-cli"
    cli_dir.mkdir(parents=True)
    (cli_dir / "language-manifest.yaml").write_text(
        dedent("""\
        name: python3-cli
        extends: python3-development:python3
        language: python
        stack: typer-cli
        version: "1.0"
        project_detection:
          markers: [pyproject.toml]
          required_dependencies: [typer]
        stage_skills:
          implementation: [python3-implementation-cli]
          design: [python3-design-cli]
    """)
    )
    return plugin_dir


class TestResolveForProject:
    """Test end-to-end resolution pipeline."""

    def test_selects_cli_for_typer_project(self, tmp_path: Path) -> None:
        project = _setup_project(tmp_path)
        plugin_dir = _setup_manifests(tmp_path)

        result = resolve_for_project(project_root=project, plugin_dirs=[plugin_dir])
        assert result is not None
        assert result.name == "python3-cli"
        assert result.stack == "typer-cli"
        # extends should be resolved -- implementation has both parent and child skills
        assert "python3-implementation" in result.stage_skills["implementation"]
        assert "python3-implementation-cli" in result.stage_skills["implementation"]
        # Parent stage preserved
        assert "python3-discovery" in result.stage_skills["discovery"]
        # Child-only stage
        assert "python3-design-cli" in result.stage_skills["design"]
        # Quality gates inherited from parent
        assert result.quality_gates is not None
        assert result.quality_gates.lint == "uv run ruff check {files}"

    def test_falls_back_to_base_without_typer(self, tmp_path: Path) -> None:
        project = tmp_path / "vanilla"
        project.mkdir()
        (project / "pyproject.toml").write_text(
            dedent("""\
            [project]
            dependencies = ["requests"]
        """)
        )
        plugin_dir = _setup_manifests(tmp_path)

        result = resolve_for_project(project_root=project, plugin_dirs=[plugin_dir])
        assert result is not None
        assert result.name == "python3"

    def test_no_matching_manifest(self, tmp_path: Path) -> None:
        """Project with no matching markers returns None."""
        project = tmp_path / "rust-project"
        project.mkdir()
        (project / "Cargo.toml").write_text("[package]\nname = 'foo'\n")
        plugin_dir = _setup_manifests(tmp_path)

        result = resolve_for_project(project_root=project, plugin_dirs=[plugin_dir])
        assert result is None


class TestRealManifestResolution:
    """Integration test using actual manifest files from the repo."""

    @pytest.fixture
    def repo_root(self) -> Path:
        """Find the repo root (where pyproject.toml lives)."""
        p = Path(__file__).resolve()
        max_depth = 10
        for _ in range(max_depth):
            if p == p.parent:
                break
            if (p / "pyproject.toml").exists() and (p / "plugins").exists():
                return p
            p = p.parent
        _skip_test("Cannot find repo root within 10 parent directories")

    def test_resolve_with_real_manifests(self, repo_root: Path, tmp_path: Path) -> None:
        """Create a mock Typer project and resolve against real manifests."""
        # Create a mock project with typer dependency
        project = tmp_path / "typer-app"
        project.mkdir()
        (project / "pyproject.toml").write_text(
            dedent("""\
            [project]
            name = "my-cli"
            dependencies = ["typer>=0.9", "rich"]
        """)
        )

        plugin_dir = repo_root / "plugins" / "python3-development"
        if not (plugin_dir / "manifests" / "python3").exists():
            _skip_test("Real manifests not yet created")

        result = resolve_for_project(project_root=project, plugin_dirs=[plugin_dir])
        assert result is not None
        assert result.name == "python3-cli"
        assert result.stack == "typer-cli"
        # Inherited from base
        assert "python3-implementation" in result.stage_skills.get("implementation", [])
        # Added by cli manifest
        assert "python3-implementation-cli" in result.stage_skills.get("implementation", [])
        # Quality gates inherited
        assert result.quality_gates is not None
        assert "ruff" in (result.quality_gates.lint or "")

    def test_resolve_base_for_vanilla_python(self, repo_root: Path, tmp_path: Path) -> None:
        """A Python project without typer should resolve to base python3."""
        project = tmp_path / "vanilla-py"
        project.mkdir()
        (project / "pyproject.toml").write_text(
            dedent("""\
            [project]
            name = "my-lib"
            dependencies = ["requests"]
        """)
        )

        plugin_dir = repo_root / "plugins" / "python3-development"
        if not (plugin_dir / "manifests" / "python3").exists():
            _skip_test("Real manifests not yet created")

        result = resolve_for_project(project_root=project, plugin_dirs=[plugin_dir])
        assert result is not None
        assert result.name == "python3"
