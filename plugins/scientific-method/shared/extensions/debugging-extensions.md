# Debugging Scenario Extensions

Add these sections after section 2 (OBSERVATIONS) when the investigation involves a software bug,
crash, or unexpected code behaviour.

## 2a CALL STACK

```text
Full stack trace or abbreviated form with truncation disclosure:

Frame N: function_name (file.py:line)
Frame N-1: caller (file.py:line)
...
Evidence: [E#]
```

## 2b RECENT CODE CHANGES

```text
Changes in the relevant area since last known-good state:

Commit: <sha> — <message>
  Files: <path>
  Relevant diff lines:
    before:
    after:
Evidence: [E#]
```

## 2c DEPENDENCY GRAPH

```text
Direct dependencies of the failing component:

Component → Dependency (version)
Component → Dependency (version)

Changed dependencies (if any):
  <dep>: <old version> → <new version>
Evidence: [E#]
```
