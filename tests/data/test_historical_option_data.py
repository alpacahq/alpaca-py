import urllib.parse
from datetime import datetime, timezone
from typing import Dict

from alpaca.data import Quote, Snapshot, Trade
from alpaca.data.enums import DataFeed, Exchange
from alpaca.data.historical.option import OptionHistoricalDataClient
from alpaca.data.models import QuoteSet, TradeSet
from alpaca.data.requests import (
    OptionLatestQuoteRequest,
    OptionLatestTradeRequest,
    OptionQuotesRequest,
    OptionSnapshotRequest,
    OptionTradesRequest,
)


def test_get_quotes(reqmock, option_client: OptionHistoricalDataClient):
    # Test single symbol request

    symbol = "AAPL240126P00050000"
    start = datetime(2024, 1, 24)
    limit = 2

    _start_in_url = urllib.parse.quote_plus(
        start.replace(tzinfo=timezone.utc).isoformat()
    )

    reqmock.get(
        f"https://data.alpaca.markets/v1beta1/options/quotes?symbols={symbol}&start={_start_in_url}&limit={limit}",
        text="""
    {
        "quotes": [
            {
                "t": "2024-01-24T09:00:00.000059Z",
                "ax": "K",
                "ap": 158.65,
                "as": 1,
                "bx": "Q",
                "bp": 159.52,
                "bs": 4,
                "c": [
                    "R"
                ],
                "z": "C"
            },
            {
                "t": "2024-01-25T09:00:00.000059Z",
                "ax": "K",
                "ap": 158.8,
                "as": 1,
                "bx": "Q",
                "bp": 159.52,
                "bs": 4,
                "c": [
                    "R"
                ],
                "z": "C"
            }
        ],
        "symbol": "AAPL240126P00050000",
        "next_page_token": "QUFQTHwyMDIyLTAzLTA5VDA5OjAwOjAwLjAwMDA1OTAwMFp8Q0ZEQUU5QTg="
    }
        """,
    )
    request = OptionQuotesRequest(symbol_or_symbols=symbol, start=start, limit=limit)

    quoteset = option_client.get_option_quotes(request_params=request)

    assert isinstance(quoteset, QuoteSet)

    assert quoteset[symbol][0].ask_price == 158.65
    assert quoteset[symbol][0].bid_size == 4

    assert quoteset[symbol][0].ask_exchange == "K"

    assert quoteset.df.index.nlevels == 2

    assert reqmock.called_once


def test_multisymbol_quotes(reqmock, option_client: OptionHistoricalDataClient):
    # test multisymbol request
    symbols = ["AAPL240126P00050000", "AAPL240126P00100000"]
    start = datetime(2024, 1, 24)
    _symbols_in_url = "%2C".join(s for s in symbols)

    _start_in_url = urllib.parse.quote_plus(
        start.replace(tzinfo=timezone.utc).isoformat()
    )

    reqmock.get(
        f"https://data.alpaca.markets/v1beta1/options/quotes?start={_start_in_url}&symbols={_symbols_in_url}",
        text="""
    {
        "quotes": {
            "AAPL240126P00050000": [
                {
                    "t": "2024-01-24T09:00:00.000059Z",
                    "ax": "K",
                    "ap": 158.65,
                    "as": 1,
                    "bx": "Q",
                    "bp": 159.52,
                    "bs": 4,
                    "c": [
                        "R"
                    ],
                    "z": "C"
                }
            ],
            "AAPL240126P00100000": [
                {
                    "t": "2024-01-24T09:00:00.000805Z",
                    "ax": "K",
                    "ap": 830,
                    "as": 1,
                    "bx": "P",
                    "bp": 840.75,
                    "bs": 1,
                    "c": [
                        "R"
                    ],
                    "z": "C"
                }
            ]
        },
        "next_page_token": null
    }
        """,
    )

    request = OptionQuotesRequest(symbol_or_symbols=symbols, start=start)

    quoteset = option_client.get_option_quotes(request_params=request)

    assert isinstance(quoteset, QuoteSet)

    assert quoteset["AAPL240126P00050000"][0].ask_size == 1
    assert quoteset["AAPL240126P00100000"][0].bid_price == 840.75

    assert quoteset["AAPL240126P00050000"][0].bid_exchange == "Q"

    assert quoteset.df.index.nlevels == 2

    assert reqmock.called_once


