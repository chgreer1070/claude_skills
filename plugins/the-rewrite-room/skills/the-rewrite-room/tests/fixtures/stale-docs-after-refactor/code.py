"""Data processing module.

This module provides utilities for processing structured data records.
"""

from __future__ import annotations


def process_data(items: list[str]) -> dict[str, int]:
    """Process a list of string items and return a frequency count.

    Args:
        items: List of string items to process.

    Returns:
        Dictionary mapping each unique item to its occurrence count.

    """
    counts: dict[str, int] = {}
    for item in items:
        counts[item] = counts.get(item, 0) + 1
    return counts
