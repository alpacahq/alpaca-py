from datetime import date

import pytest
from requests_mock import Mocker

from alpaca.common.enums import BaseURL, Sort
from alpaca.trading.client import TradingClient
from alpaca.trading.enums import ActivityCategory, ActivityType, OrderSide
from alpaca.trading.models import NonTradeActivity, TradeActivity
from alpaca.trading.requests import GetAccountActivitiesRequest

# Samples from the Trading API reference. Unlike the Broker API, the Trading API
# doesn't send account_id, and non-trade activities may come without a description.
ACTIVITIES_RESPONSE = """
[
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
    "type": "fill"
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
    "symbol": "T"
  }
]
"""


def test_get_account_activities(reqmock: Mocker, trading_client: TradingClient):
    reqmock.get(
        f"{BaseURL.TRADING_PAPER.value}/v2/account/activities",
        text=ACTIVITIES_RESPONSE,
    )

    activities = trading_client.get_account_activities()

    assert reqmock.called_once
    assert len(activities) == 2

    fill = activities[0]
    assert isinstance(fill, TradeActivity)
    assert fill.activity_type == ActivityType.FILL
    assert fill.side == OrderSide.BUY
    assert fill.price == 174.78
    assert fill.account_id is None

    dividend = activities[1]
    assert isinstance(dividend, NonTradeActivity)
    assert dividend.activity_type == ActivityType.DIV
    assert dividend.date == date(2019, 8, 1)
    assert dividend.net_amount == 1.02
    assert dividend.description is None


def test_get_account_activities_with_filter(
    reqmock: Mocker, trading_client: TradingClient
):
    reqmock.get(
        f"{BaseURL.TRADING_PAPER.value}/v2/account/activities",
        text="[]",
    )

    activities = trading_client.get_account_activities(
        GetAccountActivitiesRequest(
            activity_types=[ActivityType.FILL, ActivityType.DIV],
            direction=Sort.ASC,
            page_size=50,
            page_token="20220202135509981::2d7be4ff-d1f3-43e9-856a-0f5cf5c5088e",
        )
    )

    assert reqmock.called_once
    assert activities == []
    assert reqmock.last_request.qs == {
        "activity_types": ["fill,div"],
        "direction": ["asc"],
        "page_size": ["50"],
        "page_token": ["20220202135509981::2d7be4ff-d1f3-43e9-856a-0f5cf5c5088e"],
    }


def test_get_account_activities_raw_data(reqmock: Mocker):
    raw_client = TradingClient("key-id", "secret-key", raw_data=True)
    reqmock.get(
        f"{BaseURL.TRADING_PAPER.value}/v2/account/activities",
        text=ACTIVITIES_RESPONSE,
    )

    activities = raw_client.get_account_activities()

    assert reqmock.called_once
    assert isinstance(activities, list)
    assert activities[0]["activity_type"] == "FILL"


def test_get_account_activities_request_rejects_conflicting_filters():
    with pytest.raises(ValueError):
        GetAccountActivitiesRequest(
            category=ActivityCategory.TRADE_ACTIVITY,
            activity_types=[ActivityType.FILL],
        )

    with pytest.raises(ValueError):
        GetAccountActivitiesRequest(date="2022-02-02", after="2022-02-01")
