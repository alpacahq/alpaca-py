import urllib.parse
from datetime import datetime, timezone
from typing import Dict

from alpaca.common.enums import Sort
from alpaca.data import Bar, Quote, Snapshot, Trade
from alpaca.data.enums import DataFeed, Exchange
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.models import BarSet, QuoteSet, TradeSet
from alpaca.data.requests import (
    StockBarsRequest,
    StockLatestBarRequest,
    StockLatestQuoteRequest,
    StockLatestTradeRequest,
    StockQuotesRequest,
    StockSnapshotRequest,
    StockTradesRequest,
)
from alpaca.data.timeframe import TimeFrame


def test_get_bars(reqmock, stock_client: StockHistoricalDataClient):
    # Test single symbol request

    symbol = "AAPL"
    timeframe = TimeFrame.Day
    start = datetime(2022, 2, 1)
    limit = 2
    _start_in_url = urllib.parse.quote_plus(
        start.replace(tzinfo=timezone.utc).isoformat()
    )
    reqmock.get(
        f"https://data.alpaca.markets/v2/stocks/bars?symbols=AAPL&start={_start_in_url}&timeframe={timeframe}&limit={limit}",
        text="""
{
    "bars": {
        "AAPL": [
            {
                "t": "2022-02-01T05:00:00Z",
                "o": 174,
                "h": 174.84,
                "l": 172.31,
                "c": 174.61,
                "v": 85998033,
                "n": 732412,
                "vw": 173.703516
            },
            {
                "t": "2022-02-02T05:00:00Z",
                "o": 174.64,
                "h": 175.88,
                "l": 173.33,
                "c": 175.84,
                "v": 84817432,
                "n": 675034,
                "vw": 174.941288
            }
        ]
    },
    "next_page_token": "QUFQTHxEfDIwMjItMDItMDJUMDU6MDA6MDAuMDAwMDAwMDAwWg=="
}
        """,
    )
    request = StockBarsRequest(
        symbol_or_symbols=symbol, timeframe=timeframe, start=start, limit=limit
    )
    barset = stock_client.get_stock_bars(request_params=request)

    assert isinstance(barset, BarSet)

    assert barset[symbol][0].open == 174
    assert barset[symbol][0].high == 174.84

    assert barset.df.index.nlevels == 2

    assert reqmock.called_once


def test_get_bars_desc(reqmock, stock_client: StockHistoricalDataClient):
    symbol = "TSLA"
    timeframe = TimeFrame.Day
    start = datetime(2023, 9, 1)
    end = datetime(2023, 9, 27, 12)
    limit = 3
    _start_in_url = urllib.parse.quote_plus(
        start.replace(tzinfo=timezone.utc).isoformat()
    )
    _end_in_url = urllib.parse.quote_plus(end.replace(tzinfo=timezone.utc).isoformat())
    reqmock.get(
        f"https://data.alpaca.markets/v2/stocks/bars?symbols={symbol}&start={_start_in_url}&end={_end_in_url}&timeframe={timeframe}&limit={limit}&sort=desc",
        text="""
{
    "bars": {
        "TSLA": [
            {
                "c": 240.5,
                "h": 245.33,
                "l": 234.58,
                "n": 1393690,
                "o": 244.262,
                "t": "2023-09-27T04:00:00Z",
                "v": 136616287,
                "vw": 240.479286
            },
            {
                "c": 244.12,
                "h": 249.55,
                "l": 241.6601,
                "n": 1118004,
                "o": 242.98,
                "t": "2023-09-26T04:00:00Z",
                "v": 102033779,
                "vw": 245.559325
            },
            {
                "c": 246.99,
                "h": 247.1,
                "l": 238.31,
                "n": 1196613,
                "o": 243.38,
                "t": "2023-09-25T04:00:00Z",
                "v": 104668716,
                "vw": 244.197325
            }
        ]
    },
    "next_page_token": "VFNMQXxEfDc1Mjc3NTc2MzYwMDAwMDAwMDA="
}
        """,
    )
    request = StockBarsRequest(
        symbol_or_symbols=symbol,
        timeframe=timeframe,
        start=start,
        end=end,
        limit=limit,
        sort=Sort.DESC,
    )
    barset = stock_client.get_stock_bars(request_params=request)

    assert isinstance(barset, BarSet)
    assert reqmock.called_once

    assert barset[symbol][0].open == 244.262
    assert barset[symbol][0].close == 240.5
    assert barset[symbol][-1].high == 247.1
    assert barset[symbol][-1].volume == 104668716


