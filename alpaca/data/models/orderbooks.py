from datetime import datetime
from typing import List

from pydantic import Field, TypeAdapter

from alpaca.common.models import ValidateBaseModel as BaseModel
from alpaca.common.types import RawData
from alpaca.data.mappings import ORDERBOOK_MAPPING


class OrderbookQuote(BaseModel):
    """A single bid or ask quote in the orderbook"""

    # using field aliases for easy parsing
    price: float = Field(alias="p")
    size: float = Field(alias="s")


class Orderbook(BaseModel):
    """Level 2 ask/bid pair orderbook data.

    Attributes:
        symbol (str): The ticker identifier for the security whose data forms the orderbook.
        timestamp (datetime): The time of submission of the orderbook.
        bids (List[OrderbookQuote]): The list of bid quotes for the orderbook
        asks (List[OrderbookQuote]): The list of ask quotes for the orderbook
        reset (bool): if true, the orderbook message contains the whole server side orderbook.
        This indicates to the client that they should reset their orderbook.
        Typically sent as the first message after subscription.
    """

    symbol: str
    timestamp: datetime
    bids: List[OrderbookQuote]
    asks: List[OrderbookQuote]
    reset: bool = False

    def __init__(self, symbol: str, raw_data: RawData) -> None:
        """Instantiates an Orderbook.

        Args:
            symbol (str): The security identifier for the orderbook
            raw_data (RawData): The orderbook data as received by API
        """

        mapped_book = {
            ORDERBOOK_MAPPING.get(key): val
            for key, val in raw_data.items()
            if key in ORDERBOOK_MAPPING
        }

        mapped_book["bids"] = TypeAdapter(List[OrderbookQuote]).validate_python(
            mapped_book["bids"]
        )
        mapped_book["asks"] = TypeAdapter(List[OrderbookQuote]).validate_python(
            mapped_book["asks"]
        )

        super().__init__(symbol=symbol, **mapped_book)
