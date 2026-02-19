# Functions Reference

Complete dasel v3 function reference with signatures, descriptions, and examples. 19 built-in functions registered in `DefaultFuncCollection` (source: `execution/func.go:12-33`) plus the `sortBy` complex expression.

## filter(predicate)

Filter array elements matching a predicate. Returns a new array.

**Signature**: `array.filter(predicate)` or `filter(predicate)`

```bash
# Filter objects where active is true
echo '[{"name":"A","active":true},{"name":"B","active":false}]' \
  | dasel -i json 'filter(active == true)'
# Output: [{"name":"A","active":true}]

# Filter by numeric comparison
echo '[1,2,3,4,5]' | dasel -i json 'filter($this > 3)'
# Output: [4, 5]

# Combined predicates
dasel -f data.json 'users.filter(age >= 18 && active == true)'
```

**Returns**: Array of elements where predicate is true.

## map(expression)

Transform each element of an array. Returns a new array.

**Signature**: `array.map(expression)`

```bash
# Extract single field from array of objects
echo '[{"name":"Alice","age":30},{"name":"Bob","age":25}]' \
  | dasel -i json 'map(name)'
# Output: ["Alice", "Bob"]

# Arithmetic transformation
echo '[1,2,3]' | dasel -i json 'map($this * 2)'
# Output: [2, 4, 6]

# Map to object construction
dasel -f data.json 'users.map({ name, email })'
```

**Returns**: Array of transformed values.

## each(expression)

Modify each element in place. Used with `--root` for document modification.

**Signature**: `array.each(assignment)` or `each(assignment)`

```bash
# Multiply all values by 2
echo '[1,2,3,4,5]' | dasel -i json --root 'each($this = $this * 2)'
# Output: [2, 4, 6, 8, 10]

# Increment all integers
echo '[10,20,30]' | dasel -i json --root 'each($this = $this + 1)'
# Output: [11, 21, 31]

# Set a field on all objects
echo '[{"name":"A","score":0},{"name":"B","score":0}]' \
  | dasel -i json --root 'each(score = 100)'
# Output: [{"name":"A","score":100},{"name":"B","score":100}]
```

**Returns**: Modified array (use with `--root` to get full document output).

## search(predicate)

Recursively search through entire document tree for nodes matching a predicate. More powerful than `..` because it supports arbitrary conditions.

**Signature**: `search(predicate)`

```bash
# Find all objects with a "name" key
dasel -f data.json 'search(has("name"))'

# Find nodes where value equals 42
dasel -f data.json 'search($this == 42)'

# Combined predicate search
dasel -f data.json 'search(has("id") && has("name"))'

# Search with type check
dasel -f data.json 'search(typeOf($this) == "string")'
```

**Returns**: Array of all matching nodes found at any depth.

## has(key)

Check whether a key or index exists in the current node.

**Signature**: `has(key_string)` or `has(index)`

```bash
# Check key existence
echo '{"foo": "bar", "baz": 42}' | dasel -i json 'has("foo")'
# Output: true

echo '{"foo": "bar"}' | dasel -i json 'has("missing")'
# Output: false

# Use in filter predicate
dasel -f data.json 'items.filter(has("metadata"))'

# Check array index exists
echo '[1,2,3]' | dasel -i json 'has(5)'
# Output: false
```

**Returns**: `true` or `false`.

## len(expression)

Get the length of an array or string.

**Signature**: `len(expression)`

```bash
# Array length
echo '[1,2,3,4,5]' | dasel -i json 'len($this)'
# Output: 5

# String length
echo '"hello world"' | dasel -i json 'len($this)'
# Output: 11

# Nested array length
dasel -f data.json 'len(users)'

# Use in expressions
echo '[1,2,3]' | dasel -i json '[len($this)-1]'
# Output: 3
```

**Returns**: Integer.

## join(separator)

Join array elements into a single string.

**Signature**: `join(separator_string)`

```bash
# Basic join
echo '["a","b","c"]' | dasel -i json 'join(",")'
# Output: "a,b,c"

# Join with space
echo '["hello","world"]' | dasel -i json 'join(" ")'
# Output: "hello world"

# Join after map
dasel -f data.json 'users.map(name).join(", ")'
```

**Returns**: String.

## sum(expression)

Sum all numeric values in an array.

**Signature**: `sum(expression)`

```bash
# Sum array
echo '[1,2,3,4,5]' | dasel -i json 'sum($this)'
# Output: 15

# Sum a field from array of objects
echo '[{"val":10},{"val":20},{"val":30}]' | dasel -i json 'map(val).sum($this)'
# Output: 60

# Sum after filter
dasel -f data.json 'orders.filter(status == "paid").map(total).sum($this)'
```

**Returns**: Number (int or float depending on input).

## keys(expression)

Get all keys of a map/object as an array.

**Signature**: `keys(expression)`

```bash
# Get object keys
echo '{"a": 1, "b": 2, "c": 3}' | dasel -i json 'keys($this)'
# Output: ["a", "b", "c"]

# Keys of nested object
dasel -f config.yaml 'keys(database)'

# Use keys in further queries
dasel -f data.json 'len(keys($this))'
```

