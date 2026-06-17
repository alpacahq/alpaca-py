from alpaca.common.models import ModelWithID, ValidateBaseModel as BaseModel
from uuid import UUID
from datetime import datetime, date
from typing import Any, Literal, Optional, List, Union, Dict
from alpaca.trading.enums import (
    AssetBorrowStatus,
    AssetClass,
    AssetStatus,
    AssetExchange,
    ContractType,
    DTBPCheck,
    ExerciseStyle,
    LocateStatus,
    OrderStatus,
    OrderType,
    OrderClass,
    PDTCheck,
    PositionIntent,
    TimeInForce,
    OrderSide,
    PositionSide,
    AccountStatus,
    TradeActivityType,
    NonTradeActivityStatus,
    ActivityType,
    CorporateActionType,
    CorporateActionSubType,
    TradeConfirmationEmail,
    TradeEvent,
    ActivitySubType,
    ExecutionType,
    AdvancedInstructionsAlgorithm,
    AdvancedInstructionsDestination,
    LocateErrorCode,
    LocateQuoteErrorCode,
    TransferDirection,
    CryptoTransferStatus,
    OptionDeliverableType,
    OptionDeliverableSettlementType,
    OptionDeliverableSettlementMethod,
    TokenizationIssuer,
    TokenizationNetwork,
    TokenizationRequestType,
    TokenizationRequestStatus,
    WhitelistedAddressStatus,
    Phase,
    Market,
    SpOutlook,
    TreasurySubtype,
    BondStatus,
    CouponType,
    CouponFrequency,
    DayCount,
    CallType,
)
from pydantic import Field, model_validator


class Asset(ModelWithID):
    """
    Represents a security. Some Assets are not tradable with Alpaca. These Assets are
    marked with the flag `tradable=false`.

    For more info, visit https://alpaca.markets/docs/api-references/trading-api/assets/

    Attributes:
        id (UUID): Unique id of asset.
        asset_class (AssetClass): The name of the asset class (spec field: ``class``).
        cusip (Optional[str]): CUSIP identifier for US Equities.
        exchange (AssetExchange): Which exchange this asset is available through.
        symbol (str): The symbol identifier of the asset.
        name (str): The official name of the asset.
        status (AssetStatus): The active status of the asset.
        tradable (bool): Whether the asset can be traded.
        marginable (bool): Whether the asset can be traded on margin.
        shortable (bool): Whether the asset can be shorted.
        easy_to_borrow (bool): Deprecated. Use ``borrow_status`` instead.
        borrow_status (Optional[AssetBorrowStatus]): Borrow status for US equity assets.
        fractionable (bool): Whether fractional shares are available.
        margin_requirement_long (Optional[str]): Margin requirement % for long positions.
        margin_requirement_short (Optional[str]): Margin requirement % for short positions.
        maintenance_margin_requirement (Optional[float]): Deprecated. Use margin_requirement_long/short.
        attributes (Optional[List[str]]): Unique asset characteristics.
        min_order_size (Optional[Union[str, float]]): Minimum order size. Field available for crypto only.
        min_trade_increment (Optional[Union[str, float]]): Amount a trade quantity can be incremented by. Field available for crypto only.
        price_increment (Optional[Union[str, float]]): Amount the price can be incremented by. Field available for crypto only.
    """

    asset_class: AssetClass = Field(
        alias="class"
    )  # using a pydantic alias to allow parsing data with the `class` keyword field
    cusip: Optional[str] = None
    exchange: AssetExchange
    symbol: str
    name: str
    status: AssetStatus
    tradable: bool
    marginable: bool
    shortable: bool
    easy_to_borrow: bool
    borrow_status: Optional[AssetBorrowStatus] = None
    fractionable: bool
    margin_requirement_long: Optional[str] = None
    margin_requirement_short: Optional[str] = None
    maintenance_margin_requirement: Optional[float] = None
    attributes: Optional[List[str]] = None
    # SDK-extension fields: not in the spec but retained for backward compatibility.
    min_order_size: Optional[Union[str, float]] = None
    min_trade_increment: Optional[Union[str, float]] = None
    price_increment: Optional[Union[str, float]] = None


class USDPositionValues(BaseModel):
    """
    Represents an open long or short holding in an asset in USD.

    Attributes:
        avg_entry_price (str): The average entry price of the position.
        market_value (Optional[str]): Total dollar amount of the position.
        cost_basis (str): Total cost basis in dollars.
        unrealized_pl (Optional[str]): Unrealized profit/loss in dollars.
        unrealized_plpc (Optional[str]): Unrealized profit/loss percent.
        unrealized_intraday_pl (Optional[str]): Unrealized profit/loss in dollars for the day.
        unrealized_intraday_plpc (Optional[str]): Unrealized profit/loss percent for the day.
        current_price (Optional[str]): Current asset price per share.
        lastday_price (Optional[str]): Last day’s asset price per share based on the closing value of the last trading day.
        change_today (Optional[str]): Percent change from last day's price.

    """

    avg_entry_price: str
    market_value: Optional[str]
    cost_basis: str
    unrealized_pl: Optional[str]
    unrealized_plpc: Optional[str]
    unrealized_intraday_pl: Optional[str]
    unrealized_intraday_plpc: Optional[str]
    current_price: Optional[str]
    lastday_price: Optional[str]
    change_today: Optional[str]


class Position(BaseModel):
    """
    Represents an open long or short holding in an asset.

    Attributes:
        asset_id (UUID): ID of the asset.
        symbol (str): Symbol of the asset.
        exchange (AssetExchange): Exchange name of the asset.
        asset_class (AssetClass): Name of the asset's asset class.
        asset_marginable (bool): Indicates if this asset is marginable.
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
        swap_rate (Optional[str]): Swap rate is the exchange rate (without mark-up) used to convert the price into local currency or crypto asset.
        avg_entry_swap_rate (Optional[str]): The average exchange rate the price was converted into the local currency at.
        prev_swap_rate (Optional[str]): The average exchange rate the price was converted into the local currency at.
        usd (USDPositionValues): Represents the position in USD values.
        qty_available (Optional[str]): Total number of shares available minus open orders.

    """

    asset_id: UUID
    symbol: str
    exchange: AssetExchange
    asset_class: AssetClass
    asset_marginable: bool
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
    swap_rate: Optional[str] = None
    avg_entry_swap_rate: Optional[str] = None
    prev_swap_rate: Optional[str] = None
    usd: Optional[USDPositionValues] = None
    qty_available: Optional[str] = None


class AllAccountsPositions(BaseModel):
    """
    Represents the positions of every account as of last market close.

    Attributes:
        as_of (datetime): Timestamp for which the positions are returned.
        positions (Dict[str, List[Position]]): Positions held by an account, keyed by account_id.
    """

    as_of: datetime
    positions: Dict[str, List[Position]]


class Order(ModelWithID):
    """
    Represents a request for the sale or purchase of an asset.

    Attributes:
        id (Optional[UUID]): order ID generated by Alpaca.
        client_order_id (Optional[str]): Client unique order ID
        created_at (Optional[datetime]): Timestamp when the order was created.
        updated_at (Optional[datetime]): Timestamp when the order was last updated.
        submitted_at (Optional[datetime]): Timestamp when the order was submitted.
        filled_at (Optional[datetime]): Timestamp when the order was filled.
        expired_at (Optional[datetime]): Timestamp when the order expired at.
        expires_at (Optional[datetime]): An auto cancel request will be triggered after this timestamp.
        canceled_at (Optional[datetime]): Timestamp when the order was canceled.
        failed_at (Optional[datetime]): Timestamp when the order failed at.
        replaced_at (Optional[datetime]): Timestamp when the order was replaced by a new order.
        replaced_by (Optional[UUID]): ID of order that replaces this order.
        replaces (Optional[UUID]): ID of order which this order replaces.
        asset_id (Optional[UUID]): ID of the asset. Omitted from top-level of response if the order is of mleg class.
        symbol (Optional[str]): Symbol of the asset. Omitted from top-level of response if the order is of mleg class.
        asset_class (Optional[AssetClass]): Asset class of the asset. Omitted from top-level of response if the order is of mleg class.
        notional (Optional[str]): Ordered notional amount. If entered, qty will be null. Can take up to 9 decimal
          points.
        qty (Optional[Union[str, float]]): Ordered quantity. If entered, notional will be null. Can take up to 9 decimal points.
        filled_qty (Optional[str]): Filled quantity.
        filled_avg_price (Optional[str]): Filled average price. Can be 0 until order is processed in case order is
          passed outside of market hours.
        order_class (Optional[OrderClass]): Valid values: simple, bracket, oco or oto.
        order_type (Optional[OrderType]): Deprecated with just type field below. Omitted from legs of mleg orders.
        type (OrderType): Valid values: market, limit, stop, stop_limit, trailing_stop. Omitted from legs of mleg orders.
        side (Optional[OrderSide]): Valid values: buy and sell. Omitted from top-level of response if the order is of mleg class.
        time_in_force (TimeInForce): Length of time the order is in force.
        limit_price (Optional[str]): Limit price of the order.
        stop_price (Optional[str]): Stop price of the order.
        status (Optional[OrderStatus]): The status of the order.
        extended_hours (Optional[bool]): If true, eligible for execution outside regular trading hours.
        legs (Optional[List[alpaca.trading.models.Order]]): When querying non-simple order_class orders in a nested style,
          an array of order entities associated with this order. Otherwise, null.
        trail_percent (Optional[str]): The percent value away from the high water mark for trailing stop orders.
        trail_price (Optional[str]): The dollar value away from the high water mark for trailing stop orders.
        hwm (Optional[str]): The highest (lowest) market price seen since the trailing stop order was submitted.
        position_intent  (Optional[PositionIntent]): Represents the desired position strategy.
        ratio_qty (Optional[str]): The proportional quantity of this leg in relation to the overall multi-leg order quantity.
    """

    id: Optional[UUID] = None
    client_order_id: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    submitted_at: Optional[datetime] = None
    filled_at: Optional[datetime] = None
    expired_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    canceled_at: Optional[datetime] = None
    failed_at: Optional[datetime] = None
    replaced_at: Optional[datetime] = None
    replaced_by: Optional[UUID] = None
    replaces: Optional[UUID] = None
    asset_id: Optional[UUID] = None
    symbol: Optional[str] = None
    asset_class: Optional[AssetClass] = None
    notional: Optional[str]
    qty: Optional[Union[str, float]] = None
    filled_qty: Optional[Union[str, float]] = None
    filled_avg_price: Optional[Union[str, float]] = None
    order_class: Optional[OrderClass] = None
    order_type: Optional[OrderType] = None
    type: OrderType
    side: Optional[OrderSide] = None
    time_in_force: TimeInForce
    limit_price: Optional[Union[str, float]] = None
    stop_price: Optional[Union[str, float]] = None
    status: Optional[OrderStatus] = None
    extended_hours: Optional[bool] = None
    legs: Optional[List["OrderLeg"]] = None
    trail_percent: Optional[str] = None
    trail_price: Optional[str] = None
    hwm: Optional[str] = None
    position_intent: Optional[PositionIntent] = None
    ratio_qty: Optional[Union[str, float]] = None

    def __init__(self, **data: Any) -> None:
        if "order_class" not in data or data["order_class"] == "":
            data["order_class"] = OrderClass.SIMPLE

        # mleg responses will give ''s that will need to be converted to None
        # to avoid validation errors from pydantic
        for k in [
            "asset_id",
            "symbol",
            "asset_class",
            "side",
            "position_intent",
            "type",
            "order_type",
        ]:
            if k in data and data[k] == "":
                data[k] = None

        super().__init__(**data)


