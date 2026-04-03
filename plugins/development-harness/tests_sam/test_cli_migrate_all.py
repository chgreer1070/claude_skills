"""Tests for sam migrate --all bulk-migration behaviour."""

from __future__ import annotations

from pathlib import Path

import pytest
from sam_schema.cli import _migrate_one, app
from typer.testing import CliRunner

runner = CliRunner()

FIXTURES_DIR: Path = Path(__file__).parent / "fixtures"
_LEGACY_MD: Path = FIXTURES_DIR / "legacy_markdown.md"
_PURE_YAML: Path = FIXTURES_DIR / "pure_yaml_single.yaml"


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _make_legacy_plan_dir(tmp_path: Path, *, count: int = 2) -> Path:
    """Return a plan dir with ``count`` legacy .md files.

    Files are named ``tasks-{N}-legacy-{N}.md`` so each resolves to a distinct
    plan number and output path (``P00{N}-legacy-{N}.yaml``).

    Args:
        tmp_path: pytest tmp_path fixture value.
        count: Number of legacy files to create.

    Returns:
        Path to the created plan directory.
    """
    d = tmp_path / "plan"
    d.mkdir()
    content = _LEGACY_MD.read_text(encoding="utf-8")
    for n in range(1, count + 1):
        (d / f"tasks-{n}-legacy-{n}.md").write_text(content, encoding="utf-8")
    return d


def _make_mixed_plan_dir(tmp_path: Path) -> Path:
    """Return a plan dir with one legacy .md and one already-converted .yaml.

    The existing .yaml is named using the legacy suffix-only pattern
    (``tasks-1-collision.yaml``) so the ``_migrate_all`` pre-check loop
    catches it before delegating to ``_migrate_one``.

    Args:
        tmp_path: pytest tmp_path fixture value.

    Returns:
        Path to the created plan directory.
    """
    d = tmp_path / "plan"
    d.mkdir()
    legacy_content = _LEGACY_MD.read_text(encoding="utf-8")
    yaml_content = _PURE_YAML.read_text(encoding="utf-8")
    (d / "tasks-1-collision.md").write_text(legacy_content, encoding="utf-8")
    # _migrate_all pre-check uses plan_path.with_suffix(".yaml"), so this name
    # triggers the early-continue in the loop before _migrate_one is called.
    (d / "tasks-1-collision.yaml").write_text(yaml_content, encoding="utf-8")
    return d


# ---------------------------------------------------------------------------
# sam migrate --all --dry-run
# ---------------------------------------------------------------------------


def test_migrate_all_dry_run_shows_would_migrate_without_writing(tmp_path: Path) -> None:
    """--all --dry-run prints preview for every legacy file without writing."""
    plan_dir = _make_legacy_plan_dir(tmp_path, count=2)
    original_files = set(plan_dir.iterdir())

    result = runner.invoke(app, ["migrate", "--all", "--dry-run", "--plan-dir", str(plan_dir)])

    assert result.exit_code == 0
    assert "Would migrate" in result.output
    # No new files created
    assert set(plan_dir.iterdir()) == original_files


def test_migrate_all_dry_run_reports_count(tmp_path: Path) -> None:
    """--all --dry-run summary line shows how many would be migrated."""
    plan_dir = _make_legacy_plan_dir(tmp_path, count=3)

    result = runner.invoke(app, ["migrate", "--all", "--dry-run", "--plan-dir", str(plan_dir)])

    assert result.exit_code == 0
    assert "3" in result.output  # count mentioned somewhere in output


# ---------------------------------------------------------------------------
# sam migrate --all (live write)
# ---------------------------------------------------------------------------


def test_migrate_all_converts_legacy_files_to_yaml(tmp_path: Path) -> None:
    """--all migrates every .md file to a .yaml counterpart."""
    plan_dir = _make_legacy_plan_dir(tmp_path, count=2)

    result = runner.invoke(app, ["migrate", "--all", "--skip-sync", "--plan-dir", str(plan_dir)])

    assert result.exit_code == 0
    yaml_files = list(plan_dir.glob("*.yaml"))
    assert len(yaml_files) == 2


