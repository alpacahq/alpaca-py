from datetime import datetime
from typing import Dict, List, Optional, Union

from alpaca.common.models import ValidateBaseModel as BaseModel
from alpaca.common.types import RawData
from alpaca.data.enums import Exchange
from alpaca.data.mappings import (
    TRADE_CANCEL_MAPPING,
    TRADE_CORRECTION_MAPPING,
    TRADE_MAPPING,
    TRADING_STATUS_MAPPING,
)
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

    def __init__(self, symbol: str, raw_data: RawData) -> None:
        """Instantiates a Trade object

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
    """A collection of Trade objects.

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


class TradingStatus(BaseModel):
    """Trading status update of a security, for example if a symbol gets halted.

    Attributes:
        symbol (str): The ticker identifier.
        timestamp (datetime): The time of trading status.
        status_code (str): The tape-dependent code of the status.
        status_message (str): The status message.
        reason_code (str): The tape-dependent code of the halt reason.
        reason_message (str): The reason message.
        tape (Optional[str]): The tape (A, B or C).
    """

    symbol: str
    timestamp: datetime
    status_code: str
    status_message: str
    reason_code: str
    reason_message: str
    tape: str

    def __init__(self, symbol: str, raw_data: RawData) -> None:
        """Instantiates a Trading status object

        Args:
            symbol (str): The security identifier
            raw_data (RawData): The raw data as received by API.
        """

        mapped = {
            TRADING_STATUS_MAPPING.get(key): val
            for key, val in raw_data.items()
            if key in TRADING_STATUS_MAPPING
        }

        super().__init__(symbol=symbol, **mapped)


class TradeCancel(BaseModel):
    """Cancel of a previous trade.

    Attributes:
        symbol (str): The ticker identifier.
        timestamp (datetime): The timestamp.
        exchange (Exchange): The exchange.
        price (float): The price of the canceled trade.
        size (float): The size of the canceled trade.
        id (Optional[int]): The original ID of the canceled trade.
        action (Optional[str]): The cancel action ("C" for cancel, "E" for error)
        tape (str): The trade tape. Defaults to None.
    """

    symbol: str
    timestamp: datetime
    exchange: Exchange
    price: float
    size: float
    id: Optional[int] = None
    action: Optional[str] = None
    tape: str

    def __init__(self, symbol: str, raw_data: RawData) -> None:
        """Instantiates a trade cancel object

        Args:
            symbol (str): The security identifier
            raw_data (RawData): The raw data as received by API.
        """

        mapped = {
            TRADE_CANCEL_MAPPING.get(key): val
            for key, val in raw_data.items()
            if key in TRADE_CANCEL_MAPPING
        }

        super().__init__(symbol=symbol, **mapped)


class TradeCorrection(BaseModel):
    """Correction of a previous trade.

    Attributes:
        symbol (str): The ticker identifier.
        timestamp (datetime): The timestamp.
        exchange (Exchange): The exchange.
        original_id (Optional[int]): The original ID of the corrected trade.
        original_price (float): The original price of the corrected trade.
        original_size (float): The original size of the corrected trade.
        original_conditions (List[str]): The original conditions of the corrected trade.
        corrected_id (Optional[int]): The corrected ID of the corrected trade.
        corrected_price (float): The corrected price of the corrected trade.
        corrected_size (float): The corrected size of the corrected trade.
        corrected_conditions (List[str]): The corrected conditions of the corrected trade.
        tape (str): The trade tape. Defaults to None.
    """

    symbol: str
    timestamp: datetime
    exchange: Exchange
    original_id: Optional[int] = None
    original_price: float
    original_size: float
    original_conditions: List[str]
    corrected_id: Optional[int] = None
    corrected_price: float
    corrected_size: float
    corrected_conditions: List[str]
    tape: str

    def __init__(self, symbol: str, raw_data: RawData) -> None:
        """Instantiates a trade correction object

        Args:
            symbol (str): The security identifier
            raw_data (RawData): The raw data as received by API.
        """
        mapped = {
            TRADE_CORRECTION_MAPPING.get(key): val
            for key, val in raw_data.items()
            if key in TRADE_CORRECTION_MAPPING
        }

        super().__init__(symbol=symbol, **mapped)
