"""Local-server coverage for the modern websockets.connect migration (#743, #838).

#838 kept ``websockets.connect`` (not the explicit asyncio client import) and
picks the header kwarg name at runtime via ``get_websocket_headers_key``, so
the existing mocked tests in tests/data/test_websockets.py and
tests/trading/test_trading_stream.py only assert on the kwargs passed to the
patched ``connect``. These tests instead run a real local handshake end to
end, the same gap flagged in #795's review: connect, auth, and subscribe
should actually round-trip through a socket, and the stream's event
dispatch should actually deliver a message to a handler.
"""

import asyncio
import json
import sys

import msgpack
import pytest

from alpaca.common.utils import get_default_user_agent
from alpaca.data.live.websocket import DataStream
from alpaca.trading.stream import TradingStream

# ``websockets.asyncio.server`` needs websockets>=13, but pyproject.toml still
# allows websockets>=10.4. Import it defensively so only the two tests below
# that need a local server are skipped on older versions -- not the whole
# module (which would also drop the DeprecationWarning check that must run on
# every supported websockets version).
try:
    from websockets.asyncio.server import serve
except ImportError:
    serve = None

_requires_asyncio_server = pytest.mark.skipif(
    serve is None,
    reason="requires websockets>=13 for the asyncio server API used by these tests",
)

# Deadline for each client/server socket exchange below. Without this, a
# regression that stops the client from sending an expected message (e.g.
# ``_send_subscribe_msg()`` returning without sending) would leave the server
# handler awaiting that message while the test awaits the server's reply,
# hanging the test (and the suite) forever instead of failing.
_HANDSHAKE_TIMEOUT = 5


def _capturing_handler(handler):
    """Wrap a server connection handler so its exceptions surface in the test.

    websockets logs/swallows exceptions raised inside a connection handler
    instead of propagating them to the client. Without this, a failed
    ``assert`` in ``handler`` only closes the socket, and the test sees an
    unhelpful ``ConnectionClosedError`` from its own ``recv()``/``send()``
    instead of the real assertion failure.

    Returns the wrapped handler plus a ``check()`` callable; call ``check()``
    after the ``async with serve(...)`` block exits to re-raise any error the
    handler hit.
    """
    captured = []

    async def wrapped(socket):
        try:
            await handler(socket)
        except BaseException as exc:
            captured.append(exc)
            raise

    def check() -> None:
        if captured:
            raise captured[0]

    return wrapped, check


