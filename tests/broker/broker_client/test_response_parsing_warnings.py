"""Building Broker responses must not warn about deprecated models.

Deprecated models warn when users instantiate them directly. Pydantic also runs a
model's own ``__init__`` when it validates the model inside a list or another model,
so these paths warned on every call until they were built from the response.
"""

import importlib
import inspect
import json
import warnings

import pytest
from pydantic import BaseModel

from alpaca.broker.client import BrokerClient
from alpaca.broker.models import AccountExtended, Order, RebalancingRun
from alpaca.common.enums import BaseURL, PaginationType
from alpaca.trading.models import (
    Calendar,
    ClosePositionResponse,
    NonTradeActivity,
    TradeActivity,
)
from alpaca.trading.requests import GetAccountActivitiesRequest
from tests.common.factories.trading import create_dummy_order

_BASE = BaseURL.BROKER_SANDBOX.value
_ACCOUNT = "5fc0795e-1f16-40cc-aa90-ede67c39d7a9"


def _deprecated_model_names():
    names = set()
    for path in (
        "alpaca.trading.models",
        "alpaca.trading.requests",
        "alpaca.broker.models",
        "alpaca.broker.requests",
    ):
        for name, obj in vars(importlib.import_module(path)).items():
            if (
                inspect.isclass(obj)
                and issubclass(obj, BaseModel)
                and "__deprecated__" in obj.__dict__
            ):
                names.add(name)
    return names


DEPRECATED_MODELS = _deprecated_model_names()


def _without_model_warnings(call):
    # Only warnings about deprecated models fail the test: some methods, such as
    # get_all_runs, are deprecated themselves and warn by design.
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        result = call()
    model_warnings = [
        str(warning.message)
        for warning in caught
        if warning.category is DeprecationWarning
        and str(warning.message).split(" ", 1)[0] in DEPRECATED_MODELS
    ]
    assert model_warnings == []
    return result


@pytest.fixture
def order_json():
    with warnings.catch_warnings():
        # The factory instantiates Order directly, which warns by design.
        warnings.simplefilter("ignore", DeprecationWarning)
        return create_dummy_order().model_dump(mode="json")


def test_list_accounts_does_not_warn(reqmock, client: BrokerClient):
    account = {
        "id": _ACCOUNT,
        "account_number": "123456789",
        "status": "ACTIVE",
        "currency": "USD",
        "last_equity": "0",
        "created_at": "2022-01-01T00:00:00Z",
    }
    reqmock.get(f"{_BASE}/v1/accounts", text=json.dumps([account]))

    accounts = _without_model_warnings(client.list_accounts)

    assert [type(a) for a in accounts] == [AccountExtended]


def test_order_lists_do_not_warn(reqmock, client: BrokerClient, order_json):
    reqmock.get(
        f"{_BASE}/v1/trading/accounts/{_ACCOUNT}/orders", text=json.dumps([order_json])
    )
    reqmock.delete(
        f"{_BASE}/v1/trading/accounts/{_ACCOUNT}/positions",
        text=json.dumps([{"symbol": "AAPL", "status": 200, "body": order_json}]),
    )

    orders = _without_model_warnings(lambda: client.get_orders_for_account(_ACCOUNT))
    closed = _without_model_warnings(
        lambda: client.close_all_positions_for_account(_ACCOUNT)
    )

    assert [type(order) for order in orders] == [Order]
    assert [type(response) for response in closed] == [ClosePositionResponse]


def test_get_calendar_does_not_warn(reqmock, client: BrokerClient):
    reqmock.get(
        f"{_BASE}/v1/calendar",
        text=json.dumps([{"date": "2022-05-16", "open": "09:30", "close": "16:00"}]),
    )

    days = _without_model_warnings(client.get_calendar)

    assert [type(day) for day in days] == [Calendar]


def test_get_account_activities_does_not_warn(reqmock, client: BrokerClient):
    trade = {
        "id": "20220419125515512::f2fc4e39",
        "account_id": _ACCOUNT,
        "activity_type": "FILL",
        "transaction_time": "2022-04-19T16:55:15.512Z",
        "type": "fill",
        "price": "10",
        "qty": "1",
        "side": "buy",
        "symbol": "AAPL",
        "leaves_qty": "0",
        "order_id": "f2fc4e39-a1cf-4b8b-8f3f-4fd4b0c4b5a6",
        "cum_qty": "1",
        "order_status": "filled",
    }
    dividend = {
        "id": "20220419000000000::4a4e3f8f",
        "account_id": _ACCOUNT,
        "activity_type": "DIV",
        "date": "2022-04-19",
        "net_amount": "1.5",
        "description": "dividend",
    }
    reqmock.get(f"{_BASE}/v1/accounts/activities", text=json.dumps([trade, dividend]))

    activities = _without_model_warnings(
        lambda: client.get_account_activities(
            GetAccountActivitiesRequest(), handle_pagination=PaginationType.NONE
        )
    )

    assert [type(a) for a in activities] == [TradeActivity, NonTradeActivity]


def test_rebalancing_runs_do_not_warn(reqmock, client: BrokerClient, order_json):
    run = {
        "id": "2ad28f83-796c-4c5e-895e-b63b38d6be3f",
        "account_id": _ACCOUNT,
        "type": "full_rebalance",
        "portfolio_id": "57d4ec79-9658-4916-9eb1-7c672be97e3e",
        "weights": [{"type": "asset", "symbol": "AAPL", "percent": 100}],
        "created_at": "2022-05-16T16:32:24Z",
        "updated_at": "2022-05-16T16:32:24Z",
        "status": "COMPLETED_SUCCESS",
        "orders": [order_json],
    }
    reqmock.get(
        f"{_BASE}/v1/rebalancing/runs",
        text=json.dumps({"runs": [run], "next_page_token": None}),
    )

    # PaginationType.NONE returns a single RebalancingRunPage; the default iterates.
    page = _without_model_warnings(
        lambda: client.get_runs(handle_pagination=PaginationType.NONE)
    )
    runs = _without_model_warnings(
        lambda: client.get_all_runs(handle_pagination=PaginationType.NONE)
    )

    assert [type(r) for r in page.runs] == [RebalancingRun]
    assert [type(r) for r in runs] == [RebalancingRun]
    assert type(runs[0].orders[0]) is Order
