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

Crypto data does not require authentication to use. i.e. you can initialize ``CryptoHistoricalDataClient`` without
providing API keys. If you do provide API keys, your rate limit will be higher.

However, to access stock data, you will need to provide your API keys. The keys can be found
on the dashboard after signing in.


Getting Started with Clients
----------------------------

There are 4 different clients that let you access market data. There are 2 historical data clients
and 2 real-time data clients. The crypto data clients do not require API keys to use.


Historical Data
^^^^^^^^^^^^^^^

Historical Data can be queried by using one of the two historical data clients: `StockHistoricalDataClient`
and `CryptoHistoricalDataClient`. Historical data is available for Bar, Trade and Quote datatypes.

.. code-block:: python

    from alpaca.data import CryptoHistoricalDataClient, StockHistoricalDataClient

    # no keys required.
    crypto_client = CryptoHistoricalDataClient()

    # keys required
    stock_client = StockHistoricalDataClient("api-key",  "secret-key")


Real-time Data Stream
^^^^^^^^^^^^^^^^^^^^^

The data stream clients lets you subscribe to real-time data via WebSockets. There are clients
for crypto data and stock data.


.. code-block:: python

    from alpaca.data import CryptoDataStream, StockDataStream

    # no keys required.
    crypto_stream = CryptoDataStream()

    # keys required
    stock_stream = StockDataStream("api-key", "secret-key")


Examples
--------

Retrieving Bar Data
^^^^^^^^^^^^^^^^^^^

You can request bar data via the HistoricalDataClients. In this example, we query
daily bar data for "BTC/USD" and "ETH/USD" since July 1st 2022. You can convert the
response to a multi-index pandas dataframe using the `.df` property.

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



Subscribing to Real-Time Quote Data
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This example shows how to receive live quote data for stocks. To receive real time data, you will need to provide
the client an asynchronous function to handle the data. Finally, you will need to call the
`run` method to start receiving data.

.. code-block:: python

    from alpaca.data.live import StockDataStream


    wss_client = StockDataStream('api-key', 'secret-key')

    # async handler
    async def quote_data_handler(data: Any):
        # quote data will arrive here
        print(data)

    wss_client.subscribe_quotes(quote_data_handler, "SPY")

    wss_client.run()