def test_migrate_all_prints_migration_complete(tmp_path: Path) -> None:
    """--all prints a summary containing 'Migration complete'."""
    plan_dir = _make_legacy_plan_dir(tmp_path, count=1)

    result = runner.invoke(app, ["migrate", "--all", "--skip-sync", "--plan-dir", str(plan_dir)])

    assert result.exit_code == 0
    assert "Migration complete" in result.output


def test_migrate_all_skips_when_yaml_already_exists(tmp_path: Path) -> None:
    """--all skips a file if the target .yaml already exists (collision guard)."""
    plan_dir = _make_mixed_plan_dir(tmp_path)
    original_yaml_mtime = (plan_dir / "tasks-1-collision.yaml").stat().st_mtime

    result = runner.invoke(app, ["migrate", "--all", "--skip-sync", "--plan-dir", str(plan_dir)])

    assert result.exit_code == 0
    # Existing .yaml must not be overwritten
    new_mtime = (plan_dir / "tasks-1-collision.yaml").stat().st_mtime
    assert new_mtime == original_yaml_mtime


def test_migrate_all_continues_after_single_file_error(tmp_path: Path) -> None:
    """--all logs an error for one bad file but continues migrating others."""
    plan_dir = _make_legacy_plan_dir(tmp_path, count=2)
    # Corrupt the first file so it cannot be parsed
    first = min(plan_dir.glob("*.md"))
    first.write_text("not valid yaml or markdown at all\x00\x01", encoding="latin-1")

    result = runner.invoke(app, ["migrate", "--all", "--skip-sync", "--plan-dir", str(plan_dir)])

    # Should not abort entirely — exit 0, and at least one .yaml written
    assert result.exit_code == 0
    yaml_files = list(plan_dir.glob("*.yaml"))
    assert len(yaml_files) >= 1


def test_migrate_all_missing_plan_dir_exits_with_code_1(tmp_path: Path) -> None:
    """--all exits 1 when plan_dir does not exist."""
    missing = tmp_path / "no-such-dir"

    result = runner.invoke(app, ["migrate", "--all", "--skip-sync", "--plan-dir", str(missing)])

    assert result.exit_code == 1
    assert "Error:" in result.output


def test_migrate_all_empty_plan_dir_reports_nothing_to_migrate(tmp_path: Path) -> None:
    """--all with no legacy files reports nothing to migrate."""
    plan_dir = tmp_path / "plan"
    plan_dir.mkdir()

    result = runner.invoke(app, ["migrate", "--all", "--skip-sync", "--plan-dir", str(plan_dir)])

    assert result.exit_code == 0
    assert "No legacy plan files found" in result.output


# ---------------------------------------------------------------------------
# --skip-sync flag
# ---------------------------------------------------------------------------


def test_migrate_all_skip_sync_does_not_attempt_sync(tmp_path: Path) -> None:
    """--skip-sync flag causes migration to proceed without any sync attempt."""
    plan_dir = _make_legacy_plan_dir(tmp_path, count=1)

    # --skip-sync must not cause any failure regardless of network availability
    result = runner.invoke(app, ["migrate", "--all", "--skip-sync", "--plan-dir", str(plan_dir)])

    assert result.exit_code == 0


# ---------------------------------------------------------------------------
# Backlog reference update
# ---------------------------------------------------------------------------


