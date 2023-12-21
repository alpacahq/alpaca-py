import base64
from typing import Callable, Iterator, List, Optional, Union, Dict
from uuid import UUID

import sseclient

from pydantic import TypeAdapter
from requests import HTTPError, Response

from .enums import ACHRelationshipStatus
from alpaca.broker.models import (
    ACHRelationship,
    Account,
    Bank,
    CIPInfo,
    TradeAccount,
    TradeDocument,
    Transfer,
    Order,
    BatchJournalResponse,
    Journal,
)
from .requests import (
    CreateJournalRequest,
    CreateBatchJournalRequest,
    CreateReverseBatchJournalRequest,
    GetJournalsRequest,
    OrderRequest,
    CancelOrderResponse,
    UploadDocumentRequest,
    CreateACHRelationshipRequest,
    CreateACHTransferRequest,
    CreateBankRequest,
    CreateBankTransferRequest,
    CreatePlaidRelationshipRequest,
    GetAccountActivitiesRequest,
    GetTradeDocumentsRequest,
    GetTransfersRequest,
    ListAccountsRequest,
    CreateAccountRequest,
    UpdateAccountRequest,
    GetEventsRequest,
)
from alpaca.common.exceptions import APIError
from alpaca.common.constants import (
    ACCOUNT_ACTIVITIES_DEFAULT_PAGE_SIZE,
    BROKER_DOCUMENT_UPLOAD_LIMIT,
)
from alpaca.common.enums import BaseURL, PaginationType
from alpaca.trading.models import (
    PortfolioHistory,
    Position,
    AllAccountsPositions,
    ClosePositionResponse,
    Asset,
    Watchlist,
    Calendar,
    Clock,
    CorporateActionAnnouncement,
    AccountConfiguration as TradeAccountConfiguration,
)
from alpaca.trading.models import (
    BaseActivity,
    NonTradeActivity,
    TradeActivity,
)
from alpaca.trading.requests import (
    GetPortfolioHistoryRequest,
    ClosePositionRequest,
    GetCalendarRequest,
    UpdateWatchlistRequest,
    CreateWatchlistRequest,
    ReplaceOrderRequest,
    GetAssetsRequest,
    GetOrdersRequest,
    GetOrderByIdRequest,
    GetCorporateAnnouncementsRequest,
)
from alpaca.trading.enums import (
    ActivityType,
)
from ..common import RawData
from ..common.rest import HTTPResult, RESTClient
from alpaca.common.utils import validate_uuid_id_param, validate_symbol_or_asset_id


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
                This has not been implemented yet.
            url_override (Optional[str]): A url to override and use as the base url.
        """
        base_url = (
            url_override
            if url_override is not None
            else BaseURL.BROKER_SANDBOX.value
            if sandbox
            else BaseURL.BROKER_PRODUCTION
        )

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
        account_data: CreateAccountRequest,
    ) -> Union[Account, RawData]:
        """
        Create an account.

        Args:
            account_data (CreateAccountRequest): The data representing the Account you wish to create

        Returns:
            Account: The newly created Account instance as returned from the API. Should now have id
            and other generated fields filled out.
        """

        data = account_data.to_request_fields()
        response = self.post("/accounts", data)

        return Account(**response)

    def get_account_by_id(
        self,
        account_id: Union[UUID, str],
    ) -> Union[Account, RawData]:
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

        resp = self.get(f"/accounts/{account_id}", {"params": ""})
        return Account(**resp)

    def update_account(
        self,
        account_id: Union[UUID, str],
        update_data: UpdateAccountRequest,
    ) -> Union[Account, RawData]:
        """
        Updates data for an account with an id of `account_id`. Note that not all data for an account is modifiable
        after creation so there is a special data type of AccountUpdateRequest representing the data that is
        allowed to be modified.

        see: https://alpaca.markets/docs/api-references/broker-api/accounts/accounts/#updating-an-account for more info

        Args:
            account_id (Union[UUID, str]): The id for the account you with to update. str uuid values will be upcast
            into UUID instances
            update_data (UpdateAccountRequest): The data you wish to update this account to

        Returns:
            Account: Returns an Account instance with the updated data as returned from the api
        """
        account_id = validate_uuid_id_param(account_id)
        params = update_data.to_request_fields()

        if len(params) < 1:
            raise ValueError("update_data must contain at least 1 field to change")

        response = self.patch(f"/accounts/{account_id}", params)

        if self._use_raw_data:
            return response

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
    ) -> Union[List[Account], RawData]:
        """
        Get a List of Accounts allowing for passing in some filters.

        Args:
            search_parameters (Optional[ListAccountsRequest]): The various filtering criteria you can specify.

        Returns:
            List[Account]: The filtered list of Accounts
        """

        params = search_parameters.to_request_fields() if search_parameters else {}

        # API expects comma separated for entities not multiple params
        if "entities" in params and params["entities"] is not None:
            params["entities"] = ",".join(params["entities"])

        response = self.get(
            f"/accounts",
            params,
        )

        if self._use_raw_data:
            return response
        return TypeAdapter(List[Account]).validate_python(response)

    def get_trade_account_by_id(
        self,
        account_id: Union[UUID, str],
    ) -> Union[TradeAccount, RawData]:
        """
        Gets TradeAccount information for a given Account id.

        Args:
            account_id (Union[UUID, str]): The UUID identifier for the Account you wish to get the info for. str values
              will be upcast into UUID instances and checked for validity.

        Returns:
            alpaca.broker.models.accounts.TradeAccount: TradeAccount info for the given account if found.
        """

        account_id = validate_uuid_id_param(account_id)

        result = self.get(f"/trading/accounts/{account_id}/account")

        if self._use_raw_data:
            return result

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

    def get_trade_configuration_for_account(
        self,
        account_id: Union[UUID, str],
    ) -> Union[TradeAccountConfiguration, RawData]:
        """
        Gets the TradeAccountConfiguration for a given Account.

        Args:
            account_id (Union[UUID, str]): The id of the Account you wish to get the TradeAccountConfiguration for

        Returns:
            TradeAccountConfiguration: The resulting TradeAccountConfiguration for the Account
        """

        account_id = validate_uuid_id_param(account_id, "account_id")

        resp = self.get(f"/trading/accounts/{account_id}/account/configurations")

        if self._use_raw_data:
            return resp

        return TradeAccountConfiguration(**resp)

    def update_trade_configuration_for_account(
        self,
        account_id: Union[UUID, str],
        config: TradeAccountConfiguration,
    ) -> Union[TradeAccountConfiguration, RawData]:
        """
        Updates an Account with new TradeAccountConfiguration information.

        Args:
            account_id (Union[UUID, str]): The id of the Account you wish to update.
            config (UpdateTradeConfigurationRequest): The Updated Options you wish to set on the Account

        Returns:
            TradeAccountConfiguration: The resulting TradeAccountConfiguration with updates.
        """
        account_id = validate_uuid_id_param(account_id, "account_id")

        result = self.patch(
            f"/trading/accounts/{account_id}/account/configurations",
            config.model_dump_json(),
        )

        if self._use_raw_data:
            return result

        return TradeAccountConfiguration(**result)

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
        mapping: Callable[[HTTPResult], List[BaseActivity]],
        max_items_limit: Optional[int] = None,
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
        We cannot just use TypeAdapter for Activity types since we need to know what child instance to cast it into.

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
            return TypeAdapter(TradeActivity).validate_python(data)
        else:
            return TypeAdapter(NonTradeActivity).validate_python(data)

    # ############################## TRADE ACCOUNT DOCUMENTS ################################# #

    def get_trade_documents_for_account(
        self,
        account_id: Union[UUID, str],
        documents_filter: Optional[GetTradeDocumentsRequest] = None,
    ) -> Union[List[TradeDocument], RawData]:
        """
        Gets the list of TradeDocuments for an Account.

        Args:
            account_id (Union[UUID, str]): The id of the Account you wish to retrieve documents for. str values will
              attempt to be upcast into UUID instances
            documents_filter (Optional[GetTradeDocumentsRequest]): The optional set of filters you can apply to filter the
              returned list.

        Returns:
            List[TradeDocument]: The filtered list of TradeDocuments
        """
        account_id = validate_uuid_id_param(account_id)

        result = self.get(
            f"/accounts/{account_id}/documents",
            documents_filter.to_request_fields() if documents_filter else {},
        )

        if self._use_raw_data:
            return result

        return TypeAdapter(List[TradeDocument]).validate_python(result)

    def get_trade_document_for_account_by_id(
        self,
        account_id: Union[UUID, str],
        document_id: Union[UUID, str],
    ) -> Union[TradeDocument, RawData]:
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

        if self._use_raw_data:
            return response

        return TypeAdapter(TradeDocument).validate_python(response)

    def download_trade_document_for_account_by_id(
        self,
        account_id: Union[UUID, str],
        document_id: Union[UUID, str],
        file_path: str,
    ) -> None:
        """
        Downloads a TradeDocument to `file_path`

        Args:
            account_id (Union[UUID, str]): ID of the account to pull the document from
            document_id (Union[UUID, str]): ID of the document itself
            file_path (str): A full path for where to save the file to

        Returns:
            None:
        """

        account_id = validate_uuid_id_param(account_id)
        document_id = validate_uuid_id_param(document_id, "document_id")
        response: Optional[Response] = None

        # self.get/post/etc all set follow redirects to false, however API will return a 301 redirect we need to follow,
        # so we just do a raw request

        # force base_url to be a string value instead of enum name
        base_url = self._base_url + ""

        target_url = f"{base_url}/{self._api_version}/accounts/{account_id}/documents/{document_id}/download"
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

            # if we got here there were no issues', so response is now a value
            break

        if response is None:
            # we got here either by error or someone has mis-configured us, so we didn't even try
            raise Exception("Somehow we never made a request for download!")

        with open(file_path, "wb") as f:
            # we specify chunk_size none which is okay since we set stream to true above, so chunks will be as we
            # receive them from the api
            for chunk in response.iter_content(chunk_size=None):
                f.write(chunk)

    # ############################## FUNDING ################################# #

    def create_ach_relationship_for_account(
        self,
        account_id: Union[UUID, str],
        ach_data: Union[CreateACHRelationshipRequest, CreatePlaidRelationshipRequest],
    ) -> Union[ACHRelationship, RawData]:
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

        if self._use_raw_data:
            return response

        return ACHRelationship(**response)

    def get_ach_relationships_for_account(
        self,
        account_id: Union[UUID, str],
        statuses: Optional[List[ACHRelationshipStatus]] = None,
    ) -> Union[List[ACHRelationship], RawData]:
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

        if self._use_raw_data:
            return response

        return TypeAdapter(List[ACHRelationship]).validate_python(response)

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
    ) -> Union[Bank, RawData]:
        """
        Creates a single bank relationship for the given account.

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

        if self._use_raw_data:
            return response

        return Bank(**response)

    def get_banks_for_account(
        self,
        account_id: Union[UUID, str],
    ) -> Union[List[Bank], RawData]:
        """
        Gets the Banks for an account.

        Args:
            account_id (Union[UUID, str]): The ID of the Account to get the Banks for.

        Returns:
            List[Bank]: List of Banks returned by the query.
        """
        account_id = validate_uuid_id_param(account_id)
        response = self.get(f"/accounts/{account_id}/recipient_banks")

        if self._use_raw_data:
            return response

        return TypeAdapter(List[Bank]).validate_python(response)

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
    ) -> Union[Transfer, RawData]:
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

        if self._use_raw_data:
            return response

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

            yield TypeAdapter(List[Transfer]).validate_python(result)

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

    # ############################## TRADING ################################# #

    def get_all_positions_for_account(
        self,
        account_id: Union[UUID, str],
    ) -> Union[List[Position], RawData]:
        """
        Gets all the current positions for an account.

        Args:
            account_id (Union[UUID, str]): The ID of the Account to get the open positions for.

        Returns:
            List[Position]: List of open positions from the account.
        """
        account_id = validate_uuid_id_param(account_id)
        response = self.get(f"/trading/accounts/{account_id}/positions")

        if self._use_raw_data:
            return response
        return TypeAdapter(List[Position]).validate_python(response)

    def get_all_accounts_positions(
        self,
    ) -> Union[AllAccountsPositions, RawData]:
        """
        Gets all the current positions for every account in bulk.

        Returns:
            AllAccountsPositions: The collection of open positions keyed by account_id.
        """
        response = self.get("/accounts/positions")

        if self._use_raw_data:
            return response

        return AllAccountsPositions(**response)

    def get_open_position_for_account(
        self, account_id: Union[UUID, str], symbol_or_asset_id: Union[UUID, str]
    ) -> Union[Position, RawData]:
        """
        Gets the open position for an account for a single asset. Throws an APIError if the position does not exist.

        Args:
            account_id (Union[UUID, str]): The ID of the Account to get the open position for.
            symbol_or_asset_id (Union[UUID, str]): The symbol name of asset id of the position to get from the account.

        Returns:
            Position: Open position of the asset from the account.
        """
        account_id = validate_uuid_id_param(account_id)
        symbol_or_asset_id = validate_symbol_or_asset_id(symbol_or_asset_id)
        response = self.get(
            f"/trading/accounts/{account_id}/positions/{symbol_or_asset_id}"
        )

        if self._use_raw_data:
            return response

        return Position(**response)

    def close_all_positions_for_account(
        self,
        account_id: Union[UUID, str],
        cancel_orders: Optional[bool] = None,
    ) -> Union[List[ClosePositionResponse], RawData]:
        """
        Liquidates all positions for an account.

        Places an order for each open position to liquidate.

        Args:
            account_id (Union[UUID, str]): The ID of the Account to close the positions for.
            cancel_orders (Optional[bool]): If true is specified, cancel all open orders before liquidating all positions.

        Returns:
            List[ClosePositionResponse]: A list of responses from each closed position containing the status code and
              order id.
        """
        account_id = validate_uuid_id_param(account_id)
        response = self.delete(
            f"/trading/accounts/{account_id}/positions",
            {"cancel_orders": cancel_orders} if cancel_orders else None,
        )

        if self._use_raw_data:
            return response
        return TypeAdapter(List[ClosePositionResponse]).validate_python(response)

    def close_position_for_account(
        self,
        account_id: Union[UUID, str],
        symbol_or_asset_id: Union[UUID, str],
        close_options: Optional[ClosePositionRequest] = None,
    ) -> Union[Order, RawData]:
        """
        Liquidates the position for an account for a single asset.

        Places a single order to close the position for the asset.

        Args:
            account_id (Union[UUID, str]): The ID of the Account to close the position for.
            symbol_or_asset_id (Union[UUID, str]): The symbol name of asset id of the position to close on the account.
            close_options: The various close position request parameters.

        Returns:
            alpaca.broker.models.Order: The order that was placed to close the position.
        """
        account_id = validate_uuid_id_param(account_id)
        symbol_or_asset_id = validate_symbol_or_asset_id(symbol_or_asset_id)
        response = self.delete(
            f"/trading/accounts/{account_id}/positions/{symbol_or_asset_id}",
            close_options.to_request_fields() if close_options else {},
        )

        if self._use_raw_data:
            return response

        return Order(**response)

    def get_portfolio_history_for_account(
        self,
        account_id: Union[UUID, str],
        history_filter: Optional[GetPortfolioHistoryRequest] = None,
    ) -> Union[PortfolioHistory, RawData]:
        """
        Gets the portfolio history statistics for an account.

        Args:
            account_id (Union[UUID, str]): The ID of the Account to get the portfolio history for.
            history_filter: The various portfolio history request parameters.

        Returns:
            PortfolioHistory: The portfolio history statistics for the account.
        """
        account_id = validate_uuid_id_param(account_id)

        response = self.get(
            f"/trading/accounts/{account_id}/account/portfolio/history",
            history_filter.to_request_fields() if history_filter else {},
        )

        if self._use_raw_data:
            return response

        return PortfolioHistory(**response)

    # ############################## CLOCK & CALENDAR ################################# #

    def get_clock(self) -> Union[Clock, RawData]:
        """
        Gets the current market timestamp, whether or not the market is currently open, as well as the times
        of the next market open and close.

        Returns:
            Clock: The market Clock data
        """

        response = self.get("/clock")

        if self._use_raw_data:
            return response

        return Clock(**response)

    def get_calendar(
        self,
        filters: Optional[GetCalendarRequest] = None,
    ) -> Union[List[Calendar], RawData]:
        """
        The calendar API serves the full list of market days from 1970 to 2029. It can also be queried by specifying a
        start and/or end time to narrow down the results.

        In addition to the dates, the response also contains the specific open and close times for the market days,
        taking into account early closures.

        Args:
            filters: Any optional filters to limit the returned market days

        Returns:
            List[Calendar]: A list of Calendar objects representing the market days.
        """

        result = self.get(
            "/calendar", filters.to_request_fields() if filters is not None else {}
        )

        if self._use_raw_data:
            return result

        return TypeAdapter(List[Calendar]).validate_python(result)

    # ############################## WATCHLISTS ################################# #

    def get_watchlists_for_account(
        self,
        account_id: Union[UUID, str],
    ) -> Union[List[Watchlist], RawData]:
        """
        Returns all watchlists for an account.

        Args:
            account_id (Union[UUID, str]): The account to retrieve watchlists for

        Returns:
            List[Watchlist]: The watchlists for that account
        """
        account_id = validate_uuid_id_param(account_id, "account_id")

        result = self.get(f"/trading/accounts/{account_id}/watchlists")

        if self._use_raw_data:
            return result

        return TypeAdapter(List[Watchlist]).validate_python(result)

    def get_watchlist_for_account_by_id(
        self,
        account_id: Union[UUID, str],
        watchlist_id: Union[UUID, str],
    ) -> Union[Watchlist, RawData]:
        """
        Returns a specific watchlist by its id for a given account.

        Args:
            account_id (Union[UUID, str]): The account to retrieve watchlist data for.
            watchlist_id (Union[UUID, str]): The watchlist to retrieve.

        Returns:
            Watchlist: The watchlist.
        """
        account_id = validate_uuid_id_param(account_id, "account_id")
        watchlist_id = validate_uuid_id_param(watchlist_id, "watchlist_id")

        result = self.get(f"/trading/accounts/{account_id}/watchlists/{watchlist_id}")

        if self._use_raw_data:
            return result

        return Watchlist(**result)

    def create_watchlist_for_account(
        self,
        account_id: Union[UUID, str],
        watchlist_data: CreateWatchlistRequest,
    ) -> Union[Watchlist, RawData]:
        """
        Creates a new watchlist for a given account.

        Args:
            account_id (Union[UUID, str]): The account to create a new watchlist for.
            watchlist_data (CreateWatchlistRequest): The watchlist to create.

        Returns:
            Watchlist: The new watchlist.
        """
        account_id = validate_uuid_id_param(account_id, "account_id")

        result = self.post(
            f"/trading/accounts/{account_id}/watchlists",
            watchlist_data.to_request_fields(),
        )

        if self._use_raw_data:
            return result

        return Watchlist(**result)

    def update_watchlist_for_account_by_id(
        self,
        account_id: Union[UUID, str],
        watchlist_id: Union[UUID, str],
        # Might be worth taking a union of this and Watchlist itself; but then we should make a change like that SDK
        # wide. Probably a good 0.2.x change
        watchlist_data: UpdateWatchlistRequest,
    ) -> Union[Watchlist, RawData]:
        """
        Updates a watchlist with new data.

        Args:
            account_id (Union[UUID, str]): The account whose watchlist to be updated.
            watchlist_id (Union[UUID, str]): The watchlist to be updated.
            watchlist_data (UpdateWatchlistRequest): The new watchlist data.

        Returns:
            Watchlist: The watchlist with updated data.
        """
        watchlist_id = validate_uuid_id_param(watchlist_id, "watchlist_id")
        account_id = validate_uuid_id_param(account_id, "account_id")

        result = self.put(
            f"/trading/accounts/{account_id}/watchlists/{watchlist_id}",
            watchlist_data.to_request_fields(),
        )

        if self._use_raw_data:
            return result

        return Watchlist(**result)

    def add_asset_to_watchlist_for_account_by_id(
        self,
        account_id: Union[UUID, str],
        watchlist_id: Union[UUID, str],
        symbol: str,
    ) -> Union[Watchlist, RawData]:
        """
        Adds an asset by its symbol to a specified watchlist for a given account.
        Args:
            account_id (Union[UUID, str]): The account id that the watchlist belongs to.
            watchlist_id (Union[UUID, str]): The watchlist to add the symbol to.
            symbol (str): The symbol for the asset to add.

        Returns:
            Watchlist: The updated watchlist.
        """
        account_id = validate_uuid_id_param(account_id, "account_id")
        watchlist_id = validate_uuid_id_param(watchlist_id, "watchlist_id")

        params = {"symbol": symbol}

        result = self.post(
            f"/trading/accounts/{account_id}/watchlists/{watchlist_id}", params
        )

        if self._use_raw_data:
            return result

        return Watchlist(**result)

    def delete_watchlist_from_account_by_id(
        self,
        account_id: Union[UUID, str],
        watchlist_id: Union[UUID, str],
    ) -> None:
        """
        Deletes a watchlist. This is permanent.

        Args:
            account_id (Union[UUID, str]): The account the watchlist belongs to.
            watchlist_id (Union[UUID, str]): The watchlist to delete.

        Returns:
            None
        """
        account_id = validate_uuid_id_param(account_id, "account_id")
        watchlist_id = validate_uuid_id_param(watchlist_id, "watchlist_id")

        self.delete(f"/trading/accounts/{account_id}/watchlists/{watchlist_id}")

    def remove_asset_from_watchlist_for_account_by_id(
        self,
        account_id: Union[UUID, str],
        watchlist_id: Union[UUID, str],
        symbol: str,
    ) -> Union[Watchlist, RawData]:
        """
        Removes an asset from a watchlist for a given account.

        Args:
            account_id (Union[UUID, str]): The account the watchlist belongs to.
            watchlist_id (Union[UUID, str]): The watchlist to remove the asset from.
            symbol (str): The symbol for the asset to add.

        Returns:
            Watchlist: The updated watchlist.
        """
        account_id = validate_uuid_id_param(account_id, "account_id")
        watchlist_id = validate_uuid_id_param(watchlist_id, "watchlist_id")

        result = self.delete(
            f"/trading/accounts/{account_id}/watchlists/{watchlist_id}/{symbol}"
        )

        if self._use_raw_data:
            return result

        return Watchlist(**result)

    # ############################## JOURNALS ################################# #

    def create_journal(
        self,
        journal_data: CreateJournalRequest,
    ) -> Union[Journal, RawData]:
        """
        The journal API allows you to transfer cash and securities between accounts.

        Creates a new journal request.

        Args:
            journal_data (CreateJournalRequest): THe journal to be submitted.

        Returns:
            Journal: The submitted journal.
        """
        params = journal_data.to_request_fields() if journal_data else {}

        response = self.post("/journals", params)

        if self._use_raw_data:
            return response

        return Journal(**response)

    def create_batch_journal(
        self,
        batch_data: CreateBatchJournalRequest,
    ) -> Union[List[BatchJournalResponse], RawData]:
        """
        A batch journal moves assets from one account into many others.

        Currently, cash batch journals are supported.

        Args:
            batch_data (CreateBatchJournalRequest): The batch journals to be submitted.

        Returns:
            BatchJournalResponse: The submitted batch journals.
        """
        params = batch_data.to_request_fields() if batch_data else {}

        response = self.post("/journals/batch", params)

        if self._use_raw_data:
            return response

        return TypeAdapter(List[BatchJournalResponse]).validate_python(response)

    def create_reverse_batch_journal(
        self,
        reverse_batch_data: CreateReverseBatchJournalRequest,
    ) -> Union[List[BatchJournalResponse], RawData]:
        """
        A  reverse batch journal moves assets into one account from many others.

        Currently, cash reverse batch journals are supported.

        Args:
            reverse_batch_data (CreateReverseBatchJournalRequest): The reverse batch journals to be submitted.

        Returns:
            BatchJournalResponse: The submitted reverse batch journals.
        """
        params = reverse_batch_data.to_request_fields() if reverse_batch_data else {}

        response = self.post("/journals/reverse_batch", params)

        if self._use_raw_data:
            return response

        return TypeAdapter(List[BatchJournalResponse]).validate_python(response)

    def get_journals(
        self, journal_filter: Optional[GetJournalsRequest] = None
    ) -> Union[List[Journal], RawData]:
        """
        Returns journals from the master list.

        Args:
            journal_filter (Optional[GetJournalsRequest]): The parameters to filter the query by.

        Returns:
            List[Journal]: The journals from the query.
        """
        params = journal_filter.to_request_fields() if journal_filter else {}

        response = self.get("/journals", params)

        if self._use_raw_data:
            return response

        return TypeAdapter(List[Journal]).validate_python(response)

    def get_journal_by_id(
        self, journal_id: Union[UUID, str] = None
    ) -> Union[Journal, RawData]:
        """
        Returns a specific journal by its id.

        Args:
            journal_id (Union[UUID, str]): The id of the journal to retrieve.

        Returns:
            Journal: The journal with given id.
        """
        journal_id = validate_uuid_id_param(journal_id, "journal id")

        response = self.get(f"/journals/{journal_id}")

        if self._use_raw_data:
            return response

        return Journal(**response)

    def cancel_journal_by_id(
        self,
        journal_id: Union[UUID, str],
    ) -> None:
        """
        Cancels a specific journal by its id.

        Args:
            journal_id (Union[UUID, str]): The id of the journal to be cancelled.

        Returns:
            None
        """
        journal_id = validate_uuid_id_param(journal_id, "journal id")

        self.delete(f"/journals/{journal_id}")

    # ############################## Assets ################################# #

    def get_all_assets(
        self, filter: Optional[GetAssetsRequest] = None
    ) -> Union[List[Asset], RawData]:
        """
        The assets API serves as the master list of assets available for trade and data consumption from Alpaca.
        Some assets are not tradable with Alpaca. These assets will be marked with the flag tradable=false.

        Args:
            filter (Optional[GetAssetsRequest]): The parameters that can be assets can be queried by.

        Returns:
            List[Asset]: The list of assets.
        """
        # checking to see if we specified at least one param
        params = filter.to_request_fields() if filter is not None else {}

        response = self.get(f"/assets", params)

        if self._use_raw_data:
            return response

        return TypeAdapter(
            List[Asset],
        ).validate_python(response)

    def get_asset(self, symbol_or_asset_id: Union[UUID, str]) -> Union[Asset, RawData]:
        """
        Returns a specific asset by its symbol or asset id. If the specified asset does not exist
        a 404 error will be thrown.

        Args:
            symbol_or_asset_id (Union[UUID, str]): The symbol or asset id for the specified asset

        Returns:
            Asset: The asset if it exists.
        """

        symbol_or_asset_id = validate_symbol_or_asset_id(symbol_or_asset_id)

        response = self.get(f"/assets/{symbol_or_asset_id}")

        if self._use_raw_data:
            return response

        return Asset(**response)

    # ############################## ORDERS ################################# #

    def submit_order_for_account(
        self, account_id: Union[UUID, str], order_data: OrderRequest
    ) -> Union[Order, RawData]:
        """Creates an order to buy or sell an asset for an account.

        Args:
            account_id (Union[UUID, str]): The account the order will be created for.
            order_data (alpaca.broker.requests.OrderRequest): The request data for creating a new order.

        Returns:
            alpaca.broker.models.OrderOrder: The resulting submitted order.
        """

        account_id = validate_uuid_id_param(account_id, "account_id")

        data = order_data.to_request_fields()

        response = self.post(f"/trading/accounts/{account_id}/orders", data)

        if self._use_raw_data:
            return response

        return Order(**response)

    def get_orders_for_account(
        self, account_id: Union[UUID, str], filter: Optional[GetOrdersRequest] = None
    ) -> Union[List[Order], RawData]:
        """
        Returns all orders for an account. Orders can be filtered by parameters.

        Args:
            account_id (Union[UUID, str]): The account to get the orders for.
            filter (Optional[GetOrdersRequest]): The parameters to filter the orders with.

        Returns:
            List[alpaca.broker.models.Order]: The queried orders.
        """
        account_id = validate_uuid_id_param(account_id, "account_id")

        # checking to see if we specified at least one param
        params = filter.to_request_fields() if filter is not None else {}

        if "symbols" in params and isinstance(params["symbols"], list):
            params["symbols"] = ",".join(params["symbols"])

        response = self.get(f"/trading/accounts/{account_id}/orders", params)

        if self._use_raw_data:
            return response

        return TypeAdapter(
            List[Order],
        ).validate_python(response)

    def get_order_for_account_by_id(
        self,
        account_id: Union[UUID, str],
        order_id: Union[UUID, str],
        filter: Optional[GetOrderByIdRequest] = None,
    ) -> Union[Order, RawData]:
        """
        Returns a specific order by its order id.

        Args:
            account_id (Union[UUID, str]): The account to get the order for.
            order_id (Union[UUID, str]): The unique uuid identifier for the order.
            filter (Optional[GetOrderByIdRequest]): The parameters for the query.

        Returns:
            alpaca.broker.models.Order: The order that was queried.
        """
        account_id = validate_uuid_id_param(account_id, "account_id")
        order_id = validate_uuid_id_param(order_id, "order_id")

        # checking to see if we specified at least one param
        params = filter.to_request_fields() if filter is not None else {}

        response = self.get(f"/trading/accounts/{account_id}/orders/{order_id}", params)

        if self._use_raw_data:
            return response

        return Order(**response)

    def get_order_for_account_by_client_id(
        self, account_id: Union[UUID, str], client_id: str
    ) -> Union[Order, RawData]:
        """
        Returns a specific order by its client order id.

        Args:
            account_id (Union[UUID, str]): The account to get the order for.
            client_id (str): The client order identifier for the order.

        Returns:
            alpaca.broker.models.Order: The queried order.
        """
        account_id = validate_uuid_id_param(account_id, "account_id")

        params = {"client_order_id": client_id}

        response = self.get(
            f"/trading/accounts/{account_id}/orders:by_client_order_id", params
        )

        if self._use_raw_data:
            return response

        return Order(**response)

    def replace_order_for_account_by_id(
        self,
        account_id: Union[UUID, str],
        order_id: Union[UUID, str],
        order_data: Optional[ReplaceOrderRequest] = None,
    ) -> Union[Order, RawData]:
        """
        Updates an order with new parameters.

        Args:
            account_id (Union[UUID, str]): The account to replace the order for.
            order_id (Union[UUID, str]): The unique uuid identifier for the order being replaced.
            order_data (Optional[ReplaceOrderRequest]): The parameters we wish to update.

        Returns:
            alpaca.broker.models.Order: The updated order.
        """
        account_id = validate_uuid_id_param(account_id, "account_id")
        order_id = validate_uuid_id_param(order_id, "order_id")

        # checking to see if we specified at least one param
        params = order_data.to_request_fields() if order_data is not None else {}

        response = self.patch(
            f"/trading/accounts/{account_id}/orders/{order_id}", params
        )

        if self._use_raw_data:
            return response

        return Order(**response)

    def cancel_orders_for_account(
        self, account_id: Union[UUID, str]
    ) -> Union[List[CancelOrderResponse], RawData]:
        """
        Cancels all orders.

        Args:
            account_id (Union[UUID, str]): The account to cancel the orders for.

        Returns:
            List[CancelOrderResponse]: The list of HTTP statuses for each order attempted to be cancelled.
        """
        account_id = validate_uuid_id_param(account_id, "account_id")

        response = self.delete(f"/trading/accounts/{account_id}/orders")

        if self._use_raw_data:
            return response

        return TypeAdapter(
            List[CancelOrderResponse],
        ).validate_python(response)

    def cancel_order_for_account_by_id(
        self, account_id: Union[UUID, str], order_id: Union[UUID, str]
    ) -> None:
        """
        Cancels a specific order by its order id.

        Args:
            account_id (Union[UUID, str]): The account to cancel the order for.
            order_id (Union[UUID, str]): The unique uuid identifier of the order being cancelled.

        """
        account_id = validate_uuid_id_param(account_id, "account_id")
        order_id = validate_uuid_id_param(order_id, "order_id")

        # TODO: Should ideally return some information about the order's cancel status (Issue #78)
        # TODO: Currently no way to retrieve status details for empty responses with base REST implementation
        self.delete(f"/trading/accounts/{account_id}/orders/{order_id}")

    # ############################## CORPORATE ACTIONS ################################# #

    def get_corporate_announcements(
        self, filter: GetCorporateAnnouncementsRequest
    ) -> Union[List[CorporateActionAnnouncement], RawData]:
        """
        Returns corporate action announcements data given specified search criteria.
        Args:
            filter (GetCorporateAnnouncementsRequest): The parameters to filter the search by.
        Returns:
            List[CorporateActionAnnouncement]: The resulting announcements from the search.
        """
        params = filter.to_request_fields() if filter else {}

        if "ca_types" in params and isinstance(params["ca_types"], list):
            params["ca_types"] = ",".join(params["ca_types"])

        response = self.get("/corporate_actions/announcements", params)

        if self._use_raw_data:
            return response

        return TypeAdapter(
            List[CorporateActionAnnouncement],
        ).validate_python(response)

    def get_corporate_announcement_by_id(
        self, corporate_announcment_id: Union[UUID, str]
    ) -> Union[CorporateActionAnnouncement, RawData]:
        """
        Returns a specific corporate action announcement.
        Args:
            corporate_announcment_id: The id of the desired corporate action announcement
        Returns:
            CorporateActionAnnouncement: The corporate action queried.
        """
        corporate_announcment_id = validate_uuid_id_param(
            corporate_announcment_id, "corporate_announcment_id"
        )

        response = self.get(
            f"/corporate_actions/announcements/{corporate_announcment_id}"
        )

        if self._use_raw_data:
            return response

        return CorporateActionAnnouncement(**response)

    # ############################## EVENTS ################################# #

    def get_account_status_events(
        self, filter: Optional[GetEventsRequest] = None
    ) -> Iterator:
        """
        Subscribes to SSE stream for account status events.

        Args:
            filter: The arguments for filtering the events stream.

        Returns:
            Iterator: Yields events as they arrive
        """

        params = {}

        if filter:
            params = filter.to_request_fields()

        url = self._base_url + "/" + self._api_version + "/events/accounts/status"

        response = self._session.get(
            url=url,
            params=params,
            stream=True,
            headers=self._get_sse_headers(),
        )

        client = sseclient.SSEClient(response)

        for event in client.events():
            yield event.data

    def get_trade_events(self, filter: Optional[GetEventsRequest] = None) -> Iterator:
        """
        Subscribes to SSE stream for trade events.

        Args:
            filter: The arguments for filtering the events stream.

        Returns:
            Iterator: Yields events as they arrive
        """
        params = {}

        if filter:
            params = filter.to_request_fields()

        url = self._base_url + "/" + self._api_version + "/events/trades"

        response = self._session.get(
            url=url,
            params=params,
            stream=True,
            headers=self._get_sse_headers(),
        )

        client = sseclient.SSEClient(response)

        for event in client.events():
            yield event.data

    def get_journal_events(self, filter: Optional[GetEventsRequest] = None) -> Iterator:
        """
        Subscribes to SSE stream for journal status events.

        Args:
            filter: The arguments for filtering the events stream.

        Returns:
            Iterator: Yields events as they arrive
        """
        params = {}

        if filter:
            params = filter.to_request_fields()

        url = self._base_url + "/" + self._api_version + "/events/journals/status"

        response = self._session.get(
            url=url,
            params=params,
            stream=True,
            headers=self._get_sse_headers(),
        )

        client = sseclient.SSEClient(response)

        for event in client.events():
            yield event.data

    def get_transfer_events(
        self, filter: Optional[GetEventsRequest] = None
    ) -> Iterator:
        """
        Subscribes to SSE stream for transfer status events.

        Args:
            filter: The arguments for filtering the events stream.

        Returns:
            Iterator: Yields events as they arrive
        """
        params = {}

        if filter:
            params = filter.to_request_fields()

        url = self._base_url + "/" + self._api_version + "/events/transfers/status"

        response = self._session.get(
            url=url,
            params=params,
            stream=True,
            headers=self._get_sse_headers(),
        )

        client = sseclient.SSEClient(response)

        for event in client.events():
            yield event.data

    def get_non_trading_activity_events(
        self, filter: Optional[GetEventsRequest] = None
    ) -> Iterator:
        """
        Subscribes to SSE stream for non trading activity events.

        Args:
            filter: The arguments for filtering the events stream.

        Returns:
            Iterator: Yields events as they arrive
        """
        params = {}

        if filter:
            params = filter.to_request_fields()

        url = self._base_url + "/" + self._api_version + "/events/nta"

        response = self._session.get(
            url=url,
            params=params,
            stream=True,
            headers=self._get_sse_headers(),
        )

        client = sseclient.SSEClient(response)

        for event in client.events():
            yield event.data

    def _get_sse_headers(self) -> dict:
        headers = self._get_default_headers()

        headers["Connection"] = "keep-alive"
        headers["Cache-Control"] = "no-cache"
        headers["Content-Type"] = "text/event-stream"
        headers["Accept"] = "text/event-stream"

        return headers
