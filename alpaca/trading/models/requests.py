from datetime import datetime
from typing import List, Optional, Any
from uuid import UUID

from alpaca.common.enums import (
    OrderSide,
    OrderStatus,
    OrderType,
    Sort,
    TimeInForce,
    OrderClass,
    AssetStatus,
    AssetClass,
    AssetExchange,
)
from alpaca.common.models import NonEmptyRequest

from alpaca.common.models import ValidateBaseModel as BaseModel

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


class OrderRequest(NonEmptyRequest):
    """Contains data for submitting an order.

    Attributes:
        symbol (str): The symbol identifier for the asset being traded
        qty (Optional[float]): The number of shares to trade. Fractional qty available only with market orders.
        side (OrderSide): Whether the order will buy or sell the asset.
        type (OrderType): The execution logic type of the order (market, limit, etc).
        time_in_force (TimeInForce): The expiration logic of the order.
        extended_hours (Optional[float]): Whether the order can be executed during regular market hours.
        client_order_id (Optional[float]): A string to identify which client submitted the order.
        order_class (Optional[OrderClass]): The class of the order. Simple orders have no other legs.
        take_profit (Optional[TakeProfitRequest]): For orders with multiple legs, an order to exit a profitable trade.
        stop_loss (Optional[StopLossRequest]): For orders with multiple legs, an order to exit a losing trade.
    """

    symbol: str
    qty: float
    side: OrderSide
    type: OrderType
    time_in_force: TimeInForce
    order_class: Optional[OrderClass]
    extended_hours: Optional[bool]
    client_order_id: Optional[str]
    take_profit: Optional[TakeProfitRequest]
    stop_loss: Optional[StopLossRequest]


class MarketOrderRequest(OrderRequest):
    """
    Used to submit a market order.

    Attributes:
        notional (Optional[float]): The cash value of the shares to trade. Only works with market orders.
    """

    notional: Optional[float]

    def __init__(self, **data: Any) -> None:

        data["type"] = OrderType.MARKET

        super().__init__(**data)

    @root_validator()
    def root_validator(cls, values: dict) -> dict:

        qty_set = "qty" in values and values["qty"] is not None
        notional_set = "notional" in values and values["notional"] is not None

        if not qty_set and not notional_set:
            raise ValueError("At least one of qty or notional must be provided")
        elif qty_set and notional_set:
            raise ValueError("Both qty and notional can not be set.")

        return values


class StopOrderRequest(OrderRequest):
    """
    Used to submit a stop order.

    Attributes:
        stop_price (float): The price at which the stop order is converted to a market order or a stop limit
            order is converted to a limit order.
    """

    stop_price: float

    def __init__(self, **data: Any) -> None:

        data["type"] = OrderType.STOP

        super().__init__(**data)


class LimitOrderRequest(OrderRequest):
    """
    Used to submit a limit order.

    Attributes:
        limit_price (float): The worst fill price for a limit or stop limit order.
    """

    limit_price: float

    def __init__(self, **data: Any) -> None:

        data["type"] = OrderType.LIMIT

        super().__init__(**data)


class StopLimitOrderRequest(OrderRequest):
    """
    Used to submit a stop limit order.

    Attributes:
        stop_price (float): The price at which the stop order is converted to a market order or a stop limit
            order is converted to a limit order.
        limit_price (float): The worst fill price for a limit or stop limit order.
    """

    stop_price: float
    limit_price: float

    def __init__(self, **data: Any) -> None:

        data["type"] = OrderType.STOP_LIMIT

        super().__init__(**data)


class TrailingStopOrderRequest(OrderRequest):
    """
    Used to submit a trailing stop order.

    Attributes:
        trail_price (Optional[float]): The absolute price difference by which the trailing stop will trail.
        trail_percent (Optional[float]): The percent price difference by which the trailing stop will trail.
    """

    trail_price: Optional[float]
    trail_percent: Optional[float]

    def __init__(self, **data: Any) -> None:

        data["type"] = OrderType.TRAILING_STOP

        super().__init__(**data)

    @root_validator()
    def root_validator(cls, values: dict) -> dict:

        trail_percent_set = (
            "trail_percent" in values and values["trail_percent"] is not None
        )
        trail_price_set = "trail_price" in values and values["trail_price"] is not None

        if not trail_percent_set and not trail_price_set:
            raise ValueError(
                "Either trail_percent or trail_price must be set for a trailing stop order."
            )
        elif trail_percent_set and trail_price_set:
            raise ValueError("Both trail_percent and trail_price cannot be set.")

        return values


class GetOrdersRequest(NonEmptyRequest):
    """Contains data for submitting a request to retrieve orders.

    Attributes:
        status (Optional[OrderStatus]): Order status to be queried. open, closed or all. Defaults to open.
        limit (Optional[int]): The maximum number of orders in response. Defaults to 50 and max is 500.
        after (Optional[datetime]): The response will include only ones submitted after this timestamp.
        until (Optional[datetime]): The response will include only ones submitted until this timestamp.
        direction (Optional[Sort]): The chronological order of response based on the submission time. asc or desc. Defaults to desc.
        nested (Optional[bool]): If true, the result will roll up multi-leg orders under the legs field of primary order.
        side (Optional[OrderSide]): Filters down to orders that have a matching side field set.
        symbols (Optional[List[str]]): List of symbols to filter by.
    """

    status: Optional[OrderStatus]
    limit: Optional[int]  # not pagination
    after: Optional[datetime]
    until: Optional[datetime]
    direction: Optional[Sort]
    nested: Optional[bool]
    side: Optional[OrderSide]
    symbols: Optional[List[str]]


class GetOrderByIdRequest(NonEmptyRequest):
    """Contains data for submitting a request to retrieve a single order by its order id.

    Attributes:
        nested (bool): If true, the result will roll up multi-leg orders under the legs field of primary order.
    """

    nested: bool


class ReplaceOrderRequest(NonEmptyRequest):
    """Contains data for submitting a request to replace an order.

    Attributes:
        qty (Optional[int]): Number of shares to trade
        time_in_force (Optional[TimeInForce]): The new expiration logic of the order.
        limit_price (Optional[float]): Required if type of order being replaced is limit or stop_limit
        stop_price (Optional[float]): Required if type of order being replaced is stop or stop_limit
        trail (Optional[float]): The new value of the trail_price or trail_percent value (works only for type=“trailing_stop”)
        client_order_id (Optional[str]): A unique identifier for the order.
    """

    qty: Optional[int]
    time_in_force: Optional[TimeInForce]
    limit_price: Optional[float]
    stop_price: Optional[float]
    trail: Optional[float]
    client_order_id: Optional[str]


class CancelOrderResponse(BaseModel):
    """
    Data returned after requesting to cancel an order. It contains the cancel status of an order.

    Attributes:
        id (UUID): The order id
        status (int): The HTTP status returned after attempting to cancel the order.
    """

    id: UUID
    status: int


class GetAssetsRequest(NonEmptyRequest):
    """
    When querying for available assets, this model provides the parameters that can be filtered by.

    Attributes:
        status (Optional[AssetStatus]): The active status of the asset.
        asset_class (Optional[AssetClass]): The type of asset (i.e. us_equity, crypto).
        exchange (Optional[AssetExchange]): The exchange the asset trades on.
    """

    status: Optional[AssetStatus]
    asset_class: Optional[AssetClass]
    exchange: Optional[AssetExchange]