class FailedClosePositionDetails(BaseModel):
    """API response for failed close position request.

    Attributes:
        available (float): The qty available.
        code (int): The status code.
        existing_qty (float): The total qty in account.
        held_for_orders (float): The qty locked up in existing orders.
        message (str): Message for failed request.
        symbol (str): The symbol for the request.
    """

    code: int
    message: str
    available: Optional[float] = None
    existing_qty: Optional[float] = None
    held_for_orders: Optional[float] = None
    symbol: Optional[str] = None


class ClosePositionResponse(BaseModel):
    """API response for a close position request.
    Attributes:
        order_id (Optional[UUID]): ID of order that was created to liquidate the position.
        status (Optional[int]): Status code corresponding to the request to liquidate the position.
        symbol (Optional[str]): The symbol of the position being closed.
        body (Optional[dict]): Information relating to the successful or unsuccessful closing of the position.
    """

    order_id: Optional[UUID] = None
    status: Optional[int] = None
    symbol: Optional[str] = None
    body: Union[FailedClosePositionDetails, Order]


class PortfolioHistory(BaseModel):
    """
    Contains information about the value of a portfolio over time.

    Attributes:
        timestamp (List[int]): Time of each data element, left-labeled (the beginning of time window).
        equity (List[float]): Equity value of the account in dollar amount as of the end of each time window.
        profit_loss (List[float]): Profit/loss in dollar from the base value.
        profit_loss_pct (List[Optional[float]]): Profit/loss in percentage from the base value.
        base_value (float): Basis in dollar of the profit loss calculation.
        base_value_asof (Optional[date]): If included, then it indicates that the base_value is the account's closing equity value at this trading date.
        timeframe (str): Time window size of each data element.
        cashflow (Optional[Dict[ActivityType, List[float]]]): Cash flow amounts per activity type, if any.
    """

    timestamp: List[int]
    equity: List[float]
    profit_loss: List[float]
    profit_loss_pct: List[Optional[float]]
    base_value: float
    base_value_asof: Optional[date] = None
    timeframe: str
    cashflow: Optional[Dict[ActivityType, List[float]]] = {}


class Watchlist(ModelWithID):
    """
    A watchlist is an ordered list of assets. An account can have multiple watchlists.
    Learn more about watchlists in the documentation. https://alpaca.markets/docs/api-references/trading-api/watchlist/

    Attributes:
        account_id (UUID): The uuid identifying the account the watchlist belongs to
        id (UUID): The unique identifier for the watchlist
        name (str): An arbitrary string up to 64 characters identifying the watchlist
        created_at (datetime): When the watchlist was created
        updated_at (datetime): When the watchlist was last updated
        assets (Optional[List[Asset]]): The assets in the watchlist, not returned from all endpoints
    """

    account_id: UUID
    name: str
    created_at: datetime
    updated_at: datetime
    assets: Optional[List[Asset]] = None


class Clock(BaseModel):
    """
    The market clock for US equity markets. Timestamps are in eastern time.

    Attributes:
        timestamp (datetime): The current timestamp.
        is_open (bool): Whether the market is currently open.
        next_open (datetime): The timestamp when the market will next open.
        next_close (datetime): The timestamp when the market will next close.
    """

    timestamp: datetime
    is_open: bool
    next_open: datetime
    next_close: datetime


class Calendar(BaseModel):
    """
    The market calendar for equity markets. Describes the market open and close time on a given day.
    """

    date: date
    open: datetime
    close: datetime

    def __init__(self, **data: Any) -> None:
        """
            Converts open and close time strings from %H:%M to a datetime
        Args:
            **data: The raw calendar data from API
        """
        if "date" in data and "open" in data:
            start_datetime_str = data["date"] + " " + data["open"]
            data["open"] = datetime.strptime(start_datetime_str, "%Y-%m-%d %H:%M")

        if "date" in data and "close" in data:
            start_datetime_str = data["date"] + " " + data["close"]
            data["close"] = datetime.strptime(start_datetime_str, "%Y-%m-%d %H:%M")

        super().__init__(**data)


class BaseActivity(BaseModel):
    """
    Represents Base information for an event/activity for a specific Account.

    You most likely will want an instance of one of the child classes TradeActivity and NonTradeActivity

    Attributes:
        id (str): Unique ID of this Activity. Note that IDs for Activity instances are formatted like
          `20220203000000000::045b3b8d-c566-4bef-b741-2bf598dd6ae7` the first part before the `::` is a date string
          while the part after is a UUID
        account_id (UUID): id of the Account this activity relates too
        activity_type (ActivityType): What specific kind of Activity this was
    """

    id: str
    account_id: UUID
    activity_type: ActivityType

    def __init__(self, *args, **data):
        if "account_id" in data and type(data["account_id"]) == str:
            data["account_id"] = UUID(data["account_id"])

        super().__init__(*args, **data)


class NonTradeActivity(BaseActivity):
    """
    A NonTradeActivity represents an Activity that happened for an account that doesn't have to do with orders or trades.

    Attributes:
        date (date): The date on which the activity occurred or on which the transaction associated with the
          activity settled.
        net_amount (float): The net amount of money (positive or negative) associated with the activity.
        description (str): Extra description of the NTA if needed. Can be empty string ""
        status (NonTradeActivityStatus): Status of the activity. Not present for all activity types.
        symbol (Optional[str]): The symbol of the security involved with the activity. Not present for all activity
          types.
        qty (Optional[float]): For dividend activities, the number of shares that contributed to the payment. Not
          present for other activity types.
        price (Optional[float]) Not present for all activity types.
        per_share_amount (Optional[float]): For dividend activities, the average amount paid per share. Not present for
          other activity types.
    """

    date: date
    net_amount: float
    description: str
    status: Optional[NonTradeActivityStatus] = None
    symbol: Optional[str] = None
    qty: Optional[float] = None
    price: Optional[float] = None
    per_share_amount: Optional[float] = None


class TradeActivity(BaseActivity):
    """
    Represents information for TradeActivities. TradeActivities are Activities that pertain to trades that happened for
    an account. IE Fills or partial fills for orders.

    Attributes:
        transaction_time (datetime): The time and date of when this trade was processed
        type (TradeActivityType): What kind of trade this TradeActivity represents. See TradeActivityType for more
          details
        price (float): The per-share price that the trade was executed at.
        qty (float): The number of shares involved in the trade execution.
        side (OrderSide): What side the trade this TradeActivity represents was on. See OrderSide for more information
        symbol (str): The symbol of the asset that was traded
        leaves_qty (float): For partially filled orders, the quantity of shares that are left to be filled. Will be 0 if
          order was not a partially filled order
        order_id (UUID): The ID for the order filled
        cum_qty (float): The cumulative quantity of shares involved in the execution.
        order_status (OrderStatus): The status of the order that executed the trade. See OrderStatus for more details
    """

    transaction_time: datetime
    type: TradeActivityType
    price: float
    qty: float
    side: OrderSide
    symbol: str
    leaves_qty: float
    order_id: UUID
    cum_qty: float
    order_status: OrderStatus


class TradeAccount(ModelWithID):
    """
    Represents trading account information for an Account.

    Attributes:
        id (UUID): The account ID
        account_number (Optional[str]): The account number
        status (AccountStatus): The current status of the account
        crypto_status (Optional[AccountStatus]): The status of the account in regards to trading crypto. Only present if
          crypto trading is enabled for your brokerage account.
        currency (Optional[str]): Currently will always be the value "USD".
        buying_power (Optional[str]): Current available cash buying power. If multiplier = 2 then
          buying_power = max(equity-initial_margin(0) * 2). If multiplier = 1 then buying_power = cash.
        regt_buying_power (Optional[str]): User’s buying power under Regulation T
          (excess equity - (equity - margin value) * margin multiplier)
        daytrading_buying_power (Optional[str]): The buying power for day trades for the account
        non_marginable_buying_power (Optional[str]): The non marginable buying power for the account
        cash (Optional[str]): Cash balance in the account
        accrued_fees (Optional[str]): Fees accrued in this account
        pending_transfer_out (Optional[str]): Cash pending transfer out of this account
        pending_transfer_in (Optional[str]): Cash pending transfer into this account
        portfolio_value (str): Total value of cash + holding positions.
          (This field is deprecated. It is equivalent to the equity field.)
        pattern_day_trader (Optional[bool]): Whether the account is flagged as pattern day trader or not.
        trading_blocked (Optional[bool]): If true, the account is not allowed to place orders.
        transfers_blocked (Optional[bool]): If true, the account is not allowed to request money transfers.
        account_blocked (Optional[bool]): If true, the account activity by user is prohibited.
        created_at (Optional[datetime]): Timestamp this account was created at
        trade_suspended_by_user (Optional[bool]): If true, the account is not allowed to place orders.
        multiplier (Optional[str]): Multiplier value for this account.
        shorting_enabled (Optional[bool]): Flag to denote whether or not the account is permitted to short
        equity (Optional[str]): This value is cash + long_market_value + short_market_value. This value isn't calculated in the
          SDK it is computed on the server and we return the raw value here.
        last_equity (Optional[str]): Equity as of previous trading day at 16:00:00 ET
        long_market_value (Optional[str]): Real-time MtM value of all long positions held in the account
        short_market_value (Optional[str]): Real-time MtM value of all short positions held in the account
        initial_margin (Optional[str]): Reg T initial margin requirement
        maintenance_margin (Optional[str]): Maintenance margin requirement
        balance_asof (Optional[str]): The date of the snapshot for `last_*` fields
        last_maintenance_margin (Optional[str]): Maintenance margin requirement on the previous trading day
        sma (Optional[str]): Value of Special Memorandum Account (will be used at a later date to provide additional buying_power)
        daytrade_count (Optional[int]): The current number of daytrades that have been made in the last 5 trading days
          (inclusive of today)
        options_buying_power (Optional[str]): Your buying power for options trading
        options_approved_level (Optional[int]): The options trading level that was approved for this account.
          0=disabled, 1=Covered Call/Cash-Secured Put, 2=Long Call/Put, 3=Spreads/Straddles.
        options_trading_level (Optional[int]): The effective options trading level of the account. This is the minimum between account options_approved_level and account configurations max_options_trading_level.
          0=disabled, 1=Covered Call/Cash-Secured Put, 2=Long, 3=Spreads/Straddles.
        intraday_adjustments (Optional[str]): The intraday adjustment by non_trade_activities such as fund deposit/withdraw.
        pending_reg_taf_fees (Optional[str]): Pending regulatory fees for the account.
    """

    id: UUID
    account_number: Optional[str] = None
    status: AccountStatus
    crypto_status: Optional[AccountStatus] = None
    currency: Optional[str] = None
    buying_power: Optional[str] = None
    regt_buying_power: Optional[str] = None
    daytrading_buying_power: Optional[str] = None
    non_marginable_buying_power: Optional[str] = None
    cash: Optional[str] = None
    accrued_fees: Optional[str] = None
    pending_transfer_out: Optional[str] = None
    pending_transfer_in: Optional[str] = None
    portfolio_value: Optional[str] = None
    pattern_day_trader: Optional[bool] = None
    trading_blocked: Optional[bool] = None
    transfers_blocked: Optional[bool] = None
    account_blocked: Optional[bool] = None
    created_at: Optional[datetime] = None
    trade_suspended_by_user: Optional[bool] = None
    multiplier: Optional[str] = None
    shorting_enabled: Optional[bool] = None
    equity: Optional[str] = None
    last_equity: Optional[str] = None
    long_market_value: Optional[str] = None
    short_market_value: Optional[str] = None
    initial_margin: Optional[str] = None
    maintenance_margin: Optional[str] = None
    balance_asof: Optional[str] = None
    last_maintenance_margin: Optional[str] = None
    sma: Optional[str] = None
    daytrade_count: Optional[int] = None
    options_buying_power: Optional[str] = None
    options_approved_level: Optional[int] = None
    options_trading_level: Optional[int] = None
    intraday_adjustments: Optional[str] = None
    pending_reg_taf_fees: Optional[str] = None


