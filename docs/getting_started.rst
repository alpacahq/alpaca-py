.. _introduction:

===============
Getting Started
===============


About
-----

Alpaca-py provides an interface for interacting with the API products Alpaca offers.
These API products are provided as various REST, WebSocket and SSE endpoints that allow you to do
everything from streaming market data to creating your own trading apps. You can learn about the API products Alpaca offers at `alpaca.markets <https://alpaca.markets/>`_.

Usage
-----

Alpaca's APIs allow you to do everything from building algorithmic trading strategies to building
a full brokerage experience for your own end users.
Here are some things you can do with Alpaca-py.

**Market Data API**: Access live and historical market data for 5000+ stocks, 20+ crypto, and options.

**Trading API**: Trade stock, crypto, and options with lightning fast execution speeds.

**Broker API & Connect**: Build investment apps - from robo-advisors to brokerages.


Installation
------------

Alpaca-py is supported on Python 3.7+. You can install Alpaca-py using pip. To learn more
about version histories, visit the `PyPI page <https://pypi.org/project/alpaca-py/>`_.

To install Alpaca-py, run the following pip command in your terminal.

.. code-block:: shell-session

    pip install alpaca-py

Errors
^^^^^^

Try upgrading your pip before installing if you face errors.

.. code-block:: shell-session

    pip install --upgrade pip

Poetry
^^^^^^

If you're using poetry to manage dependencies in your project. You can add Alpaca-py
to your project by running

.. code-block:: shell-session

    poetry add alpaca-py


What's New?
-----------

If you've used the previous python SDK `alpaca-trade-api <https://github.com/alpacahq/alpaca-trade-api-python>`_, there are a few
key differences to be aware of.

Broker API
^^^^^^^^^^

Alpaca-py lets you use Broker API to start building your investment apps! Learn more at the
:ref:`broker` page.

OOP Design
^^^^^^^^^^

Alpaca-py uses a more OOP approach to submitting requests compared to the previous SDK.
To submit a request, you will most likely need to create
a request object containing the desired request data. Generally, there is a unique request model
for each method.

Some examples of request models corresponding to methods:

* ``GetOrdersRequest`` for ``TradingClient.get_orders()``
* ``CryptoLatestOrderbookRequest`` for ``CryptoHistoricalDataClient.get_crypto_latest_orderbook()``

**Request Models Usage Example**

To get historical bar data for crypto, you will need to provide a CryptoBarsRequest object.

.. code-block:: python

    from alpaca.data.historical import CryptoHistoricalDataClient
    from alpaca.data.requests import CryptoBarsRequest
    from alpaca.data.timeframe import TimeFrame

    # no keys required for crypto data
    client = CryptoHistoricalDataClient()

    request_params = CryptoBarsRequest(
                            symbol_or_symbols=["BTC/USD", "ETH/USD"],
                            timeframe=TimeFrame.Day,
                            start="2022-07-01"
                     )

    bars = client.get_crypto_bars(request_params)

Data Validation
^^^^^^^^^^^^^^^

Alpaca-py uses pydantic to validate data models at run-time. This means
if you are receiving request data via JSON from a client. You can handle parsing
and validation through Alpaca's request models. All request models can be instantiated
by passing in data in dictionary format.

Here is a rough example of what is possible.

.. code-block:: python

    @app.route('/post_json', methods=['POST'])
    def do_trade():
        # ...

        order_data_json = request.get_json()

        # validate data
        MarketOrderRequest(**order_data_json)

        # ...

Many Clients
^^^^^^^^^^^^

Alpaca-py has a lot of client classes. There is a client for each API and even
asset class specific clients (``StockHistoricalDataClient``, ``CryptoHistoricalDataClient``, ``OptionHistoricalData``). This requires
you to pick and choose clients based on your needs.

**Broker API:** ``BrokerClient``

**Trading API:** ``TradingClient``

**Market Data API:**  ``StockHistoricalDataClient``, ``CryptoHistoricalDataClient``, ``OptionHistoricalDataClient``, ``CryptoDataStream``, ``StockDataStream``, ``OptionDataStream``



API Keys
--------

Trading and Market Data API
^^^^^^^^^^^^^^^^^^^^^^^^^^^
In order to use Alpaca's services you'll need to `sign up for an Alpaca account <https://app.alpaca.markets/signup>`_ and retrieve your API keys.
Signing up is completely free and takes only a few minutes. Sandbox environments are available to test
out the API. To use the sandbox environment, you will need to provide sandbox/paper keys. API keys are
passed into Alpaca-py through either ``TradingClient``, ``StockHistoricalDataClient``, ``CryptoHistoricalDataClient``, ``OptionHistoricalDataClient``, ``StockDataStream``,  ``CryptoDataStream``, or ``OptionDataStream``.

Broker API
^^^^^^^^^^

To use the Broker API, you will need to sign up for a `broker account <https://broker-app.alpaca.markets/sign-up>`_ and retrieve
your Broker API keys. The API keys can be found on the dashboard once you've logged in. Alpaca also provides a sandbox environment to test out Broker API. To use the sandbox mode, provide your
sandbox keys. Once you have your keys, you can pass them into ``BrokerClient`` to get started.
