from datetime import datetime
from urllib.parse import parse_qs, urlparse

import pytest

from alpaca.common.enums import BaseURL
from alpaca.trading.client import TradingClient
from alpaca.trading.models import NonTradeActivities, TradingActivities
from alpaca.trading.requests import (
    ActivityEventsRequest,
    GetAccountActivitiesByTypeRequest,
    GetAccountActivitiesRequest,
)

_PAPER = BaseURL.TRADING_PAPER.value


def test_account_activities(reqmock, trading_client: TradingClient):
    activity = {"activity_type": "FILL", "symbol": "AAPL", "qty": "1", "side": "buy"}
    reqmock.get(f"{_PAPER}/v2/account/activities", json=[activity])
    reqmock.get(f"{_PAPER}/v2/account/activities/FILL", json=[activity])

    activities = trading_client.get_account_activities(
        GetAccountActivitiesRequest(
            activity_types=["FILL", "DIV"],
            direction="desc",
            page_size=100,
        )
    )
    by_type = trading_client.get_account_activities_by_type(
        "FILL",
        GetAccountActivitiesByTypeRequest(direction="desc", page_size=100),
    )

    sent = reqmock.request_history[0]
    query = parse_qs(urlparse(sent.url).query)
    assert sent.method == "GET"
    assert urlparse(sent.url).path == "/v2/account/activities"
    assert query["activity_types"] == ["FILL,DIV"]
    assert "category" not in query
    assert query["direction"] == ["desc"]
    assert query["page_size"] == ["100"]
    assert activities[0].symbol == "AAPL"
    assert (
        urlparse(reqmock.request_history[1].url).path == "/v2/account/activities/FILL"
    )
    assert by_type[0].qty == "1"


def test_subscribe_to_activities_sse_uses_v2beta1(
    reqmock, trading_client: TradingClient
):
    payload = '{"activity_type":"FILL"}'
    reqmock.get(
        f"{_PAPER}/v2beta1/events/activities",
        text=f"data: {payload}\n\n",
        headers={"Content-Type": "text/event-stream"},
    )

    events = list(
        trading_client.subscribe_to_activities_sse(
            ActivityEventsRequest(
                since="2026-01-01T00:00:00Z",
                until="2026-01-01T00:00:00Z",
                since_id="01ARZ3NDEKTSV4RRFFQ69G5FAV",
            )
        )
    )

    sent = reqmock.request_history[0]
    assert events == [payload]
    assert sent.method == "GET"
    assert urlparse(sent.url).path == "/v2beta1/events/activities"
    assert "/v2/events/activities" not in sent.url
    assert sent.headers["Accept"] == "text/event-stream"
    query = parse_qs(urlparse(sent.url).query)
    assert "since" in query
    assert "until" in query
    assert query["since_id"] == ["01ARZ3NDEKTSV4RRFFQ69G5FAV"]


# Documented Trading API examples. Fills have no account_id, and this dividend
# has no description. A fill with only activity_type and qty must still parse
# as a trade activity.
ACTIVITIES_RESPONSE = [
    {
        "activity_type": "FILL",
        "cum_qty": "2",
        "id": "20220202135509981::2d7be4ff-d1f3-43e9-856a-0f5cf5c5088e",
        "leaves_qty": "0",
        "order_id": "b5abe576-6a8a-49f3-a353-46b72c1ccae9",
        "order_status": "filled",
        "price": "174.78",
        "qty": "2",
        "side": "buy",
        "symbol": "AAPL",
        "transaction_time": "2022-02-02T18:55:09.981482Z",
        "type": "fill",
    },
    {
        "activity_sub_type": "SDIV",
        "activity_type": "DIV",
        "created_at": "2021-05-10T14:01:04.650275Z",
        "currency": "USD",
        "date": "2019-08-01",
        "id": "20190801011955195::5f596936-6f23-4cef-bdf1-3806aae57dbf",
        "net_amount": "1.02",
        "per_share_amount": "0.51",
        "qty": "2",
        "status": "executed",
        "symbol": "T",
    },
    {"activity_type": "FILL", "qty": "1"},
]


def test_get_account_activities_classifies_each_activity(
    reqmock, trading_client: TradingClient
):
    reqmock.get(f"{_PAPER}/v2/account/activities", json=ACTIVITIES_RESPONSE)
    reqmock.get(f"{_PAPER}/v2/account/activities/DIV", json=[ACTIVITIES_RESPONSE[1]])

    activities = trading_client.get_account_activities()
    by_type = trading_client.get_account_activities_by_type("DIV")

    fill, dividend, sparse_fill = activities
    assert isinstance(fill, TradingActivities)
    assert fill.price == "174.78"
    assert fill.side == "buy"
    assert isinstance(dividend, NonTradeActivities)
    assert dividend.activity_type == "DIV"
    assert dividend.net_amount == "1.02"
    assert dividend.var_date == datetime(2019, 8, 1)
    assert isinstance(sparse_fill, TradingActivities)
    assert sparse_fill.qty == "1"
    assert isinstance(by_type[0], NonTradeActivities)
    assert by_type[0].symbol == "T"


def test_get_account_activities_raw_data(reqmock):
    raw_client = TradingClient("key-id", "secret-key", raw_data=True)
    reqmock.get(f"{_PAPER}/v2/account/activities", json=ACTIVITIES_RESPONSE)

    activities = raw_client.get_account_activities()

    assert activities == ACTIVITIES_RESPONSE
    assert activities[0]["activity_type"] == "FILL"


def test_get_account_activities_sends_category(reqmock, trading_client: TradingClient):
    reqmock.get(f"{_PAPER}/v2/account/activities", json=[])

    trading_client.get_account_activities(
        GetAccountActivitiesRequest(category="trade_activity")
    )

    query = parse_qs(urlparse(reqmock.last_request.url).query)
    assert query["category"] == ["trade_activity"]


def test_account_activity_requests_reject_conflicting_filters():
    with pytest.raises(ValueError, match="category and activity_types"):
        GetAccountActivitiesRequest(
            category="trade_activity",
            activity_types=["FILL"],
        )

    with pytest.raises(ValueError, match="date and after"):
        GetAccountActivitiesRequest(date="2022-02-02", after="2022-02-01")

    with pytest.raises(ValueError, match="date and until"):
        GetAccountActivitiesByTypeRequest(date="2022-02-02", until="2022-02-03")


def test_get_account_activities_requires_activity_type(
    reqmock, trading_client: TradingClient
):
    reqmock.get(
        f"{_PAPER}/v2/account/activities",
        json=[{"symbol": "AAPL", "qty": "1"}],
    )

    with pytest.raises(ValueError, match="activity_type"):
        trading_client.get_account_activities()
