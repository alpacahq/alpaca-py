from datetime import datetime
from typing import Dict, List, Optional, Union

from pydantic import BaseModel, validator

import pandas as pd
from pandas import DataFrame

from alpaca.common.time import TimeFrame
from alpaca.common.types import RawBar, RawBarSet
from .enums import Exchange
from .mappings import BAR_MAPPING

class TimeSeriesMixin:

    @property
    def df(self) -> DataFrame:
        """Returns a pandas dataframe containing the bars data

        Returns:
            DataFrame: bars in a pandas dataframe 
        """

        df = pd.DataFrame(
            self.raw
        )
        df.columns = [self._mapping.get(c, c) for c in df.columns]

        if not df.empty:
            df.set_index('timestamp', inplace=True)
            df.index = pd.DatetimeIndex(df.index)

        return df


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
    """

    symbol: str
    timeframe: TimeFrame
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
                timeframe: TimeFrame,
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



class BarSet(BaseModel, TimeSeriesMixin):
    """A collection of Bars.

    Attributes:
        symbol (str): The ticker identifier for the security whose data forms the bar
        timeframe (TimeFrame): The interval of time price data has been aggregated over
        bars (List[Bar]): A list of Bar objects. See Bar.
        _raw (RawBarSet)
    """

    symbol: str
    timeframe: TimeFrame
    bars : List[Bar]
    raw : RawBarSet
    _mapping : Dict[str, str] = BAR_MAPPING

    def __init__(self,
                symbol: str,
                timeframe: TimeFrame, 
                bars: RawBarSet,
                ) -> None:
        """A collection of Bars.

        Args:
            symbol (str): The ticker identifier for the security whose data forms the bar
            timeframe (TimeFrame): The interval of time price data has been aggregated over
            bars (RawBarSet): List of raw bar data from API.
        """

        
        parsed_bars = [Bar(symbol, timeframe, bar) for bar in bars]


        super().__init__(symbol=symbol,
                        timeframe=timeframe,
                        bars=parsed_bars, 
                        raw=bars)
        
    
        




        

        
