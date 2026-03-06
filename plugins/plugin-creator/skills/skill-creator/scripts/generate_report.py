#!/usr/bin/env python3
"""Generate an HTML report from run_loop.py output.

Takes the JSON output from run_loop.py and generates a visual HTML report
showing each description attempt with check/x for each test case.
Distinguishes between train and test queries.
"""

from __future__ import annotations

import argparse
import html
import json
import sys
from pathlib import Path

SCORE_GOOD_THRESHOLD = 0.8
SCORE_OK_THRESHOLD = 0.5


def aggregate_runs(results: list[dict]) -> tuple[int, int]:
    """Aggregate correct and total run counts across all retries.

    Args:
        results: List of result dicts, each with keys: runs, triggers, should_trigger.

    Returns:
        Tuple of (correct, total) counts.
    """
    correct = 0
    total = 0
    for r in results:
        runs = r.get("runs", 0)
        triggers = r.get("triggers", 0)
        total += runs
        if r.get("should_trigger", True):
            correct += triggers
        else:
            correct += runs - triggers
    return correct, total


def score_class(correct: int, total: int) -> str:
    """Determine the CSS score class for a correct/total ratio.

    Args:
        correct: Number of correct results.
        total: Total number of results.

    Returns:
        CSS class string: 'score-good', 'score-ok', or 'score-bad'.
    """
    if total > 0:
        ratio = correct / total
        if ratio >= SCORE_GOOD_THRESHOLD:
            return "score-good"
        if ratio >= SCORE_OK_THRESHOLD:
            return "score-ok"
    return "score-bad"


def _build_html_header(title_prefix: str, refresh_tag: str) -> str:
    """Build the HTML document head and opening body section.

    Args:
        title_prefix: Escaped skill name prefix for the page title.
        refresh_tag: HTML meta refresh tag string, or empty string.

    Returns:
        HTML string for the document head and body opening.
    """
    return (
        """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
"""
        + refresh_tag
        + """    <title>"""
        + title_prefix
        + """Skill Description Optimization</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@500;600&family=Lora:wght@400;500&display=swap" rel="stylesheet">
    <style>
        body {
            font-family: 'Lora', Georgia, serif;
            max-width: 100%;
            margin: 0 auto;
            padding: 20px;
            background: #faf9f5;
            color: #141413;
        }
        h1 { font-family: 'Poppins', sans-serif; color: #141413; }
        .explainer {
            background: white;
            padding: 15px;
            border-radius: 6px;
            margin-bottom: 20px;
            border: 1px solid #e8e6dc;
            color: #b0aea5;
            font-size: 0.875rem;
            line-height: 1.6;
        }
        .summary {
            background: white;
            padding: 15px;
            border-radius: 6px;
            margin-bottom: 20px;
            border: 1px solid #e8e6dc;
        }
        .summary p { margin: 5px 0; }
        .best { color: #788c5d; font-weight: bold; }
        .table-container {
            overflow-x: auto;
            width: 100%;
        }
        table {
            border-collapse: collapse;
            background: white;
            border: 1px solid #e8e6dc;
            border-radius: 6px;
            font-size: 12px;
            min-width: 100%;
        }
        th, td {
            padding: 8px;
            text-align: left;
            border: 1px solid #e8e6dc;
            white-space: normal;
            word-wrap: break-word;
        }
        th {
            font-family: 'Poppins', sans-serif;
            background: #141413;
            color: #faf9f5;
            font-weight: 500;
        }
        th.test-col {
            background: #6a9bcc;
        }
        th.query-col { min-width: 200px; }
        td.description {
            font-family: monospace;
            font-size: 11px;
            word-wrap: break-word;
            max-width: 400px;
        }
        td.result {
            text-align: center;
            font-size: 16px;
            min-width: 40px;
        }
        td.test-result {
            background: #f0f6fc;
        }
        .pass { color: #788c5d; }
        .fail { color: #c44; }
        .rate {
            font-size: 9px;
            color: #b0aea5;
            display: block;
        }
        tr:hover { background: #faf9f5; }
        .score {
            display: inline-block;
            padding: 2px 6px;
            border-radius: 4px;
            font-weight: bold;
            font-size: 11px;
        }
        .score-good { background: #eef2e8; color: #788c5d; }
        .score-ok { background: #fef3c7; color: #d97706; }
        .score-bad { background: #fceaea; color: #c44; }
        .train-label { color: #b0aea5; font-size: 10px; }
        .test-label { color: #6a9bcc; font-size: 10px; font-weight: bold; }
        .best-row { background: #f5f8f2; }
        th.positive-col { border-bottom: 3px solid #788c5d; }
        th.negative-col { border-bottom: 3px solid #c44; }
        th.test-col.positive-col { border-bottom: 3px solid #788c5d; }
        th.test-col.negative-col { border-bottom: 3px solid #c44; }
        .legend { font-family: 'Poppins', sans-serif; display: flex; gap: 20px; margin-bottom: 10px; font-size: 13px; align-items: center; }
        .legend-item { display: flex; align-items: center; gap: 6px; }
        .legend-swatch { width: 16px; height: 16px; border-radius: 3px; display: inline-block; }
        .swatch-positive { background: #141413; border-bottom: 3px solid #788c5d; }
        .swatch-negative { background: #141413; border-bottom: 3px solid #c44; }
        .swatch-test { background: #6a9bcc; }
        .swatch-train { background: #141413; }
    </style>
</head>
<body>
    <h1>"""
        + title_prefix
        + """Skill Description Optimization</h1>
    <div class="explainer">
        <strong>Optimizing your skill's description.</strong> This page updates automatically as Claude tests different versions of your skill's description. Each row is an iteration — a new description attempt. The columns show test queries: green checkmarks mean the skill triggered correctly (or correctly didn't trigger), red crosses mean it got it wrong. The "Train" score shows performance on queries used to improve the description; the "Test" score shows performance on held-out queries the optimizer hasn't seen. When it's done, Claude will apply the best-performing description to your skill.
    </div>
"""
    )


