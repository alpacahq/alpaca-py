from datetime import datetime
from typing import Dict, List

from alpaca.common.models import ValidateBaseModel as BaseModel
from alpaca.common.types import RawData
from alpaca.data.mappings import AUCTION_MAPPING
from alpaca.data.models.base import BaseDataSet, TimeSeriesMixin


class Auction(BaseModel):
    """Represents one auction of aggregated trade data over a specified interval.

    Attributes:
        symbol (str): The ticker identifier for the security whose data forms the bar.
        timestamp (datetime): The timestamp of the auction.
        condition (str): The condition of the auction.
        price (float): The price of the auction.
        size (float): The size of the auction.
        exchange (str): The exchange of the auction.
        auction_type (str): The type of auction. OPEN or CLOSE.

    """

    symbol: str
    timestamp: datetime
    condition: str
    price: float
    size: float
    exchange: str
    auction_type: str

    def __init__(self, symbol: str, raw_data: RawData) -> None:
        """Instantiates an auction

        Args:
            raw_data (RawData): Raw unparsed auction data from API, contains ohlc and other fields.
        """
        mapped_auction = {}

        if raw_data is not None:
            mapped_auction = {
                AUCTION_MAPPING[key]: val
                for key, val in raw_data.items()
                if key in AUCTION_MAPPING
            }

        super().__init__(symbol=symbol, **mapped_auction)


class AuctionSet(BaseDataSet, TimeSeriesMixin):
    """A collection of Auctions.

    Attributes:
        data (Dict[str, List[Auction]]): The collection of Auctions keyed by symbol.
    """

    data: Dict[str, List[Auction]] = {}

    def __init__(self, raw_data: RawData) -> None:
        """A collection of Auctions.

        Args:
            raw_data (RawData): The collection of raw auction data from API keyed by Symbol.
        """

        parsed_auctions = {}

        raw_auctions = raw_data

        if raw_auctions is not None:
            for symbol, auctions in raw_auctions.items():

                auction_data = []
                for auction in auctions:
                    c = auction.get("c")
                    o = auction.get("o")

                    if c is not None:
                        for close_auction in c:
                            if close_auction:
                                close_auction["at"] = "CLOSE"
                        auction_data.extend(c)
                    if o is not None:
                        for open_auction in o:
                            if open_auction:
                                open_auction["at"] = "OPEN"
                        auction_data.extend(o)

                parsed_auctions[symbol] = [
                    Auction(symbol, auction)
                    for auction in auction_data
                    if auction is not None
                ]

        super().__init__(data=parsed_auctions)
