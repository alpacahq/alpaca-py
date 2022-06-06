from datetime import datetime, date
from typing import Optional
from uuid import UUID

from .models import ValidateBaseModel as BaseModel

from ..enums import (
    ActivityType,
    NonTradeActivityStatus,
    OrderStatus,
    OrderSide,
    TradeActivityType,
    AccountStatus,
)


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


class TradeAccount(BaseModel):
    """
    Represents trading account information for an Account.

    Attributes:
        id (UUID): The account ID
        account_number (str): The account number
        status (AccountStatus): The current status of the account
        crypto_status (Optional[AccountStatus]): The status of the account in regards to trading crypto. Only present if
          crypto trading is enabled for your brokerage account.
        currency (Optional[str]): Currently will always be the value "USD".
        buying_power (str): Current available cash buying power. If multiplier = 2 then
          buying_power = max(equity-initial_margin(0) * 2). If multiplier = 1 then buying_power = cash.
        regt_buying_power (str): User’s buying power under Regulation T
          (excess equity - (equity - margin value) - * margin multiplier)
        daytrading_buying_power (str): The buying power for day trades for the account
        non_marginable_buying_power (str): The non marginable buying power for the account
        cash (str): Cash balance in the account
        accrued_fees (str): Fees accrued in this account
        pending_transfer_out (Optional[str]): Cash pending transfer out of this account
        pending_transfer_in (Optional[str]): Cash pending transfer into this account
        portfolio_value (str): Total value of cash + holding positions.
          (This field is deprecated. It is equivalent to the equity field.)
        pattern_day_trader (bool): Whether the account is flagged as pattern day trader or not.
        trading_blocked (bool): If true, the account is not allowed to place orders.
        transfers_blocked (bool): If true, the account is not allowed to request money transfers.
        account_blocked (bool): If true, the account activity by user is prohibited.
        created_at (datetime): Timestamp this account was created at
        trade_suspended_by_user (bool): If true, the account is not allowed to place orders.
        multiplier (str): Multiplier value for this account.
        shorting_enabled (bool): Flag to denote whether or not the account is permitted to short
        equity (str): This value is cash + long_market_value + short_market_value. This value isn't calculated in the
          SDK it is computed on the server and we return the raw value here.
        last_equity (str): Equity as of previous trading day at 16:00:00 ET
        long_market_value (str): Real-time MtM value of all long positions held in the account
        short_market_value (str): Real-time MtM value of all short positions held in the account
        initial_margin (str): Reg T initial margin requirement
        maintenance_margin (str): Maintenance margin requirement
        last_maintenance_margin (str): Maintenance margin requirement on the previous trading day
        sma (str): Value of Special Memorandum Account (will be used at a later date to provide additional buying_power)
        daytrade_count (int): The current number of daytrades that have been made in the last 5 trading days
          (inclusive of today)
    """

    id: UUID
    account_number: str
    status: AccountStatus
    crypto_status: Optional[AccountStatus]
    currency: Optional[str]
    buying_power: str
    regt_buying_power: str
    daytrading_buying_power: str
    non_marginable_buying_power: str
    cash: str
    accrued_fees: str
    pending_transfer_out: Optional[str]
    pending_transfer_in: Optional[str]
    portfolio_value: str
    pattern_day_trader: bool
    trading_blocked: bool
    transfers_blocked: bool
    account_blocked: bool
    created_at: datetime
    trade_suspended_by_user: bool
    multiplier: str
    shorting_enabled: bool
    equity: str
    last_equity: str
    long_market_value: str
    short_market_value: str
    initial_margin: str
    maintenance_margin: str
    last_maintenance_margin: str
    sma: str
    daytrade_count: int
