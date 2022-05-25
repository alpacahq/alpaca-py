from enum import Enum


class BaseURL(str, Enum):
    """Base urls for API endpoints"""

    BROKER_SANDBOX = "https://broker-api.sandbox.alpaca.markets"
    BROKER_PRODUCTION = "https://broker-api.alpaca.markets"
    TRADING_PAPER = "https://paper-api.alpaca.markets"
    TRADING_LIVE = "https://api.alpaca.markets"
    DATA = "https://data.alpaca.markets"
    MARKET_DATA_LIVE = "wss://stream.data.alpaca.markets"


class PaginationType(str, Enum):
    """
    An enum for choosing what type of pagination of results you'd like for BrokerClient functions that support
    pagination.

    Attributes:
        NONE: Requests that we perform no pagination of results and just return the single response the API gave us.
        FULL: Requests that we perform all the pagination and return just a single List/dict/etc containing all the
          results. This is the default for most functions.
        ITERATOR: Requests that we return an Iterator that yields one "page" of results at a time
    """

    NONE = "none"
    FULL = "full"
    ITERATOR = "iterator"


class Sort(str, Enum):
    ASC = "asc"
    DESC = "desc"


class ActivityType(str, Enum):
    """
    Represents what kind of Activity an instance of TradeActivity or NonTradeActivity is.

    Please see https://alpaca.markets/docs/api-references/broker-api/accounts/account-activities/#enumactivitytype
    for descriptions of each of the types
    """

    FILL = "FILL"
    ACATC = "ACATC"
    ACATS = "ACATS"
    CIL = "CIL"
    CSD = "CSD"
    CSW = "CSW"
    DIV = "DIV"
    DIVCGL = "DIVCGL"
    DIVCGS = "DIVCGS"
    DIVNRA = "DIVNRA"
    DIVROC = "DIVROC"
    DIVTXEX = "DIVTXEX"
    FEE = "FEE"
    INT = "INT"
    JNLC = "JNLC"
    JNLS = "JNLS"
    MA = "MA"
    PTC = "PTC"
    REORG = "REORG"
    SPIN = "SPIN"
    SPLIT = "SPLIT"

    def is_trade_activity(self) -> bool:
        """
        A simple check to see if the ActivityType represents a type that belongs to TradeActivity's.

        Currently, the check is just against FILL. However, this might change in the future so we are adding this helper
        func here to help ease against future changes.

        Returns:
            bool: returns true if this ActivityType represents a TradeActivity
        """

        return self.value == self.FILL

    @staticmethod
    def is_str_trade_activity(value: str) -> bool:
        """
        similar to is_trade_activity but for raw data that hasn't been parsed into an enum yet.
        Useful for deserialization.

        Args:
            value (str): Value to check to see if it would be a valid ActivityType for a TradeActivity

        Returns:
            bool: returns true if `value` would represent a TradeActivity ActivityType
        """

        return value == ActivityType.FILL


class TradeActivityType(str, Enum):
    """
    Represents the type of TradeActivity.

    Please see https://alpaca.markets/docs/api-references/broker-api/accounts/account-activities/#attributes
    """

    PARTIAL_FILL = "partial_fill"
    FILL = "fill"


class NonTradeActivityStatus(str, Enum):
    """
    Represents the status of a NonTradeActivity.

    Please see https://alpaca.markets/docs/api-references/broker-api/accounts/account-activities/#enumaccountactivity
    for more info.
    """

    EXECUTED = "executed"
    CORRECT = "correct"
    CANCELED = "canceled"


class OrderClass(str, Enum):
    """
    Represents what class of order this is.
    """

    SIMPLE = "simple"
    BRACKET = "bracket"
    OCO = "oco"
    OTO = "oto"


class OrderType(str, Enum):
    """
    Represents what type of roder this is.
    """

    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"
    TRAILING_STOP = "trailing_stop"


class OrderSide(str, Enum):
    """
    Represents what side this order was executed on.
    """

    BUY = "buy"
    SELL = "sell"


class OrderStatus(str, Enum):
    """
    Represents the various states an Order can be in.

    please see https://alpaca.markets/docs/api-references/broker-api/trading/orders/#order-status for more info
    """

    NEW = "new"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    DONE_FOR_DAY = "done_for_day"
    CANCELED = "canceled"
    EXPIRED = "expired"
    REPLACED = "replaced"
    PENDING_CANCEL = "pending_cancel"
    PENDING_REPLACE = "pending_replace"
    ACCEPTED = "accepted"
    PENDING_NEW = "pending_new"
    ACCEPTED_FOR_BIDDING = "accepted_for_bidding"
    STOPPED = "stopped"
    REJECTED = "rejected"
    SUSPENDED = "suspended"
    CALCULATED = "calculated"


class AssetClass(str, Enum):
    """
    Represents what class of asset this is.
    """

    US_EQUITY = "us_equity"
    CRYPTO = "crypto"


class AssetStatus(str, Enum):
    """
    Represents the various states for an Asset's lifecycle
    """

    ACTIVE = "active"
    INACTIVE = "inactive"


class AssetExchange(str, Enum):
    """
    Represents the current exchanges Alpaca supports.
    """

    AMEX = "AMEX"
    ARCA = "ARCA"
    BATS = "BATS"
    NYSE = "NYSE"
    NASDAQ = "NASDAQ"
    NYSEARCA = "NYSEARCA"


class PositionSide(str, Enum):
    """
    Represents what side this position is.
    """

    SHORT = "short"
    LONG = "long"


class TimeInForce(str, Enum):
    """
    Represents the various time in force options for an Order.
    """

    DAY = "day"
    GTG = "gtg"
    OPG = "opg"
    CLS = "cls"
    IOC = "iok"
    FOK = "fok"


class CorporateActionType(str, Enum):
    """
    The general types of corporate action events.

    Learn more here: https://alpaca.markets/docs/api-references/trading-api/corporate-actions-announcements/
    """

    DIVIDEND = "dividend"
    MERGER = "merger"
    SPINOFF = "spinoff"
    SPLIT = "split"


class CorporateActionSubType(str, Enum):
    """
    The specific types of corporate actions. Each subtype is related to CorporateActionType.

    Learn more here: https://alpaca.markets/docs/api-references/trading-api/corporate-actions-announcements/
    """

    CASH = "cash"
    STOCK = "stock"
    MERGER_UPDATE = "merger_update"
    MERGER_COMPLETION = "merger_completion"
    SPINOFF = "spinoff"
    STOCK_SPLIT = "stock_split"
    UNIT_SPLIT = "unit_split"
    REVERSE_SPLIT = "reverse_split"
    RECAPITALIZATION = "recapitalization"
