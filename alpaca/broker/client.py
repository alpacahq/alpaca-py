import os
from typing import Optional, Union
from uuid import UUID

from ..common.enums import BaseURL
from ..common.rest import RESTClient
from .models import Account, AccountCreationRequest


class BrokerClient(RESTClient):
    """
    Client for accessing Broker API services
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        api_version: str = "v1",
        sandbox: bool = True,
        raw_data: bool = False,
    ):
        """
        Args:
            api_key (Optional[str], optional): Broker API key - set sandbox to true if using sandbox keys. Defaults to None.
            secret_key (Optional[str], optional): Broker API secret key - set sandbox to true if using sandbox keys. Defaults to None.
            api_version (str, optional): API version. Defaults to 'v1'.
            sandbox (bool, optional): True if using sandbox mode. Defaults to True.
            raw_data (bool, optional): True if you want raw response instead of wrapped responses. Defaults to False.
        """
        base_url: BaseURL = (
            BaseURL.BROKER_SANDBOX if sandbox else BaseURL.BROKER_PRODUCTION
        )
        super().__init__(api_key, secret_key, api_version, base_url, sandbox, raw_data)
        self._retry = int(os.environ.get("APCA_RETRY_MAX", 3))
        self._retry_wait = int(os.environ.get("APCA_RETRY_WAIT", 3))
        self._retry_codes = [
            int(o) for o in os.environ.get("APCA_RETRY_CODES", "429,504").split(",")
        ]

    def create_account(self, account_data: AccountCreationRequest) -> Account:
        """
        Create an account.

        Args:
            account_data(AccountCreationRequest): The data representing the Account you wish to create

        Returns:

        """

        data = account_data.json()
        response = self.post("/accounts", data)

        return Account(**response)

    def get_account_by_id(self, account_id: Union[UUID, str]) -> Account:
        """
        Get an Account by its associated account_id.

        Note: If no account is found the api returns a 401, not a 404

        Args:
            account_id(Union[UUID,str]): The id of the account you wish to get

        Returns:
            Account: Returns the requested account.
        """

        # should raise ValueError
        if type(account_id) == str:
            account_id = UUID(account_id)
        elif type(account_id) != UUID:
            raise ValueError("account_id must be a UUID or a UUID str")

        resp = self.get(f"/accounts/{account_id}")
        return Account(**resp)

    def get_account_details(self) -> Account:
        pass

    def update_account(self) -> Account:
        pass

    def delete_account(self) -> Account:
        pass
