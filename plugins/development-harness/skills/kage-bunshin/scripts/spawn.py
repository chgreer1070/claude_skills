#!/usr/bin/env -S uv --quiet run --active --script
# /// script
# requires-python = ">=3.11"
# ///
"""Kage-bunshin session manager — bidirectional orchestrator/claude communication.

Provides CLI subcommands for spawning and managing persistent claude CLI sessions
via tmux, named pipes (FIFOs), and JSONL output files.

Usage:
    spawn.py spawn  --name X [--worktree] [--model MODEL] [--max-budget N] "prompt"
    spawn.py send   --name X "message"
    spawn.py read   --name X [--wait SECONDS] [--follow]
    spawn.py status --name X
    spawn.py list
    spawn.py kill   --name X

Session State Directory:
    ~/.dh/projects/{slug}/kage-bunshin/
    Override base with DH_STATE_HOME environment variable.

    Slug is derived from the git repo root path by replacing '/' with '-'.
    Example: /home/user/repos/claude_skills -> -home-user-repos-claude_skills

Exit Codes:
    0: Success.
    1: Fatal error (session not found, tmux failure, etc.).
"""

from __future__ import annotations

import argparse
import contextlib
import errno
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_DEFAULT_MODEL = "sonnet"
_TMUX_PREFIX = "kb-"
_REGISTRY_FILE = "registry.json"
_POLL_INTERVAL_SECONDS = 2
_NAME_MAX_CHARS = 30
_SLUG_RE = re.compile(r"[^a-z0-9]+")


# ---------------------------------------------------------------------------
# State directory resolution
# ---------------------------------------------------------------------------


def _dh_state_home() -> Path:
    """Return the DH state home directory, respecting DH_STATE_HOME override.

    Returns:
        Path to the base DH state directory (~/.dh/ or $DH_STATE_HOME).
    """
    override = os.environ.get("DH_STATE_HOME", "").strip()
    if override:
        return Path(override)
    return Path.home() / ".dh"


def _git_repo_root() -> Path:
    """Return the root of the current git repository.

    Returns:
        Absolute path to the repository root.

    Raises:
        SystemExit: If the current directory is not inside a git repository.
    """
    result = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True, check=False)
    if result.returncode != 0:
        _die(f"not inside a git repository: {result.stderr.strip()}")
    return Path(result.stdout.strip())


def _repo_slug(repo_root: Path) -> str:
    """Derive the project slug from the repository root path.

    Replaces all '/' separators with '-'. The leading '-' is intentional.

    Args:
        repo_root: Absolute path to the git repository root.

    Returns:
        Slug string derived from the path, e.g. '-home-user-repos-project'.
    """
    return str(repo_root).replace("/", "-")


def _session_state_dir() -> Path:
    """Return (and create) the kage-bunshin state directory for the current repo.

    Returns:
        Path to ~/.dh/projects/{slug}/kage-bunshin/, created if absent.
    """
    repo_root = _git_repo_root()
    slug = _repo_slug(repo_root)
    state_dir = _dh_state_home() / "projects" / slug / "kage-bunshin"
    state_dir.mkdir(parents=True, exist_ok=True)
    return state_dir


# ---------------------------------------------------------------------------
# Registry helpers
# ---------------------------------------------------------------------------


def _registry_path(state_dir: Path) -> Path:
    """Return the path to registry.json within the state directory.

    Args:
        state_dir: Session state directory.

    Returns:
        Path to registry.json.
    """
    return state_dir / _REGISTRY_FILE


def _load_registry(state_dir: Path) -> dict[str, Any]:
    """Load the session registry from disk, returning an empty dict if absent.

    Args:
        state_dir: Session state directory.

    Returns:
        Dictionary mapping session name to session metadata.
    """
    rp = _registry_path(state_dir)
    if not rp.exists():
        return {}
    try:
        return json.loads(rp.read_text())
    except (json.JSONDecodeError, OSError):
        return {}


