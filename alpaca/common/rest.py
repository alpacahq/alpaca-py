from collections import defaultdict
from collections.abc import Callable
import time
import base64
from abc import ABC
from typing import Any, Dict, List, Optional, Type, Union, Tuple, Iterator

from pydantic import BaseModel
from requests import Session
from requests.exceptions import HTTPError
from itertools import chain

from alpaca.common.constants import (
    DEFAULT_RETRY_ATTEMPTS,
    DEFAULT_RETRY_WAIT_SECONDS,
    DEFAULT_RETRY_EXCEPTION_CODES,
)

from alpaca import __version__
from alpaca.common.exceptions import APIError, RetryException
from alpaca.common.types import RawData, HTTPResult, Credentials
from .constants import PageItem
from .enums import PaginationType, BaseURL


class RESTClient(ABC):
    """Abstract base class for REST clients"""

    def __init__(
        self,
        base_url: Union[BaseURL, str],
        api_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        oauth_token: Optional[str] = None,
        use_basic_auth: bool = False,
        api_version: str = "v2",
        sandbox: bool = False,
        raw_data: bool = False,
        retry_attempts: Optional[int] = None,
        retry_wait_seconds: Optional[int] = None,
        retry_exception_codes: Optional[List[int]] = None,
    ) -> None:
        """Abstract base class for REST clients. Handles submitting HTTP requests to
        Alpaca API endpoints.

        Args:
            base_url (Union[BaseURL, str]): The base url to target requests to. Should be an instance of BaseURL, but
              allows for raw str if you need to override
            api_key (Optional[str]): The api key string for authentication.
            secret_key (Optional[str]): The corresponding secret key string for the api key.
            oauth_token (Optional[str]): The oauth token if authenticating via OAuth.
            use_basic_auth (bool): Whether API requests should use basic authorization headers.
            api_version (Optional[str]): The API version for the endpoints.
            sandbox (bool): False if the live API should be used.
            raw_data (bool): Whether API responses should be wrapped in data models or returned raw.
            retry_attempts (Optional[int]): The number of times to retry a request that returns a RetryException.
            retry_wait_seconds (Optional[int]): The number of seconds to wait between requests before retrying.
            retry_exception_codes (Optional[List[int]]): The API exception codes to retry a request on.
        """

        self._api_key, self._secret_key, self._oauth_token = self._validate_credentials(
            api_key=api_key, secret_key=secret_key, oauth_token=oauth_token
        )
        self._api_version: str = api_version
        self._base_url: Union[BaseURL, str] = base_url
        self._sandbox: bool = sandbox
        self._use_basic_auth: bool = use_basic_auth
        self._use_raw_data: bool = raw_data
        self._session: Session = Session()

        # setting up request retry configurations
        self._retry: int = DEFAULT_RETRY_ATTEMPTS
        self._retry_wait: int = DEFAULT_RETRY_WAIT_SECONDS
        self._retry_codes: List[int] = DEFAULT_RETRY_EXCEPTION_CODES

        if retry_attempts and retry_attempts > 0:
            self._retry = retry_attempts

        if retry_wait_seconds and retry_wait_seconds > 0:
            self._retry_wait = retry_wait_seconds

        if retry_exception_codes:
            self._retry_codes = retry_exception_codes

    def _request(
        self,
        method: str,
        path: str,
        data: Optional[Union[dict, str]] = None,
        base_url: Optional[Union[BaseURL, str]] = None,
        api_version: Optional[str] = None,
    ) -> HTTPResult:
        """Prepares and submits HTTP requests to given API endpoint and returns response.
        Handles retrying if 429 (Rate Limit) error arises.

        Args:
            method (str): The API endpoint HTTP method
            path (str): The API endpoint path
            data (Optional[Union[dict, str]]): Either the payload in json format, query params urlencoded, or a dict
             of values to be converted to appropriate format based on `method`. Defaults to None.
            base_url (Optional[Union[BaseURL, str]]): The base URL of the API. Defaults to None.
            api_version (Optional[str]): The API version. Defaults to None.

        Returns:
            HTTPResult: The response from the API
        """
        base_url = base_url or self._base_url
        version = api_version if api_version else self._api_version
        url: str = base_url + "/" + version + path

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

        while retry >= 0:
            try:
                return self._one_request(method, url, opts, retry)
            except RetryException:
                time.sleep(self._retry_wait)
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
        elif self._use_basic_auth:
            api_key_secret = "{key}:{secret}".format(
                key=self._api_key, secret=self._secret_key
            ).encode("utf-8")
            encoded_api_key_secret = base64.b64encode(api_key_secret).decode("utf-8")
            headers["Authorization"] = "Basic " + encoded_api_key_secret
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
        response = self._session.request(method, url, **opts)

        try:
            response.raise_for_status()
        except HTTPError as http_error:
            # retry if we hit Rate Limit
            if response.status_code in self._retry_codes and retry > 0:
                raise RetryException()

            # raise API error for all other errors
            error = response.text

            raise APIError(error, http_error)

        if response.text != "":
            return response.json()

    def get(
        self, path: str, data: Optional[Union[dict, str]] = None, **kwargs
    ) -> HTTPResult:
        """Performs a single GET request

        Args:
            path (str): The API endpoint path
            data (Union[dict, str], optional): Query parameters to send, either
            as a str urlencoded, or a dict of values to be converted. Defaults to None.

        Returns:
            dict: The response
        """
        return self._request("GET", path, data, **kwargs)

    def post(
        self, path: str, data: Optional[Union[dict, List[dict]]] = None
    ) -> HTTPResult:
        """Performs a single POST request

        Args:
            path (str): The API endpoint path
            data (Optional[Union[dict, List[dict]]): The json payload as a dict of values to be converted.
             Defaults to None.

        Returns:
            dict: The response
        """
        return self._request("POST", path, data)

    def put(self, path: str, data: Optional[dict] = None) -> dict:
        """Performs a single PUT request

        Args:
            path (str): The API endpoint path
            data (Optional[dict]): The json payload as a dict of values to be converted.
             Defaults to None.

        Returns:
            dict: The response
        """
        return self._request("PUT", path, data)

    def patch(self, path: str, data: Optional[dict] = None) -> dict:
        """Performs a single PATCH request

        Args:
            path (str): The API endpoint path
            data (Optional[dict]): The json payload as a dict of values to be converted.
             Defaults to None.

        Returns:
            dict: The response
        """
        return self._request("PATCH", path, data)

    def delete(self, path, data: Optional[Union[dict, str]] = None) -> dict:
        """Performs a single DELETE request

        Args:
            path (str): The API endpoint path
            data (Union[dict, str], optional): The payload if any. Defaults to None.

        Returns:
            dict: The response
        """
        return self._request("DELETE", path, data)

    # TODO: Refactor to be able to handle both parsing to types and parsing to collections of types (parse_as_obj)
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

    @staticmethod
    def _validate_pagination(
        max_items_limit: Optional[int], handle_pagination: Optional[PaginationType]
    ) -> PaginationType:
        """
        Private method for validating the max_items_limit and handle_pagination arguments, returning the resolved
        PaginationType.
        """
        if handle_pagination is None:
            handle_pagination = PaginationType.FULL

        if handle_pagination != PaginationType.FULL and max_items_limit is not None:
            raise ValueError(
                "max_items_limit can only be specified for PaginationType.FULL"
            )
        return handle_pagination

    @staticmethod
    def _return_paginated_result(
        iterator: Iterator[PageItem], handle_pagination: PaginationType
    ) -> Union[List[PageItem], Iterator[List[PageItem]]]:
        """
        Private method for converting an iterator that yields results to the proper pagination type result.
        """
        if handle_pagination == PaginationType.NONE:
            # user wants no pagination, so just do a single page
            return next(iterator)
        elif handle_pagination == PaginationType.FULL:
            # the iterator returns "pages", so we use chain to flatten them all into 1 list
            return list(chain.from_iterable(iterator))
        elif handle_pagination == PaginationType.ITERATOR:
            return iterator
        else:
            raise ValueError(f"Invalid pagination type: {handle_pagination}.")

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

        if not oauth_token and not api_key:
            raise ValueError("You must supply a method of authentication")

        if oauth_token and (api_key or secret_key):
            raise ValueError(
                "Either an oauth_token or an api_key may be supplied, but not both"
            )

        if not oauth_token and not (api_key and secret_key):
            raise ValueError(
                "A corresponding secret_key must be supplied with the api_key"
            )

        return api_key, secret_key, oauth_token

    def _get_marketdata(
        self,
        path: str,
        params: Dict[str, Any],
        page_limit: int = 10_000,
        page_size: Optional[int] = None,
        no_sub_key: bool = False,
    ) -> Dict[str, List[Any]]:
        d = defaultdict(list)
        # Missing page_size indicates that we should not set a limit (e.g. for latest endpoints)
        actual_limit = min(page_size, page_limit) if page_size else None
        limit = params.get("limit")
        total_items = 0
        page_token = params.get("page_token")

        while True:
            # adjusts the limit parameter value if it is over the page_limit
            if limit:
                # actual_limit is the adjusted total number of items to query per request
                actual_limit = min(int(limit) - total_items, page_limit)
                if actual_limit < 1:
                    break
            params["limit"] = actual_limit
            params["page_token"] = page_token

            response = self.get(path=path, data=params)

            for k, v in _get_marketdata_entries(response, no_sub_key).items():
                if isinstance(v, list):
                    d[k].extend(v)
                else:
                    d[k] = v

            # if we've sent a request with a limit, increment count
            if actual_limit:
                total_items = sum([len(items) for items in d.values()])

            page_token = response.get("next_page_token", None)
            if page_token is None:
                break
        return dict(d)


def _get_marketdata_entries(response: HTTPResult, no_sub_key: bool) -> RawData:
    if no_sub_key:
        return response

    data_keys = {
        "bar",
        "bars",
        "corporate_actions",
        "news",
        "orderbook",
        "orderbooks",
        "quote",
        "quotes",
        "snapshot",
        "snapshots",
        "trade",
        "trades",
    }
    selected_keys = data_keys.intersection(response)
    # Neither of these should ever happen!
    if selected_keys is None or len(selected_keys) < 1:
        raise ValueError("The data in response does not match any known keys.")
    if len(selected_keys) > 1:
        raise ValueError("The data in response matches multiple known keys.")
    selected_key = selected_keys.pop()
    if selected_key == "news":
        return {"news": response[selected_key]}
    return response[selected_key]
