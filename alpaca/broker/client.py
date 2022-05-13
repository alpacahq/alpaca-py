from itertools import chain
from typing import Callable, Iterator, List, Optional, Union
from uuid import UUID

from pydantic import parse_obj_as
from requests import HTTPError, Response

from .enums import ACHRelationshipStatus
from .constants import BROKER_DOCUMENT_UPLOAD_LIMIT
from .models import (
    Account,
    AccountCreationRequest,
    AccountUpdateRequest,
    ActivityType,
    CIPInfo,
    GetAccountActivitiesRequest,
    GetTradeDocumentsRequest,
    ListAccountsRequest,
    TradeAccount,
    TradeDocument,
    UploadDocumentRequest,
    ACHRelationship,
    CreateACHRelationshipRequest,
    CreatePlaidRelationshipRequest,
    CreateBankRequest,
    Bank,
    Transfer,
    CreateACHTransferRequest,
    CreateBankTransferRequest,
    GetTransfersRequest,
)
from ..common import APIError
from ..common.constants import ACCOUNT_ACTIVITIES_DEFAULT_PAGE_SIZE
from ..common.enums import BaseURL, PaginationType
from ..common.models import BaseActivity, NonTradeActivity, TradeActivity
from ..common.rest import HTTPResult, RESTClient

import base64


