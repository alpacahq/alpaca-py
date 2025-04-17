import urllib.parse
from datetime import datetime, timezone
from typing import Dict

from alpaca.data import OptionsSnapshot, Quote, Trade
from alpaca.data.enums import Exchange, OptionsFeed
from alpaca.data.historical.option import OptionHistoricalDataClient
from alpaca.data.models.bars import BarSet
from alpaca.data.models.trades import TradeSet
from alpaca.data.requests import (
    OptionBarsRequest,
    OptionChainRequest,
    OptionLatestQuoteRequest,
    OptionLatestTradeRequest,
    OptionSnapshotRequest,
    OptionTradesRequest,
)
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit


def test_get_bars(reqmock, option_client: OptionHistoricalDataClient):
    # Test single symbol request
    symbol = "SPY240426C00555000"
    start = datetime(2024, 3, 12)
    limit = 2
    timeframe = TimeFrame(amount=1, unit=TimeFrameUnit.Hour)

    _start_in_url = urllib.parse.quote_plus(
        start.replace(tzinfo=timezone.utc).isoformat()
    )

    reqmock.get(
        f"https://data.alpaca.markets/v1beta1/options/bars?symbols={symbol}&start={_start_in_url}&limit={limit}&timeframe={timeframe}",
        text="""
{
  "bars": {
    "SPY240426C00555000": [
      {
        "c": 0.21,
        "h": 0.24,
        "l": 0.21,
        "n": 2,
        "o": 0.24,
        "t": "2024-03-12T13:00:00Z",
        "v": 21,
        "vw": 0.211429
      },
      {
        "c": 0.3,
        "h": 0.3,
        "l": 0.25,
        "n": 3,
        "o": 0.25,
        "t": "2024-03-12T14:00:00Z",
        "v": 3,
        "vw": 0.273333
      }
    ]
  },
  "next_page_token": "U1BZMjQwNDI2QzAwNTU1MDAwfE18MTcxMDI1NDM0MDAwMDAwMDAwMA=="
}
        """,
    )

    request = OptionBarsRequest(
        symbol_or_symbols=symbol, start=start, limit=limit, timeframe=timeframe
    )

    barset = option_client.get_option_bars(request_params=request)

    assert isinstance(barset, BarSet)
    bar = barset[symbol][0]
    assert bar.close == 0.21
    assert bar.high == 0.24
    assert bar.low == 0.21
    assert bar.trade_count == 2
    assert bar.open == 0.24
    assert bar.volume == 21
    assert bar.vwap == 0.211429
    assert bar.timestamp == datetime(2024, 3, 12, 13, 0, tzinfo=timezone.utc)

    bar2 = barset[symbol][1]
    assert bar2.close == 0.3
    assert bar2.high == 0.3
    assert bar2.low == 0.25
    assert bar2.trade_count == 3
    assert bar2.open == 0.25
    assert bar2.volume == 3
    assert bar2.vwap == 0.273333
    assert bar2.timestamp == datetime(2024, 3, 12, 14, 0, tzinfo=timezone.utc)

    assert barset.df.index.nlevels == 2

    assert reqmock.called_once


