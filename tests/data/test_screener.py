from alpaca.data.historical.screener import ScreenerClient

from alpaca.data.requests import MarketMoversRequest, MostActivesRequest

from alpaca.data.models.screener import MostActives, Movers

from alpaca.common.enums import BaseURL


def test_get_market_movers(reqmock, screener_client: ScreenerClient):
    num_movers = 10
    reqmock.get(
        f"{BaseURL.DATA}/v1beta1/screener/stocks/movers?top={num_movers}",
        text="""
        {
    "gainers": [
        {
            "change": 59.75,
            "percent_change": 1832.9,
            "price": 63.0125,
            "symbol": "BOIL"
        },
        {
            "change": 18.49,
            "percent_change": 933.84,
            "price": 20.47,
            "symbol": "UVXY"
        },
        {
            "change": 3.069,
            "percent_change": 728.98,
            "price": 3.49,
            "symbol": "SHPW"
        },
        {
            "change": 21.42,
            "percent_change": 408.02,
            "price": 26.6708,
            "symbol": "VIXY"
        },
        {
            "change": 0.0142,
            "percent_change": 249.12,
            "price": 0.0199,
            "symbol": "ADILW"
        },
        {
            "change": 0.1076,
            "percent_change": 223.24,
            "price": 0.1558,
            "symbol": "BYN.WS"
        },
        {
            "change": 0.0446,
            "percent_change": 141.14,
            "price": 0.0762,
            "symbol": "BROGW"
        },
        {
            "change": 0.676,
            "percent_change": 111.94,
            "price": 1.28,
            "symbol": "PIK"
        },
        {
            "change": 0.0663,
            "percent_change": 107.28,
            "price": 0.1281,
            "symbol": "BYNOW"
        },
        {
            "change": 0.025,
            "percent_change": 96.15,
            "price": 0.051,
            "symbol": "EFHTW"
        }
    ],
    "last_updated": "2023-06-23T14:13:00.163514169Z",
    "losers": [
        {
            "change": -0.0706,
            "percent_change": -95.02,
            "price": 0.0037,
            "symbol": "FMIVW"
        },
        {
            "change": -0.445,
            "percent_change": -60.53,
            "price": 0.2902,
            "symbol": "LOV"
        },
        {
            "change": -0.2602,
            "percent_change": -57.82,
            "price": 0.1898,
            "symbol": "SMX"
        },
        {
            "change": -0.0241,
            "percent_change": -38.81,
            "price": 0.038,
            "symbol": "CUENW"
        },
        {
            "change": -0.26,
            "percent_change": -37.68,
            "price": 0.43,
            "symbol": "ZURAW"
        },
        {
            "change": -0.0422,
            "percent_change": -37.61,
            "price": 0.07,
            "symbol": "SBEV.WS"
        },
        {
            "change": -0.0015,
            "percent_change": -37.5,
            "price": 0.0025,
            "symbol": "ENTXW"
        },
        {
            "change": -0.0142,
            "percent_change": -35.86,
            "price": 0.0254,
            "symbol": "SMXWW"
        },
        {
            "change": -0.0646,
            "percent_change": -35.75,
            "price": 0.1161,
            "symbol": "GGAAW"
        },
        {
            "change": -0.0067,
            "percent_change": -34.72,
            "price": 0.0126,
            "symbol": "AVHIW"
        }
    ],
    "market_type": "stocks"
    }
    """,
    )
    movers = screener_client.get_market_movers(MarketMoversRequest(top=num_movers))
    assert isinstance(movers, Movers)
    assert len(movers.gainers) == num_movers
    assert len(movers.losers) == num_movers


def test_get_most_actives(reqmock, screener_client: ScreenerClient):
    num_movers = 10
    reqmock.get(
        f"{BaseURL.DATA}/v1beta1/screener/stocks/most-actives?by=volume&top={num_movers}",
        text="""
        {
    "last_updated": "2023-06-23T14:19:00.182582147Z",
    "most_actives": [
        {
            "symbol": "MULN",
            "trade_count": 27058,
            "volume": 58614890
        },
        {
            "symbol": "PIK",
            "trade_count": 176643,
            "volume": 48724364
        },
        {
            "symbol": "SRGA",
            "trade_count": 81207,
            "volume": 44628275
        },
        {
            "symbol": "TSLA",
            "trade_count": 538798,
            "volume": 41377329
        },
        {
            "symbol": "ONCS",
            "trade_count": 89046,
            "volume": 37026359
        },
        {
            "symbol": "SQQQ",
            "trade_count": 74322,
            "volume": 34559063
        },
        {
            "symbol": "TQQQ",
            "trade_count": 147293,
            "volume": 33886902
        },
        {
            "symbol": "WORX",
            "trade_count": 44965,
            "volume": 29964316
        },
        {
            "symbol": "SPCE",
            "trade_count": 70019,
            "volume": 23501207
        },
        {
            "symbol": "SOFI",
            "trade_count": 64437,
            "volume": 22190348
        }
    ]
}
        """,
    )
    most_actives = screener_client.get_most_actives(MostActivesRequest(top=num_movers))
    assert isinstance(most_actives, MostActives)
    assert len(most_actives.most_actives) == num_movers
