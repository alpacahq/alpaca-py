import urllib.parse
from datetime import datetime, timezone
from typing import Dict

from alpaca.data import Quote, Snapshot, Trade
from alpaca.data.enums import Exchange
from alpaca.data.historical.option import OptionHistoricalDataClient
from alpaca.data.models import QuoteSet, TradeSet
from alpaca.data.requests import (
    OptionLatestQuoteRequest,
    OptionLatestTradeRequest,
    OptionQuotesRequest,
    OptionSnapshotRequest,
    OptionTradesRequest,
)

# TODO: waiting for the API to be available
# def test_get_quotes(reqmock, option_client: OptionHistoricalDataClient):
#     # Test single symbol request

#     symbol = "AAPL240126P00050000"
#     start = datetime(2024, 1, 24)
#     limit = 2

#     _start_in_url = urllib.parse.quote_plus(
#         start.replace(tzinfo=timezone.utc).isoformat()
#     )

#     reqmock.get(
#         f"https://data.alpaca.markets/v1beta1/options/quotes?symbols={symbol}&start={_start_in_url}&limit={limit}",
#         text="""
#         TBD
#         """,
#     )
#     request = OptionQuotesRequest(symbol_or_symbols=symbol, start=start, limit=limit)

#     quoteset = option_client.get_option_quotes(request_params=request)

#     assert isinstance(quoteset, QuoteSet)

#     assert quoteset[symbol][0].ask_price == 158.65
#     assert quoteset[symbol][0].bid_size == 4

#     assert quoteset[symbol][0].ask_exchange == "K"

#     assert quoteset.df.index.nlevels == 2

#     assert reqmock.called_once


# def test_multisymbol_quotes(reqmock, option_client: OptionHistoricalDataClient):
#     # test multisymbol request
#     symbols = ["AAPL240126P00050000", "AAPL240126P00100000"]
#     start = datetime(2024, 1, 24)
#     _symbols_in_url = "%2C".join(s for s in symbols)

#     _start_in_url = urllib.parse.quote_plus(
#         start.replace(tzinfo=timezone.utc).isoformat()
#     )

#     reqmock.get(
#         f"https://data.alpaca.markets/v1beta1/options/quotes?start={_start_in_url}&symbols={_symbols_in_url}",
#         text="""
#         TBD
#         """,
#     )

#     request = OptionQuotesRequest(symbol_or_symbols=symbols, start=start)

#     quoteset = option_client.get_option_quotes(request_params=request)

#     assert isinstance(quoteset, QuoteSet)

#     assert quoteset["AAPL240126P00050000"][0].ask_size == 1
#     assert quoteset["AAPL240126P00100000"][0].bid_price == 840.75

#     assert quoteset["AAPL240126P00050000"][0].bid_exchange == "Q"

#     assert quoteset.df.index.nlevels == 2

#     assert reqmock.called_once


# def test_get_quotes_single_empty_response(
#     reqmock, option_client: OptionHistoricalDataClient
# ):
#     symbol = "AAPL240126P00050000"
#     start = datetime(2024, 1, 24)
#     limit = 2

#     _start_in_url = urllib.parse.quote_plus(
#         start.replace(tzinfo=timezone.utc).isoformat()
#     )

#     reqmock.get(
#         f"https://data.alpaca.markets/v1beta1/options/quotes?symbols={symbol}&start={_start_in_url}&limit={limit}",
#         text="""
#         TBD
#         """,
#     )
#     request = OptionQuotesRequest(symbol_or_symbols=symbol, start=start, limit=limit)

#     quoteset = option_client.get_option_quotes(request_params=request)

#     assert isinstance(quoteset, QuoteSet)

#     assert quoteset.dict() == {"AAPL240126P00050000": []}

#     assert len(quoteset.df) == 0

#     assert reqmock.called_once


# def test_get_quotes_multi_empty_response(
#     reqmock, option_client: OptionHistoricalDataClient
# ):
#     symbol = "AAPL240126P00050000"
#     start = datetime(2024, 1, 24)
#     limit = 2