def test_get_quotes_single_empty_response(
    reqmock, option_client: OptionHistoricalDataClient
):
    symbol = "AAPL240126P00050000"
    start = datetime(2024, 1, 24)
    limit = 2

    _start_in_url = urllib.parse.quote_plus(
        start.replace(tzinfo=timezone.utc).isoformat()
    )

    reqmock.get(
        f"https://data.alpaca.markets/v1beta1/options/quotes?symbols={symbol}&start={_start_in_url}&limit={limit}",
        text="""
    {
        "next_page_token": null,
        "quotes": null,
        "symbol": "AAPL240126P00050000"
    }
        """,
    )
    request = OptionQuotesRequest(symbol_or_symbols=symbol, start=start, limit=limit)

    quoteset = option_client.get_option_quotes(request_params=request)

    assert isinstance(quoteset, QuoteSet)

    assert quoteset.dict() == {"AAPL240126P00050000": []}

    assert len(quoteset.df) == 0

    assert reqmock.called_once


def test_get_quotes_multi_empty_response(
    reqmock, option_client: OptionHistoricalDataClient
):
    symbol = "AAPL240126P00050000"
    start = datetime(2024, 1, 24)
    limit = 2

    _start_in_url = urllib.parse.quote_plus(
        start.replace(tzinfo=timezone.utc).isoformat()
    )

    reqmock.get(
        f"https://data.alpaca.markets/v1beta1/options/quotes?symbols={symbol}&start={_start_in_url}&limit={limit}",
        text="""
    {
        "next_page_token": null,
        "quotes": {}
    }
        """,
    )
    request = OptionQuotesRequest(symbol_or_symbols=[symbol], start=start, limit=limit)

    quoteset = option_client.get_option_quotes(request_params=request)

    assert isinstance(quoteset, QuoteSet)

    assert quoteset.dict() == {}

    assert len(quoteset.df) == 0

    assert reqmock.called_once


def test_get_trades(reqmock, option_client: OptionHistoricalDataClient):
    # Test single symbol request
    symbol = "AAPL240126P00050000"
    start = datetime(2024, 1, 24)
    limit = 2

    _start_in_url = urllib.parse.quote_plus(
        start.replace(tzinfo=timezone.utc).isoformat()
    )

    reqmock.get(
        f"https://data.alpaca.markets/v1beta1/options/trades?symbols={symbol}&start={_start_in_url}&limit={limit}",
        text="""
    {
        "trades": [
            {
                "t": "2024-01-24T05:00:02.183Z",
                "x": "D",
                "p": 159.07,
                "s": 1,
                "c": [
                    "@",
                    "T",
                    "I"
                ],
                "i": 151,
                "z": "C"
            },
            {
                "t": "2024-01-24T05:00:16.91Z",
                "x": "D",
                "p": 159.07,
                "s": 2,
                "c": [
                    "@",
                    "T",
                    "I"
                ],
                "i": 168,
                "z": "C"
            }
        ],
        "symbol": "AAPL240126P00050000",
        "next_page_token": "QUFQTHwyMDIyLTAzLTA5VDA1OjAwOjE2LjkxMDAwMDAwMFp8RHwwOTIyMzM3MjAzNjg1NDc3NTk3Ng=="
    }
        """,
    )

    request = OptionTradesRequest(symbol_or_symbols=symbol, start=start, limit=limit)

    tradeset = option_client.get_option_trades(request_params=request)

    assert isinstance(tradeset, TradeSet)

    assert tradeset[symbol][0].price == 159.07
    assert tradeset[symbol][0].size == 1

    assert tradeset[symbol][0].exchange == Exchange.D

    assert tradeset.df.index.nlevels == 2

    assert reqmock.called_once


