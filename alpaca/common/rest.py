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
from alpaca.common.utils import get_api_version, get_credentials

from .enums import BaseURL


class RESTClient(ABC):
    """Abstract base class for REST clients"""

    def __init__(
        self,
        api_key: str = None,
        secret_key: str = None,
        api_version: str = "v2",
        base_url: Optional[BaseURL] = None,
        sandbox: bool = False,
        raw_data: bool = False,
    ) -> None:
        """Abstract base class for REST clients. Handles submitting HTTP requests to
        Alpaca API endpoints.

        Args:
            api_key (str, optional): description. Defaults to None.
            secret_key (str, optional): description. Defaults to None.
            api_version (str, optional): description. Defaults to 'v2'.
            base_url (Optional[BaseURL], optional): description. Defaults to None.
            sandbox (bool, optional): description. Defaults to False.
            raw_data (bool, optional): description. Defaults to False.
        """

        self._api_key, self._secret_key = get_credentials(api_key, secret_key)
        self._api_version: str = get_api_version(api_version)
        self._base_url: BaseURL = base_url
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
        headers = {}

        if (
            self._base_url == BaseURL.BROKER_PRODUCTION
            or self._base_url == BaseURL.BROKER_SANDBOX
        ):
            auth_string = f"{self._api_key}:{self._secret_key}"
            auth_string_encoded = base64.b64encode(str.encode(auth_string))
            headers["Authorization"] = "Basic " + auth_string_encoded.decode("utf-8")
        else:
            headers["APCA-API-KEY-ID"] = self._api_key
            headers["APCA-API-SECRET-KEY"] = self._secret_key

        headers["User-Agent"] = "APCA-PY/" + __version__

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
        resp = self._session.request(method, url, **opts)

        try:
            resp.raise_for_status()
        except HTTPError as http_error:
            # retry if we hit Rate Limit
            if resp.status_code in retry_codes and retry > 0:
                raise RetryException()
            if "code" in resp.text:
                error = resp.json()
                if "code" in error:
                    raise APIError(error, http_error)

        if resp.text != "":
            return resp.json()

    def _data_get(
        self,
        endpoint: str,
        symbol_or_symbols: Union[str, List[str]],
        endpoint_base: str = "stocks",
        api_version: str = "v2",
        page_limit: int = DATA_V2_MAX_LIMIT,
        **kwargs,
    ) -> Generator[dict, None, None]:
        """Performs Data API GET requests accounting for pagination. Data in responses are limited to 10,000 items.
        If any more data is requested, the data will be paginated.

        Args:
            endpoint (str): The data API endpoint path - /bars, /quotes, etc
            symbol_or_symbols (Union[str, List[str]]): The symbol or list of symbols that we want to query for
            endpoint_base (str, optional): The data API security type path. Defaults to 'stocks'.
            api_version (str, optional): Data API version. Defaults to "v2".
            resp_grouped_by_symbol (Optional[bool], optional): _description_. Defaults to None.
            page_limit (int, optional): _description_. Defaults to DATA_V2_MAX_LIMIT.

        Yields:
            Generator[dict, None, None]: _description_
        """
        page_token = None
        total_items = 0
        limit = kwargs.get("limit")

        data = kwargs

        path = f"/{endpoint_base}"

        if isinstance(symbol_or_symbols, str) and symbol_or_symbols:
            path += f"/{symbol_or_symbols}"
        else:
            data["symbols"] = ",".join(symbol_or_symbols)

        if endpoint:
            path += f"/{endpoint}"

        resp_grouped_by_symbol = not isinstance(symbol_or_symbols, str)

        while True:

            actual_limit = None
            if limit:
                actual_limit = min(int(limit) - total_items, page_limit)
                if actual_limit < 1:
                    break

            data["limit"] = actual_limit
            data["page_token"] = page_token

            resp = self.get(path, data, api_version=api_version)

            if not resp_grouped_by_symbol:
                # required for /news endpoint
                k = endpoint or endpoint_base
                for item in resp.get(k, []) or []:
                    total_items += 1
                    yield item
            else:
                by_symbol = resp.get(endpoint, {}) or {}
                total_items += 1
                yield by_symbol

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
