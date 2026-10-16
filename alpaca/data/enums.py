from enum import Enum

from typing_extensions import deprecated as _deprecated

from alpaca.data._generated.enums import (
    CaEventCashDividendAllOfSubType,
    CaEventEquityPartialCallAllOfLotteryType,
    CashDividendSubType,
    CorporateActionEventAction,
    CorporateActionEventCapitalGainsDistributionAllOfEventType,
    CorporateActionEventCashDividendAllOfEventType,
    CorporateActionEventCashMergerAllOfEventType,
    CorporateActionEventEquityPartialCallAllOfEventType,
    CorporateActionEventForwardSplitAllOfEventType,
    CorporateActionEventNameChangeAllOfEventType,
    CorporateActionEventRedemptionAllOfEventType,
    CorporateActionEventRegion,
    CorporateActionEventReorganizationAllOfEventType,
    CorporateActionEventReverseSplitAllOfEventType,
    CorporateActionEventRightsDistributionAllOfEventType,
    CorporateActionEventSpinOffAllOfEventType,
    CorporateActionEventStockAndCashMergerAllOfEventType,
    CorporateActionEventStockDividendAllOfEventType,
    CorporateActionEventStockMergerAllOfEventType,
    CorporateActionEventType,
    CorporateActionEventUnitSplitAllOfEventType,
    CorporateActionEventWorthlessRemovalAllOfEventType,
    CryptoHistoricalLoc,
    CryptoLatestLoc,
    DataQuality,
    MarketType,
    MostActivesByParameter,
    NewsImageSize,
    NewsSortParameter,
    OptionChainTypeParameter,
    OptionFeed,
    OptionMetaConditionsTicktypeParameter,
    PartialCallLotteryType,
    Region,
    Sort,
    StockHistoricalFeed,
    StockLatestFeed,
    StockMetaConditionsTapeParameter,
    StockTape,
    SubscribeToCorporateActionsEventsSSERegionParameter,
)


class Exchange(str, Enum):
    """The exchanges that provide data feeds to Alpaca.

    Attributes:
        Z (str): Cboe BZ
        I (str): International Securities Exchange
        M (str): Chicago Stock Exchange
        U (str): Members Exchange
        L (str): Long Term Stock Exchange
        W (str): CBOE
        X (str): NASDAQ OMX PSX
        B (str): NASDAQ OMX BX
        D (str): FINRA ADF
        J (str): Cboe EDGA
        P (str): NYSE Arca
        Q (str): NASDAQ OMX
        S (str): NASDAQ Small Cap
        V (str): IEX
        A (str): NYSE American (AMEX)
        E (str): Market Independent
        N (str): New York Stock Exchange
        T (str): NASDAQ Int
        Y (str): Cboe BYX
        C (str): National Stock Exchange
        H (str): MIAX
        K (str): Cboe EDGX
    """

    Z = "Z"
    I = "I"
    M = "M"
    U = "U"
    L = "L"
    W = "W"
    X = "X"
    B = "B"
    D = "D"
    J = "J"
    P = "P"
    Q = "Q"
    S = "S"
    V = "V"
    A = "A"
    E = "E"
    N = "N"
    T = "T"
    Y = "Y"
    C = "C"
    H = "H"
    K = "K"


# Deprecated enums pass stacklevel=2 so the warning from ``Enum(value)`` points at
# the caller rather than at enum.py, where Python's default filters would hide it.


@_deprecated(
    "DataFeed is deprecated and will be removed in a future version. "
    "Please use `StockHistoricalFeed` for bars, quotes, trades and auctions, or "
    "`StockLatestFeed` for latest data, snapshots and streams instead.",
    stacklevel=2,
)
class DataFeed(str, Enum):
    """Equity market data feeds. OTC and SIP are available with premium data subscriptions.

    .. deprecated:: 0.45.0
        Please use `StockHistoricalFeed` for bars, quotes, trades and auctions, or
        `StockLatestFeed` for latest data, snapshots and streams instead.

    Attributes:
        IEX (str): Investor's exchange data feed
        SIP (str): Securities Information Processor feed
        DELAYED_SIP (str): SIP data with a 15 minute delay
        OTC (str): Over the counter feed
        BOATS (str): Blue Ocean, overnight US trading data
        OVERNIGHT (str): derived overnight US trading data
    """

    IEX = "iex"
    SIP = "sip"
    DELAYED_SIP = "delayed_sip"
    OTC = "otc"
    BOATS = "boats"
    OVERNIGHT = "overnight"