def test_stream_modules_import_without_legacy_deprecation():
    """Importing the stream modules must not emit the websockets.legacy warning.

    This is the acceptance criterion from #743: no DeprecationWarning on
    import, on whatever websockets version is installed.
    """
    import subprocess

    result = subprocess.run(
        [
            sys.executable,
            "-W",
            "error::DeprecationWarning",
            "-c",
            "import alpaca.data.live.websocket; import alpaca.trading.stream",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr


@_requires_asyncio_server
@pytest.mark.asyncio
async def test_data_stream_local_handshake_auth_subscription_and_dispatch():
    """Connect, authenticate, subscribe, and dispatch one bar to a handler."""
    received = {}
    observed_headers = {}

    async def handler(socket):
        observed_headers["user_agent"] = socket.request.headers["User-Agent"]
        observed_headers["content_type"] = socket.request.headers["Content-Type"]

        await socket.send(msgpack.packb([{"T": "success", "msg": "connected"}]))

        auth_msg = msgpack.unpackb(await socket.recv())
        assert auth_msg == {"action": "auth", "key": "key", "secret": "secret"}
        await socket.send(msgpack.packb([{"T": "success", "msg": "authenticated"}]))

        sub_msg = msgpack.unpackb(await socket.recv())
        assert sub_msg["action"] == "subscribe"
        assert sub_msg["bars"] == ["SPY"]

        # Deliver one bar so we exercise _consume/_dispatch, not just the
        # handshake.
        await socket.send(
            msgpack.packb(
                [
                    {
                        "T": "b",
                        "S": "SPY",
                        "o": 1.0,
                        "h": 1.0,
                        "l": 1.0,
                        "c": 1.0,
                        "v": 1,
                        "n": 1,
                        "vw": 1.0,
                        "t": msgpack.ext.Timestamp(seconds=0),
                    }
                ]
            )
        )

    handler, check_handler = _capturing_handler(handler)

    try:
        async with serve(handler, "127.0.0.1", 0) as server:
            port = server.sockets[0].getsockname()[1]
            stream = DataStream(f"ws://127.0.0.1:{port}", "key", "secret")

            async def on_bar(bar):
                received["bar"] = bar

            stream._handlers["bars"]["SPY"] = on_bar

            await asyncio.wait_for(stream._start_ws(), _HANDSHAKE_TIMEOUT)
            await asyncio.wait_for(stream._send_subscribe_msg(), _HANDSHAKE_TIMEOUT)
            r = await asyncio.wait_for(stream._ws.recv(), _HANDSHAKE_TIMEOUT)
            for msg in msgpack.unpackb(r):
                await stream._dispatch(msg)
            await stream.close()
    finally:
        # Re-raises any handler-side assertion even if the client side failed
        # first (e.g. with a ConnectionClosedError from the aborted socket),
        # so the real cause of the failure is what the test reports.
        check_handler()

    assert observed_headers["user_agent"] == get_default_user_agent()
    assert observed_headers["content_type"] == "application/msgpack"
    assert "bar" in received, "handler never dispatched a bar"
    assert received["bar"].symbol == "SPY"


@_requires_asyncio_server
@pytest.mark.asyncio
async def test_trading_stream_local_handshake_auth_subscription_and_dispatch():
    """Connect, authenticate, subscribe, and dispatch one trade update."""
    received = {}
    observed_headers = {}

    async def handler(socket):
        observed_headers["user_agent"] = socket.request.headers["User-Agent"]

        auth_msg = json.loads(await socket.recv())
        assert auth_msg["action"] == "authenticate"
        assert auth_msg["data"]["key_id"] == "key"
        await socket.send(json.dumps({"data": {"status": "authorized"}}))

        sub_msg = json.loads(await socket.recv())
        assert sub_msg == {"action": "listen", "data": {"streams": ["trade_updates"]}}

        await socket.send(
            json.dumps(
                {
                    "stream": "trade_updates",
                    "data": {
                        "event": "fill",
                        "timestamp": "2024-01-01T00:00:00Z",
                        "order": {
                            "id": "11111111-1111-1111-1111-111111111111",
                            "client_order_id": "my-order",
                            "created_at": "2024-01-01T00:00:00Z",
                            "updated_at": "2024-01-01T00:00:00Z",
                            "submitted_at": "2024-01-01T00:00:00Z",
                            "asset_id": "22222222-2222-2222-2222-222222222222",
                            "symbol": "SPY",
                            "asset_class": "us_equity",
                            "qty": "1",
                            "filled_qty": "1",
                            "filled_avg_price": "1",
                            "order_class": "simple",
                            "type": "market",
                            "side": "buy",
                            "time_in_force": "day",
                            "status": "filled",
                            "extended_hours": False,
                        },
                    },
                }
            )
        )

    handler, check_handler = _capturing_handler(handler)

    try:
        async with serve(handler, "127.0.0.1", 0) as server:
            port = server.sockets[0].getsockname()[1]
            stream = TradingStream(
                "key", "secret", paper=True, url_override=f"ws://127.0.0.1:{port}"
            )

            async def on_trade(update):
                received["update"] = update

            stream.subscribe_trade_updates(on_trade)

            await asyncio.wait_for(stream._start_ws(), _HANDSHAKE_TIMEOUT)
            r = await asyncio.wait_for(stream._ws.recv(), _HANDSHAKE_TIMEOUT)
            await stream._dispatch(json.loads(r))
            await stream.close()
    finally:
        # Re-raises any handler-side assertion even if the client side failed
        # first (e.g. with a ConnectionClosedError from the aborted socket),
        # so the real cause of the failure is what the test reports.
        check_handler()

    assert observed_headers["user_agent"] == get_default_user_agent()
    assert "update" in received, "handler never dispatched a trade update"
    assert received["update"].order.symbol == "SPY"
