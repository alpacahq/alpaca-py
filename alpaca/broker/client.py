import os
from typing import Optional

from ..common.enums import BaseURL
from ..common.rest import RESTClient
from .models import Account, AccountCreationRequest


class BrokerClient(RESTClient):
    """
    Client for accessing Broker API services
    """

    def __init__(self, 
                api_key: Optional[str] = None, 
                secret_key: Optional[str] = None, 
                api_version: str = 'v1',
                sandbox: bool = True, 
                raw_data: bool = False,
                ):
        """
        :param api_key: Broker API key - set sandbox to true if using sandbox keys
        :type api_key: str
        :param secret_key: Broker API secret key - set sandbox to true if using sandbox keys
        :type secret_key: str
        :param sandbox: True if using sandbox mode
        :type sandbox: bool
        :param raw_data: True if you want raw response instead of wrapped responses
        :type raw_data: bool
        """
        base_url: BaseURL = BaseURL.BROKER_SANDBOX if sandbox else BaseURL.BROKER_PRODUCTION
        super().__init__(api_key, secret_key, api_version, base_url, sandbox, raw_data)
        self._retry = int(os.environ.get('APCA_RETRY_MAX', 3))
        self._retry_wait = int(os.environ.get('APCA_RETRY_WAIT', 3))
        self._retry_codes = [int(o) for o in os.environ.get(
            'APCA_RETRY_CODES', '429,504').split(',')]

    def create_account(self, account: AccountCreationRequest) -> Account:

        data = account.json()
        response = self.post('/accounts', data)
        account = Account(**response)
        return response

    def get_account_details(self) -> Account:
        pass

    def update_account(self) -> Account:
        pass

    def delete_account(self) -> Account:
        pass



