import json
from typing import Iterator, List, Optional, Union
from uuid import UUID

import sseclient
from pydantic import TypeAdapter
from requests.exceptions import HTTPError
from typing_extensions import deprecated as _deprecated

from alpaca.common import RawData
from alpaca.common._deprecation import build_from_response as _build_from_response
from alpaca.common.enums import BaseURL
from alpaca.common.exceptions import APIError
from alpaca.common.rest import RESTClient
from alpaca.common.utils import (
    validate_symbol_or_asset_id,
    validate_symbol_or_contract_id,
    validate_uuid_id_param,
)
from alpaca.trading.enums import ActivityType
from alpaca.trading.models import (
    AccountConfiguration,
    AccountConfigurations,
    Asset,
    Calendar,
    Clock,
    ClockResp,
    ClosePositionResponse,
    CorporateActionAnnouncement,
    CryptoTransfer,
    CryptoWallet,
    GetAccountActivities200ResponseInner,
    ListLocateQuotesResponse,
    ListLocatesResponse,
    Locate,
    NonTradeActivities,
    OptionContract,
    OptionContractsResponse,
    Order,
    PortfolioHistory,
    Position,
    PublicCalendarResp,
    SearchVASPsResponse,
    TokenizationMintResponse,
    TokenizationRequest,
    TradeAccount,
    TradingActivities,
    WalletFeeEstimateResponse,
    Watchlist,
    WhitelistedAddress,
)
from alpaca.trading.models import _account_configuration_patch_payload
from alpaca.trading.requests import (
    ActivityEventsRequest,
    AddAssetToWatchlistRequest,
    CancelOrderResponse,
    ClosePositionRequest,
    CreateLocateRequest,
    CreateWatchlistRequest,
    CreateWhitelistedAddressRequest,
    GetAccountActivitiesByTypeRequest,
    GetAccountActivitiesRequest,
    GetAssetsRequest,
    GetCalendarRequest,
    GetCorporateAnnouncementsRequest,
    GetCryptoWalletsRequest,
    GetLocateQuotesRequest,
    GetLocatesRequest,
    GetOptionContractsRequest,
    GetOrderByIdRequest,
    GetOrdersRequest,
    GetPortfolioHistoryRequest,
    GetTokenizationRequestsRequest,
    GetV3CalendarRequest,
    GetV3ClockRequest,
    GetWalletFeeEstimateRequest,
    OrderRequest,
    PatchOrderRequest,
    ReplaceOrderRequest,
    SearchVASPsRequest,
    TokenizationMintRequest,
    UpdateWatchlistRequest,
    UpdateWhitelistedAddressTravelRuleInfoRequest,
)


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
            base_url=(
                url_override
                if url_override
                else BaseURL.TRADING_PAPER if paper else BaseURL.TRADING_LIVE
            ),
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

        return _build_from_response(Order, response)

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

        return _build_from_response(Order, response)

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

        return _build_from_response(Order, response)

    def replace_order_by_id(
        self,
        order_id: Union[UUID, str],
        order_data: Optional[Union[PatchOrderRequest, ReplaceOrderRequest]] = None,
    ) -> Union[Order, RawData]:
        """
        Updates an order with new parameters.

        Args:
            order_id (Union[UUID, str]): The unique uuid identifier for the order being replaced.
            order_data (Optional[Union[PatchOrderRequest, ReplaceOrderRequest]]): The parameters to update.
                ReplaceOrderRequest remains accepted.

        Returns:
            alpaca.trading.models.Order: The updated order.
        """
        # checking to see if we specified at least one param
        params = order_data.to_request_fields() if order_data is not None else {}

        order_id = validate_uuid_id_param(order_id, "order_id")

        response = self.patch(f"/orders/{order_id}", params)

        if self._use_raw_data:
            return response

        return _build_from_response(Order, response)

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
            None
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

        return _build_from_response(Position, response)

    def close_all_positions(
        self, cancel_orders: Optional[bool] = None
    ) -> Union[List[ClosePositionResponse], RawData]:
        """
        Liquidates all positions for an account.

        Places an order for each open position to liquidate.

        Args:
            cancel_orders (Optional[bool]): If true is specified, cancel all open orders before liquidating all positions.

        Returns:
            List[ClosePositionResponse]: A list of responses from each closed position containing the status code and
              order id.
        """
        response = self.delete(
            "/positions",
            {"cancel_orders": cancel_orders} if cancel_orders else None,
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

        return _build_from_response(Order, response)

    def exercise_options_position(
        self,
        symbol_or_contract_id: Union[UUID, str],
    ) -> None:
        """
        This endpoint enables users to exercise a held option contract, converting it into the underlying asset based on the specified terms.
        All available held shares of this option contract will be exercised.
        By default, Alpaca will automatically exercise in-the-money (ITM) contracts at expiry.
        Exercise requests will be processed immediately once received. Exercise requests submitted outside market hours will be rejected.
        To cancel an exercise request, contact support. To submit a do-not-exercise instruction, call :meth:`do_not_exercise_option`.

        Args:
            symbol_or_contract_id (Union[UUID, str]): Option contract symbol or ID.

        Returns:
            None
        """
        symbol_or_contract_id = validate_symbol_or_contract_id(symbol_or_contract_id)
        self.post(
            f"/positions/{symbol_or_contract_id}/exercise",
        )

    # ############################## Portfolio ################################# #

    def get_portfolio_history(
        self,
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
        response = self.get(
            f"/account/portfolio/history",
            history_filter.to_request_fields() if history_filter else {},
        )

        if self._use_raw_data:
            return response

        return _build_from_response(PortfolioHistory, response)

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

        return _build_from_response(Asset, response)

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

        return _build_from_response(Clock, response)

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

        return _build_from_response(TradeAccount, response)

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

        return _build_from_response(AccountConfiguration, response)

    def set_account_configurations(
        self,
        account_configurations: Union[AccountConfiguration, AccountConfigurations],
    ) -> Union[AccountConfiguration, RawData]:
        """
        Returns account configuration details. Contains information like shorting, margin multiplier
        trader confirmation emails, and Pattern Day Trading (PDT) checks.

        Args:
            account_configurations (Union[AccountConfiguration, AccountConfigurations]): The settings to update.
              With the generated AccountConfigurations, only the fields you set are sent.

        Returns:
            alpaca.broker.models.TradeAccountConfiguration: The account configuration details
        """
        response = self.patch(
            "/account/configurations",
            data=_account_configuration_patch_payload(account_configurations),
        )

        if self._use_raw_data:
            return response

        return _build_from_response(AccountConfiguration, response)

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

        return _build_from_response(Watchlist, result)

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

        return _build_from_response(Watchlist, result)

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

        return _build_from_response(Watchlist, result)

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

        return _build_from_response(Watchlist, result)

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

        return _build_from_response(Watchlist, result)

    # ############################## CORPORATE ACTIONS ################################# #

    @_deprecated(
        "get_corporate_announcements is deprecated and will be removed in a future version. "
        "Please use alpaca.data.historical.corporate_actions.CorporateActionsClient.get_corporate_actions() instead",
    )
    def get_corporate_announcements(
        self, filter: GetCorporateAnnouncementsRequest
    ) -> Union[List[CorporateActionAnnouncement], RawData]:
        """
        .. deprecated:: 0.42.1
            Please use the new corporate actions endpoint instead.
            alpaca.data.historical.corporate_actions.CorporateActionsClient.get_corporate_actions()
            ref. https://docs.alpaca.markets/reference/corporateactions-1

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

    @_deprecated(
        "get_corporate_announcement_by_id is deprecated and will be removed in a future version. "
        "Please use alpaca.data.historical.corporate_actions.CorporateActionsClient.get_corporate_actions() instead",
    )
    def get_corporate_announcement_by_id(
        self, corporate_announcment_id: Union[UUID, str]
    ) -> Union[CorporateActionAnnouncement, RawData]:
        """
        .. deprecated:: 0.45.0
            Please use the new corporate actions endpoint instead.
            alpaca.data.historical.corporate_actions.CorporateActionsClient.get_corporate_actions()
            ref. https://docs.alpaca.markets/reference/corporateactions-1

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

        return _build_from_response(CorporateActionAnnouncement, response)

    # ############################## OPTIONS CONTRACTS ################################# #

    def get_option_contracts(
        self, request: GetOptionContractsRequest
    ) -> Union[OptionContractsResponse, RawData]:
        """
        The option contracts API serves as the master list of option contracts available for trade and data consumption from Alpaca.

        Args:
            request (GetOptionContractsRequest): The parameters that option contracts can be queried by.

        Returns:
            OptionContracts (Union[OptionContractsResponse, RawData]): The object includes list of option contracts.
        """
        if request is None:
            raise ValueError("request (GetOptionContractsRequest) is required")

        params = request.to_request_fields()

        if "underlying_symbols" in params and isinstance(
            request.underlying_symbols, list
        ):
            params["underlying_symbols"] = ",".join(request.underlying_symbols)

        response = self.get("/options/contracts", params)

        if self._use_raw_data:
            return response

        return TypeAdapter(OptionContractsResponse).validate_python(response)

    def get_option_contract(
        self, symbol_or_id: Union[UUID, str]
    ) -> Union[OptionContract, RawData]:
        """
        The option contracts API serves as the master list of option contracts available for trade and data consumption from Alpaca.

        Args:
            symbol_or_id (Union[UUID, str]): The symbol or id of the option contract to retrieve.

        Returns:
            OptionContracts (Union[OptionContracts, RawData]): The list of option contracts.
        """
        if symbol_or_id == "":
            raise ValueError("symbol_or_id is required")

        response = self.get(f"/options/contracts/{symbol_or_id}")

        if self._use_raw_data:
            return response

        return TypeAdapter(OptionContract).validate_python(response)

    # ############################## LOCATES ################################# #

    def get_locates(
        self, filter: Optional[GetLocatesRequest] = None
    ) -> Union[ListLocatesResponse, RawData]:
        """Returns locates for the account.

        Args:
            filter (Optional[GetLocatesRequest]): Symbol, status, date, and page filters.

        Returns:
            Union[ListLocatesResponse, RawData]: The locates page.
        """
        response = self.get(
            "/locates",
            self._query(filter),
            api_version="v1",
        )
        return self._parse(ListLocatesResponse, response)

    def create_locate(self, locate_data: CreateLocateRequest) -> Union[Locate, RawData]:
        """Requests a locate for a short sale.

        Args:
            locate_data (CreateLocateRequest): Symbol, quantity, and optional fee limit.

        Returns:
            Union[Locate, RawData]: The created locate.
        """
        response = self.post(
            "/locates",
            locate_data.to_request_fields(),
            api_version="v1",
        )
        return self._parse(Locate, response)

    def get_locate(self, locate_id: Union[UUID, str]) -> Union[Locate, RawData]:
        """Returns one locate by id.

        Args:
            locate_id (Union[UUID, str]): Locate id.

        Returns:
            Union[Locate, RawData]: The locate.
        """
        locate_id = validate_uuid_id_param(locate_id, "locate_id")
        response = self.get(f"/locates/{locate_id}", api_version="v1")
        return self._parse(Locate, response)

    def get_locate_quotes(
        self, request: GetLocateQuotesRequest
    ) -> Union[ListLocateQuotesResponse, RawData]:
        """Returns locate quotes for the requested symbols.

        Args:
            request (GetLocateQuotesRequest): Symbols to quote.

        Returns:
            Union[ListLocateQuotesResponse, RawData]: Quotes and per-symbol errors.
        """
        response = self.get(
            "/locates/quotes",
            request.to_request_fields(),
            api_version="v1",
        )
        return self._parse(ListLocateQuotesResponse, response)

    # ############################## ACTIVITIES ################################# #

    def get_account_activities(
        self, filter: Optional[GetAccountActivitiesRequest] = None
    ) -> Union[List[GetAccountActivities200ResponseInner], RawData]:
        """Returns one page of account activities.

        Fills are ``TradingActivities``. Every other activity type is
        ``NonTradeActivities``. Pass the ``id`` of the last activity as
        ``page_token`` to request the next page.

        Args:
            filter (Optional[GetAccountActivitiesRequest]): Activity, date, and page filters.

        Returns:
            Union[List[GetAccountActivities200ResponseInner], RawData]: Trade and non-trade activities.
        """
        response = self.get("/account/activities", self._query(filter))
        return self._parse_account_activities(response)

    def get_account_activities_by_type(
        self,
        activity_type: str,
        filter: Optional[GetAccountActivitiesByTypeRequest] = None,
    ) -> Union[List[GetAccountActivities200ResponseInner], RawData]:
        """Returns one page of account activities of one type.

        Fills are ``TradingActivities``. Every other activity type is
        ``NonTradeActivities``.

        Args:
            activity_type (str): Activity type path value, such as ``FILL``.
            filter (Optional[GetAccountActivitiesByTypeRequest]): Date and page filters.

        Returns:
            Union[List[GetAccountActivities200ResponseInner], RawData]: Activities of that type.
        """
        response = self.get(
            f"/account/activities/{activity_type}",
            self._query(filter),
        )
        return self._parse_account_activities(response)

    def subscribe_to_activities_sse(
        self, request_params: Optional[ActivityEventsRequest] = None
    ) -> Iterator:
        """Subscribes to the account-activities SSE stream.

        The trading client itself is version ``v2``. This stream is ``v2beta1``,
        so the request URL is ``/v2beta1/events/activities``.

        Args:
            request_params: Optional ``since``, ``until``, ``since_id``, and ``until_id`` filters.

        Returns:
            Iterator: Yields event payloads as they arrive.
        """
        params = self._query(request_params)
        url = self._base_url + "/v2beta1/events/activities"
        response = self._session.get(
            url=url,
            params=params,
            stream=True,
            headers=self._sse_headers(),
            # Match RESTClient._request: the endpoint URL is user-configurable,
            # so refuse redirects rather than leak auth headers across hosts.
            allow_redirects=False,
        )
        try:
            response.raise_for_status()
        except HTTPError as http_error:
            response.close()
            raise APIError(response.text, http_error)

        client = sseclient.SSEClient(response)
        try:
            for event in client.events():
                yield event.data
        finally:
            response.close()

    # ############################## OPTIONS ################################# #

    def do_not_exercise_option(self, symbol_or_contract_id: Union[UUID, str]) -> None:
        """Submits a do-not-exercise instruction for a held option contract.

        Args:
            symbol_or_contract_id (Union[UUID, str]): Option contract symbol or id.
        """
        symbol_or_contract_id = validate_symbol_or_contract_id(symbol_or_contract_id)
        self.post(f"/positions/{symbol_or_contract_id}/do-not-exercise")

    # ############################## TOKENIZATION ################################# #

    def tokenization_mint(
        self, request: TokenizationMintRequest
    ) -> Union[TokenizationMintResponse, RawData]:
        """Submits a tokenization mint request.

        Args:
            request (TokenizationMintRequest): Issuer, network, quantity, symbol, and wallet.

        Returns:
            Union[TokenizationMintResponse, RawData]: The mint response.
        """
        response = self.post("/tokenization/mint", request.to_request_fields())
        return self._parse(TokenizationMintResponse, response)

    def get_tokenization_requests(
        self, filter: Optional[GetTokenizationRequestsRequest] = None
    ) -> Union[List[TokenizationRequest], RawData]:
        """Returns tokenization requests.

        Args:
            filter (Optional[GetTokenizationRequestsRequest]): Type, status, issuer, and time filters.

        Returns:
            Union[List[TokenizationRequest], RawData]: Matching tokenization requests.
        """
        response = self.get("/tokenization/requests", self._query(filter))
        return self._parse(List[TokenizationRequest], response)

    def get_tokenization_request(
        self, tokenization_request_id: Union[UUID, str]
    ) -> Union[TokenizationRequest, RawData]:
        """Returns one tokenization request by Alpaca id.

        Args:
            tokenization_request_id (Union[UUID, str]): Tokenization request id.

        Returns:
            Union[TokenizationRequest, RawData]: The tokenization request.
        """
        tokenization_request_id = validate_uuid_id_param(
            tokenization_request_id, "tokenization_request_id"
        )
        response = self.get(f"/tokenization/requests/{tokenization_request_id}")
        return self._parse(TokenizationRequest, response)

    def get_tokenization_request_by_client_request_id(
        self, client_request_id: str
    ) -> Union[TokenizationRequest, RawData]:
        """Returns one tokenization request by the caller's request id.

        Args:
            client_request_id (str): Authorized-participant request id.

        Returns:
            Union[TokenizationRequest, RawData]: The tokenization request.
        """
        response = self.get(
            "/tokenization/requests:by_client_request_id",
            {"client_request_id": client_request_id},
        )
        return self._parse(TokenizationRequest, response)

    # ############################## CRYPTO WALLETS ################################# #

    def list_crypto_funding_wallets(
        self, filter: Optional[GetCryptoWalletsRequest] = None
    ) -> Union[CryptoWallet, List[CryptoWallet], RawData]:
        """Returns crypto funding wallets for the account.

        Passing ``asset`` returns the wallet for that asset. If the account does
        not already have one, this request creates it. Omitting ``asset`` lists
        the wallets that already exist.

        The specification describes one wallet when ``asset`` is set and an
        array otherwise. Both JSON shapes are accepted.

        Args:
            filter (Optional[GetCryptoWalletsRequest]): Asset, chain, and network filters.

        Returns:
            Union[CryptoWallet, List[CryptoWallet], RawData]: One wallet, or the account's wallets.
        """
        response = self.get("/wallets", self._query(filter))
        return self._parse_one_or_many(CryptoWallet, response)

    def get_wallet_fee_estimate(
        self, request: Optional[GetWalletFeeEstimateRequest] = None
    ) -> Union[WalletFeeEstimateResponse, RawData]:
        """Estimates the fee for a crypto withdrawal.

        Args:
            request (Optional[GetWalletFeeEstimateRequest]): Asset, addresses, and amount.

        Returns:
            Union[WalletFeeEstimateResponse, RawData]: Total fee and network fee.
        """
        response = self.get("/wallets/fees/estimate", self._query(request))
        return self._parse(WalletFeeEstimateResponse, response)

    def list_crypto_funding_transfers(
        self,
    ) -> Union[CryptoTransfer, List[CryptoTransfer], RawData]:
        """Returns crypto funding transfers for the account.

        The operation description is an array of transfers. The response schema
        is one transfer, so both JSON shapes are accepted.

        Returns:
            Union[CryptoTransfer, List[CryptoTransfer], RawData]: The transfers.
        """
        response = self.get("/wallets/transfers")
        return self._parse_one_or_many(CryptoTransfer, response)

    def get_crypto_funding_transfer(
        self, transfer_id: str
    ) -> Union[CryptoTransfer, RawData]:
        """Returns one crypto funding transfer.

        Args:
            transfer_id (str): Transfer id.

        Returns:
            Union[CryptoTransfer, RawData]: The transfer.
        """
        response = self.get(f"/wallets/transfers/{transfer_id}")
        return self._parse(CryptoTransfer, response)

    def search_vasps(
        self, filter: Optional[SearchVASPsRequest] = None
    ) -> Union[SearchVASPsResponse, RawData]:
        """Searches the travel-rule VASP directory.

        Args:
            filter (Optional[SearchVASPsRequest]): Query, page, and ordering filters.

        Returns:
            Union[SearchVASPsResponse, RawData]: Matching VASPs.
        """
        response = self.get("/wallets/travel-rule/vasps", self._query(filter))
        return self._parse(SearchVASPsResponse, response)

    def list_whitelisted_addresses(
        self,
    ) -> Union[WhitelistedAddress, List[WhitelistedAddress], RawData]:
        """Returns whitelisted withdrawal addresses for the account.

        The operation description is an array of addresses. The response schema
        is one address, so both JSON shapes are accepted.

        Returns:
            Union[WhitelistedAddress, List[WhitelistedAddress], RawData]: The whitelisted addresses.
        """
        response = self.get("/wallets/whitelists")
        return self._parse_one_or_many(WhitelistedAddress, response)

    def create_whitelisted_address(
        self, request: CreateWhitelistedAddressRequest
    ) -> Union[WhitelistedAddress, RawData]:
        """Whitelists a crypto address.

        Args:
            request (CreateWhitelistedAddressRequest): Address, asset, chain, and travel-rule info.

        Returns:
            Union[WhitelistedAddress, RawData]: The whitelisted address.
        """
        response = self.post("/wallets/whitelists", request.to_request_fields())
        return self._parse(WhitelistedAddress, response)

    def delete_whitelisted_address(self, whitelisted_address_id: str) -> None:
        """Deletes a whitelisted address.

        Args:
            whitelisted_address_id (str): Whitelisted address id.
        """
        self.delete(f"/wallets/whitelists/{whitelisted_address_id}")

    def update_whitelisted_address_travel_rule_info(
        self,
        whitelisted_address_id: Union[UUID, str],
        request: UpdateWhitelistedAddressTravelRuleInfoRequest,
    ) -> None:
        """Updates travel-rule information for a whitelisted address.

        Args:
            whitelisted_address_id (Union[UUID, str]): Whitelisted address id.
            request (UpdateWhitelistedAddressTravelRuleInfoRequest): Travel-rule payload.
        """
        self.patch(
            f"/wallets/whitelists/{whitelisted_address_id}/travel-rule-info",
            request.to_request_fields(),
        )

    # ############################## WATCHLISTS BY NAME ################################# #

    def get_watchlist_by_name(self, name: str) -> Union[Watchlist, RawData]:
        """Returns a watchlist by its name.

        Args:
            name (str): Watchlist name.

        Returns:
            Union[Watchlist, RawData]: The watchlist.
        """
        result = self.get("/watchlists:by_name", {"name": name})
        return self._parse_watchlist(result)

    def delete_watchlist_by_name(self, name: str) -> None:
        """Deletes a watchlist by its name.

        Args:
            name (str): Watchlist name.
        """
        self.delete("/watchlists:by_name", {"name": name})

    def add_asset_to_watchlist_by_name(
        self, name: str, watchlist_data: AddAssetToWatchlistRequest
    ) -> Union[Watchlist, RawData]:
        """Adds an asset to the watchlist with the given name.

        Args:
            name (str): Watchlist name.
            watchlist_data (AddAssetToWatchlistRequest): Symbol to append.

        Returns:
            Union[Watchlist, RawData]: The updated watchlist.
        """
        result = self.post(
            "/watchlists:by_name",
            watchlist_data.to_request_fields(),
            params={"name": name},
        )
        return self._parse_watchlist(result)

    def update_watchlist_by_name(
        self, name: str, watchlist_data: UpdateWatchlistRequest
    ) -> Union[Watchlist, RawData]:
        """Replaces the watchlist with the given name.

        Args:
            name (str): Current watchlist name.
            watchlist_data (UpdateWatchlistRequest): New name and symbols.

        Returns:
            Union[Watchlist, RawData]: The updated watchlist.
        """
        result = self.put(
            "/watchlists:by_name",
            watchlist_data.to_request_fields(),
            params={"name": name},
        )
        return self._parse_watchlist(result)

    # ############################## MULTI-MARKET CLOCK & CALENDAR ################################# #

    def get_v3_clock(
        self, filters: Optional[GetV3ClockRequest] = None
    ) -> Union[ClockResp, RawData]:
        """Returns clocks for one or more markets.

        This is distinct from :meth:`get_clock`, which reads the v2 US-equities clock.

        Args:
            filters (Optional[GetV3ClockRequest]): Markets and the time to evaluate.

        Returns:
            Union[ClockResp, RawData]: Clocks for the requested markets.
        """
        response = self.get("/clock", self._query(filters), api_version="v3")
        return self._parse(ClockResp, response)

    def get_v3_calendar(
        self, market: str, filters: Optional[GetV3CalendarRequest] = None
    ) -> Union[PublicCalendarResp, RawData]:
        """Returns the calendar for one market.

        This is distinct from :meth:`get_calendar`, which reads the v2 US-equities calendar.

        Args:
            market (str): Market acronym, such as ``BMO`` or ``NYSE``.
            filters (Optional[GetV3CalendarRequest]): Date range and timezone.

        Returns:
            Union[PublicCalendarResp, RawData]: The market calendar.
        """
        response = self.get(
            f"/calendar/{market}",
            self._query(filters),
            api_version="v3",
        )
        return self._parse(PublicCalendarResp, response)

    def _query(self, request: Optional[object]) -> dict:
        if request is None:
            return {}
        return request.to_request_fields()

    def _parse(self, annotation: object, response: RawData) -> Union[object, RawData]:
        if self._use_raw_data:
            return response
        return TypeAdapter(annotation).validate_python(response)

    def _parse_account_activities(
        self, response: RawData
    ) -> Union[List[GetAccountActivities200ResponseInner], RawData]:
        """Classify each activity by ``activity_type`` before validation.

        ``TradingActivities`` and ``NonTradeActivities`` are both all-optional
        objects, so union validation can treat a sparse fill as a non-trade
        activity. ``FILL`` is the only trade activity type.
        """
        if self._use_raw_data:
            return response
        if not isinstance(response, list):
            raise ValueError("Account activities response was not a list")
        return [self._parse_account_activity(activity) for activity in response]

    @staticmethod
    def _parse_account_activity(data: dict) -> GetAccountActivities200ResponseInner:
        if not isinstance(data, dict) or data.get("activity_type") is None:
            raise ValueError(
                "Failed parsing raw activity data, `activity_type` is not present in fields"
            )

        model = (
            TradingActivities
            if ActivityType.is_str_trade_activity(data["activity_type"])
            else NonTradeActivities
        )
        return TypeAdapter(model).validate_python(data)

    def _parse_one_or_many(
        self, item_type: object, response: RawData
    ) -> Union[object, List[object], RawData]:
        if self._use_raw_data:
            return response
        if isinstance(response, list):
            return TypeAdapter(List[item_type]).validate_python(response)
        return TypeAdapter(item_type).validate_python(response)

    def _parse_watchlist(self, response: RawData) -> Union[Watchlist, RawData]:
        if self._use_raw_data:
            return response
        return _build_from_response(Watchlist, response)

    def _sse_headers(self) -> dict:
        headers = self._get_default_headers()
        headers["Connection"] = "keep-alive"
        headers["Cache-Control"] = "no-cache"
        headers["Accept"] = "text/event-stream"
        return headers
