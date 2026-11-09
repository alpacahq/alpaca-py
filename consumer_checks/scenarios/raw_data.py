"""raw_data=True: methods return the API's JSON instead of models.

Users who opt in index these dicts and lists directly, so their keys, nesting
and value types are part of the contract as much as the models are. One
scenario per client family, read only, on the same fixed inputs as the model
scenarios.
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any, Dict

from alpaca.data.enums import (
    CorporateActionsType,
    DataFeed,
    MostActivesBy,
    OptionsFeed,
)
from alpaca.data.requests import (
    CorporateActionsRequest,
    CryptoBarsRequest,
    CryptoLatestOrderbookRequest,
    CryptoSnapshotRequest,
    MostActivesRequest,
    NewsRequest,
    OptionBarsRequest,
    OptionChainRequest,
    StockBarsRequest,
    StockLatestQuoteRequest,
    StockSnapshotRequest,
)
from alpaca.data.timeframe import TimeFrame
from alpaca.trading.enums import ContractType
from alpaca.trading.requests import GetCalendarRequest

from . import Context, scenario

WEEK_START = datetime(2024, 3, 4, tzinfo=timezone.utc)
WEEK_END = datetime(2024, 3, 9, tzinfo=timezone.utc)
EXPIRED_CONTRACT = "AAPL240308C00175000"


@scenario(
    covers=[
        "TradingClient.get_clock",
        "TradingClient.get_asset",
        "TradingClient.get_calendar",
        "TradingClient.get_account",
    ]
)
def trading_raw_responses(ctx: Context) -> Dict[str, Any]:
    clock = ctx.raw_trading.get_clock()
    asset = ctx.raw_trading.get_asset("AAPL")
    # Typed as List[Calendar] | dict, but raw mode returns a list of dicts, so
    # raw users have to fall back to Any to index it.
    days: Any = ctx.raw_trading.get_calendar(
        GetCalendarRequest(start=date(2024, 3, 4), end=date(2024, 3, 8))
    )
    account = ctx.raw_trading.get_account()

    assert isinstance(clock, dict) and isinstance(clock["is_open"], bool)
    assert isinstance(asset, dict) and asset["symbol"] == "AAPL"
    # The API's own spelling, not the model's: "class", not "asset_class".
    assert asset["class"] == "us_equity"
    assert isinstance(days, list) and len(days) == 5
    assert days[0]["date"] == "2024-03-04"
    assert isinstance(account, dict)
    # Money stays a decimal string, as the API sends it.
    assert isinstance(account["cash"], str)
    return {"clock": clock, "asset": asset, "days": days, "account": account}


@scenario(
    covers=[
        "StockHistoricalDataClient.get_stock_bars",
        "StockHistoricalDataClient.get_stock_latest_quote",
        "StockHistoricalDataClient.get_stock_snapshot",
    ]
)
def stock_data_raw_responses(ctx: Context) -> Dict[str, Any]:
    bars = ctx.raw_stock_data.get_stock_bars(
        StockBarsRequest(
            symbol_or_symbols=["AAPL", "MSFT"],
            timeframe=TimeFrame.Day,
            start=WEEK_START,
            end=WEEK_END,
            feed=DataFeed.IEX,
        )
    )
    quotes = ctx.raw_stock_data.get_stock_latest_quote(
        StockLatestQuoteRequest(symbol_or_symbols=["AAPL"], feed=DataFeed.IEX)
    )
    snapshots = ctx.raw_stock_data.get_stock_snapshot(
        StockSnapshotRequest(symbol_or_symbols=["AAPL"], feed=DataFeed.IEX)
    )

    # Keyed by symbol, with the API's short keys ("t", "o", ...) inside.
    assert isinstance(bars, dict) and set(bars) == {"AAPL", "MSFT"}
    assert isinstance(bars["AAPL"], list) and len(bars["AAPL"]) == 5
    assert {"t", "o", "h", "l", "c", "v"} <= set(bars["AAPL"][0])
    assert isinstance(quotes, dict) and {"ap", "bp"} <= set(quotes["AAPL"])
    assert isinstance(snapshots, dict) and "latestTrade" in snapshots["AAPL"]
    return {"bars": bars, "quotes": quotes, "snapshots": snapshots}


@scenario(
    covers=[
        "CryptoHistoricalDataClient.get_crypto_bars",
        "CryptoHistoricalDataClient.get_crypto_latest_orderbook",
        "CryptoHistoricalDataClient.get_crypto_snapshot",
    ]
)
def crypto_data_raw_responses(ctx: Context) -> Dict[str, Any]:
    bars = ctx.raw_crypto_data.get_crypto_bars(
        CryptoBarsRequest(
            symbol_or_symbols="BTC/USD",
            timeframe=TimeFrame.Hour,
            start=WEEK_START,
            end=datetime(2024, 3, 4, 6, tzinfo=timezone.utc),
        )
    )
    books = ctx.raw_crypto_data.get_crypto_latest_orderbook(
        CryptoLatestOrderbookRequest(symbol_or_symbols=["BTC/USD"])
    )
    snapshots = ctx.raw_crypto_data.get_crypto_snapshot(
        CryptoSnapshotRequest(symbol_or_symbols=["BTC/USD"])
    )

    assert isinstance(bars, dict) and isinstance(bars["BTC/USD"], list)
    assert bars["BTC/USD"] and "t" in bars["BTC/USD"][0]
    assert isinstance(books, dict) and {"b", "a"} <= set(books["BTC/USD"])
    assert isinstance(snapshots, dict) and "BTC/USD" in snapshots
    return {"bars": bars, "orderbook": books, "snapshots": snapshots}


@scenario(
    covers=[
        "OptionHistoricalDataClient.get_option_chain",
        "OptionHistoricalDataClient.get_option_bars",
    ]
)
def option_data_raw_responses(ctx: Context) -> Dict[str, Any]:
    chain = ctx.raw_option_data.get_option_chain(
        OptionChainRequest(
            underlying_symbol="AAPL",
            feed=OptionsFeed.INDICATIVE,
            type=ContractType.CALL,
            strike_price_gte=200,
            strike_price_lte=205,
        )
    )
    bars = ctx.raw_option_data.get_option_bars(
        OptionBarsRequest(
            symbol_or_symbols=EXPIRED_CONTRACT,
            timeframe=TimeFrame.Day,
            start=WEEK_START,
            end=WEEK_END,
        )
    )

    assert isinstance(chain, dict) and chain
    first = chain[sorted(chain)[0]]
    assert isinstance(first, dict)
    assert isinstance(bars, dict) and isinstance(bars[EXPIRED_CONTRACT], list)
    # The chain changes as contracts roll; keep one entry and the bars.
    return {"chain_entry": first, "bars": bars}


@scenario(
    covers=[
        "NewsClient.get_news",
        "ScreenerClient.get_most_actives",
        "CorporateActionsClient.get_corporate_actions",
    ]
)
def news_screener_corporate_actions_raw_responses(ctx: Context) -> Dict[str, Any]:
    news = ctx.raw_news.get_news(
        NewsRequest(
            symbols="AAPL",
            start=WEEK_START,
            end=datetime(2024, 3, 5, tzinfo=timezone.utc),
            limit=3,
        )
    )
    actives = ctx.raw_screener.get_most_actives(
        MostActivesRequest(top=5, by=MostActivesBy.VOLUME)
    )
    actions = ctx.raw_corporate_actions.get_corporate_actions(
        CorporateActionsRequest(
            symbols=["AAPL"],
            types=[CorporateActionsType.CASH_DIVIDEND],
            start=date(2024, 1, 1),
            end=date(2024, 3, 31),
        )
    )

    assert isinstance(news, dict) and isinstance(news["news"], list)
    assert news["news"] and "AAPL" in news["news"][0]["symbols"]
    assert isinstance(actives, dict) and isinstance(actives["most_actives"], list)
    # Grouped by action type, as the API sends it.
    assert isinstance(actions, dict) and isinstance(actions["cash_dividends"], list)
    return {"news": news, "actives": actives, "actions": actions}
