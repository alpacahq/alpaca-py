from enum import Enum


class ActivityType(str, Enum):
    """
    Represents what kind of Activity an instance of TradeActivity or NonTradeActivity is.

    Please see https://alpaca.markets/docs/api-references/broker-api/accounts/account-activities/#enumactivitytype
    for descriptions of each of the types
    """

    FILL = "FILL"
    ACATC = "ACATC"
    ACATS = "ACATS"
    CFEE = "CFEE"
    CIL = "CIL"
    CSD = "CSD"
    CSW = "CSW"
    DIV = "DIV"
    DIVCGL = "DIVCGL"
    DIVCGS = "DIVCGS"
    DIVNRA = "DIVNRA"
    DIVROC = "DIVROC"
    DIVTXEX = "DIVTXEX"
    DIVWH = "DIVWH"
    EXTRD = "EXTRD"
    FEE = "FEE"
    FXTRD = "FXTRD"
    INT = "INT"
    INTPNL = "INTPNL"
    JNLC = "JNLC"
    JNLS = "JNLS"
    MA = "MA"
    MEM = "MEM"
    NC = "NC"
    OCT = "OCT"
    OPASN = "OPASN"
    OPCSH = "OPCSH"
    OPEXC = "OPEXC"
    OPEXP = "OPEXP"
    OPTRD = "OPTRD"
    PTC = "PTC"
    REORG = "REORG"
    SPIN = "SPIN"
    SPLIT = "SPLIT"
    SWP = "SWP"
    VOF = "VOF"
    WH = "WH"

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

    The order classes supported by Alpaca vary based on the order's security type.
    The following provides a comprehensive breakdown of the supported order classes for each category:
    - Equity trading: simple (or ""), oco, oto, bracket.
    - Options trading: simple (or ""), mleg (required for multi-leg complex options strategies).
    - Crypto trading: simple (or "").
    """

    SIMPLE = "simple"
    MLEG = "mleg"
    BRACKET = "bracket"
    OCO = "oco"
    OTO = "oto"


class OrderType(str, Enum):
    """
    Represents what type of order this is.

    The order types supported by Alpaca vary based on the order's security type.
    The following provides a comprehensive breakdown of the supported order types for each category:
    - Equity trading: market, limit, stop, stop_limit, trailing_stop.
    - Options trading: market, limit, stop, stop_limit.
    - Crypto trading: market, limit, stop_limit.
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
    PENDING_REVIEW = "pending_review"
    ACCEPTED = "accepted"
    PENDING_NEW = "pending_new"
    ACCEPTED_FOR_BIDDING = "accepted_for_bidding"
    STOPPED = "stopped"
    REJECTED = "rejected"
    SUSPENDED = "suspended"
    CALCULATED = "calculated"
    HELD = "held"


class AssetClass(str, Enum):
    """
    This represents the category to which the asset belongs to.
    It serves to identify the nature of the financial instrument, with options
    including "us_equity" for U.S. equities, "us_option" for U.S. options,
    and "crypto" for cryptocurrencies.
    """

    US_EQUITY = "us_equity"
    US_OPTION = "us_option"
    CRYPTO = "crypto"
    CRYPTO_PERP = "crypto_perp"


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
    ASCX = "ASCX"
    BATS = "BATS"
    NYSE = "NYSE"
    NASDAQ = "NASDAQ"
    NYSEARCA = "NYSEARCA"
    FTXU = "FTXU"
    CBSE = "CBSE"
    GNSS = "GNSS"
    ERSX = "ERSX"
    OTC = "OTC"
    CRYPTO = "CRYPTO"
    EMPTY = ""


class PositionSide(str, Enum):
    """
    Represents what side this position is.
    """

    SHORT = "short"
    LONG = "long"


class TimeInForce(str, Enum):
    """
    Represents the various time in force options for an Order.

    The Time-In-Force values supported by Alpaca vary based on the order's security type. Here is a breakdown of the supported TIFs for each specific security type:
    - Equity trading: day, gtc, opg, cls, ioc, fok.
    - Options trading: day.
    - Crypto trading: gtc, ioc.
    Below are the descriptions of each TIF:
    - day: A day order is eligible for execution only on the day it is live. By default, the order is only valid during Regular Trading Hours (9:30am - 4:00pm ET). If unfilled after the closing auction, it is automatically canceled. If submitted after the close, it is queued and submitted the following trading day. However, if marked as eligible for extended hours, the order can also execute during supported extended hours.
    - gtc: The order is good until canceled. Non-marketable GTC limit orders are subject to price adjustments to offset corporate actions affecting the issue. We do not currently support Do Not Reduce(DNR) orders to opt out of such price adjustments.
    - opg: Use this TIF with a market/limit order type to submit “market on open” (MOO) and “limit on open” (LOO) orders. This order is eligible to execute only in the market opening auction. Any unfilled orders after the open will be cancelled. OPG orders submitted after 9:28am but before 7:00pm ET will be rejected. OPG orders submitted after 7:00pm will be queued and routed to the following day’s opening auction. On open/on close orders are routed to the primary exchange. Such orders do not necessarily execute exactly at 9:30am / 4:00pm ET but execute per the exchange’s auction rules.
    - cls: Use this TIF with a market/limit order type to submit “market on close” (MOC) and “limit on close” (LOC) orders. This order is eligible to execute only in the market closing auction. Any unfilled orders after the close will be cancelled. CLS orders submitted after 3:50pm but before 7:00pm ET will be rejected. CLS orders submitted after 7:00pm will be queued and routed to the following day’s closing auction. Only available with API v2.
    - ioc: An Immediate Or Cancel (IOC) order requires all or part of the order to be executed immediately. Any unfilled portion of the order is canceled. Only available with API v2. Most market makers who receive IOC orders will attempt to fill the order on a principal basis only, and cancel any unfilled balance. On occasion, this can result in the entire order being cancelled if the market maker does not have any existing inventory of the security in question.
    - fok: A Fill or Kill (FOK) order is only executed if the entire order quantity can be filled, otherwise the order is canceled. Only available with API v2.
    """

    DAY = "day"
    GTC = "gtc"
    OPG = "opg"
    CLS = "cls"
    IOC = "ioc"
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


