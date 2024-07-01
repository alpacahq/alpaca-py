from collections import defaultdict
from enum import Enum
from typing import Dict, List, Optional, Type, Union

from alpaca.common.constants import DATA_V2_MAX_LIMIT
from alpaca.common.enums import BaseURL
from alpaca.common.rest import HTTPResult, RESTClient
from alpaca.common.types import RawData
from alpaca.data import Bar, Quote, Snapshot, Trade
from alpaca.data.historical.utils import (
    format_dataset_response,
    format_latest_data_response,
    format_snapshot_data,
    parse_obj_as_symbol_dict,
)
from alpaca.data.models import BarSet, QuoteSet, TradeSet
from alpaca.data.requests import (
    StockBarsRequest,
    StockLatestBarRequest,
    StockLatestQuoteRequest,
    StockLatestTradeRequest,
    StockQuotesRequest,
    StockSnapshotRequest,
    StockTradesRequest,
)


class DataExtensionType(Enum):
    """Used to classify the type of endpoint path extensions"""

    LATEST = "latest"
    SNAPSHOT = "snapshot"


class StockHistoricalDataClient(RESTClient):
    """
    The REST client for interacting with Alpaca Market Data API stock data endpoints.

    Learn more on https://alpaca.markets/docs/market-data/
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        oauth_token: Optional[str] = None,
        use_basic_auth: bool = False,
        raw_data: bool = False,
        url_override: Optional[str] = None,
        sandbox: bool = False,
    ) -> None:
        """
        Instantiates a Historical Data Client.

        Args:
            api_key (Optional[str], optional): Alpaca API key. Defaults to None.
            secret_key (Optional[str], optional): Alpaca API secret key. Defaults to None.
            oauth_token (Optional[str]): The oauth token if authenticating via OAuth. Defaults to None.
            use_basic_auth (bool, optional): If true, API requests will use basic authorization headers. Set to true if using
              broker api sandbox credentials
            raw_data (bool, optional): If true, API responses will not be wrapped and raw responses will be returned from
              methods. Defaults to False. This has not been implemented yet.
            url_override (Optional[str], optional): If specified allows you to override the base url the client points
              to for proxy/testing.
            sandbox (bool): True if using sandbox mode. Defaults to False.
        """

        base_url = (
            url_override
            if url_override is not None
            else BaseURL.DATA_SANDBOX if sandbox else BaseURL.DATA
        )

        super().__init__(
            api_key=api_key,
            secret_key=secret_key,
            oauth_token=oauth_token,
            use_basic_auth=use_basic_auth,
            api_version="v2",
            base_url=base_url,
            sandbox=sandbox,
            raw_data=raw_data,
        )

    def get_stock_bars(
        self, request_params: StockBarsRequest
    ) -> Union[BarSet, RawData]:
        """Returns bar data for an equity or list of equities over a given
        time period and timeframe.

        Args:
            request_params (GetStockBarsRequest): The request object for retrieving stock bar data.

        Returns:
            Union[BarSet, RawData]: The bar data either in raw or wrapped form
        """

        params = request_params.to_request_fields()

        # paginated get request for market data api
        raw_bars = self._data_get(
            endpoint_data_type="bars",
            endpoint_asset_class="stocks",
            api_version="v2",
            **params,
        )

        if self._use_raw_data:
            return raw_bars

        return BarSet(raw_bars)

    def get_stock_quotes(
        self, request_params: StockQuotesRequest
    ) -> Union[QuoteSet, RawData]:
        """Returns level 1 quote data over a given time period for a security or list of securities.

        Args:
            request_params (GetStockQuotesRequest): The request object for retrieving stock quote data.

        Returns:
            Union[QuoteSet, RawData]: The quote data either in raw or wrapped form
        """
        params = request_params.to_request_fields()

        # paginated get request for market data api
        raw_quotes = self._data_get(
            endpoint_data_type="quotes",
            endpoint_asset_class="stocks",
            api_version="v2",
            **params,
        )

        if self._use_raw_data:
            return raw_quotes

        return QuoteSet(raw_quotes)

    def get_stock_trades(
        self, request_params: StockTradesRequest
    ) -> Union[TradeSet, RawData]:
        """Returns the price and sales history over a given time period for a security or list of securities.

        Args:
            request_params (GetStockTradesRequest): The request object for retrieving stock trade data.

        Returns:
            Union[TradeSet, RawData]: The trade data either in raw or wrapped form
        """
        params = request_params.to_request_fields()

        # paginated get request for market data api
        raw_trades = self._data_get(
            endpoint_data_type="trades",
            endpoint_asset_class="stocks",
            api_version="v2",
            **params,
        )

        if self._use_raw_data:
            return raw_trades

        return TradeSet(raw_trades)

    def get_stock_latest_trade(
        self, request_params: StockLatestTradeRequest
    ) -> Union[Dict[str, Trade], RawData]:
        """Retrieves the latest trade for an equity symbol or list of equities.

        Args:
            request_params (StockLatestTradeRequest): The request object for retrieving the latest trade data.

        Returns:
            Union[Dict[str, Trade], RawData]: The latest trade in raw or wrapped format
        """

        params = request_params.to_request_fields()

        raw_latest_trades = self._data_get(
            endpoint_data_type="trades",
            endpoint_asset_class="stocks",
            api_version="v2",
            extension=DataExtensionType.LATEST,
            **params,
        )

        if self._use_raw_data:
            return raw_latest_trades

        return parse_obj_as_symbol_dict(Trade, raw_latest_trades)

    def get_stock_latest_quote(
        self, request_params: StockLatestQuoteRequest
    ) -> Union[Dict[str, Quote], RawData]:
        """Retrieves the latest quote for an equity symbol or list of equity symbols.

        Args:
            request_params (StockLatestQuoteRequest): The request object for retrieving the latest quote data.

        Returns:
            Union[Dict[str, Quote], RawData]: The latest quote in raw or wrapped format
        """
        params = request_params.to_request_fields()

        raw_latest_quotes = self._data_get(
            endpoint_data_type="quotes",
            endpoint_asset_class="stocks",
            api_version="v2",
            extension=DataExtensionType.LATEST,
            **params,
        )

        if self._use_raw_data:
            return raw_latest_quotes

        return parse_obj_as_symbol_dict(Quote, raw_latest_quotes)

    def get_stock_latest_bar(
        self, request_params: StockLatestBarRequest
    ) -> Union[Dict[str, Bar], RawData]:
        """Retrieves the latest minute bar for an equity symbol or list of equity symbols.

        Args:
            request_params (StockLatestBarRequest): The request object for retrieving the latest bar data.

        Returns:
            Union[Dict[str, Bar], RawData]: The latest minute bar in raw or wrapped format
        """
        params = request_params.to_request_fields()

        raw_latest_bars = self._data_get(
            endpoint_data_type="bars",
            endpoint_asset_class="stocks",
            api_version="v2",
            extension=DataExtensionType.LATEST,
            **params,
        )

        if self._use_raw_data:
            return raw_latest_bars

        return parse_obj_as_symbol_dict(Bar, raw_latest_bars)

    def get_stock_snapshot(
        self, request_params: StockSnapshotRequest
    ) -> Union[Dict[str, Snapshot], RawData]:
        """Returns snapshots of queried symbols. Snapshots contain latest trade, latest quote, latest minute bar,
        latest daily bar and previous daily bar data for the queried symbols.

        Args:
            request_params (StockSnapshotRequest): The request object for retrieving snapshot data.

        Returns:
            Union[SnapshotSet, RawData]: The snapshot data either in raw or wrapped form
        """

        params = request_params.to_request_fields()

        raw_snapshots = self._data_get(
            endpoint_asset_class="stocks",
            endpoint_data_type="snapshot",
            api_version="v2",
            extension=DataExtensionType.SNAPSHOT,
            **params,
        )

        if self._use_raw_data:
            return raw_snapshots

        return parse_obj_as_symbol_dict(Snapshot, raw_snapshots)

    # TODO: Remove duplication
    def _data_get(
        self,
        endpoint_asset_class: str,
        endpoint_data_type: str,
        api_version: str,
        symbol_or_symbols: Union[str, List[str]],
        limit: Optional[int] = None,
        page_limit: int = DATA_V2_MAX_LIMIT,
        extension: Optional[DataExtensionType] = None,
        **kwargs,
    ) -> RawData:
        """Performs Data API GET requests accounting for pagination. Data in responses are limited to the page_limit,
        which defaults to 10,000 items. If any more data is requested, the data will be paginated.

        Args:
            endpoint_data_type (str): The data API endpoint path - /bars, /quotes, etc
            symbol_or_symbols (Union[str, List[str]]): The symbol or list of symbols that we want to query for
            endpoint_asset_class (str): The data API security type path. Defaults to 'stocks'.
            api_version (str): Data API version. Defaults to "v2".
            limit (Optional[int]): The maximum number of items to query. Defaults to None.
            page_limit (Optional[int]): The maximum number of items returned per page - different from limit. Defaults to DATA_V2_MAX_LIMIT.

        Returns:
            RawData: Raw Market data from API
        """
        # params contains the payload data
        params = kwargs

        # stocks, crypto, etc
        path = f"/{endpoint_asset_class}"

        multi_symbol = not isinstance(symbol_or_symbols, str)

        # multiple symbols passed as query params
        # single symbols are path params
        if not multi_symbol:
            path += f"/{symbol_or_symbols}"
        else:
            params["symbols"] = ",".join(symbol_or_symbols)

        # TODO: Improve this mess if possible
        if extension == DataExtensionType.LATEST:
            path += f"/{endpoint_data_type}"
            path += "/latest"
        elif extension == DataExtensionType.SNAPSHOT:
            path += "/snapshots" if multi_symbol else "/snapshot"
        else:
            # bars, trades, quotes, etc
            path += f"/{endpoint_data_type}"

        # data_by_symbol is in format of
        #    {
        #       "symbol1": [ "data1", "data2", ... ],
        #       "symbol2": [ "data1", "data2", ... ],
        #                ....
        #    }
        data_by_symbol = defaultdict(list)

        total_items = 0
        page_token = None

        while True:
            actual_limit = None

            # adjusts the limit parameter value if it is over the page_limit
            if limit:
                # actual_limit is the adjusted total number of items to query per request
                actual_limit = min(int(limit) - total_items, page_limit)
                if actual_limit < 1:
                    break

            params["limit"] = actual_limit
            params["page_token"] = page_token

            response = self.get(path=path, data=params, api_version=api_version)

            # TODO: Merge parsing if possible
            if extension == DataExtensionType.SNAPSHOT:
                format_snapshot_data(response, data_by_symbol)
            elif extension == DataExtensionType.LATEST:
                format_latest_data_response(response, data_by_symbol)
            else:
                format_dataset_response(response, data_by_symbol)

            # if we've sent a request with a limit, increment count
            if actual_limit:
                total_items = sum([len(items) for items in data_by_symbol.values()])

            page_token = response.get("next_page_token", None)

            if page_token is None:
                break

        # users receive Type dict
        return dict(data_by_symbol)
