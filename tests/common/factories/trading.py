from alpaca.trading.models import Asset, Order
from alpaca.trading.enums import (
    AssetClass,
    OrderClass,
    OrderSide,
    OrderType,
    PositionIntent,
    TimeInForce,
)


def create_dummy_asset() -> Asset:
    """
    Creates an Asset object for testing

    Returns:
        Asset: An example asset
    """

    asset_data = {
        "id": "904837e3-3b76-47ec-b432-046db621571b",
        "class": "us_equity",
        "exchange": "NASDAQ",
        "symbol": "AAPL",
        "status": "active",
        "tradable": True,
        "marginable": True,
        "shortable": True,
        "easy_to_borrow": True,
        "fractionable": True,
    }

    return Asset(**asset_data)


def create_dummy_order() -> Order:
    """
    Creates an Order object for testing.

    Returns:
        Order: An example order.
    """
    return Order(
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
        position_intent=PositionIntent.BUY_TO_OPEN,
    )
