from datetime import datetime
import pytest
from msgpack.ext import Timestamp

from alpaca.common.websocket import BaseStream
from alpaca.data.enums import Exchange
from alpaca.data.models import Bar, Trade, News


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
        "id": 24918784,
        "headline": "Corsair Reports Purchase Of Majority Ownership In iDisplay, No Terms Disclosed",
        "summary": "Corsair Gaming, Inc. (NASDAQ:CRSR) (“Corsair”), a leading global provider and innovator of high-performance gear for gamers and content creators, today announced that it acquired a 51% stake in iDisplay",
        "author": "Benzinga Newsdesk",
        "created_at": timestamp,
        "updated_at": timestamp,
        "url": "https://www.benzinga.com/m-a/22/01/24918784/corsair-reports-purchase-of-majority-ownership-in-idisplay-no-terms-disclosed",
        "content": '\u003cp\u003eCorsair Gaming, Inc. (NASDAQ:\u003ca class="ticker" href="https://www.benzinga.com/stock/CRSR#NASDAQ"\u003eCRSR\u003c/a\u003e) (\u0026ldquo;Corsair\u0026rdquo;), a leading global ...',
        "symbols": ["CRSR"],
        "source": "benzinga",
    }

    raw_news_cast_msg = raw_ws_client._cast(raw_news_msg_type, raw_news_msg_dict)

    assert type(raw_news_cast_msg) == dict

    assert "CRSR" in raw_news_cast_msg["symbols"]
    assert raw_news_cast_msg["source"] == "benzinga"
    assert (
        raw_news_cast_msg["headline"]
        == "Corsair Reports Purchase Of Majority Ownership In iDisplay, No Terms Disclosed"
    )
