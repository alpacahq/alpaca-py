from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional, Union

import pandas as pd
from pydantic import model_validator

from alpaca.common.enums import Sort
from alpaca.common.models import ModelWithID
from alpaca.common.requests import NonEmptyRequest
from alpaca.trading.enums import (
    AssetClass,
    AssetExchange,
    AssetStatus,
    ContractType,
    CorporateActionDateType,
    CorporateActionType,
    ExerciseStyle,
    OrderClass,
    OrderSide,
    OrderType,
    PositionIntent,
    QueryOrderStatus,
    TimeInForce,
)


class ClosePositionRequest(NonEmptyRequest):
    """
    Attributes:
        qty (str): The number of shares to liquidate.
        percentage (str): The percentage of shares to liquidate.
    """

    qty: Optional[str] = None
    percentage: Optional[str] = None

    @model_validator(mode="before")
    def root_validator(cls, values: dict) -> dict:
        qty = values.get("qty", None)
        percentage = values.get("percentage", None)
        if qty is None and percentage is None:
            raise ValueError(
                "qty or percentage must be given to the ClosePositionRequest, got None for both."
            )

        if qty is not None and percentage is not None:
            raise ValueError(
                "Only one of qty or percentage must be given to the ClosePositionRequest, got both."
            )

        return values


class GetPortfolioHistoryRequest(NonEmptyRequest):
    """
    Attributes:
        period (Optional[str]): The duration of the data in number + unit, such as 1D. unit can be D for day, W for
          week, M for month and A for year. Defaults to 1M.
        timeframe (Optional[str]): The resolution of time window. 1Min, 5Min, 15Min, 1H, or 1D. If omitted, 1Min for
          less than 7 days period, 15Min for less than 30 days, or otherwise 1D.
        intraday_reporting (Optional[str]): this specfies which timestamps to return data points
        start (Optional[datetime]): The timestamp the data is returned starting from in RFC3339 format (including timezone specification).
        pnl_reset (Optional[str]): efines how we are calculating the baseline values for Profit And Loss (pnl) for queries with timeframe less than 1D (intraday queries).
        end (Optional[datetime]): The timestamp the data is returned up to in RFC3339 format (including timezone specification).
        date_end (Optional[date]): The date the data is returned up to. Defaults to the current market date (rolls over
          at the market open if extended_hours is false, otherwise at 7am ET).
        extended_hours (Optional[bool]): If true, include extended hours in the result. This is effective only for
          timeframe less than 1D.
        cashflow_types (Optional[str]): The cashflow activities to include in the report
    """

    period: Optional[str] = None
    timeframe: Optional[str] = None
    intraday_reporting: Optional[str] = None
    start: Optional[datetime] = None
    pnl_reset: Optional[str] = None
    end: Optional[datetime] = None
    date_end: Optional[date] = None
    extended_hours: Optional[bool] = None
    cashflow_types: Optional[str] = None


class GetCalendarRequest(NonEmptyRequest):
    """
    Represents the optional filtering you can do when requesting a Calendar object
    """

    start: Optional[date] = None
    end: Optional[date] = None


class CreateWatchlistRequest(NonEmptyRequest):
    """
    Represents the fields you can specify when creating a Watchlist

    Attributes:
        name(str): Name of the Watchlist
        symbols(List[str]): Symbols of Assets to watch
    """

    name: str
    symbols: List[str]


class UpdateWatchlistRequest(NonEmptyRequest):
    """
    Represents the fields you can specify when updating a Watchlist

    Attributes:
        name(Optional[str]): Name of the Watchlist
        symbols(Optional[List[str]]): Symbols of Assets to watch
    """

    name: Optional[str] = None
    symbols: Optional[List[str]] = None

    @model_validator(mode="before")
    def root_validator(cls, values: dict) -> dict:
        if ("name" not in values or values["name"] is None) and (
            "symbols" not in values or values["symbols"] is None
        ):
            raise ValueError("One of 'name' or 'symbols' must be defined")

        return values


class GetAssetsRequest(NonEmptyRequest):
    """
    When querying for available assets, this model provides the parameters that can be filtered by.

    Attributes:
        status (Optional[AssetStatus]): The active status of the asset.
        asset_class (Optional[AssetClass]): The type of asset (i.e. us_equity, crypto).
        exchange (Optional[AssetExchange]): The exchange the asset trades on.
        attributes (Optional[str]): Comma separated values to query for more than one attribute.
    """

    status: Optional[AssetStatus] = None
    asset_class: Optional[AssetClass] = None
    exchange: Optional[AssetExchange] = None
    attributes: Optional[str] = None


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


