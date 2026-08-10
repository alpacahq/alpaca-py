"""Helpers for opt-in live WebSocket stream smoke probes."""

from __future__ import annotations

import os
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional
from unittest.mock import patch

from websockets.legacy import client as websockets_legacy

from tests.live.recording import serialize_response

SubscribeFn = Callable[[Any, Callable], None]


def stream_timeout_seconds(default: float = 30.0) -> float:
    raw = os.getenv("ALPACA_LIVE_STREAM_TIMEOUT", "").strip()
    if not raw:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


@dataclass
class StreamProbeResult:
    """Outcome of a short live stream connect/subscribe/receive cycle."""

    url: Optional[str] = None
    headers: Dict[str, Any] = field(default_factory=dict)
    connected: bool = False
    messages: List[Any] = field(default_factory=list)
    error: Optional[str] = None

    def as_request(self) -> Dict[str, Any]:
        return {
            "method": "WS",
            "url": self.url,
            "headers": dict(self.headers),
            "body": None,
        }

    def as_response_body(self, *, max_messages: int = 3) -> Dict[str, Any]:
        samples = [serialize_response(m) for m in self.messages[:max_messages]]
        return {
            "connected": self.connected,
            "message_count": len(self.messages),
            "messages": samples,
        }


def probe_stream(
    stream: Any,
    *,
    subscribe: SubscribeFn,
    connect_path: str,
    timeout: Optional[float] = None,
    min_messages: int = 1,
    require_message: bool = True,
) -> StreamProbeResult:
    """Connect a stream briefly, optionally wait for messages, then disconnect.

    Patches ``websockets_legacy.connect`` at ``connect_path`` so the live
    User-Agent / URL are captured while still performing a real handshake.
    """
    timeout = stream_timeout_seconds() if timeout is None else timeout
    result = StreamProbeResult()
    real_connect = websockets_legacy.connect
    got_enough = threading.Event()
    stop_lock = threading.Lock()
    stopped = False

    async def capturing_connect(uri: Any, *args: Any, **kwargs: Any) -> Any:
        # str(Enum) can print "BaseURL.X"; prefer the URL value when present.
        result.url = getattr(uri, "value", None) or str(uri)
        result.headers = dict(kwargs.get("extra_headers") or {})
        ws = await real_connect(uri, *args, **kwargs)
        result.connected = True
        return ws

    async def handler(data: Any) -> None:
        result.messages.append(data)
        if len(result.messages) >= min_messages:
            got_enough.set()
            await _safe_stop_ws(stream)

    def stop_stream() -> None:
        nonlocal stopped
        with stop_lock:
            if stopped:
                return
            stopped = True
        try:
            if getattr(stream, "_loop", None) is not None:
                stream.stop()
        except Exception as exc:  # noqa: BLE001 — probe must always unwind
            if result.error is None:
                result.error = f"{type(exc).__name__}: {exc}"

    def runner() -> None:
        try:
            with patch(connect_path, new=capturing_connect):
                stream.run()
        except Exception as exc:  # noqa: BLE001
            result.error = f"{type(exc).__name__}: {exc}"
        finally:
            got_enough.set()

    subscribe(stream, handler)
    thread = threading.Thread(target=runner, name="live-stream-probe", daemon=True)
    thread.start()

    deadline = time.monotonic() + timeout
    # Wait until websocket is up (auth completed → _running) or timeout.
    while time.monotonic() < deadline and not result.error:
        if result.connected and getattr(stream, "_running", False):
            break
        if got_enough.is_set() and result.messages:
            break
        time.sleep(0.05)

    if require_message:
        remaining = max(0.0, deadline - time.monotonic())
        got_enough.wait(timeout=remaining)
    else:
        # Brief soak so auth + subscribe have time to complete.
        soak = min(2.0, max(0.0, deadline - time.monotonic()))
        if soak:
            time.sleep(soak)

    stop_stream()
    thread.join(timeout=10.0)

    if thread.is_alive():
        result.error = result.error or "stream thread did not exit after stop"
    elif require_message and len(result.messages) < min_messages and not result.error:
        result.error = (
            f"expected at least {min_messages} message(s) within {timeout}s, "
            f"got {len(result.messages)}"
        )
    elif not result.connected and not result.error:
        result.error = "websocket did not connect before timeout"

    return result


async def _safe_stop_ws(stream: Any) -> None:
    stop_ws = getattr(stream, "stop_ws", None)
    if stop_ws is None:
        return
    await stop_ws()
