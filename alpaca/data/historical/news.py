from collections import defaultdict
from enum import Enum
from typing import Any, Optional, Union, List
from alpaca.common.constants import DATA_V2_MAX_LIMIT

from alpaca.common.rest import RESTClient

from alpaca.common.enums import BaseURL

from alpaca.data.requests import NewsRequest

from alpaca.data.models import NewsSet

from alpaca.common.types import RawData


class NewsClient(RESTClient):
    """
    The REST client for interacting with Alpaca News API endpoints.

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

    def get_news(self, request_params: NewsRequest) -> Union[RawData, NewsSet]:
        """Returns news data

        Args:
            request_params (NewsRequest): The request params to filter the news data
        Returns:
            Union[RawData, NewsSet]: The news data
        """

        params = request_params.to_request_fields()
        # paginated get request for news data api
        raw_news = self._data_get(
            symbol_or_symbols=request_params.symbols,
            **params,
        )

        if self._use_raw_data:
            return raw_news

        return NewsSet(raw_news)

    # TODO: Remove duplication
    def _data_get(
        self,
        symbol_or_symbols: Union[str, List[str]],
        endpoint_asset_class: str = "news",
        api_version: str = "v1beta1",
        limit: Optional[int] = 10,
        page_limit: int = DATA_V2_MAX_LIMIT,
        **kwargs,
    ) -> RawData:
        """Performs Data API GET requests accounting for pagination. Data in responses are limited to the page_limit,
        which defaults to 10,000 items. If any more data is requested, the data will be paginated.

        Args:
            symbol_or_symbols (Union[str, List[str]]): The symbol or list of symbols that we want to query for
            api_version (str): Data API version. Defaults to "v1beta1".
            endpoint_asset_class (str): The data API security type path. Defaults to 'news'.
            limit (Optional[int]): The maximum number of items to query. Defaults to None.
            page_limit (Optional[int]): The maximum number of items returned per page - different from limit. Defaults to DATA_V2_MAX_LIMIT.

        Returns:
            RawData: Raw News Market data from API
        """
        # params contains the payload data
        params = kwargs

        # stocks, crypto, etc
        path = f"/{endpoint_asset_class}"

        params["symbols"] = symbol_or_symbols

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

            [data_by_symbol["news"].extend(response["news"])]

            # if we've sent a request with a limit, increment count
            if actual_limit:
                total_items += actual_limit

            page_token = response.get("next_page_token", None)

            if page_token is None:
                break

        # users receive Type dict
        return dict(data_by_symbol)
