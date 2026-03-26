# DuckDB Query Patterns for Transcript Analysis

SQL patterns for querying Claude Code JSONL transcripts via the MotherDuck MCP server (`execute_query` tool). All queries use DuckDB dialect.

**Storage model:** Session data lives in **JSONL files on disk**. DuckDB here is only the **query engine** (`read_ndjson_auto`, aggregates, etc.). The MCP server uses `:memory:`; SQL must use **absolute** paths to JSONL (see `docs/cross-platform-notes.md` for tilde/`args` pitfalls).

**Path substitution:** Replace `/path/to/*.jsonl` in all queries below with the **absolute** transcript glob path from the Data Location section of the parent skill. Do not rely on `~` inside SQL strings — the MotherDuck server does not expand it.

## Arbitrary queries (not limited to this cookbook)

1. Load the field reference: **`kaizen-analysis` MCP** — tool `get_transcript_jsonl_schema`, or **`resources/read`** URI `kaizen://session-log/schema` (same markdown), or **Read** [jsonl-schema.md](./jsonl-schema.md) / [session-log-schema.md](./session-log-schema.md) from the plugin.
2. Compose **any** DuckDB SQL against `read_ndjson_auto('ABSOLUTE/GLOB/*.jsonl', columns={line: 'JSON'})` using `json_extract`, `json_extract_string`, `->`, `->>`, and `LATERAL unnest(...)` for arrays — match paths and shapes from the schema doc.
3. Run SQL via **`kaizen-duckdb` MCP** `execute_query`.

The sections below are **examples** (tool misuse, frustration, etc.), not an exhaustive list of what you may select or filter.

## Loading JSONL Data

DuckDB reads JSONL natively via `read_ndjson_auto()`:

```sql
-- Single session
SELECT * FROM read_ndjson_auto('/path/to/session.jsonl');

-- All sessions in a project
SELECT * FROM read_ndjson_auto('/path/to/project/*.jsonl');

-- With explicit column typing
SELECT
  json_extract_string(line, '$.type') as record_type,
  json_extract_string(line, '$.timestamp') as ts,
  json_extract_string(line, '$.sessionId') as session_id
FROM read_ndjson_auto('/path/to/*.jsonl', columns={line: 'JSON'});
```

## Corpus Overview Queries

### Session inventory

```sql
SELECT
  json_extract_string(line, '$.sessionId') as session_id,
  MIN(json_extract_string(line, '$.timestamp')) as first_event,
  MAX(json_extract_string(line, '$.timestamp')) as last_event,
  COUNT(*) as record_count
FROM read_ndjson_auto('/path/to/*.jsonl', columns={line: 'JSON'})
GROUP BY session_id
ORDER BY first_event DESC;
```

### Record type distribution

```sql
SELECT
  json_extract_string(line, '$.type') as event_type,
  COUNT(*) as frequency
FROM read_ndjson_auto('/path/to/*.jsonl', columns={line: 'JSON'})
GROUP BY event_type
ORDER BY frequency DESC;
```

## Tool Misuse Detection

### Bash commands that should use built-in tools

```sql
WITH bash_calls AS (
  SELECT
    json_extract_string(line, '$.sessionId') as session_id,
    json_extract_string(line, '$.timestamp') as ts,
    elem->>'input'->>'command' as command,
    elem->>'input'->>'description' as description
  FROM read_ndjson_auto('/path/to/*.jsonl', columns={line: 'JSON'}),
    LATERAL unnest(
      from_json(json_extract(line, '$.message.content'), '["json"]')
    ) as t(elem)
  WHERE json_extract_string(line, '$.type') = 'assistant'
    AND elem->>'name' = 'Bash'
    AND elem->>'type' = 'tool_use'
)
SELECT
  session_id,
  command,
  CASE
    WHEN regexp_matches(command, '^\s*ls\b') THEN 'should_use_glob'
    WHEN regexp_matches(command, '\bgrep\b') AND NOT regexp_matches(command, '\|.*grep') THEN 'should_use_grep'
    WHEN regexp_matches(command, '\bfind\b\s+\S+\s+-name\b') THEN 'should_use_glob'
    WHEN regexp_matches(command, '\bcat\b\s+\S+\.\w+') THEN 'should_use_read'
    WHEN regexp_matches(command, '\bhead\b\s+-\d+') THEN 'should_use_read'
    WHEN regexp_matches(command, '\btail\b\s+-\d+') THEN 'should_use_read'
    WHEN regexp_matches(command, '\bsed\b') THEN 'should_use_edit'
    WHEN regexp_matches(command, '\bawk\b') THEN 'should_use_edit'
  END as violation_type
FROM bash_calls
WHERE violation_type IS NOT NULL
ORDER BY session_id, ts;
```

### Tool misuse rate per session

```sql
WITH tool_calls AS (
  SELECT
    json_extract_string(line, '$.sessionId') as session_id,
    elem->>'name' as tool_name,
    elem->>'input'->>'command' as command
  FROM read_ndjson_auto('/path/to/*.jsonl', columns={line: 'JSON'}),
    LATERAL unnest(
      from_json(json_extract(line, '$.message.content'), '["json"]')
    ) as t(elem)
  WHERE json_extract_string(line, '$.type') = 'assistant'
    AND elem->>'type' = 'tool_use'
)
SELECT
  session_id,
  COUNT(*) FILTER (WHERE tool_name = 'Bash'
    AND (regexp_matches(command, '^\s*ls\b')
      OR regexp_matches(command, '\bgrep\b')
      OR regexp_matches(command, '\bcat\b\s+\S+\.\w+')
      OR regexp_matches(command, '\bfind\b.*-name')))
    as misuse_count,
  COUNT(*) FILTER (WHERE tool_name = 'Bash') as total_bash,
  COUNT(*) as total_tools,
  ROUND(100.0 * misuse_count / NULLIF(total_bash, 0), 1) as misuse_pct
FROM tool_calls
GROUP BY session_id
HAVING misuse_count > 0
ORDER BY misuse_count DESC;
```

