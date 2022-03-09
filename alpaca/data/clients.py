from datetime import datetime
from typing import List, Optional, Union

from alpaca.common.enums import BaseURL
from alpaca.common.rest import RESTClient
from alpaca.common.time import TimeFrame
from alpaca.common.types import RawBarSet

from .models import BarSet


class HistoricalDataClient(RESTClient):
    def __init__(
        self,
        api_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        raw_data: bool = False,
    ) -> None:
        """_summary_
        Args:
        api_key (Optional[str], optional): Alpaca API key. Defaults to None.
        secret_key (Optional[str], optional): Alpaca API secret key. Defaults to None.
        raw_data (bool, optional): If true, API responses will not be wrapped and raw responses will returned from methods. Defaults to False.
        """
        super().__init__(
            api_key=api_key,
            secret_key=secret_key,
            api_version="v2",
            base_url=BaseURL.DATA,
            sandbox=False,
            raw_data=raw_data,
        )

    def get_bars(
        self,
        symbol_or_symbols: Union[str, List[str]],
        timeframe: TimeFrame,
        start: datetime,
        end: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> Union[BarSet, RawBarSet]:
        """Returns bar data for a security or list of securities over a given
        time period and timeframe

        Args:
            symbol_or_symbols (Union[str, List[str]]): The security or multiple security ticker identifiers
            timeframe (TimeFrame): The period over which the bars should be aggregated. (i.e. 5 Min bars, 1 Day bars)
            start (datetime): The beginning of the time interval for desired data
            end (Optional[datetime], optional): The beginning of the time interval for desired data. Defaults to None.
            limit (Optional[int], optional): Upper limit of number of data points to return. Defaults to None.

        Returns:
            Union[BarSet, RawBarSet]: The bar data either in raw or wrapped form
        """
        timeframe_value = timeframe.value

        bars_generator = self._data_get(
            endpoint="bars",
            symbol_or_symbols=symbol_or_symbols,
            timeframe=timeframe_value,
            start=start,
            end=end,
            limit=limit,
        )
        raw_bars = list(bars_generator)

        if isinstance(symbol_or_symbols, str):

            # BarSet expects a symbol keyed dictionary of bar data from API
            _raw_bars_dict = {symbol_or_symbols: raw_bars}

            return self.response_wrapper(
                BarSet,
                symbols=[symbol_or_symbols],
                timeframe=timeframe,
                raw_data=_raw_bars_dict,
            )

        # merge list of dictionaries (symbol (key): List[Bar] (value)) yielded by _data_get
        raw_multi_symbol_bars = {}

        for _bars_by_symbol in raw_bars:
            for _symbol, _bars in _bars_by_symbol.items():
                if _symbol not in raw_multi_symbol_bars:
                    raw_multi_symbol_bars[_symbol] = _bars
                else:
                    raw_multi_symbol_bars[_symbol].extend(_bars)

        return self.response_wrapper(
            BarSet,
            symbols=symbol_or_symbols,
            timeframe=timeframe,
            raw_data=raw_multi_symbol_bars,
        )
