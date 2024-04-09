from datetime import datetime
from typing import Dict, List, Optional, Union

from pydantic import ConfigDict

from alpaca.common.models import ValidateBaseModel as BaseModel
from alpaca.common.types import RawData
from alpaca.data.enums import Exchange
from alpaca.data.mappings import TRADE_MAPPING
from alpaca.data.models.base import BaseDataSet, TimeSeriesMixin


class Trade(BaseModel):
    """A transaction from the price and sales history of a security.

    Attributes:
        symbol (str): The ticker identifier for the security whose data forms the trade.
        timestamp (datetime): The time of submission of the trade.
        exchange (Optional[Exchange]): The exchange the trade occurred.
        price (float): The price that the transaction occurred at.
        size (float): The quantity traded
        id (Optional[int]): The trade ID
        conditions (Optional[Union[List[str], str]]): The trade conditions. Defaults to None.
        tape (Optional[str]): The trade tape. Defaults to None.
    """

    symbol: str
    timestamp: datetime
    exchange: Optional[Union[Exchange, str]] = None
    price: float
    size: float
    id: Optional[int] = None
    conditions: Optional[Union[List[str], str]] = None
    tape: Optional[str] = None

    model_config = ConfigDict(protected_namespaces=tuple())

    def __init__(self, symbol: str, raw_data: RawData) -> None:
        """Instantiates a Trade history object

        Args:
            symbol (str): The security identifier for the trade that occurred.
            raw_data (RawData): The trade data as received by API.
        """

        mapped_trade = {
            TRADE_MAPPING.get(key): val
            for key, val in raw_data.items()
            if key in TRADE_MAPPING
        }

        super().__init__(symbol=symbol, **mapped_trade)


class TradeSet(BaseDataSet, TimeSeriesMixin):
    """A collection of Trade history objects.

    Attributes:
        data (Dict[str, List[Trade]]]): The collection of Trades keyed by symbol.
    """

    data: Dict[str, List[Trade]] = {}

    def __init__(self, raw_data: RawData) -> None:
        """Instantiates a TradeSet - a collection of Trades.

        Args:
            raw_data (RawData): The raw trade data received from API keyed by symbol
        """
        parsed_trades = {}

        if raw_data is not None:
            for symbol, trades in raw_data.items():
                parsed_trades[symbol] = [
                    Trade(symbol, trade) for trade in trades if trade is not None
                ]

        super().__init__(data=parsed_trades)