class AccountConfiguration(BaseModel):
    """
    Represents configuration options for a TradeAccount.

    Attributes:
        dtbp_check (DTBPCheck): Day Trade Buying Power Check. Controls Day Trading Margin Call (DTMC) checks.
        fractional_trading (bool): If true, account is able to participate in fractional trading
        max_margin_multiplier (str): A number between 1-4 that represents your max margin multiplier
        no_shorting (bool): If true then Account becomes long-only mode.
        pdt_check (PDTCheck): Controls Pattern Day Trader (PDT) checks.
        suspend_trade (bool): If true Account becomes unable to submit new orders
        trade_confirm_email (TradeConfirmationEmail): Controls whether Trade confirmation emails are sent.
        ptp_no_exception_entry (bool): If set to true then Alpaca will accept orders for PTP symbols with no exception. Default is false.
        max_options_trading_level (Optional[int]): The desired maximum options trading level. 0=disabled, 1=Covered Call/Cash-Secured Put, 2=Long Call/Put, 3=Spreads/Straddles.
        ptp_no_exception_entry (bool): If set to true then Alpaca will accept orders for PTP symbols with no exception. Default is false.
        disable_overnight_trading (bool): If true, overnight trading is disabled.

    """

    dtbp_check: Optional[DTBPCheck] = None
    fractional_trading: Optional[bool] = None
    max_margin_multiplier: Optional[str] = None
    no_shorting: Optional[bool] = None
    pdt_check: Optional[PDTCheck] = None
    suspend_trade: Optional[bool] = None
    trade_confirm_email: Optional[TradeConfirmationEmail] = None
    ptp_no_exception_entry: Optional[bool] = None
    max_options_trading_level: Optional[int] = None
    disable_overnight_trading: Optional[bool] = None


class CorporateActionAnnouncement(ModelWithID):
    """
    An announcement of a corporate action. Corporate actions are events like dividend payouts, mergers and stock splits.

    Attributes:
        id (UUID): The unique identifier for this single announcement.
        corporate_action_id (str): ID that remains consistent across all announcements for the same corporate action.
        ca_type (CorporateActionType): The type of corporate action that was announced.
        ca_sub_type (CorporateActionSubType): The specific subtype of corporate action that was announced.
        initiating_symbol (str): Symbol of the company initiating the announcement.
        initiating_original_cusip (str): CUSIP of the company initiating the announcement.
        target_symbol (Optional[str]): Symbol of the child company involved in the announcement.
        target_original_cusip (Optional[str]): CUSIP of the child company involved in the announcement.
        declaration_date (Optional[date]): Date the corporate action or subsequent terms update was announced.
        ex_date (Optional[date]): The first date that purchasing a security will not result in a corporate action entitlement.
        record_date (Optional[date]): The date an account must hold a settled position in the security in order to receive the
            corporate action entitlement.
        payable_date (Optional[date]): The date the announcement will take effect. On this date, account stock and cash
            balances are expected to be processed accordingly.
        cash (float): The amount of cash to be paid per share held by an account on the record date.
        old_rate (float): The denominator to determine any quantity change ratios in positions.
        new_rate (float): The numerator to determine any quantity change ratios in positions.
    """

    corporate_action_id: str
    ca_type: CorporateActionType
    ca_sub_type: CorporateActionSubType
    initiating_symbol: str
    initiating_original_cusip: str
    target_symbol: Optional[str] = None
    target_original_cusip: Optional[str] = None
    declaration_date: Optional[date] = None
    ex_date: Optional[date] = None
    record_date: Optional[date] = None
    payable_date: Optional[date] = None
    cash: float
    old_rate: float
    new_rate: float


class TradeUpdate(BaseModel):
    """
    Represents a trade update.

    ref. https://docs.alpaca.markets/docs/websocket-streaming#example
    """

    event: Union[TradeEvent, str]
    execution_id: Optional[UUID] = None
    order: Order
    timestamp: datetime
    position_qty: Optional[float] = None
    price: Optional[float] = None
    qty: Optional[float] = None


class OptionContract(BaseModel):
    """
    Represents an option contract.

    Attributes:
        id (uuid): The unique identifier of the option contract.
        symbol (str): The symbol representing the option contract.
        name (str): The name of the option contract.
        status (AssetStatus): The status of the option contract.
        tradable (bool): Indicates whether the option contract is tradable.
        expiration_date (date): The expiration date of the option contract.
        root_symbol (str): The root symbol of the option contract.
        underlying_symbol (str): The underlying symbol of the option contract.
        underlying_asset_id (UUID): The unique identifier of the underlying asset.
        type (ContractType): The type of the option contract.
        style (ExerciseStyle): The style of the option contract.
        strike_price (Union[str, float]): The strike price of the option contract.
        multiplier (Union[str, float]): The multiplier of the option contract is crucial for calculating both the trade premium and the extended strike price. In standard contracts, the multiplier is always set to 100.
        size (str): The size of the option contract. Usually contracts have size=100.
        open_interest (Optional[str]): The open interest of the option contract.
        open_interest_date (Optional[date]): The date of the open interest data.
        close_price (Optional[str]): The close price of the option contract.
        close_price_date (Optional[date]): The date of the close price data.
        deliverables (Optional[array]): Represents the deliverables tied to the option contract. While standard contracts entail a single deliverable, non-standard ones can encompass multiple deliverables, each potentially customized with distinct parameters.
    """

    id: UUID
    symbol: str
    name: str
    status: AssetStatus
    tradable: bool
    expiration_date: date
    root_symbol: Optional[str]
    underlying_symbol: str
    underlying_asset_id: UUID
    type: ContractType
    style: ExerciseStyle
    strike_price: Union[str, float]
    multiplier: Union[str, float]
    size: str
    open_interest: Optional[str] = None
    open_interest_date: Optional[date] = None
    close_price: Optional[str] = None
    close_price_date: Optional[date] = None
    deliverables: Optional[List[Any]] = None


class OptionContractsResponse(BaseModel):
    """
    Represents a response from the option contracts endpoint.

    Attributes:
        option_contracts (Optional[List[OptionContract]]): The list of option contracts.
        next_page_token (Optional[str]): Pagination token for next page.
    """

    option_contracts: Optional[List[OptionContract]] = None
    next_page_token: Optional[str] = None


class CommonNTAActivityV2(BaseModel):
    """
    Common fields for all non-trade Activity V2 events.

    Attributes:
        system_date (date): The date when the activity was booked.
        group_id (Optional[UUID]): Optional group ID linking related activities.
    """

    system_date: date
    group_id: Optional[UUID] = None


class CommonCaActivityV2(CommonNTAActivityV2):
    """
    Common fields for corporate action Activity V2 events.
    Extends CommonNTAActivityV2.

    Attributes:
        position_date (date): The position date for this corporate action.
        ca_id (Optional[UUID]): Unique identifier for this corporate action.
        reorg_id (Optional[str]): Reorg identifier from the source corporate action definition.
    """

    position_date: date
    ca_id: Optional[UUID] = None
    reorg_id: Optional[str] = None


class CommonCDIVActivityV2(BaseModel):
    """
    Common fields for cash dividend Activity V2 events (mixin).

    Attributes:
        symbol (str): The symbol of the security.
        cusip (str): The CUSIP of the security.
        rate (str): Dividend rate per share.
        foreign (bool): Indicates if related to a non-US security.
        special (bool): Indicates if this is a special dividend.
        due_bill_on_date (Optional[date]): When due bills begin to apply.
        due_bill_off_date (Optional[date]): When due bills stop applying.
        ex_date (Optional[date]): Ex-date for this corporate action.
        record_date (Optional[date]): Record date for this corporate action.
        payable_date (Optional[date]): Payable date for this corporate action.
    """

    symbol: str
    cusip: str
    rate: str
    foreign: bool
    special: bool
    due_bill_on_date: Optional[date] = None
    due_bill_off_date: Optional[date] = None
    ex_date: Optional[date] = None
    record_date: Optional[date] = None
    payable_date: Optional[date] = None


class CommonSDIVActivityV2(BaseModel):
    """
    Common fields for stock dividend Activity V2 events (mixin).

    Attributes:
        symbol (str): The symbol of the security.
        cusip (str): The CUSIP of the security.
        rate (str): Dividend rate per share.
        ex_date (Optional[date]): Ex-date for this corporate action.
        record_date (Optional[date]): Record date for this corporate action.
        payable_date (Optional[date]): Payable date for this corporate action.
    """

    symbol: str
    cusip: str
    rate: str
    ex_date: Optional[date] = None
    record_date: Optional[date] = None
    payable_date: Optional[date] = None


class CommonSplitActivityV2(BaseModel):
    """
    Common fields for stock split Activity V2 events (mixin).

    Attributes:
        old_cusip (str): CUSIP of the old security before the split.
        new_cusip (str): CUSIP of the new security after the split.
        old_rate (str): Ratio of old shares exchanged.
        new_rate (str): Ratio of new shares received.
        payable_date (Optional[date]): Payable date for this corporate action.
    """

    old_cusip: str
    new_cusip: str
    old_rate: str
    new_rate: str
    payable_date: Optional[date] = None


class CommonSplitStockActivityV2(CommonCaActivityV2, CommonSplitActivityV2):
    """
    Common fields for stock split Activity V2 events that affect share counts.
    Combines CommonCaActivityV2 and CommonSplitActivityV2.

    Attributes:
        old_qty (str): The old quantity before the split.
        new_qty (str): The new quantity after the split.
    """

    old_qty: str
    new_qty: str


class CommonSpinoffActivityV2(BaseModel):
    """
    Common fields for spinoff Activity V2 events (mixin).

    Attributes:
        source_cusip (str): CUSIP of the parent security.
        source_symbol (str): Symbol of the parent security.
        source_rate (str): Ratio of parent shares.
        source_price (str): Market price of parent shares before the spinoff.
        new_cusip (str): CUSIP of the new security.
        new_symbol (str): Symbol of the new security.
        new_rate (str): Ratio of new shares received.
        new_price (str): Market price of new shares after the spinoff.
        due_bill_redemption_date (Optional[date]): When due bills are redeemed.
        ex_date (Optional[date]): Ex-date for this corporate action.
        record_date (Optional[date]): Record date for this corporate action.
        payable_date (Optional[date]): Payable date for this corporate action.
    """

    source_cusip: str
    source_symbol: str
    source_rate: str
    source_price: str
    new_cusip: str
    new_symbol: str
    new_rate: str
    new_price: str
    due_bill_redemption_date: Optional[date] = None
    ex_date: Optional[date] = None
    record_date: Optional[date] = None
    payable_date: Optional[date] = None