def _save_registry(state_dir: Path, registry: dict[str, Any]) -> None:
    """Persist the session registry to disk atomically.

    Args:
        state_dir: Session state directory.
        registry: Dictionary mapping session name to session metadata.
    """
    rp = _registry_path(state_dir)
    tmp = rp.with_suffix(".tmp")
    tmp.write_text(json.dumps(registry, indent=2))
    tmp.replace(rp)


def _get_session(state_dir: Path, name: str) -> dict[str, Any]:
    """Retrieve a session entry from the registry, failing loudly if absent.

    Args:
        state_dir: Session state directory.
        name: Session name.

    Returns:
        Session metadata dictionary.

    Raises:
        SystemExit: If the named session does not exist in the registry.
    """
    registry = _load_registry(state_dir)
    if name not in registry:
        _die(f"session '{name}' not found. Run 'list' to see active sessions.")
    return registry[name]


# ---------------------------------------------------------------------------
# tmux helpers
# ---------------------------------------------------------------------------


def _tmux_session_name(name: str) -> str:
    """Return the tmux session name for a kage-bunshin session.

    Args:
        name: Session name.

    Returns:
        tmux session name string.
    """
    return f"{_TMUX_PREFIX}{name}"


def _tmux_alive(name: str) -> bool:
    """Check whether a tmux session is currently alive.

    Args:
        name: Session name (not the tmux name — the kage-bunshin name).

    Returns:
        True if the tmux session exists, False otherwise.
    """
    result = subprocess.run(["tmux", "has-session", "-t", _tmux_session_name(name)], capture_output=True, check=False)
    return result.returncode == 0


def _tmux_kill(name: str) -> None:
    """Kill a tmux session, ignoring errors if it no longer exists.

    Args:
        name: Session name.
    """
    subprocess.run(["tmux", "kill-session", "-t", _tmux_session_name(name)], capture_output=True, check=False)


# ---------------------------------------------------------------------------
# Stream-JSON helpers
# ---------------------------------------------------------------------------


def _make_user_message(content: str) -> str:
    """Serialise a user message as a stream-json line.

    Args:
        content: Message text.

    Returns:
        JSON string (no trailing newline) suitable for writing to a FIFO.
    """
    payload: dict[str, Any] = {"type": "user", "message": {"role": "user", "content": content}}
    return json.dumps(payload)


# ---------------------------------------------------------------------------
# Error utilities
# ---------------------------------------------------------------------------


def _die(message: str, code: int = 1) -> None:
    """Print an error message to stderr and exit.

    Args:
        message: Error description.
        code: Exit code (default 1).
    """
    print(f"error: {message}", file=sys.stderr)
    sys.exit(code)


def _slugify(text: str) -> str:
    """Convert text to a URL-safe lowercase slug.

    Args:
        text: Input string.

    Returns:
        Slug with non-alphanumeric runs replaced by hyphens.
    """
    slug = _SLUG_RE.sub("-", text.lower()).strip("-")
    return slug[:_NAME_MAX_CHARS].rstrip("-")


# ---------------------------------------------------------------------------
# Subcommand: spawn
# ---------------------------------------------------------------------------


