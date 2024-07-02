from datetime import datetime

import pytest
from msgpack.ext import Timestamp
from pytz import utc

from alpaca.data.enums import Exchange
from alpaca.data.models import Bar, Trade, News
from alpaca.data.live.websocket import DataStream
from alpaca.data.models import Bar, Trade
from alpaca.data.models.news import News
from alpaca.data.models.orderbooks import Orderbook, OrderbookQuote
from alpaca.data.models.quotes import Quote
from alpaca.data.models.trades import TradeCancel, TradingStatus


@pytest.fixture
def ws_client() -> DataStream:
    """Socket client fixture with pydantic models as output."""
    return DataStream("endpoint", "key-id", "secret-key")


@pytest.fixture
def raw_ws_client() -> DataStream:
    """Socket client fixture with raw data output."""
    return DataStream("endpoint", "key-id", "secret-key", raw_data=True)


@pytest.fixture
def timestamp() -> Timestamp:
    """Msgpack mock timestamp."""
    return Timestamp(seconds=10, nanoseconds=10)


def test_cast(ws_client: DataStream, raw_ws_client: DataStream, timestamp: Timestamp):
    bar = ws_client._cast(
        {
            "T": "b",
            "S": "AAPL",
            "o": 177.94,
            "c": 178.005,
            "h": 178.005,
            "l": 177.94,
            "v": 8547,
            "t": timestamp,
            "n": 66,
            "vw": 177.987562,
        },
    )
    assert type(bar) == Bar
    assert bar.symbol == "AAPL"
    assert bar.high == 178.005

    trade = ws_client._cast(
        {
            "T": "t",
            "S": "AAPL",
            "i": 6142,
            "x": "V",
            "p": 177.79,
            "s": 90,
            "c": ["@", "I"],
            "z": "C",
            "t": timestamp,
        },
    )
    assert type(trade) == Trade
    assert trade.symbol == "AAPL"
    assert trade.price == 177.79
    assert trade.exchange == Exchange.V

    quote = ws_client._cast(
        {
            "T": "q",
            "S": "SPIP",
            "bx": "V",
            "bp": 25.41,
            "bs": 35,
            "ax": "V",
            "ap": 25.43,
            "as": 35,
            "c": ["R"],
            "z": "B",
            "t": timestamp,
        },
    )
    assert type(quote) == Quote
    assert quote.symbol == "SPIP"
    assert quote.bid_price == 25.41
    assert quote.ask_size == 35
    assert quote.conditions == ["R"]

    orderbook = ws_client._cast(
        {
            "T": "o",
            "S": "BTC/USD",
            "t": timestamp,
            "b": [{"p": 65128.1, "s": 1.6542}],
            "a": [{"p": 65128.1, "s": 1.6542}],
        },
    )
    assert type(orderbook) == Orderbook
    assert orderbook.symbol == "BTC/USD"
    assert orderbook.bids == [OrderbookQuote(p=65128.1, s=1.6542)]

    trading_status = ws_client._cast(
        {
            "T": "s",
            "S": "STRR",
            "t": timestamp,
            "sc": "T",
            "sm": "Trading Resumption",
            "rc": "C11",
            "rm": "",
            "z": "C",
        },
    )
    assert type(trading_status) == TradingStatus
    assert trading_status.status_code == "T"

    cancel = ws_client._cast(
        {
            "T": "x",
            "S": "DJT",
            "i": 4868,
            "x": "D",
            "p": 36.18,
            "s": 31800,
            "a": "C",
            "z": "C",
            "t": timestamp,
        },
    )
    assert type(cancel) == TradeCancel
    assert cancel.id == 4868
    assert cancel.exchange == "D"
    assert cancel.price == 36.18

    created_at = datetime(2024, 6, 17, 14, 11, 0, tzinfo=utc)
    news = ws_client._cast(
        {
            "T": "n",
            "id": 39358670,
            "headline": "Broadcom shares are trading higher. The company last week reported better-than-expected Q2 financial results, issued strong revenue guidance and announced a 10-for-1 forward split.",
            "summary": "",
            "author": "Benzinga Newsdesk",
            "created_at": Timestamp.from_datetime(created_at),
            "updated_at": Timestamp.from_datetime(created_at),
            "url": "https://www.benzinga.com/wiim/24/06/39358670/broadcom-shares-are-trading-higher-the-company-last-week-reported-better-than-expected-q2-financial",
            "content": "",
            "symbols": ["AVGO"],
            "source": "benzinga",
        },
    )
    assert type(news) == News
    assert news.id == 39358670
    assert news.symbols == ["AVGO"]
    assert news.created_at == created_at

    # Raw Client
    raw_bar = raw_ws_client._cast(
        {
            "T": "b",
            "S": "AAPL",
            "o": 177.94,
            "c": 178.005,
            "h": 178.005,
            "l": 177.94,
            "v": 8547,
            "t": timestamp,
            "n": 66,
            "vw": 177.987562,
        },
    )
    assert type(raw_bar) == dict
    assert raw_bar["S"] == "AAPL"
    assert raw_bar["h"] == 178.005


@pytest.mark.asyncio
async def test_dispatch(ws_client: DataStream, timestamp: Timestamp):
    articles_a, articles_b, articles_star = [], [], []

    async def handler_a(d):
        articles_a.append(d)

    async def handler_b(d):
        articles_b.append(d)

    async def handler_star(d):
        articles_star.append(d)

    ws_client._subscribe(handler_a, ("A",), ws_client._handlers["news"])
    ws_client._subscribe(handler_b, ("B",), ws_client._handlers["news"])
    ws_client._subscribe(handler_star, ("*",), ws_client._handlers["news"])

    msg_a = {
        "T": "n",
        "author": "benzinga",
        "headline": "a",
        "id": 1,
        "summary": "a",
        "content": "",
        "url": "url",
        "source": "benzinga",
        "symbols": ["A"],
        "created_at": timestamp,
        "updated_at": timestamp,
    }
    await ws_client._dispatch(msg_a.copy())
    assert len(articles_a) == 1
    assert len(articles_b) == 0
    assert len(articles_star) == 0
    assert type(articles_a[0]) == News
    assert articles_a[0].summary == "a"

    msg_b = msg_a.copy()
    msg_b["headline"] = "b"
    msg_b["symbols"] = ["B", "C"]
    await ws_client._dispatch(msg_b.copy())
    assert len(articles_a) == 1
    assert len(articles_b) == 1
    assert len(articles_star) == 1
    assert articles_b[0].headline == "b"
    assert articles_star[0].headline == "b"

    msg_c = msg_a.copy()
    msg_c["headline"] = "c"
    msg_c["symbols"] = ["C"]
    await ws_client._dispatch(msg_c.copy())
    assert len(articles_a) == 1
    assert len(articles_b) == 1
    assert len(articles_star) == 2
    assert articles_star[1].headline == "c"