class CommonMAActivityV2(BaseModel):
    """
    Common fields for merger and acquisition Activity V2 events (mixin).

    Attributes:
        acquiree_cusip (str): CUSIP of the acquiree.
        acquiree_symbol (str): Symbol of the acquiree.
        effective_date (date): When the merger/acquisition becomes effective.
        payable_date (date): The payable date.
        acquiree_rate (Optional[str]): Rate of the acquiree.
        acquirer_cusip (Optional[str]): CUSIP of the acquirer.
        acquirer_symbol (Optional[str]): Symbol of the acquirer.
        acquirer_rate (Optional[str]): Rate of the acquirer.
    """

    acquiree_cusip: str
    acquiree_symbol: str
    effective_date: date
    payable_date: date
    acquiree_rate: Optional[str] = None
    acquirer_cusip: Optional[str] = None
    acquirer_symbol: Optional[str] = None
    acquirer_rate: Optional[str] = None


class CommonNCActivityV2(BaseModel):
    """
    Common fields for name change Activity V2 events (mixin).

    Attributes:
        old_cusip (str): Old CUSIP before the name change.
        old_symbol (str): Old symbol before the name change.
        new_cusip (str): New CUSIP after the name change.
        new_symbol (str): New symbol after the name change.
    """

    old_cusip: str
    old_symbol: str
    new_cusip: str
    new_symbol: str


class CommonVOFSubtypeActivityV2(BaseModel):
    """
    Common fields for voluntary offering Activity V2 events (mixin).

    Attributes:
        source_cusip (str): CUSIP of the parent security.
        source_symbol (str): Symbol of the parent security.
        new_cusip (Optional[str]): CUSIP of the new security.
        new_symbol (Optional[str]): Symbol of the new security.
    """

    source_cusip: str
    source_symbol: str
    new_cusip: Optional[str] = None
    new_symbol: Optional[str] = None


class CommonOptionsActivityV2(CommonNTAActivityV2):
    """
    Common fields for options Activity V2 events.
    Extends CommonNTAActivityV2 and requires group_id.

    Attributes:
        group_id (UUID): Group ID linking related options activities (required).
    """

    group_id: UUID  # type: ignore[assignment]  # overrides Optional[UUID] in parent


class CommonOPCAActivityV2(CommonCaActivityV2):
    """
    Common fields for options corporate action Activity V2 events.
    Extends CommonCaActivityV2.

    Attributes:
        old_contract_symbol (str): The old contract symbol.
        new_contract_symbol (str): The new contract symbol.
        qty (Optional[str]): Quantity when old and new contract quantities are equal.
            Mutually exclusive with old_qty and new_qty.
        old_qty (Optional[str]): Old contract quantity when different from new.
            Mutually exclusive with qty.
        new_qty (Optional[str]): New contract quantity when different from old.
            Mutually exclusive with qty.
    """

    old_contract_symbol: str
    new_contract_symbol: str
    qty: Optional[str] = None
    old_qty: Optional[str] = None
    new_qty: Optional[str] = None


class CommonAcatActivityV2(BaseModel):
    """
    Common fields for ACATS transfer Activity V2 events (mixin).

    Attributes:
        external_id (str): The ID that DTCC assigned to this transfer.
        request_id (UUID): The ID for the original ACATS request.
        hold_date (Optional[date]): Hold date when the transfers settle.
    """

    external_id: str
    request_id: UUID
    hold_date: Optional[date] = None


class AcatcActivityV2(CommonNTAActivityV2, CommonAcatActivityV2):
    """
    Automated customer account transfer service (cash).

    Inherits ``system_date`` and ``group_id`` from ``CommonNTAActivityV2``,
    and ``external_id``, ``request_id``, ``hold_date`` from ``CommonAcatActivityV2``.
    """


class AcatsActivityV2(CommonNTAActivityV2, CommonAcatActivityV2):
    """
    Automated customer account transfer service (stock).

    Inherits ``system_date`` and ``group_id`` from ``CommonNTAActivityV2``,
    and ``external_id``, ``request_id``, ``hold_date`` from ``CommonAcatActivityV2``.

    Attributes:
        symbol (str): The symbol of the security involved with the activity.
    """

    symbol: str


class CommonJournalActivityV2(CommonNTAActivityV2):
    """
    Common fields for journal Activity V2 events.
    Extends CommonNTAActivityV2.

    Attributes:
        journal_id (Optional[UUID]): The journal's ID.
    """

    journal_id: Optional[UUID] = None


class DIVSPDActivityV2(CommonCaActivityV2):
    """
    Substitute payment in lieu of dividend.

    Attributes:
        entitled_qty (str): Quantity of shares entitled to receive cash in lieu.
        cash_payout (str): Total cash amount paid.
        symbol (str): The symbol of the security.
        cusip (str): The CUSIP of the security.
        rate (str): Cash payout per share.
        foreign (bool): Indicates if related to a non-US security.
        special (bool): Indicates if this is a special dividend.
        due_bill_on_date (Optional[date]): When due bills begin to apply.
        due_bill_off_date (Optional[date]): When due bills stop applying.
        ex_date (Optional[date]): Ex-date for this corporate action.
        record_date (Optional[date]): Record date for this corporate action.
        payable_date (Optional[date]): Payable date for this corporate action.
    """

    entitled_qty: str
    cash_payout: str
    symbol: str
    cusip: str
    rate: str
    foreign: bool
    special: bool
    due_bill_on_date: Optional[date] = None
    due_bill_off_date: Optional[date] = None
    ex_date: Optional[date] = None
    record_date: Optional[date] = None
    payable_date: Optional[date] = None


class CDIVActivityV2(CommonCaActivityV2, CommonCDIVActivityV2):
    """
    Cash dividend.

    Attributes:
        entitled_qty (str): Quantity of shares entitled to receive the dividend.
        cash_payout (str): Total cash amount paid.
    """

    entitled_qty: str
    cash_payout: str


class DIVNRAActivityV2(CommonNTAActivityV2):
    """
    Dividend withholding for non-resident aliens.

    Attributes:
        cusip (str): The CUSIP of the security.
        symbol (str): The symbol of the security.
        parent_id (str): The ref_id of the parent dividend activity.
    """

    cusip: str
    symbol: str
    parent_id: str


class CSWActivityV2(CommonNTAActivityV2):
    """
    Cash withdrawal.

    Attributes:
        bank_transaction_id (Optional[UUID]): The bank transaction's ID.
    """

    bank_transaction_id: Optional[UUID] = None


class ActivityV2DetailTRD(BaseModel):
    """
    Activity details for a fill or partial_fill trade event.

    Attributes:
        order_id (UUID): Order ID generated by Alpaca.
        side (Union[OrderSide, str]): Side of the transaction — ``buy`` or ``sell``.
            Typed as ``Union[OrderSide, str]`` for backward compatibility with callers
            that pass or compare raw strings.
        symbol (str): The symbol of the security involved with the activity.
        asset_id (UUID): Asset ID (for options this represents the option contract ID).
        leaves_qty (str): Unfilled quantity on the order; ``0`` when fully filled.
        cum_qty (str): Total filled quantity on the order.
        order_status (str): Identifies the current status of the order.
        execution_type (Union[ExecutionType, str]): The execution type —
            ``fill``, ``trade_correct``, or ``trade_bust``.
            Typed as ``Union[ExecutionType, str]`` for backward compatibility with callers
            that pass or compare raw strings.
        client_order_id (Optional[str]): Order ID provided by the customer.
        cusip (Optional[str]): CUSIP of the security involved with the activity.
        commission (Optional[str]): Commission to collect from the account holder.

    .. todo::
        Simplify ``side`` to ``OrderSide`` and ``execution_type`` to ``ExecutionType``
        once a breaking-change release is acceptable (drop the ``str`` fallback).
    """

    order_id: UUID
    # TODO: narrow to OrderSide / ExecutionType (drop str) on next breaking release
    side: Union[OrderSide, str]
    symbol: str
    asset_id: UUID
    leaves_qty: str
    cum_qty: str
    order_status: str
    execution_type: Union[ExecutionType, str]
    client_order_id: Optional[str] = None
    cusip: Optional[str] = None
    commission: Optional[str] = None


class ActivityV2DetailNTA(CommonNTAActivityV2):
    """
    Activity details for a non-trade activity event.

    Represents the minimum common shape of any NTA detail payload delivered
    over the Event Streaming API. Inherits system_date and group_id from
    CommonNTAActivityV2. The spec defines more than 30 concrete sub-types
    (DIVSPDActivityV2, CDIVActivityV2, AcatcActivityV2, …) each of which
    extends this base with additional fields.
    """


class ActivityEventV2CommonFields(BaseModel):
    """
    Common fields shared by all Activity V2 Events delivered over the
    Event Streaming API.

    Attributes:
        at (datetime): Timestamp of the event.
        event_id (str): Lexically sortable, monotonically increasing identifier (ULID).
        activity_type (str): The type of the activity (e.g. ``FILL``, ``DIV``).
        executed_at (datetime): Execution time for the activity event.
        status (str): Status of the activity.
        settle_date (date): Date when the activity settled.
        currency (str): Currency code in ISO format (e.g. ``USD``).
        ref_id (UUID): Unique identifier for the activity. For trades the execution_id
            is used; for other activities the trns_id is used.
        activity_subtype (Optional[str]): Sub-category for the activity type, if any.
        price (Optional[str]): Price of the security involved with the activity.
        qty (Optional[str]): Quantity of the security involved with the activity.
        net_amount (Optional[str]): Net amount of money (positive or negative)
            associated with the activity.
        swap_rate (Optional[str]): Conversion rate for local currency activities.
        swap_fee_bps (Optional[str]): Currency conversion fee rate in basis points
            for local currency activities.
        previous_id (Optional[UUID]): ID of a prior activity that this event corrects
            or cancels.
    """

    at: datetime
    event_id: str
    activity_type: str
    executed_at: datetime
    status: str
    settle_date: date
    currency: str
    ref_id: UUID
    activity_subtype: Optional[str] = None
    price: Optional[str] = None
    qty: Optional[str] = None
    net_amount: Optional[str] = None
    swap_rate: Optional[str] = None
    swap_fee_bps: Optional[str] = None
    previous_id: Optional[UUID] = None


class ActivityEventV2(ActivityEventV2CommonFields):
    """
    Represents an account activity sent over the Event Streaming API (V2).

    Inherits all common fields from ActivityEventV2CommonFields and adds
    the activity-specific detail payload.

    Attributes:
        details (Union[ActivityV2DetailTRD, ActivityV2DetailNTA]): Activity-specific
            detail payload. For trade activities (``FILL``) this is an
            ActivityV2DetailTRD; for all other activity types it is an
            ActivityV2DetailNTA.
    """

    details: Union[ActivityV2DetailTRD, ActivityV2DetailNTA]


