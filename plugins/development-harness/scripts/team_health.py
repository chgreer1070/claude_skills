#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Team agent health monitor — shows last actions + tmux window for each teammate.

Usage:
  uv run plugins/development-harness/scripts/team_health.py [team-name]

Defaults to most recently modified team.
"""

from __future__ import annotations

import json
import operator
import shutil
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

JSONL_DIR = Path.home() / ".claude/projects/-home-ubuntulinuxqa2-repos-claude-skills"
TEAMS_DIR = Path.home() / ".claude/teams"


def latest_team() -> str | None:
    """Find the most recently modified team directory.

    Returns:
        Team name (directory name) or None if no teams exist.
    """
    teams = sorted(TEAMS_DIR.glob("*/config.json"), key=lambda f: f.stat().st_mtime, reverse=True)
    return teams[0].parent.name if teams else None


def team_members(team_name: str) -> list[dict]:
    """Load team member configurations from team config file.

    Returns:
        List of member dictionaries or empty list if team not found.
    """
    cfg = TEAMS_DIR / team_name / "config.json"
    return json.loads(cfg.read_text()).get("members", []) if cfg.exists() else []


def agent_last_actions(name: str, lead_session: str | None, n: int = 5) -> tuple[list[str], str]:
    """Find the agent's JSONL session and return last N actions.

    For the team-lead:  use lead_session directly (exact file known).
    For sub-agents:     sub-agent sessions have the agent name in the first ~2 KB
                        (session init / prompt record), while the team-lead session
                        only references the name deep inside teammate messages.
                        So we sort candidates by how early the name appears.

    Returns:
        Tuple of (action strings list, session filename).
    """
    jsonl_files = sorted(JSONL_DIR.glob("*.jsonl"), key=lambda f: f.stat().st_mtime, reverse=True)[:30]

    # Team-lead: use the known lead session file directly
    if lead_session:
        jf = JSONL_DIR / f"{lead_session}.jsonl"
        try:
            text = jf.read_text()
        except OSError:
            return [], ""
        return _extract_actions(text, n), jf.name

    # Sub-agents: find the session where this name appears earliest in the file
    candidates: list[tuple[int, Path]] = []
    for jf in jsonl_files:
        try:
            head = jf.read_bytes()[:3000].decode("utf-8", errors="ignore")
        except OSError:
            continue
        pos = head.find(name)
        if pos != -1:
            candidates.append((pos, jf))

    if not candidates:
        return [], ""

    # Prefer the file where the name appears earliest (= agent's own session)
    candidates.sort(key=operator.itemgetter(0))
    _, best = candidates[0]
    try:
        text = best.read_text()
    except OSError:
        return [], ""
    return _extract_actions(text, n), best.name


def _extract_actions(text: str, n: int) -> list[str]:
    lines = text.splitlines()
    actions = []
    for ln in lines[-300:]:
        try:
            rec = json.loads(ln)
        except json.JSONDecodeError:
            continue
        if rec.get("type") != "assistant":
            continue
        ts = rec.get("timestamp", "")[:19].replace("T", " ")
        for item in rec.get("content", []):
            if item.get("type") == "tool_use":
                inp = str(item.get("input", {}))[:60].replace("\n", " ")
                actions.append(f"  {ts}  {item['name']}({inp})")
            elif item.get("type") == "text" and item.get("text", "").strip():
                snippet = item["text"].strip().replace("\n", " ")[:80]
                actions.append(f"  {ts}  [text] {snippet}")
    return actions[-n:]


def capture_pane(pane_id: str) -> str:
    """Capture last 500 chars from a specific tmux pane.

    Returns:
        Last 500 characters of pane output, or error message if unavailable.
    """
    if not pane_id:
        return ""
    tmux_path = shutil.which("tmux")
    if not tmux_path:
        return "(tmux not installed)"
    try:
        cap = subprocess.run(
            [tmux_path, "capture-pane", "-t", pane_id, "-p"], capture_output=True, text=True, timeout=5, check=False
        )
        return cap.stdout[-500:] if cap.returncode == 0 else f"(pane {pane_id} not found)"
    except subprocess.TimeoutExpired:
        return f"(tmux timeout on pane {pane_id})"


def main() -> None:
    """Display team member activity and tmux window status."""
    team_name = sys.argv[1] if len(sys.argv) > 1 else latest_team()
    if not team_name:
        print("No teams found.")
        return

    now = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC")
    cfg_path = TEAMS_DIR / team_name / "config.json"
    if not cfg_path.exists():
        print(f"Team not found: {team_name}")
        return

    cfg = json.loads(cfg_path.read_text())
    members = cfg.get("members", [])
    lead_session: str | None = cfg.get("leadSessionId")

    print(f"\n{'━' * 64}")
    print(f"  Team : {team_name}")
    print(f"  Now  : {now}")
    print(f"  Agents: {len(members)}")
    print(f"{'━' * 64}")

    for m in members:
        name = m.get("name", "?")
        atype = m.get("agentType", "")
        agent_id = m.get("agentId", "")
        pane_id = m.get("tmuxPaneId", "")
        is_lead = name == "team-lead"

        print(f"\n▶ {name}  [{atype}]")

        actions, session = agent_last_actions(name=agent_id, lead_session=lead_session if is_lead else None)
        if session:
            print(f"  session: {session}")
        if actions:
            for a in actions:
                print(a)
        else:
            print("  (no tool calls found in recent sessions)")

        if pane_id:
            content = capture_pane(pane_id)
            tail = content.replace("\n", "↵")
            print(f"  tmux[{pane_id}]: …{tail}")
        else:
            print("  tmux: no pane assigned")

    print(f"\n{'━' * 64}\n")


if __name__ == "__main__":
    main()
