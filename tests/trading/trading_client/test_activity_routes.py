from alpaca.common.enums import BaseURL, Sort
from alpaca.trading.client import TradingClient
from alpaca.trading.enums import ActivityType
from alpaca.trading.models import NonTradeActivities, TradingActivities
from alpaca.trading.requests import GetActivitiesRequest


def test_get_activities(reqmock, trading_client: TradingClient):
    reqmock.get(
        f"{BaseURL.TRADING_PAPER.value}/v2/account/activities"
        "?activity_types=FILL%2CDIV&direction=desc",
        json=[
            {
                "activity_type": "FILL",
                "id": "trade-id",
                "order_id": "4ce24134-3d0c-4f61-aef5-1807a3391380",
                "type": "partial_fill",
                "transaction_time": "2026-07-14T10:00:00Z",
            },
            {
                "activity_type": "DIV",
                "activity_sub_type": "CDIV",
                "id": "non-trade-id",
                "date": "2026-07-14T10:00:00Z",
                "net_amount": "12.34",
            },
        ],
    )

    activities = trading_client.get_activities(
        GetActivitiesRequest(
            activity_types=[ActivityType.FILL, ActivityType.DIV],
            direction=Sort.DESC,
        )
    )

    assert isinstance(activities[0], TradingActivities)
    assert isinstance(activities[1], NonTradeActivities)
