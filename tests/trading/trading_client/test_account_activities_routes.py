from typing import List

from requests_mock import Mocker

from alpaca.common.enums import BaseURL
from alpaca.trading.client import TradingClient
from alpaca.trading.enums import ActivityType
from alpaca.trading.models import BaseActivity, NonTradeActivity, TradeActivity
from alpaca.trading.requests import GetAccountActivitiesRequest


def test_get_account_activities(reqmock: Mocker, trading_client: TradingClient):
    reqmock.get(
        f"{BaseURL.TRADING_PAPER.value}/v2/account/activities",
        text="""
        [
          {
            "id": "20220419000000000::fd84741b-59c5-4ddd-a303-69f70eb7753f",
            "account_id": "aba134b6-217d-4fd2-b460-e3c80bbfb9b4",
            "activity_type": "CSD",
            "date": "2022-04-19",
            "net_amount": "33324.35",
            "description": "",
            "status": "executed"
          },
          {
            "id": "20220304095318500::092cd749-b783-49cb-a36e-4d8666be201f",
            "account_id": "6e8cb861-e8b9-4278-8ed2-c8452535a165",
            "activity_type": "FILL",
            "transaction_time": "2022-03-04T14:53:18.500245Z",
            "type": "fill",
            "price": "2630.95",
            "qty": "9",
            "side": "buy",
            "symbol": "GOOGL",
            "leaves_qty": "0",
            "order_id": "b677e464-c2d0-4fdd-a4b1-8830b386aa50",
            "cum_qty": "10.177047834",
            "order_status": "filled"
          }
        ]
        """,
    )

    activities = trading_client.get_account_activities()

    assert reqmock.called_once
    assert isinstance(activities, List)
    assert len(activities) == 2
    assert isinstance(activities[0], NonTradeActivity)
    assert isinstance(activities[1], TradeActivity)


def test_get_account_activities_with_filter(
    reqmock: Mocker, trading_client: TradingClient
):
    reqmock.get(
        f"{BaseURL.TRADING_PAPER.value}/v2/account/activities",
        text="""
        [
          {
            "id": "20220304095318500::092cd749-b783-49cb-a36e-4d8666be201f",
            "account_id": "6e8cb861-e8b9-4278-8ed2-c8452535a165",
            "activity_type": "FILL",
            "transaction_time": "2022-03-04T14:53:18.500245Z",
            "type": "fill",
            "price": "2630.95",
            "qty": "9",
            "side": "buy",
            "symbol": "GOOGL",
            "leaves_qty": "0",
            "order_id": "b677e464-c2d0-4fdd-a4b1-8830b386aa50",
            "cum_qty": "10.177047834",
            "order_status": "filled"
          }
        ]
        """,
    )

    filter = GetAccountActivitiesRequest(activity_types=[ActivityType.FILL])
    activities = trading_client.get_account_activities(activity_filter=filter)

    assert reqmock.called_once
    assert isinstance(activities, List)
    assert len(activities) == 1
    assert isinstance(activities[0], TradeActivity)

    # Verify activity_types was passed as comma-separated string
    request = reqmock.request_history[0]
    assert "activity_types" in request.qs
    assert request.qs["activity_types"] == ["FILL"]


def test_get_account_activities_by_type(
    reqmock: Mocker, trading_client: TradingClient
):
    reqmock.get(
        f"{BaseURL.TRADING_PAPER.value}/v2/account/activities/DIV",
        text="""
        [
          {
            "id": "20220419000000000::fd84741b-59c5-4ddd-a303-69f70eb7753f",
            "account_id": "aba134b6-217d-4fd2-b460-e3c80bbfb9b4",
            "activity_type": "DIV",
            "date": "2022-04-19",
            "net_amount": "100.00",
            "description": "Dividend payment",
            "status": "executed",
            "symbol": "AAPL",
            "qty": "10",
            "per_share_amount": "10.00"
          }
        ]
        """,
    )

    activities = trading_client.get_account_activities_by_type(ActivityType.DIV)

    assert reqmock.called_once
    assert isinstance(activities, List)
    assert len(activities) == 1
    assert isinstance(activities[0], NonTradeActivity)
    assert activities[0].activity_type == ActivityType.DIV


def test_get_account_activities_with_category(
    reqmock: Mocker, trading_client: TradingClient
):
    reqmock.get(
        f"{BaseURL.TRADING_PAPER.value}/v2/account/activities",
        text="""
        [
          {
            "id": "20220304095318500::092cd749-b783-49cb-a36e-4d8666be201f",
            "account_id": "6e8cb861-e8b9-4278-8ed2-c8452535a165",
            "activity_type": "FILL",
            "transaction_time": "2022-03-04T14:53:18.500245Z",
            "type": "fill",
            "price": "2630.95",
            "qty": "9",
            "side": "buy",
            "symbol": "GOOGL",
            "leaves_qty": "0",
            "order_id": "b677e464-c2d0-4fdd-a4b1-8830b386aa50",
            "cum_qty": "10.177047834",
            "order_status": "filled"
          }
        ]
        """,
    )

    filter = GetAccountActivitiesRequest(category="trade_activity")
    activities = trading_client.get_account_activities(activity_filter=filter)

    assert reqmock.called_once
    assert isinstance(activities, List)
    assert len(activities) == 1
    assert isinstance(activities[0], TradeActivity)

    # Verify category was passed
    request = reqmock.request_history[0]
    assert "category" in request.qs
    assert request.qs["category"] == ["trade_activity"]


def test_get_account_activities_empty_response(
    reqmock: Mocker, trading_client: TradingClient
):
    reqmock.get(
        f"{BaseURL.TRADING_PAPER.value}/v2/account/activities",
        text="[]",
    )

    activities = trading_client.get_account_activities()

    assert reqmock.called_once
    assert isinstance(activities, List)
    assert len(activities) == 0


def test_get_account_activities_raw_data(reqmock: Mocker):
    trading_client = TradingClient(
        api_key="key-id", secret_key="secret-key", paper=True, raw_data=True
    )

    reqmock.get(
        f"{BaseURL.TRADING_PAPER.value}/v2/account/activities",
        text="""
        [
          {
            "id": "20220419000000000::fd84741b-59c5-4ddd-a303-69f70eb7753f",
            "account_id": "aba134b6-217d-4fd2-b460-e3c80bbfb9b4",
            "activity_type": "CSD",
            "date": "2022-04-19",
            "net_amount": "33324.35",
            "description": "",
            "status": "executed"
          }
        ]
        """,
    )

    activities = trading_client.get_account_activities()

    assert reqmock.called_once
    assert isinstance(activities, List)
    assert isinstance(activities[0], dict)
