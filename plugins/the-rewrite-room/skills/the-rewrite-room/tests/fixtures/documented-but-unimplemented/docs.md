# DataProcessor

The `DataProcessor` class loads and transforms structured data records.

## Methods

### `load()`

Load records from the configured source.

### `filter(key, value)`

Filter loaded records by a key/value pair.

**Parameters:**

- `key` — field name to filter on
- `value` — value to match

**Returns:** filtered list of records

### `export_csv(path)`

Export all loaded records to a CSV file at the specified path.

**Parameters:**

- `path: str` — destination file path for the CSV export

**Returns:** `None`

**Example:**

```python
processor = DataProcessor("data.json")
processor.load()
processor.export_csv("output.csv")
```

> **Drift indicator**: The `export_csv(path: str)` method is documented here but does not
> exist in the DataProcessor class in code.py. This is a documented-but-unimplemented pattern.
