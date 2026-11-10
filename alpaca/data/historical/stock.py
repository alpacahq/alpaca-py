from typing import Any, Dict, Iterator, Optional, Type, Union

from pydantic import BaseModel

from alpaca.common.enums import BaseURL, PaginationType
from alpaca.common.rest import RESTClient
from alpaca.common.types import RawData
from alpaca.data import Bar, Quote, Snapshot, Trade
from alpaca.data._generated.models import (
    StockAuctionsResp,
    StockAuctionsRespSingle,
    StockBarsRespSingle,
    StockLatestBarsRespSingle,
    StockLatestQuotesRespSingle,
    StockLatestTradesRespSingle,
    StockQuotesRespSingle,
    StockSnapshotsRespSingle,
    StockTradesRespSingle,
)
from alpaca.data.historical.utils import (
    parse_obj_as_symbol_dict,
)
from alpaca.data.models import BarSet, QuoteSet, TradeSet
from alpaca.data.requests import (
    StockAuctionsForSymbolRequest,
    StockAuctionsRequest,
    StockBarsForSymbolRequest,
    StockBarsRequest,
    StockLatestBarForSymbolRequest,
    StockLatestBarRequest,
    StockLatestQuoteForSymbolRequest,
    StockLatestQuoteRequest,
    StockLatestTradeForSymbolRequest,
    StockLatestTradeRequest,
    StockQuotesForSymbolRequest,
    StockQuotesRequest,
    StockSnapshotForSymbolRequest,
    StockSnapshotRequest,
    StockTradesForSymbolRequest,
    StockTradesRequest,
)


