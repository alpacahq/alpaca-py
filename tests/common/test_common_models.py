import warnings

import pytest
from alpaca.trading.models import (
    AccountConfiguration,
    Asset,
    Clock,
    Calendar,
    CorporateActionAnnouncement,
    PortfolioHistory,
    TradeAccount,
)
from alpaca.trading.requests import (
    ClosePositionRequest,
    UpdateWatchlistRequest,
)
from datetime import datetime, date
from uuid import UUID
from alpaca.trading.enums import (
    AccountStatus,
    AssetBorrowStatus,
    AssetClass,
    AssetExchange,
    OrderType,
    OrderClass,
    PositionIntent,
    TimeInForce,
    OrderSide,
    PositionSide,
    CorporateActionType,
    CorporateActionSubType,
)
from alpaca.trading.models import (
    Position,
    ClosePositionResponse,
    Order,
)
from factories import create_dummy_order


def test_clock_timestamps():
    """Tests whether timestamp string is successfully parsed into datetime"""
    clock = Clock(
        timestamp="2022-04-28T14:07:04.451420928-04:00",
        is_open=True,
        next_open="2022-04-29T09:30:00-04:00",
        next_close="2022-04-28T16:00:00-04:00",
    )

    assert type(clock.timestamp) is datetime

    assert clock.timestamp.day == 28


def test_calendar_timestamps():
    """Tests whether the timestamp strings are successfully parsed into datetime"""
    calendar = Calendar(
        date="2021-03-02",
        open="09:30",
        close="4:00",
        session_open="0400",
        session_close="2000",
        settlement_date="2021-03-04",
    )

    assert type(calendar.date) is date
    assert type(calendar.open) is datetime
    assert type(calendar.close) is datetime
    assert calendar.open.minute == 30
    assert calendar.session_open == "0400"
    assert calendar.session_close == "2000"
    assert calendar.settlement_date == date(2021, 3, 4)


def test_optional_openapi_scalar_fields_round_trip():
    """Fields the Trading OpenAPI schema added stay on the parsed models."""
    asset = Asset(
        id="904837e3-3b76-47ec-b432-046db621571b",
        **{
            "class": "us_equity",
            "exchange": "NASDAQ",
            "symbol": "AAPL",
            "status": "active",
            "tradable": True,
            "marginable": True,
            "shortable": True,
            "easy_to_borrow": True,
            "fractionable": True,
            "borrow_status": "easy_to_borrow",
            "cusip": "037833100",
            "margin_requirement_long": "100",
            "margin_requirement_short": "30",
        },
    )
    assert asset.borrow_status == AssetBorrowStatus.EASY_TO_BORROW
    assert asset.cusip == "037833100"
    assert asset.margin_requirement_long == "100"
    assert asset.margin_requirement_short == "30"
    assert asset.model_dump(mode="json")["borrow_status"] == "easy_to_borrow"


def _asset_payload(**overrides):
    payload = {
        "id": "904837e3-3b76-47ec-b432-046db621571b",
        "class": "us_equity",
        "exchange": "NASDAQ",
        "symbol": "AAPL",
        "status": "active",
        "tradable": True,
        "marginable": True,
        "shortable": True,
        "fractionable": True,
    }
    payload.update(overrides)
    return payload


def test_asset_parses_without_deprecated_borrow_field():
    """easy_to_borrow is no longer required. borrow_status replaces it."""
    with warnings.catch_warnings():
        warnings.simplefilter("error", DeprecationWarning)
        asset = Asset(**_asset_payload(borrow_status="hard_to_borrow"))
        assert asset.borrow_status == AssetBorrowStatus.HARD_TO_BORROW
        assert asset.model_dump(mode="json")["easy_to_borrow"] is None

    with pytest.warns(DeprecationWarning, match="Use borrow_status instead"):
        assert asset.easy_to_borrow is None


