.. _trading:

=======
Trading
=======

Alpaca offers brokerage services for equities and crypto. Equity trading is commission free while
crypto trading fees are tiered. Alpaca-py allows you to place orders and manage your positions on your Alpaca brokerage account.

Paper Trading
-------------

Alpaca offers a paper trading sandbox environment so you can test out the API or paper trade your strategy
before you go live. The paper trading environment is free to use. You can learn more about paper trading
on the `Alpaca API documentation <https://alpaca.markets/docs/trading/paper-trading/>`_.

To use paper trading, you will need to set the `paper` parameter to `True` when instantiating the
`TradingClient`. Make sure the keys you are providing correspond to a paper account.

.. code-block:: python

    from alpaca.trading.client import TradingClient

    # paper=True enables paper trading
    trading_client = TradingClient('api-key', 'secret-key', paper=True)

Retrieving Account Details
--------------------------

You can access details about your brokerage account like how much buying power you have,
whether you've been flagged by as a pattern day trader, your total equity.

.. code-block:: python

    from alpaca.trading.client import TradingClient

    trading_client = TradingClient('api-key', 'secret-key')

    account = trading_client.get_account()


Assets
------

The assets API serves a list of assets available on Alpaca for trading and data consumption.
It is important to note that not all assets are tradable on Alpaca, and those assets will be marked
with ``tradable=False``. To learn more about Assets, visit the `Alpaca API documentation <https://alpaca.markets/docs/api-references/trading-api/assets/>`__.

Getting All Assets
^^^^^^^^^^^^^^^^^^

Retrieves a list of assets that matches the search parameters. If there is not any search parameters
provided, a list of all available assets will be returned. Search parameters for assets are defined by the
``GetAssetsRequest`` model, which allows filtering by ``AssetStatus``, ``AssetClass``, and ``AssetExchange``.

.. code-block:: python

    from alpaca.trading.client import TradingClient
    from alpaca.trading.requests import GetAssetsRequest
    from alpaca.trading.enums import AssetClass

    trading_client = TradingClient('api-key', 'secret-key')

    # search for crypto assets
    search_params = GetAssetsRequest(asset_class=AssetClass.CRYPTO)

    assets = trading_client.get_all_assets(search_params)


Orders
------

The orders API allows you to submit orders and then manage those orders. You can customize
your order with various order types, order time in forces or by creating multi-leg orders.
To learn more about orders, visit the `Alpaca API documentation <https://alpaca.markets/docs/trading/orders/>`__.

Creating an Order
^^^^^^^^^^^^^^^^^

To create on order on Alpaca-py you must use an ``OrderRequest`` object. There are different
``OrderRequest`` objects based on the type of order you want to make. For market orders, there is
``MarketOrderRequest``, limit orders have ``LimitOrderRequest``, stop orders ``StopOrderRequest``, and
trailing stop orders have ``TrailingStopOrderRequest``. Each order type have their own required parameters
for a successful order.

.. hint::
    For stocks, the notional parameter can only be used with Market orders.
    For crypto, the notional parameter can be used with any order type.

**Market Order**

A market order is an order to buy or sell a stock at the best available price. Generally,
this type of order will be executed immediately. However, the price at which a market order will be executed is not guaranteed.

Market orders allow the trade of fractional shares for stocks. Fractional shares must be denoted either with
a non-integer ``qty`` value or with the use of the ``notional`` parameter.
The ``notional`` parameter allows you to denote the amount you wish to trade in units of the quote currency.
For example, instead of trading 1 share of SPY, we can trade $200 of SPY. ``notional`` orders are inherently
fractional orders.

.. code-block:: python

    from alpaca.trading.client import TradingClient
    from alpaca.trading.requests import MarketOrderRequest
    from alpaca.trading.enums import OrderSide, TimeInForce

    trading_client = TradingClient('api-key', 'secret-key', paper=True)

    # preparing orders
    market_order_data = MarketOrderRequest(
                        symbol="SPY",
                        qty=0.023,
                        side=OrderSide.BUY,
                        time_in_force=TimeInForce.DAY
                        )

    # Market order
    market_order = trading_client.submit_order(
                    order_data=market_order_data
                   )

