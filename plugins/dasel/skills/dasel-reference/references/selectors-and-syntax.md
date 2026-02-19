# Selectors and Syntax Reference

Complete dasel v3 selector and expression syntax.

## Dot Notation

Access nested keys with dots:

```bash
# Simple path
echo '{"foo": {"bar": {"baz": 42}}}' | dasel -i json 'foo.bar.baz'
# Output: 42

# Top-level key
cat config.yaml | dasel -i yaml 'database'

# Deeply nested
cat config.yaml | dasel -i yaml 'database.primary.connection.host'
```

## Array Access

### Index (zero-based)

```bash
echo '[10, 20, 30]' | dasel -i json '[0]'
# Output: 10

echo '[10, 20, 30]' | dasel -i json '[2]'
# Output: 30

# Nested array access
cat data.json | dasel -i json 'users[0].name'
```

### Slice `[start:end]`

Returns elements from `start` through `end` (inclusive of end index position):

```bash
echo '[1,2,3,4,5]' | dasel -i json '[0:2]'
# Output: [1, 2, 3]

echo '[1,2,3,4,5]' | dasel -i json '[2:4]'
# Output: [3, 4, 5]
```

### Last Element (via `len`)

No negative index syntax; use `len` to compute:

```bash
echo '[10, 20, 30]' | dasel -i json '[len($this)-1]'
# Output: 30
```

### Append to Array

Use spread to include existing elements plus new ones:

```bash
echo '[1,2,3]' | dasel -i json --root '[$this..., 4]'
# Output: [1, 2, 3, 4]

echo '[1,2,3]' | dasel -i json --root '[0, $this...]'
# Output: [0, 1, 2, 3]
```

## Recursive Descent (`..`)

Searches all levels of nesting for matching keys:

```bash
# Find all values with key "name" at any depth
echo '{"user": {"name": "Alice", "profile": {"name": "alice123"}}}' | dasel -i json '..name'
# Output: ["Alice", "alice123"]

# First element of every nested array
cat data.json | dasel -i json '..[0]'

# All values at any depth
cat data.json | dasel -i json '..*'
```

## Object Construction

Build new objects from selected keys:

```bash
# Select specific fields
echo '{"name": "Alice", "age": 30, "email": "a@b.com"}' | dasel -i json '{ name, age }'
# Output: {"name": "Alice", "age": 30}

# Nested field selection
cat data.json | dasel -i json '{ users[0].name, config.version }'
```

### With Spread Operator

Merge objects using `...`:

```bash
# Merge two objects
echo '{}' | dasel -i json --root '{ {"firstName": "Tom"}..., "lastName": "Wright" }'
# Output: {"firstName": "Tom", "lastName": "Wright"}

# Combine defaults with overrides
cat config.json | dasel -i json --root '{ defaults..., overrides... }'
```

### Spread to Separate Documents

Output array elements as individual values:

```bash
echo '[1, 2, 3]' | dasel -i json '$this...'
# Output:
# 1
# 2
# 3
```

### Spread as Function Arguments

```bash
# Equivalent to doSomething(1, 2, 3)
doSomething([1, 2, 3]...)
```

## Conditionals

### if/else Expressions

```bash
# String literal output
echo '{"count": 7}' | dasel -i json 'if(count > 5) { "many" } else { "few" }'
# Output: "many"

# Selector-based branches
dasel -i json -f input.json '.foo.if(bar == "baz") { bong } else { qux }'

# Nested conditional
echo '{"score": 85}' | dasel -i json 'if(score >= 90) { "A" } else { if(score >= 80) { "B" } else { "C" } }'
# Output: "B"
```

## Variables

### Assignment with `$`

```bash
# Assign and reuse
cat data.json | dasel -i json '$activeUsers = users.filter(active == true); $activeUsers.map(name)'

# Multiple variables
cat data.json | dasel -i json '$a = items[0]; $b = items[1]; { first: $a, second: $b }'
```

### Special Variables

- `$root` -- always references the top-level document, regardless of current traversal depth
- `$this` -- references the current node, used inside `each`, `map`, `filter`, `search`, and array expressions

```bash
# $root: access root from inside a nested context
echo '{"base": "/api", "routes": [{"path": "users"}]}' | dasel -i json \
  'routes.map($root.base)'

# $this: reference current element in map
echo '[1,2,3]' | dasel -i json 'map($this * 10)'
```

## Multi-Statement Queries

Separate statements with semicolons. The final statement is the output:

