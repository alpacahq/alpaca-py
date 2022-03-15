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

    FTXU: str = "FTXU"
    CBSE: str = "CBSE"
    GNSS: str = "GNSS"
    ERSX: str = "ERSX"

    def __str__(self):
        return self.value
