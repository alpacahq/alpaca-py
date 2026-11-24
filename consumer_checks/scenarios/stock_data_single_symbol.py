"""Single-symbol stock routes, auctions and the stock meta codes.

These methods are not released yet, so every scenario sets ``since="0.50.0"``:
they are recorded with this checkout's SDK until BASELINE reaches 0.50.0.

The new names (requests, response envelopes, ``StockHistoricalFeed``) are imported
inside each scenario: every module is imported with the BASELINE release too
(where they do not exist yet), and a module-level import would stop collection.

The single-symbol routes (``/stocks/{symbol}/...``) put the symbol in the path
and return the API's envelope as it is: the symbol, the currency and, for
time series, the ``next_page_token`` the user passes back as ``page_token``.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict

from alpaca.common.enums import Sort, SupportedCurrencies
from alpaca.data.enums import Adjustment, DataFeed
from alpaca.data.timeframe import TimeFrame

from . import Context, scenario

SINCE = "0.50.0"

# A fixed past week (Mon 4 to Fri 8 March 2024), so live runs see stable data.
# IEX is the feed available to every paper account.
WEEK_START = datetime(2024, 3, 4, tzinfo=timezone.utc)
WEEK_END = datetime(2024, 3, 9, tzinfo=timezone.utc)


@scenario(covers=["StockHistoricalDataClient.get_stock_bars_for_symbol"], since=SINCE)
def bars_for_symbol_page_by_page(ctx: Context) -> Dict[str, Any]:
    from alpaca.data import StockBarsRespSingle
    from alpaca.data.requests import StockBarsForSymbolRequest

    first_request = StockBarsForSymbolRequest(
        symbol="AAPL",
        timeframe=TimeFrame.Day,
        start=WEEK_START,
        end=WEEK_END,
        limit=2,
        adjustment=Adjustment.RAW,
        sort=Sort.ASC,
        asof="2024-03-04",
        currency=SupportedCurrencies.USD,
        feed=DataFeed.IEX,
    )
    first = ctx.stock_data.get_stock_bars_for_symbol(first_request)

    assert isinstance(first, StockBarsRespSingle)
    assert first.symbol == "AAPL"
    assert len(first.bars) == 2
    assert first.next_page_token is not None
    assert first.bars[0].l <= first.bars[0].o <= first.bars[0].h

    second = ctx.stock_data.get_stock_bars_for_symbol(
        first_request.model_copy(update={"page_token": first.next_page_token})
    )

    assert isinstance(second, StockBarsRespSingle)
    assert second.symbol == "AAPL"
    assert second.bars[0].t > first.bars[-1].t
    return {"first": first, "second": second}


@scenario(covers=["StockHistoricalDataClient.get_stock_quotes_for_symbol"], since=SINCE)
def quotes_for_symbol_newest_first(ctx: Context) -> Dict[str, Any]:
    from alpaca.data import StockQuotesRespSingle
    from alpaca.data.requests import StockQuotesForSymbolRequest

    first_request = StockQuotesForSymbolRequest(
        symbol="AAPL",
        start=WEEK_START,
        end=WEEK_END,
        limit=3,
        sort=Sort.DESC,
        asof="2024-03-04",
        currency=SupportedCurrencies.USD,
        feed=DataFeed.IEX,
    )
    first = ctx.stock_data.get_stock_quotes_for_symbol(first_request)

    assert isinstance(first, StockQuotesRespSingle)
    assert first.symbol == "AAPL"
    assert len(first.quotes) == 3
    stamps = [quote.t for quote in first.quotes]
    assert stamps == sorted(stamps, reverse=True)
    assert first.next_page_token is not None

    second = ctx.stock_data.get_stock_quotes_for_symbol(
        first_request.model_copy(update={"page_token": first.next_page_token})
    )

    assert isinstance(second, StockQuotesRespSingle)
    assert second.quotes[0].t <= first.quotes[-1].t
    return {"first": first, "second": second}


@scenario(covers=["StockHistoricalDataClient.get_stock_trades_for_symbol"], since=SINCE)
def trades_for_symbol_page_by_page(ctx: Context) -> Dict[str, Any]:
    from alpaca.data import StockTradesRespSingle
    from alpaca.data.requests import StockTradesForSymbolRequest

    first_request = StockTradesForSymbolRequest(
        symbol="AAPL",
        start=WEEK_START,
        end=WEEK_END,
        limit=3,
        sort=Sort.ASC,
        asof="2024-03-04",
        currency=SupportedCurrencies.USD,
        feed=DataFeed.IEX,
    )
    first = ctx.stock_data.get_stock_trades_for_symbol(first_request)

    assert isinstance(first, StockTradesRespSingle)
    assert first.symbol == "AAPL"
    assert len(first.trades) == 3
    assert all(trade.p > 0 and trade.s > 0 for trade in first.trades)
    assert first.next_page_token is not None

    second = ctx.stock_data.get_stock_trades_for_symbol(
        first_request.model_copy(update={"page_token": first.next_page_token})
    )

    assert isinstance(second, StockTradesRespSingle)
    assert second.trades[0].t >= first.trades[-1].t
    return {"first": first, "second": second}


@scenario(
    covers=[
        "StockHistoricalDataClient.get_stock_latest_bar_for_symbol",
        "StockHistoricalDataClient.get_stock_latest_quote_for_symbol",
        "StockHistoricalDataClient.get_stock_latest_trade_for_symbol",
    ],
    since=SINCE,
)
def latest_bar_quote_and_trade_for_symbol(ctx: Context) -> Dict[str, Any]:
    from alpaca.data import (
        StockLatestBarsRespSingle,
        StockLatestQuotesRespSingle,
        StockLatestTradesRespSingle,
    )
    from alpaca.data.requests import (
        StockLatestBarForSymbolRequest,
        StockLatestQuoteForSymbolRequest,
        StockLatestTradeForSymbolRequest,
    )

    bar = ctx.stock_data.get_stock_latest_bar_for_symbol(
        StockLatestBarForSymbolRequest(
            symbol="AAPL", feed=DataFeed.IEX, currency=SupportedCurrencies.USD
        )
    )
    quote = ctx.stock_data.get_stock_latest_quote_for_symbol(
        StockLatestQuoteForSymbolRequest(
            symbol="AAPL", feed=DataFeed.IEX, currency=SupportedCurrencies.USD
        )
    )
    trade = ctx.stock_data.get_stock_latest_trade_for_symbol(
        StockLatestTradeForSymbolRequest(
            symbol="AAPL", feed=DataFeed.IEX, currency=SupportedCurrencies.USD
        )
    )

    assert isinstance(bar, StockLatestBarsRespSingle)
    assert isinstance(quote, StockLatestQuotesRespSingle)
    assert isinstance(trade, StockLatestTradesRespSingle)
    assert bar.symbol == quote.symbol == trade.symbol == "AAPL"
    assert bar.bar.l <= bar.bar.h
    assert trade.trade.p > 0
    return {"bar": bar, "quote": quote, "trade": trade}


@scenario(
    covers=["StockHistoricalDataClient.get_stock_snapshot_for_symbol"], since=SINCE
)
def snapshot_for_symbol(ctx: Context) -> Dict[str, Any]:
    from alpaca.data import StockSnapshotsRespSingle
    from alpaca.data.requests import StockSnapshotForSymbolRequest

    snapshot = ctx.stock_data.get_stock_snapshot_for_symbol(
        StockSnapshotForSymbolRequest(
            symbol="AAPL", feed=DataFeed.IEX, currency=SupportedCurrencies.USD
        )
    )

    assert isinstance(snapshot, StockSnapshotsRespSingle)
    assert snapshot.symbol == "AAPL"
    assert snapshot.daily_bar is not None
    assert snapshot.latest_trade is not None
    return {"snapshot": snapshot}


@scenario(
    covers=["StockHistoricalDataClient.get_stock_auctions"],
    since=SINCE,
)
def auctions_for_two_symbols(ctx: Context) -> Dict[str, Any]:
    from alpaca.data import StockAuctionsResp
    from alpaca.data.enums import StockHistoricalFeed
    from alpaca.data.requests import StockAuctionsRequest

    # Only the SIP feed has auctions.
    first_request = StockAuctionsRequest(
        symbol_or_symbols=["AAPL", "MSFT"],
        start=WEEK_START,
        end=WEEK_END,
        limit=2,
        sort=Sort.ASC,
        asof="2024-03-04",
        currency=SupportedCurrencies.USD,
        feed=StockHistoricalFeed.SIP,
    )
    first = ctx.stock_data.get_stock_auctions(first_request)

    assert isinstance(first, StockAuctionsResp)
    assert set(first.auctions) <= {"AAPL", "MSFT"}
    assert first.auctions
    day = next(iter(first.auctions.values()))[0]
    assert day.o or day.c
    assert first.next_page_token is not None

    second = ctx.stock_data.get_stock_auctions(
        first_request.model_copy(update={"page_token": first.next_page_token})
    )

    assert isinstance(second, StockAuctionsResp)
    assert second.auctions
    return {"first": first, "second": second}


@scenario(
    covers=["StockHistoricalDataClient.get_stock_auctions_for_symbol"],
    since=SINCE,
)
def auctions_for_symbol_page_by_page(ctx: Context) -> Dict[str, Any]:
    from alpaca.data import StockAuctionsRespSingle
    from alpaca.data.enums import StockHistoricalFeed
    from alpaca.data.requests import StockAuctionsForSymbolRequest

    first_request = StockAuctionsForSymbolRequest(
        symbol="AAPL",
        start=WEEK_START,
        end=WEEK_END,
        limit=2,
        sort=Sort.ASC,
        asof="2024-03-04",
        currency=SupportedCurrencies.USD,
        feed=StockHistoricalFeed.SIP,
    )
    first = ctx.stock_data.get_stock_auctions_for_symbol(first_request)

    assert isinstance(first, StockAuctionsRespSingle)
    assert first.symbol == "AAPL"
    assert len(first.auctions) == 2
    assert first.next_page_token is not None

    second = ctx.stock_data.get_stock_auctions_for_symbol(
        first_request.model_copy(update={"page_token": first.next_page_token})
    )

    assert isinstance(second, StockAuctionsRespSingle)
    assert second.auctions[0].d > first.auctions[-1].d
    return {"first": first, "second": second}


@scenario(covers=["StockHistoricalDataClient.get_stock_condition_codes"], since=SINCE)
def trade_and_quote_condition_codes(ctx: Context) -> Dict[str, Any]:
    # The codes come back as a plain dict from code to name.
    trade_codes = ctx.stock_data.get_stock_condition_codes("trade", "A")
    quote_codes = ctx.stock_data.get_stock_condition_codes("quote", "A")

    assert isinstance(trade_codes, dict) and isinstance(quote_codes, dict)
    assert trade_codes and quote_codes
    assert all(isinstance(name, str) for name in trade_codes.values())
    return {"trade_codes": trade_codes, "quote_codes": quote_codes}


@scenario(covers=["StockHistoricalDataClient.get_stock_exchange_codes"], since=SINCE)
def exchange_codes(ctx: Context) -> Dict[str, Any]:
    codes = ctx.stock_data.get_stock_exchange_codes()

    assert isinstance(codes, dict)
    assert codes.get("V") == "IEX"
    return {"codes": codes}
