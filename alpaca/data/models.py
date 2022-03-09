from datetime import datetime
from typing import Dict, List, Optional

import pandas as pd
from pandas import DataFrame
from pydantic import BaseModel

from alpaca.common.time import TimeFrame
from alpaca.common.types import RawData

from .enums import Exchange
from .mappings import BAR_MAPPING


class TimeSeriesMixin:
    @property
    def df(self) -> DataFrame:
        """Returns a pandas dataframe containing the bar data.
        Requires mapping to be defined in child class.

        Returns:
            DataFrame: bars in a pandas dataframe
        """
        # for multi-symbol data
        symbols = list(self.raw.keys())

        dataframes = {}

        # create a dataframe for each symbol's data and store in dict
        for symbol in symbols:

            _df = pd.DataFrame(self.raw[symbol])
            _df.columns = [self._key_mapping.get(c, c) for c in _df.columns]

            if not _df.empty:
                _df.set_index("timestamp", inplace=True)
                _df.index = pd.DatetimeIndex(_df.index)

            dataframes[symbol] = _df

        # concat into multi-index dataframe, it will have
        # level 0 - symbol index
        # level 1 - timestamp index
        df = pd.concat(dataframes.values(), keys=dataframes.keys(), axis=0)

        # drop symbol index for dataframe with only 1 or less symbols
        if len(symbols) < 2:
            df.reset_index(level=0, drop=True, inplace=True)

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

    def __init__(self, symbol: str, timeframe: TimeFrame, bar: RawData) -> None:
        """Instantiates a bar

        Args:
            symbol (str): The ticker identifier for the security
            timeframe (TimeFrame): The interval of time that price data has been aggregated
            bar (RawData): Raw unparsed bar data from API, contains ohlc and other fields.
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
        symbols (List[str]): The list of ticker identifiers for the securities whose data forms the set of bars.
        timeframe (TimeFrame): The interval of time price data has been aggregated over.
        bar_set(Dict[str, List[Bar]]]): The collection of Bars keyed by symbol.
        raw (Dict[str, List[RawData]): The collection of raw data from the API call keyed by symbol.
        _key_mapping (Dict[str, str]): The mapping for names of data fields from raw format received from API to data models
    """

    symbols: List[str]
    timeframe: TimeFrame
    bar_set: Dict[str, List[Bar]]
    raw: Dict[str, List[RawData]]
    _key_mapping: Dict[str, str] = BAR_MAPPING

    def __init__(
        self,
        raw_data: Dict[str, List[RawData]],
        timeframe: TimeFrame,
        symbols: List[str],
    ) -> None:
        """A collection of Bars.

        Args:
            raw_data (Dict[str, List[RawData]]): The collection of raw bar data from API keyed by Symbol.
            timeframe (TimeFrame): The interval of time price data has been aggregated over
            symbols (List[str]): The list of ticker identifiers for the securities whose data forms the set of bars.
        """

        parsed_bars = {}

        for _symbol, bars in raw_data.items():
            parsed_bars[_symbol] = [Bar(_symbol, timeframe, bar) for bar in bars]

        super().__init__(
            symbols=symbols, timeframe=timeframe, bar_set=parsed_bars, raw=raw_data
        )

    def __getitem__(self, symbol: str) -> List[Bar]:
        """Gives dictionary-like access to BarSet for multisymbol data

        Args:
            symbol (str): The ticker idenfitier for the desired data

        Raises:
            KeyError: Cannot access data for symbol not in BarSet

        Returns:
            List[Bar]: The BarSet data for the given symbol
        """
        if symbol not in self.symbols:
            raise KeyError(f"No key {symbol} was found")

        return self.bar_set[symbol]
