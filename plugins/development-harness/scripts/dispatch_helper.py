"""Dispatch helper -- assembles the 5 inputs for generic agent dispatch.

The generic stage agent receives:
1. Stage workflow skill (from dh)
2. Cross-cutting SDLC stage skill (from dh)
3. Domain skills (from resolved manifest stage_skills)
4. Task/artifact file path
5. Quality gate commands (from resolved manifest quality_gates)
6. Output artifact path (where to write results)
"""

from __future__ import annotations

from textwrap import dedent
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

    from manifest_schema import LanguageManifest


def _format_quality_gates(manifest: LanguageManifest) -> str:
    """Format quality gates as runnable commands.

    Returns:
        Newline-joined quality gate commands, or a message if none configured.
    """
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
    """Format skill loading instructions.

    Returns:
        Newline-joined Skill() call instructions, or a message if none.
    """
    if not skills:
        return "No domain skills for this stage."
    lines: list[str] = [f'- Load: `Skill(skill="{skill}")`' for skill in skills]
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

    return dedent(f"""\
        # Stage Dispatch: {stage}
        **Language:** {manifest.language} | **Stack:** {manifest.stack or "base"} | **Manifest:** {manifest.name}

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
        Write your output artifact to: `{output_artifact_path or "next to the task file"}`""")
