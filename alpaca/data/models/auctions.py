from datetime import datetime
from typing import Optional, Dict, List

from alpaca.common.types import RawData
from alpaca.common.models import ValidateBaseModel as BaseModel
from alpaca.data.models.base import BaseDataSet
from alpaca.data.mappings import AUCTION_MAPPING, DAILY_AUCTION_MAPPING
from alpaca.data.enums import Exchange


class Auction(BaseModel):
    """Represents a single trade in the Auction

    Attributes:
        timestamp (datetime): The timestamp in RFC-3339 format.
        exchange (Optional[str, Exchange]): The exchange the auction originates
        size (float): The auction trade size
        price (float): The auction trade price
        conditions (Optional[str]): The condition flag indicating that this is an auction.
    """

    timestamp: datetime
    exchange: Optional[str, Exchange]
    size: float
    price: float
    conditions: Optional[str]

    def __init__(self, symbol: str, raw_data: RawData) -> None:
        """Instantiates an auction

        Args:
            raw_data (RawData): Raw unparsed auction data from API
        """
        mapped_auction = {
            AUCTION_MAPPING[key]: val
            for key, val in raw_data.items()
            if key in AUCTION_MAPPING
        }

        super().__init__(symbol=symbol, **mapped_auction)


class DailyAuction(BaseModel):
    """Represents the auctions taking place during the day

    Attributes:
        date (date): The date for the daily auction.
        opening_auctions (Optional[List[Auction]]): The opening auctions.
        closing_auctions(Optional[List[Auction]]): The closing auctions.
            Every price / exchange / condition triplet is only shown once, with its earliest timestamp.
    """

    date: date
    opening_auctions: Optional[List[Auction]]
    closing_auctions: Optional[List[Auction]]

    def __init__(self, symbol: str, raw_data: RawData) -> None:
        """Instantiates an daily auction

        Args:
            raw_data (RawData): Raw unparsed daily auction data from API
        """
        mapped_daily_auction = {
            DAILY_AUCTION_MAPPING[key]: val
            for key, val in raw_data.items()
            if key in DAILY_AUCTION_MAPPING
        }

        super().__init__(symbol=symbol, **mapped_daily_auction)
