"""Live WebSocket stream smoke probes (paper / market-data keys)."""

from __future__ import annotations

import os

import pytest

from alpaca.common.utils import get_default_user_agent
from alpaca.data.live.crypto import CryptoDataStream
from alpaca.data.live.news import NewsDataStream
from alpaca.data.live.option import OptionDataStream
from alpaca.data.live.stock import StockDataStream
from alpaca.trading.stream import TradingStream
from tests.live.streaming import stream_timeout_seconds

DATA_CONNECT = "alpaca.data.live.websocket.websockets_legacy.connect"
TRADING_CONNECT = "alpaca.trading.stream.websockets_legacy.connect"


def _assert_user_agent(result) -> None:
    assert result.headers.get("User-Agent") == get_default_user_agent()


@pytest.mark.live
def test_trading_stream_connect(
    trading_api_credentials,
    trading_paper,
    live_stream_call,
):
    """TradingStream: connect + auth + listen (trade updates may be idle)."""
    key, secret = trading_api_credentials
    stream = TradingStream(api_key=key, secret_key=secret, paper=trading_paper)

    result = live_stream_call(
        "TradingStream.subscribe_trade_updates",
        stream,
        subscribe=lambda s, h: s.subscribe_trade_updates(h),
        connect_path=TRADING_CONNECT,
        require_message=False,
        timeout=stream_timeout_seconds(15),
    )
    assert result.connected
    _assert_user_agent(result)


@pytest.mark.live
def test_stock_data_stream_quotes(
    trading_api_credentials,
    live_stream_call,
):
    """StockDataStream: connect and receive at least one SPY quote."""
    key, secret = trading_api_credentials
    stream = StockDataStream(api_key=key, secret_key=secret)

    result = live_stream_call(
        "StockDataStream.subscribe_quotes",
        stream,
        subscribe=lambda s, h: s.subscribe_quotes(h, "SPY"),
        connect_path=DATA_CONNECT,
        require_message=True,
        timeout=stream_timeout_seconds(45),
    )
    assert result.connected
    assert len(result.messages) >= 1
    _assert_user_agent(result)


@pytest.mark.live
def test_crypto_data_stream_quotes(
    trading_api_credentials,
    live_stream_call,
):
    """CryptoDataStream: connect and receive at least one BTC/USD quote."""
    key, secret = trading_api_credentials
    stream = CryptoDataStream(api_key=key, secret_key=secret)

    result = live_stream_call(
        "CryptoDataStream.subscribe_quotes",
        stream,
        subscribe=lambda s, h: s.subscribe_quotes(h, "BTC/USD"),
        connect_path=DATA_CONNECT,
        require_message=True,
        timeout=stream_timeout_seconds(30),
    )
    assert result.connected
    assert len(result.messages) >= 1
    _assert_user_agent(result)


@pytest.mark.live
def test_option_data_stream_quotes(
    trading_api_credentials,
    live_stream_call,
):
    """OptionDataStream: connect (+ optional quote if ALPACA_LIVE_OPTION_SYMBOL)."""
    symbol = os.getenv("ALPACA_LIVE_OPTION_SYMBOL", "").strip()
    key, secret = trading_api_credentials
    stream = OptionDataStream(api_key=key, secret_key=secret)

    if symbol:
        result = live_stream_call(
            "OptionDataStream.subscribe_quotes",
            stream,
            subscribe=lambda s, h: s.subscribe_quotes(h, symbol),
            connect_path=DATA_CONNECT,
            require_message=True,
            timeout=stream_timeout_seconds(45),
        )
        assert len(result.messages) >= 1
    else:
        # Without a concrete OCC symbol, prove connect/auth via a noop subscribe
        # that still starts the socket, then stop before requiring ticks.
        result = live_stream_call(
            "OptionDataStream.connect",
            stream,
            subscribe=lambda s, h: s.subscribe_quotes(h, "SPY240119C00500000"),
            connect_path=DATA_CONNECT,
            require_message=False,
            timeout=stream_timeout_seconds(15),
        )
    assert result.connected
    _assert_user_agent(result)


@pytest.mark.live
def test_news_data_stream_connect(
    trading_api_credentials,
    live_stream_call,
):
    """NewsDataStream: connect + subscribe (news ticks are sporadic)."""
    key, secret = trading_api_credentials
    stream = NewsDataStream(api_key=key, secret_key=secret)

    result = live_stream_call(
        "NewsDataStream.subscribe_news",
        stream,
        subscribe=lambda s, h: s.subscribe_news(h, "*"),
        connect_path=DATA_CONNECT,
        require_message=False,
        timeout=stream_timeout_seconds(15),
    )
    assert result.connected
    _assert_user_agent(result)
