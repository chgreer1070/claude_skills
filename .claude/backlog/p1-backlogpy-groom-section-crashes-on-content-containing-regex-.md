---
name: backlog.py groom --section crashes on content containing regex escapes
description: "When groomed content passed to backlog.py groom --section contains backslash sequences like \\s, \\d, the _sync_groomed_to_github_issue function at line 1543 passes the content as a re.sub replacement string. Python re.sub interprets backslash sequences in the replacement, causing 'bad escape \\s' errors. The fix: use a lambda or re.escape on the replacement string in _append_or_replace_section at line 1543. Also affects line 1611 (groomed_re.sub with the content block). Reproducible: pass any content with regex-like patterns (e.g., Python code with \\s, \\d) to backlog.py groom --section."
metadata:
  topic: backlogpy-groom-section-crashes-on-content-containing-regex-
  source: 'session observation during #338 implementation'
  added: '2026-03-01'
  priority: P1
  type: Bug
  status: open
  issue: '#340'
  last_synced: '2026-03-01T14:22:15Z'
---