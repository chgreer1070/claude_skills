"""Schema validation module.

Provides utilities for validating data records against a schema definition.
"""

from __future__ import annotations


def validate_schema(data: dict, schema: dict) -> bool:
    """Validate a data dictionary against a schema definition.

    Checks that all required keys are present and that values match
    their expected types as declared in the schema.

    Args:
        data: The data record to validate.
        schema: Schema definition mapping field names to expected types.
                Example: {"name": str, "age": int, "active": bool}

    Returns:
        True if all required fields are present and correctly typed.
        False if any field is missing or has the wrong type.

    Example:
        schema = {"name": str, "age": int}
        validate_schema({"name": "Alice", "age": 30}, schema)  # True
        validate_schema({"name": "Alice"}, schema)              # False

    """
    for field, expected_type in schema.items():
        if field not in data:
            return False
        if not isinstance(data[field], expected_type):
            return False
    return True


def normalize_keys(data: dict) -> dict:
    """Normalize all string keys to lowercase with underscores replacing spaces.

    Args:
        data: Dictionary with potentially inconsistent key formatting.

    Returns:
        New dictionary with normalized keys.

    """
    return {k.lower().replace(" ", "_"): v for k, v in data.items()}