#     _start_in_url = urllib.parse.quote_plus(
#         start.replace(tzinfo=timezone.utc).isoformat()
#     )

#     reqmock.get(
#         f"https://data.alpaca.markets/v1beta1/options/quotes?symbols={symbol}&start={_start_in_url}&limit={limit}",
#         text="""
#         TBD
#         """,
#     )
#     request = OptionQuotesRequest(symbol_or_symbols=[symbol], start=start, limit=limit)

#     quoteset = option_client.get_option_quotes(request_params=request)

#     assert isinstance(quoteset, QuoteSet)

#     assert quoteset.dict() == {}

#     assert len(quoteset.df) == 0

#     assert reqmock.called_once


# def test_get_trades(reqmock, option_client: OptionHistoricalDataClient):
#     # Test single symbol request
#     symbol = "AAPL240112C00182500"
#     start = datetime(2024, 1, 24)
#     limit = 2

#     _start_in_url = urllib.parse.quote_plus(
#         start.replace(tzinfo=timezone.utc).isoformat()
#     )

#     reqmock.get(
#         f"https://data.alpaca.markets/v1beta1/options/trades?symbols={symbol}&start={_start_in_url}&limit={limit}",
#         text="""
#         TBD
#         """,
#     )

#     request = OptionTradesRequest(symbol_or_symbols=symbol, start=start, limit=limit)

#     tradeset = option_client.get_option_trades(request_params=request)

#     assert isinstance(tradeset, TradeSet)

#     assert tradeset[symbol][0].price == 2.36
#     assert tradeset[symbol][0].size == 2

#     assert tradeset[symbol][0].exchange == Exchange.D

#     assert tradeset.df.index.nlevels == 2

#     assert reqmock.called_once


# def test_multisymbol_get_trades(reqmock, option_client: OptionHistoricalDataClient):
#     # test multisymbol request
#     symbols = ["AAPL240126P00050000", "AAPL240126P00100000"]
#     start = datetime(2024, 1, 24)
#     _symbols_in_url = "%2C".join(s for s in symbols)

#     _start_in_url = urllib.parse.quote_plus(
#         start.replace(tzinfo=timezone.utc).isoformat()
#     )

#     reqmock.get(
#         f"https://data.alpaca.markets/v1beta1/options/trades?start={_start_in_url}&symbols={_symbols_in_url}",
#         text="""
#         TBD
#         """,
#     )

#     request = OptionTradesRequest(symbol_or_symbols=symbols, start=start)

#     tradeset = option_client.get_option_trades(request_params=request)

#     assert isinstance(tradeset, TradeSet)

#     assert tradeset["AAPL240126P00050000"][0].size == 1
#     assert tradeset["AAPL240126P00100000"][0].price == 833

#     assert tradeset["AAPL240126P00050000"][0].exchange == Exchange.D

#     assert tradeset.df.index[0][1].day == 24
#     assert tradeset.df.index.nlevels == 2

#     assert reqmock.called_once


# def test_get_trades_single_empty_response(
#     reqmock, option_client: OptionHistoricalDataClient
# ):
#     symbol = "AAPL240126P00050000"
#     start = datetime(2024, 1, 24)
#     limit = 2

#     _start_in_url = urllib.parse.quote_plus(
#         start.replace(tzinfo=timezone.utc).isoformat()
#     )

#     reqmock.get(
#         f"https://data.alpaca.markets/v1beta1/options/trades?symbols={symbol}&start={_start_in_url}&limit={limit}",
#         text="""
#         TBD
#         """,
#     )

#     request = OptionTradesRequest(symbol_or_symbols=symbol, start=start, limit=limit)

#     tradeset = option_client.get_option_trades(request_params=request)

#     assert isinstance(tradeset, TradeSet)

#     assert tradeset.dict() == {"AAPL240126P00050000": []}

#     assert len(tradeset.df) == 0

#     assert reqmock.called_once


# def test_get_trades_multi_empty_response(
#     reqmock, option_client: OptionHistoricalDataClient
# ):
#     symbol = "AAPL240126P00050000"
#     start = datetime(2024, 1, 24)
#     limit = 2

