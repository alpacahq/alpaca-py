from typing import Iterator, Optional, Union

import sseclient
from requests.exceptions import HTTPError

from alpaca.common.enums import BaseURL
from alpaca.common.exceptions import APIError
from alpaca.common.rest import RESTClient
from alpaca.common.types import RawData
from alpaca.data.models.corporate_actions import CorporateActionsSet
from alpaca.data.requests import CorporateActionEventsRequest, CorporateActionsRequest


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
            api_version="v1",
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
        if request_params.cusips:
            params["cusips"] = ",".join(request_params.cusips)
        if request_params.types:
            params["types"] = ",".join(request_params.types)
        if request_params.ids:
            params["ids"] = ",".join(request_params.ids)

        response = self._get_marketdata(
            path="/corporate-actions",
            params=params,
            page_limit=1000,
            page_size=1000,
        )
        if self._use_raw_data:
            return response

        return CorporateActionsSet(response)

    def get_corporate_action_events(
        self, request_params: Optional[CorporateActionEventsRequest] = None
    ) -> Iterator:
        """
        Subscribes to the corporate-actions SSE stream.

        The client itself is version ``v1``. This stream is ``v1beta1``, so the
        request URL is ``/v1beta1/events/corporate-actions`` and does not use the
        client API version prefix.

        Args:
            request_params: Query filters and the optional ``Last-Event-Id`` reconnect header.

        Returns:
            Iterator: Yields event payloads as they arrive.
        """
        params = {}
        headers = self._get_sse_headers()

        if request_params is not None:
            params = request_params.to_request_fields()
            if request_params.last_event_id:
                headers["Last-Event-Id"] = request_params.last_event_id

        url = self._base_url + "/v1beta1/events/corporate-actions"
        response = self._session.get(
            url=url,
            params=params,
            stream=True,
            headers=headers,
        )
        try:
            response.raise_for_status()
        except HTTPError as http_error:
            response.close()
            raise APIError(response.text, http_error)

        client = sseclient.SSEClient(response)
        try:
            for event in client.events():
                yield event.data
        finally:
            response.close()

    def _get_sse_headers(self) -> dict:
        headers = self._get_default_headers()
        headers["Connection"] = "keep-alive"
        headers["Cache-Control"] = "no-cache"
        headers["Accept"] = "text/event-stream"
        return headers