**Limit Order**

A limit order is an order to buy or sell a stock at a specific price or better. You can
use the ``LimitOrderRequest`` model to prepare your order details.

.. code-block:: python

    from alpaca.trading.client import TradingClient
    from alpaca.trading.requests import LimitOrderRequest
    from alpaca.trading.enums import OrderSide, TimeInForce

    trading_client = TradingClient('api-key', 'secret-key', paper=True)


    limit_order_data = LimitOrderRequest(
                        symbol="BTC/USD",
                        limit_price=17000,
                        notional=4000,
                        side=OrderSide.SELL,
                        time_in_force=TimeInForce.FOK
                       )

    # Limit order
    limit_order = trading_client.submit_order(
                    order_data=limit_order_data
                  )


Getting All Orders
^^^^^^^^^^^^^^^^^^

We can query all the orders associated with our account. It is possible to narrow
the query by passing in parameters through the ``GetOrdersRequest`` model.

.. code-block:: python

    from alpaca.trading.client import TradingClient
    from alpaca.trading.requests import GetOrdersRequest
    from alpaca.trading.enums import OrderSide, QueryOrderStatus

    trading_client = TradingClient('api-key', 'secret-key', paper=True)

    # params to filter orders by
    request_params = GetOrdersRequest(
                        status=QueryOrderStatus.OPEN,
                        side=OrderSide.SELL
                     )

    # orders that satisfy params
    orders = trading_client.get_orders(filter=request_params)


Cancel All Orders
^^^^^^^^^^^^^^^^^

We can attempt to cancel all open orders with this method. The method takes no parameters and returns a list
of ``CancelOrderResponse`` objects. The cancellation of an order is not guaranteed. The ``CancelOrderResponse`` objects
contain information about the cancel status of each attempted order cancellation.

.. code-block:: python

    from alpaca.trading.client import TradingClient

    trading_client = TradingClient('api-key', 'secret-key', paper=True)

    # attempt to cancel all open orders
    cancel_statuses = trading_client.cancel_orders()

Positions
---------

The positions endpoints lets you track and manage open positions in your portfolio.
Learn more about the positions endpoints in the `API docs <https://alpaca.markets/docs/api-references/trading-api/positions/>`_.

Getting All Positions
^^^^^^^^^^^^^^^^^^^^^

This method requires no parameters and returns all open positions in your portfolio. It will
return a list of ``Position`` objects.

.. code-block:: python

    from alpaca.trading.client import TradingClient

    trading_client = TradingClient('api-key', 'secret-key')

    trading_client.get_all_positions()



Close All Positions
^^^^^^^^^^^^^^^^^^^

This method closes all your open positions. If you set the ``cancel_orders`` parameter to ``True``,
the method will also cancel all open orders, preventing you from entering into a new position.

.. code-block:: python

    from alpaca.trading.client import TradingClient

    trading_client = TradingClient('api-key', 'secret-key')

    # closes all position AND also cancels all open orders
    trading_client.close_all_positions(cancel_orders=True)


Streaming Trade Updates
-----------------------

There is also a ``TradingStream`` websocket client which allows you to stream order updates.
Whenever an order is submitted, filled, cancelled, etc, you will receive a response on the client.

You can learn more on the `API documentation <https://alpaca.markets/docs/api-references/trading-api/streaming/>`_

Here is an example

.. code-block:: python

    from alpaca.trading.stream import TradingStream

    trading_stream = TradingStream('api-key', 'secret-key', paper=True)

    async def update_handler(data):
        # trade updates will arrive in our async handler
        print(data)

    # subscribe to trade updates and supply the handler as a parameter
    trading_stream.subscribe_trade_updates(update_handler)

    # start our websocket streaming
    trading_stream.run()