def _build_summary_section(data: dict, best_test_score: object) -> str:
    """Build the summary div showing best description and scores.

    Args:
        data: Top-level report data dict.
        best_test_score: The best test score value (used for label selection).

    Returns:
        HTML string for the summary section.
    """
    return f"""
    <div class="summary">
        <p><strong>Original:</strong> {html.escape(data.get("original_description", "N/A"))}</p>
        <p class="best"><strong>Best:</strong> {html.escape(data.get("best_description", "N/A"))}</p>
        <p><strong>Best Score:</strong> {data.get("best_score", "N/A")} {"(test)" if best_test_score else "(train)"}</p>
        <p><strong>Iterations:</strong> {data.get("iterations_run", 0)} | <strong>Train:</strong> {data.get("train_size", "?")} | <strong>Test:</strong> {data.get("test_size", "?")}</p>
    </div>
"""


def _build_table_header_cols(train_queries: list[dict], test_queries: list[dict]) -> list[str]:
    """Build the column header cells for train and test query columns.

    Args:
        train_queries: List of train query info dicts with 'query' and 'should_trigger'.
        test_queries: List of test query info dicts with 'query' and 'should_trigger'.

    Returns:
        List of HTML strings for each column header cell.
    """
    parts: list[str] = []
    for qinfo in train_queries:
        polarity = "positive-col" if qinfo["should_trigger"] else "negative-col"
        parts.append(f'                <th class="{polarity}">{html.escape(qinfo["query"])}</th>\n')
    for qinfo in test_queries:
        polarity = "positive-col" if qinfo["should_trigger"] else "negative-col"
        parts.append(f'                <th class="test-col {polarity}">{html.escape(qinfo["query"])}</th>\n')
    return parts


def _result_cell(r: dict, extra_class: str = "") -> str:
    """Build a single result table cell.

    Args:
        r: Result dict with keys: pass, triggers, runs.
        extra_class: Additional CSS class string to append (e.g. 'test-result').

    Returns:
        HTML string for the table cell.
    """
    did_pass = r.get("pass", False)
    icon = "✓" if did_pass else "✗"
    css = "pass" if did_pass else "fail"
    extra = f" {extra_class}" if extra_class else ""
    return f'                <td class="result{extra} {css}">{icon}<span class="rate">{r.get("triggers", 0)}/{r.get("runs", 0)}</span></td>\n'


