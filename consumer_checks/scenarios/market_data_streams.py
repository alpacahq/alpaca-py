"""Market-data websocket clients, against fixed frames.

Quotes, trades and the other channels cannot be made to repeat byte for byte,
so these scenarios never open a real socket. The frames are the server's
msgpack messages (see ``stub_websocket``). Replay fails if the SDK's URL,
headers, auth, or subscribe and unsubscribe messages change, or if a parsed
model changes shape.
"""

from __future__ import annotations

import threading
from typing import Any, Callable, Dict, List

from alpaca.data.models import (
    Bar,
    News,
    Orderbook,
    Quote,
    Trade,
    TradeCancel,
    TradeCorrection,
    TradingStatus,
)

from . import Context, scenario
from ._stream import (
    bar,
    frame,
    handshake,
    news,
    orderbook,
    quote,
    run_until,
    take,
    trade,
    trade_cancel,
    trade_correction,
    trading_status,
)

STOCK = "AAPL"
CRYPTO = "BTC/USD"
OPTION = "SPY240119C00500000"
NEWS_SYMBOL = "AVGO"


def _channels(names: List[str]) -> tuple:
    ready = threading.Event()
    pending = {name: False for name in names}
    buckets: Dict[str, List[Any]] = {name: [] for name in names}
    handlers = {name: take(buckets[name], pending, name, ready) for name in names}
    return ready, buckets, handlers


def _finish(
    stream: Any,
    ready: threading.Event,
    unsubscribe: Callable[[], None],
    buckets: Dict[str, List[Any]],
    expected: Dict[str, type],
) -> Dict[str, Any]:
    run_until(stream, ready, unsubscribe)
    result = {}
    for name, model in expected.items():
        assert buckets[name], name
        assert isinstance(buckets[name][0], model)
        result[name] = buckets[name][0]
    return result


_STOCK_NAMES = [
    "trade",
    "quote",
    "bar",
    "updated_bar",
    "daily_bar",
    "status",
    "correction",
    "cancel",
]
_STOCK_MESSAGES = [
    trade(STOCK),
    quote(STOCK),
    bar(STOCK, "b"),
    bar(STOCK, "u"),
    bar(STOCK, "d"),
    trading_status(STOCK),
    trade_correction(STOCK),
    trade_cancel(STOCK),
]


@scenario(
    covers=[
        "StockDataStream.subscribe_trades",
        "StockDataStream.subscribe_quotes",
        "StockDataStream.subscribe_bars",
        "StockDataStream.subscribe_updated_bars",
        "StockDataStream.subscribe_daily_bars",
        "StockDataStream.subscribe_trading_statuses",
        "StockDataStream.register_trade_corrections",
        "StockDataStream.register_trade_cancels",
        "StockDataStream.unsubscribe_trades",
        "StockDataStream.unsubscribe_quotes",
        "StockDataStream.unsubscribe_bars",
        "StockDataStream.unsubscribe_updated_bars",
        "StockDataStream.unsubscribe_daily_bars",
        "StockDataStream.unsubscribe_trading_statuses",
    ],
    stub_websocket=handshake() + [frame(message) for message in _STOCK_MESSAGES],
)
def stock_channels(ctx: Context) -> Dict[str, Any]:
    ready, buckets, handlers = _channels(_STOCK_NAMES)
    stream = ctx.stock_stream
    stream.subscribe_trades(handlers["trade"], STOCK)
    stream.subscribe_quotes(handlers["quote"], STOCK)
    stream.subscribe_bars(handlers["bar"], STOCK)
    stream.subscribe_updated_bars(handlers["updated_bar"], STOCK)
    stream.subscribe_daily_bars(handlers["daily_bar"], STOCK)
    stream.subscribe_trading_statuses(handlers["status"], STOCK)
    stream.register_trade_corrections(handlers["correction"])
    stream.register_trade_cancels(handlers["cancel"])

    def unsubscribe() -> None:
        stream.unsubscribe_trades(STOCK)
        stream.unsubscribe_quotes(STOCK)
        stream.unsubscribe_bars(STOCK)
        stream.unsubscribe_updated_bars(STOCK)
        stream.unsubscribe_daily_bars(STOCK)
        stream.unsubscribe_trading_statuses(STOCK)

    return _finish(
        stream,
        ready,
        unsubscribe,
        buckets,
        {
            "trade": Trade,
            "quote": Quote,
            "bar": Bar,
            "updated_bar": Bar,
            "daily_bar": Bar,
            "status": TradingStatus,
            "correction": TradeCorrection,
            "cancel": TradeCancel,
        },
    )


