from typing import Optional, Any

from alpaca.common.enums import OrderSide, OrderType, TimeInForce, OrderClass
from alpaca.common.models import NonEmptyRequest

from pydantic import root_validator


class TakeProfitRequest(NonEmptyRequest):
    """
    Used for providing take profit details for a bracket order.

    Attributes:
        limit_price (float): The execution price for exiting a profitable trade.
    """

    limit_price: float


class StopLossRequest(NonEmptyRequest):
    """
    Used for providing stop loss details for a bracket order.

    Attributes:
        stop_price (float): The price at which the stop loss is triggered.
        limit_price (Optional[float]): The execution price for exiting a losing trade. If not provided, the
            stop loss will execute as a market order.
    """

    stop_price: float
    limit_price: Optional[float] = None


class OrderCreationRequest(NonEmptyRequest):
    """Contains data for submitting an order.

    Attributes:
        symbol (str): The symbol identifier for the asset being traded
        qty (Optional[float]): The number of shares to trade. Fractional qty available only with market orders.
        notional (Optional[float]): The cash value of the shares to trade. Only works with market orders.
        side (OrderSide): Whether the order will buy or sell the asset.
        type (OrderType): The execution logic type of the order (market, limit, etc).
        time_in_force (TimeInForce): The expiration logic of the order.
        limit_price (Optional[float]): The worst fill price for a limit or stop limit order.
        stop_price (Optional[float]): The price at which the stop order is converted to a market order or a stop limit
            order is converted to a limit order.
        trail_price (Optional[float]): The absolute price difference by which the trailing stop will trail.
        trail_percent (Optional[float]): The percent price difference by which the trailing stop will trail.
        extended_hours (Optional[float]): Whether the order can be executed during regular market hours.
        client_order_id (Optional[float]): A string to identify which client submitted the order.
        order_class (Optional[OrderClass]): The class of the order. Simple orders have no other legs.
        take_profit (Optional[TakeProfitRequest]): For orders with multiple legs, an order to exit a profitable trade.
        stop_loss (Optional[StopLossRequest]): For orders with multiple legs, an order to exit a losing trade.
    """

    symbol: str
    qty: Optional[float]
    notional: Optional[float]
    side: OrderSide
    type: OrderType
    time_in_force: TimeInForce
    limit_price: Optional[float]
    stop_price: Optional[float]
    trail_price: Optional[float]
    trail_percent: Optional[float]
    extended_hours: Optional[bool]
    client_order_id: Optional[str]
    order_class: Optional[OrderClass]
    take_profit: Optional[TakeProfitRequest]
    stop_loss: Optional[StopLossRequest]

    @root_validator()
    def root_validator(cls, values: dict) -> dict:
        qty_set = "qty" in values and values["qty"] is not None
        notional_set = "notional" in values and values["notional"] is not None
        if not qty_set and not notional_set:
            raise ValueError("At least one of qty or notional must be provided")
        elif qty_set and notional_set:
            raise ValueError("Both qty and notional can not be set.")

        fractional_qty = (
            "qty" in values
            and values["qty"] is not None
            and not float(values["qty"]).is_integer()
        )

        type_set = "type" in values and values["type"] is not None

        if (
            (fractional_qty or notional_set)
            and type_set
            and values["type"] != OrderType.MARKET
        ):
            raise ValueError("Fractional orders are only available for market orders.")

        limit_or_stop_limit = type_set and (
            values["type"] == OrderType.LIMIT or values["type"] == OrderType.STOP_LIMIT
        )
        limit_price_set = "limit_price" in values and values["limit_price"] is not None

        if limit_or_stop_limit and not limit_price_set:
            raise ValueError("Limit and stop limit orders must have a limit_price.")
        elif not limit_or_stop_limit and limit_price_set:
            raise ValueError(
                "limit_price can only be set for limit or stop limit orders."
            )

        stop_or_stop_limit = type_set and (
            values["type"] == OrderType.STOP or values["type"] == OrderType.STOP_LIMIT
        )
        stop_price_set = "stop_price" in values and values["stop_price"] is not None

        if stop_or_stop_limit and not stop_price_set:
            raise ValueError("Stop and stop limit orders must have a stop_price.")
        elif not stop_or_stop_limit and stop_price_set:
            raise ValueError(
                "stop_price can only be set for stop or stop limit orders."
            )

        trailing_stop_set = type_set and values["type"] == OrderType.TRAILING_STOP
        trail_percent_set = (
            "trail_percent" in values and values["trail_percent"] is not None
        )
        trail_price_set = "trail_price" in values and values["trail_price"] is not None

        if trail_percent_set and trail_price_set:
            raise ValueError("Both trail_percent and trail_price cannot be set.")

        if trailing_stop_set and not (trail_percent_set or trail_price_set):
            raise ValueError(
                "Either trail_percent or trail_price must be set for a trailing stop order."
            )
        elif not trailing_stop_set and (trail_percent_set or trail_price_set):
            raise ValueError(
                "trail_percent and trail_price may be set only for trailing stop orders."
            )

        return values
