# Stream-JSON Protocol Reference

## Output Event Types

When using `--output-format stream-json`, the spawned session emits newline-delimited JSON. Each line has a `type` field.

### System Events

Emitted during session lifecycle:

```text
type=system, subtype=init          Session initialized. Contains full inventory:
                                     .tools[]        — all available tools
                                     .mcp_servers[]  — MCP server names and status
                                     .skills[]       — all skills (slash commands)
                                     .agents[]       — all agent types
                                     .plugins[]      — installed plugins with paths
                                     .model          — model in use
                                     .session_id     — UUID for this session
                                     .permissionMode — permission mode setting

type=system, subtype=hook_started  A hook began executing (.hook_name, .hook_event)
type=system, subtype=hook_response Hook completed (.output, .exit_code, .outcome)
type=system, subtype=api_retry     API rate limit retry (.attempt, .retry_delay_ms)
```

### Assistant Events

The model's response:

```text
type=assistant    Complete assistant message. Structure:
                    .message.content[]     — array of content blocks
                    .message.content[].type — "text" or "tool_use"
                    .message.content[].text — text content (when type=text)
                    .message.model         — model used
                    .message.usage         — token counts
                    .session_id            — session UUID
```

### Result Events

Turn completion:

```text
type=result, subtype=success    Turn completed successfully:
                                  .result           — final text response
                                  .duration_ms      — wall clock time
                                  .num_turns        — agentic turns taken
                                  .total_cost_usd   — cost for this turn
                                  .session_id       — session UUID
                                  .usage            — detailed token breakdown
                                  .modelUsage       — per-model token counts
```

### Rate Limit Events

```text
type=rate_limit_event    Rate limit status:
                           .rate_limit_info.status       — "allowed" or "allowed_warning"
                           .rate_limit_info.utilization   — 0.0 to 1.0
                           .rate_limit_info.rateLimitType — "seven_day" etc.
```

### Streaming Events (with --include-partial-messages)

Token-by-token streaming when `--include-partial-messages` is set:

```text
type=stream_event, event.type=message_start        New message begins
type=stream_event, event.type=content_block_start   Text or tool_use block begins
type=stream_event, event.type=content_block_delta   Incremental text chunk:
                                                      .event.delta.type = "text_delta"
                                                      .event.delta.text = "chunk"
type=stream_event, event.type=content_block_stop    Block ends
type=stream_event, event.type=message_delta         Message-level update (stop_reason)
type=stream_event, event.type=message_stop          Message ends
```

Extract streaming text with jq:

```bash
jq -rj 'select(.type == "stream_event" and .event.delta.type? == "text_delta") | .event.delta.text'
```

## JSON Output Format (--output-format json)

Single JSON object per invocation (not NDJSON):

```json
{
  "result": "Claude's text response",
  "session_id": "uuid",
  "is_error": false,
  "duration_ms": 5432,
  "num_turns": 1,
  "total_cost_usd": 0.05,
  "usage": {
    "input_tokens": 100,
    "output_tokens": 50,
    "cache_read_input_tokens": 5000,
    "cache_creation_input_tokens": 1000
  },
  "modelUsage": {
    "claude-opus-4-6[1m]": {
      "inputTokens": 100,
      "outputTokens": 50,
      "costUSD": 0.05
    }
  }
}
```

## Experiment Log: Stream-JSON Multi-Turn (2026-03-22)

### Setup

```bash
mkfifo /tmp/claude-exp1-pipe
tmux new-session -d -s claude-exp1 \
  "claude -p --input-format stream-json --output-format stream-json \
   --permission-mode auto --verbose \
   < /tmp/claude-exp1-pipe > /tmp/claude-exp1-output.jsonl 2>/tmp/claude-exp1-err.log"
```

### Messages Sent

```bash
(
  echo '{"type":"user","message":{"role":"user","content":"Respond with exactly: PING_RECEIVED_1"}}';
  sleep 30;
  echo '{"type":"user","message":{"role":"user","content":"Respond with exactly: PING_RECEIVED_2"}}';
  sleep 30;
) > /tmp/claude-exp1-pipe &
```

### Results

- Message 1: Received `PING_RECEIVED_1` — confirmed by `type=assistant` event
- Message 2: Received `PING_RECEIVED_2` — confirmed by both `type=assistant` and `type=result` events
- Both messages processed within the same session (same `session_id` across all events)
- The `init` event confirmed full capability inheritance: 90+ tools, 25+ MCP servers, 200+ skills, 70+ agents, 16 plugins
- Total cost for 2-turn experiment: $0.51 (opus model with 75K cached tokens)

### Key Finding

`claude -p --input-format stream-json` does NOT exit after the first response. It keeps stdin open and processes subsequent NDJSON messages as new conversation turns. This enables true multi-turn bidirectional communication.

## Experiment Log: Sequential Resume (2026-03-22)

### Setup

```bash
SESSION_UUID=$(uuidgen)  # f2d60e2c-57c3-413a-b0bd-6f1f1b0668d3
```

### Call 1: Set Secret

```bash
claude -p "Remember this secret word: TANGERINE. Respond with only: ACKNOWLEDGED" \
  --session-id "$SESSION_UUID" --output-format json --permission-mode auto
```

Result: `ACKNOWLEDGED`

### Call 2: Recall Secret

```bash
claude -p "What was the secret word I told you to remember?" \
  --resume "$SESSION_UUID" --output-format json --permission-mode auto
```

Result: `TANGERINE`

### Key Finding

Session state (conversation history) persists across separate `claude -p` invocations when using `--session-id` to establish and `--resume` to continue. The resumed session has full access to prior conversation context.
