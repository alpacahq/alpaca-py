from .models import ValidateBaseModel as BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional, List
from ..enums import (
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
from pydantic import Field


class Asset(BaseModel):
    """
    Represents a security. Some Assets are not tradable with Alpaca. These Assets are
    marked with the flag `tradable=false`.

    For more info, visit https://alpaca.markets/docs/api-references/trading-api/assets/
    """

    id: UUID
    asset_class: AssetClass = Field(
        alias="class"
    )  # using a pydantic alias to allow parsing data with the `class` keyword field
    exchange: AssetExchange
    symbol: str
    name: Optional[str] = None
    status: AssetStatus
    tradable: bool
    marginable: bool
    shortable: bool
    easy_to_borrow: bool
    fractionable: bool


class Position(BaseModel):
    """
    Attributes:
        asset_id (UUID): ID of the asset.
        symbol (str): Symbol of the asset.
        exchange (AssetExchange): Exchange name of the asset.
        asset_class (AssetClass): Name of the asset's asset class.
        avg_entry_price (str): The average entry price of the position.
        qty (str): The number of shares of the position.
        side (PositionSide): "long" or "short" representing the side of the position.
        market_value (str): Total dollar amount of the position.
        cost_basis (str): Total cost basis in dollars.
        unrealized_pl (str): Unrealized profit/loss in dollars.
        unrealized_plpc (str): Unrealized profit/loss percent.
        unrealized_intraday_pl (str): Unrealized profit/loss in dollars for the day.
        unrealized_intraday_plpc (str): Unrealized profit/loss percent for the day.
        current_price (str): Current asset price per share.
        lastday_price (str): Last day’s asset price per share based on the closing value of the last trading day.
        change_today (str): Percent change from last day's price.
    """

    asset_id: UUID
    symbol: str
    exchange: AssetExchange
    asset_class: AssetClass
    avg_entry_price: str
    qty: str
    side: PositionSide
    market_value: str
    cost_basis: str
    unrealized_pl: str
    unrealized_plpc: str
    unrealized_intraday_pl: str
    unrealized_intraday_plpc: str
    current_price: str
    lastday_price: str
    change_today: str


class ClosePositionResponse(BaseModel):
    """
    Attributes:
        order_id (UUID): ID of order that was created to liquidate the position.
        status_code (int): Status code corresponding to the request to liquidate the position.
    """

    order_id: UUID
    status_code: int


class Order(BaseModel):
    """
    Attributes:
        id (UUID): Order ID generated by Alpaca.
        client_order_id (UUID): Client unique order ID
        created_at (datetime): Timestamp when the Order was created.
        updated_at (datetime): Timestamp when the Order was last updated.
        submitted_at (datetime): Timestamp when the Order was submitted.
        filled_at (Optional[datetime]): Timestamp when the Order was filled.
        expired_at (Optional[datetime]): Timestamp when the Order expired at.
        canceled_at (Optional[datetime]): Timestamp when the Order was canceled.
        failed_at (Optional[datetime]): Timestamp when the Order failed at.
        replaced_at (Optional[datetime]): Timestamp when the Order was replaced by a new Order.
        replaced_by (Optional[UUID]): ID of Order that replaces this Order.
        replaces (Optional[UUID]): ID of Order which this Order replaces.
        asset_id (UUID): ID of the asset.
        symbol (str): Symbol of the asset.
        asset_class (AssetClass): Asset class of the asset.
        notional (Optional[str]): Ordered notional amount. If entered, qty will be null. Can take up to 9 decimal
          points.
        qty (Optional[str]): Ordered quantity. If entered, notional will be null. Can take up to 9 decimal points.
        filled_qty (Optional[str]): Filled quantity.
        filled_avg_price (Optional[str]): Filled average price. Can be 0 until order is processed in case order is
          passed outside of market hours.
        order_class (OrderClass): Valid values: simple, bracket, oco or oto.
        order_type (OrderType): Deprecated with just type field below.
        type (OrderType): Valid values: market, limit, stop, stop_limit, trailing_stop.
        side (OrderSide): Valid values: buy and sell.
        time_in_force (TimeInForce): Length of time the Order is in force.
        limit_price (Optional[str]): Limit price of the Order.
        stop_price (Optional[str]): Stop price of the Order.
        status (OrderStatus): The status of the Order.
        extended_hours (bool): If true, eligible for execution outside regular trading hours.
        legs (Optional[List[Order]]): When querying non-simple order_class orders in a nested style, an array of Order
          entities associated with this order. Otherwise, null.
        trail_percent (Optional[str]): The percent value away from the high water mark for trailing stop orders.
        trail_price (Optional[str]): The dollar value away from the high water mark for trailing stop orders.
        hwm (Optional[str]): The highest (lowest) market price seen since the trailing stop order was submitted.
    """

    id: UUID
    client_order_id: UUID
    created_at: datetime
    updated_at: datetime
    submitted_at: datetime
    filled_at: Optional[datetime]
    expired_at: Optional[datetime]
    canceled_at: Optional[datetime]
    failed_at: Optional[datetime]
    replaced_at: Optional[datetime]
    replaced_by: Optional[UUID]
    replaces: Optional[UUID]
    asset_id: UUID
    symbol: str
    asset_class: AssetClass
    notional: Optional[str]
    qty: Optional[str]
    filled_qty: Optional[str]
    filled_avg_price: Optional[str]
    order_class: OrderClass
    order_type: OrderType
    type: OrderType
    side: OrderSide
    time_in_force: TimeInForce
    limit_price: Optional[str]
    stop_price: Optional[str]
    status: OrderStatus
    extended_hours: bool
    legs: Optional[List["Order"]]
    trail_percent: Optional[str]
    trail_price: Optional[str]
    hwm: Optional[str]


class PortfolioHistory(BaseModel):
    """
    Attributes:
        timestamp (List[int]): Time of each data element, left-labeled (the beginning of time window).
        equity (List[float]): Equity value of the account in dollar amount as of the end of each time window.
        profit_loss (List[float]): Profit/loss in dollar from the base value.
        profit_loss_pct (List[float]): Profit/loss in percentage from the base value.
        base_value (float): Basis in dollar of the profit loss calculation.
        timeframe (str): Time window size of each data element.
    """

    timestamp: List[int]
    equity: List[float]
    profit_loss: List[float]
    profit_loss_pct: List[float]
    base_value: float
    timeframe: str