_CRYPTO_NAMES = ["trade", "quote", "bar", "updated_bar", "daily_bar", "orderbook"]
_CRYPTO_MESSAGES = [
    trade(CRYPTO),
    quote(CRYPTO),
    bar(CRYPTO, "b"),
    bar(CRYPTO, "u"),
    bar(CRYPTO, "d"),
    orderbook(CRYPTO),
]


@scenario(
    covers=[
        "CryptoDataStream.subscribe_trades",
        "CryptoDataStream.subscribe_quotes",
        "CryptoDataStream.subscribe_bars",
        "CryptoDataStream.subscribe_updated_bars",
        "CryptoDataStream.subscribe_daily_bars",
        "CryptoDataStream.subscribe_orderbooks",
        "CryptoDataStream.unsubscribe_trades",
        "CryptoDataStream.unsubscribe_quotes",
        "CryptoDataStream.unsubscribe_bars",
        "CryptoDataStream.unsubscribe_updated_bars",
        "CryptoDataStream.unsubscribe_daily_bars",
        "CryptoDataStream.unsubscribe_orderbooks",
    ],
    stub_websocket=handshake() + [frame(message) for message in _CRYPTO_MESSAGES],
)
def crypto_channels(ctx: Context) -> Dict[str, Any]:
    ready, buckets, handlers = _channels(_CRYPTO_NAMES)
    stream = ctx.crypto_stream
    stream.subscribe_trades(handlers["trade"], CRYPTO)
    stream.subscribe_quotes(handlers["quote"], CRYPTO)
    stream.subscribe_bars(handlers["bar"], CRYPTO)
    stream.subscribe_updated_bars(handlers["updated_bar"], CRYPTO)
    stream.subscribe_daily_bars(handlers["daily_bar"], CRYPTO)
    stream.subscribe_orderbooks(handlers["orderbook"], CRYPTO)

    def unsubscribe() -> None:
        stream.unsubscribe_trades(CRYPTO)
        stream.unsubscribe_quotes(CRYPTO)
        stream.unsubscribe_bars(CRYPTO)
        stream.unsubscribe_updated_bars(CRYPTO)
        stream.unsubscribe_daily_bars(CRYPTO)
        stream.unsubscribe_orderbooks(CRYPTO)

    return _finish(
        stream,
        ready,
        unsubscribe,
        buckets,
        {
            "trade": Trade,
            "quote": Quote,
            "bar": Bar,
            "updated_bar": Bar,
            "daily_bar": Bar,
            "orderbook": Orderbook,
        },
    )


_OPTION_NAMES = ["trade", "quote"]
_OPTION_MESSAGES = [trade(OPTION), quote(OPTION)]


@scenario(
    covers=[
        "OptionDataStream.subscribe_trades",
        "OptionDataStream.subscribe_quotes",
        "OptionDataStream.unsubscribe_trades",
        "OptionDataStream.unsubscribe_quotes",
    ],
    stub_websocket=handshake() + [frame(message) for message in _OPTION_MESSAGES],
)
def option_channels(ctx: Context) -> Dict[str, Any]:
    ready, buckets, handlers = _channels(_OPTION_NAMES)
    stream = ctx.option_stream
    stream.subscribe_trades(handlers["trade"], OPTION)
    stream.subscribe_quotes(handlers["quote"], OPTION)

    def unsubscribe() -> None:
        stream.unsubscribe_trades(OPTION)
        stream.unsubscribe_quotes(OPTION)

    return _finish(
        stream,
        ready,
        unsubscribe,
        buckets,
        {"trade": Trade, "quote": Quote},
    )


@scenario(
    covers=["NewsDataStream.subscribe_news", "NewsDataStream.unsubscribe_news"],
    stub_websocket=handshake() + [frame(news(NEWS_SYMBOL))],
)
def news_headline(ctx: Context) -> Dict[str, Any]:
    ready, buckets, handlers = _channels(["news"])
    stream = ctx.news_stream
    stream.subscribe_news(handlers["news"], NEWS_SYMBOL)

    def unsubscribe() -> None:
        stream.unsubscribe_news(NEWS_SYMBOL)

    return _finish(stream, ready, unsubscribe, buckets, {"news": News})