def test_deprecated_asset_fields_warn_on_read():
    asset = Asset(
        **_asset_payload(
            easy_to_borrow=True,
            maintenance_margin_requirement=30,
            margin_requirement_long="100",
            margin_requirement_short="30",
        )
    )

    with warnings.catch_warnings():
        warnings.simplefilter("error", DeprecationWarning)
        assert asset.margin_requirement_long == "100"
        assert asset.model_dump()["maintenance_margin_requirement"] == 30

    with pytest.warns(
        DeprecationWarning,
        match="Use margin_requirement_long or margin_requirement_short",
    ):
        assert asset.maintenance_margin_requirement == 30

    with pytest.warns(DeprecationWarning, match="Use borrow_status instead"):
        assert asset.easy_to_borrow is True

    position = Position(
        asset_id="904837e3-3b76-47ec-b432-046db621571b",
        symbol="AAPL",
        exchange=AssetExchange.NASDAQ,
        asset_class=AssetClass.US_EQUITY,
        avg_entry_price="100.0",
        qty="5",
        side=PositionSide.LONG,
        cost_basis="500.0",
        prev_swap_rate="1.25",
    )
    assert position.prev_swap_rate == "1.25"

    account = TradeAccount(
        id="904837e3-3b76-47ec-b432-046db621571b",
        account_number="010203ABCD",
        status=AccountStatus.ACTIVE,
        balance_asof="2023-09-27",
        intraday_adjustments="0",
        pending_reg_taf_fees="0.12",
        crypto_tier=1,
        effective_buying_power="245432.61",
        position_market_value="1259.61",
    )
    assert account.balance_asof == "2023-09-27"
    assert account.intraday_adjustments == "0"
    assert account.pending_reg_taf_fees == "0.12"
    assert account.crypto_tier == 1
    assert account.effective_buying_power == "245432.61"
    assert account.position_market_value == "1259.61"
    assert (
        TradeAccount(
            id="904837e3-3b76-47ec-b432-046db621571b",
            account_number="010203ABCD",
            status=AccountStatus.ACTIVE,
        ).crypto_tier
        is None
    )

    configuration = AccountConfiguration(
        fractional_trading=True,
        max_margin_multiplier="4",
        no_shorting=False,
        suspend_trade=False,
        trade_confirm_email="all",
        ptp_no_exception_entry=False,
        disable_overnight_trading=False,
    )
    assert configuration.disable_overnight_trading is False
    assert (
        AccountConfiguration(
            fractional_trading=True,
            max_margin_multiplier="4",
            no_shorting=False,
            suspend_trade=False,
            trade_confirm_email="all",
            ptp_no_exception_entry=False,
        ).disable_overnight_trading
        is None
    )

    history = PortfolioHistory(
        timestamp=[1697846400],
        equity=[100.0],
        profit_loss=[1.0],
        profit_loss_pct=[0.01],
        timeframe="1D",
        base_value_asof="2023-10-20",
    )
    assert history.base_value_asof == date(2023, 10, 20)
    assert history.model_dump(mode="json")["base_value_asof"] == "2023-10-20"


def test_position_uuid():
    """Tests that the asset id is up-casted to UUID."""
    position = Position(
        asset_id="904837e3-3b76-47ec-b432-046db621571b",
        symbol="AAPL",
        exchange=AssetExchange.NYSE,
        asset_class=AssetClass.US_EQUITY,
        avg_entry_price="100.0",
        qty="5",
        side=PositionSide.LONG,
        market_value="600.0",
        cost_basis="500.0",
        unrealized_pl="100.0",
        unrealized_plpc="0.20",
        unrealized_intraday_pl="10.0",
        unrealized_intraday_plpc="0.0084",
        current_price="120.0",
        lastday_price="119.0",
        change_today="0.0084",
        usd={
            "avg_entry_price": "100.0",
            "market_value": "600.0",
            "cost_basis": "500.0",
            "unrealized_pl": "100.0",
            "unrealized_plpc": "0.20",
            "unrealized_intraday_pl": "10.0",
            "unrealized_intraday_plpc": "0.0084",
            "current_price": "120.0",
            "lastday_price": "119.0",
            "change_today": "0.0084",
        },
    )

    assert isinstance(position.asset_id, UUID)


def test_close_position_response_uuid():
    """Tests that the order id is up-casted to UUID."""
    data = {
        "symbol": "SQQQ",
        "status": 403,
        "body": {
            "available": "0",
            "code": 40310000,
            "existing_qty": "1000",
            "held_for_orders": "1000",
            "message": "insufficient qty available for order (requested: 1000, available: 0)",
            "symbol": "SQQQ",
        },
    }
    close_position_response = ClosePositionResponse(**data)

    assert isinstance(close_position_response.symbol, str)


def test_order_timestamps():
    """Tests that all timestamp fields are up-casted to datetimes."""

    order = create_dummy_order()

    assert isinstance(order.created_at, datetime)
    assert isinstance(order.updated_at, datetime)
    assert isinstance(order.submitted_at, datetime)
    assert isinstance(order.filled_at, datetime)
    assert isinstance(order.expired_at, datetime)
    assert isinstance(order.canceled_at, datetime)
    assert isinstance(order.failed_at, datetime)
    assert isinstance(order.replaced_at, datetime)


