from uuid import UUID
from pydantic import parse_obj_as

from alpaca.common.utils import validate_uuid_id_param, validate_symbol_or_asset_id
from alpaca.common.rest import RESTClient
from typing import Optional, List, Union
from alpaca.common.enums import BaseURL

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
)

from alpaca.trading.models import (
    Order,
    Position,
    ClosePositionResponse,
    Asset,
    Watchlist,
    Clock,
    Calendar,
    TradeAccount,
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
        sandbox: bool = True,
        raw_data: bool = False,
        url_override: Optional[str] = None,
    ) -> None:
        super().__init__(
            api_key=api_key,
            secret_key=secret_key,
            oauth_token=oauth_token,
            api_version="v2",
            base_url=url_override
            if url_override
            else BaseURL.TRADING_PAPER
            if sandbox
            else BaseURL.TRADING_LIVE,
            sandbox=sandbox,
            raw_data=raw_data,
        )

    # ############################## ORDERS ################################# #

    def submit_order(self, order_data: OrderRequest) -> Order:
        """Creates an order to buy or sell an asset.

        Args:
            order_data (alpaca.trading.requests.OrderRequest): The request data for creating a new order.

        Returns:
            alpaca.trading.models.Order: The resulting submitted order.
        """
        data = order_data.to_request_fields()
        response = self.post("/orders", data)

        return Order(**response)

    def get_orders(self, filter: Optional[GetOrdersRequest] = None) -> List[Order]:
        """
        Returns all orders. Orders can be filtered by parameters.

        Args:
            filter (Optional[GetOrdersRequest]): The parameters to filter the orders with.

        Returns:
            List[alpaca.trading.models.Order]: The queried orders.
        """
        # checking to see if we specified at least one param
        params = filter.to_request_fields() if filter is not None else {}

        if "symbols" in params and type(params["symbols"]) is List:
            params["symbols"] = ",".join(params["symbols"])

        response = self.get("/orders", params)

        return parse_obj_as(List[Order], response)

    def get_order_by_id(
        self, order_id: Union[UUID, str], filter: Optional[GetOrderByIdRequest] = None
    ) -> Order:
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

        return Order(**response)

    def get_order_by_client_id(self, client_id: str) -> Order:
        """
        Returns a specific order by its client order id.

        Args:
            client_id (str): The client order identifier for the order.

        Returns:
            alpaca.trading.models.Order: The queried order.
        """
        response = self.get(f"/orders/{client_id}")

        return Order(**response)

    def replace_order_by_id(
        self,
        order_id: Union[UUID, str],
        order_data: Optional[ReplaceOrderRequest] = None,
    ) -> Order:
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

        return Order(**response)

    def cancel_orders(self) -> List[CancelOrderResponse]:
        """
        Cancels all orders.

        Returns:
            List[CancelOrderResponse]: The list of HTTP statuses for each order attempted to be cancelled.
        """
        response = self.delete(f"/orders")

        return parse_obj_as(List[CancelOrderResponse], response)

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
    ) -> List[Position]:
        """
        Gets all the current open positions.

        Returns:
            List[Position]: List of open positions.
        """
        response = self.get("/positions")
        return parse_obj_as(List[Position], response)

    def get_open_position(self, symbol_or_asset_id: Union[UUID, str]) -> Position:
        """
        Gets the open position for an account for a single asset.

        Args:
            symbol_or_asset_id (Union[UUID, str]): The symbol name of asset id of the position to get.

        Returns:
            Position: Open position of the asset.
        """
        symbol_or_asset_id = validate_symbol_or_asset_id(symbol_or_asset_id)
        response = self.get(f"/positions/{symbol_or_asset_id}")
        return Position(**response)

    def close_all_positions(self, cancel_orders: bool) -> List[ClosePositionResponse]:
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
        return parse_obj_as(List[ClosePositionResponse], response)

    def close_position(
        self,
        symbol_or_asset_id: Union[UUID, str],
        close_options: Optional[ClosePositionRequest] = None,
    ) -> Order:
        """
        Liquidates the position for a single asset.

        Places a single order to close the position for the asset.

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
        return Order(**response)

    # ############################## Assets ################################# #

    def get_all_assets(self, filter: Optional[GetAssetsRequest] = None) -> List[Asset]:
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

        return parse_obj_as(List[Asset], response)

    def get_asset(self, symbol_or_asset_id: Union[UUID, str]) -> Asset:
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

        return Asset(**response)

    # ############################## CLOCK & CALENDAR ################################# #

    def get_clock(self) -> Clock:
        """
        Gets the current market timestamp, whether or not the market is currently open, as well as the times
        of the next market open and close.

        Returns:
            Clock: The market Clock data
        """
        return Clock(**self.get("/clock"))

    def get_calendar(
        self,
        filters: Optional[GetCalendarRequest] = None,
    ) -> List[Calendar]:
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

        return parse_obj_as(List[Calendar], result)

    # ############################## ACCOUNT ################################# #

    def get_account(self) -> TradeAccount:
        """
        Returns account details. Contains information like buying power,
        number of day trades, and account status.

        Returns:
            alpaca.common.models.accounts.TradeAccount: The account details
        """

        response = self.get("/account")

        return TradeAccount(**response)

    # ############################## WATCHLIST ################################# #

    def get_watchlists(
        self,
    ) -> List[Watchlist]:
        """
        Returns all watchlists.

        Returns:
            List[Watchlist]: The list of all watchlists.
        """

        result = self.get(f"/watchlists")

        return parse_obj_as(List[Watchlist], result)

    def get_watchlist_by_id(
        self,
        watchlist_id: Union[UUID, str],
    ) -> Watchlist:
        """
        Returns a specific watchlist by its id.

        Args:
            watchlist_id (Union[UUID, str]): The watchlist to retrieve.

        Returns:
            Watchlist: The watchlist.
        """
        watchlist_id = validate_uuid_id_param(watchlist_id, "watchlist_id")

        result = self.get(f"/watchlists/{watchlist_id}")

        return Watchlist(**result)

    def create_watchlist(
        self,
        watchlist_data: CreateWatchlistRequest,
    ) -> Watchlist:
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

        return Watchlist(**result)

    def update_watchlist_by_id(
        self,
        watchlist_id: Union[UUID, str],
        # Might be worth taking a union of this and Watchlist itself; but then we should make a change like that SDK
        # wide. Probably a good 0.2.x change
        watchlist_data: UpdateWatchlistRequest,
    ) -> Watchlist:
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

        return Watchlist(**result)

    def add_asset_to_watchlist_by_id(
        self,
        watchlist_id: Union[UUID, str],
        symbol: str,
    ) -> Watchlist:
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
    ) -> Watchlist:
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

        return Watchlist(**result)
