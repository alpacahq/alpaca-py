from uuid import UUID
from pydantic import TypeAdapter
import json

from alpaca.common import RawData
from alpaca.common.utils import validate_uuid_id_param, validate_symbol_or_asset_id
from alpaca.common.rest import RESTClient
from typing import Callable, Iterator, Optional, List, Union
from alpaca.common.enums import BaseURL, PaginationType

from alpaca.trading.requests import (
    GetCalendarRequest,
    ClosePositionRequest,
    GetAssetsRequest,
    OrderRequest,
    GetOrdersRequest,
    ReplaceOrderRequest,
    GetOrderByIdRequest,
    CancelOrderResponse,
    CreateWatchlistRequest,
    UpdateWatchlistRequest,
    GetCorporateAnnouncementsRequest,
    GetAccountActivitiesRequest,
)

from alpaca.trading.models import (
    BaseActivity,
    NonTradeActivity,
    Order,
    Position,
    ClosePositionResponse,
    Asset,
    TradeActivity,
    Watchlist,
    Clock,
    Calendar,
    TradeAccount,
    CorporateActionAnnouncement,
    AccountConfiguration,
)

from alpaca.common.types import HTTPResult

from alpaca.common.constants import ACCOUNT_ACTIVITIES_DEFAULT_PAGE_SIZE

from alpaca.common.exceptions import APIError

from alpaca.trading.enums import ActivityType


