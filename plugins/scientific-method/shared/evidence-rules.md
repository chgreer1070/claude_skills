# Evidence Rules

All observations, results, and facts must reference Evidence IDs.

## Evidence ID Format

```text
E1: [source description]
E2: [source description]
E3: [source description]
```

Evidence IDs are sequential. Never reuse or skip numbers within an investigation.

## Valid Evidence Sources

- Command output snippet
- Log excerpt
- Stack trace
- Test report (with pass/fail counts)
- Metric snapshot (with timestamp)
- Code diff (with file path and key lines)
- Screenshot description with source

## Truncation Disclosure

When output cannot be shown in full:

```text
TRUNCATED
total lines: <N>
shown: <M>
method: head | tail | grep
fingerprint: <sha256 or key tokens>
command: <exact command used to generate output>
```

Truncation disclosure is mandatory. Silent abbreviation is prohibited.

## Forbidden in FACTS / RESULTS / STATUS

Do not write these unless verified with evidence:

- "fixed"
- "resolved" (use `resolved-verified` with evidence instead)
- "root cause is" (use "evidence suggests:" or "hypothesis:")
- "definitely"
- "must be"
- "probably"
- "likely"

Allowed replacements:

```text
hypothesis:
evidence suggests:
observed:
unknown:
```
