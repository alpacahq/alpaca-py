.. _market-data:

===========
Market Data
===========

The market data API allows you to access both live and historical data for equities and cryptocurrencies. 
Over 5 years of historical data is available for thousands of equity and cryptocurrency symbols. 
Various data types are available such as bars/candles (OHLCV), trade data (price and sales), and quote data. For
crypto, there is also orderbook data. For more information on the data types available,
please look at the `API reference <https://alpaca.markets/docs/market-data/>`_.


Subscription Plans
------------------

Most market data features are free to use. However, if you are a professional or institution, you may
wish to expand with the unlimited plan. Learn more about the subscriptions plans at
`alpaca.markets/data <https://alpaca.markets/data>`_.


API Keys
--------

You can sign up for API keys `here <https://app.alpaca.markets/signup>`_. API keys allow you to access
stock data. Keep in mind, crypto data does not require authentication to use. i.e. you can initialize ``CryptoHistoricalDataClient`` without
providing API keys. However, if you do provide API keys, your rate limit will be higher.


Historical Data
---------------

There are 2 historical data clients: ``StockHistoricalDataClient`` and ``CryptoHistoricalDataClient``.
The crypto data client does not require API keys to use.


Clients
^^^^^^^

Historical Data can be queried by using one of the two historical data clients: ``StockHistoricalDataClient``
and ``CryptoHistoricalDataClient``. Historical data is available for Bar, Trade and Quote datatypes. For
crypto, latest orderbook data is also available.

.. code-block:: python

    from alpaca.data import CryptoHistoricalDataClient, StockHistoricalDataClient

    # no keys required.
    crypto_client = CryptoHistoricalDataClient()

    # keys required
    stock_client = StockHistoricalDataClient("api-key",  "secret-key")


Retrieving Latest Quote Data
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The latest quote data is available through the historical data clients.
The method will return a dictionary of Trade objects that are keyed by the corresponding
symbol. We will need to use the ``StockLatestQuoteRequest`` model to prepare the request parameters.

.. attention::
    Models that are returned by both historical data clients are agnostic of the number of
    symbols that were passed in. This means that you must use the symbol as a key to access
    the data regardless of whether a single symbol or multiple symbols were queried. Below is an example
    of this in action.

**Multi Symbol**

.. code-block:: python

    from alpaca.data.historical import StockHistoricalDataClient
    from alpaca.data.requests import StockLatestQuoteRequest
    from alpaca.data.timeframe import TimeFrame

    # keys required for stock historical data client
    client = StockHistoricalDataClient('api-key', 'secret-key')

    # multi symbol request - single symbol is similar
    multisymbol_request_params = StockLatestQuoteRequest(symbol_or_symbols=["SPY", "GLD", "TLT"])

    latest_multisymbol_quotes = client.get_stock_latest_quote(request_params)

    gld_latest_ask_price = latest_quotes["GLD"].ask_price

**Single Symbol**

.. code-block:: python

    from alpaca.data.historical import StockHistoricalDataClient
    from alpaca.data.requests import StockLatestQuoteRequest
    from alpaca.data.timeframe import TimeFrame

    # single symbol request
    request_params = StockLatestQuoteRequest(symbol_or_symbols="ETH/USD")

    latest_quote = client.get_stock_latest_quote(request_params)

    # must use symbol to access even though it is single symbol
    latest_quote["ETH/USD"].ask_price


Retrieving Historical Bar Data
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

You can request bar (candlestick) data via the HistoricalDataClients. In this example, we query
daily bar data for "BTC/USD" and "ETH/USD" since July 1st 2022 using ``CryptoHistoricalDataClient``.
You can convert the response to a multi-index pandas dataframe using the ``.df`` property.

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

    # convert to dataframe
    bars.df

    # access bars as list - important to note that you must access by symbol key
    # even for a single symbol request - models are agnostic to number of symbols
    bars["BTC/USD"]

Real Time Data
--------------

Clients
^^^^^^^

The data stream clients lets you subscribe to real-time data via WebSockets. There are clients
for crypto data and stock data.


.. code-block:: python

    from alpaca.data import CryptoDataStream, StockDataStream

    # no keys required.
    crypto_stream = CryptoDataStream()

    # keys required
    stock_stream = StockDataStream("api-key", "secret-key")


Subscribing to Real-Time Quote Data
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This example shows how to receive live quote data for stocks. To receive real time data, you will need to provide
the client an asynchronous function to handle the data. Finally, you will need to call the
``run`` method to start receiving data.

.. code-block:: python

    from alpaca.data.live import StockDataStream


    wss_client = StockDataStream('api-key', 'secret-key')

    # async handler
    async def quote_data_handler(data: Any):
        # quote data will arrive here
        print(data)

    wss_client.subscribe_quotes(quote_data_handler, "SPY")

    wss_client.run()




