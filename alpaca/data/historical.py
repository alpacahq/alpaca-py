from datetime import datetime
from typing import List, Optional, Type, Union

from pydantic import BaseModel

from alpaca.common.enums import BaseURL
from alpaca.common.rest import RESTClient
from alpaca.common.time import TimeFrame
from alpaca.common.types import RawData

from .enums import Adjustment, DataFeed, Exchange
from .models import XBBO, BarSet, Quote, QuoteSet, SnapshotSet, Trade, TradeSet


class HistoricalDataClient(RESTClient):
    def __init__(
        self,
        api_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        raw_data: bool = False,
    ) -> None:
        """Instantiates a Historical Data Client.
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
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        limit: Optional[int] = None,
        adjustment: Optional[Adjustment] = None,
        feed: Optional[DataFeed] = None,
    ) -> Union[BarSet, RawData]:
        """Returns bar data for a security or list of securities over a given
        time period and timeframe

        Args:
            symbol_or_symbols (Union[str, List[str]]): The security or multiple security ticker identifiers
            timeframe (TimeFrame): The period over which the bars should be aggregated. (i.e. 5 Min bars, 1 Day bars)
            start (Optional[datetime], optional): The beginning of the time interval for desired data. Defaults to None.
            end (Optional[datetime], optional): The beginning of the time interval for desired data. Defaults to None.
            limit (Optional[int], optional): Upper limit of number of data points to return. Defaults to None.
            adjustment (Optional[Adjustment], optional): The type of corporate action data normalization. Defaults to None.
            feed (Optional[DataFeed], optional): The equity data feed to retrieve from. Defaults to None.

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
            adjustment=adjustment,
            feed=feed,
        )

        # casting generator type outputted from _data_get to list
        raw_bars = list(bars_generator)

        return self._format_data_response(
            symbol_or_symbols=symbol_or_symbols,
            raw_data=raw_bars,
            model=BarSet,
            timeframe=timeframe,
        )

    def get_quotes(
        self,
        symbol_or_symbols: Union[str, List[str]],
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        limit: Optional[int] = None,
        feed: Optional[DataFeed] = None,
    ) -> Union[QuoteSet, RawData]:
        """Returns Quote level 1 data over a given time period for a security or list of securities.

        Args:
            symbol_or_symbols (Union[str, List[str]]): The security or multiple security ticker identifiers.
            start (Optional[datetime], optional): The beginning of the time interval for desired data. Defaults to None.
            end (Optional[datetime], optional): The beginning of the time interval for desired data. Defaults to None.
            limit (Optional[int], optional): Upper limit of number of data points to return. Defaults to None.
            feed (Optional[DataFeed], optional): The equity data feed to retrieve from. Defaults to None.

        Returns:
            Union[QuoteSet, RawData]: The quote data either in raw or wrapped form
        """

        # paginated get request for market data api
        quotes_generator = self._data_get(
            endpoint="quotes",
            symbol_or_symbols=symbol_or_symbols,
            start=start,
            end=end,
            limit=limit,
            feed=feed,
        )

        # casting generator type outputted from _data_get to list
        raw_quotes = list(quotes_generator)

        return self._format_data_response(
            symbol_or_symbols=symbol_or_symbols,
            raw_data=raw_quotes,
            model=QuoteSet,
        )

    def get_trades(
        self,
        symbol_or_symbols: Union[str, List[str]],
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        limit: Optional[int] = None,
        feed: Optional[DataFeed] = None,
    ) -> Union[TradeSet, RawData]:
        """Returns the price and sales history over a given time period for a security or list of securities.

        Args:
            symbol_or_symbols (Union[str, List[str]]): The security or multiple security ticker identifiers
            start (Optional[datetime], optional): The beginning of the time interval for desired data. Defaults to None.
            end (Optional[datetime], optional): The beginning of the time interval for desired data. Defaults to None.
            limit (Optional[int], optional): Upper limit of number of data points to return. Defaults to None.
            feed (Optional[DataFeed], optional): The equity data feed to retrieve from. Defaults to None.

        Returns:
            Union[TradeSet, RawData]: The trade data either in raw or wrapped form
        """

        # paginated get request for market data api
        trades_generator = self._data_get(
            endpoint="trades",
            symbol_or_symbols=symbol_or_symbols,
            start=start,
            end=end,
            limit=limit,
            feed=feed,
        )

        # casting generator type outputted from _data_get to list
        raw_trades = list(trades_generator)

        return self._format_data_response(
            symbol_or_symbols=symbol_or_symbols,
            raw_data=raw_trades,
            model=TradeSet,
        )

    def get_latest_trade(self, symbol: str) -> Union[Trade, RawData]:
        """Retrieves the latest trade for a equity symbol

        Args:
            symbol (str): The equity ticker identifier

        Returns:
            Union[Trade, RawData]: The latest trade in raw or wrapped format
        """
        response = self.get(path=f"/stocks/{symbol}/trades/latest")

        raw_latest_trade = response["trade"]

        return self.response_wrapper(
            model=Trade, raw_data=raw_latest_trade, symbol=symbol
        )

    def get_latest_quote(self, symbol: str) -> Union[Quote, RawData]:
        """Retrieves the latest quote for a equity symbol

        Args:
            symbol (str): The equity ticker identifier

        Returns:
            Union[Quote, RawData]: The latest quote in raw or wrapped format
        """
        response = self.get(path=f"/stocks/{symbol}/quotes/latest")
        raw_latest_quote = response["quote"]

        return self.response_wrapper(
            model=Quote, raw_data=raw_latest_quote, symbol=symbol
        )

    def get_snapshot(
        self,
        symbol_or_symbols: Union[str, List[str]],
        feed: Optional[DataFeed] = None,
    ) -> Union[SnapshotSet, RawData]:
        """Returns snapshots of queried symbols. Snapshots contain latest trade, latest quote, latest minute bar,
        latest daily bar and previous daily bar data for the queried symbols.

        Args:
            symbol_or_symbols (Union[str, List[str]]): The security or multiple security ticker identifiers
            feed (Optional[DataFeed], optional): The equity data feed to retrieve from. Defaults to None.

        Returns:
            Union[SnapshotSet, RawData]: The snapshot data either in raw or wrapped form
        """

        raw_snapshots = {}

        # single symbol request
        if isinstance(symbol_or_symbols, str):

            raw_snapshot = self.get(
                path=f"/stocks/{symbol_or_symbols}/snapshot",
                data={"feed": feed},
            )

            raw_snapshots[symbol_or_symbols] = raw_snapshot
            symbol_or_symbols = [symbol_or_symbols]

        # multisymbol request
        else:
            comma_seperated_symbols = ",".join(s for s in symbol_or_symbols)
            raw_snapshots = self.get(
                path="/stocks/snapshots",
                data={
                    "symbols": comma_seperated_symbols,
                    "feed": feed,
                },
            )

        # casting generator type outputted from _data_get to list
        return self.response_wrapper(
            model=SnapshotSet,
            raw_data=raw_snapshots,
            symbols=symbol_or_symbols,
        )

    def get_crypto_bars(
        self,
        symbol_or_symbols: Union[str, List[str]],
        timeframe: TimeFrame,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        limit: Optional[int] = None,
        exchanges: Optional[List[Exchange]] = None,
    ) -> Union[BarSet, RawData]:
        """Gets bar/candle data for a cryptocurrency or list of cryptocurrencies.

        Args:
            symbol_or_symbols (Union[str, List[str]]): The cryptocurrency or list of multiple cryptocurrency ticker identifiers.
            timeframe (TimeFrame): The period over which the bars should be aggregated. (i.e. 5 Min bars, 1 Day bars).
            start (Optional[datetime], optional): The beginning of the time interval for desired data.
            end (Optional[datetime], optional): The end of the time interval for desired data. Defaults to None.. Defaults to None.
            limit (Optional[int], optional): Upper limit of number of data points to return. Defaults to None.. Defaults to None.
            exchanges (Optional[List[Exchange]]): The crypto exchanges to retrieve bar data from. Defaults to None.

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

        # casting generator type outputted from _data_get to list
        raw_bars = list(bars_generator)

        return self._format_data_response(
            symbol_or_symbols=symbol_or_symbols,
            raw_data=raw_bars,
            model=BarSet,
            timeframe=timeframe,
        )

    def get_crypto_quotes(
        self,
        symbol_or_symbols: Union[str, List[str]],
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        limit: Optional[int] = None,
        exchanges: Optional[List[Exchange]] = None,
    ) -> Union[QuoteSet, RawData]:
        """Returns Quote level 1 data over a given time period for a cryptocurrency or list of cryptocurrencies.

        Args:
            symbol_or_symbols (Union[str, List[str]]): The security or multiple security ticker identifiers
            start (Optional[datetime], optional): The beginning of the time interval for desired data. Defaults to None.
            end (Optional[datetime], optional): The beginning of the time interval for desired data. Defaults to None.
            limit (Optional[int], optional): Upper limit of number of data points to return. Defaults to None.
            exchanges (Optional[List[Exchange]]): The crypto exchanges to retrieve bar data from. Defaults to None.

        Returns:
            Union[QuoteSet, RawData]: The quote data either in raw or wrapped form
        """

        # paginated get request for market data api
        quotes_generator = self._data_get(
            endpoint="quotes",
            endpoint_base="crypto",
            api_version="v1beta1",
            symbol_or_symbols=symbol_or_symbols,
            start=start,
            end=end,
            limit=limit,
            exchanges=exchanges,
        )

        # casting generator type outputted from _data_get to list
        raw_quotes = list(quotes_generator)

        return self._format_data_response(
            symbol_or_symbols=symbol_or_symbols,
            raw_data=raw_quotes,
            model=QuoteSet,
        )

    def get_crypto_trades(
        self,
        symbol_or_symbols: Union[str, List[str]],
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        limit: Optional[int] = None,
        exchanges: Optional[List[Exchange]] = None,
    ) -> Union[TradeSet, RawData]:
        """Returns the price and sales history over a given time period for a cryptocurrency or list of cryptocurrencies.

        Args:
            symbol_or_symbols (Union[str, List[str]]): The security or multiple security ticker identifiers
            start (Optional[datetime], optional): The beginning of the time interval for desired data
            end (Optional[datetime], optional): The beginning of the time interval for desired data. Defaults to None.
            limit (Optional[int], optional): Upper limit of number of data points to return. Defaults to None.
            exchanges (Optional[List[Exchange]]): The crypto exchanges to retrieve bar data from. Defaults to None.

        Returns:
            Union[TradeSet, RawData]: The trade data either in raw or wrapped form
        """

        # paginated get request for market data api
        trades_generator = self._data_get(
            endpoint="trades",
            endpoint_base="crypto",
            api_version="v1beta1",
            symbol_or_symbols=symbol_or_symbols,
            start=start,
            end=end,
            limit=limit,
            exchanges=exchanges,
        )

        # casting generator type outputted from _data_get to list
        raw_trades = list(trades_generator)

        return self._format_data_response(
            symbol_or_symbols=symbol_or_symbols,
            raw_data=raw_trades,
            model=TradeSet,
        )

    def get_crypto_latest_trade(
        self, symbol: str, exchange: Exchange
    ) -> Union[Trade, RawData]:
        """Returns the latest trade for a coin for a specific exchange

        Args:
            symbol (str): The ticker symbol for the coin
            exchange (Exchange): The exchange for the latest trade

        Returns:
            Union[Trade, RawData]: The latest trade in raw or wrapped format
        """

        data = {"exchange": exchange}

        response = self.get(
            path=f"/crypto/{symbol}/trades/latest", data=data, api_version="v1beta1"
        )

        raw_latest_trade = response["trade"]

        return self.response_wrapper(
            model=Trade, raw_data=raw_latest_trade, symbol=symbol
        )

    def get_crypto_latest_quote(
        self, symbol: str, exchange: Exchange
    ) -> Union[Quote, RawData]:
        """Returns the latest quote for a coin for a specific exchange

        Args:
            symbol (str): The ticker symbol for the coin
            exchange (Exchange): The exchange for the latest quote

        Returns:
            Union[Quote, RawData]: The latest quote in raw or wrapped format
        """

        data = {"exchange": exchange}

        response = self.get(
            path=f"/crypto/{symbol}/quotes/latest", data=data, api_version="v1beta1"
        )

        raw_latest_quote = response["quote"]

        return self.response_wrapper(
            model=Quote, raw_data=raw_latest_quote, symbol=symbol
        )

    def get_crypto_snapshot(
        self, symbol_or_symbols: Union[str, List[str]], exchange: Exchange
    ) -> Union[SnapshotSet, RawData]:
        """Returns snapshots of queried crypto symbols. Snapshots contain latest trade, latest quote, latest minute bar,
        latest daily bar and previous daily bar data for the queried symbols.

        Args:
            symbol_or_symbols (Union[str, List[str]]): The security or multiple security ticker identifiers
            exchange (Exchange): The exchange for the latest quote

        Returns:
            Union[SnapshotSet, RawData]: The snapshot data either in raw or wrapped form
        """

        raw_snapshots = {}

        # single symbol
        if isinstance(symbol_or_symbols, str):

            raw_snapshot = self.get(
                path=f"/crypto/{symbol_or_symbols}/snapshot",
                api_version="v1beta1",
                data={"exchange": exchange},
            )

            raw_snapshots[symbol_or_symbols] = raw_snapshot
            symbol_or_symbols = [symbol_or_symbols]

        # multisymbol
        else:
            comma_seperated_symbols = ",".join(s for s in symbol_or_symbols)
            raw_snapshots = self.get(
                path="/crypto/snapshots",
                api_version="v1beta1",
                data={"symbols": comma_seperated_symbols, "exchange": exchange},
            )
            # crypto multisymbol snapshot endpoint has an extra "snapshots" key that contains the data
            raw_snapshots = raw_snapshots["snapshots"]

        # casting generator type outputted from _data_get to list
        return self.response_wrapper(
            model=SnapshotSet,
            raw_data=raw_snapshots,
            symbols=symbol_or_symbols,
        )

    def get_crypto_xbbo(
        self, symbol: str, exchanges: Optional[List[Exchange]] = None
    ) -> Union[XBBO, RawData]:
        """Returns the Best Bid and Offer across multiple crypto exchanges.

        Args:
            symbol (str): The ticker identifier for the cryptocurrency
            exchanges (Optional[List[Exchange]], optional): The exchanges to query across for the best bid and offer. Defaults to None.

        Returns:
            Union[XBBO, RawData]: The raw or parsed XBBO data.
        """

        data = {}

        if exchanges:
            _exchanges_comma_separated = ",".join(s.value for s in exchanges)

            data["exchanges"] = _exchanges_comma_separated

        response = self.get(
            path=f"/crypto/{symbol}/xbbo/latest", data=data, api_version="v1beta1"
        )

        raw_latest_xbbo = response["xbbo"]

        return self.response_wrapper(
            model=XBBO, raw_data=raw_latest_xbbo, symbol=symbol
        )

    def _format_data_response(
        self,
        symbol_or_symbols: Union[str, List[str]],
        raw_data: Union[RawData, List[RawData]],
        model: Type[BaseModel],
        **kwargs,
    ) -> Union[BarSet, RawData]:
        """Formats the response from market data API.

        Args:
            symbol_or_symbols (Union[str, List[str]]): The security or multiple security ticker identifiers
            raw_data (Union[RawData, List[RawData]]): The data returned by the API
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
