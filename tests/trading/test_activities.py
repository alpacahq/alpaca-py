from datetime import date, datetime
from uuid import UUID

import pytest
from pydantic import ValidationError

from alpaca.common.enums import Sort
from alpaca.trading.enums import (
    ActivityCategory,
    ActivitySubType,
    ActivityType,
    ExecutionType,
    TradeActivityType,
)
from alpaca.trading.models import (
    NonTradeActivities,
    NonTradeActivity,
    TradingActivities,
)
from alpaca.trading.requests import GetActivitiesRequest


def test_activity_type_matches_trading_api_schema():
    assert [activity_type.value for activity_type in ActivityType] == [
        "FILL",
        "TRANS",
        "MISC",
        "ACATC",
        "ACATS",
        "CFEE",
        "CGD",
        "CSD",
        "CSW",
        "DIV",
        "DIVCGL",
        "DIVCGS",
        "DIVFEE",
        "DIVFT",
        "DIVNRA",
        "DIVROC",
        "DIVTW",
        "DIVTXEX",
        "FEE",
        "INT",
        "INTNRA",
        "INTTW",
        "JNL",
        "JNLC",
        "JNLS",
        "MA",
        "NC",
        "OPASN",
        "OPCA",
        "OPCSH",
        "OPEXC",
        "OPEXP",
        "OPTRD",
        "PTC",
        "PTR",
        "REORG",
        "SPIN",
        "SPLIT",
        "FOPT",
    ]


def test_activity_subtype_and_execution_type_match_schema():
    assert [activity_sub_type.value for activity_sub_type in ActivitySubType] == [
        "CDIV",
        "SDIV",
        "SPD",
        "REG",
        "TAF",
        "LCT",
        "ORF",
        "OCC",
        "NRC",
        "NRV",
        "COM",
        "CAT",
        "MGN",
        "CDT",
        "SWP",
        "QII",
        "CMA",
        "SMA",
        "SCMA",
        "SNC",
        "CNC",
        "SCNC",
        "DIV.CDIV",
        "DIV.SDIV",
        "MA.CMA",
        "MA.SMA",
        "MA.SCMA",
        "NC.CNC",
        "NC.SNC",
        "NC.SCNC",
        "SPIN",
        "SPLIT.FSPLIT",
        "SPLIT.RSPLIT",
        "SPLIT.USPLIT",
        "WRM",
        "FSPLIT",
        "RSPLIT",
        "USPLIT",
        "VTND",
        "VWRT",
        "VRGT",
        "VEXH",
        "SWH",
        "FWH",
        "SLWH",
    ]
    assert [execution_type.value for execution_type in ExecutionType] == [
        "fill",
        "trade_correct",
        "trade_bust",
    ]


def test_activity_response_models_parse_current_schema():
    non_trade_activity = NonTradeActivities(
        activity_type="DIV",
        activity_sub_type="CDIV",
        id="2026-07-14::activity-id",
        date="2026-07-14T10:00:00Z",
        net_amount="12.34",
        currency="USD",
        status="executed",
    )
    trading_activity = TradingActivities(
        activity_type="FILL",
        id="2026-07-14::trade-id",
        order_id="4ce24134-3d0c-4f61-aef5-1807a3391380",
        type="partial_fill",
        transaction_time="2026-07-14T10:00:00Z",
    )

    assert non_trade_activity.activity_type is ActivityType.DIV
    assert non_trade_activity.activity_sub_type is ActivitySubType.CDIV
    assert isinstance(non_trade_activity.date, datetime)
    assert trading_activity.activity_type is ActivityType.FILL
    assert trading_activity.type is TradeActivityType.PARTIAL_FILL
    assert isinstance(trading_activity.order_id, UUID)


def test_get_activities_request_serializes_filters():
    request = GetActivitiesRequest(
        activity_types=[ActivityType.FILL, ActivityType.DIV],
        date=date(2026, 7, 14),
        direction=Sort.DESC,
        page_size=25,
        page_token="next",
    )

    assert request.to_request_fields() == {
        "activity_types": "FILL,DIV",
        "date": "2026-07-14T00:00:00+00:00",
        "direction": "desc",
        "page_size": 25,
        "page_token": "next",
    }
    assert GetActivitiesRequest(
        category=ActivityCategory.TRADE_ACTIVITY
    ).to_request_fields() == {"category": "trade_activity"}


def test_get_activities_request_rejects_conflicting_filters():
    with pytest.raises(ValidationError, match="activity_types and category"):
        GetActivitiesRequest(
            activity_types=[ActivityType.FILL],
            category=ActivityCategory.TRADE_ACTIVITY,
        )


@pytest.mark.parametrize("page_size", [0, 101])
def test_get_activities_request_rejects_page_size_out_of_bounds(page_size):
    with pytest.raises(ValidationError):
        GetActivitiesRequest(page_size=page_size)


def test_get_activities_request_rejects_invalid_direction():
    with pytest.raises(ValidationError):
        GetActivitiesRequest(direction="sideways")


def test_legacy_non_trade_activity_retains_price_fields():
    activity = NonTradeActivity(
        id="2026-07-14::activity-id",
        account_id="4ce24134-3d0c-4f61-aef5-1807a3391380",
        activity_type="DIV",
        date="2026-07-14",
        net_amount=12.34,
        description="Dividend",
        price=100.0,
        per_share_amount=1.25,
    )

    assert activity.price == 100.0
    assert activity.per_share_amount == 1.25
