import pytest
from alpaca.common.models import (
    Clock,
    Calendar,
    Position,
    ClosePositionResponse,
    Order,
    PortfolioHistory,
    ClosePositionRequest,
)
from datetime import datetime, date
from uuid import UUID
from alpaca.common.enums import (
    AssetClass,
    AssetStatus,
    AssetExchange,
    OrderStatus,
    OrderType,
    OrderClass,
    TimeInForce,
    OrderSide,
    PositionSide,
)
from factories import create_dummy_asset


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
    calendar = Calendar(date="2021-03-02", open="09:30", close="4:00")

    assert type(calendar.date) is date
    assert type(calendar.open) is datetime
    assert type(calendar.close) is datetime

    assert calendar.open.minute == 30


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
    )

    assert isinstance(position.asset_id, UUID)


def test_close_position_response_uuid():
    """Tests that the order id is up-casted to UUID."""
    close_position_response = ClosePositionResponse(
        order_id="904837e3-3b76-47ec-b432-046db621571b", status_code=201
    )

    assert isinstance(close_position_response.order_id, UUID)


def test_order_timestamps():
    """Tests that all timestamp fields are up-casted to datetimes."""

    order = Order(
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
        replaced_by=None,
        replaces=None,
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
        legs=None,
        trail_percent=None,
        trail_price=None,
        hwm=None,
        commission="1.25",
    )

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

    order = Order(
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
        legs=None,
        trail_percent=None,
        trail_price=None,
        hwm=None,
        commission="1.25",
    )

    assert isinstance(order.id, UUID)
    assert isinstance(order.client_order_id, UUID)
    assert isinstance(order.replaced_by, UUID)
    assert isinstance(order.replaces, UUID)
    assert isinstance(order.asset_id, UUID)


def test_order_legs():
    """Tests recursive Order object with legs field"""

    order = Order(
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
        legs=None,
        trail_percent=None,
        trail_price=None,
        hwm=None,
        commission="1.25",
    )

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
        commission="1.25",
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
        close_position_request = ClosePositionRequest(qty="100", percentage="0.5")

    assert (
        "Only one of qty or percentage must be given to the ClosePositionRequest, got both."
        in str(e.value)
    )


def test_close_position_request_with_neither_qty_or_percentage():
    with pytest.raises(ValueError) as e:
        close_position_request = ClosePositionRequest()

    assert (
        "qty or percentage must be given to the ClosePositionRequest, got None for both."
        in str(e.value)
    )