class OptionLegRequest(NonEmptyRequest):
    """
    Used for providing details for a leg of a multi-leg order.

    Attributes:
        symbol (str): The symbol identifier for the asset being traded.
        ratio_qty (float): The proportional quantity of this leg in relation to the overall multi-leg order quantity.
        side (Optional[OrderSide]): Represents the side this order was on.
        position_intent (Optional[PositionIntent]): Represents the position strategy for this leg.
    """

    symbol: str
    ratio_qty: float
    side: Optional[OrderSide] = None
    position_intent: Optional[PositionIntent] = None

    @model_validator(mode="before")
    def root_validator(cls, values: dict) -> dict:
        side = values.get("side", None)
        position_intent = values.get("position_intent", None)

        if side is None and position_intent is None:
            raise ValueError(
                "at least one of side or position_intent must be provided for OptionLegRequest"
            )

        return values


class GetOrdersRequest(NonEmptyRequest):
    """Contains data for submitting a request to retrieve orders.

    Attributes:
        status (Optional[QueryOrderStatus]): Order status to be queried. open, closed or all. Defaults to open. Not same as OrderStatus property of Order.
        limit (Optional[int]): The maximum number of orders in response. Defaults to 50 and max is 500.
        after (Optional[datetime]): The response will include only ones submitted after this timestamp.
        until (Optional[datetime]): The response will include only ones submitted until this timestamp.
        direction (Optional[Sort]): The chronological order of response based on the submission time. asc or desc. Defaults to desc.
        nested (Optional[bool]): If true, the result will roll up multi-leg orders under the legs field of primary order.
        side (Optional[OrderSide]): Filters down to orders that have a matching side field set.
        symbols (Optional[List[str]]): List of symbols to filter by.
    """

    status: Optional[QueryOrderStatus] = None
    limit: Optional[int] = None  # not pagination = None
    after: Optional[datetime] = None
    until: Optional[datetime] = None
    direction: Optional[Sort] = None
    nested: Optional[bool] = None
    side: Optional[OrderSide] = None
    symbols: Optional[List[str]] = None


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

    qty: Optional[int] = None
    time_in_force: Optional[TimeInForce] = None
    limit_price: Optional[float] = None
    stop_price: Optional[float] = None
    trail: Optional[float] = None
    client_order_id: Optional[str] = None

    @model_validator(mode="before")
    def root_validator(cls, values: dict) -> dict:
        qty = values.get("qty", None)
        limit_price = values.get("limit_price", None)
        stop_price = values.get("stop_price", None)
        trail = values.get("trail", None)

        if (qty is not None) and (qty <= 0):
            raise ValueError("qty must be greater than 0")
        if (stop_price is not None) and (stop_price <= 0):
            raise ValueError("stop_price must be greater than 0")
        if (trail is not None) and (trail <= 0):
            raise ValueError("trail must be greater than 0")

        return values


class CancelOrderResponse(ModelWithID):
    """
    Data returned after requesting to cancel an order. It contains the cancel status of an order.

    Attributes:
        id (UUID): The order id
        status (int): The HTTP status returned after attempting to cancel the order.
        body (Dict[str, Any]): an error description
    """

    status: int
    body: Optional[Dict[str, Any]] = None


