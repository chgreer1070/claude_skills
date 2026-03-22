#!/usr/bin/env -S uv --quiet run --active --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "typer>=0.21.0",
#     "rich>=13.0.0",
#     "ruamel.yaml>=0.18.0",
# ]
# ///
"""Migrate existing plan artifacts to the artifact manifest system.

Scans ``plan/`` and ``research/`` directories for existing plan artifacts,
determines their type from filename patterns, extracts the linked GitHub issue
number from YAML frontmatter, and registers each artifact via
``GitHubArtifactProvider`` + ``ArtifactRegistry``.

Idempotent: re-running skips already-registered artifacts (the registry upserts
on ``(artifact_type, path)`` — existing entries are updated in-place).

Content upload follows ``GitHubArtifactProvider`` tier-2 auto-read: when no
explicit content is provided, the provider reads the local file and uploads it
to a GitHub issue comment automatically.

Usage::

    # Dry-run — report what would be migrated without making any API calls
    uv run migrate_artifacts.py --dry-run

    # Migrate artifacts for a single issue
    uv run migrate_artifacts.py --issue 480

    # Full migration
    uv run migrate_artifacts.py
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table
from ruamel.yaml import YAML

# ---------------------------------------------------------------------------
# backlog_core import guard
# ---------------------------------------------------------------------------

# When running via `uv run --active`, the project venv is active and
# backlog_core is importable via the workspace dependency.  When invoked
# outside a project context this import will fail with an ImportError; the
# error message below guides the operator.

try:
    from backlog_core import operations as _backlog_operations
    from backlog_core.artifact_provider import GitHubArtifactProvider
    from backlog_core.artifact_registry import ArtifactRegistry
    from backlog_core.models import ArtifactEntry, ArtifactStatus, ArtifactType, discover_repo
except ImportError as exc:
    Console(stderr=True).print(
        f"[red]ImportError:[/red] {exc}\n"
        "Ensure you are running inside the project venv:\n"
        "  uv run --active migrate_artifacts.py"
    )
    sys.exit(1)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

#: Repository root (script lives at plugins/development-harness/scripts/).
_REPO_ROOT = Path(__file__).resolve().parents[3]

#: Filename pattern → ArtifactType mapping (ordered — first match wins).
_FILENAME_PATTERNS: list[tuple[re.Pattern[str], ArtifactType]] = [
    (re.compile(r"^feature-context-(.+)\.md$"), ArtifactType.FEATURE_CONTEXT),
    (re.compile(r"^architect-(.+)\.md$"), ArtifactType.ARCHITECT),
    (re.compile(r"^P\d+-(.+)\.yaml$"), ArtifactType.TASK_PLAN),
    (re.compile(r"^T0-baseline-(.+)\.yaml$"), ArtifactType.T0_BASELINE),
    (re.compile(r"^TN-verification-(.+)\.yaml$"), ArtifactType.TN_VERIFICATION),
]

#: Pattern for markdown files inside plan/codebase/ → codebase-analysis.
_CODEBASE_ANALYSIS_PATTERN = re.compile(r"^.+\.md$")

console = Console()
err_console = Console(stderr=True)
_yaml = YAML()
_yaml.preserve_quotes = True


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class ArtifactCandidate:
    """A discovered artifact file ready for registration.

    Attributes:
        path: Repo-relative path string (e.g. ``plan/architect-foo.md``).
        artifact_type: Resolved ``ArtifactType`` enum value.
        issue_number: GitHub issue number extracted from frontmatter, or
            ``None`` when not found.
        skip_reason: Human-readable reason the candidate was skipped, or
            ``None`` when it should be processed.
    """

    path: str
    artifact_type: ArtifactType
    issue_number: int | None
    skip_reason: str | None = None


@dataclass
class MigrationResult:
    """Accumulated counts from a migration run.

    Attributes:
        migrated: Number of artifacts successfully registered.
        skipped: Number of artifacts skipped (no issue number found).
        failed: Number of artifacts that raised an exception during
            registration.
        details: Per-artifact outcome strings for display.
    """

    migrated: int = 0
    skipped: int = 0
    failed: int = 0
    details: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# YAML / frontmatter helpers
# ---------------------------------------------------------------------------


def _extract_issue_from_yaml(file_path: Path) -> int | None:
    """Read the ``issue`` field from YAML frontmatter or a bare YAML file.

    Handles two formats:

    1. **YAML file** (``.yaml`` / ``.yml``): parsed directly.
    2. **Markdown with YAML frontmatter**: content between opening ``---``
       and closing ``---`` / ``...`` delimiters.

    Args:
        file_path: Absolute path to the file.

    Returns:
        Integer issue number when found and parseable, ``None`` otherwise.
    """
    try:
        text = file_path.read_text(encoding="utf-8")
    except OSError:
        return None

    raw_data: object = None
    if file_path.suffix in {".yaml", ".yml"}:
        try:
            raw_data = _yaml.load(text)
        except Exception:  # noqa: BLE001
            return None
    else:
        # Markdown: extract frontmatter between --- delimiters.
        fm_match = re.match(r"^---\r?\n(.*?)\r?\n(?:---|\.\.\.)(?:\r?\n|$)", text, re.DOTALL)
        if not fm_match:
            return None
        try:
            raw_data = _yaml.load(fm_match.group(1))
        except Exception:  # noqa: BLE001
            return None

    if isinstance(raw_data, dict):
        return _coerce_issue(raw_data.get("issue"))
    return None


def _coerce_issue(value: object) -> int | None:
    """Coerce a YAML value to an integer issue number.

    Args:
        value: Raw value from YAML (may be int, str, or None).

    Returns:
        Positive integer, or ``None`` when the value cannot be coerced.
    """
    if value is None:
        return None
    try:
        n = int(str(value))
    except (ValueError, TypeError):
        return None
    else:
        return n if n > 0 else None


# ---------------------------------------------------------------------------
# Slug-based backlog fallback
# ---------------------------------------------------------------------------


def _slug_from_filename(file_path: Path) -> str:
    r"""Extract the slug portion from a plan filename.

    Strips known prefixes (``feature-context-``, ``architect-``, ``P\\d+-``,
    ``T0-baseline-``, ``TN-verification-``) and the file extension.

    Args:
        file_path: Path object for the plan file.

    Returns:
        Slug string (e.g. ``"my-feature"`` from
        ``"plan/feature-context-my-feature.md"``).
    """
    name = file_path.stem
    for prefix in ("feature-context-", "architect-", "T0-baseline-", "TN-verification-"):
        if name.startswith(prefix):
            return name[len(prefix) :]
    # P{N}-{slug} pattern
    p_match = re.match(r"^P\d+-(.+)$", name)
    if p_match:
        return p_match.group(1)
    return name


def _find_issue_via_backlog(slug: str, backlog_items: list[dict]) -> int | None:
    """Match a slug against cached backlog items to find an issue number.

    Compares the slug against backlog item titles and file paths.  Returns
    the first match found.

    Args:
        slug: Slug string extracted from the artifact filename.
        backlog_items: List of backlog item dicts as returned by
            ``backlog_list`` MCP output (each dict has ``title``,
            ``number``, and optionally ``plan`` fields).

    Returns:
        Matched GitHub issue number, or ``None`` when no match is found.
    """
    slug_words = set(slug.replace("-", " ").replace("_", " ").lower().split())
    for item in backlog_items:
        title: str = item.get("title", "") or ""
        plan_path: str = item.get("plan", "") or ""
        issue_number: int | None = _coerce_issue(item.get("number"))
        if issue_number is None:
            continue
        # Direct slug match in plan path
        if slug in plan_path:
            return issue_number
        # Word-overlap heuristic on title
        title_words = set(title.replace("-", " ").replace("_", " ").lower().split())
        overlap = slug_words & title_words
        if len(overlap) >= max(1, len(slug_words) // 2):
            return issue_number
    return None


# ---------------------------------------------------------------------------
# Discovery
# ---------------------------------------------------------------------------


def _resolve_issue(file_path: Path, backlog_items: list[dict]) -> int | None:
    """Resolve the issue number for a file via frontmatter or slug fallback.

    Args:
        file_path: Absolute path to the artifact file.
        backlog_items: Pre-fetched backlog items for slug-based fallback.

    Returns:
        Resolved issue number, or ``None``.
    """
    issue = _extract_issue_from_yaml(file_path)
    if issue is None:
        slug = _slug_from_filename(file_path)
        issue = _find_issue_via_backlog(slug, backlog_items)
    return issue


def _scan_codebase_dir(
    codebase_dir: Path, repo_root: Path, issue_filter: int | None, backlog_items: list[dict]
) -> list[ArtifactCandidate]:
    """Scan ``plan/codebase/`` for markdown analysis files.

    Args:
        codebase_dir: Absolute path to the ``plan/codebase/`` directory.
        repo_root: Absolute path to the repository root.
        issue_filter: When set, only candidates linked to this issue are kept.
        backlog_items: Pre-fetched backlog items for slug-based fallback.

    Returns:
        List of ``ArtifactCandidate`` objects for codebase-analysis files.
    """
    results: list[ArtifactCandidate] = []
    for child in codebase_dir.iterdir():
        if child.is_file() and _CODEBASE_ANALYSIS_PATTERN.match(child.name):
            rel = child.relative_to(repo_root).as_posix()
            issue = _resolve_issue(child, backlog_items)
            results.append(_make_candidate(rel, ArtifactType.CODEBASE_ANALYSIS, issue, issue_filter))
    return results


def _discover_plan_artifacts(
    repo_root: Path, issue_filter: int | None, backlog_items: list[dict]
) -> list[ArtifactCandidate]:
    """Scan ``plan/`` for artifact files and classify them.

    Args:
        repo_root: Absolute path to the repository root.
        issue_filter: When set, only candidates linked to this issue number
            are returned.
        backlog_items: Pre-fetched backlog items for slug-based fallback
            issue resolution.

    Returns:
        List of ``ArtifactCandidate`` objects, one per discovered file.
    """
    candidates: list[ArtifactCandidate] = []
    plan_dir = repo_root / "plan"
    if not plan_dir.is_dir():
        return candidates

    for file_path in plan_dir.iterdir():
        if file_path.is_dir():
            if file_path.name == "codebase":
                candidates.extend(_scan_codebase_dir(file_path, repo_root, issue_filter, backlog_items))
            continue

        if not file_path.is_file():
            continue

        artifact_type = _classify_plan_file(file_path)
        if artifact_type is None:
            continue

        rel = file_path.relative_to(repo_root).as_posix()
        issue = _resolve_issue(file_path, backlog_items)
        candidates.append(_make_candidate(rel, artifact_type, issue, issue_filter))

    return candidates


def _discover_research_artifacts(
    repo_root: Path, issue_filter: int | None, backlog_items: list[dict]
) -> list[ArtifactCandidate]:
    """Scan ``research/`` for artifact files.

    Research files do not follow a slug-naming convention — they rely on the
    ``issue`` frontmatter field or slug-based backlog matching as fallback.

    Args:
        repo_root: Absolute path to the repository root.
        issue_filter: When set, only candidates linked to this issue number
            are returned.
        backlog_items: Pre-fetched backlog items for slug-based fallback.

    Returns:
        List of ``ArtifactCandidate`` objects.
    """
    candidates: list[ArtifactCandidate] = []
    research_dir = repo_root / "research"
    if not research_dir.is_dir():
        return candidates

    for file_path in research_dir.rglob("*.md"):
        if not file_path.is_file():
            continue
        rel = file_path.relative_to(repo_root).as_posix()
        issue = _extract_issue_from_yaml(file_path)
        if issue is None:
            slug = _slug_from_filename(file_path)
            issue = _find_issue_via_backlog(slug, backlog_items)
        candidates.append(_make_candidate(rel, ArtifactType.RESEARCH, issue, issue_filter))

    return candidates


def _classify_plan_file(file_path: Path) -> ArtifactType | None:
    """Classify a plan file by its filename pattern.

    Args:
        file_path: Path object for the file to classify.

    Returns:
        Matching ``ArtifactType``, or ``None`` when the filename does not
        match any known pattern.
    """
    name = file_path.name
    for pattern, artifact_type in _FILENAME_PATTERNS:
        if pattern.match(name):
            return artifact_type
    return None


def _make_candidate(
    rel_path: str, artifact_type: ArtifactType, issue_number: int | None, issue_filter: int | None
) -> ArtifactCandidate:
    """Build an ``ArtifactCandidate``, setting ``skip_reason`` when appropriate.

    Args:
        rel_path: Repo-relative path string.
        artifact_type: Resolved artifact type.
        issue_number: Resolved issue number, or ``None``.
        issue_filter: When set, candidates not matching this issue are
            marked as skipped.

    Returns:
        Populated ``ArtifactCandidate``.
    """
    skip_reason: str | None = None
    if issue_number is None:
        skip_reason = "no issue number found"
    elif issue_filter is not None and issue_number != issue_filter:
        skip_reason = f"filtered (issue={issue_filter})"
    return ArtifactCandidate(
        path=rel_path, artifact_type=artifact_type, issue_number=issue_number, skip_reason=skip_reason
    )


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------


def _register_artifact(
    provider: GitHubArtifactProvider, registry: ArtifactRegistry, candidate: ArtifactCandidate
) -> tuple[bool, str]:
    """Register a single artifact via provider + registry.

    Reads the current manifest, upserts the entry, and persists the updated
    manifest.  Content upload (tier-2 auto-read) is handled by
    ``GitHubArtifactProvider.store_artifact_content`` when the local file
    exists.

    Args:
        provider: Initialised ``GitHubArtifactProvider`` instance.
        registry: ``ArtifactRegistry`` instance for upsert logic.
        candidate: Artifact to register (must have non-``None`` issue_number).

    Returns:
        Tuple of ``(success: bool, message: str)``.
    """
    assert candidate.issue_number is not None  # guarded by caller  # noqa: S101

    entry = ArtifactEntry(
        artifact_type=candidate.artifact_type,
        path=candidate.path,
        status=ArtifactStatus.CURRENT,
        agent="migrate-artifacts",
    )

    manifest = provider.get_manifest(candidate.issue_number)
    existed = any(e.artifact_type == candidate.artifact_type and e.path == candidate.path for e in manifest.artifacts)
    updated_manifest = registry.register(manifest, entry)
    provider.set_manifest(candidate.issue_number, updated_manifest)

    # Attempt tier-2 content upload: read local file if it exists.
    local_content = provider.read_local_artifact_content(candidate.path)
    if local_content is not None:
        provider.store_artifact_content(
            candidate.issue_number, str(candidate.artifact_type), candidate.path, local_content
        )
        content_note = " (content uploaded)"
    else:
        content_note = " (no local file — manifest-only)"

    action = "updated" if existed else "added"
    return True, f"{action}{content_note}"


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------


def _print_summary_table(candidates: list[ArtifactCandidate], result: MigrationResult, dry_run: bool) -> None:
    """Print a Rich table summarising migration outcomes.

    Args:
        candidates: All discovered candidates (including skipped ones).
        result: Accumulated migration result counters.
        dry_run: When ``True``, labels the run as a dry run.
    """
    mode_label = "[yellow]DRY RUN[/yellow]" if dry_run else "[green]LIVE RUN[/green]"
    table = Table(title=f"Artifact Migration — {mode_label}", show_lines=True)
    table.add_column("Path", style="cyan", no_wrap=False)
    table.add_column("Type", style="magenta")
    table.add_column("Issue", justify="right")
    table.add_column("Outcome", style="bold")

    for detail in result.details:
        parts = detail.split("|")
        if len(parts) == 4:  # noqa: PLR2004
            table.add_row(*parts)

    console.print(table)
    console.print(
        f"\n:white_check_mark: Migrated: [green]{result.migrated}[/green]  "
        f":next_track_button: Skipped: [yellow]{result.skipped}[/yellow]  "
        f":cross_mark: Failed: [red]{result.failed}[/red]"
    )


# ---------------------------------------------------------------------------
# Main CLI
# ---------------------------------------------------------------------------

app = typer.Typer(help="Migrate plan artifacts to the artifact manifest system.")


@app.command()
def migrate(
    dry_run: Annotated[
        bool, typer.Option("--dry-run", help="Report what would be migrated without making any API calls.")
    ] = False,
    issue: Annotated[
        int | None, typer.Option("--issue", "-i", help="Migrate artifacts for a specific GitHub issue number only.")
    ] = None,
    repo_root: Annotated[
        Path,
        typer.Option(
            "--repo-root",
            help="Repository root path. Defaults to three levels above this script.",
            exists=True,
            file_okay=False,
            dir_okay=True,
            resolve_path=True,
        ),
    ] = _REPO_ROOT,
) -> None:
    """Migrate existing plan artifacts to the artifact manifest system.

    Scans plan/ and research/ directories, determines artifact type from
    filename patterns, extracts the GitHub issue number from YAML frontmatter,
    and calls artifact_register for each discovered file.

    Safe to re-run — artifact_register is idempotent (upserts on type+path).

    Args:
        dry_run: When True, only report what would be migrated.
        issue: When set, only process artifacts linked to this issue number.
        repo_root: Repository root directory. Auto-detected from script location.
    """
    # Discover repo slug for provider initialisation.
    try:
        repo_slug = discover_repo()
    except Exception as exc:
        err_console.print(f"[red]Cannot discover repository slug:[/red] {exc}")
        raise typer.Exit(1) from exc

    console.print(f":magnifying_glass_tilted_right: Repository: [cyan]{repo_slug}[/cyan]")
    console.print(f":open_file_folder: Repo root: [cyan]{repo_root}[/cyan]")
    if dry_run:
        console.print("[yellow]DRY RUN — no API calls will be made[/yellow]")
    if issue is not None:
        console.print(f":dart: Filtering to issue [cyan]#{issue}[/cyan]")

    # Fetch backlog items for slug-based fallback resolution.
    backlog_items: list[dict] = []
    if not dry_run:
        try:
            raw = _backlog_operations.list_items()
            if isinstance(raw, list):
                backlog_items = raw
        except Exception:  # noqa: BLE001
            console.print(
                "[yellow]Warning:[/yellow] Could not fetch backlog items for slug matching. Continuing without fallback."
            )

    # Discover all candidates.
    plan_candidates = _discover_plan_artifacts(repo_root, issue, backlog_items)
    research_candidates = _discover_research_artifacts(repo_root, issue, backlog_items)
    all_candidates = plan_candidates + research_candidates

    console.print(f":clipboard: Discovered [cyan]{len(all_candidates)}[/cyan] artifact(s)")

    if dry_run:
        _print_dry_run_table(all_candidates)
        return

    # Initialise provider + registry.
    provider = GitHubArtifactProvider(repo=repo_slug, root_worktree=repo_root)
    registry = ArtifactRegistry()
    result = MigrationResult()

    for candidate in all_candidates:
        issue_str = f"#{candidate.issue_number}" if candidate.issue_number else "—"
        if candidate.skip_reason:
            result.skipped += 1
            result.details.append(
                f"{candidate.path}|{candidate.artifact_type}|{issue_str}|[yellow]skipped — {candidate.skip_reason}[/yellow]"
            )
            continue

        try:
            _ok, action_msg = _register_artifact(provider, registry, candidate)
            result.migrated += 1
            result.details.append(f"{candidate.path}|{candidate.artifact_type}|{issue_str}|[green]{action_msg}[/green]")
        except Exception as exc:  # noqa: BLE001
            result.failed += 1
            result.details.append(f"{candidate.path}|{candidate.artifact_type}|{issue_str}|[red]FAILED: {exc}[/red]")
            err_console.print(f"[red]FAILED[/red] {candidate.path}: {exc}")

    _print_summary_table(all_candidates, result, dry_run=False)

    if result.failed > 0:
        raise typer.Exit(1)


def _print_dry_run_table(candidates: list[ArtifactCandidate]) -> None:
    """Print a dry-run preview table without performing any registrations.

    Args:
        candidates: All discovered artifact candidates.
    """
    table = Table(title="Artifact Migration — DRY RUN PREVIEW", show_lines=True)
    table.add_column("Path", style="cyan", no_wrap=False)
    table.add_column("Type", style="magenta")
    table.add_column("Issue", justify="right")
    table.add_column("Action")

    skipped = 0
    would_register = 0
    for c in candidates:
        issue_str = f"#{c.issue_number}" if c.issue_number else "—"
        if c.skip_reason:
            table.add_row(c.path, str(c.artifact_type), issue_str, f"[yellow]skip — {c.skip_reason}[/yellow]")
            skipped += 1
        else:
            table.add_row(c.path, str(c.artifact_type), issue_str, "[green]would register[/green]")
            would_register += 1

    console.print(table)
    console.print(
        f"\n:white_check_mark: Would register: [green]{would_register}[/green]  "
        f":next_track_button: Would skip: [yellow]{skipped}[/yellow]"
    )


if __name__ == "__main__":
    app()
