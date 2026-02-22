#!/usr/bin/env -S uv --quiet run --active --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["typer>=0.21.0", "rich>=14.0.0", "ruamel.yaml>=0.18.0"]
# ///
"""The Rewrite Room — Workflow Router.

Classifies a task description and selects the appropriate canonical workflow.
Reads routing-rules.yaml to determine intent, source types, and artifact targets.
"""

from __future__ import annotations

import operator
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table
from ruamel.yaml import YAML

app = typer.Typer(name="router", help="The Rewrite Room workflow router")
console = Console()
err_console = Console(stderr=True)

SCRIPT_DIR = Path(__file__).parent
REGISTRY_DIR = SCRIPT_DIR.parent / "registry"
ROUTING_RULES_PATH = REGISTRY_DIR / "routing-rules.yaml"
WORKFLOWS_PATH = REGISTRY_DIR / "workflows.yaml"

# Minimum confidence percentage for second-place workflow to trigger disambiguation note
SECONDARY_CONFIDENCE_THRESHOLD = 30


def _load_yaml(path: Path) -> dict:
    """Load a YAML file using ruamel.yaml."""
    yaml = YAML()
    yaml.preserve_quotes = True
    with path.open(encoding="utf-8") as fh:
        return yaml.load(fh)


def _load_routing_rules() -> dict:
    """Load routing-rules.yaml from registry."""
    if not ROUTING_RULES_PATH.exists():
        err_console.print(
            f"[red]ERROR[/red] routing-rules.yaml not found at {ROUTING_RULES_PATH}"
        )
        raise typer.Exit(1)
    return _load_yaml(ROUTING_RULES_PATH)


def _load_workflows() -> dict:
    """Load workflows.yaml from registry."""
    if not WORKFLOWS_PATH.exists():
        err_console.print(
            f"[red]ERROR[/red] workflows.yaml not found at {WORKFLOWS_PATH}"
        )
        raise typer.Exit(1)
    return _load_yaml(WORKFLOWS_PATH)


def _score_workflow(
    description: str,
    workflow_id: str,
    signals: dict,
    source_type: str | None,
    artifact: str | None,
) -> float:
    """Score a workflow by keyword matches, source_type, and artifact signals."""
    description_lower = description.lower()
    score = 0.0

    keywords = signals.get("keywords", [])
    for keyword in keywords:
        if keyword.lower() in description_lower:
            score += 1.0

    source_signals = signals.get("source_signals", [])
    if source_type and source_type in source_signals:
        score *= 1.5

    artifact_signals = signals.get("artifact_signals", [])
    if artifact and artifact in artifact_signals:
        score *= 1.3

    return score


def _get_chain(workflow_id: str, rules: dict) -> list[str]:
    """Get the workflow chain for a given workflow ID."""
    chain_rules = rules.get("routing", {}).get("chain_rules", [])
    for rule in chain_rules:
        if rule.get("pattern") == workflow_id:
            return rule.get("chain", [workflow_id])
    return [workflow_id]


@app.command()
def classify(
    description: Annotated[str, typer.Argument(help="Task description to classify")],
    source_type: Annotated[
        str | None,
        typer.Option(
            "--source-type", help="Source type: file, url, image, diff, git-diff"
        ),
    ] = None,
    artifact: Annotated[
        str | None,
        typer.Option(
            "--artifact", help="Artifact target: README.md, CLAUDE.md, SKILL.md, docs"
        ),
    ] = None,
) -> None:
    """Classify a task description and select the appropriate workflow."""
    rules = _load_routing_rules()
    intent_signals = rules.get("routing", {}).get("intent_signals", {})

    scores: dict[str, float] = {}
    for workflow_id, signals in intent_signals.items():
        scores[workflow_id] = _score_workflow(
            description, workflow_id, signals, source_type, artifact
        )

    if not any(s > 0 for s in scores.values()):
        console.print(
            "[yellow]No workflow matched. Try describing the task differently or use --source-type and --artifact flags.[/yellow]"
        )
        raise typer.Exit(0)

    ranked = sorted(scores.items(), key=operator.itemgetter(1), reverse=True)
    top_id, top_score = ranked[0]
    total = sum(s for _, s in ranked if s > 0)
    confidence = (top_score / total * 100) if total > 0 else 0.0

    chain = _get_chain(top_id, rules)

    console.print(f"\n[bold green]Workflow:[/bold green] {top_id}")
    console.print(f"[bold]Confidence:[/bold] {confidence:.0f}%")
    console.print(f"[bold]Chain:[/bold] {' → '.join(chain)}")

    if len(ranked) > 1 and ranked[1][1] > 0:
        second_id, second_score = ranked[1]
        second_conf = second_score / total * 100 if total > 0 else 0.0
        if second_conf > SECONDARY_CONFIDENCE_THRESHOLD:
            console.print(
                f"\n[yellow]Note:[/yellow] {second_id} also matched ({second_conf:.0f}%). Use --source-type or --artifact to disambiguate."
            )

    hybrid_rules = rules.get("routing", {}).get("disambiguation", [])
    for rule in hybrid_rules:
        conflict = rule.get("conflict", [])
        if top_id in conflict and len(ranked) > 1 and ranked[1][0] in conflict:
            console.print(
                f"\n[yellow]Disambiguation hint:[/yellow] {rule.get('resolution', '')}"
            )


@app.command(name="list")
def list_workflows() -> None:
    """List all registered workflows."""
    workflows_data = _load_workflows()
    workflows = workflows_data.get("workflows", [])

    table = Table(
        title="Registered Workflows", show_header=True, header_style="bold cyan"
    )
    table.add_column("ID", style="bold", min_width=22)
    table.add_column("Name", min_width=24)
    table.add_column("Canonical", min_width=32)
    table.add_column("Validators")

    for wf in workflows:
        canonical = (
            wf.get("canonical_agent")
            or wf.get("canonical_skill")
            or str(wf.get("canonical_tools", ["multiple"])[0].get("name", "multiple"))
        )
        validators = ", ".join(wf.get("validators", []))
        table.add_row(wf.get("id", ""), wf.get("name", ""), canonical, validators)

    console.print(table)


if __name__ == "__main__":
    app()