class AccountConfigurations(BaseModel):
    """
    Account configuration settings returned by the Trading API.

    All fields are optional because the API may omit any setting that has
    not been explicitly configured. The account configuration API provides
    custom configurations about your trading account settings.

    Attributes:
        dtbp_check (Optional[Union[DTBPCheck, str]]): Controls Day Trading Margin
            Call (DTMC) checks. Accepts ``DTBPCheck`` enum values or the raw
            strings ``"both"``, ``"entry"``, ``"exit"``.
        trade_confirm_email (Optional[str]): ``all`` or ``none``. Controls whether
            trade confirmation emails are sent.
        suspend_trade (Optional[bool]): If ``True``, new orders are blocked.
        no_shorting (Optional[bool]): If ``True``, account becomes long-only.
        fractional_trading (Optional[bool]): If ``True``, account can participate
            in fractional trading.
        max_margin_multiplier (Optional[str]): ``"1"``, ``"2"``, or ``"4"``.
        max_options_trading_level (Optional[int]): Maximum options trading level.
            0=disabled, 1=Covered Call/Cash-Secured Put, 2=Long Call/Put,
            3=Spreads/Straddles.
        pdt_check (Optional[str]): ``both``, ``entry``, or ``exit``.
            Controls Pattern Day Trader (PDT) checks.
        ptp_no_exception_entry (Optional[bool]): If ``True``, Alpaca accepts orders
            for PTP symbols with no exception.
        disable_overnight_trading (Optional[bool]): If ``True``, overnight trading
            is disabled.
    """

    dtbp_check: Optional[Union[DTBPCheck, Literal["both", "entry", "exit"]]] = None
    trade_confirm_email: Optional[str] = None
    suspend_trade: Optional[bool] = None
    no_shorting: Optional[bool] = None
    fractional_trading: Optional[bool] = None
    max_margin_multiplier: Optional[str] = None
    max_options_trading_level: Optional[int] = None
    pdt_check: Optional[str] = None
    ptp_no_exception_entry: Optional[bool] = None
    disable_overnight_trading: Optional[bool] = None


class SDIVActivityV2(CommonCaActivityV2, CommonSDIVActivityV2):
    """
    Stock dividend.

    Attributes:
        entitled_qty (str): Quantity of shares entitled to receive the dividend.
        paid_qty (str): The paid quantity of shares.
        new_qty (str): The total number of shares after the dividend.
    """

    entitled_qty: str
    paid_qty: str
    new_qty: str


class SpinoffActivityV2(CommonCaActivityV2, CommonSpinoffActivityV2):
    """
    Spinoff.

    Attributes:
        source_qty (str): The source quantity of shares.
        new_qty (str): The new quantity of shares received.
    """

    source_qty: str
    new_qty: str


class MAActivityV2(CommonCaActivityV2, CommonMAActivityV2):
    """
    Merger and acquisition.

    Attributes:
        acquiree_qty (str): Quantity of acquiree shares.
        acquirer_qty (Optional[str]): Quantity of acquirer shares.
        cash_rate (Optional[str]): The cash rate.
        cash_payout (Optional[str]): The cash payout.
    """

    acquiree_qty: str
    acquirer_qty: Optional[str] = None
    cash_rate: Optional[str] = None
    cash_payout: Optional[str] = None


class NCActivityV2(CommonCaActivityV2, CommonNCActivityV2):
    """
    Name change.

    Attributes:
        position_qty (str): The position quantity.
    """

    position_qty: str


class WRMActivityV2(CommonCaActivityV2):
    """
    Worthless removal.

    Attributes:
        cusip (str): The CUSIP of the security.
        symbol (str): The symbol of the security.
        removed_qty (str): The removed quantity of shares.
    """

    cusip: str
    symbol: str
    removed_qty: str


class TenderOfferActivityV2(CommonNTAActivityV2, CommonVOFSubtypeActivityV2):
    """
    Tender offer voluntary offering activity.
    Combines CommonNTAActivityV2 and CommonVOFSubtypeActivityV2.
    """


class FOPTActivityV2(CommonNTAActivityV2):
    """
    Free-of-payment (FOP) transfer.

    Attributes:
        external_id (str): External ID of the transfer.
        contra (str): Contra for the transfer.
        symbol (str): The symbol of the security involved with the activity.
    """

    external_id: str
    contra: str
    symbol: str


class JNLSActivityV2(CommonJournalActivityV2):
    """
    Journal entry (stock).

    Attributes:
        symbol (str): The symbol of the security involved with the activity.
    """

    symbol: str


class JNLCActivityV2(CommonJournalActivityV2):
    """
    Journal entry (cash).
    Inherits all fields from CommonJournalActivityV2.
    """


class FEEActivityV2(CommonNTAActivityV2):
    """
    Fee activity.

    Attributes:
        parent_id (str): The parent transaction's ID.
    """

    parent_id: UUID


class OPASNActivityV2(CommonOptionsActivityV2):
    """
    Option assignment.
    Inherits all fields from CommonOptionsActivityV2.
    """


class OPEXCActivityV2(CommonOptionsActivityV2):
    """
    Option exercise.
    Inherits all fields from CommonOptionsActivityV2.
    """


class OPEXPActivityV2(CommonOptionsActivityV2):
    """
    Option expiry.
    Inherits all fields from CommonOptionsActivityV2.
    """


class OPTRDActivityV2(CommonOptionsActivityV2):
    """
    Trading activity paired with an option assignment or exercise.
    Inherits all fields from CommonOptionsActivityV2.
    """


class OpcaCDIVActivityV2(CommonOPCAActivityV2, CommonCDIVActivityV2):
    """
    Options corporate action — cash dividend.
    Combines CommonOPCAActivityV2 and CommonCDIVActivityV2.
    """


class OpcaSDIVActivityV2(CommonOPCAActivityV2, CommonSDIVActivityV2):
    """
    Options corporate action — stock dividend.
    Combines CommonOPCAActivityV2 and CommonSDIVActivityV2.
    """


class OpcaMAActivityV2(CommonOPCAActivityV2, CommonMAActivityV2):
    """
    Options corporate action — merger and acquisition.
    Combines CommonOPCAActivityV2 and CommonMAActivityV2.
    """


class OpcaNCActivityV2(CommonOPCAActivityV2, CommonNCActivityV2):
    """
    Options corporate action — name change.
    Combines CommonOPCAActivityV2 and CommonNCActivityV2.
    """


class OpcaSPINActivityV2(CommonOPCAActivityV2, CommonSpinoffActivityV2):
    """
    Options corporate action — spin-off.
    Combines CommonOPCAActivityV2 and CommonSpinoffActivityV2.
    """


class OpcaFSPLITActivityV2(CommonOPCAActivityV2, CommonSplitActivityV2):
    """
    Options corporate action — forward stock split.

    Attributes:
        symbol (str): The symbol of the security being split.
        due_bill_redemption_date (Optional[date]): When due bills related to the split are redeemed.
        ex_date (Optional[date]): Ex-date for this corporate action.
        record_date (Optional[date]): Record date for this corporate action.
    """

    symbol: str
    due_bill_redemption_date: Optional[date] = None
    ex_date: Optional[date] = None
    record_date: Optional[date] = None


class OpcaRSPLITActivityV2(CommonOPCAActivityV2, CommonSplitActivityV2):
    """
    Options corporate action — reverse stock split.

    Attributes:
        symbol (str): The symbol of the security involved with the activity.
        new_symbol (Optional[str]): Symbol of the new security after the split.
        ex_date (Optional[date]): Ex-date for this corporate action.
        record_date (Optional[date]): Record date for this corporate action.
    """

    symbol: str
    new_symbol: Optional[str] = None
    ex_date: Optional[date] = None
    record_date: Optional[date] = None


class OpcaUSPLITActivityV2(CommonOPCAActivityV2, CommonSplitActivityV2):
    """
    Options corporate action — unit split.

    Attributes:
        old_symbol (str): The old symbol of the security.
        new_symbol (str): Symbol of the new security after the unit split.
        alternate_cusip (str): CUSIP for the alternate security after the split.
        alternate_symbol (str): Symbol for the alternate security after the split.
        alternate_rate (str): Ratio of alternate shares received.
        effective_date (date): When the unit split becomes effective.
    """

    old_symbol: str
    new_symbol: str
    alternate_cusip: str
    alternate_symbol: str
    alternate_rate: str
    effective_date: date


class UnitSplitActivityV2(CommonSplitStockActivityV2):
    """
    Unit split.

    Attributes:
        old_symbol (str): Symbol of the old security before the split.
        new_symbol (str): Symbol of the new security after the split.
        alternate_cusip (str): CUSIP for the alternate security after the split.
        alternate_symbol (str): Symbol for the alternate security after the split.
        alternate_rate (str): Ratio of alternate shares received.
        alternate_qty (str): Quantity of alternate shares received.
        effective_date (date): When the unit split becomes effective.
    """

    old_symbol: str
    new_symbol: str
    alternate_cusip: str
    alternate_symbol: str
    alternate_rate: str
    alternate_qty: str
    effective_date: date


class AdvancedInstructions(BaseModel):
    """
    Advanced instructions for the Alpaca Elite Smart Router.
    See https://docs.alpaca.markets/docs/alpaca-elite-smart-router

    Attributes:
        algorithm (Optional[Union[AdvancedInstructionsAlgorithm, Literal["DMA","TWAP","VWAP"]]]):
            Advanced routing algorithm to use. Accepts the ``AdvancedInstructionsAlgorithm``
            enum or a raw string; values are still validated against the allowed set for
            backward compatibility.
        destination (Optional[Union[AdvancedInstructionsDestination, Literal["NYSE","NASDAQ","ARCA"]]]):
            Target exchange for execution. Accepts the ``AdvancedInstructionsDestination``
            enum or a raw string; values are still validated against the allowed set for
            backward compatibility.
        display_qty (Optional[str]): Maximum shares displayed on the exchange at any time
            (must be in round-lot increments).
        start_time (Optional[datetime]): When the algorithm starts executing
            (must be within current market trading hours).
        end_time (Optional[datetime]): When the algorithm finishes executing
            (must be within current market trading hours).
        max_percentage (Optional[str]): Maximum percentage of the ticker's period volume
            this order may participate in (0 < value < 1, up to 3 decimal points).

    .. todo::
        Simplify ``algorithm`` to ``AdvancedInstructionsAlgorithm`` and ``destination`` to
        ``AdvancedInstructionsDestination`` (drop the ``Literal`` fallback) on the next
        breaking release.
    """

    # TODO: simplify to just AdvancedInstructionsAlgorithm / AdvancedInstructionsDestination
    # on next breaking release (drop the Literal fallback — it exists only so callers passing
    # raw strings still get validated against the allowed set, matching the original strictness).
    algorithm: Optional[
        Union[AdvancedInstructionsAlgorithm, Literal["DMA", "TWAP", "VWAP"]]
    ] = None
    destination: Optional[
        Union[AdvancedInstructionsDestination, Literal["NYSE", "NASDAQ", "ARCA"]]
    ] = None
    display_qty: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    max_percentage: Optional[str] = None


