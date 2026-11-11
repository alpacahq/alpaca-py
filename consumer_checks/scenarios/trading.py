"""Trading API: market info, assets, and the order lifecycle."""

from __future__ import annotations

from datetime import date
from typing import Any, Dict

from alpaca.common.exceptions import APIError
from alpaca.trading.enums import (
    AssetClass,
    OrderSide,
    OrderStatus,
    OrderType,
    QueryOrderStatus,
    TimeInForce,
)
from alpaca.trading.models import Asset, Calendar, Clock, Order
from alpaca.trading.requests import (
    GetCalendarRequest,
    GetOrdersRequest,
    LimitOrderRequest,
)

from . import Context, scenario

# Far below the market so the order never fills, on paper or otherwise.
UNFILLABLE_LIMIT_PRICE = 1.00


@scenario(covers=["TradingClient.get_clock"])
def market_clock(ctx: Context) -> Dict[str, Any]:
    clock = ctx.trading.get_clock()

    assert isinstance(clock, Clock)
    assert isinstance(clock.is_open, bool)
    assert clock.next_close > clock.timestamp
    assert clock.timestamp.tzinfo is not None
    return {"clock": clock}


@scenario(covers=["TradingClient.get_calendar"])
def trading_calendar_for_a_week(ctx: Context) -> Dict[str, Any]:
    days = ctx.trading.get_calendar(
        GetCalendarRequest(start=date(2024, 3, 1), end=date(2024, 3, 8))
    )

    assert isinstance(days, list)
    assert [day.date for day in days] == [
        date(2024, 3, 1),
        date(2024, 3, 4),
        date(2024, 3, 5),
        date(2024, 3, 6),
        date(2024, 3, 7),
        date(2024, 3, 8),
    ]
    assert all(isinstance(day, Calendar) for day in days)
    assert days[0].open < days[0].close
    return {"days": days}


@scenario(covers=["TradingClient.get_asset"])
def asset_by_symbol(ctx: Context) -> Dict[str, Any]:
    asset = ctx.trading.get_asset("AAPL")

    assert isinstance(asset, Asset)
    assert asset.symbol == "AAPL"
    assert asset.asset_class == AssetClass.US_EQUITY
    assert isinstance(asset.tradable, bool)
    return {"asset": asset}


@scenario(covers=["TradingClient.get_asset"])
def unknown_asset_raises_api_error(ctx: Context) -> Dict[str, Any]:
    # Users catch APIError and branch on status_code. Both are part of the contract.
    try:
        ctx.trading.get_asset("NOT-A-REAL-SYMBOL")
    except APIError as error:
        assert isinstance(error.status_code, int)
        assert 400 <= error.status_code < 500
        return {"error": error}
    raise AssertionError("expected APIError for an unknown symbol")


@scenario(
    covers=[
        "TradingClient.submit_order",
        "TradingClient.get_order_by_id",
        "TradingClient.get_order_by_client_id",
        "TradingClient.get_orders",
        "TradingClient.cancel_order_by_id",
    ]
)
def limit_order_lifecycle(ctx: Context) -> Dict[str, Any]:
    client_order_id = ctx.unique_id("client_order_id")
    order = ctx.trading.submit_order(
        LimitOrderRequest(
            symbol="AAPL",
            qty=1,
            side=OrderSide.BUY,
            time_in_force=TimeInForce.DAY,
            limit_price=UNFILLABLE_LIMIT_PRICE,
            client_order_id=client_order_id,
        )
    )
    assert isinstance(order, Order)
    try:
        assert order.client_order_id == client_order_id
        assert order.symbol == "AAPL"
        assert order.type == OrderType.LIMIT
        assert order.side == OrderSide.BUY

        by_id = ctx.trading.get_order_by_id(order.id)
        by_client_id = ctx.trading.get_order_by_client_id(client_order_id)
        assert isinstance(by_id, Order) and isinstance(by_client_id, Order)
        assert by_id.id == by_client_id.id == order.id

        open_orders = ctx.trading.get_orders(
            GetOrdersRequest(status=QueryOrderStatus.OPEN, symbols=["AAPL"])
        )
        assert isinstance(open_orders, list)
        # Other open orders on the paper account are not part of the snapshot.
        listed = [listed for listed in open_orders if listed.id == order.id]
        assert len(listed) == 1
    finally:
        ctx.trading.cancel_order_by_id(order.id)

    canceled = ctx.trading.get_order_by_id(order.id)
    for _ in range(10):
        assert isinstance(canceled, Order)
        if canceled.status == OrderStatus.CANCELED:
            break
        ctx.sleep(1)
        canceled = ctx.trading.get_order_by_id(order.id)
    assert isinstance(canceled, Order)
    assert canceled.status == OrderStatus.CANCELED
    return {
        "submitted": order,
        "by_id": by_id,
        "listed": listed[0],
        "canceled": canceled,
    }