#     _start_in_url = urllib.parse.quote_plus(
#         start.replace(tzinfo=timezone.utc).isoformat()
#     )

#     reqmock.get(
#         f"https://data.alpaca.markets/v1beta1/options/trades?symbols={symbol}&start={_start_in_url}&limit={limit}",
#         text="""
#         TBD
#         """,
#     )

#     request = OptionTradesRequest(symbol_or_symbols=[symbol], start=start, limit=limit)

#     tradeset = option_client.get_option_trades(request_params=request)

#     assert isinstance(tradeset, TradeSet)

#     assert tradeset.dict() == {}

#     assert len(tradeset.df) == 0

#     assert reqmock.called_once


def test_get_latest_trade(reqmock, option_client: OptionHistoricalDataClient):
    # Test single symbol request
    symbol = "AAPL240126P00050000"

    reqmock.get(
        f"https://data.alpaca.markets/v1beta1/options/trades/latest?symbols={symbol}",
        text="""
    {
        "symbol": "AAPL240126P00050000",
        "trade": {
            "t": "2024-01-24T14:02:09.722539521Z",
            "x": "A",
            "p": 0.06,
            "s": 1,
            "c": "I"
        }
    }
        """,
    )
    request = OptionLatestTradeRequest(symbol_or_symbols=symbol)

    trades = option_client.get_option_latest_trade(request_params=request)

    assert isinstance(trades, Dict)

    trade = trades[symbol]

    assert isinstance(trade, Trade)

    assert trade.price == 0.06
    assert trade.size == 1

    assert trade.exchange == Exchange.A

    assert reqmock.called_once


def test_get_multisymbol_latest_trade(
    reqmock, option_client: OptionHistoricalDataClient
):
    symbols = ["AAPL240126P00050000", "AAPL240126P00100000"]
    _symbols_in_url = "%2C".join(s for s in symbols)
    reqmock.get(
        f"https://data.alpaca.markets/v1beta1/options/trades/latest?symbols={_symbols_in_url}",
        text="""
    {
        "trades": {
            "AAPL240126P00050000": {
                "t": "2024-01-24T14:02:09.722539521Z",
                "x": "A",
                "p": 0.06,
                "s": 1,
                "c": "I"
            },
            "AAPL240126P00100000": {
                "t": "2024-01-24T19:59:59.405545378Z",
                "x": "M",
                "p": 0.59,
                "s": 50,
                "c": "I"
            }
        }
    }
        """,
    )
    request = OptionLatestTradeRequest(symbol_or_symbols=symbols)

    trades = option_client.get_option_latest_trade(request_params=request)

    assert isinstance(trades, Dict)

    trade = trades["AAPL240126P00050000"]

    assert isinstance(trade, Trade)

    assert trade.price == 0.06
    assert trade.size == 1

    assert trade.exchange == Exchange.A

    assert reqmock.called_once


def test_get_latest_trade_multi_not_found(
    reqmock, option_client: OptionHistoricalDataClient
):
    symbol = "AAAAPL240126P00050000PL"

    reqmock.get(
        f"https://data.alpaca.markets/v1beta1/options/trades/latest?symbols={symbol}",
        text="""
    {
        "trades": {}
    }
        """,
    )
    request = OptionLatestTradeRequest(symbol_or_symbols=[symbol])

    trades = option_client.get_option_latest_trade(request_params=request)

    assert isinstance(trades, Dict)

    assert trades == {}

    assert reqmock.called_once


def test_get_latest_quote(reqmock, option_client: OptionHistoricalDataClient):
    # Test single symbol request
    symbol = "AAPL240126P00050000"

    reqmock.get(
        f"https://data.alpaca.markets/v1beta1/options/quotes/latest?symbols={symbol}",
        text="""
    {
        "symbol": "AAPL240126P00050000",
        "quote": {
            "t": "2024-01-24T14:02:43.651613184Z",
            "ax": "N",
            "ap": 0.06,
            "as": 1593,
            "bx": "N",
            "bp": 0.05,
            "bs": 1344,
            "c": "B"
        }
    }
        """,
    )

    request = OptionLatestQuoteRequest(symbol_or_symbols=symbol)

    quotes = option_client.get_option_latest_quote(request)

    assert isinstance(quotes, Dict)

    quote = quotes[symbol]

    assert isinstance(quote, Quote)

    assert quote.ask_price == 0.06
    assert quote.bid_size == 1344

    assert quote.bid_exchange == "N"

    assert reqmock.called_once