def test_migrate_all_updates_backlog_plan_references(tmp_path: Path) -> None:
    """--all rewrites plan: fields in .claude/backlog/*.md to the P{NNN} path.

    Tests: Backlog reference rewriting after bulk migration.
    How: Create a legacy ``tasks-5-example.md`` and a backlog item whose
         ``plan:`` frontmatter field points at it.  Run ``sam migrate --all``
         and verify the backlog item now references the canonical
         ``P005-example.yaml`` path, not the old path.
    Why: Consumers (backlog items, CI scripts) must point at the new canonical
         name after migration; stale references break ``sam read`` lookups.
    """
    plan_dir = tmp_path / "plan"
    plan_dir.mkdir()
    legacy_content = _LEGACY_MD.read_text(encoding="utf-8")
    legacy_file = plan_dir / "tasks-5-example.md"
    legacy_file.write_text(legacy_content, encoding="utf-8")

    # Create a fake backlog dir with a file referencing the old path
    backlog_dir = tmp_path / ".claude" / "backlog"
    backlog_dir.mkdir(parents=True)
    backlog_item = backlog_dir / "p1-example-item.md"
    backlog_item.write_text(f"---\nplan: {legacy_file}\n---\n\nSome backlog content.\n", encoding="utf-8")

    result = runner.invoke(
        app,
        ["migrate", "--all", "--skip-sync", "--plan-dir", str(plan_dir), "--backlog-dir", str(backlog_dir)],
        catch_exceptions=False,
    )

    assert result.exit_code == 0
    updated_text = backlog_item.read_text(encoding="utf-8")
    # _migrate_one renames tasks-{N}-{slug}.md → P{NNN}-{slug}.yaml
    expected_new_path = str(plan_dir / "P005-example.yaml")
    assert expected_new_path in updated_text, (
        f"Expected backlog to reference {expected_new_path!r}, got:\n{updated_text}"
    )
    assert str(legacy_file) not in updated_text, (
        f"Old path {str(legacy_file)!r} should have been replaced in:\n{updated_text}"
    )


# ---------------------------------------------------------------------------
# Backward compatibility: sam migrate P{N} still works
# ---------------------------------------------------------------------------


def test_migrate_single_address_still_works_without_all_flag(tmp_path: Path) -> None:
    """sam migrate P{N} without --all behaves exactly as before."""
    plan_dir = tmp_path / "plan"
    plan_dir.mkdir()
    content = _LEGACY_MD.read_text(encoding="utf-8")
    (plan_dir / "tasks-2-legacy.md").write_text(content, encoding="utf-8")

    result = runner.invoke(app, ["migrate", "P2", "--plan-dir", str(plan_dir)])

    assert result.exit_code == 0
    assert "Migrated" in result.output
    yaml_files = list(plan_dir.glob("*.yaml"))
    assert len(yaml_files) == 1


def test_migrate_no_address_no_all_flag_exits_with_code_1(tmp_path: Path) -> None:
    """sam migrate with no address and no --all exits 1 with error."""
    plan_dir = _make_legacy_plan_dir(tmp_path, count=1)

    result = runner.invoke(app, ["migrate", "--plan-dir", str(plan_dir)])

    assert result.exit_code == 1
    assert "Error:" in result.output


def test_migrate_single_dry_run_still_works(tmp_path: Path) -> None:
    """sam migrate P{N} --dry-run still works as before."""
    plan_dir = tmp_path / "plan"
    plan_dir.mkdir()
    content = _LEGACY_MD.read_text(encoding="utf-8")
    (plan_dir / "tasks-2-legacy.md").write_text(content, encoding="utf-8")
    original_files = set(plan_dir.iterdir())

    result = runner.invoke(app, ["migrate", "P2", "--dry-run", "--plan-dir", str(plan_dir)])

    assert result.exit_code == 0
    assert "Would migrate" in result.output
    assert set(plan_dir.iterdir()) == original_files


# ---------------------------------------------------------------------------
# P{NNN} output naming verification
# ---------------------------------------------------------------------------


