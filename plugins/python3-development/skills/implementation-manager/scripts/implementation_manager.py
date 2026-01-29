#!/usr/bin/env python3
"""Implementation Manager CLI - Query and manage feature implementation task status.

This CLI tool provides commands to query task files for feature implementations,
returning JSON output for orchestrator consumption.

Usage:
    ./implementation_manager.py list-features /path/to/project
    ./implementation_manager.py status /path/to/project prepare-host
    ./implementation_manager.py ready-tasks /path/to/project prepare-host
    ./implementation_manager.py validate /path/to/project prepare-host
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from enum import IntEnum, StrEnum
from pathlib import Path
from typing import Annotated, TypedDict

import typer
from rich.console import Console

app = typer.Typer(
    name="implementation-manager",
    help="Query and manage feature implementation task status.",
    no_args_is_help=True,
)
console = Console()


# =============================================================================
# Enums and Data Models
# =============================================================================


class TaskStatus(StrEnum):
    """Status of a task in the task file."""

    NOT_STARTED = "NOT STARTED"
    IN_PROGRESS = "IN PROGRESS"
    COMPLETE = "COMPLETE"


class TaskPriority(IntEnum):
    """Priority levels for tasks (1=highest, 5=lowest).

    Used to order task execution and validate priority values.
    Raises ValueError when instantiated with an invalid value.
    """

    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4
    LOWEST = 5


@dataclass
class Task:
    """Represents a single task parsed from a task file.

    Args:
        id: Task identifier (e.g., "1.1", "2.3")
        name: Task name/title
        status: Current task status
        dependencies: List of dependency task IDs
        agent: Agent name to execute this task
        priority: Task priority (1-5)
        complexity: Task complexity (Low/Medium/High)
        started: ISO timestamp when task started
        completed: ISO timestamp when task completed
    """

    id: str
    name: str
    status: TaskStatus
    dependencies: list[str] = field(default_factory=list)
    agent: str | None = None
    priority: TaskPriority = TaskPriority.CRITICAL
    complexity: str = "Medium"
    started: str | None = None
    completed: str | None = None

    def to_dict(self) -> TaskDict:
        """Convert task to dictionary for JSON serialization.

        Returns:
            TaskDict with enum fields converted to primitive values.
        """
        return TaskDict(
            id=self.id,
            name=self.name,
            status=self.status.value,
            dependencies=self.dependencies,
            agent=self.agent,
            priority=self.priority.value,
            complexity=self.complexity,
            started=self.started,
            completed=self.completed,
        )


@dataclass
class Feature:
    """Represents a feature with its task file.

    Args:
        slug: Feature slug derived from filename
        task_file: Filename of the task file
        path: Full path to the task file
    """

    slug: str
    task_file: str
    path: Path

    def to_dict(self) -> dict[str, str]:
        """Convert feature to dictionary for JSON serialization.

        Returns:
            Dictionary with slug, task_file, and path as strings.
        """
        return {"slug": self.slug, "task_file": self.task_file, "path": str(self.path)}


class TaskData(TypedDict):
    """Type-safe dictionary for task parsing intermediate state.

    Used during parsing before converting to Task dataclass.
    All fields use enum types for type safety.
    """

    id: str
    name: str
    status: TaskStatus
    dependencies: list[str]
    agent: str | None
    priority: TaskPriority
    complexity: str
    started: str | None
    completed: str | None


class TaskDict(TypedDict):
    """Type-safe dictionary for JSON serialization of Task.

    All enum fields are converted to their primitive values.
    Used as the return type for Task.to_dict().
    """

    id: str
    name: str
    status: str  # TaskStatus.value
    dependencies: list[str]
    agent: str | None
    priority: int  # TaskPriority.value
    complexity: str
    started: str | None
    completed: str | None


# =============================================================================
# Task File Parsing
# =============================================================================


def parse_status(status_text: str) -> TaskStatus:
    """Parse task status from various formats.

    Handles emoji formats like :white_check_mark:, :x:, etc.

    Args:
        status_text: Raw status text from task file.

    Returns:
        Normalized TaskStatus enum value.
    """
    status_lower = status_text.lower().strip()

    # Check for COMPLETE indicators
    complete_patterns = [
        "complete",
        ":white_check_mark:",
        ":heavy_check_mark:",
        "\\u2705",  # Unicode checkmark
        "\\u2714",  # Heavy checkmark
    ]
    for pattern in complete_patterns:
        if pattern in status_lower:
            return TaskStatus.COMPLETE

    # Check for IN PROGRESS indicators
    in_progress_patterns = [
        "in progress",
        "in_progress",
        ":arrows_counterclockwise:",
        ":repeat:",
        "\\ud83d\\udd04",  # Unicode arrows
    ]
    for pattern in in_progress_patterns:
        if pattern in status_lower:
            return TaskStatus.IN_PROGRESS

    # Check for NOT STARTED indicators
    not_started_patterns = [
        "not started",
        "not_started",
        ":x:",
        ":cross_mark:",
        "\\u274c",  # Unicode cross
    ]
    for pattern in not_started_patterns:
        if pattern in status_lower:
            return TaskStatus.NOT_STARTED

    # Default to NOT_STARTED if unclear
    return TaskStatus.NOT_STARTED


def parse_dependencies(dep_text: str) -> list[str]:
    """Parse dependency references from task file.

    Handles formats like "Task 1, Task 2", "Task 1.1, Task 1.2", "None".

    Args:
        dep_text: Raw dependencies text from task file.

    Returns:
        List of dependency task IDs.
    """
    if not dep_text or dep_text.lower().strip() == "none":
        return []

    # Extract task IDs from various formats
    # Match "Task X.Y" or "Task X" patterns
    pattern = r"Task\s+(\d+(?:\.\d+)?)"
    return re.findall(pattern, dep_text, re.IGNORECASE)


# =============================================================================
# Field Parsers (OCP: extend by adding new parsers, not modifying existing code)
# =============================================================================


class FieldParser:
    """Protocol for task field parsers (SRP: each parser handles one field)."""

    pattern: re.Pattern[str]

    def parse(self, match: re.Match[str], task_data: dict[str, object]) -> None:
        """Parse matched field and update task_data."""
        raise NotImplementedError


class StatusParser(FieldParser):
    """Parse **Status** field."""

    pattern = re.compile(r"^\*\*Status\*\*:\s*(.+)$")

    def parse(self, match: re.Match[str], task_data: dict[str, object]) -> None:
        """Parse status field and update task data.

        Args:
            match: Regex match object containing the captured status value.
            task_data: Mutable dictionary to update with parsed status.
        """
        task_data["status"] = parse_status(match.group(1))


class DependenciesParser(FieldParser):
    """Parse **Dependencies** field."""

    pattern = re.compile(r"^\*\*Dependencies\*\*:\s*(.+)$")

    def parse(self, match: re.Match[str], task_data: dict[str, object]) -> None:
        """Parse dependencies field and update task data.

        Args:
            match: Regex match object containing the captured dependencies.
            task_data: Mutable dictionary to update with parsed list.
        """
        task_data["dependencies"] = parse_dependencies(match.group(1))


class AgentParser(FieldParser):
    """Parse **Agent** field."""

    pattern = re.compile(r"^\*\*Agent\*\*:\s*(.+)$")

    def parse(self, match: re.Match[str], task_data: dict[str, object]) -> None:
        """Parse agent field and update task data if valid.

        Args:
            match: Regex match object containing the captured agent name.
            task_data: Mutable dictionary to update with agent value.

        Note:
            Agent values of 'none', 'n/a', or '-' are ignored.
        """
        agent_value = match.group(1).strip()
        if agent_value.lower() not in {"none", "n/a", "-"}:
            task_data["agent"] = agent_value


class PriorityParser(FieldParser):
    """Parse **Priority** field."""

    pattern = re.compile(r"^\*\*Priority\*\*:\s*(\d+)")

    def parse(self, match: re.Match[str], task_data: dict[str, object]) -> None:
        """Parse priority field and convert to TaskPriority enum.

        Args:
            match: Regex match object containing the captured priority digit.
            task_data: Mutable dictionary to update with TaskPriority.

        Raises:
            ValueError: If priority value is not a valid TaskPriority.
        """
        task_data["priority"] = TaskPriority(int(match.group(1)))


class ComplexityParser(FieldParser):
    """Parse **Complexity** field."""

    pattern = re.compile(r"^\*\*Complexity\*\*:\s*(\w+)")

    def parse(self, match: re.Match[str], task_data: dict[str, object]) -> None:
        """Parse complexity field and update task data.

        Args:
            match: Regex match object containing the captured complexity word.
            task_data: Mutable dictionary to update with complexity string.
        """
        task_data["complexity"] = match.group(1)


class StartedParser(FieldParser):
    """Parse **Started** field."""

    pattern = re.compile(r"^\*\*Started\*\*:\s*(.+)$")

    def parse(self, match: re.Match[str], task_data: dict[str, object]) -> None:
        """Parse started timestamp and update task data.

        Args:
            match: Regex match object containing the captured timestamp.
            task_data: Mutable dictionary to update with started value.
        """
        task_data["started"] = match.group(1).strip()


class CompletedParser(FieldParser):
    """Parse **Completed** field."""

    pattern = re.compile(r"^\*\*Completed\*\*:\s*(.+)$")

    def parse(self, match: re.Match[str], task_data: dict[str, object]) -> None:
        """Parse completed timestamp and update task data.

        Args:
            match: Regex match object containing the captured timestamp.
            task_data: Mutable dictionary to update with completed value.
        """
        task_data["completed"] = match.group(1).strip()


# Registry of field parsers (OCP: add new parsers here without modifying core logic)
FIELD_PARSERS: list[FieldParser] = [
    StatusParser(),
    DependenciesParser(),
    AgentParser(),
    PriorityParser(),
    ComplexityParser(),
    StartedParser(),
    CompletedParser(),
]


# =============================================================================
# Task Parsing (SRP: separated into focused functions)
# =============================================================================


def _create_empty_task_data(task_id: str, task_name: str) -> TaskData:
    """Create a new task data dictionary with defaults.

    Args:
        task_id: Task identifier from header.
        task_name: Task name from header.

    Returns:
        TaskData dictionary with all fields initialized to defaults.
    """
    return TaskData(
        id=task_id,
        name=task_name,
        status=TaskStatus.NOT_STARTED,
        dependencies=[],
        agent=None,
        priority=TaskPriority.CRITICAL,
        complexity="Medium",
        started=None,
        completed=None,
    )


def _parse_line(line: str, task_data: TaskData) -> None:
    """Parse a single line and update task_data if a field matches.

    Iterates through registered FieldParsers and applies the first match.

    Args:
        line: Line of text to parse.
        task_data: TaskData dictionary to update in-place.
    """
    for parser in FIELD_PARSERS:
        match = parser.pattern.match(line)
        if match:
            parser.parse(match, task_data)  # type: ignore[arg-type]
            return


def parse_task_content(content: str) -> list[Task]:
    """Parse task content and extract all tasks.

    Follows SRP by delegating field parsing to FieldParser implementations.

    Args:
        content: Raw text content of task file.

    Returns:
        List of Task objects parsed from the content.
    """
    tasks: list[Task] = []
    task_header_pattern = re.compile(r"^##\s+Task\s+([\d.]+):\s*(.+)$")
    current_task: TaskData | None = None

    for line in content.split("\n"):
        header_match = task_header_pattern.match(line)
        if header_match:
            if current_task:
                tasks.append(_create_task_from_dict(current_task))
            current_task = _create_empty_task_data(
                header_match.group(1), header_match.group(2).strip()
            )
        elif current_task:
            _parse_line(line, current_task)

    if current_task:
        tasks.append(_create_task_from_dict(current_task))

    return tasks


def parse_task_file(file_path: Path) -> list[Task]:
    """Parse a task file and extract all tasks.

    Follows DIP by separating file I/O from parsing logic.

    Args:
        file_path: Path to the task file.

    Returns:
        List of Task objects parsed from the file.

    Raises:
        FileNotFoundError: If the task file does not exist.
    """
    content = file_path.read_text(encoding="utf-8")
    return parse_task_content(content)


def _create_task_from_dict(task_data: TaskData) -> Task:
    """Create a Task dataclass from a TaskData dictionary.

    Args:
        task_data: Type-safe dictionary with all task fields.

    Returns:
        Task dataclass instance with validated fields.
    """
    return Task(
        id=task_data["id"],
        name=task_data["name"],
        status=task_data["status"],
        dependencies=task_data["dependencies"],
        agent=task_data["agent"],
        priority=task_data["priority"],
        complexity=task_data["complexity"],
        started=task_data["started"],
        completed=task_data["completed"],
    )


def discover_plan_directory(project_path: Path) -> Path | None:
    """Discover the plan directory in a project.

    Searches common locations for plan directories containing task files.
    The search prioritizes explicit common locations before falling back
    to a recursive search with depth limits for performance.

    Search order (first match wins):
    1. Explicit common locations: plan/, .claude/plan/, plans/, docs/plan/
    2. Package-level plan directories: */plan/, packages/*/plan/
    3. Recursive search (limited depth) for any plan/ or plans/ directory

    Args:
        project_path: Root path of the project.

    Returns:
        Path to plan directory if found with task files, None otherwise.
    """
    task_file_pattern = "tasks-*.md"

    # Priority 1: Check explicit common locations (fast path)
    common_locations = [
        project_path / "plan",
        project_path / ".claude" / "plan",
        project_path / "plans",
        project_path / "docs" / "plan",
        project_path / "docs" / "plans",
    ]

    for location in common_locations:
        if (
            location.exists()
            and location.is_dir()
            and list(location.glob(task_file_pattern))
        ):
            return location

    # Priority 2: Check package-level plan directories (monorepo support)
    package_patterns = [
        project_path / "*" / "plan",
        project_path / "packages" / "*" / "plan",
        project_path / "src" / "*" / "plan",
    ]

    for pattern in package_patterns:
        for plan_dir in sorted(pattern.parent.glob(pattern.name)):
            if plan_dir.is_dir() and list(plan_dir.glob(task_file_pattern)):
                return plan_dir

    # Priority 3: Recursive search with depth limit (slower, but comprehensive)
    # Limit to 3 levels deep to avoid scanning entire filesystems
    max_depth = 3
    for depth in range(1, max_depth + 1):
        glob_pattern = "/".join(["*"] * depth) + "/plan"
        for plan_dir in sorted(project_path.glob(glob_pattern)):
            if plan_dir.is_dir() and list(plan_dir.glob(task_file_pattern)):
                return plan_dir

        glob_pattern = "/".join(["*"] * depth) + "/plans"
        for plan_dir in sorted(project_path.glob(glob_pattern)):
            if plan_dir.is_dir() and list(plan_dir.glob(task_file_pattern)):
                return plan_dir

    return None


def find_task_files(project_path: Path) -> list[Feature]:
    """Find all task files in the plan directory.

    Uses discover_plan_directory to locate the plan directory dynamically,
    supporting various project structures including:
    - Standard: project/plan/
    - Claude-specific: project/.claude/plan/
    - Documentation: project/docs/plan/
    - Monorepo: project/packages/*/plan/

    Args:
        project_path: Root path of the project.

    Returns:
        List of Feature objects representing task files.
    """
    plan_dir = discover_plan_directory(project_path)

    if plan_dir is None:
        return []

    features: list[Feature] = []
    pattern = re.compile(r"tasks-(\d+)-(.+)\.md$")

    for file_path in sorted(plan_dir.glob("tasks-*.md")):
        match = pattern.match(file_path.name)
        if match:
            slug = match.group(2)
            features.append(
                Feature(slug=slug, task_file=file_path.name, path=file_path)
            )

    return features


def find_task_file_by_slug(project_path: Path, slug: str) -> Path | None:
    """Find task file by feature slug.

    Args:
        project_path: Root path of the project.
        slug: Feature slug (e.g., "prepare-host").

    Returns:
        Path to task file if found, None otherwise.
    """
    features = find_task_files(project_path)

    for feature in features:
        if feature.slug == slug:
            return feature.path

    # Try partial match
    for feature in features:
        if slug in feature.slug:
            return feature.path

    return None


def get_ready_tasks(tasks: list[Task]) -> list[Task]:
    """Get tasks that are ready for execution.

    A task is ready when:
    1. Status is NOT_STARTED
    2. All dependencies are COMPLETE (or no dependencies)

    Args:
        tasks: List of all tasks.

    Returns:
        List of tasks ready for execution.
    """
    # Build a lookup for task status by ID
    status_by_id: dict[str, TaskStatus] = {task.id: task.status for task in tasks}

    ready: list[Task] = []

    for task in tasks:
        # Skip if not NOT_STARTED
        if task.status != TaskStatus.NOT_STARTED:
            continue

        # Check if all dependencies are complete
        deps_satisfied = True
        for dep_id in task.dependencies:
            dep_status = status_by_id.get(dep_id)
            if dep_status != TaskStatus.COMPLETE:
                deps_satisfied = False
                break

        if deps_satisfied:
            ready.append(task)

    return ready


# =============================================================================
# CLI Commands
# =============================================================================


ProjectPath = Annotated[
    Path,
    typer.Argument(
        help="Path to the project root directory.",
        exists=True,
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
    ),
]

FeatureSlug = Annotated[
    str, typer.Argument(help="Feature slug (e.g., 'prepare-host') or partial match.")
]


@app.command(name="list-features")
def list_features(project_path: ProjectPath) -> None:
    """List all features with task files.

    Args:
        project_path: Path to the project root directory.
    """
    features = find_task_files(project_path)

    output = {"features": [f.to_dict() for f in features], "count": len(features)}

    console.print(json.dumps(output, indent=2))


@app.command(name="status")
def status(project_path: ProjectPath, feature_slug: FeatureSlug) -> None:
    """Get detailed status for a specific feature.

    Args:
        project_path: Path to the project root directory.
        feature_slug: Feature slug or partial match.
    """
    task_file = find_task_file_by_slug(project_path, feature_slug)

    if not task_file:
        error_output = {
            "error": f"No task file found for feature: {feature_slug}",
            "available_features": [f.slug for f in find_task_files(project_path)],
        }
        console.print(json.dumps(error_output, indent=2))
        raise typer.Exit(1)

    tasks = parse_task_file(task_file)
    ready_tasks = get_ready_tasks(tasks)

    # Calculate statistics
    completed = sum(1 for t in tasks if t.status == TaskStatus.COMPLETE)
    in_progress = sum(1 for t in tasks if t.status == TaskStatus.IN_PROGRESS)
    not_started = sum(1 for t in tasks if t.status == TaskStatus.NOT_STARTED)

    output = {
        "feature": feature_slug,
        "task_file": task_file.name,
        "total_tasks": len(tasks),
        "completed": completed,
        "in_progress": in_progress,
        "not_started": not_started,
        "ready_tasks": [
            {"id": t.id, "name": t.name, "agent": t.agent} for t in ready_tasks
        ],
        "tasks": [t.to_dict() for t in tasks],
    }

    console.print(json.dumps(output, indent=2))


@app.command(name="ready-tasks")
def ready_tasks(project_path: ProjectPath, feature_slug: FeatureSlug) -> None:
    """List tasks ready for execution (dependencies satisfied).

    Args:
        project_path: Path to the project root directory.
        feature_slug: Feature slug or partial match.
    """
    task_file = find_task_file_by_slug(project_path, feature_slug)

    if not task_file:
        error_output = {
            "error": f"No task file found for feature: {feature_slug}",
            "available_features": [f.slug for f in find_task_files(project_path)],
        }
        console.print(json.dumps(error_output, indent=2))
        raise typer.Exit(1)

    tasks = parse_task_file(task_file)
    ready = get_ready_tasks(tasks)

    output = {
        "feature": feature_slug,
        "ready_tasks": [{"id": t.id, "name": t.name, "agent": t.agent} for t in ready],
        "count": len(ready),
    }

    console.print(json.dumps(output, indent=2))


@app.command(name="validate")
def validate(project_path: ProjectPath, feature_slug: FeatureSlug) -> None:
    """Validate task file frontmatter and structure.

    Args:
        project_path: Path to the project root directory.
        feature_slug: Feature slug or partial match.
    """
    task_file = find_task_file_by_slug(project_path, feature_slug)

    if not task_file:
        error_output = {
            "error": f"No task file found for feature: {feature_slug}",
            "available_features": [f.slug for f in find_task_files(project_path)],
        }
        console.print(json.dumps(error_output, indent=2))
        raise typer.Exit(1)

    tasks = parse_task_file(task_file)
    errors: list[str] = []
    warnings: list[str] = []

    # Validate each task
    for task in tasks:
        # Check for missing agent field
        if not task.agent:
            warnings.append(f"Task {task.id} missing Agent field")

        # Priority validation happens at parse time via TaskPriority enum constructor

        # Validate dependencies exist
        task_ids = {t.id for t in tasks}
        errors.extend(
            f"Task {task.id} has unknown dependency: Task {dep_id}"
            for dep_id in task.dependencies
            if dep_id not in task_ids
        )

    # Check for duplicate task IDs
    task_ids_list = [t.id for t in tasks]
    seen: set[str] = set()
    for task_id in task_ids_list:
        if task_id in seen:
            errors.append(f"Duplicate task ID: {task_id}")
        seen.add(task_id)

    output = {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "task_count": len(tasks),
    }

    console.print(json.dumps(output, indent=2))

    if errors:
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
