from enum import Enum


class ActivityType(str, Enum):
    """
    Represents the type of account activity returned by the Trading API.

    Please see https://alpaca.markets/docs/api-references/trading-api/account-activities/
    for descriptions of each of the types
    """

    FILL = "FILL"
    TRANS = "TRANS"
    MISC = "MISC"
    ACATC = "ACATC"
    ACATS = "ACATS"
    CFEE = "CFEE"
    CGD = "CGD"
    CSD = "CSD"
    CSW = "CSW"
    DIV = "DIV"
    DIVCGL = "DIVCGL"
    DIVCGS = "DIVCGS"
    DIVFEE = "DIVFEE"
    DIVFT = "DIVFT"
    DIVNRA = "DIVNRA"
    DIVROC = "DIVROC"
    DIVTW = "DIVTW"
    DIVTXEX = "DIVTXEX"
    FEE = "FEE"
    INT = "INT"
    INTNRA = "INTNRA"
    INTTW = "INTTW"
    JNL = "JNL"
    JNLC = "JNLC"
    JNLS = "JNLS"
    MA = "MA"
    NC = "NC"
    OPASN = "OPASN"
    OPCA = "OPCA"
    OPCSH = "OPCSH"
    OPEXC = "OPEXC"
    OPEXP = "OPEXP"
    OPTRD = "OPTRD"
    PTC = "PTC"
    PTR = "PTR"
    REORG = "REORG"
    SPIN = "SPIN"
    SPLIT = "SPLIT"
    FOPT = "FOPT"

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
    EMPTY = ""


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
    IPO = "ipo"


class AssetStatus(str, Enum):
    """
    Represents the various states for an Asset's lifecycle
    """

    ACTIVE = "active"
    INACTIVE = "inactive"


class LocateStatus(str, Enum):
    """
    Represents the lifecycle status of a locate request.
    """

    ACTIVE = "active"
    EXPIRED = "expired"
    REJECTED = "rejected"


class LocateErrorCode(str, Enum):
    """
    Represents machine-readable error codes returned by the Locates API.
    """

    INVALID_INPUT = "invalid_input"
    INVALID_REQUEST_BODY = "invalid_request_body"
    INVALID_LIMIT_PRICE = "invalid_limit_price"
    INVALID_SYMBOLS = "invalid_symbols"
    SYMBOL_NOT_FOUND = "symbol_not_found"
    SECURITY_NOT_FOUND = "security_not_found"
    INSUFFICIENT_BUYING_POWER = "insufficient_buying_power"
    EASY_TO_BORROW = "easy_to_borrow"
    THRESHOLD_SECURITY = "threshold_security"


class LocateQuoteErrorCode(str, Enum):
    """
    Represents machine-readable quote-level error codes returned by the Locates API.
    """

    SYMBOL_NOT_FOUND = "symbol_not_found"
    EASY_TO_BORROW = "easy_to_borrow"
    THRESHOLD_SECURITY = "threshold_security"
    CORPORATE_ACTION = "corporate_action"


class AssetBorrowStatus(str, Enum):
    """
    Borrow status for US equity assets. This field is omitted for non-US-equity assets.
    """

    EASY_TO_BORROW = "easy_to_borrow"
    HARD_TO_BORROW = "hard_to_borrow"


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
    OTC = "OTC"
    CRYPTO = "CRYPTO"


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

    INACTIVE = "INACTIVE"
    PAPER_ONLY = "PAPER_ONLY"
    ONBOARDING = "ONBOARDING"
    SUBMISSION_FAILED = "SUBMISSION_FAILED"
    SUBMITTED = "SUBMITTED"
    ACCOUNT_UPDATED = "ACCOUNT_UPDATED"
    APPROVAL_PENDING = "APPROVAL_PENDING"
    ACTIVE = "ACTIVE"
    REJECTED = "REJECTED"
    ACCOUNT_CLOSED = "ACCOUNT_CLOSED"
    APPROVED = "APPROVED"
    ACCOUNT_CLOSED_PENDING = "ACCOUNT_CLOSED_PENDING"
    ACTION_REQUIRED = "ACTION_REQUIRED"
    LIMITED = "LIMITED"


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


