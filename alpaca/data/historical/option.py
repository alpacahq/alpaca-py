from enum import Enum
from typing import Dict, Iterator, Literal, Optional, Union, overload

from alpaca.common.enums import BaseURL, PaginationType
from alpaca.common.rest import RESTClient
from alpaca.common.types import RawData
from alpaca.data.historical.utils import (
    parse_obj_as_symbol_dict,
)
from alpaca.data.models.bars import BarSet
from alpaca.data.models.quotes import Quote
from alpaca.data.models.snapshots import OptionsSnapshot
from alpaca.data.models.trades import Trade, TradeSet
from alpaca.data.requests import (
    OptionBarsRequest,
    OptionChainRequest,
    OptionLatestQuoteRequest,
    OptionLatestTradeRequest,
    OptionSnapshotRequest,
    OptionTradesRequest,
)


class OptionHistoricalDataClient(RESTClient):
    """
    The REST client for interacting with Alpaca Market Data API option data endpoints.

    Learn more on https://docs.alpaca.markets/docs/about-market-data-api
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        oauth_token: Optional[str] = None,
        use_basic_auth: bool = False,
        raw_data: bool = False,
        url_override: Optional[str] = None,
        sandbox: bool = False,
    ) -> None:
        """
        Instantiates a Historical Data Client.

        Args:
            api_key (Optional[str], optional): Alpaca API key. Defaults to None.
            secret_key (Optional[str], optional): Alpaca API secret key. Defaults to None.
            oauth_token (Optional[str]): The oauth token if authenticating via OAuth. Defaults to None.
            use_basic_auth (bool, optional): If true, API requests will use basic authorization headers. Set to true if using
              broker api sandbox credentials
            raw_data (bool, optional): If true, API responses will not be wrapped and raw responses will be returned from
              methods. Defaults to False. This has not been implemented yet.
            url_override (Optional[str], optional): If specified allows you to override the base url the client points
              to for proxy/testing.
            sandbox (bool): True if using sandbox mode. Defaults to False.
        """

        base_url = (
            url_override
            if url_override is not None
            else BaseURL.DATA_SANDBOX if sandbox else BaseURL.DATA
        )

        super().__init__(
            api_key=api_key,
            secret_key=secret_key,
            oauth_token=oauth_token,
            use_basic_auth=use_basic_auth,
            api_version="v1beta1",
            base_url=base_url,
            sandbox=sandbox,
            raw_data=raw_data,
        )

    # Overloads are matched in order. Omitting handle_pagination, or passing
    # FULL or NONE, keeps the return type from before pagination. ITERATOR is
    # the only mode typed as an iterator. A plain PaginationType value matches
    # the last overload, whose return is the union of both.
    @overload
    def get_option_bars(
        self,
        request_params: OptionBarsRequest,
        handle_pagination: Literal[PaginationType.ITERATOR],
    ) -> Iterator[Union[BarSet, RawData]]: ...

    @overload
    def get_option_bars(
        self,
        request_params: OptionBarsRequest,
        handle_pagination: Union[
            Literal[PaginationType.FULL, PaginationType.NONE], None
        ] = None,
    ) -> Union[BarSet, RawData]: ...

    @overload
    def get_option_bars(
        self,
        request_params: OptionBarsRequest,
        handle_pagination: Optional[PaginationType] = None,
    ) -> Union[BarSet, RawData, Iterator[Union[BarSet, RawData]]]: ...

    def get_option_bars(
        self,
        request_params: OptionBarsRequest,
        handle_pagination: Optional[PaginationType] = None,
    ) -> Union[BarSet, RawData, Iterator[Union[BarSet, RawData]]]:
        """Returns bar data for an option contract or list of option contracts over a given
        time period and timeframe.

        Args:
            request_params (OptionBarsRequest): The request object for retrieving option bar data.
            handle_pagination (Optional[PaginationType]): How to page through the results. Defaults to
              ``PaginationType.FULL``, which fetches every page and returns one merged BarSet.
              ``PaginationType.ITERATOR`` returns a lazy iterator that fetches and yields one page at a time,
              so large queries don't have to fit in memory. ``PaginationType.NONE`` fetches only one page;
              pass its ``next_page_token`` as the request's ``page_token`` to continue.

        Returns:
            Union[BarSet, RawData, Iterator[Union[BarSet, RawData]]]: ``BarSet`` or raw JSON when
              ``handle_pagination`` is omitted, ``FULL``, or ``NONE``. An iterator of those pages
              when it is ``ITERATOR``. A value typed only as ``PaginationType`` is the union of both.
        """

        return self._get_paginated_marketdata(
            path=f"/options/bars",
            params=request_params.to_request_fields(),
            page_size=10_000,
            set_type=BarSet,
            handle_pagination=handle_pagination,
        )

    def get_option_exchange_codes(self) -> RawData:
        """Returns the mapping between the option exchange codes and the corresponding exchanges names.

        Args:
            None

        Returns:
            RawData: The mapping between the option exchange codes and the corresponding exchanges names.
        """
        path = "/options/meta/exchanges"
        raw_exchange_code = self.get(
            path=path,
            api_version=self._api_version,
        )

        return raw_exchange_code

    def get_option_latest_quote(
        self, request_params: OptionLatestQuoteRequest
    ) -> Union[Dict[str, Quote], RawData]:
        """Retrieves the latest quote for an option symbol or list of option symbols.

        Args:
            request_params (OptionLatestQuoteRequest): The request object for retrieving the latest quote data.

        Returns:
            Union[Dict[str, Quote], RawData]: The latest quote in raw or wrapped format
        """
        raw_latest_quotes = self._get_marketdata(
            path=f"/options/quotes/latest",
            params=request_params.to_request_fields(),
        )

        if self._use_raw_data:
            return raw_latest_quotes

        return parse_obj_as_symbol_dict(Quote, raw_latest_quotes)

    def get_option_latest_trade(
        self, request_params: OptionLatestTradeRequest
    ) -> Union[Dict[str, Trade], RawData]:
        """Retrieves the latest trade for an option symbol or list of option symbols.

        Args:
            request_params (OptionLatestTradeRequest): The request object for retrieving the latest trade data.

        Returns:
            Union[Dict[str, Trade], RawData]: The latest trade in raw or wrapped format
        """
        raw_latest_trades = self._get_marketdata(
            path=f"/options/trades/latest",
            params=request_params.to_request_fields(),
        )

        if self._use_raw_data:
            return raw_latest_trades

        return parse_obj_as_symbol_dict(Trade, raw_latest_trades)

    @overload
    def get_option_trades(
        self,
        request_params: OptionTradesRequest,
        handle_pagination: Literal[PaginationType.ITERATOR],
    ) -> Iterator[Union[TradeSet, RawData]]: ...

    @overload
    def get_option_trades(
        self,
        request_params: OptionTradesRequest,
        handle_pagination: Union[
            Literal[PaginationType.FULL, PaginationType.NONE], None
        ] = None,
    ) -> Union[TradeSet, RawData]: ...

    @overload
    def get_option_trades(
        self,
        request_params: OptionTradesRequest,
        handle_pagination: Optional[PaginationType] = None,
    ) -> Union[TradeSet, RawData, Iterator[Union[TradeSet, RawData]]]: ...

    def get_option_trades(
        self,
        request_params: OptionTradesRequest,
        handle_pagination: Optional[PaginationType] = None,
    ) -> Union[TradeSet, RawData, Iterator[Union[TradeSet, RawData]]]:
        """The historical option trades API provides trade data for a list of contract symbols between the specified dates up to 7 days ago.

        Args:
            request_params (OptionTradesRequest): The request object for retrieving option trade data.
            handle_pagination (Optional[PaginationType]): How to page through the results. Defaults to
              ``PaginationType.FULL``, which fetches every page and returns one merged TradeSet.
              ``PaginationType.ITERATOR`` returns a lazy iterator that fetches and yields one page at a time,
              so large queries don't have to fit in memory. ``PaginationType.NONE`` fetches only one page;
              pass its ``next_page_token`` as the request's ``page_token`` to continue.

        Returns:
            Union[TradeSet, RawData, Iterator[Union[TradeSet, RawData]]]: ``TradeSet`` or raw JSON when
              ``handle_pagination`` is omitted, ``FULL``, or ``NONE``. An iterator of those pages
              when it is ``ITERATOR``. A value typed only as ``PaginationType`` is the union of both.
        """
        return self._get_paginated_marketdata(
            path=f"/options/trades",
            params=request_params.to_request_fields(),
            page_size=10_000,
            set_type=TradeSet,
            handle_pagination=handle_pagination,
        )

    def get_option_snapshot(
        self, request_params: OptionSnapshotRequest
    ) -> Union[Dict[str, OptionsSnapshot], RawData]:
        """Returns snapshots of queried symbols. OptionsSnapshot contain latest trade,
        latest quote, implied volatility, and greeks for the queried symbols.

        Args:
            request_params (OptionSnapshotRequest): The request object for retrieving snapshot data.

        Returns:
            Union[Dict[str, OptionsSnapshot], RawData]: The snapshot data either in raw or wrapped form
        """
        raw_snapshots = self._get_marketdata(
            path=f"/options/snapshots",
            params=request_params.to_request_fields(),
            page_limit=1000,
            page_size=1000,
        )

        if self._use_raw_data:
            return raw_snapshots

        return parse_obj_as_symbol_dict(OptionsSnapshot, raw_snapshots)

    def get_option_chain(
        self, request_params: OptionChainRequest
    ) -> Union[Dict[str, OptionsSnapshot], RawData]:
        """The option chain endpoint for underlying symbol provides the latest trade, latest quote,
        implied volatility, and greeks for each contract symbol of the underlying symbol.

        Args:
            request_params (OptionChainRequest): The request object for retrieving snapshot data.

        Returns:
            Union[Dict[str, OptionsSnapshot], RawData]: The snapshot data either in raw or wrapped form
        """

        params = request_params.to_request_fields()
        del params["underlying_symbol"]

        raw_snapshots = self._get_marketdata(
            path=f"/options/snapshots/{request_params.underlying_symbol}",
            params=params,
            page_limit=1000,
            page_size=1000,
        )

        if self._use_raw_data:
            return raw_snapshots

        return parse_obj_as_symbol_dict(OptionsSnapshot, raw_snapshots)