def test_get_latest_quote_single_empty_response(
    reqmock, option_client: OptionHistoricalDataClient
):
    # Test single symbol request
    symbol = "AAPL240126P00050000"

    reqmock.get(
        f"https://data.alpaca.markets/v1beta1/options/quotes/latest?symbols={symbol}",
        text="""
    {
        "quotes": {}
    }
        """,
    )

    request = OptionLatestQuoteRequest(symbol_or_symbols=symbol)

    quote = option_client.get_option_latest_quote(request)

    assert isinstance(quote, Dict)

    assert quote == {}

    assert reqmock.called_once


def test_get_latest_quote_multi_empty_response(
    reqmock, option_client: OptionHistoricalDataClient
):
    symbol = "AAPL240126P00050000"

    reqmock.get(
        f"https://data.alpaca.markets/v1beta1/options/quotes/latest?symbols={symbol}",
        text="""
    {
        "quotes": {}
    }
        """,
    )

    request = OptionLatestQuoteRequest(symbol_or_symbols=[symbol])

    quotes = option_client.get_option_latest_quote(request)

    assert isinstance(quotes, Dict)

    assert quotes == {}

    assert reqmock.called_once


def test_get_snapshot(reqmock, option_client: OptionHistoricalDataClient):
    # Test single symbol request
    symbol = "AAPL240126P00050000"

    reqmock.get(
        f"https://data.alpaca.markets/v1beta1/options/snapshots?symbols={symbol}",
        text="""
    {
        "snapshots": {
            "AAPL240126P00050000":{
                "latestQuote": {
                    "ap":0.59,
                    "as":458,
                    "ax":"X",
                    "bp":0.48,
                    "bs":396,
                    "bx":"X",
                    "c":" ",
                    "t":"2024-02-02T20:59:59.731674112Z"
                },
                "latestTrade": {
                    "c":"I",
                    "p":0.52,
                    "s":1,
                    "t":"2024-02-02T17:29:53.55240448Z",
                    "x":"W"
                }
            }
        }
    }
        """,
    )

    request = OptionSnapshotRequest(symbol_or_symbols=symbol)

    snapshots = option_client.get_option_snapshot(request)

    assert isinstance(snapshots, Dict)

    snapshot = snapshots[symbol]

    assert isinstance(snapshot, Snapshot)

    assert snapshot.latest_trade.price == 0.52
    assert snapshot.latest_quote.bid_size == 396
    assert snapshot.minute_bar is None
    assert snapshot.daily_bar is None
    assert snapshot.previous_daily_bar is None

    assert reqmock.called_once


def test_get_snapshot_single_empty_response(
    reqmock, option_client: OptionHistoricalDataClient
):
    symbol = "AAPL240126P00050000"

    reqmock.get(
        f"https://data.alpaca.markets/v1beta1/options/snapshots?symbols={symbol}",
        text="""
    {
        "snapshots":{}
    }
        """,
    )

    request = OptionSnapshotRequest(symbol_or_symbols=symbol)

    snapshot = option_client.get_option_snapshot(request)

    assert isinstance(snapshot, Dict)

    assert snapshot == {}

    assert reqmock.called_once


def test_get_snapshot_multi_empty_response(
    reqmock, option_client: OptionHistoricalDataClient
):
    symbol = "AAPL240126P00050000"

    reqmock.get(
        f"https://data.alpaca.markets/v1beta1/options/snapshots?symbols={symbol}",
        text="""
    {
        "snapshots":{}
    }
        """,
    )

    request = OptionSnapshotRequest(symbol_or_symbols=[symbol])

    snapshots = option_client.get_option_snapshot(request)

    assert isinstance(snapshots, Dict)

    assert snapshots == {}

    assert reqmock.called_once
