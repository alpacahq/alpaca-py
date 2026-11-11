"""Historical crypto market data."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict

from alpaca.data.models import (
    Bar,
    BarSet,
    Orderbook,
    Quote,
    QuoteSet,
    Snapshot,
    Trade,
    TradeSet,
)
from alpaca.data.requests import (
    CryptoBarsRequest,
    CryptoLatestBarRequest,
    CryptoLatestOrderbookRequest,
    CryptoLatestQuoteRequest,
    CryptoLatestTradeRequest,
    CryptoQuoteRequest,
    CryptoSnapshotRequest,
    CryptoTradesRequest,
)
from alpaca.data.timeframe import TimeFrame

from . import Context, scenario


@scenario(covers=["CryptoHistoricalDataClient.get_crypto_bars"])
def hourly_bars_with_slash_symbol(ctx: Context) -> Dict[str, Any]:
    # Symbols with "/" must survive query encoding and come back as data keys.
    start = datetime(2024, 3, 4, tzinfo=timezone.utc)
    end = datetime(2024, 3, 4, 6, tzinfo=timezone.utc)
    request = CryptoBarsRequest(
        symbol_or_symbols="BTC/USD",
        timeframe=TimeFrame.Hour,
        start=start,
        end=end,
    )
    bars = ctx.crypto_data.get_crypto_bars(request)

    assert isinstance(bars, BarSet)
    btc = bars["BTC/USD"]
    # The exact count (is the end bar included?) is pinned by the snapshot.
    assert btc
    assert all(bar.symbol == "BTC/USD" for bar in btc)
    stamps = [bar.timestamp for bar in btc]
    assert stamps == sorted(stamps)
    assert all(start <= stamp <= end for stamp in stamps)
    assert all(stamp.minute == 0 and stamp.second == 0 for stamp in stamps)
    assert isinstance(btc[0].volume, float)
    return {"bars": bars, "df": bars.df}


@scenario(
    covers=[
        "CryptoHistoricalDataClient.get_crypto_quotes",
        "CryptoHistoricalDataClient.get_crypto_trades",
    ]
)
def historical_quotes_and_trades_with_limit(ctx: Context) -> Dict[str, Any]:
    # Crypto trade history on this feed does not reach back to March 2024, and
    # trades are sparse (about one an hour), so this uses a full day in June.
    start = datetime(2024, 6, 3, tzinfo=timezone.utc)
    end = datetime(2024, 6, 4, tzinfo=timezone.utc)
    quotes = ctx.crypto_data.get_crypto_quotes(
        CryptoQuoteRequest(symbol_or_symbols="BTC/USD", start=start, end=end, limit=3)
    )
    trades = ctx.crypto_data.get_crypto_trades(
        CryptoTradesRequest(symbol_or_symbols="BTC/USD", start=start, end=end, limit=3)
    )

    assert isinstance(quotes, QuoteSet) and isinstance(trades, TradeSet)
    assert len(quotes["BTC/USD"]) == 3 and len(trades["BTC/USD"]) == 3
    quote = quotes["BTC/USD"][0]
    trade = trades["BTC/USD"][0]
    assert isinstance(quote, Quote) and isinstance(trade, Trade)
    assert quote.bid_price <= quote.ask_price
    # Crypto sizes are fractional.
    assert isinstance(trade.size, float)
    return {"quotes": quotes, "trades": trades, "trades_df": trades.df}


@scenario(
    covers=[
        "CryptoHistoricalDataClient.get_crypto_latest_bar",
        "CryptoHistoricalDataClient.get_crypto_latest_quote",
        "CryptoHistoricalDataClient.get_crypto_latest_trade",
        "CryptoHistoricalDataClient.get_crypto_latest_orderbook",
    ]
)
def latest_crypto_data_by_symbol(ctx: Context) -> Dict[str, Any]:
    symbols = ["BTC/USD", "ETH/USD"]
    bars = ctx.crypto_data.get_crypto_latest_bar(
        CryptoLatestBarRequest(symbol_or_symbols=symbols)
    )
    quotes = ctx.crypto_data.get_crypto_latest_quote(
        CryptoLatestQuoteRequest(symbol_or_symbols=symbols)
    )
    trades = ctx.crypto_data.get_crypto_latest_trade(
        CryptoLatestTradeRequest(symbol_or_symbols=symbols)
    )
    books = ctx.crypto_data.get_crypto_latest_orderbook(
        CryptoLatestOrderbookRequest(symbol_or_symbols=symbols)
    )

    for result in (bars, quotes, trades, books):
        assert isinstance(result, dict)
        assert set(result) == set(symbols)
    assert isinstance(bars, dict) and isinstance(bars["BTC/USD"], Bar)
    assert isinstance(quotes, dict) and isinstance(quotes["BTC/USD"], Quote)
    assert isinstance(trades, dict) and isinstance(trades["BTC/USD"], Trade)
    assert isinstance(books, dict)
    book = books["BTC/USD"]
    assert isinstance(book, Orderbook)
    assert book.bids and book.asks
    assert book.bids[0].price < book.asks[0].price
    return {"bars": bars, "quotes": quotes, "trades": trades, "orderbook": book}


@scenario(covers=["CryptoHistoricalDataClient.get_crypto_snapshot"])
def snapshot_by_symbol(ctx: Context) -> Dict[str, Any]:
    snapshots = ctx.crypto_data.get_crypto_snapshot(
        CryptoSnapshotRequest(symbol_or_symbols=["BTC/USD", "ETH/USD"])
    )

    # Typed as a single Snapshot in 0.45.0, but it returns a dict keyed by
    # symbol, and that is what users index. This pins the runtime behavior.
    assert isinstance(snapshots, dict)
    assert set(snapshots) == {"BTC/USD", "ETH/USD"}
    btc = snapshots["BTC/USD"]
    assert isinstance(btc, Snapshot)
    assert btc.symbol == "BTC/USD"
    return {"snapshots": snapshots}
