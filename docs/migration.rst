.. _migration:

========================================
Migration from alpaca-trade-api-python
========================================

This guide covers the minimum changes needed to migrate code from
`alpaca-trade-api-python <https://github.com/alpacahq/alpaca-trade-api-python>`_
to alpaca-py.

At a high level, alpaca-py replaces the older single-client style with
domain-specific clients, typed request models, and typed response models.
Most migrations are therefore a mechanical change from:

* one broad ``REST`` object to one or more focused clients,
* keyword arguments to request model objects, and
* string constants to enums.

Minimum migration steps
-----------------------

1. Replace the dependency
^^^^^^^^^^^^^^^^^^^^^^^^^

Remove the previous package and install alpaca-py.

.. code-block:: shell-session

    pip uninstall alpaca-trade-api
    pip install alpaca-py

If you manage dependencies in a lockfile, replace ``alpaca-trade-api`` with
``alpaca-py`` there as well.

2. Replace the client
^^^^^^^^^^^^^^^^^^^^^

The previous SDK commonly used a single ``REST`` client:

.. code-block:: python

    import alpaca_trade_api as tradeapi

    api = tradeapi.REST(API_KEY, SECRET_KEY, base_url=BASE_URL)

In alpaca-py, create the client for the API surface you are using:

.. code-block:: python

    from alpaca.trading.client import TradingClient
    from alpaca.data.historical import StockHistoricalDataClient

    trading_client = TradingClient(API_KEY, SECRET_KEY, paper=True)
    stock_data_client = StockHistoricalDataClient(API_KEY, SECRET_KEY)

Use ``paper=True`` for paper trading and ``paper=False`` for live trading.
Create data clients separately for market data requests.

Common clients
~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1

   * - Use case
     - alpaca-py client
   * - Trading API
     - ``TradingClient``
   * - Stock historical market data
     - ``StockHistoricalDataClient``
   * - Crypto historical market data
     - ``CryptoHistoricalDataClient``
   * - Option historical market data
     - ``OptionHistoricalDataClient``
   * - News
     - ``NewsClient``
   * - Broker API
     - ``BrokerClient``
   * - Stock market data stream
     - ``StockDataStream``
   * - Crypto market data stream
     - ``CryptoDataStream``
   * - Option market data stream
     - ``OptionDataStream``
   * - Trading stream
     - ``TradingStream``

3. Convert order calls to request objects
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The previous SDK accepted order fields directly as keyword arguments:

.. code-block:: python

    api.submit_order(
        symbol="SPY",
        qty=1,
        side="buy",
        type="market",
        time_in_force="day",
    )

In alpaca-py, create the correct order request model and pass it to
``TradingClient.submit_order``:

.. code-block:: python

    from alpaca.trading.client import TradingClient
    from alpaca.trading.enums import OrderSide, TimeInForce
    from alpaca.trading.requests import MarketOrderRequest

    trading_client = TradingClient(API_KEY, SECRET_KEY, paper=True)

    order = trading_client.submit_order(
        MarketOrderRequest(
            symbol="SPY",
            qty=1,
            side=OrderSide.BUY,
            time_in_force=TimeInForce.DAY,
        )
    )

Use ``LimitOrderRequest``, ``StopOrderRequest``,
``StopLimitOrderRequest``, or ``TrailingStopOrderRequest`` for other order
types.

4. Convert query parameters to request objects
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Many alpaca-py methods take a request object instead of loose keyword
arguments. For example, order filtering changes from:

.. code-block:: python

    orders = api.list_orders(status="open", limit=100)

to:

.. code-block:: python

    from alpaca.trading.enums import QueryOrderStatus
    from alpaca.trading.requests import GetOrdersRequest

    orders = trading_client.get_orders(
        GetOrdersRequest(status=QueryOrderStatus.OPEN, limit=100)
    )

The request model validates the fields before the API request is sent.

5. Convert market data calls
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Historical market data is now split by asset class. For example, stock bars
change from:

.. code-block:: python

    from alpaca_trade_api.rest import TimeFrame

    bars = api.get_bars("AAPL", TimeFrame.Day, "2024-01-01").df

to:

.. code-block:: python

    from alpaca.data.historical import StockHistoricalDataClient
    from alpaca.data.requests import StockBarsRequest
    from alpaca.data.timeframe import TimeFrame

    stock_data_client = StockHistoricalDataClient(API_KEY, SECRET_KEY)

    bars = stock_data_client.get_stock_bars(
        StockBarsRequest(
            symbol_or_symbols="AAPL",
            timeframe=TimeFrame.Day,
            start="2024-01-01",
        )
    ).df

