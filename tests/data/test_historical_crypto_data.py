import pytest
import requests_mock

from alpaca.data.time import TimeFrame
from alpaca.data.historical import HistoricalDataClient
from alpaca.data.enums import Exchange
from alpaca.data.models import (
    XBBO,
    BarSet,
    Quote,
    QuoteSet,
    SnapshotSet,
    Trade,
    TradeSet,
)


@pytest.fixture
def reqmock():
    with requests_mock.Mocker() as m:
        yield m


@pytest.fixture
def client():
    client = HistoricalDataClient("key-id", "secret-key")
    return client


@pytest.fixture
def raw_client():
    raw_client = HistoricalDataClient("key-id", "secret-key", raw_data=True)
    return raw_client


def test_get_crypto_bars(reqmock, client, raw_client):

    # Test single symbol request

    symbol = "BTCUSD"
    timeframe = TimeFrame.Day
    start = "2022-02-01"
    limit = 2
    exchanges = [Exchange.FTXU]
    _exchanges_in_url = "%2C".join(e.value for e in exchanges)

    reqmock.get(
        f"https://data.alpaca.markets/v1beta1/crypto/{symbol}/bars?timeframe={timeframe}&start={start}&limit={limit}&exchanges={_exchanges_in_url}",
        text="""
    {
        "bars": [
            {
                "t": "2022-02-01T05:00:00Z",
                "x": "FTXU",
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
                "x": "FTXU",
                "o": 174.64,
                "h": 175.88,
                "l": 173.33,
                "c": 175.84,
                "v": 84817432,
                "n": 675034,
                "vw": 174.941288
            }
        ],
        "symbol": "BTCUSD",
        "next_page_token": "QUFQTHxEfDIwMjItMDItMDJUMDU6MDA6MDAuMDAwMDAwMDAwWg=="
    }   
        """,
    )

    barset = client.get_crypto_bars(
        symbol_or_symbols=symbol,
        timeframe=timeframe,
        start=start,
        limit=limit,
        exchanges=exchanges,
    )

    assert type(barset) == BarSet

    assert barset[symbol][0].open == 174
    assert barset[symbol][0].high == 174.84

    assert barset[symbol][0].exchange == Exchange.FTXU

    assert barset.df.index.nlevels == 1
    assert barset.df.index[0].day == 1

    # raw data client
    raw_barset = raw_client.get_crypto_bars(
        symbol_or_symbols=symbol,
        timeframe=timeframe,
        start=start,
        limit=limit,
        exchanges=exchanges,
    )

    assert type(raw_barset) == dict
    assert raw_barset[symbol][0]["o"] == 174
    assert raw_barset[symbol][0]["h"] == 174.84

    assert raw_barset[symbol][0]["x"] == "FTXU"

    # test multisymbol request
    symbols = ["BTCUSD", "ETHUSD"]
    start = "2022-03-09"
    end = "2022-03-09"
    _symbols_in_url = "%2C".join(s for s in symbols)

    reqmock.get(
        f"https://data.alpaca.markets/v1beta1/crypto/bars?timeframe={timeframe}&start={start}&end={end}&symbols={_symbols_in_url}",
        text="""
    {
        "bars": {
            "BTCUSD": [
                {
                    "t": "2022-03-09T05:00:00Z",
                    "x": "CBSE",
                    "o": 161.51,
                    "h": 163.41,
                    "l": 159.41,
                    "c": 162.95,
                    "v": 88496480,
                    "n": 700291,
                    "vw": 161.942117
                }
            ],
            "ETHUSD": [
                {
                    "t": "2022-03-09T05:00:00Z",
                    "x": "ERSX",
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
    barset = client.get_crypto_bars(
        symbol_or_symbols=symbols, timeframe=timeframe, start=start, end=end
    )

    assert type(barset) == BarSet

    assert barset["BTCUSD"][0].open == 161.51
    assert barset["ETHUSD"][0].low == 832.01

    assert barset["BTCUSD"][0].exchange == Exchange.CBSE
    assert barset["ETHUSD"][0].exchange == Exchange.ERSX

    assert barset.df.index[0][1].day == 9
    assert barset.df.index.nlevels == 2

    # raw data client
    raw_barset = raw_client.get_crypto_bars(
        symbol_or_symbols=symbols, timeframe=timeframe, start=start, end=end
    )

    assert type(raw_barset) == dict

    assert raw_barset["BTCUSD"][0]["x"] == "CBSE"
    assert raw_barset["ETHUSD"][0]["x"] == "ERSX"


def test_get_crypto_quotes(reqmock, client, raw_client):

    # Test single symbol request

    symbol = "BTCUSD"
    start = "2022-03-09T00:00:00"
    end = "2022-03-09T00:00:30"
    limit = 2

    reqmock.get(
        f"https://data.alpaca.markets/v2/stocks/{symbol}/quotes?start={start}&limit={limit}",
        text="""
    {
        "quotes": [
            {
                "t": "2022-03-09T06:00:00.03994496Z",
                "x": "FTXU",
                "bp": 41397.43,
                "bs": 0.1847,
                "ap": 41659.6,
                "as": 0.385
            },
            {
                "t": "2022-03-09T06:00:00.060563155Z",
                "x": "ERSX",
                "bp": 41414.38,
                "bs": 1.5,
                "ap": 41672.24,
                "as": 1.444128
            }
        ],
        "symbol": "BTCUSD",
        "next_page_token": null
    }   
        """,
    )

    quoteset = client.get_quotes(symbol_or_symbols=symbol, start=start, limit=limit)

    assert type(quoteset) == QuoteSet

    assert quoteset[symbol][0].ask_price == 41659.6
    assert quoteset[symbol][0].bid_size == 0.1847

    assert quoteset[symbol][0].exchange == Exchange.FTXU

    assert quoteset.df.index.nlevels == 1
    assert quoteset.df.index[0].day == 9

    # raw data client
    raw_quoteset = raw_client.get_quotes(
        symbol_or_symbols=symbol, start=start, limit=limit
    )

    assert type(raw_quoteset) == dict

    assert raw_quoteset[symbol][1]["ap"] == 41672.24
    assert raw_quoteset[symbol][1]["bs"] == 1.5

    assert raw_quoteset[symbol][1]["x"] == "ERSX"

    # test multisymbol request
    symbols = ["BTCUSD", "ETHUSD"]
    start = "2022-03-09T00:00:00"
    end = "2022-03-09T00:00:30"
    _symbols_in_url = "%2C".join(s for s in symbols)

    reqmock.get(
        f"https://data.alpaca.markets/v2/stocks/quotes?start={start}&end={end}&symbols={_symbols_in_url}",
        text="""
    {
        "quotes": {
            "BTCUSD": [
                {
                    "t": "2022-03-09T06:00:00.03994496Z",
                    "x": "FTXU",
                    "bp": 41397.43,
                    "bs": 0.1847,
                    "ap": 41659.6,
                    "as": 0.385
                },
                {
                    "t": "2022-03-09T06:00:00.060563155Z",
                    "x": "ERSX",
                    "bp": 41414.38,
                    "bs": 1.5,
                    "ap": 41672.24,
                    "as": 1.444128
                }
            ],
            "ETHUSD": [
                {
                    "t": "2022-03-09T06:00:00.23589632Z",
                    "x": "FTXU",
                    "bp": 2706.95,
                    "bs": 5.46,
                    "ap": 2723.85,
                    "as": 3.9
                },
                {
                    "t": "2022-03-09T06:00:00.290033408Z",
                    "x": "FTXU",
                    "bp": 2706.95,
                    "bs": 5.46,
                    "ap": 2723.85,
                    "as": 3.9
                }
            ]
        },
        "next_page_token": null
    }   
        """,
    )
    quoteset = client.get_quotes(symbol_or_symbols=symbols, start=start, end=end)

    assert type(quoteset) == QuoteSet

    assert quoteset["BTCUSD"][0].ask_size == 0.385
    assert quoteset["ETHUSD"][0].bid_price == 2706.95

    assert quoteset["BTCUSD"][0].exchange == Exchange.FTXU

    assert quoteset.df.index[0][1].day == 9
    assert quoteset.df.index.nlevels == 2

    # raw data client
    raw_quoteset = raw_client.get_quotes(
        symbol_or_symbols=symbols, start=start, end=end
    )

    assert type(raw_quoteset) == dict

    assert raw_quoteset["BTCUSD"][0]["ap"] == 41659.6
    assert raw_quoteset["ETHUSD"][0]["bs"] == 5.46

    assert raw_quoteset["ETHUSD"][0]["x"] == "FTXU"


def test_get_trades(reqmock, client, raw_client):

    # Test single symbol request
    symbol = "BTCUSD"
    start = "2022-03-09"
    limit = 2

    reqmock.get(
        f"https://data.alpaca.markets/v1beta1/crypto/{symbol}/trades?start={start}&limit={limit}",
        text="""
    {
        "trades": [
            {
            "t": "2022-03-09T06:00:00.059832Z",
            "x": "CBSE",
            "p": 41521.33,
            "s": 0.00024136,
            "tks": "S",
            "i": 293648597
            }
        ],
        "symbol": "BTCUSD",
        "next_page_token": null
    }  
        """,
    )

    tradeset = client.get_crypto_trades(
        symbol_or_symbols=symbol, start=start, limit=limit
    )

    assert type(tradeset) == TradeSet

    assert tradeset[symbol][0].price == 41521.33
    assert tradeset[symbol][0].size == 0.00024136

    assert tradeset[symbol][0].exchange == Exchange.CBSE

    assert tradeset.df.index.nlevels == 1
    assert tradeset.df.index[0].day == 9

    # raw data client
    raw_tradeset = raw_client.get_crypto_trades(
        symbol_or_symbols=symbol, start=start, limit=limit
    )

    assert type(raw_tradeset) == dict

    assert raw_tradeset[symbol][0]["p"] == 41521.33
    assert raw_tradeset[symbol][0]["s"] == 0.00024136

    assert raw_tradeset[symbol][0]["x"] == "CBSE"

    # test multisymbol request
    symbols = ["BTCUSD", "ETHUSD"]
    start = "2022-03-09"
    end = "2022-03-09"
    _symbols_in_url = "%2C".join(s for s in symbols)

    reqmock.get(
        f"https://data.alpaca.markets/v1beta1/crypto/trades?start={start}&symbols={_symbols_in_url}",
        text="""
    {
        "trades": {
            "BTCUSD": [
                {
                    "t": "2022-03-09T06:00:00.080264Z",
                    "x": "CBSE",
                    "p": 41516.08,
                    "s": 0.00315427,
                    "tks": "B",
                    "i": 293648598
                }
            ],
            "ETHUSD": [
                {
                    "t": "2022-03-09T06:00:00.228546Z",
                    "x": "CBSE",
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
    tradeset = client.get_crypto_trades(symbol_or_symbols=symbols, start=start)
    assert type(tradeset) == TradeSet

    assert tradeset["BTCUSD"][0].price == 41516.08
    assert tradeset["ETHUSD"][0].size == 0.001

    assert tradeset["BTCUSD"][0].exchange == Exchange.CBSE

    assert tradeset.df.index[0][1].day == 9
    assert tradeset.df.index.nlevels == 2

    # raw data client
    raw_tradeset = raw_client.get_crypto_trades(
        symbol_or_symbols=symbols, start=start, end=end
    )

    assert type(raw_tradeset) == dict

    assert raw_tradeset["ETHUSD"][0]["p"] == 2715.06
    assert raw_tradeset["BTCUSD"][0]["s"] == 0.00315427

    assert raw_tradeset["ETHUSD"][0]["x"] == "CBSE"


def test_get_crypto_latest_trade(reqmock, client, raw_client):

    # Test single symbol request
    symbol = "BTCUSD"
    exchange = Exchange.FTXU

    reqmock.get(
        f"https://data.alpaca.markets/v1beta1/crypto/{symbol}/trades/latest?exchange=FTXU",
        text="""
    {
        "symbol": "BTCUSD",
        "trade": {
            "t": "2022-03-18T14:03:31.960672Z",
            "x": "FTXU",
            "p": 40650,
            "s": 0.1517,
            "tks": "B",
            "i": 26932440
        }
    } 
        """,
    )

    trade = client.get_crypto_latest_trade(symbol=symbol, exchange=exchange)

    assert type(trade) == Trade

    assert trade.price == 40650
    assert trade.size == 0.1517

    assert trade.exchange == Exchange.FTXU

    # raw data client
    raw_trade = raw_client.get_crypto_latest_trade(symbol=symbol, exchange=exchange)

    assert type(raw_trade) == dict

    assert raw_trade["tks"] == "B"
    assert raw_trade["i"] == 26932440

    assert raw_trade["x"] == "FTXU"


def test_get_crypto_latest_quote(reqmock, client, raw_client):

    # Test single symbol request
    symbol = "BTCUSD"
    exchange = Exchange.FTXU

    reqmock.get(
        f"https://data.alpaca.markets/v1beta1/crypto/{symbol}/quotes/latest?exchange=FTXU",
        text="""
    {
        "symbol": "BTCUSD",
        "quote": {
            "t": "2022-03-18T14:03:13.661518592Z",
            "x": "FTXU",
            "bp": 40517.08,
            "bs": 4.0178,
            "ap": 40765.93,
            "as": 1.5516
        }
    }
        """,
    )

    quote = client.get_crypto_latest_quote(symbol=symbol, exchange=exchange)

    assert type(quote) == Quote

    assert quote.ask_price == 40765.93
    assert quote.bid_size == 4.0178

    assert quote.exchange == Exchange.FTXU

    # raw data client
    raw_quote = raw_client.get_crypto_latest_quote(symbol=symbol, exchange=exchange)

    assert type(raw_quote) == dict

    assert raw_quote["bp"] == 40517.08
    assert raw_quote["as"] == 1.5516

    assert raw_quote["x"] == "FTXU"


def test_crypto_get_snapshot(reqmock, client, raw_client):

    # Test single symbol request
    symbol = "BTCUSD"
    exchange = Exchange.CBSE
    reqmock.get(
        f"https://data.alpaca.markets/v1beta1/crypto/{symbol}/snapshot?exchange={exchange}",
        text="""
    {
        "symbol": "BTCUSD",
        "latestTrade": {
            "t": "2022-03-28T17:27:57.794134Z",
            "x": "CBSE",
            "p": 47458.69,
            "s": 0.00008231,
            "tks": "S",
            "i": 304771804
        },
        "latestQuote": {
            "t": "2022-03-28T17:27:42.591Z",
            "x": "CBSE",
            "bp": 47466.1,
            "bs": 0.001,
            "ap": 47467.49,
            "as": 0.001197
        },
        "minuteBar": {
            "t": "2022-03-28T17:26:00Z",
            "x": "CBSE",
            "o": 47431.48,
            "h": 47449.87,
            "l": 47418.34,
            "c": 47447.73,
            "v": 3.28432365,
            "n": 472,
            "vw": 47436.1727214804
        },
        "dailyBar": {
            "t": "2022-03-28T05:00:00Z",
            "x": "CBSE",
            "o": 47149.3,
            "h": 47900,
            "l": 46770.7,
            "c": 47447.73,
            "v": 8720.15520728,
            "n": 345005,
            "vw": 47383.1123162664
        },
        "prevDailyBar": {
            "t": "2022-03-27T05:00:00Z",
            "x": "CBSE",
            "o": 44598.44,
            "h": 47694,
            "l": 44437.22,
            "c": 47148.98,
            "v": 12278.6017929,
            "n": 559695,
            "vw": 46041.2023793348
        }
    }        
    """,
    )

    snapshot = client.get_crypto_snapshot(symbol_or_symbols=symbol, exchange=exchange)

    assert type(snapshot) == SnapshotSet

    assert snapshot[symbol].latest_trade.price == 47458.69
    assert snapshot[symbol].latest_quote.bid_size == 0.001
    assert snapshot[symbol].minute_bar.close == 47447.73
    assert snapshot[symbol].daily_bar.volume == 8720.15520728
    assert snapshot[symbol].previous_daily_bar.high == 47694

    # raw data client
    raw_snapshot = raw_client.get_crypto_snapshot(
        symbol_or_symbols=symbol, exchange=exchange
    )

    assert type(raw_snapshot) == dict

    assert raw_snapshot[symbol]["latestTrade"]["p"] == 47458.69
    assert raw_snapshot[symbol]["latestQuote"]["bs"] == 0.001
    assert raw_snapshot[symbol]["minuteBar"]["c"] == 47447.73
    assert raw_snapshot[symbol]["dailyBar"]["v"] == 8720.15520728
    assert raw_snapshot[symbol]["prevDailyBar"]["h"] == 47694

    # test multisymbol request
    symbols = ["BTCUSD", "ETHUSD"]

    _symbols_in_url = "%2C".join(s for s in symbols)

    reqmock.get(
        f"https://data.alpaca.markets/v1beta1/crypto/snapshots?symbols={_symbols_in_url}&exchange={exchange}",
        text="""
    {
        "snapshots": {
            "ETHUSD": {
                "latestTrade": {
                    "t": "2022-03-28T17:33:20.180926Z",
                    "x": "CBSE",
                    "p": 3373.04,
                    "s": 0.2436732,
                    "tks": "S",
                    "i": 247644006
                },
                "latestQuote": {
                    "t": "2022-03-28T17:32:30.318Z",
                    "x": "CBSE",
                    "bp": 3374.33,
                    "bs": 0.001,
                    "ap": 3374.34,
                    "as": 0.001
                },
                "minuteBar": {
                    "t": "2022-03-28T17:32:00Z",
                    "x": "CBSE",
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
                    "x": "CBSE",
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
                    "x": "CBSE",
                    "o": 3140.35,
                    "h": 3328.83,
                    "l": 3127.74,
                    "c": 3319.46,
                    "v": 143163.68434276,
                    "n": 493112,
                    "vw": 3240.5911005308
                }
            },
            "BTCUSD": {
                "latestTrade": {
                    "t": "2022-03-28T17:33:20.19842Z",
                    "x": "CBSE",
                    "p": 47537.64,
                    "s": 0.00023096,
                    "tks": "B",
                    "i": 304775291
                },
                "latestQuote": {
                    "t": "2022-03-28T17:32:30.824Z",
                    "x": "CBSE",
                    "bp": 47530.99,
                    "bs": 1.65666998,
                    "ap": 47531.66,
                    "as": 0.00209349
                },
                "minuteBar": {
                    "t": "2022-03-28T17:32:00Z",
                    "x": "CBSE",
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
                    "x": "CBSE",
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
                    "x": "CBSE",
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
    snapshots = client.get_crypto_snapshot(symbol_or_symbols=symbols, exchange=exchange)

    assert type(snapshot) == SnapshotSet

    assert snapshots["ETHUSD"].latest_trade.price == 3373.04
    assert snapshots["ETHUSD"].latest_quote.bid_size == 0.001
    assert snapshots["ETHUSD"].daily_bar.low == 3305
    assert snapshots["BTCUSD"].minute_bar.close == 47532.2
    assert snapshots["BTCUSD"].daily_bar.volume == 8888.08292165
    assert snapshots["BTCUSD"].previous_daily_bar.high == 47694

    # raw data client
    raw_snapshots = raw_client.get_crypto_snapshot(
        symbol_or_symbols=symbols, exchange=exchange
    )

    assert type(raw_snapshot) == dict

    assert raw_snapshots["ETHUSD"]["latestTrade"]["p"] == 3373.04
    assert raw_snapshots["ETHUSD"]["latestQuote"]["bs"] == 0.001
    assert raw_snapshots["ETHUSD"]["dailyBar"]["l"] == 3305
    assert raw_snapshots["BTCUSD"]["minuteBar"]["c"] == 47532.2
    assert raw_snapshots["BTCUSD"]["dailyBar"]["v"] == 8888.08292165
    assert raw_snapshots["BTCUSD"]["prevDailyBar"]["h"] == 47694


def test_get_crypto_xbbo(reqmock, client, raw_client):

    # Test single symbol request
    symbol = "BTCUSD"
    exchanges = [Exchange.FTXU, Exchange.CBSE, Exchange.ERSX]

    _exchanges_in_url = "%2C".join(s.value for s in exchanges)
    reqmock.get(
        f"https://data.alpaca.markets/v1beta1/crypto/{symbol}/xbbo/latest?exchanges={_exchanges_in_url}",
        text="""
    {
        "symbol": "BTCUSD",
        "xbbo": {
            "t": "2022-03-28T18:27:25.962996224Z",
            "ax": "FTXU",
            "ap": 47726,
            "as": 0.325,
            "bx": "CBSE",
            "bp": 47757.59,
            "bs": 0.001
        }
    }
        """,
    )

    xbbo = client.get_crypto_xbbo(symbol=symbol, exchanges=exchanges)

    assert type(xbbo) == XBBO

    assert xbbo.ask_price == 47726
    assert xbbo.bid_size == 0.001

    assert xbbo.ask_exchange == Exchange.FTXU
    assert xbbo.bid_exchange == Exchange.CBSE

    # raw data client
    raw_xbbo = raw_client.get_crypto_xbbo(symbol=symbol, exchanges=exchanges)

    assert type(raw_xbbo) == dict

    assert raw_xbbo["bp"] == 47757.59
    assert raw_xbbo["as"] == 0.325

    assert raw_xbbo["ax"] == "FTXU"
    assert raw_xbbo["bx"] == "CBSE"
