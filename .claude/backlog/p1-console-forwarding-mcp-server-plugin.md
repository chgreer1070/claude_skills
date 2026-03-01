---
name: Console Forwarding MCP Server Plugin
description: "Create a new plugin with a FastMCP server that enables Claude Code sessions to communicate with other Claude sessions locally (via dtach/tmux) and on remote hosts (via SSH). The server should allow monitoring of long-running multi-agent sessions, reading terminal output, sending commands, and coordinating across sessions.\n\nReferences:\n- ./research/developer-tools/dtach.md — minimal detach/reattach for long-running sessions\n- ./research/developer-tools/tabz-browser-console-forwarder.md — browser console to terminal forwarding pattern\n- ./research/developer-tools/using-tmux-with-claude-code.md — tmux + Claude Code workflow patterns\n- ./research/developer-tools/psmux.md — Windows tmux replacement (Rust) with drop-in compatibility\n- ./research/developer-tools/shpool.md — shell session pool with detach/reattach and daemon mode\n- ./research/developer-tools/byobu.md — enhanced tmux/screen wrapper with 40+ status bar plugins and F-key layer\n- ./research/developer-tools/tmuxp.md — Python tmux session manager with YAML/JSON workspace configs and plugin hooks\n- /fastmcp-creator skill for MCP server implementation"
metadata:
  topic: console-forwarding-mcp-server-plugin
  source: User request
  added: '2026-03-01'
  priority: P1
  type: Feature
  status: open
  issue: '#364'
  last_synced: '2026-03-01T18:14:33Z'
---