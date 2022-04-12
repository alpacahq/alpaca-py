from enum import Enum


class Exchange(Enum):
    """The exchanges that provide data feeds to Alpaca

    Attributes:
        FTXU (str): FTX exchange
        CBSE (str): Coinbase exchange
        GNSS (str): Genesis exchange
        ERSX (str): ErisX exchange
        IEX (str): Investors Exchange

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

    # CRYPTO
    FTXU: str = "FTXU"
    CBSE: str = "CBSE"
    GNSS: str = "GNSS"
    ERSX: str = "ERSX"

    Z: str = "Z"
    I: str = "I"
    M: str = "M"
    U: str = "U"
    L: str = "L"
    W: str = "W"
    X: str = "X"
    B: str = "B"
    D: str = "D"
    J: str = "J"
    P: str = "P"
    Q: str = "Q"
    S: str = "S"
    V: str = "V"
    A: str = "A"
    E: str = "E"
    N: str = "N"
    T: str = "T"
    Y: str = "Y"
    C: str = "C"
    H: str = "H"
    K: str = "K"

    def __str__(self):
        return self.value


class DataFeed(Enum):
    """Equity market data feeds. OTC and SIP are available with premium data subscriptions.

    Attributes:
        IEX (str): Investor's exchange data feed
        SIP (str): Securities Information Processor feed
        OTC (str): Over the counter feed
    """

    IEX: str = "iex"
    SIP: str = "sip"
    OTC: str = "otc"

    def __str__(self):
        return self.value


class Adjustment(Enum):
    """Data normalization based on types of corporate actions.

    Attributes:
        RAW (str): Unadjusted data
        SPLIT (str): Stock-split adjusted data
        DIVIDEND (str): Dividend adjusted data
        ALL (str): Data adjusted for all corporate actions
    """

    RAW: str = "raw"
    SPLIT: str = "split"
    DIVIDEND: str = "dividend"
    ALL: str = "all"

    def __str__(self):
        return self.value
