# Data Processing Module

This module provides utilities for processing structured data records.

## Functions

### `process_items(items)`

Process a list of items and return the processed results.

**Parameters:**

- `items` — list of items to process

**Returns:** processed result list

**Example:**

```python
result = process_items(["a", "b", "a"])
```

> **Drift indicator**: The function was renamed from `process_items` to `process_data` and its
> signature changed to `process_data(items: list[str]) -> dict[str, int]`. This documentation
> still references the old name `process_items` which no longer exists in the codebase.