class CanceledOrderResponse(BaseModel):
    """
    Result of a request to cancel an order.

    Attributes:
        id (Optional[UUID]): The order ID.
        status (Optional[int]): HTTP response code from the cancel attempt.
        body (Optional[Dict[str, Any]]): Error detail when the cancellation failed.
    """

    id: Optional[UUID] = None
    status: Optional[int] = None
    body: Optional[Dict[str, Any]] = None  # API extension; not in spec


class PositionClosedReponse(BaseModel):
    """
    Result of asking the API to close a single position.

    Note: the class name preserves the typo ("Reponse") present in the OpenAPI spec.

    Attributes:
        symbol (str): Symbol name of the asset.
        status (int): HTTP status code for the close attempt.
        body (Optional[Order]): The resulting sell order when the close succeeded.
    """

    symbol: str
    status: int
    body: Optional[Order] = None


class ExchangeOfferActivityV2(CommonNTAActivityV2, CommonVOFSubtypeActivityV2):
    """
    Exchange offer voluntary corporate action activity (VOF sub-type).

    Combines CommonNTAActivityV2 (system_date, group_id) and
    CommonVOFSubtypeActivityV2 (source_cusip, source_symbol, new_cusip, new_symbol).
    """


class RightsSubscriptionElectionActivityV2(
    CommonNTAActivityV2, CommonVOFSubtypeActivityV2
):
    """
    Rights subscription election voluntary corporate action activity (VOF sub-type).

    Combines CommonNTAActivityV2 (system_date, group_id) and
    CommonVOFSubtypeActivityV2 (source_cusip, source_symbol, new_cusip, new_symbol).
    """


class FixedIncomeRedemptionActivityV2(CommonNTAActivityV2):
    """
    Fixed income redemption activity.

    Attributes:
        ca_id (UUID): Unique identifier for this corporate action.
        payment_date (date): The payment date.
        cusip (str): CUSIP of the security involved.
        qty (str): Quantity for the redemption.
        cash_payout (str): The cash payout amount.
    """

    ca_id: UUID
    payment_date: date
    cusip: str
    qty: str
    cash_payout: str


class ForwardSplitActivityV2(CommonSplitStockActivityV2):
    """
    Forward stock split corporate action activity.

    Attributes:
        symbol (str): Symbol of the security being split.
        due_bill_redemption_date (Optional[date]): When due bills related to the split are redeemed.
        ex_date (Optional[date]): Ex-date for this corporate action.
        record_date (Optional[date]): Record date for this corporate action.
    """

    symbol: str
    due_bill_redemption_date: Optional[date] = None
    ex_date: Optional[date] = None
    record_date: Optional[date] = None


class ReverseSplitActivityV2(CommonSplitStockActivityV2):
    """
    Reverse stock split corporate action activity.

    Attributes:
        symbol (str): Symbol of the security involved with the activity.
        new_symbol (Optional[str]): Symbol of the new security after the split.
        ex_date (Optional[date]): Ex-date for this corporate action.
        record_date (Optional[date]): Record date for this corporate action.
    """

    symbol: str
    new_symbol: Optional[str] = None
    ex_date: Optional[date] = None
    record_date: Optional[date] = None


class RightsDistributionActivityV2(CommonCaActivityV2):
    """
    Rights distribution corporate action activity.

    Attributes:
        source_cusip (str): The source CUSIP.
        source_symbol (str): The source symbol.
        source_qty (str): The source quantity.
        new_cusip (str): The new CUSIP.
        new_symbol (str): The new symbol.
        new_qty (str): The new quantity.
        rate (str): The rate for the rights distribution.
        expiration_date (Optional[date]): Expiration date for the rights distribution.
        ex_date (Optional[date]): Ex-date for this corporate action.
        record_date (Optional[date]): Record date for this corporate action.
        payable_date (Optional[date]): Payable date for this corporate action.
    """

    source_cusip: str
    source_symbol: str
    source_qty: str
    new_cusip: str
    new_symbol: str
    new_qty: str
    rate: str
    expiration_date: Optional[date] = None
    ex_date: Optional[date] = None
    record_date: Optional[date] = None
    payable_date: Optional[date] = None


class CryptoTransfer(BaseModel):
    """
    Represents a crypto asset transfer into or out of an account.

    Attributes:
        id (Optional[UUID]): The crypto transfer ID.
        tx_hash (Optional[str]): On-chain transaction hash (e.g. ``0xabc...xyz``).
        direction (Optional[TransferDirection]): Whether this is an incoming deposit or
            outgoing withdrawal.
        status (Optional[CryptoTransferStatus]): Current processing status of the transfer.
        amount (Optional[str]): Amount of the transfer denominated in the underlying crypto asset.
        usd_value (Optional[str]): Equivalent USD value at the time of the transfer.
        network_fee (Optional[str]): Network fee charged for the transfer.
        fees (Optional[str]): Total fees charged for the transfer.
        chain (Optional[str]): Underlying blockchain network for the transfer.
        asset (Optional[str]): Symbol of the crypto asset (e.g. ``BTC``).
        from_address (Optional[str]): Originating wallet address.
        to_address (Optional[str]): Destination wallet address.
        created_at (Optional[datetime]): Timestamp when the transfer was created.
    """

    id: Optional[UUID] = None
    tx_hash: Optional[str] = None
    direction: Optional[TransferDirection] = None
    status: Optional[CryptoTransferStatus] = None
    amount: Optional[str] = None
    usd_value: Optional[str] = None
    network_fee: Optional[str] = None
    fees: Optional[str] = None
    chain: Optional[str] = None
    asset: Optional[str] = None
    from_address: Optional[str] = None
    to_address: Optional[str] = None
    created_at: Optional[datetime] = None


class CryptoWallet(BaseModel):
    """
    Represents a crypto wallet associated with an account.

    Attributes:
        chain (Optional[str]): Blockchain network identifier.
        address (Optional[str]): Wallet address.
        created_at (Optional[datetime]): Timestamp when the wallet was created.
    """

    chain: Optional[str] = None
    address: Optional[str] = None
    created_at: Optional[datetime] = None


class NonTradeActivities(BaseModel):
    """
    Represents a non-trade account activity (dividends, fees, interest, corporate actions, etc.).

    Attributes:
        activity_type (Optional[ActivityType]): The type of activity.
        activity_sub_type (Optional[ActivitySubType]): More specific classification of the
            activity type.
        id (Optional[str]): Activity ID, always in ``"<date>::<uuid>"`` format. Can be used
            as ``page_token`` to paginate results.
        date (Optional[datetime]): Date on which the activity occurred or on which the
            associated transaction settled.
        net_amount (Optional[str]): Net amount of money (positive or negative) associated
            with the activity.
        currency (Optional[str]): Currency code for the activity.
        symbol (Optional[str]): Symbol of the security involved. Not present for all types.
        cusip (Optional[str]): CUSIP of the security involved. Not present for all types.
        qty (Optional[str]): For dividend activities, the number of shares that contributed
            to the payment.
        per_share_amount (Optional[str]): For dividend activities, the average amount paid
            per share.
        group_id (Optional[str]): ID linking related sibling activities together.
        status (Optional[NonTradeActivityStatus]): The activity status.
        created_at (Optional[datetime]): Timestamp when the activity was created. Null for
            trade activities.
    """

    activity_type: Optional[ActivityType] = None
    activity_sub_type: Optional[ActivitySubType] = None
    id: Optional[str] = None
    date: Optional[datetime] = None
    net_amount: Optional[str] = None
    currency: Optional[str] = None
    symbol: Optional[str] = None
    cusip: Optional[str] = None
    qty: Optional[str] = None
    per_share_amount: Optional[str] = None
    group_id: Optional[str] = None
    status: Optional[NonTradeActivityStatus] = None
    created_at: Optional[datetime] = None


class Error(BaseModel):
    """
    Standard API error response.

    Attributes:
        code (float): Alpaca error code.
        message (str): Human-readable error description.
    """

    code: float
    message: str


class MLegOrderLeg(BaseModel):
    """
    An individual leg of a multi-leg options order.

    Attributes:
        symbol (str): Symbol or asset ID of the asset to trade.
        ratio_qty (str): Proportional quantity of this leg relative to the overall
            multi-leg order quantity.
        side (Optional[OrderSide]): Buy or sell side for this leg.
        position_intent (Optional[PositionIntent]): The position intent for this leg.
    """

    symbol: str
    ratio_qty: str
    side: Optional[OrderSide] = None
    position_intent: Optional[PositionIntent] = None


class OptionDeliverable(BaseModel):
    """
    Describes what is delivered when an option contract is exercised or assigned.

    Attributes:
        type (OptionDeliverableType): Whether the deliverable is cash or equity.
        symbol (str): Symbol of the deliverable asset.
        amount (str): Deliverable amount (100 for standard contracts; may be null if
            delayed settlement is pending determination).
        allocation_percentage (str): Cost allocation percentage used to determine the
            cost basis of equity shares received from exercise.
        settlement_type (OptionDeliverableSettlementType): Settlement timing relative to
            the exercise/assignment date.
        settlement_method (OptionDeliverableSettlementMethod): Settlement method (BTOB,
            CADF, CAFX, or CCC).
        delayed_settlement (bool): If ``True``, settlement of the deliverable is delayed.
        asset_id (Optional[UUID]): Unique identifier of the deliverable asset. Not
            returned for cash deliverables.
    """

    type: OptionDeliverableType
    symbol: str
    amount: str
    allocation_percentage: str
    settlement_type: OptionDeliverableSettlementType
    settlement_method: OptionDeliverableSettlementMethod
    delayed_settlement: bool
    asset_id: Optional[UUID] = None


