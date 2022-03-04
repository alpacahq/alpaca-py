from datetime import datetime
from typing import Dict, List, Optional, Union

import pandas as pd
from pandas import DataFrame
from pydantic import BaseModel, validator

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

        df = pd.DataFrame(self.raw)
        df.columns = [self._mapping.get(c, c) for c in df.columns]

        if not df.empty:
            df.set_index("timestamp", inplace=True)
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

    def __init__(self, symbol: str, timeframe: TimeFrame, bar: RawBar) -> None:
        """Instantiates a bar

        Args:
            symbol (str): The ticker identifier for the security
            timeframe (TimeFrame): The interval of time that price data has been aggregated
            bar (RawBar): Raw unparsed bar data from API, contains ohlc and other fields.
        """
        mapped_bar = {
            BAR_MAPPING[key]: val for key, val in bar.items() if key in BAR_MAPPING
        }

        mapped_bar["symbol"] = symbol
        mapped_bar["timeframe"] = timeframe

        super().__init__(**mapped_bar)


class BarSet(BaseModel, TimeSeriesMixin):
    """A collection of Bars.

    Attributes:
        symbol (str): The ticker identifier for the security whose data forms the bar.
        timeframe (TimeFrame): The interval of time price data has been aggregated over.
        bars_set(Union[List[Bar], Dict[str, List[Bar]]]): The collection of Bars.
        _raw (Union[RawBarSet, Dict[str, List[RawBarSet]]]): The raw data from the API call.
    """

    symbol: Optional[str] = None
    timeframe: TimeFrame
    bar_set: Union[List[Bar], Dict[str, List[Bar]]]
    raw: Union[RawBarSet, Dict[str, RawBarSet]]
    _mapping: Dict[str, str] = BAR_MAPPING

    def __init__(
        self,
        raw_data: Union[RawBarSet, Dict[str, RawBarSet]],
        timeframe: TimeFrame,
        symbol: Optional[str] = None,
    ) -> None:
        """A collection of Bars.

        Args:
            bars (Union[RawBarSet, Dict[str, RawBarSet]]): The raw bar data from API.
            timeframe (TimeFrame): The interval of time price data has been aggregated over
            symbol (str): The ticker identifier for the security whose data forms the bar. Defaults to None.
        """
        if symbol:
            parsed_bars = [Bar(symbol, timeframe, bar) for bar in raw_data]
        else:
            parsed_bars = {}

            for _symbol, bars in raw_data.items():
                parsed_bars[_symbol] = [Bar(_symbol, timeframe, bar) for bar in bars]

        super().__init__(
            symbol=symbol, timeframe=timeframe, bar_set=parsed_bars, raw=raw_data
        )

    def __getitem__(self, symbol: str) -> List[Bar]:
        """Gives dictionary-like access to BarSet for multisymbol data

        Args:
            symbol (str): The ticker idenfitier for the desired data

        Raises:
            KeyError: No keys available when single symbol data

        Returns:
            List[Bar]: The BarSet data for the given symbol
        """
        if self.symbol != None:
            raise KeyError(f"No key {symbol} was found")

        return self.bar_set[symbol]

    @validator("bar_set")
    def multi_symbol_has_no_symbol_value(cls, v, values, **kwargs):

        if not isinstance(v, List) and values["symbol"] != None:
            raise ValueError("Symbol field cannot have value for multisymbol data")

        return v

    @validator("bar_set")
    def single_symbol_has_symbol_value(cls, v, values, **kwargs):

        if isinstance(v, List) and values["symbol"] == None:
            raise ValueError("Symbol field is required for single symbol data")

        return v