```bash
cat data.json | dasel -i json '$active = users.filter(active == true); $names = $active.map(name); $names'

# Variable reuse across statements
cat config.yaml | dasel -i yaml '$port = server.port; $host = server.host; join(":", [$host, toString($port)])'
```

## Operators

### Comparison Operators

| Operator | Meaning |
|----------|---------|
| `==` | Equal |
| `!=` | Not equal |
| `<` | Less than |
| `>` | Greater than |
| `<=` | Less than or equal |
| `>=` | Greater than or equal |

### Logical Operators

| Operator | Meaning |
|----------|---------|
| `&&` | Logical AND |
| `\|\|` | Logical OR |
| `!` | Logical NOT (unary). Source: `execute_unary.go:21-26` |

### Arithmetic Operators

Source: `execution/execute_binary.go:74-89`

| Operator | Meaning |
|----------|---------|
| `+` | Addition |
| `-` | Subtraction |
| `*` | Multiplication |
| `/` | Division |
| `%` | Modulo |

### Pattern Matching Operators

Source: `execution/execute_binary.go:139-162`

| Operator | Meaning |
|----------|---------|
| `~` | Regex match (right side must be regex pattern) |
| `!~` | Regex NOT match |

### Null Coalescing Operator

Source: `execution/execute_binary.go:163-196`

| Operator | Meaning |
|----------|---------|
| `??` | Returns left if not null/error, else right. Also handles `MapKeyNotFound`, `SliceIndexOutOfRange`, and type errors. |

```bash
# Combined predicates
cat data.json | dasel -i json 'users.filter(age >= 18 && active == true)'

# OR condition
cat data.json | dasel -i json 'items.filter(status == "pending" || status == "review")'

# Numeric comparison
echo '[1,2,3,4,5]' | dasel -i json 'filter($this > 3)'
# Output: [4, 5]

# Regex match
echo '[{"name":"Alice"},{"name":"Bob"},{"name":"Anna"}]' \
  | dasel -i json 'filter(name ~ /^A/)'

# Regex NOT match
echo '[{"name":"Alice"},{"name":"Bob"}]' \
  | dasel -i json 'filter(name !~ /^A/)'

# Null coalescing
echo '{"a": 1}' | dasel -i json 'b ?? "default"'
# Output: "default"

# Logical NOT
echo 'true' | dasel -i json '!$this'
# Output: false

# Modulo
echo '10' | dasel -i json '$this % 3'
# Output: 1
```

## Assignment Expressions

Modifications use `=` inside a query, combined with `--root` to output the full document:

```bash
# Set a string value
echo '{"name": "old"}' | dasel -i json --root 'name = "new"'
# Output: {"name": "new"}

# Set numeric value
echo '{"count": 0}' | dasel -i json --root 'count = 42'

# Set boolean
echo '{"enabled": false}' | dasel -i json --root 'enabled = true'

# Set nested value
echo '{"a": {"b": 1}}' | dasel -i json --root 'a.b = 99'
# Output: {"a": {"b": 99}}
```

Without `--root`, dasel outputs only the result of the assignment expression, not the full document.

## External Variables (`--var`)

Pass values from the shell into queries:

```bash
cat config.json | dasel -i json --var 'name=production' 'environments.filter($this.name == $name)'

# Multiple variables
cat data.json | dasel -i json --var 'min=10' --var 'max=50' 'values.filter($this >= toInt($min) && $this <= toInt($max))'
```

## Sources

- Query syntax: <https://daseldocs.tomwright.me/syntax/query-syntax.md> (fetched 2026-02-19)
- Arrays/slices: <https://daseldocs.tomwright.me/syntax/arrays-slices.md> (fetched 2026-02-19)
- Objects/maps: <https://daseldocs.tomwright.me/syntax/objects-maps.md> (fetched 2026-02-19)
- Conditionals: <https://daseldocs.tomwright.me/syntax/conditionals.md> (fetched 2026-02-19)
- Recursive descent: <https://daseldocs.tomwright.me/syntax/recursive-descent.md> (fetched 2026-02-19)
- Spread: <https://daseldocs.tomwright.me/syntax/spread.md> (fetched 2026-02-19)
- Types/Literals: <https://daseldocs.tomwright.me/syntax/types-literals.md> (fetched 2026-02-19)
- Source code analysis: `execution/execute_binary.go` (operators), `execution/execute_unary.go` (unary NOT), `selector/lexer/token.go` (token definitions) (analyzed 2026-02-19)