class OrderLeg(ModelWithID):
    """
    A single leg of a multi-leg order as returned by the API.

    This schema mirrors ``Order`` but omits recursive leg nesting — the spec
    defines it as a separate schema to avoid circular references. Legs of an
    ``OrderLeg`` are always ``None``.

    Attributes:
        id (Optional[UUID]): Order ID.
        symbol (str): Asset symbol.
        notional (Optional[str]): Ordered notional amount (mutually exclusive with qty).
        qty (Optional[Union[str, float]]): Ordered quantity (mutually exclusive with notional).
        type (OrderType): The order type.
        side (OrderSide): Buy or sell.
        time_in_force (TimeInForce): Time-in-force for the order.
        client_order_id (Optional[str]): Client-supplied order ID (max 128 chars).
        created_at (Optional[datetime]): When the order was created.
        updated_at (Optional[datetime]): When the order was last updated.
        submitted_at (Optional[datetime]): When the order was submitted.
        filled_at (Optional[datetime]): When the order was filled.
        expired_at (Optional[datetime]): When the order expired.
        canceled_at (Optional[datetime]): When the order was canceled.
        failed_at (Optional[datetime]): When the order failed.
        replaced_at (Optional[datetime]): When the order was replaced.
        replaced_by (Optional[UUID]): ID of the order that replaced this one.
        replaces (Optional[UUID]): ID of the order this one replaces.
        asset_id (Optional[UUID]): Asset ID (option contract ID for options).
        asset_class (Optional[AssetClass]): Asset class.
        filled_qty (Optional[str]): Filled quantity.
        filled_avg_price (Optional[str]): Filled average price.
        order_class (Optional[OrderClass]): Order class.
        order_type (Optional[str]): Deprecated in favour of ``type``.
        limit_price (Optional[str]): Limit price.
        stop_price (Optional[str]): Stop price.
        status (Optional[OrderStatus]): Current order status.
        extended_hours (Optional[bool]): Eligible for extended-hours execution.
        trail_percent (Optional[str]): Percent value away from HWM for trailing stops.
        trail_price (Optional[str]): Dollar value away from HWM for trailing stops.
        hwm (Optional[str]): Highest (or lowest) market price since trailing stop submission.
        position_intent (Optional[PositionIntent]): Position intent.
        legs (Optional[List[Any]]): Always ``None``; legs are not nested beyond one level.
        ratio_qty (Optional[str]): The proportional quantity of this leg in relation to the overall multi-leg order quantity.
    """

    id: Optional[UUID] = None
    symbol: str
    notional: Optional[str]
    qty: Optional[Union[str, float]]
    type: OrderType
    side: OrderSide
    time_in_force: TimeInForce
    client_order_id: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    submitted_at: Optional[datetime] = None
    filled_at: Optional[datetime] = None
    expired_at: Optional[datetime] = None
    canceled_at: Optional[datetime] = None
    failed_at: Optional[datetime] = None
    replaced_at: Optional[datetime] = None
    replaced_by: Optional[UUID] = None
    replaces: Optional[UUID] = None
    asset_id: Optional[UUID] = None
    asset_class: Optional[AssetClass] = None
    filled_qty: Optional[str] = None
    filled_avg_price: Optional[str] = None
    order_class: Optional[OrderClass] = None
    order_type: Optional[str] = None
    limit_price: Optional[str] = None
    stop_price: Optional[str] = None
    status: Optional[OrderStatus] = None
    extended_hours: Optional[bool] = None
    trail_percent: Optional[str] = None
    trail_price: Optional[str] = None
    hwm: Optional[str] = None
    position_intent: Optional[PositionIntent] = None
    legs: Optional[List[Any]] = None


class TokenizationMintResponse(BaseModel):
    """
    Response returned after submitting a tokenization mint request.

    Attributes:
        tokenization_request_id (str): Unique identifier assigned by Alpaca.
        status (TokenizationRequestStatus): Current processing status.
        underlying_symbol (str): The underlying asset symbol.
        token_symbol (str): The tokenized asset symbol.
        qty (str): Quantity submitted for this tokenization request.
        created_at (datetime): When the request was created.
        issuer (TokenizationIssuer): The tokenized asset's issuer.
        network (TokenizationNetwork): The blockchain network for the token.
    """

    tokenization_request_id: str
    status: TokenizationRequestStatus
    underlying_symbol: str
    token_symbol: str
    qty: str
    created_at: datetime
    issuer: TokenizationIssuer
    network: TokenizationNetwork


class TokenizationRequest(BaseModel):
    """
    A tokenization request record as returned by the API.

    Attributes:
        tokenization_request_id (str): Unique identifier assigned by Alpaca.
        created_at (datetime): When the request was created.
        type (TokenizationRequestType): Whether this is a mint or redeem request.
        status (TokenizationRequestStatus): Current processing status.
        underlying_symbol (str): The underlying asset symbol.
        token_symbol (str): The tokenized asset symbol.
        qty (str): Quantity to convert.
        issuer (TokenizationIssuer): The tokenized asset's issuer.
        network (TokenizationNetwork): The blockchain network for the token.
        wallet_address (str): Wallet address associated with this request.
        issuer_request_id (Optional[str]): Identifier assigned by the issuer.
        account (Optional[str]): Alpaca account ID associated with this request.
        issuer_account (Optional[str]): Issuer's account ID.
        updated_at (Optional[datetime]): When the request was last updated.
        tx_hash (Optional[str]): On-chain transaction hash once completed.
        fees (Optional[str]): Fees charged for this request.
    """

    tokenization_request_id: str
    created_at: datetime
    type: TokenizationRequestType
    status: TokenizationRequestStatus
    underlying_symbol: str
    token_symbol: str
    qty: str
    issuer: TokenizationIssuer
    network: TokenizationNetwork
    wallet_address: str
    issuer_request_id: Optional[str] = None
    account: Optional[str] = None
    issuer_account: Optional[str] = None
    updated_at: Optional[datetime] = None
    tx_hash: Optional[str] = None
    fees: Optional[str] = None


class WarrantExerciseElectionActivityV2(
    CommonNTAActivityV2, CommonVOFSubtypeActivityV2
):
    """
    Warrant exercise election voluntary corporate action activity (VOF sub-type).

    Combines CommonNTAActivityV2 (system_date, group_id) and
    CommonVOFSubtypeActivityV2 (source_cusip, source_symbol, new_cusip, new_symbol).
    """


class WhitelistedAddress(BaseModel):
    """
    A whitelisted crypto wallet address for withdrawals.

    New addresses enter ``PENDING`` status and transition to ``APPROVED`` after
    a 24-hour waiting period.

    Attributes:
        id (Optional[str]): Unique ID for the whitelisted address.
        chain (Optional[str]): Blockchain network this address belongs to.
        asset (Optional[str]): Symbol of the underlying asset.
        address (Optional[str]): The whitelisted wallet address.
        status (Optional[WhitelistedAddressStatus]): Current approval status.
        created_at (Optional[datetime]): When the address was registered.
    """

    id: Optional[str] = None
    chain: Optional[str] = None
    asset: Optional[str] = None
    address: Optional[str] = None
    status: Optional[WhitelistedAddressStatus] = None
    created_at: Optional[datetime] = None


class Locate(ModelWithID):
    """
    A locate request and its current lifecycle status.

    Attributes:
        id (UUID): Locate ID.
        symbol (str): Stock symbol.
        requested_qty (int): Number of shares requested.
        all_or_none (bool): Whether the request required the full quantity.
        status (LocateStatus): Locate status.
        created_at (datetime): Time when the locate was created.
        expires_at (Optional[datetime]): Time when the active locate expires.
        limit_price (Optional[str]): Maximum acceptable fee per share from the request.
        located_price (Optional[str]): Locate fee per share in USD.
        located_qty (Optional[int]): Number of shares located.
        total_fee (Optional[str]): Total locate fee in USD.
        rejection_reason (Optional[str]): Machine-readable rejection reason.
    """

    symbol: str
    requested_qty: int
    all_or_none: bool
    status: LocateStatus
    created_at: datetime
    expires_at: Optional[datetime] = None
    limit_price: Optional[str] = None
    located_price: Optional[str] = None
    located_qty: Optional[int] = None
    total_fee: Optional[str] = None
    rejection_reason: Optional[str] = None


class ErrorResponse(BaseModel):
    """
    API error response.

    Attributes:
        message (Optional[str]): Human-readable error message.
    """

    message: Optional[str] = None


class LocateError(BaseModel):
    """
    Locates API error response.

    Attributes:
        message (str): Error message.
        code (Optional[LocateErrorCode]): Machine-readable locate error code.
    """

    message: str
    code: Optional[LocateErrorCode] = None


class ListLocatesResponse(BaseModel):
    """
    Response returned when listing locate requests.

    Attributes:
        locates (List[Locate]): Locates matching the filter criteria.
        next_page_token (Optional[str]): Pagination token for the next page.
    """

    locates: List[Locate]
    next_page_token: Optional[str]


class LocateQuote(BaseModel):
    """
    Current locate pricing and availability for a symbol.

    Attributes:
        symbol (str): Stock symbol.
        available_qty (int): Available locate quantity.
        quoted_at (datetime): Time when the quote was issued.
        price (Optional[str]): Locate fee per share.
    """

    symbol: str
    available_qty: int
    quoted_at: datetime
    price: Optional[str] = None


class LocateQuoteError(BaseModel):
    """
    Error returned for a symbol that could not be quoted.

    Attributes:
        symbol (str): Requested stock symbol that could not be quoted.
        code (LocateQuoteErrorCode): Error code.
        message (str): Error message.
    """

    symbol: str
    code: LocateQuoteErrorCode
    message: str


class ListLocateQuotesResponse(BaseModel):
    """
    Response returned when fetching locate quotes.

    Attributes:
        quotes (List[LocateQuote]): Locate quotes returned for requested symbols.
        errors (Optional[List[LocateQuoteError]]): Symbols that could not be quoted.
    """

    quotes: List[LocateQuote]
    errors: Optional[List[LocateQuoteError]] = None


LocatesResponse = ListLocatesResponse
LocateQuotesResponse = ListLocateQuotesResponse


class TradingActivities(BaseModel):
    """
    Represents a trade (fill or partial fill) account activity.

    Attributes:
        activity_type (Optional[ActivityType]): The type of activity.
        id (Optional[str]): Activity ID, always in ``"<date>::<uuid>"`` format. Can be
            used as ``page_token`` to paginate results.
        cum_qty (Optional[str]): Cumulative quantity of shares involved in the execution.
        leaves_qty (Optional[str]): For partial fills, the remaining quantity to be filled.
        price (Optional[str]): Per-share price at which the trade was executed.
        qty (Optional[str]): Number of shares involved in this trade execution.
        side (Optional[str]): ``buy`` or ``sell``.
        symbol (Optional[str]): The symbol of the security being traded.
        transaction_time (Optional[datetime]): When the execution occurred.
        order_id (Optional[UUID]): ID of the order that filled.
        type (Optional[TradeActivityType]): ``fill`` or ``partial_fill``.
        order_status (Optional[OrderStatus]): Current status of the order.
    """

    activity_type: Optional[ActivityType] = None
    id: Optional[str] = None
    cum_qty: Optional[str] = None
    leaves_qty: Optional[str] = None
    price: Optional[str] = None
    qty: Optional[str] = None
    side: Optional[str] = None
    symbol: Optional[str] = None
    transaction_time: Optional[datetime] = None
    order_id: Optional[UUID] = None
    type: Optional[TradeActivityType] = None
    order_status: Optional[OrderStatus] = None


class WatchlistWithoutAsset(ModelWithID):
    """
    A watchlist without its asset list — returned by endpoints that do not include
    the asset details.

    See also ``Watchlist`` which extends this with an optional ``assets`` field.

    Attributes:
        id (UUID): Unique watchlist identifier.
        account_id (UUID): ID of the account that owns the watchlist.
        name (str): User-defined watchlist name (up to 64 characters).
        created_at (datetime): When the watchlist was created.
        updated_at (datetime): When the watchlist was last updated.
    """

    account_id: UUID
    name: str
    created_at: datetime
    updated_at: datetime


class CalendarDay(BaseModel):
    """
    A single trading calendar day with session times.

    Attributes:
        date (date): The calendar date.
        core_start (datetime): Start of the core market session.
        core_end (datetime): End of the core market session.
        pre_start (Optional[datetime]): Start of the pre-market session.
        pre_end (Optional[datetime]): End of the pre-market session.
        lunch_start (Optional[datetime]): Start of the lunch session.
        lunch_end (Optional[datetime]): End of the lunch session.
        post_start (Optional[datetime]): Start of the after-hours session.
        post_end (Optional[datetime]): End of the after-hours session.
        settlement_date (Optional[date]): Settlement date for trades on this day.
    """

    date: date
    core_start: datetime
    core_end: datetime
    pre_start: Optional[datetime] = None
    pre_end: Optional[datetime] = None
    lunch_start: Optional[datetime] = None
    lunch_end: Optional[datetime] = None
    post_start: Optional[datetime] = None
    post_end: Optional[datetime] = None
    settlement_date: Optional[date] = None


