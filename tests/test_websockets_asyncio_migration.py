"""Modern asyncio WebSocket contract for both SDK streaming clients."""

import subprocess
import sys
import json
from unittest.mock import AsyncMock, patch

import msgpack
import pytest
from websockets.asyncio.server import serve

from alpaca.common.utils import get_default_user_agent
from alpaca.data.live.websocket import DataStream
from alpaca.trading.stream import TradingStream


def test_stream_modules_import_without_legacy_deprecation():
    result = subprocess.run(
        [sys.executable, "-W", "error::DeprecationWarning", "-c",
         "import alpaca.data.live.websocket; import alpaca.trading.stream"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr


@pytest.mark.asyncio
async def test_data_stream_connect_uses_modern_client_and_preserves_headers():
    stream = DataStream(
        "wss://example.test/data", "key", "secret",
        websocket_params={
            "ping_interval": 10,
            "extra_headers": {"X-Legacy": "1", "User-Agent": "override"},
            "additional_headers": {"X-Modern": "2", "Content-Type": "wrong"},
            "user_agent_header": "override",
        },
    )
    socket = AsyncMock()
    socket.recv.return_value = msgpack.packb([{"T": "success", "msg": "connected"}])
    with patch("alpaca.data.live.websocket.connect", new=AsyncMock(return_value=socket)) as connector:
        await stream._connect()
    kwargs = connector.call_args.kwargs
    assert kwargs["user_agent_header"] == get_default_user_agent()
    assert kwargs["additional_headers"] == {
        "X-Legacy": "1", "X-Modern": "2", "Content-Type": "application/msgpack"
    }
    assert kwargs["ping_interval"] == 10
    assert "extra_headers" not in kwargs


@pytest.mark.asyncio
async def test_trading_stream_connect_uses_modern_client_and_preserves_headers():
    stream = TradingStream(
        "key", "secret", paper=True,
        websocket_params={
            "ping_interval": 10,
            "extra_headers": {"X-Legacy": "1", "User-Agent": "override"},
            "additional_headers": {"X-Modern": "2"},
        },
    )
    socket = AsyncMock()
    with patch("alpaca.trading.stream.connect", new=AsyncMock(return_value=socket)) as connector:
        await stream._connect()
    kwargs = connector.call_args.kwargs
    assert kwargs["user_agent_header"] == get_default_user_agent()
    assert kwargs["additional_headers"] == {"X-Legacy": "1", "X-Modern": "2"}
    assert kwargs["ping_interval"] == 10
    assert "extra_headers" not in kwargs


@pytest.mark.asyncio
async def test_data_stream_local_handshake_auth_and_subscription():
    observed = {}

    async def handler(socket):
        observed["agent"] = socket.request.headers["User-Agent"]
        observed["content_type"] = socket.request.headers["Content-Type"]
        await socket.send(msgpack.packb([{"T": "success", "msg": "connected"}]))
        observed["auth"] = msgpack.unpackb(await socket.recv())
        await socket.send(msgpack.packb([{"T": "success", "msg": "authenticated"}]))
        observed["subscription"] = msgpack.unpackb(await socket.recv())

    async with serve(handler, "127.0.0.1", 0) as server:
        port = server.sockets[0].getsockname()[1]
        stream = DataStream(f"ws://127.0.0.1:{port}", "key", "secret")
        stream._handlers["bars"]["SPY"] = lambda bar: None
        await stream._start_ws()
        await stream._send_subscribe_msg()
        await stream.close()

    assert observed["agent"] == get_default_user_agent()
    assert observed["content_type"] == "application/msgpack"
    assert observed["auth"] == {"action": "auth", "key": "key", "secret": "secret"}
    assert observed["subscription"]["action"] == "subscribe"
    assert observed["subscription"]["bars"] == ["SPY"]


@pytest.mark.asyncio
async def test_trading_stream_local_handshake_auth_and_subscription():
    observed = {}

    async def handler(socket):
        observed["agent"] = socket.request.headers["User-Agent"]
        observed["auth"] = json.loads(await socket.recv())
        await socket.send(json.dumps({"data": {"status": "authorized"}}))
        observed["subscription"] = json.loads(await socket.recv())

    async with serve(handler, "127.0.0.1", 0) as server:
        port = server.sockets[0].getsockname()[1]
        stream = TradingStream("key", "secret", url_override=f"ws://127.0.0.1:{port}")

        async def on_trade(update):
            pass

        stream.subscribe_trade_updates(on_trade)
        await stream._start_ws()
        await stream.close()

    assert observed["agent"] == get_default_user_agent()
    assert observed["auth"]["action"] == "authenticate"
    assert observed["auth"]["data"]["key_id"] == "key"
    assert observed["subscription"] == {
        "action": "listen", "data": {"streams": ["trade_updates"]}
    }