def test_multisymbol_get_trades(reqmock, option_client: OptionHistoricalDataClient):
    # test multisymbol request
    symbols = ["AAPL240126P00050000", "AAPL240126P00100000"]
    start = datetime(2024, 1, 24)
    _symbols_in_url = "%2C".join(s for s in symbols)

    _start_in_url = urllib.parse.quote_plus(
        start.replace(tzinfo=timezone.utc).isoformat()
    )

    reqmock.get(
        f"https://data.alpaca.markets/v1beta1/options/trades?start={_start_in_url}&symbols={_symbols_in_url}",
        text="""
    {
        "trades": {
            "AAPL240126P00050000": [
                {
                    "t": "2024-01-24T05:00:02.183Z",
                    "x": "D",
                    "p": 159.07,
                    "s": 1,
                    "c": [
                        "@",
                        "T",
                        "I"
                    ],
                    "i": 151,
                    "z": "C"
                }
            ],
            "AAPL240126P00100000": [
                {
                    "t": "2024-01-24T05:08:03.035Z",
                    "x": "D",
                    "p": 833,
                    "s": 1,
                    "c": [
                        "@",
                        "T",
                        "I"
                    ],
                    "i": 145,
                    "z": "C"
                }
            ]
        },
        "next_page_token": null
    }
        """,
    )

    request = OptionTradesRequest(symbol_or_symbols=symbols, start=start)

    tradeset = option_client.get_option_trades(request_params=request)

    assert isinstance(tradeset, TradeSet)

    assert tradeset["AAPL240126P00050000"][0].size == 1
    assert tradeset["AAPL240126P00100000"][0].price == 833

    assert tradeset["AAPL240126P00050000"][0].exchange == Exchange.D

    assert tradeset.df.index[0][1].day == 24
    assert tradeset.df.index.nlevels == 2

    assert reqmock.called_once


def test_get_trades_single_empty_response(
    reqmock, option_client: OptionHistoricalDataClient
):
    symbol = "AAPL240126P00050000"
    start = datetime(2024, 1, 24)
    limit = 2

    _start_in_url = urllib.parse.quote_plus(
        start.replace(tzinfo=timezone.utc).isoformat()
    )

    reqmock.get(
        f"https://data.alpaca.markets/v1beta1/options/trades?symbols={symbol}&start={_start_in_url}&limit={limit}",
        text="""
    {
        "next_page_token": null,
        "trades": null,
        "symbol": "AAPL240126P00050000"
    }
        """,
    )

    request = OptionTradesRequest(symbol_or_symbols=symbol, start=start, limit=limit)

    tradeset = option_client.get_option_trades(request_params=request)

    assert isinstance(tradeset, TradeSet)

    assert tradeset.dict() == {"AAPL240126P00050000": []}

    assert len(tradeset.df) == 0

    assert reqmock.called_once


def test_get_trades_multi_empty_response(
    reqmock, option_client: OptionHistoricalDataClient
):
    symbol = "AAPL240126P00050000"
    start = datetime(2024, 1, 24)
    limit = 2

    _start_in_url = urllib.parse.quote_plus(
        start.replace(tzinfo=timezone.utc).isoformat()
    )

    reqmock.get(
        f"https://data.alpaca.markets/v1beta1/options/trades?symbols={symbol}&start={_start_in_url}&limit={limit}",
        text="""
    {
        "next_page_token": null,
        "trades": {}
    }
        """,
    )

    request = OptionTradesRequest(symbol_or_symbols=[symbol], start=start, limit=limit)

    tradeset = option_client.get_option_trades(request_params=request)

    assert isinstance(tradeset, TradeSet)

    assert tradeset.dict() == {}

    assert len(tradeset.df) == 0

    assert reqmock.called_once


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
            "x": "D",
            "p": 161.2958,
            "s": 100,
            "c": [
                "@"
            ],
            "i": 22730,
            "z": "C"
        }
    }
        """,
    )
    request = OptionLatestTradeRequest(symbol_or_symbols=symbol, feed=DataFeed.IEX)

    trades = option_client.get_option_latest_trade(request_params=request)

    assert isinstance(trades, Dict)

    trade = trades[symbol]

    assert isinstance(trade, Trade)

    assert trade.price == 161.2958
    assert trade.size == 100

    assert trade.exchange == Exchange.D

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
            "x": "D",
            "p": 161.2958,
            "s": 100,
            "c": [
                "@"
            ],
            "i": 22730,
            "z": "C"
        },
        "AAPL240126P00100000": {
            "t": "2024-01-24T19:59:59.405545378Z",
            "x": "V",
            "p": 720.19,
            "s": 100,
            "c": [
                "@"
            ],
            "i": 11017,
            "z": "C"
        }
    }
    }
        """,
    )
    request = OptionLatestTradeRequest(symbol_or_symbols=symbols, feed=DataFeed.IEX)

    trades = option_client.get_option_latest_trade(request_params=request)

    assert isinstance(trades, Dict)

    trade = trades["AAPL240126P00050000"]

    assert isinstance(trade, Trade)

    assert trade.price == 161.2958
    assert trade.size == 100

    assert trade.exchange == Exchange.D

    assert reqmock.called_once


