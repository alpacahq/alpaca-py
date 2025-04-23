from collections import defaultdict
from enum import Enum
from typing import Dict, List, Optional, Union

from alpaca.common.constants import DATA_V2_MAX_LIMIT
from alpaca.common.enums import BaseURL
from alpaca.common.rest import RESTClient
from alpaca.common.types import RawData
from alpaca.data import Bar, Quote, Snapshot, Trade
from alpaca.data.historical.utils import (
    parse_obj_as_symbol_dict,
)
from alpaca.data.models import BarSet, QuoteSet, TradeSet
from alpaca.data.requests import (
    StockBarsRequest,
    StockLatestBarRequest,
    StockLatestQuoteRequest,
    StockLatestTradeRequest,
    StockQuotesRequest,
    StockSnapshotRequest,
    StockTradesRequest,
)


class StockHistoricalDataClient(RESTClient):
    """
    The REST client for interacting with Alpaca Market Data API stock data endpoints.

    Learn more on https://alpaca.markets/docs/market-data/
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
            api_version="v2",
            base_url=base_url,
            sandbox=sandbox,
            raw_data=raw_data,
        )

    def get_stock_bars(
        self, request_params: StockBarsRequest
    ) -> Union[BarSet, RawData]:
        """Returns bar data for an equity or list of equities over a given
        time period and timeframe.

        Args:
            request_params (GetStockBarsRequest): The request object for retrieving stock bar data.

        Returns:
            Union[BarSet, RawData]: The bar data either in raw or wrapped form
        """
        raw_bars = self._get_marketdata(
            path="/stocks/bars",
            params=request_params.to_request_fields(),
            page_size=10_000,
        )

        if self._use_raw_data:
            return raw_bars

        return BarSet(raw_bars)

    def get_stock_quotes(
        self, request_params: StockQuotesRequest
    ) -> Union[QuoteSet, RawData]:
        """Returns level 1 quote data over a given time period for a security or list of securities.

        Args:
            request_params (GetStockQuotesRequest): The request object for retrieving stock quote data.

        Returns:
            Union[QuoteSet, RawData]: The quote data either in raw or wrapped form
        """
        raw_quotes = self._get_marketdata(
            path="/stocks/quotes",
            params=request_params.to_request_fields(),
            page_size=10_000,
        )

        if self._use_raw_data:
            return raw_quotes

        return QuoteSet(raw_quotes)

    def get_stock_trades(
        self, request_params: StockTradesRequest
    ) -> Union[TradeSet, RawData]:
        """Returns the price and sales history over a given time period for a security or list of securities.

        Args:
            request_params (GetStockTradesRequest): The request object for retrieving stock trade data.

        Returns:
            Union[TradeSet, RawData]: The trade data either in raw or wrapped form
        """
        raw_trades = self._get_marketdata(
            path="/stocks/trades",
            params=request_params.to_request_fields(),
            page_size=10_000,
        )

        if self._use_raw_data:
            return raw_trades

        return TradeSet(raw_trades)

    def get_stock_latest_trade(
        self, request_params: StockLatestTradeRequest
    ) -> Union[Dict[str, Trade], RawData]:
        """Retrieves the latest trade for an equity symbol or list of equities.

        Args:
            request_params (StockLatestTradeRequest): The request object for retrieving the latest trade data.

        Returns:
            Union[Dict[str, Trade], RawData]: The latest trade in raw or wrapped format
        """
        raw_latest_trades = self._get_marketdata(
            path="/stocks/trades/latest",
            params=request_params.to_request_fields(),
        )

        if self._use_raw_data:
            return raw_latest_trades

        return parse_obj_as_symbol_dict(Trade, raw_latest_trades)

    def get_stock_latest_quote(
        self, request_params: StockLatestQuoteRequest
    ) -> Union[Dict[str, Quote], RawData]:
        """Retrieves the latest quote for an equity symbol or list of equity symbols.

        Args:
            request_params (StockLatestQuoteRequest): The request object for retrieving the latest quote data.

        Returns:
            Union[Dict[str, Quote], RawData]: The latest quote in raw or wrapped format
        """
        raw_latest_quotes = self._get_marketdata(
            path="/stocks/quotes/latest",
            params=request_params.to_request_fields(),
        )

        if self._use_raw_data:
            return raw_latest_quotes

        return parse_obj_as_symbol_dict(Quote, raw_latest_quotes)

    def get_stock_latest_bar(
        self, request_params: StockLatestBarRequest
    ) -> Union[Dict[str, Bar], RawData]:
        """Retrieves the latest minute bar for an equity symbol or list of equity symbols.

        Args:
            request_params (StockLatestBarRequest): The request object for retrieving the latest bar data.

        Returns:
            Union[Dict[str, Bar], RawData]: The latest minute bar in raw or wrapped format
        """
        raw_latest_bars = self._get_marketdata(
            path="/stocks/bars/latest",
            params=request_params.to_request_fields(),
        )

        if self._use_raw_data:
            return raw_latest_bars

        return parse_obj_as_symbol_dict(Bar, raw_latest_bars)

    def get_stock_snapshot(
        self, request_params: StockSnapshotRequest
    ) -> Union[Dict[str, Snapshot], RawData]:
        """Returns snapshots of queried symbols. Snapshots contain latest trade, latest quote, latest minute bar,
        latest daily bar and previous daily bar data for the queried symbols.

        Args:
            request_params (StockSnapshotRequest): The request object for retrieving snapshot data.

        Returns:
            Union[SnapshotSet, RawData]: The snapshot data either in raw or wrapped form
        """
        raw_snapshots = self._get_marketdata(
            path="/stocks/snapshots",
            params=request_params.to_request_fields(),
            no_sub_key=True,
        )

        if self._use_raw_data:
            return raw_snapshots

        return parse_obj_as_symbol_dict(Snapshot, raw_snapshots)
