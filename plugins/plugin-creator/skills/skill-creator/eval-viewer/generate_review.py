#!/usr/bin/env python3
"""Generate and serve a review page for eval results.

Reads the workspace directory, discovers runs (directories with outputs/),
embeds all output data into a self-contained HTML page, and serves it via
a tiny HTTP server. Feedback auto-saves to feedback.json in the workspace.

Usage:
    python generate_review.py <workspace-path> [--port PORT] [--skill-name NAME]
    python generate_review.py <workspace-path> --previous-feedback /path/to/old/feedback.json

No dependencies beyond the Python stdlib are required.
"""

from __future__ import annotations

import argparse
import base64
import contextlib
import json
import mimetypes
import os
import re
import signal
import subprocess
import sys
import time
import webbrowser
from functools import partial
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

# Files to exclude from output listings
METADATA_FILES = {"transcript.md", "user_notes.md", "metrics.json"}

# Extensions we render as inline text
TEXT_EXTENSIONS = {
    ".txt",
    ".md",
    ".json",
    ".csv",
    ".py",
    ".js",
    ".ts",
    ".tsx",
    ".jsx",
    ".yaml",
    ".yml",
    ".xml",
    ".html",
    ".css",
    ".sh",
    ".rb",
    ".go",
    ".rs",
    ".java",
    ".c",
    ".cpp",
    ".h",
    ".hpp",
    ".sql",
    ".r",
    ".toml",
}

# Extensions we render as inline images
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp"}

# MIME type overrides for common types
MIME_OVERRIDES = {
    ".svg": "image/svg+xml",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
}


def get_mime_type(path: Path) -> str:
    """Return the MIME type for a file path.

    Args:
        path: File path to inspect.

    Returns:
        MIME type string, falling back to ``"application/octet-stream"`` when
        the type cannot be determined.
    """
    ext = path.suffix.lower()
    if ext in MIME_OVERRIDES:
        return MIME_OVERRIDES[ext]
    mime, _ = mimetypes.guess_type(str(path))
    return mime or "application/octet-stream"


def find_runs(workspace: Path) -> list[dict]:
    """Recursively find directories that contain an outputs/ subdirectory.

    Args:
        workspace: Root directory to search.

    Returns:
        List of run dicts sorted by ``(eval_id, id)``.
    """
    runs: list[dict] = []
    _find_runs_recursive(workspace, workspace, runs)
    runs.sort(key=lambda r: (r.get("eval_id", float("inf")), r["id"]))
    return runs


def _find_runs_recursive(root: Path, current: Path, runs: list[dict]) -> None:
    if not current.is_dir():
        return

    outputs_dir = current / "outputs"
    if outputs_dir.is_dir():
        run = build_run(root, current)
        if run:
            runs.append(run)
        return

    skip = {"node_modules", ".git", "__pycache__", "skill", "inputs"}
    for child in sorted(current.iterdir()):
        if child.is_dir() and child.name not in skip:
            _find_runs_recursive(root, child, runs)


def _resolve_prompt(run_dir: Path) -> tuple[str, object]:
    """Resolve the eval prompt and ID for a run directory.

    Checks ``eval_metadata.json`` first, then falls back to ``transcript.md``.

    Args:
        run_dir: Path to the run directory.

    Returns:
        Two-tuple of ``(prompt_text, eval_id)``.  ``prompt_text`` is
        ``"(No prompt found)"`` when neither source yields text.
        ``eval_id`` is ``None`` when not determinable.
    """
    prompt = ""
    eval_id = None

    for candidate in [run_dir / "eval_metadata.json", run_dir.parent / "eval_metadata.json"]:
        if candidate.exists():
            try:
                metadata = json.loads(candidate.read_text())
                prompt = metadata.get("prompt", "")
                eval_id = metadata.get("eval_id")
            except (json.JSONDecodeError, OSError):
                pass
            if prompt:
                return prompt, eval_id

    for candidate in [run_dir / "transcript.md", run_dir / "outputs" / "transcript.md"]:
        if candidate.exists():
            try:
                text = candidate.read_text()
                match = re.search(r"## Eval Prompt\n\n([\s\S]*?)(?=\n##|$)", text)
                if match:
                    prompt = match.group(1).strip()
            except OSError:
                pass
            if prompt:
                return prompt, eval_id

    return prompt or "(No prompt found)", eval_id