def validate_uuid_id_param(
    account_id: Union[UUID, str],
    var_name: Optional[str] = None,
) -> UUID:
    """
    A small helper function to eliminate duplicate checks of various id parameters to ensure they are
    valid UUIDs. Upcasts str instances that are valid UUIDs into UUID instances.

    Args:
        account_id (Union[UUID, str]): The parameter to be validated
        var_name (Optional[str]): the name of the parameter you'd like to generate in the error message. Defaults to
          using `account_id` due to it being the most commonly needed case

    Returns:
        UUID: The valid UUID instance
    """

    if var_name is None:
        var_name = "account_id"

    # should raise ValueError
    if type(account_id) == str:
        account_id = UUID(account_id)
    elif type(account_id) != UUID:
        raise ValueError(f"{var_name} must be a UUID or a UUID str")

    return account_id


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
        url_override: Optional[str] = None,
    ):
        """
        Args:
            api_key (Optional[str]): Broker API key - set sandbox to true if using sandbox keys. Defaults to None.
            secret_key (Optional[str]): Broker API secret key - set sandbox to true if using sandbox keys. Defaults to None.
            api_version (str): API version. Defaults to 'v1'.
            sandbox (bool): True if using sandbox mode. Defaults to True.
            raw_data (bool): True if you want raw response instead of wrapped responses. Defaults to False.
            url_override (Optional[str]): A url to override and use as the base url.
        """
        base_url = (
            url_override
            if url_override is not None
            else BaseURL.BROKER_SANDBOX
            if sandbox
            else BaseURL.BROKER_PRODUCTION
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

    def _get_auth_headers(self) -> dict:
        # We override this since we use Basic auth
        auth_string = f"{self._api_key}:{self._secret_key}"
        auth_string_encoded = base64.b64encode(str.encode(auth_string))

        return {"Authorization": "Basic " + auth_string_encoded.decode("utf-8")}

    # ############################## ACCOUNTS/TRADING ACCOUNTS ################################# #

    def create_account(
        self,
        account_data: AccountCreationRequest,
    ) -> Account:
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

    def get_account_by_id(
        self,
        account_id: Union[UUID, str],
    ) -> Account:
        """
        Get an Account by its associated account_id.

        Note: If no account is found the api returns a 401, not a 404

        Args:
            account_id (Union[UUID, str]): The id of the account you wish to get. str uuid values will be upcast
            into UUID instances

        Returns:
            Account: Returns the requested account.
        """

        account_id = validate_uuid_id_param(account_id)

        resp = self.get(f"/accounts/{account_id}")
        return Account(**resp)

    def update_account(
        self,
        account_id: Union[UUID, str],
        update_data: AccountUpdateRequest,
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
        account_id = validate_uuid_id_param(account_id)
        params = update_data.to_request_fields()

        if len(params) < 1:
            raise ValueError("update_data must contain at least 1 field to change")

        response = self.patch(f"/accounts/{account_id}", params)

        return Account(**response)

    def delete_account(
        self,
        account_id: Union[UUID, str],
    ) -> None:
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

        account_id = validate_uuid_id_param(account_id)

        self.delete(f"/accounts/{account_id}")

    def list_accounts(
        self,
        search_parameters: Optional[ListAccountsRequest] = None,
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

    def get_trade_account_by_id(
        self,
        account_id: Union[UUID, str],
    ) -> TradeAccount:
        """
        Gets TradeAccount information for a given Account id.

        Args:
            account_id (Union[UUID, str]): The UUID identifier for the Account you wish to get the info for. str values
              will be upcast into UUID instances and checked for validity.

        Returns:
            TradeAccount: TradeAccount info for the given account if found.
        """

        account_id = validate_uuid_id_param(account_id)

        result = self.get(f"/trading/accounts/{account_id}/account")

        return TradeAccount(**result)

    def upload_documents_to_account(
        self,
        account_id: Union[UUID, str],
        document_data: List[UploadDocumentRequest],
    ) -> None:
        """
        Allows you to upload up to 10 documents at a time for an Account.

        Document data must be a binary objects whose contents are encoded in base64. Each encoded content size is
        limited to 10MB if you use Alpaca for KYCaaS.

        If you perform your own KYC there are no document size limitations.

        Args:
            account_id (Union[UUID, str]): The id of the Account you wish to upload the document data to.
            document_data (List[UploadDocumentRequest]): List of UploadDocumentRequest's that contain the relevant
              Document data

        Returns:
            None: This function returns nothing on success and will raise an APIError in case of a failure

        Raises:
            APIError: this will be raised if the API didn't return a 204 for your request.
        """

        account_id = validate_uuid_id_param(account_id)

        if len(document_data) > BROKER_DOCUMENT_UPLOAD_LIMIT:
            raise ValueError(
                f"document_data cannot be longer than {BROKER_DOCUMENT_UPLOAD_LIMIT}"
            )

        self.post(
            f"/accounts/{account_id}/documents/upload",
            [document.to_request_fields() for document in document_data],
        )

    def get_cip_data_for_account_by_id(
        self,
        account_id: Union[UUID, str],
    ) -> None:
        """
        Get CIP Info for an account.

        Args:
            account_id (Union[UUID, str]): The Account id you wish to retrieve CIPInfo for

        Returns:
            CIPInfo: The CIP info for the Account
        """
        account_id = validate_uuid_id_param(account_id)
        # TODO: can't verify the CIP routes in sandbox they always return 404.
        #  Need to ask broker team how we'll even test this
        pass

    def upload_cip_data_for_account_by_id(
        self,
        account_id: Union[UUID, str],
    ):
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
        handle_pagination = BrokerClient._validate_pagination(
            max_items_limit, handle_pagination
        )

        # otherwise, user wants pagination so we grab an interator
        iterator = self._get_account_activities_iterator(
            activity_filter=activity_filter,
            max_items_limit=max_items_limit,
            mapping=lambda raw_activities: [
                self._parse_activity(activity) for activity in raw_activities
            ],
        )

        return BrokerClient._return_paginated_result(iterator, handle_pagination)

    def _get_account_activities_iterator(
        self,
        activity_filter: GetAccountActivitiesRequest,
        max_items_limit: Optional[int],
        mapping: Callable[[HTTPResult], List[BaseActivity]],
    ) -> Iterator[List[BaseActivity]]:
        """
        Private method for handling the iterator parts of get_account_activities
        """

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

    # ############################## TRADE ACCOUNT DOCUMENTS ################################# #

    def get_trade_documents_for_account(
        self,
        account_id: Union[UUID, str],
        documents_filter: Optional[GetTradeDocumentsRequest] = None,
    ) -> List[TradeDocument]:
        """
        Gets the list of TradeDocuments for an Account.

        Args:
            account_id (Union[UUID, str]): The id of the Account you wish to retrieve documents for. str values will
              attempt to be upcast into UUID instances
            documents_filter (GetTradeDocumentsRequest): The optional set of filters you can apply to filter the
              returned list.

        Returns:
            List[TradeDocument]: The filtered list of TradeDocuments
        """
        account_id = validate_uuid_id_param(account_id)

        result = self.get(
            f"/accounts/{account_id}/documents",
            documents_filter.to_request_fields() if documents_filter else {},
        )

        return parse_obj_as(List[TradeDocument], result)

    def get_trade_document_for_account_by_id(
        self,
        account_id: Union[UUID, str],
        document_id: Union[UUID, str],
    ) -> TradeDocument:
        """
        Gets a single TradeDocument by its id

        Args:
            account_id (Union[UUID, str]): The id of the Account that owns the document
            document_id (Union[UUID, str]): The id of the TradeDocument

        Returns:
            TradeDocument: The requested TradeDocument
        Raises:
            APIError: Will raise an APIError if the account_id or a matching document_id for the account are not found.
        """

        account_id = validate_uuid_id_param(account_id)
        document_id = validate_uuid_id_param(document_id, "document_id")

        response = self.get(f"/accounts/{account_id}/documents/{document_id}")

        return parse_obj_as(TradeDocument, response)

    def download_trade_document_for_account_by_id(
        self,
        account_id: Union[UUID, str],
        document_id: Union[UUID, str],
        file_name: str,
    ) -> None:

        account_id = validate_uuid_id_param(account_id)
        document_id = validate_uuid_id_param(document_id, "document_id")
        response: Optional[Response] = None

        # self.get/post/etc all set follow redirects to false, however API will return a 301 redirect we need to follow,
        # so we just do a raw request

        target_url = f"{self._base_url}/{self._api_version}/accounts/{account_id}/documents/{document_id}/download"
        num_tries = 0

        while num_tries <= self._retry:
            response = self._session.get(
                url=target_url,
                headers=self._get_default_headers(),
                allow_redirects=True,
                stream=True,
            )
            num_tries += 1

            try:
                response.raise_for_status()
            except HTTPError as http_error:
                if response.status_code in self._retry_codes:
                    continue
                if "code" in response.text:
                    error = response.json()
                    if "code" in error:
                        raise APIError(error, http_error)
                else:
                    raise http_error

            # if we got here there were no issues response is now a value
            break

        if response is None:
            # we got here either by error or someone has configured us, so we didn't even try
            raise Exception("Somehow we never made a request for download!")

        with open(file_name, "wb") as f:
            # we specify chunk_size none which is okay since we set stream to true above, so chunks will be as we
            # receive them from the api
            for chunk in response.iter_content(chunk_size=None):
                f.write(chunk)

    # ############################## FUNDING ################################# #

    def create_ach_relationship_for_account(
        self,
        account_id: Union[UUID, str],
        ach_data: Union[CreateACHRelationshipRequest, CreatePlaidRelationshipRequest],
    ) -> ACHRelationship:
        """
        Creates a single ACH relationship for the given account.

        Args:
            account_id (Union[UUID, str]): The ID of the Account that has the ACH Relationship.
            ach_data (Union[CreateACHRelationshipRequest, CreatePlaidRelationshipRequest]): The request data used to
              create the ACH relationship.

        Returns:
            ACHRelationship: The ACH relationship that was created.
        """
        account_id = validate_uuid_id_param(account_id)

        if not isinstance(
            ach_data, (CreateACHRelationshipRequest, CreatePlaidRelationshipRequest)
        ):
            raise ValueError(
                f"Request data must either be a CreateACHRelationshipRequest instance, or a "
                f"CreatePlaidRelationshipRequest instance. Got unsupported {type(ach_data)} instead."
            )

        response = self.post(
            f"/accounts/{account_id}/ach_relationships", ach_data.to_request_fields()
        )
        return ACHRelationship(**response)

    def get_ach_relationships_for_account(
        self,
        account_id: Union[UUID, str],
        statuses: Optional[List[ACHRelationshipStatus]] = None,
    ) -> List[ACHRelationship]:
        """
        Gets the ACH relationships for an account.

        Args:
            account_id (Union[UUID, str]): The ID of the Account to get the ACH relationships for.
            statuses (Optional[List[ACHRelationshipStatus]]): Optionally filter a subset of ACH relationship statuses.

        Returns:
            List[ACHRelationship]: List of ACH relationships returned by the query.
        """
        account_id = validate_uuid_id_param(account_id)

        params = {}
        if statuses is not None and len(statuses) != 0:
            params["statuses"] = ",".join(statuses)

        response = self.get(f"/accounts/{account_id}/ach_relationships", params)
        return parse_obj_as(List[ACHRelationship], response)

    def delete_ach_relationship_for_account(
        self,
        account_id: Union[UUID, str],
        ach_relationship_id: Union[UUID, str],
    ) -> None:
        """
        Delete an ACH Relation by its ID.

        As the api itself returns a 204 on success this function returns nothing in the successful case and will raise
        an exception in any other case.

        Args:
            account_id (Union[UUID, str]): The ID of the Account which has the ACH relationship to be deleted.
            ach_relationship_id (Union[UUID, str]): The ID of the ACH relationship to delete.
        """
        account_id = validate_uuid_id_param(account_id)
        ach_relationship_id = validate_uuid_id_param(
            ach_relationship_id, "ach_relationship_id"
        )
        self.delete(f"/accounts/{account_id}/ach_relationships/{ach_relationship_id}")

    def create_bank_for_account(
        self,
        account_id: Union[UUID, str],
        bank_data: CreateBankRequest,
    ) -> Bank:
        """
        Creates a single ACH relationship for the given account.

        Args:
            account_id (Union[UUID, str]): The ID of the Account to create the bank connection for.
            bank_data (CreateBankRequest): The request data used to create the bank connection.

        Returns:
            Bank: The Bank that was created.
        """
        account_id = validate_uuid_id_param(account_id)
        response = self.post(
            f"/accounts/{account_id}/recipient_banks", bank_data.to_request_fields()
        )
        return Bank(**response)

    def get_banks_for_account(
        self,
        account_id: Union[UUID, str],
    ) -> List[Bank]:
        """
        Gets the Banks for an account.

        Args:
            account_id (Union[UUID, str]): The ID of the Account to get the Banks for.

        Returns:
            List[Bank]: List of Banks returned by the query.
        """
        account_id = validate_uuid_id_param(account_id)
        response = self.get(f"/accounts/{account_id}/recipient_banks")
        return parse_obj_as(List[Bank], response)

    def delete_bank_for_account(
        self,
        account_id: Union[UUID, str],
        bank_id: Union[UUID, str],
    ) -> None:
        """
        Delete a Bank by its ID.

        As the api itself returns a 204 on success this function returns nothing in the successful case and will raise
        an exception in any other case.

        Args:
            account_id (Union[UUID, str]): The ID of the Account which has the Bank to be deleted.
            bank_id (Union[UUID, str]): The ID of the Bank to delete.
        """
        account_id = validate_uuid_id_param(account_id)
        bank_id = validate_uuid_id_param(bank_id, "bank_id")
        self.delete(f"/accounts/{account_id}/recipient_banks/{bank_id}")

    def create_transfer_for_account(
        self,
        account_id: Union[UUID, str],
        transfer_data: Union[CreateACHTransferRequest, CreateBankTransferRequest],
    ) -> Transfer:
        """
        Creates a single Transfer for the given account.

        Args:
            account_id (Union[UUID, str]): The ID of the Account to create the bank connection for.
            transfer_data (Union[CreateACHTransferRequest, CreateBankTransferRequest]): The request data used to
              create the bank connection.

        Returns:
            Transfer: The Transfer that was created.
        """
        account_id = validate_uuid_id_param(account_id)
        response = self.post(
            f"/accounts/{account_id}/transfers", transfer_data.to_request_fields()
        )
        return Transfer(**response)

    def get_transfers_for_account(
        self,
        account_id: Union[UUID, str],
        transfers_filter: Optional[GetTransfersRequest] = None,
        max_items_limit: Optional[int] = None,
        handle_pagination: Optional[PaginationType] = None,
    ) -> Union[List[Transfer], Iterator[List[Transfer]]]:
        """
        Gets the transfers for an account.

        Args:
            account_id (Union[UUID, str]): The ID of the Account to create the bank connection for.
            transfers_filter (Optional[GetTransferRequest]): The various filtering parameters to apply to the request.
            max_items_limit (Optional[int]): A maximum number of items to return over all for when handle_pagination is
              of type `PaginationType.FULL`. Ignored otherwise.
            handle_pagination (Optional[PaginationType]): What kind of pagination you want. If None then defaults to
              `PaginationType.FULL`.

        Returns:
            Union[List[Transfer], Iterator[List[Transfer]]]: Either a list or an Iterator of lists of Transfer child
              classes.
        """
        account_id = validate_uuid_id_param(account_id)
        handle_pagination = BrokerClient._validate_pagination(
            max_items_limit, handle_pagination
        )

        iterator = self._get_transfers_iterator(
            account_id=account_id,
            transfers_filter=transfers_filter
            if transfers_filter is not None
            else GetTransfersRequest(),
            max_items_limit=max_items_limit,
        )

        return BrokerClient._return_paginated_result(iterator, handle_pagination)

    def _get_transfers_iterator(
        self,
        account_id: UUID,
        transfers_filter: GetTransfersRequest,
        max_items_limit: Optional[int],
    ) -> Iterator[List[Transfer]]:
        """
        Private method for handling the iterator parts of get_transfers_for_account.
        """
        # We need to track total items retrieved.
        total_items = 0
        request_fields = transfers_filter.to_request_fields()

        while True:
            request_fields["offset"] = total_items
            result = self.get(f"/accounts/{account_id}/transfers", request_fields)

            # The api returns [] when it's done.
            if not isinstance(result, List) or len(result) == 0:
                break

            num_items_returned = len(result)

            if (
                max_items_limit is not None
                and num_items_returned + total_items > max_items_limit
            ):
                result = result[: (max_items_limit - total_items)]
                total_items += max_items_limit - total_items
            else:
                total_items += num_items_returned

            yield parse_obj_as(List[Transfer], result)

            if max_items_limit is not None and total_items >= max_items_limit:
                break

    def cancel_transfer_for_account(
        self,
        account_id: Union[UUID, str],
        transfer_id: Union[UUID, str],
    ) -> None:
        """
        Cancel a Transfer by its ID.

        As the api itself returns a 204 on success this function returns nothing in the successful case and will raise
        an exception in any other case.

        Args:
            account_id (Union[UUID, str]): The ID of the Account which has the Transfer to be canceled.
            transfer_id (Union[UUID, str]): The ID of the Transfer to cancel.
        """
        account_id = validate_uuid_id_param(account_id)
        transfer_id = validate_uuid_id_param(transfer_id, "transfer_id")
        self.delete(f"/accounts/{account_id}/transfers/{transfer_id}")
