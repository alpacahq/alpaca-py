from datetime import date, datetime
from uuid import UUID

import pytest

from alpaca.trading.enums import (
    ActivityCategory,
    ActivitySubType,
    ActivityType,
    ExecutionType,
    TradeActivityType,
)
from alpaca.trading.models import (
    AcatcActivityV2,
    ActivityEventV2,
    ActivityV2DetailNTA,
    ActivityV2DetailTRD,
    CDIVActivityV2,
    CommonSplitStockActivityV2,
    ExchangeOfferActivityV2,
    FixedIncomeRedemptionActivityV2,
    ForwardSplitActivityV2,
    NonTradeActivities,
    NonTradeActivity,
    OpcaCDIVActivityV2,
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


def test_activity_v2_common_base_parses_inherited_fields():
    group_id = UUID("4ce24134-3d0c-4f61-aef5-1807a3391380")

    activity = CommonSplitStockActivityV2(
        system_date="2026-07-14",
        group_id=str(group_id),
        position_date="2026-07-11",
        old_cusip="old-cusip",
        new_cusip="new-cusip",
        old_rate="1",
        new_rate="2",
        payable_date="2026-07-15",
        old_qty="5",
        new_qty="10",
    )

    assert activity.system_date == date(2026, 7, 14)
    assert activity.group_id == group_id
    assert activity.position_date == date(2026, 7, 11)
    assert activity.payable_date == date(2026, 7, 15)
    assert activity.new_qty == "10"


@pytest.mark.parametrize(
    ("model", "payload", "field", "expected"),
    [
        (
            AcatcActivityV2,
            {
                "system_date": "2026-07-14",
                "external_id": "acat-1",
                "request_id": "4ce24134-3d0c-4f61-aef5-1807a3391380",
            },
            "request_id",
            UUID("4ce24134-3d0c-4f61-aef5-1807a3391380"),
        ),
        (
            CDIVActivityV2,
            {
                "system_date": "2026-07-14",
                "position_date": "2026-07-11",
                "entitled_qty": "10",
                "cash_payout": "2.50",
                "symbol": "AAPL",
                "cusip": "037833100",
                "rate": "0.25",
                "foreign": False,
                "special": False,
            },
            "position_date",
            date(2026, 7, 11),
        ),
        (
            OpcaCDIVActivityV2,
            {
                "system_date": "2026-07-14",
                "position_date": "2026-07-11",
                "old_contract_symbol": "AAPL260717C00150000",
                "new_contract_symbol": "AAPL1260717C00150000",
                "symbol": "AAPL",
                "cusip": "037833100",
                "rate": "0.25",
                "foreign": False,
                "special": True,
            },
            "special",
            True,
        ),
        (
            ForwardSplitActivityV2,
            {
                "system_date": "2026-07-14",
                "position_date": "2026-07-11",
                "old_cusip": "old",
                "new_cusip": "new",
                "old_rate": "1",
                "new_rate": "2",
                "old_qty": "5",
                "new_qty": "10",
                "symbol": "AAPL",
            },
            "new_qty",
            "10",
        ),
        (
            ExchangeOfferActivityV2,
            {
                "system_date": "2026-07-14",
                "source_cusip": "old",
                "source_symbol": "OLD",
                "new_cusip": "new",
                "new_symbol": "NEW",
            },
            "new_symbol",
            "NEW",
        ),
        (
            FixedIncomeRedemptionActivityV2,
            {
                "system_date": "2026-07-14",
                "ca_id": "8f027b04-755e-4e33-88c8-66c5aa1e8109",
                "payment_date": "2026-07-15",
                "cusip": "91282CKQ3",
                "qty": "10",
                "cash_payout": "10000",
            },
            "payment_date",
            date(2026, 7, 15),
        ),
    ],
)
def test_concrete_activity_v2_models_parse_representative_payloads(
    model, payload, field, expected
):
    activity = model(**payload)

    assert getattr(activity, field) == expected


def test_activity_v2_event_envelope_parses_trade_details():
    event = ActivityEventV2(
        at="2026-07-14T10:00:01Z",
        event_id="01J2Y7YQJFM6V3J5A8YF0P0M0A",
        activity_type="FILL",
        activity_subtype="CDIV",
        executed_at="2026-07-14T10:00:00Z",
        status="executed",
        settle_date="2026-07-16",
        currency="USD",
        ref_id="4ce24134-3d0c-4f61-aef5-1807a3391380",
        details={
            "order_id": "8f027b04-755e-4e33-88c8-66c5aa1e8109",
            "side": "buy",
            "symbol": "AAPL",
            "asset_id": "3b7f98a8-941a-4c59-9b12-1c728c1131ac",
            "leaves_qty": "0",
            "cum_qty": "2",
            "order_status": "filled",
            "execution_type": "fill",
        },
    )

    assert isinstance(event.at, datetime)
    assert event.activity_type is ActivityType.FILL
    assert event.activity_subtype is ActivitySubType.CDIV
    assert isinstance(event.details, ActivityV2DetailTRD)
    assert event.details.execution_type == ExecutionType.FILL


def test_activity_v2_event_envelope_parses_non_trade_details():
    event = ActivityEventV2(
        at="2026-07-14T10:00:01Z",
        event_id="01J2Y7YQJFM6V3J5A8YF0P0M0B",
        activity_type="DIV",
        executed_at="2026-07-14T10:00:00Z",
        status="executed",
        settle_date="2026-07-16",
        currency="USD",
        ref_id="4ce24134-3d0c-4f61-aef5-1807a3391380",
        net_amount="12.34",
        details={"system_date": "2026-07-14"},
    )

    assert isinstance(event.details, ActivityV2DetailNTA)
    assert event.details.system_date == date(2026, 7, 14)


def test_get_activities_request_serializes_filters():
    request = GetActivitiesRequest(
        activity_types=[ActivityType.FILL, ActivityType.DIV],
        date=date(2026, 7, 14),
        direction="desc",
        page_size=25,
        page_token="next",
    )

    assert request.to_request_fields() == {
        "activity_types": ["FILL", "DIV"],
        "date": "2026-07-14T00:00:00+00:00",
        "direction": "desc",
        "page_size": 25,
        "page_token": "next",
    }
    assert GetActivitiesRequest(
        category=ActivityCategory.TRADE_ACTIVITY
    ).to_request_fields() == {"category": "trade_activity"}


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