def test_multisymbol_get_bars(reqmock, option_client: OptionHistoricalDataClient):
    # test multisymbol request
    symbols = ["SPY240426C00550000", "SPY240426C00555000"]
    start = datetime(2024, 3, 12)
    _symbols_in_url = "%2C".join(s for s in symbols)
    timeframe = TimeFrame(amount=1, unit=TimeFrameUnit.Hour)

    _start_in_url = urllib.parse.quote_plus(
        start.replace(tzinfo=timezone.utc).isoformat()
    )

    reqmock.get(
        f"https://data.alpaca.markets/v1beta1/options/bars?start={_start_in_url}&symbols={_symbols_in_url}&timeframe={timeframe}&limit=10000",
        text="""
{
  "bars": {
    "SPY240426C00550000": [
      {
        "c": 0.37,
        "h": 0.37,
        "l": 0.37,
        "n": 1,
        "o": 0.37,
        "t": "2024-03-12T13:00:00Z",
        "v": 1,
        "vw": 0.37
      },
      {
        "c": 0.51,
        "h": 0.52,
        "l": 0.41,
        "n": 6,
        "o": 0.41,
        "t": "2024-03-12T14:00:00Z",
        "v": 16,
        "vw": 0.496875
      }
    ],
    "SPY240426C00555000": [
      {
        "c": 0.21,
        "h": 0.24,
        "l": 0.21,
        "n": 2,
        "o": 0.24,
        "t": "2024-03-12T13:00:00Z",
        "v": 21,
        "vw": 0.211429
      }
    ]
  },
  "next_page_token": null
}
        """,
    )

    request = OptionBarsRequest(
        symbol_or_symbols=symbols, start=start, timeframe=timeframe
    )

    barset = option_client.get_option_bars(request_params=request)

    assert isinstance(barset, BarSet)

    bar = barset["SPY240426C00550000"][0]
    assert bar.close == 0.37
    assert bar.high == 0.37
    assert bar.low == 0.37
    assert bar.trade_count == 1
    assert bar.open == 0.37
    assert bar.volume == 1
    assert bar.vwap == 0.37
    assert bar.timestamp == datetime(2024, 3, 12, 13, 0, tzinfo=timezone.utc)

    bar2 = barset["SPY240426C00550000"][1]
    assert bar2.close == 0.51
    assert bar2.high == 0.52
    assert bar2.low == 0.41
    assert bar2.trade_count == 6
    assert bar2.open == 0.41
    assert bar2.volume == 16
    assert bar2.vwap == 0.496875
    assert bar2.timestamp == datetime(2024, 3, 12, 14, 0, tzinfo=timezone.utc)

    bar3 = barset["SPY240426C00555000"][0]
    assert bar3.close == 0.21
    assert bar3.high == 0.24
    assert bar3.low == 0.21
    assert bar3.trade_count == 2
    assert bar3.open == 0.24
    assert bar3.volume == 21
    assert bar3.vwap == 0.211429
    assert bar3.timestamp == datetime(2024, 3, 12, 13, 0, tzinfo=timezone.utc)

    df = barset.df
    assert df.index.nlevels == 2
    assert len(df) == 3

    assert reqmock.called_once


def test_get_bars_single_empty_response(
    reqmock, option_client: OptionHistoricalDataClient
):
    symbol = "AAPL240126P00050000"
    start = datetime(2024, 1, 24)
    limit = 2
    timeframe = TimeFrame(amount=1, unit=TimeFrameUnit.Hour)

    _start_in_url = urllib.parse.quote_plus(
        start.replace(tzinfo=timezone.utc).isoformat()
    )

    reqmock.get(
        f"https://data.alpaca.markets/v1beta1/options/bars?symbols={symbol}&start={_start_in_url}&limit={limit}&timeframe={timeframe}",
        text="""
{
  "next_page_token": null,
  "bars": {}
}
        """,
    )

    request = OptionBarsRequest(
        symbol_or_symbols=symbol, start=start, limit=limit, timeframe=timeframe
    )

    barset = option_client.get_option_bars(request_params=request)

    assert isinstance(barset, BarSet)

    # this behaviour is different than stocks as no single symbol request endpoint for options
    assert barset.dict() == {}

    assert len(barset.df) == 0

    assert reqmock.called_once


def test_get_bars_multi_empty_response(
    reqmock, option_client: OptionHistoricalDataClient
):
    symbol = "AAPL240126P00050000"
    start = datetime(2024, 1, 24)
    limit = 2
    timeframe = TimeFrame(amount=1, unit=TimeFrameUnit.Hour)

    _start_in_url = urllib.parse.quote_plus(
        start.replace(tzinfo=timezone.utc).isoformat()
    )

    reqmock.get(
        f"https://data.alpaca.markets/v1beta1/options/bars?symbols={symbol}&start={_start_in_url}&limit={limit}&timeframe={timeframe}",
        text="""
{
  "next_page_token": null,
  "bars": {}
}
        """,
    )

    request = OptionBarsRequest(
        symbol_or_symbols=[symbol], start=start, limit=limit, timeframe=timeframe
    )

    barset = option_client.get_option_bars(request_params=request)

    assert isinstance(barset, BarSet)

    assert barset.dict() == {}

    assert len(barset.df) == 0

    assert reqmock.called_once


