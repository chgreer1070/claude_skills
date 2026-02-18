# Extraction Patterns

All JSONL queries use the `kaizen-duckdb` MCP tool (`execute_query`). DuckDB reads JSONL files directly via `read_ndjson_auto()`.

## Agent Output Transcripts (`/tmp/claude-*/tasks/*.output`)

JSONL files, one JSON record per line. Replace `FILE` with the actual path.

### Tool invocations by name

```sql
SELECT
  json_extract_string(c.value, '$.name') AS tool_name,
  COUNT(*) AS cnt
FROM read_ndjson_auto('FILE', ignore_errors := true) t,
  LATERAL (SELECT unnest(json_extract(t.message, '$.content')::JSON[]) AS value) c
WHERE t.type = 'assistant'
  AND json_extract_string(c.value, '$.type') = 'tool_use'
GROUP BY tool_name
ORDER BY cnt DESC
```

### MCP tool elapsed times

```sql
SELECT
  json_extract_string(t.data, '$.toolName') AS tool_name,
  json_extract(t.data, '$.elapsedTimeMs')::INT AS elapsed_ms
FROM read_ndjson_auto('FILE', ignore_errors := true) t
WHERE t.type = 'progress'
  AND json_extract_string(t.data, '$.status') = 'completed'
  AND json_extract(t.data, '$.elapsedTimeMs') IS NOT NULL
ORDER BY elapsed_ms DESC
```

### Total and average MCP time

```sql
SELECT
  COUNT(*) AS query_count,
  SUM(json_extract(t.data, '$.elapsedTimeMs')::INT) AS total_ms,
  AVG(json_extract(t.data, '$.elapsedTimeMs')::INT)::INT AS avg_ms
FROM read_ndjson_auto('FILE', ignore_errors := true) t
WHERE t.type = 'progress'
  AND json_extract_string(t.data, '$.status') = 'completed'
  AND json_extract(t.data, '$.elapsedTimeMs') IS NOT NULL
```

### Distinct LLM API turns

```sql
SELECT COUNT(DISTINCT requestId) AS llm_turns
FROM read_ndjson_auto('FILE', ignore_errors := true)
WHERE requestId IS NOT NULL
```

### Wall clock duration (first and last timestamps)

```sql
SELECT
  MIN(timestamp) AS first_event,
  MAX(timestamp) AS last_event
FROM read_ndjson_auto('FILE', ignore_errors := true)
```

### Failed tool calls

```sql
SELECT COUNT(*) AS failed_calls
FROM read_ndjson_auto('FILE', ignore_errors := true)
WHERE toolUseResult::VARCHAR LIKE '%"is_error":true%'
   OR (type = 'user' AND message::VARCHAR LIKE '%"is_error":true%')
```

### Total records

```sql
SELECT COUNT(*) AS total_records
FROM read_ndjson_auto('FILE', ignore_errors := true)
```

## Kaizen Analysis Reports (`.planning/kaizen/analysis-*.md`)

Structured markdown. Use Grep for these — they are small files.

### Count findings by severity

Use Grep tool with pattern `Severity.*critical`, `Severity.*warning`, `Severity.*info` and `output_mode: count`.

### List finding titles

Use Grep tool with pattern `^###` and `output_mode: content`.

### Extract session IDs mentioned

Use Grep tool with pattern `[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12}`.

## Raw Session JSONL (`~/.claude/projects/*/*.jsonl`)

Same schema as agent output transcripts. Use DuckDB — these are 100s of MB.

### Corpus summary

```sql
SELECT
  COUNT(*) AS total_records,
  COUNT(DISTINCT sessionId) AS total_sessions,
  MIN(timestamp) AS earliest,
  MAX(timestamp) AS latest
FROM read_ndjson_auto('~/.claude/projects/-PROJECT-KEY-/*.jsonl', ignore_errors := true)
```

### Record type distribution

```sql
SELECT type, COUNT(*) AS cnt
FROM read_ndjson_auto('~/.claude/projects/-PROJECT-KEY-/*.jsonl', ignore_errors := true)
GROUP BY type
ORDER BY cnt DESC
```
