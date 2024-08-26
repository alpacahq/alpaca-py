from collections import defaultdict
from typing import Optional, Union

from alpaca.common.enums import BaseURL
from alpaca.common.rest import RESTClient
from alpaca.common.types import RawData
from alpaca.data.historical.utils import get_data_from_response
from alpaca.data.models.corporate_actions import CorporateActionsSet
from alpaca.data.requests import CorporateActionsRequest


class CorporateActionsClient(RESTClient):
    """
    The REST client for interacting with Alpaca Corporate Actions API endpoints.

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

    def get_corporate_actions(
        self, request_params: CorporateActionsRequest
    ) -> Union[RawData, CorporateActionsSet]:
        """Returns corporate actions data

        Args:
            request_params (CorporateActionsRequest): The request params to filter the corporate actions data
        """
        params = request_params.to_request_fields()

        if request_params.symbols is not None and len(request_params.symbols) > 0:
            params["symbols"] = ",".join(request_params.symbols)
        if request_params.types is not None and len(request_params.types) > 0:
            params["types"] = ",".join(request_params.types)

        response = self._data_get(
            path="/corporate-actions", api_version=self._api_version, **params
        )
        if self._use_raw_data:
            return response

        return CorporateActionsSet(response)

    def _data_get(
        self,
        path: str,
        limit: Optional[int] = None,
        page_limit: int = 1000,
        api_version: str = "v1beta1",
        **kwargs,
    ) -> RawData:
        """Performs Data API GET requests accounting for pagination. Data in responses are limited to the page_limit,
        which defaults to 1,000 items. If any more data is requested, the data will be paginated.

        Args:
            limit (Optional[int]): The maximum number of items to query. Defaults to None.
            page_limit (Optional[int]): The maximum number of items returned per page - different from limit. Defaults to 1000.

        Returns:
            RawData: Raw Market data from API
        """
        params = kwargs

        # data_by_type is in format of
        #    {
        #       "type1": [ "data1", "data2", ... ],
        #       "type2": [ "data1", "data2", ... ],
        #                ....
        #    }
        data_by_type = defaultdict(list)

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

            d = get_data_from_response(response)
            [
                (
                    data_by_type[ctype].extend(data)
                    if isinstance(data, list)
                    else data_by_type[ctype].append(data)
                )
                for ctype, data in d.items()
            ]

            # if we've sent a request with a limit, increment count
            if actual_limit:
                total_items = sum([len(items) for items in data_by_type.values()])

            page_token = response.get("next_page_token", None)

            if page_token is None:
                break

        # users receive Type dict
        return dict(data_by_type)
