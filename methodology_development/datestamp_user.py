#!/usr/bin/env -S uv --quiet run --active --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "typer>=0.12.0",
# ]
# ///
"""Print ISO timestamp and current username for methodology tracking."""

from __future__ import annotations

import getpass
from datetime import UTC, datetime

import typer


def main(
    utc: bool = typer.Option(
        False,
        "--utc/--local",
        help="Use UTC timestamp (default: local time with timezone).",
    ),
) -> None:
    """Print an ISO timestamp and the current username."""
    now = datetime.now(UTC) if utc else datetime.now().astimezone()
    typer.echo(f"timestamp={now.isoformat(timespec='seconds')}")
    typer.echo(f"username={getpass.getuser()}")


if __name__ == "__main__":
    typer.run(main)
