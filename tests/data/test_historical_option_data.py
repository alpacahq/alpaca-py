import urllib.parse
from datetime import datetime, timezone
from typing import Dict

from alpaca.data import Quote, Snapshot, Trade
from alpaca.data.enums import Exchange
from alpaca.data.historical.option import OptionHistoricalDataClient
from alpaca.data.requests import (
    OptionLatestQuoteRequest,
    OptionLatestTradeRequest,
    OptionSnapshotRequest,
)


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
