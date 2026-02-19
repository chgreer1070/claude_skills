"""Panel (HoloViz) dashboard for sentiment analysis visualization.

Provides an interactive web dashboard that visualizes VADER sentiment
scores produced by the ``sentiment-score.py`` script. The dashboard
runs as a daemon thread inside the MCP server process and auto-refreshes
when the source CSV changes.

Dashboard views:
    Session Timeline - Compound score per message over time, colored by session.
    Session Heatmap  - Per-session message indices colored by compound score.
    Distribution     - Histogram of compound scores with mean/median lines.
    Hot Spots        - Table of the most negative messages (compound < -0.5).
"""

from __future__ import annotations

import logging
import threading
from pathlib import Path

import holoviews as hv  # ty: ignore[unresolved-import]
import hvplot.pandas  # noqa: F401  # ty: ignore[unresolved-import]
import pandas as pd
import panel as pn  # ty: ignore[unresolved-import]

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_CSV_COLUMNS: list[str] = [
    "session_id",
    "timestamp",
    "message_index",
    "compound",
    "positive",
    "negative",
    "neutral",
    "message_length",
    "message_preview",
]
_HOTSPOT_THRESHOLD: float = -0.5
_REFRESH_INTERVAL_MS: int = 5000
_SCORE_MIN: float = -1.0
_SCORE_MAX: float = 1.0
_PREVIEW_TRUNCATE: int = 80
_HISTOGRAM_BINS: int = 30


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------


def _load_sentiment_data(csv_path: Path) -> pd.DataFrame | None:
    """Load sentiment CSV into a DataFrame, returning None if unavailable.

    Parses the ``timestamp`` column as datetime and coerces numeric columns.
    Returns ``None`` when the file does not exist or is empty.

    Args:
        csv_path: Absolute path to the sentiment CSV file.

    Returns:
        A DataFrame with parsed columns, or ``None`` if the file is missing
        or contains no data rows.
    """
    if not csv_path.exists():
        return None

    try:
        df = pd.read_csv(csv_path)
    except (pd.errors.EmptyDataError, pd.errors.ParserError):
        return None

    if df.empty:
        return None

    # Coerce types
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    for col in ("compound", "positive", "negative", "neutral"):
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["message_index"] = pd.to_numeric(df["message_index"], errors="coerce").astype(
        "Int64"
    )
    df["message_length"] = pd.to_numeric(df["message_length"], errors="coerce").astype(
        "Int64"
    )

    # Drop rows where critical columns are NaN
    df = df.dropna(subset=["compound", "session_id"])
    return df if not df.empty else None


# ---------------------------------------------------------------------------
# Dashboard views
# ---------------------------------------------------------------------------


def _build_placeholder(csv_path: Path) -> pn.pane.Markdown:
    """Build a placeholder pane shown when sentiment data is unavailable.

    Args:
        csv_path: The path where the CSV is expected.

    Returns:
        A Markdown pane with instructions for the user.
    """
    return pn.pane.Markdown(
        f"""
## No Sentiment Data Available

The sentiment CSV was not found at:

```
{csv_path}
```

**To generate it**, run the sentiment scoring script:

```bash
uv run scripts/sentiment-score.py --output {csv_path}
```

The dashboard will automatically pick up the data once the file exists.
""",
        sizing_mode="stretch_width",
    )


def _build_timeline(df: pd.DataFrame) -> pn.pane.HoloViews:
    """Build the Session Timeline scatter plot.

    Plots compound sentiment score per message over time, with each
    session rendered in a distinct color. Hover tooltips show the
    message preview.

    Args:
        df: Sentiment DataFrame with columns ``timestamp``, ``compound``,
            ``session_id``, and ``message_preview``.

    Returns:
        A HoloViews pane containing the interactive scatter plot.
    """
    # Truncate previews for tooltip readability
    plot_df = df.copy()
    plot_df["preview"] = plot_df["message_preview"].str[:_PREVIEW_TRUNCATE]

    scatter = plot_df.hvplot.scatter(
        x="timestamp",
        y="compound",
        by="session_id",
        hover_cols=["preview", "message_index"],
        title="Compound Sentiment Score Over Time",
        xlabel="Timestamp",
        ylabel="Compound Score",
        ylim=(_SCORE_MIN, _SCORE_MAX),
        height=450,
        responsive=True,
        legend="bottom",
    )

    # Add a zero reference line
    zero_line = hv.HLine(0).opts(color="gray", line_dash="dashed", line_width=1)

    return pn.pane.HoloViews(scatter * zero_line, sizing_mode="stretch_width")