def test_get_trades(reqmock, option_client: OptionHistoricalDataClient):
    # Test single symbol request
    symbol = "SPY240426C00555000"
    start = datetime(2024, 3, 12)
    limit = 2

    _start_in_url = urllib.parse.quote_plus(
        start.replace(tzinfo=timezone.utc).isoformat()
    )

    reqmock.get(
        f"https://data.alpaca.markets/v1beta1/options/trades?symbols={symbol}&start={_start_in_url}&limit={limit}",
        text="""
    {
        "next_page_token": "U1BZMjQwNDI2QzAwNTU1MDAwfDE3MTAyNTE1NDI1NTg0NDcxMDR8Qg==",
        "trades": {
            "SPY240426C00555000": [
            {
                "c": "I",
                "p": 0.24,
                "s": 1,
                "t": "2024-03-12T13:34:54.178322688Z",
                "x": "M"
            },
            {
                "c": "j",
                "p": 0.21,
                "s": 20,
                "t": "2024-03-12T13:52:22.558447104Z",
                "x": "B"
            }
            ]
        }
    }
        """,
    )

    request = OptionTradesRequest(symbol_or_symbols=symbol, start=start, limit=limit)

    tradeset = option_client.get_option_trades(request_params=request)

    assert isinstance(tradeset, TradeSet)
    trade: Trade = tradeset[symbol][0]
    assert trade.conditions == "I"
    assert trade.price == 0.24
    assert trade.size == 1
    assert trade.timestamp == datetime(
        2024, 3, 12, 13, 34, 54, 178322, tzinfo=timezone.utc
    )
    assert trade.exchange == Exchange.M

    trade2: Trade = tradeset[symbol][1]
    assert trade2.conditions == "j"
    assert trade2.price == 0.21
    assert trade2.size == 20
    assert trade2.timestamp == datetime(
        2024, 3, 12, 13, 52, 22, 558447, tzinfo=timezone.utc
    )
    assert trade2.exchange == Exchange.B

    assert tradeset.df.index.nlevels == 2

    assert reqmock.called_once