class OrderRequest(NonEmptyRequest):
    """A base class for requests for creating an order. You probably shouldn't directly use
    this class when submitting an order. Instead, use one of the order type specific classes.

    Attributes:
        symbol (str): The symbol identifier for the asset being traded. Required for all order classes other than
            mleg.
        qty (Optional[float]): The number of shares to trade. Fractional qty for stocks only with market orders.
            Required for mleg order class.
        notional (Optional[float]): The base currency value of the shares to trade. For stocks, only works with MarketOrders.
            **Does not work with qty**.
        side (Optional[OrderSide]): Whether the order will buy or sell the asset. Either side or position_intent is required for all order classes other than mleg.
        type (OrderType): The execution logic type of the order (market, limit, etc).
        time_in_force (TimeInForce): The expiration logic of the order.
        extended_hours (Optional[float]): Whether the order can be executed during regular market hours.
        client_order_id (Optional[str]): A string to identify which client submitted the order.
        order_class (Optional[OrderClass]): The class of the order. Simple orders have no other legs.
        legs (Optional[List[OptionLegRequest]]): For multi-leg option orders, the legs of the order If specified (must contain at least 2 but no more than 4 legs for options).
            Otherwise, for equities, a list of individual orders.
        take_profit (Optional[TakeProfitRequest]): For orders with multiple legs, an order to exit a profitable trade.
        stop_loss (Optional[StopLossRequest]): For orders with multiple legs, an order to exit a losing trade.
        position_intent (Optional[PositionIntent]): An enum to indicate the desired position strategy: BTO, BTC, STO, STC.
    """

    symbol: Optional[str] = None
    qty: Optional[float] = None
    notional: Optional[float] = None
    side: Optional[OrderSide] = None
    type: OrderType
    time_in_force: TimeInForce
    order_class: Optional[OrderClass] = None
    extended_hours: Optional[bool] = None
    client_order_id: Optional[str] = None
    legs: Optional[List[OptionLegRequest]] = None
    take_profit: Optional[TakeProfitRequest] = None
    stop_loss: Optional[StopLossRequest] = None
    position_intent: Optional[PositionIntent] = None

    @model_validator(mode="before")
    def root_validator(cls, values: dict) -> dict:
        qty_set = "qty" in values and values["qty"] is not None
        notional_set = "notional" in values and values["notional"] is not None

        if not qty_set and not notional_set:
            raise ValueError("At least one of qty or notional must be provided")
        elif qty_set and notional_set:
            raise ValueError("Both qty and notional can not be set.")

        # mleg-related checks
        if "order_class" in values and values["order_class"] == OrderClass.MLEG:
            if not qty_set:
                raise ValueError("qty is required for the mleg order class.")
            if "legs" not in values or values["legs"] is None:
                raise ValueError("legs is required for the mleg order class.")
            l_len = len(values["legs"])
            if l_len > 4:
                raise ValueError("At most 4 legs are allowed for the mleg order class.")
            if l_len < 2:
                raise ValueError(
                    "At least 2 legs are required for the mleg order class."
                )
            n_unique = len(set([l.symbol for l in values["legs"]]))
            if n_unique != l_len:
                raise ValueError("All legs must have unique symbols.")
        else:
            if "symbol" not in values or values["symbol"] is None:
                raise ValueError(
                    "symbol is required for all order classes other than mleg."
                )
            if "side" not in values or values["side"] is None:
                raise ValueError(
                    "side is required for all order classes other than mleg."
                )

        return values


class MarketOrderRequest(OrderRequest):
    """
    Used to submit a market order.

    Attributes:
        symbol (str): The symbol identifier for the asset being traded. Required for all order classes other than
            mleg.
        qty (Optional[float]): The number of shares to trade. Fractional qty for stocks only with market orders.
        notional (Optional[float]): The base currency value of the shares to trade. For stocks, only works with MarketOrders.
            **Does not work with qty**.
        side (OrderSide): Whether the order will buy or sell the asset. Required for all order classes other than mleg.
        type (OrderType): The execution logic type of the order (market, limit, etc).
        time_in_force (TimeInForce): The expiration logic of the order.
        extended_hours (Optional[float]): Whether the order can be executed during regular market hours.
        client_order_id (Optional[str]): A string to identify which client submitted the order.
        order_class (Optional[OrderClass]): The class of the order. Simple orders have no other legs.
        legs (Optional[List[OptionLegRequest]]): For multi-leg option orders, the legs of the order. At most 4 legs are allowed for options.
        take_profit (Optional[TakeProfitRequest]): For orders with multiple legs, an order to exit a profitable trade.
        stop_loss (Optional[StopLossRequest]): For orders with multiple legs, an order to exit a losing trade.
        position_intent (Optional[PositionIntent]): An enum to indicate the desired position strategy: BTO, BTC, STO, STC.
    """

    def __init__(self, **data: Any) -> None:
        data["type"] = OrderType.MARKET

        super().__init__(**data)


class StopOrderRequest(OrderRequest):
    """
    Used to submit a stop order.

    Attributes:
        symbol (str): The symbol identifier for the asset being traded
        qty (Optional[float]): The number of shares to trade. Fractional qty for stocks only with market orders.
        notional (Optional[float]): The base currency value of the shares to trade. For stocks, only works with MarketOrders.
            **Does not work with qty**.
        side (OrderSide): Whether the order will buy or sell the asset.
        type (OrderType): The execution logic type of the order (market, limit, etc).
        time_in_force (TimeInForce): The expiration logic of the order.
        extended_hours (Optional[float]): Whether the order can be executed during regular market hours.
        client_order_id (Optional[str]): A string to identify which client submitted the order.
        order_class (Optional[OrderClass]): The class of the order. Simple orders have no other legs.
        legs (Optional[List[OptionLegRequest]]): For multi-leg option orders, the legs of the order. At most 4 legs are allowed for options.
        take_profit (Optional[TakeProfitRequest]): For orders with multiple legs, an order to exit a profitable trade.
        stop_loss (Optional[StopLossRequest]): For orders with multiple legs, an order to exit a losing trade.
        stop_price (float): The price at which the stop order is converted to a market order or a stop limit
            order is converted to a limit order.
        position_intent (Optional[PositionIntent]): An enum to indicate the desired position strategy: BTO, BTC, STO, STC.
    """

    stop_price: float

    def __init__(self, **data: Any) -> None:
        data["type"] = OrderType.STOP

        super().__init__(**data)