def _resolve_grading(run_dir: Path) -> dict | None:
    """Load grading.json from the run dir or its parent.

    Args:
        run_dir: Path to the run directory.

    Returns:
        Parsed grading dict, or ``None`` if not found or unreadable.
    """
    for candidate in [run_dir / "grading.json", run_dir.parent / "grading.json"]:
        if candidate.exists():
            grading = None
            with contextlib.suppress(json.JSONDecodeError, OSError):
                grading = json.loads(candidate.read_text())
            if grading:
                return grading
    return None


def build_run(root: Path, run_dir: Path) -> dict | None:
    """Build a run dict with prompt, outputs, and grading data.

    Args:
        root: Workspace root used for computing relative IDs.
        run_dir: Path to the individual run directory.

    Returns:
        Run dict with keys ``id``, ``prompt``, ``eval_id``, ``outputs``, and
        ``grading``, or ``None`` when the directory is not a valid run.
    """
    prompt, eval_id = _resolve_prompt(run_dir)
    run_id = str(run_dir.relative_to(root)).replace("/", "-").replace("\\", "-")

    outputs_dir = run_dir / "outputs"
    output_files: list[dict] = []
    if outputs_dir.is_dir():
        output_files.extend(
            embed_file(f) for f in sorted(outputs_dir.iterdir()) if f.is_file() and f.name not in METADATA_FILES
        )

    grading = _resolve_grading(run_dir)

    return {"id": run_id, "prompt": prompt, "eval_id": eval_id, "outputs": output_files, "grading": grading}


def embed_file(path: Path) -> dict:
    """Read a file and return an embedded representation.

    Args:
        path: File to embed.

    Returns:
        Dict with at least ``name`` and ``type`` keys.  Additional keys depend
        on the file type: ``content`` for text/error, ``data_uri`` for
        images/PDFs/binary, ``data_b64`` for xlsx.
    """
    ext = path.suffix.lower()
    mime = get_mime_type(path)

    if ext in TEXT_EXTENSIONS:
        try:
            content = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            content = "(Error reading file)"
        return {"name": path.name, "type": "text", "content": content}
    if ext in IMAGE_EXTENSIONS:
        try:
            raw = path.read_bytes()
            b64 = base64.b64encode(raw).decode("ascii")
        except OSError:
            return {"name": path.name, "type": "error", "content": "(Error reading file)"}
        return {"name": path.name, "type": "image", "mime": mime, "data_uri": f"data:{mime};base64,{b64}"}
    if ext == ".pdf":
        try:
            raw = path.read_bytes()
            b64 = base64.b64encode(raw).decode("ascii")
        except OSError:
            return {"name": path.name, "type": "error", "content": "(Error reading file)"}
        return {"name": path.name, "type": "pdf", "data_uri": f"data:{mime};base64,{b64}"}
    if ext == ".xlsx":
        try:
            raw = path.read_bytes()
            b64 = base64.b64encode(raw).decode("ascii")
        except OSError:
            return {"name": path.name, "type": "error", "content": "(Error reading file)"}
        return {"name": path.name, "type": "xlsx", "data_b64": b64}
    # Binary / unknown — base64 download link
    try:
        raw = path.read_bytes()
        b64 = base64.b64encode(raw).decode("ascii")
    except OSError:
        return {"name": path.name, "type": "error", "content": "(Error reading file)"}
    return {"name": path.name, "type": "binary", "mime": mime, "data_uri": f"data:{mime};base64,{b64}"}


def load_previous_iteration(workspace: Path) -> dict[str, dict]:
    """Load previous iteration's feedback and outputs.

    Args:
        workspace: Previous iteration's workspace directory.

    Returns:
        Map of ``run_id`` -> ``{"feedback": str, "outputs": list[dict]}``.
    """
    result: dict[str, dict] = {}

    # Load feedback
    feedback_map: dict[str, str] = {}
    feedback_path = workspace / "feedback.json"
    if feedback_path.exists():
        try:
            data = json.loads(feedback_path.read_text())
            feedback_map = {
                r["run_id"]: r["feedback"] for r in data.get("reviews", []) if r.get("feedback", "").strip()
            }
        except (json.JSONDecodeError, OSError, KeyError):
            pass

    # Load runs (to get outputs)
    prev_runs = find_runs(workspace)
    for run in prev_runs:
        result[run["id"]] = {"feedback": feedback_map.get(run["id"], ""), "outputs": run.get("outputs", [])}

    # Also add feedback for run_ids that had feedback but no matching run
    for run_id, fb in feedback_map.items():
        if run_id not in result:
            result[run_id] = {"feedback": fb, "outputs": []}

    return result