class ActivitySubType(str, Enum):
    """
    Represents a more specific classification to the activity_type field.
    This field is optional and may not always be populated, depending on the
    activity type and the available data.

    Values are grouped by the parent activity_type they belong to.
    OPCA sub-types that contain a dot separator are rendered with an underscore
    in the Python name (e.g. DIV_CDIV = "DIV.CDIV").
    """

    # DIV — Dividend
    CDIV = "CDIV"
    SDIV = "SDIV"
    SPD = "SPD"

    # FEE — Fee-related
    REG = "REG"
    TAF = "TAF"
    LCT = "LCT"
    ORF = "ORF"
    OCC = "OCC"
    NRC = "NRC"
    NRV = "NRV"
    COM = "COM"
    CAT = "CAT"

    # INT — Interest
    MGN = "MGN"
    CDT = "CDT"
    SWP = "SWP"
    QII = "QII"

    # MA — Merger and Acquisition
    CMA = "CMA"
    SMA = "SMA"
    SCMA = "SCMA"

    # NC — Name Change
    SNC = "SNC"
    CNC = "CNC"
    SCNC = "SCNC"

    # OPCA — Option Corporate Action (dot-separated values)
    DIV_CDIV = "DIV.CDIV"
    DIV_SDIV = "DIV.SDIV"
    MA_CMA = "MA.CMA"
    MA_SMA = "MA.SMA"
    MA_SCMA = "MA.SCMA"
    NC_CNC = "NC.CNC"
    NC_SNC = "NC.SNC"
    NC_SCNC = "NC.SCNC"
    SPIN = "SPIN"
    SPLIT_FSPLIT = "SPLIT.FSPLIT"
    SPLIT_RSPLIT = "SPLIT.RSPLIT"
    SPLIT_USPLIT = "SPLIT.USPLIT"

    # REORG — Reorganization
    WRM = "WRM"

    # SPLIT — Stock Split
    FSPLIT = "FSPLIT"
    RSPLIT = "RSPLIT"
    USPLIT = "USPLIT"

    # VOF — Voluntary Offering
    VTND = "VTND"
    VWRT = "VWRT"
    VRGT = "VRGT"
    VEXH = "VEXH"

    # WH — Withholding
    SWH = "SWH"
    FWH = "FWH"
    SLWH = "SLWH"


class ExecutionType(str, Enum):
    """
    Execution type for a trade activity event (ActivityV2DetailTRD).

    Values correspond to the ``execution_type`` field in the ActivityV2DetailTRD schema.
    """

    FILL = "fill"
    TRADE_CORRECT = "trade_correct"
    TRADE_BUST = "trade_bust"


class AdvancedInstructionsAlgorithm(str, Enum):
    """
    Routing algorithm for the Alpaca Elite Smart Router (AdvancedInstructions).

    See https://docs.alpaca.markets/docs/alpaca-elite-smart-router
    """

    DMA = "DMA"
    TWAP = "TWAP"
    VWAP = "VWAP"


class AdvancedInstructionsDestination(str, Enum):
    """
    Target exchange destination for the Alpaca Elite Smart Router (AdvancedInstructions).

    See https://docs.alpaca.markets/docs/alpaca-elite-smart-router
    """

    NYSE = "NYSE"
    NASDAQ = "NASDAQ"
    ARCA = "ARCA"


class CreateCryptoTransferRequestChain(str, Enum):
    """
    Blockchain network for a crypto withdrawal transfer (CreateCryptoTransferRequest).
    """

    SOL = "SOL"
    ETH = "ETH"
    BTC = "BTC"
    XRP = "XRP"
    ARB = "ARB"


class TransferDirection(str, Enum):
    """Direction of a crypto transfer."""

    INCOMING = "INCOMING"
    OUTGOING = "OUTGOING"


class CryptoTransferStatus(str, Enum):
    """Processing status of a crypto transfer."""

    PROCESSING = "PROCESSING"
    FAILED = "FAILED"
    COMPLETE = "COMPLETE"


class OptionDeliverableType(str, Enum):
    """Type of deliverable for an option contract (OptionDeliverable)."""

    CASH = "cash"
    EQUITY = "equity"


class OptionDeliverableSettlementType(str, Enum):
    """
    Settlement timing for an option deliverable (OptionDeliverable).

    Values use ``T_PLUS_N`` naming because the spec values (``T+0`` … ``T+5``)
    contain a ``+`` character that is not valid in Python identifiers.
    """

    T_PLUS_0 = "T+0"
    T_PLUS_1 = "T+1"
    T_PLUS_2 = "T+2"
    T_PLUS_3 = "T+3"
    T_PLUS_4 = "T+4"
    T_PLUS_5 = "T+5"


class OptionDeliverableSettlementMethod(str, Enum):
    """
    Settlement method for an option deliverable (OptionDeliverable).

    - BTOB: Broker to Broker
    - CADF: Cash Difference
    - CAFX: Cash Fixed
    - CCC: Correspondent Clearing Corp
    """

    BTOB = "BTOB"
    CADF = "CADF"
    CAFX = "CAFX"
    CCC = "CCC"


