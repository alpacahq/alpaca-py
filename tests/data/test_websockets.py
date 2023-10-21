import pytest
from msgpack.ext import Timestamp

from alpaca.common.websocket import BaseStream
from alpaca.data.enums import Exchange
from alpaca.data.models import Bar, Trade


@pytest.fixture
def ws_client() -> BaseStream:
    """Socket client fixture with pydantic models as output."""
    return BaseStream("endpoint", "key-id", "secret-key")


@pytest.fixture
def raw_ws_client() -> BaseStream:
    """Socket client fixture with raw data output."""
    return BaseStream("endpoint", "key-id", "secret-key", raw_data=True)


@pytest.fixture
def timestamp() -> Timestamp:
    """Msgpack mock timestamp."""
    return Timestamp(seconds=10, nanoseconds=10)


def test_cast(ws_client: BaseStream, raw_ws_client: BaseStream, timestamp: Timestamp):
    """Test the value error in case there's a different timestamp type."""
    # Bar
    bar_msg_type = "b"
    bar_msg_dict = {
        "S": "AAPL",
        "o": 177.94,
        "c": 178.005,
        "h": 178.005,
        "l": 177.94,
        "v": 8547,
        "t": timestamp,
        "n": 66,
        "vw": 177.987562,
    }

    bar_cast_msg = ws_client._cast(bar_msg_type, bar_msg_dict)

    assert type(bar_cast_msg) == Bar

    assert bar_cast_msg.symbol == "AAPL"
    assert bar_cast_msg.high == 178.005

    # Trade
    trade_msg_type = "t"
    trade__msg_dict = {
        "T": "t",
        "S": "AAPL",
        "i": 6142,
        "x": "V",
        "p": 177.79,
        "s": 90,
        "c": ["@", "I"],
        "z": "C",
        "t": timestamp,
    }

    trade_cast_msg = ws_client._cast(trade_msg_type, trade__msg_dict)

    assert type(trade_cast_msg) == Trade

    assert trade_cast_msg.symbol == "AAPL"
    assert trade_cast_msg.price == 177.79
    assert trade_cast_msg.exchange == Exchange.V

    # News
    news_msg_type = "n"
    news_msg_dict = {
        "T": "n",
        "id": 24919710,
        "headline": "Granite Wins $90M Construction Manager/General Contractor Project In Northern California",
        "summary": "Granite (NYSE:GVA) announced today that it has been selected by the California Department of Transportation (Caltrans) as the Construction Manager/General Contractor (CM/GC) for the approximately $90 million State Route",
        "author": "Benzinga Newsdesk",
        "created_at": "2022-01-05T22:30:29Z",
        "updated_at": "2022-01-05T22:30:30Z",
        "url": "https://www.benzinga.com/news/22/01/24919710/granite-wins-90m-construction-managergeneral-contractor-project-in-northern-california",
        "content": "content",
        "symbols": ["GVA"],
        "source": "benzinga",
    }

    news_cast_msg = ws_client._cast(news_msg_type, news_msg_dict)
    print(news_cast_msg)
    assert type(news_cast_msg) == dict

    assert "GVA" in raw_news_cast_msg.symbols
    assert news_cast_msg.source == "benzinga"
    assert (
        news_cast_msg.headline
        == "Granite Wins $90M Construction Manager/General Contractor Project In Northern California"
    )

    # Raw Client

    # Bar
    raw_bar_msg_type = "b"
    raw_bar_msg_dict = {
        "S": "AAPL",
        "o": 177.94,
        "c": 178.005,
        "h": 178.005,
        "l": 177.94,
        "v": 8547,
        "t": timestamp,
        "n": 66,
        "vw": 177.987562,
    }

    raw_bar_cast_msg = raw_ws_client._cast(raw_bar_msg_type, raw_bar_msg_dict)

    assert type(raw_bar_cast_msg) == dict

    assert raw_bar_cast_msg["S"] == "AAPL"
    assert raw_bar_cast_msg["h"] == 178.005

    # Trade
    raw_trade_msg_type = "t"
    raw_trade_msg_dict = {
        "T": "t",
        "S": "AAPL",
        "i": 6142,
        "x": "V",
        "p": 177.79,
        "s": 90,
        "c": ["@", "I"],
        "z": "C",
        "t": timestamp,
    }

    raw_trade_cast_msg = raw_ws_client._cast(raw_trade_msg_type, raw_trade_msg_dict)

    assert type(raw_trade_cast_msg) == dict

    assert raw_trade_cast_msg["S"] == "AAPL"
    assert raw_trade_cast_msg["p"] == 177.79
    assert raw_trade_cast_msg["x"] == "V"

    # News
    raw_news_msg_type = "n"
    raw_news_msg_dict = {
        "T": "n",
        "id": 24919710,
        "headline": "Granite Wins $90M Construction Manager/General Contractor Project In Northern California",
        "summary": "Granite (NYSE:GVA) announced today that it has been selected by the California Department of Transportation (Caltrans) as the Construction Manager/General Contractor (CM/GC) for the approximately $90 million State Route",
        "author": "Benzinga Newsdesk",
        "created_at": "2022-01-05T22:30:29Z",
        "updated_at": "2022-01-05T22:30:30Z",
        "url": "https://www.benzinga.com/news/22/01/24919710/granite-wins-90m-construction-managergeneral-contractor-project-in-northern-california",
        "content": "content",
        "symbols": ["GVA"],
        "source": "benzinga",
    }

    raw_news_cast_msg = raw_ws_client._cast(raw_news_msg_type, raw_news_msg_dict)
    print(raw_news_cast_msg)
    assert type(raw_news_cast_msg) == dict

    assert "GVA" in raw_news_cast_msg["symbols"]
    assert raw_news_cast_msg["source"] == "benzinga"
    assert (
        raw_news_cast_msg["headline"]
        == "Granite Wins $90M Construction Manager/General Contractor Project In Northern California"
    )
