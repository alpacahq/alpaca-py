from typing import List, Optional, Union
from uuid import UUID
from pydantic import parse_obj_as

from ..common.enums import BaseURL
from ..common.rest import RESTClient
from .models import (
    Account,
    AccountCreationRequest,
    AccountUpdateRequest,
    ListAccountsRequest,
)


def validate_account_id_param(account_id: Union[UUID, str]) -> UUID:
    """
    A small helper function to eliminate duplicate checks of account_id parameters to ensure they are
    valid UUIDs

    Args:
        account_id (Union[UUID, str]): The parameter to be validated

    Returns:
        UUID: The valid UUID instance
    """
    # should raise ValueError
    if type(account_id) == str:
        account_id = UUID(account_id)
    elif type(account_id) != UUID:
        raise ValueError("account_id must be a UUID or a UUID str")

    return account_id


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

        # TODO: Actually check raw_data everywhere
        super().__init__(api_key, secret_key, api_version, base_url, sandbox, raw_data)

    def create_account(self, account_data: AccountCreationRequest) -> Account:
        """
        Create an account.

        Args:
            account_data(AccountCreationRequest): The data representing the Account you wish to create

        Returns:
            Account: The newly created Account instance as returned from the API. Should now have id
            and other generated fields filled out.
        """

        data = account_data.json()
        response = self.post("/accounts", data)

        return Account(**response)

    def get_account_by_id(self, account_id: Union[UUID, str]) -> Account:
        """
        Get an Account by its associated account_id.

        Note: If no account is found the api returns a 401, not a 404

        Args:
            account_id(Union[UUID,str]): The id of the account you wish to get. str uuid values will be upcast
            into UUID instances

        Returns:
            Account: Returns the requested account.
        """

        account_id = validate_account_id_param(account_id)

        resp = self.get(f"/accounts/{account_id}")
        return Account(**resp)

    def update_account(
        self, account_id: Union[UUID, str], update_data: AccountUpdateRequest
    ) -> Account:
        """
        Updates data for an account with an id of `account_id`. Note that not all data for an account is modifiable
        after creation so there is a special data type of AccountUpdateRequest representing the data that is
        allowed to be modified.

        see: https://alpaca.markets/docs/api-references/broker-api/accounts/accounts/#updating-an-account for more info

        Args:
            account_id (Union[UUID, str]): The id for the account you with to update. str uuid values will be upcast
            into UUID instances
            update_data (AccountUpdateRequest): The data you wish to update this account to

        Returns:
            Account: Returns an Account instance with the updated data as returned from the api
        """
        account_id = validate_account_id_param(account_id)
        params = update_data.to_request_fields()

        if len(params) < 1:
            raise ValueError("update_data must contain at least 1 field to change")

        response = self.patch(f"/accounts/{account_id}", params)

        return Account(**response)

    def delete_account(self, account_id: Union[UUID, str]) -> None:
        """
        Delete an Account by its id.

        As the api itself returns a 204 on success this function returns nothing in the successful case and will raise
        and exception in any other case.

        Args:
            account_id (Union[UUID, str]): the id of the Account you wish to delete. str values will attempt to be
            upcast to UUID to validate.

        Returns:
            None:
        """

        account_id = validate_account_id_param(account_id)

        self.delete(f"/accounts/{account_id}")

    def list_accounts(
        self, search_parameters: Optional[ListAccountsRequest] = None
    ) -> List[Account]:
        # this is a get request, so we're safe not checking to see if we specified at least one param
        params = search_parameters.dict() if search_parameters is not None else {}

        # API expects comma separated for entities not multiple params
        if "entities" in params and params["entities"] is not None:
            params["entities"] = ",".join(params["entities"])

        response = self.get(
            f"/accounts",
            params,
        )

        return parse_obj_as(List[Account], response)