def test_get_latest_trade_multi_not_found(
    reqmock, option_client: OptionHistoricalDataClient
):
    symbol = "AAPL240126P00050000"

    reqmock.get(
        f"https://data.alpaca.markets/v1beta1/options/trades/latest?symbols={symbol}",
        text="""
    {
        "next_page_token": null
        "trade": null,
        "symbol": "AAPL240126P00050000"
    }
        """,
    )
    request = OptionLatestTradeRequest(symbol_or_symbols=symbol, feed=DataFeed.IEX)

    trade = option_client.get_option_latest_trade(request_params=request)

    assert isinstance(trade, Dict)

    assert trade == {}

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
    request = OptionLatestTradeRequest(symbol_or_symbols=[symbol], feed=DataFeed.IEX)

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
            "ax": "P",
            "ap": 161.11,
            "as": 13,
            "bx": "K",
            "bp": 161.1,
            "bs": 2,
            "c": [
                "R"
            ],
            "z": "C"
        }
    }
        """,
    )

    request = OptionLatestQuoteRequest(symbol_or_symbols=symbol)

    quotes = option_client.get_option_latest_quote(request)

    assert isinstance(quotes, Dict)

    quote = quotes[symbol]

    assert isinstance(quote, Quote)

    assert quote.ask_price == 161.11
    assert quote.bid_size == 2

    assert quote.bid_exchange == "K"

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
        "next_page_token": null,
        "quote": null,
        "symbol": "AAPL240126P00050000"
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
        "symbol": "AAPL240126P00050000",
        "latestTrade": {
            "t": "2024-01-24T14:33:58.448432206Z",
            "x": "D",
            "p": 161.1998,
            "s": 200,
            "c": [
                "@"
            ],
            "i": 39884,
            "z": "C"
        },
        "latestQuote": {
            "t": "2022-03-18T14:33:58.547942Z",
            "ax": "K",
            "ap": 161.2,
            "as": 2,
            "bx": "K",
            "bp": 161.19,
            "bs": 5,
            "c": [
                "R"
            ],
            "z": "C"
        }
    }
        """,
    )

    request = OptionSnapshotRequest(symbol_or_symbols=symbol)

    snapshots = option_client.get_option_snapshot(request)

    assert isinstance(snapshots, Dict)

    snapshot = snapshots[symbol]

    assert isinstance(snapshot, Snapshot)

    assert snapshot.latest_trade.price == 161.1998
    assert snapshot.latest_quote.bid_size == 5
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
        "symbol": "AAPL240126P00050000",
        "latestTrade": null,
        "latestQuote": null,
        "minuteBar": null,
        "dailyBar": null,
        "prevDailyBar": null
    }
        """,
    )

    request = OptionSnapshotRequest(symbol_or_symbols=symbol)

    snapshot = option_client.get_option_snapshot(request)

    assert isinstance(snapshot, Dict)

    assert "AAPL240126P00050000" in snapshot

    assert snapshot["AAPL240126P00050000"].model_dump() == {
        "daily_bar": None,
        "latest_quote": None,
        "latest_trade": None,
        "minute_bar": None,
        "previous_daily_bar": None,
        "symbol": "AAPL240126P00050000",
    }

    assert reqmock.called_once


def test_get_snapshot_multi_empty_response(
    reqmock, option_client: OptionHistoricalDataClient
):
    symbol = "AAPL240126P00050000"

    reqmock.get(
        f"https://data.alpaca.markets/v1beta1/options/snapshots?symbols={symbol}",
        text="""
    {}
        """,
    )

    request = OptionSnapshotRequest(symbol_or_symbols=[symbol])

    snapshots = option_client.get_option_snapshot(request)

    assert isinstance(snapshots, Dict)

    assert snapshots == {}

    assert reqmock.called_once
