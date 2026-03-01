#!/usr/bin/env -S uv --quiet run --active --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "typer>=0.19.2",
# ]
# ///
"""Marketplace and plugin installer for Claude Code.

Wraps `claude plugin marketplace add` and `claude plugin install`.
"""

from __future__ import annotations

import subprocess

import typer

app = typer.Typer(name="install", help="Install Claude Code marketplaces and plugins")


def _run(cmd: list[str]) -> None:
    result = subprocess.run(cmd, check=False)
    if result.returncode != 0:
        raise typer.Exit(result.returncode)


@app.command()
def marketplace(
    source: str = typer.Argument(help="Path, URL, or GitHub repo (owner/repo)"),
    scope: str = typer.Option("user", help="Where to declare: user, project, or local"),
) -> None:
    """Add a marketplace to Claude Code."""
    _run(["claude", "plugin", "marketplace", "add", source, "--scope", scope])


@app.command()
def plugin(
    name: str = typer.Argument(help="Plugin name, optionally plugin@marketplace"),
    scope: str = typer.Option("user", help="Installation scope: user, project, or local"),
) -> None:
    """Install a plugin from an available marketplace."""
    _run(["claude", "plugin", "install", name, "--scope", scope])


if __name__ == "__main__":
    app()
