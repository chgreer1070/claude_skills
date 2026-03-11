# DH Phase 1: Manifest + Dispatch Engine — Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the manifest resolver, language manifests, and generic agent dispatch model for the development harness. At the end of Phase 1, a generic harness agent can execute a Python task by loading a stage workflow skill + python3 domain skill resolved from a YAML manifest with `extends` inheritance.

**Architecture:** Language manifests are YAML files declaring stage-to-skill mappings, quality gates, and project detection rules per stack. Manifests support `extends` inheritance (GitLab CI semantics: scalars replace, lists append, dicts deep merge). Discovery follows a 5-level priority hierarchy (enterprise > personal > project > plugin > skill). A manifest resolver script discovers all matching manifests, scores them by `required_dependencies` match count, resolves the `extends` chain on the winner, and returns the fully resolved manifest. A generic stage agent receives 5 inputs at dispatch time: stage workflow mermaid, cross-cutting SDLC stage skill, domain skills from the resolved manifest, task/artifact file, and quality gate commands.

**Tech Stack:** Python 3.11+, ruamel.yaml, typer, rich, Claude Code plugin system

**Design Source:** [plan/architect-dh-architecture-refactor.md](./architect-dh-architecture-refactor.md) (sections 2, 3, 4)

---

## File Structure

### Files to Create

```text
plugins/development-harness/scripts/manifest_resolver.py          — Main CLI: discover, score, resolve, return manifest
plugins/development-harness/scripts/manifest_schema.py            — Dataclasses for manifest YAML schema
plugins/development-harness/scripts/manifest_merge.py             — Merge logic (scalars replace, lists append, dicts deep merge)
plugins/development-harness/scripts/manifest_discovery.py         — Discovery across 5 priority levels + project detection
plugins/development-harness/scripts/dispatch_helper.py            — Assembles 5 inputs for generic agent dispatch
plugins/development-harness/tests/test_manifest_schema.py         — Schema validation tests
plugins/development-harness/tests/test_manifest_merge.py          — Merge logic tests
plugins/development-harness/tests/test_manifest_discovery.py      — Discovery and scoring tests
plugins/development-harness/tests/test_manifest_resolver.py       — End-to-end resolver tests
plugins/development-harness/tests/test_dispatch_helper.py         — Dispatch helper tests
plugins/development-harness/tests/conftest.py                     — Shared fixtures (tmp manifests, mock projects)
plugins/python3-development/manifests/python3/language-manifest.yaml    — Base python3 manifest
plugins/python3-development/manifests/python3-cli/language-manifest.yaml — python3-cli manifest extending base
plugins/development-harness/agents/generic-stage-agent.md         — Generic stage agent markdown
```

### Files to Modify

```text
plugins/development-harness/.claude-plugin/plugin.json            — No name change needed (already "development-harness")
```

---

## Chunk 1: Manifest Schema and Parser

### Task 1: Manifest YAML Dataclass Model

**Files:**

- Create: `plugins/development-harness/scripts/manifest_schema.py`
- Test: `plugins/development-harness/tests/test_manifest_schema.py`

- [ ] **Step 1: Write the failing test**

Create `plugins/development-harness/tests/test_manifest_schema.py`:

```python
"""Tests for manifest YAML schema dataclasses."""

import pytest
from manifest_schema import LanguageManifest, ProjectDetection, QualityGates


class TestLanguageManifest:
    """Test LanguageManifest dataclass construction and validation."""

    def test_minimal_manifest(self) -> None:
        """A manifest with only required fields should construct successfully."""
        m = LanguageManifest(
            name="python3",
            language="python",
            version="1.0",
            project_detection=ProjectDetection(markers=["pyproject.toml"]),
        )
        assert m.name == "python3"
        assert m.extends is None
        assert m.stack is None
        assert m.stage_skills == {}
        assert m.quality_gates is None

    def test_full_manifest(self) -> None:
        """A manifest with all fields should construct successfully."""
        m = LanguageManifest(
            name="python3-cli",
            extends="python3-development:python3",
            language="python",
            stack="typer-cli",
            version="1.0",
            project_detection=ProjectDetection(
                markers=["pyproject.toml"],
                required_dependencies=["typer"],
                source_patterns=["src/**/*.py"],
                test_patterns=["tests/**/*.py"],
            ),
            stage_skills={
                "discovery": ["python3-discovery"],
                "implementation": ["python3-implementation", "python3-implementation-cli"],
            },
            quality_gates=QualityGates(
                format="uv run ruff format {files}",
                lint="uv run ruff check {files}",
                typecheck="uv run mypy {files}",
                test="uv run pytest tests/ --tb=short",
                standards="/python3-development:modernpython",
            ),
        )
        assert m.name == "python3-cli"
        assert m.extends == "python3-development:python3"
        assert m.stack == "typer-cli"
        assert m.project_detection.required_dependencies == ["typer"]
        assert len(m.stage_skills["implementation"]) == 2

    def test_extends_as_list(self) -> None:
        """extends field accepts a list of strings."""
        m = LanguageManifest(
            name="combo",
            extends=["python3-development:python3", "python3-development:python3-cli"],
            language="python",
            version="1.0",
            project_detection=ProjectDetection(markers=["pyproject.toml"]),
        )
        assert isinstance(m.extends, list)
        assert len(m.extends) == 2

    def test_missing_name_raises(self) -> None:
        """name is required."""
        with pytest.raises(TypeError):
            LanguageManifest(
                language="python",
                version="1.0",
                project_detection=ProjectDetection(markers=["pyproject.toml"]),
            )

    def test_missing_markers_raises(self) -> None:
        """ProjectDetection requires at least markers."""
        with pytest.raises(TypeError):
            ProjectDetection()


class TestProjectDetection:
    """Test ProjectDetection dataclass."""

    def test_defaults(self) -> None:
        pd = ProjectDetection(markers=["pyproject.toml"])
        assert pd.required_dependencies == []
        assert pd.source_patterns == []
        assert pd.test_patterns == []

    def test_specificity_score_no_deps(self) -> None:
        """Manifest with no required_dependencies scores 0."""
        pd = ProjectDetection(markers=["pyproject.toml"])
        assert pd.specificity_score({"typer", "rich"}) == 0

    def test_specificity_score_partial_match(self) -> None:
        """Score counts matched required_dependencies."""
        pd = ProjectDetection(
            markers=["pyproject.toml"],
            required_dependencies=["typer", "rich", "httpx"],
        )
        assert pd.specificity_score({"typer", "rich"}) == 2

    def test_specificity_score_full_match(self) -> None:
        pd = ProjectDetection(
            markers=["pyproject.toml"],
            required_dependencies=["typer"],
        )
        assert pd.specificity_score({"typer", "rich", "click"}) == 1

    def test_specificity_score_no_match(self) -> None:
        """If no required_dependencies match, score is 0."""
        pd = ProjectDetection(
            markers=["pyproject.toml"],
            required_dependencies=["django"],
        )
        assert pd.specificity_score({"typer", "rich"}) == 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /home/ubuntulinuxqa2/repos/claude_skills && uv run pytest plugins/development-harness/tests/test_manifest_schema.py -x`
Expected: FAIL with `ModuleNotFoundError: No module named 'manifest_schema'`

- [ ] **Step 3: Write minimal implementation**

Create `plugins/development-harness/scripts/manifest_schema.py`:

```python
"""Language manifest YAML schema dataclasses.

Defines the structure for language manifests that configure
the development harness for specific language stacks.
"""

from dataclasses import dataclass, field


@dataclass(slots=True)
class ProjectDetection:
    """Project detection rules for a language manifest."""

    markers: list[str]
    required_dependencies: list[str] = field(default_factory=list)
    source_patterns: list[str] = field(default_factory=list)
    test_patterns: list[str] = field(default_factory=list)

    def specificity_score(self, actual_deps: set[str]) -> int:
        """Score this manifest against actual project dependencies.

        Returns the count of required_dependencies found in actual_deps.
        A manifest with no required_dependencies always scores 0 (base fallback).
        """
        if not self.required_dependencies:
            return 0
        return len(set(self.required_dependencies) & actual_deps)


@dataclass(slots=True)
class QualityGates:
    """Quality gate commands for a language manifest."""

    format: str | None = None
    lint: str | None = None
    typecheck: str | None = None
    test: str | None = None
    standards: str | None = None


@dataclass(slots=True)
class LanguageManifest:
    """A language manifest declaring stack-specific configuration.

    One manifest per stack (not per language). Examples: python3 (base),
    python3-cli (Typer projects), python3-fastapi (FastAPI services).
    """

    name: str
    language: str
    version: str
    project_detection: ProjectDetection
    extends: str | list[str] | None = None
    stack: str | None = None
    stage_skills: dict[str, list[str]] = field(default_factory=dict)
    quality_gates: QualityGates | None = None
```

- [ ] **Step 4: Write conftest.py for sys.path setup**

Create `plugins/development-harness/tests/conftest.py`:

```python
"""Shared test configuration for development-harness tests.

Note: Test imports resolve via [tool.pytest.ini_options] pythonpath
in pyproject.toml, which includes plugins/development-harness/scripts.
No sys.path manipulation needed.
"""
```