For crypto bars, use ``CryptoHistoricalDataClient`` and
``CryptoBarsRequest``. For option bars, use ``OptionHistoricalDataClient``
and ``OptionBarsRequest``.

6. Convert streams to stream-specific clients
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Streaming clients are also split by purpose. A stock quote stream looks like
this:

.. code-block:: python

    from alpaca.data.live import StockDataStream

    stream = StockDataStream(API_KEY, SECRET_KEY)

    async def handle_quote(quote):
        print(quote)

    stream.subscribe_quotes(handle_quote, "SPY")
    stream.run()

Use ``TradingStream`` for trade updates, ``CryptoDataStream`` for crypto
market data, and ``OptionDataStream`` for option market data.

Common method mapping
---------------------

.. list-table::
   :header-rows: 1

   * - alpaca-trade-api-python
     - alpaca-py
   * - ``api.get_account()``
     - ``trading_client.get_account()``
   * - ``api.submit_order(...)``
     - ``trading_client.submit_order(OrderRequest(...))``
   * - ``api.list_orders(...)``
     - ``trading_client.get_orders(GetOrdersRequest(...))``
   * - ``api.get_order(order_id)``
     - ``trading_client.get_order_by_id(order_id)``
   * - ``api.get_order_by_client_order_id(client_order_id)``
     - ``trading_client.get_order_by_client_id(client_order_id)``
   * - ``api.cancel_all_orders()``
     - ``trading_client.cancel_orders()``
   * - ``api.cancel_order(order_id)``
     - ``trading_client.cancel_order_by_id(order_id)``
   * - ``api.list_positions()``
     - ``trading_client.get_all_positions()``
   * - ``api.get_position(symbol)``
     - ``trading_client.get_open_position(symbol)``
   * - ``api.close_all_positions()``
     - ``trading_client.close_all_positions()``
   * - ``api.close_position(symbol)``
     - ``trading_client.close_position(symbol)``
   * - ``api.list_assets(...)``
     - ``trading_client.get_all_assets(GetAssetsRequest(...))``
   * - ``api.get_asset(symbol)``
     - ``trading_client.get_asset(symbol)``
   * - ``api.get_clock()``
     - ``trading_client.get_clock()``
   * - ``api.get_calendar(...)``
     - ``trading_client.get_calendar(GetCalendarRequest(...))``
   * - ``api.get_portfolio_history(...)``
     - ``trading_client.get_portfolio_history(GetPortfolioHistoryRequest(...))``
   * - ``api.get_bars(...)``
     - ``stock_data_client.get_stock_bars(StockBarsRequest(...))``
   * - ``api.get_quotes(...)``
     - ``stock_data_client.get_stock_quotes(StockQuotesRequest(...))``
   * - ``api.get_trades(...)``
     - ``stock_data_client.get_stock_trades(StockTradesRequest(...))``

Migration notes
---------------

Request models
^^^^^^^^^^^^^^

alpaca-py uses pydantic request models. This is useful when your application
receives JSON or form input before placing orders:

.. code-block:: python

    from alpaca.trading.requests import MarketOrderRequest

    order_data = request.get_json()
    validated_order = MarketOrderRequest(**order_data)
    trading_client.submit_order(validated_order)

Enums
^^^^^

Prefer alpaca-py's enums over raw strings. For example, use
``OrderSide.BUY`` instead of ``"buy"`` and ``TimeInForce.DAY`` instead of
``"day"``.

Response models
^^^^^^^^^^^^^^^

alpaca-py returns typed models for most endpoints. Prefer attributes over
dictionary indexing:

.. code-block:: python

    account = trading_client.get_account()
    print(account.buying_power)

Market data collection responses also expose ``.df`` for conversion to a
pandas ``DataFrame``.

What alpaca-py adds
-------------------

Compared with the previous SDK, alpaca-py adds or expands support for:

* Broker API through ``BrokerClient`` for account opening, funding, account
  documents, journals, account-level trading, events, and related brokerage
  workflows.
* Option trading and option data clients, including option contracts,
  option bars, trades, quotes, snapshots, and chains.
* Separate clients for stocks, crypto, options, news, trading, broker, and
  streams.
* Pydantic request validation and typed response models.
* Asset-class specific stream clients, including stock, crypto, option, news,
  and trading streams.
* Additional API surfaces such as corporate actions, screener endpoints, and
  fixed income asset discovery where supported by Alpaca APIs.

Suggested migration order
-------------------------

For most applications, migrate in this order:

1. Replace imports and client construction.
2. Migrate account, clock, calendar, assets, and positions.
3. Migrate order submission and order management.
4. Migrate historical market data.
5. Migrate websocket streams.
6. Add tests around order request construction and any market data shape your
   strategy depends on.

This keeps the highest-risk trading behavior isolated and easier to verify.