def cmd_spawn(args: argparse.Namespace) -> None:
    """Spawn a new persistent claude session inside a tmux window.

    Creates a named FIFO for input, launches claude inside tmux with
    stream-json I/O, sends the initial prompt, and keeps the write end
    of the FIFO open so the session remains alive.

    Args:
        args: Parsed arguments containing name, prompt, worktree, model,
            max_budget fields.
    """
    if shutil.which("claude") is None:
        _die("claude binary not found in PATH")
    if shutil.which("tmux") is None:
        _die("tmux binary not found in PATH")

    state_dir = _session_state_dir()
    registry = _load_registry(state_dir)

    name: str = args.name or _slugify(args.prompt[0])
    if not name:
        _die("could not derive a session name from the prompt; pass --name explicitly")

    if name in registry:
        if _tmux_alive(name):
            _die(f"session '{name}' already exists and is alive. Kill it first.")
        # Dead entry — clean up and re-spawn.
        registry.pop(name)

    fifo_path = state_dir / f"{name}-input.fifo"
    output_path = state_dir / f"{name}-output.jsonl"
    error_path = state_dir / f"{name}-err.log"
    tmux_session = _tmux_session_name(name)

    # Create (or recreate) the FIFO.
    if fifo_path.exists():
        fifo_path.unlink()
    os.mkfifo(fifo_path, mode=stat.S_IRUSR | stat.S_IWUSR)

    # Build claude command.
    claude_cmd_parts: list[str] = [
        "claude",
        "-p",
        "--dangerously-skip-permissions",
        "--input-format",
        "stream-json",
        "--output-format",
        "stream-json",
        "--verbose",
        "--model",
        args.model,
    ]
    if args.max_budget is not None:
        claude_cmd_parts += ["--max-budget-usd", str(args.max_budget)]
    if args.worktree:
        claude_cmd_parts += ["--worktree", name]

    # The tmux shell command:
    #   cat <fifo> | claude ... > output.jsonl 2> err.log
    # Using 'cat' keeps the read end open as long as any writer holds the
    # write end open, which we ensure via the background tail below.
    claude_cmd = " ".join(f"'{p}'" if " " in p else p for p in claude_cmd_parts)
    shell_cmd = f"cat {fifo_path} | {claude_cmd} >> {output_path} 2>> {error_path}"

    result = subprocess.run(
        ["tmux", "new-session", "-d", "-s", tmux_session, "bash", "-c", shell_cmd],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        _die(f"tmux new-session failed: {result.stderr.strip()}")

    # Keep the write end open BEFORE writing the initial prompt.
    # This prevents a race where 'cat' in tmux reads the prompt and gets
    # EOF before any persistent writer opens the FIFO.
    # tail -f /dev/null writes nothing but holds the fd open indefinitely.
    subprocess.Popen(
        ["bash", "-c", f"tail -f /dev/null > {fifo_path}"],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )

    # Write the initial prompt to the FIFO.  The keepalive above ensures
    # 'cat' always has at least one writer, so it won't get EOF after
    # consuming this message.
    _write_to_fifo(fifo_path, _make_user_message(args.prompt[0]))

    spawned_at = datetime.now(UTC).isoformat()
    entry: dict[str, Any] = {
        "name": name,
        "model": args.model,
        "spawned_at": spawned_at,
        "worktree": args.worktree,
        "fifo_path": str(fifo_path),
        "output_path": str(output_path),
        "error_path": str(error_path),
        "tmux_session": tmux_session,
    }
    registry[name] = entry
    _save_registry(state_dir, registry)

    record: dict[str, Any] = {
        "name": name,
        "tmux_session": tmux_session,
        "model": args.model,
        "spawned_at": spawned_at,
        "worktree": args.worktree,
        "fifo_path": str(fifo_path),
        "output_path": str(output_path),
        "error_path": str(error_path),
    }
    print(json.dumps(record))


def _write_to_fifo(fifo_path: Path, line: str, retries: int = 10, delay: float = 0.3) -> None:
    """Write a newline-terminated JSON line to the FIFO with retry logic.

    Opening the write end of a FIFO blocks until a reader is present.
    We use O_NONBLOCK with retries to handle the brief window before
    tmux's 'cat' opens the read end.

    Args:
        fifo_path: Path to the named pipe.
        line: JSON string to write (newline will be appended).
        retries: Maximum number of open attempts before giving up.
        delay: Seconds to wait between retries.

    Raises:
        SystemExit: If the FIFO cannot be opened after all retries.
    """
    for _attempt in range(retries):
        try:
            fd = os.open(str(fifo_path), os.O_WRONLY | os.O_NONBLOCK)
            with os.fdopen(fd, "w") as fh:
                fh.write(line + "\n")
        except OSError as exc:
            if exc.errno in {errno.ENXIO, errno.EAGAIN}:
                # No reader yet — wait and retry.
                time.sleep(delay)
                continue
            _die(f"could not write to FIFO {fifo_path}: {exc}")
        else:
            return
    _die(f"FIFO {fifo_path} has no reader after {retries} attempts. Is the session alive?")


# ---------------------------------------------------------------------------
# Subcommand: send
# ---------------------------------------------------------------------------


def cmd_send(args: argparse.Namespace) -> None:
    """Send a message to an existing session via its input FIFO.

    Args:
        args: Parsed arguments with name and message fields.
    """
    state_dir = _session_state_dir()
    session = _get_session(state_dir, args.name)

    if not _tmux_alive(args.name):
        _die(f"session '{args.name}' tmux session is dead")

    fifo_path = Path(session["fifo_path"])
    if not fifo_path.exists():
        _die(f"FIFO not found at {fifo_path}. Session may have died.")

    _write_to_fifo(fifo_path, _make_user_message(args.message[0]))
    print(json.dumps({"status": "sent", "name": args.name}))


# ---------------------------------------------------------------------------
# Subcommand: read
# ---------------------------------------------------------------------------


def _parse_jsonl_events(output_path: Path) -> list[dict[str, Any]]:
    """Parse all valid JSON lines from the output JSONL file.

    Args:
        output_path: Path to the session's output JSONL file.

    Returns:
        List of parsed event dicts. Malformed lines are silently skipped.
    """
    if not output_path.exists():
        return []
    events: list[dict[str, Any]] = []
    for raw_line in output_path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        with contextlib.suppress(json.JSONDecodeError):
            events.append(json.loads(line))
    return events


def _extract_assistant_text(events: list[dict[str, Any]]) -> str | None:
    """Extract the text content from the last assistant message event.

    Args:
        events: Parsed stream-json events.

    Returns:
        Text string from the last assistant message, or None if not found.
    """
    for event in reversed(events):
        if event.get("type") != "assistant":
            continue
        msg = event.get("message", {})
        content = msg.get("content", [])
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts = [
                block.get("text", "") for block in content if isinstance(block, dict) and block.get("type") == "text"
            ]
            if parts:
                return "".join(parts)
    return None


def cmd_read(args: argparse.Namespace) -> None:
    """Read responses from a session's output JSONL file.

    By default prints the latest assistant message text.
    With --follow, tails the output file continuously.
    With --wait N, polls for up to N seconds.

    Args:
        args: Parsed arguments with name, wait, follow fields.
    """
    state_dir = _session_state_dir()
    session = _get_session(state_dir, args.name)
    output_path = Path(session["output_path"])

    if args.follow:
        _follow_output(output_path)
        return

    wait_seconds: float = args.wait or 0.0
    deadline = time.monotonic() + wait_seconds
    last_seen = 0

    while True:
        events = _parse_jsonl_events(output_path)
        new_events = events[last_seen:]

        for event in new_events:
            etype = event.get("type", "")
            if etype == "assistant":
                text = _extract_assistant_text([event])
                if text:
                    print(text)
            elif etype == "result":
                # Print result summary as JSON.
                print(json.dumps(event))

        if new_events:
            last_seen = len(events)

        if not new_events and wait_seconds > 0 and time.monotonic() < deadline:
            time.sleep(_POLL_INTERVAL_SECONDS)
            continue

        break

    if last_seen == 0 and not output_path.exists():
        print("(no output yet)", file=sys.stderr)


def _follow_output(output_path: Path) -> None:
    """Continuously tail the output JSONL file, printing new events.

    Runs until interrupted with Ctrl-C.

    Args:
        output_path: Path to the session output file.
    """
    print(f"Following {output_path} (Ctrl-C to stop)", file=sys.stderr)
    offset = 0
    if output_path.exists():
        offset = output_path.stat().st_size

    try:
        while True:
            if not output_path.exists():
                time.sleep(_POLL_INTERVAL_SECONDS)
                continue

            current_size = output_path.stat().st_size
            if current_size <= offset:
                time.sleep(_POLL_INTERVAL_SECONDS)
                continue

            with output_path.open(encoding="utf-8") as fh:
                fh.seek(offset)
                chunk = fh.read(current_size - offset)
            offset = current_size

            for raw_line in chunk.splitlines():
                line = raw_line.strip()
                if not line:
                    continue
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    continue

                etype = event.get("type", "")
                if etype == "assistant":
                    text = _extract_assistant_text([event])
                    if text:
                        print(text)
                elif etype == "result":
                    print(json.dumps(event))

    except KeyboardInterrupt:
        pass


# ---------------------------------------------------------------------------
# Subcommand: status
# ---------------------------------------------------------------------------


def cmd_status(args: argparse.Namespace) -> None:
    """Print status for a named session.

    Checks tmux liveness, reads the latest result event for cost/turns.

    Args:
        args: Parsed arguments with name field.
    """
    state_dir = _session_state_dir()
    session = _get_session(state_dir, args.name)

    alive = _tmux_alive(args.name)
    output_path = Path(session["output_path"])
    events = _parse_jsonl_events(output_path)

    # Find the most recent result event.
    cost: float | None = None
    turns: int | None = None
    for event in reversed(events):
        if event.get("type") == "result":
            cost = event.get("cost_usd")
            turns = event.get("num_turns")
            break

    spawned_at = session.get("spawned_at", "unknown")
    try:
        dt = datetime.fromisoformat(spawned_at)
        age_seconds = (datetime.now(UTC) - dt).total_seconds()
        age_str = _format_age(age_seconds)
    except ValueError:
        age_str = "unknown"

    status: dict[str, Any] = {
        "name": args.name,
        "alive": alive,
        "model": session.get("model"),
        "spawned_at": spawned_at,
        "age": age_str,
        "worktree": session.get("worktree"),
        "tmux_session": session.get("tmux_session"),
        "cost_usd": cost,
        "turns": turns,
    }
    print(json.dumps(status, indent=2))


# ---------------------------------------------------------------------------
# Subcommand: list
# ---------------------------------------------------------------------------


def cmd_list(_args: argparse.Namespace) -> None:
    """List all registered sessions with live/dead status.

    Args:
        _args: Parsed arguments (unused).
    """
    state_dir = _session_state_dir()
    registry = _load_registry(state_dir)

    if not registry:
        print("No sessions registered.")
        return

    rows: list[dict[str, Any]] = []
    for name, session in registry.items():
        alive = _tmux_alive(name)
        spawned_at = session.get("spawned_at", "")
        try:
            dt = datetime.fromisoformat(spawned_at)
            age_str = _format_age((datetime.now(UTC) - dt).total_seconds())
        except ValueError:
            age_str = "unknown"
        rows.append({
            "name": name,
            "model": session.get("model", "?"),
            "status": "alive" if alive else "dead",
            "age": age_str,
            "worktree": session.get("worktree", False),
            "tmux_session": session.get("tmux_session", ""),
        })

    # Simple columnar output.
    col_widths = {
        "name": max(len(r["name"]) for r in rows),
        "model": max(len(r["model"]) for r in rows),
        "status": 5,
        "age": max(len(r["age"]) for r in rows),
    }
    header = (
        f"{'NAME':<{col_widths['name']}}  "
        f"{'MODEL':<{col_widths['model']}}  "
        f"{'STATUS':<{col_widths['status']}}  "
        f"{'AGE':<{col_widths['age']}}  "
        f"WORKTREE"
    )
    print(header)
    print("-" * len(header))
    for r in rows:
        print(
            f"{r['name']:<{col_widths['name']}}  "
            f"{r['model']:<{col_widths['model']}}  "
            f"{r['status']:<{col_widths['status']}}  "
            f"{r['age']:<{col_widths['age']}}  "
            f"{'yes' if r['worktree'] else 'no'}"
        )


# ---------------------------------------------------------------------------
# Subcommand: kill
# ---------------------------------------------------------------------------


def cmd_kill(args: argparse.Namespace) -> None:
    """Kill a session: terminate tmux, remove FIFO, update registry.

    Output and error logs are preserved for post-mortem review.

    Args:
        args: Parsed arguments with name field.
    """
    state_dir = _session_state_dir()
    session = _get_session(state_dir, args.name)

    _tmux_kill(args.name)

    fifo_path = Path(session.get("fifo_path", ""))
    if fifo_path.exists() and fifo_path.is_fifo():
        fifo_path.unlink()

    registry = _load_registry(state_dir)
    registry.pop(args.name, None)
    _save_registry(state_dir, registry)

    print(json.dumps({"status": "killed", "name": args.name}))


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------


def _format_age(seconds: float) -> str:
    """Format a duration in seconds as a human-readable age string.

    Args:
        seconds: Duration in seconds.

    Returns:
        Age string like '5m', '2h', '3d', or '45s'.
    """
    seconds = int(seconds)
    if seconds < 60:  # noqa: PLR2004
        return f"{seconds}s"
    if seconds < 3600:  # noqa: PLR2004
        return f"{seconds // 60}m"
    if seconds < 86400:  # noqa: PLR2004
        return f"{seconds // 3600}h"
    return f"{seconds // 86400}d"


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------


def _build_parser() -> argparse.ArgumentParser:
    """Build the top-level argument parser with all subcommands.

    Returns:
        Configured :class:`argparse.ArgumentParser` instance.
    """
    parser = argparse.ArgumentParser(
        prog="spawn.py",
        description="Kage-bunshin: bidirectional manager for persistent claude sessions.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="command", metavar="COMMAND", required=True)

    # spawn
    p_spawn = sub.add_parser("spawn", help="Launch a new claude session in tmux.")
    p_spawn.add_argument("prompt", nargs=1, metavar="PROMPT", help="Initial prompt to send.")
    p_spawn.add_argument("--name", default=None, help="Session name (auto-derived from prompt if omitted).")
    p_spawn.add_argument(
        "--worktree", action="store_true", default=False, help="Use claude's built-in --worktree flag."
    )
    p_spawn.add_argument("--model", default=_DEFAULT_MODEL, help=f"Model to use (default: {_DEFAULT_MODEL}).")
    p_spawn.add_argument("--max-budget", type=float, default=None, metavar="USD", help="Maximum USD spend.")
    p_spawn.set_defaults(func=cmd_spawn)

    # send
    p_send = sub.add_parser("send", help="Send a message to a running session.")
    p_send.add_argument("--name", required=True, help="Session name.")
    p_send.add_argument("message", nargs=1, metavar="MESSAGE", help="Message text to send.")
    p_send.set_defaults(func=cmd_send)

    # read
    p_read = sub.add_parser("read", help="Read responses from a session.")
    p_read.add_argument("--name", required=True, help="Session name.")
    p_read.add_argument(
        "--wait", type=float, default=0.0, metavar="SECONDS", help="Poll for up to N seconds if no response yet."
    )
    p_read.add_argument(
        "--follow", action="store_true", default=False, help="Tail output continuously (Ctrl-C to stop)."
    )
    p_read.set_defaults(func=cmd_read)

    # status
    p_status = sub.add_parser("status", help="Show status of a session.")
    p_status.add_argument("--name", required=True, help="Session name.")
    p_status.set_defaults(func=cmd_status)

    # list
    p_list = sub.add_parser("list", help="List all registered sessions.")
    p_list.set_defaults(func=cmd_list)

    # kill
    p_kill = sub.add_parser("kill", help="Kill a session and clean up its FIFO.")
    p_kill.add_argument("--name", required=True, help="Session name.")
    p_kill.set_defaults(func=cmd_kill)

    return parser


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> None:
    """Parse arguments and dispatch to the appropriate subcommand handler.

    Args:
        argv: Argument list (defaults to sys.argv[1:]).
    """
    parser = _build_parser()
    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