**Returns**: Array of strings.

## reverse(expression)

Reverse the order of elements in an array.

**Signature**: `reverse(expression)`

```bash
# Reverse array
echo '[1,2,3,4,5]' | dasel -i json 'reverse($this)'
# Output: [5, 4, 3, 2, 1]

# Reverse string array
echo '["a","b","c"]' | dasel -i json 'reverse($this)'
# Output: ["c", "b", "a"]

# Reverse after sort/filter
dasel -f data.json 'reverse(users.filter(active == true))'
```

**Returns**: Array in reversed order.

## typeOf(expression)

Get the type of a value as a string.

**Signature**: `typeOf(expression)`

Possible return values: `"string"`, `"int"`, `"float"`, `"bool"`, `"array"`, `"null"`

```bash
# String type
echo '"hello"' | dasel -i json 'typeOf($this)'
# Output: "string"

# Integer type
echo '42' | dasel -i json 'typeOf($this)'
# Output: "int"

# Boolean type
echo 'true' | dasel -i json 'typeOf($this)'
# Output: "bool"

# Use in search/filter
dasel -f data.json 'search(typeOf($this) == "array")'
```

**Returns**: String describing the type.

## toString(expression)

Convert a value to its string representation.

**Signature**: `toString(expression)`

```bash
# Integer to string
echo '123' | dasel -i json 'toString($this)'
# Output: "123"

# Boolean to string
echo 'true' | dasel -i json 'toString($this)'
# Output: "true"

# Use in join
echo '[1,2,3]' | dasel -i json 'map(toString($this)).join("-")'
# Output: "1-2-3"
```

**Returns**: String.

## toInt(expression)

Convert a value to an integer.

**Signature**: `toInt(expression)`

```bash
# String to integer
echo '"42"' | dasel -i json 'toInt($this)'
# Output: 42

# Float to integer (truncates)
echo '3.14' | dasel -i json 'toInt($this)'
# Output: 3

# Use in arithmetic
echo '{"port": "8080"}' | dasel -i json 'toInt(port) + 1'
```

**Returns**: Integer.

## toFloat(expression)

Convert a value to a floating-point number.

**Signature**: `toFloat(expression)`

```bash
# String to float
echo '"3.14"' | dasel -i json 'toFloat($this)'
# Output: 3.14

# Integer to float
echo '42' | dasel -i json 'toFloat($this)'
# Output: 42.0

# Arithmetic with float conversion
echo '{"price": "19.99", "tax": "0.08"}' \
  | dasel -i json 'toFloat(price) * (1 + toFloat(tax))'
```

**Returns**: Float.

## add(args...)

Add two or more numbers together. Returns int if all arguments are int, float otherwise.

**Signature**: `add(num1, num2, ...)` -- minimum 1 argument

Source: `execution/func_add.go:11-44`

```bash
# Add integers
echo 'null' | dasel -i json 'add(1, 2, 3)'
# Output: 6

# Mixed int and float returns float
echo 'null' | dasel -i json 'add(1, 2.5, 3)'
# Output: 6.5
```

**Returns**: Integer or float.

## merge(args...)

Merge two or more maps together. Later arguments override earlier keys.

**Signature**: `merge(map1, map2, ...)` -- minimum 1 argument, all must be maps

Source: `execution/func_merge.go:11-54`

```bash
# Merge two objects
echo '{"a": 1}' | dasel -i json 'merge($this, {"b": 2})'

# Override values
echo '{"defaults": {"a": 1, "b": 2}, "overrides": {"b": 3}}' \
  | dasel -i json 'merge(defaults, overrides)'
# Output: {"a": 1, "b": 3}
```

**Returns**: Merged map.

## max(args...)

Return the maximum value from the arguments.

**Signature**: `max(val1, val2, ...)` -- minimum 1 argument

Source: `execution/func_max.go:9-33`

```bash
# Max of numbers
echo 'null' | dasel -i json 'max(3, 1, 4, 1, 5)'
# Output: 5

# Max with spread from array
echo '[3, 1, 4, 1, 5]' | dasel -i json 'max($this...)'
```

**Returns**: The largest value.

## min(args...)

Return the minimum value from the arguments.

**Signature**: `min(val1, val2, ...)` -- minimum 1 argument

Source: `execution/func_min.go:9-33`

```bash
# Min of numbers
echo 'null' | dasel -i json 'min(3, 1, 4, 1, 5)'
# Output: 1

# Min with spread from array
echo '[3, 1, 4, 1, 5]' | dasel -i json 'min($this...)'
```

**Returns**: The smallest value.

## base64e(str)

Base64 encode a string value.

**Signature**: `base64e(string_value)` -- exactly 1 argument

Source: `execution/func_base64.go:11-23`

```bash
echo '"hello world"' | dasel -i json 'base64e($this)'
# Output: "aGVsbG8gd29ybGQ="
```

**Returns**: Base64-encoded string.

## base64d(str)

Base64 decode a string value.

