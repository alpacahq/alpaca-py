import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from alpaca.common.utils import get_default_user_agent
from alpaca.trading.stream import TradingStream


@pytest.fixture
def trading_stream() -> TradingStream:
    return TradingStream("key-id", "secret-key", paper=True)


@pytest.mark.asyncio
async def test_connect_sets_user_agent_header(trading_stream: TradingStream):
    """TradingStream should send the same User-Agent format as REST/DataStream."""
    mock_ws = AsyncMock()

    with patch(
        "alpaca.trading.stream.websockets_legacy.connect",
        new=AsyncMock(return_value=mock_ws),
    ) as mock_connect:
        await trading_stream._connect()

    _, kwargs = mock_connect.call_args
    assert kwargs["extra_headers"]["User-Agent"] == get_default_user_agent()


@pytest.mark.asyncio
async def test_connect_preserves_user_agent_when_extra_headers_overridden():
    stream = TradingStream(
        "key-id",
        "secret-key",
        paper=True,
        websocket_params={
            "ping_interval": 10,
            "extra_headers": {"X-Test": "1", "User-Agent": "custom-agent"},
        },
    )
    mock_ws = AsyncMock()

    with patch(
        "alpaca.trading.stream.websockets_legacy.connect",
        new=AsyncMock(return_value=mock_ws),
    ) as mock_connect:
        await stream._connect()

    _, kwargs = mock_connect.call_args
    assert kwargs["extra_headers"]["X-Test"] == "1"
    assert kwargs["extra_headers"]["User-Agent"] == get_default_user_agent()


@pytest.mark.asyncio
async def test_run_forever_unblocks_on_subscribe(trading_stream: TradingStream):
    async def mock_handler(data):
        pass

    async def mock_consume_side_effect():
        await trading_stream.stop_ws()

    with patch.object(trading_stream, "_start_ws", new_callable=AsyncMock) as mock_start, \
         patch.object(trading_stream, "_consume", new_callable=AsyncMock) as mock_consume:
        mock_consume.side_effect = mock_consume_side_effect

        task = asyncio.create_task(trading_stream._run_forever())
        await asyncio.sleep(0.05)
        assert not mock_start.called

        trading_stream.subscribe_trade_updates(mock_handler)
        await asyncio.wait_for(task, timeout=2.0)
        assert mock_start.called


@pytest.mark.asyncio
async def test_run_forever_stops_cleanly_when_no_subscriptions(trading_stream: TradingStream):
    task = asyncio.create_task(trading_stream._run_forever())
    await asyncio.sleep(0.05)
    await trading_stream.stop_ws()
    await asyncio.wait_for(task, timeout=2.0)
