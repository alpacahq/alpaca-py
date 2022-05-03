import base64
import os
import time
from abc import ABC
from typing import Any, List, Optional, Type, Union

from pydantic import BaseModel
from requests import Session
from requests.exceptions import HTTPError

from alpaca import __version__
from alpaca.common.exceptions import APIError, RetryException
from alpaca.common.types import RawData
from alpaca.common.utils import get_api_version, get_credentials
from .enums import BaseURL

# TODO: Refine this type
HTTPResult = Union[dict, List[dict], Any]


class RESTClient(ABC):
    """Abstract base class for REST clients"""

    def __init__(
        self,
        base_url: Union[BaseURL, str],
        api_key: str = None,
        secret_key: str = None,
        api_version: str = "v2",
        sandbox: bool = False,
        raw_data: bool = False,
    ) -> None:
        """Abstract base class for REST clients. Handles submitting HTTP requests to
        Alpaca API endpoints.

        Args:
            base_url (Union[BaseURL, str]): The base url to target requests to. Should be an instance of BaseURL, but
              allows for raw str if you need to override
            api_key (str, optional): description. Defaults to None.
            secret_key (str, optional): description. Defaults to None.
            api_version (str, optional): description. Defaults to 'v2'.
            sandbox (bool, optional): description. Defaults to False.
            raw_data (bool, optional): description. Defaults to False.
        """

        self._api_key, self._secret_key = get_credentials(api_key, secret_key)
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
        data: Optional[Union[dict, str]] = None,
        base_url: Optional[Union[BaseURL, str]] = None,
        api_version: Optional[str] = None,
    ) -> dict:
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
            dict: The response from the API
        """
        base_url = base_url or self._base_url
        version = api_version if api_version else self._api_version
        url: str = base_url + "/" + version + path

        headers = self._get_auth_headers()

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

    def _get_auth_headers(self) -> dict:
        """
        Get the auth headers for a request. Meant to be overridden in clients that don't use this format for requests,
        ie: BrokerClient

        Returns:
            dict: A dict containing the expected auth headers
        """

        return {
            "APCA-API-KEY-ID": self._api_key,
            "APCA-API-SECRET-KEY": self._secret_key,
        }

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
            else:
                raise http_error

        if resp.text != "":
            return resp.json()

    def get(self, path: str, data: Union[dict, str] = None, **kwargs) -> HTTPResult:
        """Performs a single GET request

        Args:
            path (str): The API endpoint path
            data (Union[dict, str], optional): Query parameters to send, either
            as a str urlencoded, or a dict of values to be converted. Defaults to None.

        Returns:
            dict: The response
        """
        return self._request("GET", path, data, **kwargs)

    def post(self, path: str, data: Union[dict, str] = None) -> dict:
        """Performs a single POST request

        Args:
            path (str): The API endpoint path
            data (Union[dict, str], optional): The json payload if str, or a dict of values to be converted.
             Defaults to None.

        Returns:
            dict: The response
        """
        return self._request("POST", path, data)

    def put(self, path: str, data: Union[dict, str] = None) -> dict:
        """Performs a single PUT request

        Args:
            path (str): The API endpoint path
            data (Union[dict, str], optional): The json payload if str, or a dict of values to be converted.
             Defaults to None.

        Returns:
            dict: The response
        """
        return self._request("PUT", path, data)

    def patch(self, path: str, data: Union[dict, str] = None) -> dict:
        """Performs a single PATCH request

        Args:
            path (str): The API endpoint path
            data (Union[dict, str], optional): The json payload if str, or a dict of values to be converted.
             Defaults to None.

        Returns:
            dict: The response
        """
        return self._request("PATCH", path, data)

    def delete(self, path, data: Union[dict, str] = None) -> dict:
        """Performs a single DELETE request

        Args:
            path (str): The API endpoint path
            data (Union[dict, str], optional): The payload if any. Defaults to None.

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