**Signature**: `base64d(string_value)` -- exactly 1 argument

Source: `execution/func_base64.go:26-41`

```bash
echo '"aGVsbG8gd29ybGQ="' | dasel -i json 'base64d($this)'
# Output: "hello world"
```

**Returns**: Decoded string.

## parse(format, content)

Parse data at runtime. Takes a format string and content string, returns parsed value.

**Signature**: `parse(format_string, content_string)` -- exactly 2 arguments

Source: `execution/func_parse.go:10-43`

```bash
# Parse JSON string embedded in a value
echo '{"raw": "{\"nested\": true}"}' | dasel -i json 'parse("json", raw)'
# Output: {"nested": true}

# Parse YAML content
echo '{"config": "key: value"}' | dasel -i json 'parse("yaml", config)'
```

**Returns**: Parsed value (type depends on content).

## readFile(path)

Read file contents from a filepath at runtime. Returns the file content as a string.

**Signature**: `readFile(filepath_string)` -- exactly 1 argument

Source: `execution/func_readfile.go:12-36`

```bash
# Read a file and use its contents
echo 'null' | dasel -i json 'readFile("config.json")'

# Combine with parse to load and parse a file
echo 'null' | dasel -i json 'parse("json", readFile("data.json"))'
```

**Returns**: String (file contents).

## get(key)

Get value at a map key or slice index. Returns `false` if the data type does not match the key type.

**Signature**: `get(key_or_index)` -- minimum 1 argument

Source: `execution/func_get.go:10-42`

```bash
# Get by string key (on a map)
echo '{"name": "Alice"}' | dasel -i json 'get("name")'
# Output: "Alice"

# Get by integer index (on a slice)
echo '[10, 20, 30]' | dasel -i json 'get(1)'
# Output: 20
```

**Returns**: Value at the key/index.

## contains(value)

Check if a slice contains a specific value.

**Signature**: `contains(target_value)` -- exactly 1 argument

Source: `execution/func_contains.go:10-44`

```bash
# Check if array contains value
echo '[1, 2, 3, 4, 5]' | dasel -i json 'contains(3)'
# Output: true

echo '["a", "b", "c"]' | dasel -i json 'contains("d")'
# Output: false
```

**Returns**: `true` or `false`.

## ignore()

Mark a value to be excluded from a branch result. Takes no arguments.

**Signature**: `ignore()` -- exactly 0 arguments

Source: `execution/func_ignore.go:9-16`

```bash
# Used to conditionally exclude values from branch results
echo '[1, 2, 3]' | dasel -i json 'map(if($this > 1) { $this } else { ignore() })'
```

**Returns**: The data value, marked for exclusion from branch.

## sortBy(expr[, direction])

Sort array elements by an expression. This is a complex expression (like `filter`/`map`), not a regular function. Default direction is ascending.

**Signature**: `sortBy(expression)` or `sortBy(expression, asc)` or `sortBy(expression, desc)`

Source: `execution/execute_sort_by.go:12-64`, `selector/parser/parse_sort_by.go:8-60`

```bash
# Sort ascending (default)
echo '[3, 1, 4, 1, 5]' | dasel -i json 'sortBy($this)'
# Output: [1, 1, 3, 4, 5]

# Sort descending
echo '[3, 1, 4, 1, 5]' | dasel -i json 'sortBy($this, desc)'
# Output: [5, 4, 3, 1, 1]

# Sort objects by field
echo '[{"name":"C"},{"name":"A"},{"name":"B"}]' | dasel -i json 'sortBy(name)'
# Output: [{"name":"A"},{"name":"B"},{"name":"C"}]
```

**Returns**: Sorted array.

## Sources

- Functions index: <https://daseldocs.tomwright.me/functions> (fetched 2026-02-19)
- filter(): <https://daseldocs.tomwright.me/functions/filter.md> (fetched 2026-02-19)
- map(): <https://daseldocs.tomwright.me/functions/map.md> (fetched 2026-02-19)
- each(): <https://daseldocs.tomwright.me/functions/each.md> (fetched 2026-02-19)
- search(): <https://daseldocs.tomwright.me/functions/search.md> (fetched 2026-02-19)
- has(): <https://daseldocs.tomwright.me/functions/has.md> (fetched 2026-02-19)
- typeOf(): <https://daseldocs.tomwright.me/functions/typeof.md> (fetched 2026-02-19)
- toString(): <https://daseldocs.tomwright.me/functions/tostring.md> (fetched 2026-02-19)
- toInt(): <https://daseldocs.tomwright.me/functions/toint.md> (fetched 2026-02-19)
- join(): <https://daseldocs.tomwright.me/functions/join.md> (fetched 2026-02-19)
- Source code analysis: `execution/func.go`, `execution/func_add.go`, `execution/func_merge.go`, `execution/func_max.go`, `execution/func_min.go`, `execution/func_base64.go`, `execution/func_parse.go`, `execution/func_readfile.go`, `execution/func_get.go`, `execution/func_contains.go`, `execution/func_ignore.go`, `execution/execute_sort_by.go` (analyzed 2026-02-19)
