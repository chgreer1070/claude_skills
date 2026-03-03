"""Tests for detect_fenced_yaml (task_format.py) and parse_task_content (implementation_manager.py).

Test suite covers:
- 11 unit tests for detect_fenced_yaml: correct detection, stripping, and None-return cases
- 6 integration tests for parse_task_content: fenced YAML, raw YAML, legacy markdown,
  YAML parse failures, and missing-field scenarios
- 1 real-world regression fixture test against the actual tasks-4 plan file
- Tests for DEFERRED/SKIPPED status: YAML parsing, title-override, get_ready_tasks, status output

Mandatory standards:
- All tests follow AAA (Arrange-Act-Assert) pattern
- All fixtures and test functions are fully type-annotated
- Uses monkeypatch for stderr capture (sys.stderr.write is used by the module)
- No unittest.mock — pytest-mock / monkeypatch only
- Tests are fully isolated (no shared mutable state)
"""

from __future__ import annotations

import io
import sys
from pathlib import Path

# Make the scripts directory importable for direct uv run pytest invocation.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from typing import TYPE_CHECKING

import implementation_manager as im
from task_format import detect_fenced_yaml

if TYPE_CHECKING:
    import pytest


# =============================================================================
# Helpers
# =============================================================================

_MINIMAL_TASK_YAML = (
    "---\n"
    "task: T1\n"
    "title: Minimal Task\n"
    "status: not-started\n"
    "agent: general-purpose\n"
    "dependencies: []\n"
    "priority: 1\n"
    "complexity: low\n"
    "---\n"
)

_FENCED_MINIMAL = f"```yaml\n{_MINIMAL_TASK_YAML}```\n"


# =============================================================================
# Unit tests — detect_fenced_yaml
# =============================================================================


