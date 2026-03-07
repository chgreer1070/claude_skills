#!/usr/bin/env python3
"""Pre-commit hook to enforce COMPAT annotation standards.

Scans Python files for COMPAT annotations and validates they contain
all required fields (issue=, remove_when=, added=). Also checks for
bare fm.get("task") calls without the task_id fallback guard.
"""

from __future__ import annotations

import argparse
import pathlib
import re
import sys

# Pattern to match COMPAT annotation lines
COMPAT_PATTERN = re.compile(r"#\s*COMPAT\(")

# Required fields inside a COMPAT annotation
REQUIRED_FIELDS: list[str] = ["issue=", "remove_when=", "added="]

# Bare fm.get("task") without the task_id fallback guard
# Matches fm.get("task") but NOT fm.get("task") if "task" in fm else fm.get("task_id")
# Also excludes fm.get("task_id") and fm.get("task_file")
BARE_TASK_GET_PATTERN = re.compile(
    r'fm\.get\(["\']task["\']\)'
    r'(?!\s*if\s+"task"\s+in\s+fm\s+else\s+fm\.get\(["\']task_id["\']\))'
)


def check_compat_annotation(line: str, file_path: str, line_number: int) -> str | None:
    """Validate a COMPAT annotation has all required fields.

    Args:
        line: The source line containing the COMPAT annotation.
        file_path: Path to the file being checked.
        line_number: 1-based line number.

    Returns:
        Error message string if validation fails, None if valid.
    """
    for field in REQUIRED_FIELDS:
        if field not in line:
            field_name = field.rstrip("=")
            return f"ERROR: {file_path}:{line_number}: COMPAT annotation missing required field '{field_name}'"
    return None


def check_bare_task_get(line: str, file_path: str, line_number: int, *, in_docstring: bool) -> str | None:
    """Check for bare fm.get("task") without task_id fallback.

    Args:
        line: The source line to check.
        file_path: Path to the file being checked.
        line_number: 1-based line number.
        in_docstring: Whether this line is inside a multi-line docstring.

    Returns:
        Error message string if a bare fm.get("task") is found, None if clean.
    """
    # Skip lines inside docstrings
    if in_docstring:
        return None

    stripped = line.lstrip()

    # Skip pure comment lines
    if stripped.startswith("#"):
        return None

    # Skip lines where every fm.get("task") match is inside a string literal.
    # Check each match position: if preceded by an f-string/string opener
    # pattern like `"...fm.get` or `'...fm.get`, it's inside a string, not code.
    has_code_match = False
    for m in re.finditer(r'fm\.get\(["\']task["\']\)', line):
        prefix = line[: m.start()]
        # Count unescaped quotes before match position. If the number of
        # unmatched double quotes is odd, the match is inside a string literal.
        double_quotes = len(re.findall(r'(?<!\\)"', prefix))
        single_quotes = len(re.findall(r"(?<!\\)'", prefix))
        if double_quotes % 2 == 0 and single_quotes % 2 == 0:
            has_code_match = True
            break
    if not has_code_match:
        return None

    if BARE_TASK_GET_PATTERN.search(line):
        return f'ERROR: {file_path}:{line_number}: bare fm.get("task") without task_id fallback'
    return None


def check_file(file_path: str) -> list[str]:
    """Scan a single Python file for COMPAT and bare task_get violations.

    Args:
        file_path: Path to the Python file to check.

    Returns:
        List of error message strings found in the file.
    """
    errors: list[str] = []

    if not file_path.endswith(".py"):
        return errors

    try:
        with pathlib.Path(file_path).open(encoding="utf-8") as f:
            lines = f.readlines()
    except OSError as exc:
        errors.append(f"ERROR: {file_path}: could not read file: {exc}")
        return errors

    in_docstring = False
    for i, line in enumerate(lines, start=1):
        # Track multi-line docstring boundaries (triple-quoted strings)
        triple_count = line.count('"""') + line.count("'''")
        if triple_count % 2 == 1:
            in_docstring = not in_docstring

        # Check COMPAT annotations
        if COMPAT_PATTERN.search(line):
            error = check_compat_annotation(line, file_path, i)
            if error:
                errors.append(error)

        # Check bare fm.get("task")
        error = check_bare_task_get(line, file_path, i, in_docstring=in_docstring)
        if error:
            errors.append(error)

    return errors


def main() -> int:
    """Run COMPAT annotation checker on provided files.

    Returns:
        Exit code: 0 if all clean, 1 if violations found.
    """
    parser = argparse.ArgumentParser(description="Enforce COMPAT annotation standards in Python files.")
    parser.add_argument("files", nargs="*", help="File paths to check (standard pre-commit hook interface).")
    parser.add_argument("--check-file", help="Check a single file (for manual invocation).")

    args = parser.parse_args()

    files_to_check: list[str] = list(args.files)
    if args.check_file:
        files_to_check.append(args.check_file)

    if not files_to_check:
        parser.error("No files provided. Pass file paths as arguments or use --check-file.")

    all_errors: list[str] = []
    for file_path in files_to_check:
        all_errors.extend(check_file(file_path))

    for error in all_errors:
        print(error)

    return 1 if all_errors else 0


if __name__ == "__main__":
    sys.exit(main())
