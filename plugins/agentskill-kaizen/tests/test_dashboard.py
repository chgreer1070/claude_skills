"""Test suite for dashboard.py — port allocation, health endpoint, state management.

Tests cover:
- get_dashboard_url() public accessor
- HealthHandler Tornado request handler
- _reset_dashboard_state() state cleanup
- _allocate_port() OS port allocation
- start_dashboard() integration (mock-based, no real server)

Strategy:
    Heavy third-party dependencies (panel, holoviews, hvplot, tornado) are
    stubbed at the module level before ``dashboard`` is imported.  This
    allows the test suite to exercise the port allocation, state management,
    health endpoint, and start_dashboard logic without requiring a live
    Panel/Bokeh server.
"""

from __future__ import annotations

import json
import os
import sys
import time
import types
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Stub third-party modules that are not installed in the test venv.
# Must happen before ``import dashboard``.
# ---------------------------------------------------------------------------

# --- tornado stubs ---
_tornado_mod = types.ModuleType("tornado")
_tornado_web_mod = types.ModuleType("tornado.web")


class _StubRequestHandler:
    """Minimal tornado.web.RequestHandler stand-in for testing."""

    def __init__(self, *args: object, **kwargs: object) -> None:
        self._headers: dict[str, str] = {}
        self._body: str = ""

    def set_header(self, name: str, value: str) -> None:
        self._headers[name] = value

    def write(self, chunk: str | bytes) -> None:
        if isinstance(chunk, bytes):
            chunk = chunk.decode("utf-8")
        self._body += chunk

    def initialize(self, **kwargs: object) -> None:
        pass


_tornado_web_mod.RequestHandler = _StubRequestHandler
_tornado_mod.web = _tornado_web_mod

# --- holoviews stubs ---
_hv_mod = types.ModuleType("holoviews")
_hv_mod.extension = MagicMock()
_hv_mod.HLine = MagicMock()
_hv_mod.VLine = MagicMock()
_hv_mod.Text = MagicMock()

# --- hvplot stubs ---
_hvplot_mod = types.ModuleType("hvplot")
_hvplot_pandas_mod = types.ModuleType("hvplot.pandas")
_hvplot_mod.pandas = _hvplot_pandas_mod

# --- panel stubs ---
_pn_mod = types.ModuleType("panel")
_pn_mod.serve = MagicMock()
_pn_mod.Tabs = MagicMock()
_pn_mod.Column = MagicMock()

_pn_pane = types.ModuleType("panel.pane")
_pn_pane.Markdown = MagicMock()
_pn_pane.HoloViews = MagicMock()
_pn_mod.pane = _pn_pane

_pn_widgets = types.ModuleType("panel.widgets")
_pn_widgets.Tabulator = MagicMock()
_pn_mod.widgets = _pn_widgets

_pn_state = MagicMock()
_pn_state.add_periodic_callback = MagicMock()
_pn_state.onload = MagicMock()
_pn_mod.state = _pn_state

_pn_template = types.ModuleType("panel.template")
_pn_template.FastListTemplate = MagicMock()
_pn_mod.template = _pn_template

# Install stubs into sys.modules
sys.modules["tornado"] = _tornado_mod
sys.modules["tornado.web"] = _tornado_web_mod
sys.modules["holoviews"] = _hv_mod
sys.modules["hvplot"] = _hvplot_mod
sys.modules["hvplot.pandas"] = _hvplot_pandas_mod
sys.modules["panel"] = _pn_mod
sys.modules["panel.pane"] = _pn_pane
sys.modules["panel.widgets"] = _pn_widgets
sys.modules["panel.template"] = _pn_template

# Add mcp/ to sys.path so ``import dashboard`` resolves
_MCP_DIR = str(Path(__file__).resolve().parent.parent / "mcp")
if _MCP_DIR not in sys.path:
    sys.path.insert(0, _MCP_DIR)

import dashboard  # noqa: E402

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _reset_module_state() -> Any:
    """Reset dashboard module-level state before and after every test.

    Ensures complete test isolation — no state leaks between tests.
    """
    dashboard._reset_dashboard_state()
    yield
    dashboard._reset_dashboard_state()


# ===================================================================
# Unit Tests: get_dashboard_url()
# ===================================================================


