from enum import Enum
from typing import Callable, Iterator, List, Optional, TypeVar, Union
from uuid import UUID
from pydantic import parse_obj_as
from itertools import chain

from .constants import ACCOUNT_ACTIVITIES_DEFAULT_PAGE_SIZE
from ..common import APIError
from ..common.enums import BaseURL
from ..common.rest import HTTPResult, RESTClient
from .models import (
    Account,
    AccountCreationRequest,
    AccountUpdateRequest,
    CIPInfo,
    ListAccountsRequest,
    TradeAccount,
    BaseActivity,
    GetAccountActivitiesRequest,
    ActivityType,
    NonTradeActivity,
    TradeActivity,
)


def validate_account_id_param(account_id: Union[UUID, str]) -> UUID:
    """
    A small helper function to eliminate duplicate checks of account_id parameters to ensure they are
    valid UUIDs. Upcasts str instances that are valid UUIDs into UUID instances.

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


class PaginationType(Enum):
    """
    An enum for choosing what type of pagination of results you'd like for BrokerClient functions that support
    pagination.

    * NONE: Requests that we perform no pagination of results and just return the single response the API gave us.
    * FULL: Requests that we perform all the pagination and return just a single List/dict/etc containing all the
      results. This is the default for most functions.
    * ITERATOR: Requests that we return an Iterator that yields one "page" of results at a time
    """

    NONE = "none"
    FULL = "full"
    ITERATOR = "iterator"


class BrokerClient(RESTClient):
    """
    Client for accessing Broker API services

    **Note on the `handle_pagination` param you'll see across these methods**

    By default, these methods will attempt to handle the fact that the API paginates results for the specific endpoint
    for you by returning it all as one List.

    However, that could:

    1. Take a long time if there are many results to paginate or if you request a small page size and have moderate
    network latency
    2. Use up a large amount of memory to build all the results at once

    So for those cases where a single list all at once would be prohibitive you can specify what kind of pagination you
    want with the `handle_pagination` parameter. Please see the PaginationType enum for an explanation as to what the
    different values mean for what you get back.
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
        super().__init__(
            base_url=base_url,
            api_key=api_key,
            secret_key=secret_key,
            api_version=api_version,
            sandbox=sandbox,
            raw_data=raw_data,
        )

    # ############################## ACCOUNTS/TRADING ACCOUNTS ################################# #

    def create_account(self, account_data: AccountCreationRequest) -> Account:
        """
        Create an account.

        Args:
            account_data (AccountCreationRequest): The data representing the Account you wish to create

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
            account_id (Union[UUID, str]): The id of the account you wish to get. str uuid values will be upcast
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
        """
        Get a List of Accounts allowing for passing in some filters.

        Args:
            search_parameters (Optional[ListAccountsRequest]): The various filtering criteria you can specify.

        Returns:
            List[Account]: The filtered list of Accounts
        """

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

    def get_trade_account_by_id(self, account_id: Union[UUID, str]) -> TradeAccount:
        """
        Gets TradeAccount information for a given Account id.

        Args:
            account_id (Union[UUID, str]): The UUID identifier for the Account you wish to get the info for. str values
              will be upcast into UUID instances and checked for validity.

        Returns:
            TradeAccount: TradeAccount info for the given account if found.
        """

        account_id = validate_account_id_param(account_id)

        result = self.get(f"/trading/accounts/{account_id}/account")

        return TradeAccount(**result)

    def get_cip_data_for_account_by_id(self, account_id: Union[UUID, str]) -> None:
        """
        Get CIP Info for an account.

        Args:
            account_id (Union[UUID, str]): The Account id you wish to retrieve CIPInfo for

        Returns:
            CIPInfo: The CIP info for the Account
        """
        account_id = validate_account_id_param(account_id)
        # TODO: can't verify the CIP routes in sandbox they always return 404.
        #  Need to ask broker team how we'll even test this
        pass

    def upload_cip_data_for_account_by_id(self, account_id: Union[UUID, str]):
        # TODO: can't verify the CIP routes in sandbox they always return 404.
        #  Need to ask broker team how we'll even test this
        pass

    # ############################## ACCOUNT ACTIVITIES ################################# #

    def get_account_activities(
        self,
        activity_filter: GetAccountActivitiesRequest,
        max_items_limit: Optional[int] = None,
        handle_pagination: Optional[PaginationType] = None,
    ) -> Union[List[BaseActivity], Iterator[List[BaseActivity]]]:
        """
        Gets a list of Account activities, with various filtering options. Please see the documentation for
        GetAccountActivitiesRequest for more information as to what filters are available.

        The return type of this function is List[BaseActivity] however the list will contain concrete instances of one
        of the child classes of BaseActivity, either TradeActivity or NonTradeActivity. It can be a mixed list depending
        on what filtering criteria you pass through `activity_filter`


        Args:
            activity_filter (GetAccountActivitiesRequest): The various filtering fields you can specify to restrict
              results
            max_items_limit (Optional[int]): A maximum number of items to return over all for when handle_pagination is
              of type `PaginationType.FULL`. Ignored otherwise.
            handle_pagination (Optional[PaginationType]): What kind of pagination you want. If None then defaults to
              `PaginationType.FULL`

        Returns:
            Union[List[BaseActivity], Iterator[List[BaseActivity]]]: Either a list or an Iterator of lists of
              BaseActivity child classes
        """

        if handle_pagination is None:
            handle_pagination = PaginationType.FULL

        if handle_pagination != PaginationType.FULL and max_items_limit is not None:
            raise ValueError(
                "max_items_limit can only be specified for PaginationType.FULL"
            )

        def get_as_iterator(
            mapping: Callable[[HTTPResult], List[BaseActivity]]
        ) -> Iterator[List[BaseActivity]]:
            # we need to track total items retrieved
            total_items = 0
            request_fields = activity_filter.to_request_fields()

            while True:
                """
                we have a couple cases to handle here:
                  - max limit isn't set, so just handle normally
                  - max is set, and page_size isn't
                    - date isn't set. So we'll fall back to the default page size
                    - date is set, in this case the api is allowed to not page and return all results. Need to  make
                      sure only take the we allow for making still a single request here but only taking the items we
                      need, in case user wanted only 1 request to happen.
                  - max is set, and page_size is also set. Keep track of total_items and run a min check every page to
                    see if we need to take less than the page_size items
                """

                if max_items_limit is not None:
                    page_size = (
                        activity_filter.page_size
                        if activity_filter.page_size is not None
                        else ACCOUNT_ACTIVITIES_DEFAULT_PAGE_SIZE
                    )

                    normalized_page_size = min(
                        int(max_items_limit) - total_items, page_size
                    )

                    request_fields["page_size"] = normalized_page_size

                result = self.get("/accounts/activities", request_fields)

                # the api returns [] when it's done

                if not isinstance(result, List) or len(result) == 0:
                    break

                num_items_returned = len(result)

                # need to handle the case where the api won't page and returns all results, ie `date` is set
                if (
                    max_items_limit is not None
                    and num_items_returned + total_items > max_items_limit
                ):
                    result = result[: (max_items_limit - total_items)]

                    total_items += max_items_limit - total_items
                else:
                    total_items += num_items_returned

                yield mapping(result)

                if max_items_limit is not None and total_items >= max_items_limit:
                    break

                # ok we made it to the end, we need to ask for the next page of results
                last_result = result[-1]

                if "id" not in last_result:
                    raise APIError(
                        "AccountActivity didn't contain an `id` field to use for paginating results"
                    )

                # set the pake token to the id of the last activity so we can get the next page
                request_fields["page_token"] = last_result["id"]

        # otherwise, user wants pagination so we grab an interator
        iterator = get_as_iterator(lambda x: [self._parse_activity(x) for x in x])

        if handle_pagination == PaginationType.NONE:
            # user wants no pagination, so just do a single page
            return next(iterator)
        elif handle_pagination == PaginationType.FULL:
            # the iterator returns "pages", so we use chain to flatten them all into 1 list
            return list(chain.from_iterable(iterator))
        elif handle_pagination == PaginationType.ITERATOR:
            return iterator

    # ############################## HELPER/PRIVATE FUNCS ################################# #

    @staticmethod
    def _parse_activity(data: dict) -> Union[TradeActivity, NonTradeActivity]:
        """
        We cannot just use parse_obj_as for Activity types since we need to know what child instance to cast it into.

        So this method does just that.

        Args:
            data (dict): a dict of raw data to attempt to convert into an Activity instance

        Raises:
            ValueError: Will raise a ValueError if `data` doesn't contain an `activity_type` field to compare
        """

        if "activity_type" not in data or data["activity_type"] is None:
            raise ValueError(
                "Failed parsing raw activity data, `activity_type` is not present in fields"
            )

        if ActivityType.is_str_trade_activity(data["activity_type"]):
            return parse_obj_as(TradeActivity, data)
        else:
            return parse_obj_as(NonTradeActivity, data)
