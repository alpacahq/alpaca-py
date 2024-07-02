import asyncio
from typing import Awaitable, Callable, Dict, Optional, Union

from alpaca.common.enums import BaseURL
from alpaca.data.enums import DataFeed
from alpaca.data.live.websocket import DataStream
from alpaca.data.models.bars import Bar
from alpaca.data.models.quotes import Quote
from alpaca.data.models.trades import Trade, TradeCancel, TradeCorrection, TradingStatus


class StockDataStream(DataStream):
    """
    A WebSocket client for streaming live stock data.
    """

    def __init__(
        self,
        api_key: str,
        secret_key: str,
        raw_data: bool = False,
        feed: DataFeed = DataFeed.IEX,
        websocket_params: Optional[Dict] = None,
        url_override: Optional[str] = None,
    ) -> None:
        """
        Instantiates a WebSocket client for accessing live stock data.

        Args:
            api_key (str): Alpaca API key.
            secret_key (str): Alpaca API secret key.
            raw_data (bool, optional): Whether to return wrapped data or raw API data. Defaults to False.
            feed (DataFeed, optional): Which market data feed to use; IEX or SIP.
                Defaults to IEX. SIP requires a subscription.
            websocket_params (Optional[Dict], optional): Any parameters for configuring websocket connection. Defaults to None.
            url_override (Optional[str]): If specified allows you to override the base url the client
                points to for proxy/testing. Defaults to None.

        Raises:
            ValueError: Only IEX or SIP market data feeds are supported
        """
        if feed not in (DataFeed.IEX, DataFeed.SIP):
            raise ValueError("only IEX and SIP feeds ar supported")

        super().__init__(
            endpoint=(
                url_override
                if url_override is not None
                else BaseURL.MARKET_DATA_STREAM.value + "/v2/" + feed.value
            ),
            api_key=api_key,
            secret_key=secret_key,
            raw_data=raw_data,
            websocket_params=websocket_params,
        )

    def subscribe_trades(
        self, handler: Callable[[Union[Trade, Dict]], Awaitable[None]], *symbols: str
    ) -> None:
        """Subscribe to trades.

        Args:
            handler (Callable[[Union[Trade, Dict]], Awaitable[None]]): The coroutine callback
                function to handle the incoming data.
            *symbols: List of ticker symbols to subscribe to. "*" for everything.
        """
        self._subscribe(handler, symbols, self._handlers["trades"])

    def subscribe_quotes(
        self, handler: Callable[[Union[Quote, Dict]], Awaitable[None]], *symbols: str
    ) -> None:
        """Subscribe to quotes

        Args:
            handler (Callable[[Union[Trade, Dict]], Awaitable[None]]): The coroutine callback
                function to handle the incoming data.
            *symbols: List of ticker symbols to subscribe to. "*" for everything.
        """
        self._subscribe(handler, symbols, self._handlers["quotes"])

    def subscribe_bars(
        self, handler: Callable[[Union[Bar, Dict]], Awaitable[None]], *symbols: str
    ) -> None:
        """Subscribe to minute bars

        Args:
            handler (Callable[[Union[Trade, Dict]], Awaitable[None]]): The coroutine callback
                function to handle the incoming data.
            *symbols: List of ticker symbols to subscribe to. "*" for everything.
        """
        self._subscribe(handler, symbols, self._handlers["bars"])

    def subscribe_updated_bars(
        self, handler: Callable[[Union[Bar, Dict]], Awaitable[None]], *symbols: str
    ) -> None:
        """Subscribe to updated minute bars

        Args:
            handler (Callable[[Union[Bar, Dict]], Awaitable[None]]): The coroutine callback
                function to handle the incoming data.
            *symbols: List of ticker symbols to subscribe to. "*" for everything.
        """
        self._subscribe(handler, symbols, self._handlers["updatedBars"])

    def subscribe_daily_bars(
        self, handler: Callable[[Union[Bar, Dict]], Awaitable[None]], *symbols: str
    ) -> None:
        """Subscribe to daily bars

        Args:
            handler (Callable[[Union[Bar, Dict]], Awaitable[None]]): The coroutine callback
                function to handle the incoming data.
            *symbols: List of ticker symbols to subscribe to. "*" for everything.
        """
        self._subscribe(handler, symbols, self._handlers["dailyBars"])

    def subscribe_trading_statuses(
        self, handler: Callable[[Union[TradingStatus, Dict]], Awaitable[None]], *symbols
    ) -> None:
        """Subscribe to trading statuses (halts, resumes)

        Args:
            handler (Callable[[Union[TradingStatus, Dict]], Awaitable[None]]): The coroutine callback
                function to handle the incoming data.
            *symbols: List of ticker symbols to subscribe to. "*" for everything.
        """
        self._subscribe(handler, symbols, self._handlers["statuses"])

    def register_trade_corrections(
        self, handler: Callable[[Union[TradeCorrection, Dict]], Awaitable[None]]
    ) -> None:
        """Register a trade correction handler. You can only subscribe to trade corrections by
        subscribing to the underlying trades.

        Args:
            handler (Callable[[Union[TradeCorrection, Dict]]): The coroutine callback
                function to handle the incoming data.
        """
        self._handlers["corrections"] = {"*": handler}

    def register_trade_cancels(
        self, handler: Callable[[Union[TradeCancel, Dict]], Awaitable[None]]
    ) -> None:
        """Register a trade cancel handler. You can only subscribe to trade cancels by
        subscribing to the underlying trades.

        Args:
            handler (Callable[[Union[TradeCancel, Dict]], Awaitable[None]]): The coroutine callback
                function to handle the incoming data.
        """
        self._handlers["cancelErrors"] = {"*": handler}

    def unsubscribe_trades(self, *symbols: str) -> None:
        """Unsubscribe from trades

        Args:
            *symbols (str): List of ticker symbols to unsubscribe from. "*" for everything.
        """
        self._unsubscribe("trades", symbols)

    def unsubscribe_quotes(self, *symbols: str) -> None:
        """Unsubscribe from quotes

        Args:
            *symbols (str): List of ticker symbols to unsubscribe from. "*" for everything.
        """
        self._unsubscribe("quotes", symbols)

    def unsubscribe_bars(self, *symbols: str) -> None:
        """Unsubscribe from minute bars

        Args:
            *symbols (str): List of ticker symbols to unsubscribe from. "*" for everything.
        """
        self._unsubscribe("bars", symbols)

    def unsubscribe_updated_bars(self, *symbols: str) -> None:
        """Unsubscribe from updated bars

        Args:
            *symbols (str): List of ticker symbols to unsubscribe from. "*" for everything.
        """
        self._unsubscribe("updatedBars", symbols)

    def unsubscribe_daily_bars(self, *symbols: str) -> None:
        """Unsubscribe from daily bars

        Args:
            *symbols (str): List of ticker symbols to unsubscribe from. "*" for everything.
        """
        self._unsubscribe("dailyBars", symbols)

    def unsubscribe_trading_statuses(self, *symbols: str) -> None:
        """Unsubscribe from trading statuses

        Args:
            *symbols (str): List of ticker symbols to unsubscribe from. "*" for everything.
        """
        self._unsubscribe("statuses", symbols)