class StockHistoricalDataClient(RESTClient):
    """
    The REST client for interacting with Alpaca Market Data API stock data endpoints.

    Learn more on https://alpaca.markets/docs/about-market-data-api
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
        self,
        request_params: StockBarsRequest,
        handle_pagination: Optional[PaginationType] = None,
    ) -> Union[BarSet, RawData, Iterator[Union[BarSet, RawData]]]:
        """Returns bar data for an equity or list of equities over a given
        time period and timeframe.

        Args:
            request_params (GetStockBarsRequest): The request object for retrieving stock bar data.
            handle_pagination (Optional[PaginationType]): How to page through the results. Defaults to
              ``PaginationType.FULL``, which fetches every page and returns one merged BarSet.
              ``PaginationType.ITERATOR`` returns a lazy iterator that fetches and yields one page at a time,
              so large queries don't have to fit in memory. ``PaginationType.NONE`` fetches only one page;
              pass its ``next_page_token`` as the request's ``page_token`` to continue.

        Returns:
            Union[BarSet, RawData, Iterator[Union[BarSet, RawData]]]: The bar data either in raw or wrapped form, or an
              iterator of pages for ``PaginationType.ITERATOR`` (raw JSON pages if raw_data is set).
        """
        return self._get_paginated_marketdata(
            path="/stocks/bars",
            params=request_params.to_request_fields(),
            page_size=10_000,
            set_type=BarSet,
            handle_pagination=handle_pagination,
        )

    def get_stock_quotes(
        self,
        request_params: StockQuotesRequest,
        handle_pagination: Optional[PaginationType] = None,
    ) -> Union[QuoteSet, RawData, Iterator[Union[QuoteSet, RawData]]]:
        """Returns level 1 quote data over a given time period for a security or list of securities.

        Args:
            request_params (GetStockQuotesRequest): The request object for retrieving stock quote data.
            handle_pagination (Optional[PaginationType]): How to page through the results. Defaults to
              ``PaginationType.FULL``, which fetches every page and returns one merged QuoteSet.
              ``PaginationType.ITERATOR`` returns a lazy iterator that fetches and yields one page at a time,
              so large queries don't have to fit in memory. ``PaginationType.NONE`` fetches only one page;
              pass its ``next_page_token`` as the request's ``page_token`` to continue.

        Returns:
            Union[QuoteSet, RawData, Iterator[Union[QuoteSet, RawData]]]: The quote data either in raw or wrapped form, or an
              iterator of pages for ``PaginationType.ITERATOR`` (raw JSON pages if raw_data is set).
        """
        return self._get_paginated_marketdata(
            path="/stocks/quotes",
            params=request_params.to_request_fields(),
            page_size=10_000,
            set_type=QuoteSet,
            handle_pagination=handle_pagination,
        )

    def get_stock_trades(
        self,
        request_params: StockTradesRequest,
        handle_pagination: Optional[PaginationType] = None,
    ) -> Union[TradeSet, RawData, Iterator[Union[TradeSet, RawData]]]:
        """Returns the price and sales history over a given time period for a security or list of securities.

        Args:
            request_params (GetStockTradesRequest): The request object for retrieving stock trade data.
            handle_pagination (Optional[PaginationType]): How to page through the results. Defaults to
              ``PaginationType.FULL``, which fetches every page and returns one merged TradeSet.
              ``PaginationType.ITERATOR`` returns a lazy iterator that fetches and yields one page at a time,
              so large queries don't have to fit in memory. ``PaginationType.NONE`` fetches only one page;
              pass its ``next_page_token`` as the request's ``page_token`` to continue.

        Returns:
            Union[TradeSet, RawData, Iterator[Union[TradeSet, RawData]]]: The trade data either in raw or wrapped form, or an
              iterator of pages for ``PaginationType.ITERATOR`` (raw JSON pages if raw_data is set).
        """
        return self._get_paginated_marketdata(
            path="/stocks/trades",
            params=request_params.to_request_fields(),
            page_size=10_000,
            set_type=TradeSet,
            handle_pagination=handle_pagination,
        )

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

    def get_stock_bars_for_symbol(
        self, request_params: StockBarsForSymbolRequest
    ) -> Union[StockBarsRespSingle, RawData]:
        """Returns bar data for one equity symbol.

        The symbol is a path parameter. Pages are not flattened: the response
        keeps ``symbol``, ``currency``, and ``next_page_token``. Pass that token
        back as ``page_token`` to read the next page.

        Args:
            request_params (StockBarsForSymbolRequest): The request object for retrieving stock bar data.

        Returns:
            Union[StockBarsRespSingle, RawData]: The bar page, either wrapped or as the JSON object the server sent.
        """
        return self._get_envelope(
            model=StockBarsRespSingle,
            path=f"/stocks/{request_params.symbol}/bars",
            params=request_params.to_request_fields(),
        )

    def get_stock_quotes_for_symbol(
        self, request_params: StockQuotesForSymbolRequest
    ) -> Union[StockQuotesRespSingle, RawData]:
        """Returns quote data for one equity symbol.

        Args:
            request_params (StockQuotesForSymbolRequest): The request object for retrieving stock quote data.

        Returns:
            Union[StockQuotesRespSingle, RawData]: The quote page, either wrapped or as the JSON object the server sent.
        """
        return self._get_envelope(
            model=StockQuotesRespSingle,
            path=f"/stocks/{request_params.symbol}/quotes",
            params=request_params.to_request_fields(),
        )

    def get_stock_trades_for_symbol(
        self, request_params: StockTradesForSymbolRequest
    ) -> Union[StockTradesRespSingle, RawData]:
        """Returns trade data for one equity symbol.

        Args:
            request_params (StockTradesForSymbolRequest): The request object for retrieving stock trade data.

        Returns:
            Union[StockTradesRespSingle, RawData]: The trade page, either wrapped or as the JSON object the server sent.
        """
        return self._get_envelope(
            model=StockTradesRespSingle,
            path=f"/stocks/{request_params.symbol}/trades",
            params=request_params.to_request_fields(),
        )

    def get_stock_latest_bar_for_symbol(
        self, request_params: StockLatestBarForSymbolRequest
    ) -> Union[StockLatestBarsRespSingle, RawData]:
        """Returns the latest minute bar for one equity symbol.

        Args:
            request_params (StockLatestBarForSymbolRequest): The request object for retrieving the latest bar.

        Returns:
            Union[StockLatestBarsRespSingle, RawData]: The latest bar envelope. The bar is the ``bar`` field.
        """
        return self._get_envelope(
            model=StockLatestBarsRespSingle,
            path=f"/stocks/{request_params.symbol}/bars/latest",
            params=request_params.to_request_fields(),
        )

    def get_stock_latest_quote_for_symbol(
        self, request_params: StockLatestQuoteForSymbolRequest
    ) -> Union[StockLatestQuotesRespSingle, RawData]:
        """Returns the latest quote for one equity symbol.

        Args:
            request_params (StockLatestQuoteForSymbolRequest): The request object for retrieving the latest quote.

        Returns:
            Union[StockLatestQuotesRespSingle, RawData]: The latest quote envelope.
        """
        return self._get_envelope(
            model=StockLatestQuotesRespSingle,
            path=f"/stocks/{request_params.symbol}/quotes/latest",
            params=request_params.to_request_fields(),
        )

    def get_stock_latest_trade_for_symbol(
        self, request_params: StockLatestTradeForSymbolRequest
    ) -> Union[StockLatestTradesRespSingle, RawData]:
        """Returns the latest trade for one equity symbol.

        Args:
            request_params (StockLatestTradeForSymbolRequest): The request object for retrieving the latest trade.

        Returns:
            Union[StockLatestTradesRespSingle, RawData]: The latest trade envelope.
        """
        return self._get_envelope(
            model=StockLatestTradesRespSingle,
            path=f"/stocks/{request_params.symbol}/trades/latest",
            params=request_params.to_request_fields(),
        )

    def get_stock_snapshot_for_symbol(
        self, request_params: StockSnapshotForSymbolRequest
    ) -> Union[StockSnapshotsRespSingle, RawData]:
        """Returns the latest snapshot for one equity symbol.

        Args:
            request_params (StockSnapshotForSymbolRequest): The request object for retrieving the snapshot.

        Returns:
            Union[StockSnapshotsRespSingle, RawData]: The snapshot envelope.
        """
        return self._get_envelope(
            model=StockSnapshotsRespSingle,
            path=f"/stocks/{request_params.symbol}/snapshot",
            params=request_params.to_request_fields(),
        )

    def get_stock_auctions(
        self, request_params: StockAuctionsRequest
    ) -> Union[StockAuctionsResp, RawData]:
        """Returns auction prices for a list of equity symbols.

        Args:
            request_params (StockAuctionsRequest): The request object for retrieving auction data.

        Returns:
            Union[StockAuctionsResp, RawData]: Auctions keyed by symbol, plus ``currency`` and ``next_page_token``.
        """
        return self._get_envelope(
            model=StockAuctionsResp,
            path="/stocks/auctions",
            params=request_params.to_request_fields(),
        )

    def get_stock_auctions_for_symbol(
        self, request_params: StockAuctionsForSymbolRequest
    ) -> Union[StockAuctionsRespSingle, RawData]:
        """Returns auction prices for one equity symbol.

        Args:
            request_params (StockAuctionsForSymbolRequest): The request object for retrieving auction data.

        Returns:
            Union[StockAuctionsRespSingle, RawData]: The auction page for the path symbol.
        """
        return self._get_envelope(
            model=StockAuctionsRespSingle,
            path=f"/stocks/{request_params.symbol}/auctions",
            params=request_params.to_request_fields(),
        )

    def get_stock_condition_codes(self, ticktype: str, tape: str) -> RawData:
        """Returns the mapping between condition codes and names for one tape.

        Args:
            ticktype (str): ``trade`` or ``quote``.
            tape (str): One-character tape name: ``A``, ``B``, or ``C``.

        Returns:
            RawData: Condition code map.
        """
        return self.get(
            path=f"/stocks/meta/conditions/{ticktype}",
            data={"tape": tape},
        )

    def get_stock_exchange_codes(self) -> RawData:
        """Returns the mapping between stock exchange codes and exchange names.

        Returns:
            RawData: Exchange code map.
        """
        return self.get(path="/stocks/meta/exchanges")

    def _get_envelope(
        self,
        model: Type[BaseModel],
        path: str,
        params: Dict[str, Any],
    ) -> Union[BaseModel, RawData]:
        """GET one market-data page and keep the response envelope intact."""
        raw = self.get(path=path, data=params)
        if self._use_raw_data:
            return raw
        return model.model_validate(raw)