def generate_html(
    runs: list[dict], skill_name: str, previous: dict[str, dict] | None = None, benchmark: dict | None = None
) -> str:
    """Generate the complete standalone HTML page with embedded data.

    Args:
        runs: List of run dicts from :func:`find_runs`.
        skill_name: Display name shown in the page header.
        previous: Optional map of previous-iteration data keyed by run ID.
        benchmark: Optional benchmark dict to embed in the page.

    Returns:
        Complete HTML string with all data embedded as a JSON constant.
    """
    template_path = Path(__file__).parent / "viewer.html"
    template = template_path.read_text()

    # Build previous_feedback and previous_outputs maps for the template
    previous_feedback: dict[str, str] = {}
    previous_outputs: dict[str, list[dict]] = {}
    if previous:
        for run_id, data in previous.items():
            if data.get("feedback"):
                previous_feedback[run_id] = data["feedback"]
            if data.get("outputs"):
                previous_outputs[run_id] = data["outputs"]

    embedded = {
        "skill_name": skill_name,
        "runs": runs,
        "previous_feedback": previous_feedback,
        "previous_outputs": previous_outputs,
    }
    if benchmark:
        embedded["benchmark"] = benchmark

    data_json = json.dumps(embedded)

    return template.replace("/*__EMBEDDED_DATA__*/", f"const EMBEDDED_DATA = {data_json};")


# ---------------------------------------------------------------------------
# HTTP server (stdlib only, zero dependencies)
# ---------------------------------------------------------------------------


def _kill_port(port: int) -> None:
    """Kill any process listening on the given port."""
    try:
        result = subprocess.run(["lsof", "-ti", f":{port}"], capture_output=True, text=True, timeout=5, check=False)
        for pid_str in result.stdout.strip().split("\n"):
            if pid_str.strip():
                with contextlib.suppress(ProcessLookupError, ValueError):
                    os.kill(int(pid_str.strip()), signal.SIGTERM)
        if result.stdout.strip():
            time.sleep(0.5)
    except subprocess.TimeoutExpired:
        pass
    except FileNotFoundError:
        print("Note: lsof not found, cannot check if port is in use", file=sys.stderr)


class ReviewHandler(BaseHTTPRequestHandler):
    """Serves the review HTML and handles feedback saves.

    Regenerates the HTML on each page load so that refreshing the browser
    picks up new eval outputs without restarting the server.
    """

    def __init__(
        self,
        workspace: Path,
        skill_name: str,
        feedback_path: Path,
        previous: dict[str, dict],
        benchmark_path: Path | None,
        *args,
        **kwargs,
    ) -> None:
        self.workspace = workspace
        self.skill_name = skill_name
        self.feedback_path = feedback_path
        self.previous = previous
        self.benchmark_path = benchmark_path
        super().__init__(*args, **kwargs)

    def do_GET(self) -> None:
        if self.path in {"/", "/index.html"}:
            # Regenerate HTML on each request (re-scans workspace for new outputs)
            runs = find_runs(self.workspace)
            benchmark = None
            if self.benchmark_path and self.benchmark_path.exists():
                with contextlib.suppress(json.JSONDecodeError, OSError):
                    benchmark = json.loads(self.benchmark_path.read_text())
            html = generate_html(runs, self.skill_name, self.previous, benchmark)
            content = html.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
        elif self.path == "/api/feedback":
            data = b"{}"
            if self.feedback_path.exists():
                data = self.feedback_path.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        else:
            self.send_error(404)

    def do_POST(self) -> None:
        if self.path == "/api/feedback":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length)
            try:
                data = json.loads(body)
                if not isinstance(data, dict) or "reviews" not in data:
                    msg = "Expected JSON object with 'reviews' key"
                    raise ValueError(msg)  # noqa: TRY301
                self.feedback_path.write_text(json.dumps(data, indent=2) + "\n")
                resp = b'{"ok":true}'
                self.send_response(200)
            except (json.JSONDecodeError, OSError, ValueError) as e:
                resp = json.dumps({"error": str(e)}).encode()
                self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(resp)))
            self.end_headers()
            self.wfile.write(resp)
        else:
            self.send_error(404)

    def log_message(self, format: str, *args: object) -> None:  # noqa: A002
        # Suppress request logging to keep terminal clean
        pass


