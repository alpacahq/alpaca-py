from collections import defaultdict
from enum import Enum
from typing import Dict, List, Optional, Union

from alpaca.common.constants import DATA_V2_MAX_LIMIT
from alpaca.common.enums import BaseURL
from alpaca.common.rest import RESTClient
from alpaca.common.types import RawData
from alpaca.data.historical.utils import (
    format_dataset_response,
    format_latest_data_response,
    format_snapshot_data,
    parse_obj_as_symbol_dict,
)
from alpaca.data.models.quotes import Quote
from alpaca.data.models.snapshots import Snapshot
from alpaca.data.models.trades import Trade
from alpaca.data.requests import (
    OptionChainRequest,
    OptionLatestQuoteRequest,
    OptionLatestTradeRequest,
    OptionSnapshotRequest,
)


class DataExtensionType(Enum):
    """Used to classify the type of endpoint path extensions"""

    LATEST = "latest"
    SNAPSHOT = "snapshot"


class OptionHistoricalDataClient(RESTClient):
    """
    The REST client for interacting with Alpaca Market Data API option data endpoints.

    Learn more on https://docs.alpaca.markets/docs/about-market-data-api
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        oauth_token: Optional[str] = None,
        use_basic_auth: bool = False,
        raw_data: bool = False,
        url_override: Optional[str] = None,
    ) -> None:
        """
        Instantiates a Historical Data Client.

        Args:
            api_key (Optional[str], optional): Alpaca API key. Defaults to None.
            secret_key (Optional[str], optional): Alpaca API secret key. Defaults to None.
            oauth_token (Optional[str]): The oauth token if authenticating via OAuth. Defaults to None.
            use_basic_auth (bool, optional): If true, API requests will use basic authorization headers.
            raw_data (bool, optional): If true, API responses will not be wrapped and raw responses will be returned from
              methods. Defaults to False. This has not been implemented yet.
            url_override (Optional[str], optional): If specified allows you to override the base url the client points
              to for proxy/testing.
        """
        super().__init__(
            api_key=api_key,
            secret_key=secret_key,
            oauth_token=oauth_token,
            use_basic_auth=use_basic_auth,
            api_version="v1beta1",
            base_url=url_override if url_override is not None else BaseURL.DATA,
            sandbox=False,
            raw_data=raw_data,
        )

    def get_option_latest_quote(
        self, request_params: OptionLatestQuoteRequest
    ) -> Union[Dict[str, Quote], RawData]:
        """Retrieves the latest quote for an option symbol or list of option symbols.

        Args:
            request_params (OptionLatestQuoteRequest): The request object for retrieving the latest quote data.

        Returns:
            Union[Dict[str, Quote], RawData]: The latest quote in raw or wrapped format
        """
        params = request_params.to_request_fields()

        raw_latest_quotes = self._data_get(
            endpoint_data_type="quotes",
            endpoint_asset_class="options",
            api_version=self._api_version,
            extension=DataExtensionType.LATEST,
            **params,
        )

        if self._use_raw_data:
            return raw_latest_quotes

        return parse_obj_as_symbol_dict(Quote, raw_latest_quotes)

    def get_option_latest_trade(
        self, request_params: OptionLatestTradeRequest
    ) -> Union[Dict[str, Trade], RawData]:
        """Retrieves the latest trade for an option symbol or list of option symbols.

        Args:
            request_params (OptionLatestQuoteRequest): The request object for retrieving the latest quote data.

        Returns:
            Union[Dict[str, Quote], RawData]: The latest quote in raw or wrapped format
        """
        params = request_params.to_request_fields()

        raw_latest_quotes = self._data_get(
            endpoint_data_type="trades",
            endpoint_asset_class="options",
            api_version=self._api_version,
            extension=DataExtensionType.LATEST,
            **params,
        )

        if self._use_raw_data:
            return raw_latest_quotes

        return parse_obj_as_symbol_dict(Trade, raw_latest_quotes)

    def get_option_snapshot(
        self, request_params: OptionSnapshotRequest
    ) -> Union[Dict[str, Snapshot], RawData]:
        """Returns snapshots of queried symbols. Snapshots contain latest trade and latest quote for the queried symbols.

        Args:
            request_params (OptionSnapshotRequest): The request object for retrieving snapshot data.

        Returns:
            Union[SnapshotSet, RawData]: The snapshot data either in raw or wrapped form
        """

        params = request_params.to_request_fields()

        raw_snapshots = self._data_get(
            endpoint_asset_class="options",
            endpoint_data_type="snapshot",
            api_version=self._api_version,
            extension=DataExtensionType.SNAPSHOT,
            **params,
        )

        if self._use_raw_data:
            return raw_snapshots

        return parse_obj_as_symbol_dict(Snapshot, raw_snapshots)

    def get_option_chain(
        self, request_params: OptionChainRequest
    ) -> Union[Dict[str, Snapshot], RawData]:
        """The option chain endpoint for underlying symbol provides the latest trade, latest quote for each contract symbol of the underlying symbol.

        Args:
            request_params (OptionChainRequest): The request object for retrieving snapshot data.

        Returns:
            Union[SnapshotSet, RawData]: The snapshot data either in raw or wrapped form
        """

        params = request_params.to_request_fields()

        raw_snapshots = self._data_get(
            endpoint_asset_class="options",
            endpoint_data_type="snapshot",
            api_version=self._api_version,
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
        symbol_or_symbols: Optional[Union[str, List[str]]] = None,
        limit: Optional[int] = None,
        page_limit: int = DATA_V2_MAX_LIMIT,
        extension: Optional[DataExtensionType] = None,
        underlying_symbol: Optional[str] = None,
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

        if underlying_symbol is not None:
            pass
        # multiple symbols passed as query params
        # single symbols are path params
        elif not multi_symbol:
            params["symbols"] = symbol_or_symbols
        else:
            params["symbols"] = ",".join(symbol_or_symbols)

        # TODO: Improve this mess if possible
        if extension == DataExtensionType.LATEST:
            path += f"/{endpoint_data_type}"
            path += "/latest"
        elif extension == DataExtensionType.SNAPSHOT:
            path += "/snapshots"
        else:
            # bars, trades, quotes, etc
            path += f"/{endpoint_data_type}"

        if underlying_symbol is not None:
            path += f"/{underlying_symbol}"
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
