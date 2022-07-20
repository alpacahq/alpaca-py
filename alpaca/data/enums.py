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
