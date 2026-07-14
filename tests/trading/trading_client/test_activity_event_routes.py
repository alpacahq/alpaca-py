import json

from alpaca.common.enums import BaseURL
from alpaca.trading import requests
from alpaca.trading.client import TradingClient
from alpaca.trading.models import ActivityEventV2, CDIVActivityV2


def test_get_activity_events(reqmock, trading_client: TradingClient):
    request_class = getattr(requests, "GetActivityEventsRequest", None)
    assert request_class is not None

    event = {
        "at": "2026-07-14T10:00:01Z",
        "event_id": "01J2Y7YQJFM6V3J5A8YF0P0M0B",
        "activity_type": "DIV",
        "activity_subtype": "CDIV",
        "executed_at": "2026-07-14T10:00:00Z",
        "status": "executed",
        "settle_date": "2026-07-16",
        "currency": "USD",
        "ref_id": "4ce24134-3d0c-4f61-aef5-1807a3391380",
        "details": {
            "system_date": "2026-07-14",
            "position_date": "2026-07-11",
            "symbol": "AAPL",
            "cusip": "037833100",
            "rate": "0.25",
            "foreign": False,
            "special": False,
            "entitled_qty": "10",
            "cash_payout": "2.50",
        },
    }
    reqmock.get(
        f"{BaseURL.TRADING_PAPER.value}/v2beta1/events/activities"
        "?since_id=01J2Y7YQJFM6V3J5A8YF0P0M0A",
        text=f"data: {json.dumps(event)}\n\n",
        headers={"Content-Type": "text/event-stream"},
    )

    events = list(
        trading_client.get_activity_events(
            request_class(since_id="01J2Y7YQJFM6V3J5A8YF0P0M0A")
        )
    )

    assert isinstance(events[0], ActivityEventV2)
    assert isinstance(events[0].details, CDIVActivityV2)
