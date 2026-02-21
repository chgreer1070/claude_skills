"""Unit tests for ConsoleReporter, CIReporter, and SummaryReporter.

Tests:
- ConsoleReporter initialization (default, injected console, no_color)
- ConsoleReporter report/summarize output with Rich Console capture
- CIReporter plain text report/summarize output
- SummaryReporter single-line summary output

Note: CIReporter and SummaryReporter use ``print()`` for output. Tests capture
stdout via ``contextlib.redirect_stdout`` instead of ``capsys`` to remain
compatible with pytest-xdist parallel workers.
"""

from __future__ import annotations

import contextlib
import sys
from io import StringIO
from pathlib import Path

# Add parent directory to path to import plugin_validator
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from plugin_validator import (
    CIReporter,
    ConsoleReporter,
    SummaryReporter,
    ValidationIssue,
    ValidationResult,
)


def _make_passing_result() -> ValidationResult:
    """Create a ValidationResult that passes with no issues."""
    return ValidationResult(passed=True, errors=[], warnings=[], info=[])


def _make_failing_result() -> ValidationResult:
    """Create a ValidationResult that fails with one error."""
    return ValidationResult(
        passed=False,
        errors=[
            ValidationIssue(
                field="description",
                severity="error",
                message="Missing required field",
                code="FM001",
                line=3,
                suggestion="Add a description field",
            )
        ],
        warnings=[],
        info=[],
    )


def _make_warning_result() -> ValidationResult:
    """Create a ValidationResult that passes but has a warning."""
    return ValidationResult(
        passed=True,
        errors=[],
        warnings=[
            ValidationIssue(
                field="tools",
                severity="warning",
                message="Tools should be comma-separated",
                code="FM004",
            )
        ],
        info=[],
    )


class TestConsoleReporter:
    """Test ConsoleReporter initialization and output."""

    def test_default_init(self) -> None:
        """Test ConsoleReporter creates a console when none is provided.

        Tests: Default initialization path
        How: Instantiate with no args, check console attribute
        Why: Verify default Console is created internally
        """
        reporter = ConsoleReporter()
        assert reporter.console is not None

    def test_injected_console(self) -> None:
        """Test ConsoleReporter uses injected Console instance.

        Tests: Dependency injection path
        How: Pass a Console with color_system=None, verify it is stored
        Why: Verify DI pattern works for testability
        """
        from rich.console import Console

        injected = Console(color_system=None)
        reporter = ConsoleReporter(console=injected)
        assert reporter.console is injected

    def test_no_color_flag(self) -> None:
        """Test ConsoleReporter sets no_color attribute when flag is True.

        Tests: no_color parameter
        How: Pass no_color=True, check attribute
        Why: Verify no_color flag is stored for CI environments
        """
        reporter = ConsoleReporter(no_color=True)
        assert reporter.no_color is True

    def test_report_passed_file(self) -> None:
        """Test report output for a passing file shows pass marker.

        Tests: Passed file reporting with show_progress=True
        How: Inject Console writing to StringIO, call report with passing result
        Why: Verify PASSED indicator appears in output
        """
        from rich.console import Console

        buf = StringIO()
        console = Console(file=buf, color_system=None, width=200)
        reporter = ConsoleReporter(console=console)

        file_results = {
            Path("/tmp/test/SKILL.md"): [("frontmatter", _make_passing_result())]
        }
        reporter.report(file_results, show_progress=True)

        output = buf.getvalue()
        assert "PASSED" in output

    def test_report_failed_file(self) -> None:
        """Test report output for a failing file shows error details.

        Tests: Failed file reporting with error issues
        How: Inject Console writing to StringIO, call report with failing result
        Why: Verify error code and message appear in output
        """
        from rich.console import Console

        buf = StringIO()
        console = Console(file=buf, color_system=None, width=200)
        reporter = ConsoleReporter(console=console)

        file_results = {
            Path("/tmp/test/SKILL.md"): [("frontmatter", _make_failing_result())]
        }
        reporter.report(file_results)

        output = buf.getvalue()
        assert "FM001" in output
        assert "Missing required field" in output

    def test_report_warnings(self) -> None:
        """Test report output includes warnings.

        Tests: Warning issue display
        How: Inject Console writing to StringIO, call report with warning result
        Why: Verify warning code appears in output
        """
        from rich.console import Console

        buf = StringIO()
        console = Console(file=buf, color_system=None, width=200)
        reporter = ConsoleReporter(console=console)

        file_results = {
            Path("/tmp/test/SKILL.md"): [("frontmatter", _make_warning_result())]
        }
        reporter.report(file_results)

        output = buf.getvalue()
        assert "FM004" in output
        assert "comma-separated" in output

    def test_summarize(self) -> None:
        """Test summarize output includes stats and status text.

        Tests: Summary panel rendering
        How: Inject Console writing to StringIO, call summarize with stats
        Why: Verify summary contains all stat lines
        """
        from rich.console import Console

        buf = StringIO()
        console = Console(file=buf, color_system=None, width=200)
        reporter = ConsoleReporter(console=console)

        reporter.summarize(total_files=5, passed=3, failed=1, warnings=1)

        output = buf.getvalue()
        assert "Total files: 5" in output
        assert "Passed: 3" in output
        assert "Failed: 1" in output
        assert "Warnings: 1" in output
        assert "FAILED" in output