class Adjustment(str, Enum):
    """Data normalization based on types of corporate actions.

    Attributes:
        RAW (str): Unadjusted data
        SPLIT (str): Adjust price and volume for forward and reverse stock splits
        SPIN_OFF (str): Adjust price for spin-offs
        DIVIDEND (str): Adjust price for cash dividends
        ALL (str): Apply all above adjustments
    """

    RAW = "raw"
    SPLIT = "split"
    SPIN_OFF = "spin-off"
    DIVIDEND = "dividend"
    ALL = "all"


@_deprecated(
    "CryptoFeed is deprecated and will be removed in a future version. "
    "Please use `CryptoHistoricalLoc` for bars, quotes and trades, or "
    "`CryptoLatestLoc` for latest data, snapshots and streams instead.",
    stacklevel=2,
)
class CryptoFeed(str, Enum):
    """
    Crypto location

    .. deprecated:: 0.45.0
        Please use `CryptoHistoricalLoc` for bars, quotes and trades, or
        `CryptoLatestLoc` for latest data, snapshots and streams instead.

    Attributes:
        US (str): United States crypto feed
    """

    US = "us"


@_deprecated(
    "OptionsFeed is deprecated and will be removed in a future version. "
    "Please use `OptionFeed` instead.",
    stacklevel=2,
)
class OptionsFeed(str, Enum):
    """
    The source feed of the data.
    `opra` requires subscription

    .. deprecated:: 0.45.0
        Please use `OptionFeed` instead.

    Attributes:
        OPRA (str): Options Price Reporting Authority
        INDICATIVE (str): Indicative data
    """

    OPRA = "opra"
    INDICATIVE = "indicative"


@_deprecated(
    "MostActivesBy is deprecated and will be removed in a future version. "
    "Please use `MostActivesByParameter` instead.",
    stacklevel=2,
)
class MostActivesBy(str, Enum):
    """
    Most actives possible filters.

    .. deprecated:: 0.45.0
        Please use `MostActivesByParameter` instead.

    Attributes:
        volume (str):
            Retrieve most actives by trading volume.
        trades (str):
            Retrieve most actives by number of trades.
    """

    VOLUME = "volume"
    TRADES = "trades"


class CorporateActionsType(str, Enum):
    """
    The type of corporate action.
    ref. https://docs.alpaca.markets/reference/corporateactions-1

    Attributes:
        REVERSE_SPLIT (str): Reverse split
        FORWARD_SPLIT (str): Forward split
        UNIT_SPLIT (str): Unit split
        CASH_DIVIDEND (str): Cash dividend
        STOCK_DIVIDEND (str): Stock dividend
        SPIN_OFF (str): Spin off
        CASH_MERGER (str): Cash merger
        STOCK_MERGER (str): Stock merger
        STOCK_AND_CASH_MERGER (str): Stock and cash merger
        REDEMPTION (str): Redemption
        NAME_CHANGE (str): Name change
        WORTHLESS_REMOVAL (str): Worthless removal
        RIGHTS_DISTRIBUTION (str): Rights distribution
        PARTIAL_CALL (str): Partial call
        REORGANIZATION (str): Reorganization
        CAPITAL_GAINS_DISTRIBUTION (str): Capital gains distribution
    """

    REVERSE_SPLIT = "reverse_split"
    FORWARD_SPLIT = "forward_split"
    UNIT_SPLIT = "unit_split"
    CASH_DIVIDEND = "cash_dividend"
    STOCK_DIVIDEND = "stock_dividend"
    SPIN_OFF = "spin_off"
    CASH_MERGER = "cash_merger"
    STOCK_MERGER = "stock_merger"
    STOCK_AND_CASH_MERGER = "stock_and_cash_merger"
    REDEMPTION = "redemption"
    NAME_CHANGE = "name_change"
    WORTHLESS_REMOVAL = "worthless_removal"
    RIGHTS_DISTRIBUTION = "rights_distribution"
    PARTIAL_CALL = "partial_call"
    REORGANIZATION = "reorganization"
    CAPITAL_GAINS_DISTRIBUTION = "capital_gains_distribution"