class LimitOrderRequest(OrderRequest):
    """
    Used to submit a limit order.

    Attributes:
        symbol (str): The symbol identifier for the asset being traded
        qty (Optional[float]): The number of shares to trade. Fractional qty for stocks only with market orders.
        notional (Optional[float]): The base currency value of the shares to trade. For stocks, only works with MarketOrders.
            **Does not work with qty**.
        side (OrderSide): Whether the order will buy or sell the asset.
        type (OrderType): The execution logic type of the order (market, limit, etc).
        time_in_force (TimeInForce): The expiration logic of the order.
        extended_hours (Optional[float]): Whether the order can be executed during regular market hours.
        client_order_id (Optional[str]): A string to identify which client submitted the order.
        order_class (Optional[OrderClass]): The class of the order. Simple orders have no other legs.
        legs (Optional[List[OptionLegRequest]]): For multi-leg option orders, the legs of the order. At most 4 legs are allowed for options.
        take_profit (Optional[TakeProfitRequest]): For orders with multiple legs, an order to exit a profitable trade.
        stop_loss (Optional[StopLossRequest]): For orders with multiple legs, an order to exit a losing trade.
        limit_price (Optional[float]): The worst fill price for a limit or stop limit order. For the mleg order class, this
            is specified such that a positive value indicates a debit (representing a cost or payment to be made) while a
            negative value signifies a credit (reflecting an amount to be received).
        position_intent (Optional[PositionIntent]): An enum to indicate the desired position strategy: BTO, BTC, STO, STC.
    """

    limit_price: Optional[float] = None

    def __init__(self, **data: Any) -> None:
        data["type"] = OrderType.LIMIT

        super().__init__(**data)

    @model_validator(mode="before")
    def root_validator(cls, values: dict) -> dict:
        # noinspection PyCallingNonCallable
        super().root_validator(values)
        if values.get("order_class", "") != OrderClass.OCO:
            limit_price = values.get("limit_price", None)
            if limit_price is None:
                raise ValueError("limit_price is required")
        return values


class StopLimitOrderRequest(OrderRequest):
    """
    Used to submit a stop limit order.

    Attributes:
        symbol (str): The symbol identifier for the asset being traded
        qty (Optional[float]): The number of shares to trade. Fractional qty for stocks only with market orders.
        notional (Optional[float]): The base currency value of the shares to trade. For stocks, only works with MarketOrders.
            **Does not work with qty**.
        side (OrderSide): Whether the order will buy or sell the asset.
        type (OrderType): The execution logic type of the order (market, limit, etc).
        time_in_force (TimeInForce): The expiration logic of the order.
        extended_hours (Optional[float]): Whether the order can be executed during regular market hours.
        client_order_id (Optional[str]): A string to identify which client submitted the order.
        order_class (Optional[OrderClass]): The class of the order. Simple orders have no other legs.
        legs (Optional[List[OptionLegRequest]]): For multi-leg option orders, the legs of the order. At most 4 legs are allowed for options.
        take_profit (Optional[TakeProfitRequest]): For orders with multiple legs, an order to exit a profitable trade.
        stop_loss (Optional[StopLossRequest]): For orders with multiple legs, an order to exit a losing trade.
        stop_price (float): The price at which the stop order is converted to a market order or a stop limit
            order is converted to a limit order.
        limit_price (float): The worst fill price for a limit or stop limit order. For the mleg order class, this
            is specified such that a positive value indicates a debit (representing a cost or payment to be made) while a
            negative value signifies a credit (reflecting an amount to be received).
        position_intent (Optional[PositionIntent]): An enum to indicate the desired position strategy: BTO, BTC, STO, STC.
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
        symbol (str): The symbol identifier for the asset being traded
        qty (Optional[float]): The number of shares to trade. Fractional qty for stocks only with market orders.
        notional (Optional[float]): The base currency value of the shares to trade. For stocks, only works with MarketOrders.
            **Does not work with qty**.
        side (OrderSide): Whether the order will buy or sell the asset.
        type (OrderType): The execution logic type of the order (market, limit, etc).
        time_in_force (TimeInForce): The expiration logic of the order.
        extended_hours (Optional[float]): Whether the order can be executed during regular market hours.
        client_order_id (Optional[str]): A string to identify which client submitted the order.
        order_class (Optional[OrderClass]): The class of the order. Simple orders have no other legs.
        legs (Optional[List[OptionLegRequest]]): For multi-leg option orders, the legs of the order. At most 4 legs are allowed for options.
        take_profit (Optional[TakeProfitRequest]): For orders with multiple legs, an order to exit a profitable trade.
        stop_loss (Optional[StopLossRequest]): For orders with multiple legs, an order to exit a losing trade.
        trail_price (Optional[float]): The absolute price difference by which the trailing stop will trail.
        trail_percent (Optional[float]): The percent price difference by which the trailing stop will trail.
        position_intent (Optional[PositionIntent]): An enum to indicate the desired position strategy: BTO, BTC, STO, STC.
    """

    trail_price: Optional[float] = None
    trail_percent: Optional[float] = None

    def __init__(self, **data: Any) -> None:
        data["type"] = OrderType.TRAILING_STOP

        super().__init__(**data)

    @model_validator(mode="before")
    def root_validator(cls, values: dict) -> dict:
        # noinspection PyCallingNonCallable
        super().root_validator(values)
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


