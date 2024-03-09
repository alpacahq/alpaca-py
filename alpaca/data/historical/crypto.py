from collections import defaultdict
from typing import Union, Optional, List, Dict

from alpaca.common.constants import DATA_V2_MAX_LIMIT
from alpaca.common.types import RawData
from alpaca.common.enums import BaseURL
from alpaca.common.rest import RESTClient
from alpaca.common.types import Credentials
from alpaca.data import Snapshot, Bar
from alpaca.data.historical.utils import (
    parse_obj_as_symbol_dict,
    format_latest_data_response,
    format_dataset_response,
)
from alpaca.data.models import BarSet, QuoteSet, TradeSet, Orderbook, Trade, Quote
from alpaca.data.historical.stock import DataExtensionType
from alpaca.data.requests import (
    CryptoBarsRequest,
    CryptoTradesRequest,
    CryptoLatestTradeRequest,
    CryptoLatestQuoteRequest,
    CryptoSnapshotRequest,
    CryptoLatestOrderbookRequest,
    CryptoLatestBarRequest,
)
from alpaca.data.enums import CryptoFeed


class CryptoHistoricalDataClient(RESTClient):
    """
    A REST client for retrieving crypto market data.

    This client does not need any authentication to use.
    You can instantiate it with or without API keys.

    However, authenticating increases your data rate limit.

    Learn more about crypto historical data here:
    https://alpaca.markets/docs/api-references/market-data-api/crypto-pricing-data/historical/
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        oauth_token: Optional[str] = None,
        raw_data: bool = False,
        url_override: Optional[str] = None,
    ) -> None:
        """
        Instantiates a Historical Data Client for Crypto Data.

        Args:
            api_key (Optional[str], optional): Alpaca API key. Defaults to None.
            secret_key (Optional[str], optional): Alpaca API secret key. Defaults to None.
            oauth_token (Optional[str]): The oauth token if authenticating via OAuth. Defaults to None.
            raw_data (bool, optional): If true, API responses will not be wrapped and raw responses will be returned from
              methods. Defaults to False. This has not been implemented yet.
            url_override (Optional[str], optional): If specified allows you to override the base url the client points
              to for proxy/testing.
        """
        super().__init__(
            api_key=api_key,
            secret_key=secret_key,
            oauth_token=oauth_token,
            api_version="v1beta3",
            base_url=url_override if url_override is not None else BaseURL.DATA,
            sandbox=False,
            raw_data=raw_data,
        )

    def get_crypto_bars(
        self, request_params: CryptoBarsRequest, feed: CryptoFeed = CryptoFeed.US
    ) -> Union[BarSet, RawData]:
        """Gets bar/candle data for a cryptocurrency or list of cryptocurrencies.

        Args:
            request_params (CryptoBarsRequest): The parameters for the request.
            feed (CryptoFeed): The data feed for crypto bars.

        Returns:
            Union[BarSet, RawData]: The crypto bar data either in raw or wrapped form
        """

        params = request_params.to_request_fields()

        # paginated get request for crypto market data api
        raw_bars = self._data_get(
            endpoint_asset_class="crypto",
            endpoint_data_type="bars",
            api_version="v1beta3",
            feed=feed,
            **params,
        )

        if self._use_raw_data:
            return raw_bars

        return BarSet(raw_bars)

    def get_crypto_trades(
        self, request_params: CryptoTradesRequest, feed: CryptoFeed = CryptoFeed.US
    ) -> Union[TradeSet, RawData]:
        """Returns the price and sales history over a given time period for a cryptocurrency
        or list of cryptocurrencies.

        Args:
            request_params (CryptoTradesRequest): The parameters for the request.
            feed (CryptoFeed): The data feed for crypto trades.

        Returns:
            Union[TradeSet, RawData]: The trade data either in raw or wrapped form
        """

        params = request_params.to_request_fields()

        # paginated get request for market data api
        raw_trades = self._data_get(
            endpoint_asset_class="crypto",
            endpoint_data_type="trades",
            api_version="v1beta3",
            feed=feed,
            **params,
        )

        if self._use_raw_data:
            return raw_trades

        return TradeSet(raw_trades)

    def get_crypto_latest_trade(
        self, request_params: CryptoLatestTradeRequest, feed: CryptoFeed = CryptoFeed.US
    ) -> Union[Dict[str, Trade], RawData]:
        """Returns the latest trade for a coin.

        Args:
            request_params (CryptoLatestTradeRequest): The parameters for the request.
            feed (CryptoFeed): The data feed for the latest crypto trade.

        Returns:
            Union[Dict[str, Trade], RawData]: The latest trade in raw or wrapped format
        """

        params = request_params.to_request_fields()

        raw_trades = self._data_get(
            endpoint_asset_class="crypto",
            endpoint_data_type="trades",
            api_version="v1beta3",
            extension=DataExtensionType.LATEST,
            feed=feed,
            **params,
        )

        if self._use_raw_data:
            return raw_trades

        return parse_obj_as_symbol_dict(Trade, raw_trades)

    def get_crypto_latest_quote(
        self, request_params: CryptoLatestQuoteRequest, feed: CryptoFeed = CryptoFeed.US
    ) -> Union[Dict[str, Quote], RawData]:
        """Returns the latest quote for a coin.

        Args:
            request_params (CryptoLatestQuoteRequest): The parameters for the request.
            feed (CryptoFeed): The data feed for the latest crypto quote.

        Returns:
            Union[Dict[str, Quote], RawData]: The latest quote in raw or wrapped format
        """

        params = request_params.to_request_fields()

        raw_quotes = self._data_get(
            endpoint_asset_class="crypto",
            endpoint_data_type="quotes",
            api_version="v1beta3",
            extension=DataExtensionType.LATEST,
            feed=feed,
            **params,
        )

        if self._use_raw_data:
            return raw_quotes

        return parse_obj_as_symbol_dict(Quote, raw_quotes)

    def get_crypto_latest_bar(
        self, request_params: CryptoLatestBarRequest, feed: CryptoFeed = CryptoFeed.US
    ) -> Union[Dict[str, Bar], RawData]:
        """Returns the latest minute bar for a coin.

        Args:
            request_params (CryptoLatestBarRequest): The parameters for the request.
            feed (CryptoFeed): The data feed for the latest crypto bar.

        Returns:
            Union[Dict[str, Bar], RawData]: The latest bar in raw or wrapped format
        """

        params = request_params.to_request_fields()

        raw_bars = self._data_get(
            endpoint_asset_class="crypto",
            endpoint_data_type="bars",
            api_version="v1beta3",
            extension=DataExtensionType.LATEST,
            feed=feed,
            **params,
        )

        if self._use_raw_data:
            return raw_bars

        return parse_obj_as_symbol_dict(Bar, raw_bars)

    def get_crypto_latest_orderbook(
        self,
        request_params: CryptoLatestOrderbookRequest,
        feed: CryptoFeed = CryptoFeed.US,
    ) -> Union[Dict[str, Orderbook], RawData]:
        """
        Returns the latest orderbook state for the queried crypto symbols.

        Args:
            request_params (CryptoOrderbookRequest): The parameters for the orderbook request.
            feed (CryptoFeed): The data feed for the latest crypto orderbook.

        Returns:
            Union[Dict[str, Orderbook], RawData]: The orderbook data either in raw or wrapped form.
        """

        params = request_params.to_request_fields()

        raw_orderbooks = self._data_get(
            endpoint_asset_class="crypto",
            endpoint_data_type="orderbooks",
            api_version="v1beta3",
            extension=DataExtensionType.LATEST,
            feed=feed,
            **params,
        )

        if self._use_raw_data:
            return raw_orderbooks

        return parse_obj_as_symbol_dict(Orderbook, raw_orderbooks)

    def get_crypto_snapshot(
        self, request_params: CryptoSnapshotRequest, feed: CryptoFeed = CryptoFeed.US
    ) -> Union[Snapshot, RawData]:
        """Returns snapshots of queried crypto symbols. Snapshots contain latest trade, latest quote, latest minute bar,
        latest daily bar and previous daily bar data for the queried symbols.

        Args:
            request_params (CryptoSnapshotRequest): The parameters for the snapshot request.
            feed (CryptoFeed): The data feed for crypto snapshots.

        Returns:
            Union[SnapshotSet, RawData]: The snapshot data either in raw or wrapped form
        """

        params = request_params.to_request_fields()

        raw_snapshots = self._data_get(
            endpoint_asset_class="crypto",
            endpoint_data_type="snapshots",
            api_version="v1beta3",
            extension=DataExtensionType.SNAPSHOT,
            feed=feed,
            **params,
        )

        if self._use_raw_data:
            return raw_snapshots

        return parse_obj_as_symbol_dict(Snapshot, raw_snapshots)

    # TODO: Remove duplicate code
    def _data_get(
        self,
        endpoint_asset_class: str,
        endpoint_data_type: str,
        api_version: str,
        feed: CryptoFeed,
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
            page_limit (Optional[int]): The maximum number of items returned per page - different from limit.
                Defaults to DATA_V2_MAX_LIMIT.
            feed (CryptoFeed): The data feed for crypto snapshots.

        Returns:
            RawData: Raw Market data from API
        """
        # params contains the payload data
        params = kwargs

        # stocks, crypto, etc
        path = f"/{endpoint_asset_class}"

        path += f"/{feed.value}"

        if isinstance(symbol_or_symbols, str):
            symbol_or_symbols = [symbol_or_symbols]

        params["symbols"] = ",".join(symbol_or_symbols)

        # TODO: Improve this mess if possible
        if extension == DataExtensionType.LATEST:
            path += "/latest"
            path += f"/{endpoint_data_type}"
        elif extension == DataExtensionType.SNAPSHOT:
            path += "/snapshots"
        else:
            # bars, trades, quotes, etc
            path += f"/{endpoint_data_type}"

        # data_by_symbol is in format of
        #    {
        #       "symbol1": [ "data1", "data2", ... ],
        #       "symbol2": [ "data1", "data2", ... ],
        #                ....
        #    }
        # using default dict to improve parsing,
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
            if (
                extension == DataExtensionType.LATEST
                or extension == DataExtensionType.SNAPSHOT
            ):
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

    @staticmethod
    def _validate_credentials(
        api_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        oauth_token: Optional[str] = None,
    ) -> Credentials:
        """Gathers API credentials from parameters and environment variables, and validates them.
        Args:
            api_key (Optional[str]): The API key for authentication. Defaults to None.
            secret_key (Optional[str]): The secret key for authentication. Defaults to None.
            oauth_token (Optional[str]): The oauth token if authenticating via OAuth. Defaults to None.
        Raises:
             ValueError: If the combination of keys and tokens provided are not valid.
        Returns:
            Credentials: The set of validated authentication keys
        """

        if oauth_token and (api_key or secret_key):
            raise ValueError(
                "Either an oauth_token or an api_key may be supplied, but not both"
            )

        return api_key, secret_key, oauth_token
