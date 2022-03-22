from enum import Enum


class Exchange(Enum):
    """The exchanges that provide data feeds to Alpaca

    Attributes:
        FTXU (str): FTX exchange
        CBSE (str): Coinbase exchange
        GNSS (str): Genesis exchange
        ERSX (str): ErisX exchange
        IEX (str): Investors Exchange
    """

    FTXU: str = "FTXU"
    CBSE: str = "CBSE"
    GNSS: str = "GNSS"
    ERSX: str = "ERSX"

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


class Currency(Enum):
    """International fiat currency types

    Attributes:
        USD (str): United States Dollar
        JPY (str): Japanese Yen
    """

    USD: str = "USD"
    JPY: str = "JPY"

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