class GetCorporateAnnouncementsRequest(NonEmptyRequest):
    """
    Contains parameters for querying corporate action data.
    Attributes:
        ca_types (List[CorporateActionType]): A list of corporate action types.
        since (date): The start (inclusive) of the date range when searching corporate action announcements.
            The date range is limited to 90 days.
        until (date): The end (inclusive) of the date range when searching corporate action announcements.
            The date range is limited to 90 days.
        symbol (Optional[str]): The symbol of the company initiating the announcement.
        cusip (Optional[str]): The CUSIP of the company initiating the announcement.
        date_type (Optional[CorporateActionDateType]): The date type for the announcement.
    """

    ca_types: List[CorporateActionType]
    since: date
    until: date
    symbol: Optional[str] = None
    cusip: Optional[str] = None
    date_type: Optional[CorporateActionDateType] = None

    @model_validator(mode="before")
    def root_validator(cls, values: dict) -> dict:
        since = pd.Timestamp(values.get("since")).date()
        until = pd.Timestamp(values.get("until")).date()

        if (
            since is not None
            and until is not None
            and (until - since) > timedelta(days=90)
        ):
            raise ValueError("The date range is limited to 90 days.")

        return values


class GetOptionContractsRequest(NonEmptyRequest):
    """
    Used to fetch option contracts for a given underlying symbol.

    Attributes:
        underlying_symbols (Optional[List[str]]): The underlying symbols for the option contracts to be returned. (e.g. ["AAPL", "SPY"])
        status (Optional[AssetStatus]): The status of the asset.
        expiration_date (Optional[Union[date, str]]): The expiration date of the option contract. (YYYY-MM-DD)
        expiration_date_gte (Optional[Union[date, str]]): The expiration date of the option contract greater than or equal to. (YYYY-MM-DD)
        expiration_date_lte (Optional[Union[date, str]]): The expiration date of the option contract less than or equal to. (YYYY-MM-DD)
        root_symbol (Optional[str]): The option root symbol.
        type (Optional[ContractType]): The option contract type.
        style (Optional[ExerciseStyle]): The option contract style.
        strike_price_gte (Optional[str]): The option contract strike price greater than or equal to.
        strike_price_lte (Optional[str]): The option contract strike price less than or equal to.
        limit (Optional[int]): The number of contracts to limit per page (default=100, max=10000).
        page_token (Optional[str]): Pagination token to continue from. The value to pass here is returned in specific
            requests when more data is available than the request limit allows.
    """

    underlying_symbols: Optional[List[str]] = None
    status: Optional[AssetStatus] = AssetStatus.ACTIVE
    expiration_date: Optional[Union[date, str]] = None
    expiration_date_gte: Optional[Union[date, str]] = None
    expiration_date_lte: Optional[Union[date, str]] = None
    root_symbol: Optional[str] = None
    type: Optional[ContractType] = None
    style: Optional[ExerciseStyle] = None
    strike_price_gte: Optional[str] = None
    strike_price_lte: Optional[str] = None

    limit: Optional[int] = None
    page_token: Optional[str] = None
