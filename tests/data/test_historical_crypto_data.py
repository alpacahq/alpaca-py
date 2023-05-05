from datetime import datetime
from typing import Dict

from alpaca.data import Quote, Trade, Bar
from alpaca.data.historical.crypto import CryptoHistoricalDataClient
from alpaca.data.requests import (
    CryptoBarsRequest,
    CryptoTradesRequest,
    CryptoLatestTradeRequest,
    CryptoLatestQuoteRequest,
    CryptoSnapshotRequest,
    CryptoLatestBarRequest,
)
from alpaca.data.timeframe import TimeFrame
from alpaca.data.models import (
    BarSet,
    Snapshot,
    TradeSet,
)


def test_get_crypto_bars(reqmock, crypto_client: CryptoHistoricalDataClient):

    # test multisymbol request
    symbols = ["BTC/USD", "ETH/USD"]
    start = datetime(2022, 3, 9)
    end = datetime(2022, 3, 9)
    timeframe = TimeFrame.Day
    _symbols_in_url = "%2C".join(s for s in symbols)

    _start_in_url = start.isoformat("T") + "Z"
    _end_in_url = end.isoformat("T") + "Z"
    reqmock.get(
        f"https://data.alpaca.markets/v1beta3/crypto/us/bars?timeframe={timeframe}&start={_start_in_url}&end={_end_in_url}&symbols={_symbols_in_url}",
        text="""
    {
        "bars": {
            "BTC/USD": [
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
            "ETH/USD": [
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
    request = CryptoBarsRequest(
        symbol_or_symbols=symbols, timeframe=timeframe, start=start, end=end
    )
    barset = crypto_client.get_crypto_bars(request)

    assert isinstance(barset, BarSet)

    assert barset["BTC/USD"][0].open == 161.51
    assert barset["ETH/USD"][0].low == 832.01

    assert barset.df.index[0][1].day == 9
    assert barset.df.index.nlevels == 2


def test_get_trades(reqmock, crypto_client: CryptoHistoricalDataClient):

    # test multisymbol request
    symbols = ["BTC/USD", "ETH/USD"]
    start = datetime(2022, 3, 9)
    _symbols_in_url = "%2C".join(s for s in symbols)

    _start_in_url = start.isoformat("T") + "Z"

    reqmock.get(
        f"https://data.alpaca.markets/v1beta3/crypto/us/trades?start={_start_in_url}&symbols={_symbols_in_url}",
        text="""
    {
        "trades": {
            "BTC/USD": [
                {
                    "t": "2022-03-09T06:00:00.080264Z",
                    "p": 41516.08,
                    "s": 0.00315427,
                    "tks": "B",
                    "i": 293648598
                }
            ],
            "ETH/USD": [
                {
                    "t": "2022-03-09T06:00:00.228546Z",
                    "p": 2715.06,
                    "s": 0.001,
                    "tks": "S",
                    "i": 236866246
                }
            ]
        },
        "next_page_token": null
    }   
        """,
    )

    request = CryptoTradesRequest(symbol_or_symbols=symbols, start=start)
    tradeset = crypto_client.get_crypto_trades(request)
    assert isinstance(tradeset, TradeSet)

    assert tradeset["BTC/USD"][0].price == 41516.08
    assert tradeset["ETH/USD"][0].size == 0.001

    assert tradeset.df.index[0][1].day == 9
    assert tradeset.df.index.nlevels == 2

    assert reqmock.called_once


def test_get_crypto_latest_trade(reqmock, crypto_client: CryptoHistoricalDataClient):

    # Test single symbol request
    symbol = "BTC/USD"

    reqmock.get(
        f"https://data.alpaca.markets/v1beta3/crypto/us/latest/trades?symbols={symbol}",
        text="""
    {
        "symbol": "BTC/USD",
        "trade": {
            "t": "2022-03-18T14:03:31.960672Z",
            "p": 40650,
            "s": 0.1517,
            "tks": "B",
            "i": 26932440
        }
    } 
        """,
    )

    request = CryptoLatestTradeRequest(symbol_or_symbols=symbol)

    trades = crypto_client.get_crypto_latest_trade(request)

    assert isinstance(trades, Dict)

    trade = trades[symbol]

    assert isinstance(trade, Trade)

    assert trade.price == 40650
    assert trade.size == 0.1517

    assert reqmock.called_once


def test_get_crypto_latest_quote(reqmock, crypto_client: CryptoHistoricalDataClient):

    # Test single symbol request
    symbol = "BTC/USD"

    reqmock.get(
        f"https://data.alpaca.markets/v1beta3/crypto/us/latest/quotes?symbols={symbol}",
        text="""
    {
        "symbol": "BTC/USD",
        "quote": {
            "t": "2022-03-18T14:03:13.661518592Z",
            "bp": 40517.08,
            "bs": 4.0178,
            "ap": 40765.93,
            "as": 1.5516
        }
    }
        """,
    )

    request = CryptoLatestQuoteRequest(symbol_or_symbols=symbol)

    quotes = crypto_client.get_crypto_latest_quote(request)

    assert isinstance(quotes, Dict)

    quote = quotes[symbol]

    assert isinstance(quote, Quote)

    assert quote.ask_price == 40765.93
    assert quote.bid_size == 4.0178

    assert reqmock.called_once


def test_crypto_get_snapshot(reqmock, crypto_client: CryptoHistoricalDataClient):

    # test multisymbol request
    symbols = ["BTC/USD", "ETH/USD"]

    _symbols_in_url = "%2C".join(s for s in symbols)

    reqmock.get(
        f"https://data.alpaca.markets/v1beta3/crypto/us/snapshots?symbols={_symbols_in_url}",
        text="""
    {
        "snapshots": {
            "ETH/USD": {
                "latestTrade": {
                    "t": "2022-03-28T17:33:20.180926Z",
                    "p": 3373.04,
                    "s": 0.2436732,
                    "tks": "S",
                    "i": 247644006
                },
                "latestQuote": {
                    "t": "2022-03-28T17:32:30.318Z",
                    "bp": 3374.33,
                    "bs": 0.001,
                    "ap": 3374.34,
                    "as": 0.001
                },
                "minuteBar": {
                    "t": "2022-03-28T17:32:00Z",
                    "o": 3368.5,
                    "h": 3376.31,
                    "l": 3366.76,
                    "c": 3374.07,
                    "v": 907.81905184,
                    "n": 1149,
                    "vw": 3372.4441210299
                },
                "dailyBar": {
                    "t": "2022-03-28T05:00:00Z",
                    "o": 3319.63,
                    "h": 3402.17,
                    "l": 3305,
                    "c": 3374.07,
                    "v": 112120.6572392,
                    "n": 382244,
                    "vw": 3353.1926442533
                },
                "prevDailyBar": {
                    "t": "2022-03-27T05:00:00Z",
                    "o": 3140.35,
                    "h": 3328.83,
                    "l": 3127.74,
                    "c": 3319.46,
                    "v": 143163.68434276,
                    "n": 493112,
                    "vw": 3240.5911005308
                }
            },
            "BTC/USD": {
                "latestTrade": {
                    "t": "2022-03-28T17:33:20.19842Z",
                    "p": 47537.64,
                    "s": 0.00023096,
                    "tks": "B",
                    "i": 304775291
                },
                "latestQuote": {
                    "t": "2022-03-28T17:32:30.824Z",
                    "bp": 47530.99,
                    "bs": 1.65666998,
                    "ap": 47531.66,
                    "as": 0.00209349
                },
                "minuteBar": {
                    "t": "2022-03-28T17:32:00Z",
                    "o": 47494.71,
                    "h": 47542.23,
                    "l": 47471.56,
                    "c": 47532.2,
                    "v": 41.34429609,
                    "n": 873,
                    "vw": 47515.679114746
                },
                "dailyBar": {
                    "t": "2022-03-28T05:00:00Z",
                    "o": 47149.3,
                    "h": 47900,
                    "l": 46770.7,
                    "c": 47532.2,
                    "v": 8888.08292165,
                    "n": 348798,
                    "vw": 47385.1549250663
                },
                "prevDailyBar": {
                    "t": "2022-03-27T05:00:00Z",
                    "o": 44598.44,
                    "h": 47694,
                    "l": 44437.22,
                    "c": 47148.98,
                    "v": 12278.6017929,
                    "n": 559695,
                    "vw": 46041.2023793348
                }
            }
        }
    }  
        """,
    )

    request = CryptoSnapshotRequest(symbol_or_symbols=symbols)
    snapshots = crypto_client.get_crypto_snapshot(request)

    assert isinstance(snapshots, Dict)
    snapshot = snapshots["BTC/USD"]

    assert isinstance(snapshot, Snapshot)

    assert snapshot.latest_trade.price == 47537.64
    assert snapshot.latest_quote.bid_size == 1.65666998
    assert snapshot.daily_bar.low == 46770.7
    assert snapshot.minute_bar.close == 47532.2
    assert snapshot.daily_bar.volume == 8888.08292165
    assert snapshot.previous_daily_bar.high == 47694

    assert reqmock.called_once


def test_crypto_latest_bar(reqmock, crypto_client: CryptoHistoricalDataClient):

    symbol = "BTC/USD"
    reqmock.get(
        f"https://data.alpaca.markets/v1beta3/crypto/us/latest/bars?symbols={symbol}",
        text="""
           {
            "bars": {
                "BTC/USD": 
                    {
                        "t": "2022-05-27T10:18:00Z",
                        "o": 28999,
                        "h": 29003,
                        "l": 28999,
                        "c": 29003,
                        "v": 0.01,
                        "n": 4,
                        "vw": 29001
                    }
                
            },
            "next_page_token": null
        }
    """,
    )

    request = CryptoLatestBarRequest(symbol_or_symbols=symbol)

    bars = crypto_client.get_crypto_latest_bar(request)

    assert isinstance(bars, Dict)

    bar = bars[symbol]

    assert isinstance(bar, Bar)

    assert bar.open == 28999

    assert reqmock.called_once