class AccountStatus(str, Enum):
    """
    The various statuses each brokerage account can take during its lifetime

    see https://alpaca.markets/docs/broker/api-references/accounts/accounts/#account-status
    """

    ACCOUNT_CLOSED = "ACCOUNT_CLOSED"
    ACCOUNT_UPDATED = "ACCOUNT_UPDATED"
    ACTION_REQUIRED = "ACTION_REQUIRED"
    ACTIVE = "ACTIVE"
    AML_REVIEW = "AML_REVIEW"
    APPROVAL_PENDING = "APPROVAL_PENDING"
    APPROVED = "APPROVED"
    DISABLED = "DISABLED"
    DISABLE_PENDING = "DISABLE_PENDING"
    EDITED = "EDITED"
    INACTIVE = "INACTIVE"
    KYC_SUBMITTED = "KYC_SUBMITTED"
    LIMITED = "LIMITED"
    ONBOARDING = "ONBOARDING"
    PAPER_ONLY = "PAPER_ONLY"
    REAPPROVAL_PENDING = "REAPPROVAL_PENDING"
    REJECTED = "REJECTED"
    RESUBMITTED = "RESUBMITTED"
    SIGNED_UP = "SIGNED_UP"
    SUBMISSION_FAILED = "SUBMISSION_FAILED"
    SUBMITTED = "SUBMITTED"


class CorporateActionDateType(str, Enum):
    DECLARATION_DATE = "declaration_date"
    EX_DATE = "ex_date"
    RECORD_DATE = "record_date"
    PAYABLE_DATE = "payable_date"


class TradeEvent(str, Enum):
    ACCEPTED = "accepted"
    CANCELED = "canceled"
    EXPIRED = "expired"
    FILL = "fill"
    NEW = "new"
    PARTIAL_FILL = "partial_fill"
    PENDING_CANCEL = "pending_cancel"
    PENDING_NEW = "pending_new"
    PENDING_REPLACE = "pending_replace"
    REJECTED = "rejected"
    REPLACED = "replaced"
    RESTATED = "restated"


class QueryOrderStatus(str, Enum):
    OPEN = "open"
    CLOSED = "closed"
    ALL = "all"


class DTBPCheck(str, Enum):
    """
    Specifies when to run a DTBP check for an account.

    NOTE: These values are currently the same as PDTCheck however they are not guaranteed to be in sync the future

    please see https://alpaca.markets/docs/api-references/broker-api/trading/trading-configurations/#attributes
    for more info.
    """

    BOTH = "both"
    ENTRY = "entry"
    EXIT = "exit"


class PDTCheck(str, Enum):
    """
    Specifies when to run a PDT check for an account.

    NOTE: These values are currently the same as DTBPCheck however they are not guaranteed to be in sync the future

    please see https://alpaca.markets/docs/api-references/broker-api/trading/trading-configurations/#attributes
    for more info.
    """

    BOTH = "both"
    ENTRY = "entry"
    EXIT = "exit"


class TradeConfirmationEmail(str, Enum):
    """
    Used for controlling when an Account will receive a trade confirmation email.

    please see https://docs.alpaca.markets/reference/getaccountconfig
    for more info.
    """

    ALL = "all"
    NONE = "none"


class ContractType(str, Enum):
    """
    Represents the contract type of options
    """

    CALL = "call"
    PUT = "put"


class ExerciseStyle(str, Enum):
    """
    Represents the exercise style of options
    """

    AMERICAN = "american"
    EUROPEAN = "european"


class ActivityCategory(str, Enum):
    """
    Represents the category of an Activity
    """

    TRADE_ACTIVITY = "trade_activity"
    NON_TRADE_ACTIVITY = "non_trade_activity"


class PositionIntent(str, Enum):
    """
    Represents what side this order was executed on.
    """

    BUY_TO_OPEN = "buy_to_open"
    BUY_TO_CLOSE = "buy_to_close"
    SELL_TO_OPEN = "sell_to_open"
    SELL_TO_CLOSE = "sell_to_close"
