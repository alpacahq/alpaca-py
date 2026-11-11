"""Historical and latest stock market data."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict

from alpaca.data.enums import Adjustment, DataFeed
from alpaca.data.models import Bar, BarSet, Quote, QuoteSet, Snapshot, Trade, TradeSet
from alpaca.data.requests import (
    StockBarsRequest,
    StockLatestBarRequest,
    StockLatestQuoteRequest,
    StockLatestTradeRequest,
    StockQuotesRequest,
    StockSnapshotRequest,
    StockTradesRequest,
)
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit

from . import Context, scenario

# A fixed past week (Mon 4 to Fri 8 March 2024), so live runs see stable data.
# IEX is the feed available to every paper account.
WEEK_START = datetime(2024, 3, 4, tzinfo=timezone.utc)
WEEK_END = datetime(2024, 3, 9, tzinfo=timezone.utc)


@scenario(covers=["StockHistoricalDataClient.get_stock_bars"])
def daily_bars_for_two_symbols(ctx: Context) -> Dict[str, Any]:
    request = StockBarsRequest(
        symbol_or_symbols=["AAPL", "MSFT"],
        timeframe=TimeFrame.Day,
        start=WEEK_START,
        end=WEEK_END,
        adjustment=Adjustment.RAW,
        feed=DataFeed.IEX,
    )
    bars = ctx.stock_data.get_stock_bars(request)

    assert isinstance(bars, BarSet)
    assert set(bars.data) == {"AAPL", "MSFT"}
    aapl = bars["AAPL"]
    assert len(aapl) == 5
    first = aapl[0]
    assert isinstance(first, Bar)
    assert first.symbol == "AAPL"
    assert first.low <= first.open <= first.high
    assert first.timestamp.tzinfo is not None

    df = bars.df
    assert list(df.index.names) == ["symbol", "timestamp"]
    assert {"open", "high", "low", "close", "volume"} <= set(df.columns)
    return {"bars": bars, "df": df}


@scenario(covers=["StockHistoricalDataClient.get_stock_bars"])
def intraday_bars_with_limit(ctx: Context) -> Dict[str, Any]:
    # A custom timeframe and a total limit: both are serialized by the SDK.
    request = StockBarsRequest(
        symbol_or_symbols="AAPL",
        timeframe=TimeFrame(15, TimeFrameUnit.Minute),
        start=WEEK_START,
        end=WEEK_END,
        limit=10,
        feed=DataFeed.IEX,
    )
    bars = ctx.stock_data.get_stock_bars(request)

    assert isinstance(bars, BarSet)
    assert len(bars["AAPL"]) == 10
    stamps = [bar.timestamp for bar in bars["AAPL"]]
    assert stamps == sorted(stamps)
    assert (stamps[1] - stamps[0]).total_seconds() % (15 * 60) == 0
    return {"bars": bars}


@scenario(covers=["StockHistoricalDataClient.get_stock_quotes"])
def historical_quotes_with_limit(ctx: Context) -> Dict[str, Any]:
    request = StockQuotesRequest(
        symbol_or_symbols="AAPL",
        start=WEEK_START,
        end=WEEK_END,
        limit=3,
        feed=DataFeed.IEX,
    )
    quotes = ctx.stock_data.get_stock_quotes(request)

    assert isinstance(quotes, QuoteSet)
    assert len(quotes["AAPL"]) == 3
    quote = quotes["AAPL"][0]
    assert isinstance(quote, Quote)
    assert quote.bid_price <= quote.ask_price or quote.ask_price == 0
    return {"quotes": quotes, "df": quotes.df}


@scenario(covers=["StockHistoricalDataClient.get_stock_latest_quote"])
def latest_quote_by_symbol(ctx: Context) -> Dict[str, Any]:
    request = StockLatestQuoteRequest(symbol_or_symbols=["AAPL"], feed=DataFeed.IEX)
    latest = ctx.stock_data.get_stock_latest_quote(request)

    assert isinstance(latest, dict)
    quote = latest["AAPL"]
    assert isinstance(quote, Quote)
    assert quote.symbol == "AAPL"
    return {"latest": latest}


@scenario(covers=["StockHistoricalDataClient.get_stock_trades"])
def historical_trades_with_limit(ctx: Context) -> Dict[str, Any]:
    request = StockTradesRequest(
        symbol_or_symbols="AAPL",
        start=WEEK_START,
        end=WEEK_END,
        limit=3,
        feed=DataFeed.IEX,
    )
    trades = ctx.stock_data.get_stock_trades(request)

    assert isinstance(trades, TradeSet)
    assert len(trades["AAPL"]) == 3
    trade = trades["AAPL"][0]
    assert isinstance(trade, Trade)
    assert trade.symbol == "AAPL"
    assert trade.price > 0 and trade.size > 0
    return {"trades": trades, "df": trades.df}


@scenario(
    covers=[
        "StockHistoricalDataClient.get_stock_latest_trade",
        "StockHistoricalDataClient.get_stock_latest_bar",
    ]
)
def latest_trade_and_bar_by_symbol(ctx: Context) -> Dict[str, Any]:
    symbols = ["AAPL", "MSFT"]
    trades = ctx.stock_data.get_stock_latest_trade(
        StockLatestTradeRequest(symbol_or_symbols=symbols, feed=DataFeed.IEX)
    )
    bars = ctx.stock_data.get_stock_latest_bar(
        StockLatestBarRequest(symbol_or_symbols=symbols, feed=DataFeed.IEX)
    )

    assert isinstance(trades, dict) and isinstance(bars, dict)
    assert set(trades) == set(bars) == set(symbols)
    assert all(isinstance(trade, Trade) for trade in trades.values())
    assert all(isinstance(bar, Bar) for bar in bars.values())
    assert trades["AAPL"].symbol == bars["AAPL"].symbol == "AAPL"
    return {"trades": trades, "bars": bars}


@scenario(covers=["StockHistoricalDataClient.get_stock_snapshot"])
def snapshot_for_two_symbols(ctx: Context) -> Dict[str, Any]:
    snapshots = ctx.stock_data.get_stock_snapshot(
        StockSnapshotRequest(symbol_or_symbols=["AAPL", "MSFT"], feed=DataFeed.IEX)
    )

    assert isinstance(snapshots, dict)
    assert set(snapshots) == {"AAPL", "MSFT"}
    aapl = snapshots["AAPL"]
    assert isinstance(aapl, Snapshot)
    assert aapl.symbol == "AAPL"
    assert isinstance(aapl.daily_bar, Bar)
    assert isinstance(aapl.latest_trade, Trade)
    return {"snapshots": snapshots}
