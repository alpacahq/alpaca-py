from datetime import datetime
from typing import Dict, List, Optional

from alpaca.common.models import ValidateBaseModel as BaseModel
from alpaca.common.types import RawData
from alpaca.data.mappings import BAR_MAPPING
from alpaca.data.models.base import BaseDataSet, TimeSeriesMixin


class Bar(BaseModel):
    """Represents one bar/candlestick of aggregated trade data over a specified interval.

    Attributes:
        symbol (str): The ticker identifier for the security whose data forms the bar.
        timestamp (datetime): The closing timestamp of the bar.
        open (float): The opening price of the interval.
        high (float): The high price during the interval.
        low (float): The low price during the interval.
        close (float): The closing price of the interval.
        volume (float): The volume traded over the interval.
        trade_count (Optional[float]): The number of trades that occurred.
        vwap (Optional[float]): The volume weighted average price.
        exchange (Optional[float]): The exchange the bar was formed on.
    """

    symbol: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    trade_count: Optional[float]
    vwap: Optional[float]

    def __init__(self, symbol: str, raw_data: RawData) -> None:
        """Instantiates a bar

        Args:
            raw_data (RawData): Raw unparsed bar data from API, contains ohlc and other fields.
        """
        mapped_bar = {}

        if raw_data is not None:
            mapped_bar = {
                BAR_MAPPING[key]: val
                for key, val in raw_data.items()
                if key in BAR_MAPPING
            }

        super().__init__(symbol=symbol, **mapped_bar)


class BarSet(BaseDataSet, TimeSeriesMixin):
    """A collection of Bars.

    Attributes:
        data (Dict[str, List[Bar]]): The collection of Bars keyed by symbol.
    """

    data: Dict[str, List[Bar]] = {}

    def __init__(
        self,
        raw_data: RawData,
    ) -> None:
        """A collection of Bars.

        Args:
            raw_data (RawData): The collection of raw bar data from API keyed by Symbol.
        """

        parsed_bars = {}

        raw_bars = raw_data

        if raw_bars is not None:
            for symbol, bars in raw_bars.items():
                parsed_bars[symbol] = [
                    Bar(symbol, bar) for bar in bars if bar is not None
                ]

        super().__init__(data=parsed_bars)
