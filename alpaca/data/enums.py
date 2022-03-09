from enum import Enum


class Exchange(Enum):
    """The exchanges that provide data feeds to Alpaca

    Attributes:
        FTX (str): FTX exchange
        CBSE (str): Coinbase exchange
        GNSS (str): Genesis exchange
        ERSX (str): ErisX exchange
        IEX (str): Investors Exchange
    """

    FTX: str = "FTX"
    CBSE: str = "CBSE"
    GNSS: str = "GNSS"
    ERSX: str = "ERSX"
    IEX: str = "IEX"