class TestGetDashboardUrl:
    """Tests for get_dashboard_url() public accessor."""

    def test_get_dashboard_url_when_port_is_none(self) -> None:
        """get_dashboard_url() returns None when _dashboard_port is None.

        Tests: Public accessor returns None when no dashboard is running.
        How: Ensure _dashboard_port is None (default state), call accessor.
        Why: MCP tool must detect when dashboard is not running.
        """
        # Arrange — state is already None from autouse fixture

        # Act
        result = dashboard.get_dashboard_url()

        # Assert
        assert result is None

    def test_get_dashboard_url_when_port_is_set(self) -> None:
        """get_dashboard_url() returns correct URL when _dashboard_port is set.

        Tests: Public accessor returns formatted URL string.
        How: Set _dashboard_port to a known value, call accessor.
        Why: MCP tool needs the correct URL to open in the browser.
        """
        # Arrange
        dashboard._dashboard_port = 49152

        # Act
        result = dashboard.get_dashboard_url()

        # Assert
        assert result == "http://localhost:49152/"


# ===================================================================
# Unit Tests: HealthHandler
# ===================================================================


class TestHealthHandler:
    """Tests for HealthHandler Tornado RequestHandler.

    Uses mock-based testing — constructs HealthHandler instances with
    lambda accessors and calls get() directly.  No real Tornado event
    loop or HTTP server is started.
    """

    def _make_handler(
        self,
        *,
        port: int | None = 8080,
        start_time: float | None = None,
        csv_path: Path | None = None,
        csv_rows: int | None = None,
    ) -> dashboard.HealthHandler:
        """Create a HealthHandler with given state accessors.

        Returns an initialised handler instance ready for get() calls.
        """
        handler = dashboard.HealthHandler.__new__(dashboard.HealthHandler)
        # Initialise the stub base class attributes
        handler._headers = {}
        handler._body = ""
        # Call initialize with lambda accessors
        handler.initialize(
            get_port=lambda: port,
            get_start_time=lambda: start_time,
            get_csv_path=lambda: csv_path,
            get_csv_rows=lambda: csv_rows,
        )
        return handler

    def test_health_handler_get_with_all_state(self, tmp_path: Path) -> None:
        """HealthHandler.get() returns 200 with all 7 JSON fields populated.

        Tests: Health endpoint returns complete JSON response.
        How: Create handler with all state set, including an existing CSV file.
        Why: Monitoring tools rely on all fields being present.
        """
        # Arrange
        csv_file = tmp_path / "sentiment.csv"
        csv_file.write_text("header\nrow1\n", encoding="utf-8")
        start_time = time.monotonic() - 10.0
        handler = self._make_handler(
            port=49152, start_time=start_time, csv_path=csv_file, csv_rows=42
        )

        # Act
        handler.get()

        # Assert
        assert handler._headers["Content-Type"] == "application/json"
        body = json.loads(handler._body)
        assert body["status"] == "ok"
        assert body["port"] == 49152
        assert body["pid"] == os.getpid()
        assert body["csv_path"] == str(csv_file)
        assert body["csv_exists"] is True
        assert body["csv_rows"] == 42
        assert body["uptime_seconds"] > 0

        # Verify all 7 fields are present
        expected_fields = {
            "status",
            "port",
            "pid",
            "csv_path",
            "csv_exists",
            "csv_rows",
            "uptime_seconds",
        }
        assert set(body.keys()) == expected_fields

    def test_health_handler_get_csv_missing(self, tmp_path: Path) -> None:
        """HealthHandler.get() returns 200 with csv_exists=false, csv_rows=null when CSV is missing.

        Tests: Health endpoint handles missing CSV gracefully.
        How: Point csv_path to a non-existent file, set csv_rows to None.
        Why: Dashboard is healthy even if CSV data has not been generated yet.
        """
        # Arrange
        missing_csv = tmp_path / "nonexistent.csv"
        handler = self._make_handler(
            port=49152, start_time=time.monotonic(), csv_path=missing_csv, csv_rows=None
        )

        # Act
        handler.get()

        # Assert
        body = json.loads(handler._body)
        assert body["status"] == "ok"
        assert body["csv_exists"] is False
        assert body["csv_rows"] is None

    def test_health_handler_uptime_calculation(self) -> None:
        """HealthHandler.get() returns positive uptime_seconds.

        Tests: Uptime is calculated as monotonic delta.
        How: Set start_time to a past monotonic value, verify uptime > 0.
        Why: Uptime must reflect actual dashboard running time.
        """
        # Arrange
        past_time = time.monotonic() - 5.0
        handler = self._make_handler(
            port=8080, start_time=past_time, csv_path=None, csv_rows=None
        )

        # Act
        handler.get()

        # Assert
        body = json.loads(handler._body)
        assert body["uptime_seconds"] >= 4.0
        assert body["uptime_seconds"] < 60.0  # Sanity upper bound


# ===================================================================
# Unit Tests: _reset_dashboard_state()
# ===================================================================


