from enum import Enum

from typing_extensions import deprecated as _deprecated

from alpaca._deprecating_enum import DeprecatingEnumMeta as _DeprecatingEnumMeta
from alpaca.trading._generated.enums import AssetAttribute
from alpaca.trading._generated.enums import AssetClass as _GeneratedAssetClass
from alpaca.trading._generated.enums import (
    AccountConfigurationsMaxOptionsTradingLevel,
    AccountOptionsApprovedLevel,
    AccountOptionsTradingLevel,
    ActivityV2DetailTRDExecutionType,
    ActivityV2DetailTRDSide,
    AdvancedInstructionsAlgorithm,
    AdvancedInstructionsDestination,
    AssetBorrowStatus,
    AssetsStatus,
    CalendarTimezoneParameter,
    CommonCDIVActivityV2Foreign,
    CommonCDIVActivityV2Special,
    CorporateActionCaType,
    CryptoChain,
    CryptoTransferStatus,
    Exchange,
    ExchangeForPosition,
    FixedIncomeInterestType,
    GetAccountActivitiesCategoryParameter,
    GetAccountActivitiesDirectionParameter,
    GetAccountPortfolioHistoryIntradayReportingParameter,
    GetAccountPortfolioHistoryPnlResetParameter,
    GetAllOrdersAssetClassParameterInner,
    GetAllOrdersDirectionParameter,
    GetAllOrdersStatusParameter,
    GetOptionsContractsStatusParameter,
    GetV2CorporateActionsAnnouncementsDateTypeParameter,
    LegacyCalendarDateTypeParameter,
    LocateErrorCode,
    LocateQuoteErrorCode,
    LocateStatus,
    Market,
    NonTradeActivitiesStatus,
    OptionContractStatus,
    OptionContractStyle,
    OptionContractType,
    OptionDeliverableSettlementMethod,
    OptionDeliverableSettlementType,
    OptionDeliverableType,
    OrderGroupRole,
    PortfolioHistoryTimeframe,
    TradingActivitiesType,
    TokenizationIssuer,
    TokenizationNetwork,
    TokenizationRequestStatus,
    TokenizationRequestType,
    TokenizationTransferStatus,
    TransferDirection,
    TravelRuleNextActionType,
    TravelRuleRequiredFieldValueType,
    TravelRuleValidationErrorCode,
    V2WalletsNetworkParameter,
    WhitelistedAddressStatus,
)
from alpaca.trading._generated.enums import OrderClass as _GeneratedOrderClass
from alpaca.trading._generated.enums import OrderType as _GeneratedOrderType
from alpaca.trading._generated.enums import Phase
from alpaca.trading._generated.enums import PositionIntent as _GeneratedPositionIntent
from alpaca.trading._generated.enums import PositionSide as _GeneratedPositionSide
from alpaca.trading._generated.enums import TimeInForce as _GeneratedTimeInForce

# Deprecated enums pass stacklevel=2 so the warning from ``Enum(value)`` points at
# the caller rather than at enum.py, where Python's default filters would hide it.
# Member access such as ``TradeActivityType.FILL`` does not warn at runtime; type
# checkers and IDEs flag it instead.


@_deprecated(
    "TradeActivityType is deprecated and will be removed in a future version. "
    "Please use `TradingActivitiesType` instead.",
    stacklevel=2,
)
class TradeActivityType(str, Enum):
    """
    Represents the type of TradeActivity.

    Please see https://alpaca.markets/docs/api-references/broker-api/accounts/account-activities/#attributes

    .. deprecated:: 0.45.0
        Please use `TradingActivitiesType` instead.
    """

    PARTIAL_FILL = "partial_fill"
    FILL = "fill"


