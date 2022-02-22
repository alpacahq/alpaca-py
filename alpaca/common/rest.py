import base64
import os
import time
from abc import ABC
from typing import Optional, Union

from pydantic import BaseModel
from requests import Session
from requests.exceptions import HTTPError

from alpaca.common.exceptions import APIError, RetryException
from alpaca.common.utils import get_api_version, get_credentials

from .enums import BaseURL


class RESTClient(ABC):
    """Abstract base class for REST clients
    """

    def __init__(self, 
                api_key: str = None, 
                secret_key: str = None, 
                api_version: str = 'v2',
                base_url: Optional[BaseURL] = None,
                sandbox: bool = False, 
                raw_data: bool = False
                ):
        """Abstract base class for REST clients

        Args:
            api_key (str, optional): _description_. Defaults to None.
            secret_key (str, optional): _description_. Defaults to None.
            api_version (str, optional): _description_. Defaults to 'v2'.
            base_url (Optional[BaseURL], optional): _description_. Defaults to None.
            sandbox (bool, optional): _description_. Defaults to False.
            raw_data (bool, optional): _description_. Defaults to False.
        """

        self._api_key, self. _secret_key = get_credentials(api_key, secret_key)
        self._api_version: str = get_api_version(api_version)
        self._base_url: BaseURL = base_url
        self._sandbox: bool = sandbox
        self._use_raw_data: bool = raw_data
        self._session: Session = Session()
        self._retry = int(os.environ.get('APCA_RETRY_MAX', 3))
        self._retry_wait = int(os.environ.get('APCA_RETRY_WAIT', 3))
        self._retry_codes = [int(o) for o in os.environ.get(
            'APCA_RETRY_CODES', '429,504').split(',')]

    def _request(self,
                 method,
                 path,
                 data=None,
                 base_url: BaseURL = None,
                 api_version: str = None):
        base_url = base_url or self._base_url
        version = api_version if api_version else self._api_version
        url: str = base_url.value + '/' + version + path
        headers = {}

        if self._base_url == BaseURL.BROKER_PRODUCTION or self._base_url == BaseURL.BROKER_SANDBOX:
            auth_string = f'{self._api_key}:{self._secret_key}'
            auth_string_encoded = base64.b64encode(str.encode(auth_string))
            headers['Authorization'] = 'Basic ' + auth_string_encoded.decode('utf-8')
        else:
            headers['APCA-API-KEY-ID'] = self._api_key
            headers['APCA-API-SECRET-KEY'] = self._secret_key

        opts = {
            'headers': headers,
        }

        if method.upper() in ['GET', 'DELETE']:
            opts['params'] = data
        else:
            opts['json'] = data
    

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

    def _one_request(self, method: str, url: str, opts: dict, retry: int):
        """Perform one request, possibly raising RetryException in the case
        the response is 429 or 504.
        """
        retry_codes = self._retry_codes
        resp = self._session.request(method, url, **opts)
        
        try:
            resp.raise_for_status()
        except HTTPError as http_error:
             # retry if we hit Rate Limit
            if resp.status_code in retry_codes and retry > 0:
                raise RetryException()
            if 'code' in resp.text:
                error = resp.json()
                if 'code' in error:
                    raise APIError(error, http_error)
        
        if resp.text != '':
            return resp.json()


    def get(self, path, data=None):
        return self._request('GET', path, data)

    def post(self, path, data=None):
        return self._request('POST', path, data)

    def put(self, path, data=None):
        return self._request('PUT', path, data)

    def patch(self, path, data=None):
        return self._request('PATCH', path, data)

    def delete(self, path, data=None):
        return self._request('DELETE', path, data)

    def response_wrapper(self, obj: dict, entity: BaseModel) -> Union[dict, BaseModel]:
        """To allow the user to get raw response from the api, we wrap all
        functions with this method, checking if the user has set raw_data
        bool. if they didn't, we wrap the response with an Entity object.

        Args:
            obj (Any): response from server
            model (BaseModel): derivative object of Entity

        Returns:
            Union[dict, BaseModel]: either raw or parsed data
        """
        if self._use_raw_data:
            return obj
        else:
            return entity(**obj)