class TestResetDashboardState:
    """Tests for _reset_dashboard_state() state cleanup."""

    def test_reset_dashboard_state(self) -> None:
        """_reset_dashboard_state() sets all 4 module-level variables to None.

        Tests: State reset function clears all dashboard state.
        How: Set all state variables to non-None values, call reset, verify all None.
        Why: After dashboard crash, state must be clean so get_dashboard_url() returns None.
        """
        # Arrange
        dashboard._dashboard_port = 12345
        dashboard._dashboard_start_time = 1000.0
        dashboard._dashboard_csv_path = Path("/tmp/test.csv")
        dashboard._dashboard_csv_rows = 100

        # Act
        dashboard._reset_dashboard_state()

        # Assert
        assert dashboard._dashboard_port is None
        assert dashboard._dashboard_start_time is None
        assert dashboard._dashboard_csv_path is None
        assert dashboard._dashboard_csv_rows is None


# ===================================================================
# Unit Tests: _allocate_port()
# ===================================================================


class TestAllocatePort:
    """Tests for _allocate_port() OS port allocation."""

    def test_allocate_port_returns_valid_port(self) -> None:
        """_allocate_port() returns a port > 0 and < 65536.

        Tests: Port allocation returns a valid ephemeral port.
        How: Call _allocate_port() and verify the returned value is in range.
        Why: Port must be a valid TCP port number for pn.serve() to bind.
        """
        # Arrange — no setup needed

        # Act
        port = dashboard._allocate_port()

        # Assert
        assert isinstance(port, int)
        assert port > 0
        assert port < 65536


# ===================================================================
# Integration Tests: start_dashboard()
# ===================================================================


class TestStartDashboard:
    """Integration tests for start_dashboard() orchestration.

    All tests mock pn.serve and threading.Thread.start to avoid
    starting a real Panel/Bokeh server.  Module-level state is
    verified after each call.
    """

    @patch.object(dashboard.threading.Thread, "start")
    @patch.object(dashboard, "_allocate_port", return_value=55555)
    def test_start_dashboard_called_once(
        self, mock_allocate: MagicMock, mock_thread_start: MagicMock, tmp_path: Path
    ) -> None:
        """start_dashboard() sets module state, returns thread, thread is daemon.

        Tests: First call to start_dashboard sets up everything correctly.
        How: Mock port allocation and thread start, call start_dashboard().
        Why: Module state must be set before thread starts so get_dashboard_url()
             returns a valid URL immediately.
        """
        # Arrange
        csv_file = tmp_path / "sentiment.csv"
        csv_file.write_text(
            "session_id,timestamp,message_index,compound,positive,negative,neutral,message_length,message_preview\n",
            encoding="utf-8",
        )

        # Act
        result = dashboard.start_dashboard(csv_path=csv_file)

        # Assert
        assert result is not None
        assert isinstance(result, dashboard.threading.Thread)
        assert result.daemon is True
        assert result.name == "kaizen-dashboard"
        assert dashboard._dashboard_port == 55555
        assert dashboard._dashboard_start_time is not None
        assert dashboard._dashboard_csv_path == csv_file
        mock_allocate.assert_called_once()
        mock_thread_start.assert_called_once()

    @patch.object(dashboard.threading.Thread, "start")
    @patch.object(dashboard, "_allocate_port", return_value=55555)
    def test_start_dashboard_called_twice(
        self, mock_allocate: MagicMock, mock_thread_start: MagicMock
    ) -> None:
        """Second call to start_dashboard() returns None, no new thread started.

        Tests: Within-process guard prevents duplicate dashboard instances.
        How: Call start_dashboard() twice, verify second returns None.
        Why: Each process should have at most one dashboard instance.
        """
        # Arrange — first call
        first_result = dashboard.start_dashboard()
        assert first_result is not None

        # Act — second call
        second_result = dashboard.start_dashboard()

        # Assert
        assert second_result is None
        # _allocate_port should only be called once (first invocation)
        mock_allocate.assert_called_once()

    @patch.object(dashboard, "_allocate_port", side_effect=OSError("bind failed"))
    def test_start_dashboard_port_allocation_failure(
        self, mock_allocate: MagicMock
    ) -> None:
        """start_dashboard() returns None on OSError from _allocate_port().

        Tests: Port allocation failure is handled gracefully.
        How: Mock _allocate_port to raise OSError, verify None return.
        Why: Network issues should not crash the MCP server process.
        """
        # Arrange — mock already set up via decorator

        # Act
        result = dashboard.start_dashboard()

        # Assert
        assert result is None
        assert dashboard._dashboard_port is None
        assert dashboard._dashboard_start_time is None
        assert dashboard._dashboard_csv_path is None
        assert dashboard._dashboard_csv_rows is None
