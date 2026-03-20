---
name: Migrate SAM plan storage from YAML files to SQLite3
description: 'Agents currently edit YAML plan files directly (task status, TN verification, timestamps) instead of going through a programmatic mutation layer. This is fragile — agents can misformat YAML, corrupt structure, or write invalid values. Replace YAML file storage with SQLite3 database. The sam CLI already has the right interface shape (state, ready, status, claim) — the backend changes from file I/O to SQL. SQLite gives proper CRUD, transactions, atomic updates, and structured queries. Covers: task files, T0/TN verification reports, plan artifacts.'
metadata:
  topic: migrate-sam-plan-storage-from-yaml-files-to-sqlite3
  source: 'Session observation 2026-03-20: agents editing YAML files directly instead of using programmatic mutations'
  added: '2026-03-20'
  priority: P1
  type: Feature
  status: open
  issue: '#912'
  last_synced: '2026-03-20T16:06:20Z'
---