## Error Pattern Detection

### Tool errors by type

```sql
SELECT
  json_extract_string(line, '$.sessionId') as session_id,
  CASE
    WHEN content LIKE '%File has not been read yet%' THEN 'edit_before_read'
    WHEN content LIKE '%String to replace not found%' THEN 'stale_edit'
    WHEN content LIKE '%User denied tool use%' THEN 'user_denied'
    WHEN content LIKE '%Exit code%' THEN 'command_failure'
    WHEN content LIKE '%not found%' THEN 'missing_binary'
    WHEN content LIKE '%does not exist%' THEN 'file_not_found'
    ELSE 'other'
  END as error_type,
  COUNT(*) as occurrences
FROM read_ndjson_auto('/path/to/*.jsonl', columns={line: 'JSON'}),
  LATERAL (
    SELECT json_extract_string(line, '$.message.content') as content
  )
WHERE json_extract_string(line, '$.type') = 'user'
  AND json_extract(line, '$.message.content[0].is_error')::boolean = true
GROUP BY session_id, error_type
ORDER BY occurrences DESC;
```

## User Frustration Detection

### Interrupts and corrections

```sql
SELECT
  json_extract_string(line, '$.sessionId') as session_id,
  json_extract_string(line, '$.timestamp') as ts,
  json_extract_string(line, '$.message.content') as content,
  CASE
    WHEN content LIKE '%Request interrupted by user%' THEN 'interrupt'
    WHEN content LIKE '%Request interrupted by user for tool use%' THEN 'tool_denial'
    WHEN regexp_matches(content, '^(No,|Don''t|Stop |Why did you|Why would)') THEN 'correction'
    WHEN regexp_matches(content, '(wrong|incorrect|that''s not|you should not)') THEN 'correction'
  END as signal_type
FROM read_ndjson_auto('/path/to/*.jsonl', columns={line: 'JSON'})
WHERE json_extract_string(line, '$.type') = 'user'
  AND json_extract(line, '$.toolUseResult') IS NULL
  AND signal_type IS NOT NULL
ORDER BY session_id, ts;
```

## Subagent Delegation Analysis

### Agent types used

```sql
SELECT
  elem->>'input'->>'subagent_type' as agent_type,
  elem->>'input'->>'description' as task_description,
  elem->>'input'->>'model' as model,
  COUNT(*) as usage_count
FROM read_ndjson_auto('/path/to/*.jsonl', columns={line: 'JSON'}),
  LATERAL unnest(
    from_json(json_extract(line, '$.message.content'), '["json"]')
  ) as t(elem)
WHERE json_extract_string(line, '$.type') = 'assistant'
  AND elem->>'name' = 'Task'
  AND elem->>'type' = 'tool_use'
GROUP BY agent_type, task_description, model
ORDER BY usage_count DESC;
```

## Context Waste Detection

### Orchestrator reads file then delegates task mentioning same file

```sql
WITH ordered_tools AS (
  SELECT
    json_extract_string(line, '$.sessionId') as session_id,
    json_extract_string(line, '$.timestamp') as ts,
    elem->>'name' as tool_name,
    elem->>'input'->>'file_path' as read_path,
    elem->>'input'->>'prompt' as task_prompt,
    ROW_NUMBER() OVER (PARTITION BY json_extract_string(line, '$.sessionId') ORDER BY json_extract_string(line, '$.timestamp')) as turn_num
  FROM read_ndjson_auto('/path/to/*.jsonl', columns={line: 'JSON'}),
    LATERAL unnest(
      from_json(json_extract(line, '$.message.content'), '["json"]')
    ) as t(elem)
  WHERE json_extract_string(line, '$.type') = 'assistant'
    AND elem->>'type' = 'tool_use'
    AND elem->>'name' IN ('Read', 'Task')
)
SELECT
  r.session_id,
  r.read_path,
  t.task_prompt
FROM ordered_tools r
JOIN ordered_tools t
  ON r.session_id = t.session_id
  AND t.tool_name = 'Task'
  AND t.turn_num > r.turn_num
  AND t.turn_num <= r.turn_num + 5
  AND r.tool_name = 'Read'
  AND t.task_prompt LIKE '%' || r.read_path || '%';
```

## Session Timing Analysis

### Turn durations

```sql
SELECT
  json_extract_string(line, '$.sessionId') as session_id,
  AVG(json_extract(line, '$.durationMs')::int) as avg_turn_ms,
  MAX(json_extract(line, '$.durationMs')::int) as max_turn_ms,
  COUNT(*) as turn_count
FROM read_ndjson_auto('/path/to/*.jsonl', columns={line: 'JSON'})
WHERE json_extract_string(line, '$.type') = 'system'
  AND json_extract_string(line, '$.subtype') = 'turn_duration'
GROUP BY session_id
ORDER BY avg_turn_ms DESC;
```

## Notes

- DuckDB JSONL parsing is schema-flexible — fields not present in a record return NULL
- Use `columns={line: 'JSON'}` for raw JSON access when auto-detection fails
- `LATERAL unnest` with `from_json` unpacks JSON arrays for tool call extraction
- Adjust glob paths to match your project transcript location

SOURCE: DuckDB documentation (duckdb.org/docs), MotherDuck MCP server README (github.com/motherduckdb/mcp-server-motherduck), empirical testing against claude-skills transcripts (2026-02-18)
