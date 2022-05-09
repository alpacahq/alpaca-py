import base64
import os
import time
from abc import ABC
from typing import Generator, List, Optional, Union, Type

from pydantic import BaseModel
from requests import Session
from requests.exceptions import HTTPError

from alpaca import __version__
from alpaca.common.constants import DATA_V2_MAX_LIMIT
from alpaca.common.exceptions import APIError, RetryException
from alpaca.common.types import RawData
from alpaca.common.utils import get_api_version, validate_credentials

from .enums import BaseURL


class RESTClient(ABC):
    """Abstract base class for REST clients"""

    def __init__(
        self,
        base_url: Union[BaseURL, str],
        api_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        oauth_token: Optional[str] = None,
        api_version: str = "v2",
        sandbox: bool = False,
        raw_data: bool = False,
    ) -> None:
        """Abstract base class for REST clients. Handles submitting HTTP requests to
        Alpaca API endpoints.

        Args:
            base_url (Union[BaseURL, str]): The base url to target requests to. Should be an instance of BaseURL, but
              allows for raw str if you need to override
            api_key (Optional[str]): The api key string for authentication. Defaults to None.
            secret_key (Optional[str]): The corresponding secret key string for the api key. Defaults to None.
            oauth_token (Optional[str]): The oauth token if authenticating via OAuth. Defaults to None.
            api_version (Optional[str]): The API version for the endpoints. Defaults to 'v2'.
            sandbox (bool): False if the live API should be used. Defaults to False.
            raw_data (bool): Whether API responses should be wrapped in data models or returned raw. Defaults to False.
        """

        self._api_key, self._secret_key, self._oauth_token = validate_credentials(
            api_key, secret_key, oauth_token
        )
        self._api_version: str = get_api_version(api_version)
        self._base_url: Union[BaseURL, str] = base_url
        self._sandbox: bool = sandbox
        self._use_raw_data: bool = raw_data
        self._session: Session = Session()
        self._retry = int(os.environ.get("APCA_RETRY_MAX", 3))
        self._retry_wait = int(os.environ.get("APCA_RETRY_WAIT", 3))
        self._retry_codes = [
            int(o) for o in os.environ.get("APCA_RETRY_CODES", "429,504").split(",")
        ]

    def _request(
        self,
        method: str,
        path: str,
        data: dict = None,
        base_url: BaseURL = None,
        api_version: str = None,
    ) -> dict:
        """Prepares and submits HTTP requests to given API endpoint and returns response.
        Handles retrying if 429 (Rate Limit) error arises.

        Args:
            method (str): The API endpoint HTTP method
            path (str): The API endpoint path
            data (dict, optional): The payload if any. Defaults to None.
            base_url (BaseURL, optional): The base URL of the API. Defaults to None.
            api_version (str, optional): The API version. Defaults to None.

        Returns:
            dict: The response from the API
        """
        base_url = base_url or self._base_url
        version = api_version if api_version else self._api_version
        url: str = base_url.value + "/" + version + path

        headers = self._get_default_headers()

        opts = {
            "headers": headers,
            # Since we allow users to set endpoint URL via env var,
            # human error to put non-SSL endpoint could exploit
            # uncanny issues in non-GET request redirecting http->https.
            # It's better to fail early if the URL isn't right.
            "allow_redirects": False,
        }

        if method.upper() in ["GET", "DELETE"]:
            opts["params"] = data
        else:
            opts["json"] = data

        retry = self._retry
        if retry < 0:
            retry = 0
        while retry >= 0:
            try:
                return self._one_request(method, url, opts, retry)
            except RetryException:
                retry_wait = self._retry_wait
                time.sleep(retry_wait)
                retry -= 1
                continue

    def _get_default_headers(self) -> dict:
        """
        Returns a dict with some default headers set; ie AUTH headers and such that should be useful on all requests
        Extracted for cases when using the default request functions are insufficient
        Returns:
            dict: The resulting dict of headers
        """
        headers = self._get_auth_headers()

        headers["User-Agent"] = "APCA-PY/" + __version__

        return headers

    def _get_auth_headers(self) -> dict:
        """
        Get the auth headers for a request. Meant to be overridden in clients that don't use this format for requests,
        ie: BrokerClient
        Returns:
            dict: A dict containing the expected auth headers
        """

        headers = {}

        if self._oauth_token:
            headers["Authorization"] = "Bearer " + self._oauth_token
        else:
            headers["APCA-API-KEY-ID"] = self._api_key
            headers["APCA-API-SECRET-KEY"] = self._secret_key

        return headers

    def _one_request(self, method: str, url: str, opts: dict, retry: int) -> dict:
        """Perform one request, possibly raising RetryException in the case
        the response is 429. Otherwise, if error text contain "code" string,
        then it decodes to json object and returns APIError.
        Returns the body json in the 200 status.

        Args:
            method (str): The HTTP method - GET, POST, etc
            url (str): The API endpoint URL
            opts (dict): Contains optional parameters including headers and parameters
            retry (int): The number of times to retry in case of RetryException

        Raises:
            RetryException: Raised if request produces 429 error and retry limit has not been reached
            APIError: Raised if API returns an error

        Returns:
            dict: The response data
        """
        retry_codes = self._retry_codes
        response = self._session.request(method, url, **opts)

        try:
            response.raise_for_status()
        except HTTPError as http_error:

            # retry if we hit Rate Limit or any other exception that allows retries
            if response.status_code in retry_codes and retry > 0:
                raise RetryException()

            # raise API error for all other errors
            error = response.json()

            raise APIError(error, http_error)

        if response.text != "":
            return response.json()

    def _data_get(
        self,
        endpoint: str,
        symbol_or_symbols: Union[str, List[str]],
        endpoint_base: str = "stocks",
        api_version: str = "v2",
        max_items_limit: Optional[int] = None,
        page_limit: int = DATA_V2_MAX_LIMIT,
        **kwargs,
    ) -> Generator[dict, None, None]:
        """Performs Data API GET requests accounting for pagination. Data in responses are limited to the page_limit,
        which defaults to 10,000 items. If any more data is requested, the data will be paginated.

        Args:
            endpoint (str): The data API endpoint path - /bars, /quotes, etc
            symbol_or_symbols (Union[str, List[str]]): The symbol or list of symbols that we want to query for
            endpoint_base (str, optional): The data API security type path. Defaults to 'stocks'.
            api_version (str, optional): Data API version. Defaults to "v2".
            max_items_limit (Optional[int]): The maximum number of items to query. Defaults to None.
            page_limit (int, optional): The maximum number of items returned per page - different from limit. Defaults to DATA_V2_MAX_LIMIT.

        Yields:
            Generator[dict, None, None]: Market data from API
        """
        page_token = None
        total_items = 0

        data = kwargs

        path = f"/{endpoint_base}"

        multi_symbol = not isinstance(symbol_or_symbols, str)

        if not multi_symbol and symbol_or_symbols:
            path += f"/{symbol_or_symbols}"
        else:
            data["symbols"] = ",".join(symbol_or_symbols)

        if endpoint:
            path += f"/{endpoint}"

        while True:

            actual_limit = None

            # adjusts the limit parameter value if it is over the page_limit
            if max_items_limit:
                # actual_limit is the adjusted total number of items to query per request
                actual_limit = min(int(max_items_limit) - total_items, page_limit)
                if actual_limit < 1:
                    break

            data["limit"] = actual_limit
            data["page_token"] = page_token

            resp = self.get(path, data, api_version=api_version)

            if not multi_symbol:
                # required for /news endpoint
                _endpoint = endpoint or endpoint_base

                data = resp.get(_endpoint, []) or []

                for item in data:
                    total_items += 1
                    yield item
            else:
                data_by_symbol = resp.get(endpoint, {}) or {}

                # if we've sent a request with a limit, increment count
                if actual_limit:
                    total_items += actual_limit

                yield data_by_symbol

            page_token = resp.get("next_page_token")

            if not page_token:
                break

    def get(self, path: str, data: dict = None, **kwargs) -> dict:
        """Performs a single GET request

        Args:
            path (str): The API endpoint path
            data (dict, optional): The payload if any - includes query parameters. Defaults to None.

        Returns:
            dict: The response
        """
        return self._request("GET", path, data, **kwargs)

    def post(self, path: str, data: dict = None) -> dict:
        """Performs a single POST request

        Args:
            path (str): The API endpoint path
            data (dict, optional): The payload if any. Defaults to None.

        Returns:
            dict: The response
        """
        return self._request("POST", path, data)

    def put(self, path: str, data: dict = None) -> dict:
        """Performs a single PUT request

        Args:
            path (str): The API endpoint path
            data (dict, optional): The payload if any. Defaults to None.

        Returns:
            dict: The response
        """
        return self._request("PUT", path, data)

    def patch(self, path: str, data: dict = None) -> dict:
        """Performs a single PATCH request

        Args:
            path (str): The API endpoint path
            data (dict, optional): The payload if any. Defaults to None.

        Returns:
            dict: The response
        """
        return self._request("PATCH", path, data)

    def delete(self, path, data=None) -> dict:
        """Performs a single DELETE request

        Args:
            path (str): The API endpoint path
            data (dict, optional): The payload if any. Defaults to None.

        Returns:
            dict: The response
        """
        return self._request("DELETE", path, data)

    def response_wrapper(
        self, model: Type[BaseModel], raw_data: RawData, **kwargs
    ) -> Union[BaseModel, RawData]:
        """To allow the user to get raw response from the api, we wrap all
        functions with this method, checking if the user has set raw_data
        bool. if they didn't, we wrap the response with a BaseModel object.

        Args:
            model (Type[BaseModel]): Class that response will be wrapped in
            raw_data (RawData): The raw data from API in dictionary
            kwargs : Any constructor parameters necessary for the base model

        Returns:
            Union[BaseModel, RawData]: either raw or parsed data
        """
        if self._use_raw_data:
            return raw_data
        else:
            return model(raw_data=raw_data, **kwargs)
