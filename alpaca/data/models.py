from datetime import datetime
from typing import Dict, List, Optional, Union

from pydantic import BaseModel, validator

from ..common.time import TimeFrame
from ..common.types import RawBar, RawBarSet, TimeFrameType
from .enums import Exchange
from .mappings import BAR_MAPPING


class Bar(BaseModel):
    """Represents one bar/candlestick of aggregated trade data over a specified interval.

    Attributes:
        symbol (str): The ticker identifier for the security whose data forms the bar
        timeframe (TimeFrame): The interval of time price data has been aggregated over
        timestamp (datetime): The closing timestamp of the bar
        open (float): The opening price of the interval
        high (float): The high price during the interval
        low (float): The low price during the interval
        close (float): The closing price of the interval
        volume (float): The volume traded over the interval
        trade_count (Optional[float]): The number of trades that occurred 
        vwap (Optional[float]): The volume weighted average price
        exchange (Optional[float]): The exchange the bar was formed on
        KEY_MAPPING (Dict[str, str]): The mapping between raw data keys and parsed data fields
    """

    symbol: str
    timeframe: TimeFrameType
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    trade_count: Optional[float] = None
    vwap: Optional[float] = None
    exchange: Optional[Exchange] = None

    def __init__(self,
                symbol: str, 
                timeframe: TimeFrameType, 
                bar: RawBar
                ) -> None:
        """Instantiates a bar

        Args:
            symbol (str): The ticker identifier for the security
            timeframe (TimeFrame): The interval of time that price data has been aggregated
            bar (RawBar): Raw unparsed bar data from API, contains ohlc and other fields. 
        """
        mapped_bar = {
            BAR_MAPPING[key]: val
            for key, val in bar.items()
            if key in BAR_MAPPING
        }

        mapped_bar['symbol'] = symbol
        mapped_bar['timeframe'] = timeframe

        super().__init__(**mapped_bar)


class BarSet(BaseModel):
    """_summary_

    Attributes:
        symbol (str): The ticker identifier for the security whose data forms the bar
        timeframe (TimeFrame): The interval of time price data has been aggregated over
        bars (List[Bar]): A list of Bar objects. See Bar.
    """

    symbol: str
    timeframe: TimeFrameType
    bars : List[Bar]

    def __init__(self,
                symbol: str,
                timeframe: TimeFrameType, 
                bars: RawBarSet,
                ) -> None:
        """A collection of Bars.

        Args:
            symbol (str): The ticker identifier for the security whose data forms the bar
            timeframe (TimeFrame): The interval of time price data has been aggregated over
            bars (RawBarSet): List of raw bar data from API.
        """

        parsed_bars = [Bar(symbol, timeframe, bar) for bar in bars]

        bar_set = { 'symbol': symbol, 'timeframe': timeframe, 'bars': parsed_bars}

        super().__init__(**bar_set)

    # def __getitem__(self, key):
    #     return super(BarSet, self).__getitem__(key-1)
        



        

        