def test_multisymbol_get_trades(reqmock, option_client: OptionHistoricalDataClient):
    # test multisymbol request
    symbols = ["SPY240426C00550000", "SPY240426C00555000"]
    start = datetime(2024, 3, 12)
    _symbols_in_url = "%2C".join(s for s in symbols)

    _start_in_url = urllib.parse.quote_plus(
        start.replace(tzinfo=timezone.utc).isoformat()
    )

    reqmock.get(
        f"https://data.alpaca.markets/v1beta1/options/trades?start={_start_in_url}&symbols={_symbols_in_url}&limit=10000",
        text="""
{
  "next_page_token": null,
  "trades": {
    "SPY240426C00550000": [
      {
        "c": "g",
        "p": 0.37,
        "s": 1,
        "t": "2024-03-12T13:55:39.17011584Z",
        "x": "C"
      },
      {
        "c": "a",
        "p": 0.41,
        "s": 1,
        "t": "2024-03-12T14:10:14.088364544Z",
        "x": "C"
      }
    ],
    "SPY240426C00555000": [
      {
        "c": "I",
        "p": 0.24,
        "s": 1,
        "t": "2024-03-12T13:34:54.178322688Z",
        "x": "M"
      }
    ]
  }
}
        """,
    )

    request = OptionTradesRequest(symbol_or_symbols=symbols, start=start)

    tradeset = option_client.get_option_trades(request_params=request)

    assert isinstance(tradeset, TradeSet)

    trade: Trade = tradeset["SPY240426C00550000"][0]
    assert trade.conditions == "g"
    assert trade.price == 0.37
    assert trade.size == 1
    assert trade.timestamp == datetime(
        2024, 3, 12, 13, 55, 39, 170115, tzinfo=timezone.utc
    )
    assert trade.exchange == Exchange.C

    trade2: Trade = tradeset["SPY240426C00550000"][1]
    assert trade2.conditions == "a"
    assert trade2.price == 0.41
    assert trade2.size == 1
    assert trade2.timestamp == datetime(
        2024, 3, 12, 14, 10, 14, 88364, tzinfo=timezone.utc
    )
    assert trade2.exchange == Exchange.C

    trade3: Trade = tradeset["SPY240426C00555000"][0]
    assert trade3.conditions == "I"
    assert trade3.price == 0.24
    assert trade3.size == 1
    assert trade3.timestamp == datetime(
        2024, 3, 12, 13, 34, 54, 178322, tzinfo=timezone.utc
    )
    assert trade3.exchange == Exchange.M

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
  "trades": {}
}
        """,
    )

    request = OptionTradesRequest(symbol_or_symbols=symbol, start=start, limit=limit)

    tradeset = option_client.get_option_trades(request_params=request)

    assert isinstance(tradeset, TradeSet)

    # this behaviour is different than stocks as no single symbol request endpoint for options
    assert tradeset.dict() == {}

    assert len(tradeset.df) == 0

    assert reqmock.called_once


def test_get_trades_multi_empty_response(
    reqmock, option_client: OptionHistoricalDataClient
):
    symbols = ["SPY240426C00550000", "SPY240426C00555000"]
    _symbols_in_url = "%2C".join(s for s in symbols)
    start = datetime(2024, 1, 24)
    limit = 2

    _start_in_url = urllib.parse.quote_plus(
        start.replace(tzinfo=timezone.utc).isoformat()
    )

    reqmock.get(
        f"https://data.alpaca.markets/v1beta1/options/trades?symbols={_symbols_in_url}&start={_start_in_url}&limit={limit}",
        text="""
{
  "next_page_token": null,
  "trades": {}
}
        """,
    )

    request = OptionTradesRequest(symbol_or_symbols=symbols, start=start, limit=limit)

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
        "trades": {
            "AAPL240126P00050000": {
                "t": "2024-01-24T14:02:09.722539521Z",
                "x": "A",
                "p": 0.06,
                "s": 1,
                "c": "I"
            }
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
    assert "limit" not in reqmock.last_request.qs


def test_get_latest_trade_with_feed(reqmock, option_client: OptionHistoricalDataClient):
    # Test single symbol request
    symbol = "AAPL240126P00050000"

    reqmock.get(
        f"https://data.alpaca.markets/v1beta1/options/trades/latest?symbols={symbol}&feed=indicative",
        text="""
    {
        "trade": {
            "AAPL240126P00050000": {
                "t": "2024-01-24T14:02:09.722539521Z",
                "x": "A",
                "p": 0.06,
                "s": 1,
                "c": "I"
            }
        }
    }
        """,
    )
    request = OptionLatestTradeRequest(
        symbol_or_symbols=symbol,
        feed=OptionsFeed.INDICATIVE,
    )

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
        "quotes": {
            "AAPL240126P00050000": {
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


def test_get_latest_quote_with_feed(reqmock, option_client: OptionHistoricalDataClient):
    # Test single symbol request
    symbol = "AAPL240126P00050000"

    reqmock.get(
        f"https://data.alpaca.markets/v1beta1/options/quotes/latest?symbols={symbol}&feed=indicative",
        text="""
    {
        "quotes": {
            "AAPL240126P00050000": {
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
    }
        """,
    )

    request = OptionLatestQuoteRequest(
        symbol_or_symbols=symbol,
        feed=OptionsFeed.INDICATIVE,
    )

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
        f"https://data.alpaca.markets/v1beta1/options/snapshots?symbols={symbol}&limit=1000",
        text="""
    {
        "snapshots": {
            "AAPL240126P00050000":{
                "greeks": {
                    "delta": 0.6742666141545315,
                    "gamma": 0.027997890141030567,
                    "rho": 0.06118767991284862,
                    "theta": -0.12579419566886865,
                    "vega": 0.1466720335488638
                },
                "impliedVolatility": 0.3160291785379539,
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

    assert isinstance(snapshot, OptionsSnapshot)

    assert snapshot.latest_trade.price == 0.52
    assert snapshot.latest_quote.bid_size == 396
    assert snapshot.greeks.delta == 0.6742666141545315
    assert snapshot.greeks.gamma == 0.027997890141030567
    assert snapshot.greeks.rho == 0.06118767991284862
    assert snapshot.greeks.theta == -0.12579419566886865
    assert snapshot.greeks.vega == 0.1466720335488638
    assert snapshot.implied_volatility == 0.3160291785379539

    assert reqmock.called_once


def test_get_snapshot_latest_quote_only(
    reqmock, option_client: OptionHistoricalDataClient
):
    # Test single symbol request
    symbol = "AAPL240126P00050000"

    reqmock.get(
        f"https://data.alpaca.markets/v1beta1/options/snapshots?symbols={symbol}&limit=1000",
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

    assert isinstance(snapshot, OptionsSnapshot)

    assert snapshot.latest_trade is None
    assert snapshot.latest_quote.bid_size == 396
    assert snapshot.greeks is None
    assert snapshot.implied_volatility is None

    assert reqmock.called_once


def test_get_snapshot_with_feed(reqmock, option_client: OptionHistoricalDataClient):
    # Test single symbol request
    symbol = "AAPL240126P00050000"

    reqmock.get(
        f"https://data.alpaca.markets/v1beta1/options/snapshots?symbols={symbol}&feed=indicative&limit=1000",
        text="""
    {
        "snapshots": {
            "AAPL240126P00050000":{
                "greeks": {
                    "delta": 0.6742666141545315,
                    "gamma": 0.027997890141030567,
                    "rho": 0.06118767991284862,
                    "theta": -0.12579419566886865,
                    "vega": 0.1466720335488638
                },
                "impliedVolatility": 0.3160291785379539,
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

    request = OptionSnapshotRequest(
        symbol_or_symbols=symbol,
        feed=OptionsFeed.INDICATIVE,
    )

    snapshots = option_client.get_option_snapshot(request)

    assert isinstance(snapshots, Dict)

    snapshot = snapshots[symbol]

    assert isinstance(snapshot, OptionsSnapshot)

    assert snapshot.latest_trade.price == 0.52
    assert snapshot.latest_quote.bid_size == 396
    assert snapshot.greeks.delta == 0.6742666141545315
    assert snapshot.greeks.gamma == 0.027997890141030567
    assert snapshot.greeks.rho == 0.06118767991284862
    assert snapshot.greeks.theta == -0.12579419566886865
    assert snapshot.greeks.vega == 0.1466720335488638
    assert snapshot.implied_volatility == 0.3160291785379539

    assert reqmock.called_once


def test_get_snapshot_single_empty_response(
    reqmock, option_client: OptionHistoricalDataClient
):
    symbol = "AAPL240126P00050000"

    reqmock.get(
        f"https://data.alpaca.markets/v1beta1/options/snapshots?symbols={symbol}&limit=1000",
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
        f"https://data.alpaca.markets/v1beta1/options/snapshots?symbols={symbol}&limit=1000",
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


def test_get_option_chain(reqmock, option_client: OptionHistoricalDataClient):
    # Test single symbol request
    symbol = "AAPL"

    reqmock.get(
        f"https://data.alpaca.markets/v1beta1/options/snapshots/{symbol}?updated_since=2024-04-25T00%3A00%3A00%2B00%3A00",
        text="""
        {
            "next_page_token": null,
            "snapshots": {
                "AAPL240503P00155000": {
                    "greeks": {
                        "delta": -0.06962352623019707,
                        "gamma": 0.012407748296130911,
                        "rho": -0.00233165154510125,
                        "theta": -0.10116067021921063,
                        "vega": 0.03143087569879542
                    },
                    "impliedVolatility": 0.4584478444465036,
                    "latestQuote": {
                        "ap": 0.35,
                        "as": 119,
                        "ax": "W",
                        "bp": 0.32,
                        "bs": 73,
                        "bx": "N",
                        "c": "A",
                        "t": "2024-04-25T20:00:00.259610112Z"
                    },
                    "latestTrade": {
                        "c": "I",
                        "p": 0.34,
                        "s": 1,
                        "t": "2024-04-25T19:58:16.034908416Z",
                        "x": "N"
                    }
                }
            }
        }
        """,
    )

    request = OptionChainRequest(
        underlying_symbol=symbol, updated_since=datetime(2024, 4, 25)
    )

    snapshots = option_client.get_option_chain(request)

    assert isinstance(snapshots, Dict)

    snapshot = snapshots["AAPL240503P00155000"]

    assert isinstance(snapshot, OptionsSnapshot)

    assert snapshot.latest_trade.price == 0.34
    assert snapshot.latest_quote.bid_size == 73
    assert snapshot.greeks.delta == -0.06962352623019707
    assert snapshot.greeks.gamma == 0.012407748296130911
    assert snapshot.greeks.rho == -0.00233165154510125
    assert snapshot.greeks.theta == -0.10116067021921063
    assert snapshot.greeks.vega == 0.03143087569879542
    assert snapshot.implied_volatility == 0.4584478444465036

    assert reqmock.called_once
