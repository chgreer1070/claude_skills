---
description: Audit documentation against code for drift, sync docs after code changes, or track doc freshness. Delegates to the right specialist automatically.
argument-hint: <task description — what to audit or sync>
agent: rewrite-room-auditor
allowed-tools: Read, Grep, Glob, Bash, Task, Write, Edit
---

Route this documentation audit or sync task to the rewrite-room-auditor agent.

Task: $ARGUMENTS

The agent will determine whether this is a drift audit, documentation sync, or freshness task and delegate to the appropriate specialist.