class LegacyCalendarDay(BaseModel):
    """
    A single trading calendar day in the legacy calendar format.

    Attributes:
        date (date): The calendar date (YYYY-MM-DD).
        open (str): Market open time in ``HH:MM`` format.
        close (str): Market close time in ``HH:MM`` format.
        session_open (str): Session open time in ``HHMM`` format.
        session_close (str): Session close time in ``HHMM`` format.
        settlement_date (date): Settlement date for trades on this day.
    """

    date: date
    open: str
    close: str
    session_open: str
    session_close: str
    settlement_date: date


class LegacyClock(BaseModel):
    """
    Market clock in the legacy format.

    See also ``Clock`` which is the existing SDK alias for this schema.

    Attributes:
        timestamp (datetime): Current timestamp.
        is_open (bool): Whether the market is currently open.
        next_open (datetime): Next market open timestamp.
        next_close (datetime): Next market close timestamp.
    """

    timestamp: datetime
    is_open: bool
    next_open: datetime
    next_close: datetime


class PublicMarket(BaseModel):
    """
    Market metadata as returned in clock responses.

    Attributes:
        acronym (str): The market's acronym (e.g. ``NYSE``).
        name (str): Full name of the market.
        timezone (str): IANA timezone identifier (e.g. ``America/New_York``).
        mic (Optional[str]): Market Identifier Code (ISO 10383, 4 characters).
        bic (Optional[str]): Business Identifier Code / SWIFT code (11 characters).
    """

    acronym: str
    name: str
    timezone: str
    mic: Optional[str] = None
    bic: Optional[str] = None


class MarketClock(BaseModel):
    """
    Clock for a specific market, including current phase information.

    Attributes:
        market (PublicMarket): The market this clock applies to.
        timestamp (datetime): The current time on the clock.
        is_market_day (bool): Whether today is a trading day for this market.
        next_market_open (datetime): Next time this market opens.
        next_market_close (datetime): Next time this market closes.
        phase (Phase): The current trading session phase.
        phase_until (datetime): When the current phase ends.
    """

    market: PublicMarket
    timestamp: datetime
    is_market_day: bool
    next_market_open: datetime
    next_market_close: datetime
    phase: Phase
    phase_until: datetime


class ClockResp(BaseModel):
    """
    Response containing clocks for one or more markets.

    Attributes:
        clocks (List[MarketClock]): One clock entry per requested market.
    """

    clocks: List[MarketClock]


class PublicCalendarResp(BaseModel):
    """
    Calendar response for a specific market.

    Attributes:
        market (PublicMarket): The market this calendar applies to.
        calendar (List[CalendarDay]): Ordered list of trading calendar days.
    """

    market: PublicMarket
    calendar: List[CalendarDay]


class USTreasury(BaseModel):
    """
    A US Treasury security.

    Attributes:
        cusip (str): CUSIP — nine-character alphanumeric identifier.
        isin (str): International Securities Identification Number.
        bond_status (BondStatus): Current status of the treasury.
        tradable (bool): Whether the treasury is tradable.
        subtype (TreasurySubtype): The treasury subtype (bill, note, bond, etc.).
        issue_date (date): The date the security was issued.
        maturity_date (date): The date the security matures.
        description (str): Full description of the treasury.
        description_short (str): Short description of the treasury.
        coupon (float): Annual interest rate as a percentage of par value.
        coupon_type (CouponType): Type of the coupon rate.
        coupon_frequency (CouponFrequency): How often the coupon is paid.
        close_price (Optional[float]): Last close price as a percentage of par.
        close_price_date (Optional[date]): Date of the close price.
        close_yield_to_maturity (Optional[float]): Yield to maturity at last close.
        close_yield_to_worst (Optional[float]): Yield to worst at last close.
        first_coupon_date (Optional[date]): Date of the first coupon payment.
        next_coupon_date (Optional[date]): Date of the next coupon payment.
        last_coupon_date (Optional[date]): Date of the last coupon payment.
    """

    cusip: str
    isin: str
    bond_status: BondStatus
    tradable: bool
    subtype: TreasurySubtype
    issue_date: date
    maturity_date: date
    description: str
    description_short: str
    coupon: float
    coupon_type: CouponType
    coupon_frequency: CouponFrequency
    close_price: Optional[float] = None
    close_price_date: Optional[date] = None
    close_yield_to_maturity: Optional[float] = None
    close_yield_to_worst: Optional[float] = None
    first_coupon_date: Optional[date] = None
    next_coupon_date: Optional[date] = None
    last_coupon_date: Optional[date] = None


class USCorporate(BaseModel):
    """
    A US corporate bond.

    Attributes:
        cusip (str): CUSIP — nine-character alphanumeric identifier.
        isin (str): International Securities Identification Number.
        bond_status (BondStatus): Current status of the bond.
        tradable (bool): Whether the bond is tradable.
        marginable (bool): Whether the bond is marginable.
        issue_date (date): Date the bond was issued.
        country_domicile (str): Two-letter country code of domicile (e.g. ``US``).
        ticker (str): Ticker symbol.
        seniority (str): Seniority of the bond.
        issuer (str): Name of the bond issuer.
        sector (str): Sector of the bond.
        description (str): Full description.
        description_short (str): Short description.
        coupon (float): Annual interest rate as a percentage of par value.
        coupon_type (CouponType): Type of coupon rate.
        coupon_frequency (CouponFrequency): How often the coupon is paid.
        perpetual (bool): Whether the bond is perpetual.
        day_count (DayCount): Day count convention for accrued interest.
        dated_date (date): Date interest starts accruing.
        issue_size (float): Total size of the bond issue in issuing currency.
        issue_price (float): Issue price as a percentage of par value.
        issue_minimum_denomination (float): Smallest purchasable unit at issuance.
        par_value (float): Amount the issuer repays at maturity.
        callable (bool): Whether the issuer can redeem before maturity.
        puttable (bool): Whether the holder can sell back before maturity.
        convertible (bool): Whether the bond can be converted to equity.
        reg_s (bool): Whether the bond falls under Regulation S.
        maturity_date (Optional[date]): Date the bond matures.
        reissue_date (Optional[date]): Date the bond was reissued.
        reissue_size (Optional[float]): Total size of the reissue.
        reissue_price (Optional[float]): Reissue price as a percentage of par.
        first_coupon_date (Optional[date]): Date of the first coupon payment.
        next_coupon_date (Optional[date]): Date of the next coupon payment.
        last_coupon_date (Optional[date]): Date of the last coupon payment.
        next_call_date (Optional[date]): Date of the next possible call.
        next_call_price (Optional[float]): Call price as a percentage of par.
        close_price (Optional[float]): Last close price as a percentage of par.
        close_price_date (Optional[date]): Date of the close price.
        close_yield_to_maturity (Optional[float]): Yield to maturity at last close.
        close_yield_to_worst (Optional[float]): Yield to worst at last close.
        accrued_interest (Optional[float]): Accrued interest in dollars per bond.
        call_type (Optional[CallType]): Type of call provision.
        sp_rating (Optional[str]): S&P credit rating (e.g. ``AAA``).
        sp_rating_date (Optional[date]): Date of the most recent S&P rating.
        sp_creditwatch (Optional[str]): S&P CreditWatch opinion.
        sp_creditwatch_date (Optional[date]): Date of the most recent CreditWatch.
        sp_outlook (Optional[SpOutlook]): S&P rating outlook.
        sp_outlook_date (Optional[date]): Date of the most recent S&P outlook.
        liquidity_micro_buy (Optional[float]): Micro liquidity score for buys (1–5).
        liquidity_micro_sell (Optional[float]): Micro liquidity score for sells (1–5).
        liquidity_micro_aggregate (Optional[float]): Micro aggregate liquidity score.
        liquidity_retail_buy (Optional[float]): Retail liquidity score for buys.
        liquidity_retail_sell (Optional[float]): Retail liquidity score for sells.
        liquidity_retail_aggregate (Optional[float]): Retail aggregate liquidity score.
        liquidity_institutional_buy (Optional[float]): Institutional buy liquidity score.
        liquidity_institutional_sell (Optional[float]): Institutional sell liquidity score.
        liquidity_institutional_aggregate (Optional[float]): Institutional aggregate score.
    """

    cusip: str
    isin: str
    bond_status: BondStatus
    tradable: bool
    marginable: bool
    issue_date: date
    country_domicile: str
    ticker: str
    seniority: str
    issuer: str
    sector: str
    description: str
    description_short: str
    coupon: float
    coupon_type: CouponType
    coupon_frequency: CouponFrequency
    perpetual: bool
    day_count: DayCount
    dated_date: date
    issue_size: float
    issue_price: float
    issue_minimum_denomination: float
    par_value: float
    callable: bool
    puttable: bool
    convertible: bool
    reg_s: bool
    maturity_date: Optional[date] = None
    reissue_date: Optional[date] = None
    reissue_size: Optional[float] = None
    reissue_price: Optional[float] = None
    first_coupon_date: Optional[date] = None
    next_coupon_date: Optional[date] = None
    last_coupon_date: Optional[date] = None
    next_call_date: Optional[date] = None
    next_call_price: Optional[float] = None
    close_price: Optional[float] = None
    close_price_date: Optional[date] = None
    close_yield_to_maturity: Optional[float] = None
    close_yield_to_worst: Optional[float] = None
    accrued_interest: Optional[float] = None
    call_type: Optional[CallType] = None
    sp_rating: Optional[str] = None
    sp_rating_date: Optional[date] = None
    sp_creditwatch: Optional[str] = None
    sp_creditwatch_date: Optional[date] = None
    sp_outlook: Optional[SpOutlook] = None
    sp_outlook_date: Optional[date] = None
    liquidity_micro_buy: Optional[float] = None
    liquidity_micro_sell: Optional[float] = None
    liquidity_micro_aggregate: Optional[float] = None
    liquidity_retail_buy: Optional[float] = None
    liquidity_retail_sell: Optional[float] = None
    liquidity_retail_aggregate: Optional[float] = None
    liquidity_institutional_buy: Optional[float] = None
    liquidity_institutional_sell: Optional[float] = None
    liquidity_institutional_aggregate: Optional[float] = None


class USTreasuriesResp(BaseModel):
    """
    Response containing a list of US Treasury securities.

    Attributes:
        us_treasuries (List[USTreasury]): The list of treasury securities.
    """

    us_treasuries: List[USTreasury]


class USCorporatesResp(BaseModel):
    """
    Response containing a list of US corporate bonds.

    Attributes:
        us_corporates (List[USCorporate]): The list of corporate bonds.
    """

    us_corporates: List[USCorporate]


class WalletFeeEstimate(BaseModel):
    """
    Estimated gas fee for a proposed crypto transfer transaction.

    Attributes:
        fee (Optional[str]): The estimated total fee amount as a string.
        network_fee (Optional[str]): The estimated network fee amount as a string.
    """

    fee: Optional[str] = None
    network_fee: Optional[str] = None
