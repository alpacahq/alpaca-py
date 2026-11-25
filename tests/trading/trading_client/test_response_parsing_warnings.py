"""Building responses must not warn about deprecated models.

Deprecated models warn when users instantiate them directly. Pydantic also runs a
model's own ``__init__`` when it validates the model inside a list or another model,
so these paths warned on every call until they were built from the response.
"""

import json
import warnings

import pytest

from alpaca.common.enums import BaseURL
from alpaca.trading.client import TradingClient
from alpaca.trading.models import Calendar, ClosePositionResponse, Order, TradeUpdate
from alpaca.trading.stream import TradingStream
from tests.common.factories.trading import create_dummy_order

_PAPER = BaseURL.TRADING_PAPER.value


@pytest.fixture
def order_json():
    with warnings.catch_warnings():
        # The factory instantiates Order directly, which warns by design.
        warnings.simplefilter("ignore", DeprecationWarning)
        return create_dummy_order().model_dump(mode="json")


def _silently(call):
    with warnings.catch_warnings():
        warnings.simplefilter("error", DeprecationWarning)
        return call()


def test_get_orders_does_not_warn(reqmock, trading_client: TradingClient, order_json):
    reqmock.get(f"{_PAPER}/v2/orders", text=json.dumps([order_json]))

    orders = _silently(trading_client.get_orders)

    assert [type(order) for order in orders] == [Order]


def test_close_all_positions_does_not_warn(
    reqmock, trading_client: TradingClient, order_json
):
    reqmock.delete(
        f"{_PAPER}/v2/positions",
        text=json.dumps([{"symbol": "AAPL", "status": 200, "body": order_json}]),
    )

    closed = _silently(trading_client.close_all_positions)

    assert [type(response) for response in closed] == [ClosePositionResponse]
    assert type(closed[0].body) is Order


def test_get_calendar_does_not_warn(reqmock, trading_client: TradingClient):
    reqmock.get(
        f"{_PAPER}/v2/calendar",
        text=json.dumps([{"date": "2022-05-16", "open": "09:30", "close": "16:00"}]),
    )

    days = _silently(trading_client.get_calendar)

    assert [type(day) for day in days] == [Calendar]


def test_trade_updates_stream_does_not_warn(order_json):
    stream = TradingStream("key-id", "secret-key")
    message = {
        "stream": "trade_updates",
        "data": {
            "event": "fill",
            "timestamp": "2022-05-16T16:32:24.14373588-04:00",
            "order": order_json,
        },
    }

    update = _silently(lambda: stream._cast(message))

    assert type(update) is TradeUpdate
    assert type(update.order) is Order