def test_order_uuids():
    """Tests that the Order's id fields are up-casted to UUIDs."""

    order = create_dummy_order()

    assert isinstance(order.id, UUID)
    assert isinstance(order.replaced_by, UUID)
    assert isinstance(order.replaces, UUID)
    assert isinstance(order.asset_id, UUID)


def test_order_legs():
    """Tests recursive Order object with legs field"""

    order = create_dummy_order()

    order_with_legs = Order(
        id="61e69015-8549-4bfd-b9c3-01e75843f47d",
        client_order_id="eb9e2aaa-f71a-4f51-b5b4-52a6c565dad4",
        created_at="2021-03-16T18:38:01.942282Z",
        updated_at="2021-03-16T18:38:01.942282Z",
        submitted_at="2021-03-16T18:38:01.937734Z",
        filled_at="2021-03-16T18:38:01.937734Z",
        expired_at="2021-03-16T18:38:01.937734Z",
        canceled_at="2021-03-16T18:38:01.937734Z",
        failed_at="2021-03-16T18:38:01.937734Z",
        replaced_at="2021-03-16T18:38:01.937734Z",
        replaced_by="61e69015-8549-4bfd-b9c3-01e75843f47d",
        replaces="61e69015-8549-4bfd-b9c3-01e75843f47d",
        asset_id="b0b6dd9d-8b9b-48a9-ba46-b9d54906e415",
        symbol="AAPL",
        asset_class=AssetClass.US_EQUITY,
        notional="500",
        qty=None,
        filled_qty="0",
        filled_avg_price=None,
        order_class=OrderClass.SIMPLE,
        order_type=OrderType.MARKET,
        type=OrderType.MARKET,
        side=OrderSide.BUY,
        time_in_force=TimeInForce.DAY,
        limit_price=None,
        stop_price=None,
        status="accepted",
        extended_hours=False,
        legs=[order],
        trail_percent=None,
        trail_price=None,
        hwm=None,
        position_intent=PositionIntent.BUY_TO_OPEN,
    )

    assert isinstance(order_with_legs.legs, list)
    assert isinstance(order_with_legs.legs[0], Order)


def test_close_position_request_with_qty():
    close_position_request = ClosePositionRequest(qty="100")
    assert close_position_request.qty == "100"
    assert close_position_request.percentage is None


def test_close_position_request_with_percentage():
    close_position_request = ClosePositionRequest(percentage="0.5")
    assert close_position_request.qty is None
    assert close_position_request.percentage == "0.5"


def test_close_position_request_with_qty_and_percentage():
    with pytest.raises(ValueError) as e:
        ClosePositionRequest(qty="100", percentage="0.5")

    assert (
        "Only one of qty or percentage must be given to the ClosePositionRequest, got both."
        in str(e.value)
    )


def test_close_position_request_with_neither_qty_or_percentage():
    with pytest.raises(ValueError) as e:
        ClosePositionRequest()

    assert (
        "qty or percentage must be given to the ClosePositionRequest, got None for both."
        in str(e.value)
    )


def test_parse_corporate_action_announcement():
    data = {
        "id": "be3c368a-4c7c-4384-808e-f02c9f5a8afe",
        "corporate_action_id": "F58684224_XY37",
        "ca_type": "dividend",
        "ca_sub_type": "cash",
        "initiating_symbol": "MLLAX",
        "initiating_original_cusip": "55275E101",
        "target_symbol": "MLLAX",
        "target_original_cusip": "55275E101",
        "declaration_date": "2021-01-05",
        "ex_date": "2021-01-12",
        "record_date": "2021-01-13",
        "payable_date": "2021-01-14",
        "cash": "0.018",
        "old_rate": "1",
        "new_rate": "1",
    }

    announcement = CorporateActionAnnouncement(**data)

    assert announcement.ca_type == CorporateActionType.DIVIDEND
    assert announcement.ca_sub_type == CorporateActionSubType.CASH
    assert type(announcement.declaration_date) is date


def test_update_watchlist_request_asserts_at_least_1_field():
    with pytest.raises(ValueError) as e:
        UpdateWatchlistRequest()

    assert "One of 'name' or 'symbols' must be defined" in str(e.value)
