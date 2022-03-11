from alpaca.data.clients import HistoricalDataClient
from alpaca.common.time import TimeFrame
from alpaca.data.models import BarSet

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


def test_get_bars(reqmock, client, raw_client):

    # Test single symbol request
    reqmock.get("https://data.alpaca.markets/v2/stocks/AAPL/bars?timeframe=1Day&start=2022-02-01&limit=2", text='''
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
        ''',
    )   

    barset = client.get_bars("AAPL", TimeFrame.Day, "2022-02-01", limit=2)

    assert type(barset) == BarSet

    assert barset["AAPL"][0].open == 174
    assert barset["AAPL"][0].high == 174.84

    assert barset.df.index.nlevels == 1
    assert barset.df.index[0].day == 1

    # raw data client
    raw_barset = raw_client.get_bars("AAPL", TimeFrame.Day, "2022-02-01", limit=2)

    assert type(raw_barset) == dict
    assert raw_barset["AAPL"][0]['o'] == 174
    assert raw_barset["AAPL"][0]['h'] == 174.84
    
    # test multisymbol request
    reqmock.get("https://data.alpaca.markets/v2/stocks/bars?timeframe=1Day&start=2022-03-09&end=2022-03-09&symbols=AAPL%2CTSLA", text='''
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
        ''',
    )
    barset = client.get_bars(["AAPL", "TSLA"], TimeFrame.Day, "2022-03-09", end="2022-03-09")

    assert(type(barset) == BarSet)

    assert barset["TSLA"][0].open == 839
    assert barset["AAPL"][0].low == 159.41

    assert barset.df.index[0][1].day == 9
    assert barset.df.index.nlevels == 2

    # raw data client
    raw_barset = raw_client.get_bars(["AAPL", "TSLA"], TimeFrame.Day, "2022-03-09", end="2022-03-09")

    assert type(raw_barset) == dict

    assert raw_barset["TSLA"][0]['o'] == 839
    assert raw_barset["AAPL"][0]['l']== 159.41


   