import asyncio
import threading
from unittest.mock import AsyncMock, MagicMock, PropertyMock, patch

import pytest

from alpaca.common.utils import get_default_user_agent
from alpaca.trading.stream import TradingStream


@pytest.fixture
def trading_stream() -> TradingStream:
    return TradingStream("key-id", "secret-key", paper=True)


@pytest.mark.asyncio
async def test_run_forever_waits_for_subscription_without_polling(
    trading_stream: TradingStream,
):
    sleep_calls = []
    original_sleep = asyncio.sleep

    async def tracked_sleep(delay):
        sleep_calls.append(delay)
        await original_sleep(delay)

    with patch("alpaca.trading.stream.asyncio.sleep", new=tracked_sleep):
        run_task = asyncio.create_task(trading_stream._run_forever())
        try:
            await original_sleep(0)
            await original_sleep(0)
            assert sleep_calls == []
        finally:
            await trading_stream.stop_ws()
            await asyncio.wait_for(run_task, timeout=1)


@pytest.mark.asyncio
async def test_wait_for_subscription_honors_stop_state(
    trading_stream: TradingStream,
):
    trading_stream._should_run = False

    assert await trading_stream._wait_for_subscription() is False


@pytest.mark.asyncio
async def test_run_forever_wakes_for_subscription_from_another_thread(
    trading_stream: TradingStream,
):
    websocket_started = asyncio.Event()
    thread_errors = []

    async def handler(_):
        pass

    async def start_ws():
        websocket_started.set()
        trading_stream._should_run = False

    def subscribe():
        try:
            trading_stream.subscribe_trade_updates(handler)
        except Exception as error:
            thread_errors.append(error)

    with (
        patch.object(trading_stream, "_start_ws", side_effect=start_ws),
        patch.object(trading_stream, "_consume", new=AsyncMock()),
    ):
        run_task = asyncio.create_task(trading_stream._run_forever())
        await asyncio.sleep(0)
        subscription_thread = threading.Thread(target=subscribe)
        subscription_thread.start()
        subscription_thread.join(timeout=1)

        assert not subscription_thread.is_alive()
        assert thread_errors == []
        await asyncio.wait_for(websocket_started.wait(), timeout=1)
        await asyncio.wait_for(run_task, timeout=1)


def test_signal_state_change_uses_event_snapshot(trading_stream: TradingStream):
    loop = MagicMock()
    subscription_event = MagicMock()
    trading_stream._loop = loop

    with patch.object(
        TradingStream, "_subscription_event", new_callable=PropertyMock, create=True
    ) as event_attribute:
        event_attribute.side_effect = [subscription_event, None]
        trading_stream._signal_state_change()

    loop.call_soon_threadsafe.assert_called_once_with(subscription_event.set)


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