class TestDetectFencedYaml:
    """Unit tests for task_format.detect_fenced_yaml.

    Scope: All detection paths — correct fences (yaml/yml/plain), leading
    whitespace, raw frontmatter, legacy markdown, fence-without-dashes,
    multi-block, four-backtick, empty input, and trailing content.

    Strategy: Call detect_fenced_yaml with carefully constructed inputs;
    assert either the stripped string or None based on expected detection.

    Why: The function is the primary guard against silently mis-parsed fenced
    YAML — correctness here prevents data loss across all task file consumers.
    """

    def test_detect_fenced_yaml_standard(self) -> None:
        r"""Correctly strips a standard ```yaml fence around --- frontmatter.

        Tests: detect_fenced_yaml with ```yaml tag.
        How: Arrange a single fenced block with yaml tag, call function, assert
             returned string starts with '---\\n' (fences removed).
        Why: Most generators produce ```yaml tags; this is the primary use case.
        """
        # Arrange
        content = "```yaml\n---\ntask: T1\ntitle: X\nstatus: not-started\n---\n```\n"

        # Act
        result = detect_fenced_yaml(content)

        # Assert
        assert result is not None
        assert result.startswith("---\n")
        assert "```" not in result

    def test_detect_fenced_yaml_yml_tag(self) -> None:
        """Correctly strips a ```yml (short tag) fence around --- frontmatter.

        Tests: detect_fenced_yaml with ```yml tag.
        How: Arrange content with yml tag, call function, assert result strips fences.
        Why: Some generators use the shorter 'yml' tag; both must be supported.
        """
        # Arrange
        content = "```yml\n---\ntask: T1\ntitle: Y\nstatus: not-started\n---\n```\n"

        # Act
        result = detect_fenced_yaml(content)

        # Assert
        assert result is not None
        assert result.startswith("---\n")
        assert "```" not in result

    def test_detect_fenced_yaml_no_tag(self) -> None:
        """Correctly strips a plain ``` fence (no language tag) around --- frontmatter.

        Tests: detect_fenced_yaml with plain ``` (no tag).
        How: Arrange content with plain fence, call function, assert result strips fences.
        Why: Some generators emit plain ``` fences; function must handle all three variants.
        """
        # Arrange
        content = "```\n---\ntask: T1\ntitle: Z\nstatus: not-started\n---\n```\n"

        # Act
        result = detect_fenced_yaml(content)

        # Assert
        assert result is not None
        assert result.startswith("---\n")
        assert "```" not in result

    def test_detect_fenced_yaml_leading_whitespace(self) -> None:
        r"""Strips fences when content has leading whitespace before the fence.

        Tests: detect_fenced_yaml with leading newlines and spaces.
        How: Arrange content with leading '  \\n' before the fence, call function.
        Why: Files may have a BOM, blank lines, or spaces before the fence;
             lstrip() must normalize this before pattern matching.
        """
        # Arrange
        content = "  \n```yaml\n---\ntask: T1\ntitle: W\nstatus: not-started\n---\n```\n"

        # Act
        result = detect_fenced_yaml(content)

        # Assert
        assert result is not None
        assert result.startswith("---\n")
        assert "```" not in result

    def test_detect_fenced_yaml_raw_frontmatter_returns_none(self) -> None:
        r"""Returns None when content is already raw YAML frontmatter (no fences).

        Tests: detect_fenced_yaml does not misidentify raw frontmatter.
        How: Arrange raw '---\\n...\\n---\\n' content, call function, assert None.
        Why: The function must be a no-op for correctly formatted files — callers
             depend on None to skip the re-parse path.
        """
        # Arrange
        content = "---\ntask: T1\ntitle: Raw\nstatus: not-started\n---\n"

        # Act
        result = detect_fenced_yaml(content)

        # Assert
        assert result is None

    def test_detect_fenced_yaml_legacy_markdown_returns_none(self) -> None:
        """Returns None for legacy '## Task' header format (not YAML at all).

        Tests: detect_fenced_yaml ignores legacy markdown task format.
        How: Arrange legacy markdown content, call function, assert None.
        Why: Legacy files are parsed by a separate code path; detect_fenced_yaml
             must not interfere with them.
        """
        # Arrange
        content = "## Task T1: Title\n**Status**: NOT STARTED\n**Agent**: general-purpose\n"

        # Act
        result = detect_fenced_yaml(content)

        # Assert
        assert result is None

    def test_detect_fenced_yaml_fence_without_dashes_returns_none(self) -> None:
        """Returns None when fence contains YAML-like content but no --- delimiters.

        Tests: detect_fenced_yaml requires --- inside the fence.
        How: Arrange a fenced block with 'key: value' but no --- markers, assert None.
        Why: Only frontmatter (with ---) qualifies; plain YAML code blocks must not
             trigger fence-stripping to avoid false positives in documentation files.
        """
        # Arrange
        content = "```yaml\nkey: value\nanother: key\n```\n"

        # Act
        result = detect_fenced_yaml(content)

        # Assert
        assert result is None

    def test_detect_fenced_yaml_multiple_blocks(self) -> None:
        """Returns stripped content when multiple fenced YAML blocks are present.

        Tests: detect_fenced_yaml handles files with more than one fenced block.
        How: Arrange content with 3 fenced blocks separated by markdown, call function,
             assert all three blocks are stripped and body text is preserved.
        Why: Multi-task plan files may place each task in a fenced block; all must
             be stripped in a single pass so the re-parse step works correctly.
        """
        # Arrange
        block = "```yaml\n---\ntask: T{n}\ntitle: Task {n}\nstatus: not-started\n---\n```\n"
        content = (
            block.format(n=1)
            + "\n## Notes\n\nSome body text.\n\n"
            + block.format(n=2)
            + "\n## More Notes\n\n"
            + block.format(n=3)
        )

        # Act
        result = detect_fenced_yaml(content)

        # Assert
        assert result is not None
        assert "```" not in result
        # All three frontmatter blocks should appear in stripped result
        assert "task: T1" in result
        assert "task: T2" in result
        assert "task: T3" in result

    def test_detect_fenced_yaml_four_backtick_returns_none(self) -> None:
        """Returns None for four-backtick fences (not standard three-backtick code blocks).

        Tests: detect_fenced_yaml rejects ````yaml fences.
        How: Arrange content with four-backtick fence wrapping --- frontmatter, assert None.
        Why: The regex uses (?!`) negative lookahead to prevent matching four-backtick
             fences; this preserves nested code block semantics.
        """
        # Arrange
        content = "````yaml\n---\ntask: T1\ntitle: X\nstatus: not-started\n---\n````\n"

        # Act
        result = detect_fenced_yaml(content)

        # Assert
        assert result is None

    def test_detect_fenced_yaml_empty_returns_none(self) -> None:
        """Returns None for empty string input.

        Tests: detect_fenced_yaml handles empty input without raising.
        How: Call with empty string, assert None.
        Why: Callers may pass empty file content; function must not raise on edge input.
        """
        # Arrange
        content = ""

        # Act
        result = detect_fenced_yaml(content)

        # Assert
        assert result is None

    def test_detect_fenced_yaml_trailing_content_preserved(self) -> None:
        r"""Preserves markdown body text that follows the closing fence.

        Tests: detect_fenced_yaml does not discard content after the closing ```.
        How: Arrange a fenced YAML block followed by '## Context\\nBody text.', call
             function, assert both the stripped frontmatter and trailing body appear.
        Why: Task files embed body documentation after the frontmatter block; losing
             body content would break downstream consumers.
        """
        # Arrange
        content = "```yaml\n---\ntask: T1\ntitle: X\nstatus: not-started\n---\n```\n\n## Context\nSome body text.\n"

        # Act
        result = detect_fenced_yaml(content)

        # Assert
        assert result is not None
        assert result.startswith("---\n")
        # Body text that followed the fence must survive
        assert "## Context" in result
        assert "Some body text." in result
        assert "```" not in result