class TradingClient(RESTClient):
    """
    A client to interact with the trading API, in both paper and live mode.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        oauth_token: Optional[str] = None,
        paper: bool = True,
        raw_data: bool = False,
        url_override: Optional[str] = None,
    ) -> None:
        """
        Instantiates a client for trading and managing personal brokerage accounts.

        Args:
            api_key (Optional[str]): The API key for trading. Use paper keys if paper is set to true.
            secret_key (Optional[str]): The secret key for trading. Use paper keys if paper is set to true.
            oauth_token (Optional[str]): The oauth token for trading on behalf of end user.
            paper (bool): True is paper trading should be enabled.
            raw_data (bool): Whether API responses should be wrapped in data models or returned raw.
                This has not been implemented yet.
            url_override (Optional[str]): If specified allows you to override the base url the client points to for proxy/testing.
        """
        super().__init__(
            api_key=api_key,
            secret_key=secret_key,
            oauth_token=oauth_token,
            api_version="v2",
            base_url=url_override
            if url_override
            else BaseURL.TRADING_PAPER
            if paper
            else BaseURL.TRADING_LIVE,
            sandbox=paper,
            raw_data=raw_data,
        )

    # ############################## ORDERS ################################# #

    def submit_order(self, order_data: OrderRequest) -> Union[Order, RawData]:
        """Creates an order to buy or sell an asset.

        Args:
            order_data (alpaca.trading.requests.OrderRequest): The request data for creating a new order.

        Returns:
            alpaca.trading.models.Order: The resulting submitted order.
        """
        data = order_data.to_request_fields()
        response = self.post("/orders", data)

        if self._use_raw_data:
            return response

        return Order(**response)

    def get_orders(
        self, filter: Optional[GetOrdersRequest] = None
    ) -> Union[List[Order], RawData]:
        """
        Returns all orders. Orders can be filtered by parameters.

        Args:
            filter (Optional[GetOrdersRequest]): The parameters to filter the orders with.

        Returns:
            List[alpaca.trading.models.Order]: The queried orders.
        """
        # checking to see if we specified at least one param
        params = filter.to_request_fields() if filter is not None else {}

        if "symbols" in params and isinstance(params["symbols"], list):
            params["symbols"] = ",".join(params["symbols"])

        response = self.get("/orders", params)

        if self._use_raw_data:
            return response

        return TypeAdapter(List[Order]).validate_python(response)

    def get_order_by_id(
        self, order_id: Union[UUID, str], filter: Optional[GetOrderByIdRequest] = None
    ) -> Union[Order, RawData]:
        """
        Returns a specific order by its order id.

        Args:
            order_id (Union[UUID, str]): The unique uuid identifier for the order.
            filter (Optional[GetOrderByIdRequest]): The parameters for the query.

        Returns:
            alpaca.trading.models.Order: The order that was queried.
        """
        # checking to see if we specified at least one param
        params = filter.to_request_fields() if filter is not None else {}

        order_id = validate_uuid_id_param(order_id, "order_id")

        response = self.get(f"/orders/{order_id}", params)

        if self._use_raw_data:
            return response

        return Order(**response)

    def get_order_by_client_id(self, client_id: str) -> Union[Order, RawData]:
        """
        Returns a specific order by its client order id.

        Args:
            client_id (str): The client order identifier for the order.

        Returns:
            alpaca.trading.models.Order: The queried order.
        """
        params = {"client_order_id": client_id}

        response = self.get(f"/orders:by_client_order_id", params)

        if self._use_raw_data:
            return response

        return Order(**response)

    def replace_order_by_id(
        self,
        order_id: Union[UUID, str],
        order_data: Optional[ReplaceOrderRequest] = None,
    ) -> Union[Order, RawData]:
        """
        Updates an order with new parameters.

        Args:
            order_id (Union[UUID, str]): The unique uuid identifier for the order being replaced.
            order_data (Optional[ReplaceOrderRequest]): The parameters we wish to update.

        Returns:
            alpaca.trading.models.Order: The updated order.
        """
        # checking to see if we specified at least one param
        params = order_data.to_request_fields() if order_data is not None else {}

        order_id = validate_uuid_id_param(order_id, "order_id")

        response = self.patch(f"/orders/{order_id}", params)

        if self._use_raw_data:
            return response

        return Order(**response)

    def cancel_orders(self) -> Union[List[CancelOrderResponse], RawData]:
        """
        Cancels all orders.

        Returns:
            List[CancelOrderResponse]: The list of HTTP statuses for each order attempted to be cancelled.
        """
        response = self.delete(f"/orders")

        if self._use_raw_data:
            return response

        return TypeAdapter(List[CancelOrderResponse]).validate_python(response)

    def cancel_order_by_id(self, order_id: Union[UUID, str]) -> None:
        """
        Cancels a specific order by its order id.

        Args:
            order_id (Union[UUID, str]): The unique uuid identifier of the order being cancelled.

        Returns:
            CancelOrderResponse: The HTTP response from the cancel request.
        """
        order_id = validate_uuid_id_param(order_id, "order_id")

        # TODO: Should ideally return some information about the order's cancel status. (Issue #78).
        # TODO: Currently no way to retrieve status details for empty responses with base REST implementation
        self.delete(f"/orders/{order_id}")

    # ############################## POSITIONS ################################# #

    def get_all_positions(
        self,
    ) -> Union[List[Position], RawData]:
        """
        Gets all the current open positions.

        Returns:
            List[Position]: List of open positions.
        """
        response = self.get("/positions")

        if self._use_raw_data:
            return response

        return TypeAdapter(List[Position]).validate_python(response)

    def get_open_position(
        self, symbol_or_asset_id: Union[UUID, str]
    ) -> Union[Position, RawData]:
        """
        Gets the open position for an account for a single asset. Throws an APIError if the position does not exist.

        Args:
            symbol_or_asset_id (Union[UUID, str]): The symbol name of asset id of the position to get.

        Returns:
            Position: Open position of the asset.
        """
        symbol_or_asset_id = validate_symbol_or_asset_id(symbol_or_asset_id)
        response = self.get(f"/positions/{symbol_or_asset_id}")

        if self._use_raw_data:
            return response

        return Position(**response)

    def close_all_positions(
        self, cancel_orders: bool
    ) -> Union[List[ClosePositionResponse], RawData]:
        """
        Liquidates all positions for an account.

        Places an order for each open position to liquidate.

        Args:
            cancel_orders (bool): If true is specified, cancel all open orders before liquidating all positions.

        Returns:
            List[ClosePositionResponse]: A list of responses from each closed position containing the status code and
              order id.
        """
        response = self.delete(
            "/positions",
            {"cancel_orders": cancel_orders},
        )

        if self._use_raw_data:
            return response

        return TypeAdapter(List[ClosePositionResponse]).validate_python(response)

    def close_position(
        self,
        symbol_or_asset_id: Union[UUID, str],
        close_options: Optional[ClosePositionRequest] = None,
    ) -> Union[Order, RawData]:
        """
        Liquidates the position for a single asset.

        Places a single order to close the position for the asset.

        **This method will throw an error if the position does not exist!**

        Args:
            symbol_or_asset_id (Union[UUID, str]): The symbol name of asset id of the position to close.
            close_options: The various close position request parameters.

        Returns:
            alpaca.trading.models.Order: The order that was placed to close the position.
        """
        symbol_or_asset_id = validate_symbol_or_asset_id(symbol_or_asset_id)
        response = self.delete(
            f"/positions/{symbol_or_asset_id}",
            close_options.to_request_fields() if close_options else {},
        )

        if self._use_raw_data:
            return response

        return Order(**response)

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

        return TypeAdapter(List[Asset]).validate_python(response)

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

        result = self.get("/calendar", filters.to_request_fields() if filters else {})

        if self._use_raw_data:
            return result

        return TypeAdapter(List[Calendar]).validate_python(result)

    # ############################## ACCOUNT ################################# #

    def get_account(self) -> Union[TradeAccount, RawData]:
        """
        Returns account details. Contains information like buying power,
        number of day trades, and account status.

        Returns:
            alpaca.trading.models.TradeAccount: The account details
        """

        response = self.get("/account")

        if self._use_raw_data:
            return response

        return TradeAccount(**response)

    def get_account_configurations(self) -> Union[AccountConfiguration, RawData]:
        """
        Returns account configuration details. Contains information like shorting, margin multiplier
        trader confirmation emails, and Pattern Day Trading (PDT) checks.

        Returns:
            alpaca.broker.models.AccountConfiguration: The account configuration details
        """
        response = self.get("/account/configurations")

        if self._use_raw_data:
            return response

        return AccountConfiguration(**response)

    def set_account_configurations(
        self, account_configurations: AccountConfiguration
    ) -> Union[AccountConfiguration, RawData]:
        """
        Returns account configuration details. Contains information like shorting, margin multiplier
        trader confirmation emails, and Pattern Day Trading (PDT) checks.

        Returns:
            alpaca.broker.models.TradeAccountConfiguration: The account configuration details
        """
        response = self.patch(
            "/account/configurations", data=account_configurations.model_dump()
        )

        if self._use_raw_data:
            return response

        return AccountConfiguration(**json.loads(response))

    # ############################## ACCOUNT ACTIVITIES ######################## #

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
        handle_pagination = TradingClient._validate_pagination(
            max_items_limit, handle_pagination
        )

        # otherwise, user wants pagination so we grab an interator
        iterator = self._get_account_activities_iterator(
            activity_filter=activity_filter,
            max_items_limit=max_items_limit,
            mapping=lambda raw_activities: [
                TradingClient._parse_activity(activity) for activity in raw_activities
            ],
        )

        return TradingClient._return_paginated_result(iterator, handle_pagination)

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

            result = self.get("/account/activities", request_fields)

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

    # ############################## WATCHLIST ################################# #

    def get_watchlists(
        self,
    ) -> Union[List[Watchlist], RawData]:
        """
        Returns all watchlists.

        Returns:
            List[Watchlist]: The list of all watchlists.
        """

        result = self.get(f"/watchlists")

        if self._use_raw_data:
            return result

        return TypeAdapter(List[Watchlist]).validate_python(result)

    def get_watchlist_by_id(
        self,
        watchlist_id: Union[UUID, str],
    ) -> Union[Watchlist, RawData]:
        """
        Returns a specific watchlist by its id.

        Args:
            watchlist_id (Union[UUID, str]): The watchlist to retrieve.

        Returns:
            Watchlist: The watchlist.
        """
        watchlist_id = validate_uuid_id_param(watchlist_id, "watchlist_id")

        result = self.get(f"/watchlists/{watchlist_id}")

        if self._use_raw_data:
            return result

        return Watchlist(**result)

    def create_watchlist(
        self,
        watchlist_data: CreateWatchlistRequest,
    ) -> Union[Watchlist, RawData]:
        """
        Creates a new watchlist.

        Args:
            watchlist_data (CreateWatchlistRequest): The watchlist to create.

        Returns:
            Watchlist: The new watchlist.
        """
        result = self.post(
            "/watchlists",
            watchlist_data.to_request_fields(),
        )

        if self._use_raw_data:
            return result

        return Watchlist(**result)

    def update_watchlist_by_id(
        self,
        watchlist_id: Union[UUID, str],
        # Might be worth taking a union of this and Watchlist itself; but then we should make a change like that SDK
        # wide. Probably a good 0.2.x change
        watchlist_data: UpdateWatchlistRequest,
    ) -> Union[Watchlist, RawData]:
        """
        Updates a watchlist with new data.

        Args:
            watchlist_id (Union[UUID, str]): The watchlist to be updated.
            watchlist_data (UpdateWatchlistRequest): The new watchlist data.

        Returns:
            Watchlist: The watchlist with updated data.
        """
        watchlist_id = validate_uuid_id_param(watchlist_id, "watchlist_id")

        result = self.put(
            f"/watchlists/{watchlist_id}",
            watchlist_data.to_request_fields(),
        )

        if self._use_raw_data:
            return result

        return Watchlist(**result)

    def add_asset_to_watchlist_by_id(
        self,
        watchlist_id: Union[UUID, str],
        symbol: str,
    ) -> Union[Watchlist, RawData]:
        """
        Adds an asset by its symbol to a specified watchlist.

        Args:
            watchlist_id (Union[UUID, str]): The watchlist to add the symbol to.
            symbol (str): The symbol for the asset to add.

        Returns:
            Watchlist: The updated watchlist.
        """
        watchlist_id = validate_uuid_id_param(watchlist_id, "watchlist_id")

        params = {"symbol": symbol}

        result = self.post(f"/watchlists/{watchlist_id}", params)

        if self._use_raw_data:
            return result

        return Watchlist(**result)

    def delete_watchlist_by_id(
        self,
        watchlist_id: Union[UUID, str],
    ) -> None:
        """
        Deletes a watchlist. This is permanent.

        Args:
            watchlist_id (Union[UUID, str]): The watchlist to delete.

        Returns:
            None
        """
        watchlist_id = validate_uuid_id_param(watchlist_id, "watchlist_id")

        self.delete(f"/watchlists/{watchlist_id}")

    def remove_asset_from_watchlist_by_id(
        self,
        watchlist_id: Union[UUID, str],
        symbol: str,
    ) -> Union[Watchlist, RawData]:
        """
        Removes an asset from a watchlist.

        Args:
            watchlist_id (Union[UUID, str]): The watchlist to remove the asset from.
            symbol (str): The symbol for the asset to add.

        Returns:
            Watchlist: The updated watchlist.
        """
        watchlist_id = validate_uuid_id_param(watchlist_id, "watchlist_id")

        result = self.delete(f"/watchlists/{watchlist_id}/{symbol}")

        if self._use_raw_data:
            return result

        return Watchlist(**result)

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

        return TypeAdapter(List[CorporateActionAnnouncement]).validate_python(response)

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