@_deprecated(
    "NonTradeActivityStatus is deprecated and will be removed in a future version. "
    "Please use `NonTradeActivitiesStatus` instead.",
    stacklevel=2,
)
class NonTradeActivityStatus(str, Enum):
    """
    Represents the status of a NonTradeActivity.

    Please see https://alpaca.markets/docs/api-references/broker-api/accounts/account-activities/#enumaccountactivity
    for more info.

    .. deprecated:: 0.45.0
        Please use `NonTradeActivitiesStatus` instead.
    """

    EXECUTED = "executed"
    CORRECT = "correct"
    CANCELED = "canceled"


@_deprecated(
    "AssetStatus is deprecated and will be removed in a future version. "
    "Please use `AssetsStatus` instead. AssetsStatus has no ALL member; for "
    "Broker GET /v1/assets use GetAssetsStatusParameter from alpaca.broker.enums.",
    stacklevel=2,
)
class AssetStatus(str, Enum):
    """
    Represents the various states for an Asset's lifecycle.

    Broker ``GET /v1/assets`` also accepts ``all``, which returns both active
    and inactive assets.

    .. deprecated:: 0.45.0
        Please use `AssetsStatus` instead. It has no ``ALL`` member; for Broker
        ``GET /v1/assets`` use `GetAssetsStatusParameter` from ``alpaca.broker.enums``.
    """

    ACTIVE = "active"
    INACTIVE = "inactive"
    ALL = "all"


_DEPRECATED_ASSET_EXCHANGES = {
    name: (
        f"AssetExchange.{name} is deprecated and will be removed in the next release. "
        "It is no longer a valid asset exchange."
    )
    for name in ("ASCX", "FTXU", "CBSE", "GNSS", "ERSX")
}


# category=None keeps the class-level deprecation static only: a runtime warning
# would fire for every member, doubling the per-member warnings on removed
# exchanges and making the stable ones warn too.
@_deprecated(
    "AssetExchange is deprecated and will be removed in a future version. "
    "Please use `Exchange` instead. Exchange has no EMPTY member.",
    category=None,
)
class AssetExchange(
    str, Enum, metaclass=_DeprecatingEnumMeta, deprecations=_DEPRECATED_ASSET_EXCHANGES
):
    """
    Represents the current exchanges Alpaca supports.

    ASCX, FTXU, CBSE, GNSS, and ERSX are deprecated and will be removed in the
    next release. They are no longer valid asset exchanges.

    .. deprecated:: 0.45.0
        Please use `Exchange` instead. It has no ``EMPTY`` member.
    """

    AMEX = "AMEX"
    ARCA = "ARCA"
    ASCX = "ASCX"
    BATS = "BATS"
    NYSE = "NYSE"
    NASDAQ = "NASDAQ"
    NYSEARCA = "NYSEARCA"
    TXSE = "TXSE"
    FTXU = "FTXU"
    CBSE = "CBSE"
    GNSS = "GNSS"
    ERSX = "ERSX"
    OTC = "OTC"
    CRYPTO = "CRYPTO"
    EMPTY = ""


@_deprecated(
    "CorporateActionType is deprecated and will be removed in a future version. "
    "Please use `CorporateActionCaType` instead. Its values are capitalized "
    "(Dividend) while this enum's are lowercase (dividend), so check that the API "
    "accepts them before switching.",
    stacklevel=2,
)
class CorporateActionType(str, Enum):
    """
    The general types of corporate action events.

    Learn more here: https://alpaca.markets/docs/api-references/trading-api/corporate-actions-announcements/

    .. deprecated:: 0.45.0
        Please use `CorporateActionCaType` instead. Its values are capitalized
        (``Dividend``) while this enum's are lowercase (``dividend``), so check that
        the API accepts them before switching.
    """

    DIVIDEND = "dividend"
    MERGER = "merger"
    SPINOFF = "spinoff"
    SPLIT = "split"