def _build_arg_parser() -> argparse.ArgumentParser:
    """Build and return the CLI argument parser.

    Returns:
        Configured :class:`argparse.ArgumentParser` instance.
    """
    parser = argparse.ArgumentParser(description="Generate and serve eval review")
    parser.add_argument("workspace", type=Path, help="Path to workspace directory")
    parser.add_argument("--port", "-p", type=int, default=3117, help="Server port (default: 3117)")
    parser.add_argument("--skill-name", "-n", type=str, default=None, help="Skill name for header")
    parser.add_argument(
        "--previous-workspace",
        type=Path,
        default=None,
        help="Path to previous iteration's workspace (shows old outputs and feedback as context)",
    )
    parser.add_argument(
        "--benchmark", type=Path, default=None, help="Path to benchmark.json to show in the Benchmark tab"
    )
    parser.add_argument(
        "--static",
        "-s",
        type=Path,
        default=None,
        help="Write standalone HTML to this path instead of starting a server",
    )
    return parser


def _load_benchmark(benchmark_path: Path | None) -> dict | None:
    """Load benchmark.json if the path is set and the file exists.

    Args:
        benchmark_path: Resolved path to benchmark.json, or ``None``.

    Returns:
        Parsed benchmark dict, or ``None`` when unavailable or unreadable.
    """
    if benchmark_path is None or not benchmark_path.exists():
        return None
    result: dict | None = None
    with contextlib.suppress(json.JSONDecodeError, OSError):
        result = json.loads(benchmark_path.read_text())
    return result


def _start_server(
    workspace: Path,
    skill_name: str,
    feedback_path: Path,
    previous: dict[str, dict],
    benchmark_path: Path | None,
    previous_workspace: Path | None,
    port: int,
) -> None:
    """Start the HTTP review server, print connection info, and open the browser.

    Args:
        workspace: Resolved workspace directory.
        skill_name: Display name shown in the page header.
        feedback_path: Path where feedback.json is written.
        previous: Previous-iteration data map.
        benchmark_path: Resolved path to benchmark.json, or ``None``.
        previous_workspace: Original ``--previous-workspace`` arg (for display).
        port: Preferred server port.
    """
    _kill_port(port)
    handler = partial(ReviewHandler, workspace, skill_name, feedback_path, previous, benchmark_path)
    try:
        server = HTTPServer(("127.0.0.1", port), handler)
    except OSError:
        # Port still in use after kill attempt — find a free one
        server = HTTPServer(("127.0.0.1", 0), handler)
        port = server.server_address[1]

    url = f"http://localhost:{port}"
    print("\n  Eval Viewer")
    print("  ─────────────────────────────────")
    print(f"  URL:       {url}")
    print(f"  Workspace: {workspace}")
    print(f"  Feedback:  {feedback_path}")
    if previous:
        print(f"  Previous:  {previous_workspace} ({len(previous)} runs)")
    if benchmark_path:
        print(f"  Benchmark: {benchmark_path}")
    print("\n  Press Ctrl+C to stop.\n")

    webbrowser.open(url)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
        server.server_close()


def main() -> None:
    """Parse arguments and either write a static HTML file or start the review server."""
    args = _build_arg_parser().parse_args()

    workspace = args.workspace.resolve()
    if not workspace.is_dir():
        print(f"Error: {workspace} is not a directory", file=sys.stderr)
        sys.exit(1)

    runs = find_runs(workspace)
    if not runs:
        print(f"No runs found in {workspace}", file=sys.stderr)
        sys.exit(1)

    skill_name = args.skill_name or workspace.name.replace("-workspace", "")
    feedback_path = workspace / "feedback.json"

    previous: dict[str, dict] = {}
    if args.previous_workspace:
        previous = load_previous_iteration(args.previous_workspace.resolve())

    benchmark_path = args.benchmark.resolve() if args.benchmark else None
    benchmark = _load_benchmark(benchmark_path)

    if args.static:
        html = generate_html(runs, skill_name, previous, benchmark)
        args.static.parent.mkdir(parents=True, exist_ok=True)
        args.static.write_text(html)
        print(f"\n  Static viewer written to: {args.static}\n")
        sys.exit(0)

    _start_server(workspace, skill_name, feedback_path, previous, benchmark_path, args.previous_workspace, args.port)


if __name__ == "__main__":
    main()
