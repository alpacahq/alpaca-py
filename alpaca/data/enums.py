from enum import Enum


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


class DataFeed(str, Enum):
    """Equity market data feeds. OTC and SIP are available with premium data subscriptions.

    Attributes:
        IEX (str): Investor's exchange data feed
        SIP (str): Securities Information Processor feed
        OTC (str): Over the counter feed
    """

    IEX = "iex"
    SIP = "sip"
    OTC = "otc"


class Adjustment(str, Enum):
    """Data normalization based on types of corporate actions.

    Attributes:
        RAW (str): Unadjusted data
        SPLIT (str): Stock-split adjusted data
        DIVIDEND (str): Dividend adjusted data
        ALL (str): Data adjusted for all corporate actions
    """

    RAW = "raw"
    SPLIT = "split"
    DIVIDEND = "dividend"
    ALL = "all"


class CryptoFeed(str, Enum):
    """
    Crypto location

    Attributes:
        US (str): United States crypto feed
    """

    US = "us"


class OptionsFeed(str, Enum):
    """
    The source feed of the data.
    `opra` requires subscription

    Attributes:
        OPRA (str): Options Price Reporting Authority
        INDICATIVE (str): Indicative data
    """

    OPRA = "opra"
    INDICATIVE = "indicative"


class MostActivesBy(str, Enum):
    """
    Most actives possible filters.

    Attributes:
        volume (str):
            Retrieve most actives by trading volume.
        trades (str):
            Retrieve most actives by number of trades.
    """

    VOLUME = "volume"
    TRADES = "trades"


class MarketType(str, Enum):
    """
    Most actives possible filters.

    Attributes:
        stocks (str)
        crypto (str)
    """

    STOCKS = "stocks"
    CRYPTO = "crypto"


class NewsImageSize(str, Enum):
    THUMB = "thumb"
    SMALL = "small"
    LARGE = "large"


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