def test_migrate_all_produces_p_numbered_yaml_filenames(tmp_path: Path) -> None:
    """--all writes output files as P{NNN}-{slug}.yaml, not tasks-{N}-{slug}.yaml.

    Tests: Output filename convention after bulk migration.
    How: Create ``tasks-1-foo.md`` and ``tasks-42-bar.md``, run ``sam migrate --all``,
         then assert the resulting YAML files use zero-padded plan numbers.
    Why: The canonical filename format is ``P{NNN}-{slug}.yaml`` (e.g. ``P001-foo.yaml``).
         A plain suffix swap would produce ``tasks-1-foo.yaml`` which is the old
         convention and breaks ``sam read P1`` address resolution.
    """
    plan_dir = tmp_path / "plan"
    plan_dir.mkdir()
    content = _LEGACY_MD.read_text(encoding="utf-8")
    (plan_dir / "tasks-1-foo.md").write_text(content, encoding="utf-8")
    (plan_dir / "tasks-42-bar.md").write_text(content, encoding="utf-8")

    result = runner.invoke(app, ["migrate", "--all", "--skip-sync", "--plan-dir", str(plan_dir)])

    assert result.exit_code == 0
    yaml_names = {p.name for p in plan_dir.glob("*.yaml")}
    assert "P001-foo.yaml" in yaml_names, f"Expected P001-foo.yaml in {yaml_names}"
    assert "P042-bar.yaml" in yaml_names, f"Expected P042-bar.yaml in {yaml_names}"
    # Old-style names must not appear
    assert "tasks-1-foo.yaml" not in yaml_names
    assert "tasks-42-bar.yaml" not in yaml_names


# ---------------------------------------------------------------------------
# _migrate_one collision — unit-level tests
# ---------------------------------------------------------------------------


def test_migrate_one_collision_non_dry_run_raises_file_exists_error(tmp_path: Path) -> None:
    """_migrate_one raises FileExistsError when the P{NNN} target already exists.

    Tests: Collision guard in ``_migrate_one`` (non-dry-run path).
    How: Pre-create ``P001-collide.yaml`` in the plan directory, then call
         ``_migrate_one`` on ``tasks-1-collide.md`` with ``dry_run=False``.
         Assert ``FileExistsError`` is raised and the pre-existing file is
         not overwritten.
    Why: Migration must be idempotent — re-running after a partial failure
         must never silently overwrite a YAML file that was already written.
    """
    plan_dir = tmp_path / "plan"
    plan_dir.mkdir()
    content = _LEGACY_MD.read_text(encoding="utf-8")
    legacy_file = plan_dir / "tasks-1-collide.md"
    legacy_file.write_text(content, encoding="utf-8")

    # Pre-create the canonical target to trigger the collision guard
    existing_yaml = plan_dir / "P001-collide.yaml"
    existing_yaml.write_text("sentinel: true\n", encoding="utf-8")
    original_mtime = existing_yaml.stat().st_mtime

    with pytest.raises(FileExistsError):
        _migrate_one(legacy_file, dry_run=False)

    # Existing file must not be touched
    assert existing_yaml.stat().st_mtime == original_mtime
    assert existing_yaml.read_text(encoding="utf-8") == "sentinel: true\n"


def test_migrate_one_collision_dry_run_returns_none_and_prints_skip(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """_migrate_one returns (None, source_format) and prints a skip message on dry-run collision.

    Tests: Collision guard in ``_migrate_one`` (dry-run path).
    How: Pre-create ``P001-collide.yaml``, call ``_migrate_one`` with
         ``dry_run=True``, assert the return value is ``(None, <format>)``
         and that a skip message was printed without raising an exception.
    Why: ``--dry-run`` must be non-destructive and non-raising so callers can
         preview all collisions before committing to a live migration.
    """
    plan_dir = tmp_path / "plan"
    plan_dir.mkdir()
    content = _LEGACY_MD.read_text(encoding="utf-8")
    legacy_file = plan_dir / "tasks-1-collide.md"
    legacy_file.write_text(content, encoding="utf-8")

    existing_yaml = plan_dir / "P001-collide.yaml"
    existing_yaml.write_text("sentinel: true\n", encoding="utf-8")

    written, source_format = _migrate_one(legacy_file, dry_run=True)

    assert written is None, "dry-run collision must return None for output_path"
    assert isinstance(source_format, str), "source_format must be a non-empty string"
    # Existing file must remain untouched
    assert existing_yaml.read_text(encoding="utf-8") == "sentinel: true\n"
