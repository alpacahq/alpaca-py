from alpaca.common.models import ModelWithID, ValidateBaseModel as BaseModel
from uuid import UUID
from datetime import datetime, date
from typing import Any, Optional, List, Union, Dict
from alpaca.trading.enums import (
    AssetClass,
    AssetStatus,
    AssetExchange,
    ContractType,
    DTBPCheck,
    ExerciseStyle,
    OrderStatus,
    OrderType,
    OrderClass,
    PDTCheck,
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
)
from pydantic import Field


class Asset(ModelWithID):
    """
    Represents a security. Some Assets are not tradable with Alpaca. These Assets are
    marked with the flag `tradable=false`.

    For more info, visit https://alpaca.markets/docs/api-references/trading-api/assets/

    Attributes:
        id (UUID): Unique id of asset
        asset_class (AssetClass): The name of the asset class.
        exchange (AssetExchange): Which exchange this asset is available through.
        symbol (str): The symbol identifier of the asset.
        name (Optional[str]): The name of the asset.
        status (AssetStatus): The active status of the asset.
        tradable (bool): Whether the asset can be traded.
        marginable (bool): Whether the asset can be traded on margin.
        shortable (bool): Whether the asset can be shorted.
        easy_to_borrow (bool): When shorting, whether the asset is easy to borrow
        fractionable (bool): Whether fractional shares are available
        attributes (Optional[List[str]]): One of ptp_no_exception or ptp_with_exception. It will include unique characteristics of the asset here.
    """

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
    min_order_size: Optional[float] = None
    min_trade_increment: Optional[float] = None
    price_increment: Optional[float] = None
    maintenance_margin_requirement: Optional[float] = None
    attributes: Optional[List[str]] = None