def test_multisymbol_get_bars(reqmock, stock_client: StockHistoricalDataClient):
    # test multisymbol request
    symbols = ["AAPL", "TSLA"]
    start = datetime(2022, 2, 1)
    end = datetime(2022, 3, 9)
    timeframe = TimeFrame.Day
    _symbols_in_url = "%2C".join(s for s in symbols)

    _start_in_url = urllib.parse.quote_plus(
        start.replace(tzinfo=timezone.utc).isoformat()
    )
    _end_in_url = urllib.parse.quote_plus(end.replace(tzinfo=timezone.utc).isoformat())

    reqmock.get(
        f"https://data.alpaca.markets/v2/stocks/bars?timeframe={timeframe}&start={_start_in_url}&end={_end_in_url}&symbols={_symbols_in_url}&limit=10000",
        text="""
    {
        "bars": {
            "AAPL": [
                {
                    "t": "2022-03-09T05:00:00Z",
                    "o": 161.51,
                    "h": 163.41,
                    "l": 159.41,
                    "c": 162.95,
                    "v": 88496480,
                    "n": 700291,
                    "vw": 161.942117
                }
            ],
            "TSLA": [
                {
                    "t": "2022-03-09T05:00:00Z",
                    "o": 839,
                    "h": 860.56,
                    "l": 832.01,
                    "c": 858.97,
                    "v": 19227323,
                    "n": 528531,
                    "vw": 850.616587
                }
            ]
        },
        "next_page_token": null
    }
        """,
    )

    request = StockBarsRequest(
        symbol_or_symbols=symbols, timeframe=timeframe, start=start, end=end
    )

    barset = stock_client.get_stock_bars(request_params=request)

    assert type(barset) == BarSet

    assert barset["TSLA"][0].open == 839
    assert barset["AAPL"][0].low == 159.41

    assert barset.df.index[0][1].day == 9
    assert barset.df.index.nlevels == 2


def test_get_bars_single_empty_response(
    reqmock, stock_client: StockHistoricalDataClient
):
    symbol = "AAPL"
    timeframe = TimeFrame.Day
    start = datetime(2022, 2, 1)
    limit = 2
    _start_in_url = urllib.parse.quote_plus(
        start.replace(tzinfo=timezone.utc).isoformat()
    )
    reqmock.get(
        f"https://data.alpaca.markets/v2/stocks/bars?symbols={symbol}&start={_start_in_url}&timeframe={timeframe}&limit={limit}",
        text="""
    {
        "bars": {},
        "next_page_token": null
    }
        """,
    )
    request = StockBarsRequest(
        symbol_or_symbols=symbol, timeframe=timeframe, start=start, limit=limit
    )
    barset = stock_client.get_stock_bars(request_params=request)

    assert isinstance(barset, BarSet)

    assert len(barset.dict()) == 0

    assert len(barset.df) == 0

    assert reqmock.called_once


def test_get_bars_multi_empty_response(
    reqmock, stock_client: StockHistoricalDataClient
):
    symbol = "AAPL"
    timeframe = TimeFrame.Day
    start = datetime(2022, 2, 1)
    limit = 2
    _start_in_url = urllib.parse.quote_plus(
        start.replace(tzinfo=timezone.utc).isoformat()
    )
    reqmock.get(
        f"https://data.alpaca.markets/v2/stocks/bars?symbols={symbol}&start={_start_in_url}&timeframe={timeframe}&limit={limit}",
        text="""
    {
        "bars": {},
        "next_page_token": null
    }
        """,
    )
    request = StockBarsRequest(
        symbol_or_symbols=[symbol], timeframe=timeframe, start=start, limit=limit
    )
    barset = stock_client.get_stock_bars(request_params=request)

    assert isinstance(barset, BarSet)

    assert barset.dict() == {}

    assert len(barset.df) == 0

    assert reqmock.called_once