def _build_heatmap(df: pd.DataFrame) -> pn.pane.HoloViews:
    """Build the Session Heatmap.

    Creates a heatmap with one row per session and columns as message
    indices. Color intensity represents the compound sentiment score,
    making it easy to spot sessions with sentiment drops.

    Args:
        df: Sentiment DataFrame with columns ``session_id``,
            ``message_index``, and ``compound``.

    Returns:
        A HoloViews pane containing the heatmap.
    """
    # Shorten session IDs for display (last 8 chars)
    plot_df = df.copy()
    plot_df["session_short"] = plot_df["session_id"].str[-8:]

    heatmap = plot_df.hvplot.heatmap(
        x="message_index",
        y="session_short",
        C="compound",
        cmap="RdYlGn",
        clim=(_SCORE_MIN, _SCORE_MAX),
        title="Sentiment by Session and Message Index",
        xlabel="Message Index",
        ylabel="Session (last 8 chars)",
        height=max(300, len(plot_df["session_id"].unique()) * 25 + 100),
        responsive=True,
        colorbar=True,
    )

    return pn.pane.HoloViews(heatmap, sizing_mode="stretch_width")


def _build_distribution(df: pd.DataFrame) -> pn.pane.HoloViews:
    """Build the compound score distribution histogram.

    Shows a histogram of all compound scores with vertical lines for
    the mean and median values.

    Args:
        df: Sentiment DataFrame with a ``compound`` column.

    Returns:
        A HoloViews pane containing the histogram with annotation lines.
    """
    hist = df.hvplot.hist(
        y="compound",
        bins=_HISTOGRAM_BINS,
        title="Distribution of Compound Sentiment Scores",
        xlabel="Compound Score",
        ylabel="Count",
        color="#4c78a8",
        height=400,
        responsive=True,
    )

    mean_val = float(df["compound"].mean())
    median_val = float(df["compound"].median())

    mean_line = hv.VLine(mean_val).opts(color="red", line_dash="dashed", line_width=2)
    median_line = hv.VLine(median_val).opts(
        color="orange", line_dash="dotted", line_width=2
    )

    # Labels for the lines
    mean_label = hv.Text(
        mean_val, 0, f"Mean: {mean_val:.3f}", halign="left", fontsize=9
    ).opts(color="red")
    median_label = hv.Text(
        median_val, 0, f"Median: {median_val:.3f}", halign="right", fontsize=9
    ).opts(color="orange")

    overlay = hist * mean_line * median_line * mean_label * median_label
    return pn.pane.HoloViews(overlay, sizing_mode="stretch_width")


def _build_hotspots(df: pd.DataFrame) -> pn.pane.Perspective | pn.widgets.Tabulator:
    """Build the Hot Spots table of most negative messages.

    Filters messages with compound score below the threshold and displays
    them sorted by compound ascending (most negative first).

    Args:
        df: Sentiment DataFrame.

    Returns:
        A Tabulator widget showing the hot spot messages.
    """
    hotspots = (
        df
        .loc[
            df["compound"] < _HOTSPOT_THRESHOLD,
            ["session_id", "timestamp", "compound", "message_preview"],
        ]
        .sort_values("compound", ascending=True)
        .reset_index(drop=True)
    )

    if hotspots.empty:
        return pn.pane.Markdown(
            "**No hot spots found.** All messages have compound scores "
            f">= {_HOTSPOT_THRESHOLD}.",
            sizing_mode="stretch_width",
        )

    # Format compound for display
    hotspots["compound"] = hotspots["compound"].round(4)

    return pn.widgets.Tabulator(
        hotspots,
        sizing_mode="stretch_width",
        height=500,
        show_index=False,
        frozen_columns=["session_id"],
        text_align={"compound": "right"},
        titles={
            "session_id": "Session ID",
            "timestamp": "Timestamp",
            "compound": "Compound",
            "message_preview": "Message Preview",
        },
    )


