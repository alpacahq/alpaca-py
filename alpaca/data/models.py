from datetime import datetime
from typing import Dict, List, Optional, Union

import pandas as pd
from pandas import DataFrame
from pydantic import BaseModel

from alpaca.common.time import TimeFrame
from alpaca.common.types import RawData

from .enums import Exchange
from .mappings import (
    BAR_MAPPING,
    QUOTE_MAPPING,
    SNAPSHOT_MAPPING,
    TRADE_MAPPING,
    XBBO_MAPPING,
)


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

    def __init__(self, symbol: str, timeframe: TimeFrame, raw_data: RawData) -> None:
        """Instantiates a bar

        Args:
            symbol (str): The ticker identifier for the security
            timeframe (TimeFrame): The interval of time that price data has been aggregated
            raw_data (RawData): Raw unparsed bar data from API, contains ohlc and other fields.
        """
        mapped_bar = {
            BAR_MAPPING[key]: val for key, val in raw_data.items() if key in BAR_MAPPING
        }

        super().__init__(symbol=symbol, timeframe=timeframe, **mapped_bar)


class BarSet(BaseModel, TimeSeriesMixin):
    """A collection of Bars.

    Attributes:
        symbols (List[str]): The list of ticker identifiers for the securities whose data forms the set of bars.
        timeframe (TimeFrame): The interval of time price data has been aggregated over.
        bar_set(Dict[str, List[Bar]]): The collection of Bars keyed by symbol.
        raw (Dict[str, List[RawData]]): The collection of raw data from the API call keyed by symbol.
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
            symbol (str): The ticker identifier for the desired data

        Raises:
            KeyError: Cannot access data for symbol not in BarSet

        Returns:
            List[Bar]: The BarSet data for the given symbol
        """
        if symbol not in self.symbols:
            raise KeyError(f"No key {symbol} was found")

        return self.bar_set[symbol]


