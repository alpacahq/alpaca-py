from datetime import datetime
from typing import List, Optional, Type, Union

from pydantic import BaseModel

from alpaca.common.enums import BaseURL
from alpaca.common.rest import RESTClient
from alpaca.common.time import TimeFrame
from alpaca.common.types import RawData

from .enums import Exchange
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
    ) -> Union[BarSet, RawData]:
        """Returns bar data for a security or list of securities over a given
        time period and timeframe

        Args:
            symbol_or_symbols (Union[str, List[str]]): The security or multiple security ticker identifiers
            timeframe (TimeFrame): The period over which the bars should be aggregated. (i.e. 5 Min bars, 1 Day bars)
            start (datetime): The beginning of the time interval for desired data
            end (Optional[datetime], optional): The beginning of the time interval for desired data. Defaults to None.
            limit (Optional[int], optional): Upper limit of number of data points to return. Defaults to None.

        Returns:
            Union[BarSet, RawData]: The bar data either in raw or wrapped form
        """
        # replace timeframe object with it's string representation
        timeframe_value = timeframe.value

        # paginated get request for market data api
        bars_generator = self._data_get(
            endpoint="bars",
            symbol_or_symbols=symbol_or_symbols,
            timeframe=timeframe_value,
            start=start,
            end=end,
            limit=limit,
        )

        # casting generator type outputted from to list
        raw_bars = list(bars_generator)

        return self._format_data_response(
            symbol_or_symbols=symbol_or_symbols,
            raw_data=raw_bars,
            model=BarSet,
            timeframe=timeframe,
        )

    def get_crypto_bars(
        self,
        symbol_or_symbols: Union[str, List[str]],
        timeframe: TimeFrame,
        start: datetime,
        end: Optional[datetime] = None,
        limit: Optional[int] = None,
        exchanges: Optional[List[Exchange]] = [],
    ) -> Union[BarSet, RawData]:
        """Gets bar/candle data for cryptocurrencies.

        Args:
            symbol_or_symbols (Union[str, List[str]]): The cryptocurrencysecurity or multiple security ticker identifiers
            timeframe (TimeFrame): _description_
            start (datetime): _description_
            end (Optional[datetime], optional): _description_. Defaults to None.
            limit (Optional[int], optional): _description_. Defaults to None.

        Returns:
            Union[BarSet, RawData]: The crypto bar data either in raw or wrapped form
        """

        # replace timeframe object with it's string representation
        timeframe_value = timeframe.value

        # paginated get request for crypto market data api
        bars_generator = self._data_get(
            endpoint="bars",
            endpoint_base="crypto",
            api_version="v1beta1",
            symbol_or_symbols=symbol_or_symbols,
            timeframe=timeframe_value,
            start=start,
            end=end,
            limit=limit,
            exchanges=exchanges,
        )

        # casting generator type outputted from to list
        raw_bars = list(bars_generator)

        return self._format_data_response(
            symbol_or_symbols=symbol_or_symbols,
            raw_data=raw_bars,
            model=BarSet,
            timeframe=timeframe,
        )

    def _format_data_response(
        self,
        symbol_or_symbols: Union[str, List[str]],
        raw_data: RawData,
        model: Type[BaseModel],
        **kwargs
    ) -> Union[BarSet, RawData]:
        """Formats the response from market data API.

        Args:
            symbol_or_symbols (Union[str, List[str]]): The security or multiple security ticker identifiers
            raw_data (RawData): The data returned by the _data_get method
            model (Type[BaseModel]): The model we want to wrap the data in

        Returns:
            Union[BarSet, RawData]: The bar data either in raw or wrapped form
        """
        if isinstance(symbol_or_symbols, str):

            # BarSet expects a symbol keyed dictionary of bar data from API
            _raw_data_dict = {symbol_or_symbols: raw_data}

            return self.response_wrapper(
                model,
                symbols=[symbol_or_symbols],
                raw_data=_raw_data_dict,
                **kwargs,
            )

        # merge list of dictionaries (symbol (key): List[Bar] (value)) yielded by _data_get
        raw_multi_symbol_data = {}

        for _data_by_symbol in raw_data:
            for _symbol, _bars in _data_by_symbol.items():
                if _symbol not in raw_multi_symbol_data:
                    raw_multi_symbol_data[_symbol] = _bars
                else:
                    raw_multi_symbol_data[_symbol].extend(_bars)

        return self.response_wrapper(
            model,
            symbols=symbol_or_symbols,
            raw_data=raw_multi_symbol_data,
            **kwargs,
        )
