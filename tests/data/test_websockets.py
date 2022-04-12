import pytest

from alpaca.common.websocket import BaseStream
from alpaca.data.enums import Exchange
from alpaca.data.models import Bar, Trade


@pytest.fixture
def client():
    client = BaseStream("endpoint", "key-id", "secret-key")
    return client


@pytest.fixture
def raw_client():
    raw_client = BaseStream("endpoint", "key-id", "secret-key", raw_data=True)
    return raw_client


@pytest.fixture
def timestamp():
    class MockTimestamp:
        def __init__(self, _seconds, _nanoseconds):
            self.seconds = _seconds
            self.nanoseconds = _nanoseconds

    return MockTimestamp(0, 0)


def test_cast(client, raw_client, timestamp):

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

    bar_cast_msg = client._cast(bar_msg_type, bar_msg_dict)

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

    trade_cast_msg = client._cast(trade_msg_type, trade__msg_dict)

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

    raw_bar_cast_msg = raw_client._cast(raw_bar_msg_type, raw_bar_msg_dict)

    assert type(raw_bar_cast_msg) == dict

    assert raw_bar_cast_msg["S"] == "AAPL"
    assert raw_bar_cast_msg["h"] == 178.005

    # Trade
    raw_trade_msg_type = "t"
    raw_trade__msg_dict = {
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

    raw_trade_cast_msg = raw_client._cast(raw_trade_msg_type, raw_trade__msg_dict)

    assert type(raw_trade_cast_msg) == dict

    assert raw_trade_cast_msg["S"] == "AAPL"
    assert raw_trade_cast_msg["p"] == 177.79
    assert raw_trade_cast_msg["x"] == "V"