def test_get_quotes(reqmock, stock_client: StockHistoricalDataClient):
    # Test single symbol request

    symbol = "AAPL"
    start = datetime(2022, 3, 9)
    limit = 2

    _start_in_url = urllib.parse.quote_plus(
        start.replace(tzinfo=timezone.utc).isoformat()
    )

    reqmock.get(
        f"https://data.alpaca.markets/v2/stocks/quotes?symbols={symbol}&start={_start_in_url}&limit={limit}",
        text="""
{
    "quotes": {
        "AAPL": [
            {
                "t": "2022-03-09T09:00:00.000059Z",
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
                "t": "2022-03-09T09:00:00.000059Z",
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
        ]
    },
    "next_page_token": "QUFQTHwyMDIyLTAzLTA5VDA5OjAwOjAwLjAwMDA1OTAwMFp8Q0ZEQUU5QTg="
}
        """,
    )
    request = StockQuotesRequest(symbol_or_symbols=symbol, start=start, limit=limit)

    quoteset = stock_client.get_stock_quotes(request_params=request)

    assert isinstance(quoteset, QuoteSet)

    assert quoteset[symbol][0].ask_price == 158.65
    assert quoteset[symbol][0].bid_size == 4

    assert quoteset[symbol][0].ask_exchange == "K"

    assert quoteset.df.index.nlevels == 2

    assert reqmock.called_once