def _build_iteration_row(h: dict, train_queries: list[dict], test_queries: list[dict], best_iter: object) -> list[str]:
    """Build HTML cells for a single iteration row.

    Args:
        h: History entry dict for this iteration.
        train_queries: List of train query info dicts.
        test_queries: List of test query info dicts.
        best_iter: The iteration number/id of the best-performing iteration.

    Returns:
        List of HTML strings making up the row cells.
    """
    iteration = h.get("iteration", "?")
    train_results = h.get("train_results", h.get("results", []))
    test_results = h.get("test_results", [])

    train_by_query = {r["query"]: r for r in train_results}
    test_by_query = {r["query"]: r for r in test_results} if test_results else {}

    train_correct, train_runs = aggregate_runs(train_results)
    test_correct, test_runs = aggregate_runs(test_results)
    row_class = "best-row" if iteration == best_iter else ""

    parts: list[str] = [
        f"""            <tr class="{row_class}">
                <td>{iteration}</td>
                <td><span class="score {score_class(train_correct, train_runs)}">{train_correct}/{train_runs}</span></td>
                <td><span class="score {score_class(test_correct, test_runs)}">{test_correct}/{test_runs}</span></td>
                <td class="description">{html.escape(h.get("description", ""))}</td>
"""
    ]

    parts.extend(_result_cell(train_by_query.get(q["query"], {})) for q in train_queries)
    parts.extend(_result_cell(test_by_query.get(q["query"], {}), "test-result") for q in test_queries)
    parts.append("            </tr>\n")
    return parts


def generate_html(data: dict, auto_refresh: bool = False, skill_name: str = "") -> str:
    """Generate HTML report from loop output data.

    If auto_refresh is True, adds a meta refresh tag to reload the page every 5 seconds.

    Args:
        data: Parsed JSON output from run_loop.py.
        auto_refresh: Whether to include a meta refresh tag for live reloading.
        skill_name: Skill name to display in the report title.

    Returns:
        Complete HTML document as a string.
    """
    history = data.get("history", [])
    title_prefix = html.escape(skill_name + " \u2014 ") if skill_name else ""

    train_queries: list[dict] = []
    test_queries: list[dict] = []
    if history:
        train_queries.extend(
            {"query": r["query"], "should_trigger": r.get("should_trigger", True)}
            for r in history[0].get("train_results", history[0].get("results", []))
        )
        if history[0].get("test_results"):
            test_queries.extend(
                {"query": r["query"], "should_trigger": r.get("should_trigger", True)}
                for r in history[0].get("test_results", [])
            )

    refresh_tag = '    <meta http-equiv="refresh" content="5">\n' if auto_refresh else ""
    best_test_score = data.get("best_test_score")

    html_parts = [_build_html_header(title_prefix, refresh_tag)]
    html_parts.extend([
        _build_summary_section(data, best_test_score),
        """
    <div class="legend">
        <span style="font-weight:600">Query columns:</span>
        <span class="legend-item"><span class="legend-swatch swatch-positive"></span> Should trigger</span>
        <span class="legend-item"><span class="legend-swatch swatch-negative"></span> Should NOT trigger</span>
        <span class="legend-item"><span class="legend-swatch swatch-train"></span> Train</span>
        <span class="legend-item"><span class="legend-swatch swatch-test"></span> Test</span>
    </div>
""",
        """
    <div class="table-container">
    <table>
        <thead>
            <tr>
                <th>Iter</th>
                <th>Train</th>
                <th>Test</th>
                <th class="query-col">Description</th>
""",
    ])

    html_parts.extend(_build_table_header_cols(train_queries, test_queries))

    html_parts.append("""            </tr>
        </thead>
        <tbody>
""")

    if test_queries:
        best_iter = max(history, key=lambda h: h.get("test_passed") or 0).get("iteration")
    else:
        best_iter = max(history, key=lambda h: h.get("train_passed", h.get("passed", 0))).get("iteration")

    for h in history:
        html_parts.extend(_build_iteration_row(h, train_queries, test_queries, best_iter))

    html_parts.extend(("""        </tbody>\n    </table>\n    </div>\n""", """\n</body>\n</html>\n"""))

    return "".join(html_parts)


def main() -> None:
    """Parse arguments, load JSON input, and write the HTML report."""
    parser = argparse.ArgumentParser(description="Generate HTML report from run_loop output")
    parser.add_argument("input", help="Path to JSON output from run_loop.py (or - for stdin)")
    parser.add_argument("-o", "--output", default=None, help="Output HTML file (default: stdout)")
    parser.add_argument("--skill-name", default="", help="Skill name to include in the report title")
    args = parser.parse_args()

    data = json.load(sys.stdin) if args.input == "-" else json.loads(Path(args.input).read_text(encoding="utf-8"))

    html_output = generate_html(data, skill_name=args.skill_name)

    if args.output:
        Path(args.output).write_text(html_output, encoding="utf-8")
        print(f"Report written to {args.output}", file=sys.stderr)
    else:
        print(html_output)


if __name__ == "__main__":
    main()