@_deprecated(
    "CorporateActionSubType is deprecated and will be removed in a future version. "
    "Please use `AnnouncementCASubType` instead. It spells UNIT_SPLIT's value "
    "until_split rather than unit_split.",
    stacklevel=2,
)
class CorporateActionSubType(str, Enum):
    """
    The specific types of corporate actions. Each subtype is related to CorporateActionType.

    Learn more here: https://alpaca.markets/docs/api-references/trading-api/corporate-actions-announcements/

    .. deprecated:: 0.45.0
        Please use `AnnouncementCASubType` instead. It spells the unit split value
        ``until_split`` rather than ``unit_split``.
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


_DEPRECATED_ACCOUNT_STATUSES = {
    name: (
        f"AccountStatus.{name} is deprecated and will be removed in the next release. "
        "It is no longer a valid account status."
    )
    for name in (
        "AML_REVIEW",
        "DISABLED",
        "DISABLE_PENDING",
        "EDITED",
        "KYC_SUBMITTED",
        "REAPPROVAL_PENDING",
        "RESUBMITTED",
        "SIGNED_UP",
    )
}


# AccountStatus, ActivityType and OrderStatus share their name with a generated
# twin, so users have nothing else to migrate to. Their deprecation is static only
# (category=None): type checkers and IDEs flag them, naming what the twin lacks,
# while runtime warnings come only from the deprecated members. The public name
# switches to the generated enum once those members are removed. OrderSide stays
# hand-written and is not deprecated: it keeps FIX sides the twin lacks so
# responses that use them still parse.


@_deprecated(
    "AccountStatus is a temporary compatibility shape and will be replaced by the "
    "OpenAPI-generated AccountStatus in a future release. That enum has no "
    "AML_REVIEW, DISABLED, DISABLE_PENDING, EDITED, KYC_SUBMITTED, "
    "REAPPROVAL_PENDING, RESUBMITTED or SIGNED_UP members.",
    category=None,
)
class AccountStatus(
    str, Enum, metaclass=_DeprecatingEnumMeta, deprecations=_DEPRECATED_ACCOUNT_STATUSES
):
    """
    The various statuses each brokerage account can take during its lifetime

    see https://alpaca.markets/docs/broker/api-references/accounts/accounts/#account-status

    AML_REVIEW, DISABLED, DISABLE_PENDING, EDITED, KYC_SUBMITTED,
    REAPPROVAL_PENDING, RESUBMITTED, and SIGNED_UP are deprecated and will be
    removed in the next release. They are no longer valid account statuses.

    .. deprecated:: 0.45.0
        Will be replaced by the OpenAPI-generated ``AccountStatus``, which has none
        of the deprecated members above.
    """

    ACCOUNT_CLOSED = "ACCOUNT_CLOSED"
    ACCOUNT_CLOSED_PENDING = "ACCOUNT_CLOSED_PENDING"
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


@_deprecated(
    "CorporateActionDateType is deprecated and will be removed in a future version. "
    "Please use `GetV2CorporateActionsAnnouncementsDateTypeParameter` instead.",
    stacklevel=2,
)
class CorporateActionDateType(str, Enum):
    """
    Which announcement date ``since`` and ``until`` apply to.

    .. deprecated:: 0.45.0
        Please use `GetV2CorporateActionsAnnouncementsDateTypeParameter` instead.
    """

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


@_deprecated(
    "QueryOrderStatus is deprecated and will be removed in a future version. "
    "Please use `GetAllOrdersStatusParameter` instead.",
    stacklevel=2,
)
class QueryOrderStatus(str, Enum):
    """
    Which orders ``GET /v2/orders`` returns.

    .. deprecated:: 0.45.0
        Please use `GetAllOrdersStatusParameter` instead.
    """

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


@_deprecated(
    "TradeConfirmationEmail is deprecated and will be removed in a future version. "
    "Please use `AccountConfigurationsTradeConfirmEmail` instead.",
    stacklevel=2,
)
class TradeConfirmationEmail(str, Enum):
    """
    Used for controlling when an Account will receive a trade confirmation email.

    please see https://docs.alpaca.markets/reference/getaccountconfig
    for more info.

    .. deprecated:: 0.45.0
        Please use `AccountConfigurationsTradeConfirmEmail` instead.
    """

    ALL = "all"
    NONE = "none"


@_deprecated(
    "ContractType is deprecated and will be removed in a future version. "
    "Please use `OptionContractType` instead.",
    stacklevel=2,
)
class ContractType(str, Enum):
    """
    Represents the contract type of options

    .. deprecated:: 0.45.0
        Please use `OptionContractType` instead.
    """

    CALL = "call"
    PUT = "put"


@_deprecated(
    "ExerciseStyle is deprecated and will be removed in a future version. "
    "Please use `OptionContractStyle` instead.",
    stacklevel=2,
)
class ExerciseStyle(str, Enum):
    """
    Represents the exercise style of options

    .. deprecated:: 0.45.0
        Please use `OptionContractStyle` instead.
    """

    AMERICAN = "american"
    EUROPEAN = "european"


@_deprecated(
    "ActivityCategory is deprecated and will be removed in a future version. "
    "Please use `GetAccountActivitiesCategoryParameter` instead.",
    stacklevel=2,
)
class ActivityCategory(str, Enum):
    """
    Represents the category of an Activity

    .. deprecated:: 0.45.0
        Please use `GetAccountActivitiesCategoryParameter` instead.
    """

    TRADE_ACTIVITY = "trade_activity"
    NON_TRADE_ACTIVITY = "non_trade_activity"


class OrderSide(str, Enum):
    """
    Represents which side this order was on.

    The trading OpenAPI spec lists buy and sell. These extra values stay so
    responses that still use the older FIX sides keep parsing.
    """

    BUY = "buy"
    SELL = "sell"
    BUY_MINUS = "buy_minus"
    SELL_PLUS = "sell_plus"
    SELL_SHORT = "sell_short"
    SELL_SHORT_EXEMPT = "sell_short_exempt"
    UNDISCLOSED = "undisclosed"
    CROSS = "cross"
    CROSS_SHORT = "cross_short"


# These generated enums preserve every legacy value (and may add new values), so
# the canonical public names can move to generated ownership without invalidating
# existing serialized values.
AssetClass = _GeneratedAssetClass
OrderClass = _GeneratedOrderClass
OrderType = _GeneratedOrderType
PositionIntent = _GeneratedPositionIntent
PositionSide = _GeneratedPositionSide
TimeInForce = _GeneratedTimeInForce


_DEPRECATED_ACTIVITY_TYPES = {
    name: (
        f"ActivityType.{name} is deprecated and will be removed in the next release. "
        "It is no longer a valid activity type."
    )
    for name in ("CIL", "DIVWH", "EXTRD", "FXTRD", "INTPNL", "MEM", "SWP", "VOF", "WH")
}


@_deprecated(
    "ActivityType is a temporary compatibility shape and will be replaced by the "
    "OpenAPI-generated ActivityType in a future release. That enum has no CIL, "
    "DIVWH, EXTRD, FXTRD, INTPNL, MEM, SWP, VOF or WH members, and no "
    "is_trade_activity or is_str_trade_activity helpers.",
    category=None,
)
class ActivityType(
    str, Enum, metaclass=_DeprecatingEnumMeta, deprecations=_DEPRECATED_ACTIVITY_TYPES
):
    """
    Represents what kind of Activity an instance of TradeActivity or NonTradeActivity is.

    Please see https://alpaca.markets/docs/api-references/broker-api/accounts/account-activities/#enumactivitytype
    for descriptions of each of the types

    CIL, DIVWH, EXTRD, FXTRD, INTPNL, MEM, SWP, VOF, and WH are deprecated and
    will be removed in the next release. They are no longer valid activity types.

    .. deprecated:: 0.45.0
        Will be replaced by the OpenAPI-generated ``ActivityType``, which has none of
        the deprecated members above and no ``is_trade_activity`` or
        ``is_str_trade_activity`` helpers.
    """

    FILL = "FILL"
    ACATC = "ACATC"
    ACATS = "ACATS"
    CFEE = "CFEE"
    CGD = "CGD"
    CIL = "CIL"
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
    DIVWH = "DIVWH"
    EXTRD = "EXTRD"
    FEE = "FEE"
    FOPT = "FOPT"
    FXTRD = "FXTRD"
    INT = "INT"
    INTNRA = "INTNRA"
    INTPNL = "INTPNL"
    INTTW = "INTTW"
    JNL = "JNL"
    JNLC = "JNLC"
    JNLS = "JNLS"
    MA = "MA"
    MEM = "MEM"
    MISC = "MISC"
    NC = "NC"
    OCT = "OCT"
    OPASN = "OPASN"
    OPCA = "OPCA"
    OPCSH = "OPCSH"
    OPEXC = "OPEXC"
    OPEXP = "OPEXP"
    OPTRD = "OPTRD"
    PTC = "PTC"
    PTR = "PTR"
    REO = "REO"
    REORG = "REORG"
    SPIN = "SPIN"
    SPLIT = "SPLIT"
    SWP = "SWP"
    TRANS = "TRANS"
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


_DEPRECATED_ORDER_STATUSES = {
    "PENDING_REVIEW": (
        "OrderStatus.PENDING_REVIEW is deprecated and will be removed in the next "
        "release. It is no longer a valid order status."
    )
}


@_deprecated(
    "OrderStatus is a temporary compatibility shape and will be replaced by the "
    "OpenAPI-generated OrderStatus in a future release. That enum has no "
    "PENDING_REVIEW member.",
    category=None,
)
class OrderStatus(
    str, Enum, metaclass=_DeprecatingEnumMeta, deprecations=_DEPRECATED_ORDER_STATUSES
):
    """
    Represents the various states an Order can be in.

    please see https://alpaca.markets/docs/api-references/broker-api/trading/orders/#order-status for more info

    PENDING_REVIEW is deprecated and will be removed in the next release.
    It is no longer a valid order status.

    .. deprecated:: 0.45.0
        Will be replaced by the OpenAPI-generated ``OrderStatus``, which has no
        ``PENDING_REVIEW`` member.
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


