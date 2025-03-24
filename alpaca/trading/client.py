from uuid import UUID
from pydantic import TypeAdapter
import json

from alpaca.common import RawData
from alpaca.common.utils import (
    validate_symbol_or_contract_id,
    validate_uuid_id_param,
    validate_symbol_or_asset_id,
)
from alpaca.common.rest import RESTClient
from typing import Optional, List, Union
from alpaca.common.enums import BaseURL

from alpaca.trading.requests import (
    GetCalendarRequest,
    ClosePositionRequest,
    GetAssetsRequest,
    GetOptionContractsRequest,
    GetPortfolioHistoryRequest,
    OrderRequest,
    GetOrdersRequest,
    ReplaceOrderRequest,
    GetOrderByIdRequest,
    CancelOrderResponse,
    CreateWatchlistRequest,
    UpdateWatchlistRequest,
    GetCorporateAnnouncementsRequest,
)

from alpaca.trading.models import (
    OptionContract,
    OptionContractsResponse,
    Order,
    PortfolioHistory,
    Position,
    ClosePositionResponse,
    Asset,
    Watchlist,
    Clock,
    Calendar,
    TradeAccount,
    CorporateActionAnnouncement,
    AccountConfiguration,
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

        return Position(**response)

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

        return Order(**response)

    def exercise_options_position(
        self,
        symbol_or_contract_id: Union[UUID, str],
    ) -> None:
        """
        This endpoint enables users to exercise a held option contract, converting it into the underlying asset based on the specified terms.
        All available held shares of this option contract will be exercised.
        By default, Alpaca will automatically exercise in-the-money (ITM) contracts at expiry.
        Exercise requests will be processed immediately once received. Exercise requests submitted outside market hours will be rejected.
        To cancel an exercise request or to submit a Do-not-exercise (DNE) instruction, please contact our support team.

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

        return PortfolioHistory(**response)

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

        return AccountConfiguration(**response)

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
