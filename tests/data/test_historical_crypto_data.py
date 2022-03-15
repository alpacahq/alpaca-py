from ast import ExceptHandler
from alpaca.data.clients import HistoricalDataClient
from alpaca.common.time import TimeFrame
from alpaca.data.models import BarSet
from alpaca.data.enums import Exchange

import pytest
import requests_mock

@pytest.fixture
def reqmock():
    with requests_mock.Mocker() as m:
        yield m

@pytest.fixture
def client():
    client = HistoricalDataClient('key-id', 'secret-key')
    return client

@pytest.fixture
def raw_client():
    raw_client = HistoricalDataClient('key-id', 'secret-key', raw_data=True)
    return raw_client


def test_get_crypto_bars(reqmock, client, raw_client):

    
    # Test single symbol request

    symbol = 'BTCUSD'
    timeframe = TimeFrame.Day
    start = '2022-02-01'
    limit = 2
    exchanges = [Exchange.FTXU]
    _exchanges_in_url = '%2C'.join(e.value for e in exchanges)

    reqmock.get(f"https://data.alpaca.markets/v1beta1/crypto/{symbol}/bars?timeframe={timeframe}&start={start}&limit={limit}&exchanges={_exchanges_in_url}", text='''
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
        ''',
    )   

    barset = client.get_crypto_bars(symbol_or_symbols=symbol, timeframe=timeframe, start=start, limit=limit, exchanges=exchanges)

    assert type(barset) == BarSet

    assert barset[symbol][0].open == 174
    assert barset[symbol][0].high == 174.84

    assert barset[symbol][0].exchange.value == 'FTXU'

    assert barset.df.index.nlevels == 1
    assert barset.df.index[0].day == 1

    # raw data client
    raw_barset = raw_client.get_crypto_bars(symbol_or_symbols=symbol, timeframe=timeframe, start=start, limit=limit, exchanges=exchanges)

    assert type(raw_barset) == dict
    assert raw_barset[symbol][0]['o'] == 174
    assert raw_barset[symbol][0]['h'] == 174.84

    assert raw_barset[symbol][0]['x'] == 'FTXU'
    
    # test multisymbol request
    symbols = ["BTCUSD", "ETHUSD"]
    start = "2022-03-09"
    end = "2022-03-09"
    _symbols_in_url = '%2C'.join(s for s in symbols)

    reqmock.get(f"https://data.alpaca.markets/v1beta1/crypto/bars?timeframe={timeframe}&start={start}&end={end}&symbols={_symbols_in_url}", text='''
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
        ''',
    )
    barset = client.get_crypto_bars(symbol_or_symbols=symbols, timeframe=timeframe, start=start, end=end)

    assert(type(barset) == BarSet)

    assert barset["BTCUSD"][0].open == 161.51
    assert barset["ETHUSD"][0].low == 832.01

    assert barset["BTCUSD"][0].exchange.value == "CBSE"
    assert barset["ETHUSD"][0].exchange.value == "ERSX"

    assert barset.df.index[0][1].day == 9
    assert barset.df.index.nlevels == 2

    # raw data client
    raw_barset = raw_client.get_crypto_bars(symbol_or_symbols=symbols, timeframe=timeframe, start=start, end=end)

    assert type(raw_barset) == dict

    assert raw_barset["BTCUSD"][0]['x'] == "CBSE"
    assert raw_barset["ETHUSD"][0]['x']== "ERSX"