class USDPositionValues(BaseModel):
    """
    Represents an open long or short holding in an asset in USD.

    Attributes:
        avg_entry_price (str): The average entry price of the position.
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

    avg_entry_price: str
    market_value: str
    cost_basis: str
    unrealized_pl: str
    unrealized_plpc: str
    unrealized_intraday_pl: str
    unrealized_intraday_plpc: str
    current_price: str
    lastday_price: str
    change_today: str


class Position(BaseModel):
    """
    Represents an open long or short holding in an asset.

    Attributes:
        asset_id (UUID): ID of the asset.
        symbol (str): Symbol of the asset.
        exchange (AssetExchange): Exchange name of the asset.
        asset_class (AssetClass): Name of the asset's asset class.
        asset_marginable (Optional[bool]): Indicates if this asset is marginable.
        avg_entry_price (str): The average entry price of the position.
        qty (str): The number of shares of the position.
        side (PositionSide): "long" or "short" representing the side of the position.
        market_value (Optional[str]): Total dollar amount of the position.
        cost_basis (str): Total cost basis in dollars.
        unrealized_pl (Optional[str]): Unrealized profit/loss in dollars.
        unrealized_plpc (Optional[str]): Unrealized profit/loss percent.
        unrealized_intraday_pl (Optional[str]): Unrealized profit/loss in dollars for the day.
        unrealized_intraday_plpc (Optional[str]): Unrealized profit/loss percent for the day.
        current_price (Optional[str]): Current asset price per share.
        lastday_price (Optional[str]): Last day’s asset price per share based on the closing value of the last trading day.
        change_today (Optional[str]): Percent change from last day's price.
        swap_rate (Optional[str]): Swap rate is the exchange rate (without mark-up) used to convert the price into local currency or crypto asset.
        avg_entry_swap_rate (Optional[str]): The average exchange rate the price was converted into the local currency at.
        usd (USDPositionValues): Represents the position in USD values.
        qty_available (Optional[str]): Total number of shares available minus open orders.

    """

    asset_id: UUID
    symbol: str
    exchange: AssetExchange
    asset_class: AssetClass
    asset_marginable: Optional[bool] = None
    avg_entry_price: str
    qty: str
    side: PositionSide
    market_value: Optional[str] = None
    cost_basis: str
    unrealized_pl: Optional[str] = None
    unrealized_plpc: Optional[str] = None
    unrealized_intraday_pl: Optional[str] = None
    unrealized_intraday_plpc: Optional[str] = None
    current_price: Optional[str] = None
    lastday_price: Optional[str] = None
    change_today: Optional[str] = None
    swap_rate: Optional[str] = None
    avg_entry_swap_rate: Optional[str] = None
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
        id (UUID): order ID generated by Alpaca.
        client_order_id (str): Client unique order ID
        created_at (datetime): Timestamp when the order was created.
        updated_at (datetime): Timestamp when the order was last updated.
        submitted_at (datetime): Timestamp when the order was submitted.
        filled_at (Optional[datetime]): Timestamp when the order was filled.
        expired_at (Optional[datetime]): Timestamp when the order expired at.
        canceled_at (Optional[datetime]): Timestamp when the order was canceled.
        failed_at (Optional[datetime]): Timestamp when the order failed at.
        replaced_at (Optional[datetime]): Timestamp when the order was replaced by a new order.
        replaced_by (Optional[UUID]): ID of order that replaces this order.
        replaces (Optional[UUID]): ID of order which this order replaces.
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
        time_in_force (TimeInForce): Length of time the order is in force.
        limit_price (Optional[str]): Limit price of the order.
        stop_price (Optional[str]): Stop price of the order.
        status (OrderStatus): The status of the order.
        extended_hours (bool): If true, eligible for execution outside regular trading hours.
        legs (Optional[List[alpaca.trading.models.Order]]): When querying non-simple order_class orders in a nested style,
          an array of order entities associated with this order. Otherwise, null.
        trail_percent (Optional[str]): The percent value away from the high water mark for trailing stop orders.
        trail_price (Optional[str]): The dollar value away from the high water mark for trailing stop orders.
        hwm (Optional[str]): The highest (lowest) market price seen since the trailing stop order was submitted.
    """

    client_order_id: str
    created_at: datetime
    updated_at: datetime
    submitted_at: datetime
    filled_at: Optional[datetime] = None
    expired_at: Optional[datetime] = None
    canceled_at: Optional[datetime] = None
    failed_at: Optional[datetime] = None
    replaced_at: Optional[datetime] = None
    replaced_by: Optional[UUID] = None
    replaces: Optional[UUID] = None
    asset_id: UUID
    symbol: str
    asset_class: AssetClass
    notional: Optional[str] = None
    qty: Optional[Union[str, float]] = None
    filled_qty: Optional[Union[str, float]] = None
    filled_avg_price: Optional[Union[str, float]] = None
    order_class: OrderClass
    order_type: OrderType
    type: OrderType
    side: OrderSide
    time_in_force: TimeInForce
    limit_price: Optional[Union[str, float]] = None
    stop_price: Optional[Union[str, float]] = None
    status: OrderStatus
    extended_hours: bool
    legs: Optional[List["Order"]] = None
    trail_percent: Optional[str] = None
    trail_price: Optional[str] = None
    hwm: Optional[str] = None

    def __init__(self, **data: Any) -> None:
        if "order_class" not in data or data["order_class"] == "":
            data["order_class"] = OrderClass.SIMPLE

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
        timeframe (str): Time window size of each data element.
    """

    timestamp: List[int]
    equity: List[float]
    profit_loss: List[float]
    profit_loss_pct: List[Optional[float]]
    base_value: float
    timeframe: str


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
        account_number (str): The account number
        status (AccountStatus): The current status of the account
        crypto_status (Optional[AccountStatus]): The status of the account in regards to trading crypto. Only present if
          crypto trading is enabled for your brokerage account.
        currency (Optional[str]): Currently will always be the value "USD".
        buying_power (Optional[str]): Current available cash buying power. If multiplier = 2 then
          buying_power = max(equity-initial_margin(0) * 2). If multiplier = 1 then buying_power = cash.
        regt_buying_power (Optional[str]): User’s buying power under Regulation T
          (excess equity - (equity - margin value) - * margin multiplier)
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
        last_maintenance_margin (Optional[str]): Maintenance margin requirement on the previous trading day
        sma (Optional[str]): Value of Special Memorandum Account (will be used at a later date to provide additional buying_power)
        daytrade_count (Optional[int]): The current number of daytrades that have been made in the last 5 trading days
          (inclusive of today)
        options_buying_power (Optional[str]): Your buying power for options trading
        options_approved_level (Optional[int]): The options trading level that was approved for this account.
          0=disabled, 1=Covered Call/Cash-Secured Put, 2=Long Call/Put.
        options_trading_level (Optional[int]): The effective options trading level of the account. This is the minimum between account options_approved_level and account configurations max_options_trading_level.
          0=disabled, 1=Covered Call/Cash-Secured Put, 2=Long
    """

    account_number: str
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
    last_maintenance_margin: Optional[str] = None
    sma: Optional[str] = None
    daytrade_count: Optional[int] = None
    options_buying_power: Optional[str] = None
    options_approved_level: Optional[int] = None
    options_trading_level: Optional[int] = None


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
        max_options_trading_level (Optional[int]): The desired maximum options trading level. 0=disabled, 1=Covered Call/Cash-Secured Put, 2=Long Call/Put.
    """

    dtbp_check: DTBPCheck
    fractional_trading: bool
    max_margin_multiplier: str
    no_shorting: bool
    pdt_check: PDTCheck
    suspend_trade: bool
    trade_confirm_email: TradeConfirmationEmail
    ptp_no_exception_entry: bool
    max_options_trading_level: Optional[int] = None


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
        id (str): The unique identifier of the option contract.
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
        strike_price (float): The strike price of the option contract.
        size (str): The size of the option contract. Usually contracts have size=100.
        open_interest (Optional[str]): The open interest of the option contract.
        open_interest_date (Optional[date]): The date of the open interest data.
        close_price (Optional[str]): The close price of the option contract.
        close_price_date (Optional[date]): The date of the close price data.
    """

    id: str
    symbol: str
    name: str
    status: AssetStatus
    tradable: bool
    expiration_date: date
    root_symbol: str
    underlying_symbol: str
    underlying_asset_id: UUID
    type: ContractType
    style: ExerciseStyle
    strike_price: float
    size: str
    open_interest: Optional[str] = None
    open_interest_date: Optional[date] = None
    close_price: Optional[str] = None
    close_price_date: Optional[date] = None


class OptionContractsResponse(BaseModel):
    """
    Represents a response from the option contracts endpoint.

    Attributes:
        option_contracts (Optional[List[OptionContract]]): The list of option contracts.
        next_page_token (Optional[str]): Pagination token for next page.
    """

    option_contracts: Optional[List[OptionContract]] = None
    next_page_token: Optional[str] = None
