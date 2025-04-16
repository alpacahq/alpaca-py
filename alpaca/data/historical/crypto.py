from typing import Dict, Optional, Union

from alpaca.common.enums import BaseURL
from alpaca.common.rest import RESTClient
from alpaca.common.types import Credentials, RawData
from alpaca.data import Bar, Snapshot
from alpaca.data.enums import CryptoFeed
from alpaca.data.historical.utils import (
    parse_obj_as_symbol_dict,
)
from alpaca.data.models import BarSet, Orderbook, Quote, QuoteSet, Trade, TradeSet
from alpaca.data.requests import (
    CryptoBarsRequest,
    CryptoLatestBarRequest,
    CryptoLatestOrderbookRequest,
    CryptoLatestQuoteRequest,
    CryptoLatestTradeRequest,
    CryptoQuoteRequest,
    CryptoSnapshotRequest,
    CryptoTradesRequest,
)


class CryptoHistoricalDataClient(RESTClient):
    """
    A REST client for retrieving crypto market data.

    This client does not need any authentication to use.
    You can instantiate it with or without API keys.

    However, authenticating increases your data rate limit.

    Learn more about crypto historical data here:
    https://alpaca.markets/docs/api-references/market-data-api/crypto-pricing-data/historical/
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        oauth_token: Optional[str] = None,
        raw_data: bool = False,
        url_override: Optional[str] = None,
        use_basic_auth: bool = False,
        sandbox: bool = False,
    ) -> None:
        """
        Instantiates a Historical Data Client for Crypto Data.

        Args:
            api_key (Optional[str], optional): Alpaca API key. Defaults to None.
            secret_key (Optional[str], optional): Alpaca API secret key. Defaults to None.
            oauth_token (Optional[str]): The oauth token if authenticating via OAuth. Defaults to None.
            raw_data (bool, optional): If true, API responses will not be wrapped and raw responses will be returned from
              methods. Defaults to False. This has not been implemented yet.
            url_override (Optional[str], optional): If specified allows you to override the base url the client points
              to for proxy/testing.
            use_basic_auth (bool, optional): If true, API requests will use basic authorization headers. Set to true if using
              broker api sandbox credentials
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
            api_version="v1beta3",
            base_url=base_url,
            sandbox=sandbox,
            raw_data=raw_data,
            use_basic_auth=use_basic_auth,
        )

    def get_crypto_bars(
        self, request_params: CryptoBarsRequest, feed: CryptoFeed = CryptoFeed.US
    ) -> Union[BarSet, RawData]:
        """Gets bar/candle data for a cryptocurrency or list of cryptocurrencies.

        Args:
            request_params (CryptoBarsRequest): The parameters for the request.
            feed (CryptoFeed): The data feed for crypto bars.

        Returns:
            Union[BarSet, RawData]: The crypto bar data either in raw or wrapped form
        """

        # paginated get request for crypto market data api
        raw_bars = self._get_marketdata(
            path=f"/crypto/{feed.value}/bars",
            params=request_params.to_request_fields(),
            page_size=10_000,
        )

        if self._use_raw_data:
            return raw_bars

        return BarSet(raw_bars)

    def get_crypto_quotes(
        self, request_params: CryptoQuoteRequest, feed: CryptoFeed = CryptoFeed.US
    ) -> Union[QuoteSet, RawData]:
        """Returns the quote data for a cryptocurrency or list of cryptocurrencies.

        Args:
            request_params (CryptoQuoteRequest): The parameters for the request.
            feed (CryptoFeed): The data feed for crypto quotes.

        Returns:
            Union[QuoteSet, RawData]: The crypto quote data either in raw or wrapped form
        """

        # paginated get request for market data api
        raw_quotes = self._get_marketdata(
            path=f"/crypto/{feed.value}/quotes",
            params=request_params.to_request_fields(),
            page_size=10_000,
        )

        if self._use_raw_data:
            return raw_quotes

        return QuoteSet(raw_quotes)

    def get_crypto_trades(
        self, request_params: CryptoTradesRequest, feed: CryptoFeed = CryptoFeed.US
    ) -> Union[TradeSet, RawData]:
        """Returns the price and sales history over a given time period for a cryptocurrency
        or list of cryptocurrencies.

        Args:
            request_params (CryptoTradesRequest): The parameters for the request.
            feed (CryptoFeed): The data feed for crypto trades.

        Returns:
            Union[TradeSet, RawData]: The trade data either in raw or wrapped form
        """

        # paginated get request for market data api
        raw_trades = self._get_marketdata(
            path=f"/crypto/{feed.value}/trades",
            params=request_params.to_request_fields(),
            page_size=10_000,
        )

        if self._use_raw_data:
            return raw_trades

        return TradeSet(raw_trades)

    def get_crypto_latest_trade(
        self, request_params: CryptoLatestTradeRequest, feed: CryptoFeed = CryptoFeed.US
    ) -> Union[Dict[str, Trade], RawData]:
        """Returns the latest trade for a coin.

        Args:
            request_params (CryptoLatestTradeRequest): The parameters for the request.
            feed (CryptoFeed): The data feed for the latest crypto trade.

        Returns:
            Union[Dict[str, Trade], RawData]: The latest trade in raw or wrapped format
        """

        raw_trades = self._get_marketdata(
            path=f"/crypto/{feed.value}/latest/trades",
            params=request_params.to_request_fields(),
        )

        if self._use_raw_data:
            return raw_trades

        return parse_obj_as_symbol_dict(Trade, raw_trades)

    def get_crypto_latest_quote(
        self, request_params: CryptoLatestQuoteRequest, feed: CryptoFeed = CryptoFeed.US
    ) -> Union[Dict[str, Quote], RawData]:
        """Returns the latest quote for a coin.

        Args:
            request_params (CryptoLatestQuoteRequest): The parameters for the request.
            feed (CryptoFeed): The data feed for the latest crypto quote.

        Returns:
            Union[Dict[str, Quote], RawData]: The latest quote in raw or wrapped format
        """

        raw_quotes = self._get_marketdata(
            path=f"/crypto/{feed.value}/latest/quotes",
            params=request_params.to_request_fields(),
        )

        if self._use_raw_data:
            return raw_quotes

        return parse_obj_as_symbol_dict(Quote, raw_quotes)

    def get_crypto_latest_bar(
        self, request_params: CryptoLatestBarRequest, feed: CryptoFeed = CryptoFeed.US
    ) -> Union[Dict[str, Bar], RawData]:
        """Returns the latest minute bar for a coin.

        Args:
            request_params (CryptoLatestBarRequest): The parameters for the request.
            feed (CryptoFeed): The data feed for the latest crypto bar.

        Returns:
            Union[Dict[str, Bar], RawData]: The latest bar in raw or wrapped format
        """

        raw_bars = self._get_marketdata(
            path=f"/crypto/{feed.value}/latest/bars",
            params=request_params.to_request_fields(),
        )

        if self._use_raw_data:
            return raw_bars

        return parse_obj_as_symbol_dict(Bar, raw_bars)

    def get_crypto_latest_orderbook(
        self,
        request_params: CryptoLatestOrderbookRequest,
        feed: CryptoFeed = CryptoFeed.US,
    ) -> Union[Dict[str, Orderbook], RawData]:
        """
        Returns the latest orderbook state for the queried crypto symbols.

        Args:
            request_params (CryptoOrderbookRequest): The parameters for the orderbook request.
            feed (CryptoFeed): The data feed for the latest crypto orderbook.

        Returns:
            Union[Dict[str, Orderbook], RawData]: The orderbook data either in raw or wrapped form.
        """

        raw_orderbooks = self._get_marketdata(
            path=f"/crypto/{feed.value}/latest/orderbooks",
            params=request_params.to_request_fields(),
        )

        if self._use_raw_data:
            return raw_orderbooks

        return parse_obj_as_symbol_dict(Orderbook, raw_orderbooks)

    def get_crypto_snapshot(
        self, request_params: CryptoSnapshotRequest, feed: CryptoFeed = CryptoFeed.US
    ) -> Union[Snapshot, RawData]:
        """Returns snapshots of queried crypto symbols. Snapshots contain latest trade, latest quote, latest minute bar,
        latest daily bar and previous daily bar data for the queried symbols.

        Args:
            request_params (CryptoSnapshotRequest): The parameters for the snapshot request.
            feed (CryptoFeed): The data feed for crypto snapshots.

        Returns:
            Union[SnapshotSet, RawData]: The snapshot data either in raw or wrapped form
        """

        raw_snapshots = self._get_marketdata(
            path=f"/crypto/{feed.value}/snapshots",
            params=request_params.to_request_fields(),
        )

        if self._use_raw_data:
            return raw_snapshots

        return parse_obj_as_symbol_dict(Snapshot, raw_snapshots)

    # We override the _validate_credentials static method for crypto,
    # because crypto does not actually require authentication.
    @staticmethod
    def _validate_credentials(
        api_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        oauth_token: Optional[str] = None,
    ) -> Credentials:
        """Gathers API credentials from parameters and environment variables, and validates them.
        Args:
            api_key (Optional[str]): The API key for authentication. Defaults to None.
            secret_key (Optional[str]): The secret key for authentication. Defaults to None.
            oauth_token (Optional[str]): The oauth token if authenticating via OAuth. Defaults to None.
        Raises:
             ValueError: If the combination of keys and tokens provided are not valid.
        Returns:
            Credentials: The set of validated authentication keys
        """

        if oauth_token and (api_key or secret_key):
            raise ValueError(
                "Either an oauth_token or an api_key may be supplied, but not both"
            )

        return api_key, secret_key, oauth_token