Add to `pyproject.toml` (or the plugin's local pytest config):

```toml
[tool.pytest.ini_options]
pythonpath = ["plugins/development-harness/scripts"]
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd /home/ubuntulinuxqa2/repos/claude_skills && uv run pytest plugins/development-harness/tests/test_manifest_schema.py -v`
Expected: All 10 tests PASS

- [ ] **Step 6: Commit**

```text
feat(development-harness): add manifest YAML schema dataclasses
```

---

### Task 2: YAML Loading and Validation

**Files:**

- Modify: `plugins/development-harness/scripts/manifest_schema.py` (add `load_manifest` and `validate_manifest`)
- Test: `plugins/development-harness/tests/test_manifest_schema.py` (add loading tests)

- [ ] **Step 1: Write the failing tests**

Append to `plugins/development-harness/tests/test_manifest_schema.py`:

```python
# NOTE: Path is already imported from Task 1. Only add new imports here.
from textwrap import dedent
from manifest_schema import load_manifest, validate_manifest, ManifestValidationError, ValidationResult


class TestLoadManifest:
    """Test YAML loading into LanguageManifest."""

    def test_load_valid_yaml(self, tmp_path: Path) -> None:
        """Load a valid manifest YAML file."""
        yaml_content = dedent("""\
            name: python3
            language: python
            version: "1.0"
            project_detection:
              markers: [pyproject.toml]
              source_patterns: ["src/**/*.py"]
            stage_skills:
              discovery: [python3-discovery]
            quality_gates:
              lint: "uv run ruff check {files}"
              test: "uv run pytest tests/"
        """)
        manifest_file = tmp_path / "language-manifest.yaml"
        manifest_file.write_text(yaml_content)
        m = load_manifest(manifest_file)
        assert m.name == "python3"
        assert m.language == "python"
        assert m.project_detection.markers == ["pyproject.toml"]
        assert m.stage_skills["discovery"] == ["python3-discovery"]
        assert m.quality_gates is not None
        assert m.quality_gates.lint == "uv run ruff check {files}"

    def test_load_with_extends_string(self, tmp_path: Path) -> None:
        yaml_content = dedent("""\
            name: python3-cli
            extends: python3-development:python3
            language: python
            version: "1.0"
            project_detection:
              markers: [pyproject.toml]
              required_dependencies: [typer]
        """)
        manifest_file = tmp_path / "language-manifest.yaml"
        manifest_file.write_text(yaml_content)
        m = load_manifest(manifest_file)
        assert m.extends == "python3-development:python3"

    def test_load_with_extends_list(self, tmp_path: Path) -> None:
        yaml_content = dedent("""\
            name: combo
            extends:
              - python3-development:python3
              - python3-development:python3-cli
            language: python
            version: "1.0"
            project_detection:
              markers: [pyproject.toml]
        """)
        manifest_file = tmp_path / "language-manifest.yaml"
        manifest_file.write_text(yaml_content)
        m = load_manifest(manifest_file)
        assert isinstance(m.extends, list)
        assert len(m.extends) == 2

    def test_load_missing_name_raises(self, tmp_path: Path) -> None:
        yaml_content = dedent("""\
            language: python
            version: "1.0"
            project_detection:
              markers: [pyproject.toml]
        """)
        manifest_file = tmp_path / "language-manifest.yaml"
        manifest_file.write_text(yaml_content)
        with pytest.raises(ManifestValidationError, match="name"):
            load_manifest(manifest_file)

    def test_load_missing_markers_raises(self, tmp_path: Path) -> None:
        yaml_content = dedent("""\
            name: python3
            language: python
            version: "1.0"
            project_detection: {}
        """)
        manifest_file = tmp_path / "language-manifest.yaml"
        manifest_file.write_text(yaml_content)
        with pytest.raises(ManifestValidationError, match="markers"):
            load_manifest(manifest_file)

    def test_load_nonexistent_file_raises(self) -> None:
        with pytest.raises(FileNotFoundError):
            load_manifest(Path("/nonexistent/manifest.yaml"))

    def test_load_malformed_yaml_raises(self, tmp_path: Path) -> None:
        """Malformed YAML should raise ManifestValidationError, not crash."""
        bad_yaml = tmp_path / "language-manifest.yaml"
        bad_yaml.write_text("name: python3\n  bad_indent: [unmatched\n")
        with pytest.raises(ManifestValidationError, match="Invalid YAML"):
            load_manifest(bad_yaml)


class TestValidateManifest:
    """Test manifest validation rules."""

    def test_valid_manifest_passes(self) -> None:
        m = LanguageManifest(
            name="python3",
            language="python",
            version="1.0",
            project_detection=ProjectDetection(markers=["pyproject.toml"]),
        )
        result = validate_manifest(m)
        assert result.errors == []
        assert result.warnings == []

    def test_empty_markers_fails(self) -> None:
        m = LanguageManifest(
            name="python3",
            language="python",
            version="1.0",
            project_detection=ProjectDetection(markers=[]),
        )
        result = validate_manifest(m)
        assert any("markers" in e for e in result.errors)

    def test_invalid_stage_name_warns(self) -> None:
        m = LanguageManifest(
            name="python3",
            language="python",
            version="1.0",
            project_detection=ProjectDetection(markers=["pyproject.toml"]),
            stage_skills={"invalid-stage-name": ["some-skill"]},
        )
        result = validate_manifest(m)
        assert result.errors == [], "Unrecognized stages should be warnings, not errors"
        assert any("stage" in w.lower() for w in result.warnings)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /home/ubuntulinuxqa2/repos/claude_skills && uv run pytest plugins/development-harness/tests/test_manifest_schema.py::TestLoadManifest -x`
Expected: FAIL with `ImportError: cannot import name 'load_manifest'`

- [ ] **Step 3: Write minimal implementation**

Add to `plugins/development-harness/scripts/manifest_schema.py`:

```python
from pathlib import Path

from ruamel.yaml import YAML, YAMLError

# Canonical SDLC stage identifiers from the design doc
VALID_STAGES: frozenset[str] = frozenset({
    "discovery",
    "design",
    "planning-context-integration",
    "planning-task-decomposition",
    "implementation",
    "testing-forensic-review",
    "testing-verification",
})


class ManifestValidationError(Exception):
    """Raised when a manifest fails validation."""


def load_manifest(path: Path) -> LanguageManifest:
    """Load a language manifest from a YAML file.

    Raises:
        FileNotFoundError: If path does not exist.
        ManifestValidationError: If required fields are missing or invalid.
    """
    yaml = YAML()
    try:
        data = yaml.load(path)
    except FileNotFoundError:
        raise FileNotFoundError(f"Manifest not found: {path}") from None
    except YAMLError as exc:
        msg = f"Invalid YAML in manifest {path}: {exc}"
        raise ManifestValidationError(msg) from exc
    if not isinstance(data, dict):
        msg = f"Manifest must be a YAML mapping, got {type(data).__name__}"
        raise ManifestValidationError(msg)

    # Validate required top-level fields
    for required_field in ("name", "language", "version"):
        if required_field not in data:
            msg = f"Missing required field: {required_field}"
            raise ManifestValidationError(msg)

    # Parse project_detection
    pd_data = data.get("project_detection", {})
    if not isinstance(pd_data, dict) or "markers" not in pd_data:
        msg = "project_detection.markers is required"
        raise ManifestValidationError(msg)

    project_detection = ProjectDetection(
        markers=list(pd_data.get("markers", [])),
        required_dependencies=list(pd_data.get("required_dependencies", [])),
        source_patterns=list(pd_data.get("source_patterns", [])),
        test_patterns=list(pd_data.get("test_patterns", [])),
    )

    # Parse quality_gates
    qg_data = data.get("quality_gates")
    quality_gates = None
    if isinstance(qg_data, dict):
        quality_gates = QualityGates(
            format=qg_data.get("format"),
            lint=qg_data.get("lint"),
            typecheck=qg_data.get("typecheck"),
            test=qg_data.get("test"),
            standards=qg_data.get("standards"),
        )

    # Parse stage_skills
    stage_skills_data = data.get("stage_skills", {})
    stage_skills: dict[str, list[str]] = {}
    if isinstance(stage_skills_data, dict):
        for stage, skills in stage_skills_data.items():
            if not isinstance(skills, list):
                skills = [skills]
            stage_skills[str(stage)] = [str(s) for s in skills]

    manifest = LanguageManifest(
        name=data["name"],
        extends=data.get("extends"),
        language=data["language"],
        stack=data.get("stack"),
        version=str(data["version"]),
        project_detection=project_detection,
        stage_skills=stage_skills,
        quality_gates=quality_gates,
    )

    # Semantic validation after parsing — validate_manifest and ValidationResult
    # must be defined BEFORE load_manifest in the file (move them above this function).
    validation = validate_manifest(manifest)
    if validation.errors:
        msg = f"Manifest validation failed for {path}: {'; '.join(validation.errors)}"
        raise ManifestValidationError(msg)
    for warning in validation.warnings:
        import logging
        logging.getLogger(__name__).warning("Manifest %s: %s", path, warning)

    return manifest


# NOTE: ValidationResult and validate_manifest must be defined BEFORE load_manifest.
# The implementer must reorder these definitions so that load_manifest can call
# validate_manifest. They are shown here in logical grouping order, not file order.

@dataclass(slots=True)
class ValidationResult:
    """Structured validation result separating errors from warnings."""

    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def validate_manifest(manifest: LanguageManifest) -> ValidationResult:
    """Validate a loaded manifest.

    Returns:
        ValidationResult with separate errors and warnings lists.
        Errors are hard failures; warnings are informational.
    """
    result = ValidationResult()

    if not manifest.project_detection.markers:
        result.errors.append("project_detection.markers must not be empty")

    # Warn about unrecognized stage names (custom stages are allowed but flagged)
    for stage in manifest.stage_skills:
        if stage not in VALID_STAGES:
            result.warnings.append(
                f"Unrecognized stage name '{stage}' in stage_skills. "
                f"Valid stages: {', '.join(sorted(VALID_STAGES))}"
            )

    return result
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /home/ubuntulinuxqa2/repos/claude_skills && uv run pytest plugins/development-harness/tests/test_manifest_schema.py -v`
Expected: All tests PASS

- [ ] **Step 5: Commit**

```text
feat(development-harness): add manifest YAML loading and validation
```

---

### Task 3: Extends Resolution (Recursive, Name-Based and Path-Based)

**Files:**

- Create: `plugins/development-harness/scripts/manifest_merge.py`
- Test: `plugins/development-harness/tests/test_manifest_merge.py`

- [ ] **Step 1: Write the failing tests**

Create `plugins/development-harness/tests/test_manifest_merge.py`:

```python
"""Tests for manifest extends resolution and merge logic."""

from pathlib import Path
from textwrap import dedent

import pytest
from manifest_merge import (
    deep_merge_dicts,
    merge_manifests,
    resolve_extends_chain,
)
from manifest_schema import LanguageManifest, ProjectDetection, QualityGates


class TestDeepMergeDicts:
    """Test dict deep merge."""

    def test_disjoint_keys(self) -> None:
        base = {"a": 1}
        child = {"b": 2}
        result = deep_merge_dicts(base, child)
        assert result == {"a": 1, "b": 2}

    def test_scalar_replace(self) -> None:
        base = {"a": 1, "b": 2}
        child = {"b": 3}
        result = deep_merge_dicts(base, child)
        assert result == {"a": 1, "b": 3}

    def test_nested_merge(self) -> None:
        base = {"a": {"x": 1, "y": 2}}
        child = {"a": {"y": 3, "z": 4}}
        result = deep_merge_dicts(base, child)
        assert result == {"a": {"x": 1, "y": 3, "z": 4}}

    def test_list_append(self) -> None:
        base = {"a": [1, 2]}
        child = {"a": [3, 4]}
        result = deep_merge_dicts(base, child)
        assert result == {"a": [1, 2, 3, 4]}

    def test_empty_child(self) -> None:
        base = {"a": 1}
        result = deep_merge_dicts(base, {})
        assert result == {"a": 1}

    def test_empty_base(self) -> None:
        child = {"a": 1}
        result = deep_merge_dicts({}, child)
        assert result == {"a": 1}


class TestMergeManifests:
    """Test merging parent + child manifests."""

    def test_child_scalar_replaces_parent(self) -> None:
        parent = LanguageManifest(
            name="python3",
            language="python",
            version="1.0",
            stack="base",
            project_detection=ProjectDetection(markers=["pyproject.toml"]),
        )
        child = LanguageManifest(
            name="python3-cli",
            language="python",
            version="1.0",
            stack="typer-cli",
            project_detection=ProjectDetection(
                markers=["pyproject.toml"],
                required_dependencies=["typer"],
            ),
        )
        merged = merge_manifests(parent, child)
        assert merged.name == "python3-cli"
        assert merged.stack == "typer-cli"

    def test_stage_skills_append(self) -> None:
        parent = LanguageManifest(
            name="python3",
            language="python",
            version="1.0",
            project_detection=ProjectDetection(markers=["pyproject.toml"]),
            stage_skills={"implementation": ["python3-implementation"]},
        )
        child = LanguageManifest(
            name="python3-cli",
            language="python",
            version="1.0",
            project_detection=ProjectDetection(markers=["pyproject.toml"]),
            stage_skills={
                "implementation": ["python3-implementation-cli"],
                "design": ["python3-design-cli"],
            },
        )
        merged = merge_manifests(parent, child)
        assert merged.stage_skills["implementation"] == [
            "python3-implementation", "python3-implementation-cli"
        ]
        assert merged.stage_skills["design"] == ["python3-design-cli"]

    def test_stage_skills_deduped_after_append(self) -> None:
        """I4: Duplicate skills in stage_skills should be deduplicated after merge."""
        parent = LanguageManifest(
            name="python3",
            language="python",
            version="1.0",
            project_detection=ProjectDetection(markers=["pyproject.toml"]),
            stage_skills={"implementation": ["python3-implementation"]},
        )
        child = LanguageManifest(
            name="python3-cli",
            language="python",
            version="1.0",
            project_detection=ProjectDetection(markers=["pyproject.toml"]),
            stage_skills={
                "implementation": ["python3-implementation", "python3-implementation-cli"],
            },
        )
        merged = merge_manifests(parent, child)
        assert merged.stage_skills["implementation"] == [
            "python3-implementation", "python3-implementation-cli"
        ]

    def test_quality_gates_merge(self) -> None:
        parent = LanguageManifest(
            name="python3",
            language="python",
            version="1.0",
            project_detection=ProjectDetection(markers=["pyproject.toml"]),
            quality_gates=QualityGates(
                lint="uv run ruff check {files}",
                test="uv run pytest tests/",
            ),
        )
        child = LanguageManifest(
            name="python3-cli",
            language="python",
            version="1.0",
            project_detection=ProjectDetection(markers=["pyproject.toml"]),
            quality_gates=QualityGates(
                test="uv run pytest tests/ --tb=short",
                standards="/python3-development:modernpython",
            ),
        )
        merged = merge_manifests(parent, child)
        assert merged.quality_gates is not None
        assert merged.quality_gates.lint == "uv run ruff check {files}"
        assert merged.quality_gates.test == "uv run pytest tests/ --tb=short"
        assert merged.quality_gates.standards == "/python3-development:modernpython"

    def test_child_required_deps_append(self) -> None:
        parent = LanguageManifest(
            name="python3",
            language="python",
            version="1.0",
            project_detection=ProjectDetection(
                markers=["pyproject.toml"],
                required_dependencies=["ruff"],
            ),
        )
        child = LanguageManifest(
            name="python3-cli",
            language="python",
            version="1.0",
            project_detection=ProjectDetection(
                markers=["pyproject.toml"],
                required_dependencies=["typer"],
            ),
        )
        merged = merge_manifests(parent, child)
        assert merged.project_detection.required_dependencies == ["ruff", "typer"]

    def test_duplicate_required_deps_deduped(self) -> None:
        """I3: Duplicate required_dependencies should be deduplicated after merge."""
        parent = LanguageManifest(
            name="python3",
            language="python",
            version="1.0",
            project_detection=ProjectDetection(
                markers=["pyproject.toml"],
                required_dependencies=["ruff", "typer"],
            ),
        )
        child = LanguageManifest(
            name="python3-cli",
            language="python",
            version="1.0",
            project_detection=ProjectDetection(
                markers=["pyproject.toml"],
                required_dependencies=["ruff", "rich"],
            ),
        )
        merged = merge_manifests(parent, child)
        assert merged.project_detection.required_dependencies == ["ruff", "typer", "rich"]


class TestResolveExtendsChain:
    """Test recursive extends resolution."""

    def test_no_extends(self, tmp_path: Path) -> None:
        """Manifest with no extends returns itself."""
        yaml_content = dedent("""\
            name: python3
            language: python
            version: "1.0"
            project_detection:
              markers: [pyproject.toml]
        """)
        manifest_file = tmp_path / "manifests" / "python3" / "language-manifest.yaml"
        manifest_file.parent.mkdir(parents=True)
        manifest_file.write_text(yaml_content)
        resolved = resolve_extends_chain(
            manifest_file,
            search_paths=[("test", tmp_path / "manifests")],
        )
        assert resolved.name == "python3"

    def test_single_extends_by_name(self, tmp_path: Path) -> None:
        """Resolve extends: plugin:manifest-name via search paths.

        C1: Uses canonical plugin name from (name, path) tuples, not path components.
        """
        # Parent manifest
        parent_dir = tmp_path / "plugin-a" / "manifests" / "base"
        parent_dir.mkdir(parents=True)
        (parent_dir / "language-manifest.yaml").write_text(dedent("""\
            name: base
            language: python
            version: "1.0"
            project_detection:
              markers: [pyproject.toml]
            stage_skills:
              discovery: [base-discovery]
        """))

        # Child manifest
        child_dir = tmp_path / "plugin-b" / "manifests" / "child"
        child_dir.mkdir(parents=True)
        child_file = child_dir / "language-manifest.yaml"
        child_file.write_text(dedent("""\
            name: child
            extends: plugin-a:base
            language: python
            version: "1.0"
            project_detection:
              markers: [pyproject.toml]
            stage_skills:
              implementation: [child-impl]
        """))

        # C1: search_paths use canonical plugin names, not path components
        search_paths: list[tuple[str, Path]] = [
            ("plugin-a", tmp_path / "plugin-a" / "manifests"),
            ("plugin-b", tmp_path / "plugin-b" / "manifests"),
        ]
        resolved = resolve_extends_chain(child_file, search_paths=search_paths)
        assert resolved.name == "child"
        assert resolved.stage_skills["discovery"] == ["base-discovery"]
        assert resolved.stage_skills["implementation"] == ["child-impl"]

    def test_extends_by_relative_path(self, tmp_path: Path) -> None:
        """Resolve extends: ./relative/path."""
        parent_file = tmp_path / "base.yaml"
        parent_file.write_text(dedent("""\
            name: base
            language: python
            version: "1.0"
            project_detection:
              markers: [pyproject.toml]
            stage_skills:
              discovery: [base-discovery]
        """))

        child_file = tmp_path / "child.yaml"
        child_file.write_text(dedent("""\
            name: child
            extends: ./base.yaml
            language: python
            version: "1.0"
            project_detection:
              markers: [pyproject.toml]
        """))

        resolved = resolve_extends_chain(child_file, search_paths=[])
        assert resolved.name == "child"
        assert resolved.stage_skills["discovery"] == ["base-discovery"]

    def test_circular_extends_raises(self, tmp_path: Path) -> None:
        """Circular extends chain should raise an error."""
        a_dir = tmp_path / "manifests" / "a"
        b_dir = tmp_path / "manifests" / "b"
        a_dir.mkdir(parents=True)
        b_dir.mkdir(parents=True)

        (a_dir / "language-manifest.yaml").write_text(dedent("""\
            name: a
            extends: test:b
            language: python
            version: "1.0"
            project_detection:
              markers: [pyproject.toml]
        """))
        (b_dir / "language-manifest.yaml").write_text(dedent("""\
            name: b
            extends: test:a
            language: python
            version: "1.0"
            project_detection:
              markers: [pyproject.toml]
        """))

        from manifest_merge import CircularExtendsError
        with pytest.raises(CircularExtendsError):
            resolve_extends_chain(
                a_dir / "language-manifest.yaml",
                search_paths=[("test", tmp_path / "manifests")],
            )

    def test_two_level_chain(self, tmp_path: Path) -> None:
        """grandparent -> parent -> child resolves correctly."""
        gp_dir = tmp_path / "manifests" / "gp"
        p_dir = tmp_path / "manifests" / "parent"
        c_dir = tmp_path / "manifests" / "child"
        for d in (gp_dir, p_dir, c_dir):
            d.mkdir(parents=True)

        (gp_dir / "language-manifest.yaml").write_text(dedent("""\
            name: gp
            language: python
            version: "1.0"
            project_detection:
              markers: [pyproject.toml]
            quality_gates:
              lint: "ruff check"
        """))
        (p_dir / "language-manifest.yaml").write_text(dedent("""\
            name: parent
            extends: test:gp
            language: python
            version: "1.0"
            project_detection:
              markers: [pyproject.toml]
            stage_skills:
              implementation: [parent-impl]
        """))
        (c_dir / "language-manifest.yaml").write_text(dedent("""\
            name: child
            extends: test:parent
            language: python
            version: "1.0"
            project_detection:
              markers: [pyproject.toml]
            stage_skills:
              implementation: [child-impl]
        """))

        search: list[tuple[str, Path]] = [("test", tmp_path / "manifests")]
        resolved = resolve_extends_chain(c_dir / "language-manifest.yaml", search_paths=search)
        assert resolved.name == "child"
        assert resolved.stage_skills["implementation"] == ["parent-impl", "child-impl"]
        assert resolved.quality_gates is not None
        assert resolved.quality_gates.lint == "ruff check"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /home/ubuntulinuxqa2/repos/claude_skills && uv run pytest plugins/development-harness/tests/test_manifest_merge.py -x`
Expected: FAIL with `ModuleNotFoundError: No module named 'manifest_merge'`

- [ ] **Step 3: Write minimal implementation**

Create `plugins/development-harness/scripts/manifest_merge.py`:

```python
"""Manifest merge and extends resolution logic.

Implements GitLab CI-style extends semantics:
- Scalars: child replaces parent
- Lists: child appends to parent
- Dicts: deep merge (child keys added, matching keys replaced)
"""

from dataclasses import fields
from pathlib import Path
from typing import Any

from manifest_schema import (
    LanguageManifest,
    ProjectDetection,
    QualityGates,
    load_manifest,
)


class CircularExtendsError(Exception):
    """Raised when a circular extends chain is detected."""


def deep_merge_dicts(base: dict[str, Any], child: dict[str, Any]) -> dict[str, Any]:
    """Deep merge two dicts. Lists append (deduped), dicts recurse, scalars replace."""
    result = dict(base)
    for key, child_val in child.items():
        if key in result:
            base_val = result[key]
            if isinstance(base_val, dict) and isinstance(child_val, dict):
                result[key] = deep_merge_dicts(base_val, child_val)
            elif isinstance(base_val, list) and isinstance(child_val, list):
                # Append then deduplicate preserving order
                result[key] = list(dict.fromkeys(base_val + child_val))
            else:
                result[key] = child_val
        else:
            result[key] = child_val
    return result


def _merge_quality_gates(
    parent: QualityGates | None,
    child: QualityGates | None,
) -> QualityGates | None:
    """Merge quality gates: child scalars replace parent scalars."""
    if parent is None:
        return child
    if child is None:
        return parent
    merged = {}
    for f in fields(QualityGates):
        child_val = getattr(child, f.name)
        merged[f.name] = child_val if child_val is not None else getattr(parent, f.name)
    return QualityGates(**merged)


def _merge_project_detection(
    parent: ProjectDetection,
    child: ProjectDetection,
) -> ProjectDetection:
    """Merge project detection: markers replace, deps/patterns append (deduped)."""
    return ProjectDetection(
        markers=child.markers if child.markers else parent.markers,
        required_dependencies=list(dict.fromkeys(
            parent.required_dependencies + child.required_dependencies
        )),
        source_patterns=parent.source_patterns + child.source_patterns,
        test_patterns=parent.test_patterns + child.test_patterns,
    )


def merge_manifests(parent: LanguageManifest, child: LanguageManifest) -> LanguageManifest:
    """Merge parent and child manifests following extends semantics.

    - Scalars (name, language, version, stack): child replaces parent
    - stage_skills: deep merge with list append per stage
    - quality_gates: child scalars replace parent scalars
    - project_detection: markers replace, deps/patterns append
    """
    merged_skills = deep_merge_dicts(parent.stage_skills, child.stage_skills)
    merged_gates = _merge_quality_gates(parent.quality_gates, child.quality_gates)
    merged_detection = _merge_project_detection(
        parent.project_detection, child.project_detection
    )

    return LanguageManifest(
        name=child.name,
        extends=None,  # extends is consumed during resolution
        language=child.language if child.language else parent.language,
        stack=child.stack if child.stack is not None else parent.stack,
        version=child.version if child.version else parent.version,
        project_detection=merged_detection,
        stage_skills=merged_skills,
        quality_gates=merged_gates,
    )


def _resolve_extends_ref(
    ref: str,
    child_path: Path,
    search_paths: list[tuple[str, Path]],
) -> Path:
    """Resolve an extends reference to a file path.

    Two forms:
    - Name-based: "plugin-name:manifest-name" -> search search_paths for manifest-name/language-manifest.yaml
      where plugin-name matches the canonical name from plugin.json (not path components)
    - Path-based: "./relative/path.yaml" -> resolve relative to child_path's parent

    Args:
        ref: The extends reference string.
        child_path: Path to the child manifest (for relative path resolution).
        search_paths: List of (canonical_plugin_name, manifests_dir) tuples
            from _collect_search_paths.
    """
    if ref.startswith("./") or ref.startswith("../"):
        resolved = (child_path.parent / ref).resolve()
        if not resolved.exists():
            msg = f"Extends path not found: {ref} (resolved to {resolved})"
            raise FileNotFoundError(msg)
        return resolved

    # Name-based: plugin-name:manifest-name
    if ":" in ref:
        plugin_name, manifest_name = ref.split(":", 1)
        # Filter search paths by canonical plugin name from plugin.json
        filtered_paths = [(n, p) for n, p in search_paths if n == plugin_name]
        if not filtered_paths:
            filtered_paths = search_paths  # Fallback to all paths
    else:
        manifest_name = ref
        filtered_paths = search_paths

    for _name, search_path in filtered_paths:
        candidate = search_path / manifest_name / "language-manifest.yaml"
        if candidate.exists():
            return candidate

    path_strs = [str(p) for _, p in search_paths]
    msg = f"Cannot resolve extends reference '{ref}' in search paths: {path_strs}"
    raise FileNotFoundError(msg)


def resolve_extends_chain(
    manifest_path: Path,
    search_paths: list[tuple[str, Path]],
    _seen: set[str] | None = None,
) -> LanguageManifest:
    """Recursively resolve the extends chain for a manifest.

    Each referenced manifest resolves its own extends first, then
    the child is merged on top.

    Args:
        manifest_path: Path to the manifest YAML file.
        search_paths: List of (canonical_plugin_name, manifests_dir) tuples
            from _collect_search_paths. Plugin names come from plugin.json.
        _seen: Internal cycle detection set.

    Returns:
        Fully resolved LanguageManifest with all extends chains flattened.

    Raises:
        CircularExtendsError: If a circular extends chain is detected.
    """
    if _seen is None:
        _seen = set()

    manifest = load_manifest(manifest_path)

    if manifest.name in _seen:
        msg = f"Circular extends chain detected: {manifest.name} already in chain {_seen}"
        raise CircularExtendsError(msg)
    _seen.add(manifest.name)

    if manifest.extends is None:
        return manifest

    # Normalize extends to a list
    extends_list: list[str] = (
        manifest.extends if isinstance(manifest.extends, list) else [manifest.extends]
    )

    # Resolve left to right, accumulating into a base
    resolved_base: LanguageManifest | None = None
    for ref in extends_list:
        parent_path = _resolve_extends_ref(ref, manifest_path, search_paths)
        # Share _seen across siblings so diamond inheritance loads each parent once
        parent_resolved = resolve_extends_chain(parent_path, search_paths, _seen)
        if resolved_base is None:
            resolved_base = parent_resolved
        else:
            resolved_base = merge_manifests(resolved_base, parent_resolved)

    if resolved_base is not None:
        return merge_manifests(resolved_base, manifest)
    return manifest
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /home/ubuntulinuxqa2/repos/claude_skills && uv run pytest plugins/development-harness/tests/test_manifest_merge.py -v`
Expected: All tests PASS

- [ ] **Step 5: Commit**

```text
feat(development-harness): add manifest extends resolution and merge logic
```

## Chunk 2: Manifest Discovery

### Task 4: Discovery Across Priority Levels

**Files:**

- Create: `plugins/development-harness/scripts/manifest_discovery.py`
- Test: `plugins/development-harness/tests/test_manifest_discovery.py`

- [ ] **Step 1: Write the failing tests**

Create `plugins/development-harness/tests/test_manifest_discovery.py`:

```python
"""Tests for manifest discovery across priority levels."""

from pathlib import Path
from textwrap import dedent

import pytest
from manifest_discovery import (
    MANIFEST_FILENAME,
    PriorityLevel,
    DiscoveredManifest,
    discover_manifests,
    detect_project_dependencies,
    select_best_manifest,
)


def _write_manifest(
    path: Path,
    name: str,
    markers: str = "pyproject.toml",
    required_dependencies: str = "",
) -> Path:
    """Helper to write a minimal manifest YAML."""
    deps_line = (
        f"\n      required_dependencies: [{required_dependencies}]"
        if required_dependencies
        else ""
    )
    content = dedent(f"""\
        name: {name}
        language: python
        version: "1.0"
        project_detection:
          markers: [{markers}]{deps_line}
    """)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
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

        results = discover_manifests(
            project_root=tmp_path,
            plugin_dirs=[],
            project_markers={"pyproject.toml"},
        )
        names = [r.manifest.name for r in results]
        assert "custom" in names

    def test_discover_filters_by_marker(self, tmp_path: Path) -> None:
        """Only discover manifests whose markers match the project."""
        plugin_dir = tmp_path / "plugins" / "ts" / "manifests" / "typescript"
        _write_manifest(
            plugin_dir / MANIFEST_FILENAME, "typescript", markers="package.json"
        )

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
            project_root=tmp_path,
            plugin_dirs=[tmp_path / "plugins" / "bad"],
            project_markers={"pyproject.toml"},
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
            project_root=tmp_path,
            plugin_dirs=[tmp_path / "plugins" / "py"],
            project_markers={"pyproject.toml"},
        )
        # Both should be found; project-level has higher priority
        project_results = [
            r for r in results if r.priority == PriorityLevel.PROJECT
        ]
        plugin_results = [
            r for r in results if r.priority == PriorityLevel.PLUGIN
        ]
        assert len(project_results) >= 1
        assert len(plugin_results) >= 1
        assert project_results[0].priority.value < plugin_results[0].priority.value


class TestDetectProjectDependencies:
    """Test dependency detection from project files."""

    def test_pyproject_toml_deps(self, tmp_path: Path) -> None:
        """Extract dependencies from pyproject.toml."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text(dedent("""\
            [project]
            dependencies = ["typer>=0.9", "rich", "httpx>=0.24"]
        """))
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
                project_detection=ProjectDetection(
                    markers=["pyproject.toml"],
                    required_dependencies=["typer"],
                ),
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
        from manifest_schema import LanguageManifest, ProjectDetection
        from manifest_resolver import _dedup_by_name_priority

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
                project_detection=ProjectDetection(
                    markers=["pyproject.toml"],
                    required_dependencies=["ruff"],
                ),
            ),
            path=tmp_path / "plugin.yaml",
            priority=PriorityLevel.PLUGIN,
        )
        deduped = _dedup_by_name_priority([project_m, plugin_m])
        assert len(deduped) == 1
        assert deduped[0].priority == PriorityLevel.PROJECT
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /home/ubuntulinuxqa2/repos/claude_skills && uv run pytest plugins/development-harness/tests/test_manifest_discovery.py -x`
Expected: FAIL with `ModuleNotFoundError: No module named 'manifest_discovery'`

- [ ] **Step 3: Write minimal implementation**

Create `plugins/development-harness/scripts/manifest_discovery.py`:

```python
"""Manifest discovery across priority levels.

Discovers language manifests from 5 priority levels (highest to lowest):
1. Enterprise (managed settings — future, not implemented)
2. Personal (~/.claude/manifests/)
3. Project (.claude/manifests/)
4. Plugin (plugins/*/manifests/)
5. Skill (plugins/*/skills/*/assets/ — most specific)
"""

import logging
import re
from dataclasses import dataclass
from enum import IntEnum
from pathlib import Path

from ruamel.yaml import YAMLError

from manifest_schema import LanguageManifest, ManifestValidationError, load_manifest

logger = logging.getLogger(__name__)

MANIFEST_FILENAME = "language-manifest.yaml"


class PriorityLevel(IntEnum):
    """Priority levels for manifest discovery.

    Lower numeric value = higher priority. Ordering contract:
    ENTERPRISE (1) > PERSONAL (2) > PROJECT (3) > PLUGIN (4) > SKILL (5).
    Values are compared numerically; do not reorder without updating
    all call sites that rely on ``value < other.value`` comparisons.
    """

    ENTERPRISE = 1  # Phase 2+ — managed settings, not yet implemented
    PERSONAL = 2
    PROJECT = 3
    PLUGIN = 4
    SKILL = 5


@dataclass(slots=True)
class DiscoveredManifest:
    """A manifest discovered at a specific priority level."""

    manifest: LanguageManifest
    path: Path
    priority: PriorityLevel


def _discover_from_directory(
    base_dir: Path,
    priority: PriorityLevel,
    project_markers: set[str],
) -> list[DiscoveredManifest]:
    """Discover manifests from a directory containing manifest-name/ subdirs."""
    results: list[DiscoveredManifest] = []
    if not base_dir.is_dir():
        return results

    for manifest_dir in sorted(base_dir.iterdir()):
        manifest_file = manifest_dir / MANIFEST_FILENAME
        if not manifest_file.is_file():
            continue
        try:
            manifest = load_manifest(manifest_file)
        except (ManifestValidationError, FileNotFoundError, ValueError, YAMLError) as exc:
            logger.warning("Skipping %s: %s", manifest_file, exc)
            continue

        # Filter: at least one marker must match the project
        if project_markers and not (
            set(manifest.project_detection.markers) & project_markers
        ):
            continue

        results.append(
            DiscoveredManifest(
                manifest=manifest,
                path=manifest_file,
                priority=priority,
            )
        )
    return results


def discover_manifests(
    project_root: Path,
    plugin_dirs: list[Path],
    project_markers: set[str],
    personal_dir: Path | None = None,
) -> list[DiscoveredManifest]:
    """Discover all matching manifests across priority levels.

    Args:
        project_root: Root of the project being analyzed.
        plugin_dirs: List of plugin directories (each is plugins/plugin-name/).
        project_markers: Set of marker filenames found in the project root.
        personal_dir: Override for personal manifests dir (default: ~/.claude/manifests/).

    Returns:
        List of DiscoveredManifest, unordered.
    """
    results: list[DiscoveredManifest] = []

    # TODO(phase2): enterprise manifest discovery — ENTERPRISE = 1 is declared
    # in PriorityLevel but has no discovery path yet. Enterprise manifests will
    # come from managed settings (organisation-level config). Skipped for Phase 1.

    # Level 2: Personal
    if personal_dir is None:
        personal_dir = Path.home() / ".claude" / "manifests"
    results.extend(
        _discover_from_directory(personal_dir, PriorityLevel.PERSONAL, project_markers)
    )

    # Level 3: Project
    project_manifests_dir = project_root / ".claude" / "manifests"
    results.extend(
        _discover_from_directory(
            project_manifests_dir, PriorityLevel.PROJECT, project_markers
        )
    )

    # Level 4: Plugin
    for plugin_dir in plugin_dirs:
        manifests_dir = plugin_dir / "manifests"
        results.extend(
            _discover_from_directory(manifests_dir, PriorityLevel.PLUGIN, project_markers)
        )

    # Level 5: Skill
    for plugin_dir in plugin_dirs:
        skills_dir = plugin_dir / "skills"
        if not skills_dir.is_dir():
            continue
        for skill_dir in sorted(skills_dir.iterdir()):
            assets_dir = skill_dir / "assets"
            manifest_file = assets_dir / MANIFEST_FILENAME
            if manifest_file.is_file():
                try:
                    manifest = load_manifest(manifest_file)
                except (ManifestValidationError, FileNotFoundError, ValueError, YAMLError) as exc:
                    logger.warning("Skipping %s: %s", manifest_file, exc)
                    continue
                if project_markers and not (
                    set(manifest.project_detection.markers) & project_markers
                ):
                    continue
                results.append(
                    DiscoveredManifest(
                        manifest=manifest,
                        path=manifest_file,
                        priority=PriorityLevel.SKILL,
                    )
                )

    return results


def detect_project_dependencies(project_root: Path) -> set[str]:
    """Detect project dependencies from pyproject.toml.

    Extracts package names (without version specifiers) from
    [project].dependencies in pyproject.toml.
    """
    pyproject = project_root / "pyproject.toml"
    if not pyproject.exists():
        return set()

    import tomlkit

    try:
        data = tomlkit.loads(pyproject.read_text())
    except (FileNotFoundError, tomlkit.exceptions.TOMLKitError) as exc:
        logger.warning("Cannot read dependencies from %s: %s", pyproject, exc)
        return set()

    deps_list = data.get("project", {}).get("dependencies", [])
    result: set[str] = set()
    for dep in deps_list:
        # Strip version specifiers: "typer>=0.9" -> "typer"
        name = re.split(r"[>=<!~\[;]", str(dep))[0].strip().lower()
        if name:
            result.add(name)
    return result


def select_best_manifest(
    candidates: list[DiscoveredManifest],
    actual_deps: set[str],
) -> DiscoveredManifest | None:
    """Select the best manifest by specificity scoring.

    Scoring: count of required_dependencies matching actual_deps.
    Tie-break: higher priority level (lower PriorityLevel value) wins.
    """
    if not candidates:
        return None

    def score_key(dm: DiscoveredManifest) -> tuple[int, int]:
        """Higher dep match score first, then higher priority (lower int)."""
        dep_score = dm.manifest.project_detection.specificity_score(actual_deps)
        # Negate priority so lower PriorityLevel value sorts first
        return (dep_score, -dm.priority.value)

    return max(candidates, key=score_key)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /home/ubuntulinuxqa2/repos/claude_skills && uv run pytest plugins/development-harness/tests/test_manifest_discovery.py -v`
Expected: All tests PASS

- [ ] **Step 5: Commit**

```text
feat(development-harness): add manifest discovery across priority levels
```

---

### Task 5: Full Resolution Pipeline (CLI)

**Files:**

- Create: `plugins/development-harness/scripts/manifest_resolver.py`
- Test: `plugins/development-harness/tests/test_manifest_resolver.py`

- [ ] **Step 1: Write the failing test**

Create `plugins/development-harness/tests/test_manifest_resolver.py`:

```python
"""Tests for the full manifest resolution pipeline.

Note: Imports resolve via [tool.pytest.ini_options] pythonpath in pyproject.toml.
"""

import json
from pathlib import Path
from textwrap import dedent

import pytest
from manifest_resolver import resolve_for_project


def _setup_project(tmp_path: Path) -> Path:
    """Create a mock Python/Typer project."""
    project = tmp_path / "myproject"
    project.mkdir()
    (project / "pyproject.toml").write_text(dedent("""\
        [project]
        dependencies = ["typer>=0.9", "rich"]
    """))
    return project


def _setup_manifests(tmp_path: Path) -> Path:
    """Create base and CLI manifests in a plugin dir."""
    plugin_dir = tmp_path / "plugins" / "python3-development"
    base_dir = plugin_dir / "manifests" / "python3"
    base_dir.mkdir(parents=True)
    (base_dir / "language-manifest.yaml").write_text(dedent("""\
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
    """))

    cli_dir = plugin_dir / "manifests" / "python3-cli"
    cli_dir.mkdir(parents=True)
    (cli_dir / "language-manifest.yaml").write_text(dedent("""\
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
    """))
    return plugin_dir


class TestResolveForProject:
    """Test end-to-end resolution pipeline."""

    def test_selects_cli_for_typer_project(self, tmp_path: Path) -> None:
        project = _setup_project(tmp_path)
        plugin_dir = _setup_manifests(tmp_path)

        result = resolve_for_project(
            project_root=project,
            plugin_dirs=[plugin_dir],
        )
        assert result is not None
        assert result.name == "python3-cli"
        assert result.stack == "typer-cli"
        # extends should be resolved — implementation has both parent and child skills
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
        (project / "pyproject.toml").write_text(dedent("""\
            [project]
            dependencies = ["requests"]
        """))
        plugin_dir = _setup_manifests(tmp_path)

        result = resolve_for_project(
            project_root=project,
            plugin_dirs=[plugin_dir],
        )
        assert result is not None
        assert result.name == "python3"

    def test_no_matching_manifest(self, tmp_path: Path) -> None:
        """Project with no matching markers returns None."""
        project = tmp_path / "rust-project"
        project.mkdir()
        (project / "Cargo.toml").write_text("[package]\nname = 'foo'\n")
        plugin_dir = _setup_manifests(tmp_path)

        result = resolve_for_project(
            project_root=project,
            plugin_dirs=[plugin_dir],
        )
        assert result is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /home/ubuntulinuxqa2/repos/claude_skills && uv run pytest plugins/development-harness/tests/test_manifest_resolver.py -x`
Expected: FAIL with `ModuleNotFoundError: No module named 'manifest_resolver'`

- [ ] **Step 3: Write minimal implementation**

Create `plugins/development-harness/scripts/manifest_resolver.py`:

```python
#!/usr/bin/env -S uv --quiet run --active --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["ruamel.yaml", "tomlkit", "typer", "rich"]
# ///
"""Manifest resolver CLI — discover, score, resolve, return manifest.

Usage:
    uv run manifest_resolver.py resolve /path/to/project [--plugin-dir DIR]...
    uv run manifest_resolver.py show /path/to/manifest.yaml
"""

import json
from dataclasses import asdict
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

from manifest_discovery import (
    DiscoveredManifest,
    detect_project_dependencies,
    discover_manifests,
    select_best_manifest,
)
from manifest_merge import resolve_extends_chain
from manifest_schema import LanguageManifest, ManifestValidationError, load_manifest

app = typer.Typer(help="Language manifest resolver for the development harness.")
console = Console(stderr=True)


def _detect_project_markers(
    project_root: Path,
    plugin_dirs: list[Path] | None = None,
) -> set[str]:
    """Detect which marker files exist in the project root.

    Derives known markers from loaded manifests when plugin_dirs are provided,
    falling back to a minimal default set for bootstrapping.
    """
    # Minimal fallback set for when no manifests are available yet
    known_markers = {"pyproject.toml", "package.json", "Cargo.toml", "go.mod"}

    # Derive additional markers from discovered manifests
    if plugin_dirs:
        for pd in plugin_dirs:
            manifests_dir = pd / "manifests"
            if not manifests_dir.is_dir():
                continue
            for manifest_dir in manifests_dir.iterdir():
                manifest_file = manifest_dir / "language-manifest.yaml"
                if manifest_file.is_file():
                    try:
                        m = load_manifest(manifest_file)
                        known_markers.update(m.project_detection.markers)
                    except (FileNotFoundError, ValueError, ManifestValidationError):
                        continue

    return {m for m in known_markers if (project_root / m).exists()}


def _read_plugin_name(plugin_dir: Path) -> str | None:
    """Read the canonical plugin name from plugin.json.

    Returns the 'name' field from .claude-plugin/plugin.json or
    plugin.json, or None if neither exists or is unreadable.
    """
    for candidate in (plugin_dir / ".claude-plugin" / "plugin.json", plugin_dir / "plugin.json"):
        if candidate.is_file():
            try:
                import json
                data = json.loads(candidate.read_text())
                return data.get("name")
            except (json.JSONDecodeError, OSError):
                continue
    return None


def _collect_search_paths(
    plugin_dirs: list[Path],
    project_root: Path | None = None,
    personal_dir: Path | None = None,
) -> list[tuple[str, Path]]:
    """Collect all manifest search paths with their canonical plugin names.

    Returns (plugin_name, manifests_path) tuples. For project-level and
    personal-level paths, plugin_name is "__project__" or "__personal__"
    respectively (synthetic names that cannot collide with real plugins).

    Includes all 5 priority levels (except enterprise, deferred to Phase 2):
    - Personal: ~/.claude/manifests/
    - Project: .claude/manifests/
    - Plugin: plugins/*/manifests/
    - Skill-level paths are not included here (handled by discover_manifests)
    """
    paths: list[tuple[str, Path]] = []

    # Personal-level manifests
    if personal_dir is None:
        personal_dir = Path.home() / ".claude" / "manifests"
    if personal_dir.is_dir():
        paths.append(("__personal__", personal_dir))

    # Project-level manifests
    if project_root is not None:
        project_manifests = project_root / ".claude" / "manifests"
        if project_manifests.is_dir():
            paths.append(("__project__", project_manifests))

    # Plugin-level manifests — use canonical name from plugin.json
    for pd in plugin_dirs:
        manifests_dir = pd / "manifests"
        if manifests_dir.is_dir():
            plugin_name = _read_plugin_name(pd) or pd.name
            paths.append((plugin_name, manifests_dir))

    return paths


def _dedup_by_name_priority(
    candidates: list[DiscoveredManifest],
) -> list[DiscoveredManifest]:
    """Deduplicate manifests by name, keeping highest priority (lowest int).

    Architecture spec: "Higher-priority locations win when manifests share
    the same name." This dedup happens BEFORE scoring by specificity.
    """
    best_by_name: dict[str, DiscoveredManifest] = {}
    for dm in candidates:
        name = dm.manifest.name
        if name not in best_by_name or dm.priority.value < best_by_name[name].priority.value:
            best_by_name[name] = dm
    return list(best_by_name.values())


def resolve_for_project(
    project_root: Path,
    plugin_dirs: list[Path],
    personal_dir: Path | None = None,
) -> LanguageManifest | None:
    """Full resolution pipeline: discover -> dedup by name -> score -> select -> resolve extends.

    Returns the fully resolved manifest for the project, or None if no
    matching manifest is found.
    """
    markers = _detect_project_markers(project_root, plugin_dirs)
    if not markers:
        return None

    candidates = discover_manifests(
        project_root=project_root,
        plugin_dirs=plugin_dirs,
        project_markers=markers,
        personal_dir=personal_dir,
    )
    if not candidates:
        return None

    # Dedup same-name manifests by priority BEFORE scoring (C2)
    candidates = _dedup_by_name_priority(candidates)

    actual_deps = detect_project_dependencies(project_root)
    best = select_best_manifest(candidates, actual_deps)
    if best is None:
        return None

    # Collect search paths from all 5 levels (C3) — includes personal + project
    search_paths = _collect_search_paths(
        plugin_dirs, project_root=project_root, personal_dir=personal_dir
    )
    resolved = resolve_extends_chain(best.path, search_paths=search_paths)
    return resolved


def _normalize_for_json(obj: object) -> object:
    """Recursively normalize types for JSON serialization."""
    if isinstance(obj, dict):
        return {str(k): _normalize_for_json(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_normalize_for_json(item) for item in obj]
    if isinstance(obj, set):
        return sorted(str(item) for item in obj)
    if isinstance(obj, Path):
        return str(obj)
    return obj


def _manifest_to_dict(m: LanguageManifest) -> dict:
    """Convert manifest to a JSON-serializable dict."""
    raw = asdict(m)
    return _normalize_for_json(raw)


def _validate_plugin_dir(path: Path) -> Path:
    """Typer callback to validate --plugin-dir exists and is a directory."""
    if not path.is_dir():
        msg = f"Plugin directory does not exist or is not a directory: {path}"
        raise typer.BadParameter(msg)
    return path


@app.command()
def resolve(
    project_root: Annotated[
        Path, typer.Argument(help="Path to the project root")
    ],
    plugin_dir: Annotated[
        list[Path],
        typer.Option(
            "--plugin-dir",
            help="Plugin directories to search for manifests",
            callback=_validate_plugin_dir,
        ),
    ] = [],
) -> None:
    """Resolve the best manifest for a project and print as JSON."""
    result = resolve_for_project(project_root, plugin_dir)
    if result is None:
        console.print("[yellow]No matching manifest found.[/yellow]")
        raise typer.Exit(1)

    print(json.dumps(_manifest_to_dict(result), indent=2))


@app.command()
def show(
    manifest_path: Annotated[
        Path, typer.Argument(help="Path to a manifest YAML file")
    ],
) -> None:
    """Load and display a single manifest as JSON (no extends resolution)."""
    m = load_manifest(manifest_path)
    print(json.dumps(_manifest_to_dict(m), indent=2))


if __name__ == "__main__":
    app()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /home/ubuntulinuxqa2/repos/claude_skills && uv run pytest plugins/development-harness/tests/test_manifest_resolver.py -v`
Expected: All tests PASS

- [ ] **Step 5: Commit**

```text
feat(development-harness): add manifest resolver CLI with full pipeline
```

## Chunk 3: Language Manifests

### Task 6: Base `python3` Language Manifest YAML

**Files:**

- Create: `plugins/python3-development/manifests/python3/language-manifest.yaml`

- [ ] **Step 1: Create the base python3 manifest**

Create `plugins/python3-development/manifests/python3/language-manifest.yaml`:

```yaml
name: python3
language: python
version: "1.0"

project_detection:
  markers: [pyproject.toml, setup.py, setup.cfg]
  source_patterns: ["src/**/*.py", "**/*.py"]
  test_patterns: ["tests/**/*.py", "test_*.py", "*_test.py"]

stage_skills:
  discovery: [python3-discovery]
  design: [python3-design]
  planning-context-integration: [python3-implementation]
  planning-task-decomposition: [python3-planning-task-decomposition]
  implementation: [python3-implementation]
  testing-forensic-review: [python3-testing-forensic-review]
  testing-verification: [python3-testing]

# Quality gate commands. {files} is a template variable substituted at
# dispatch time via str.format(files=...) with the list of affected files.
quality_gates:
  format: "uv run ruff format {files}"
  lint: "uv run ruff check {files}"
  typecheck: "uv run mypy {files}"
  test: "uv run pytest tests/ --tb=short"
  standards: "/python3-development:modernpython"
```

- [ ] **Step 2: Validate the manifest loads**

Run: `cd /home/ubuntulinuxqa2/repos/claude_skills && uv run plugins/development-harness/scripts/manifest_resolver.py show plugins/python3-development/manifests/python3/language-manifest.yaml`
Expected: JSON output with name "python3", all stage_skills populated

- [ ] **Step 3: Commit**

```text
feat(python3-development): add base python3 language manifest YAML
```

---

### Task 7: `python3-cli` Manifest Extending Base

**Files:**

- Create: `plugins/python3-development/manifests/python3-cli/language-manifest.yaml`

- [ ] **Step 1: Create the python3-cli manifest**

Create `plugins/python3-development/manifests/python3-cli/language-manifest.yaml`:

```yaml
name: python3-cli
extends: python3-development:python3
language: python
stack: typer-cli
version: "1.0"

project_detection:
  markers: [pyproject.toml]
  required_dependencies: [typer]

stage_skills:
  design: [python3-design-cli]
  implementation: [python3-implementation-cli]
```

- [ ] **Step 2: Validate extends resolution**

Run: `cd /home/ubuntulinuxqa2/repos/claude_skills && uv run plugins/development-harness/scripts/manifest_resolver.py show plugins/python3-development/manifests/python3-cli/language-manifest.yaml`
Expected: JSON output with name "python3-cli", extends "python3-development:python3"

- [ ] **Step 3: Commit**

```text
feat(python3-development): add python3-cli manifest extending base
```

---

### Task 8: Integration Test — Resolve Manifest for Mock Typer Project

**Files:**

- Modify: `plugins/development-harness/tests/test_manifest_resolver.py` (add integration test using real manifest files)

- [ ] **Step 1: Write the integration test**

Append to `plugins/development-harness/tests/test_manifest_resolver.py`:

```python
class TestRealManifestResolution:
    """Integration test using actual manifest files from the repo."""

    @pytest.fixture()
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
        pytest.skip("Cannot find repo root within 10 parent directories")

    def test_resolve_with_real_manifests(self, repo_root: Path, tmp_path: Path) -> None:
        """Create a mock Typer project and resolve against real manifests."""
        # Create a mock project with typer dependency
        project = tmp_path / "typer-app"
        project.mkdir()
        (project / "pyproject.toml").write_text(dedent("""\
            [project]
            name = "my-cli"
            dependencies = ["typer>=0.9", "rich"]
        """))

        plugin_dir = repo_root / "plugins" / "python3-development"
        if not (plugin_dir / "manifests" / "python3").exists():
            pytest.skip("Real manifests not yet created")

        result = resolve_for_project(
            project_root=project,
            plugin_dirs=[plugin_dir],
        )
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
        (project / "pyproject.toml").write_text(dedent("""\
            [project]
            name = "my-lib"
            dependencies = ["requests"]
        """))

        plugin_dir = repo_root / "plugins" / "python3-development"
        if not (plugin_dir / "manifests" / "python3").exists():
            pytest.skip("Real manifests not yet created")

        result = resolve_for_project(
            project_root=project,
            plugin_dirs=[plugin_dir],
        )
        assert result is not None
        assert result.name == "python3"
```

- [ ] **Step 2: Run integration test**

Run: `cd /home/ubuntulinuxqa2/repos/claude_skills && uv run pytest plugins/development-harness/tests/test_manifest_resolver.py::TestRealManifestResolution -v`
Expected: Both tests PASS (or skip if manifests not yet created)

- [ ] **Step 3: Commit**

```text
test(development-harness): add integration tests for real manifest resolution
```

## Chunk 4: Generic Agent and Proof-of-Concept

### Task 9: Generic Stage Agent Markdown

**Files:**

- Create: `plugins/development-harness/agents/generic-stage-agent.md`

- [ ] **Step 1: Create the generic stage agent**

Create `plugins/development-harness/agents/generic-stage-agent.md`:

```markdown
---
name: generic-stage-agent
description: Generic SDLC stage agent that executes workflow steps using loaded domain skills and quality gates
tools:
  - Read
  - Write
  - Edit
  - Bash
  - Grep
  - Glob
  - Skill
model: sonnet
---

# Generic Stage Agent

You are a generic development stage agent. You execute a specific SDLC stage by following a workflow and applying domain knowledge from loaded skills.

## Inputs You Receive

You receive 5 inputs in your dispatch prompt:

1. **Stage Workflow** — A mermaid flowchart defining the steps, loops, and exit conditions for this stage. Follow it mechanically.
2. **Cross-Cutting Stage Skill** — An SDLC stage skill from the development harness (e.g., software-architecture-planning). Load it with `Skill(skill="...")`.
3. **Domain Skills** — Language/framework-specific skills from the resolved manifest (e.g., python3-implementation, python3-implementation-cli). Load each with `Skill(skill="...")`. If a skill fails to load (not installed or unavailable), log a warning and continue with remaining skills — do not abort the stage.
4. **Task/Artifact File** — The input artifact from the previous stage. Read it to understand what you are working on.
5. **Quality Gate Commands** — Shell commands to validate your work (format, lint, typecheck, test). Run ALL of them before declaring completion. Commands containing `{files}` use Python `str.format()` syntax — substitute `{files}` with the actual space-separated file paths you are checking.

## Execution Protocol

1. Load all skills specified in inputs 2 and 3
2. Read the task/artifact file (input 4)
3. Follow the stage workflow mermaid (input 1) step by step
4. Apply domain knowledge from loaded skills at each step
5. Run quality gate commands (input 5) before completing
6. If any quality gate fails, fix the issues and re-run
7. Write your output artifact to the path specified in the dispatch prompt

## Constraints

- Follow the workflow mermaid exactly — do not skip steps or reorder
- Domain skills provide the knowledge — you provide the execution
- Quality gates are mandatory — never skip them
- If a step is unclear, read the loaded skill documentation before proceeding
- Write output artifacts as files, not conversation responses
```

- [ ] **Step 2: Validate the agent file parses**

Run: `cd /home/ubuntulinuxqa2/repos/claude_skills && uv run python3 -c "from ruamel.yaml import YAML; y=YAML(); data=y.load(open('plugins/development-harness/agents/generic-stage-agent.md').read().split('---')[1]); print(data['name'])"`
Expected: `generic-stage-agent`

- [ ] **Step 3: Commit**

```text
feat(development-harness): add generic stage agent markdown
```

---

### Task 10: Dispatch Helper

**Files:**

- Create: `plugins/development-harness/scripts/dispatch_helper.py`
- Test: `plugins/development-harness/tests/test_dispatch_helper.py`

- [ ] **Step 1: Write the failing test**

Create `plugins/development-harness/tests/test_dispatch_helper.py`:

```python
"""Tests for the dispatch helper that assembles 5 inputs for generic agent."""

from pathlib import Path
from textwrap import dedent

import pytest
from dispatch_helper import build_dispatch_prompt
from manifest_schema import LanguageManifest, ProjectDetection, QualityGates


class TestBuildDispatchPrompt:
    """Test dispatch prompt assembly."""

    def test_basic_dispatch(self) -> None:
        """Build a dispatch prompt with all 5 inputs."""
        manifest = LanguageManifest(
            name="python3-cli",
            language="python",
            version="1.0",
            project_detection=ProjectDetection(markers=["pyproject.toml"]),
            stage_skills={
                "implementation": ["python3-implementation", "python3-implementation-cli"],
            },
            quality_gates=QualityGates(
                format="uv run ruff format {files}",
                lint="uv run ruff check {files}",
                test="uv run pytest tests/",
            ),
        )
        prompt = build_dispatch_prompt(
            stage="implementation",
            manifest=manifest,
            task_file="plan/tasks-1-auth/T1.md",
            stage_workflow_skill="development-harness:execution",
            cross_cutting_skill="development-harness:implementation",
        )

        # Verify all 5 inputs are present
        assert "development-harness:execution" in prompt
        assert "development-harness:implementation" in prompt
        assert "python3-implementation" in prompt
        assert "python3-implementation-cli" in prompt
        assert "plan/tasks-1-auth/T1.md" in prompt
        assert "uv run ruff format" in prompt
        assert "uv run ruff check" in prompt
        assert "uv run pytest" in prompt

    def test_stage_without_skills(self) -> None:
        """Stage not in manifest stage_skills should still produce a prompt."""
        manifest = LanguageManifest(
            name="python3",
            language="python",
            version="1.0",
            project_detection=ProjectDetection(markers=["pyproject.toml"]),
            stage_skills={},
        )
        prompt = build_dispatch_prompt(
            stage="discovery",
            manifest=manifest,
            task_file="plan/task.md",
            stage_workflow_skill="development-harness:discovery",
            cross_cutting_skill=None,
        )
        assert "development-harness:discovery" in prompt
        no_skills_indicators = [
            "No domain skills" in prompt,
            "domain_skills: []" in prompt.lower(),
            "none" in prompt.lower(),
        ]
        assert any(no_skills_indicators), (
            f"Expected prompt to indicate no domain skills, got: {prompt[:200]}"
        )

    def test_no_quality_gates(self) -> None:
        """Manifest without quality gates should note it in the prompt."""
        manifest = LanguageManifest(
            name="python3",
            language="python",
            version="1.0",
            project_detection=ProjectDetection(markers=["pyproject.toml"]),
        )
        prompt = build_dispatch_prompt(
            stage="discovery",
            manifest=manifest,
            task_file="plan/task.md",
            stage_workflow_skill="development-harness:discovery",
            cross_cutting_skill=None,
        )
        assert "plan/task.md" in prompt

    def test_output_artifact_path_included(self) -> None:
        """I5: Dispatch prompt should include the output artifact path."""
        manifest = LanguageManifest(
            name="python3",
            language="python",
            version="1.0",
            project_detection=ProjectDetection(markers=["pyproject.toml"]),
            stage_skills={"implementation": ["python3-implementation"]},
        )
        from pathlib import Path as P
        prompt = build_dispatch_prompt(
            stage="implementation",
            manifest=manifest,
            task_file="plan/task.md",
            stage_workflow_skill="development-harness:execution",
            cross_cutting_skill=None,
            output_artifact_path=P("plan/output/T1-result.md"),
        )
        assert "plan/output/T1-result.md" in prompt

    def test_files_template_variable_documented(self) -> None:
        """N5: Dispatch prompt should document {files} template variable contract."""
        manifest = LanguageManifest(
            name="python3",
            language="python",
            version="1.0",
            project_detection=ProjectDetection(markers=["pyproject.toml"]),
            quality_gates=QualityGates(lint="uv run ruff check {files}"),
        )
        prompt = build_dispatch_prompt(
            stage="implementation",
            manifest=manifest,
            task_file="plan/task.md",
            stage_workflow_skill="development-harness:execution",
            cross_cutting_skill=None,
        )
        assert "{files}" in prompt or "files" in prompt.lower()
        # Should explain the substitution protocol
        assert "substitute" in prompt.lower() or "format" in prompt.lower()

    def test_prompt_contains_skill_load_instructions(self) -> None:
        """Prompt should contain Skill() call instructions."""
        manifest = LanguageManifest(
            name="python3-cli",
            language="python",
            version="1.0",
            project_detection=ProjectDetection(markers=["pyproject.toml"]),
            stage_skills={
                "implementation": ["python3-implementation"],
            },
        )
        prompt = build_dispatch_prompt(
            stage="implementation",
            manifest=manifest,
            task_file="plan/task.md",
            stage_workflow_skill="development-harness:execution",
            cross_cutting_skill="development-harness:implementation",
        )
        # Should contain instructions to load skills
        assert "Skill(" in prompt or "skill=" in prompt.lower()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /home/ubuntulinuxqa2/repos/claude_skills && uv run pytest plugins/development-harness/tests/test_dispatch_helper.py -x`
Expected: FAIL with `ModuleNotFoundError: No module named 'dispatch_helper'`

- [ ] **Step 3: Write minimal implementation**

Create `plugins/development-harness/scripts/dispatch_helper.py`:

```python
"""Dispatch helper — assembles the 5 inputs for generic agent dispatch.

The generic stage agent receives:
1. Stage workflow skill (from dh)
2. Cross-cutting SDLC stage skill (from dh)
3. Domain skills (from resolved manifest stage_skills)
4. Task/artifact file path
5. Quality gate commands (from resolved manifest quality_gates)
6. Output artifact path (where to write results)
"""

from pathlib import Path
from textwrap import dedent

from manifest_schema import LanguageManifest


def _format_quality_gates(manifest: LanguageManifest) -> str:
    """Format quality gates as runnable commands."""
    if manifest.quality_gates is None:
        return "No quality gates configured."

    gates: list[str] = []
    qg = manifest.quality_gates
    if qg.format:
        gates.append(f"- Format: `{qg.format}`")
    if qg.lint:
        gates.append(f"- Lint: `{qg.lint}`")
    if qg.typecheck:
        gates.append(f"- Typecheck: `{qg.typecheck}`")
    if qg.test:
        gates.append(f"- Test: `{qg.test}`")
    if qg.standards:
        gates.append(f"- Standards: Load skill `{qg.standards}`")

    if not gates:
        return "No quality gates configured."
    return "\n".join(gates)


def _format_skill_loads(skills: list[str]) -> str:
    """Format skill loading instructions."""
    if not skills:
        return "No domain skills for this stage."
    lines: list[str] = []
    for skill in skills:
        lines.append(f'- Load: `Skill(skill="{skill}")`')
    return "\n".join(lines)


def build_dispatch_prompt(
    stage: str,
    manifest: LanguageManifest,
    task_file: str,
    stage_workflow_skill: str,
    cross_cutting_skill: str | None,
    output_artifact_path: Path | None = None,
) -> str:
    """Build the dispatch prompt for a generic stage agent.

    Assembles all 5 inputs (plus output path) into a structured prompt
    that the generic stage agent can follow mechanically.

    Args:
        stage: The SDLC stage identifier (e.g., "implementation").
        manifest: The fully resolved language manifest.
        task_file: Path to the task/artifact file.
        stage_workflow_skill: Skill name for the stage workflow (e.g., "development-harness:execution").
        cross_cutting_skill: Optional cross-cutting SDLC skill name.
        output_artifact_path: Where the agent should write its output artifact.
            If None, the agent writes output next to the task file.

    Returns:
        Formatted dispatch prompt string.
    """
    domain_skills = manifest.stage_skills.get(stage, [])

    cross_cutting_section = (
        dedent(f"""\
            ## Input 2: Cross-Cutting Stage Skill
            Load: `Skill(skill="{cross_cutting_skill}")`
            This provides SDLC-stage-level guidance applicable across all languages.""")
        if cross_cutting_skill
        else dedent("""\
            ## Input 2: Cross-Cutting Stage Skill
            No cross-cutting skill for this stage.""")
    )

    template = dedent(f"""\
        # Stage Dispatch: {stage}
        **Language:** {manifest.language} | **Stack:** {manifest.stack or 'base'} | **Manifest:** {manifest.name}

        ## Input 1: Stage Workflow
        Load the stage workflow skill: `Skill(skill="{stage_workflow_skill}")`
        Follow the workflow mermaid from this skill step by step.

        {cross_cutting_section}

        ## Input 3: Domain Skills
        {_format_skill_loads(domain_skills)}

        ## Input 4: Task/Artifact File
        Read this file for your task context: `{task_file}`

        ## Input 5: Quality Gates
        Run ALL of these before declaring completion:
        {_format_quality_gates(manifest)}

        **Note on `{{files}}` in quality gate commands**: Commands containing `{{files}}`
        use Python `str.format()` syntax. Substitute `{{files}}` with the actual
        space-separated file paths you are checking before running the command.

        ## Output Artifact
        Write your output artifact to: `{output_artifact_path or 'next to the task file'}`""")

    return template
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /home/ubuntulinuxqa2/repos/claude_skills && uv run pytest plugins/development-harness/tests/test_dispatch_helper.py -v`
Expected: All tests PASS

- [ ] **Step 5: Commit**

```text
feat(development-harness): add dispatch helper for generic agent prompt assembly
```

---

### Task 11: Proof-of-Concept End-to-End Test

**Files:**

- Create: `plugins/development-harness/tests/test_proof_of_concept.py`

This test validates the full pipeline: resolve manifest for a Python/Typer project, build a dispatch prompt for the implementation stage, and verify all 5 inputs are correctly assembled.

- [ ] **Step 1: Write the proof-of-concept test**

Create `plugins/development-harness/tests/test_proof_of_concept.py`:

```python
"""Proof-of-concept: end-to-end manifest resolution + dispatch prompt assembly.

Validates that a generic harness agent can be dispatched with the correct
5 inputs for a Python/Typer project at the implementation stage.

Note: _setup_mock_project and _setup_manifests duplicate logic from
test_manifest_resolver.py. Extract to shared fixtures in conftest.py
when adding more integration tests (see L7 in code review).
"""

from pathlib import Path
from textwrap import dedent

import pytest
from dispatch_helper import build_dispatch_prompt
from manifest_resolver import resolve_for_project


class TestProofOfConcept:
    """End-to-end: resolve manifest -> build dispatch prompt."""

    def _setup_mock_project(self, tmp_path: Path) -> Path:
        """Create a minimal Typer project."""
        project = tmp_path / "my-cli"
        project.mkdir()
        (project / "pyproject.toml").write_text(dedent("""\
            [project]
            name = "my-cli"
            version = "0.1.0"
            dependencies = ["typer>=0.9", "rich"]
        """))
        (project / "src").mkdir()
        (project / "src" / "main.py").write_text("import typer\napp = typer.Typer()\n")
        return project

    def _setup_manifests(self, tmp_path: Path) -> Path:
        """Create base and CLI manifests."""
        plugin_dir = tmp_path / "plugins" / "python3-development"
        base = plugin_dir / "manifests" / "python3"
        base.mkdir(parents=True)
        (base / "language-manifest.yaml").write_text(dedent("""\
            name: python3
            language: python
            version: "1.0"
            project_detection:
              markers: [pyproject.toml]
            stage_skills:
              discovery: [python3-discovery]
              implementation: [python3-implementation]
            quality_gates:
              format: "uv run ruff format {files}"
              lint: "uv run ruff check {files}"
              typecheck: "uv run mypy {files}"
              test: "uv run pytest tests/ --tb=short"
              standards: "/python3-development:modernpython"
        """))

        cli = plugin_dir / "manifests" / "python3-cli"
        cli.mkdir(parents=True)
        (cli / "language-manifest.yaml").write_text(dedent("""\
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
        """))
        return plugin_dir

    def test_full_pipeline(self, tmp_path: Path) -> None:
        """Resolve manifest for Typer project, then build dispatch prompt."""
        project = self._setup_mock_project(tmp_path)
        plugin_dir = self._setup_manifests(tmp_path)

        # Step 1: Resolve manifest
        manifest = resolve_for_project(
            project_root=project,
            plugin_dirs=[plugin_dir],
        )
        assert manifest is not None
        assert manifest.name == "python3-cli"
        assert manifest.stack == "typer-cli"

        # Verify extends resolution worked
        assert "python3-implementation" in manifest.stage_skills["implementation"]
        assert "python3-implementation-cli" in manifest.stage_skills["implementation"]
        assert manifest.quality_gates is not None
        assert manifest.quality_gates.lint == "uv run ruff check {files}"

        # Step 2: Build dispatch prompt for implementation stage
        prompt = build_dispatch_prompt(
            stage="implementation",
            manifest=manifest,
            task_file="plan/tasks-1-my-cli/T1-add-cli-entrypoint.md",
            stage_workflow_skill="development-harness:execution",
            cross_cutting_skill="development-harness:implementation",
        )

        # Verify all 5 inputs present in prompt
        # Input 1: Stage workflow skill
        assert "development-harness:execution" in prompt

        # Input 2: Cross-cutting skill
        assert "development-harness:implementation" in prompt

        # Input 3: Domain skills from resolved manifest
        assert "python3-implementation" in prompt
        assert "python3-implementation-cli" in prompt

        # Input 4: Task file
        assert "plan/tasks-1-my-cli/T1-add-cli-entrypoint.md" in prompt

        # Input 5: Quality gates
        assert "uv run ruff format" in prompt
        assert "uv run ruff check" in prompt
        assert "uv run mypy" in prompt
        assert "uv run pytest" in prompt

        # Verify metadata
        assert "python" in prompt.lower()
        assert "typer-cli" in prompt

    def test_base_manifest_dispatch(self, tmp_path: Path) -> None:
        """Vanilla Python project resolves to base manifest."""
        project = tmp_path / "vanilla"
        project.mkdir()
        (project / "pyproject.toml").write_text(dedent("""\
            [project]
            name = "my-lib"
            dependencies = ["requests"]
        """))
        plugin_dir = self._setup_manifests(tmp_path)

        manifest = resolve_for_project(
            project_root=project,
            plugin_dirs=[plugin_dir],
        )
        assert manifest is not None
        assert manifest.name == "python3"

        prompt = build_dispatch_prompt(
            stage="implementation",
            manifest=manifest,
            task_file="plan/task.md",
            stage_workflow_skill="development-harness:execution",
            cross_cutting_skill=None,
        )
        # Only base skill, no CLI skill
        assert "python3-implementation" in prompt
        assert "python3-implementation-cli" not in prompt
```

- [ ] **Step 2: Run the proof-of-concept test**

Run: `cd /home/ubuntulinuxqa2/repos/claude_skills && uv run pytest plugins/development-harness/tests/test_proof_of_concept.py -v`
Expected: All tests PASS

- [ ] **Step 3: Run all tests together**

Run: `cd /home/ubuntulinuxqa2/repos/claude_skills && uv run pytest plugins/development-harness/tests/ -v --tb=short`
Expected: All tests across all test files PASS

- [ ] **Step 4: Commit**

```text
feat(development-harness): add proof-of-concept end-to-end test for manifest dispatch
```

---

## Final Verification

After all tasks complete:

- [ ] Run full test suite: `uv run pytest plugins/development-harness/tests/ -v`
- [ ] Run linting: `uv run ruff check plugins/development-harness/scripts/ plugins/development-harness/tests/`
- [ ] Run formatting: `uv run ruff format --check plugins/development-harness/scripts/ plugins/development-harness/tests/`
- [ ] Verify CLI works: `uv run plugins/development-harness/scripts/manifest_resolver.py resolve . --plugin-dir plugins/python3-development`
- [ ] Verify no YAML parse errors in manifest files
- [ ] Verify design review fixes:
  - [ ] C1: `_resolve_extends_ref` filters by canonical plugin name from `plugin.json`, not path components
  - [ ] C2: Same-name manifests are deduped by priority before scoring (`_dedup_by_name_priority`)
  - [ ] C3: `_collect_search_paths` includes personal + project directories, not just plugin dirs
  - [ ] C4: `ENTERPRISE = 1` has deferral comment; `discover_manifests` has TODO(phase2) comment
  - [ ] I3: `_merge_project_detection` deduplicates `required_dependencies` via `dict.fromkeys`
  - [ ] I4: `deep_merge_dicts` deduplicates lists after append via `dict.fromkeys`
  - [ ] I5: `build_dispatch_prompt` includes `output_artifact_path` parameter and output section
  - [ ] I7: `load_manifest` catches `YAMLError`; `_discover_from_directory` catches `YAMLError`
  - [ ] N3: `load_manifest` calls `validate_manifest` after parsing; raises on errors
  - [ ] N5: `{files}` template variable contract documented in dispatch prompt and agent instructions
- [ ] Final commit with all remaining changes
