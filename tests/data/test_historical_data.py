import pytest
import requests_mock

from alpaca.common.time import TimeFrame
from alpaca.data.clients import HistoricalDataClient
from alpaca.data.models import BarSet, QuoteSet, TradeSet


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


def test_get_bars(reqmock, client, raw_client):

    # Test single symbol request

    symbol = "AAPL"
    timeframe = TimeFrame.Day
    start = "2022-02-01"
    limit = 2

    reqmock.get(
        f"https://data.alpaca.markets/v2/stocks/{symbol}/bars?timeframe={timeframe}&start={start}&limit={limit}",
        text="""
    {
        "bars": [
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
        ],
        "symbol": "AAPL",
        "next_page_token": "QUFQTHxEfDIwMjItMDItMDJUMDU6MDA6MDAuMDAwMDAwMDAwWg=="
    }   
        """,
    )

    barset = client.get_bars(
        symbol_or_symbols=symbol, timeframe=timeframe, start=start, limit=limit
    )

    assert type(barset) == BarSet

    assert barset[symbol][0].open == 174
    assert barset[symbol][0].high == 174.84

    assert barset.df.index.nlevels == 1
    assert barset.df.index[0].day == 1

    # raw data client
    raw_barset = raw_client.get_bars(
        symbol_or_symbols=symbol, timeframe=timeframe, start=start, limit=limit
    )

    assert type(raw_barset) == dict
    assert raw_barset[symbol][0]["o"] == 174
    assert raw_barset[symbol][0]["h"] == 174.84

    # test multisymbol request
    symbols = ["AAPL", "TSLA"]
    start = "2022-03-09"
    end = "2022-03-09"
    _symbols_in_url = "%2C".join(s for s in symbols)

    reqmock.get(
        f"https://data.alpaca.markets/v2/stocks/bars?timeframe={timeframe}&start={start}&end={end}&symbols={_symbols_in_url}",
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
    barset = client.get_bars(
        symbol_or_symbols=symbols, timeframe=timeframe, start=start, end=end
    )

    assert type(barset) == BarSet

    assert barset["TSLA"][0].open == 839
    assert barset["AAPL"][0].low == 159.41

    assert barset.df.index[0][1].day == 9
    assert barset.df.index.nlevels == 2

    # raw data client
    raw_barset = raw_client.get_bars(
        symbol_or_symbols=symbols, timeframe=timeframe, start=start, end=end
    )

    assert type(raw_barset) == dict

    assert raw_barset["TSLA"][0]["o"] == 839
    assert raw_barset["AAPL"][0]["l"] == 159.41


def test_get_quotes(reqmock, client, raw_client):

    # Test single symbol request

    symbol = "AAPL"
    start = "2022-03-09"
    limit = 2

    reqmock.get(
        f"https://data.alpaca.markets/v2/stocks/{symbol}/quotes?start={start}&limit={limit}",
        text="""
    {
        "quotes": [
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
        ],
        "symbol": "AAPL",
        "next_page_token": "QUFQTHwyMDIyLTAzLTA5VDA5OjAwOjAwLjAwMDA1OTAwMFp8Q0ZEQUU5QTg="
    }   
        """,
    )

    quoteset = client.get_quotes(symbol_or_symbols=symbol, start=start, limit=limit)

    assert type(quoteset) == QuoteSet

    assert quoteset[symbol][0].ask_price == 158.65
    assert quoteset[symbol][0].bid_size == 4

    assert quoteset[symbol][0].ask_exchange == "K"

    assert quoteset.df.index.nlevels == 1
    assert quoteset.df.index[0].day == 9

    # raw data client
    raw_quoteset = raw_client.get_quotes(
        symbol_or_symbols=symbol, start=start, limit=limit
    )

    assert type(raw_quoteset) == dict

    assert raw_quoteset[symbol][0]["ap"] == 158.65
    assert raw_quoteset[symbol][0]["bs"] == 4

    assert raw_quoteset[symbol][0]["ax"] == "K"

    # test multisymbol request
    symbols = ["AAPL", "TSLA"]
    start = "2022-03-09"
    end = "2022-03-09"
    _symbols_in_url = "%2C".join(s for s in symbols)

    reqmock.get(
        f"https://data.alpaca.markets/v2/stocks/quotes?start={start}&symbols={_symbols_in_url}",
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
    quoteset = client.get_quotes(symbol_or_symbols=symbols, start=start)

    assert type(quoteset) == QuoteSet

    assert quoteset["AAPL"][0].ask_size == 1
    assert quoteset["TSLA"][0].bid_price == 840.75

    assert quoteset["AAPL"][0].bid_exchange == "Q"

    assert quoteset.df.index[0][1].day == 9
    assert quoteset.df.index.nlevels == 2

    # raw data client
    raw_quoteset = raw_client.get_quotes(
        symbol_or_symbols=symbols,
        start=start,
    )

    assert type(raw_quoteset) == dict

    assert raw_quoteset["AAPL"][0]["ap"] == 158.65
    assert raw_quoteset["TSLA"][0]["bs"] == 1

    assert raw_quoteset["AAPL"][0]["ax"] == "K"


def test_get_trades(reqmock, client, raw_client):

    # Test single symbol request
    symbol = "AAPL"
    start = "2022-03-09"
    limit = 2

    reqmock.get(
        f"https://data.alpaca.markets/v2/stocks/{symbol}/trades?start={start}&limit={limit}",
        text="""
    {
        "trades": [
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
        ],
        "symbol": "AAPL",
        "next_page_token": "QUFQTHwyMDIyLTAzLTA5VDA1OjAwOjE2LjkxMDAwMDAwMFp8RHwwOTIyMzM3MjAzNjg1NDc3NTk3Ng=="
    }  
        """,
    )

    tradeset = client.get_trades(symbol_or_symbols=symbol, start=start, limit=limit)

    assert type(tradeset) == TradeSet

    assert tradeset[symbol][0].price == 159.07
    assert tradeset[symbol][0].size == 1

    assert tradeset[symbol][0].exchange == "D"

    assert tradeset.df.index.nlevels == 1
    assert tradeset.df.index[0].day == 9

    # raw data client
    raw_tradeset = raw_client.get_trades(
        symbol_or_symbols=symbol, start=start, limit=limit
    )

    assert type(raw_tradeset) == dict

    assert raw_tradeset[symbol][0]["p"] == 159.07
    assert raw_tradeset[symbol][0]["s"] == 1

    assert raw_tradeset[symbol][0]["x"] == "D"

    # test multisymbol request
    symbols = ["AAPL", "TSLA"]
    start = "2022-03-09"
    end = "2022-03-09"
    _symbols_in_url = "%2C".join(s for s in symbols)

    reqmock.get(
        f"https://data.alpaca.markets/v2/stocks/trades?start={start}&symbols={_symbols_in_url}",
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
    tradeset = client.get_trades(symbol_or_symbols=symbols, start=start)
    assert type(tradeset) == TradeSet

    assert tradeset["AAPL"][0].size == 1
    assert tradeset["TSLA"][0].price == 833

    assert tradeset["AAPL"][0].exchange == "D"

    assert tradeset.df.index[0][1].day == 9
    assert tradeset.df.index.nlevels == 2

    # raw data client
    raw_tradeset = raw_client.get_trades(
        symbol_or_symbols=symbols, start=start, end=end
    )

    assert type(raw_tradeset) == dict

    assert raw_tradeset["AAPL"][0]["p"] == 159.07
    assert raw_tradeset["TSLA"][0]["s"] == 1

    assert raw_tradeset["AAPL"][0]["x"] == "D"
