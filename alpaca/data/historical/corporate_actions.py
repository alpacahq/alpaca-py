from collections import defaultdict
from typing import Callable, Optional, Union

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
        Instantiates a Corporate Actions Client.

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

        if request_params.symbols:
            params["symbols"] = ",".join(request_params.symbols)
        if request_params.types:
            params["types"] = ",".join(request_params.types)

        response = self._data_get(
            path="/corporate-actions", api_version=self._api_version, **params
        )
        if self._use_raw_data:
            return response

        return CorporateActionsSet(response)

    # TODO: Refactor data_get (common to all historical data queries!)
    def _data_get(
        self,
        path: str,
        limit: Optional[int] = None,
        page_limit: int = 1000,
        api_version: str = "v1",
        **kwargs,
    ) -> RawData:
        params = kwargs

        # data is grouped by corporate action type (reverse_splits, forward_splits, etc.)
        d = defaultdict(list)

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

            for ca_type, cas in get_data_from_response(response).items():
                d[ca_type].extend(cas)

            # if we've sent a request with a limit, increment count
            if actual_limit:
                total_items = sum([len(items) for items in d.values()])

            page_token = response.get("next_page_token", None)

            if page_token is None:
                break

        # users receive Type dict
        return dict(d)
