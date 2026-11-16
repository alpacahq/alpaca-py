"""Building Market Data responses must not warn about deprecated models.

Deprecated models warn when users instantiate them directly. The data sets and the
news stream built them directly from API data, so every response warned until they
were built from the response.
"""

import json
import warnings

from msgpack.ext import Timestamp

from alpaca.data.historical.option import OptionHistoricalDataClient
from alpaca.data.historical.screener import ScreenerClient
from alpaca.data.live.websocket import DataStream
from alpaca.data.models import (
    CorporateActionsSet,
    ForwardSplit,
    MostActives,
    News,
    NewsSet,
    OptionsSnapshot,
)
from alpaca.data.requests import MostActivesRequest, OptionSnapshotRequest

_ARTICLE = {
    "id": 24843171,
    "headline": "Apple shares are trading higher",
    "source": "benzinga",
    "url": "https://www.benzinga.com/news/24843171",
    "summary": "",
    "created_at": "2022-01-05T22:00:37Z",
    "updated_at": "2022-01-05T22:00:38Z",
    "symbols": ["AAPL"],
    "author": "Benzinga Newsdesk",
    "content": "",
}


def _silently(call):
    with warnings.catch_warnings():
        warnings.simplefilter("error", DeprecationWarning)
        return call()


def test_news_set_does_not_warn():
    news = _silently(lambda: NewsSet({"news": [_ARTICLE], "next_page_token": None}))

    assert [type(article) for article in news.data["news"]] == [News]


def test_corporate_actions_set_does_not_warn():
    split = {
        "id": "a7932b15-f816-4f83-921e-998b524487b0",
        "symbol": "AAPL",
        "cusip": "037833100",
        "new_rate": 4,
        "old_rate": 1,
        "process_date": "2020-08-31",
        "ex_date": "2020-08-31",
    }

    actions = _silently(lambda: CorporateActionsSet({"forward_splits": [split]}))

    assert [type(a) for a in actions.data["forward_splits"]] == [ForwardSplit]


def test_news_stream_does_not_warn():
    stream = DataStream("endpoint", "key-id", "secret-key")
    message = {
        **_ARTICLE,
        "T": "n",
        "created_at": Timestamp.from_unix(1641420037),
        "updated_at": Timestamp.from_unix(1641420038),
    }

    article = _silently(lambda: stream._cast(message))

    assert type(article) is News


def test_option_snapshots_do_not_warn(
    reqmock, option_client: OptionHistoricalDataClient
):
    reqmock.get(
        "https://data.alpaca.markets/v1beta1/options/snapshots",
        text=json.dumps({"snapshots": {"AAPL250620C00100000": {}}}),
    )

    snapshots = _silently(
        lambda: option_client.get_option_snapshot(
            OptionSnapshotRequest(symbol_or_symbols="AAPL250620C00100000")
        )
    )

    assert type(snapshots["AAPL250620C00100000"]) is OptionsSnapshot


def test_screener_does_not_warn(reqmock, screener_client: ScreenerClient):
    reqmock.get(
        "https://data.alpaca.markets/v1beta1/screener/stocks/most-actives",
        text=json.dumps(
            {
                "most_actives": [{"symbol": "AAPL", "volume": 100, "trade_count": 10}],
                "last_updated": "2022-05-16T16:32:24Z",
            }
        ),
    )

    actives = _silently(
        lambda: screener_client.get_most_actives(MostActivesRequest(top=1))
    )

    assert type(actives) is MostActives