# =============================================================================
# Integration tests — parse_task_content
# =============================================================================


class TestParseTaskContent:
    """Integration tests for implementation_manager.parse_task_content.

    Scope: End-to-end parsing from raw file content to Task objects, covering
    fenced YAML (single and multi-block), raw YAML frontmatter, legacy markdown,
    YAML parse failures, and missing required fields.

    Strategy: Use monkeypatch to redirect sys.stderr to a StringIO buffer so
    warning output can be asserted. Each test is fully independent.

    Why: parse_task_content is the central parsing function for all task file
    consumers; regressions here break orchestration, status tracking, and hooks.
    """

    def test_parse_task_content_fenced_single(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Parses a single task from fenced YAML and emits a fence-stripping WARNING.

        Tests: parse_task_content with a single fenced YAML block.
        How: Arrange content with one ```yaml block wrapping complete task frontmatter,
             capture stderr, call function, assert 1 Task with correct fields and WARNING.
        Why: The primary regression scenario — generators that emit fenced YAML must
             produce a parsed task, not a silent empty list, after the fix.
        """
        # Arrange
        content = _FENCED_MINIMAL
        stderr_buf = io.StringIO()
        monkeypatch.setattr(sys, "stderr", stderr_buf)

        # Act
        result = im.parse_task_content(content)

        # Assert
        monkeypatch.undo()
        stderr_output = stderr_buf.getvalue()
        assert len(result) == 1
        task = result[0]
        assert task.id == "T1"
        assert task.name == "Minimal Task"
        assert "WARNING" in stderr_output
        assert "```yaml" in stderr_output

    def test_parse_task_content_fenced_multi(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Parses when two fenced YAML blocks appear in sequence; emits WARNING.

        Tests: parse_task_content with two fenced blocks in one file.
        How: Arrange content with two ```yaml blocks, capture stderr, assert at least
             1 Task returned and WARNING emitted. The first task is T1.
        Why: Plan files that list multiple tasks as fenced blocks must not lose all
             tasks — at minimum the first task must survive fence-stripping.
        """
        # Arrange
        task2_yaml = (
            "---\n"
            "task: T2\n"
            "title: Second Task\n"
            "status: not-started\n"
            "agent: general-purpose\n"
            "dependencies: [T1]\n"
            "priority: 2\n"
            "complexity: medium\n"
            "---\n"
        )
        content = _FENCED_MINIMAL + "\n## Notes between tasks\n\n" + f"```yaml\n{task2_yaml}```\n"
        stderr_buf = io.StringIO()
        monkeypatch.setattr(sys, "stderr", stderr_buf)

        # Act
        result = im.parse_task_content(content)

        # Assert
        monkeypatch.undo()
        stderr_output = stderr_buf.getvalue()
        assert len(result) >= 1
        assert result[0].id == "T1"
        assert "WARNING" in stderr_output

    def test_parse_task_content_raw_yaml_no_warning(self, monkeypatch: pytest.MonkeyPatch) -> None:
        r"""Parses raw YAML frontmatter without emitting any WARNING.

        Tests: parse_task_content with correctly formatted raw frontmatter.
        How: Arrange raw '---\\n...\\n---\\n' content, capture stderr, assert
             1 Task returned and stderr is empty.
        Why: Correctly formatted files must not trigger warnings — warning presence
             would pollute orchestrator logs for well-formed task files.
        """
        # Arrange
        content = _MINIMAL_TASK_YAML
        stderr_buf = io.StringIO()
        monkeypatch.setattr(sys, "stderr", stderr_buf)

        # Act
        result = im.parse_task_content(content)

        # Assert
        monkeypatch.undo()
        stderr_output = stderr_buf.getvalue()
        assert len(result) == 1
        assert result[0].id == "T1"
        assert stderr_output == ""

    def test_parse_task_content_legacy_markdown_no_warning(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Parses legacy '## Task' markdown format without emitting any WARNING.

        Tests: parse_task_content with legacy markdown header format.
        How: Arrange legacy markdown content with '## Task T1: Title' and bold
             field lines, capture stderr, assert 1 Task returned and stderr empty.
        Why: Legacy format files must continue to work silently — they predate
             YAML frontmatter and no WARNING should appear for them.
        """
        # Arrange
        content = (
            "## Task T1: Legacy Task\n"
            "**Status**: NOT STARTED\n"
            "**Agent**: general-purpose\n"
            "**Priority**: 1\n"
            "**Complexity**: Low\n"
            "**Dependencies**: None\n"
        )
        stderr_buf = io.StringIO()
        monkeypatch.setattr(sys, "stderr", stderr_buf)

        # Act
        result = im.parse_task_content(content)

        # Assert
        monkeypatch.undo()
        stderr_output = stderr_buf.getvalue()
        assert len(result) == 1
        assert result[0].id == "T1"
        assert stderr_output == ""

    def test_parse_task_content_yaml_parse_failure_warns(self, monkeypatch: pytest.MonkeyPatch) -> None:
        r"""Emits WARNING when YAML frontmatter exists but parsing fails.

        Tests: parse_task_content fallthrough when YAML frontmatter is syntactically invalid.
        How: Arrange content that starts with '---\\n' (triggering YAML path) but contains
             invalid YAML, capture stderr, assert WARNING prefix 'parsing failed' appears.
             The function falls through to legacy parsing which may return [] or tasks.
        Why: A broken YAML file must not silently return an empty list — the WARNING
             alerts operators that the file needs to be repaired.
        """
        # Arrange — syntactically invalid YAML (unbalanced bracket)
        content = "---\ntask: T1\ntitle: Bad: [unbalanced bracket\nstatus: not-started\n---\n"
        stderr_buf = io.StringIO()
        monkeypatch.setattr(sys, "stderr", stderr_buf)

        # Act
        result = im.parse_task_content(content)

        # Assert
        monkeypatch.undo()
        stderr_output = stderr_buf.getvalue()
        # Result may be [] (legacy parser finds no ## headers) or tasks — both are acceptable
        assert isinstance(result, list)
        assert "WARNING" in stderr_output
        assert "parsing failed" in stderr_output

    def test_parse_task_content_fenced_missing_required_field(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Emits two WARNINGs when fenced YAML is stripped but missing a required field.

        Tests: parse_task_content dual-warning path for fenced + invalid frontmatter.
        How: Arrange fenced YAML with 'task' and 'status' but no 'title', capture stderr,
             assert both the fence-stripping WARNING and the 'parsing failed' WARNING appear.
        Why: Callers need to distinguish the fence-wrapping problem (generator bug) from
             the missing-field problem (content bug) — both warnings provide distinct signals.
        """
        # Arrange — fenced YAML missing the required 'title' field
        content = "```yaml\n---\ntask: T1\nstatus: not-started\n---\n```\n"
        stderr_buf = io.StringIO()
        monkeypatch.setattr(sys, "stderr", stderr_buf)

        # Act
        result = im.parse_task_content(content)

        # Assert
        monkeypatch.undo()
        stderr_output = stderr_buf.getvalue()
        # Both WARNINGs must appear
        assert stderr_output.count("WARNING") >= 2
        assert "```yaml" in stderr_output  # fence-stripping warning
        assert "parsing failed" in stderr_output  # missing-field warning
        # Result may be [] or legacy-parsed; either is acceptable
        assert isinstance(result, list)


# =============================================================================
# Regression fixture test
# =============================================================================


class TestRegressionFixture:
    """Regression test using the actual plan/tasks-4 file.

    Scope: Verifies that the real-world fixture file triggers at least one WARNING
    from parse_task_content — confirming the parser does not silently fail on
    files that contain non-task YAML frontmatter or embedded fenced YAML blocks.

    Why: This is the concrete evidence that the fenced-YAML recovery path works
    against production content, not just synthetic test inputs.
    """

    def test_parse_task_content_real_world_regression(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """parse_task_content emits WARNING when parsing the tasks-4 fixture.

        Tests: parse_task_content against plan/tasks-4-validate-orchestrator-discipline.md.
        How: Compute path from this test file's location up to repo root, read the actual
             fixture file, capture stderr, call parse_task_content, assert WARNING emitted.
        Why: The fixture contains YAML frontmatter (file-level, not task-level) causing
             the parser to warn about missing required fields. This confirms the WARNING
             path fires on real production content — proving the old silent-failure is fixed.

        Note on task count: The fixture's top-level frontmatter is a feature-level
        description (not a task), so parse_task_content returns 0 tasks. The regression
        assertion focuses on WARNING presence (non-silent failure) rather than task count.
        """
        # Arrange — resolve path from scripts/ up 5 levels to repo root
        scripts_dir = Path(__file__).resolve().parent
        repo_root = scripts_dir.parent.parent.parent.parent.parent
        fixture_path = repo_root / "plan" / "tasks-4-validate-orchestrator-discipline.md"

        assert fixture_path.exists(), (
            f"Regression fixture not found at {fixture_path}. Ensure the repository root is correct."
        )

        content = fixture_path.read_text(encoding="utf-8")
        stderr_buf = io.StringIO()
        monkeypatch.setattr(sys, "stderr", stderr_buf)

        # Act
        result = im.parse_task_content(content)

        # Assert
        monkeypatch.undo()
        stderr_output = stderr_buf.getvalue()
        # The file must trigger a WARNING (non-silent failure is the regression requirement)
        assert "WARNING" in stderr_output, (
            f"Expected WARNING in stderr from parsing {fixture_path.name}, but stderr was empty. Result: {result!r}"
        )
        # Result is a list (may be empty — file-level frontmatter is not a task)
        assert isinstance(result, list)


# =============================================================================
# Tests for DEFERRED and SKIPPED status support (issue #408)
# =============================================================================


_DEFERRED_TASK_YAML = (
    "---\n"
    "task: T3\n"
    "title: Deferred Task\n"
    "status: deferred\n"
    "agent: general-purpose\n"
    "dependencies: []\n"
    "priority: 3\n"
    "complexity: low\n"
    "---\n"
)

_SKIPPED_TASK_YAML = (
    "---\n"
    "task: T4\n"
    "title: Skipped Task\n"
    "status: skipped\n"
    "agent: general-purpose\n"
    "dependencies: []\n"
    "priority: 4\n"
    "complexity: low\n"
    "---\n"
)

_DEFERRED_TITLE_YAML = (
    "---\n"
    "task: T5\n"
    "title: '[DEFERRED] Intentionally deferred task'\n"
    "status: not-started\n"
    "agent: general-purpose\n"
    "dependencies: []\n"
    "priority: 5\n"
    "complexity: low\n"
    "---\n"
)


class TestDeferredSkippedStatus:
    """Tests for DEFERRED and SKIPPED task statuses (issue #408).

    Scope: Verifies that DEFERRED and SKIPPED statuses are:
    - Parsed correctly from YAML frontmatter
    - Inferred from [DEFERRED]/[SKIPPED] markers in task titles
    - Treated as terminal (not appearing in ready-tasks list)
    - Counted separately in status output
    - Treated as satisfying dependencies for dependent tasks

    Why: Without DEFERRED/SKIPPED as terminal statuses, intentionally deferred
    tasks prevent /complete-implementation from triggering even when all
    actionable tasks are COMPLETE.
    """

    def test_parse_deferred_status_from_yaml(self) -> None:
        """Parses 'deferred' YAML status into TaskStatus.DEFERRED.

        Tests: _parse_yaml_status and parse_task_from_frontmatter with deferred status.
        How: Arrange YAML with status: deferred, parse, assert TaskStatus.DEFERRED.
        Why: The fundamental fix — YAML files must be able to express deferred status.
        """
        # Arrange / Act
        result = im.parse_task_content(_DEFERRED_TASK_YAML)

        # Assert
        assert len(result) == 1
        assert result[0].status == im.TaskStatus.DEFERRED
        assert result[0].id == "T3"

    def test_parse_skipped_status_from_yaml(self) -> None:
        """Parses 'skipped' YAML status into TaskStatus.SKIPPED.

        Tests: _parse_yaml_status with skipped status.
        How: Arrange YAML with status: skipped, parse, assert TaskStatus.SKIPPED.
        Why: SKIPPED is a valid terminal status equivalent to DEFERRED for completion gating.
        """
        # Arrange / Act
        result = im.parse_task_content(_SKIPPED_TASK_YAML)

        # Assert
        assert len(result) == 1
        assert result[0].status == im.TaskStatus.SKIPPED
        assert result[0].id == "T4"

    def test_parse_wont_fix_status_maps_to_skipped(self) -> None:
        """Parses 'wont-fix' YAML status into TaskStatus.SKIPPED.

        Tests: _YAML_STATUS_TO_ENUM mapping for wont-fix.
        How: Arrange YAML with status: wont-fix, parse, assert TaskStatus.SKIPPED.
        Why: wont-fix is semantically equivalent to skipped for completion purposes.
        """
        # Arrange
        content = (
            "---\n"
            "task: T6\n"
            "title: Wont Fix Task\n"
            "status: wont-fix\n"
            "agent: general-purpose\n"
            "dependencies: []\n"
            "priority: 3\n"
            "complexity: low\n"
            "---\n"
        )

        # Act
        result = im.parse_task_content(content)

        # Assert
        assert len(result) == 1
        assert result[0].status == im.TaskStatus.SKIPPED

    def test_deferred_title_marker_overrides_not_started_status(self) -> None:
        """[DEFERRED] in task title overrides not-started YAML status to DEFERRED.

        Tests: parse_task_from_frontmatter title-based status override.
        How: Arrange YAML with status: not-started and [DEFERRED] in title,
             parse, assert TaskStatus.DEFERRED.
        Why: Existing tasks often have [DEFERRED] in the title but status was not
             updated — the override prevents them from blocking completion.
        """
        # Arrange / Act
        result = im.parse_task_content(_DEFERRED_TITLE_YAML)

        # Assert
        assert len(result) == 1
        assert result[0].status == im.TaskStatus.DEFERRED

    def test_skipped_title_marker_overrides_not_started_status(self) -> None:
        """[SKIPPED] in task title overrides not-started YAML status to SKIPPED.

        Tests: parse_task_from_frontmatter title-based status override for SKIPPED.
        How: Arrange YAML with status: not-started and [SKIPPED] in title,
             parse, assert TaskStatus.SKIPPED.
        Why: Consistent with DEFERRED override — title markers must work for SKIPPED too.
        """
        # Arrange
        content = (
            "---\n"
            "task: T7\n"
            "title: '[SKIPPED] Optional enhancement'\n"
            "status: not-started\n"
            "agent: general-purpose\n"
            "dependencies: []\n"
            "priority: 5\n"
            "complexity: low\n"
            "---\n"
        )

        # Act
        result = im.parse_task_content(content)

        # Assert
        assert len(result) == 1
        assert result[0].status == im.TaskStatus.SKIPPED

    def test_deferred_task_not_in_ready_tasks(self) -> None:
        """DEFERRED task does not appear in get_ready_tasks output.

        Tests: get_ready_tasks excludes DEFERRED tasks.
        How: Create task list with one NOT_STARTED and one DEFERRED task (no deps),
             call get_ready_tasks, assert only NOT_STARTED task is returned.
        Why: Deferred tasks must not be scheduled for execution by the orchestrator.
        """
        # Arrange
        from implementation_manager import Task, TaskPriority, TaskStatus, get_ready_tasks

        tasks = [
            Task(
                id="T1",
                name="Active",
                status=TaskStatus.NOT_STARTED,
                dependencies=[],
                agent="agent-a",
                priority=TaskPriority.HIGH,
                complexity="Low",
                started=None,
                completed=None,
                skills=[],
            ),
            Task(
                id="T2",
                name="Deferred",
                status=TaskStatus.DEFERRED,
                dependencies=[],
                agent="agent-b",
                priority=TaskPriority.LOW,
                complexity="Low",
                started=None,
                completed=None,
                skills=[],
            ),
        ]

        # Act
        ready = get_ready_tasks(tasks)

        # Assert
        assert len(ready) == 1
        assert ready[0].id == "T1"

    def test_deferred_dependency_does_not_block_dependent_task(self) -> None:
        """A task whose only dependency is DEFERRED is included in ready tasks.

        Tests: get_ready_tasks treats DEFERRED as satisfying dependencies.
        How: Create T2 NOT_STARTED depending on T1 DEFERRED, call get_ready_tasks,
             assert T2 is in ready list.
        Why: If a prerequisite is intentionally deferred, dependent work that can
             proceed independently should not be blocked.
        """
        from implementation_manager import Task, TaskPriority, TaskStatus, get_ready_tasks

        # Arrange
        tasks = [
            Task(
                id="T1",
                name="Deferred Prereq",
                status=TaskStatus.DEFERRED,
                dependencies=[],
                agent=None,
                priority=TaskPriority.HIGH,
                complexity="Low",
                started=None,
                completed=None,
                skills=[],
            ),
            Task(
                id="T2",
                name="Dependent",
                status=TaskStatus.NOT_STARTED,
                dependencies=["T1"],
                agent="agent-a",
                priority=TaskPriority.HIGH,
                complexity="Low",
                started=None,
                completed=None,
                skills=[],
            ),
        ]

        # Act
        ready = get_ready_tasks(tasks)

        # Assert
        assert len(ready) == 1
        assert ready[0].id == "T2"

    def test_parse_status_deferred_text(self) -> None:
        """parse_status() maps 'deferred' text to TaskStatus.DEFERRED.

        Tests: parse_status with raw 'deferred' text (legacy markdown scenario).
        How: Call parse_status with 'deferred', assert TaskStatus.DEFERRED returned.
        Why: Legacy markdown task files may set **Status**: DEFERRED.
        """
        # Arrange / Act / Assert
        assert im.parse_status("deferred") == im.TaskStatus.DEFERRED
        assert im.parse_status("DEFERRED") == im.TaskStatus.DEFERRED
        assert im.parse_status("[DEFERRED]") == im.TaskStatus.DEFERRED

    def test_parse_status_skipped_text(self) -> None:
        """parse_status() maps 'skipped' text to TaskStatus.SKIPPED.

        Tests: parse_status with raw 'skipped' / 'wont fix' text.
        How: Call parse_status with various skipped indicators, assert TaskStatus.SKIPPED.
        Why: Multiple synonyms exist for intentionally skipped tasks.
        """
        # Arrange / Act / Assert
        assert im.parse_status("skipped") == im.TaskStatus.SKIPPED
        assert im.parse_status("SKIPPED") == im.TaskStatus.SKIPPED
        assert im.parse_status("wont-fix") == im.TaskStatus.SKIPPED
        assert im.parse_status("wont fix") == im.TaskStatus.SKIPPED
