# Performance Investigation Extensions

Add these sections after section 2 (OBSERVATIONS) when the investigation involves latency,
throughput, memory, or resource regressions.

## 2a BASELINE METRICS

```text
Metric: <name>
Baseline value: <N> <unit> (measured at: <commit|timestamp>)
Current value: <N> <unit> (measured at: <commit|timestamp>)
Delta: <+/-N> (<+/-N%>)
Evidence: [E#]
```

## 2b REGRESSION WINDOW

```text
Last known-good: <commit sha or timestamp>
First known-bad: <commit sha or timestamp>
Commits in window: <N>
Narrowed by bisect: (yes | no)
Evidence: [E#]
```

## 2c HOT PATH ANALYSIS

```text
Profile tool: <name and version>
Top N functions by time/allocations:

1. function_name — <N>ms | <N>% total (file.py:line)
2. function_name — <N>ms | <N>% total (file.py:line)

Evidence: [E#]
```

## 2d RESOURCE UTILIZATION

```text
CPU: <N>% (peak: <N>%)
Memory: <N>MB RSS (peak: <N>MB)
I/O: <N> reads/s, <N> writes/s
Network: <N>MB/s in, <N>MB/s out
Measurement window: <duration>
Evidence: [E#]
```
