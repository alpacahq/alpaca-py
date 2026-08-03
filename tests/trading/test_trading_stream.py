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
