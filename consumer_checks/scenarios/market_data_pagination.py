"""Page-by-page quotes, trades and crypto/option bars (#877), ``since="0.46.0"``.

Each scenario fetches one page with ``handle_pagination=PaginationType.NONE``,
then the next by passing its ``next_page_token`` back as ``page_token``: the
same round trip as ``stock_data_pagination.bars_one_page_at_a_time``, for every
other method #877 added it to. Stubbed, like that module, and recorded with
this checkout's SDK until BASELINE reaches 0.46.0.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, Type

from alpaca.common.enums import PaginationType
from alpaca.data.enums import DataFeed
from alpaca.data.models import BarSet, QuoteSet, TradeSet
from alpaca.data.models.base import BaseDataSet
from alpaca.data.requests import (
    CryptoBarsRequest,
    CryptoQuoteRequest,
    CryptoTradesRequest,
    OptionBarsRequest,
    OptionTradesRequest,
    StockQuotesRequest,
    StockTradesRequest,
)
from alpaca.data.timeframe import TimeFrame

from . import Context, scenario

SINCE = "0.46.0"
START = datetime(2024, 3, 4, tzinfo=timezone.utc)
END = datetime(2024, 3, 9, tzinfo=timezone.utc)
CONTRACT = "AAPL240308C00175000"
T = "2024-03-04T15:00:00Z"

BAR = {"t": T, "o": 2.5, "h": 2.7, "l": 2.4, "c": 2.6, "v": 10, "n": 3, "vw": 2.55}
STOCK_QUOTE = {
    "t": T,
    "bx": "V",
    "bp": 174.9,
    "bs": 2,
    "ax": "V",
    "ap": 175.1,
    "as": 3,
    "c": ["R"],
    "z": "C",
}
STOCK_TRADE = {"t": T, "x": "V", "p": 175.0, "s": 100, "c": ["@"], "i": 1, "z": "C"}
CRYPTO_QUOTE = {"t": T, "bp": 62999.0, "bs": 0.4, "ap": 63001.0, "as": 0.3}
CRYPTO_TRADE = {"t": T, "p": 63000.0, "s": 0.0014, "i": 1, "tks": "B"}
OPTION_TRADE = {"t": T, "x": "C", "p": 2.5, "s": 1, "c": "I"}


def _pages(key: str, symbol: str, item: Dict[str, Any]) -> List[Dict[str, Any]]:
    """A first page pointing to a second, last one."""
    return [
        {"status": 200, "json": {key: {symbol: [item]}, "next_page_token": "page-2"}},
        {"status": 200, "json": {key: {symbol: [item]}, "next_page_token": None}},
    ]


def _first_then_next(
    fetch: Callable[..., Any],
    make_request: Callable[[Optional[str]], Any],
    set_type: Type[BaseDataSet],
) -> Dict[str, Any]:
    first = fetch(make_request(None), handle_pagination=PaginationType.NONE)
    assert isinstance(first, set_type)
    assert first.next_page_token == "page-2"
    last = fetch(
        make_request(first.next_page_token), handle_pagination=PaginationType.NONE
    )
    assert isinstance(last, set_type)
    assert last.next_page_token is None
    return {"first": first, "last": last}


@scenario(
    covers=["StockHistoricalDataClient.get_stock_quotes"],
    since=SINCE,
    stub_responses=_pages("quotes", "AAPL", STOCK_QUOTE),
)
def stock_quotes_one_page_at_a_time(ctx: Context) -> Dict[str, Any]:
    return _first_then_next(
        ctx.stock_data.get_stock_quotes,
        lambda token: StockQuotesRequest(
            symbol_or_symbols="AAPL",
            start=START,
            end=END,
            feed=DataFeed.IEX,
            page_token=token,
        ),
        QuoteSet,
    )


@scenario(
    covers=["StockHistoricalDataClient.get_stock_trades"],
    since=SINCE,
    stub_responses=_pages("trades", "AAPL", STOCK_TRADE),
)
def stock_trades_one_page_at_a_time(ctx: Context) -> Dict[str, Any]:
    return _first_then_next(
        ctx.stock_data.get_stock_trades,
        lambda token: StockTradesRequest(
            symbol_or_symbols="AAPL",
            start=START,
            end=END,
            feed=DataFeed.IEX,
            page_token=token,
        ),
        TradeSet,
    )


@scenario(
    covers=["CryptoHistoricalDataClient.get_crypto_bars"],
    since=SINCE,
    stub_responses=_pages("bars", "BTC/USD", BAR),
)
def crypto_bars_one_page_at_a_time(ctx: Context) -> Dict[str, Any]:
    return _first_then_next(
        ctx.crypto_data.get_crypto_bars,
        lambda token: CryptoBarsRequest(
            symbol_or_symbols="BTC/USD",
            timeframe=TimeFrame.Hour,
            start=START,
            end=END,
            page_token=token,
        ),
        BarSet,
    )


@scenario(
    covers=["CryptoHistoricalDataClient.get_crypto_quotes"],
    since=SINCE,
    stub_responses=_pages("quotes", "BTC/USD", CRYPTO_QUOTE),
)
def crypto_quotes_one_page_at_a_time(ctx: Context) -> Dict[str, Any]:
    return _first_then_next(
        ctx.crypto_data.get_crypto_quotes,
        lambda token: CryptoQuoteRequest(
            symbol_or_symbols="BTC/USD", start=START, end=END, page_token=token
        ),
        QuoteSet,
    )


@scenario(
    covers=["CryptoHistoricalDataClient.get_crypto_trades"],
    since=SINCE,
    stub_responses=_pages("trades", "BTC/USD", CRYPTO_TRADE),
)
def crypto_trades_one_page_at_a_time(ctx: Context) -> Dict[str, Any]:
    return _first_then_next(
        ctx.crypto_data.get_crypto_trades,
        lambda token: CryptoTradesRequest(
            symbol_or_symbols="BTC/USD", start=START, end=END, page_token=token
        ),
        TradeSet,
    )


@scenario(
    covers=["OptionHistoricalDataClient.get_option_bars"],
    since=SINCE,
    stub_responses=_pages("bars", CONTRACT, BAR),
)
def option_bars_one_page_at_a_time(ctx: Context) -> Dict[str, Any]:
    return _first_then_next(
        ctx.option_data.get_option_bars,
        lambda token: OptionBarsRequest(
            symbol_or_symbols=CONTRACT,
            timeframe=TimeFrame.Day,
            start=START,
            end=END,
            page_token=token,
        ),
        BarSet,
    )


@scenario(
    covers=["OptionHistoricalDataClient.get_option_trades"],
    since=SINCE,
    stub_responses=_pages("trades", CONTRACT, OPTION_TRADE),
)
def option_trades_one_page_at_a_time(ctx: Context) -> Dict[str, Any]:
    return _first_then_next(
        ctx.option_data.get_option_trades,
        lambda token: OptionTradesRequest(
            symbol_or_symbols=CONTRACT, start=START, end=END, page_token=token
        ),
        TradeSet,
    )
