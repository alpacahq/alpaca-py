from datetime import datetime
from typing import Dict, List, Optional, Union

from alpaca.common.models import ValidateBaseModel as BaseModel
from alpaca.common.types import RawData
from alpaca.data.enums import Exchange
from alpaca.data.mappings import QUOTE_MAPPING
from alpaca.data.models.base import BaseDataSet, TimeSeriesMixin


class Quote(BaseModel):
    """Level 1 ask/bid pair quote data. Contains information about size and origin exchange.

    Attributes:
        symbol (str): The ticker identifier for the security whose data forms the quote.
        timestamp (datetime): The time of submission of the quote.
        bid_price (float): The bidding price of the quote.
        bid_size (float): The size of the quote bid.
        bid_exchange (Optional[Union[str, Exchange]]): The exchange the quote bid originates. Defaults to None.
        ask_price (float): The asking price of the quote.
        ask_size (float): The size of the quote ask.
        ask_exchange (Optional[Union[str, Exchange]]): The exchange the quote ask originates. Defaults to None.
        conditions (Optional[Union[List[str], str]]): The quote conditions. Defaults to None.
        tape (Optional[str]): The quote tape. Defaults to None.
    """

    symbol: str
    timestamp: datetime
    bid_price: float
    bid_size: float
    bid_exchange: Optional[Union[str, Exchange]] = None
    ask_price: float
    ask_size: float
    ask_exchange: Optional[Union[str, Exchange]] = None
    conditions: Optional[Union[List[str], str]] = None
    tape: Optional[str] = None

    def __init__(self, symbol: str, raw_data: RawData) -> None:
        """Instantiates a Quote

        Args:
            symbol (str): The security identifier for the quote
            raw_data (RawData): The quote data as received by API
        """

        mapped_quote = {
            QUOTE_MAPPING.get(key): val
            for key, val in raw_data.items()
            if key in QUOTE_MAPPING
        }

        super().__init__(symbol=symbol, **mapped_quote)


class QuoteSet(BaseDataSet, TimeSeriesMixin):
    """A collection of Quotes.

    Attributes:
        data (Dict[str, List[Quote]]): The collection of Quotes keyed by symbol.
    """

    data: Dict[str, List[Quote]] = {}

    def __init__(self, raw_data: RawData) -> None:
        """Instantiates a QuoteSet.

        Args:
            raw_data (RawData): The raw quote data received from API keyed by symbol
        """
        parsed_quotes = {}

        if raw_data is not None:
            for symbol, quotes in raw_data.items():
                parsed_quotes[symbol] = [
                    Quote(symbol, quote) for quote in quotes if quote is not None
                ]

        super().__init__(data=parsed_quotes)
