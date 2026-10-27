"""Unit tests for live stream probe helpers (no network)."""

from __future__ import annotations

import asyncio
import functools
import inspect
from typing import Callable, Dict, Optional
from unittest.mock import AsyncMock, patch

import alpaca.common.utils as alpaca_utils
from alpaca.data.live import websocket as data_ws
from tests.live.streaming import StreamProbeResult, probe_stream, stream_timeout_seconds

CONNECT_PATH = "alpaca.data.live.websocket.websockets.connect"


def test_stream_timeout_seconds_default(monkeypatch):
    monkeypatch.delenv("ALPACA_LIVE_STREAM_TIMEOUT", raising=False)
    assert stream_timeout_seconds(12.0) == 12.0


def test_stream_timeout_seconds_env(monkeypatch):
    monkeypatch.setenv("ALPACA_LIVE_STREAM_TIMEOUT", "7.5")
    assert stream_timeout_seconds() == 7.5


def test_stream_probe_result_shapes():
    result = StreamProbeResult(
        url="wss://example/stream",
        headers={"User-Agent": "APCA-PY/1.0"},
        connected=True,
        messages=[{"T": "q", "S": "SPY"}],
    )
    assert result.as_request()["method"] == "WS"
    assert result.as_request()["url"] == "wss://example/stream"
    assert result.as_request()["headers"]["User-Agent"] == "APCA-PY/1.0"
    body = result.as_response_body()
    assert body["connected"] is True
    assert body["message_count"] == 1
    assert body["messages"][0]["S"] == "SPY"


class _FakeStream:
    """Minimal stand-in that uses the same connect symbol DataStream patches."""

    def __init__(self) -> None:
        self._running = False
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._handler: Optional[Callable] = None
        self.stop_calls = 0

    def subscribe(self, handler: Callable) -> None:
        self._handler = handler

    async def stop_ws(self) -> None:
        self._running = False

    def stop(self) -> None:
        self.stop_calls += 1
        self._running = False

    def run(self) -> None:
        async def _run() -> None:
            self._loop = asyncio.get_running_loop()
            await data_ws.websockets.connect(
                "wss://example.test/v2/iex",
                extra_headers={"User-Agent": "test-ua"},
            )
            self._running = True
            if self._handler:
                await self._handler({"T": "q", "S": "SPY"})
            while self._running:
                await asyncio.sleep(0.01)

        asyncio.run(_run())


def test_probe_stream_captures_headers_and_message():
    stream = _FakeStream()
    fake_ws = AsyncMock()

    async def fake_network_connect(uri, *args, **kwargs):
        return fake_ws

    with patch(
        "tests.live.streaming.websockets.connect",
        new=fake_network_connect,
    ):
        result = probe_stream(
            stream,
            subscribe=lambda s, h: s.subscribe(h),
            connect_path=CONNECT_PATH,
            timeout=5,
            min_messages=1,
            require_message=True,
        )

    assert result.error is None
    assert result.connected is True
    assert result.url == "wss://example.test/v2/iex"
    assert result.headers["User-Agent"] == "test-ua"
    assert len(result.messages) == 1
    assert stream.stop_calls >= 1 or not stream._running


def test_probe_stream_connect_wrapper_preserves_header_key_detection(monkeypatch):
    """Regression: capturing_connect must not poison get_websocket_headers_key.

    probe_stream swaps in ``capturing_connect`` for ``websockets.connect``
    while the stream runs. ``get_websocket_headers_key()`` caches its result
    process-wide the first time it's called, based on
    ``inspect.signature(websockets.connect)``. If the installed wrapper only
    exposes ``(uri, *args, **kwargs)`` instead of mirroring the real
    ``connect`` signature, the very first call made while the probe is active
    would permanently cache the wrong header kwarg name (``extra_headers``
    instead of ``additional_headers`` on modern ``websockets`` versions),
    breaking every subsequent live connection.
    """
    real_connect = data_ws.websockets.connect
    expected_key = (
        "additional_headers"
        if "additional_headers" in inspect.signature(real_connect).parameters
        else "extra_headers"
    )

    fake_ws = AsyncMock()

    # Stand in for the network layer without actually connecting, but keep
    # the real signature intact (as the production websockets.connect would)
    # so this test actually exercises capturing_connect's own wrapping.
    @functools.wraps(real_connect)
    async def fake_network_connect(uri, *args, **kwargs):
        return fake_ws

    captured_key: Dict[str, str] = {}

    class _HeaderCheckingStream(_FakeStream):
        def run(self) -> None:
            async def _run() -> None:
                self._loop = asyncio.get_running_loop()
                # Resolve the header kwarg name for the first time ever,
                # while websockets.connect has been replaced by
                # probe_stream's capturing_connect wrapper.
                captured_key["value"] = alpaca_utils.get_websocket_headers_key()
                await data_ws.websockets.connect(
                    "wss://example.test/v2/iex",
                    **{captured_key["value"]: {"User-Agent": "test-ua"}},
                )
                self._running = True
                if self._handler:
                    await self._handler({"T": "q", "S": "SPY"})
                while self._running:
                    await asyncio.sleep(0.01)

            asyncio.run(_run())

    # Force the "first call ever" path regardless of test execution order.
    monkeypatch.setattr(alpaca_utils, "_WS_HEADERS_KEY", None)

    stream = _HeaderCheckingStream()
    with patch(
        "tests.live.streaming.websockets.connect",
        new=fake_network_connect,
    ):
        result = probe_stream(
            stream,
            subscribe=lambda s, h: s.subscribe(h),
            connect_path=CONNECT_PATH,
            timeout=5,
            min_messages=1,
            require_message=True,
        )

    assert result.error is None
    assert captured_key.get("value") == expected_key


def test_probe_stream_require_message_timeout():
    stream = _FakeStream()

    def quiet_run() -> None:
        async def _run() -> None:
            stream._loop = asyncio.get_running_loop()
            await data_ws.websockets.connect(
                "wss://example.test/v2/iex",
                extra_headers={"User-Agent": "test-ua"},
            )
            stream._running = True
            while stream._running:
                await asyncio.sleep(0.01)

        asyncio.run(_run())

    stream.run = quiet_run  # type: ignore[method-assign]
    fake_ws = AsyncMock()

    async def fake_network_connect(uri, *args, **kwargs):
        return fake_ws

    with patch(
        "tests.live.streaming.websockets.connect",
        new=fake_network_connect,
    ):
        result = probe_stream(
            stream,
            subscribe=lambda s, h: None,
            connect_path=CONNECT_PATH,
            timeout=0.3,
            require_message=True,
        )

    assert result.connected is True
    assert result.error is not None
    assert "expected at least 1 message" in result.error