class TokenizationIssuer(str, Enum):
    """Issuer of a tokenized asset."""

    XSTOCKS = "xstocks"
    ST0X = "st0x"


class TokenizationNetwork(str, Enum):
    """Blockchain network for a tokenized asset."""

    SOLANA = "solana"
    ARBITRUM = "arbitrum"
    ETHEREUM = "ethereum"
    BINANCE = "binance"
    BASE = "base"
    TON = "ton"
    TRON = "tron"
    MANTLE = "mantle"


class TokenizationRequestType(str, Enum):
    """Direction of a tokenization request."""

    MINT = "mint"
    REDEEM = "redeem"


class TokenizationRequestStatus(str, Enum):
    """Processing status of a tokenization request."""

    PENDING = "pending"
    REJECTED = "rejected"
    COMPLETED = "completed"


class WhitelistedAddressStatus(str, Enum):
    """
    Approval status of a whitelisted crypto address.

    Newly added addresses enter PENDING and transition to APPROVED after a 24-hour
    waiting period.
    """

    APPROVED = "APPROVED"
    PENDING = "PENDING"


class BondStatus(str, Enum):
    """Status of a bond."""

    OUTSTANDING = "outstanding"
    MATURED = "matured"
    PRE_ISSUANCE = "pre_issuance"


class CallType(str, Enum):
    """
    Type of call on a callable bond.

    Describes the circumstances under which the bond may be called.
    """

    ORDINARY = "ordinary"
    MAKE_WHOLE = "make_whole"
    REGULATORY = "regulatory"
    SPECIAL = "special"


class CouponFrequency(str, Enum):
    """How often the bond coupon is paid."""

    ANNUAL = "annual"
    SEMI_ANNUAL = "semi_annual"
    QUARTERLY = "quarterly"
    MONTHLY = "monthly"
    ZERO = "zero"


class CouponType(str, Enum):
    """Type of the bond coupon rate."""

    FIXED = "fixed"
    FLOATING = "floating"
    ZERO = "zero"


class DayCount(str, Enum):
    """
    Day count convention used to calculate accrued interest.

    Python member names replace ``/`` with ``_`` and prefix numeric-starting
    values to form valid identifiers (e.g. ``30/360`` → ``THIRTY_360``).
    """

    A_360 = "A/360"
    A_365 = "A/365"
    THIRTY_360 = "30/360"
    THIRTY_365 = "30/365"
    A_A = "A/A"
    THIRTY_E_360 = "30E/360"
    B_252 = "B/252"
    A_364 = "A/364"


class Market(str, Enum):
    """
    Market identifier (MIC, BIC, or acronym) used in clock and calendar APIs.
    """

    BMO = "BMO"
    BNYM = "BNYM"
    BOATS = "BOATS"
    CEUX = "CEUX"
    CHIX = "CHIX"
    HKEX = "HKEX"
    IEX = "IEX"
    IEXG = "IEXG"
    ISE = "ISE"
    LSE = "LSE"
    MTA = "MTA"
    MTAA = "MTAA"
    NASDAQ = "NASDAQ"
    NYSE = "NYSE"
    OCEA = "OCEA"
    OPRA = "OPRA"
    OTC = "OTC"
    OTCM = "OTCM"
    SIFMA = "SIFMA"
    TADAWUL = "TADAWUL"
    XAMS = "XAMS"
    XBRU = "XBRU"
    XDUB = "XDUB"
    XETR = "XETR"
    XETRA = "XETRA"
    XHKG = "XHKG"
    XLIS = "XLIS"
    XLON = "XLON"
    XNAS = "XNAS"
    XNYS = "XNYS"
    XPAR = "XPAR"
    XSAU = "XSAU"


class Phase(str, Enum):
    """Trading session phase reported by the clock API."""

    CLOSED = "closed"
    PRE = "pre"
    CORE = "core"
    LUNCH = "lunch"
    POST = "post"


class SpOutlook(str, Enum):
    """
    Standard & Poor's rating outlook.

    Indicates S&P's view regarding the potential direction of a long-term
    credit rating over the intermediate term (2 years for investment grade,
    1 year for speculative grade).
    """

    POSITIVE = "positive"
    NEGATIVE = "negative"
    DEVELOPING = "developing"
    STABLE = "stable"
    NOT_RATED = "not_rated"
    NOT_MEANINGFUL = "not_meaningful"


class TreasurySubtype(str, Enum):
    """Subtype of a US Treasury security."""

    BOND = "bond"
    BILL = "bill"
    NOTE = "note"
    STRIPS = "strips"
    TIPS = "tips"
    FLOATING = "floating"