class TestCIReporter:
    """Test CIReporter plain text output.

    Uses ``contextlib.redirect_stdout`` to capture ``print()`` output,
    which is compatible with pytest-xdist parallel execution.
    """

    def test_report_passed_file(self) -> None:
        """Test CIReporter shows pass marker for passing files.

        Tests: Passed file reporting in plain text
        How: Call report with passing result, capture stdout
        Why: Verify plain text PASSED format (no ANSI codes)
        """
        reporter = CIReporter()
        file_results = {
            Path("/tmp/test/SKILL.md"): [("frontmatter", _make_passing_result())]
        }

        buf = StringIO()
        with contextlib.redirect_stdout(buf):
            reporter.report(file_results, show_progress=True)

        output = buf.getvalue()
        assert "PASSED" in output
        assert "\x1b" not in output

    def test_report_failed_file(self) -> None:
        """Test CIReporter shows error details for failing files.

        Tests: Failed file reporting in plain text
        How: Call report with failing result, capture stdout
        Why: Verify error format uses plain text markers
        """
        reporter = CIReporter()
        file_results = {
            Path("/tmp/test/SKILL.md"): [("frontmatter", _make_failing_result())]
        }

        buf = StringIO()
        with contextlib.redirect_stdout(buf):
            reporter.report(file_results)

        output = buf.getvalue()
        assert "\u2717 ERROR" in output
        assert "FM001" in output

    def test_report_warnings(self) -> None:
        """Test CIReporter shows warning format.

        Tests: Warning issue display in plain text
        How: Call report with warning result, capture stdout
        Why: Verify warning prefix format
        """
        reporter = CIReporter()
        file_results = {
            Path("/tmp/test/SKILL.md"): [("frontmatter", _make_warning_result())]
        }

        buf = StringIO()
        with contextlib.redirect_stdout(buf):
            reporter.report(file_results)

        output = buf.getvalue()
        assert "\u26a0 WARN" in output
        assert "FM004" in output

    def test_summarize(self) -> None:
        """Test CIReporter summarize shows plain text stats.

        Tests: Summary statistics in plain text
        How: Call summarize with stats, capture stdout
        Why: Verify plain text summary format
        """
        reporter = CIReporter()

        buf = StringIO()
        with contextlib.redirect_stdout(buf):
            reporter.summarize(total_files=5, passed=3, failed=1, warnings=1)

        output = buf.getvalue()
        assert "Total files: 5" in output
        assert "Passed: 3" in output
        assert "Failed: 1" in output
        assert "Warnings: 1" in output
        assert "\u2717 FAILED" in output


class TestSummaryReporter:
    """Test SummaryReporter single-line output.

    Uses ``contextlib.redirect_stdout`` to capture ``print()`` output,
    which is compatible with pytest-xdist parallel execution.
    """

    def test_report_and_summarize(self) -> None:
        """Test SummaryReporter produces no per-file output and a single-line summary.

        Tests: Full report + summarize flow
        How: Call report (should produce nothing), then summarize, capture stdout
        Why: Verify summary-only behavior
        """
        reporter = SummaryReporter()

        # report() should produce no output for summary reporter
        file_results = {
            Path("/tmp/test/SKILL.md"): [("frontmatter", _make_failing_result())],
            Path("/tmp/test/agent.md"): [("frontmatter", _make_passing_result())],
        }

        report_buf = StringIO()
        with contextlib.redirect_stdout(report_buf):
            reporter.report(file_results)
        assert report_buf.getvalue() == ""

        # summarize() should produce single-line output
        summary_buf = StringIO()
        with contextlib.redirect_stdout(summary_buf):
            reporter.summarize(total_files=4, passed=3, failed=1, warnings=0)
        assert "1/4 files failed" in summary_buf.getvalue()

    def test_summarize_all_passed(self) -> None:
        """Test SummaryReporter shows passed status when no failures.

        Tests: All-pass summary line
        How: Call summarize with zero failures, capture stdout
        Why: Verify pass summary format
        """
        reporter = SummaryReporter()

        buf = StringIO()
        with contextlib.redirect_stdout(buf):
            reporter.summarize(total_files=3, passed=3, failed=0, warnings=0)

        output = buf.getvalue()
        assert "3/3 files passed" in output
        assert "\u2713" in output

    def test_summarize_with_warnings(self) -> None:
        """Test SummaryReporter includes warning count when present.

        Tests: Warning count in summary
        How: Call summarize with warnings > 0, capture stdout
        Why: Verify warning count appears in parentheses
        """
        reporter = SummaryReporter()

        buf = StringIO()
        with contextlib.redirect_stdout(buf):
            reporter.summarize(total_files=5, passed=5, failed=0, warnings=2)

        output = buf.getvalue()
        assert "2 with warnings" in output