def test_multisymbol_quotes(reqmock, stock_client: StockHistoricalDataClient):
    # test multisymbol request
    symbols = ["AAPL", "TSLA"]
    start = datetime(2022, 3, 9)
    _symbols_in_url = "%2C".join(s for s in symbols)

    _start_in_url = urllib.parse.quote_plus(
        start.replace(tzinfo=timezone.utc).isoformat()
    )

    reqmock.get(
        f"https://data.alpaca.markets/v2/stocks/quotes?start={_start_in_url}&symbols={_symbols_in_url}&asof=-&limit=10000",
        text="""
    {
        "quotes": {
            "AAPL": [
                {
                    "t": "2022-03-09T09:00:00.000059Z",
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
            "TSLA": [
                {
                    "t": "2022-03-09T09:00:00.000805Z",
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

    request = StockQuotesRequest(symbol_or_symbols=symbols, start=start, asof="-")

    quoteset = stock_client.get_stock_quotes(request_params=request)

    assert isinstance(quoteset, QuoteSet)

    assert quoteset["AAPL"][0].ask_size == 1
    assert quoteset["TSLA"][0].bid_price == 840.75

    assert quoteset["AAPL"][0].bid_exchange == "Q"

    assert quoteset.df.index.nlevels == 2

    assert reqmock.called_once


def test_get_quotes_multi_empty_response(
    reqmock, stock_client: StockHistoricalDataClient
):
    symbol = "AAPL"
    start = datetime(2022, 3, 9)
    limit = 2

    _start_in_url = urllib.parse.quote_plus(
        start.replace(tzinfo=timezone.utc).isoformat()
    )

    reqmock.get(
        f"https://data.alpaca.markets/v2/stocks/quotes?symbols={symbol}&start={_start_in_url}&limit={limit}",
        text="""
    {
        "next_page_token": null,
        "quotes": {}
    }
        """,
    )
    request = StockQuotesRequest(symbol_or_symbols=[symbol], start=start, limit=limit)

    quoteset = stock_client.get_stock_quotes(request_params=request)

    assert isinstance(quoteset, QuoteSet)

    assert quoteset.dict() == {}

    assert len(quoteset.df) == 0

    assert reqmock.called_once


def test_get_trades(reqmock, stock_client: StockHistoricalDataClient):
    # Test single symbol request
    symbol = "AAPL"
    start = datetime(2022, 3, 9)
    limit = 2

    _start_in_url = urllib.parse.quote_plus(
        start.replace(tzinfo=timezone.utc).isoformat()
    )

    reqmock.get(
        f"https://data.alpaca.markets/v2/stocks/trades?symbols=AAPL&start={_start_in_url}&limit={limit}&asof=2022-03-09",
        text="""
{
    "trades": {
        "AAPL": [
            {
                "t": "2022-03-09T05:00:02.183Z",
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
                "t": "2022-03-09T05:00:16.91Z",
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
        ]
    },
    "next_page_token": "QUFQTHwyMDIyLTAzLTA5VDA1OjAwOjE2LjkxMDAwMDAwMFp8RHwwOTIyMzM3MjAzNjg1NDc3NTk3Ng=="
}
        """,
    )

    request = StockTradesRequest(
        symbol_or_symbols=symbol, start=start, limit=limit, asof="2022-03-09"
    )

    tradeset = stock_client.get_stock_trades(request_params=request)

    assert isinstance(tradeset, TradeSet)

    assert tradeset[symbol][0].price == 159.07
    assert tradeset[symbol][0].size == 1

    assert tradeset[symbol][0].exchange == Exchange.D

    assert tradeset.df.index.nlevels == 2

    assert reqmock.called_once


def test_multisymbol_get_trades(reqmock, stock_client: StockHistoricalDataClient):
    # test multisymbol request
    symbols = ["AAPL", "TSLA"]
    start = datetime(2022, 3, 9)
    _symbols_in_url = "%2C".join(s for s in symbols)

    _start_in_url = urllib.parse.quote_plus(
        start.replace(tzinfo=timezone.utc).isoformat()
    )

    reqmock.get(
        f"https://data.alpaca.markets/v2/stocks/trades?start={_start_in_url}&symbols={_symbols_in_url}&limit=10000",
        text="""
    {
        "trades": {
            "AAPL": [
                {
                    "t": "2022-03-09T05:00:02.183Z",
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
            "TSLA": [
                {
                    "t": "2022-03-09T05:08:03.035Z",
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

    request = StockTradesRequest(symbol_or_symbols=symbols, start=start)

    tradeset = stock_client.get_stock_trades(request_params=request)

    assert isinstance(tradeset, TradeSet)

    assert tradeset["AAPL"][0].size == 1
    assert tradeset["TSLA"][0].price == 833

    assert tradeset["AAPL"][0].exchange == Exchange.D

    assert tradeset.df.index[0][1].day == 9
    assert tradeset.df.index.nlevels == 2

    assert reqmock.called_once


def test_get_trades_multi_empty_response(
    reqmock, stock_client: StockHistoricalDataClient
):
    symbol = "AAPL"
    start = datetime(2022, 3, 9)
    limit = 2

    _start_in_url = urllib.parse.quote_plus(
        start.replace(tzinfo=timezone.utc).isoformat()
    )

    reqmock.get(
        f"https://data.alpaca.markets/v2/stocks/trades?symbols={symbol}&start={_start_in_url}&limit={limit}",
        text="""
    {
        "next_page_token": null,
        "trades": {}
    }
        """,
    )

    request = StockTradesRequest(symbol_or_symbols=[symbol], start=start, limit=limit)

    tradeset = stock_client.get_stock_trades(request_params=request)

    assert isinstance(tradeset, TradeSet)

    assert tradeset.dict() == {}

    assert len(tradeset.df) == 0

    assert reqmock.called_once


def test_get_latest_trade(reqmock, stock_client: StockHistoricalDataClient):
    # Test single symbol request
    symbol = "AAPL"

    reqmock.get(
        f"https://data.alpaca.markets/v2/stocks/trades/latest?symbols=AAPL&feed=IEX",
        text="""
{
    "trades": {
        "AAPL": {
            "t": "2022-03-18T14:02:09.722539521Z",
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
}
        """,
    )
    request = StockLatestTradeRequest(symbol_or_symbols=symbol, feed=DataFeed.IEX)

    trades = stock_client.get_stock_latest_trade(request_params=request)

    assert isinstance(trades, Dict)

    trade = trades[symbol]

    assert isinstance(trade, Trade)

    assert trade.price == 161.2958
    assert trade.size == 100

    assert trade.exchange == Exchange.D

    assert reqmock.called_once
    assert "limit" not in reqmock.last_request.qs


def test_get_multisymbol_latest_trade(reqmock, stock_client: StockHistoricalDataClient):
    symbols = ["AAPL", "TSLA"]
    _symbols_in_url = "%2C".join(s for s in symbols)
    reqmock.get(
        f"https://data.alpaca.markets/v2/stocks/trades/latest?symbols={_symbols_in_url}",
        text="""
    {
    "trades": {
        "AAPL": {
            "t": "2022-03-18T14:02:09.722539521Z",
            "x": "D",
            "p": 161.2958,
            "s": 100,
            "c": [
                "@"
            ],
            "i": 22730,
            "z": "C"
        },
        "TSLA": {
            "t": "2022-07-15T19:59:59.405545378Z",
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
    request = StockLatestTradeRequest(symbol_or_symbols=symbols, feed=DataFeed.IEX)

    trades = stock_client.get_stock_latest_trade(request_params=request)

    assert isinstance(trades, Dict)

    trade = trades["AAPL"]

    assert isinstance(trade, Trade)

    assert trade.price == 161.2958
    assert trade.size == 100

    assert trade.exchange == Exchange.D

    assert reqmock.called_once


def test_get_latest_trade_multi_not_found(
    reqmock, stock_client: StockHistoricalDataClient
):
    symbol = "AAPL"

    reqmock.get(
        f"https://data.alpaca.markets/v2/stocks/trades/latest?symbols={symbol}&feed=IEX",
        text="""
    {
        "trades": {}
    }
        """,
    )
    request = StockLatestTradeRequest(symbol_or_symbols=[symbol], feed=DataFeed.IEX)

    trades = stock_client.get_stock_latest_trade(request_params=request)

    assert isinstance(trades, Dict)

    assert trades == {}

    assert reqmock.called_once


def test_get_latest_quote(reqmock, stock_client: StockHistoricalDataClient):
    # Test single symbol request
    symbol = "AAPL"

    reqmock.get(
        f"https://data.alpaca.markets/v2/stocks/quotes/latest?symbols=AAPL",
        text="""
{
    "quotes": {
        "AAPL": {
            "t": "2022-03-18T14:02:43.651613184Z",
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
}
        """,
    )

    request = StockLatestQuoteRequest(symbol_or_symbols=symbol)

    quotes = stock_client.get_stock_latest_quote(request)

    assert isinstance(quotes, Dict)

    quote = quotes[symbol]

    assert isinstance(quote, Quote)

    assert quote.ask_price == 161.11
    assert quote.bid_size == 2

    assert quote.bid_exchange == "K"

    assert reqmock.called_once


def test_get_latest_quote_multi_empty_response(
    reqmock, stock_client: StockHistoricalDataClient
):
    symbol = "AAPL"

    reqmock.get(
        f"https://data.alpaca.markets/v2/stocks/quotes/latest?symbols={symbol}",
        text="""
    {
        "quotes": {}
    }
        """,
    )

    request = StockLatestQuoteRequest(symbol_or_symbols=[symbol])

    quotes = stock_client.get_stock_latest_quote(request)

    assert isinstance(quotes, Dict)

    assert quotes == {}

    assert reqmock.called_once


def test_get_snapshot(reqmock, stock_client: StockHistoricalDataClient):
    # Test single symbol request
    symbol = "AAPL"

    reqmock.get(
        f"https://data.alpaca.markets/v2/stocks/snapshots?symbols=AAPL",
        text="""
{
    "AAPL": {
        "latestTrade": {
            "t": "2022-03-18T14:33:58.448432206Z",
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
        },
        "minuteBar": {
            "t": "2022-03-18T14:32:00Z",
            "o": 161.595,
            "h": 161.63,
            "l": 161.31,
            "c": 161.365,
            "v": 195503,
            "n": 1880,
            "vw": 161.448073
        },
        "dailyBar": {
            "t": "2022-03-18T04:00:00Z",
            "o": 160.59,
            "h": 161.92,
            "l": 159.76,
            "c": 161.365,
            "v": 31749988,
            "n": 186143,
            "vw": 160.683364
        },
        "prevDailyBar": {
            "t": "2022-03-17T04:00:00Z",
            "o": 158.6,
            "h": 161,
            "l": 157.63,
            "c": 160.62,
            "v": 73839892,
            "n": 609067,
            "vw": 159.425082
        }
    }
}
        """,
    )

    request = StockSnapshotRequest(symbol_or_symbols=symbol)

    snapshots = stock_client.get_stock_snapshot(request)

    assert isinstance(snapshots, Dict)

    snapshot = snapshots[symbol]

    assert isinstance(snapshot, Snapshot)

    assert snapshot.latest_trade.price == 161.1998
    assert snapshot.latest_quote.bid_size == 5
    assert snapshot.minute_bar.close == 161.365
    assert snapshot.daily_bar.volume == 31749988
    assert snapshot.previous_daily_bar.high == 161

    assert reqmock.called_once
    assert "limit" not in reqmock.last_request.qs


def test_get_snapshot_multi_empty_response(
    reqmock, stock_client: StockHistoricalDataClient
):
    symbol = "AAPL"

    reqmock.get(
        f"https://data.alpaca.markets/v2/stocks/snapshots?symbols={symbol}",
        text="""
    {}
        """,
    )

    request = StockSnapshotRequest(symbol_or_symbols=symbol)

    snapshots = stock_client.get_stock_snapshot(request)

    assert isinstance(snapshots, Dict)

    assert snapshots == {}

    assert reqmock.called_once


def test_stock_latest_bar(reqmock, stock_client: StockHistoricalDataClient):
    symbol = "SPY"
    reqmock.get(
        f"https://data.alpaca.markets/v2/stocks/bars/latest?symbols=SPY",
        text="""
{
    "bars": {
        "SPY": {
            "t": "2022-07-26T20:50:00Z",
            "o": 392.18,
            "h": 392.18,
            "l": 392.18,
            "c": 392.18,
            "v": 2100,
            "n": 2,
            "vw": 392.18
        }
    }
}
    """,
    )

    request = StockLatestBarRequest(symbol_or_symbols=symbol)

    bars = stock_client.get_stock_latest_bar(request)

    assert isinstance(bars, Dict)

    bar = bars[symbol]

    assert isinstance(bar, Bar)

    assert bar.open == 392.18

    assert reqmock.called_once


def test_multi_stock_latest_bar(reqmock, stock_client: StockHistoricalDataClient):
    symbols = ["SPY", "TSLA"]
    _symbols_in_url = "%2C".join(s for s in symbols)
    reqmock.get(
        f"https://data.alpaca.markets/v2/stocks/bars/latest?symbols={_symbols_in_url}",
        text="""
    {
        "bars": {
            "SPY": {
                "t": "2022-07-26T20:50:00Z",
                "o": 392.18,
                "h": 392.18,
                "l": 392.18,
                "c": 392.18,
                "v": 2100,
                "n": 2,
                "vw": 392.18
            },
            "TSLA": {
                "t": "2022-07-26T19:59:00Z",
                "o": 776.605,
                "h": 776.95,
                "l": 776.41,
                "c": 776.63,
                "v": 5993,
                "n": 124,
                "vw": 776.654473
            }
        }
    }
    """,
    )

    request = StockLatestBarRequest(symbol_or_symbols=symbols)

    bars = stock_client.get_stock_latest_bar(request)

    assert isinstance(bars, Dict)

    bar = bars[symbols[0]]

    assert isinstance(bar, Bar)

    assert bar.open == 392.18

    assert reqmock.called_once


def test_stock_latest_bar_multi_empty_response(
    reqmock, stock_client: StockHistoricalDataClient
):
    symbol = "AAPL"
    reqmock.get(
        f"https://data.alpaca.markets/v2/stocks/bars/latest?symbols={symbol}",
        text="""
    {
        "bars": {}
    }
    """,
    )

    request = StockLatestBarRequest(symbol_or_symbols=[symbol])

    bars = stock_client.get_stock_latest_bar(request)

    assert isinstance(bars, Dict)

    assert bars == {}

    assert reqmock.called_once