# ---------------------------------------------------------------------------
# Dashboard assembly
# ---------------------------------------------------------------------------


def _build_dashboard(csv_path: Path) -> pn.Tabs:
    """Assemble the full dashboard with all four views.

    Reads the CSV and builds each tab. If the CSV is missing, returns
    a placeholder tab with instructions.

    Args:
        csv_path: Path to the sentiment CSV file.

    Returns:
        A Panel Tabs component containing all dashboard views.
    """
    df = _load_sentiment_data(csv_path)

    if df is None:
        return pn.Tabs(("Overview", _build_placeholder(csv_path)), dynamic=True)

    return pn.Tabs(
        ("Session Timeline", _build_timeline(df)),
        ("Session Heatmap", _build_heatmap(df)),
        ("Distribution", _build_distribution(df)),
        ("Hot Spots", _build_hotspots(df)),
        dynamic=True,
    )


def _create_app(csv_path: Path) -> pn.template.FastListTemplate:
    """Create the Panel application with auto-refresh capability.

    Uses a periodic callback to reload the CSV and rebuild the dashboard
    views when the file changes on disk.

    Args:
        csv_path: Path to the sentiment CSV file.

    Returns:
        A Panel FastListTemplate ready to be served.
    """
    hv.extension("bokeh")

    # Track file modification time for change detection
    state: dict[str, float] = {"last_mtime": 0.0}

    dashboard_container = pn.Column(
        _build_dashboard(csv_path), sizing_mode="stretch_width"
    )

    def _refresh() -> None:
        """Check if the CSV has changed and rebuild the dashboard if so."""
        try:
            current_mtime = csv_path.stat().st_mtime if csv_path.exists() else 0.0
        except OSError:
            current_mtime = 0.0

        if current_mtime != state["last_mtime"]:
            state["last_mtime"] = current_mtime
            dashboard_container.objects = [_build_dashboard(csv_path)]

    # Register periodic callback for auto-refresh
    pn.state.add_periodic_callback(_refresh, period=_REFRESH_INTERVAL_MS)

    return pn.template.FastListTemplate(
        title="Kaizen Sentiment Dashboard",
        main=[dashboard_container],
        accent="#4c78a8",
        main_layout=None,
        theme="default",
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def start_dashboard(
    csv_path: Path | None = None, port: int = 5006
) -> threading.Thread | None:
    """Start the Panel dashboard server in a daemon thread.

    Launches the dashboard on ``localhost:{port}`` in a background thread
    so that the MCP server can continue its normal startup. The dashboard
    auto-refreshes when the underlying CSV file changes.

    Args:
        csv_path: Path to the sentiment CSV. Defaults to
            ``~/.claude/kaizen/sentiment.csv``.
        port: TCP port for the dashboard server. Defaults to ``5006``.

    Returns:
        The daemon ``threading.Thread`` running the server, or ``None``
        if the server failed to start.
    """
    resolved_path = (csv_path or Path("~/.claude/kaizen/sentiment.csv")).expanduser()

    def _serve() -> None:
        """Target function for the daemon thread."""
        try:
            app = _create_app(resolved_path)
            pn.serve(
                {"/": app},
                port=port,
                address="localhost",
                show=False,
                start=True,
                threaded=False,
                verbose=False,
            )
        except OSError as exc:
            logger.warning("Dashboard server failed to start: %s", exc)
        except Exception:
            logger.exception("Unexpected error in dashboard server")

    thread = threading.Thread(target=_serve, name="kaizen-dashboard", daemon=True)
    thread.start()
    logger.info("Sentiment dashboard starting on http://localhost:%d/", port)
    return thread