@_deprecated(
    "CalendarDateType is deprecated and will be removed in a future version. "
    "Please use `LegacyCalendarDateTypeParameter` instead.",
    stacklevel=2,
)
class CalendarDateType(str, Enum):
    """
    Which calendar date ``GET /v1/calendar`` filters on.

    ``TRADING`` selects market sessions. ``SETTLEMENT`` selects settlement dates.

    .. deprecated:: 0.45.0
        Please use `LegacyCalendarDateTypeParameter` instead.
    """

    TRADING = "TRADING"
    SETTLEMENT = "SETTLEMENT"


# These enums are generated for the Broker API, not Trading, and are the
# replacements named by TradeConfirmationEmail and CorporateActionSubType. The
# Trading OpenAPI spec types the corresponding fields as plain strings, so no
# Trading-owned enum exists. alpaca.broker imports from alpaca.trading.enums at
# module load time, so a normal top-level import from alpaca.broker._generated.enums
# here would deadlock as a circular import. Module __getattr__ (PEP 562) defers the
# import until the name is actually looked up, by which point both packages have
# finished loading.
_BROKER_GENERATED_ENUMS = (
    "AccountConfigurationsTradeConfirmEmail",
    "AnnouncementCASubType",
)


def __getattr__(name: str):
    if name in _BROKER_GENERATED_ENUMS:
        from alpaca.broker._generated import enums as broker_enums

        value = getattr(broker_enums, name)
        globals()[name] = value
        return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
