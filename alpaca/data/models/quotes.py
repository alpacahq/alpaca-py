from datetime import datetime
from typing import Optional, Dict, List, Union

from pydantic import ConfigDict

from alpaca.common.types import RawData
from alpaca.common.models import ValidateBaseModel as BaseModel
from alpaca.data.enums import Exchange
from alpaca.data.mappings import QUOTE_MAPPING
from alpaca.data.models.base import TimeSeriesMixin, BaseDataSet


class Quote(BaseModel):
    """Level 1 ask/bid pair quote data. Contains information about size and origin exchange.

    Attributes:
        symbol (str): The ticker identifier for the security whose data forms the quote.
        timestamp (datetime): The time of submission of the quote.
        ask_exchange (Optional[str, Exchange]): The exchange the quote ask originates. Defaults to None.
        ask_price (float): The asking price of the quote.
        ask_size (float): The size of the quote ask.
        bid_exchange (Optional[str, Exchange]): The exchange the quote bid originates. Defaults to None.
        bid_price (float): The bidding price of the quote.
        bid_size (float): The size of the quote bid.
        conditions (Optional[List[str]]): The quote conditions. Defaults to None.
        tape (Optional[str]): The quote tape. Defaults to None.
    """

    symbol: str
    timestamp: datetime
    ask_exchange: Optional[Union[str, Exchange]] = None
    ask_price: float
    ask_size: float
    bid_exchange: Optional[Union[str, Exchange]] = None
    bid_price: float
    bid_size: float
    conditions: Optional[List[str]] = None
    tape: Optional[str] = None

    model_config = ConfigDict(protected_namespaces=tuple())

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

    def __init__(self, raw_data: RawData) -> None:
        """Instantiates a QuoteSet.

        Args:
            raw_data (RawData): The raw quote data received from API keyed by symbol
        """
        parsed_quotes = {}

        for symbol, quotes in raw_data.items():
            parsed_quotes[symbol] = [Quote(symbol, quote) for quote in quotes]

        super().__init__(data=parsed_quotes)
