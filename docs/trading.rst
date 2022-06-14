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

Retrieving Account Details
--------------------------

You can access details about your brokerage account like how much buying power you have,
whether you've been flagged by as a pattern day trader, your total equity.

.. code-block:: python

    from alpaca.trading import TradingClient

    trading_client = TradingClient('api-key', 'secret-key')

    trading_client.


Assets
------


Orders
------


Positions
---------