class Quote(BaseModel):
    """Level 1 ask/bid pair quote data. Contains information about size and origin exchange.

    Attributes:
        symbol (str): The ticker identifier for the security whose data forms the quote.
        timestamp (datetime): The time of submission of the quote.
        exchange (Optional[Exchange]): The exchange the quote originates. Used when single origin for both ask and bid. Defaults to None.
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
    exchange: Optional[Exchange] = None
    ask_exchange: Optional[Union[str, Exchange]] = None
    ask_price: float
    ask_size: float
    bid_exchange: Optional[Union[str, Exchange]] = None
    bid_price: float
    bid_size: float
    conditions: Optional[List[str]] = None
    tape: Optional[str] = None

    def __init__(self, symbol: str, raw_data: RawData) -> None:
        """Instantiates a Quote

        Args:
            symbol (str): The security identifer for the quote
            raw_data (RawData): The quote data as received by API
        """

        mapped_quote = {
            QUOTE_MAPPING.get(key): val
            for key, val in raw_data.items()
            if key in QUOTE_MAPPING
        }

        super().__init__(symbol=symbol, **mapped_quote)


class QuoteSet(BaseModel, TimeSeriesMixin):
    """A collection of Quotes.

    Attributes:
        symbols (List[str]): The list of ticker identifiers for the securities whose data forms the set of quotes.
        quote_set(Dict[str, List[Quote]]): The collection of Quotes keyed by symbol.
        raw (Dict[str, List[RawData]]): The collection of raw data from the API call keyed by symbol.
        _key_mapping (Dict[str, str]): The mapping for names of data fields from raw format received from API to data models
    """

    symbols: List[str]
    quote_set: Dict[str, List[Quote]]
    raw: Dict[str, List[RawData]]
    _key_mapping: Dict[str, str] = QUOTE_MAPPING

    def __init__(self, raw_data: Dict[str, List[RawData]], symbols: List[str]) -> None:
        """Instantiates a QuoteSet.

        Args:
            raw_data (Dict[str, List[RawData]]): The raw quote data received from API keyed by symbol
            symbols (List[str]): The list of ticker identifiers for the securities whose data forms the set of quotes.
        """
        parsed_quotes = {}

        for _symbol, quotes in raw_data.items():
            parsed_quotes[_symbol] = [Quote(_symbol, quote) for quote in quotes]

        super().__init__(symbols=symbols, quote_set=parsed_quotes, raw=raw_data)

    def __getitem__(self, symbol: str) -> List[Quote]:
        """Retrieves the quotes for a given symbol

        Args:
            symbol (str): The ticker idenfitier for the desired data

        Raises:
            KeyError: Cannot access data for symbol not in QuoteSet

        Returns:
            List[Quote]: The QuoteSet data for the given symbol
        """
        if symbol not in self.symbols:
            raise KeyError(f"No key {symbol} was found")

        return self.quote_set[symbol]


class Trade(BaseModel):
    """A transaction from the price and sales history of a security.

    Attributes:
        symbol (str): The ticker identifier for the security whose data forms the trade.
        timestamp (datetime): The time of submission of the trade.
        exchange (Exchange): The exchange the trade occurred.
        price (float): The price that the transaction occurred at.
        size (float): The quantity traded
        id (int): The trade ID
        conditions (Optional[List[str]]): The trade conditions. Defaults to None.
        tape (Optional[str]): The trade tape. Defaults to None.
    """

    symbol: str
    timestamp: datetime
    exchange: Exchange
    price: float
    size: float
    id: int
    conditions: Optional[List[str]] = None
    tape: Optional[str] = None

    def __init__(self, symbol: str, raw_data: RawData) -> None:
        """Instantiates a Trade history object

        Args:
            symbol (str): The security identifer for the trade that occurred
            raw_data (RawData): The trade data as received by API
        """

        mapped_trade = {
            TRADE_MAPPING.get(key): val
            for key, val in raw_data.items()
            if key in TRADE_MAPPING
        }

        super().__init__(symbol=symbol, **mapped_trade)


class TradeSet(BaseModel, TimeSeriesMixin):
    """A collection of Trade history objects.

    Attributes:
        symbols (List[str]): The list of ticker identifiers for the securities whose data forms the set of trades.
        trade_set(Dict[str, List[Trade]]]): The collection of Trades keyed by symbol.
        raw (Dict[str, List[RawData]]): The collection of raw data from the API call keyed by symbol.
        _key_mapping (Dict[str, str]): The mapping for names of data fields from raw format received from API to data models
    """

    symbols: List[str]
    trade_set: Dict[str, List[Trade]]
    raw: Dict[str, List[RawData]]
    _key_mapping: Dict[str, str] = TRADE_MAPPING

    def __init__(self, raw_data: Dict[str, List[RawData]], symbols: List[str]) -> None:
        """Instantiates a TradeSet - a collection of Trades.

        Args:
            raw_data (Dict[str, List[RawData]]): The raw trade data received from API keyed by symbol
            symbols (List[str]): The list of ticker identifiers for the securities whose data forms the set of trades.
        """
        parsed_trades = {}

        for _symbol, trades in raw_data.items():
            parsed_trades[_symbol] = [Trade(_symbol, trade) for trade in trades]

        super().__init__(symbols=symbols, trade_set=parsed_trades, raw=raw_data)

    def __getitem__(self, symbol: str) -> List[Trade]:
        """Retrieves the trades for a given symbol

        Args:
            symbol (str): The ticker idenfitier for the desired data

        Raises:
            KeyError: Cannot access data for symbol not in TradeSet

        Returns:
            List[Bar]: The TradeSet data for the given symbol
        """
        if symbol not in self.symbols:
            raise KeyError(f"No key {symbol} was found")

        return self.trade_set[symbol]


class Snapshot(BaseModel):
    """A Snapshot contains the latest trade, latest quote, minute bar daily bar
    and previous daily bar data for a given ticker symbol.

    Attributes:
        symbol (str): The identifier for the snapshot security.
        latest_trade(Trade): The latest transaction on the price and sales tape
        latest_quote (Quote): Level 1 ask/bid pair quote data.
        minute_bar (Bar): The latest minute OHLC bar data
        daily_bar (Bar): The latest daily OHLC bar data
        previous_daily_bar (Bar): The 2nd to latest (2 trading days ago) daily OHLC bar data
    """

    symbol: str
    latest_trade: Trade
    latest_quote: Quote
    minute_bar: Bar
    daily_bar: Bar
    previous_daily_bar: Bar

    def __init__(self, symbol: str, raw_data: Dict[str, RawData]) -> None:
        """Instantiates a Snapshot

        Args:
            symbol (str): The identifier for the snapshot security.
            raw_data (Dict[str, RawData]): The raw API snapshot data keyed by symbol
        """
        mapped_snapshot = {
            SNAPSHOT_MAPPING.get(key): val
            for key, val in raw_data.items()
            if key in SNAPSHOT_MAPPING
        }

        mapped_snapshot["latest_trade"] = Trade(symbol, mapped_snapshot["latest_trade"])
        mapped_snapshot["latest_quote"] = Quote(symbol, mapped_snapshot["latest_quote"])
        mapped_snapshot["minute_bar"] = Bar(
            symbol, TimeFrame.Minute, mapped_snapshot["minute_bar"]
        )
        mapped_snapshot["daily_bar"] = Bar(
            symbol, TimeFrame.Day, mapped_snapshot["daily_bar"]
        )
        mapped_snapshot["previous_daily_bar"] = Bar(
            symbol, TimeFrame.Day, mapped_snapshot["previous_daily_bar"]
        )

        super().__init__(symbol=symbol, **mapped_snapshot)


class SnapshotSet(BaseModel):
    """A collection of Snapshots keyed by symbol

    Attributes:
        symbols (List[str]): The list of ticker identifiers for the snapshot securities.
        snapshot_set (Dict[str, Snapshot]): Snapshot data keyed by symbol
    """

    symbols: List[str]
    snapshot_set: Dict[str, Snapshot]

    def __init__(self, symbols: List[str], raw_data: Dict[str, RawData]) -> None:

        parsed_snapshots = {}

        for _symbol, snapshot in raw_data.items():
            parsed_snapshots[_symbol] = Snapshot(_symbol, snapshot)

        super().__init__(symbols=symbols, snapshot_set=parsed_snapshots)

    def __getitem__(self, symbol: str) -> List[Trade]:
        """Retrieves the snapshot for a given symbol

        Args:
            symbol (str): The ticker idenfitier for the desired data

        Raises:
            KeyError: Cannot access data for symbol not in SnapshotSet

        Returns:
            List[Bar]: The SnapshotSet data for the given symbol
        """
        if symbol not in self.symbols:
            raise KeyError(f"No key {symbol} was found")

        return self.snapshot_set[symbol]


class XBBO(BaseModel):
    """Exchange Best Bid and Offer (XBBO). The best bid and offer across multiple exchanges. The best bid and offer are returned as a
    level 1 quote, containing information about quote size and quote origin exchange.

    Attributes:
        symbol (str): The ticker identifier for the security.
        timestamp (datetime): The timestamp of the XBBO.
        ask_exchange (Exchange): The exchange the ask originates. Defaults to None.
        ask_price (float): The best asking price.
        ask_size (float): The size of the ask.
        bid_exchange (Exchange): The exchange the bid originates. Defaults to None.
        bid_price (float): The best bidding price.
        bid_size (float): The size of the bid.
    """

    symbol: str
    timestamp: datetime
    ask_exchange: Exchange
    ask_price: float
    ask_size: float
    bid_exchange: Exchange
    bid_price: float
    bid_size: float

    def __init__(self, symbol: str, raw_data: RawData) -> None:
        """Instantiates an exchange best bid and offer (XBBO) data point

        Args:
            symbol (str): The security identifer for the quote
            raw_data (RawData): The XBBO data as received by API
        """

        mapped_xbbo = {
            XBBO_MAPPING.get(key): val
            for key, val in raw_data.items()
            if key in XBBO_MAPPING
        }

        super().__init__(symbol=symbol, **mapped_xbbo)
